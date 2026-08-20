"""P11-TAM-D declaration, identity, and ownership trace production smoke."""

from __future__ import annotations

from pathlib import Path
import subprocess

from language.compiler import compile_source_with_map
from language.declarations import ProjectDeclarationOwner, ProjectDeclarationOwnership
from language.identities import ProjectDeclaredIdentity, ProjectIdentityIndex
from tam import (
    TraceDomain,
    TraceMap,
    trace_map_from_declaration_identity_indexes,
    trace_record_from_declaration_owner,
    trace_record_from_declared_identity,
)


PREDECESSOR_TAG = "afp-p11-tam-c-freeze"
PREDECESSOR_COMMIT = "8e64220fba18ff4e72726468dd59f041bc493bd2"

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


def _canonical_span_and_air_id():
    artifact = compile_source_with_map(SOURCE, source_name="tam_d.apex")
    _require(len(artifact.source_map.entries) > 0, "fixture has no SourceMap entry")
    entry = next(entry for entry in artifact.source_map.entries if entry.air_id == "directive:Main")
    return entry.span, entry.air_id


def _indexes():
    span, air_id = _canonical_span_and_air_id()

    owner_a = ProjectDeclarationOwner(
        kind="directive",
        air_id=air_id,
        source_name="tam_d.apex",
        module_name=None,
        span=span,
    )
    owner_b = ProjectDeclarationOwner(
        kind="function",
        air_id="function:MainAlias",
        source_name="tam_d.apex",
        module_name=None,
        span=span,
    )
    identity_a = ProjectDeclaredIdentity(
        kind="directive",
        declared_name="Main",
        current_air_id=air_id,
        source_name="tam_d.apex",
        module_name=None,
        qualified_display_name="Main",
        span=span,
    )
    identity_b = ProjectDeclaredIdentity(
        kind="function",
        declared_name="MainAlias",
        current_air_id="function:MainAlias",
        source_name="tam_d.apex",
        module_name=None,
        qualified_display_name="MainAlias",
        span=span,
    )
    return (
        ProjectDeclarationOwnership((owner_a, owner_b)),
        ProjectIdentityIndex((identity_a, identity_b)),
    )


def _assert_predecessor() -> None:
    tag = _git("rev-parse", "{}^{{}}".format(PREDECESSOR_TAG))
    _require(tag.returncode == 0, tag.stderr.strip())
    _require(
        tag.stdout.strip() == PREDECESSOR_COMMIT,
        "TAM-C freeze target changed",
    )
    ancestry = _git("merge-base", "--is-ancestor", PREDECESSOR_TAG, "HEAD")
    _require(ancestry.returncode == 0, "TAM-C is not an ancestor of TAM-D")


def _assert_index_projection() -> None:
    ownership, identity_index = _indexes()

    first = trace_map_from_declaration_identity_indexes(
        ownership,
        identity_index,
    )
    second = trace_map_from_declaration_identity_indexes(
        ownership,
        identity_index,
    )

    _require(type(first) is TraceMap, "combined projection did not return TraceMap")
    _require(first == second, "same indexes produced different TraceMap")

    ownership_records = first.records[: len(ownership.declarations)]
    identity_records = first.records[len(ownership.declarations) :]

    _require(
        len(ownership_records) == len(ownership.declarations),
        "declaration ownership record count changed",
    )
    _require(
        len(identity_records) == len(identity_index.identities),
        "declared identity record count changed",
    )

    for index, (declaration, record) in enumerate(
        zip(ownership.declarations, ownership_records)
    ):
        expected = trace_record_from_declaration_owner(
            declaration,
            declaration_index=index,
        )
        _require(record == expected, "declaration ownership order changed")
        _require(
            record.domain == TraceDomain("ownership"),
            "declaration owner trace domain changed",
        )
        _require(
            record.source_span is declaration.span,
            "declaration owner lost exact SourceSpan reference",
        )
        _require(
            record.canonical_identity == declaration.air_id,
            "declaration owner AIR identity changed",
        )
        _require(
            record.provenance == (),
            "declaration owner fabricated provenance",
        )
        _require(
            record.upstream_trace_ids == ()
            and record.downstream_trace_ids == (),
            "declaration owner fabricated graph links",
        )

    for index, (identity, record) in enumerate(
        zip(identity_index.identities, identity_records)
    ):
        expected = trace_record_from_declared_identity(
            identity,
            identity_index=index,
        )
        _require(record == expected, "declared identity order changed")
        _require(
            record.domain == TraceDomain("declaration"),
            "declared identity trace domain changed",
        )
        _require(
            record.source_span is identity.span,
            "declared identity lost exact SourceSpan reference",
        )
        _require(
            record.canonical_identity == identity.current_air_id,
            "declared identity AIR identity changed",
        )
        _require(
            record.provenance == (),
            "declared identity fabricated provenance",
        )
        _require(
            record.upstream_trace_ids == ()
            and record.downstream_trace_ids == (),
            "declared identity fabricated graph links",
        )

    _require(
        ownership_records[0].canonical_identity
        == identity_records[0].canonical_identity,
        "fixture no longer shares canonical AIR identity",
    )
    _require(
        ownership_records[0].trace_id != identity_records[0].trace_id,
        "ownership and declared identity traces collapsed",
    )


def _assert_identity_determinism() -> None:
    ownership, identity_index = _indexes()
    declaration = ownership.declarations[0]
    identity = identity_index.identities[0]

    owner_first = trace_record_from_declaration_owner(
        declaration,
        declaration_index=0,
    )
    owner_second = trace_record_from_declaration_owner(
        declaration,
        declaration_index=0,
    )
    identity_first = trace_record_from_declared_identity(
        identity,
        identity_index=0,
    )
    identity_second = trace_record_from_declared_identity(
        identity,
        identity_index=0,
    )

    _require(owner_first.trace_id == owner_second.trace_id, "owner ID unstable")
    _require(
        identity_first.trace_id == identity_second.trace_id,
        "declared identity ID unstable",
    )
    _require(
        owner_first.trace_id.value.startswith("tam:declaration-owner:"),
        "ownership trace prefix changed",
    )
    _require(
        identity_first.trace_id.value.startswith("tam:declared-identity:"),
        "declared identity trace prefix changed",
    )

    _expect(
        ValueError,
        lambda: trace_record_from_declaration_owner(
            declaration,
            declaration_index=-1,
        ),
    )
    _expect(
        TypeError,
        lambda: trace_record_from_declared_identity(
            identity,
            identity_index=True,
        ),
    )


def _assert_empty_indexes() -> None:
    result = trace_map_from_declaration_identity_indexes(
        ProjectDeclarationOwnership(),
        ProjectIdentityIndex(),
    )
    _require(result == TraceMap(), "empty metadata indexes fabricated traces")


def _assert_exact_types() -> None:
    ownership, identity_index = _indexes()
    _expect(
        TypeError,
        lambda: trace_map_from_declaration_identity_indexes(
            object(),
            identity_index,
        ),
    )
    _expect(
        TypeError,
        lambda: trace_map_from_declaration_identity_indexes(
            ownership,
            object(),
        ),
    )
    _expect(
        TypeError,
        lambda: trace_record_from_declaration_owner(
            object(),
            declaration_index=0,
        ),
    )
    _expect(
        TypeError,
        lambda: trace_record_from_declared_identity(
            object(),
            identity_index=0,
        ),
    )


def _assert_pure_adapter_surface() -> None:
    text = (_root() / "apexforge/tam/production.py").read_text(encoding="utf-8")

    forbidden = (
        "ProjectBuilder",
        "parse_source_unit(",
        "compile_source_with_map(",
        "compile_source(",
        ".find_all(",
        ".find_current_air_id(",
        ".find_qualified_display_name(",
        "resolve_reference",
        "resolve_identity",
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
        _require(token not in text, "TAM-D acquired operative behavior: " + token)


def _assert_frozen_owners_unchanged() -> None:
    paths = (
        "apexforge/tam/model.py",
        "apexforge/language/source.py",
        "apexforge/language/compiler.py",
        "apexforge/language/declarations.py",
        "apexforge/language/identities.py",
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
    _require(diff.returncode == 0, "TAM-D mutated frozen semantic owner")


def main() -> None:
    _assert_predecessor()
    _assert_index_projection()
    _assert_identity_determinism()
    _assert_empty_indexes()
    _assert_exact_types()
    _assert_pure_adapter_surface()
    _assert_frozen_owners_unchanged()

    print("P11_TAM_C_FREEZE_ANCESTRY=PASS")
    print("DECLARATION_OWNER_CONSUMPTION=PASS")
    print("DECLARED_IDENTITY_CONSUMPTION=PASS")
    print("AIR_ID=REFERENCE_ONLY")
    print("SOURCE_SPAN=EXACT_REFERENCE")
    print("OWNER_AND_IDENTITY_TRACES=DISTINCT")
    print("OWNERSHIP_INPUT_ORDER=PRESERVED")
    print("IDENTITY_INPUT_ORDER=PRESERVED")
    print("SAME_INPUT_SAME_TRACE_ID=PASS")
    print("SAME_INPUT_SAME_TRACE_MAP=PASS")
    print("MISSING_EVIDENCE=NO_FABRICATION")
    print("EMPTY_INDEXES=EMPTY_TRACE_MAP")
    print("GRAPH_LINK_INFERENCE=NONE")
    print("DECLARATION_GENERATION=NONE")
    print("IDENTITY_GENERATION=NONE")
    print("RESOLUTION_EXECUTION=NONE")
    print("COMPILER_MUTATION=NONE")
    print("PROJECTBUILDER_MUTATION=NONE")
    print("CLI_LSP_INTEGRATION=NONE")
    print("SEMANTIC_EXECUTION=NONE")
    print("P11_TAM_D_DECLARATION_IDENTITY_OWNERSHIP_TRACE_PRODUCTION=PASS")


if __name__ == "__main__":
    main()