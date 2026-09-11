from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs/p12/P12_3E_NATIVE_EXPORT_RESOURCE_LIFECYCLE_CONTRACT.json"
ABI = ROOT / "docs/p12/P12_3C_WIN_X64_MANAGED_NATIVE_ABI_MEMORY_OWNERSHIP_CONTRACT.json"
MANAGED = ROOT / "runtimes/dotnet/ApexForge.Runtime/ManagedNativeAbi.cs"


def require(value: bool, message: str) -> None:
    if not value:
        raise AssertionError(message)


def main() -> int:
    data = json.loads(CONTRACT.read_text(encoding="utf-8"))
    abi = json.loads(ABI.read_text(encoding="utf-8"))
    managed = MANAGED.read_text(encoding="utf-8")
    require(data["profile_id"] == "apexforge.win-x64-native-export-lifecycle/v1", "native lifecycle profile changed")
    require(data["abi_profile"] == "apexforge.win-x64-managed-native-abi/v1", "ABI dependency changed")
    require(data["library"]["logical_name"] == "apexforge_native", "logical library name changed")
    require(data["library"]["export_names_exact"] is True, "export names are no longer exact")
    require(data["library"]["c_linkage_semantics"] is True, "C linkage requirement changed")
    require(data["library"]["cpp_name_mangling"] is False, "C++ name mangling entered ABI")
    require(data["status"]["representation"] == "I32", "native status representation changed")
    require(data["status"]["success"] == 0, "native success code changed")
    require(data["status"]["valid_resource_release_must_succeed"] is True, "valid native release may fail")
    require(data["status"]["exceptions_cross_boundary"] is False, "exceptions allowed across boundary")
    exports = {item["symbol"]: item for item in data["exports"]}
    require(set(exports) == {"apexforge_release_handle", "apexforge_release_buffer"}, "native export set changed")
    handle = exports["apexforge_release_handle"]
    buffer = exports["apexforge_release_buffer"]
    require(handle["parameters"] == ["OPAQUE_NATIVE_HANDLE"], "handle release signature changed")
    require(handle["ownership_effect"] == "ON_SUCCESS_CONSUMES_ONE_LIVE_NATIVE_HANDLE", "handle lifecycle changed")
    require(buffer["parameters"] == ["NATIVE_OWNED_BUFFER_POINTER", "U64_LENGTH"], "buffer release signature changed")
    require(buffer["ownership_effect"] == "ON_SUCCESS_CONSUMES_ONE_LIVE_NATIVE_BUFFER", "buffer lifecycle changed")
    require(data["lifecycle"]["managed_wrapper"] == "SAFEHANDLE", "managed lifecycle wrapper changed")
    require(data["lifecycle"]["release_count"] == "EXACTLY_ONE_SUCCESSFUL_RELEASE_PER_LIVE_RESOURCE", "release-count invariant changed")
    require(data["lifecycle"]["cross_runtime_free"] == "FORBIDDEN", "cross-runtime free allowed")
    require(data["lifecycle"]["managed_allocator_release"] == "FORBIDDEN", "managed allocator may release native resource")
    require(data["surface"]["creation_exports"] == "DEFERRED", "creation ABI entered P12.3E")
    require(data["surface"]["callbacks"] == "DEFERRED", "callback ABI entered P12.3E")
    require(data["surface"]["reverse_pinvoke"] == "DEFERRED", "reverse P/Invoke entered P12.3E")
    require(data["toolchain"]["native_compiler"] == "UNSELECTED", "native compiler selected in lifecycle contract")
    require(data["toolchain"]["native_implementation"] == "DEFERRED", "native implementation entered lifecycle contract")
    require(abi["errors"]["function_result"] == "I32_STATUS_CODE", "P12.3C status contract changed")
    require(abi["errors"]["success_code"] == 0, "P12.3C success code changed")
    require(abi["memory_ownership"]["cross_runtime_free"] == "FORBIDDEN", "P12.3C ownership contract changed")
    require("[LibraryImport(LibraryName, EntryPoint = \"apexforge_release_handle\")]" in managed, "managed handle import disagrees with native contract")
    require("[LibraryImport(LibraryName, EntryPoint = \"apexforge_release_buffer\")]" in managed, "managed buffer import disagrees with native contract")
    require("internal static partial int ReleaseHandle(nint handle);" in managed, "managed handle signature disagrees with native contract")
    require("internal static partial int ReleaseBuffer(nint data, ulong length);" in managed, "managed buffer signature disagrees with native contract")
    require(managed.count("[LibraryImport(") == 2, "unexpected managed native exports entered P12.3E baseline")
    print("P12_3E_PROFILE_ID=apexforge.win-x64-native-export-lifecycle/v1")
    print("P12_3E_ABI_PROFILE=apexforge.win-x64-managed-native-abi/v1")
    print("P12_3E_NATIVE_LIBRARY=apexforge_native")
    print("P12_3E_EXPORT_SET=apexforge_release_handle,apexforge_release_buffer")
    print("P12_3E_RELEASE_STATUS=I32_ZERO_SUCCESS")
    print("P12_3E_VALID_RESOURCE_RELEASE_MUST_SUCCEED=True")
    print("P12_3E_RELEASE_COUNT=EXACTLY_ONE_SUCCESSFUL_RELEASE_PER_LIVE_RESOURCE")
    print("P12_3E_CROSS_RUNTIME_FREE=FORBIDDEN")
    print("P12_3E_CREATION_EXPORTS=DEFERRED")
    print("P12_3E_CALLBACKS=DEFERRED")
    print("P12_3E_REVERSE_PINVOKE=DEFERRED")
    print("P12_3E_NATIVE_COMPILER=UNSELECTED")
    print("P12_3E_NATIVE_IMPLEMENTATION=DEFERRED")
    print("P12_3E_MANAGED_NATIVE_EXPORT_SIGNATURE_ALIGNMENT=PASS")
    print("P12_3E_NATIVE_EXPORT_RESOURCE_LIFECYCLE_CONTRACT=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
