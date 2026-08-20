"""P11-TAM-C deterministic trace production foundation smoke test."""

from __future__ import annotations

from pathlib import Path
import subprocess

from language.compiler import SourceMap, compile_source_with_map
from tam import (
    TraceDomain,
    TraceIdentity,
    TraceMap,
    TraceRecord,
    trace_identity_for_source_map_entry,
    trace_identity_for_source_span,
    trace_map_from_source_map,
)


PREDECESSOR_TAG = "afp-p11-tam-b-freeze"
PREDECESSOR_COMMIT = "1cac37a13af6ab229401277848a1a1c6bfef3c4b"

SOURCE = """\
directive Main {
    state count: int = 0
}
"""


def _root() -> Path:
    return Path(__file__).resolve().parents[1]


def _git(*arguments: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ("git", *arguments),
        cwd=_root(),
        check=False,
        text=True,
        encoding="utf-8",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _expect(exc_type, operation):
    try:
        operation()
    except exc_type as error:
        return error
    raise AssertionError("Expected {}.".format(exc_type.__name__))


def _artifact():
    return compile_source_with_map(SOURCE, source_name="tam_c.apex")


def _assert_predecessor() -> None:
    tag = _git("rev-parse", "{}^{{}}".format(PREDECESSOR_TAG))
    _require(tag.returncode == 0, tag.stderr.strip())
    _require(
        tag.stdout.strip() == PREDECESSOR_COMMIT,
        "TAM-B freeze target changed",
    )
    ancestry = _git(
        "merge-base",
        "--is-ancestor",
        PREDECESSOR_TAG,
        "HEAD",
    )
    _require(ancestry.returncode == 0, "TAM-B is not an ancestor of TAM-C")


def _assert_frozen_model_reuse() -> None:
    production = (_root() / "apexforge/tam/production.py").read_text(
        encoding="utf-8"
    )
    _require(
        "from .model import TraceDomain, TraceIdentity, TraceMap, TraceRecord"
        in production,
        "TAM-C does not reuse the frozen TAM-B model",
    )

    diff = _git(
        "diff",
        "--exit-code",
        PREDECESSOR_TAG,
        "--",
        "apexforge/tam/model.py",
    )
    _require(diff.returncode == 0, "TAM-C mutated frozen TAM-B model.py")


def _assert_real_source_map_projection() -> None:
    artifact = _artifact()
    source_map = artifact.source_map

    _require(type(source_map) is SourceMap, "compile source map type changed")
    _require(len(source_map.entries) > 0, "fixture produced no source-map entries")

    first = trace_map_from_source_map(source_map)
    second = trace_map_from_source_map(source_map)

    _require(type(first) is TraceMap, "projection did not return TraceMap")
    _require(first == second, "same SourceMap produced different TraceMap")
    _require(
        tuple(record.trace_id for record in first.records)
        == tuple(record.trace_id for record in second.records),
        "same SourceMap produced different trace identities",
    )

    transformation_records = tuple(
        record
        for record in first.records
        if record.domain == TraceDomain("transformation")
    )
    source_records = tuple(
        record
        for record in first.records
        if record.domain == TraceDomain("source")
    )

    _require(
        len(transformation_records) == len(source_map.entries),
        "SourceMapEntry count does not match transformation trace count",
    )
    _require(len(source_records) > 0, "source trace records missing")

    _require(
        tuple(record.canonical_identity for record in transformation_records)
        == tuple(entry.air_id for entry in source_map.entries),
        "SourceMap entry order or AIR identity reference changed",
    )

    for index, (entry, record) in enumerate(
        zip(source_map.entries, transformation_records)
    ):
        _require(
            record.trace_id
            == trace_identity_for_source_map_entry(entry, entry_index=index),
            "source-map entry trace identity changed",
        )
        _require(
            record.source_span is entry.span,
            "TAM did not preserve exact SourceSpan reference",
        )
        _require(
            record.canonical_identity == entry.air_id,
            "TAM replaced or changed existing AIR identity",
        )
        _require(
            record.provenance == (),
            "TAM fabricated provenance for SourceMap evidence",
        )
        _require(
            len(record.upstream_trace_ids) == 1,
            "SourceMap trace must have one source upstream trace",
        )
        _require(
            record.upstream_trace_ids[0]
            == trace_identity_for_source_span(entry.span),
            "source upstream trace identity changed",
        )

    for record in source_records:
        _require(record.canonical_identity is None, "source trace fabricated identity")
        _require(record.provenance == (), "source trace fabricated provenance")
        _require(record.source_span is not None, "source trace lost SourceSpan")
        _require(
            record.trace_id == trace_identity_for_source_span(record.source_span),
            "source trace identity changed",
        )
        _require(
            len(record.downstream_trace_ids) > 0,
            "source trace lost observed downstream mapping",
        )


def _assert_empty_source_map() -> None:
    empty = trace_map_from_source_map(SourceMap())
    _require(empty == TraceMap(), "empty SourceMap fabricated traces")


def _assert_identity_determinism() -> None:
    artifact = _artifact()
    entry = artifact.source_map.entries[0]

    first_span = trace_identity_for_source_span(entry.span)
    second_span = trace_identity_for_source_span(entry.span)
    _require(first_span == second_span, "source span trace identity is unstable")

    first_entry = trace_identity_for_source_map_entry(entry, entry_index=0)
    second_entry = trace_identity_for_source_map_entry(entry, entry_index=0)
    _require(first_entry == second_entry, "source-map trace identity is unstable")

    _require(type(first_span) is TraceIdentity, "source trace identity type changed")
    _require(type(first_entry) is TraceIdentity, "entry trace identity type changed")
    _require(first_span.value.startswith("tam:source:"), "source trace prefix changed")
    _require(
        first_entry.value.startswith("tam:source-map-entry:"),
        "source-map trace prefix changed",
    )

    _expect(
        ValueError,
        lambda: trace_identity_for_source_map_entry(entry, entry_index=-1),
    )
    _expect(
        TypeError,
        lambda: trace_identity_for_source_map_entry(entry, entry_index=True),
    )


def _assert_pure_adapter_surface() -> None:
    text = (_root() / "apexforge/tam/production.py").read_text(encoding="utf-8")

    forbidden = (
        "compile_source_with_map(",
        "compile_source(",
        "parse_source_unit(",
        "ProjectBuilder",
        "analyze_semantic_decision_source(",
        "analyze_narrative_source(",
        "evaluate_advanced_condition",
        "construct_semantic_convergence_set",
        "apply_semantic_convergence_policy",
        "assess_paradox_elevation",
        "elevate_paradox",
        "runtime.engine",
        "language_server",
        "tooling.cli",
    )
    for token in forbidden:
        _require(token not in text, "TAM-C acquired operative integration: " + token)


def _assert_predecessor_owners_unchanged() -> None:
    paths = (
        "apexforge/language/source.py",
        "apexforge/language/compiler.py",
        "apexforge/language/project.py",
        "apexforge/tooling/cli.py",
        "apexforge/tooling/project_loader.py",
        "apexforge/language_server/diagnostics.py",
        "apexforge/language/semantic_decision_analysis.py",
        "apexforge/language/semantic_decision_project_analysis.py",
        "apexforge/language/narrative_analysis.py",
        "apexforge/semantic_lattice/adapters.py",
    )
    diff = _git("diff", "--exit-code", PREDECESSOR_TAG, "--", *paths)
    _require(diff.returncode == 0, "TAM-C mutated frozen integration owners")


def main() -> None:
    _assert_predecessor()
    _assert_frozen_model_reuse()
    _assert_real_source_map_projection()
    _assert_empty_source_map()
    _assert_identity_determinism()
    _assert_pure_adapter_surface()
    _assert_predecessor_owners_unchanged()

    print("P11_TAM_B_FREEZE_ANCESTRY=PASS")
    print("TAM_B_MODEL_REUSE=PASS")
    print("REAL_SOURCE_MAP_CONSUMPTION=PASS")
    print("SAME_INPUT_SAME_TRACE_ID=PASS")
    print("SAME_INPUT_SAME_TRACE_MAP=PASS")
    print("SOURCE_MAP_ENTRY_ORDER=PRESERVED")
    print("SOURCE_SPAN=EXACT_REFERENCE")
    print("AIR_ID=REFERENCE_ONLY")
    print("SOURCE_MAP=CONSUMED_NOT_REPLACED")
    print("MISSING_EVIDENCE=NO_FABRICATION")
    print("EMPTY_SOURCE_MAP=EMPTY_TRACE_MAP")
    print("UPSTREAM_DOWNSTREAM_LINKS=OBSERVATIONAL")
    print("COMPILER_MUTATION=NONE")
    print("PROJECTBUILDER_MUTATION=NONE")
    print("CLI_LSP_INTEGRATION=NONE")
    print("SEMANTIC_EXECUTION=NONE")
    print("P11_TAM_C_DETERMINISTIC_TRACE_PRODUCTION=PASS")


if __name__ == "__main__":
    main()