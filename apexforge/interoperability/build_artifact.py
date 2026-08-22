"""Passive build-artifact interoperability inspection for P11.15B."""

from __future__ import annotations

from dataclasses import dataclass
import json

from tooling.build_artifact import (
    BUILD_ARTIFACT_SCHEMA,
    BUILD_ARTIFACT_SCHEMA_V2,
    BUILD_ARTIFACT_SCHEMA_V3,
)


_SUPPORTED_SCHEMAS = (
    BUILD_ARTIFACT_SCHEMA,
    BUILD_ARTIFACT_SCHEMA_V2,
    BUILD_ARTIFACT_SCHEMA_V3,
)


@dataclass(frozen=True)
class BuildArtifactInterchange:
    """Exact bytes plus one recognized outer build-artifact schema."""

    schema: str
    content: bytes

    def __post_init__(self) -> None:
        if type(self.schema) is not str:
            raise TypeError(
                "BuildArtifactInterchange.schema must be an exact str"
            )
        if self.schema not in _SUPPORTED_SCHEMAS:
            raise ValueError(
                "BuildArtifactInterchange.schema is not supported"
            )
        if type(self.content) is not bytes:
            raise TypeError(
                "BuildArtifactInterchange.content must be exact bytes"
            )
        if not self.content:
            raise ValueError(
                "BuildArtifactInterchange.content must not be empty"
            )


def inspect_build_artifact_interchange(
    content: bytes,
) -> BuildArtifactInterchange:
    """Inspect one build artifact without reconstructing or executing it."""

    if type(content) is not bytes:
        raise TypeError(
            "inspect_build_artifact_interchange requires exact bytes"
        )
    if not content:
        raise ValueError(
            "inspect_build_artifact_interchange content must not be empty"
        )

    text = content.decode("utf-8")
    value = json.loads(text)

    if type(value) is not dict:
        raise ValueError(
            "build artifact interchange content must contain a JSON object"
        )

    schema = value.get("schema")
    if type(schema) is not str:
        raise ValueError(
            "build artifact interchange schema must be an exact str"
        )
    if schema not in _SUPPORTED_SCHEMAS:
        raise ValueError(
            "build artifact interchange schema is not supported"
        )

    return BuildArtifactInterchange(
        schema=schema,
        content=content,
    )


__all__ = (
    "BuildArtifactInterchange",
    "inspect_build_artifact_interchange",
)