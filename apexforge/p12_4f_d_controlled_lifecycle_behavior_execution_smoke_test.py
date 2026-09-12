from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs/p12/P12_4F_D_CONTROLLED_LIFECYCLE_BEHAVIOR_EXECUTION.json"
PROBE = ROOT / "runtimes/native/probes/p12_4f_d_lifecycle_behavior_probe.c"
HEADER = ROOT / "runtimes/native/include/apexforge_native.h"

def require(value: bool, message: str) -> None:
    if not value:
        raise AssertionError(message)

def main() -> int:
    data = json.loads(CONTRACT.read_text(encoding="utf-8"))
    probe = PROBE.read_text(encoding="utf-8")
    header = HEADER.read_text(encoding="utf-8")
    require(data["profile_id"] == "apexforge.win-x64-native-lifecycle-behavior-execution/v1", "profile identity changed")
    require(data["artifact"]["kind"] == "TEMPORARY_TEST_EXECUTABLE", "artifact scope changed")
    require(data["artifact"]["format"] == "PE32_PLUS" and data["artifact"]["machine"] == "AMD64", "target artifact changed")
    require(data["artifact"]["nodefaultlib"] is True and data["artifact"]["crt_imports_allowed"] is False, "CRT isolation changed")
    require(data["artifact"]["production_dll_produced"] is False, "production DLL entered P12.4F-D")
    require(data["abi"]["public_status_namespace_extended"] is False, "public status namespace changed")
    require(data["abi"]["public_creation_exports"] is False, "public creation exports entered")
    require(data["allocator"]["allocator_family"] == "UNSELECTED" and data["allocator"]["dynamic_allocator_used"] is False, "allocator policy changed")
    require(data["scope"]["native_link_attempted"] is True and data["scope"]["production_dll_link_attempted"] is False, "link scope changed")
    for key, value in data["behavior"].items():
        require(value == "REQUIRED", "behavior requirement changed: " + key)
    require("apexforge_release_handle((apexforge_handle_t)0)" in probe, "null-resource test missing")
    require("apexforge_release_handle(&u)" in probe, "unknown-resource test missing")
    require("apexforge_release_buffer(&h,0u)" in probe, "wrong-kind test missing")
    require("apexforge_release_buffer(&b,15u)" in probe and "apexforge_release_buffer(&b,16u)" in probe, "buffer-length behavior test missing")
    require("dispose_count!=3" in probe, "disposer/reuse final assertion missing")
    require("ExitProcess(run_tests())" in probe, "test result exit boundary missing")
    require("__declspec(dllexport)" not in probe, "test probe added exports")
    for forbidden in ("malloc(", "calloc(", "realloc(", "free(", "LoadLibrary", "GetProcAddress"):
        require(forbidden not in probe, "forbidden behavior probe dependency: " + forbidden)
    require("apexforge_status_t apexforge_release_handle(apexforge_handle_t handle);" in header, "public handle ABI changed")
    require("apexforge_status_t apexforge_release_buffer(void* data, uint64_t length);" in header, "public buffer ABI changed")
    print("P12_4F_D_PROFILE_ID=apexforge.win-x64-native-lifecycle-behavior-execution/v1")
    print("P12_4F_D_ARTIFACT_KIND=TEMPORARY_TEST_EXECUTABLE")
    print("P12_4F_D_NODEFAULTLIB=True")
    print("P12_4F_D_PRODUCTION_DLL_PRODUCED=False")
    print("P12_4F_D_PUBLIC_STATUS_NAMESPACE_EXTENDED=False")
    print("P12_4F_D_PUBLIC_CREATION_EXPORTS=False")
    print("P12_4F_D_ALLOCATOR_FAMILY=UNSELECTED")
    print("P12_4F_D_BEHAVIOR_CONTRACT=PASS")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
