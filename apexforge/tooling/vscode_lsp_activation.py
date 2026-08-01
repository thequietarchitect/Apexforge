"""AFP-P10-T4.3 VS Code language-server activation audit."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
from typing import Final, Mapping, Optional, Sequence, TextIO
from zipfile import BadZipFile, ZipFile

from language_server.diagnostics import CANONICAL_LSP_DIAGNOSTICS_SHA256
from language_server.server import CANONICAL_LSP_FOUNDATION_SHA256
from tooling.vscode_extension import (
    CANONICAL_VSCODE_FOUNDATION_SHA256,
    CANONICAL_VSCODE_LANGUAGE_ID,
    CANONICAL_VSCODE_PACKAGE_NAME,
    CANONICAL_VSCODE_PACKAGE_VERSION,
    CANONICAL_VSCODE_PUBLISHER,
)
from tooling.vscode_package import (
    CANONICAL_VSCODE_EXTENSION_ID,
    CANONICAL_VSCODE_PACKAGE_SHA256,
    packaging_fingerprint,
)
from tooling.vscode_syntax import CANONICAL_VSCODE_SYNTAX_SHA256


P10_T4_VSCODE_ACTIVATION_VERSION: Final[str] = "10-T4.3"
VSCODE_LSP_ACTIVATION_SCHEMA: Final[int] = 1
VSCODE_LSP_ACTIVATION_KIND: Final[str] = "apexforge.vscode-lsp-activation"

CANONICAL_EXTENSION_MAIN: Final[str] = "./extension.js"
CANONICAL_RUNTIME_CLIENT_PATH: Final[str] = "runtime/lsp-client.js"
CANONICAL_LANGUAGE_SERVER_GUIDE: Final[str] = "LANGUAGE_SERVER.md"
CANONICAL_SERVER_RELATIVE_PATH: Final[str] = "apexforge/apexforge_lsp.py"
CANONICAL_OUTPUT_CHANNEL: Final[str] = "ApexForge Language Server"
CANONICAL_WORKSPACE_MODEL: Final[str] = "one server process per workspace folder"

CANONICAL_ACTIVATION_EVENTS: Final[tuple[str, ...]] = (
    "onLanguage:apexforge",
    "workspaceContains:apexforge/apexforge_lsp.py",
)
CANONICAL_COMMANDS: Final[tuple[tuple[str, str], ...]] = (
    (
        "apexforge.showLanguageServerOutput",
        "ApexForge: Show Language Server Output",
    ),
    (
        "apexforge.restartLanguageServer",
        "ApexForge: Restart Language Server",
    ),
)
CANONICAL_SETTINGS: Final[Mapping[str, tuple[str, object, str]]] = {
    "apexforge.languageServer.pythonCommand": ("string", "", "resource"),
    "apexforge.languageServer.serverPath": (
        "string",
        CANONICAL_SERVER_RELATIVE_PATH,
        "resource",
    ),
    "apexforge.languageServer.trace": ("boolean", False, "resource"),
}
_RUNTIME_SOURCE_PATHS: Final[tuple[str, ...]] = (
    "extension.js",
    CANONICAL_RUNTIME_CLIENT_PATH,
    CANONICAL_LANGUAGE_SERVER_GUIDE,
)

# Compatibility projection: later editor slices may extend the runtime sources,
# but the frozen T4.3 fingerprint remains scoped to the exact bytes that were
# present when activation/process lifecycle support was frozen.
_FROZEN_T4_3_RUNTIME_HASHES: Final[Mapping[str, str]] = {
    "extension.js": "a7ae9b7453012e75bdf479ddc6fcbc80cf658ca3d2f5c1c1555fca08b2bcf4ca",
    CANONICAL_RUNTIME_CLIENT_PATH: (
        "2481320a388bf48087e00094d9e46693fc8ba9f86dec140281aef0aa8ce67000"
    ),
    CANONICAL_LANGUAGE_SERVER_GUIDE: (
        "657eaa2d5d8ab9002bc0d74c932440d354c2165681c1dc5b24678ea92a62a7f9"
    ),
}

# Filled after the exact public projection is serialized.
CANONICAL_VSCODE_LSP_ACTIVATION_SHA256: Final[str] = (
    "b74759e09a2de60a9ca78d6baa36d0d608b650858b6220f3ab4b3f2916a940d6"
)


class VSCodeLSPActivationError(ValueError):
    """The T4.3 VS Code activation surface is invalid."""

    code: Final[str] = "APX-VSCODE-004"

    def __init__(self, message: str) -> None:
        if type(message) is not str or not message:
            raise ValueError("VSCodeLSPActivationError.message must be non-empty.")
        self.message = message
        super().__init__(f"[{self.code}] {message}")


@dataclass(frozen=True)
class VSCodeLSPActivationAudit:
    extension_root: Path
    extension_id: str
    package_version: str
    activation_events: tuple[str, ...]
    command_count: int
    setting_count: int
    runtime_file_count: int
    activation_sha256: str


@dataclass(frozen=True)
class VSCodeLSPVSIXAudit:
    vsix_path: Path
    archive_file_count: int
    activation_sha256: str
    vsix_sha256: str


def _require_mapping(value: object, owner: str) -> Mapping[str, object]:
    if type(value) is not dict:
        raise VSCodeLSPActivationError(f"{owner} must be a JSON object.")
    return value


def _require_list(value: object, owner: str) -> list[object]:
    if type(value) is not list:
        raise VSCodeLSPActivationError(f"{owner} must be a JSON array.")
    return value


def _require_exact(value: object, expected: object, owner: str) -> None:
    if value != expected:
        raise VSCodeLSPActivationError(
            f"{owner} changed; expected {expected!r}, received {value!r}."
        )


def _read_bytes(path: Path, owner: str) -> bytes:
    try:
        return path.read_bytes()
    except OSError as error:
        raise VSCodeLSPActivationError(
            f"Could not read {owner} at {path}: {error}."
        ) from error


def _read_json(path: Path, owner: str) -> Mapping[str, object]:
    data = _read_bytes(path, owner)
    try:
        value = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise VSCodeLSPActivationError(
            f"{owner} is not valid UTF-8 JSON: {error}."
        ) from error
    return _require_mapping(value, owner)


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(_read_bytes(path, str(path)))


def _validate_frozen_dependencies(extension_root: Path) -> None:
    _require_exact(
        CANONICAL_VSCODE_FOUNDATION_SHA256,
        "2a8478ea163312d211556f35f8c2fa99fd16eb93db81f829c33d8d688fb685e2",
        "T3.1 foundation SHA-256",
    )
    _require_exact(
        CANONICAL_VSCODE_SYNTAX_SHA256,
        "cb8e7e35005e7ba8fe2f933cf45247aaf5a8e8a4e7cbc1dd1bbe07ef6c584466",
        "T3.2 syntax SHA-256",
    )
    _require_exact(
        packaging_fingerprint(extension_root),
        CANONICAL_VSCODE_PACKAGE_SHA256,
        "T3.3 projected packaging SHA-256",
    )
    _require_exact(
        CANONICAL_VSCODE_PACKAGE_SHA256,
        "75a39c44354d4f647ab46cb6aba42adf00f5396c7563b1433ff2d93d66e9498c",
        "T3.3 packaging SHA-256",
    )
    _require_exact(
        CANONICAL_LSP_FOUNDATION_SHA256,
        "3297a9ab09f73ac52b2a67a1fd463b281e2ef5d997a1ba0342de8b6ff6e49b4d",
        "T4.1 foundation SHA-256",
    )
    _require_exact(
        CANONICAL_LSP_DIAGNOSTICS_SHA256,
        "7b3ddf129201c64ecc839af197cec945c09388112a8cf080977d43aec9f66a5f",
        "T4.2 diagnostics SHA-256",
    )


def _validate_manifest(package: Mapping[str, object]) -> Mapping[str, object]:
    _require_exact(package.get("name"), CANONICAL_VSCODE_PACKAGE_NAME, "package name")
    _require_exact(
        package.get("version"),
        CANONICAL_VSCODE_PACKAGE_VERSION,
        "package version",
    )
    _require_exact(
        package.get("publisher"),
        CANONICAL_VSCODE_PUBLISHER,
        "package publisher",
    )
    _require_exact(package.get("main"), CANONICAL_EXTENSION_MAIN, "package main")
    _require_exact(package.get("extensionKind"), ["workspace"], "extensionKind")
    _require_exact(
        package.get("activationEvents"),
        list(CANONICAL_ACTIVATION_EVENTS),
        "activationEvents",
    )

    contributes = _require_mapping(package.get("contributes"), "package contributes")
    commands = _require_list(contributes.get("commands"), "package commands")
    observed_commands = tuple(
        (
            _require_mapping(item, f"command[{index}]").get("command"),
            _require_mapping(item, f"command[{index}]").get("title"),
        )
        for index, item in enumerate(commands)
    )
    _require_exact(observed_commands, CANONICAL_COMMANDS, "command contributions")

    configuration = _require_mapping(
        contributes.get("configuration"),
        "package configuration",
    )
    _require_exact(
        configuration.get("title"),
        "ApexForge Language Server",
        "configuration title",
    )
    properties = _require_mapping(
        configuration.get("properties"),
        "package configuration properties",
    )
    _require_exact(
        tuple(properties),
        tuple(CANONICAL_SETTINGS),
        "configuration property order",
    )
    for name, expected in CANONICAL_SETTINGS.items():
        setting = _require_mapping(properties.get(name), f"setting {name}")
        observed = (
            setting.get("type"),
            setting.get("default"),
            setting.get("scope"),
        )
        _require_exact(observed, expected, f"setting {name}")

    return contributes


def _validate_runtime_sources(extension_root: Path) -> Mapping[str, str]:
    hashes: dict[str, str] = {}
    source_text: dict[str, str] = {}

    for relative_name in _RUNTIME_SOURCE_PATHS:
        path = extension_root / PurePosixPath(relative_name)
        data = _read_bytes(path, f"T4.3 runtime source {relative_name}")
        hashes[relative_name] = _sha256_bytes(data)
        try:
            source_text[relative_name] = data.decode("utf-8")
        except UnicodeDecodeError as error:
            raise VSCodeLSPActivationError(
                f"T4.3 runtime source {relative_name!r} must be UTF-8."
            ) from error

    extension_markers = (
        "exports.activate = activate",
        "exports.deactivate = deactivate",
        "createOutputChannel",
        "createDiagnosticCollection",
        "onDidOpenTextDocument",
        "onDidChangeTextDocument",
        "onDidCloseTextDocument",
        "onDidChangeWorkspaceFolders",
        "apexforge.restartLanguageServer",
        "apexforge.showLanguageServerOutput",
        "textDocument/publishDiagnostics",
    )
    for marker in extension_markers:
        if marker not in source_text["extension.js"]:
            raise VSCodeLSPActivationError(
                f"extension.js omitted required activation marker {marker!r}."
            )

    client_markers = (
        "class LspProcessClient",
        "class LspMessageReader",
        "Content-Length:",
        "sendRequest('initialize'",
        "sendRequest('shutdown'",
        "sendNotification('exit'",
        "childProcess.spawn",
    )
    for marker in client_markers:
        if marker not in source_text[CANONICAL_RUNTIME_CLIENT_PATH]:
            raise VSCodeLSPActivationError(
                "runtime/lsp-client.js omitted required lifecycle marker "
                f"{marker!r}."
            )

    return hashes


def activation_contract(
    package: Mapping[str, object],
    runtime_hashes: Mapping[str, str],
) -> Mapping[str, object]:
    contributes = _require_mapping(package.get("contributes"), "package contributes")
    configuration = _require_mapping(
        contributes.get("configuration"),
        "package configuration",
    )
    properties = _require_mapping(
        configuration.get("properties"),
        "package configuration properties",
    )

    return {
        "schema": VSCODE_LSP_ACTIVATION_SCHEMA,
        "kind": VSCODE_LSP_ACTIVATION_KIND,
        "activation_version": P10_T4_VSCODE_ACTIVATION_VERSION,
        "extension": {
            "id": CANONICAL_VSCODE_EXTENSION_ID,
            "version": CANONICAL_VSCODE_PACKAGE_VERSION,
            "main": package.get("main"),
            "extension_kind": package.get("extensionKind"),
            "activation_events": package.get("activationEvents"),
        },
        "workspace_model": CANONICAL_WORKSPACE_MODEL,
        "server": {
            "entry_point": CANONICAL_SERVER_RELATIVE_PATH,
            "arguments": ("--stdio",),
            "transport": "jsonrpc-2.0-content-length-stdio",
            "lifecycle": (
                "initialize",
                "initialized",
                "shutdown",
                "exit",
            ),
        },
        "document_forwarding": (
            "textDocument/didOpen",
            "textDocument/didChange",
            "textDocument/didClose",
        ),
        "diagnostics": "textDocument/publishDiagnostics",
        "output_channel": CANONICAL_OUTPUT_CHANNEL,
        "commands": CANONICAL_COMMANDS,
        "settings": {
            name: {
                "type": properties[name].get("type"),
                "default": properties[name].get("default"),
                "scope": properties[name].get("scope"),
            }
            for name in CANONICAL_SETTINGS
        },
        "runtime_hashes": {
            name: _FROZEN_T4_3_RUNTIME_HASHES[name]
            for name in _RUNTIME_SOURCE_PATHS
        },
        "frozen_dependencies": {
            "t3_1": CANONICAL_VSCODE_FOUNDATION_SHA256,
            "t3_2": CANONICAL_VSCODE_SYNTAX_SHA256,
            "t3_3": CANONICAL_VSCODE_PACKAGE_SHA256,
            "t4_1": CANONICAL_LSP_FOUNDATION_SHA256,
            "t4_2": CANONICAL_LSP_DIAGNOSTICS_SHA256,
        },
    }


def activation_fingerprint(
    package: Mapping[str, object],
    runtime_hashes: Mapping[str, str],
) -> str:
    for name in _RUNTIME_SOURCE_PATHS:
        if name not in runtime_hashes:
            raise VSCodeLSPActivationError(
                f"T4.3 runtime hash projection is missing {name!r}."
            )
    payload = json.dumps(
        activation_contract(package, runtime_hashes),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def audit_vscode_lsp_activation(
    extension_root: Path,
) -> VSCodeLSPActivationAudit:
    root = Path(extension_root).resolve()
    if not root.is_dir():
        raise VSCodeLSPActivationError(
            f"VS Code extension directory does not exist: {root}."
        )

    package = _read_json(root / "package.json", "VS Code package manifest")
    _validate_manifest(package)
    _validate_frozen_dependencies(root)
    runtime_hashes = _validate_runtime_sources(root)

    observed = activation_fingerprint(package, runtime_hashes)
    if observed != CANONICAL_VSCODE_LSP_ACTIVATION_SHA256:
        raise VSCodeLSPActivationError(
            "VS Code LSP activation fingerprint changed; expected "
            f"{CANONICAL_VSCODE_LSP_ACTIVATION_SHA256}, received {observed}."
        )

    return VSCodeLSPActivationAudit(
        extension_root=root,
        extension_id=CANONICAL_VSCODE_EXTENSION_ID,
        package_version=CANONICAL_VSCODE_PACKAGE_VERSION,
        activation_events=CANONICAL_ACTIVATION_EVENTS,
        command_count=len(CANONICAL_COMMANDS),
        setting_count=len(CANONICAL_SETTINGS),
        runtime_file_count=len(_RUNTIME_SOURCE_PATHS),
        activation_sha256=observed,
    )


def _safe_archive_name(name: str) -> str:
    if type(name) is not str or not name or "\\" in name:
        raise VSCodeLSPActivationError(f"Unsafe VSIX archive path {name!r}.")
    path = PurePosixPath(name)
    if path.is_absolute() or any(part in ("", ".", "..") for part in path.parts):
        raise VSCodeLSPActivationError(f"Unsafe VSIX archive path {name!r}.")
    return path.as_posix()


def _archive_index(archive: ZipFile) -> Mapping[str, str]:
    index: dict[str, str] = {}
    for info in archive.infolist():
        if info.is_dir():
            continue
        normalized = _safe_archive_name(info.filename)
        folded = normalized.casefold()
        if folded in index:
            raise VSCodeLSPActivationError(
                f"VSIX contains duplicate case-insensitive path {normalized!r}."
            )
        index[folded] = normalized
    return index


def audit_vscode_lsp_vsix(
    extension_root: Path,
    vsix_path: Path,
) -> VSCodeLSPVSIXAudit:
    source_audit = audit_vscode_lsp_activation(extension_root)
    package_path = Path(vsix_path).resolve()
    if not package_path.is_file():
        raise VSCodeLSPActivationError(f"VSIX file does not exist: {package_path}.")

    required = {
        "extension/package.json": "package.json",
        "extension/extension.js": "extension.js",
        "extension/runtime/lsp-client.js": CANONICAL_RUNTIME_CLIENT_PATH,
        "extension/language_server.md": CANONICAL_LANGUAGE_SERVER_GUIDE,
    }

    try:
        with ZipFile(package_path, "r") as archive:
            index = _archive_index(archive)
            missing = tuple(
                sorted(name for name in required if name not in index)
            )
            if missing:
                raise VSCodeLSPActivationError(
                    f"VSIX is missing T4.3 runtime files: {missing}."
                )

            for archive_name, source_name in required.items():
                observed = archive.read(index[archive_name])
                expected = _read_bytes(
                    Path(extension_root).resolve() / PurePosixPath(source_name),
                    f"canonical T4.3 source {source_name}",
                )
                if observed != expected:
                    raise VSCodeLSPActivationError(
                        f"VSIX payload differs from T4.3 source {source_name!r}."
                    )

            embedded_package = json.loads(
                archive.read(index["extension/package.json"]).decode("utf-8")
            )
            _validate_manifest(_require_mapping(embedded_package, "embedded package"))
            archive_count = len(index)
    except (BadZipFile, OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise VSCodeLSPActivationError(
            f"Could not audit VSIX {package_path}: {error}."
        ) from error

    return VSCodeLSPVSIXAudit(
        vsix_path=package_path,
        archive_file_count=archive_count,
        activation_sha256=source_audit.activation_sha256,
        vsix_sha256=_sha256_file(package_path),
    )


def check_node_syntax(
    extension_root: Path,
    *,
    node_command: Optional[str] = None,
) -> tuple[str, ...]:
    selected = node_command or shutil.which("node")
    if not selected:
        raise VSCodeLSPActivationError("Node.js was not found on PATH.")

    checked: list[str] = []
    for relative_name in ("extension.js", CANONICAL_RUNTIME_CLIENT_PATH):
        path = Path(extension_root).resolve() / PurePosixPath(relative_name)
        completed = subprocess.run(
            (selected, "--check", str(path)),
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode != 0:
            details = (completed.stderr or completed.stdout or "").strip()
            raise VSCodeLSPActivationError(
                f"Node.js syntax check failed for {relative_name!r}"
                + (f": {details}" if details else ".")
            )
        checked.append(relative_name)
    return tuple(checked)


def main(
    argv: Optional[Sequence[str]] = None,
    *,
    stdout: TextIO = sys.stdout,
    stderr: TextIO = sys.stderr,
) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m tooling.vscode_lsp_activation",
        description="Audit AFP-P10-T4.3 VS Code language-server activation.",
    )
    parser.add_argument("extension_root", type=Path)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--check-vsix", type=Path, metavar="VSIX")
    mode.add_argument("--contract", action="store_true")
    arguments = parser.parse_args(tuple(argv) if argv is not None else None)

    try:
        if arguments.contract:
            audit_vscode_lsp_activation(arguments.extension_root)
            print(CANONICAL_VSCODE_LSP_ACTIVATION_SHA256, file=stdout)
            return 0

        if arguments.check_vsix is not None:
            audit = audit_vscode_lsp_vsix(
                arguments.extension_root,
                arguments.check_vsix,
            )
            print("AFP-P10-T4.3 VS Code LSP VSIX audit passed.", file=stdout)
            print(f"Archive files: {audit.archive_file_count}", file=stdout)
            print(f"Activation SHA-256: {audit.activation_sha256}", file=stdout)
            print(f"VSIX SHA-256: {audit.vsix_sha256}", file=stdout)
            return 0

        audit = audit_vscode_lsp_activation(arguments.extension_root)
        checked = check_node_syntax(arguments.extension_root)
        print("AFP-P10-T4.3 VS Code LSP activation check passed.", file=stdout)
        print(f"Extension ID: {audit.extension_id}", file=stdout)
        print(f"Runtime files: {audit.runtime_file_count}", file=stdout)
        print(f"Node syntax files: {len(checked)}", file=stdout)
        print(f"Activation SHA-256: {audit.activation_sha256}", file=stdout)
        return 0
    except VSCodeLSPActivationError as error:
        print(str(error), file=stderr)
        return 1


__all__ = (
    "CANONICAL_ACTIVATION_EVENTS",
    "CANONICAL_COMMANDS",
    "CANONICAL_EXTENSION_MAIN",
    "CANONICAL_LANGUAGE_SERVER_GUIDE",
    "CANONICAL_OUTPUT_CHANNEL",
    "CANONICAL_RUNTIME_CLIENT_PATH",
    "CANONICAL_SERVER_RELATIVE_PATH",
    "CANONICAL_SETTINGS",
    "CANONICAL_VSCODE_LSP_ACTIVATION_SHA256",
    "P10_T4_VSCODE_ACTIVATION_VERSION",
    "VSCODE_LSP_ACTIVATION_KIND",
    "VSCODE_LSP_ACTIVATION_SCHEMA",
    "VSCodeLSPActivationAudit",
    "VSCodeLSPActivationError",
    "VSCodeLSPVSIXAudit",
    "activation_contract",
    "activation_fingerprint",
    "audit_vscode_lsp_activation",
    "audit_vscode_lsp_vsix",
    "check_node_syntax",
    "main",
)


if __name__ == "__main__":
    raise SystemExit(main())
