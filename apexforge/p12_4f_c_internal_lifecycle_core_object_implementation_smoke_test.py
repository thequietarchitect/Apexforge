from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs/p12/P12_4F_C_INTERNAL_LIFECYCLE_CORE_OBJECT_IMPLEMENTATION.json"
CORE = ROOT / "runtimes/native/src/apexforge_lifecycle_core.c"
PUBLIC = ROOT / "runtimes/native/include/apexforge_native.h"

def require(v: bool, m: str) -> None:
    if not v:
        raise AssertionError(m)

def main() -> int:
    c = json.loads(CONTRACT.read_text(encoding="utf-8"))
    s = CORE.read_text(encoding="utf-8")
    h = PUBLIC.read_text(encoding="utf-8")
    require(c["profile_id"] == "apexforge.win-x64-native-lifecycle-core-object/v1", "profile changed")
    require(c["implementation"]["registry_storage"] == "STATIC_INTERNAL_FIXED_CAPACITY", "registry storage changed")
    require(c["implementation"]["dynamic_allocator_used"] is False, "dynamic allocator entered core")
    require(c["implementation"]["arbitrary_pointer_dereference_before_validation"] is False, "unsafe dereference policy changed")
    require(c["implementation"]["handle_buffer_kind_separation"] is True, "kind separation changed")
    require(c["implementation"]["buffer_registered_length_validation"] is True, "buffer length validation changed")
    require(c["implementation"]["release_consumes_registry_liveness_before_disposer_call"] is True, "reentrant consumption ordering changed")
    require(c["implementation"]["released_slots_reusable"] is True, "released slots stopped being reusable")
    require(c["implementation"]["released_resource_tombstone_required"] is False, "tombstone requirement changed")
    require(c["implementation"]["thread_safety"] == "DEFERRED", "thread-safety scope changed")
    require(c["status"]["public_success"] == 0, "public success changed")
    require(c["status"]["public_failure_contract"] == "ANY_NONZERO_OPAQUE_V1", "public failure contract changed")
    require(c["status"]["public_status_namespace_extended"] is False, "public status namespace expanded")
    require(c["allocator"]["family"] == "UNSELECTED", "allocator selected")
    require(c["allocator"]["disposal_mechanism"] == "INTERNAL_REGISTERED_DISPOSER_CALLBACK", "disposal seam changed")
    require(c["scope"]["native_link_attempted"] is False, "link entered F-C")
    require(c["scope"]["dll_production_attempted"] is False, "DLL entered F-C")
    require(c["scope"]["public_creation_exports"] is False, "public creation export entered F-C")
    require("apexforge_internal_release_handle" in s and "apexforge_internal_release_buffer" in s, "release implementation missing")
    require("apexforge_internal_register_handle" in s and "apexforge_internal_register_buffer" in s, "registration seam missing")
    require("entry->resource = NULL;" in s and "entry->live = 0;" in s, "successful release does not clear live registry identity")
    require(s.index("entry->resource = NULL;") < s.index("disposer(resource, registered_length, context);"), "registry identity must be consumed before disposer")
    require("entry->length != length" in s, "buffer length validation missing")
    require("entry->kind != expected_kind" in s, "resource-kind validation missing")
    require("if (resource == NULL)" in s, "null validation missing")
    require("malloc(" not in s and "calloc(" not in s and "realloc(" not in s and "free(" not in s, "CRT allocator entered core")
    require("HeapAlloc" not in s and "HeapFree" not in s and "CoTaskMemAlloc" not in s and "CoTaskMemFree" not in s, "platform allocator entered core")
    require("APEXFORGE_STATUS_INVALID" not in h and "APEXFORGE_STATUS_NOT_FOUND" not in h and "APEXFORGE_STATUS_ALREADY_RELEASED" not in h, "public error namespace expanded")
    require("apexforge_internal_register_" not in h, "internal registration leaked into public header")
    print("P12_4F_C_PROFILE_ID=apexforge.win-x64-native-lifecycle-core-object/v1")
    print("P12_4F_C_REGISTRY_STORAGE=STATIC_INTERNAL_FIXED_CAPACITY")
    print("P12_4F_C_REGISTRY_CAPACITY=64")
    print("P12_4F_C_DYNAMIC_ALLOCATOR_USED=False")
    print("P12_4F_C_ALLOCATOR_FAMILY=UNSELECTED")
    print("P12_4F_C_VALIDATE_BEFORE_DISPOSE=True")
    print("P12_4F_C_LIVENESS_CONSUMED_BEFORE_DISPOSER=True")
    print("P12_4F_C_RELEASED_SLOTS_REUSABLE=True")
    print("P12_4F_C_THREAD_SAFETY=DEFERRED")
    print("P12_4F_C_PUBLIC_STATUS_NAMESPACE_EXTENDED=False")
    print("P12_4F_C_PUBLIC_CREATION_EXPORTS=False")
    print("P12_4F_C_NATIVE_LINK_ATTEMPTED=False")
    print("P12_4F_C_DLL_PRODUCTION_ATTEMPTED=False")
    print("P12_4F_C_SOURCE_CONTRACT=PASS")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
