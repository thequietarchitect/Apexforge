from __future__ import annotations
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

PROJECT = ROOT / "runtimes/dotnet/ApexForge.Runtime/ApexForge.Runtime.csproj"
IDENTITY = ROOT / "runtimes/dotnet/ApexForge.Runtime/RuntimeIdentity.cs"
CONTRACT = ROOT / "runtimes/dotnet/ApexForge.Runtime/CanonicalExecutionContract.cs"
HOST = ROOT / "runtimes/dotnet/ApexForge.Runtime/ManagedRuntimeHost.cs"

def require(value: bool, message: str) -> None:
    if not value:
        raise AssertionError(message)

def main() -> int:
    project = ET.parse(PROJECT).getroot()
    props = {child.tag: (child.text or "") for group in project.findall("PropertyGroup") for child in group}
    require(props.get("TargetFramework") == "net10.0", "managed target framework changed")
    require(props.get("AssemblyName") == "ApexForge.Runtime", "managed assembly identity changed")
    require(props.get("Deterministic") == "true", "deterministic build contract changed")
    require(not project.findall(".//ProjectReference"), "managed runtime gained project dependency")
    identity = IDENTITY.read_text(encoding="utf-8")
    contract = CONTRACT.read_text(encoding="utf-8")
    host = HOST.read_text(encoding="utf-8")
    managed_text = identity + contract + host
    require("CSHARP_DOTNET_MANAGED_RUNTIME" in identity, "managed runtime identity missing")
    require("air.model.VerifiedAIRProgram" in identity, "Verified AIR ownership marker missing")
    require("workflow.air_runner.RegistryExecutionPlan" in identity, "execution-plan ownership marker missing")
    require("DefinesLanguageSemantics = false" in identity, "managed runtime semantic-ownership guard missing")
    require("IsVisualStudioIntegration = false" in identity, "Visual Studio isolation guard missing")
    require("ApexForge.VisualStudio" not in managed_text, "managed runtime depends on Visual Studio identity")
    require("CanonicalExecutionContract" in contract, "canonical execution contract missing")
    require("ValidateContract" in host, "managed runtime host contract validation missing")
    from apexforge.native_backend import DEFAULT_NATIVE_BACKEND_IDENTITY
    native = DEFAULT_NATIVE_BACKEND_IDENTITY
    require(native.target_id == "NATIVE_BACKEND", "native backend identity changed")
    require(native.verified_air_owner == "air.model.VerifiedAIRProgram", "native Verified AIR ownership changed")
    require(native.managed_runtime_relationship == "SIBLING_TARGET", "native/managed relationship changed")
    require(native.compiler_backend == "UNSELECTED", "native compiler backend prematurely selected")
    require(native.llvm_required is False, "LLVM prematurely required")
    require(native.defines_language_semantics is False, "native backend acquired semantic ownership")
    require(native.is_contract_safe(), "native backend foundation contract failed")
    print("P12_1B_MANAGED_RUNTIME_PROJECT=PASS")
    print("P12_1B_MANAGED_RUNTIME_TARGET_FRAMEWORK=net10.0")
    print("P12_1B_MANAGED_RUNTIME_VISUAL_STUDIO_DEPENDENCY=False")
    print("P12_1B_MANAGED_RUNTIME_DEFINES_LANGUAGE_SEMANTICS=False")
    print("P12_1B_NATIVE_BACKEND_PACKAGE=PASS")
    print("P12_1B_NATIVE_BACKEND_MANAGED_RELATIONSHIP=SIBLING_TARGET")
    print("P12_1B_NATIVE_BACKEND_COMPILER=UNSELECTED")
    print("P12_1B_NATIVE_BACKEND_LLVM_REQUIRED=False")
    print("P12_1B_NATIVE_BACKEND_DEFINES_LANGUAGE_SEMANTICS=False")
    print("P12_1B_EXECUTION_TARGET_IMPLEMENTATION_FOUNDATIONS=PASS")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
