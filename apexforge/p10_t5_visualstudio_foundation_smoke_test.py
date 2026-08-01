"""AFP-P10-T5.1 Visual Studio extension foundation smoke test."""
from __future__ import annotations

from pathlib import Path
import tempfile
import zipfile

from language_server.integration import CANONICAL_INTEGRATION_SHA256
from tooling.visualstudio_extension import (
    CANONICAL_VISUAL_STUDIO_EXTENSION_SHA256,
    VisualStudioExtensionError,
    audit_visualstudio_extension,
    audit_visualstudio_vsix,
)
from tooling.visualstudio_foundation import (
    CANONICAL_VISUAL_STUDIO_FOUNDATION_SHA256,
    visual_studio_foundation_fingerprint,
)

EXPECTED_T4_INTEGRATION = "c2fff74134a40bd335e1c04123127d4cc87df7aa2ed3accc5133d93da9066897"
EXPECTED_FOUNDATION = "4c18e2840fa7ca7d74307f8ef71dc0510a84c0c6aa5b99619eb3a522ef4c3f54"
EXPECTED_EXTENSION = "06d8b8f428b033d5e522b4eaf842560fc7c5b4e953ebcf3338f7e1a87d6b363e"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def expect_failure(callback, marker: str) -> None:
    try:
        callback()
    except VisualStudioExtensionError as error:
        require(marker in str(error), f"failure omitted {marker!r}: {error}")
        return
    raise AssertionError(f"expected VisualStudioExtensionError containing {marker!r}")


def synthetic_vsix(path: Path, manifest: bytes) -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("extension.vsixmanifest", manifest)
        archive.writestr("ApexForge.VisualStudio.dll", b"synthetic managed assembly")
        archive.writestr("catalog.json", b"{}")


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    extension_root = repo_root / "editors" / "visualstudio-apexforge"

    require(CANONICAL_INTEGRATION_SHA256 == EXPECTED_T4_INTEGRATION, "T4.11 integration fingerprint changed")
    require(visual_studio_foundation_fingerprint() == EXPECTED_FOUNDATION, "T5.1 foundation fingerprint changed")
    require(CANONICAL_VISUAL_STUDIO_FOUNDATION_SHA256 == EXPECTED_FOUNDATION, "declared T5.1 foundation fingerprint changed")

    audit = audit_visualstudio_extension(extension_root)
    require(audit.extension_sha256 == EXPECTED_EXTENSION, "Visual Studio extension audit changed")
    require(CANONICAL_VISUAL_STUDIO_EXTENSION_SHA256 == EXPECTED_EXTENSION, "declared Visual Studio extension fingerprint changed")

    manifest_path = extension_root / "src" / "ApexForge.VisualStudio" / "source.extension.vsixmanifest"
    with tempfile.TemporaryDirectory(prefix="apexforge-t5-1-") as temporary:
        temp_root = Path(temporary)
        vsix_path = temp_root / "ApexForge.VisualStudio.synthetic.vsix"
        synthetic_vsix(vsix_path, manifest_path.read_bytes())
        vsix = audit_visualstudio_vsix(vsix_path)
        require(vsix.identity == "GravitasStudios.ApexForge.VisualStudio", "synthetic VSIX identity changed")
        require(vsix.version == "0.1.0", "synthetic VSIX version changed")
        require(vsix.architectures == ("amd64", "arm64"), "synthetic VSIX architectures changed")

        bad_vsix = temp_root / "ApexForge.VisualStudio.bad.vsix"
        synthetic_vsix(bad_vsix, manifest_path.read_bytes())
        with zipfile.ZipFile(bad_vsix, "a", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("source/Forbidden.cs", "class Forbidden {}")
        expect_failure(lambda: audit_visualstudio_vsix(bad_vsix), "source/debug files")

    print("AFP-P10-T5.1 Visual Studio extension foundation smoke test passed.")
    print("Frozen T4.11 prerequisite: PASS")
    print("Solution and SDK-style VSIX project: PASS")
    print("Visual Studio 17.x AMD64/ARM64 targets: PASS")
    print("ApexForge .apex MEF content type: PASS")
    print("AsyncPackage command shell: PASS")
    print("Synthetic VSIX payload audit: PASS")
    print("Deterministic T5.1 fingerprints: PASS")


if __name__ == "__main__":
    main()
