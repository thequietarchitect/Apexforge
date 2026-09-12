from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs/p12/P12_4G_C_DLL_REPRODUCIBILITY_POLICY.json"
PRODUCTION = ROOT / "docs/p12/P12_4G_B_PRODUCTION_NATIVE_LIBRARY_CONTRACT.json"
DEF = ROOT / "runtimes/native/link/apexforge_native.def"


def require(value: bool, message: str) -> None:
    if not value:
        raise AssertionError(message)


def main() -> int:
    data = json.loads(CONTRACT.read_text(encoding="utf-8"))
    production = json.loads(PRODUCTION.read_text(encoding="utf-8"))
    def_lines = [line.strip() for line in DEF.read_text(encoding="utf-8").splitlines() if line.strip()]
    require(data["profile_id"] == "apexforge.win-x64-production-native-library-reproducibility/v1", "profile changed")
    require(data["applies_to_profile"] == "apexforge.win-x64-production-native-library/v1", "production profile binding changed")
    require(production["profile_id"] == data["applies_to_profile"], "production contract/profile mismatch")
    require(data["artifact"]["logical_library"] == "apexforge_native", "logical library changed")
    require(data["artifact"]["file_name"] == "apexforge_native.dll", "DLL filename changed")
    require(data["artifact"]["machine"] == "AMD64" and data["artifact"]["pe_format"] == "PE32_PLUS", "target identity changed")
    required_flags = ["/DLL", "/NOENTRY", "/NODEFAULTLIB", "/MACHINE:X64", "/Brepro"]
    require(data["build_requirements"]["linker_flags_required"] == required_flags, "governed linker flags changed")
    require(data["build_requirements"]["compiler_object_flag"] == "/Brepro", "object reproducibility flag changed")
    require(data["build_requirements"]["linker_flag"] == "/Brepro", "link reproducibility flag changed")
    require(data["build_requirements"]["build_directory_is_artifact_identity"] is False, "build directory became artifact identity")
    require(def_lines == ["LIBRARY apexforge_native", "EXPORTS", "apexforge_release_handle", "apexforge_release_buffer"], "module-definition surface changed")
    repro = data["reproducibility"]
    require(repro["same_path_whole_dll_identity_required"] is True, "same-path identity requirement changed")
    require(repro["cross_directory_whole_dll_identity_required"] is True, "cross-directory identity requirement changed")
    require(repro["same_path_pe_timestamp_identity_required"] is True, "same-path timestamp requirement changed")
    require(repro["cross_directory_pe_timestamp_identity_required"] is True, "cross-directory timestamp requirement changed")
    require(repro["section_variance_allowed"] is False, "section variance became allowed")
    require(repro["release_artifact_identity"] == "WHOLE_DLL_SHA256", "release identity changed")
    require(repro["ignore_rdata_variance"] is False and repro["ignore_pe_header_timestamp_variance"] is False, "metadata variance exclusion added")
    require(sorted(data["surface"]["exports"]) == ["apexforge_release_buffer", "apexforge_release_handle"], "export surface changed")
    require(data["surface"]["import_dll_count"] == 0 and data["surface"]["crt_imports_allowed"] is False, "dependency surface changed")
    evidence = data["evidence"]
    require(evidence["same_path_whole_dll_identical"] is True and evidence["cross_directory_whole_dll_identical"] is True, "characterization evidence changed")
    require(evidence["same_path_section_variance_count"] == 0 and evidence["cross_directory_section_variance_count"] == 0, "section evidence changed")
    require(evidence["observed_whole_dll_sha256"] == "ED1708825B13B6C23D1017A933EAAB1B681BD5D6D686C28525B9EC403B9A42A8", "evidence hash changed")
    require(data["artifact_policy"]["binary_tracked_in_git"] is False, "binary source-control policy changed")
    require(data["scope"]["toolchain_change_requires_recharacterization"] is True, "toolchain recharacterization requirement changed")
    require(data["scope"]["runtime_host_produced"] is False and data["scope"]["public_creation_exports"] is False, "stage scope expanded")
    require(data["semantics"]["native_backend_semantic_authority"] is False, "semantic authority changed")
    print("P12_4G_C_PROFILE_ID=apexforge.win-x64-production-native-library-reproducibility/v1")
    print("P12_4G_C_COMPILER_BREPRO_REQUIRED=True")
    print("P12_4G_C_LINKER_BREPRO_REQUIRED=True")
    print("P12_4G_C_RELEASE_ARTIFACT_IDENTITY=WHOLE_DLL_SHA256")
    print("P12_4G_C_SAME_PATH_WHOLE_DLL_IDENTITY_REQUIRED=True")
    print("P12_4G_C_CROSS_DIRECTORY_WHOLE_DLL_IDENTITY_REQUIRED=True")
    print("P12_4G_C_SECTION_VARIANCE_ALLOWED=False")
    print("P12_4G_C_TOOLCHAIN_CHANGE_REQUIRES_RECHARACTERIZATION=True")
    print("P12_4G_C_BINARY_TRACKED_IN_GIT=False")
    print("P12_4G_C_DLL_REPRODUCIBILITY_POLICY=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
