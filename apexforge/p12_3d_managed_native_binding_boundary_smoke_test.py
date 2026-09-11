from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs/p12/P12_3C_WIN_X64_MANAGED_NATIVE_ABI_MEMORY_OWNERSHIP_CONTRACT.json"
CSPROJ = ROOT / "runtimes/dotnet/ApexForge.Runtime/ApexForge.Runtime.csproj"
BINDING = ROOT / "runtimes/dotnet/ApexForge.Runtime/ManagedNativeAbi.cs"


def require(value: bool, message: str) -> None:
    if not value:
        raise AssertionError(message)


def main() -> int:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    project = CSPROJ.read_text(encoding="utf-8")
    source = BINDING.read_text(encoding="utf-8")
    require(contract["profile_id"] == "apexforge.win-x64-managed-native-abi/v1", "P12.3C profile changed")
    require(contract["memory_ownership"]["cross_runtime_free"] == "FORBIDDEN", "cross-runtime free contract changed")
    require(contract["memory_ownership"]["managed_handle_wrapper"] == "SAFEHANDLE_PLANNED_P12_3D", "SafeHandle delegation changed")
    require(contract["ffi"]["managed_binding_mechanism"] == "DEFERRED_TO_P12_3D", "P12.3D delegation changed")
    require("<AllowUnsafeBlocks>true</AllowUnsafeBlocks>" in project, "LibraryImport project support missing")
    require("internal static partial class ManagedNativeAbi" in source, "managed native ABI boundary missing")
    require("ProfileId = \"apexforge.win-x64-managed-native-abi/v1\"" in source, "ABI profile identity missing")
    require("LibraryName = \"apexforge_native\"" in source, "native logical library name missing")
    require("[LibraryImport(LibraryName, EntryPoint = \"apexforge_release_handle\")]" in source, "native handle release import missing")
    require("[LibraryImport(LibraryName, EntryPoint = \"apexforge_release_buffer\")]" in source, "native buffer release import missing")
    require("internal sealed class ApexForgeNativeSafeHandle : SafeHandle" in source, "opaque handle SafeHandle missing")
    require("internal sealed class ApexForgeNativeOwnedBufferHandle : SafeHandle" in source, "native buffer SafeHandle missing")
    require("ManagedNativeAbi.ReleaseHandle(handle)" in source, "opaque handle does not release through native creator")
    require("ManagedNativeAbi.ReleaseBuffer(handle, Length)" in source, "native-owned output does not release through native creator")
    require("OperatingSystem.IsWindows()" in source, "Windows host guard missing")
    require("RuntimeInformation.ProcessArchitecture != Architecture.X64" in source, "x64 host guard missing")
    require("IntPtr.Size != 8" in source, "64-bit pointer guard missing")
    forbidden = ("Marshal.FreeHGlobal", "Marshal.FreeCoTaskMem", "NativeMemory.Free", "GCHandle.Free", "DllImport(")
    require(not any(item in source for item in forbidden), "cross-runtime allocator or alternate binding mechanism entered boundary")
    require("unsafe " not in source, "raw unsafe pointer implementation entered managed boundary")
    require("UnmanagedCallersOnly" not in source, "reverse P/Invoke entered P12.3D")
    require("delegate*" not in source, "function-pointer callback ABI entered P12.3D")
    print("P12_3D_PROFILE_ID=apexforge.win-x64-managed-native-abi/v1")
    print("P12_3D_BINDING_MECHANISM=LibraryImport")
    print("P12_3D_NATIVE_LIBRARY_NAME=apexforge_native")
    print("P12_3D_OPAQUE_HANDLE_WRAPPER=SafeHandle")
    print("P12_3D_NATIVE_OUTPUT_BUFFER_WRAPPER=SafeHandle")
    print("P12_3D_RELEASE_HANDLE_ENTRYPOINT=apexforge_release_handle")
    print("P12_3D_RELEASE_BUFFER_ENTRYPOINT=apexforge_release_buffer")
    print("P12_3D_HOST_GUARD=WINDOWS_X64_64BIT")
    print("P12_3D_CROSS_RUNTIME_FREE=FORBIDDEN")
    print("P12_3D_CALLBACKS=NOT_INTRODUCED")
    print("P12_3D_REVERSE_PINVOKE=NOT_INTRODUCED")
    print("P12_3D_RUNTIME_NATIVE_LIBRARY_LOAD_ATTEMPTED=False")
    print("P12_3D_NATIVE_LIBRARY_REQUIRED_FOR_BUILD=False")
    print("P12_3D_MANAGED_NATIVE_BINDING_BOUNDARY=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
