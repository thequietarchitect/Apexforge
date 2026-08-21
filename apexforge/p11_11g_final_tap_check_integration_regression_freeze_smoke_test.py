"""P11.11G final TAP Check integration, regression, and freeze coverage."""

from __future__ import annotations

import hashlib
import inspect
from pathlib import Path
import subprocess

import tap_check
from tap_check import (
    TAP_CHECK_CATEGORY_IDS,
    TapCheckAuditLedger,
    TapCheckLedgerEntry,
    compose_tap_check_ledgers,
    tap_check_category_coverage,
)
from tooling import cli


PREDECESSOR_TAG = "afp-p11-11f-freeze"
PREDECESSOR_COMMIT = "69ca0d2d5e48f232ebf08d7b03902de0ba1f609a"

FREEZE_CHAIN = (
    ("afp-p11-11a-freeze", "e8d541a61cce3c27f3b1154b21e684453c5612ce"),
    ("afp-p11-11b-freeze", "295613496b2c5f8d9123fd90cd55f501c6ec76ec"),
    ("afp-p11-11c-freeze", "80a690c04f2fd6dcc6cd30f69373040ee8973bb2"),
    ("afp-p11-11d-freeze", "f8a3b6ddc2115ffa8f02033c4a45cf5b722bcc44"),
    ("afp-p11-11e-freeze", "1e75e0b228836a2e045829512f745d2c4b40e2d8"),
    ("afp-p11-11f-freeze", "69ca0d2d5e48f232ebf08d7b03902de0ba1f609a"),
)

FROZEN_HASHES = {
    "apexforge/tap_check/model.py":
        "C1E6F650977A73A7E3F3655A948416129AAB0AFDDB69DA561582F771C16B8769",
    "apexforge/tap_check/projection.py":
        "C43F222DC98704A3C3803F475359F97B72FCB0BEAB6F829188493CF591B117A2",
    "apexforge/tap_check/adapters.py":
        "8895FBF8D79EC70BE09E0F73E31B42829A3C6BB326F5B0326B54E9793C0C7CBA",
    "apexforge/tap_check/aggregation.py":
        "D272A29774AC435ACF58CCB2CD678A234F2CC47D0EEDBBAEA502D99AE9733BAA",
    "apexforge/tap_check/__init__.py":
        "8ED086D0CA4FD55B80D8F86118370489D0410F815897EA76C62BC445F8D59A26",
    "apexforge/tooling/cli.py":
        "B5B74D7EE69B05C545C4F2CCAA2DA60505A917D8910D4CEF62B845A8A085328A",
    "apexforge/p11_11f_tap_check_cli_project_acceptance_smoke_test.py":
        "8C7758D82FA666EC9C75B7E5446E9019D906977325B5FED57758EFF07790B8DC",
    "apexforge/p11_11f_tap_check_powershell_acceptance.ps1":
        "4C3526E32F3A69322A15A0713777CC41B7525EFA9AB225CA343C17FCEC548362",
    "docs/p11/P11_11F_TAP_CHECK_CLI_PROJECT_ACCEPTANCE.md":
        "3F779E6B96E2B2DA26EE5D4E3676BF3EBE3064549D03DEA30A92B39F715563E8",
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

EXPECTED_SIGNATURES = {
    "audit_trace_map":
        "(trace_map: 'TraceMap') -> 'TapCheckAuditLedger'",
    "adapt_runtime_result":
        "(result: 'ExecutionResult') -> 'TapCheckLedgerEntry'",
    "adapt_convergence_ruling":
        "(resolution: 'SemanticConvergenceResolution') -> 'TapCheckLedgerEntry'",
    "adapt_narrative_state_change":
        "(result: 'NarrativeExecutionResult') -> 'TapCheckLedgerEntry'",
    "adapt_air_lowering":
        "(result: 'GenericLoweringResult') -> 'TapCheckLedgerEntry'",
    "adapt_active_directive":
        "(result: 'DirectiveExecutionResult') -> 'TapCheckLedgerEntry'",
    "compose_tap_check_ledgers":
        "(ledgers: 'Tuple[TapCheckAuditLedger, ...]') -> 'TapCheckAuditLedger'",
    "tap_check_category_coverage":
        "(ledger: 'TapCheckAuditLedger') -> 'Tuple[Tuple[str, int], ...]'",
}

OBSERVABLE_CATEGORIES = (
    "active-directives",
    "compiler-transformations",
    "authority-intervention",
    "narrative-state-changes",
    "convergence-rulings",
    "air-lowering",
    "runtime-results",
)

DEFERRED_CATEGORIES = (
    "semantic-changes",
    "optimization-decisions",
    "continuity-effects",
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
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _assert_freeze_chain() -> None:
    for tag, expected in FREEZE_CHAIN:
        resolved = _git("rev-parse", "{}^{{}}".format(tag))
        _require(resolved.returncode == 0, resolved.stderr.strip())
        _require(
            resolved.stdout.strip() == expected,
            "{} target changed".format(tag),
        )
        _require(
            _git("merge-base", "--is-ancestor", tag, "HEAD").returncode == 0,
            "{} is not an ancestor of P11.11G".format(tag),
        )


def _assert_frozen_hashes() -> None:
    for relative, expected in FROZEN_HASHES.items():
        _require(
            _sha256(_root() / relative) == expected,
            "{} frozen hash changed".format(relative),
        )


def _assert_final_public_contract() -> None:
    _require(
        TAP_CHECK_CATEGORY_IDS == EXPECTED_CATEGORIES,
        "TAP category taxonomy changed",
    )
    _require(
        tap_check.__all__ == EXPECTED_PUBLIC_SURFACE,
        "TAP public surface changed",
    )
    for name, expected in EXPECTED_SIGNATURES.items():
        actual = str(inspect.signature(getattr(tap_check, name)))
        _require(actual == expected, "{} signature changed: {}".format(name, actual))


def _assert_final_capability_census() -> None:
    projection_module = inspect.getmodule(tap_check.audit_trace_map)
    _require(projection_module is not None, "audit_trace_map module missing")
    projection_source = inspect.getsource(projection_module)

    _require(
        projection_source.count('"compiler-transformations"') >= 1,
        "compiler-transformation projection disappeared",
    )
    _require(
        projection_source.count('"authority-intervention"') >= 1,
        "authority-intervention projection disappeared",
    )

    adapter_categories = {
        "adapt_runtime_result": "runtime-results",
        "adapt_convergence_ruling": "convergence-rulings",
        "adapt_narrative_state_change": "narrative-state-changes",
        "adapt_air_lowering": "air-lowering",
        "adapt_active_directive": "active-directives",
    }
    for name, category in adapter_categories.items():
        source = inspect.getsource(getattr(tap_check, name))
        _require(
            '"{}"'.format(category) in source,
            "{} no longer reports {}".format(name, category),
        )

    entries = tuple(
        TapCheckLedgerEntry(
            category_id=category,
            subject="p11.11g:{}".format(category),
        )
        for category in OBSERVABLE_CATEGORIES
    )
    ledger = compose_tap_check_ledgers(
        (
            TapCheckAuditLedger(entries[:2]),
            TapCheckAuditLedger(),
            TapCheckAuditLedger(entries[2:5]),
            TapCheckAuditLedger(entries[5:]),
        )
    )
    _require(ledger.entries == entries, "whole-ledger order changed")
    for index, entry in enumerate(entries):
        _require(
            ledger.entries[index] is entry,
            "ledger entry reference {} was replaced".format(index),
        )

    coverage = tap_check_category_coverage(ledger)
    _require(
        tuple(category for category, _ in coverage) == EXPECTED_CATEGORIES,
        "coverage order changed",
    )
    _require(len(coverage) == 10, "coverage row count changed")
    coverage_map = dict(coverage)
    for category in OBSERVABLE_CATEGORIES:
        _require(
            coverage_map[category] == 1,
            "{} observed count changed".format(category),
        )
    for category in DEFERRED_CATEGORIES:
        _require(
            coverage_map[category] == 0,
            "{} should remain unobserved in final census".format(category),
        )
    _require(
        sum(count for _, count in coverage) == 7,
        "final observed capability count changed",
    )


def _assert_cli_boundary() -> None:
    source = inspect.getsource(cli._run_tap_check)

    for token in (
        "load_project(Path(path))",
        "compose_tap_check_ledgers(())",
        "tap_check_category_coverage(ledger)",
        "TAP_CHECK_MODE",
    ):
        _require(token in source, "final CLI contract missing " + token)

    for token in (
        "build_project",
        "compile_",
        "parse_",
        "audit_trace_map",
        "adapt_runtime_result",
        "adapt_convergence_ruling",
        "adapt_narrative_state_change",
        "adapt_air_lowering",
        "adapt_active_directive",
        "trace_map_from_",
        "RuntimeEngine",
        ".execute(",
        "apply_semantic_convergence_policy",
        "assess_paradox_elevation",
        "lower_linked_generics",
    ):
        _require(token not in source, "final CLI acquired behavior: " + token)


def _assert_no_g_production_mutation() -> None:
    paths = (
        "apexforge/tap_check",
        "apexforge/tooling",
        "apexforge/tam",
        "apexforge/governance",
        "apexforge/language",
        "apexforge/air",
        "apexforge/authority",
        "apexforge/runtime",
        "apexforge/language_server",
        "apexforge/semantic_lattice",
        "apexforge/semantic_decision",
        "apexforge/aether_air",
        "apexforge/type_system",
        "apexforge/workflow",
    )
    diff = _git("diff", "--exit-code", PREDECESSOR_TAG, "--", *paths)
    _require(diff.returncode == 0, "P11.11G mutated production or owner code")


def main() -> None:
    _assert_freeze_chain()
    _assert_frozen_hashes()
    _assert_final_public_contract()
    _assert_final_capability_census()
    _assert_cli_boundary()
    _assert_no_g_production_mutation()

    print("P11_11_A_THROUGH_F_FREEZE_CHAIN=PASS")
    print("P11_11_FROZEN_PREDECESSOR_SLICES=6")
    print("TAP_CHECK_CATEGORY_COUNT=10")
    print("TAP_CHECK_PUBLIC_SYMBOL_COUNT=11")
    print("TAP_CHECK_OPERATION_COUNT=8")
    print("TRACE_MAP_DIRECT_CATEGORY_COUNT=2")
    print("OWNER_ADAPTER_CATEGORY_COUNT=5")
    print("EXPLICIT_OBSERVATION_CAPABILITY_CATEGORY_COUNT=7")
    print("DEFERRED_UNAMBIGUOUS_OWNER_CATEGORY_COUNT=3")
    print(
        "OBSERVABLE_CATEGORIES={}".format(
            ",".join(OBSERVABLE_CATEGORIES)
        )
    )
    print(
        "DEFERRED_CATEGORIES={}".format(
            ",".join(DEFERRED_CATEGORIES)
        )
    )
    print("TEN_ROW_REPORTING_TAXONOMY=COMPLETE")
    print("WHOLE_LEDGER_COMPOSITION=PASS")
    print("LEDGER_ENTRY_REFERENCE_PRESERVATION=PASS")
    print("CANONICAL_COVERAGE_ORDER=PASS")
    print("PARTIAL_EVIDENCE_COVERAGE=VALID")
    print("MISSING_EVIDENCE=UNOBSERVED_NOT_NEGATIVE_RESULT")
    print("DEFERRED_CATEGORY_FABRICATION=NONE")
    print("CLI_COMMAND=apexforge tap-check .")
    print("CLI_MODE=observational")
    print("CLI_PREREQUISITE_CREATION=NONE")
    print("CLI_RUNTIME_EXECUTION=NONE")
    print("DIRECTIVE_ACTIVATION_BY_TAP=NONE")
    print("AUTHORITY_DECISION_BY_TAP=NONE")
    print("SEMANTIC_DECISION_BY_TAP=NONE")
    print("PROJECT_MUTATION_BY_TAP=NONE")
    print("G_PRODUCTION_MUTATION=NONE")
    print("P11_11G_FINAL_TAP_CHECK_INTEGRATION_REGRESSION_FREEZE=PASS")


if __name__ == "__main__":
    main()