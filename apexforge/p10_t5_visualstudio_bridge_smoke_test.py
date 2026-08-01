"""AFP-P10-T5.3 Visual Studio language-server process bridge smoke test."""
from __future__ import annotations

from pathlib import Path
import shutil
import tempfile
import zipfile

from language_server.integration import CANONICAL_INTEGRATION_SHA256
from tooling.visualstudio_bridge import (
    CANONICAL_VISUAL_STUDIO_BRIDGE_SHA256,
    VisualStudioBridgeError,
    audit_visualstudio_bridge,
    audit_visualstudio_bridge_vsix,
)
from tooling.visualstudio_editor import CANONICAL_VISUAL_STUDIO_EDITOR_SHA256
from tooling.visualstudio_extension import CANONICAL_VISUAL_STUDIO_EXTENSION_SHA256
from tooling.visualstudio_language_client import (
    CANONICAL_VISUAL_STUDIO_LANGUAGE_CLIENT_SHA256,
    build_launch_plan,
    resolve_repository_root,
    visual_studio_language_client_fingerprint,
)

EXPECTED_T4_11 = "c2fff74134a40bd335e1c04123127d4cc87df7aa2ed3accc5133d93da9066897"
EXPECTED_T5_1 = "06d8b8f428b033d5e522b4eaf842560fc7c5b4e953ebcf3338f7e1a87d6b363e"
EXPECTED_T5_2 = "4aea8eff4f5c6e934be5220e4c880b6c7ac40722b0bea2caa037a141fa4c1b67"
EXPECTED_CLIENT = "6248cc0469bcaaed7a11358334e9a23fc9c1f965d38c23bb724dc9c5c9d52921"
EXPECTED_BRIDGE = "443e19a53353e282130b0ada1c43812cf3a896977f64a9a5443133919c1b26c6"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def make_repository(root: Path) -> None:
    (root / "apexforge/language_server").mkdir(parents=True)
    (root / "apexforge/apexforge_lsp.py").write_text(
        "from language_server.server import main\n",
        encoding="utf-8",
    )
    (root / "apexforge/language_server/server.py").write_text(
        "def main(): return 0\n",
        encoding="utf-8",
    )
    (root / "apexforge/language_server/integration.py").write_text(
        "CANONICAL_INTEGRATION_SHA256 = 'synthetic'\n",
        encoding="utf-8",
    )


def synthetic_vsix(path: Path, *, include_host_runtime: bool = False) -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("extension.vsixmanifest", b"<PackageManifest />")
        archive.writestr("ApexForge.VisualStudio.dll", b"synthetic assembly")
        if include_host_runtime:
            archive.writestr(
                "Microsoft.VisualStudio.LanguageServer.Client.dll",
                b"must not be bundled",
            )


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    extension_root = repo_root / "editors" / "visualstudio-apexforge"

    require(CANONICAL_INTEGRATION_SHA256 == EXPECTED_T4_11, "T4.11 integration fingerprint changed")
    require(CANONICAL_VISUAL_STUDIO_EXTENSION_SHA256 == EXPECTED_T5_1, "T5.1 extension fingerprint changed")
    require(CANONICAL_VISUAL_STUDIO_EDITOR_SHA256 == EXPECTED_T5_2, "T5.2 editor fingerprint changed")
    require(visual_studio_language_client_fingerprint() == EXPECTED_CLIENT, "T5.3 client contract changed")
    require(CANONICAL_VISUAL_STUDIO_LANGUAGE_CLIENT_SHA256 == EXPECTED_CLIENT, "declared T5.3 client fingerprint changed")

    audit = audit_visualstudio_bridge(extension_root)
    require(audit.bridge_sha256 == EXPECTED_BRIDGE, "Visual Studio T5.3 bridge audit changed")
    require(CANONICAL_VISUAL_STUDIO_BRIDGE_SHA256 == EXPECTED_BRIDGE, "declared T5.3 bridge fingerprint changed")

    with tempfile.TemporaryDirectory(prefix="apexforge-t5-3-eol-") as temporary:
        normalized_root = Path(temporary) / "visualstudio-apexforge"
        shutil.copytree(extension_root, normalized_root)
        project = normalized_root / "src/ApexForge.VisualStudio/ApexForge.VisualStudio.csproj"
        project_text = project.read_text(encoding="utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")
        project.write_bytes(b"\xef\xbb\xbf" + project_text.replace("\n", "\r\n").encode("utf-8"))
        normalized_audit = audit_visualstudio_bridge(normalized_root)
        require(normalized_audit.bridge_sha256 == EXPECTED_BRIDGE, "CRLF/BOM normalization changed bridge contract")

    with tempfile.TemporaryDirectory(prefix="apexforge-t5-3-") as temporary:
        temp_root = Path(temporary)
        repository = temp_root / "workspace" / "ApexForge"
        make_repository(repository)

        nested = repository / "editors" / "visualstudio-apexforge"
        nested.mkdir(parents=True)
        resolved = resolve_repository_root((nested,))
        require(resolved == repository.resolve(), "ancestor repository discovery failed")

        unrelated = temp_root / "elsewhere"
        unrelated.mkdir()
        resolved_from_environment = resolve_repository_root(
            (unrelated,),
            environment_root=repository,
        )
        require(resolved_from_environment == repository.resolve(), "environment repository discovery failed")

        plan = build_launch_plan(repository, python_executable="python.exe")
        require(plan.python_executable == "python.exe", "Python executable selection changed")
        require(plan.script_path == (repository / "apexforge/apexforge_lsp.py").resolve(), "server script changed")
        require(plan.arguments[-1] == "--stdio", "stdio argument missing")
        require(plan.working_directory == (repository / "apexforge").resolve(), "working directory changed")

        good_vsix = temp_root / "ApexForge.VisualStudio.synthetic.vsix"
        synthetic_vsix(good_vsix)
        vsix = audit_visualstudio_bridge_vsix(good_vsix)
        require(vsix.entry_count == 2, "synthetic VSIX entry count changed")

        bad_vsix = temp_root / "ApexForge.VisualStudio.bad.vsix"
        synthetic_vsix(bad_vsix, include_host_runtime=True)
        try:
            audit_visualstudio_bridge_vsix(bad_vsix)
        except VisualStudioBridgeError as error:
            require("hosted runtime assemblies" in str(error), "bad VSIX failure changed")
        else:
            raise AssertionError("host runtime assembly was not rejected")

    print("AFP-P10-T5.3 Visual Studio language-server bridge smoke test passed.")
    print("Frozen T4.11/T5.1/T5.2 prerequisites: PASS")
    print("Code-remote ApexForge content type: PASS")
    print("ILanguageClient MEF activation contract: PASS")
    print("Deterministic repository and Python discovery: PASS")
    print("Redirected stdio and stderr containment: PASS")
    print("Previous-process replacement and failure cleanup: PASS")
    print("Visual Studio-hosted runtime VSIX boundary: PASS")
    print("UTF-8 BOM and line-ending normalization: PASS")
    print("Deterministic T5.3 fingerprints: PASS")


if __name__ == "__main__":
    main()
