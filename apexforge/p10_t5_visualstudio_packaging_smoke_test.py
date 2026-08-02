"""AFP-P10-T5.7 Visual Studio packaging hardening smoke test."""
from __future__ import annotations

from pathlib import Path
import tempfile
import zipfile

from tooling.visualstudio_packaging import (
    CANONICAL_VISUAL_STUDIO_PACKAGING_SHA256,
    VisualStudioPackagingError,
    audit_visualstudio_installed_copy,
    audit_visualstudio_vsix_hardening,
    visual_studio_packaging_fingerprint,
)


PACKAGED_MANIFEST = b'''<?xml version="1.0" encoding="utf-8"?>
<PackageManifest Version="2.0.0" xmlns="http://schemas.microsoft.com/developer/vsx-schema/2011">
  <Metadata>
    <Identity Id="GravitasStudios.ApexForge.VisualStudio" Version="0.1.0" Language="en-US" Publisher="Gravitas Studios" />
    <DisplayName>ApexForge Language</DisplayName>
    <Description xml:space="preserve">ApexForge Visual Studio language support.</Description>
  </Metadata>
  <Installation>
    <InstallationTarget Id="Microsoft.VisualStudio.Community" Version="[17.0,)"><ProductArchitecture>amd64</ProductArchitecture></InstallationTarget>
    <InstallationTarget Id="Microsoft.VisualStudio.Community" Version="[17.0,)"><ProductArchitecture>arm64</ProductArchitecture></InstallationTarget>
  </Installation>
  <Dependencies />
  <Prerequisites>
    <Prerequisite Id="Microsoft.VisualStudio.Component.CoreEditor" Version="[17.0,)" DisplayName="Visual Studio core editor" />
  </Prerequisites>
  <Assets>
    <Asset Type="Microsoft.VisualStudio.VsPackage" d:Source="Project" d:ProjectName="ApexForge.VisualStudio" Path="ApexForge.VisualStudio.pkgdef" xmlns:d="http://schemas.microsoft.com/developer/vsx-schema-design/2011" />
    <Asset Type="Microsoft.VisualStudio.MefComponent" d:Source="Project" d:ProjectName="ApexForge.VisualStudio" Path="ApexForge.VisualStudio.dll" xmlns:d="http://schemas.microsoft.com/developer/vsx-schema-design/2011" />
  </Assets>
</PackageManifest>
'''
DLL = b"MZ\x90\x00AFP-P10-T5.7 synthetic assembly"
PKGDEF = b"[$RootKey$\\Packages\\{DF54A578-54A2-52F4-8643-4A85DDDFB2F2}]\n"
CONTENT_TYPES = b'''<?xml version="1.0" encoding="utf-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types" />'''


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def require_packaging_error(operation, marker: str) -> None:
    try:
        operation()
    except VisualStudioPackagingError as error:
        require(marker in str(error), f"expected marker {marker!r}, received {error}")
        return
    raise AssertionError(f"operation unexpectedly passed; expected {marker!r}")


def write_vsix(path: Path, extras: tuple[tuple[str, bytes], ...] = ()) -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("extension.vsixmanifest", PACKAGED_MANIFEST)
        archive.writestr("ApexForge.VisualStudio.dll", DLL)
        archive.writestr("ApexForge.VisualStudio.pkgdef", PKGDEF)
        archive.writestr("[Content_Types].xml", CONTENT_TYPES)
        for name, data in extras:
            archive.writestr(name, data)


def main() -> None:
    require(
        visual_studio_packaging_fingerprint()
        == CANONICAL_VISUAL_STUDIO_PACKAGING_SHA256,
        "T5.7 packaging contract fingerprint changed",
    )

    with tempfile.TemporaryDirectory(prefix="apexforge-t5-7-") as directory:
        root = Path(directory)
        valid = root / "valid.vsix"
        write_vsix(valid)
        audit = audit_visualstudio_vsix_hardening(valid)
        require(audit.identity == "GravitasStudios.ApexForge.VisualStudio", "identity changed")
        require(audit.version == "0.1.0", "version changed")
        require(audit.assembly_sha256, "assembly hash missing")

        duplicate = root / "duplicate.vsix"
        write_vsix(duplicate, (("APEXFORGE.VISUALSTUDIO.DLL", DLL),))
        require_packaging_error(
            lambda: audit_visualstudio_vsix_hardening(duplicate),
            "duplicate normalized archive paths",
        )

        traversal = root / "traversal.vsix"
        write_vsix(traversal, (("../escape.txt", b"escape"),))
        require_packaging_error(
            lambda: audit_visualstudio_vsix_hardening(traversal),
            "unsafe path",
        )

        source_payload = root / "source-payload.vsix"
        write_vsix(source_payload, (("Commands/Unsafe.cs", b"class Unsafe {}"),))
        require_packaging_error(
            lambda: audit_visualstudio_vsix_hardening(source_payload),
            "forbidden source/debug payload",
        )

        profile = root / "18.0_TestExp"
        extension = profile / "Extensions" / "ApexForge"
        extension.mkdir(parents=True)
        (extension / "extension.vsixmanifest").write_bytes(PACKAGED_MANIFEST)
        (extension / "ApexForge.VisualStudio.dll").write_bytes(DLL)
        installed = audit_visualstudio_installed_copy(valid, profile)
        require(installed.assembly_sha256 == audit.assembly_sha256, "installed hash changed")

        stale = profile / "Extensions" / "StaleApexForge"
        stale.mkdir(parents=True)
        (stale / "extension.vsixmanifest").write_bytes(PACKAGED_MANIFEST)
        (stale / "ApexForge.VisualStudio.dll").write_bytes(DLL)
        require_packaging_error(
            lambda: audit_visualstudio_installed_copy(valid, profile),
            "stale duplicate extension registrations",
        )

        (stale / "extension.vsixmanifest").unlink()
        (extension / "ApexForge.VisualStudio.dll").write_bytes(b"different")
        require_packaging_error(
            lambda: audit_visualstudio_installed_copy(valid, profile),
            "does not match the built VSIX assembly",
        )

    print("AFP-P10-T5.7 Visual Studio packaging hardening smoke test passed.")
    print("Archive path normalization and duplicate rejection: PASS")
    print("Source/debug and traversal payload rejection: PASS")
    print("Manifest identity and architecture audit: PASS")
    print("Installed-copy uniqueness and assembly hash equality: PASS")
    print(f"Packaging contract SHA-256: {CANONICAL_VISUAL_STUDIO_PACKAGING_SHA256}")


if __name__ == "__main__":
    main()
