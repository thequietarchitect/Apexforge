from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APEXFORGE = ROOT / "apexforge"
CONTRACT = APEXFORGE / "p12_5_rcv_51_p12_5_recovery_terminal_closure.json"
DOC = APEXFORGE / "p12_5_rcv_51_p12_5_recovery_terminal_closure.md"
RCV50 = APEXFORGE / "p12_5_rcv_50_recovery_closure_audit.json"
RCV50_SMOKE = APEXFORGE / "p12_5_rcv_50_recovery_closure_audit_smoke_test.py"


def req(value, message):
    if not value:
        raise AssertionError(message)


def main() -> int:
    previous = json.loads(RCV50.read_text(encoding="utf-8-sig"))
    data = json.loads(CONTRACT.read_text(encoding="utf-8-sig"))
    doc = DOC.read_text(encoding="utf-8-sig")
    req(previous["result"] == "PASS", "RCV-50 audit changed")
    req(data["predecessor"]["stage"] == "P12.5-RCV-50", "predecessor changed")

    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    audit = subprocess.run(
        [sys.executable, "-B", str(RCV50_SMOKE)], cwd=ROOT, env=env,
        text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    req(audit.returncode == 0, "closure audit failed\n" + audit.stdout + audit.stderr)
    req("P12_5_RCV_50_RECOVERY_CLOSURE_AUDIT=PASS" in audit.stdout, "audit marker missing")

    gates = []
    for path in APEXFORGE.glob("p12_5_rcv_*_smoke_test.py"):
        if re.match(r"p12_5_rcv_\d+_", path.name):
            gates.append(path)
    req(len(gates) == 48, f"terminal recovery gate count changed: {len(gates)}")

    closure = data["closure"]
    expected = {
        "recovery_terminal_closure": "PASS",
        "language_semantic_authority": "CANONICAL_AIR",
        "no_second_semantic_implementation": True,
        "p12_4_freeze_preserved": True,
        "provenance_preserved": True,
        "determinism": "PASS",
        "managed_runtime_build": "PASS",
        "regression_stack": "PASS",
        "historical_identity_claim": False,
        "ready_for_freeze_review": True,
    }
    req(closure == expected, "terminal closure result changed")
    req(data["implemented_boundary"]["decoder_root"] == "WHOLE_CANONICAL_AIR_DOCUMENT", "decoder root changed")
    req(data["implemented_boundary"]["projection"] == "$.functions", "function projection changed")
    req("EXECUTION_DISPATCH" in data["deferred_boundaries"], "execution dispatch not deferred")
    req("NONFINITE_TRANSPORT_NORMALIZATION" in data["deferred_boundaries"], "non-finite normalization not deferred")
    req(data["git_actions"] == {"files_staged": False, "commit_created": False, "tag_created": False, "push_attempted": False, "freeze_authorized": False}, "Git boundary changed")
    req("does not authorize staging, committing, tagging, or pushing" in doc, "freeze review warning missing")
    print("P12_5_RECOVERY_TERMINAL_CLOSURE=PASS")
    print("P12_5_LANGUAGE_SEMANTIC_AUTHORITY=CANONICAL_AIR")
    print("P12_5_NO_SECOND_SEMANTIC_IMPLEMENTATION=True")
    print("P12_5_P12_4_FREEZE_PRESERVED=True")
    print("P12_5_PROVENANCE_PRESERVED=True")
    print("P12_5_DETERMINISM=PASS")
    print("P12_5_MANAGED_RUNTIME_BUILD=PASS")
    print("P12_5_REGRESSION_STACK=PASS")
    print("P12_5_HISTORICAL_IDENTITY_CLAIM=False")
    print("P12_5_READY_FOR_FREEZE_REVIEW=True")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
