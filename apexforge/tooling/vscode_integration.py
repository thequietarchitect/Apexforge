"""AFP-P10-T4.11 VS Code integration-hardening and VSIX audit."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Final, Mapping, Optional, Sequence, TextIO
from zipfile import BadZipFile, ZipFile

from language_server.integration import CANONICAL_INTEGRATION_SHA256
from tooling.vscode_formatting import (
    CANONICAL_VSCODE_FORMATTING_SHA256,
    VSCodeFormattingError,
    audit_vscode_formatting,
)
from tooling.vscode_lsp_activation import (
    CANONICAL_LANGUAGE_SERVER_GUIDE,
    CANONICAL_RUNTIME_CLIENT_PATH,
)
from tooling.vscode_package import (
    CANONICAL_VSCODE_EXTENSION_ID,
    CANONICAL_VSCODE_PACKAGE_VERSION,
)

P10_T4_VSCODE_INTEGRATION_VERSION: Final[str] = "10-T4.11"
VSCODE_INTEGRATION_SCHEMA: Final[int] = 1
VSCODE_INTEGRATION_KIND: Final[str] = "apexforge.vscode-integration-hardening"
_RUNTIME_SOURCE_PATHS: Final[tuple[str, ...]] = (
    "extension.js",
    CANONICAL_RUNTIME_CLIENT_PATH,
    CANONICAL_LANGUAGE_SERVER_GUIDE,
)
CANONICAL_VSCODE_INTEGRATION_SHA256: Final[str] = "b901ace810dece5e59840148263a893ea6920424ca7d0b7a2dfd594bb9b20e0b"


class VSCodeIntegrationError(ValueError):
    code: Final[str] = "APX-VSCODE-012"

    def __init__(self, message: str) -> None:
        if type(message) is not str or not message:
            raise ValueError("VSCodeIntegrationError.message must be non-empty.")
        self.message = message
        super().__init__(f"[{self.code}] {message}")


@dataclass(frozen=True)
class VSCodeIntegrationAudit:
    extension_root: Path
    extension_id: str
    package_version: str
    runtime_file_count: int
    integration_sha256: str


@dataclass(frozen=True)
class VSCodeIntegrationVSIXAudit:
    vsix_path: Path
    archive_file_count: int
    integration_sha256: str
    vsix_sha256: str


def _read_bytes(path: Path, owner: str) -> bytes:
    try:
        return path.read_bytes()
    except OSError as error:
        raise VSCodeIntegrationError(f"Could not read {owner} at {path}: {error}.") from error


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(_read_bytes(path, str(path)))


def _runtime_hashes(root: Path) -> Mapping[str, str]:
    hashes: dict[str, str] = {}
    texts: dict[str, str] = {}
    for name in _RUNTIME_SOURCE_PATHS:
        data = _read_bytes(root / PurePosixPath(name), f"T4.11 runtime source {name}")
        hashes[name] = _sha256_bytes(data)
        try:
            texts[name] = data.decode("utf-8")
        except UnicodeDecodeError as error:
            raise VSCodeIntegrationError(f"T4.11 runtime source {name!r} must be UTF-8.") from error

    extension_markers = (
        "CLIENT_VERSION = '10-T4.11'",
        "restartPromise",
        "generation",
        "handleClientExit",
        "Discarded stale language-server startup",
        "Promise.allSettled",
        "AFP-P10-T4.11 extension activation completed.",
        "registerDocumentFormattingEditProvider",
        "registerWorkspaceSymbolProvider",
    )
    runtime_markers = (
        "REQUEST_CANCELLED",
        "$/cancelRequest",
        "CancellationError",
        "onCancellationRequested",
        "stopPromise",
        "onExit",
        "JSON-RPC response omitted both result and error",
    )
    guide_markers = (
        "AFP-P10-T4.11",
        "$/cancelRequest",
        "$/setTrace",
        "-32800",
        "generation guard",
        "VSIX audit",
        "Range formatting",
        "cross-file rename",
    )
    for marker in extension_markers:
        if marker not in texts["extension.js"]:
            raise VSCodeIntegrationError(f"extension.js omitted T4.11 marker {marker!r}.")
    for marker in runtime_markers:
        if marker not in texts[CANONICAL_RUNTIME_CLIENT_PATH]:
            raise VSCodeIntegrationError(f"runtime client omitted T4.11 marker {marker!r}.")
    for marker in guide_markers:
        if marker not in texts[CANONICAL_LANGUAGE_SERVER_GUIDE]:
            raise VSCodeIntegrationError(f"LANGUAGE_SERVER.md omitted T4.11 marker {marker!r}.")
    return hashes


def integration_contract(runtime_hashes: Mapping[str, str]) -> Mapping[str, object]:
    return {'schema': 1, 'kind': 'apexforge.vscode-integration-hardening', 'integration_version': '10-T4.11', 'extension': {'id': 'gravitas-studios.apexforge-language', 'version': '0.1.0'}, 'workspace_model': 'one guarded server process per file workspace folder', 'request_cancellation': {'method': '$/cancelRequest', 'code': -32800, 'local_pending_cleanup': True}, 'restart_model': 'serialized restart promise plus generation guard', 'unexpected_exit': 'clear synchronized versions and diagnostics', 'vsix_audit': 'exact runtime parity plus safe-path and forbidden-payload checks', 'server_integration_sha256': 'c2fff74134a40bd335e1c04123127d4cc87df7aa2ed3accc5133d93da9066897', 'frozen_formatting_sha256': '46a4267481b3f4fabd250c7324cc3b4f7be98bb6d5b2b7a52ef05bb6fc27c6ff', 'runtime_hashes': {'extension.js': '45e4b9d96a579a558055d24fde05ae9806dab1a70c0d2f3c42ad502cb5f98b3e', 'runtime/lsp-client.js': '853b5c026e65b9db895c82ab322fcf267b41b57e87f2d819c1e1336c64d80145', 'LANGUAGE_SERVER.md': '98fd6e92d7ea765fdc3cd280beeb836c773e6453e70ca097bcd6cc6d75ed0f91'}, 'features_deferred': ('cross_file_definition', 'workspace_references', 'cross_file_rename', 'range_formatting', 'format_on_type', 'persistent_workspace_index')}


def integration_fingerprint(runtime_hashes: Mapping[str, str]) -> str:
    for name in _RUNTIME_SOURCE_PATHS:
        if name not in runtime_hashes:
            raise VSCodeIntegrationError(f"T4.11 runtime hash projection is missing {name!r}.")
    payload = json.dumps(
        integration_contract(runtime_hashes),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _validate_package_manifest(root: Path) -> Mapping[str, object]:
    package_path = root / "package.json"
    try:
        value = json.loads(_read_bytes(package_path, "package.json").decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise VSCodeIntegrationError(f"package.json must be valid UTF-8 JSON: {error}.") from error
    if type(value) is not dict:
        raise VSCodeIntegrationError("package.json root must be an object.")
    expected = {
        "name": "apexforge-language",
        "publisher": "gravitas-studios",
        "version": CANONICAL_VSCODE_PACKAGE_VERSION,
        "main": "./extension.js",
    }
    for key, expected_value in expected.items():
        if value.get(key) != expected_value:
            raise VSCodeIntegrationError(
                f"package.json {key!r} changed; expected {expected_value!r}."
            )
    activation = value.get("activationEvents")
    if not isinstance(activation, list) or "onLanguage:apexforge" not in activation:
        raise VSCodeIntegrationError("package.json omitted onLanguage:apexforge activation.")
    return value


def audit_vscode_integration(extension_root: Path) -> VSCodeIntegrationAudit:
    root = Path(extension_root).resolve()
    if not root.is_dir():
        raise VSCodeIntegrationError(f"VS Code extension directory does not exist: {root}.")
    try:
        previous = audit_vscode_formatting(root)
    except VSCodeFormattingError as error:
        raise VSCodeIntegrationError(str(error)) from error
    if previous.formatting_sha256 != CANONICAL_VSCODE_FORMATTING_SHA256:
        raise VSCodeIntegrationError("Frozen T4.10 formatting projection changed.")
    _validate_package_manifest(root)
    hashes = _runtime_hashes(root)
    observed = integration_fingerprint(hashes)
    if observed != CANONICAL_VSCODE_INTEGRATION_SHA256:
        raise VSCodeIntegrationError(
            "VS Code integration fingerprint changed; expected "
            f"{CANONICAL_VSCODE_INTEGRATION_SHA256}, received {observed}."
        )
    return VSCodeIntegrationAudit(
        extension_root=root,
        extension_id=CANONICAL_VSCODE_EXTENSION_ID,
        package_version=CANONICAL_VSCODE_PACKAGE_VERSION,
        runtime_file_count=len(_RUNTIME_SOURCE_PATHS),
        integration_sha256=observed,
    )


def _safe_archive_name(name: str) -> str:
    if type(name) is not str or not name or "\\" in name:
        raise VSCodeIntegrationError(f"Unsafe VSIX archive path {name!r}.")
    path = PurePosixPath(name)
    if path.is_absolute() or any(part in ("", ".", "..") for part in path.parts):
        raise VSCodeIntegrationError(f"Unsafe VSIX archive path {name!r}.")
    return path.as_posix()


def _archive_index(archive: ZipFile) -> Mapping[str, str]:
    index: dict[str, str] = {}
    forbidden_parts = {".git", ".vscode", "__pycache__"}
    for info in archive.infolist():
        if info.is_dir():
            continue
        normalized = _safe_archive_name(info.filename)
        path = PurePosixPath(normalized)
        folded = normalized.casefold()
        if folded in index:
            raise VSCodeIntegrationError(
                f"VSIX contains duplicate case-insensitive path {normalized!r}."
            )
        if any(part.casefold() in forbidden_parts for part in path.parts):
            raise VSCodeIntegrationError(f"VSIX contains forbidden payload {normalized!r}.")
        if folded.endswith((".pyc", ".pyo", ".vsix")):
            raise VSCodeIntegrationError(f"VSIX contains forbidden payload {normalized!r}.")
        index[folded] = normalized
    return index


def audit_vscode_integration_vsix(
    extension_root: Path,
    vsix_path: Path,
) -> VSCodeIntegrationVSIXAudit:
    source = audit_vscode_integration(extension_root)
    root = Path(extension_root).resolve()
    package = Path(vsix_path).resolve()
    if not package.is_file():
        raise VSCodeIntegrationError(f"VSIX file does not exist: {package}.")
    required = {
        "extension/extension.js": "extension.js",
        "extension/runtime/lsp-client.js": CANONICAL_RUNTIME_CLIENT_PATH,
        "extension/language_server.md": CANONICAL_LANGUAGE_SERVER_GUIDE,
        "extension/package.json": "package.json",
    }
    try:
        with ZipFile(package, "r") as archive:
            index = _archive_index(archive)
            missing = tuple(sorted(name for name in required if name not in index))
            if missing:
                raise VSCodeIntegrationError(f"VSIX is missing T4.11 runtime files: {missing}.")
            for archive_name, source_name in required.items():
                observed = archive.read(index[archive_name])
                expected = _read_bytes(root / PurePosixPath(source_name), source_name)
                if observed != expected:
                    raise VSCodeIntegrationError(
                        f"VSIX payload differs from T4.11 source {source_name!r}."
                    )
            count = len(index)
    except (BadZipFile, OSError) as error:
        raise VSCodeIntegrationError(f"Could not audit VSIX {package}: {error}.") from error
    return VSCodeIntegrationVSIXAudit(
        vsix_path=package,
        archive_file_count=count,
        integration_sha256=source.integration_sha256,
        vsix_sha256=_sha256_file(package),
    )


def check_node_syntax(extension_root: Path, node_command: Optional[str] = None) -> tuple[str, ...]:
    selected = node_command
    if not selected:
        from shutil import which
        selected = which("node")
    if not selected:
        raise VSCodeIntegrationError("Node.js was not found on PATH.")
    checked: list[str] = []
    for name in ("extension.js", CANONICAL_RUNTIME_CLIENT_PATH):
        completed = subprocess.run(
            (selected, "--check", str(Path(extension_root).resolve() / PurePosixPath(name))),
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode != 0:
            raise VSCodeIntegrationError(
                f"Node.js syntax check failed for {name!r}: "
                f"{(completed.stderr or completed.stdout or '').strip()}."
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
        prog="python -m tooling.vscode_integration",
        description="Audit AFP-P10-T4.11 VS Code integration hardening.",
    )
    parser.add_argument("extension_root", type=Path)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--check-vsix", type=Path, metavar="VSIX")
    mode.add_argument("--contract", action="store_true")
    args = parser.parse_args(tuple(argv) if argv is not None else None)
    try:
        if args.contract:
            audit_vscode_integration(args.extension_root)
            print(CANONICAL_VSCODE_INTEGRATION_SHA256, file=stdout)
            return 0
        if args.check_vsix is not None:
            audit = audit_vscode_integration_vsix(args.extension_root, args.check_vsix)
            print("AFP-P10-T4.11 VS Code integration VSIX audit passed.", file=stdout)
            print(f"Archive files: {audit.archive_file_count}", file=stdout)
            print(f"Integration SHA-256: {audit.integration_sha256}", file=stdout)
            print(f"VSIX SHA-256: {audit.vsix_sha256}", file=stdout)
            return 0
        audit = audit_vscode_integration(args.extension_root)
        checked = check_node_syntax(args.extension_root)
        print("AFP-P10-T4.11 VS Code integration check passed.", file=stdout)
        print(f"Extension ID: {audit.extension_id}", file=stdout)
        print(f"Runtime files: {audit.runtime_file_count}", file=stdout)
        print(f"Node syntax files: {len(checked)}", file=stdout)
        print(f"Integration SHA-256: {audit.integration_sha256}", file=stdout)
        return 0
    except VSCodeIntegrationError as error:
        print(str(error), file=stderr)
        return 1


__all__ = (
    "CANONICAL_VSCODE_INTEGRATION_SHA256",
    "P10_T4_VSCODE_INTEGRATION_VERSION",
    "VSCODE_INTEGRATION_KIND",
    "VSCODE_INTEGRATION_SCHEMA",
    "VSCodeIntegrationAudit",
    "VSCodeIntegrationError",
    "VSCodeIntegrationVSIXAudit",
    "audit_vscode_integration",
    "audit_vscode_integration_vsix",
    "check_node_syntax",
    "integration_contract",
    "integration_fingerprint",
    "main",
)


if __name__ == "__main__":
    raise SystemExit(main())
