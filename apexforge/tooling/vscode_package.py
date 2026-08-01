"""AFP-P10-T3.3 VS Code VSIX packaging and local-install audit.

The implementation packages the frozen T3.1/T3.2 syntax-only extension with the
official ``@vscode/vsce`` command, validates the resulting ZIP/VSIX payload, and
can install the audited package through the VS Code command-line interface.
Archive timestamps are deliberately excluded from the frozen fingerprint;
canonical source payload bytes and packaging policy are fingerprinted instead.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from typing import Callable, Final, Mapping, Optional, Sequence, TextIO
import xml.etree.ElementTree as ET
from zipfile import BadZipFile, ZipFile

from tooling.vscode_extension import (
    CANONICAL_VSCODE_ENGINE,
    CANONICAL_VSCODE_FOUNDATION_SHA256,
    CANONICAL_VSCODE_LANGUAGE_ID,
    CANONICAL_VSCODE_PACKAGE_NAME,
    CANONICAL_VSCODE_PACKAGE_VERSION,
    CANONICAL_VSCODE_PUBLISHER,
    CANONICAL_VSCODE_SOURCE_EXTENSION,
    audit_vscode_extension,
)
from tooling.vscode_syntax import (
    CANONICAL_TEXTMATE_PATH,
    CANONICAL_TEXTMATE_SCOPE,
    CANONICAL_VSCODE_SYNTAX_SHA256,
    audit_vscode_syntax,
)


P10_T3_VSCODE_PACKAGE_VERSION: Final[str] = "10-T3.3"
VSCODE_PACKAGE_SCHEMA: Final[int] = 1
VSCODE_PACKAGE_KIND: Final[str] = "apexforge.vscode-package"
VSCODE_VSCE_VERSION: Final[str] = "3.9.1"
MINIMUM_NODE_MAJOR: Final[int] = 20

CANONICAL_VSCODE_EXTENSION_ID: Final[str] = (
    f"{CANONICAL_VSCODE_PUBLISHER}.{CANONICAL_VSCODE_PACKAGE_NAME}"
)
CANONICAL_VSIX_FILENAME: Final[str] = (
    f"{CANONICAL_VSCODE_PACKAGE_NAME}-{CANONICAL_VSCODE_PACKAGE_VERSION}.vsix"
)

_EXPECTED_IGNORE_PATTERNS: Final[tuple[str, ...]] = (
    ".vscode/**",
    ".git/**",
    "node_modules/**",
    "package-lock.json",
    "*.vsix",
)

# Keys are the case-folded paths used inside a VSIX archive. Values are the
# canonical source paths inside editors/vscode-apexforge.
_PACKAGED_SOURCE_PATHS: Final[Mapping[str, str]] = {
    "extension/package.json": "package.json",
    "extension/language-configuration.json": "language-configuration.json",
    "extension/readme.md": "README.md",
    "extension/changelog.md": "CHANGELOG.md",
    "extension/syntaxes/apexforge.tmlanguage.json": (
        "syntaxes/apexforge.tmLanguage.json"
    ),
}

_REQUIRED_VSIX_ROOTS: Final[tuple[str, ...]] = (
    "[content_types].xml",
    "extension.vsixmanifest",
)

_VSCE_PACKAGE_ARGUMENTS: Final[tuple[str, ...]] = (
    "package",
    "--no-dependencies",
    "--allow-missing-repository",
    "--skip-license",
    "--no-rewrite-relative-links",
    "--out",
)

# Filled after the canonical T3.3 source projection is serialized. The smoke
# test rejects drift, while VSIX ZIP timestamps remain intentionally unfrozen.
CANONICAL_VSCODE_PACKAGE_SHA256: Final[str] = (
    "75a39c44354d4f647ab46cb6aba42adf00f5396c7563b1433ff2d93d66e9498c"
)


class VSCodePackageError(ValueError):
    """The ApexForge VS Code package or installation is invalid."""

    code: Final[str] = "APX-VSCODE-003"

    def __init__(self, message: str) -> None:
        if type(message) is not str or not message:
            raise ValueError("VSCodePackageError.message must be non-empty.")
        self.message = message
        super().__init__(f"[{self.code}] {message}")


@dataclass(frozen=True)
class VSCodePackageAudit:
    extension_root: Path
    vsix_path: Path
    extension_id: str
    package_version: str
    archive_file_count: int
    payload_sha256: str
    vsix_sha256: str


@dataclass(frozen=True)
class VSCodeInstallAudit:
    extension_id: str
    package_version: str
    code_command: str


Runner = Callable[..., subprocess.CompletedProcess]


def _read_json_bytes(data: bytes, owner: str) -> Mapping[str, object]:
    try:
        value = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise VSCodePackageError(f"{owner} is not valid UTF-8 JSON: {error}.") from error
    if type(value) is not dict:
        raise VSCodePackageError(f"{owner} must contain a JSON object.")
    return value


def _require_mapping(value: object, owner: str) -> Mapping[str, object]:
    if type(value) is not dict:
        raise VSCodePackageError(f"{owner} must be a JSON object.")
    return value


def _require_list(value: object, owner: str) -> list[object]:
    if type(value) is not list:
        raise VSCodePackageError(f"{owner} must be a JSON array.")
    return value


def _require_exact(value: object, expected: object, owner: str) -> None:
    if value != expected:
        raise VSCodePackageError(
            f"{owner} changed; expected {expected!r}, received {value!r}."
        )


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as stream:
            while True:
                block = stream.read(1024 * 1024)
                if not block:
                    break
                digest.update(block)
    except OSError as error:
        raise VSCodePackageError(f"Could not hash file {path}: {error}.") from error
    return digest.hexdigest()


def _read_required_file(path: Path, owner: str) -> bytes:
    try:
        return path.read_bytes()
    except OSError as error:
        raise VSCodePackageError(f"Could not read {owner} at {path}: {error}.") from error


def _validate_ignore_file(extension_root: Path) -> tuple[str, ...]:
    path = extension_root / ".vscodeignore"
    data = _read_required_file(path, "VS Code ignore file")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as error:
        raise VSCodePackageError(".vscodeignore must be UTF-8.") from error
    patterns = tuple(line.strip() for line in text.splitlines() if line.strip())
    _require_exact(patterns, _EXPECTED_IGNORE_PATTERNS, ".vscodeignore patterns")
    return patterns


def _source_payload_hashes(extension_root: Path) -> Mapping[str, str]:
    values: dict[str, str] = {}
    for archive_name, source_name in sorted(_PACKAGED_SOURCE_PATHS.items()):
        data = _read_required_file(
            extension_root / PurePosixPath(source_name),
            f"packaged source {source_name}",
        )
        values[archive_name] = _sha256_bytes(data)
    return values


def _package_projection(extension_root: Path) -> Mapping[str, object]:
    return {
        "schema": VSCODE_PACKAGE_SCHEMA,
        "kind": VSCODE_PACKAGE_KIND,
        "package_version": P10_T3_VSCODE_PACKAGE_VERSION,
        "foundation_sha256": CANONICAL_VSCODE_FOUNDATION_SHA256,
        "syntax_sha256": CANONICAL_VSCODE_SYNTAX_SHA256,
        "extension_id": CANONICAL_VSCODE_EXTENSION_ID,
        "extension_version": CANONICAL_VSCODE_PACKAGE_VERSION,
        "vsix_filename": CANONICAL_VSIX_FILENAME,
        "vsce_version": VSCODE_VSCE_VERSION,
        "minimum_node_major": MINIMUM_NODE_MAJOR,
        "vsce_arguments": _VSCE_PACKAGE_ARGUMENTS,
        "ignore_patterns": _validate_ignore_file(extension_root),
        "payload_hashes": _source_payload_hashes(extension_root),
    }


def packaging_fingerprint(extension_root: Path) -> str:
    """Return the deterministic T3.3 source-payload and policy fingerprint."""

    root = Path(extension_root).resolve()
    payload = json.dumps(
        _package_projection(root),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def audit_vscode_package_source(
    extension_root: Path,
    *,
    repository_root: Optional[Path] = None,
) -> str:
    """Validate the frozen editor package and return its T3.3 fingerprint."""

    root = Path(extension_root).resolve()
    if not root.is_dir():
        raise VSCodePackageError(
            f"VS Code extension directory does not exist: {root}."
        )

    selected_repository_root = (
        Path(repository_root).resolve()
        if repository_root is not None
        else root.parent.parent.resolve()
    )

    foundation = audit_vscode_extension(
        root,
        repository_root=selected_repository_root,
    )
    _require_exact(
        foundation.foundation_sha256,
        CANONICAL_VSCODE_FOUNDATION_SHA256,
        "T3.1 foundation SHA-256",
    )

    syntax = audit_vscode_syntax(
        root,
        repository_root=selected_repository_root,
    )
    _require_exact(
        syntax.syntax_sha256,
        CANONICAL_VSCODE_SYNTAX_SHA256,
        "T3.2 syntax SHA-256",
    )

    observed = packaging_fingerprint(root)
    if observed != CANONICAL_VSCODE_PACKAGE_SHA256:
        raise VSCodePackageError(
            "VS Code packaging fingerprint changed; expected "
            f"{CANONICAL_VSCODE_PACKAGE_SHA256}, received {observed}."
        )
    return observed


def _safe_archive_name(name: str) -> str:
    if type(name) is not str or not name:
        raise VSCodePackageError("VSIX archive contains an empty path.")
    if "\\" in name:
        raise VSCodePackageError(
            f"VSIX archive path must use forward slashes: {name!r}."
        )
    path = PurePosixPath(name)
    if path.is_absolute() or any(part in ("", ".", "..") for part in path.parts):
        raise VSCodePackageError(f"Unsafe VSIX archive path: {name!r}.")
    return path.as_posix()


def _archive_index(archive: ZipFile) -> Mapping[str, str]:
    index: dict[str, str] = {}
    for info in archive.infolist():
        if info.is_dir():
            continue
        normalized = _safe_archive_name(info.filename)
        folded = normalized.casefold()
        if folded in index:
            raise VSCodePackageError(
                "VSIX archive contains duplicate case-insensitive path "
                f"{normalized!r}."
            )
        index[folded] = normalized
    return index


def _validate_no_forbidden_payload(index: Mapping[str, str]) -> None:
    for folded, original in index.items():
        if folded.startswith("extension/.git/"):
            raise VSCodePackageError(f"VSIX contains forbidden Git file {original!r}.")
        if folded.startswith("extension/.vscode/"):
            raise VSCodePackageError(
                f"VSIX contains forbidden VS Code workspace file {original!r}."
            )
        if folded.startswith("extension/node_modules/"):
            raise VSCodePackageError(
                f"VSIX contains forbidden node_modules payload {original!r}."
            )
        if "__pycache__" in folded or folded.endswith(".pyc"):
            raise VSCodePackageError(
                f"VSIX contains forbidden Python cache payload {original!r}."
            )
        if folded.startswith("extension/") and folded.endswith(".vsix"):
            raise VSCodePackageError(
                f"VSIX contains a nested VSIX payload {original!r}."
            )


def _xml_local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _find_xml_elements(root: ET.Element, local_name: str) -> tuple[ET.Element, ...]:
    return tuple(
        element for element in root.iter() if _xml_local_name(element.tag) == local_name
    )


def _validate_content_types(data: bytes) -> None:
    try:
        root = ET.fromstring(data)
    except ET.ParseError as error:
        raise VSCodePackageError(
            f"[Content_Types].xml is invalid XML: {error}."
        ) from error
    if _xml_local_name(root.tag) != "Types":
        raise VSCodePackageError("[Content_Types].xml root must be Types.")


def _validate_vsix_manifest(data: bytes) -> None:
    try:
        root = ET.fromstring(data)
    except ET.ParseError as error:
        raise VSCodePackageError(
            f"extension.vsixmanifest is invalid XML: {error}."
        ) from error
    if _xml_local_name(root.tag) != "PackageManifest":
        raise VSCodePackageError("VSIX manifest root must be PackageManifest.")

    identities = _find_xml_elements(root, "Identity")
    if len(identities) != 1:
        raise VSCodePackageError("VSIX manifest must contain exactly one Identity.")
    identity = identities[0]
    _require_exact(identity.get("Id"), CANONICAL_VSCODE_PACKAGE_NAME, "VSIX identity Id")
    _require_exact(
        identity.get("Version"),
        CANONICAL_VSCODE_PACKAGE_VERSION,
        "VSIX identity Version",
    )
    _require_exact(
        identity.get("Publisher"),
        CANONICAL_VSCODE_PUBLISHER,
        "VSIX identity Publisher",
    )

    targets = _find_xml_elements(root, "InstallationTarget")
    if not any(item.get("Id") == "Microsoft.VisualStudio.Code" for item in targets):
        raise VSCodePackageError(
            "VSIX manifest does not target Microsoft.VisualStudio.Code."
        )

    assets = _find_xml_elements(root, "Asset")
    if not any(
        item.get("Type") == "Microsoft.VisualStudio.Code.Manifest"
        and (item.get("Path") or "").casefold() == "extension/package.json"
        for item in assets
    ):
        raise VSCodePackageError(
            "VSIX manifest does not expose extension/package.json as the Code manifest."
        )

    properties = _find_xml_elements(root, "Property")
    engine_values = tuple(
        item.get("Value")
        for item in properties
        if item.get("Id") == "Microsoft.VisualStudio.Code.Engine"
    )
    if engine_values and engine_values != (CANONICAL_VSCODE_ENGINE,):
        raise VSCodePackageError(
            "VSIX manifest engine property changed; expected "
            f"{CANONICAL_VSCODE_ENGINE!r}, received {engine_values!r}."
        )


def _validate_embedded_package(package: Mapping[str, object]) -> None:
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
    engines = _require_mapping(package.get("engines"), "package engines")
    _require_exact(engines.get("vscode"), CANONICAL_VSCODE_ENGINE, "package engine")

    contributes = _require_mapping(package.get("contributes"), "package contributes")
    languages = _require_list(contributes.get("languages"), "package languages")
    if len(languages) != 1:
        raise VSCodePackageError("Package must contain exactly one language contribution.")
    language = _require_mapping(languages[0], "package language contribution")
    _require_exact(language.get("id"), CANONICAL_VSCODE_LANGUAGE_ID, "language id")
    _require_exact(
        language.get("extensions"),
        [CANONICAL_VSCODE_SOURCE_EXTENSION],
        "language extension",
    )

    grammars = _require_list(contributes.get("grammars"), "package grammars")
    if len(grammars) != 1:
        raise VSCodePackageError("Package must contain exactly one grammar contribution.")
    grammar = _require_mapping(grammars[0], "package grammar contribution")
    _require_exact(grammar.get("language"), CANONICAL_VSCODE_LANGUAGE_ID, "grammar language")
    _require_exact(grammar.get("scopeName"), CANONICAL_TEXTMATE_SCOPE, "grammar scope")
    _require_exact(grammar.get("path"), CANONICAL_TEXTMATE_PATH, "grammar path")


def audit_vscode_vsix(
    extension_root: Path,
    vsix_path: Path,
    *,
    repository_root: Optional[Path] = None,
) -> VSCodePackageAudit:
    """Validate an official VSIX against the canonical source payload."""

    root = Path(extension_root).resolve()
    payload_hash = audit_vscode_package_source(
        root,
        repository_root=repository_root,
    )
    package_path = Path(vsix_path).resolve()
    if not package_path.is_file():
        raise VSCodePackageError(f"VSIX file does not exist: {package_path}.")
    if package_path.suffix.casefold() != ".vsix":
        raise VSCodePackageError(f"Package must use the .vsix suffix: {package_path}.")

    try:
        with ZipFile(package_path, "r") as archive:
            index = _archive_index(archive)
            _validate_no_forbidden_payload(index)

            required = set(_REQUIRED_VSIX_ROOTS) | set(_PACKAGED_SOURCE_PATHS)
            missing = tuple(sorted(name for name in required if name not in index))
            if missing:
                raise VSCodePackageError(
                    f"VSIX is missing required archive files: {missing}."
                )

            _validate_content_types(
                archive.read(index["[content_types].xml"])
            )
            _validate_vsix_manifest(
                archive.read(index["extension.vsixmanifest"])
            )

            embedded_package_bytes = archive.read(index["extension/package.json"])
            embedded_package = _read_json_bytes(
                embedded_package_bytes,
                "embedded extension/package.json",
            )
            _validate_embedded_package(embedded_package)

            for archive_name, source_name in _PACKAGED_SOURCE_PATHS.items():
                observed = archive.read(index[archive_name])
                expected = _read_required_file(
                    root / PurePosixPath(source_name),
                    f"canonical extension source {source_name}",
                )
                if observed != expected:
                    raise VSCodePackageError(
                        "VSIX payload differs from canonical source bytes for "
                        f"{source_name!r}."
                    )

            archive_count = len(index)
    except BadZipFile as error:
        raise VSCodePackageError(f"VSIX is not a valid ZIP archive: {error}.") from error
    except OSError as error:
        raise VSCodePackageError(f"Could not read VSIX {package_path}: {error}.") from error

    return VSCodePackageAudit(
        extension_root=root,
        vsix_path=package_path,
        extension_id=CANONICAL_VSCODE_EXTENSION_ID,
        package_version=CANONICAL_VSCODE_PACKAGE_VERSION,
        archive_file_count=archive_count,
        payload_sha256=payload_hash,
        vsix_sha256=_sha256_file(package_path),
    )


def _resolve_command(base_name: str) -> str:
    candidates = (
        (f"{base_name}.cmd", base_name)
        if os.name == "nt"
        else (base_name,)
    )
    for candidate in candidates:
        resolved = shutil.which(candidate)
        if resolved:
            return resolved
    raise VSCodePackageError(
        f"Required command {base_name!r} was not found on PATH."
    )


def _run_command(
    command: Sequence[str],
    *,
    cwd: Optional[Path],
    runner: Runner,
) -> subprocess.CompletedProcess:
    try:
        completed = runner(
            tuple(command),
            cwd=str(cwd) if cwd is not None else None,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as error:
        raise VSCodePackageError(
            f"Could not execute command {command[0]!r}: {error}."
        ) from error
    if completed.returncode != 0:
        details = (completed.stderr or completed.stdout or "").strip()
        raise VSCodePackageError(
            f"Command failed with exit code {completed.returncode}: "
            f"{' '.join(command)}"
            + (f"\n{details}" if details else "")
        )
    return completed


def _node_major(
    *,
    runner: Runner = subprocess.run,
    node_command: Optional[str] = None,
) -> int:
    command = node_command or _resolve_command("node")
    completed = _run_command((command, "--version"), cwd=None, runner=runner)
    match = re.fullmatch(r"v?(\d+)(?:\.\d+){1,2}(?:[-+].*)?", completed.stdout.strip())
    if match is None:
        raise VSCodePackageError(
            f"Could not parse Node.js version output {completed.stdout.strip()!r}."
        )
    major = int(match.group(1))
    if major < MINIMUM_NODE_MAJOR:
        raise VSCodePackageError(
            f"@vscode/vsce {VSCODE_VSCE_VERSION} requires Node.js "
            f"{MINIMUM_NODE_MAJOR} or newer; received major version {major}."
        )
    return major


def vsce_package_command(npx_command: str, output_path: Path) -> tuple[str, ...]:
    """Return the frozen official packaging command."""

    return (
        npx_command,
        "--yes",
        f"@vscode/vsce@{VSCODE_VSCE_VERSION}",
        *_VSCE_PACKAGE_ARGUMENTS,
        str(Path(output_path).resolve()),
    )


def package_vscode_extension(
    extension_root: Path,
    output_path: Path,
    *,
    repository_root: Optional[Path] = None,
    runner: Runner = subprocess.run,
    node_command: Optional[str] = None,
    npx_command: Optional[str] = None,
) -> VSCodePackageAudit:
    """Package with pinned ``@vscode/vsce`` and audit the resulting VSIX."""

    root = Path(extension_root).resolve()
    audit_vscode_package_source(root, repository_root=repository_root)
    _node_major(runner=runner, node_command=node_command)
    selected_npx = npx_command or _resolve_command("npx")
    destination = Path(output_path).resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        if destination.is_dir():
            raise VSCodePackageError(
                f"VSIX output path is a directory: {destination}."
            )
        destination.unlink()

    command = vsce_package_command(selected_npx, destination)
    _run_command(command, cwd=root, runner=runner)
    return audit_vscode_vsix(
        root,
        destination,
        repository_root=repository_root,
    )


def parse_installed_extensions(output: str) -> Mapping[str, str]:
    """Parse ``code --list-extensions --show-versions`` deterministically."""

    if type(output) is not str:
        raise TypeError("Installed-extension output must be a string.")
    installed: dict[str, str] = {}
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if "@" not in line:
            continue
        extension_id, version = line.rsplit("@", 1)
        extension_id = extension_id.strip().casefold()
        version = version.strip()
        if not extension_id or not version:
            continue
        installed[extension_id] = version
    return installed


def check_vscode_installation(
    *,
    code_command: Optional[str] = None,
    runner: Runner = subprocess.run,
) -> VSCodeInstallAudit:
    """Confirm that the canonical extension ID and version are installed."""

    selected_code = code_command or _resolve_command("code")
    completed = _run_command(
        (selected_code, "--list-extensions", "--show-versions"),
        cwd=None,
        runner=runner,
    )
    installed = parse_installed_extensions(completed.stdout)
    observed = installed.get(CANONICAL_VSCODE_EXTENSION_ID.casefold())
    if observed != CANONICAL_VSCODE_PACKAGE_VERSION:
        raise VSCodePackageError(
            "Installed ApexForge extension version changed; expected "
            f"{CANONICAL_VSCODE_PACKAGE_VERSION!r}, received {observed!r}."
        )
    return VSCodeInstallAudit(
        extension_id=CANONICAL_VSCODE_EXTENSION_ID,
        package_version=observed,
        code_command=selected_code,
    )


def install_vscode_extension(
    extension_root: Path,
    vsix_path: Path,
    *,
    repository_root: Optional[Path] = None,
    code_command: Optional[str] = None,
    runner: Runner = subprocess.run,
) -> VSCodeInstallAudit:
    """Audit, install with ``code --install-extension``, then verify version."""

    package = audit_vscode_vsix(
        extension_root,
        vsix_path,
        repository_root=repository_root,
    )
    selected_code = code_command or _resolve_command("code")
    _run_command(
        (
            selected_code,
            "--install-extension",
            str(package.vsix_path),
            "--force",
        ),
        cwd=None,
        runner=runner,
    )
    return check_vscode_installation(
        code_command=selected_code,
        runner=runner,
    )


def main(
    argv: Optional[Sequence[str]] = None,
    *,
    stdout: TextIO = sys.stdout,
    stderr: TextIO = sys.stderr,
) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m tooling.vscode_package",
        description="Package, audit, and locally install AFP-P10-T3.3 VSIX files.",
    )
    parser.add_argument("extension_root", type=Path)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--package", type=Path, metavar="VSIX")
    mode.add_argument("--check-vsix", type=Path, metavar="VSIX")
    mode.add_argument("--install", type=Path, metavar="VSIX")
    mode.add_argument("--check-installed", action="store_true")
    arguments = parser.parse_args(tuple(argv) if argv is not None else None)

    try:
        if arguments.package is not None:
            audit = package_vscode_extension(
                arguments.extension_root,
                arguments.package,
            )
            print("AFP-P10-T3.3 VS Code VSIX packaging passed.", file=stdout)
            print(f"VSIX: {audit.vsix_path}", file=stdout)
            print(f"Extension ID: {audit.extension_id}", file=stdout)
            print(f"Payload SHA-256: {audit.payload_sha256}", file=stdout)
            print(f"VSIX SHA-256: {audit.vsix_sha256}", file=stdout)
            return 0

        if arguments.check_vsix is not None:
            audit = audit_vscode_vsix(
                arguments.extension_root,
                arguments.check_vsix,
            )
            print("AFP-P10-T3.3 VS Code VSIX audit passed.", file=stdout)
            print(f"Extension ID: {audit.extension_id}", file=stdout)
            print(f"Archive files: {audit.archive_file_count}", file=stdout)
            print(f"Payload SHA-256: {audit.payload_sha256}", file=stdout)
            print(f"VSIX SHA-256: {audit.vsix_sha256}", file=stdout)
            return 0

        if arguments.install is not None:
            audit = install_vscode_extension(
                arguments.extension_root,
                arguments.install,
            )
            print("AFP-P10-T3.3 local VS Code installation passed.", file=stdout)
            print(f"Installed: {audit.extension_id}@{audit.package_version}", file=stdout)
            return 0

        audit = check_vscode_installation()
        print("AFP-P10-T3.3 installed-extension check passed.", file=stdout)
        print(f"Installed: {audit.extension_id}@{audit.package_version}", file=stdout)
        return 0
    except VSCodePackageError as error:
        print(str(error), file=stderr)
        return 1


__all__ = (
    "CANONICAL_VSCODE_EXTENSION_ID",
    "CANONICAL_VSCODE_PACKAGE_SHA256",
    "CANONICAL_VSIX_FILENAME",
    "MINIMUM_NODE_MAJOR",
    "P10_T3_VSCODE_PACKAGE_VERSION",
    "VSCODE_PACKAGE_KIND",
    "VSCODE_PACKAGE_SCHEMA",
    "VSCODE_VSCE_VERSION",
    "VSCodeInstallAudit",
    "VSCodePackageAudit",
    "VSCodePackageError",
    "audit_vscode_package_source",
    "audit_vscode_vsix",
    "check_vscode_installation",
    "install_vscode_extension",
    "package_vscode_extension",
    "packaging_fingerprint",
    "parse_installed_extensions",
    "vsce_package_command",
    "main",
)


if __name__ == "__main__":
    raise SystemExit(main())
