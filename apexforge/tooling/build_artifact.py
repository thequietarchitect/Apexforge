"""Canonical P11.1C multi-source build-artifact construction and writing."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Any, Mapping, Optional, TYPE_CHECKING, Union

from air.serialization import air_to_dict
from tooling.project_loader import LoadedProject


if TYPE_CHECKING:
    from language.project import ProjectBuild


BUILD_ARTIFACT_SCHEMA = "apexforge.build-artifact/v1"
BUILD_ARTIFACT_FINGERPRINT_ALGORITHM = "sha256"


class BuildArtifactOutputError(OSError):
    """The fully constructed artifact could not be atomically written."""


@dataclass(frozen=True)
class CanonicalBuildArtifact:
    """One fully serialized artifact ready for an atomic filesystem write."""

    content: bytes
    entry: Optional[str]
    fingerprint: str
    source_count: int


def canonical_json_bytes(value: Mapping[str, Any]) -> bytes:
    """Serialize a mapping under the P11.1C canonical JSON contract."""

    text = (
        json.dumps(
            value,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    return text.encode("utf-8")


def _artifact_entry(build: ProjectBuild) -> Optional[str]:
    if build.entry_directive is not None:
        return build.resolve_entry()

    if len(tuple(build.program.directives)) == 1:
        return build.resolve_entry()

    return None


def construct_build_artifact(
    loaded: LoadedProject,
    build: ProjectBuild,
) -> CanonicalBuildArtifact:
    """Construct and fingerprint one canonical linked build in memory."""

    entry = _artifact_entry(build)
    sources = [
        {
            "path": source.name,
            "sha256": hashlib.sha256(source.source_bytes).hexdigest(),
        }
        for source in loaded.sources
    ]
    project = {
        "entry": entry,
        "name": loaded.manifest.name,
        "source_count": len(sources),
        "sources": sources,
    }
    payload = {
        "air": air_to_dict(build.program),
        "project": project,
        "schema": BUILD_ARTIFACT_SCHEMA,
    }
    fingerprint = hashlib.sha256(canonical_json_bytes(payload)).hexdigest()
    artifact = dict(payload)
    artifact["fingerprint"] = {
        "algorithm": BUILD_ARTIFACT_FINGERPRINT_ALGORITHM,
        "value": fingerprint,
    }

    return CanonicalBuildArtifact(
        content=canonical_json_bytes(artifact),
        entry=entry,
        fingerprint=fingerprint,
        source_count=len(sources),
    )


def write_build_artifact_atomic(
    artifact: CanonicalBuildArtifact,
    output_path: Union[str, Path],
) -> None:
    """Write through a temporary sibling and atomically replace on success."""

    output = Path(output_path)
    temporary_path: Optional[Path] = None
    file_descriptor: Optional[int] = None

    try:
        file_descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{output.name}.",
            suffix=".tmp",
            dir=str(output.parent),
        )
        temporary_path = Path(temporary_name)

        with os.fdopen(file_descriptor, "wb") as stream:
            file_descriptor = None
            stream.write(artifact.content)
            stream.flush()
            os.fsync(stream.fileno())

        os.replace(temporary_path, output)
        temporary_path = None
    except (OSError, ValueError) as exc:
        if file_descriptor is not None:
            try:
                os.close(file_descriptor)
            except OSError:
                pass
        if temporary_path is not None:
            try:
                temporary_path.unlink()
            except OSError:
                pass
        raise BuildArtifactOutputError(
            "[APX-BUILD-040] Unable to write build artifact."
        ) from exc


__all__ = (
    "BUILD_ARTIFACT_FINGERPRINT_ALGORITHM",
    "BUILD_ARTIFACT_SCHEMA",
    "BuildArtifactOutputError",
    "CanonicalBuildArtifact",
    "canonical_json_bytes",
    "construct_build_artifact",
    "write_build_artifact_atomic",
)
