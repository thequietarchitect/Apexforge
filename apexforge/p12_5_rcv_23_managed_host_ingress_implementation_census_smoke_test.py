from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "apexforge/p12_5_rcv_23_managed_host_ingress_implementation_census.json"
RCV22 = ROOT / "apexforge/p12_5_rcv_22_cross_runtime_transport_contract_decision_smoke_test.py"
RCV10 = ROOT / "apexforge/p12_5_rcv_10_host_ingress_contract_decision.json"
HOST_DIR = ROOT / "runtimes/dotnet/ApexForge.Runtime.Host"
HOST_PROGRAM = HOST_DIR / "Program.cs"
HOST_LIFECYCLE = HOST_DIR / "RuntimeHostLifecycle.cs"
FUTURE_INGRESS = HOST_DIR / "RuntimeHostIngress.cs"
MANAGED_HOST = ROOT / "runtimes/dotnet/ApexForge.Runtime/ManagedRuntimeHost.cs"
HANDOFF = ROOT / "runtimes/dotnet/ApexForge.Runtime/TargetNeutralLoweringHandoff.cs"

FORBIDDEN_HOST_TOKENS = (
    "JsonSerializer",
    "Console.ReadLine",
    "Console.In",
    "OpenStandardInput",
    "File.Read",
    "FileStream",
    "NamedPipe",
    "TcpListener",
    "TcpClient",
    "HttpListener",
    "HttpClient",
    "ProcessStartInfo",
    "Python.Runtime",
)

def req(c, m):
    if not c:
        raise AssertionError(m)

def run(*args):
    return subprocess.run(list(args), cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def read_all_host_cs():
    rows = []
    for p in sorted(HOST_DIR.glob("*.cs")):
        rows.append((p, p.read_text(encoding="utf-8-sig")))
    return rows

def main():
    print("=== P12.5-RCV-23 MANAGED HOST INGRESS IMPLEMENTATION CENSUS ===")
    for p in (CONTRACT, RCV22, RCV10, HOST_PROGRAM, HOST_LIFECYCLE, MANAGED_HOST, HANDOFF):
        req(p.exists(), f"missing required file: {p}")

    cp = run(sys.executable, str(RCV22))
    req(cp.returncode == 0, "RCV-22 regression failed:\n" + cp.stdout + "\n" + cp.stderr)
    print("P12_5_RCV_23_RCV22_REGRESSION=PASS")

    ingress_decision = json.loads(RCV10.read_text(encoding="utf-8-sig"))
    d10 = ingress_decision["decision"]
    req(d10["host_ingress_family"] == "IN_PROCESS_API", "RCV-10 host ingress family changed")
    req(d10["future_ingress_type"] == "ApexForge.Runtime.Host.RuntimeHostIngress", "RCV-10 future ingress type changed")
    req(d10["ingress_owner"] == "ApexForge.Runtime.Host", "RCV-10 ingress owner changed")
    req(d10["external_serialization"] == "UNSELECTED", "RCV-10 serialization changed")
    req(d10["network_ingress"] == "FORBIDDEN_IN_THIS_LINE", "RCV-10 network policy changed")

    data = json.loads(CONTRACT.read_text(encoding="utf-8-sig"))
    req(data["profile"] == "apexforge.p12.managed-host-ingress-implementation-census/v1", "profile changed")
    req(data["predecessor"]["stage"] == "P12.5-RCV-22", "predecessor changed")
    hist = data["historical_evidence"]
    req(hist["host_ingress_family"] == "IN_PROCESS_API", "historical ingress family changed")
    req(hist["future_ingress_type"] == "ApexForge.Runtime.Host.RuntimeHostIngress", "future ingress type changed")
    req(hist["historical_implementation_body_recovered"] is False, "unsupported historical implementation claim introduced")
    req(hist["external_serialization"] == "UNSELECTED", "historical serialization state changed")
    req(hist["network_ingress"] == "FORBIDDEN_IN_THIS_LINE", "network policy weakened")

    managed_host = MANAGED_HOST.read_text(encoding="utf-8-sig")
    handoff = HANDOFF.read_text(encoding="utf-8-sig")
    lifecycle = HOST_LIFECYCLE.read_text(encoding="utf-8-sig")
    program = HOST_PROGRAM.read_text(encoding="utf-8-sig")

    req("public sealed record TargetNeutralLoweringHandoff" in handoff, "managed handoff type missing")
    req("public TargetNeutralLoweringHandoff AdmitTargetNeutralHandoff(TargetNeutralLoweringHandoff handoff)" in managed_host, "managed admission method missing")
    req("ArgumentNullException.ThrowIfNull(handoff);" in managed_host, "managed admission null guard missing")
    req("handoff.Validate();" in managed_host, "managed admission validation missing")
    req("return handoff;" in managed_host, "managed admission validate-and-return behavior missing")
    req("public sealed class RuntimeHostLifecycle" in lifecycle, "host lifecycle type missing")

    if FUTURE_INGRESS.exists():
        req((ROOT / "apexforge/p12_5_rcv_25_managed_host_ingress_implementation_foundation.json").exists(), "later ingress implementation lacks RCV-25 lineage")
    req("RuntimeHostIngress" not in program, "Program.cs references ingress before contract gate")

    host_files = read_all_host_cs()
    ingress_name_refs = 0
    handoff_refs = 0
    external_transport_refs = 0
    for p, text in host_files:
        for token in FORBIDDEN_HOST_TOKENS:
            external_transport_refs += text.count(token)
        if p.resolve() == FUTURE_INGRESS.resolve():
            continue
        ingress_name_refs += text.count("RuntimeHostIngress")
        handoff_refs += text.count("TargetNeutralLoweringHandoff")

    req(ingress_name_refs == 0, f"unexpected RuntimeHostIngress references: {ingress_name_refs}")
    req(handoff_refs == 0, f"host project already references target-neutral handoff: {handoff_refs}")
    req(external_transport_refs == 0, f"host project contains external transport references: {external_transport_refs}")

    state = data["selection_state"]
    req(state["ingress_implementation"] == "UNSELECTED", "ingress implementation selected during census")
    req(state["ingress_method_name"] == "UNSELECTED", "ingress method selected during census")
    req(state["ingress_constructor_shape"] == "UNSELECTED", "constructor shape selected during census")
    req(state["ingress_lifecycle_coupling"] == "UNSELECTED", "lifecycle coupling selected during census")
    req(state["external_serialization"] == "UNSELECTED", "serialization selected during census")
    req(state["cross_runtime_transport"] == "DEFERRED_NO_TRANSPORT_AUTHORIZED", "cross-runtime transport changed")
    req(state["execution_dispatch"] == "DEFERRED", "execution dispatch changed")

    auth = data["authority"]
    req(auth["language_semantics"] == "CANONICAL_AIR", "semantic authority changed")
    req(auth["managed_runtime_validation_owner"] == "ApexForge.Runtime", "managed validation owner changed")
    req(auth["managed_host_ingress_owner"] == "ApexForge.Runtime.Host", "ingress owner changed")
    req(auth["host_may_execute_on_ingress"] is False, "host gained execution authority")
    req(auth["host_may_lower_on_ingress"] is False, "host gained lowering authority")
    req(auth["host_may_reinterpret_on_ingress"] is False, "host gained reinterpretation authority")
    req(auth["host_may_select_transport"] is False, "host gained transport authority")

    print(f"P12_5_RCV_23_HOST_CSHARP_FILE_COUNT={len(host_files)}")
    print(f"P12_5_RCV_23_RUNTIME_HOST_INGRESS_REFERENCE_COUNT={ingress_name_refs}")
    print(f"P12_5_RCV_23_TARGET_NEUTRAL_HANDOFF_HOST_REFERENCE_COUNT={handoff_refs}")
    print(f"P12_5_RCV_23_EXTERNAL_TRANSPORT_REFERENCE_COUNT={external_transport_refs}")
    print("P12_5_RCV_23_PROFILE=apexforge.p12.managed-host-ingress-implementation-census/v1")
    print("P12_5_RCV_23_HOST_INGRESS_FAMILY=IN_PROCESS_API")
    print("P12_5_RCV_23_FUTURE_INGRESS_TYPE=ApexForge.Runtime.Host.RuntimeHostIngress")
    print("P12_5_RCV_23_HISTORICAL_IMPLEMENTATION_BODY_RECOVERED=False")
    print("P12_5_RCV_23_RUNTIME_HOST_INGRESS_IMPLEMENTATION=ABSENT")
    print("P12_5_RCV_23_EXTERNAL_SERIALIZATION=UNSELECTED")
    print("P12_5_RCV_23_CROSS_RUNTIME_TRANSPORT=DEFERRED_NO_TRANSPORT_AUTHORIZED")
    print("P12_5_RCV_23_EXECUTION_DISPATCH=DEFERRED")
    print("P12_5_RCV_23_MANAGED_HOST_INGRESS_IMPLEMENTATION_CENSUS=PASS")
    print("P12_5_RCV_23_NEXT=P12.5-RCV-24_MANAGED_HOST_INGRESS_IMPLEMENTATION_CONTRACT")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
