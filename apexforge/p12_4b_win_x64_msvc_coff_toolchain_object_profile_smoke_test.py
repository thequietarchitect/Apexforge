from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "docs/p12/P12_4B_WIN_X64_MSVC_COFF_TOOLCHAIN_OBJECT_PROFILE.json"
HEADER = ROOT / "runtimes/native/include/apexforge_native.h"
LIFECYCLE = ROOT / "docs/p12/P12_3E_NATIVE_EXPORT_RESOURCE_LIFECYCLE_CONTRACT.json"


def require(value: bool, message: str) -> None:
    if not value:
        raise AssertionError(message)


def main() -> int:
    data = json.loads(PROFILE.read_text(encoding="utf-8"))
    header = HEADER.read_text(encoding="utf-8")
    lifecycle = json.loads(LIFECYCLE.read_text(encoding="utf-8"))
    require(data["profile_id"] == "apexforge.win-x64-msvc-coff/v1", "toolchain profile identity changed")
    require(data["target"]["os"] == "windows", "target OS changed")
    require(data["target"]["architecture"] == "x64", "target architecture changed")
    require(data["target"]["rid"] == "win-x64", "target RID changed")
    require(data["target"]["pointer_bits"] == 64, "pointer width changed")
    require(data["target"]["abi_profile"] == "apexforge.win-x64-managed-native-abi/v1", "ABI profile changed")
    require(data["compiler"]["selected"] is True, "compiler not selected")
    require(data["compiler"]["family"] == "MSVC", "compiler family changed")
    require(data["compiler"]["driver"] == "cl.exe", "compiler driver changed")
    require(data["compiler"]["target_architecture"] == "x64", "compiler target changed")
    require(data["compiler"]["llvm_required"] is False, "LLVM became mandatory")
    require(data["object"]["selected"] is True, "object format not selected")
    require(data["object"]["format"] == "COFF", "object format changed")
    require(data["object"]["machine"] == "AMD64", "COFF machine changed")
    require(data["object"]["extension"] == ".obj", "object extension changed")
    require(data["linker"]["selected"] is True, "linker not selected")
    require(data["linker"]["family"] == "MSVC_LINK", "linker family changed")
    require(data["linker"]["driver"] == "link.exe", "linker driver changed")
    require(data["linker"]["image_format"] == "PE32_PLUS", "image format changed")
    require(data["librarian"]["driver"] == "lib.exe", "librarian changed")
    require(data["inspection"]["tool"] == "dumpbin.exe", "inspection tool changed")
    require(data["build"]["build_system"] == "UNSELECTED", "build system selected prematurely")
    require(data["build"]["visual_studio_ide_dependency"] is False, "Visual Studio IDE became runtime dependency")
    require(data["semantics"]["native_backend_semantic_authority"] is False, "native backend gained semantic ownership")
    require(data["semantics"]["toolchain_may_redefine_language"] is False, "toolchain may redefine language")
    require(data["scope"]["object_emission_attempted"] is False, "object emission entered P12.4B")
    require(data["scope"]["native_link_attempted"] is False, "native link entered P12.4B")
    require(data["scope"]["dll_production_attempted"] is False, "DLL production entered P12.4B")
    require(data["scope"]["native_source_implementation"] == "DEFERRED_TO_P12_4C", "native implementation entered P12.4B")
    require(lifecycle["profile_id"] == "apexforge.win-x64-native-export-lifecycle/v1", "P12.3 lifecycle identity changed")
    require("apexforge_status_t apexforge_release_handle(apexforge_handle_t handle);" in header, "P12.3 handle declaration changed")
    require("apexforge_status_t apexforge_release_buffer(void* data, uint64_t length);" in header, "P12.3 buffer declaration changed")
    print("P12_4B_PROFILE_ID=apexforge.win-x64-msvc-coff/v1")
    print("P12_4B_TARGET=windows-x64")
    print("P12_4B_COMPILER=MSVC_CL")
    print("P12_4B_OBJECT_FORMAT=COFF_X64")
    print("P12_4B_OBJECT_EXTENSION=.obj")
    print("P12_4B_LINKER=MSVC_LINK")
    print("P12_4B_IMAGE_FORMAT=PE32_PLUS")
    print("P12_4B_LIBRARIAN=MSVC_LIB")
    print("P12_4B_INSPECTION_TOOL=DUMPBIN")
    print("P12_4B_LLVM_REQUIRED=False")
    print("P12_4B_BUILD_SYSTEM=UNSELECTED")
    print("P12_4B_VISUAL_STUDIO_IDE_DEPENDENCY=False")
    print("P12_4B_OBJECT_EMISSION_ATTEMPTED=False")
    print("P12_4B_NATIVE_LINK_ATTEMPTED=False")
    print("P12_4B_DLL_PRODUCTION_ATTEMPTED=False")
    print("P12_4B_P12_3_ABI_PRESERVED=PASS")
    print("P12_4B_WIN_X64_MSVC_COFF_TOOLCHAIN_OBJECT_PROFILE=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
