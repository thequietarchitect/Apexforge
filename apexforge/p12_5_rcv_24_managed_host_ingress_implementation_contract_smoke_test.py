from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "apexforge/p12_5_rcv_24_managed_host_ingress_implementation_contract.json"
RCV23 = ROOT / "apexforge/p12_5_rcv_23_managed_host_ingress_implementation_census_smoke_test.py"
FUTURE_INGRESS = ROOT / "runtimes/dotnet/ApexForge.Runtime.Host/RuntimeHostIngress.cs"
MANAGED_HOST = ROOT / "runtimes/dotnet/ApexForge.Runtime/ManagedRuntimeHost.cs"
HANDOFF = ROOT / "runtimes/dotnet/ApexForge.Runtime/TargetNeutralLoweringHandoff.cs"

def req(c, m):
    if not c:
        raise AssertionError(m)

def run(*args):
    return subprocess.run(list(args), cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def main():
    print("=== P12.5-RCV-24 MANAGED HOST INGRESS IMPLEMENTATION CONTRACT ===")
    for p in (CONTRACT, RCV23, MANAGED_HOST, HANDOFF):
        req(p.exists(), f"missing required file: {p}")

    cp = run(sys.executable, str(RCV23))
    req(cp.returncode == 0, "RCV-23 regression failed:\n" + cp.stdout + "\n" + cp.stderr)
    print("P12_5_RCV_24_RCV23_REGRESSION=PASS")

    data = json.loads(CONTRACT.read_text(encoding="utf-8-sig"))
    req(data["profile"] == "apexforge.p12.managed-host-ingress-implementation-contract/v1", "profile changed")
    req(data["predecessor"]["stage"] == "P12.5-RCV-23", "predecessor changed")

    hist = data["historical_evidence"]
    req(hist["host_ingress_family"] == "IN_PROCESS_API", "historical ingress family changed")
    req(hist["future_ingress_type"] == "ApexForge.Runtime.Host.RuntimeHostIngress", "future ingress type changed")
    for key in (
        "historical_implementation_body_recovered",
        "historical_constructor_shape_recovered",
        "historical_method_name_recovered",
        "historical_lifecycle_coupling_recovered",
        "historical_identity_claim",
    ):
        req(hist[key] is False, f"unsupported historical identity/detail claim introduced: {key}")

    d = data["decision"]
    req(d["type"] == "ApexForge.Runtime.Host.RuntimeHostIngress", "ingress type changed")
    req(d["owner_project"] == "ApexForge.Runtime.Host", "ingress owner changed")
    req(d["representation"] == "SEALED_IN_PROCESS_ADAPTER", "representation changed")
    req(d["constructor_dependency"] == "ApexForge.Runtime.ManagedRuntimeHost", "constructor dependency changed")
    req(d["constructor_null_guard"] is True, "constructor null guard removed")
    req(d["method"] == "Admit", "method name changed")
    req(d["method_input"] == "ApexForge.Runtime.TargetNeutralLoweringHandoff", "method input changed")
    req(d["method_output"] == "ApexForge.Runtime.TargetNeutralLoweringHandoff", "method output changed")
    req(d["method_behavior"] == "DELEGATE_TO_ManagedRuntimeHost.AdmitTargetNeutralHandoff", "delegation behavior changed")
    req(d["returns_delegate_result"] is True, "delegate result return changed")
    req(d["duplicates_validation"] is False, "duplicate validation selected")
    req(d["lifecycle_coupling"] == "NONE_IN_INITIAL_IMPLEMENTATION", "lifecycle coupling selected too early")
    req(d["external_serialization"] == "UNSELECTED", "serialization selected")
    req(d["cross_runtime_transport"] == "DEFERRED_NO_TRANSPORT_AUTHORIZED", "cross-runtime transport changed")
    req(d["execution_dispatch"] == "DEFERRED", "execution dispatch changed")

    managed_host = MANAGED_HOST.read_text(encoding="utf-8-sig")
    req("AdmitTargetNeutralHandoff" in managed_host, "managed admission delegate target missing")
    req("handoff.Validate();" in managed_host, "managed validation target missing")
    req("public sealed record TargetNeutralLoweringHandoff" in HANDOFF.read_text(encoding="utf-8-sig"), "handoff type missing")

    if FUTURE_INGRESS.exists():
        req((ROOT / "apexforge/p12_5_rcv_25_managed_host_ingress_implementation_foundation.json").exists(), "later ingress implementation lacks RCV-25 lineage")

    a = data["authority"]
    req(a["language_semantics"] == "CANONICAL_AIR", "semantic authority changed")
    req(a["validation_owner"] == "ApexForge.Runtime.ManagedRuntimeHost", "validation owner changed")
    req(a["ingress_owner"] == "ApexForge.Runtime.Host", "ingress owner changed")
    for key in (
        "ingress_defines_language_semantics",
        "ingress_executes",
        "ingress_lowers",
        "ingress_reinterprets",
        "ingress_selects_transport",
        "ingress_calls_native_abi",
    ):
        req(a[key] is False, f"ingress authority widened: {key}")

    c = data["constraints"]
    for key, value in c.items():
        req(value is True, f"constraint weakened: {key}")

    req(data["implementation"] == "DEFERRED", "implementation selected during contract gate")

    print("P12_5_RCV_24_PROFILE=apexforge.p12.managed-host-ingress-implementation-contract/v1")
    print("P12_5_RCV_24_INGRESS_TYPE=ApexForge.Runtime.Host.RuntimeHostIngress")
    print("P12_5_RCV_24_REPRESENTATION=SEALED_IN_PROCESS_ADAPTER")
    print("P12_5_RCV_24_CONSTRUCTOR_DEPENDENCY=ApexForge.Runtime.ManagedRuntimeHost")
    print("P12_5_RCV_24_METHOD=Admit")
    print("P12_5_RCV_24_METHOD_BEHAVIOR=DELEGATE_TO_ManagedRuntimeHost.AdmitTargetNeutralHandoff")
    print("P12_5_RCV_24_DUPLICATES_VALIDATION=False")
    print("P12_5_RCV_24_LIFECYCLE_COUPLING=NONE_IN_INITIAL_IMPLEMENTATION")
    print("P12_5_RCV_24_EXTERNAL_SERIALIZATION=UNSELECTED")
    print("P12_5_RCV_24_CROSS_RUNTIME_TRANSPORT=DEFERRED_NO_TRANSPORT_AUTHORIZED")
    print("P12_5_RCV_24_EXECUTION_DISPATCH=DEFERRED")
    print("P12_5_RCV_24_IMPLEMENTATION=DEFERRED")
    print("P12_5_RCV_24_MANAGED_HOST_INGRESS_IMPLEMENTATION_CONTRACT=PASS")
    print("P12_5_RCV_24_NEXT=P12.5-RCV-25_MANAGED_HOST_INGRESS_IMPLEMENTATION_FOUNDATION")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
