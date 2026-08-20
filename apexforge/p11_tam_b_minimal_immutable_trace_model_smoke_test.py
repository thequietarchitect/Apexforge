"""P11-TAM-B minimal immutable trace model smoke test."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path
import subprocess

from tam import (
    CANONICAL_TRACE_DOMAINS,
    TRACE_DOMAIN_IDS,
    TRACE_SCHEMA_VERSION,
    TraceDomain,
    TraceIdentity,
    TraceMap,
    TraceRecord,
)


PREDECESSOR_TAG = "afp-p11-tam-a-freeze"
PREDECESSOR_COMMIT = "d7967f0fd25d96c8bbd779627adff5aa37431b07"

EXPECTED_DOMAINS = (
    "source",
    "token",
    "declaration",
    "reference",
    "scope",
    "type",
    "authority",
    "narrative",
    "ownership",
    "transformation",
)

FROZEN_PREDECESSOR_OWNERS = (
    "apexforge/language/source.py",
    "apexforge/language/lexer.py",
    "apexforge/language/parser.py",
    "apexforge/language/compiler.py",
    "apexforge/language/declarations.py",
    "apexforge/language/identities.py",
    "apexforge/language/resolution_candidates.py",
    "apexforge/language/resolution_context.py",
    "apexforge/language/narrative_source.py",
    "apexforge/language/narrative_analysis.py",
    "apexforge/language/narrative_lowering.py",
    "apexforge/language/semantic_decision_source.py",
    "apexforge/language/semantic_decision_parser.py",
    "apexforge/language/semantic_decision_lowering.py",
    "apexforge/language/semantic_decision_analysis.py",
    "apexforge/language/semantic_decision_project_analysis.py",
    "apexforge/aether_air/records.py",
    "apexforge/aether_air/transformation.py",
    "apexforge/aether_air/projection.py",
    "apexforge/semantic_lattice/model.py",
    "apexforge/semantic_lattice/adapters.py",
)


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


def _domain(name: str) -> TraceDomain:
    return TraceDomain(name)


def _record(
    trace_id: str,
    domain: str,
    *,
    upstream=(),
    downstream=(),
) -> TraceRecord:
    return TraceRecord(
        trace_id=TraceIdentity(trace_id),
        domain=_domain(domain),
        producer="language.compiler",
        owner="language.compiler",
        representation="source-map",
        canonical_identity="directive:Main",
        provenance=("source:main.apex:1:1-1:10",),
        upstream_trace_ids=tuple(TraceIdentity(item) for item in upstream),
        downstream_trace_ids=tuple(TraceIdentity(item) for item in downstream),
    )


def _assert_predecessor_freeze() -> None:
    tag = _git("rev-parse", "{}^{{}}".format(PREDECESSOR_TAG))
    _require(tag.returncode == 0, tag.stderr.strip())
    _require(tag.stdout.strip() == PREDECESSOR_COMMIT, "TAM-A freeze target changed")

    ancestry = _git(
        "merge-base",
        "--is-ancestor",
        PREDECESSOR_TAG,
        "HEAD",
    )
    _require(ancestry.returncode == 0, "TAM-A is not an ancestor of TAM-B")


def _assert_domain_contract() -> None:
    _require(TRACE_SCHEMA_VERSION == 1, "unexpected TAM schema version")
    _require(TRACE_DOMAIN_IDS == EXPECTED_DOMAINS, "trace-domain taxonomy changed")
    _require(
        tuple(item.canonical_id for item in CANONICAL_TRACE_DOMAINS)
        == EXPECTED_DOMAINS,
        "canonical trace-domain objects changed",
    )
    _require(
        len(set(CANONICAL_TRACE_DOMAINS)) == len(EXPECTED_DOMAINS),
        "canonical trace domains are not unique",
    )

    _expect(ValueError, lambda: TraceDomain("unknown"))
    _expect(ValueError, lambda: TraceDomain(" source"))
    _expect(TypeError, lambda: TraceDomain(1))


def _assert_identity_contract() -> None:
    identity = TraceIdentity("tam:source:main")
    _require(identity.value == "tam:source:main", "trace identity changed")
    _expect(ValueError, lambda: TraceIdentity(""))
    _expect(ValueError, lambda: TraceIdentity(" padded "))
    _expect(TypeError, lambda: TraceIdentity(7))


def _assert_record_immutability_and_validation() -> None:
    record = _record(
        "tam:transformation:compile-main",
        "transformation",
        upstream=("tam:source:main",),
        downstream=("tam:declaration:main",),
    )

    _require(record.schema_version == 1, "trace schema version changed")
    _require(record.source_span is None, "unexpected source span fabricated")
    _require(
        record.canonical_identity == "directive:Main",
        "canonical identity reference changed",
    )
    _require(
        record.provenance == ("source:main.apex:1:1-1:10",),
        "provenance changed",
    )

    _expect(
        FrozenInstanceError,
        lambda: setattr(record, "producer", "mutated"),
    )
    _expect(
        TypeError,
        lambda: TraceRecord(
            trace_id=TraceIdentity("tam:bad:span"),
            domain=_domain("source"),
            producer="language.source",
            owner="language.source",
            representation="source",
            source_span=object(),
        ),
    )
    _expect(
        ValueError,
        lambda: TraceRecord(
            trace_id=TraceIdentity("tam:self"),
            domain=_domain("transformation"),
            producer="producer",
            owner="owner",
            representation="stage",
            upstream_trace_ids=(TraceIdentity("tam:self"),),
        ),
    )
    _expect(
        ValueError,
        lambda: TraceRecord(
            trace_id=TraceIdentity("tam:duplicate-provenance"),
            domain=_domain("source"),
            producer="producer",
            owner="owner",
            representation="stage",
            provenance=("evidence:a", "evidence:a"),
        ),
    )


def _assert_trace_map_contract() -> None:
    first = _record(
        "tam:source:main",
        "source",
        downstream=("tam:transformation:compile-main",),
    )
    second = _record(
        "tam:transformation:compile-main",
        "transformation",
        upstream=("tam:source:main",),
    )

    trace_map = TraceMap((first, second))
    repeated = TraceMap((first, second))

    _require(trace_map == repeated, "TraceMap construction is not deterministic")
    _require(trace_map.records == (first, second), "TraceMap order changed")
    _require(trace_map.find(first.trace_id) is first, "TraceMap.find changed identity")
    _require(
        trace_map.find(TraceIdentity("tam:missing")) is None,
        "TraceMap.find fabricated a missing record",
    )
    _require(
        trace_map.for_domain(_domain("source")) == (first,),
        "TraceMap domain query changed",
    )
    _require(
        trace_map.for_domain(_domain("reference")) == (),
        "TraceMap fabricated a domain record",
    )

    _expect(
        FrozenInstanceError,
        lambda: setattr(trace_map, "records", ()),
    )
    _expect(ValueError, lambda: TraceMap((first, first)))
    _expect(TypeError, lambda: TraceMap([first]))


def _assert_observational_only_surface() -> None:
    root = _root()
    model_text = (root / "apexforge/tam/model.py").read_text(encoding="utf-8")
    forbidden = (
        "evaluate_advanced_condition",
        "construct_semantic_convergence_set",
        "apply_semantic_convergence_policy",
        "assess_paradox_elevation",
        "elevate_paradox",
        "validate_semantic_outcome",
        "runtime.engine",
        "ProjectBuilder",
        "parse_source_unit(",
        "compile_source(",
        "analyze_semantic_decision_source(",
        "analyze_narrative_source(",
    )
    for name in forbidden:
        _require(name not in model_text, "TAM-B acquired operative behavior: " + name)


def _assert_predecessor_owner_immutability() -> None:
    completed = _git(
        "diff",
        "--exit-code",
        PREDECESSOR_TAG,
        "--",
        *FROZEN_PREDECESSOR_OWNERS,
    )
    _require(
        completed.returncode == 0,
        "TAM-B mutated frozen predecessor owner",
    )


def main() -> None:
    _assert_predecessor_freeze()
    _assert_domain_contract()
    _assert_identity_contract()
    _assert_record_immutability_and_validation()
    _assert_trace_map_contract()
    _assert_observational_only_surface()
    _assert_predecessor_owner_immutability()

    print("P11_TAM_A_FREEZE_ANCESTRY=PASS")
    print("TRACE_SCHEMA_VERSION=1")
    print("TRACE_DOMAIN_COUNT=10")
    print("TRACE_DOMAIN_TAXONOMY=PASS")
    print("TRACE_IDENTITY=PASS")
    print("TRACE_RECORD_IMMUTABLE=PASS")
    print("TRACE_MAP_IMMUTABLE=PASS")
    print("TRACE_MAP_ORDER_PRESERVED=PASS")
    print("TRACE_MAP_LOOKUP=PASS")
    print("SOURCE_SPAN_REFERENCE=OPTIONAL_NO_FABRICATION")
    print("CANONICAL_IDENTITY=REFERENCE_ONLY")
    print("PROVENANCE=REFERENCE_ONLY")
    print("UPSTREAM_DOWNSTREAM_LINKS=OBSERVATIONAL")
    print("COMPILER_INSTRUMENTATION=NONE")
    print("CLI_LSP_INTEGRATION=NONE")
    print("SEMANTIC_EXECUTION=NONE")
    print("FROZEN_OWNER_IMMUTABILITY=PASS")
    print("P11_TAM_B_MINIMAL_IMMUTABLE_TRACE_MODEL=PASS")


if __name__ == "__main__":
    main()