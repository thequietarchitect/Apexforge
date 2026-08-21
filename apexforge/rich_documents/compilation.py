"""P11.13D extraction and canonical compilation of Apex document blocks.

This module does not implement an Apex parser or compiler. It extracts blocks
classified as ``apex`` and delegates each exact block string to
``language.compiler.compile_source_with_map``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

from language.compiler import CompiledSource, compile_source_with_map
from language.source import SourceSpan
from rich_documents.model import (
    ApexDocument,
    DocumentBlockKind,
)


@dataclass(frozen=True)
class ApexExecutableBlockSource:
    """One extracted Apex source block with original document lineage."""

    document_id: str
    block_id: str
    source_name: str
    text: str
    span: Optional[SourceSpan]

    def __post_init__(self) -> None:
        for field_name, value in (
            ("document_id", self.document_id),
            ("block_id", self.block_id),
            ("source_name", self.source_name),
        ):
            if type(value) is not str:
                raise TypeError(
                    "ApexExecutableBlockSource.{} must be an exact str".format(
                        field_name
                    )
                )
            if not value or value != value.strip():
                raise ValueError(
                    "ApexExecutableBlockSource.{} must be non-empty and "
                    "trimmed".format(field_name)
                )
        if type(self.text) is not str:
            raise TypeError(
                "ApexExecutableBlockSource.text must be an exact str"
            )
        if self.span is not None and type(self.span) is not SourceSpan:
            raise TypeError(
                "ApexExecutableBlockSource.span must be None or exact "
                "SourceSpan"
            )


@dataclass(frozen=True)
class ApexExecutableBlockCompilation:
    """Canonical CompiledSource paired with immutable rich-document lineage."""

    source: ApexExecutableBlockSource
    compiled: CompiledSource

    def __post_init__(self) -> None:
        if type(self.source) is not ApexExecutableBlockSource:
            raise TypeError(
                "ApexExecutableBlockCompilation.source must be an exact "
                "ApexExecutableBlockSource"
            )
        if type(self.compiled) is not CompiledSource:
            raise TypeError(
                "ApexExecutableBlockCompilation.compiled must be an exact "
                "CompiledSource"
            )
        for entry in self.compiled.source_map.entries:
            if entry.span.source_name != self.source.source_name:
                raise ValueError(
                    "CompiledSource source-map entry lost executable block "
                    "virtual source identity"
                )


def _virtual_source_name(
    document: ApexDocument,
    block_id: str,
) -> str:
    return "{}::apexdoc::{}::{}".format(
        document.source_name,
        document.document_id,
        block_id,
    )


def extract_apex_executable_blocks(
    document: ApexDocument,
) -> Tuple[ApexExecutableBlockSource, ...]:
    """Extract Apex blocks in document encounter order without rewriting text."""

    if type(document) is not ApexDocument:
        raise TypeError("document must be an exact ApexDocument")

    result = []
    for block in document.blocks:
        if block.kind is not DocumentBlockKind.APEX:
            continue
        result.append(
            ApexExecutableBlockSource(
                document_id=document.document_id,
                block_id=block.block_id,
                source_name=_virtual_source_name(
                    document,
                    block.block_id,
                ),
                text=block.content,
                span=block.span,
            )
        )
    return tuple(result)


def compile_apex_document_blocks(
    document: ApexDocument,
) -> Tuple[ApexExecutableBlockCompilation, ...]:
    """Compile extracted Apex blocks through the canonical compiler owner."""

    result = []
    for source in extract_apex_executable_blocks(document):
        compiled = compile_source_with_map(
            source.text,
            source_name=source.source_name,
        )
        result.append(
            ApexExecutableBlockCompilation(
                source=source,
                compiled=compiled,
            )
        )
    return tuple(result)


__all__ = (
    "ApexExecutableBlockSource",
    "ApexExecutableBlockCompilation",
    "extract_apex_executable_blocks",
    "compile_apex_document_blocks",
)