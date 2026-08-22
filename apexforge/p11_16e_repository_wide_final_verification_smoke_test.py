# P11.16E repository-wide final verification evidence gate.

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
D_FREEZE = "3ffe6e2b9f04507abfa756f750e97aef493eaaa2"
D_TAG = "afp-p11-16d-freeze"

MANIFEST = ROOT / "docs/p11/P11_16E_REPOSITORY_WIDE_FINAL_VERIFICATION_MANIFEST.json"
DOC = ROOT / "docs/p11/P11_16E_REPOSITORY_WIDE_FINAL_VERIFICATION.md"

D_BLOB_SHA256 = {
    "apexforge/p11_16d_historical_environment_toolchain_resolution_smoke_test.py":
        "B7C1836371BE937A9037C141329B793DB45E62971773618BDEA1B00AD98E32D9",
    "docs/p11/P11_16D_NON_DURABLE_RESOLUTION_MANIFEST.json":
        "B852F64B6CBEC9298E15635BADF05009CE345D022FA5C0738839A01CF7E2B018",
    "docs/p11/P11_16D_HISTORICAL_ENVIRONMENT_TOOLCHAIN_RESOLUTION.md":
        "7E4423CDD327FE3374BDEFE67527F9180F0B7115DB3BFE29A6C5157F8D05F6FE",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def git_bytes(*args: str) -> bytes:
    proc = subprocess.run(
        ("git",) + args,
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0:
        raise AssertionError(proc.stderr.decode("utf-8", "replace"))
    return proc.stdout


def git_text(*args: str) -> str:
    return git_bytes(*args).decode("utf-8").strip()


def main() -> int:
    require(git_text("rev-parse", "HEAD") == D_FREEZE, "HEAD must remain frozen D")
    require(git_text("cat-file", "-t", D_TAG) == "tag", "D tag must remain annotated")
    require(git_text("rev-parse", D_TAG + "^{commit}") == D_FREEZE, "D tag target changed")

    for path, expected in D_BLOB_SHA256.items():
        observed = hashlib.sha256(
            git_bytes("show", D_FREEZE + ":" + path)
        ).hexdigest().upper()
        require(observed == expected, "D committed evidence changed: " + path)

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    require(manifest["stage"] == "P11.16E", "E stage changed")
    require(
        manifest["scope"] == "REPOSITORY_WIDE_VERIFICATION_EVIDENCE_ONLY",
        "E scope changed",
    )
    require(manifest["production_mutation"] is False, "production mutation flag changed")
    require(
        manifest["repository_mutation_during_execution"] is False,
        "repository mutation evidence changed",
    )

    routed = manifest["routed_matrix"]
    require(routed["total"] == 178, "routed total changed")
    require(routed["durable_executed"] == 48, "durable total changed")
    require(
        routed["non_durable_resolved_by_p11_16d"] == 130,
        "non-durable resolution total changed",
    )
    require(routed["closure"] == "PASS", "routed closure changed")

    expected_matrix = {
        "DURABLE_CURRENT": 48,
        "ENVIRONMENT_FIXTURE_BOUND": 32,
        "EXTERNAL_TOOLCHAIN_BOUND": 16,
        "HISTORICAL_EXACT_FREEZE": 82,
    }
    require(
        routed["corrected_class_counts"] == expected_matrix,
        "routed class counts changed",
    )

    tracked = manifest["tracked_python"]
    require(tracked["count"] == 610, "tracked Python count changed")
    require(tracked["parse_pass"] == 610, "tracked Python parse pass changed")
    require(tracked["parse_fail"] == 0, "tracked Python parse fail changed")
    require(tracked["python_version_contract"] == "3.9", "Python contract changed")

    durable = manifest["durable_execution"]
    require(durable["total"] == 48, "durable total changed")
    require(durable["pass"] == 48, "durable pass changed")
    require(durable["fail"] == 0, "durable fail changed")
    require(len(durable["results"]) == 48, "durable result row count changed")
    require(
        all(item["exit_code"] == 0 for item in durable["results"]),
        "durable execution result changed",
    )

    legacy = manifest["legacy_unittest_surface"]
    require(legacy["test_file_total"] == 13, "legacy file total changed")
    require(legacy["current_test_file_total"] == 12, "legacy current total changed")
    require(legacy["current_pass"] == 12, "legacy current pass changed")
    require(legacy["current_fail"] == 0, "legacy current fail changed")
    require(legacy["workflow_current_contract"] == "PASS", "workflow contract changed")
    require(legacy["stale_test_file_total"] == 1, "stale legacy total changed")
    require(len(legacy["stale_tests"]) == 1, "stale legacy evidence changed")
    stale = legacy["stale_tests"][0]
    require(
        stale["path"] == "apexforge/tests/test_execution_pipeline.py",
        "stale test identity changed",
    )
    require(
        stale["reason"] == "TEST_CONTRACT_UNSATISFIED_AT_INTRODUCTION",
        "stale test reason changed",
    )
    require(stale["compiler_history_commits"] == 24, "compiler history count changed")
    require(stale["required_symbol_history_matches"] == 0, "compiler.source history changed")

    sentinels = manifest["repository_sentinels"]
    regression = sentinels["regression_harness"]
    require(regression["execution"] == "DISCOVERY_ONLY", "regression harness mode changed")
    require(regression["option"] == "--list", "regression harness option changed")
    require(
        regression["pre_candidate_discovered_smoke_tests"] == 275,
        "pre-candidate discovery count changed",
    )
    require(
        regression["post_candidate_expected_smoke_tests"] == 276,
        "post-candidate discovery expectation changed",
    )
    require(regression["broad_execution_authorized"] is False, "broad regression execution policy changed")

    performance = sentinels["performance_baseline"]
    require(performance["execution"] == "READ_ONLY_DEFAULT", "performance execution mode changed")
    require(performance["exit_code"] == 0, "performance baseline exit changed")
    require(performance["json_output_requested"] is False, "performance JSON-output policy changed")
    require(performance["fixtures"] == ["minimal", "representative-linked"], "performance fixture set changed")
    require(
        performance["threshold_policy"] == "ADVISORY_ONLY_NO_PASS_FAIL_THRESHOLD",
        "performance threshold policy changed",
    )
    require(performance["volatile_timings_frozen"] is False, "volatile timing policy changed")
    require(manifest["volatile_performance_timings_frozen"] is False, "volatile timing freeze changed")

    require(manifest["successor"] == "P11.16F_FINAL_FREEZE", "successor changed")

    doc = DOC.read_text(encoding="utf-8")
    for marker in (
        "The **48 durable rows** execute",
        "remaining **130 non-durable rows**",
        "All **610 tracked Python files**",
        "current pass: **12**",
        "proven stale test files: **1**",
        "discovers **275**",
        "expected to increase discovery by one, to **276**",
        "Volatile timing measurements are **not frozen**",
        "**P11.16F â€” Final Freeze**",
    ):
        require(marker in doc, "E documentation marker missing: " + marker)

    print("P11_16E_SCOPE=REPOSITORY_WIDE_VERIFICATION_EVIDENCE_ONLY")
    print("P11_16E_PRODUCTION_FILES=0")
    print("P11_16E_ROUTED_MATRIX_TOTAL=178")
    print("P11_16E_DURABLE_PASS=48")
    print("P11_16E_NON_DURABLE_RESOLVED=130")
    print("P11_16E_TRACKED_PYTHON_PARSE_PASS=610")
    print("P11_16E_LEGACY_CURRENT_PASS=12")
    print("P11_16E_LEGACY_STALE_TESTS=1")
    print("P11_16E_WORKFLOW_CURRENT_CONTRACT=PASS")
    print("P11_16E_REGRESSION_HARNESS_EXECUTION=DISCOVERY_ONLY")
    print("P11_16E_PERFORMANCE_BASELINE=PASS")
    print("P11_16E_VOLATILE_PERFORMANCE_TIMINGS_FROZEN=NO")
    print("P11_16E_PRODUCTION_MUTATION=NONE")
    print("P11_16E_NEXT=P11_16F_FINAL_FREEZE")
    print("P11_16E_REPOSITORY_WIDE_FINAL_VERIFICATION=PASS")
    print("P11_16E_EXIT=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
