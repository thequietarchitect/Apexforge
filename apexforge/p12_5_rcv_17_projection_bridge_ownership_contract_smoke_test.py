from __future__ import annotations
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "apexforge/p12_5_rcv_17_projection_bridge_ownership_contract.json"
RCV16 = ROOT / "apexforge/p12_5_rcv_16_target_neutral_handoff_projection_bridge_census_smoke_test.py"
LOWERING = ROOT / "apexforge/native_backend/target_neutral_lowering.py"
HANDOFF = ROOT / "runtimes/dotnet/ApexForge.Runtime/TargetNeutralLoweringHandoff.cs"
HOST = ROOT / "runtimes/dotnet/ApexForge.Runtime/ManagedRuntimeHost.cs"
HOST_PROJECT = ROOT / "runtimes/dotnet/ApexForge.Runtime.Host/ApexForge.Runtime.Host.csproj"

EXPECTED_FIELDS = [
    "Schema",
    "VerifiedAirFingerprint",
    "RoutingFingerprint",
    "EntryDirective",
    "DirectiveOwnerIds",
    "ProductFingerprint",
]

def req(c, m):
    if not c:
        raise AssertionError(m)

def run(*args):
    return subprocess.run(list(args), cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def main():
    print("=== P12.5-RCV-17 PROJECTION BRIDGE OWNERSHIP CONTRACT ===")
    for p in (CONTRACT, RCV16, LOWERING, HANDOFF, HOST, HOST_PROJECT):
        req(p.exists(), f"missing required file: {p}")

    cp = run(sys.executable, str(RCV16))
    req(cp.returncode == 0, "RCV-16 regression failed:\n" + cp.stdout + "\n" + cp.stderr)
    print("P12_5_RCV_17_RCV16_REGRESSION=PASS")

    data = json.loads(CONTRACT.read_text(encoding="utf-8-sig"))
    req(data["profile"] == "apexforge.p12.projection-bridge-ownership-contract/v1", "profile changed")
    req(data["predecessor"]["stage"] == "P12.5-RCV-16", "predecessor changed")

    own = data["ownership"]
    req(own["source_product_owner"] == "apexforge.native_backend", "source owner changed")
    req(own["projection_owner"] == "apexforge.native_backend", "projection owner changed")
    req(own["managed_handoff_owner"] == "ApexForge.Runtime", "managed handoff owner changed")
    req(own["managed_validation_owner"] == "ApexForge.Runtime", "managed validation owner changed")
    req(own["managed_admission_owner"] == "ApexForge.Runtime.ManagedRuntimeHost", "managed admission owner changed")
    req(own["host_shell_owner"] == "ApexForge.Runtime.Host", "host shell owner changed")
    req(own["language_semantic_authority"] == "CANONICAL_AIR", "semantic authority changed")

    bridge = data["bridge_contract"]
    req(bridge["direction"] == "PYTHON_PRODUCT_TO_MANAGED_HANDOFF", "bridge direction changed")
    for key in (
        "projection_is_semantic_authority",
        "projection_may_execute",
        "projection_may_lower",
        "projection_may_reinterpret",
        "projection_may_select_transport",
        "managed_runtime_may_reconstruct_source_objects",
    ):
        req(bridge[key] is False, f"ownership boundary weakened: {key}")
    req(bridge["managed_runtime_may_validate"] is True, "managed validation permission missing")
    req(bridge["managed_runtime_may_admit"] is True, "managed admission permission missing")

    req(data["boundary_fields"] == EXPECTED_FIELDS, "boundary fields changed")
    req("canonical_json" in data["not_crossing_boundary"], "canonical_json exclusion missing")
    req("RegistryExecutionPlanBinding object" in data["not_crossing_boundary"], "binding object exclusion missing")
    req("RegistryExecutionPlan object" in data["not_crossing_boundary"], "execution plan exclusion missing")
    req("VerifiedAIRProgram object" in data["not_crossing_boundary"], "Verified AIR exclusion missing")

    impl = data["implementation"]
    req(impl["projection_bridge"] == "DEFERRED", "bridge implementation selected too early")
    req(impl["projection_representation"] == "UNSELECTED", "bridge representation selected too early")
    req(impl["external_serialization"] == "UNSELECTED", "external serialization selected too early")
    req(impl["cross_runtime_transport"] == "UNSELECTED", "transport selected too early")

    lower = LOWERING.read_text(encoding="utf-8-sig")
    handoff = HANDOFF.read_text(encoding="utf-8-sig")
    host = HOST.read_text(encoding="utf-8-sig")

    req("class TargetNeutralLoweringProduct" in lower, "canonical source product missing")
    req("public sealed record TargetNeutralLoweringHandoff" in handoff, "managed handoff missing")
    req("AdmitTargetNeutralHandoff" in host, "managed admission missing")

    # Ownership contract only at this gate; accept the later RCV-19 projection.
    for rel in (
        "apexforge/native_backend/managed_handoff_projection.py",
        "apexforge/native_backend/target_neutral_handoff_projection.py",
        "apexforge/native_backend/managed_handoff_bridge.py",
    ):
        path = ROOT / rel
        if path.exists():
            req(rel == "apexforge/native_backend/managed_handoff_projection.py" and (ROOT / "apexforge/p12_5_rcv_19_projection_value_object_implementation_foundation.json").exists(), f"projection implementation lacks RCV-19 lineage: {rel}")

    print("P12_5_RCV_17_PROFILE=apexforge.p12.projection-bridge-ownership-contract/v1")
    print("P12_5_RCV_17_SOURCE_PRODUCT_OWNER=apexforge.native_backend")
    print("P12_5_RCV_17_PROJECTION_OWNER=apexforge.native_backend")
    print("P12_5_RCV_17_MANAGED_HANDOFF_OWNER=ApexForge.Runtime")
    print("P12_5_RCV_17_MANAGED_ADMISSION_OWNER=ApexForge.Runtime.ManagedRuntimeHost")
    print("P12_5_RCV_17_HOST_SHELL_OWNER=ApexForge.Runtime.Host")
    print("P12_5_RCV_17_LANGUAGE_SEMANTIC_AUTHORITY=CANONICAL_AIR")
    print("P12_5_RCV_17_PROJECTION_REPRESENTATION=UNSELECTED")
    print("P12_5_RCV_17_EXTERNAL_SERIALIZATION=UNSELECTED")
    print("P12_5_RCV_17_EXECUTION_DISPATCH=DEFERRED")
    print("P12_5_RCV_17_PROJECTION_BRIDGE_OWNERSHIP_CONTRACT=PASS")
    print("P12_5_RCV_17_NEXT=P12.5-RCV-18_PROJECTION_BRIDGE_REPRESENTATION_DECISION")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
