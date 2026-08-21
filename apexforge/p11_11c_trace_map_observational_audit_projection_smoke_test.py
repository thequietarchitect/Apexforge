"""P11.11C deterministic TraceMap observational audit projection coverage."""

from __future__ import annotations

import inspect
from pathlib import Path
import subprocess

from tam import TraceDomain, TraceIdentity, TraceMap, TraceRecord
from tap_check import (
    TapCheckAuditLedger,
    audit_trace_map,
)


PREDECESSOR_TAG = "afp-p11-11b-freeze"
PREDECESSOR_COMMIT = "295613496b2c5f8d9123fd90cd55f501c6ec76ec"

B_FROZEN_HASHES = {
    "apexforge/p11_11b_minimal_immutable_tap_audit_ledger_model_smoke_test.py":
        "C06658BFA2E09AC8242DA106C610C4CA0C9A58E17C8998EBF53CF2F9DB5540C3",
    "apexforge/tap_check/model.py":
        "C1E6F650977A73A7E3F3655A948416129AAB0AFDDB69DA561582F771C16B8769",
    "docs/p11/P11_11B_MINIMAL_IMMUTABLE_TAP_AUDIT_LEDGER_MODEL.md":
        "324824868B42ABAD5C5C9871998F214DB5048128052D3A5276E11726E6471B8F",
}

EXPECTED_PUBLIC_SURFACE = (
    "TAP_CHECK_CATEGORY_IDS",
    "TapCheckLedgerEntry",
    "TapCheckAuditLedger",
    "audit_trace_map",
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


def _sha256(path: Path) -> str:
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _record(
    trace_id: str,
    domain: str,
    producer: str,
    owner: str,
    representation: str,
    *,
    canonical_identity=None,
) -> TraceRecord:
    return TraceRecord(
        trace_id=TraceIdentity(trace_id),
        domain=TraceDomain(domain),
        producer=producer,
        owner=owner,
        representation=representation,
        canonical_identity=canonical_identity,
    )


def _assert_predecessor() -> None:
    resolved = _git("rev-parse", "{}^{{}}".format(PREDECESSOR_TAG))
    _require(resolved.returncode == 0, resolved.stderr.strip())
    _require(
        resolved.stdout.strip() == PREDECESSOR_COMMIT,
        "P11.11B freeze target changed",
    )
    ancestry = _git("merge-base", "--is-ancestor", PREDECESSOR_TAG, "HEAD")
    _require(
        ancestry.returncode == 0,
        "P11.11B freeze is not an ancestor of P11.11C",
    )
    for relative, expected in B_FROZEN_HASHES.items():
        _require(
            _sha256(_root() / relative) == expected,
            "{} frozen B artifact changed".format(relative),
        )


def _assert_public_surface() -> None:
    import tap_check

    _require(
        tap_check.__all__ == EXPECTED_PUBLIC_SURFACE,
        "tap_check public surface changed",
    )
    _require(
        str(inspect.signature(audit_trace_map))
        == "(trace_map: 'TraceMap') -> 'TapCheckAuditLedger'",
        "audit_trace_map signature changed",
    )


def _assert_direct_mapping_and_order() -> None:
    source = _record(
        "trace:source",
        "source",
        "language.source",
        "language.source",
        "source-span",
    )
    transformation = _record(
        "trace:transform",
        "transformation",
        "language.compiler",
        "language.compiler",
        "source-map-entry",
        canonical_identity="air:Main",
    )
    principal = _record(
        "trace:principal",
        "authority",
        "authority.model",
        "authority.model",
        "principal",
        canonical_identity="principal:Operator",
    )
    authority_check = _record(
        "trace:authority-check",
        "authority",
        "authority.model",
        "authority.model",
        "authority-check",
        canonical_identity="authority:check:Main",
    )
    narrative = _record(
        "trace:narrative",
        "narrative",
        "narrative.model",
        "narrative.model",
        "narrative-state-fact",
    )
    authority_grant = _record(
        "trace:authority-grant",
        "authority",
        "authority.model",
        "authority.model",
        "authority-grant",
    )
    resolution = _record(
        "trace:resolution",
        "reference",
        "language.resolution_queries",
        "language.resolution_queries",
        "project-resolved-binding",
        canonical_identity="air:Child",
    )

    trace_map = TraceMap(
        (
            source,
            transformation,
            principal,
            authority_check,
            narrative,
            authority_grant,
            resolution,
        )
    )
    first = audit_trace_map(trace_map)
    second = audit_trace_map(trace_map)

    _require(type(first) is TapCheckAuditLedger, "projection returned wrong type")
    _require(first == second, "same TraceMap did not yield equal ledger")
    _require(
        tuple(entry.category_id for entry in first.entries)
        == (
            "compiler-transformations",
            "authority-intervention",
            "authority-intervention",
        ),
        "direct mapping or TraceMap order changed",
    )
    _require(
        tuple(entry.subject for entry in first.entries)
        == (
            "air:Main",
            "authority:check:Main",
            "trace:authority-grant",
        ),
        "passive subject derivation changed",
    )
    _require(
        tuple(entry.trace_ids[0] for entry in first.entries)
        == (
            transformation.trace_id,
            authority_check.trace_id,
            authority_grant.trace_id,
        ),
        "trace links changed",
    )
    _require(
        first.entries[0].trace_ids[0] is transformation.trace_id,
        "transformation TraceIdentity reference was replaced",
    )
    _require(
        first.entries[1].trace_ids[0] is authority_check.trace_id,
        "authority-check TraceIdentity reference was replaced",
    )
    _require(
        first.entries[2].trace_ids[0] is authority_grant.trace_id,
        "authority-grant TraceIdentity reference was replaced",
    )

    _require(
        first.entries[0].evidence
        == (
            "domain=transformation",
            "producer=language.compiler",
            "owner=language.compiler",
            "representation=source-map-entry",
            "schema_version=1",
            "canonical_identity=air:Main",
        ),
        "transformation evidence serialization changed",
    )
    _require(
        first.entries[2].evidence
        == (
            "domain=authority",
            "producer=authority.model",
            "owner=authority.model",
            "representation=authority-grant",
            "schema_version=1",
        ),
        "authority-grant evidence serialization changed",
    )

    unmapped_ids = {
        source.trace_id,
        principal.trace_id,
        narrative.trace_id,
        resolution.trace_id,
    }
    emitted_ids = {
        entry.trace_ids[0]
        for entry in first.entries
    }
    _require(
        unmapped_ids.isdisjoint(emitted_ids),
        "unmapped evidence was forced into a TAP category",
    )


def _assert_conservative_signature_mapping() -> None:
    same_rep_wrong_domain = _record(
        "trace:wrong-domain",
        "source",
        "language.compiler",
        "language.compiler",
        "source-map-entry",
    )
    same_rep_wrong_owner = _record(
        "trace:wrong-owner",
        "transformation",
        "language.compiler",
        "other.owner",
        "source-map-entry",
    )
    same_domain_unknown_rep = _record(
        "trace:unknown-transform",
        "transformation",
        "language.compiler",
        "language.compiler",
        "future-transform",
    )
    authority_principal = _record(
        "trace:principal-only",
        "authority",
        "authority.model",
        "authority.model",
        "principal",
    )
    future_authority = _record(
        "trace:future-authority",
        "authority",
        "authority.model",
        "authority.model",
        "authority-decision",
    )

    result = audit_trace_map(
        TraceMap(
            (
                same_rep_wrong_domain,
                same_rep_wrong_owner,
                same_domain_unknown_rep,
                authority_principal,
                future_authority,
            )
        )
    )
    _require(
        result.entries == (),
        "signature mapping inferred semantics from partial matches",
    )


def _assert_missing_evidence_and_empty_input() -> None:
    empty = audit_trace_map(TraceMap())
    _require(empty.entries == (), "empty TraceMap fabricated ledger entries")

    token_only = audit_trace_map(
        TraceMap(
            (
                _record(
                    "trace:token",
                    "token",
                    "language.lexer",
                    "language.lexer",
                    "token",
                ),
            )
        )
    )
    _require(
        token_only.entries == (),
        "unmapped TraceMap fabricated negative category results",
    )

    try:
        audit_trace_map(())
    except TypeError as error:
        _require(
            "exact TraceMap" in str(error),
            "audit_trace_map type diagnostic changed",
        )
    else:
        raise AssertionError("audit_trace_map accepted a non-TraceMap")


def _assert_projection_is_passive() -> None:
    text = (
        _root() / "apexforge/tap_check/projection.py"
    ).read_text(encoding="utf-8")

    required = (
        "from tam.model import TraceMap, TraceRecord",
        '"source-map-entry"',
        '"authority-check"',
        '"authority-grant"',
    )
    for token in required:
        _require(token in text, "projection contract missing " + token)

    forbidden = (
        "tam.production",
        "trace_map_from_",
        "compose_trace_maps",
        "route_conflict_evidence",
        "AuthorityRegistry",
        "RuntimeEngine",
        "evaluate_advanced_condition",
        "apply_semantic_convergence_policy",
        "assess_paradox_elevation",
        "sorted(",
        ".sort(",
        "compile(",
        "parse(",
        "resolve(",
        "execute(",
        "subprocess",
        "Path(",
        "open(",
    )
    for token in forbidden:
        _require(token not in text, "projection acquired forbidden behavior: " + token)


def _assert_owner_boundaries() -> None:
    paths = (
        "apexforge/tam",
        "apexforge/governance",
        "apexforge/language",
        "apexforge/air",
        "apexforge/authority",
        "apexforge/runtime",
        "apexforge/tooling",
        "apexforge/language_server",
        "apexforge/semantic_lattice",
        "apexforge/semantic_decision",
        "apexforge/aether_air",
        "apexforge/type_system",
    )
    diff = _git("diff", "--exit-code", PREDECESSOR_TAG, "--", *paths)
    _require(diff.returncode == 0, "P11.11C mutated predecessor owners")


def main() -> None:
    _assert_predecessor()
    _assert_public_surface()
    _assert_direct_mapping_and_order()
    _assert_conservative_signature_mapping()
    _assert_missing_evidence_and_empty_input()
    _assert_projection_is_passive()
    _assert_owner_boundaries()

    print("P11_11B_FREEZE_ANCESTRY=PASS")
    print("TAP_CORE_TRACE_API=audit_trace_map")
    print("INPUT=EXACT_TraceMap")
    print("OUTPUT=TapCheckAuditLedger")
    print("DIRECT_MAPPING_SIGNATURES=3")
    print("DIRECT_MAPPING_CATEGORIES=2")
    print("SOURCE_MAP_ENTRY=compiler-transformations")
    print("AUTHORITY_CHECK=authority-intervention")
    print("AUTHORITY_GRANT=authority-intervention")
    print("AUTHORITY_PRINCIPAL=UNMAPPED")
    print("GENERIC_NARRATIVE_EVIDENCE=UNMAPPED")
    print("REFERENCE_RESOLUTION_EVIDENCE=UNMAPPED")
    print("TYPE_EVIDENCE=UNMAPPED")
    print("TOKEN_EVIDENCE=UNMAPPED")
    print("AIR_LOWERING=DEFERRED_NO_EXPLICIT_TAM_REPRESENTATION")
    print("NARRATIVE_STATE_CHANGE=DEFERRED_NO_PROVEN_EXPLICIT_MAPPING")
    print("UNMAPPED_RECORD_POLICY=OMIT")
    print("ONE_MAPPED_RECORD=ONE_LEDGER_ENTRY")
    print("TRACE_MAP_ORDER=PRESERVED_AMONG_MAPPED_RECORDS")
    print("TRACE_ID_REFERENCE_PRESERVATION=PASS")
    print("SUBJECT=CANONICAL_IDENTITY_ELSE_TRACE_ID")
    print("EVIDENCE=EXPLICIT_TRACE_RECORD_FIELDS_ONLY")
    print("SORTING=NONE")
    print("DEDUPLICATION=NONE")
    print("TRACE_PRODUCER_EXECUTION=NONE")
    print("TRACE_MAP_COMPOSITION=NONE")
    print("SEMANTIC_INFERENCE=NONE")
    print("MISSING_EVIDENCE=ABSENT_NOT_NEGATIVE_RESULT")
    print("AUTHORITY_DECISION=NONE")
    print("DIRECTIVE_ACTIVATION=NONE")
    print("RUNTIME_EXECUTION=NONE")
    print("PREDECESSOR_OWNER_MUTATION=NONE")
    print("P11_11C_TRACE_MAP_OBSERVATIONAL_AUDIT_PROJECTION=PASS")


if __name__ == "__main__":
    main()