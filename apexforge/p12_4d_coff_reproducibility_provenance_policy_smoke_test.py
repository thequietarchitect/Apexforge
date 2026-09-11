from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "docs/p12/P12_4D_COFF_REPRODUCIBILITY_PROVENANCE_POLICY.json"
PROFILE = ROOT / "docs/p12/P12_4B_WIN_X64_MSVC_COFF_TOOLCHAIN_OBJECT_PROFILE.json"


def require(value: bool, message: str) -> None:
    if not value:
        raise AssertionError(message)


def main() -> int:
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    profile = json.loads(PROFILE.read_text(encoding="utf-8"))
    require(policy["profile_id"] == "apexforge.win-x64-coff-reproducibility/v1", "policy identity changed")
    require(policy["applies_to"]["toolchain_profile"] == "apexforge.win-x64-msvc-coff/v1", "toolchain binding changed")
    require(profile["profile_id"] == policy["applies_to"]["toolchain_profile"], "P12.4B profile mismatch")
    require(policy["applies_to"]["object_format"] == "COFF", "object format changed")
    require(policy["applies_to"]["machine"] == "AMD64", "machine changed")
    require(policy["identity"]["portable_code_identity"] == "ORDERED_EXECUTABLE_SECTION_NAME_SIZE_SHA256", "portable code identity changed")
    require(policy["identity"]["whole_object_hash_portable_across_arbitrary_build_directories"] is False, "whole object incorrectly became portable identity")
    require(policy["same_invocation"]["identical_output_path_byte_identity_required"] is True, "same-invocation byte identity weakened")
    require(policy["same_invocation"]["brepro_required"] is True, "Brepro requirement removed")
    require(policy["cross_directory"]["whole_object_byte_identity_required"] is False, "cross-directory whole-object requirement reintroduced")
    require(policy["cross_directory"]["executable_code_section_identity_required"] is True, "code section determinism weakened")
    require(policy["cross_directory"]["directive_section_identity_required"] is True, "directive determinism weakened")
    require(policy["cross_directory"]["allowed_varying_sections"] == [".debug$S", ".chks64"], "metadata allowlist changed")
    require(policy["cross_directory"]["unexpected_executable_section_variance"] == "FAIL", "executable variance no longer fails")
    require(policy["observed_evidence"]["text_section"] == ".text$mn", "observed text section changed")
    require(policy["observed_evidence"]["text_section_identical"] is True, "observed code identity changed")
    require(policy["observed_evidence"]["text_section_sha256"] == "4BC724F3B1D0CAF4FE369C18CBA3102E6C4EA057F63FE1587E3973134A7F755E", "observed text hash changed")
    require(policy["observed_evidence"]["directive_section_identical"] is True, "observed directive identity changed")
    require(policy["observed_evidence"]["differing_sections"] == [".chks64", ".debug$S"], "observed variance set changed")
    require(policy["provenance"]["build_directory_is_not_semantic_identity"] is True, "build directory became semantic identity")
    require(policy["semantics"]["canonical_semantics_owner"] == "UPSTREAM_CANONICAL_AIR", "semantic owner changed")
    require(policy["scope"]["native_link_attempted"] is False, "native linking entered P12.4D")
    require(policy["scope"]["dll_production_attempted"] is False, "DLL production entered P12.4D")
    require(policy["scope"]["native_lifecycle_exports_implemented"] is False, "lifecycle implementation entered P12.4D")
    print("P12_4D_PROFILE_ID=apexforge.win-x64-coff-reproducibility/v1")
    print("P12_4D_PORTABLE_CODE_IDENTITY=ORDERED_EXECUTABLE_SECTION_NAME_SIZE_SHA256")
    print("P12_4D_SAME_PATH_WHOLE_OBJECT_DETERMINISM_REQUIRED=True")
    print("P12_4D_CROSS_DIRECTORY_WHOLE_OBJECT_IDENTITY_REQUIRED=False")
    print("P12_4D_CROSS_DIRECTORY_EXECUTABLE_SECTION_IDENTITY_REQUIRED=True")
    print("P12_4D_ALLOWED_VARYING_SECTIONS=.debug$S,.chks64")
    print("P12_4D_EXECUTABLE_SECTION_VARIANCE_POLICY=FAIL")
    print("P12_4D_BUILD_DIRECTORY_IS_SEMANTIC_IDENTITY=False")
    print("P12_4D_NATIVE_LINK_ATTEMPTED=False")
    print("P12_4D_DLL_PRODUCTION_ATTEMPTED=False")
    print("P12_4D_COFF_REPRODUCIBILITY_PROVENANCE_POLICY=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
