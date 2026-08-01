"""AFP-P10-T5.3 Visual Studio language-server bridge auditor."""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import sys
from typing import Final, Mapping, Optional, Sequence
import xml.etree.ElementTree as ET
import zipfile

from language_server.integration import CANONICAL_INTEGRATION_SHA256
from tooling.visualstudio_editor import (
    CANONICAL_VISUAL_STUDIO_EDITOR_SHA256,
    VisualStudioEditorError,
    audit_visualstudio_editor,
)
from tooling.visualstudio_extension import (
    CANONICAL_VISUAL_STUDIO_EXTENSION_SHA256,
)
from tooling.visualstudio_language_client import (
    CANONICAL_VISUAL_STUDIO_LANGUAGE_CLIENT_SHA256,
)

P10_T5_VISUAL_STUDIO_BRIDGE_VERSION: Final[str] = "10-T5.3"
VISUAL_STUDIO_BRIDGE_SCHEMA: Final[int] = 1
VISUAL_STUDIO_BRIDGE_KIND: Final[str] = "apexforge.visual-studio-language-server-bridge"

_EXPECTED_CONTRACT: Final[Mapping[str, object]] = {'schema': 1, 'kind': 'apexforge.visual-studio-language-server-bridge', 'bridge_version': '10-T5.3', 'required_t4_integration_sha256': 'c2fff74134a40bd335e1c04123127d4cc87df7aa2ed3accc5133d93da9066897', 'required_t5_1_extension_sha256': '06d8b8f428b033d5e522b4eaf842560fc7c5b4e953ebcf3338f7e1a87d6b363e', 'required_t5_2_editor_sha256': '4aea8eff4f5c6e934be5220e4c880b6c7ac40722b0bea2caa037a141fa4c1b67', 'language_client_sha256': '6248cc0469bcaaed7a11358334e9a23fc9c1f965d38c23bb724dc9c5c9d52921', 'root': 'editors/visualstudio-apexforge', 'required_files': ('src/ApexForge.VisualStudio/ApexForge.VisualStudio.csproj', 'src/ApexForge.VisualStudio/Content/ApexForgeContentType.cs', 'src/ApexForge.VisualStudio/Commands/ShowStatusCommand.cs', 'src/ApexForge.VisualStudio/LanguageServer/ApexForgeLanguageServerLocator.cs', 'src/ApexForge.VisualStudio/LanguageServer/ApexForgeLanguageServerTrace.cs', 'src/ApexForge.VisualStudio/LanguageServer/ApexForgeLanguageClient.cs'), 'file_sha256': {'src/ApexForge.VisualStudio/ApexForge.VisualStudio.csproj': 'a3480b1b189a2b90b41dde7eb5f736cfb5e3b05412bd97354316659d0e1e41fc', 'src/ApexForge.VisualStudio/Content/ApexForgeContentType.cs': '5a0c3a1468369474a827221a2102e0f4c5cd35304bb1651de6e6f296258cb2d6', 'src/ApexForge.VisualStudio/Commands/ShowStatusCommand.cs': 'f57deb9cdd4c7185032aa9763d4f46cfe56649134d67f8438b4e642da54992a2', 'src/ApexForge.VisualStudio/LanguageServer/ApexForgeLanguageServerLocator.cs': 'c872070df44e619c85ced7b2c9839fb304541c30bab09e7a915b0406adee73fa', 'src/ApexForge.VisualStudio/LanguageServer/ApexForgeLanguageServerTrace.cs': '1aa54a31f065421df158710b4f39ff0ecf73f0d0f4bd9fe108d21fb64c7c6af7', 'src/ApexForge.VisualStudio/LanguageServer/ApexForgeLanguageClient.cs': '7baec08b13054e98b259baf88c4d094fa29eec9be1aa88d32986cf200a9966e9'}, 'content_type': 'apexforge', 'content_base': 'CodeRemoteContentDefinition.CodeRemoteContentTypeName', 'package': 'Microsoft.VisualStudio.LanguageServer.Client@17.14.60', 'package_runtime_assets_excluded': True, 'client_contract': 'ILanguageClient', 'transport': 'stdio', 'server_entry': 'apexforge/apexforge_lsp.py --stdio', 'repository_discovery': ('APEXFORGE_REPOSITORY_ROOT', 'ancestor walk', '%USERPROFILE%/source/repos/ApexForge', '%USERPROFILE%/Documents/GitHub/ApexForge'), 'python_discovery': ('APEXFORGE_PYTHON', 'py.exe'), 'stderr_drained': True, 'process_restart_replaces_previous': True, 'failure_terminates_process': True, 'show_notification_on_initialize_failed': True, 'structured_initialize_failure_callback': True, 'legacy_exception_failure_callback': True, 'log_path': '%TEMP%/ApexForge/visualstudio-language-client.log', 't4_server_modified': False, 'vsix_host_runtime_assemblies_forbidden': ('Microsoft.VisualStudio.LanguageServer.Client.dll', 'StreamJsonRpc.dll', 'Newtonsoft.Json.dll')}
CANONICAL_VISUAL_STUDIO_BRIDGE_SHA256: Final[str] = "443e19a53353e282130b0ada1c43812cf3a896977f64a9a5443133919c1b26c6"


class VisualStudioBridgeError(ValueError):
    code: Final[str] = "APX-VS-003"

    def __init__(self, message: str) -> None:
        if type(message) is not str or not message:
            raise ValueError("VisualStudioBridgeError.message must be non-empty.")
        self.message = message
        super().__init__(f"[{self.code}] {message}")


@dataclass(frozen=True)
class VisualStudioBridgeAudit:
    root: Path
    bridge_sha256: str
    file_sha256: Mapping[str, str]


@dataclass(frozen=True)
class VisualStudioBridgeVsixAudit:
    path: Path
    entry_count: int
    vsix_sha256: str


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_json(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError) as error:
        raise VisualStudioBridgeError(
            f"Could not read UTF-8 file {path}: {error}"
        ) from error


def _source_sha256(path: Path) -> str:
    text = _read_text(path).replace("\r\n", "\n").replace("\r", "\n")
    return _sha256(text.encode("utf-8"))


def _parse_xml(path: Path) -> ET.Element:
    try:
        return ET.fromstring(_read_text(path))
    except ET.ParseError as error:
        raise VisualStudioBridgeError(f"Malformed XML in {path}: {error}") from error


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _children(root: ET.Element, name: str):
    return tuple(item for item in root.iter() if _local_name(item.tag) == name)


def _require_marker(text: str, marker: str, owner: str) -> None:
    if marker not in text:
        raise VisualStudioBridgeError(f"{owner} omitted required marker {marker!r}.")


def audit_visualstudio_bridge(root: Path | str) -> VisualStudioBridgeAudit:
    selected = Path(root).resolve()
    if not selected.is_dir():
        raise VisualStudioBridgeError(
            f"Visual Studio extension root does not exist: {selected}."
        )

    if CANONICAL_INTEGRATION_SHA256 != _EXPECTED_CONTRACT["required_t4_integration_sha256"]:
        raise VisualStudioBridgeError("T4.11 language-server integration fingerprint changed.")
    if CANONICAL_VISUAL_STUDIO_EXTENSION_SHA256 != _EXPECTED_CONTRACT["required_t5_1_extension_sha256"]:
        raise VisualStudioBridgeError("T5.1 extension fingerprint changed.")
    if CANONICAL_VISUAL_STUDIO_EDITOR_SHA256 != _EXPECTED_CONTRACT["required_t5_2_editor_sha256"]:
        raise VisualStudioBridgeError("T5.2 editor fingerprint changed.")
    if CANONICAL_VISUAL_STUDIO_LANGUAGE_CLIENT_SHA256 != _EXPECTED_CONTRACT["language_client_sha256"]:
        raise VisualStudioBridgeError("T5.3 language-client contract fingerprint changed.")

    try:
        previous = audit_visualstudio_editor(selected)
    except VisualStudioEditorError as error:
        raise VisualStudioBridgeError(str(error)) from error
    if previous.editor_sha256 != _EXPECTED_CONTRACT["required_t5_2_editor_sha256"]:
        raise VisualStudioBridgeError("T5.2 Visual Studio editor audit changed.")

    hashes = {}
    for relative in _EXPECTED_CONTRACT["required_files"]:
        path = selected / str(relative)
        if not path.is_file():
            raise VisualStudioBridgeError(f"T5.3 bridge file is missing: {relative}.")
        hashes[str(relative)] = _source_sha256(path)
    if hashes != dict(_EXPECTED_CONTRACT["file_sha256"]):
        changed = tuple(
            name for name in _EXPECTED_CONTRACT["required_files"]
            if hashes.get(str(name)) != dict(_EXPECTED_CONTRACT["file_sha256"]).get(str(name))
        )
        raise VisualStudioBridgeError(
            "T5.3 Visual Studio bridge source drifted: " + ", ".join(changed)
        )

    project = _parse_xml(selected / "src/ApexForge.VisualStudio/ApexForge.VisualStudio.csproj")
    package_items = tuple(_children(project, "PackageReference"))
    language_packages = tuple(
        item for item in package_items
        if item.attrib.get("Include") == "Microsoft.VisualStudio.LanguageServer.Client"
    )
    if len(language_packages) != 1:
        raise VisualStudioBridgeError(
            "T5.3 requires one Microsoft.VisualStudio.LanguageServer.Client package reference."
        )
    package = language_packages[0]
    if package.attrib.get("Version") != "17.14.60":
        raise VisualStudioBridgeError("T5.3 language-client package version changed.")
    if package.attrib.get("ExcludeAssets") != "runtime":
        raise VisualStudioBridgeError(
            "T5.3 must consume the Visual Studio-hosted language-client runtime."
        )

    content = _read_text(selected / "src/ApexForge.VisualStudio/Content/ApexForgeContentType.cs")
    for marker in (
        "using Microsoft.VisualStudio.LanguageServer.Client;",
        "[BaseDefinition(CodeRemoteContentDefinition.CodeRemoteContentTypeName)]",
        "[FileExtension(FileExtension)]",
        "[ContentType(Name)]",
    ):
        _require_marker(content, marker, "ApexForgeContentType.cs")
    if '[BaseDefinition("text")]' in content:
        raise VisualStudioBridgeError("T5.3 content type must use the Visual Studio code-remote base.")

    status = _read_text(selected / "src/ApexForge.VisualStudio/Commands/ShowStatusCommand.cs")
    for marker in (
        "Language-server bridge: active (AFP-P10-T5.3).",
        "ApexForgeLanguageServerTrace.LogPath",
    ):
        _require_marker(status, marker, "ShowStatusCommand.cs")
    if "deferred to AFP-P10-T5.3" in status:
        raise VisualStudioBridgeError("T5.3 status command still reports a deferred bridge.")

    locator = _read_text(selected / "src/ApexForge.VisualStudio/LanguageServer/ApexForgeLanguageServerLocator.cs")
    for marker in (
        'RepositoryEnvironmentVariable = "APEXFORGE_REPOSITORY_ROOT"',
        'PythonEnvironmentVariable = "APEXFORGE_PYTHON"',
        'RelativeServerScript = @"apexforge\\apexforge_lsp.py"',
        'pythonExecutable = "py.exe"',
        'Path.Combine(profile, "source", "repos", "ApexForge")',
        'Path.Combine(profile, "Documents", "GitHub", "ApexForge")',
        'depth < 12',
        'File.Exists(Path.Combine(candidate, "apexforge", "language_server", "integration.py"))',
        'QuoteArgument(scriptPath) + " --stdio"',
    ):
        _require_marker(locator, marker, "ApexForgeLanguageServerLocator.cs")

    trace = _read_text(selected / "src/ApexForge.VisualStudio/LanguageServer/ApexForgeLanguageServerTrace.cs")
    for marker in (
        '"visualstudio-language-client.log"',
        'Trace.WriteLine(line, "ApexForge Language Server")',
        'new UTF8Encoding(encoderShouldEmitUTF8Identifier: false)',
        'lock (Gate)',
    ):
        _require_marker(trace, marker, "ApexForgeLanguageServerTrace.cs")

    client = _read_text(selected / "src/ApexForge.VisualStudio/LanguageServer/ApexForgeLanguageClient.cs")
    for marker in (
        '[Export(typeof(ILanguageClient))]',
        '[ContentType(ApexForgeContentType.Name)]',
        'public sealed class ApexForgeLanguageClient : ILanguageClient',
        'public async Task<Connection> ActivateAsync(CancellationToken token)',
        'RedirectStandardInput = true',
        'RedirectStandardOutput = true',
        'RedirectStandardError = true',
        'UseShellExecute = false',
        'CreateNoWindow = true',
        'startInfo.EnvironmentVariables["PYTHONUTF8"] = "1"',
        'startInfo.EnvironmentVariables["PYTHONDONTWRITEBYTECODE"] = "1"',
        'process.BeginErrorReadLine()',
        'return new Connection(',
        'process.StandardOutput.BaseStream',
        'process.StandardInput.BaseStream',
        'await handler.InvokeAsync(this, EventArgs.Empty)',
        'public bool ShowNotificationOnInitializeFailed => true',
        'OnServerInitializeFailedAsync(Exception exception)',
        'Task<InitializationFailureContext> OnServerInitializeFailedAsync(',
        'ILanguageClientInitializationInfo initializationState',
        'OnServerInitializedAsync()',
        'TryTerminate(previous)',
        'process.WaitForExit(2000)',
    ):
        _require_marker(client, marker, "ApexForgeLanguageClient.cs")
    if 'ProcessWindowStyle' in client or 'UseShellExecute = true' in client:
        raise VisualStudioBridgeError("T5.3 must use a headless redirected stdio process.")

    contract = dict(_EXPECTED_CONTRACT)
    contract["file_sha256"] = hashes
    fingerprint = _sha256(_canonical_json(contract))
    if fingerprint != CANONICAL_VISUAL_STUDIO_BRIDGE_SHA256:
        raise VisualStudioBridgeError(
            f"Visual Studio bridge fingerprint changed: {fingerprint}."
        )
    return VisualStudioBridgeAudit(selected, fingerprint, hashes)


def audit_visualstudio_bridge_vsix(path: Path | str) -> VisualStudioBridgeVsixAudit:
    selected = Path(path).resolve()
    if not selected.is_file():
        raise VisualStudioBridgeError(f"VSIX file does not exist: {selected}.")
    try:
        archive = zipfile.ZipFile(selected, "r")
    except (OSError, zipfile.BadZipFile) as error:
        raise VisualStudioBridgeError(f"Invalid VSIX archive: {error}") from error

    with archive:
        names = tuple(archive.namelist())
        folded = {Path(name).name.casefold() for name in names}
        if "apexforge.visualstudio.dll" not in folded:
            raise VisualStudioBridgeError("T5.3 VSIX omitted ApexForge.VisualStudio.dll.")
        forbidden = tuple(
            name for name in _EXPECTED_CONTRACT["vsix_host_runtime_assemblies_forbidden"]
            if str(name).casefold() in folded
        )
        if forbidden:
            raise VisualStudioBridgeError(
                "T5.3 VSIX bundled Visual Studio-hosted runtime assemblies: "
                + ", ".join(str(item) for item in forbidden)
            )
        return VisualStudioBridgeVsixAudit(
            path=selected,
            entry_count=len(names),
            vsix_sha256=_sha256(selected.read_bytes()),
        )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", help="Visual Studio extension root")
    parser.add_argument("--check", action="store_true", help="audit the T5.3 bridge source")
    parser.add_argument("--check-vsix", metavar="PATH", help="audit a built T5.3 VSIX")
    parser.add_argument("--contract", action="store_true", help="print the deterministic T5.3 fingerprint")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    arguments = _parser().parse_args(argv)
    try:
        if arguments.contract:
            print(CANONICAL_VISUAL_STUDIO_BRIDGE_SHA256)
            return 0
        if arguments.check_vsix:
            audit = audit_visualstudio_bridge_vsix(arguments.check_vsix)
            print(f"Visual Studio T5.3 VSIX audit passed: {audit.vsix_sha256}")
            return 0
        if arguments.check:
            if not arguments.root:
                raise VisualStudioBridgeError("--check requires the Visual Studio extension root.")
            audit = audit_visualstudio_bridge(arguments.root)
            print(f"Visual Studio T5.3 bridge audit passed: {audit.bridge_sha256}")
            return 0
        _parser().print_help()
        return 0
    except VisualStudioBridgeError as error:
        print(str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
