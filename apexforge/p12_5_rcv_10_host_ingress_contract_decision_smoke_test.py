from __future__ import annotations
import json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "apexforge/p12_5_rcv_10_host_ingress_contract_decision.json"
RCV9 = ROOT / "apexforge/p12_5_rcv_9_host_ingress_architecture_census_smoke_test.py"
LOWERING = ROOT / "apexforge/native_backend/target_neutral_lowering.py"
HOST_DIR = ROOT / "runtimes/dotnet/ApexForge.Runtime.Host"

def req(c, m):
    if not c:
        raise AssertionError(m)

def run(*args):
    return subprocess.run(list(args), cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def main():
    print("=== P12.5-RCV-10 HOST INGRESS CONTRACT DECISION ===")
    req(CONTRACT.exists(), "RCV-10 contract missing")
    req(RCV9.exists(), "RCV-9 smoke missing")
    cp = run(sys.executable, str(RCV9))
    req(cp.returncode == 0, "RCV-9 regression failed:\n" + cp.stdout + "\n" + cp.stderr)
    print("P12_5_RCV_10_RCV9_REGRESSION=PASS")

    data = json.loads(CONTRACT.read_text(encoding="utf-8"))
    req(data["profile"] == "apexforge.p12.host-ingress-contract-decision/v1", "profile changed")
    req(data["predecessor"]["stage"] == "P12.5-RCV-9", "predecessor changed")
    d = data["decision"]
    req(d["host_ingress_family"] == "IN_PROCESS_API", "ingress family changed")
    req(d["handoff_subject"] == "TARGET_NEUTRAL_LOWERING_PRODUCT", "handoff subject changed")
    req(d["concrete_managed_handoff_type"] == "DEFERRED_TO_RECONSTRUCTION_GATE", "managed handoff selected too early")
    req(d["external_serialization"] == "UNSELECTED", "serialization selected too early")
    req(d["command_line_payload_ingress"] == "DEFERRED", "CLI payload ingress selected too early")
    req(d["standard_input_payload_ingress"] == "DEFERRED", "stdin payload ingress selected too early")
    req(d["file_path_payload_ingress"] == "DEFERRED", "file payload ingress selected too early")
    req(d["network_ingress"] == "FORBIDDEN_IN_THIS_LINE", "network ingress policy weakened")

    a = data["authority"]
    req(a["language_semantics"] == "CANONICAL_AIR", "semantic authority changed")
    req(a["canonical_verified_air_owner"] == "air.model.VerifiedAIRProgram", "Verified AIR owner changed")
    req(a["canonical_execution_plan_owner"] == "workflow.air_runner.RegistryExecutionPlan", "execution plan owner changed")
    req(a["host_defines_language_semantics"] is False, "host gained semantic authority")
    req(a["ingress_may_validate"] is True, "validation permission missing")
    req(a["ingress_may_execute"] is False, "ingress execution selected too early")
    req(a["ingress_may_lower"] is False, "ingress lowering selected too early")
    req(a["ingress_may_reinterpret"] is False, "ingress reinterpretation selected too early")

    req(LOWERING.exists(), "P12.2 target-neutral lowering missing")
    lower = LOWERING.read_text(encoding="utf-8")
    req("apexforge.target-neutral-lowering/v1" in lower, "P12.2 schema missing")
    req("TargetNeutralLoweringProduct" in lower, "P12.2 product missing")

    host_text = ""
    for p in HOST_DIR.rglob("*.cs"):
        host_text += p.read_text(encoding="utf-8")
    for forbidden in ("JsonSerializer", "Console.ReadLine", "OpenStandardInput", "TcpListener", "HttpListener", "NamedPipeServerStream", "ManagedExecutableCarrier"):
        req(forbidden not in host_text, f"premature ingress/dispatch implementation found: {forbidden}")
    if "TargetNeutralLoweringHandoff" in host_text:
        req((ROOT / "apexforge/p12_5_rcv_25_managed_host_ingress_implementation_foundation.json").exists(), "later in-process handoff ingress lacks RCV-25 lineage")

    print("P12_5_RCV_10_PROFILE=apexforge.p12.host-ingress-contract-decision/v1")
    print("P12_5_RCV_10_HOST_INGRESS_FAMILY=IN_PROCESS_API")
    print("P12_5_RCV_10_HANDOFF_SUBJECT=TARGET_NEUTRAL_LOWERING_PRODUCT")
    print("P12_5_RCV_10_CONCRETE_MANAGED_HANDOFF_TYPE=DEFERRED")
    print("P12_5_RCV_10_EXTERNAL_SERIALIZATION=UNSELECTED")
    print("P12_5_RCV_10_LANGUAGE_SEMANTIC_AUTHORITY=CANONICAL_AIR")
    print("P12_5_RCV_10_EXECUTION_DISPATCH=DEFERRED")
    print("P12_5_RCV_10_HOST_INGRESS_CONTRACT_DECISION=PASS")
    print("P12_5_RCV_10_NEXT=P12.5-RCV-11_TARGET_NEUTRAL_MANAGED_HANDOFF_RECONSTRUCTION_CONTRACT")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
