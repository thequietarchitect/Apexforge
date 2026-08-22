from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
B_FREEZE = "4c1de19080a7dfbe51492041c8968ddcd409ec77"
B_TAG = "afp-p11-16b-freeze"
B_MANIFEST_SHA256 = "950719EC51C523FCA3BF2BC39771AD068109EA3E8E7A23407E4C15C38E53AC2E"

B_MANIFEST = ROOT / "docs/p11/P11_16B_FINAL_VERIFICATION_MATRIX_MANIFEST.json"
CORRECTION = ROOT / "docs/p11/P11_16C_DURABLE_SEMANTIC_EXECUTION_CORRECTION.json"
DOC = ROOT / "docs/p11/P11_16C_DURABLE_SEMANTIC_EXECUTION.md"

EXPECTED = {
    "apexforge/p11_1b_run_command_smoke_test.py": "ENVIRONMENT_FIXTURE_BOUND",
    "apexforge/p11_1c_build_artifact_smoke_test.py": "ENVIRONMENT_FIXTURE_BOUND",
    "apexforge/p11_9h_aether_air_reporting_tooling_traceability_smoke_test.py": "HISTORICAL_EXACT_FREEZE",
    "apexforge/p11_src_a_semantic_decision_source_architecture_audit_smoke_test.py": "HISTORICAL_EXACT_FREEZE",
    "apexforge/p11_src_b_immutable_semantic_decision_source_ast_smoke_test.py": "HISTORICAL_EXACT_FREEZE",
    "apexforge/p11_src_c_deterministic_semantic_decision_source_parser_smoke_test.py": "HISTORICAL_EXACT_FREEZE",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def git(*args: str) -> str:
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
    require(git("rev-parse", "HEAD") == B_FREEZE, "HEAD changed")
    require(git("cat-file", "-t", B_TAG) == "tag", "B tag not annotated")
    require(git("rev-parse", B_TAG + "^{commit}") == B_FREEZE, "B tag target changed")
    require(hashlib.sha256(B_MANIFEST.read_bytes()).hexdigest().upper() == B_MANIFEST_SHA256, "B manifest bytes changed")

    base = json.loads(B_MANIFEST.read_text(encoding="utf-8"))
    correction = json.loads(CORRECTION.read_text(encoding="utf-8"))

    require(correction["frozen_b_manifest_mutated"] is False, "B mutation flag changed")
    require(correction["production_mutation"] is False, "production mutation flag changed")
    require(correction["correction_count"] == 6, "correction count changed")
    require({x["path"]: x["to_class"] for x in correction["corrections"]} == EXPECTED, "correction set changed")
    require(correction["corrected_class_counts"] == {
        "DURABLE_CURRENT": 48,
        "HISTORICAL_EXACT_FREEZE": 82,
        "ENVIRONMENT_FIXTURE_BOUND": 32,
        "EXTERNAL_TOOLCHAIN_BOUND": 16,
    }, "corrected counts changed")
    require(correction["corrected_matrix_total"] == 178, "matrix total changed")

    execution = correction["durable_execution"]
    require(execution["total"] == 48, "durable total changed")
    require(execution["pass"] == 48, "durable pass changed")
    require(execution["fail"] == 0, "durable fail changed")
    require(execution["repository_mutation"] is False, "repository mutation flag changed")
    require(len(execution["results"]) == 48, "result count changed")
    require(all(x["exit_code"] == 0 for x in execution["results"]), "nonzero durable result")

    corrected = {x["path"]: x["primary_class"] for x in base["entries"]}
    for path, new_class in EXPECTED.items():
        require(corrected[path] == "DURABLE_CURRENT", "B source class changed")
        corrected[path] = new_class
    expected_durable = sorted(path for path, value in corrected.items() if value == "DURABLE_CURRENT")
    result_paths = sorted(x["path"] for x in execution["results"])
    require(result_paths == expected_durable, "durable coverage changed")

    doc = DOC.read_text(encoding="utf-8")
    require("`DURABLE_CURRENT`: **48**" in doc, "doc durable count changed")
    require("`HISTORICAL_EXACT_FREEZE`: **82**" in doc, "doc historical count changed")
    require("`ENVIRONMENT_FIXTURE_BOUND`: **32**" in doc, "doc environment count changed")
    require("`EXTERNAL_TOOLCHAIN_BOUND`: **16**" in doc, "doc external count changed")

    print("P11_16C_SCOPE=VERIFICATION_EVIDENCE_ONLY")
    print("P11_16C_PRODUCTION_FILES=0")
    print("P11_16C_FROZEN_B_MANIFEST_MUTATED=NO")
    print("P11_16C_CORRECTION_COUNT=6")
    print("P11_16C_CORRECTED_DURABLE=48")
    print("P11_16C_CORRECTED_HISTORICAL=82")
    print("P11_16C_CORRECTED_ENVIRONMENT=32")
    print("P11_16C_CORRECTED_EXTERNAL=16")
    print("P11_16C_CORRECTED_MATRIX_TOTAL=178")
    print("P11_16C_DURABLE_EXECUTION_PASS=48")
    print("P11_16C_DURABLE_EXECUTION_FAIL=0")
    print("P11_16C_REPOSITORY_MUTATION=NONE")
    print("P11_16C_PRODUCTION_MUTATION=NONE")
    print("P11_16C_NEXT=P11_16D_HISTORICAL_ENVIRONMENT_TOOLCHAIN_RESOLUTION")
    print("P11_16C_CORRECTED_DURABLE_SEMANTIC_EXECUTION=PASS")
    print("P11_16C_EXIT=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())