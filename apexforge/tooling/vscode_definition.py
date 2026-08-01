"""AFP-P10-T4.7 VS Code same-document definition integration audit."""

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

from language_server.definition import CANONICAL_DEFINITION_SHA256
from tooling.vscode_completion import (
    CANONICAL_VSCODE_COMPLETION_SHA256,
    VSCodeCompletionError,
    audit_vscode_completion,
)
from tooling.vscode_document_symbols import CANONICAL_VSCODE_DOCUMENT_SYMBOLS_SHA256
from tooling.vscode_hover import CANONICAL_VSCODE_HOVER_SHA256
from tooling.vscode_lsp_activation import (
    CANONICAL_LANGUAGE_SERVER_GUIDE,
    CANONICAL_RUNTIME_CLIENT_PATH,
    CANONICAL_VSCODE_LSP_ACTIVATION_SHA256,
)
from tooling.vscode_package import (
    CANONICAL_VSCODE_EXTENSION_ID,
    CANONICAL_VSCODE_PACKAGE_VERSION,
)


P10_T4_VSCODE_DEFINITION_VERSION: Final[str] = "10-T4.7"
VSCODE_DEFINITION_SCHEMA: Final[int] = 1
VSCODE_DEFINITION_KIND: Final[str] = "apexforge.vscode-definition"
DEFINITION_METHOD: Final[str] = "textDocument/definition"
DEFINITION_PROVIDER: Final[str] = "registerDefinitionProvider"

_RUNTIME_SOURCE_PATHS: Final[tuple[str, ...]] = (
    "extension.js",
    CANONICAL_RUNTIME_CLIENT_PATH,
    CANONICAL_LANGUAGE_SERVER_GUIDE,
)

CANONICAL_VSCODE_DEFINITION_SHA256: Final[str] = "939e9649c7c44d7b5a7cce0ac9eaa7ab900b12a49df1b7dab7d55500b8996e1a"


class VSCodeDefinitionError(ValueError):
    code: Final[str] = "APX-VSCODE-008"

    def __init__(self, message: str) -> None:
        if type(message) is not str or not message:
            raise ValueError("VSCodeDefinitionError.message must be non-empty.")
        self.message = message
        super().__init__(f"[{self.code}] {message}")


@dataclass(frozen=True)
class VSCodeDefinitionAudit:
    extension_root: Path
    extension_id: str
    package_version: str
    runtime_file_count: int
    definition_sha256: str


@dataclass(frozen=True)
class VSCodeDefinitionVSIXAudit:
    vsix_path: Path
    archive_file_count: int
    definition_sha256: str
    vsix_sha256: str


def _read_bytes(path: Path, owner: str) -> bytes:
    try:
        return path.read_bytes()
    except OSError as error:
        raise VSCodeDefinitionError(
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
            f"T4.7 runtime source {name}",
        )
        hashes[name] = _sha256_bytes(data)
        try:
            texts[name] = data.decode("utf-8")
        except UnicodeDecodeError as error:
            raise VSCodeDefinitionError(
                f"T4.7 runtime source {name!r} must be UTF-8."
            ) from error

    required_extension_markers = (
        "registerDefinitionProvider",
        "provideDefinition",
        "textDocument/definition",
        "convertDefinition",
        "new vscode.Location",
        "definition: {",
        "linkSupport: false",
    )
    for marker in required_extension_markers:
        if marker not in texts["extension.js"]:
            raise VSCodeDefinitionError(
                f"extension.js omitted T4.7 definition marker {marker!r}."
            )

    guide_markers = (
        "textDocument/definition",
        "same-document",
        "F12",
        "cross-file",
    )
    for marker in guide_markers:
        if marker not in texts[CANONICAL_LANGUAGE_SERVER_GUIDE]:
            raise VSCodeDefinitionError(
                f"LANGUAGE_SERVER.md omitted T4.7 marker {marker!r}."
            )
    return hashes


def definition_contract(runtime_hashes: Mapping[str, str]) -> Mapping[str, object]:
    return {
        "schema": VSCODE_DEFINITION_SCHEMA,
        "kind": VSCODE_DEFINITION_KIND,
        "definition_version": P10_T4_VSCODE_DEFINITION_VERSION,
        "extension": {
            "id": CANONICAL_VSCODE_EXTENSION_ID,
            "version": CANONICAL_VSCODE_PACKAGE_VERSION,
        },
        "method": DEFINITION_METHOD,
        "provider": DEFINITION_PROVIDER,
        "selector": {
            "language": "apexforge",
            "scheme": "file",
        },
        "result": "vscode.Location | vscode.Location[] | undefined",
        "workspace_model": "one server process per workspace folder",
        "server_contract_sha256": CANONICAL_DEFINITION_SHA256,
        "frozen_activation_sha256": CANONICAL_VSCODE_LSP_ACTIVATION_SHA256,
        "frozen_document_symbols_sha256": CANONICAL_VSCODE_DOCUMENT_SYMBOLS_SHA256,
        "frozen_hover_sha256": CANONICAL_VSCODE_HOVER_SHA256,
        "frozen_completion_sha256": CANONICAL_VSCODE_COMPLETION_SHA256,
        "runtime_hashes": dict(runtime_hashes),
        "features_deferred": (
            "references",
            "rename",
            "workspace_symbols",
            "formatting",
            "cross_file_resolution",
            "location_links",
        ),
    }


def definition_fingerprint(runtime_hashes: Mapping[str, str]) -> str:
    payload = json.dumps(
        definition_contract(runtime_hashes),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def audit_vscode_definition(extension_root: Path) -> VSCodeDefinitionAudit:
    root = Path(extension_root).resolve()
    if not root.is_dir():
        raise VSCodeDefinitionError(
            f"VS Code extension directory does not exist: {root}."
        )

    try:
        completion = audit_vscode_completion(root)
    except VSCodeCompletionError as error:
        raise VSCodeDefinitionError(str(error)) from error
    if completion.completion_sha256 != CANONICAL_VSCODE_COMPLETION_SHA256:
        raise VSCodeDefinitionError("Frozen T4.6 completion projection changed.")

    hashes = _runtime_hashes(root)
    observed = definition_fingerprint(hashes)
    if observed != CANONICAL_VSCODE_DEFINITION_SHA256:
        raise VSCodeDefinitionError(
            "VS Code definition fingerprint changed; expected "
            f"{CANONICAL_VSCODE_DEFINITION_SHA256}, received {observed}."
        )

    return VSCodeDefinitionAudit(
        extension_root=root,
        extension_id=CANONICAL_VSCODE_EXTENSION_ID,
        package_version=CANONICAL_VSCODE_PACKAGE_VERSION,
        runtime_file_count=len(_RUNTIME_SOURCE_PATHS),
        definition_sha256=observed,
    )


def _safe_archive_name(name: str) -> str:
    if type(name) is not str or not name or "\\" in name:
        raise VSCodeDefinitionError(f"Unsafe VSIX archive path {name!r}.")
    path = PurePosixPath(name)
    if path.is_absolute() or any(part in ("", ".", "..") for part in path.parts):
        raise VSCodeDefinitionError(f"Unsafe VSIX archive path {name!r}.")
    return path.as_posix()


def _archive_index(archive: ZipFile) -> Mapping[str, str]:
    index: dict[str, str] = {}
    for info in archive.infolist():
        if info.is_dir():
            continue
        normalized = _safe_archive_name(info.filename)
        folded = normalized.casefold()
        if folded in index:
            raise VSCodeDefinitionError(
                f"VSIX contains duplicate case-insensitive path {normalized!r}."
            )
        index[folded] = normalized
    return index


def audit_vscode_definition_vsix(
    extension_root: Path,
    vsix_path: Path,
) -> VSCodeDefinitionVSIXAudit:
    source_audit = audit_vscode_definition(extension_root)
    package_path = Path(vsix_path).resolve()
    if not package_path.is_file():
        raise VSCodeDefinitionError(f"VSIX file does not exist: {package_path}.")

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
                raise VSCodeDefinitionError(
                    f"VSIX is missing T4.7 runtime files: {missing}."
                )
            for archive_name, source_name in required.items():
                observed = archive.read(index[archive_name])
                expected = _read_bytes(
                    Path(extension_root).resolve() / PurePosixPath(source_name),
                    f"canonical T4.7 source {source_name}",
                )
                if observed != expected:
                    raise VSCodeDefinitionError(
                        f"VSIX payload differs from T4.7 source {source_name!r}."
                    )
            archive_count = len(index)
    except (BadZipFile, OSError) as error:
        raise VSCodeDefinitionError(
            f"Could not audit VSIX {package_path}: {error}."
        ) from error

    return VSCodeDefinitionVSIXAudit(
        vsix_path=package_path,
        archive_file_count=archive_count,
        definition_sha256=source_audit.definition_sha256,
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
        raise VSCodeDefinitionError("Node.js was not found on PATH.")

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
            raise VSCodeDefinitionError(
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
        prog="python -m tooling.vscode_definition",
        description="Audit AFP-P10-T4.7 VS Code definition integration.",
    )
    parser.add_argument("extension_root", type=Path)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--check-vsix", type=Path, metavar="VSIX")
    mode.add_argument("--contract", action="store_true")
    arguments = parser.parse_args(tuple(argv) if argv is not None else None)

    try:
        if arguments.contract:
            audit_vscode_definition(arguments.extension_root)
            print(CANONICAL_VSCODE_DEFINITION_SHA256, file=stdout)
            return 0
        if arguments.check_vsix is not None:
            audit = audit_vscode_definition_vsix(
                arguments.extension_root,
                arguments.check_vsix,
            )
            print("AFP-P10-T4.7 VS Code definition VSIX audit passed.", file=stdout)
            print(f"Archive files: {audit.archive_file_count}", file=stdout)
            print(f"Definition SHA-256: {audit.definition_sha256}", file=stdout)
            print(f"VSIX SHA-256: {audit.vsix_sha256}", file=stdout)
            return 0

        audit = audit_vscode_definition(arguments.extension_root)
        checked = check_node_syntax(arguments.extension_root)
        print("AFP-P10-T4.7 VS Code definition check passed.", file=stdout)
        print(f"Extension ID: {audit.extension_id}", file=stdout)
        print(f"Runtime files: {audit.runtime_file_count}", file=stdout)
        print(f"Node syntax files: {len(checked)}", file=stdout)
        print(f"Definition SHA-256: {audit.definition_sha256}", file=stdout)
        return 0
    except VSCodeDefinitionError as error:
        print(str(error), file=stderr)
        return 1


__all__ = (
    "CANONICAL_VSCODE_DEFINITION_SHA256",
    "DEFINITION_METHOD",
    "DEFINITION_PROVIDER",
    "P10_T4_VSCODE_DEFINITION_VERSION",
    "VSCODE_DEFINITION_KIND",
    "VSCODE_DEFINITION_SCHEMA",
    "VSCodeDefinitionAudit",
    "VSCodeDefinitionError",
    "VSCodeDefinitionVSIXAudit",
    "audit_vscode_definition",
    "audit_vscode_definition_vsix",
    "check_node_syntax",
    "definition_contract",
    "definition_fingerprint",
    "main",
)


if __name__ == "__main__":
    raise SystemExit(main())
