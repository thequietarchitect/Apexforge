from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs/p12/P12_0E_NATIVE_BACKEND_OWNERSHIP_BOUNDARY.json"

def require(value: bool, message: str) -> None:
    if not value:
        raise AssertionError(message)

def main() -> int:
    data = json.loads(DOC.read_text(encoding="utf-8"))
    require(data["schema"] == 1, "schema changed")
    require(data["stage"] == "P12.0E", "stage changed")
    require(data["identity"]["id"] == "NATIVE_BACKEND", "native backend identity changed")
    require(data["identity"]["classification"] == "FIRST_CLASS_EXECUTION_TARGET", "native backend classification changed")
    require(data["identity"]["implementation_technology"] == "UNSELECTED", "toolchain prematurely selected")
    require(data["planned_layout"]["package_root"] == "apexforge/native_backend", "native backend package path changed")
    require(data["canonical_input"]["verified_air_owner"] == "air.model.VerifiedAIRProgram", "Verified AIR ownership changed")
    require(data["managed_runtime_boundary"]["relationship"] == "SIBLING_TARGET", "managed runtime relationship changed")
    require(data["managed_runtime_boundary"]["native_backend_owns_managed_runtime"] is False, "native backend acquired managed runtime ownership")
    require(data["managed_runtime_boundary"]["managed_runtime_owns_native_backend"] is False, "managed runtime acquired native backend ownership")
    require(data["python_reference_boundary"]["native_backend_replaces_python_runtime"] is False, "Python runtime silently replaced")
    require(data["editor_boundary"]["visual_studio_runtime_or_backend_owner"] is False, "Visual Studio became native backend owner")
    require(data["toolchain_policy"]["llvm_required"] is False, "LLVM prematurely required")
    require(data["toolchain_policy"]["compiler_backend"] == "UNSELECTED", "compiler backend prematurely selected")
    require(data["abi_policy"]["state"] == "DEFERRED_TO_P12_3_CONCRETE_ABI_CONTRACT", "ABI boundary changed")
    require(data["abi_policy"]["generic_ffi"] == "NOT_INTRODUCED", "generic FFI prematurely introduced")
    require(data["optimization_policy"]["semantic_owner"] is False, "native backend acquired optimizer semantic ownership")
    require("PolyPlane" in data["does_not_own"], "PolyPlane exclusion missing")
    require("NO_GENERIC_FFI_BEFORE_CONCRETE_INTEROP_CONTRACT" in data["invariants"], "FFI invariant missing")
    require("POLYPLANE_REMAINS_DEFERRED" in data["invariants"], "PolyPlane deferral missing")
    print("P12_0E_NATIVE_BACKEND_FIRST_CLASS_TARGET=PASS")
    print("P12_0E_CANONICAL_INPUT_VERIFIED_AIR=air.model.VerifiedAIRProgram")
    print("P12_0E_MANAGED_RUNTIME_RELATIONSHIP=SIBLING_TARGET")
    print("P12_0E_PYTHON_REFERENCE_RUNTIME_REPLACED=False")
    print("P12_0E_VISUAL_STUDIO_BACKEND_OWNER=False")
    print("P12_0E_TOOLCHAIN=UNSELECTED")
    print("P12_0E_LLVM_REQUIRED=False")
    print("P12_0E_ABI=DEFERRED_TO_P12_3_CONCRETE_ABI_CONTRACT")
    print("P12_0E_GENERIC_FFI=NOT_INTRODUCED")
    print("P12_0E_OPTIMIZER_SEMANTIC_OWNER=False")
    print("P12_0E_POLYPLANE=DEFERRED")
    print("P12_0E_NATIVE_BACKEND_OWNERSHIP_BOUNDARY=PASS")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
