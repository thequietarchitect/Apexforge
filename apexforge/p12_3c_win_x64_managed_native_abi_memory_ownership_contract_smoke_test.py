from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs/p12/P12_3C_WIN_X64_MANAGED_NATIVE_ABI_MEMORY_OWNERSHIP_CONTRACT.json"
MARKDOWN = ROOT / "docs/p12/P12_3C_WIN_X64_MANAGED_NATIVE_ABI_MEMORY_OWNERSHIP_CONTRACT.md"


def require(value: bool, message: str) -> None:
    if not value:
        raise AssertionError(message)


def main() -> int:
    data = json.loads(CONTRACT.read_text(encoding="utf-8"))
    md = MARKDOWN.read_text(encoding="utf-8")
    require(data["profile_id"] == "apexforge.win-x64-managed-native-abi/v1", "ABI profile identity changed")
    scope = data["scope"]
    require(scope["os"] == "windows", "ABI operating system changed")
    require(scope["rid"] == "win-x64", "ABI RID changed")
    require(scope["architecture"] == "x64", "ABI architecture changed")
    require(scope["pointer_bits"] == 64, "ABI pointer width changed")
    require(scope["endianness"] == "little", "ABI endianness changed")
    require(scope["profile_scope"] == "CONCRETE_WINDOWS_X64_PROFILE_NOT_UNIVERSAL_ABI", "ABI scope broadened silently")
    ownership = data["ownership"]
    require(ownership["abi_owner"] == "NATIVE_BACKEND", "native ABI ownership changed")
    require(ownership["managed_runtime_relationship"] == "SIBLING_EXECUTION_TARGET", "managed/native sibling relation changed")
    require(ownership["visual_studio_dependency"] is False, "Visual Studio dependency entered ABI")
    require(ownership["optimizer_semantic_ownership"] is False, "optimizer semantic ownership entered ABI")
    calling = data["calling_convention"]
    require(calling["selected"] == "WINDOWS_X64_PLATFORM_ABI", "calling convention changed")
    require(calling["c_compatible"] is True, "C-compatible ABI requirement removed")
    require(calling["cpp_name_mangling"] is False, "C++ name mangling entered ABI")
    require(calling["exceptions_cross_boundary"] is False, "exceptions allowed across ABI")
    values = data["value_boundary"]
    require(values["text"] == "UTF8_POINTER_PLUS_U64_LENGTH", "text ABI changed")
    require(values["null_termination_required"] is False, "NUL termination requirement entered ABI")
    require(values["structs_by_value"] == "FORBIDDEN_V1", "by-value structs entered v1 ABI")
    require(values["opaque_native_handles"] == "POINTER_SIZED_OPAQUE_NON_DEREFERENCEABLE_BY_MANAGED", "opaque-handle rule changed")
    memory = data["memory_ownership"]
    require(memory["input_buffers"] == "CALLER_OWNED_BORROWED_FOR_CALL_DURATION_ONLY", "input ownership changed")
    require(memory["callee_may_retain_input"] is False, "callee retention of borrowed input allowed")
    require(memory["output_buffers"] == "NATIVE_OWNED_UNTIL_EXPLICIT_NATIVE_RELEASE", "output ownership changed")
    require(memory["cross_runtime_free"] == "FORBIDDEN", "cross-runtime free allowed")
    require(memory["managed_gc_pointer_retention"] == "FORBIDDEN", "managed GC pointer retention allowed")
    errors = data["errors"]
    require(errors["function_result"] == "I32_STATUS_CODE", "status-code ABI changed")
    require(errors["success_code"] == 0, "success code changed")
    require(errors["exceptions_cross_boundary"] is False, "exception boundary changed")
    ffi = data["ffi"]
    require(ffi["generic_ffi"] is False, "generic FFI introduced")
    require(ffi["managed_binding_mechanism"] == "DEFERRED_TO_P12_3D", "managed FFI mechanism selected too early")
    require(ffi["callbacks"] == "DEFERRED", "callback ABI selected too early")
    toolchain = data["toolchain"]
    require(toolchain["native_compiler"] == "UNSELECTED", "native compiler selected in ABI contract")
    require(toolchain["compiler_required_for_this_contract"] is False, "compiler made prerequisite for contract")
    require("Windows x64 platform ABI" in md, "markdown calling-convention statement missing")
    require("Cross-runtime free is forbidden" in md, "markdown ownership rule missing")
    require("SafeHandle integration is deferred to P12.3D" in md, "markdown managed-handle deferral missing")
    print("P12_3C_PROFILE_ID=apexforge.win-x64-managed-native-abi/v1")
    print("P12_3C_PLATFORM=windows-x64")
    print("P12_3C_POINTER_BITS=64")
    print("P12_3C_ENDIANNESS=little")
    print("P12_3C_CALLING_CONVENTION=WINDOWS_X64_PLATFORM_ABI")
    print("P12_3C_C_COMPATIBLE_BOUNDARY=True")
    print("P12_3C_STRUCTS_BY_VALUE=FORBIDDEN_V1")
    print("P12_3C_INPUT_BUFFERS=CALLER_OWNED_BORROWED_FOR_CALL_DURATION_ONLY")
    print("P12_3C_OUTPUT_BUFFERS=NATIVE_OWNED_UNTIL_EXPLICIT_NATIVE_RELEASE")
    print("P12_3C_CROSS_RUNTIME_FREE=FORBIDDEN")
    print("P12_3C_EXCEPTIONS_CROSS_BOUNDARY=False")
    print("P12_3C_GENERIC_FFI=False")
    print("P12_3C_MANAGED_BINDING_MECHANISM=DEFERRED_TO_P12_3D")
    print("P12_3C_NATIVE_COMPILER=UNSELECTED")
    print("P12_3C_WIN_X64_MANAGED_NATIVE_ABI_MEMORY_OWNERSHIP_CONTRACT=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
