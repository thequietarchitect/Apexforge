from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs/p12/P12_0C_EXECUTION_TARGET_ARCHITECTURE_CONTRACT.json"

def require(value: bool, message: str) -> None:
    if not value:
        raise AssertionError(message)

def main() -> int:
    data = json.loads(DOC.read_text(encoding="utf-8"))
    require(data["schema"] == 1, "schema changed")
    require(data["stage"] == "P12.0C", "stage changed")
    require(data["canonical_ownership"]["rule"] == "execution targets consume canonical semantics and MUST NOT redefine language meaning", "canonical ownership changed")
    targets = {item["id"]: item for item in data["targets"]}
    require(set(targets) == {"PYTHON_REFERENCE_RUNTIME", "CSHARP_DOTNET_MANAGED_RUNTIME", "NATIVE_BACKEND"}, "target inventory changed")
    require(targets["PYTHON_REFERENCE_RUNTIME"]["status"] == "EXISTING", "Python reference runtime status changed")
    require(targets["CSHARP_DOTNET_MANAGED_RUNTIME"]["status"] == "PLANNED_P12", "managed runtime status changed")
    require(targets["NATIVE_BACKEND"]["status"] == "ACTIVE_P12_DESIGN", "native backend status changed")
    require(all(not item["may_define_language_semantics"] for item in targets.values()), "target acquired semantic ownership")
    require(data["editor_boundary"]["is_csharp_runtime"] is False, "Visual Studio incorrectly became runtime owner")
    require(data["managed_runtime_contract"]["first_class_target"] is True, "managed runtime ceased to be first class")
    require(data["managed_runtime_contract"]["separate_from_visual_studio"] is True, "managed runtime merged with Visual Studio")
    require(data["native_backend_contract"]["first_class_target"] is True, "native backend ceased to be first class")
    require(data["reference_runtime_contract"]["replacement_by_p12"] is False, "Python reference runtime was silently replaced")
    require(data["deferred"]["polyplane"] == "DEFERRED", "PolyPlane entered P12.0C")
    print("P12_0C_CANONICAL_SEMANTICS_SINGLE_OWNER=PASS")
    print("P12_0C_PYTHON_REFERENCE_RUNTIME=EXISTING")
    print("P12_0C_CSHARP_DOTNET_MANAGED_RUNTIME=PLANNED_P12")
    print("P12_0C_NATIVE_BACKEND=ACTIVE_P12_DESIGN")
    print("P12_0C_VISUAL_STUDIO_IS_RUNTIME=False")
    print("P12_0C_POLYPLANE=DEFERRED")
    print("P12_0C_EXECUTION_TARGET_ARCHITECTURE_CONTRACT=PASS")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
