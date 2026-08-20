"""P11-TAM-E reference, scope, and resolution-evidence trace production."""

from __future__ import annotations

from pathlib import Path
import subprocess

from language.compiler import compile_source_with_map
from language.declarations import ProjectDeclarationOwner
from language.identities import ProjectDeclaredIdentity
from language.resolution_candidates import (
    ProjectQualification,
    ProjectResolutionCandidate,
    ProjectResolutionCandidateIndex,
)
from language.resolution_context import ProjectResolutionContext
from language.resolution_queries import (
    ProjectAmbiguousResolution,
    ProjectResolvedBinding,
    ProjectResolutionQuery,
    ProjectUnresolvedResolution,
)
from tam import (
    TraceDomain,
    TraceMap,
    trace_map_from_resolution_observation,
    trace_record_from_resolution_candidate,
    trace_record_from_resolution_context,
    trace_record_from_resolution_outcome,
    trace_record_from_resolution_query,
)


PREDECESSOR_TAG = "afp-p11-tam-d-freeze"
PREDECESSOR_COMMIT = "8b97f4336d724155e423ec3cf6ef9fddd3c210da"

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


def _directive_span(source_name: str):
    artifact = compile_source_with_map(SOURCE, source_name=source_name)
    return next(
        entry.span
        for entry in artifact.source_map.entries
        if entry.air_id == "directive:Main"
    )


def _candidate(
    *,
    source_name: str,
    module_name,
) -> ProjectResolutionCandidate:
    span = _directive_span(source_name)
    identity = ProjectDeclaredIdentity(
        kind="directive",
        declared_name="Main",
        current_air_id="directive:Main",
        source_name=source_name,
        module_name=module_name,
        qualified_display_name=(
            "Main" if module_name is None else "{}.Main".format(module_name)
        ),
        span=span,
    )
    owner = ProjectDeclarationOwner(
        kind="directive",
        air_id="directive:Main",
        source_name=source_name,
        module_name=module_name,
        span=span,
    )
    qualification = ProjectQualification(
        kind="directive",
        module_segments=(
            () if module_name is None else tuple(module_name.split("."))
        ),
        declaration_path=("Main",),
        legacy=module_name is None,
    )
    return ProjectResolutionCandidate(
        identity=identity,
        owner=owner,
        qualification=qualification,
    )


def _fixture():
    legacy = _candidate(
        source_name="legacy.apex",
        module_name=None,
    )
    module = _candidate(
        source_name="module.apex",
        module_name="pkg",
    )
    index = ProjectResolutionCandidateIndex((module, legacy))
    query = ProjectResolutionQuery(
        kind="directive",
        declaration_path=("Main",),
        module_segments=None,
    )
    context = ProjectResolutionContext(
        source_name="consumer.apex",
        module_segments=(),
        imported_modules=(("pkg",),),
    )
    resolved = ProjectResolvedBinding(query=query, candidate=legacy)
    unresolved = ProjectUnresolvedResolution(query=query)
    ambiguous = ProjectAmbiguousResolution(
        query=query,
        candidates=(module, legacy),
    )
    return index, query, context, resolved, unresolved, ambiguous


def _assert_predecessor() -> None:
    tag = _git("rev-parse", "{}^{{}}".format(PREDECESSOR_TAG))
    _require(tag.returncode == 0, tag.stderr.strip())
    _require(
        tag.stdout.strip() == PREDECESSOR_COMMIT,
        "TAM-D freeze target changed",
    )
    ancestry = _git("merge-base", "--is-ancestor", PREDECESSOR_TAG, "HEAD")
    _require(ancestry.returncode == 0, "TAM-D is not an ancestor of TAM-E")


def _assert_query_and_scope_projection() -> None:
    _, query, context, _, _, _ = _fixture()

    query_first = trace_record_from_resolution_query(query)
    query_second = trace_record_from_resolution_query(query)
    _require(query_first == query_second, "query trace is non-deterministic")
    _require(
        query_first.domain == TraceDomain("reference"),
        "query trace domain changed",
    )
    _require(query_first.source_span is None, "query fabricated SourceSpan")
    _require(
        query_first.canonical_identity is None,
        "query fabricated canonical identity",
    )
    _require(query_first.provenance == (), "query fabricated provenance")

    context_first = trace_record_from_resolution_context(context)
    context_second = trace_record_from_resolution_context(context)
    _require(context_first == context_second, "context trace is non-deterministic")
    _require(
        context_first.domain == TraceDomain("scope"),
        "context trace domain changed",
    )
    _require(context_first.source_span is None, "context fabricated SourceSpan")
    _require(
        context_first.canonical_identity is None,
        "context fabricated canonical identity",
    )
    _require(context_first.provenance == (), "context fabricated provenance")


def _assert_candidate_projection() -> None:
    index, _, _, _, _, _ = _fixture()

    first_records = tuple(
        trace_record_from_resolution_candidate(
            candidate,
            candidate_index=index_value,
        )
        for index_value, candidate in enumerate(index.candidates)
    )
    second_records = tuple(
        trace_record_from_resolution_candidate(
            candidate,
            candidate_index=index_value,
        )
        for index_value, candidate in enumerate(index.candidates)
    )
    _require(first_records == second_records, "candidate traces are unstable")

    for candidate, record in zip(index.candidates, first_records):
        _require(
            record.domain == TraceDomain("reference"),
            "candidate trace domain changed",
        )
        _require(
            record.source_span is candidate.identity.span,
            "candidate lost exact identity SourceSpan",
        )
        _require(
            record.canonical_identity == candidate.identity.current_air_id,
            "candidate AIR ID changed",
        )
        _require(record.provenance == (), "candidate fabricated provenance")
        _require(
            record.upstream_trace_ids == ()
            and record.downstream_trace_ids == (),
            "candidate fabricated graph links",
        )


def _assert_outcome_projection() -> None:
    _, _, _, resolved, unresolved, ambiguous = _fixture()

    resolved_record = trace_record_from_resolution_outcome(resolved)
    _require(
        resolved_record.representation == "project-resolved-binding",
        "resolved representation changed",
    )
    _require(
        resolved_record.canonical_identity
        == resolved.candidate.identity.current_air_id,
        "resolved binding AIR identity changed",
    )
    _require(
        resolved_record.source_span is resolved.candidate.identity.span,
        "resolved binding lost exact SourceSpan",
    )

    unresolved_record = trace_record_from_resolution_outcome(unresolved)
    _require(
        unresolved_record.representation == "project-unresolved-resolution",
        "unresolved representation changed",
    )
    _require(
        unresolved_record.canonical_identity is None,
        "unresolved resolution fabricated canonical identity",
    )
    _require(
        unresolved_record.source_span is None,
        "unresolved resolution fabricated SourceSpan",
    )

    ambiguous_record = trace_record_from_resolution_outcome(ambiguous)
    _require(
        ambiguous_record.representation == "project-ambiguous-resolution",
        "ambiguous representation changed",
    )
    _require(
        ambiguous_record.canonical_identity is None,
        "ambiguous resolution collapsed multiple candidates",
    )
    _require(
        ambiguous_record.source_span is None,
        "ambiguous resolution fabricated one source span",
    )

    _require(
        trace_record_from_resolution_outcome(resolved)
        == trace_record_from_resolution_outcome(resolved),
        "resolved outcome trace is unstable",
    )
    _require(
        trace_record_from_resolution_outcome(unresolved)
        == trace_record_from_resolution_outcome(unresolved),
        "unresolved outcome trace is unstable",
    )
    _require(
        trace_record_from_resolution_outcome(ambiguous)
        == trace_record_from_resolution_outcome(ambiguous),
        "ambiguous outcome trace is unstable",
    )


def _assert_aggregate_projection() -> None:
    index, query, context, _, _, ambiguous = _fixture()

    first = trace_map_from_resolution_observation(
        index,
        query,
        context,
        ambiguous,
    )
    second = trace_map_from_resolution_observation(
        index,
        query,
        context,
        ambiguous,
    )
    _require(type(first) is TraceMap, "aggregate did not return TraceMap")
    _require(first == second, "same resolution observation produced different maps")
    _require(
        len(first.records) == 2 + len(index.candidates) + 1,
        "aggregate trace record count changed",
    )
    _require(
        first.records[0] == trace_record_from_resolution_query(query),
        "aggregate query position changed",
    )
    _require(
        first.records[1] == trace_record_from_resolution_context(context),
        "aggregate context position changed",
    )

    candidate_records = first.records[2:-1]
    expected_candidates = tuple(
        trace_record_from_resolution_candidate(
            candidate,
            candidate_index=index_value,
        )
        for index_value, candidate in enumerate(index.candidates)
    )
    _require(
        candidate_records == expected_candidates,
        "canonical candidate-index order was not preserved",
    )
    _require(
        first.records[-1] == trace_record_from_resolution_outcome(ambiguous),
        "aggregate outcome position changed",
    )


def _assert_no_resolution_execution() -> None:
    text = (_root() / "apexforge/tam/production.py").read_text(encoding="utf-8")
    forbidden = (
        "resolve_project_query(",
        "resolve_project_contextual_query(",
        "collect_project_visibility_evidence(",
        "evaluate_project_visibility(",
        "filter_project_visible_candidates(",
        ".find_all(",
        ".find_current_air_id(",
        ".find_qualification(",
        "ProjectBuilder",
        "parse_source_unit(",
        "compile_source_with_map(",
        "compile_source(",
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
        _require(token not in text, "TAM-E acquired operative behavior: " + token)


def _assert_type_and_coherence_guards() -> None:
    index, query, context, resolved, _, _ = _fixture()

    _expect(TypeError, lambda: trace_record_from_resolution_query(object()))
    _expect(TypeError, lambda: trace_record_from_resolution_context(object()))
    _expect(
        TypeError,
        lambda: trace_record_from_resolution_candidate(
            object(),
            candidate_index=0,
        ),
    )
    _expect(
        TypeError,
        lambda: trace_record_from_resolution_candidate(
            index.candidates[0],
            candidate_index=True,
        ),
    )
    _expect(TypeError, lambda: trace_record_from_resolution_outcome(object()))

    different_query = ProjectResolutionQuery(
        kind="directive",
        declaration_path=("Other",),
        module_segments=None,
    )
    _expect(
        ValueError,
        lambda: trace_map_from_resolution_observation(
            index,
            different_query,
            context,
            resolved,
        ),
    )

    foreign_candidate = _candidate(
        source_name="foreign.apex",
        module_name=None,
    )
    foreign_resolved = ProjectResolvedBinding(
        query=query,
        candidate=foreign_candidate,
    )
    _expect(
        ValueError,
        lambda: trace_map_from_resolution_observation(
            index,
            query,
            context,
            foreign_resolved,
        ),
    )

    mixed_ambiguous = ProjectAmbiguousResolution(
        query=query,
        candidates=(index.candidates[0], foreign_candidate),
    )
    _expect(
        ValueError,
        lambda: trace_map_from_resolution_observation(
            index,
            query,
            context,
            mixed_ambiguous,
        ),
    )


def _assert_frozen_owners_unchanged() -> None:
    paths = (
        "apexforge/tam/model.py",
        "apexforge/language/source.py",
        "apexforge/language/compiler.py",
        "apexforge/language/declarations.py",
        "apexforge/language/identities.py",
        "apexforge/language/project.py",
        "apexforge/language/resolution_candidates.py",
        "apexforge/language/resolution_context.py",
        "apexforge/language/resolution_queries.py",
        "apexforge/language/resolution_outcomes.py",
        "apexforge/language/resolution_visibility.py",
        "apexforge/tooling/cli.py",
        "apexforge/tooling/project_loader.py",
        "apexforge/language_server/diagnostics.py",
        "apexforge/language/semantic_decision_analysis.py",
        "apexforge/language/semantic_decision_project_analysis.py",
        "apexforge/language/narrative_analysis.py",
        "apexforge/semantic_lattice/adapters.py",
    )
    diff = _git("diff", "--exit-code", PREDECESSOR_TAG, "--", *paths)
    _require(diff.returncode == 0, "TAM-E mutated frozen semantic owner")


def main() -> None:
    _assert_predecessor()
    _assert_query_and_scope_projection()
    _assert_candidate_projection()
    _assert_outcome_projection()
    _assert_aggregate_projection()
    _assert_no_resolution_execution()
    _assert_type_and_coherence_guards()
    _assert_frozen_owners_unchanged()

    print("P11_TAM_D_FREEZE_ANCESTRY=PASS")
    print("RESOLUTION_QUERY_CONSUMPTION=PASS")
    print("RESOLUTION_CONTEXT_CONSUMPTION=PASS")
    print("RESOLUTION_CANDIDATE_CONSUMPTION=PASS")
    print("RESOLVED_OUTCOME_CONSUMPTION=PASS")
    print("UNRESOLVED_OUTCOME_CONSUMPTION=PASS")
    print("AMBIGUOUS_OUTCOME_CONSUMPTION=PASS")
    print("QUERY_DOMAIN=REFERENCE")
    print("CONTEXT_DOMAIN=SCOPE")
    print("CANDIDATE_DOMAIN=REFERENCE")
    print("OUTCOME_DOMAIN=REFERENCE")
    print("CANDIDATE_AIR_ID=REFERENCE_ONLY")
    print("CANDIDATE_SOURCE_SPAN=EXACT_REFERENCE")
    print("RESOLVED_AIR_ID=REFERENCE_ONLY")
    print("UNRESOLVED_CANONICAL_IDENTITY=NONE")
    print("AMBIGUOUS_CANONICAL_IDENTITY=NONE")
    print("CANDIDATE_INDEX_ORDER=PRESERVED")
    print("OUTCOME_CANDIDATE_INDEX_COHERENCE=PASS")
    print("SAME_INPUT_SAME_TRACE_ID=PASS")
    print("SAME_INPUT_SAME_TRACE_MAP=PASS")
    print("GRAPH_LINK_INFERENCE=NONE")
    print("RESOLUTION_EXECUTION=NONE")
    print("VISIBILITY_EVALUATION=NONE")
    print("CANDIDATE_SELECTION=NONE")
    print("SCOPE_INFERENCE=NONE")
    print("COMPILER_MUTATION=NONE")
    print("PROJECTBUILDER_MUTATION=NONE")
    print("CLI_LSP_INTEGRATION=NONE")
    print("SEMANTIC_EXECUTION=NONE")
    print("P11_TAM_E_REFERENCE_SCOPE_RESOLUTION_EVIDENCE_TRACE_PRODUCTION=PASS")


if __name__ == "__main__":
    main()