from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HEADER = ROOT / "runtimes/native/include/apexforge_native.h"
LIFECYCLE = ROOT / "docs/p12/P12_3E_NATIVE_EXPORT_RESOURCE_LIFECYCLE_CONTRACT.json"
ABI = ROOT / "docs/p12/P12_3C_WIN_X64_MANAGED_NATIVE_ABI_MEMORY_OWNERSHIP_CONTRACT.json"
MANAGED = ROOT / "runtimes/dotnet/ApexForge.Runtime/ManagedNativeAbi.cs"


def require(value: bool, message: str) -> None:
    if not value:
        raise AssertionError(message)


def main() -> int:
    header = HEADER.read_text(encoding="utf-8")
    lifecycle = json.loads(LIFECYCLE.read_text(encoding="utf-8"))
    abi = json.loads(ABI.read_text(encoding="utf-8"))
    managed = MANAGED.read_text(encoding="utf-8")
    require(lifecycle["profile_id"] == "apexforge.win-x64-native-export-lifecycle/v1", "P12.3E lifecycle profile changed")
    require(abi["profile_id"] == "apexforge.win-x64-managed-native-abi/v1", "P12.3C ABI profile changed")
    require("#ifndef APEXFORGE_NATIVE_H" in header and "#define APEXFORGE_NATIVE_H" in header, "header guard missing")
    require("#include <stdint.h>" in header, "fixed-width integer declaration missing")
    require("#ifdef __cplusplus" in header and "extern \"C\" {" in header, "C-linkage guard missing")
    require("typedef int32_t apexforge_status_t;" in header, "I32 status declaration changed")
    require("typedef void* apexforge_handle_t;" in header, "opaque handle declaration changed")
    require("#define APEXFORGE_STATUS_OK ((apexforge_status_t)0)" in header, "zero-success declaration changed")
    require("apexforge_status_t apexforge_release_handle(apexforge_handle_t handle);" in header, "handle release declaration changed")
    require("apexforge_status_t apexforge_release_buffer(void* data, uint64_t length);" in header, "buffer release declaration changed")
    symbols = re.findall(r"^apexforge_status_t\s+(apexforge_[a-z0-9_]+)\s*\(", header, flags=re.MULTILINE)
    require(symbols == ["apexforge_release_handle", "apexforge_release_buffer"], "native declaration export set changed")
    require(lifecycle["exports"][0]["symbol"] == "apexforge_release_handle", "P12.3E handle export changed")
    require(lifecycle["exports"][1]["symbol"] == "apexforge_release_buffer", "P12.3E buffer export changed")
    require(lifecycle["status"]["representation"] == "I32" and lifecycle["status"]["success"] == 0, "P12.3E status model changed")
    require(lifecycle["lifecycle"]["cross_runtime_free"] == "FORBIDDEN", "P12.3E ownership invariant changed")
    require("[LibraryImport(LibraryName, EntryPoint = \"apexforge_release_handle\")]" in managed, "managed handle binding disagrees with header")
    require("[LibraryImport(LibraryName, EntryPoint = \"apexforge_release_buffer\")]" in managed, "managed buffer binding disagrees with header")
    require("internal static partial int ReleaseHandle(nint handle);" in managed, "managed handle signature disagrees with header")
    require("internal static partial int ReleaseBuffer(nint data, ulong length);" in managed, "managed buffer signature disagrees with header")
    forbidden = ("__declspec", "__attribute__", "__cdecl", "__stdcall", "WINAPI", "malloc(", "calloc(", "realloc(", "free(", "new ", "delete ", "struct ", "class ")
    require(not any(item in header for item in forbidden), "compiler-specific or implementation surface entered declaration header")
    require("apexforge_create_" not in header and "apexforge_retain_" not in header and "apexforge_clone_" not in header, "resource creation or retention surface entered P12.3F")
    require("(*" not in header, "callback/function-pointer ABI entered P12.3F")
    print("P12_3F_HEADER=runtimes/native/include/apexforge_native.h")
    print("P12_3F_ABI_PROFILE=apexforge.win-x64-managed-native-abi/v1")
    print("P12_3F_LIFECYCLE_PROFILE=apexforge.win-x64-native-export-lifecycle/v1")
    print("P12_3F_STATUS_TYPE=int32_t")
    print("P12_3F_HANDLE_TYPE=void*")
    print("P12_3F_BUFFER_LENGTH_TYPE=uint64_t")
    print("P12_3F_C_LINKAGE_GUARD=True")
    print("P12_3F_DECLARED_EXPORT_SET=apexforge_release_handle,apexforge_release_buffer")
    print("P12_3F_COMPILER_SPECIFIC_ATTRIBUTES=False")
    print("P12_3F_NATIVE_IMPLEMENTATION_PRESENT=False")
    print("P12_3F_CREATION_EXPORTS_PRESENT=False")
    print("P12_3F_CALLBACK_ABI_PRESENT=False")
    print("P12_3F_NATIVE_COMPILER_REQUIRED=False")
    print("P12_3F_MANAGED_HEADER_SIGNATURE_ALIGNMENT=PASS")
    print("P12_3F_NATIVE_ABI_DECLARATION_HEADER_SURFACE=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
