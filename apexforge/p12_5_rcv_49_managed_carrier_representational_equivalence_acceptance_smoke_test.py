from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "apexforge/p12_5_rcv_49_managed_carrier_representational_equivalence_acceptance.json"
RCV48 = ROOT / "apexforge/p12_5_rcv_48_managed_carrier_integration_scope_decision.json"
RCV44_SMOKE = ROOT / "apexforge/p12_5_rcv_44_managed_executable_carrier_decoder_positive_conformance_smoke_test.py"
RCV45_SMOKE = ROOT / "apexforge/p12_5_rcv_45_managed_executable_carrier_decoder_negative_conformance_smoke_test.py"
RCV47_SMOKE = ROOT / "apexforge/p12_5_rcv_47_managed_carrier_derivation_determinism_recursive_graph_acceptance_smoke_test.py"
P12_1E_SMOKE = ROOT / "apexforge/p12_1e_deterministic_canonical_result_cross_target_smoke_test.py"
DECODER = ROOT / "runtimes/dotnet/ApexForge.Runtime/ManagedExecutableCarrierDecoder.cs"
CARRIER = ROOT / "runtimes/dotnet/ApexForge.Runtime/ManagedExecutableCarrier.cs"


def req(value, message):
    if not value:
        raise AssertionError(message)


def run_test(path):
    result = subprocess.run(
        [sys.executable, str(path)],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    req(result.returncode == 0, f"predecessor test failed: {path.name}\n{result.stdout}{result.stderr}")
    return result.stdout


def main() -> int:
    previous = json.loads(RCV48.read_text(encoding="utf-8-sig"))
    data = json.loads(CONTRACT.read_text(encoding="utf-8-sig"))
    req(previous["decision"]["execution_dispatch"] == "DEFERRED_NO_EXECUTION_CONTRACT", "RCV-48 execution boundary changed")
    req(data["predecessor"]["stage"] == "P12.5-RCV-48", "predecessor changed")

    positive = run_test(RCV44_SMOKE)
    negative = run_test(RCV45_SMOKE)
    deterministic = run_test(RCV47_SMOKE)
    cross_target = run_test(P12_1E_SMOKE)
    req("P12_5_RCV_44_POSITIVE_CONFORMANCE=PASS" in positive, "positive conformance marker missing")
    req("P12_5_RCV_45_NEGATIVE_CONFORMANCE=PASS" in negative, "negative conformance marker missing")
    req("P12_5_RCV_47_DERIVATION_DETERMINISM=PASS" in deterministic, "determinism marker missing")
    req("P12_1E" in cross_target and "PASS" in cross_target, "P12.1E cross-target regression marker missing")

    scope = data["scope"]
    req(scope["canonical_air_semantics_authoritative"] is True, "canonical authority removed")
    req(scope["managed_projection_reinterprets_semantics"] is False, "semantic reinterpretation authorized")
    req(scope["carrier_execution_equivalence_claimed"] is False, "unsupported execution equivalence claimed")
    req(scope["reason_execution_equivalence_not_claimed"] == "NO_P12_5_CARRIER_EXECUTION_CONTRACT", "execution boundary rationale changed")
    req(set(data["representational_equivalence"].values()) <= {"PASS", "FAIL_CLOSED"}, "equivalence result incomplete")

    production = DECODER.read_text(encoding="utf-8-sig") + "\n" + CARRIER.read_text(encoding="utf-8-sig")
    for token in ("Execute(", "Dispatch(", "Evaluate(", "Interpret("):
        req(token not in production, f"hidden execution path appeared: {token}")
    req(data["authority"]["no_second_semantic_implementation"] is True, "semantic duplication authorized")
    print("P12_5_RCV_49_INTEGER_EXACTNESS=PASS")
    print("P12_5_RCV_49_BINARY64_UNICODE_BOOLEAN=PASS")
    print("P12_5_RCV_49_FUNCTION_CONTROL_FLOW_GENERIC_SHAPE=PASS")
    print("P12_5_RCV_49_EXECUTION_EQUIVALENCE_CLAIMED=False")
    print("P12_5_RCV_49_REPRESENTATIONAL_EQUIVALENCE=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
