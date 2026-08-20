"""P11-TAM-K deterministic whole-map composition."""

from __future__ import annotations

from pathlib import Path
import subprocess

from authority.model import Principal
from language.compiler import SourceMap, SourceMapEntry
from language.declarations import (
    ProjectDeclarationOwner,
    ProjectDeclarationOwnership,
)
from language.identities import ProjectDeclaredIdentity, ProjectIdentityIndex
from language.lexer import Token
from language.narrative_model import NarrativeIdentity
from language.resolution_candidates import (
    ProjectQualification,
    ProjectResolutionCandidate,
    ProjectResolutionCandidateIndex,
)
from language.resolution_context import ProjectResolutionContext
from language.resolution_queries import (
    ProjectResolutionQuery,
    ProjectResolvedBinding,
)
from language.source import SourcePosition, SourceSpan
from tam import (
    TRACE_DOMAIN_IDS,
    TraceMap,
    compose_trace_maps,
    trace_map_from_authority_evidence,
    trace_map_from_declaration_identity_indexes,
    trace_map_from_narrative_evidence,
    trace_map_from_resolution_observation,
    trace_map_from_source_map,
    trace_map_from_token_evidence,
    trace_map_from_type_evidence,
)
from type_system.model import ApexType


PREDECESSOR_TAG = "afp-p11-tam-j-freeze"
PREDECESSOR_COMMIT = "661926bd8d42e7e93f05f4d2178216ae8a91c5b6"

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


def _assert_predecessor() -> None:
    resolved = _git("rev-parse", "{}^{{}}".format(PREDECESSOR_TAG))
    _require(resolved.returncode == 0, resolved.stderr.strip())
    _require(
        resolved.stdout.strip() == PREDECESSOR_COMMIT,
        "TAM-J freeze target changed",
    )
    ancestry = _git("merge-base", "--is-ancestor", PREDECESSOR_TAG, "HEAD")
    _require(
        ancestry.returncode == 0,
        "TAM-J is not an ancestor of TAM-K",
    )


def _real_maps():
    start = SourcePosition(1, 1, 0)
    end = SourcePosition(1, 6, 5)
    span = SourceSpan("TamK.apex", start, end)

    source_map = trace_map_from_source_map(
        SourceMap(
            (
                SourceMapEntry(
                    air_id="directive:Alpha",
                    span=span,
                    kind="directive",
                    reference="Alpha",
                ),
            )
        )
    )

    owner = ProjectDeclarationOwner(
        kind="directive",
        air_id="directive:Alpha",
        source_name="TamK.apex",
        module_name="demo",
        span=span,
    )
    identity = ProjectDeclaredIdentity(
        kind="directive",
        declared_name="Alpha",
        current_air_id="directive:Alpha",
        source_name="TamK.apex",
        module_name="demo",
        qualified_display_name="demo.Alpha",
        span=span,
    )
    declaration_map = trace_map_from_declaration_identity_indexes(
        ProjectDeclarationOwnership((owner,)),
        ProjectIdentityIndex((identity,)),
    )

    qualification = ProjectQualification(
        kind="directive",
        module_segments=("demo",),
        declaration_path=("Alpha",),
        legacy=False,
    )
    candidate = ProjectResolutionCandidate(
        identity=identity,
        owner=owner,
        qualification=qualification,
    )
    candidate_index = ProjectResolutionCandidateIndex((candidate,))
    query = ProjectResolutionQuery(
        kind="directive",
        declaration_path=("Alpha",),
        module_segments=("demo",),
    )
    context = ProjectResolutionContext(
        source_name="TamK.apex",
        module_segments=("demo",),
    )
    outcome = ProjectResolvedBinding(
        query=query,
        candidate=candidate,
    )
    resolution_map = trace_map_from_resolution_observation(
        candidate_index,
        query,
        context,
        outcome,
    )

    type_map = trace_map_from_type_evidence((ApexType("TamKType"),))
    authority_map = trace_map_from_authority_evidence(
        (Principal("tam-k-principal"),)
    )
    narrative_map = trace_map_from_narrative_evidence(
        (NarrativeIdentity("story", ("TamKStory",)),)
    )
    token_map = trace_map_from_token_evidence(
        (Token("IDENT", "Alpha", span),)
    )

    maps = (
        source_map,
        declaration_map,
        resolution_map,
        type_map,
        authority_map,
        narrative_map,
        token_map,
    )
    _require(
        all(type(trace_map) is TraceMap for trace_map in maps),
        "real predecessor producer did not return exact TraceMap",
    )
    return maps


def _flatten(trace_maps):
    return tuple(
        record
        for trace_map in trace_maps
        for record in trace_map.records
    )


def _assert_real_ten_domain_composition() -> None:
    trace_maps = _real_maps()
    expected_records = _flatten(trace_maps)
    first = compose_trace_maps(trace_maps)
    second = compose_trace_maps(trace_maps)

    _require(type(first) is TraceMap, "composition did not return TraceMap")
    _require(first == second, "same map tuple produced different TraceMap")
    _require(
        first.records == expected_records,
        "composition changed caller map-block or record order",
    )
    _require(
        all(
            actual is expected
            for actual, expected in zip(first.records, expected_records)
        ),
        "composition rewrote one or more TraceRecord objects",
    )

    observed = frozenset(
        record.domain.canonical_id
        for record in first.records
    )
    _require(
        observed == frozenset(EXPECTED_DOMAINS),
        "real predecessor evidence did not coexist across all ten domains",
    )
    _require(
        TRACE_DOMAIN_IDS == EXPECTED_DOMAINS,
        "canonical TAM domain taxonomy changed",
    )


def _assert_order_is_caller_owned() -> None:
    trace_maps = _real_maps()
    left = compose_trace_maps((trace_maps[3], trace_maps[0]))
    right = compose_trace_maps((trace_maps[0], trace_maps[3]))

    _require(
        left.records
        == trace_maps[3].records + trace_maps[0].records,
        "caller map order was not preserved",
    )
    _require(
        right.records
        == trace_maps[0].records + trace_maps[3].records,
        "reversed caller map order was not preserved",
    )
    _require(
        left.records != right.records,
        "composition sorted records independently of caller order",
    )


def _assert_empty_single_and_partial() -> None:
    trace_maps = _real_maps()

    _require(
        compose_trace_maps(()) == TraceMap(),
        "empty composition fabricated evidence",
    )

    single = compose_trace_maps((trace_maps[3],))
    _require(
        single.records == trace_maps[3].records,
        "single-map composition changed record content",
    )
    _require(
        all(
            actual is expected
            for actual, expected in zip(
                single.records,
                trace_maps[3].records,
            )
        ),
        "single-map composition rewrote records",
    )

    partial = compose_trace_maps((trace_maps[3], trace_maps[4]))
    domains = tuple(
        record.domain.canonical_id
        for record in partial.records
    )
    _require(
        set(domains) == {"type", "authority"},
        "partial composition fabricated absent domains",
    )


def _assert_duplicate_identity_rejected() -> None:
    trace_map = _real_maps()[3]
    error = _expect(
        ValueError,
        lambda: compose_trace_maps((trace_map, trace_map)),
    )
    _require(
        str(error)
        == "TraceMap.records cannot contain duplicate trace identities",
        "composition did not preserve frozen TraceMap duplicate-ID invariant",
    )


def _assert_type_guards() -> None:
    trace_map = _real_maps()[3]

    _expect(
        TypeError,
        lambda: compose_trace_maps([trace_map]),
    )
    _expect(
        TypeError,
        lambda: compose_trace_maps((object(),)),
    )


def _assert_integration_is_thin() -> None:
    path = _root() / "apexforge/tam/integration.py"
    text = path.read_text(encoding="utf-8")

    _require(
        "from tam.model import TraceMap" in text,
        "integration stopped using the frozen TraceMap model",
    )

    forbidden = (
        "from tam.production",
        "trace_map_from_",
        "trace_record_from_",
        "TraceRecord(",
        "TraceIdentity(",
        "TraceDomain(",
        "sorted(",
        ".sort(",
        "lex(",
        "parse(",
        "compile(",
        "resolve(",
        "validate(",
        "infer_",
        "AuthorityEngine",
        "NarrativeSemanticGraph",
        "SemanticLattice",
        "runtime.",
        "language_server.",
        "tooling.",
    )
    for token in forbidden:
        _require(
            token not in text,
            "TAM-K integration acquired forbidden behavior: " + token,
        )


def _assert_frozen_owners_unchanged() -> None:
    paths = (
        "apexforge/tam/model.py",
        "apexforge/tam/production.py",
        "apexforge/language",
        "apexforge/air",
        "apexforge/authority",
        "apexforge/runtime",
        "apexforge/tooling",
        "apexforge/language_server",
        "apexforge/semantic_lattice",
        "apexforge/aether_air",
        "apexforge/type_system",
    )
    diff = _git(
        "diff",
        "--exit-code",
        PREDECESSOR_TAG,
        "--",
        *paths
    )
    _require(
        diff.returncode == 0,
        "TAM-K mutated frozen model/production/evidence owners",
    )


def main() -> None:
    _assert_predecessor()
    _assert_real_ten_domain_composition()
    _assert_order_is_caller_owned()
    _assert_empty_single_and_partial()
    _assert_duplicate_identity_rejected()
    _assert_type_guards()
    _assert_integration_is_thin()
    _assert_frozen_owners_unchanged()

    print("P11_TAM_J_FREEZE_ANCESTRY=PASS")
    print("CANONICAL_INTEGRATION_OWNER=tam.integration")
    print("CANONICAL_INTEGRATION_API=compose_trace_maps")
    print("COMPOSITION_INPUT=EXACT_TUPLE_OF_TRACE_MAPS")
    print("REAL_PREDECESSOR_MAP_PRODUCERS=7_OF_7")
    print("TRACE_DOMAIN_PRODUCTION_COVERAGE=10_OF_10")
    print("TEN_DOMAIN_COEXISTENCE=PASS")
    print("COMPOSITION_ORDER=CALLER_MAP_ORDER_THEN_RECORD_ORDER")
    print("TRACE_RECORD_REFERENCE_PRESERVATION=PASS")
    print("TRACE_RECORD_REWRITE=NONE")
    print("TRACE_IDENTITY_REWRITE=NONE")
    print("SORTING=NONE")
    print("DEDUPLICATION=NONE")
    print("DUPLICATE_TRACE_IDENTITY=REJECT_VIA_FROZEN_TRACE_MAP")
    print("EMPTY_INPUT=EMPTY_TRACE_MAP")
    print("SINGLE_MAP_COMPOSITION=PASS")
    print("PARTIAL_DOMAIN_COVERAGE=VALID")
    print("ABSENT_DOMAIN_FABRICATION=NONE")
    print("PRODUCER_EXECUTION_INSIDE_INTEGRATION=NONE")
    print("GRAPH_LINK_INFERENCE=NONE")
    print("SEMANTIC_LATTICE_PROJECTION=NONE")
    print("LEXING_PARSING_COMPILATION_RESOLUTION_VALIDATION_EXECUTION=NONE")
    print("TAP_CHECK_CONSUMER_BOUNDARY=CANONICAL_TRACE_MAP_EVIDENCE")
    print("P11_TAM_K_DETERMINISTIC_WHOLE_MAP_COMPOSITION=PASS")


if __name__ == "__main__":
    main()