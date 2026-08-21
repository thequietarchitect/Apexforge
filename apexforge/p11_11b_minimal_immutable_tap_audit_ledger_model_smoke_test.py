"""P11.11B minimal immutable TAP Check audit-ledger model coverage."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, is_dataclass
import inspect
from pathlib import Path
import subprocess

from tam import TraceIdentity
from tap_check import (
    TAP_CHECK_CATEGORY_IDS,
    TapCheckAuditLedger,
    TapCheckLedgerEntry,
)


PREDECESSOR_TAG = "afp-p11-11a-freeze"
PREDECESSOR_COMMIT = "e8d541a61cce3c27f3b1154b21e684453c5612ce"

A_HASHES = {
    "apexforge/p11_11a_tap_check_architecture_ownership_audit_smoke_test.py":
        "48C71D9E41131098F75BD67204CFF633C1DFB2D5B765912A1617258B58FCA7B7",
    "docs/p11/P11_11A_TAP_CHECK_ARCHITECTURE_OWNERSHIP_AUDIT.md":
        "9D8CFC9588E59EA4AA34564D5E0B01069E5ACE5554895BFE30789E1608AA8E9D",
}

EXPECTED_CATEGORIES = (
    "active-directives",
    "compiler-transformations",
    "semantic-changes",
    "authority-intervention",
    "optimization-decisions",
    "continuity-effects",
    "narrative-state-changes",
    "convergence-rulings",
    "air-lowering",
    "runtime-results",
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


def _expect_error(error_type, thunk, phrase: str) -> None:
    try:
        thunk()
    except error_type as error:
        _require(phrase in str(error), "diagnostic changed: {!r}".format(error))
    else:
        raise AssertionError("{} was not raised".format(error_type.__name__))


def _assert_predecessor() -> None:
    resolved = _git("rev-parse", "{}^{{}}".format(PREDECESSOR_TAG))
    _require(resolved.returncode == 0, resolved.stderr.strip())
    _require(
        resolved.stdout.strip() == PREDECESSOR_COMMIT,
        "P11.11A freeze target changed",
    )
    ancestry = _git("merge-base", "--is-ancestor", PREDECESSOR_TAG, "HEAD")
    _require(
        ancestry.returncode == 0,
        "P11.11A freeze is not an ancestor of P11.11B",
    )
    for relative, expected in A_HASHES.items():
        _require(
            _sha256(_root() / relative) == expected,
            "{} frozen hash changed".format(relative),
        )


def _assert_public_surface() -> None:
    import tap_check

    _require(
        tap_check.__all__
        == (
            "TAP_CHECK_CATEGORY_IDS",
            "TapCheckLedgerEntry",
            "TapCheckAuditLedger",
        ),
        "tap_check public surface changed",
    )
    _require(TAP_CHECK_CATEGORY_IDS == EXPECTED_CATEGORIES, "category order changed")
    _require(len(TAP_CHECK_CATEGORY_IDS) == 10, "category count changed")
    _require(len(set(TAP_CHECK_CATEGORY_IDS)) == 10, "category ids are not unique")

    _require(is_dataclass(TapCheckLedgerEntry), "entry stopped being a dataclass")
    _require(
        TapCheckLedgerEntry.__dataclass_params__.frozen,
        "entry stopped being frozen",
    )
    _require(is_dataclass(TapCheckAuditLedger), "ledger stopped being a dataclass")
    _require(
        TapCheckAuditLedger.__dataclass_params__.frozen,
        "ledger stopped being frozen",
    )

    _require(
        tuple(field.name for field in fields(TapCheckLedgerEntry))
        == ("category_id", "subject", "evidence", "trace_ids"),
        "entry field contract changed",
    )
    _require(
        tuple(field.name for field in fields(TapCheckAuditLedger))
        == ("entries",),
        "ledger field contract changed",
    )

    _require(
        str(inspect.signature(TapCheckLedgerEntry))
        == "(category_id: 'str', subject: 'str', evidence: 'Tuple[str, ...]' = (), "
        "trace_ids: 'Tuple[TraceIdentity, ...]' = ()) -> None",
        "entry constructor signature changed",
    )
    _require(
        str(inspect.signature(TapCheckAuditLedger))
        == "(entries: 'Tuple[TapCheckLedgerEntry, ...]' = ()) -> None",
        "ledger constructor signature changed",
    )


def _assert_entry_contract() -> None:
    first_id = TraceIdentity("tam:tap:first")
    second_id = TraceIdentity("tam:tap:second")

    entry = TapCheckLedgerEntry(
        category_id="compiler-transformations",
        subject="directive:Alpha",
        evidence=("lowered-to-air", "source-map-preserved"),
        trace_ids=(first_id, second_id),
    )
    _require(entry.category_id == "compiler-transformations", "category changed")
    _require(entry.subject == "directive:Alpha", "subject changed")
    _require(
        entry.evidence == ("lowered-to-air", "source-map-preserved"),
        "evidence order changed",
    )
    _require(entry.trace_ids == (first_id, second_id), "trace-id order changed")
    _require(entry.trace_ids[0] is first_id, "trace-id reference was replaced")
    _require(entry.trace_ids[1] is second_id, "trace-id reference was replaced")

    duplicate = TapCheckLedgerEntry(
        category_id="compiler-transformations",
        subject="directive:Alpha",
        evidence=("same", "same"),
        trace_ids=(first_id, first_id),
    )
    _require(
        duplicate.evidence == ("same", "same"),
        "entry deduplicated supplied evidence",
    )
    _require(
        duplicate.trace_ids == (first_id, first_id),
        "entry deduplicated supplied trace ids",
    )

    _expect_error(
        ValueError,
        lambda: TapCheckLedgerEntry("unknown", "subject"),
        "canonical TAP Check category id",
    )
    _expect_error(
        ValueError,
        lambda: TapCheckLedgerEntry("runtime-results", ""),
        "non-empty string",
    )
    _expect_error(
        TypeError,
        lambda: TapCheckLedgerEntry(
            "runtime-results",
            "subject",
            evidence=["result"],
        ),
        "exact tuple",
    )
    _expect_error(
        ValueError,
        lambda: TapCheckLedgerEntry(
            "runtime-results",
            "subject",
            evidence=("",),
        ),
        "non-empty string",
    )
    _expect_error(
        TypeError,
        lambda: TapCheckLedgerEntry(
            "runtime-results",
            "subject",
            trace_ids=[first_id],
        ),
        "exact tuple",
    )
    _expect_error(
        TypeError,
        lambda: TapCheckLedgerEntry(
            "runtime-results",
            "subject",
            trace_ids=("not-a-trace-id",),
        ),
        "exact TraceIdentity",
    )

    try:
        entry.subject = "mutated"
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError("TapCheckLedgerEntry is mutable")


def _assert_ledger_contract() -> None:
    trace_id = TraceIdentity("tam:tap:ledger")
    first = TapCheckLedgerEntry(
        "active-directives",
        "directive:Alpha",
        evidence=("activation-observed",),
        trace_ids=(trace_id,),
    )
    second = TapCheckLedgerEntry(
        "runtime-results",
        "workflow:Main",
        evidence=("exit:0",),
    )

    empty = TapCheckAuditLedger()
    _require(empty.entries == (), "empty ledger fabricated entries")

    ledger = TapCheckAuditLedger((first, second))
    _require(ledger.entries == (first, second), "ledger entry order changed")
    _require(ledger.entries[0] is first, "ledger replaced first entry")
    _require(ledger.entries[1] is second, "ledger replaced second entry")
    _require(
        TapCheckAuditLedger((first, second)) == ledger,
        "same input did not produce equal immutable ledger",
    )

    runtime_only = TapCheckAuditLedger((second,))
    _require(
        runtime_only.entries == (second,),
        "partial category coverage was not preserved",
    )
    _require(
        all(entry.category_id != "authority-intervention" for entry in runtime_only.entries),
        "missing category was fabricated as a negative result",
    )

    _expect_error(
        TypeError,
        lambda: TapCheckAuditLedger([first]),
        "exact tuple",
    )
    _expect_error(
        TypeError,
        lambda: TapCheckAuditLedger(("not-an-entry",)),
        "exact TapCheckLedgerEntry",
    )

    try:
        ledger.entries = ()
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError("TapCheckAuditLedger is mutable")


def _assert_model_is_passive() -> None:
    model = (_root() / "apexforge/tap_check/model.py").read_text(encoding="utf-8")
    forbidden = (
        "audit_trace_map",
        "route_conflict_evidence",
        "AuthorityRegistry",
        "RuntimeEngine",
        "evaluate_advanced_condition",
        "apply_semantic_convergence_policy",
        "assess_paradox_elevation",
        "compile(",
        "parse(",
        "resolve(",
        "execute(",
        "subprocess",
        "Path(",
        "open(",
        "sorted(",
        ".sort(",
    )
    for token in forbidden:
        _require(token not in model, "model acquired forbidden behavior: " + token)

    _require(
        "from tam.model import TraceIdentity" in model,
        "model stopped linking through canonical TAM TraceIdentity",
    )


def _assert_predecessor_owners_unchanged() -> None:
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
    _require(diff.returncode == 0, "P11.11B mutated predecessor owners")


def main() -> None:
    _assert_predecessor()
    _assert_public_surface()
    _assert_entry_contract()
    _assert_ledger_contract()
    _assert_model_is_passive()
    _assert_predecessor_owners_unchanged()

    print("P11_11A_FREEZE_ANCESTRY=PASS")
    print("TAP_OWNER=tap_check")
    print("CATEGORY_TAXONOMY=TAP_CHECK_CATEGORY_IDS")
    print("CATEGORY_COUNT=10")
    print("CATEGORY_ORDER=ROADMAP_ORDER")
    print("ENTRY_MODEL=TapCheckLedgerEntry")
    print("LEDGER_MODEL=TapCheckAuditLedger")
    print("MODELS=FROZEN_DATACLASSES")
    print("CONTAINERS=EXACT_TUPLES")
    print("ENTRY_ORDER=PRESERVED")
    print("EVIDENCE_ORDER=PRESERVED")
    print("TRACE_ID_ORDER=PRESERVED")
    print("TRACE_ID_REFERENCE_PRESERVATION=PASS")
    print("SORTING=NONE")
    print("DEDUPLICATION=NONE")
    print("EMPTY_LEDGER=VALID")
    print("PARTIAL_CATEGORY_COVERAGE=VALID")
    print("MISSING_CATEGORY=ABSENT_NOT_NEGATIVE_RESULT")
    print("TRACE_LINK_TYPE=EXACT_TraceIdentity")
    print("TRACE_IDENTITY_FABRICATION=NONE")
    print("TRACE_MAP_PROJECTION=NONE_DEFERRED_TO_P11_11C")
    print("AUTHORITY_DECISION=NONE")
    print("SEMANTIC_DECISION=NONE")
    print("DIRECTIVE_ACTIVATION=NONE")
    print("RUNTIME_EXECUTION=NONE")
    print("PREDECESSOR_OWNER_MUTATION=NONE")
    print("P11_11B_MINIMAL_IMMUTABLE_TAP_AUDIT_LEDGER_MODEL=PASS")


if __name__ == "__main__":
    main()