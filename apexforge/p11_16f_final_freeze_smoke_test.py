# P11.16F final-freeze evidence gate.

from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
E_FREEZE = "5283471832281f8a591438073d05bdc619d62072"
E_TAG = "afp-p11-16e-freeze"

MANIFEST = ROOT / "docs/p11/P11_16F_FINAL_FREEZE_MANIFEST.json"
DOC = ROOT / "docs/p11/P11_16F_FINAL_FREEZE.md"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def git_text(*args: str) -> str:
    proc = subprocess.run(
        ("git",) + args,
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise AssertionError(proc.stderr)
    return proc.stdout.strip()


def main() -> int:
    require(git_text("cat-file", "-t", E_TAG) == "tag", "E tag must remain annotated")
    require(
        git_text("rev-parse", E_TAG + "^{commit}") == E_FREEZE,
        "E tag target changed",
    )

    head = git_text("rev-parse", "HEAD")
    ancestor = subprocess.run(
        ("git", "merge-base", "--is-ancestor", E_FREEZE, head),
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    require(ancestor.returncode == 0, "E freeze must remain ancestor of current HEAD")

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    require(manifest["stage"] == "P11.16F", "F stage changed")
    require(
        manifest["scope"] == "FINAL_VERIFICATION_BINDING_ONLY",
        "F scope changed",
    )
    require(manifest["production_mutation"] is False, "production mutation flag changed")
    require(manifest["semantic_reclassification"] is False, "semantic reclassification flag changed")
    require(manifest["test_weakening"] is False, "test weakening flag changed")
    require(manifest["fixture_restoration"] is False, "fixture restoration flag changed")

    closure = manifest["p11_16_verification_closure"]
    require(closure["matrix_total"] == 178, "matrix total changed")
    require(closure["durable_current"] == 48, "durable count changed")
    require(closure["historical_exact_freeze"] == 82, "historical count changed")
    require(closure["environment_fixture_bound"] == 32, "environment count changed")
    require(closure["external_toolchain_bound"] == 16, "external count changed")
    require(closure["non_durable_resolved"] == 130, "non-durable total changed")
    require(closure["durable_pass"] == 48, "durable pass changed")
    require(closure["closure"] == "PASS", "routed closure changed")

    repo = manifest["repository_wide_evidence"]
    require(repo["tracked_python_verified_at_e"] == 610, "E tracked Python evidence changed")
    require(repo["tracked_python_parse_pass_at_e"] == 610, "E Python parse evidence changed")
    require(repo["legacy_test_files"] == 13, "legacy test total changed")
    require(repo["legacy_current_pass"] == 12, "legacy current pass changed")
    require(repo["legacy_stale"] == 1, "legacy stale count changed")
    require(repo["workflow_current_contract"] == "PASS", "workflow contract changed")
    require(repo["regression_discovery_after_e"] == 276, "E regression discovery changed")
    require(repo["regression_harness_execution"] == "DISCOVERY_ONLY", "regression harness mode changed")
    require(repo["performance_baseline"] == "PASS", "performance baseline evidence changed")
    require(repo["volatile_performance_timings_frozen"] is False, "performance timing freeze changed")

    completion = manifest["completion"]
    require(completion["p11_16_status"] == "COMPLETE", "P11.16 completion changed")
    require(completion["p11_final_verification_status"] == "COMPLETE", "final verification completion changed")
    require(completion["p11_status"] == "VERIFIED_COMPLETE", "P11 completion changed")

    require(
        manifest["intended_terminal_tags"]
        == ["afp-p11-16f-freeze", "afp-p11-16-freeze"],
        "terminal tags changed",
    )
    require(manifest["successor"] == "P12_NATIVE_BACKEND", "successor changed")

    doc = DOC.read_text(encoding="utf-8")
    for marker in (
        "total routed closure: **178 / 178**",
        "tracked Python verified at E: **610 / 610 parse PASS**",
        "current legacy unittest files: **12 / 12 PASS**",
        "P11.16: **COMPLETE**",
        "P11: **VERIFIED COMPLETE**",
        "**P12 â€” Native Backend**",
    ):
        require(marker in doc, "F documentation marker missing: " + marker)

    print("P11_16F_SCOPE=FINAL_VERIFICATION_BINDING_ONLY")
    print("P11_16F_PRODUCTION_FILES=0")
    print("P11_16F_ROUTED_CLOSURE=178_OF_178")
    print("P11_16F_DURABLE_PASS=48")
    print("P11_16F_NON_DURABLE_RESOLVED=130")
    print("P11_16F_P11_16_STATUS=COMPLETE")
    print("P11_16F_P11_STATUS=VERIFIED_COMPLETE")
    print("P11_16F_PRODUCTION_MUTATION=NONE")
    print("P11_16F_SUCCESSOR=P12_NATIVE_BACKEND")
    print("P11_16F_FINAL_FREEZE_EVIDENCE=PASS")
    print("P11_16F_EXIT=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
