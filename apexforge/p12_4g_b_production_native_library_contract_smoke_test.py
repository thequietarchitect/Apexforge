from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs/p12/P12_4G_B_PRODUCTION_NATIVE_LIBRARY_CONTRACT.json"
DEF = ROOT / "runtimes/native/link/apexforge_native.def"
HEADER = ROOT / "runtimes/native/include/apexforge_native.h"
MANAGED = ROOT / "runtimes/dotnet/ApexForge.Runtime/ManagedNativeAbi.cs"

def require(value: bool, message: str) -> None:
    if not value:
        raise AssertionError(message)

def main() -> int:
    data = json.loads(CONTRACT.read_text(encoding="utf-8"))
    def_lines = [line.strip() for line in DEF.read_text(encoding="utf-8").splitlines() if line.strip()]
    header = HEADER.read_text(encoding="utf-8")
    managed = MANAGED.read_text(encoding="utf-8")
    require(data["profile_id"] == "apexforge.win-x64-production-native-library/v1", "profile changed")
    require(data["identity"]["logical_library"] == "apexforge_native", "logical library changed")
    require(data["identity"]["file_name"] == "apexforge_native.dll", "DLL filename changed")
    require(data["identity"]["machine"] == "AMD64" and data["identity"]["pe_format"] == "PE32_PLUS", "target identity changed")
    require(data["link"]["dll"] is True and data["link"]["noentry"] is True and data["link"]["nodefaultlib"] is True, "link policy changed")
    require(data["link"]["export_mechanism"] == "MODULE_DEFINITION_FILE", "export mechanism changed")
    require(def_lines == ["LIBRARY apexforge_native", "EXPORTS", "apexforge_release_handle", "apexforge_release_buffer"], "module-definition surface changed")
    expected = ["apexforge_release_buffer", "apexforge_release_handle"]
    header_exports = sorted(re.findall(r"^apexforge_status_t\s+(apexforge_[a-z0-9_]+)\s*\(", header, re.MULTILINE))
    require(header_exports == expected, "public header export set changed")
    library_match = re.search(r'\b(?:const|static\s+readonly)\s+string\s+LibraryName\s*=\s*"([^"]+)"\s*;', managed)
    require(library_match is not None and library_match.group(1) == "apexforge_native", "managed library identity changed")
    managed_entries = sorted(re.findall(r'\[LibraryImport\(\s*LibraryName\s*,\s*EntryPoint\s*=\s*"([^"]+)"\s*\)\]', managed))
    require(managed_entries == expected, "managed entry-point set changed")
    require(sorted(data["exports"]["names"]) == expected and data["exports"]["count"] == 2, "contract export surface changed")
    require(data["exports"]["internal_symbols_exported"] is False, "internal export policy changed")
    require(data["dependencies"]["import_dll_count"] == 0 and data["dependencies"]["crt_imports_allowed"] is False, "dependency policy changed")
    require(data["artifact_policy"]["dll_tracked_in_git"] is False and data["artifact_policy"]["release_pipeline_is_artifact_producer"] is True, "artifact policy changed")
    require(data["reproducibility"]["dll_reproducibility_characterization"] == "DEFERRED" and data["reproducibility"]["deferred_to"] == "P12.4G-C", "DLL reproducibility scope changed")
    require(data["abi"]["public_creation_exports"] is False and data["abi"]["generic_ffi"] is False, "ABI scope expanded")
    require(data["allocator"]["family"] == "UNSELECTED", "allocator family selected early")
    require(data["semantics"]["native_backend_semantic_authority"] is False, "native backend gained semantic authority")
    require(data["runtime_host_produced"] is False and data["production_binary_persisted_in_repository"] is False, "artifact scope expanded")
    print("P12_4G_B_PROFILE_ID=apexforge.win-x64-production-native-library/v1")
    print("P12_4G_B_NATIVE_LIBRARY=apexforge_native.dll")
    print("P12_4G_B_EXPORT_SET=apexforge_release_handle,apexforge_release_buffer")
    print("P12_4G_B_EXPORT_MECHANISM=MODULE_DEFINITION_FILE")
    print("P12_4G_B_IMPORT_DLL_COUNT=0")
    print("P12_4G_B_BINARY_TRACKED_IN_GIT=False")
    print("P12_4G_B_DLL_REPRODUCIBILITY=DEFERRED_TO_P12.4G-C")
    print("P12_4G_B_PRODUCTION_NATIVE_LIBRARY_CONTRACT=PASS")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
