"""P11.11E deterministic whole-ledger aggregation and coverage."""

from __future__ import annotations

import inspect
from pathlib import Path
import subprocess

from tap_check import (
    TAP_CHECK_CATEGORY_IDS,
    TapCheckAuditLedger,
    TapCheckLedgerEntry,
    compose_tap_check_ledgers,
    tap_check_category_coverage,
)


PREDECESSOR_TAG = "afp-p11-11d-freeze"
PREDECESSOR_COMMIT = "f8a3b6ddc2115ffa8f02033c4a45cf5b722bcc44"

FROZEN_OWNER_HASHES = {
    "apexforge/tap_check/model.py":
        "C1E6F650977A73A7E3F3655A948416129AAB0AFDDB69DA561582F771C16B8769",
    "apexforge/tap_check/projection.py":
        "C43F222DC98704A3C3803F475359F97B72FCB0BEAB6F829188493CF591B117A2",
    "apexforge/tap_check/adapters.py":
        "8895FBF8D79EC70BE09E0F73E31B42829A3C6BB326F5B0326B54E9793C0C7CBA",
    "apexforge/p11_11d_read_only_owner_evidence_adapters_smoke_test.py":
        "76DD972536B65974E9E4A461885AE0E25753DE8E9342662F70ED2A72B80FD88F",
    "docs/p11/P11_11D_READ_ONLY_OWNER_EVIDENCE_ADAPTERS.md":
        "44E13A0A93626AFDAC6583F74C14728B622C1007CBB1A83CC82A3B3FFB98149D",
}

EXPECTED_PUBLIC_SURFACE = (
    "TAP_CHECK_CATEGORY_IDS",
    "TapCheckLedgerEntry",
    "TapCheckAuditLedger",
    "audit_trace_map",
    "adapt_runtime_result",
    "adapt_convergence_ruling",
    "adapt_narrative_state_change",
    "adapt_air_lowering",
    "adapt_active_directive",
    "compose_tap_check_ledgers",
    "tap_check_category_coverage",
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


def _expect_type_error(thunk, phrase: str) -> None:
    try:
        thunk()
    except TypeError as error:
        _require(phrase in str(error), "diagnostic changed: {!r}".format(error))
    else:
        raise AssertionError("TypeError was not raised")


def _assert_predecessor() -> None:
    resolved = _git("rev-parse", "{}^{{}}".format(PREDECESSOR_TAG))
    _require(resolved.returncode == 0, resolved.stderr.strip())
    _require(
        resolved.stdout.strip() == PREDECESSOR_COMMIT,
        "P11.11D freeze target changed",
    )
    _require(
        _git("merge-base", "--is-ancestor", PREDECESSOR_TAG, "HEAD").returncode
        == 0,
        "P11.11D freeze is not an ancestor of P11.11E",
    )
    for relative, expected in FROZEN_OWNER_HASHES.items():
        _require(
            _sha256(_root() / relative) == expected,
            "{} frozen predecessor hash changed".format(relative),
        )


def _assert_public_surface() -> None:
    import tap_check

    _require(
        tap_check.__all__ == EXPECTED_PUBLIC_SURFACE,
        "tap_check public surface changed",
    )
    _require(
        str(inspect.signature(compose_tap_check_ledgers))
        == "(ledgers: 'Tuple[TapCheckAuditLedger, ...]') -> 'TapCheckAuditLedger'",
        "compose_tap_check_ledgers signature changed",
    )
    _require(
        str(inspect.signature(tap_check_category_coverage))
        == "(ledger: 'TapCheckAuditLedger') -> 'Tuple[Tuple[str, int], ...]'",
        "tap_check_category_coverage signature changed",
    )


def _assert_composition_contract() -> None:
    first = TapCheckLedgerEntry(
        "runtime-results",
        "runtime:first",
        ("diagnostic_count=0",),
    )
    second = TapCheckLedgerEntry(
        "compiler-transformations",
        "compiler:first",
        ("representation=source-map-entry",),
    )
    duplicate = TapCheckLedgerEntry(
        "runtime-results",
        "runtime:first",
        ("diagnostic_count=0",),
    )
    authority = TapCheckLedgerEntry(
        "authority-intervention",
        "authority:check",
        ("representation=authority-check",),
    )

    left = TapCheckAuditLedger((first, second))
    middle = TapCheckAuditLedger()
    right = TapCheckAuditLedger((duplicate, authority))

    composed = compose_tap_check_ledgers((left, middle, right))
    again = compose_tap_check_ledgers((left, middle, right))

    _require(
        composed.entries == (first, second, duplicate, authority),
        "ledger block or entry order changed",
    )
    _require(composed == again, "composition stopped being deterministic")
    _require(composed.entries[0] is first, "first entry reference was replaced")
    _require(composed.entries[1] is second, "second entry reference was replaced")
    _require(
        composed.entries[2] is duplicate,
        "duplicate entry reference was replaced",
    )
    _require(
        composed.entries[3] is authority,
        "authority entry reference was replaced",
    )
    _require(
        composed.entries.count(first) == 2,
        "equal duplicate entries were deduplicated",
    )

    _require(
        compose_tap_check_ledgers(()).entries == (),
        "empty composition fabricated entries",
    )
    _require(
        compose_tap_check_ledgers((middle,)).entries == (),
        "empty ledger block fabricated entries",
    )

    _expect_type_error(
        lambda: compose_tap_check_ledgers([left]),
        "exact tuple",
    )
    _expect_type_error(
        lambda: compose_tap_check_ledgers((object(),)),
        "exact TapCheckAuditLedger",
    )


def _assert_coverage_contract() -> None:
    entries = (
        TapCheckLedgerEntry("runtime-results", "r1"),
        TapCheckLedgerEntry("compiler-transformations", "c1"),
        TapCheckLedgerEntry("runtime-results", "r2"),
        TapCheckLedgerEntry("authority-intervention", "a1"),
        TapCheckLedgerEntry("authority-intervention", "a2"),
    )
    ledger = TapCheckAuditLedger(entries)

    coverage = tap_check_category_coverage(ledger)
    again = tap_check_category_coverage(ledger)

    _require(type(coverage) is tuple, "coverage stopped returning an exact tuple")
    _require(coverage == again, "coverage stopped being deterministic")
    _require(
        tuple(category_id for category_id, _ in coverage)
        == TAP_CHECK_CATEGORY_IDS,
        "coverage category order changed",
    )
    _require(len(coverage) == 10, "coverage row count changed")
    _require(
        dict(coverage)["runtime-results"] == 2,
        "runtime observed-entry count changed",
    )
    _require(
        dict(coverage)["compiler-transformations"] == 1,
        "compiler observed-entry count changed",
    )
    _require(
        dict(coverage)["authority-intervention"] == 2,
        "authority observed-entry count changed",
    )
    _require(
        dict(coverage)["semantic-changes"] == 0,
        "absent semantic-change category count changed",
    )
    _require(
        dict(coverage)["optimization-decisions"] == 0,
        "absent optimization category count changed",
    )
    _require(
        dict(coverage)["continuity-effects"] == 0,
        "absent continuity category count changed",
    )
    _require(
        sum(count for _, count in coverage) == len(entries),
        "coverage counts do not equal observed ledger entry count",
    )

    empty_coverage = tap_check_category_coverage(TapCheckAuditLedger())
    _require(len(empty_coverage) == 10, "empty coverage lost canonical rows")
    _require(
        all(count == 0 for _, count in empty_coverage),
        "empty ledger coverage fabricated observed entries",
    )

    _expect_type_error(
        lambda: tap_check_category_coverage(object()),
        "exact TapCheckAuditLedger",
    )


def _assert_aggregation_is_pure() -> None:
    text = (
        _root() / "apexforge/tap_check/aggregation.py"
    ).read_text(encoding="utf-8")

    required = (
        "TAP_CHECK_CATEGORY_IDS",
        "TapCheckAuditLedger",
        "compose_tap_check_ledgers",
        "tap_check_category_coverage",
    )
    for token in required:
        _require(token in text, "aggregation contract missing " + token)

    forbidden = (
        "audit_trace_map",
        "adapt_runtime_result",
        "adapt_convergence_ruling",
        "adapt_narrative_state_change",
        "adapt_air_lowering",
        "adapt_active_directive",
        "TraceMap",
        "TraceIdentity",
        "RuntimeEngine",
        "apply_semantic_convergence_policy",
        "lower_linked_generics",
        "compile_",
        "parse_",
        "execute(",
        "sorted(",
        ".sort(",
        "subprocess",
        "Path(",
        "open(",
    )
    for token in forbidden:
        _require(token not in text, "aggregation acquired forbidden behavior: " + token)


def _assert_existing_owners_unchanged() -> None:
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
        "apexforge/workflow",
    )
    diff = _git("diff", "--exit-code", PREDECESSOR_TAG, "--", *paths)
    _require(diff.returncode == 0, "P11.11E mutated existing evidence owners")


def main() -> None:
    _assert_predecessor()
    _assert_public_surface()
    _assert_composition_contract()
    _assert_coverage_contract()
    _assert_aggregation_is_pure()
    _assert_existing_owners_unchanged()

    print("P11_11D_FREEZE_ANCESTRY=PASS")
    print("AGGREGATION_OWNER=tap_check.aggregation")
    print("COMPOSE_API=compose_tap_check_ledgers")
    print("COVERAGE_API=tap_check_category_coverage")
    print("COMPOSITION_INPUT=EXACT_TUPLE_OF_EXACT_LEDGERS")
    print("COMPOSITION_ORDER=CALLER_BLOCK_ORDER_THEN_ENTRY_ORDER")
    print("ENTRY_REFERENCE_PRESERVATION=PASS")
    print("DUPLICATE_ENTRY_PRESERVATION=PASS")
    print("EMPTY_COMPOSITION=EMPTY_LEDGER")
    print("EMPTY_LEDGER_BLOCK=VALID")
    print("SORTING=NONE")
    print("DEDUPLICATION=NONE")
    print("ENTRY_REWRITE=NONE")
    print("COVERAGE_ROWS=10")
    print("COVERAGE_ORDER=TAP_CHECK_CATEGORY_IDS")
    print("COVERAGE_VALUE=OBSERVED_ENTRY_COUNT")
    print("PARTIAL_CATEGORY_COVERAGE=VALID")
    print("ZERO_COUNT=NO_OBSERVED_ENTRY_NOT_NEGATIVE_RESULT")
    print("EVIDENCE_PRODUCTION_INSIDE_AGGREGATION=NONE")
    print("AUDIT_TRACE_MAP_INVOCATION=NONE")
    print("OWNER_ADAPTER_INVOCATION=NONE")
    print("SEMANTIC_INFERENCE=NONE")
    print("RUNTIME_EXECUTION=NONE")
    print("PROJECT_IO=NONE")
    print("EXISTING_OWNER_MUTATION=NONE")
    print("P11_11E_DETERMINISTIC_WHOLE_LEDGER_AGGREGATION_COVERAGE=PASS")


if __name__ == "__main__":
    main()