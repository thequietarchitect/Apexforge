from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs/p12/P12_4F_INTERNAL_LIFECYCLE_CORE_CONTRACT.json"
HEADER = ROOT / "runtimes/native/include/apexforge_native.h"
EXPORTS = ROOT / "runtimes/native/src/apexforge_lifecycle_exports.c"
LIFECYCLE = ROOT / "docs/p12/P12_3E_NATIVE_EXPORT_RESOURCE_LIFECYCLE_CONTRACT.json"


def require(value: bool, message: str) -> None:
    if not value:
        raise AssertionError(message)


def main() -> int:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    header = HEADER.read_text(encoding="utf-8")
    exports = EXPORTS.read_text(encoding="utf-8")
    lifecycle = LIFECYCLE.read_text(encoding="utf-8")
    require(contract["profile_id"] == "apexforge.win-x64-native-lifecycle-core/v1", "profile identity changed")
    require(contract["public_abi"]["status_type"] == "I32", "public status width changed")
    require(contract["public_abi"]["success_status"] == "ZERO", "zero-success contract changed")
    require(contract["public_abi"]["public_failure_status"] == "ANY_NONZERO_OPAQUE_V1", "public failure compatibility changed")
    require(contract["public_abi"]["public_status_namespace_extended"] is False, "public status namespace expanded")
    require(contract["public_abi"]["release_symbols"] == ["apexforge_release_handle", "apexforge_release_buffer"], "public release surface changed")
    require("#define APEXFORGE_STATUS_OK ((apexforge_status_t)0)" in header, "public zero-success declaration changed")
    require("APEXFORGE_STATUS_INVALID" not in header and "APEXFORGE_STATUS_NOT_FOUND" not in header and "APEXFORGE_STATUS_ALREADY_RELEASED" not in header, "P12.4F added public error constants")
    require("return apexforge_internal_release_handle(handle);" in exports, "handle forwarding boundary changed")
    require("return apexforge_internal_release_buffer(data, length);" in exports, "buffer forwarding boundary changed")
    require("ON_SUCCESS_CONSUMES_ONE_LIVE_NATIVE_HANDLE" in lifecycle, "handle success ownership contract changed")
    require("ON_SUCCESS_CONSUMES_ONE_LIVE_NATIVE_BUFFER" in lifecycle, "buffer success ownership contract changed")
    require(contract["lifecycle"]["successful_release_count"] == "EXACTLY_ONE_PER_LIVE_RESOURCE", "single-release invariant changed")
    require(contract["lifecycle"]["null_resource"] == "NONZERO_FAILURE_NO_CONSUME", "null-resource rule changed")
    require(contract["lifecycle"]["unknown_resource"] == "NONZERO_FAILURE_NO_CONSUME", "unknown-resource rule changed")
    require(contract["lifecycle"]["already_released_resource"] == "NONZERO_FAILURE_NO_CONSUME", "double-release rule changed")
    require(contract["lifecycle"]["buffer_length_mismatch"] == "NONZERO_FAILURE_NO_CONSUME", "buffer length rule changed")
    require(contract["lifecycle"]["cross_runtime_free"] == "FORBIDDEN", "cross-runtime free changed")
    require(contract["validation"]["native_ownership_registry_required"] is True, "ownership validation registry removed")
    require(contract["validation"]["validate_before_dispose"] is True, "validate-before-dispose weakened")
    require(contract["validation"]["arbitrary_pointer_dereference_before_validation"] is False, "unsafe pointer dereference permitted")
    require(contract["validation"]["handle_buffer_kind_separation_required"] is True, "resource-kind separation removed")
    require(contract["validation"]["buffer_registered_length_required"] is True, "buffer length identity removed")
    require(contract["internal_surface"]["internal_symbols_are_public_abi"] is False, "internal lifecycle symbols became public ABI")
    require(contract["allocator"]["allocator_family"] == "UNSELECTED", "allocator selected prematurely")
    require(contract["allocator"]["public_creation_exports"] is False, "public creation exports entered P12.4F-B")
    require(contract["artifact_scope"]["native_link_attempted"] is False, "native linking entered P12.4F-B")
    require(contract["artifact_scope"]["dll_production_attempted"] is False, "DLL production entered P12.4F-B")
    require(contract["semantics"]["canonical_semantics_owner"] == "UPSTREAM_CANONICAL_AIR", "semantic authority changed")
    print("P12_4F_PROFILE_ID=apexforge.win-x64-native-lifecycle-core/v1")
    print("P12_4F_PUBLIC_SUCCESS_STATUS=ZERO")
    print("P12_4F_PUBLIC_FAILURE_STATUS=ANY_NONZERO_OPAQUE_V1")
    print("P12_4F_PUBLIC_STATUS_NAMESPACE_EXTENDED=False")
    print("P12_4F_NATIVE_OWNERSHIP_REGISTRY_REQUIRED=True")
    print("P12_4F_VALIDATE_BEFORE_DISPOSE=True")
    print("P12_4F_ARBITRARY_POINTER_DEREFERENCE_BEFORE_VALIDATION=False")
    print("P12_4F_EXACTLY_ONE_SUCCESSFUL_RELEASE_PER_LIVE_RESOURCE=True")
    print("P12_4F_BUFFER_REGISTERED_LENGTH_REQUIRED=True")
    print("P12_4F_ALLOCATOR_FAMILY=UNSELECTED")
    print("P12_4F_PUBLIC_CREATION_EXPORTS=False")
    print("P12_4F_NATIVE_LINK_ATTEMPTED=False")
    print("P12_4F_DLL_PRODUCTION_ATTEMPTED=False")
    print("P12_4F_INTERNAL_LIFECYCLE_CORE_CONTRACT=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
