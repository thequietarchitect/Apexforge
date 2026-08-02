"""AFP-P10-T5.7 Visual Studio VSIX packaging and installation auditor."""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path, PurePosixPath
import stat
import sys
from typing import Final, Mapping, Optional, Sequence
import xml.etree.ElementTree as ET
import zipfile

P10_T5_VISUAL_STUDIO_PACKAGING_VERSION: Final[str] = "10-T5.7"
VISUAL_STUDIO_PACKAGING_SCHEMA: Final[int] = 1
VISUAL_STUDIO_PACKAGING_KIND: Final[str] = (
    "apexforge.visual-studio-packaging-hardening"
)

_EXTENSION_ID: Final[str] = "GravitasStudios.ApexForge.VisualStudio"
_EXTENSION_VERSION: Final[str] = "0.1.0"
_EXTENSION_PUBLISHER: Final[str] = "Gravitas Studios"
_EXPECTED_ARCHITECTURES: Final[tuple[str, ...]] = ("amd64", "arm64")
_REQUIRED_SOURCE_FILES: Final[tuple[str, ...]] = (
    "ApexForge.VisualStudio.sln",
    "src/ApexForge.VisualStudio/ApexForge.VisualStudio.csproj",
    "src/ApexForge.VisualStudio/source.extension.vsixmanifest",
    "VISUAL_STUDIO_PACKAGING.md",
)
_REQUIRED_ARCHIVE_BASENAMES: Final[tuple[str, ...]] = (
    "extension.vsixmanifest",
    "ApexForge.VisualStudio.dll",
    "ApexForge.VisualStudio.pkgdef",
    "[Content_Types].xml",
)
_FORBIDDEN_SUFFIXES: Final[tuple[str, ...]] = (
    ".cs",
    ".py",
    ".pyc",
    ".pdb",
    ".sln",
    ".csproj",
    ".vsct",
    ".user",
    ".suo",
    ".cache",
    ".vsix",
)
_FORBIDDEN_SEGMENTS: Final[frozenset[str]] = frozenset(
    {
        ".git",
        ".github",
        ".vs",
        ".vscode",
        "__pycache__",
        "bin",
        "obj",
        "node_modules",
    }
)
_MAX_ENTRY_UNCOMPRESSED_BYTES: Final[int] = 64 * 1024 * 1024
_MAX_TOTAL_UNCOMPRESSED_BYTES: Final[int] = 128 * 1024 * 1024
_MAX_COMPRESSION_RATIO: Final[float] = 1000.0

_EXPECTED_CONTRACT: Final[Mapping[str, object]] = {
    "schema": VISUAL_STUDIO_PACKAGING_SCHEMA,
    "kind": VISUAL_STUDIO_PACKAGING_KIND,
    "packaging_version": P10_T5_VISUAL_STUDIO_PACKAGING_VERSION,
    "extension_id": _EXTENSION_ID,
    "extension_version": _EXTENSION_VERSION,
    "publisher": _EXTENSION_PUBLISHER,
    "architectures": _EXPECTED_ARCHITECTURES,
    "required_source_files": _REQUIRED_SOURCE_FILES,
    "required_archive_basenames": _REQUIRED_ARCHIVE_BASENAMES,
    "forbidden_suffixes": _FORBIDDEN_SUFFIXES,
    "forbidden_segments": tuple(sorted(_FORBIDDEN_SEGMENTS)),
    "max_entry_uncompressed_bytes": _MAX_ENTRY_UNCOMPRESSED_BYTES,
    "max_total_uncompressed_bytes": _MAX_TOTAL_UNCOMPRESSED_BYTES,
    "max_compression_ratio": _MAX_COMPRESSION_RATIO,
    "installed_copy_policy": (
        "exactly-one-matching-manifest",
        "built-installed-dll-sha256-equality",
    ),
}


class VisualStudioPackagingError(ValueError):
    """Raised when a source tree, VSIX, or installed copy violates T5.7."""

    code: Final[str] = "APX-VS-PKG-001"

    def __init__(self, message: str) -> None:
        if type(message) is not str or not message:
            raise ValueError("VisualStudioPackagingError.message must be non-empty.")
        self.message = message
        super().__init__(f"[{self.code}] {message}")


@dataclass(frozen=True)
class VisualStudioPackagingSourceAudit:
    root: Path
    fingerprint: str


@dataclass(frozen=True)
class VisualStudioPackagingVsixAudit:
    path: Path
    identity: str
    version: str
    architectures: tuple[str, ...]
    manifest_entry: str
    assembly_entry: str
    package_definition_entry: str
    entry_count: int
    total_uncompressed_bytes: int
    assembly_sha256: str
    manifest_sha256: str
    vsix_sha256: str


@dataclass(frozen=True)
class VisualStudioInstalledAudit:
    profile_root: Path
    extension_root: Path
    manifest_path: Path
    assembly_path: Path
    assembly_sha256: str


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_json(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _children_by_name(root: ET.Element, name: str) -> tuple[ET.Element, ...]:
    return tuple(item for item in root.iter() if _local_name(item.tag) == name)


def _parse_xml_bytes(data: bytes, owner: str) -> ET.Element:
    try:
        return ET.fromstring(data)
    except ET.ParseError as error:
        raise VisualStudioPackagingError(
            f"Malformed XML in {owner}: {error}."
        ) from error


def _read_utf8(path: Path, owner: str) -> str:
    try:
        return path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError) as error:
        raise VisualStudioPackagingError(
            f"Could not read UTF-8 {owner} at {path}: {error}."
        ) from error


def _manifest_identity(manifest: ET.Element, owner: str) -> ET.Element:
    identities = _children_by_name(manifest, "Identity")
    if len(identities) != 1:
        raise VisualStudioPackagingError(
            f"{owner} must contain exactly one Identity element."
        )
    identity = identities[0]
    observed = (
        identity.attrib.get("Id", ""),
        identity.attrib.get("Version", ""),
        identity.attrib.get("Publisher", ""),
    )
    expected = (_EXTENSION_ID, _EXTENSION_VERSION, _EXTENSION_PUBLISHER)
    if observed != expected:
        raise VisualStudioPackagingError(
            f"{owner} identity changed: expected {expected!r}, observed {observed!r}."
        )
    return identity


def _manifest_architectures(manifest: ET.Element, owner: str) -> tuple[str, ...]:
    architectures: list[str] = []
    for target in _children_by_name(manifest, "InstallationTarget"):
        for child in target:
            if _local_name(child.tag) == "ProductArchitecture":
                architectures.append((child.text or "").strip())
    observed = tuple(architectures)
    if observed != _EXPECTED_ARCHITECTURES:
        raise VisualStudioPackagingError(
            f"{owner} architectures changed: {observed!r}."
        )
    return observed


_SOURCE_MANIFEST_ASSETS: Final[tuple[tuple[str, str], ...]] = (
    (
        "Microsoft.VisualStudio.VsPackage",
        "|%CurrentProject%;PkgdefProjectOutputGroup|",
    ),
    (
        "Microsoft.VisualStudio.MefComponent",
        "|%CurrentProject%;BuiltProjectOutputGroup|",
    ),
)
_PACKAGED_MANIFEST_ASSETS: Final[tuple[tuple[str, str], ...]] = (
    ("Microsoft.VisualStudio.VsPackage", "ApexForge.VisualStudio.pkgdef"),
    ("Microsoft.VisualStudio.MefComponent", "ApexForge.VisualStudio.dll"),
)


def _validate_manifest_surface(
    manifest: ET.Element,
    owner: str,
    *,
    packaged: bool,
) -> tuple[str, ...]:
    identity = _manifest_identity(manifest, owner)
    architectures = _manifest_architectures(manifest, owner)

    assets = tuple(
        (item.attrib.get("Type", ""), item.attrib.get("Path", ""))
        for item in _children_by_name(manifest, "Asset")
    )
    expected_assets = (
        _PACKAGED_MANIFEST_ASSETS if packaged else _SOURCE_MANIFEST_ASSETS
    )
    if assets != expected_assets:
        surface = "packaged" if packaged else "source"
        raise VisualStudioPackagingError(
            f"{owner} {surface} asset surface changed: {assets!r}."
        )

    prerequisites = _children_by_name(manifest, "Prerequisite")
    if len(prerequisites) != 1:
        raise VisualStudioPackagingError(
            f"{owner} must contain exactly one prerequisite."
        )
    prerequisite = prerequisites[0]
    if (
        prerequisite.attrib.get("Id")
        != "Microsoft.VisualStudio.Component.CoreEditor"
        or prerequisite.attrib.get("Version") != "[17.0,)"
    ):
        raise VisualStudioPackagingError(
            f"{owner} Core Editor prerequisite changed."
        )

    if identity.attrib.get("Language", "en-US") not in ("", "en-US"):
        raise VisualStudioPackagingError(
            f"{owner} identity language changed unexpectedly."
        )
    return architectures


def visual_studio_packaging_contract() -> Mapping[str, object]:
    return _EXPECTED_CONTRACT


def visual_studio_packaging_fingerprint() -> str:
    return _sha256(_canonical_json(visual_studio_packaging_contract()))


CANONICAL_VISUAL_STUDIO_PACKAGING_SHA256: Final[str] = "44825d6431ffbce78bfc2f3c099bee34608518cb177b8196fd66c12df4bf0019"


def audit_visualstudio_packaging_source(
    root: Path | str,
) -> VisualStudioPackagingSourceAudit:
    selected = Path(root).resolve()
    if not selected.is_dir():
        raise VisualStudioPackagingError(
            f"Visual Studio extension root does not exist: {selected}."
        )
    for relative in _REQUIRED_SOURCE_FILES:
        path = selected / PurePosixPath(relative)
        if not path.is_file():
            raise VisualStudioPackagingError(
                f"T5.7 required source file is missing: {relative}."
            )

    manifest_path = (
        selected
        / "src"
        / "ApexForge.VisualStudio"
        / "source.extension.vsixmanifest"
    )
    manifest = _parse_xml_bytes(
        _read_utf8(manifest_path, "source VSIX manifest").encode("utf-8"),
        "source VSIX manifest",
    )
    _validate_manifest_surface(
        manifest,
        "source VSIX manifest",
        packaged=False,
    )

    documentation = _read_utf8(
        selected / "VISUAL_STUDIO_PACKAGING.md",
        "T5.7 packaging documentation",
    )
    for marker in (
        "AFP-P10-T5.7",
        "duplicate normalized archive paths",
        "built/installed assembly SHA-256 equality",
        "stale duplicate extension registrations",
    ):
        if marker not in documentation:
            raise VisualStudioPackagingError(
                f"VISUAL_STUDIO_PACKAGING.md omitted marker {marker!r}."
            )

    fingerprint = visual_studio_packaging_fingerprint()
    if (
        CANONICAL_VISUAL_STUDIO_PACKAGING_SHA256
        and fingerprint != CANONICAL_VISUAL_STUDIO_PACKAGING_SHA256
    ):
        raise VisualStudioPackagingError(
            f"T5.7 packaging contract changed: {fingerprint}."
        )
    return VisualStudioPackagingSourceAudit(
        root=selected,
        fingerprint=fingerprint,
    )


def _normalized_archive_name(name: str) -> str:
    if type(name) is not str or not name:
        raise VisualStudioPackagingError("VSIX contains an empty archive name.")
    if "\\" in name:
        raise VisualStudioPackagingError(
            f"VSIX entry uses a backslash path separator: {name!r}."
        )
    path = PurePosixPath(name)
    if path.is_absolute() or name.startswith("/"):
        raise VisualStudioPackagingError(
            f"VSIX entry uses an absolute path: {name!r}."
        )
    parts = path.parts
    if not parts or any(part in ("", ".", "..") for part in parts):
        raise VisualStudioPackagingError(
            f"VSIX entry uses an unsafe path: {name!r}."
        )
    if ":" in parts[0]:
        raise VisualStudioPackagingError(
            f"VSIX entry resembles a drive-qualified path: {name!r}."
        )
    return path.as_posix()


def _is_symbolic_link(info: zipfile.ZipInfo) -> bool:
    unix_mode = (info.external_attr >> 16) & 0xFFFF
    return stat.S_ISLNK(unix_mode)


def _find_unique_basename(
    names: tuple[str, ...],
    basename: str,
    owner: str,
) -> str:
    candidates = tuple(
        name
        for name in names
        if PurePosixPath(name.rstrip("/")).name.casefold() == basename.casefold()
    )
    if len(candidates) != 1:
        raise VisualStudioPackagingError(
            f"{owner} must contain exactly one {basename}; observed {candidates!r}."
        )
    return candidates[0]


def audit_visualstudio_vsix_hardening(
    path: Path | str,
) -> VisualStudioPackagingVsixAudit:
    selected = Path(path).resolve()
    if not selected.is_file():
        raise VisualStudioPackagingError(f"VSIX file does not exist: {selected}.")
    try:
        archive = zipfile.ZipFile(selected, "r")
    except (OSError, zipfile.BadZipFile) as error:
        raise VisualStudioPackagingError(f"Invalid VSIX archive: {error}.") from error

    with archive:
        infos = tuple(archive.infolist())
        normalized_names: list[str] = []
        observed_casefolded: set[str] = set()
        total_uncompressed = 0

        for info in infos:
            normalized = _normalized_archive_name(info.filename)
            folded = normalized.rstrip("/").casefold()
            if folded in observed_casefolded:
                raise VisualStudioPackagingError(
                    f"VSIX contains duplicate normalized archive paths: {normalized!r}."
                )
            observed_casefolded.add(folded)
            normalized_names.append(normalized)

            if info.flag_bits & 0x1:
                raise VisualStudioPackagingError(
                    f"VSIX entry is encrypted: {normalized!r}."
                )
            if _is_symbolic_link(info):
                raise VisualStudioPackagingError(
                    f"VSIX entry is a symbolic link: {normalized!r}."
                )
            if info.is_dir():
                continue

            if info.file_size > _MAX_ENTRY_UNCOMPRESSED_BYTES:
                raise VisualStudioPackagingError(
                    f"VSIX entry exceeds the T5.7 size limit: {normalized!r}."
                )
            total_uncompressed += info.file_size
            if total_uncompressed > _MAX_TOTAL_UNCOMPRESSED_BYTES:
                raise VisualStudioPackagingError(
                    "VSIX exceeds the T5.7 total uncompressed size limit."
                )
            if info.compress_size > 0:
                ratio = info.file_size / info.compress_size
                if ratio > _MAX_COMPRESSION_RATIO:
                    raise VisualStudioPackagingError(
                        f"VSIX entry has an unsafe compression ratio: {normalized!r}."
                    )

            parts = tuple(part.casefold() for part in PurePosixPath(normalized).parts)
            if any(part in _FORBIDDEN_SEGMENTS for part in parts):
                raise VisualStudioPackagingError(
                    f"VSIX contains a forbidden development directory: {normalized!r}."
                )
            lower = normalized.casefold()
            if lower.endswith(_FORBIDDEN_SUFFIXES):
                raise VisualStudioPackagingError(
                    f"VSIX contains a forbidden source/debug payload: {normalized!r}."
                )

        names = tuple(normalized_names)
        manifest_entry = _find_unique_basename(
            names,
            "extension.vsixmanifest",
            "VSIX",
        )
        if manifest_entry != "extension.vsixmanifest":
            raise VisualStudioPackagingError(
                "VSIX manifest must be at the archive root as extension.vsixmanifest."
            )
        assembly_entry = _find_unique_basename(
            names,
            "ApexForge.VisualStudio.dll",
            "VSIX",
        )
        package_definition_entry = _find_unique_basename(
            names,
            "ApexForge.VisualStudio.pkgdef",
            "VSIX",
        )
        content_types_entry = _find_unique_basename(
            names,
            "[Content_Types].xml",
            "VSIX",
        )
        if content_types_entry != "[Content_Types].xml":
            raise VisualStudioPackagingError(
                "VSIX [Content_Types].xml must be at the archive root."
            )

        try:
            manifest_bytes = archive.read(manifest_entry)
            assembly_bytes = archive.read(assembly_entry)
        except (KeyError, RuntimeError, OSError) as error:
            raise VisualStudioPackagingError(
                f"Could not read required VSIX payload: {error}."
            ) from error

        manifest = _parse_xml_bytes(manifest_bytes, "built VSIX manifest")
        identity = _manifest_identity(manifest, "built VSIX manifest")
        architectures = _validate_manifest_surface(
            manifest,
            "built VSIX manifest",
            packaged=True,
        )

        return VisualStudioPackagingVsixAudit(
            path=selected,
            identity=identity.attrib.get("Id", ""),
            version=identity.attrib.get("Version", ""),
            architectures=architectures,
            manifest_entry=manifest_entry,
            assembly_entry=assembly_entry,
            package_definition_entry=package_definition_entry,
            entry_count=len(infos),
            total_uncompressed_bytes=total_uncompressed,
            assembly_sha256=_sha256(assembly_bytes),
            manifest_sha256=_sha256(manifest_bytes),
            vsix_sha256=_sha256(selected.read_bytes()),
        )


def _matching_installed_manifests(profile_root: Path) -> tuple[Path, ...]:
    matches: list[Path] = []
    try:
        candidates = tuple(profile_root.rglob("extension.vsixmanifest"))
    except OSError as error:
        raise VisualStudioPackagingError(
            f"Could not scan Visual Studio profile {profile_root}: {error}."
        ) from error
    for candidate in candidates:
        try:
            manifest = _parse_xml_bytes(candidate.read_bytes(), str(candidate))
            identities = _children_by_name(manifest, "Identity")
        except (OSError, VisualStudioPackagingError):
            continue
        if len(identities) == 1 and identities[0].attrib.get("Id") == _EXTENSION_ID:
            matches.append(candidate.resolve())
    return tuple(sorted(matches, key=lambda item: str(item).casefold()))


def audit_visualstudio_installed_copy(
    vsix_path: Path | str,
    profile_root: Path | str,
) -> VisualStudioInstalledAudit:
    built = audit_visualstudio_vsix_hardening(vsix_path)
    profile = Path(profile_root).resolve()
    if not profile.is_dir():
        raise VisualStudioPackagingError(
            f"Visual Studio profile root does not exist: {profile}."
        )

    manifests = _matching_installed_manifests(profile)
    if len(manifests) != 1:
        raise VisualStudioPackagingError(
            "Expected exactly one installed ApexForge manifest; observed: "
            + repr(tuple(str(item) for item in manifests))
            + ". This usually indicates stale duplicate extension registrations."
        )
    manifest_path = manifests[0]
    manifest = _parse_xml_bytes(manifest_path.read_bytes(), str(manifest_path))
    _validate_manifest_surface(
        manifest,
        "installed VSIX manifest",
        packaged=True,
    )

    extension_root = manifest_path.parent
    assemblies = tuple(
        path.resolve()
        for path in extension_root.rglob("ApexForge.VisualStudio.dll")
        if path.is_file()
    )
    if len(assemblies) != 1:
        raise VisualStudioPackagingError(
            "Installed extension must contain exactly one ApexForge.VisualStudio.dll; "
            f"observed {tuple(str(item) for item in assemblies)!r}."
        )
    assembly_path = assemblies[0]
    try:
        installed_hash = _sha256(assembly_path.read_bytes())
    except OSError as error:
        raise VisualStudioPackagingError(
            f"Could not read installed assembly {assembly_path}: {error}."
        ) from error
    if installed_hash != built.assembly_sha256:
        raise VisualStudioPackagingError(
            "Installed ApexForge assembly does not match the built VSIX assembly: "
            f"built={built.assembly_sha256}, installed={installed_hash}."
        )

    return VisualStudioInstalledAudit(
        profile_root=profile,
        extension_root=extension_root,
        manifest_path=manifest_path,
        assembly_path=assembly_path,
        assembly_sha256=installed_hash,
    )


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="apexforge-visualstudio-packaging",
        description=(
            "Audit AFP-P10-T5.7 Visual Studio VSIX packaging and installed-copy integrity."
        ),
    )
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--contract", action="store_true")
    modes.add_argument("--check-source", metavar="ROOT")
    modes.add_argument("--check-vsix", metavar="PATH")
    modes.add_argument("--check-installed", metavar="VSIX")
    parser.add_argument(
        "--profile-root",
        help="Visual Studio profile root required with --check-installed",
    )
    arguments = parser.parse_args(tuple(argv) if argv is not None else None)

    try:
        if arguments.contract:
            print(visual_studio_packaging_fingerprint())
            return 0
        if arguments.check_source:
            audit = audit_visualstudio_packaging_source(arguments.check_source)
            print(f"AFP-P10-T5.7 packaging source audit passed: {audit.root}")
            print(f"Packaging contract SHA-256: {audit.fingerprint}")
            return 0
        if arguments.check_vsix:
            audit = audit_visualstudio_vsix_hardening(arguments.check_vsix)
            print(f"AFP-P10-T5.7 hardened VSIX audit passed: {audit.path}")
            print(f"VSIX SHA-256: {audit.vsix_sha256}")
            print(f"Assembly SHA-256: {audit.assembly_sha256}")
            print(f"Entries: {audit.entry_count}")
            return 0
        if arguments.check_installed:
            if not arguments.profile_root:
                parser.error("--profile-root is required with --check-installed")
            audit = audit_visualstudio_installed_copy(
                arguments.check_installed,
                arguments.profile_root,
            )
            print(
                "AFP-P10-T5.7 installed-copy audit passed: "
                f"{audit.extension_root}"
            )
            print(f"Installed assembly SHA-256: {audit.assembly_sha256}")
            return 0
        raise AssertionError("unreachable CLI mode")
    except VisualStudioPackagingError as error:
        print(str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
