from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "apexforge/p12_5_rcv_27_managed_host_program_integration_contract.json"
RCV26 = ROOT / "apexforge/p12_5_rcv_26_managed_host_ingress_integration_census_smoke_test.py"
PROGRAM = ROOT / "runtimes/dotnet/ApexForge.Runtime.Host/Program.cs"
LIFECYCLE = ROOT / "runtimes/dotnet/ApexForge.Runtime.Host/RuntimeHostLifecycle.cs"
INGRESS = ROOT / "runtimes/dotnet/ApexForge.Runtime.Host/RuntimeHostIngress.cs"

def req(c, m):
    if not c:
        raise AssertionError(m)

def run(*args):
    return subprocess.run(list(args), cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def main():
    print("=== P12.5-RCV-27 MANAGED HOST PROGRAM INTEGRATION CONTRACT ===")
    for p in (CONTRACT, RCV26, PROGRAM, LIFECYCLE, INGRESS):
        req(p.exists(), f"missing required file: {p}")

    cp = run(sys.executable, str(RCV26))
    req(cp.returncode == 0, "RCV-26 regression failed:\n" + cp.stdout + "\n" + cp.stderr)
    print("P12_5_RCV_27_RCV26_REGRESSION=PASS")

    data = json.loads(CONTRACT.read_text(encoding="utf-8-sig"))
    req(data["profile"] == "apexforge.p12.managed-host-program-integration-contract/v1", "profile changed")
    req(data["predecessor"]["stage"] == "P12.5-RCV-26", "predecessor changed")

    hist = data["historical_evidence"]
    req(hist["runtime_host_ingress_type_recovered"] is True, "ingress recovery status changed")
    for key in (
        "program_wiring_recovered",
        "program_handoff_admission_recovered",
        "external_payload_source_recovered",
        "cross_runtime_transport_recovered",
        "historical_identity_claim",
    ):
        req(hist[key] is False, f"unsupported historical program-integration claim introduced: {key}")

    d = data["decision"]
    req(d["program_ingress_wiring"] == "DEFERRED_NO_PAYLOAD_SOURCE", "program wiring decision changed")
    req(d["program_constructs_runtime_host_ingress"] is False, "program constructs ingress")
    req(d["program_admits_target_neutral_handoff"] is False, "program admits handoff")
    req(d["program_reads_external_payload"] is False, "program reads external payload")
    req(d["lifecycle_ingress_coupling"] == "DEFERRED", "lifecycle coupling selected")
    req(d["runtime_host_ingress_remains_available_as_in_process_api"] is True, "in-process ingress availability changed")
    req(d["external_serialization"] == "UNSELECTED", "serialization selected")
    req(d["cross_runtime_transport"] == "DEFERRED_NO_TRANSPORT_AUTHORIZED", "cross-runtime transport selected")
    req(d["network_ingress"] == "FORBIDDEN_IN_THIS_LINE", "network ingress policy weakened")
    req(d["execution_dispatch"] == "DEFERRED", "execution dispatch selected")

    program = PROGRAM.read_text(encoding="utf-8-sig")
    lifecycle = LIFECYCLE.read_text(encoding="utf-8-sig")
    ingress = INGRESS.read_text(encoding="utf-8-sig")

    req("new ManagedRuntimeHost()" in program, "existing managed runtime construction missing")
    req("new RuntimeHostLifecycle()" in program, "existing lifecycle construction missing")
    req("RuntimeHostIngress" not in program, "Program.cs ingress wiring appeared contrary to RCV-27")
    req("TargetNeutralLoweringHandoff" not in program, "Program.cs handoff admission appeared contrary to RCV-27")
    req("RuntimeHostIngress" not in lifecycle, "lifecycle ingress coupling appeared contrary to RCV-27")
    req("RuntimeHostLifecycle" not in ingress, "ingress lifecycle coupling appeared contrary to RCV-27")

    for token in (
        "JsonSerializer",
        "Console.ReadLine",
        "Console.In",
        "OpenStandardInput",
        "File.Read",
        "FileStream",
        "NamedPipe",
        "TcpListener",
        "HttpListener",
        "ProcessStartInfo",
        "Python.Runtime",
        "ManagedExecutableCarrier",
        "ManagedNativeAbi.",
    ):
        req(token not in program, f"premature Program.cs concern found: {token}")

    r = data["rationale"]
    for key in (
        "avoid_dead_composition",
        "avoid_inventing_payload_source",
        "avoid_inventing_transport",
        "preserve_existing_program_lifecycle_behavior",
        "preserve_runtime_host_ingress_as_library_surface",
    ):
        req(r[key] is True, f"rationale invariant weakened: {key}")

    a = data["authority"]
    req(a["language_semantics"] == "CANONICAL_AIR", "semantic authority changed")
    req(a["managed_validation_owner"] == "ApexForge.Runtime.ManagedRuntimeHost", "validation owner changed")
    req(a["ingress_owner"] == "ApexForge.Runtime.Host", "ingress owner changed")
    req(a["program_role"] == "ORCHESTRATION_AND_LIFECYCLE_SHELL", "program role changed")
    req(a["program_defines_language_semantics"] is False, "program gained semantic authority")
    req(a["program_executes_handoff"] is False, "program gained execution authority")
    req(a["program_selects_transport"] is False, "program gained transport authority")

    print("P12_5_RCV_27_PROFILE=apexforge.p12.managed-host-program-integration-contract/v1")
    print("P12_5_RCV_27_PROGRAM_INGRESS_WIRING=DEFERRED_NO_PAYLOAD_SOURCE")
    print("P12_5_RCV_27_PROGRAM_CONSTRUCTS_INGRESS=False")
    print("P12_5_RCV_27_PROGRAM_ADMITS_HANDOFF=False")
    print("P12_5_RCV_27_RUNTIME_HOST_INGRESS_LIBRARY_SURFACE=True")
    print("P12_5_RCV_27_LIFECYCLE_INGRESS_COUPLING=DEFERRED")
    print("P12_5_RCV_27_EXTERNAL_SERIALIZATION=UNSELECTED")
    print("P12_5_RCV_27_CROSS_RUNTIME_TRANSPORT=DEFERRED_NO_TRANSPORT_AUTHORIZED")
    print("P12_5_RCV_27_NETWORK_INGRESS=FORBIDDEN_IN_THIS_LINE")
    print("P12_5_RCV_27_EXECUTION_DISPATCH=DEFERRED")
    print("P12_5_RCV_27_MANAGED_HOST_PROGRAM_INTEGRATION_CONTRACT=PASS")
    print("P12_5_RCV_27_NEXT=P12.5-RCV-28_MANAGED_EXECUTABLE_CARRIER_HISTORICAL_CENSUS")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
