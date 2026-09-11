from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "docs/p12/P12_4B_WIN_X64_MSVC_COFF_TOOLCHAIN_OBJECT_PROFILE.json"
SOURCE = ROOT / "runtimes/native/probes/p12_4c_object_probe.c"
HEADER = ROOT / "runtimes/native/include/apexforge_native.h"


def require(value: bool, message: str) -> None:
    if not value:
        raise AssertionError(message)


def main() -> int:
    profile = json.loads(PROFILE.read_text(encoding="utf-8"))
    source = SOURCE.read_text(encoding="utf-8")
    header = HEADER.read_text(encoding="utf-8")
    require(profile["profile_id"] == "apexforge.win-x64-msvc-coff/v1", "P12.4B profile changed")
    require(profile["compiler"]["family"] == "MSVC", "compiler profile changed")
    require(profile["object"]["format"] == "COFF", "object format changed")
    require(profile["object"]["machine"] == "AMD64", "object machine changed")
    require(profile["object"]["extension"] == ".obj", "object extension changed")
    require("#include \"apexforge_native.h\"" in source, "P12.3 ABI header not consumed")
    require("#if !defined(_M_X64)" in source, "x64 compile guard missing")
    require("sizeof(apexforge_status_t) == 4" in source, "status-width compile assertion missing")
    require("sizeof(apexforge_handle_t) == 8" in source, "handle-width compile assertion missing")
    require("sizeof(uint64_t) == 8" in source, "buffer-length compile assertion missing")
    require("apexforge_status_t apexforge_p12_4c_object_probe(void)" in source, "object probe symbol missing")
    require("return APEXFORGE_STATUS_OK;" in source, "object probe result changed")
    require("apexforge_release_handle(" not in source, "P12.3 handle implementation entered object probe")
    require("apexforge_release_buffer(" not in source, "P12.3 buffer implementation entered object probe")
    forbidden = ("malloc(", "calloc(", "realloc(", "free(", "LoadLibrary", "GetProcAddress", "__declspec", "main(")
    require(not any(item in source for item in forbidden), "runtime/link/export implementation entered controlled object probe")
    require("apexforge_status_t apexforge_release_handle(apexforge_handle_t handle);" in header, "P12.3 handle declaration changed")
    require("apexforge_status_t apexforge_release_buffer(void* data, uint64_t length);" in header, "P12.3 buffer declaration changed")
    print("P12_4C_PROBE_SOURCE=runtimes/native/probes/p12_4c_object_probe.c")
    print("P12_4C_PROBE_SOURCE_LANGUAGE=C")
    print("P12_4C_TARGET=windows-x64")
    print("P12_4C_EXPECTED_OBJECT_FORMAT=COFF")
    print("P12_4C_EXPECTED_MACHINE=AMD64")
    print("P12_4C_P12_3_HEADER_CONSUMED=True")
    print("P12_4C_ABI_WIDTH_ASSERTIONS_PRESENT=True")
    print("P12_4C_LIFECYCLE_EXPORT_IMPLEMENTATION_PRESENT=False")
    print("P12_4C_NATIVE_LINK_REQUIRED=False")
    print("P12_4C_SOURCE_CONTRACT=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
