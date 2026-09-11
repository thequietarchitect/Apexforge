from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs/p12/P12_0D_CSHARP_DOTNET_MANAGED_RUNTIME_OWNERSHIP_BOUNDARY.json"

def require(value: bool, message: str) -> None:
    if not value:
        raise AssertionError(message)

def main() -> int:
    data = json.loads(DOC.read_text(encoding="utf-8"))
    require(data["schema"] == 1, "schema changed")
    require(data["stage"] == "P12.0D", "stage changed")
    require(data["identity"]["id"] == "CSHARP_DOTNET_MANAGED_RUNTIME", "runtime identity changed")
    require(data["identity"]["classification"] == "FIRST_CLASS_EXECUTION_TARGET", "runtime classification changed")
    require(data["planned_layout"]["project_file"] == "runtimes/dotnet/ApexForge.Runtime/ApexForge.Runtime.csproj", "managed runtime project path changed")
    require(data["canonical_input"]["verified_air_owner"] == "air.model.VerifiedAIRProgram", "Verified AIR ownership changed")
    require(data["canonical_input"]["execution_plan_owner"] == "workflow.air_runner.RegistryExecutionPlan", "execution-plan ownership changed")
    require(data["visual_studio_boundary"]["runtime_owner"] is False, "Visual Studio became runtime owner")
    require(data["visual_studio_boundary"]["may_define_semantics"] is False, "Visual Studio acquired semantic ownership")
    require(data["visual_studio_boundary"]["reverse_dependency_from_runtime_forbidden"] is True, "runtime may depend on Visual Studio")
    require(data["python_reference_boundary"]["replaced_by_managed_runtime"] is False, "Python reference runtime silently replaced")
    require(data["python_reference_boundary"]["required_as_managed_runtime_production_dependency"] is False, "managed runtime improperly depends on Python runtime")
    require(data["native_boundary"]["relationship"] == "SIBLING_TARGET", "native target relationship changed")
    require(data["native_boundary"]["managed_runtime_owns_native_backend"] is False, "managed runtime acquired native ownership")
    require("ApexForge grammar" in data["does_not_own"], "grammar exclusion missing")
    require("native ABI" in data["does_not_own"], "native ABI exclusion missing")
    require("PolyPlane" in data["does_not_own"], "PolyPlane exclusion missing")
    require("NO_GENERIC_FFI_BEFORE_CONCRETE_INTEROP_CONTRACT" in data["invariants"], "FFI boundary missing")
    require("POLYPLANE_REMAINS_DEFERRED" in data["invariants"], "PolyPlane deferral missing")
    print("P12_0D_MANAGED_RUNTIME_IDENTITY=CSHARP_DOTNET_MANAGED_RUNTIME")
    print("P12_0D_MANAGED_RUNTIME_FIRST_CLASS_TARGET=PASS")
    print("P12_0D_CANONICAL_INPUT_VERIFIED_AIR=air.model.VerifiedAIRProgram")
    print("P12_0D_CANONICAL_EXECUTION_PLAN=workflow.air_runner.RegistryExecutionPlan")
    print("P12_0D_VISUAL_STUDIO_RUNTIME_OWNER=False")
    print("P12_0D_PYTHON_REFERENCE_RUNTIME_REPLACED=False")
    print("P12_0D_NATIVE_BACKEND_RELATIONSHIP=SIBLING_TARGET")
    print("P12_0D_GENERIC_FFI=DEFERRED_TO_CONCRETE_INTEROP_CONTRACT")
    print("P12_0D_POLYPLANE=DEFERRED")
    print("P12_0D_CSHARP_DOTNET_MANAGED_RUNTIME_OWNERSHIP_BOUNDARY=PASS")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
