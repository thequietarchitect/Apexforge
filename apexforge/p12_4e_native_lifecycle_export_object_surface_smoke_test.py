from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs/p12/P12_4E_NATIVE_LIFECYCLE_EXPORT_OBJECT_SURFACE.json"
SOURCE = ROOT / "runtimes/native/src/apexforge_lifecycle_exports.c"
PROFILE = ROOT / "docs/p12/P12_4B_WIN_X64_MSVC_COFF_TOOLCHAIN_OBJECT_PROFILE.json"
POLICY = ROOT / "docs/p12/P12_4D_COFF_REPRODUCIBILITY_PROVENANCE_POLICY.json"
HEADER = ROOT / "runtimes/native/include/apexforge_native.h"

def require(value: bool, message: str) -> None:
    if not value:
        raise AssertionError(message)

def main() -> int:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    source = SOURCE.read_text(encoding="utf-8")
    profile = json.loads(PROFILE.read_text(encoding="utf-8"))
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    header = HEADER.read_text(encoding="utf-8")

    require(contract["profile_id"] == "apexforge.win-x64-native-lifecycle-export-object/v1", "P12.4E profile changed")
    require(contract["target"]["toolchain_profile"] == "apexforge.win-x64-msvc-coff/v1", "toolchain profile changed")
    require(contract["target"]["reproducibility_profile"] == "apexforge.win-x64-coff-reproducibility/v1", "reproducibility profile changed")
    require(profile["profile_id"] == contract["target"]["toolchain_profile"], "P12.4B profile mismatch")
    require(policy["profile_id"] == contract["target"]["reproducibility_profile"], "P12.4D policy mismatch")
    require(contract["target"]["object_format"] == "COFF", "object format changed")
    require(contract["target"]["machine"] == "AMD64", "machine changed")
    require(contract["surface"]["public_defined_symbols"] == ["apexforge_release_handle", "apexforge_release_buffer"], "public release surface changed")
    require(contract["surface"]["internal_undefined_dependencies"] == ["apexforge_internal_release_handle", "apexforge_internal_release_buffer"], "internal lifecycle dependency surface changed")
    require(contract["surface"]["public_release_symbols_forward_only"] is True, "public release surface stopped being forwarding-only")
    require(contract["surface"]["allocator_symbols_permitted"] is False, "allocator symbols became permitted")
    require(contract["surface"]["creation_symbols_permitted"] is False, "creation symbols became permitted")
    require(contract["ownership"]["allocator_behavior_implemented"] is False, "allocator behavior entered P12.4E")
    require(contract["ownership"]["lifecycle_core_implemented"] is False, "lifecycle core entered P12.4E")
    require(contract["ownership"]["lifecycle_core_deferred_to"] == "P12.4F", "lifecycle core deferral changed")
    require(contract["ownership"]["cross_runtime_free"] == "FORBIDDEN", "cross-runtime free changed")
    require(contract["ownership"]["public_release_success_semantics_claimed"] is False, "release success semantics claimed prematurely")
    require(contract["emission"]["native_link_attempted"] is False, "native linking entered P12.4E")
    require(contract["emission"]["dll_production_attempted"] is False, "DLL production entered P12.4E")
    require(contract["semantics"]["canonical_semantics_owner"] == "UPSTREAM_CANONICAL_AIR", "semantic owner changed")
    require(contract["semantics"]["native_backend_semantic_authority"] is False, "native backend gained semantic ownership")

    require('#include "apexforge_native.h"' in source, "P12.3 ABI header not consumed")
    require("apexforge_status_t apexforge_release_handle(apexforge_handle_t handle)" in source, "release_handle definition missing")
    require("apexforge_status_t apexforge_release_buffer(void* data, uint64_t length)" in source, "release_buffer definition missing")
    require("return apexforge_internal_release_handle(handle);" in source, "release_handle is not a pure forwarder")
    require("return apexforge_internal_release_buffer(data, length);" in source, "release_buffer is not a pure forwarder")
    require("extern apexforge_status_t apexforge_internal_release_handle" in source, "internal handle lifecycle dependency missing")
    require("extern apexforge_status_t apexforge_internal_release_buffer" in source, "internal buffer lifecycle dependency missing")
    forbidden = ("malloc(", "calloc(", "realloc(", "free(", "HeapAlloc", "HeapFree", "VirtualAlloc", "VirtualFree", "__declspec", "LoadLibrary", "GetProcAddress")
    require(not any(item in source for item in forbidden), "allocator/link/export behavior entered P12.4E")
    require("apexforge_status_t apexforge_release_handle(apexforge_handle_t handle);" in header, "P12.3 handle declaration changed")
    require("apexforge_status_t apexforge_release_buffer(void* data, uint64_t length);" in header, "P12.3 buffer declaration changed")

    print("P12_4E_PROFILE_ID=apexforge.win-x64-native-lifecycle-export-object/v1")
    print("P12_4E_TARGET=windows-x64")
    print("P12_4E_OBJECT_FORMAT=COFF_X64")
    print("P12_4E_PUBLIC_RELEASE_SYMBOLS=apexforge_release_handle,apexforge_release_buffer")
    print("P12_4E_INTERNAL_LIFECYCLE_DEPENDENCIES=apexforge_internal_release_handle,apexforge_internal_release_buffer")
    print("P12_4E_PUBLIC_RELEASE_SYMBOLS_FORWARD_ONLY=True")
    print("P12_4E_ALLOCATOR_BEHAVIOR_IMPLEMENTED=False")
    print("P12_4E_LIFECYCLE_CORE_IMPLEMENTED=False")
    print("P12_4E_LIFECYCLE_CORE_DEFERRED_TO=P12.4F")
    print("P12_4E_NATIVE_LINK_ATTEMPTED=False")
    print("P12_4E_DLL_PRODUCTION_ATTEMPTED=False")
    print("P12_4E_SOURCE_CONTRACT=PASS")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
