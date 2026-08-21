"""Minimal immutable model for P11.13 rich documents and package tiers.

This module defines structure only. It does not parse ``.apexdoc`` files,
compile executable blocks, mutate project manifests, resolve packages, access
remote registries, execute runtime behavior, or duplicate narrative semantics.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple

from language.source import SourceSpan


RICH_DOCUMENT_SCHEMA_VERSION = 1

DOCUMENT_BLOCK_KIND_IDS = (
    "text",
    "apex",
    "semantic-table",
    "diagram",
    "world-bible",
    "character-sheet",
    "simulation-description",
)

PACKAGE_TIER_IDS = (
    "core",
    "standard",
    "domain",
    "experimental",
)


class DocumentBlockKind(str, Enum):
    """Canonical rich-document block classifications."""

    TEXT = "text"
    APEX = "apex"
    SEMANTIC_TABLE = "semantic-table"
    DIAGRAM = "diagram"
    WORLD_BIBLE = "world-bible"
    CHARACTER_SHEET = "character-sheet"
    SIMULATION_DESCRIPTION = "simulation-description"


class PackageTier(str, Enum):
    """Canonical P11.13 package tier classifications."""

    CORE = "core"
    STANDARD = "standard"
    DOMAIN = "domain"
    EXPERIMENTAL = "experimental"


Metadata = Tuple[Tuple[str, str], ...]


def _require_nonempty_string(value: object, *, owner: str) -> str:
    if type(value) is not str:
        raise TypeError(
            "{} must be a str; received {}".format(
                owner,
                type(value).__name__,
            )
        )
    if not value.strip():
        raise ValueError("{} must not be empty or whitespace".format(owner))
    return value


def _validate_metadata(
    metadata: object,
    *,
    owner: str,
) -> Metadata:
    if type(metadata) is not tuple:
        raise TypeError("{} must be a tuple".format(owner))

    seen = set()
    for index, item in enumerate(metadata):
        if type(item) is not tuple or len(item) != 2:
            raise TypeError(
                "{} item {} must be an exact (str, str) tuple".format(
                    owner,
                    index,
                )
            )
        key, value = item
        if type(key) is not str or type(value) is not str:
            raise TypeError(
                "{} item {} must contain only str values".format(
                    owner,
                    index,
                )
            )
        if not key.strip():
            raise ValueError(
                "{} item {} key must not be empty or whitespace".format(
                    owner,
                    index,
                )
            )
        if key in seen:
            raise ValueError(
                "{} contains duplicate key {!r}".format(owner, key)
            )
        seen.add(key)

    return metadata


@dataclass(frozen=True)
class ApexDocumentBlock:
    """One immutable block inside an :class:`ApexDocument`."""

    block_id: str
    kind: DocumentBlockKind
    content: str
    span: Optional[SourceSpan] = None
    metadata: Metadata = ()

    def __post_init__(self) -> None:
        _require_nonempty_string(
            self.block_id,
            owner="ApexDocumentBlock.block_id",
        )
        if type(self.kind) is not DocumentBlockKind:
            raise TypeError(
                "ApexDocumentBlock.kind must be an exact DocumentBlockKind"
            )
        if type(self.content) is not str:
            raise TypeError(
                "ApexDocumentBlock.content must be a str; received {}".format(
                    type(self.content).__name__,
                )
            )
        if self.span is not None and type(self.span) is not SourceSpan:
            raise TypeError(
                "ApexDocumentBlock.span must be None or exact SourceSpan"
            )
        _validate_metadata(
            self.metadata,
            owner="ApexDocumentBlock.metadata",
        )


@dataclass(frozen=True)
class ApexDocument:
    """Minimal immutable rich-document container."""

    document_id: str
    source_name: str
    blocks: Tuple[ApexDocumentBlock, ...] = ()
    metadata: Metadata = ()

    def __post_init__(self) -> None:
        _require_nonempty_string(
            self.document_id,
            owner="ApexDocument.document_id",
        )
        _require_nonempty_string(
            self.source_name,
            owner="ApexDocument.source_name",
        )
        if type(self.blocks) is not tuple:
            raise TypeError("ApexDocument.blocks must be a tuple")

        seen = set()
        for index, block in enumerate(self.blocks):
            if type(block) is not ApexDocumentBlock:
                raise TypeError(
                    "ApexDocument.blocks item {} must be exact "
                    "ApexDocumentBlock".format(index)
                )
            if block.block_id in seen:
                raise ValueError(
                    "ApexDocument.blocks contains duplicate block_id {!r}".format(
                        block.block_id
                    )
                )
            seen.add(block.block_id)

        _validate_metadata(
            self.metadata,
            owner="ApexDocument.metadata",
        )


@dataclass(frozen=True)
class PackageDescriptor:
    """Minimal immutable package-tier descriptor.

    ``documents`` contains ordered document identifiers only. Resolution of
    those identifiers into loaded files/documents belongs to later P11.13
    integration slices.
    """

    package_id: str
    tier: PackageTier
    version: str
    documents: Tuple[str, ...] = ()
    metadata: Metadata = ()

    def __post_init__(self) -> None:
        _require_nonempty_string(
            self.package_id,
            owner="PackageDescriptor.package_id",
        )
        if type(self.tier) is not PackageTier:
            raise TypeError(
                "PackageDescriptor.tier must be an exact PackageTier"
            )
        _require_nonempty_string(
            self.version,
            owner="PackageDescriptor.version",
        )
        if type(self.documents) is not tuple:
            raise TypeError("PackageDescriptor.documents must be a tuple")

        seen = set()
        for index, document_id in enumerate(self.documents):
            _require_nonempty_string(
                document_id,
                owner="PackageDescriptor.documents[{}]".format(index),
            )
            if document_id in seen:
                raise ValueError(
                    "PackageDescriptor.documents contains duplicate "
                    "document identifier {!r}".format(document_id)
                )
            seen.add(document_id)

        _validate_metadata(
            self.metadata,
            owner="PackageDescriptor.metadata",
        )


__all__ = (
    "RICH_DOCUMENT_SCHEMA_VERSION",
    "DOCUMENT_BLOCK_KIND_IDS",
    "PACKAGE_TIER_IDS",
    "DocumentBlockKind",
    "ApexDocumentBlock",
    "ApexDocument",
    "PackageTier",
    "PackageDescriptor",
)