"""AFP-P10-T4.8 VS Code references and safe rename integration audit."""

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

from language_server.references import CANONICAL_REFERENCES_SHA256
from language_server.rename import CANONICAL_RENAME_SHA256
from tooling.vscode_definition import (
    CANONICAL_VSCODE_DEFINITION_SHA256,
    VSCodeDefinitionError,
    audit_vscode_definition,
)
from tooling.vscode_lsp_activation import (
    CANONICAL_LANGUAGE_SERVER_GUIDE,
    CANONICAL_RUNTIME_CLIENT_PATH,
)
from tooling.vscode_package import (
    CANONICAL_VSCODE_EXTENSION_ID,
    CANONICAL_VSCODE_PACKAGE_VERSION,
)


P10_T4_VSCODE_REFERENCES_RENAME_VERSION: Final[str] = "10-T4.8"
VSCODE_REFERENCES_RENAME_SCHEMA: Final[int] = 1
VSCODE_REFERENCES_RENAME_KIND: Final[str] = "apexforge.vscode-references-rename"
REFERENCES_METHOD: Final[str] = "textDocument/references"
PREPARE_RENAME_METHOD: Final[str] = "textDocument/prepareRename"
RENAME_METHOD: Final[str] = "textDocument/rename"
REFERENCES_PROVIDER: Final[str] = "registerReferenceProvider"
RENAME_PROVIDER: Final[str] = "registerRenameProvider"

_RUNTIME_SOURCE_PATHS: Final[tuple[str, ...]] = (
    "extension.js",
    CANONICAL_RUNTIME_CLIENT_PATH,
    CANONICAL_LANGUAGE_SERVER_GUIDE,
)

CANONICAL_VSCODE_REFERENCES_RENAME_SHA256: Final[str] = "8dcb0b5ca57e2a8a507d16513fcb75d96e7f15d72db3d768afdcb8161d7d6119"


class VSCodeReferencesRenameError(ValueError):
    code: Final[str] = "APX-VSCODE-009"

    def __init__(self, message: str) -> None:
        if type(message) is not str or not message:
            raise ValueError("VSCodeReferencesRenameError.message must be non-empty.")
        self.message = message
        super().__init__(f"[{self.code}] {message}")


@dataclass(frozen=True)
class VSCodeReferencesRenameAudit:
    extension_root: Path
    extension_id: str
    package_version: str
    runtime_file_count: int
    references_rename_sha256: str


@dataclass(frozen=True)
class VSCodeReferencesRenameVSIXAudit:
    vsix_path: Path
    archive_file_count: int
    references_rename_sha256: str
    vsix_sha256: str


def _read_bytes(path: Path, owner: str) -> bytes:
    try:
        return path.read_bytes()
    except OSError as error:
        raise VSCodeReferencesRenameError(
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
            f"T4.8 runtime source {name}",
        )
        hashes[name] = _sha256_bytes(data)
        try:
            texts[name] = data.decode("utf-8")
        except UnicodeDecodeError as error:
            raise VSCodeReferencesRenameError(
                f"T4.8 runtime source {name!r} must be UTF-8."
            ) from error

    extension_markers = (
        "registerReferenceProvider",
        "provideReferences",
        "textDocument/references",
        "convertReferences",
        "registerRenameProvider",
        "prepareRename",
        "provideRenameEdits",
        "textDocument/prepareRename",
        "textDocument/rename",
        "convertWorkspaceEdit",
        "new vscode.WorkspaceEdit",
        "prepareSupport: true",
    )
    for marker in extension_markers:
        if marker not in texts["extension.js"]:
            raise VSCodeReferencesRenameError(
                f"extension.js omitted T4.8 marker {marker!r}."
            )

    guide_markers = (
        "textDocument/references",
        "textDocument/prepareRename",
        "textDocument/rename",
        "Shift+F12",
        "F2",
        "same-document",
        "cross-file",
    )
    for marker in guide_markers:
        if marker not in texts[CANONICAL_LANGUAGE_SERVER_GUIDE]:
            raise VSCodeReferencesRenameError(
                f"LANGUAGE_SERVER.md omitted T4.8 marker {marker!r}."
            )
    return hashes


def references_rename_contract(runtime_hashes: Mapping[str, str]) -> Mapping[str, object]:
    return {
        "schema": VSCODE_REFERENCES_RENAME_SCHEMA,
        "kind": VSCODE_REFERENCES_RENAME_KIND,
        "references_rename_version": P10_T4_VSCODE_REFERENCES_RENAME_VERSION,
        "extension": {
            "id": CANONICAL_VSCODE_EXTENSION_ID,
            "version": CANONICAL_VSCODE_PACKAGE_VERSION,
        },
        "methods": (
            REFERENCES_METHOD,
            PREPARE_RENAME_METHOD,
            RENAME_METHOD,
        ),
        "providers": (
            REFERENCES_PROVIDER,
            RENAME_PROVIDER,
        ),
        "selector": {
            "language": "apexforge",
            "scheme": "file",
        },
        "results": {
            "references": "vscode.Location[]",
            "prepare_rename": "vscode.Range | {range, placeholder} | undefined",
            "rename": "vscode.WorkspaceEdit | undefined",
        },
        "workspace_model": "one server process per workspace folder",
        "server_references_sha256": CANONICAL_REFERENCES_SHA256,
        "server_rename_sha256": CANONICAL_RENAME_SHA256,
        "frozen_definition_sha256": CANONICAL_VSCODE_DEFINITION_SHA256,
        "runtime_hashes": dict(runtime_hashes),
        "features_deferred": (
            "workspace_references",
            "cross_file_rename",
            "workspace_symbols",
            "formatting",
            "file_and_module_rename",
        ),
    }


def references_rename_fingerprint(runtime_hashes: Mapping[str, str]) -> str:
    payload = json.dumps(
        references_rename_contract(runtime_hashes),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def audit_vscode_references_rename(extension_root: Path) -> VSCodeReferencesRenameAudit:
    root = Path(extension_root).resolve()
    if not root.is_dir():
        raise VSCodeReferencesRenameError(
            f"VS Code extension directory does not exist: {root}."
        )

    try:
        definition = audit_vscode_definition(root)
    except VSCodeDefinitionError as error:
        raise VSCodeReferencesRenameError(str(error)) from error
    if definition.definition_sha256 != CANONICAL_VSCODE_DEFINITION_SHA256:
        raise VSCodeReferencesRenameError("Frozen T4.7 definition projection changed.")

    hashes = _runtime_hashes(root)
    observed = references_rename_fingerprint(hashes)
    if observed != CANONICAL_VSCODE_REFERENCES_RENAME_SHA256:
        raise VSCodeReferencesRenameError(
            "VS Code references/rename fingerprint changed; expected "
            f"{CANONICAL_VSCODE_REFERENCES_RENAME_SHA256}, received {observed}."
        )

    return VSCodeReferencesRenameAudit(
        extension_root=root,
        extension_id=CANONICAL_VSCODE_EXTENSION_ID,
        package_version=CANONICAL_VSCODE_PACKAGE_VERSION,
        runtime_file_count=len(_RUNTIME_SOURCE_PATHS),
        references_rename_sha256=observed,
    )


def _safe_archive_name(name: str) -> str:
    if type(name) is not str or not name or "\\" in name:
        raise VSCodeReferencesRenameError(f"Unsafe VSIX archive path {name!r}.")
    path = PurePosixPath(name)
    if path.is_absolute() or any(part in ("", ".", "..") for part in path.parts):
        raise VSCodeReferencesRenameError(f"Unsafe VSIX archive path {name!r}.")
    return path.as_posix()


def _archive_index(archive: ZipFile) -> Mapping[str, str]:
    index: dict[str, str] = {}
    for info in archive.infolist():
        if info.is_dir():
            continue
        normalized = _safe_archive_name(info.filename)
        folded = normalized.casefold()
        if folded in index:
            raise VSCodeReferencesRenameError(
                f"VSIX contains duplicate case-insensitive path {normalized!r}."
            )
        index[folded] = normalized
    return index


def audit_vscode_references_rename_vsix(
    extension_root: Path,
    vsix_path: Path,
) -> VSCodeReferencesRenameVSIXAudit:
    source_audit = audit_vscode_references_rename(extension_root)
    package_path = Path(vsix_path).resolve()
    if not package_path.is_file():
        raise VSCodeReferencesRenameError(f"VSIX file does not exist: {package_path}.")

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
                raise VSCodeReferencesRenameError(
                    f"VSIX is missing T4.8 runtime files: {missing}."
                )
            for archive_name, source_name in required.items():
                observed = archive.read(index[archive_name])
                expected = _read_bytes(
                    Path(extension_root).resolve() / PurePosixPath(source_name),
                    f"canonical T4.8 source {source_name}",
                )
                if observed != expected:
                    raise VSCodeReferencesRenameError(
                        f"VSIX payload differs from T4.8 source {source_name!r}."
                    )
            archive_count = len(index)
    except (BadZipFile, OSError) as error:
        raise VSCodeReferencesRenameError(
            f"Could not audit VSIX {package_path}: {error}."
        ) from error

    return VSCodeReferencesRenameVSIXAudit(
        vsix_path=package_path,
        archive_file_count=archive_count,
        references_rename_sha256=source_audit.references_rename_sha256,
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
        raise VSCodeReferencesRenameError("Node.js was not found on PATH.")

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
            raise VSCodeReferencesRenameError(
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
        prog="python -m tooling.vscode_references_rename",
        description="Audit AFP-P10-T4.8 VS Code references and rename integration.",
    )
    parser.add_argument("extension_root", type=Path)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--check-vsix", type=Path, metavar="VSIX")
    mode.add_argument("--contract", action="store_true")
    arguments = parser.parse_args(tuple(argv) if argv is not None else None)

    try:
        if arguments.contract:
            audit_vscode_references_rename(arguments.extension_root)
            print(CANONICAL_VSCODE_REFERENCES_RENAME_SHA256, file=stdout)
            return 0
        if arguments.check_vsix is not None:
            audit = audit_vscode_references_rename_vsix(
                arguments.extension_root,
                arguments.check_vsix,
            )
            print("AFP-P10-T4.8 VS Code references/rename VSIX audit passed.", file=stdout)
            print(f"Archive files: {audit.archive_file_count}", file=stdout)
            print(
                f"References/Rename SHA-256: {audit.references_rename_sha256}",
                file=stdout,
            )
            print(f"VSIX SHA-256: {audit.vsix_sha256}", file=stdout)
            return 0

        audit = audit_vscode_references_rename(arguments.extension_root)
        checked = check_node_syntax(arguments.extension_root)
        print("AFP-P10-T4.8 VS Code references/rename check passed.", file=stdout)
        print(f"Extension ID: {audit.extension_id}", file=stdout)
        print(f"Runtime files: {audit.runtime_file_count}", file=stdout)
        print(f"Node syntax files: {len(checked)}", file=stdout)
        print(
            f"References/Rename SHA-256: {audit.references_rename_sha256}",
            file=stdout,
        )
        return 0
    except VSCodeReferencesRenameError as error:
        print(str(error), file=stderr)
        return 1


__all__ = (
    "CANONICAL_VSCODE_REFERENCES_RENAME_SHA256",
    "P10_T4_VSCODE_REFERENCES_RENAME_VERSION",
    "PREPARE_RENAME_METHOD",
    "REFERENCES_METHOD",
    "REFERENCES_PROVIDER",
    "RENAME_METHOD",
    "RENAME_PROVIDER",
    "VSCODE_REFERENCES_RENAME_KIND",
    "VSCODE_REFERENCES_RENAME_SCHEMA",
    "VSCodeReferencesRenameAudit",
    "VSCodeReferencesRenameError",
    "VSCodeReferencesRenameVSIXAudit",
    "audit_vscode_references_rename",
    "audit_vscode_references_rename_vsix",
    "check_node_syntax",
    "main",
    "references_rename_contract",
    "references_rename_fingerprint",
)


if __name__ == "__main__":
    raise SystemExit(main())
