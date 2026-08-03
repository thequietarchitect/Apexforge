"""AFP-P10-T1.1 deterministic ApexForge project discovery and loading."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Mapping, Tuple, Union

from tooling.project_manifest import (
    PROJECT_MANIFEST_NAME,
    ProjectManifest,
    ProjectManifestError,
    load_project_manifest,
)


@dataclass(frozen=True)
class LoadedProjectSource:
    """One immutable project-relative UTF-8 ApexForge source."""

    name: str
    path: Path
    source: str
    source_bytes: bytes = b""

    def __post_init__(self) -> None:
        if type(self.name) is not str or not self.name:
            raise TypeError("LoadedProjectSource.name must be non-empty.")
        if not isinstance(self.path, Path):
            raise TypeError("LoadedProjectSource.path must be pathlib.Path.")
        if type(self.source) is not str:
            raise TypeError("LoadedProjectSource.source must be a string.")
        if type(self.source_bytes) is not bytes:
            raise TypeError("LoadedProjectSource.source_bytes must be bytes.")

        if not self.source_bytes and self.source:
            object.__setattr__(
                self,
                "source_bytes",
                self.source.encode("utf-8"),
            )


@dataclass(frozen=True)
class LoadedProject:
    """One validated project manifest plus its immutable source snapshot."""

    root: Path
    manifest_path: Path
    manifest: ProjectManifest
    sources: Tuple[LoadedProjectSource, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.root, Path):
            raise TypeError("LoadedProject.root must be pathlib.Path.")
        if not isinstance(self.manifest_path, Path):
            raise TypeError("LoadedProject.manifest_path must be pathlib.Path.")
        if not isinstance(self.manifest, ProjectManifest):
            raise TypeError("LoadedProject.manifest must be ProjectManifest.")

        normalized_sources = tuple(self.sources)
        if any(
            not isinstance(source, LoadedProjectSource)
            for source in normalized_sources
        ):
            raise TypeError(
                "LoadedProject.sources must contain LoadedProjectSource values."
            )
        if tuple(source.name for source in normalized_sources) != (
            self.manifest.sources
        ):
            raise ValueError(
                "LoadedProject source order must match the canonical manifest."
            )

        object.__setattr__(self, "sources", normalized_sources)

    def source_mapping(self) -> Mapping[str, str]:
        """Return a read-only filename-to-source mapping for ProjectBuilder."""

        return MappingProxyType(
            {
                source.name: source.source
                for source in self.sources
            }
        )


def find_project_manifest(
    start: Union[str, Path],
) -> Path:
    """Find the nearest ``apexforge.json`` at or above ``start``."""

    candidate = Path(start)

    if candidate.is_file():
        if candidate.name == PROJECT_MANIFEST_NAME:
            return candidate.resolve()
        candidate = candidate.parent

    current = candidate.resolve()
    for directory in (current,) + tuple(current.parents):
        manifest = directory / PROJECT_MANIFEST_NAME
        if manifest.is_file():
            return manifest.resolve()

    raise ProjectManifestError(
        code="APX-TOOL-001",
        message=(
            f"No {PROJECT_MANIFEST_NAME!r} was found at or above "
            f"{current}."
        ),
        manifest_path=current / PROJECT_MANIFEST_NAME,
    )


def _resolve_source_path(root: Path, relative_name: str) -> Path:
    candidate = root.joinpath(*relative_name.split("/"))
    resolved = candidate.resolve()

    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ProjectManifestError(
            code="APX-TOOL-005",
            message=(
                f"Project source {relative_name!r} resolves outside "
                "the project root."
            ),
            manifest_path=root / PROJECT_MANIFEST_NAME,
        ) from exc

    return resolved


def load_project(
    start: Union[str, Path],
) -> LoadedProject:
    """Find a manifest, validate it, and snapshot all declared source files."""

    manifest_path = find_project_manifest(start)
    manifest = load_project_manifest(manifest_path)
    root = manifest_path.parent.resolve()

    loaded = []
    for relative_name in manifest.sources:
        source_path = _resolve_source_path(root, relative_name)

        if not source_path.is_file():
            raise ProjectManifestError(
                code="APX-TOOL-006",
                message=(
                    f"Declared project source {relative_name!r} was not found."
                ),
                manifest_path=manifest_path,
            )

        try:
            source_bytes = source_path.read_bytes()
            source_text = source_bytes.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ProjectManifestError(
                code="APX-TOOL-007",
                message=(
                    f"Declared project source {relative_name!r} "
                    "is not valid UTF-8."
                ),
                manifest_path=manifest_path,
            ) from exc
        except OSError as exc:
            raise ProjectManifestError(
                code="APX-TOOL-006",
                message=(
                    f"Unable to read declared project source "
                    f"{relative_name!r}: {exc}."
                ),
                manifest_path=manifest_path,
            ) from exc

        # Preserve the existing universal-newline source-text contract while
        # retaining the exact loaded bytes for content-addressed tooling.
        source_text = source_text.replace("\r\n", "\n").replace("\r", "\n")

        loaded.append(
            LoadedProjectSource(
                name=relative_name,
                path=source_path,
                source=source_text,
                source_bytes=source_bytes,
            )
        )

    return LoadedProject(
        root=root,
        manifest_path=manifest_path,
        manifest=manifest,
        sources=tuple(loaded),
    )


__all__ = (
    "LoadedProject",
    "LoadedProjectSource",
    "find_project_manifest",
    "load_project",
)
