from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/p12/P12_4G_D_MANAGED_PRODUCTION_DLL_BINDING_EXECUTION.json"
MANAGED = ROOT / "runtimes/dotnet/ApexForge.Runtime/ManagedNativeAbi.cs"
PROJECT = ROOT / "runtimes/dotnet/ApexForge.Runtime/ApexForge.Runtime.csproj"
HEADER = ROOT / "runtimes/native/include/apexforge_native.h"
DEF = ROOT / "runtimes/native/link/apexforge_native.def"

def require(value: bool, message: str) -> None:
    if not value:
        raise AssertionError(message)

def main() -> int:
    data = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    managed = MANAGED.read_text(encoding="utf-8")
    project = PROJECT.read_text(encoding="utf-8")
    header = HEADER.read_text(encoding="utf-8")
    def_lines = [line.strip() for line in DEF.read_text(encoding="utf-8").splitlines() if line.strip()]
    require(data["profile_id"] == "apexforge.win-x64-managed-production-native-binding-execution/v1", "profile changed")
    require(data["predecessor_commit"] == "280b40a000a7ccd8fe434eb5dd10cf135155b265", "predecessor changed")
    require(data["managed"]["namespace"] == "ApexForge.Runtime", "namespace changed")
    require(data["managed"]["binding_type"] == "ManagedNativeAbi", "binding type changed")
    require(data["managed"]["target_framework"] == "net10.0", "target framework changed")
    require(data["managed"]["logical_library"] == "apexforge_native", "logical library changed")
    require(data["managed"]["mechanism"] == "LibraryImport", "binding mechanism changed")
    require(data["managed"]["custom_dll_resolver_required"] is False, "resolver requirement changed")
    require(data["managed"]["test_access_mechanism"] == "REFLECTION_TO_INTERNAL_GENERATED_STUBS", "test access changed")
    require(re.search(r'\b(?:const|static\s+readonly)\s+string\s+LibraryName\s*=\s*"apexforge_native"\s*;', managed) is not None, "managed library identity changed")
    entries = sorted(re.findall(r'\[LibraryImport\(\s*LibraryName\s*,\s*EntryPoint\s*=\s*"([^"]+)"\s*\)\]', managed))
    expected = ["apexforge_release_buffer", "apexforge_release_handle"]
    require(entries == expected, "managed entry-point set changed")
    require("<TargetFramework>net10.0</TargetFramework>" in project, "managed target changed")
    header_exports = sorted(re.findall(r"^apexforge_status_t\s+(apexforge_[a-z0-9_]+)\s*\(", header, re.MULTILINE))
    require(header_exports == expected, "public header export set changed")
    require(def_lines == ["LIBRARY apexforge_native", "EXPORTS", "apexforge_release_handle", "apexforge_release_buffer"], "DEF surface changed")
    require(data["native"]["observed_whole_dll_sha256"] == "ED1708825B13B6C23D1017A933EAAB1B681BD5D6D686C28525B9EC403B9A42A8", "native characterization identity changed")
    require(data["native"]["export_count"] == 2 and data["native"]["import_dll_count"] == 0, "native surface evidence changed")
    execution = data["execution"]
    require(execution["actual_libraryimport_invoked"] is True, "actual binding execution not recorded")
    require(execution["handle_null_rejected"] is True and execution["buffer_null_rejected"] is True, "null rejection evidence changed")
    require(execution["handle_unknown_rejected"] is True and execution["buffer_unknown_rejected"] is True, "unknown rejection evidence changed")
    require(execution["observed_status_numbers_are_public_contract"] is False, "private status numbers became public contract")
    require(execution["required_public_result"] == "NONZERO_OPAQUE_FAILURE", "public result contract changed")
    require(execution["live_resource_successful_release_executed"] is False, "live-resource success overclaimed")
    require(execution["live_resource_successful_release_deferred_reason"] == "PUBLIC_CREATION_EXPORTS_DEFERRED", "live-resource deferral changed")
    require(data["scope"]["public_creation_exports"] is False, "creation ABI expanded")
    require(data["scope"]["allocator_family"] == "UNSELECTED", "allocator selected early")
    require(data["scope"]["generic_ffi"] is False and data["scope"]["runtime_host_produced"] is False, "stage scope expanded")
    require(data["scope"]["native_backend_semantic_authority"] is False, "native backend gained semantic authority")
    require(data["artifact_policy"]["native_dll_tracked_in_git"] is False, "native binary tracking changed")
    require(data["artifact_policy"]["managed_probe_tracked_in_git"] is False, "probe tracking changed")
    require(data["artifact_policy"]["execution_artifacts_temporary"] is True, "temporary artifact policy changed")
    print("P12_4G_D_PROFILE_ID=apexforge.win-x64-managed-production-native-binding-execution/v1")
    print("P12_4G_D_ACTUAL_LIBRARYIMPORT_INVOKED=True")
    print("P12_4G_D_NULL_REJECTIONS_PROVEN=True")
    print("P12_4G_D_UNKNOWN_REJECTIONS_PROVEN=True")
    print("P12_4G_D_STATUS_NUMBERS_PUBLIC_CONTRACT=False")
    print("P12_4G_D_LIVE_RESOURCE_SUCCESSFUL_RELEASE=DEFERRED")
    print("P12_4G_D_PUBLIC_CREATION_EXPORTS=False")
    print("P12_4G_D_NATIVE_DLL_TRACKED_IN_GIT=False")
    print("P12_4G_D_MANAGED_PRODUCTION_DLL_BINDING_EXECUTION_EVIDENCE=PASS")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
