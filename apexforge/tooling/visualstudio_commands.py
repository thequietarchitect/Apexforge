"""AFP-P10-T5.6 Visual Studio native editor-command auditor."""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import sys
from typing import Final, Mapping, Optional, Sequence, Union

from tooling.visualstudio_intelligence import (
    CANONICAL_VISUAL_STUDIO_INTELLIGENCE_SHA256,
    VisualStudioIntelligenceError,
    audit_visualstudio_intelligence,
    audit_visualstudio_intelligence_vsix,
)

P10_T5_VISUAL_STUDIO_COMMANDS_VERSION: Final[str] = "10-T5.6"
VISUAL_STUDIO_COMMANDS_SCHEMA: Final[int] = 1
VISUAL_STUDIO_COMMANDS_KIND: Final[str] = "apexforge.visual-studio-editor-commands"

_REQUIRED_FILES: Final[Mapping[str, str]] = {
    "src/ApexForge.VisualStudio/ApexForgePackage.cs":
        "90a2031cdb6d14cabd17f942a7135c32a500ed579fbc2c517bedd4cde55bda21",
    "src/ApexForge.VisualStudio/Commands/ShowStatusCommand.cs":
        "fb01f2da4954848663daf6a127c92bd3b17fcd5309536dfd82e9dbe68a4eeb44",
    "src/ApexForge.VisualStudio/Commands/RestartLanguageServerCommand.cs":
        "b68dfd04d3c764b2343c56b79f139c859deb530fc889191ec176cbd4b3a4d54d",
    "src/ApexForge.VisualStudio/Commands/OpenLanguageServerLogCommand.cs":
        "376405cfc13c5e0790ce14be9709704ba7e9d713fd8849fc2595dcab52f9e1f5",
    "src/ApexForge.VisualStudio/LanguageServer/ApexForgeLanguageClient.cs":
        "b5191aabaf9d2e354e80ee7b2709b914c0aa15beca49a82ac068e0971bab57d1",
    "src/ApexForge.VisualStudio/Resources/ApexForge.vsct":
        "7ee2948a9d39b288975527f89999bfc55489b554f9acecce0b7d31ca97fc3131",
    "VISUAL_STUDIO_LANGUAGE_FEATURES.md":
        "e921fbcb138e80c3dd7ccc75f4078cbb4e92ca209b7581dc8277002fbfece5b7",
}

_COMMANDS: Final[tuple[Mapping[str, object], ...]] = (
    {
        "id": 0x0100,
        "symbol": "ShowStatusCommandId",
        "text": "ApexForge Extension Status",
    },
    {
        "id": 0x0101,
        "symbol": "RestartLanguageServerCommandId",
        "text": "Restart ApexForge Language Server",
    },
    {
        "id": 0x0102,
        "symbol": "OpenLanguageServerLogCommandId",
        "text": "Open ApexForge Language Server Log",
    },
)


class VisualStudioCommandsError(ValueError):
    code: Final[str] = "APX-VS-006"

    def __init__(self, message: str) -> None:
        if type(message) is not str or not message:
            raise ValueError("VisualStudioCommandsError.message must be non-empty.")
        self.message = message
        super().__init__(f"[{self.code}] {message}")


@dataclass(frozen=True)
class VisualStudioCommandsAudit:
    root: Path
    commands_sha256: str
    command_count: int
    file_sha256: Mapping[str, str]


@dataclass(frozen=True)
class VisualStudioCommandsVsixAudit:
    path: Path
    vsix_sha256: str


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError) as error:
        raise VisualStudioCommandsError(
            f"Could not read UTF-8 file {path}: {error}"
        ) from error


def _source_sha256(path: Path) -> str:
    text = _read_text(path).replace("\r\n", "\n").replace("\r", "\n")
    return _sha256(text.encode("utf-8"))


def _require_marker(text: str, marker: str, owner: str) -> None:
    if marker not in text:
        raise VisualStudioCommandsError(
            f"{owner} omitted required marker {marker!r}."
        )


def visual_studio_commands_contract() -> Mapping[str, object]:
    return {
        "schema": VISUAL_STUDIO_COMMANDS_SCHEMA,
        "kind": VISUAL_STUDIO_COMMANDS_KIND,
        "commands_version": P10_T5_VISUAL_STUDIO_COMMANDS_VERSION,
        "required_t5_5_intelligence_sha256":
            CANONICAL_VISUAL_STUDIO_INTELLIGENCE_SHA256,
        "menu": "Tools",
        "command_set": "744A30FD-DF87-5104-A449-A95DF8E526FA",
        "commands": _COMMANDS,
        "restart_lifecycle": (
            "StopAsync",
            "terminate surviving process",
            "StartAsync",
            "ActivateAsync",
            "await OnServerInitializedAsync",
            "document resynchronization grace",
        ),
        "restart_serialized": True,
        "restart_initialization_timeout_seconds": 15,
        "document_resynchronization_delay_milliseconds": 350,
        "restart_success_requires_initialized_server": True,
        "log_path": "%TEMP%/ApexForge/visualstudio-language-client.log",
        "native_format_document_preserved": True,
        "t4_server_modified": False,
        "file_sha256": dict(_REQUIRED_FILES),
    }


def visual_studio_commands_fingerprint() -> str:
    payload = json.dumps(
        visual_studio_commands_contract(),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return _sha256(payload)


CANONICAL_VISUAL_STUDIO_COMMANDS_SHA256: Final[str] = "4a3dbadee01faee40b69098530d270164baf1a2a0411d68f83d1aa60f9a9d5ce"


def audit_visualstudio_commands(
    root: Union[Path, str],
) -> VisualStudioCommandsAudit:
    selected = Path(root).resolve()
    if not selected.is_dir():
        raise VisualStudioCommandsError(
            f"Visual Studio extension root does not exist: {selected}."
        )

    try:
        intelligence = audit_visualstudio_intelligence(selected)
    except VisualStudioIntelligenceError as error:
        raise VisualStudioCommandsError(str(error)) from error
    if (
        intelligence.intelligence_sha256
        != CANONICAL_VISUAL_STUDIO_INTELLIGENCE_SHA256
    ):
        raise VisualStudioCommandsError(
            "Frozen T5.5 language-intelligence fingerprint changed."
        )

    observed_hashes: dict[str, str] = {}
    for relative, expected in _REQUIRED_FILES.items():
        path = selected / relative
        if not path.is_file():
            raise VisualStudioCommandsError(
                f"T5.6 Visual Studio command file is missing: {relative}."
            )
        observed = _source_sha256(path)
        observed_hashes[relative] = observed
        if observed != expected:
            raise VisualStudioCommandsError(
                f"T5.6 Visual Studio command source drifted: {relative}."
            )

    package = _read_text(
        selected / "src/ApexForge.VisualStudio/ApexForgePackage.cs"
    )
    for marker in (
        "ShowStatusCommand.InitializeAsync(this)",
        "RestartLanguageServerCommand.InitializeAsync(this)",
        "OpenLanguageServerLogCommand.InitializeAsync(this)",
    ):
        _require_marker(package, marker, "ApexForgePackage.cs")

    vsct = _read_text(
        selected / "src/ApexForge.VisualStudio/Resources/ApexForge.vsct"
    )
    for command in _COMMANDS:
        _require_marker(vsct, str(command["symbol"]), "ApexForge.vsct")
        _require_marker(vsct, str(command["text"]), "ApexForge.vsct")
        _require_marker(
            vsct,
            f'value="0x{int(command["id"]):04X}"',
            "ApexForge.vsct",
        )

    client = _read_text(
        selected
        / "src/ApexForge.VisualStudio/LanguageServer/ApexForgeLanguageClient.cs"
    )
    for marker in (
        "private AsyncEventHandler<EventArgs> stopAsync;",
        "add { stopAsync += value; }",
        "remove { stopAsync -= value; }",
        "internal static async Task<bool> RequestRestartAsync()",
        "private async Task<bool> RestartAsync()",
        "await restartGate.WaitAsync()",
        "await stopHandler.InvokeAsync(this, EventArgs.Empty)",
        "StopActiveProcess();",
        "await startHandler.InvokeAsync(this, EventArgs.Empty)",
        "int initializationBaseline = Volatile.Read(",
        "WaitForServerInitializationAsync(",
        "RecordServerInitialization(true)",
        "Interlocked.Increment(",
        "RestartReadinessPollInterval",
        "DocumentResynchronizationDelay",
        "restartGate.Release();",
    ):
        _require_marker(client, marker, "ApexForgeLanguageClient.cs")

    restart = _read_text(
        selected
        / "src/ApexForge.VisualStudio/Commands/RestartLanguageServerCommand.cs"
    )
    for marker in (
        "public const int CommandId = 0x0101;",
        "private void Execute(object sender, EventArgs eventArgs)",
        "private async Task ExecuteAsync()",
        "package.JoinableTaskFactory.RunAsync(ExecuteAsync).Task.Forget();",
        "ApexForgeLanguageClient.RequestRestartAsync()",
        "completed document resynchronization",
        "Open an .apex file and try again.",
    ):
        _require_marker(restart, marker, "RestartLanguageServerCommand.cs")
    for forbidden in (
        "private async void Execute",
        "ThreadHelper.JoinableTaskFactory.RunAsync",
        "TaskCompletionSource<bool>",
    ):
        if forbidden in restart:
            raise VisualStudioCommandsError(
                "RestartLanguageServerCommand.cs retained unsafe async pattern "
                + repr(forbidden)
                + "."
            )

    open_log = _read_text(
        selected
        / "src/ApexForge.VisualStudio/Commands/OpenLanguageServerLogCommand.cs"
    )
    for marker in (
        "public const int CommandId = 0x0102;",
        "ApexForgeLanguageServerTrace.LogPath",
        "UseShellExecute = true",
    ):
        _require_marker(open_log, marker, "OpenLanguageServerLogCommand.cs")

    status = _read_text(
        selected / "src/ApexForge.VisualStudio/Commands/ShowStatusCommand.cs"
    )
    for marker in (
        "Editor commands/restart/log: active (AFP-P10-T5.6).",
        "Language client loaded: ",
        "ApexForgeLanguageClient.IsLoaded",
    ):
        _require_marker(status, marker, "ShowStatusCommand.cs")

    guide = _read_text(selected / "VISUAL_STUDIO_LANGUAGE_FEATURES.md")
    for marker in (
        "AFP-P10-T5.6 — Native editor commands and controlled restart",
        "Restart ApexForge Language Server",
        "Open ApexForge Language Server Log",
        "StopAsync",
        "StartAsync",
        "Format Document",
    ):
        _require_marker(guide, marker, "VISUAL_STUDIO_LANGUAGE_FEATURES.md")

    observed = visual_studio_commands_fingerprint()
    if observed != CANONICAL_VISUAL_STUDIO_COMMANDS_SHA256:
        raise VisualStudioCommandsError(
            "T5.6 Visual Studio command fingerprint changed: " + observed
        )

    return VisualStudioCommandsAudit(
        root=selected,
        commands_sha256=observed,
        command_count=len(_COMMANDS),
        file_sha256=observed_hashes,
    )


def audit_visualstudio_commands_vsix(
    path: Union[Path, str],
) -> VisualStudioCommandsVsixAudit:
    selected = Path(path).resolve()
    try:
        predecessor = audit_visualstudio_intelligence_vsix(selected)
    except VisualStudioIntelligenceError as error:
        raise VisualStudioCommandsError(str(error)) from error
    return VisualStudioCommandsVsixAudit(
        path=selected,
        vsix_sha256=predecessor.vsix_sha256,
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", help="Visual Studio extension root")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--check-vsix", metavar="PATH")
    parser.add_argument("--contract", action="store_true")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    arguments = _parser().parse_args(argv)
    try:
        if arguments.contract:
            print(CANONICAL_VISUAL_STUDIO_COMMANDS_SHA256)
            return 0
        if arguments.check_vsix:
            audit = audit_visualstudio_commands_vsix(arguments.check_vsix)
            print(
                "Visual Studio T5.6 VSIX audit passed: "
                + audit.vsix_sha256
            )
            return 0
        if arguments.check:
            if not arguments.root:
                raise VisualStudioCommandsError(
                    "--check requires the Visual Studio extension root."
                )
            audit = audit_visualstudio_commands(arguments.root)
            print(
                "Visual Studio T5.6 command audit passed: "
                + audit.commands_sha256
            )
            return 0
        _parser().print_help()
        return 0
    except VisualStudioCommandsError as error:
        print(str(error), file=sys.stderr)
        return 1


__all__ = (
    "CANONICAL_VISUAL_STUDIO_COMMANDS_SHA256",
    "P10_T5_VISUAL_STUDIO_COMMANDS_VERSION",
    "VISUAL_STUDIO_COMMANDS_KIND",
    "VISUAL_STUDIO_COMMANDS_SCHEMA",
    "VisualStudioCommandsAudit",
    "VisualStudioCommandsError",
    "VisualStudioCommandsVsixAudit",
    "audit_visualstudio_commands",
    "audit_visualstudio_commands_vsix",
    "main",
    "visual_studio_commands_contract",
    "visual_studio_commands_fingerprint",
)


if __name__ == "__main__":
    raise SystemExit(main())
