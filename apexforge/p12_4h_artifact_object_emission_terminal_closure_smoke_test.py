from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLOSURE = ROOT / "docs/p12/P12_4H_ARTIFACT_OBJECT_EMISSION_TERMINAL_CLOSURE.json"
HEADER = ROOT / "runtimes/native/include/apexforge_native.h"
DEF = ROOT / "runtimes/native/link/apexforge_native.def"
MANAGED = ROOT / "runtimes/dotnet/ApexForge.Runtime/ManagedNativeAbi.cs"


def require(value: bool, message: str) -> None:
    if not value:
        raise AssertionError(message)


def main() -> int:
    data = json.loads(CLOSURE.read_text(encoding="utf-8"))
    require(data["profile_id"] == "apexforge.p12.artifact-object-emission-terminal-closure/v1", "profile changed")
    require(data["predecessor_commit"] == "cd4649a396fe33c414255b2bedbe4f08dffb2c6e", "predecessor changed")
    require(data["phase"] == "P12.4", "phase changed")
    require(data["state"] == "TERMINALLY_READY_FOR_FREEZE", "closure state changed")
    gates = data["completed_gates"]
    require(gates["P12.4A"] == "CAPABILITY_CENSUS_CLOSED", "P12.4A changed")
    require(gates["P12.4B"] == "TOOLCHAIN_OBJECT_PROFILE_COMMITTED", "P12.4B changed")
    require(gates["P12.4C"] == "CONTROLLED_AMD64_COFF_OBJECT_COMMITTED", "P12.4C changed")
    require(gates["P12.4D"] == "COFF_REPRODUCIBILITY_POLICY_COMMITTED", "P12.4D changed")
    require(gates["P12.4E"] == "NATIVE_LIFECYCLE_EXPORT_OBJECT_SURFACE_COMMITTED", "P12.4E changed")
    require(gates["P12.4F"] == "NATIVE_LIFECYCLE_OWNERSHIP_COMPLETE", "P12.4F changed")
    require(gates["P12.4G"] == "PRODUCTION_NATIVE_LIBRARY_LINK_COMPLETE", "P12.4G changed")
    require(gates["P12.4H_A"] == "TERMINAL_READINESS_CENSUS_PASS", "P12.4H-A changed")
    native = data["production_native_library"]
    require(native["logical_name"] == "apexforge_native", "logical library changed")
    require(native["file_name"] == "apexforge_native.dll", "DLL name changed")
    require(native["machine"] == "AMD64" and native["pe_format"] == "PE32_PLUS", "PE target changed")
    require(sorted(native["exports"]) == ["apexforge_release_buffer", "apexforge_release_handle"], "export contract changed")
    require(native["import_dll_count"] == 0, "dependency surface changed")
    require(native["whole_dll_reproducibility_required"] is True, "whole DLL reproducibility changed")
    require(native["governed_reproducibility_flag"] == "/Brepro", "reproducibility flag changed")
    require(native["observed_characterization_sha256"] == "ED1708825B13B6C23D1017A933EAAB1B681BD5D6D686C28525B9EC403B9A42A8", "characterization hash changed")
    require(native["characterization_hash_is_permanent_abi_constant"] is False, "characterization hash became ABI constant")
    require(native["generated_binary_tracked_in_git"] is False, "generated DLL tracking changed")
    managed = data["managed_native_binding"]
    require(managed["target_framework"] == "net10.0", "managed target changed")
    require(managed["mechanism"] == "LibraryImport", "binding mechanism changed")
    require(managed["actual_binding_execution_proven"] is True, "binding execution proof missing")
    require(managed["null_rejection_proven"] is True and managed["unknown_resource_rejection_proven"] is True, "managed rejection proof changed")
    require(managed["live_resource_successful_release_proven"] is False, "live-resource success overclaimed")
    require(managed["live_resource_successful_release_deferred_reason"] == "PUBLIC_CREATION_EXPORTS_DEFERRED", "live-resource deferral changed")
    boundaries = data["semantic_boundaries"]
    require(boundaries["canonical_semantics_owner"] == "UPSTREAM_CANONICAL_AIR", "semantic owner changed")
    require(boundaries["native_backend_semantic_authority"] is False, "native backend gained semantic authority")
    require(boundaries["generic_ffi"] is False, "generic FFI expanded")
    require(boundaries["public_creation_exports"] is False, "creation exports expanded")
    require(boundaries["runtime_host_produced"] is False, "runtime host moved into P12.4")
    require(boundaries["allocator_family"] == "UNSELECTED", "allocator selected early")
    require(boundaries["thread_safety"] == "DEFERRED", "thread safety overclaimed")
    require(data["freeze"]["recommended"] is True, "freeze recommendation changed")
    require(data["freeze"]["proposed_tag"] == "afp-p12.4-freeze", "freeze tag changed")
    require(data["next_stage"] == "P12.5 RUNTIME HOSTS", "next stage changed")
    header = HEADER.read_text(encoding="utf-8")
    header_exports = sorted(re.findall(r"^apexforge_status_t\s+(apexforge_[a-z0-9_]+)\s*\(", header, re.MULTILINE))
    require(header_exports == ["apexforge_release_buffer", "apexforge_release_handle"], "header export set changed")
    def_lines = [line.strip() for line in DEF.read_text(encoding="utf-8").splitlines() if line.strip()]
    require(def_lines == ["LIBRARY apexforge_native", "EXPORTS", "apexforge_release_handle", "apexforge_release_buffer"], "DEF surface changed")
    managed_source = MANAGED.read_text(encoding="utf-8")
    managed_entries = sorted(re.findall(r'\[LibraryImport\(\s*LibraryName\s*,\s*EntryPoint\s*=\s*"([^"]+)"\s*\)\]', managed_source, re.DOTALL))
    require(managed_entries == ["apexforge_release_buffer", "apexforge_release_handle"], "managed entry-point set changed")
    require(re.search(r'\bLibraryName\s*=\s*"apexforge_native"\s*;', managed_source) is not None, "managed library identity changed")
    print("P12_4H_PROFILE_ID=apexforge.p12.artifact-object-emission-terminal-closure/v1")
    print("P12_4H_PHASE_STATE=TERMINALLY_READY_FOR_FREEZE")
    print("P12_4H_P12_4G_COMPLETE=True")
    print("P12_4H_WHOLE_DLL_SHA256_IDENTITY=True")
    print("P12_4H_ACTUAL_MANAGED_LIBRARYIMPORT_EXECUTION_PROVEN=True")
    print("P12_4H_LIVE_RESOURCE_SUCCESSFUL_RELEASE=DEFERRED")
    print("P12_4H_PUBLIC_CREATION_EXPORTS=False")
    print("P12_4H_RUNTIME_HOST_PRODUCED=False")
    print("P12_4H_PROPOSED_FREEZE_TAG=afp-p12.4-freeze")
    print("P12_4H_NEXT_STAGE=P12.5_RUNTIME_HOSTS")
    print("P12_4H_ARTIFACT_OBJECT_EMISSION_TERMINAL_CLOSURE=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
