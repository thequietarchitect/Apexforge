from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "apexforge/p12_5_rcv_26_managed_host_ingress_integration_census.json"
RCV25 = ROOT / "apexforge/p12_5_rcv_25_managed_host_ingress_implementation_foundation_smoke_test.py"
HOST_PROJ = ROOT / "runtimes/dotnet/ApexForge.Runtime.Host/ApexForge.Runtime.Host.csproj"
PROGRAM = ROOT / "runtimes/dotnet/ApexForge.Runtime.Host/Program.cs"
LIFECYCLE = ROOT / "runtimes/dotnet/ApexForge.Runtime.Host/RuntimeHostLifecycle.cs"
INGRESS = ROOT / "runtimes/dotnet/ApexForge.Runtime.Host/RuntimeHostIngress.cs"
MANAGED_HOST = ROOT / "runtimes/dotnet/ApexForge.Runtime/ManagedRuntimeHost.cs"
HANDOFF = ROOT / "runtimes/dotnet/ApexForge.Runtime/TargetNeutralLoweringHandoff.cs"

EXTERNAL_TOKENS = (
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

EXECUTION_TOKENS = (
    "ManagedExecutableCarrier",
    "Execute(",
    "Dispatch(",
    "ManagedNativeAbi.",
)

def req(c, m):
    if not c:
        raise AssertionError(m)

def run(*args):
    return subprocess.run(list(args), cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def main():
    print("=== P12.5-RCV-26 MANAGED HOST INGRESS INTEGRATION CENSUS ===")
    for p in (CONTRACT, RCV25, HOST_PROJ, PROGRAM, LIFECYCLE, INGRESS, MANAGED_HOST, HANDOFF):
        req(p.exists(), f"missing required file: {p}")

    cp = run(sys.executable, str(RCV25))
    req(cp.returncode == 0, "RCV-25 regression failed:\n" + cp.stdout + "\n" + cp.stderr)
    print("P12_5_RCV_26_RCV25_REGRESSION=PASS")

    data = json.loads(CONTRACT.read_text(encoding="utf-8-sig"))
    req(data["profile"] == "apexforge.p12.managed-host-ingress-integration-census/v1", "profile changed")
    req(data["predecessor"]["stage"] == "P12.5-RCV-25", "predecessor changed")

    program = PROGRAM.read_text(encoding="utf-8-sig")
    lifecycle = LIFECYCLE.read_text(encoding="utf-8-sig")
    ingress = INGRESS.read_text(encoding="utf-8-sig")
    managed_host = MANAGED_HOST.read_text(encoding="utf-8-sig")
    handoff = HANDOFF.read_text(encoding="utf-8-sig")

    req("public sealed class RuntimeHostIngress" in ingress, "RuntimeHostIngress missing")
    req("return _runtimeHost.AdmitTargetNeutralHandoff(handoff);" in ingress, "ingress delegation changed")
    req("public TargetNeutralLoweringHandoff AdmitTargetNeutralHandoff(TargetNeutralLoweringHandoff handoff)" in managed_host, "managed admission missing")
    req("public sealed record TargetNeutralLoweringHandoff" in handoff, "managed handoff missing")

    program_ingress_refs = program.count("RuntimeHostIngress")
    program_handoff_refs = program.count("TargetNeutralLoweringHandoff")
    lifecycle_ingress_refs = lifecycle.count("RuntimeHostIngress")
    ingress_lifecycle_refs = ingress.count("RuntimeHostLifecycle")

    req(program_ingress_refs == 0, f"Program.cs wired ingress before integration contract: {program_ingress_refs}")
    req(program_handoff_refs == 0, f"Program.cs handles handoff before integration contract: {program_handoff_refs}")
    req(lifecycle_ingress_refs == 0, f"lifecycle coupled to ingress before contract: {lifecycle_ingress_refs}")
    req(ingress_lifecycle_refs == 0, f"ingress coupled to lifecycle before contract: {ingress_lifecycle_refs}")

    host_surface = program + "\n" + lifecycle + "\n" + ingress
    external_refs = sum(host_surface.count(token) for token in EXTERNAL_TOKENS)
    execution_refs = sum(host_surface.count(token) for token in EXECUTION_TOKENS)
    req(external_refs == 0, f"host external transport references found: {external_refs}")
    req(execution_refs == 0, f"host execution-dispatch references found: {execution_refs}")

    build = run("dotnet", "build", str(HOST_PROJ), "-c", "Release", "--nologo")
    req(build.returncode == 0, "managed host build failed:\n" + build.stdout + "\n" + build.stderr)
    print("P12_5_RCV_26_HOST_BUILD=PASS")

    state = data["integration_state"]
    req(state["runtime_host_ingress_implemented"] is True, "ingress implementation state changed")
    req(state["program_constructs_ingress"] is False, "program integration selected early")
    req(state["program_admits_handoff"] is False, "program handoff admission selected early")
    req(state["lifecycle_references_ingress"] is False, "lifecycle integration selected early")
    req(state["ingress_references_lifecycle"] is False, "ingress lifecycle coupling selected early")
    req(state["host_external_payload_ingress"] is False, "external payload ingress selected")
    req(state["cross_runtime_transport"] == "DEFERRED_NO_TRANSPORT_AUTHORIZED", "cross-runtime transport changed")
    req(state["external_serialization"] == "UNSELECTED", "external serialization changed")
    req(state["execution_dispatch"] == "DEFERRED", "execution dispatch changed")

    auth = data["authority"]
    req(auth["language_semantics"] == "CANONICAL_AIR", "semantic authority changed")
    req(auth["managed_validation_owner"] == "ApexForge.Runtime.ManagedRuntimeHost", "validation owner changed")
    req(auth["ingress_owner"] == "ApexForge.Runtime.Host", "ingress owner changed")
    req(auth["host_program_role"] == "ORCHESTRATION_AND_LIFECYCLE_SHELL", "host role changed")
    req(auth["integration_census_defines_semantics"] is False, "census gained semantic authority")
    req(auth["integration_census_selects_transport"] is False, "census selected transport")
    req(auth["integration_census_executes"] is False, "census selected execution")

    print("P12_5_RCV_26_PROFILE=apexforge.p12.managed-host-ingress-integration-census/v1")
    print(f"P12_5_RCV_26_PROGRAM_INGRESS_REFERENCE_COUNT={program_ingress_refs}")
    print(f"P12_5_RCV_26_PROGRAM_HANDOFF_REFERENCE_COUNT={program_handoff_refs}")
    print(f"P12_5_RCV_26_LIFECYCLE_INGRESS_REFERENCE_COUNT={lifecycle_ingress_refs}")
    print(f"P12_5_RCV_26_INGRESS_LIFECYCLE_REFERENCE_COUNT={ingress_lifecycle_refs}")
    print(f"P12_5_RCV_26_EXTERNAL_TRANSPORT_REFERENCE_COUNT={external_refs}")
    print(f"P12_5_RCV_26_EXECUTION_DISPATCH_REFERENCE_COUNT={execution_refs}")
    print("P12_5_RCV_26_RUNTIME_HOST_INGRESS_IMPLEMENTED=True")
    print("P12_5_RCV_26_HOST_PROGRAM_WIRING=False")
    print("P12_5_RCV_26_LIFECYCLE_COUPLING=False")
    print("P12_5_RCV_26_EXTERNAL_SERIALIZATION=UNSELECTED")
    print("P12_5_RCV_26_CROSS_RUNTIME_TRANSPORT=DEFERRED_NO_TRANSPORT_AUTHORIZED")
    print("P12_5_RCV_26_EXECUTION_DISPATCH=DEFERRED")
    print("P12_5_RCV_26_MANAGED_HOST_INGRESS_INTEGRATION_CENSUS=PASS")
    print("P12_5_RCV_26_NEXT=P12.5-RCV-27_MANAGED_HOST_PROGRAM_INTEGRATION_CONTRACT")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
