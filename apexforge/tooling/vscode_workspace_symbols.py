"""AFP-P10-T4.9 VS Code workspace-symbol integration audit."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
import sys
from typing import Final, Mapping, Optional, Sequence, TextIO
from zipfile import BadZipFile, ZipFile

from language_server.workspace_symbols import CANONICAL_WORKSPACE_SYMBOLS_SHA256
from tooling.vscode_lsp_activation import (
    CANONICAL_LANGUAGE_SERVER_GUIDE,
    CANONICAL_RUNTIME_CLIENT_PATH,
)
from tooling.vscode_package import (
    CANONICAL_VSCODE_EXTENSION_ID,
    CANONICAL_VSCODE_PACKAGE_VERSION,
)
from tooling.vscode_references_rename import (
    CANONICAL_VSCODE_REFERENCES_RENAME_SHA256,
    VSCodeReferencesRenameError,
    audit_vscode_references_rename,
)


P10_T4_VSCODE_WORKSPACE_SYMBOLS_VERSION: Final[str] = "10-T4.9"
VSCODE_WORKSPACE_SYMBOLS_SCHEMA: Final[int] = 1
VSCODE_WORKSPACE_SYMBOLS_KIND: Final[str] = "apexforge.vscode-workspace-symbols"
WORKSPACE_SYMBOL_METHOD: Final[str] = "workspace/symbol"
WORKSPACE_SYMBOL_PROVIDER: Final[str] = "registerWorkspaceSymbolProvider"

_RUNTIME_SOURCE_PATHS: Final[tuple[str, ...]] = (
    "extension.js",
    CANONICAL_RUNTIME_CLIENT_PATH,
    CANONICAL_LANGUAGE_SERVER_GUIDE,
)

CANONICAL_VSCODE_WORKSPACE_SYMBOLS_SHA256: Final[str] = "ddf809a166f95fed8215a2a6cbcf11f0f318199d5dfb8f719fa09ec49e60c9aa"


class VSCodeWorkspaceSymbolsError(ValueError):
    code: Final[str] = "APX-VSCODE-010"

    def __init__(self, message: str) -> None:
        if type(message) is not str or not message:
            raise ValueError("VSCodeWorkspaceSymbolsError.message must be non-empty.")
        self.message = message
        super().__init__(f"[{self.code}] {message}")


@dataclass(frozen=True)
class VSCodeWorkspaceSymbolsAudit:
    extension_root: Path
    extension_id: str
    package_version: str
    runtime_file_count: int
    workspace_symbols_sha256: str


@dataclass(frozen=True)
class VSCodeWorkspaceSymbolsVSIXAudit:
    vsix_path: Path
    archive_file_count: int
    workspace_symbols_sha256: str
    vsix_sha256: str


def _read_bytes(path: Path, owner: str) -> bytes:
    try:
        return path.read_bytes()
    except OSError as error:
        raise VSCodeWorkspaceSymbolsError(
            f"Could not read {owner} at {path}: {error}."
        ) from error


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(_read_bytes(path, str(path)))


def _runtime_hashes(extension_root: Path) -> Mapping[str, str]:
    hashes: dict[str, str] = {}
    texts: dict[str, str] = {}
    for name in _RUNTIME_SOURCE_PATHS:
        data = _read_bytes(
            extension_root / PurePosixPath(name),
            f"T4.9 runtime source {name}",
        )
        hashes[name] = _sha256_bytes(data)
        try:
            texts[name] = data.decode("utf-8")
        except UnicodeDecodeError as error:
            raise VSCodeWorkspaceSymbolsError(
                f"T4.9 runtime source {name!r} must be UTF-8."
            ) from error

    extension_markers = (
        "registerWorkspaceSymbolProvider",
        "provideWorkspaceSymbols",
        "workspace/symbol",
        "convertWorkspaceSymbol",
        "new vscode.SymbolInformation",
        "workspaceSymbols(query, token)",
        "workspace: {",
        "symbol: {",
        "dynamicRegistration: false",
    )
    for marker in extension_markers:
        if marker not in texts["extension.js"]:
            raise VSCodeWorkspaceSymbolsError(
                f"extension.js omitted T4.9 marker {marker!r}."
            )

    guide_markers = (
        "workspace/symbol",
        "Ctrl+T",
        "Go to Symbol in Workspace",
        "read-only",
        "unsaved open-document",
        "cross-file",
        "Formatting",
    )
    for marker in guide_markers:
        if marker not in texts[CANONICAL_LANGUAGE_SERVER_GUIDE]:
            raise VSCodeWorkspaceSymbolsError(
                f"LANGUAGE_SERVER.md omitted T4.9 marker {marker!r}."
            )
    return hashes


def workspace_symbols_contract(runtime_hashes: Mapping[str, str]) -> Mapping[str, object]:
    return {
        "schema": VSCODE_WORKSPACE_SYMBOLS_SCHEMA,
        "kind": VSCODE_WORKSPACE_SYMBOLS_KIND,
        "workspace_symbols_version": P10_T4_VSCODE_WORKSPACE_SYMBOLS_VERSION,
        "extension": {
            "id": CANONICAL_VSCODE_EXTENSION_ID,
            "version": CANONICAL_VSCODE_PACKAGE_VERSION,
        },
        "method": WORKSPACE_SYMBOL_METHOD,
        "provider": WORKSPACE_SYMBOL_PROVIDER,
        "result": "vscode.SymbolInformation[]",
        "workspace_model": "one server process per workspace folder",
        "multi_root_merge": "deterministic provider aggregation",
        "server_workspace_symbols_sha256": CANONICAL_WORKSPACE_SYMBOLS_SHA256,
        "frozen_references_rename_sha256": CANONICAL_VSCODE_REFERENCES_RENAME_SHA256,
        "runtime_hashes": dict(runtime_hashes),
        "features_deferred": (
            "persistent_index",
            "workspace_symbol_resolve",
            "cross_file_definition",
            "workspace_references",
            "cross_file_rename",
            "formatting",
        ),
    }


def workspace_symbols_fingerprint(runtime_hashes: Mapping[str, str]) -> str:
    for name in _RUNTIME_SOURCE_PATHS:
        if name not in runtime_hashes:
            raise VSCodeWorkspaceSymbolsError(
                f"T4.9 runtime hash projection is missing {name!r}."
            )
    payload = json.dumps(
        workspace_symbols_contract(runtime_hashes),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def audit_vscode_workspace_symbols(extension_root: Path) -> VSCodeWorkspaceSymbolsAudit:
    root = Path(extension_root).resolve()
    if not root.is_dir():
        raise VSCodeWorkspaceSymbolsError(
            f"VS Code extension directory does not exist: {root}."
        )

    try:
        previous = audit_vscode_references_rename(root)
    except VSCodeReferencesRenameError as error:
        raise VSCodeWorkspaceSymbolsError(str(error)) from error
    if previous.references_rename_sha256 != CANONICAL_VSCODE_REFERENCES_RENAME_SHA256:
        raise VSCodeWorkspaceSymbolsError(
            "Frozen T4.8 references/rename projection changed."
        )

    hashes = _runtime_hashes(root)
    observed = workspace_symbols_fingerprint(hashes)
    if observed != CANONICAL_VSCODE_WORKSPACE_SYMBOLS_SHA256:
        raise VSCodeWorkspaceSymbolsError(
            "VS Code workspace-symbol fingerprint changed; expected "
            f"{CANONICAL_VSCODE_WORKSPACE_SYMBOLS_SHA256}, received {observed}."
        )

    return VSCodeWorkspaceSymbolsAudit(
        extension_root=root,
        extension_id=CANONICAL_VSCODE_EXTENSION_ID,
        package_version=CANONICAL_VSCODE_PACKAGE_VERSION,
        runtime_file_count=len(_RUNTIME_SOURCE_PATHS),
        workspace_symbols_sha256=observed,
    )


def _safe_archive_name(name: str) -> str:
    if type(name) is not str or not name or "\\" in name:
        raise VSCodeWorkspaceSymbolsError(f"Unsafe VSIX archive path {name!r}.")
    path = PurePosixPath(name)
    if path.is_absolute() or any(part in ("", ".", "..") for part in path.parts):
        raise VSCodeWorkspaceSymbolsError(f"Unsafe VSIX archive path {name!r}.")
    return path.as_posix()


def _archive_index(archive: ZipFile) -> Mapping[str, str]:
    index: dict[str, str] = {}
    for info in archive.infolist():
        if info.is_dir():
            continue
        normalized = _safe_archive_name(info.filename)
        folded = normalized.casefold()
        if folded in index:
            raise VSCodeWorkspaceSymbolsError(
                f"VSIX contains duplicate case-insensitive path {normalized!r}."
            )
        index[folded] = normalized
    return index


def audit_vscode_workspace_symbols_vsix(
    extension_root: Path,
    vsix_path: Path,
) -> VSCodeWorkspaceSymbolsVSIXAudit:
    source_audit = audit_vscode_workspace_symbols(extension_root)
    package_path = Path(vsix_path).resolve()
    if not package_path.is_file():
        raise VSCodeWorkspaceSymbolsError(
            f"VSIX file does not exist: {package_path}."
        )

    required = {
        "extension/extension.js": "extension.js",
        "extension/runtime/lsp-client.js": CANONICAL_RUNTIME_CLIENT_PATH,
        "extension/language_server.md": CANONICAL_LANGUAGE_SERVER_GUIDE,
    }
    try:
        with ZipFile(package_path, "r") as archive:
            index = _archive_index(archive)
            missing = tuple(sorted(name for name in required if name not in index))
            if missing:
                raise VSCodeWorkspaceSymbolsError(
                    f"VSIX is missing T4.9 runtime files: {missing}."
                )
            for archive_name, source_name in required.items():
                observed = archive.read(index[archive_name])
                expected = _read_bytes(
                    Path(extension_root).resolve() / PurePosixPath(source_name),
                    f"canonical T4.9 source {source_name}",
                )
                if observed != expected:
                    raise VSCodeWorkspaceSymbolsError(
                        f"VSIX payload differs from T4.9 source {source_name!r}."
                    )
            archive_count = len(index)
    except (BadZipFile, OSError) as error:
        raise VSCodeWorkspaceSymbolsError(
            f"Could not audit VSIX {package_path}: {error}."
        ) from error

    return VSCodeWorkspaceSymbolsVSIXAudit(
        vsix_path=package_path,
        archive_file_count=archive_count,
        workspace_symbols_sha256=source_audit.workspace_symbols_sha256,
        vsix_sha256=_sha256_file(package_path),
    )


def check_node_syntax(
    extension_root: Path,
    *,
    node_command: Optional[str] = None,
) -> tuple[str, ...]:
    selected = node_command
    if not selected:
        from shutil import which
        selected = which("node")
    if not selected:
        raise VSCodeWorkspaceSymbolsError("Node.js was not found on PATH.")

    checked: list[str] = []
    for name in ("extension.js", CANONICAL_RUNTIME_CLIENT_PATH):
        path = Path(extension_root).resolve() / PurePosixPath(name)
        completed = subprocess.run(
            (selected, "--check", str(path)),
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode != 0:
            details = (completed.stderr or completed.stdout or "").strip()
            raise VSCodeWorkspaceSymbolsError(
                f"Node.js syntax check failed for {name!r}"
                + (f": {details}" if details else ".")
            )
        checked.append(name)
    return tuple(checked)


def main(
    argv: Optional[Sequence[str]] = None,
    *,
    stdout: TextIO = sys.stdout,
    stderr: TextIO = sys.stderr,
) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m tooling.vscode_workspace_symbols",
        description="Audit AFP-P10-T4.9 VS Code workspace-symbol integration.",
    )
    parser.add_argument("extension_root", type=Path)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--check-vsix", type=Path, metavar="VSIX")
    mode.add_argument("--contract", action="store_true")
    arguments = parser.parse_args(tuple(argv) if argv is not None else None)

    try:
        if arguments.contract:
            audit_vscode_workspace_symbols(arguments.extension_root)
            print(CANONICAL_VSCODE_WORKSPACE_SYMBOLS_SHA256, file=stdout)
            return 0
        if arguments.check_vsix is not None:
            audit = audit_vscode_workspace_symbols_vsix(
                arguments.extension_root,
                arguments.check_vsix,
            )
            print("AFP-P10-T4.9 VS Code workspace-symbol VSIX audit passed.", file=stdout)
            print(f"Archive files: {audit.archive_file_count}", file=stdout)
            print(
                f"Workspace Symbols SHA-256: {audit.workspace_symbols_sha256}",
                file=stdout,
            )
            print(f"VSIX SHA-256: {audit.vsix_sha256}", file=stdout)
            return 0

        audit = audit_vscode_workspace_symbols(arguments.extension_root)
        checked = check_node_syntax(arguments.extension_root)
        print("AFP-P10-T4.9 VS Code workspace-symbol check passed.", file=stdout)
        print(f"Extension ID: {audit.extension_id}", file=stdout)
        print(f"Runtime files: {audit.runtime_file_count}", file=stdout)
        print(f"Node syntax files: {len(checked)}", file=stdout)
        print(
            f"Workspace Symbols SHA-256: {audit.workspace_symbols_sha256}",
            file=stdout,
        )
        return 0
    except VSCodeWorkspaceSymbolsError as error:
        print(str(error), file=stderr)
        return 1


__all__ = (
    "CANONICAL_VSCODE_WORKSPACE_SYMBOLS_SHA256",
    "P10_T4_VSCODE_WORKSPACE_SYMBOLS_VERSION",
    "VSCODE_WORKSPACE_SYMBOLS_KIND",
    "VSCODE_WORKSPACE_SYMBOLS_SCHEMA",
    "VSCodeWorkspaceSymbolsAudit",
    "VSCodeWorkspaceSymbolsError",
    "VSCodeWorkspaceSymbolsVSIXAudit",
    "WORKSPACE_SYMBOL_METHOD",
    "WORKSPACE_SYMBOL_PROVIDER",
    "audit_vscode_workspace_symbols",
    "audit_vscode_workspace_symbols_vsix",
    "check_node_syntax",
    "main",
    "workspace_symbols_contract",
    "workspace_symbols_fingerprint",
)


if __name__ == "__main__":
    raise SystemExit(main())
