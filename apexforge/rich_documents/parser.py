"""Deterministic P11.13D parser for the minimal ``.apexdoc`` container.

The parser owns only rich-document container syntax. Apex block content remains
opaque here and is compiled later through the canonical Apex compiler.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import List, Tuple

from language.diagnostics import BuildDiagnostic
from language.parser import ParseError
from language.source import SourceSpan, SourceText
from rich_documents.model import (
    ApexDocument,
    ApexDocumentBlock,
    DocumentBlockKind,
)


_HEADER_PATTERN = re.compile(r"@apexdoc ([^\s]+)")
_BLOCK_PATTERN = re.compile(r"@block ([^\s]+) ([^\s]+)")


@dataclass(frozen=True)
class _Line:
    start: int
    end: int
    body: str


def _require_source(source_name: object, text: object) -> Tuple[str, str]:
    if type(source_name) is not str:
        raise TypeError("source_name must be an exact str")
    if not source_name or source_name != source_name.strip():
        raise ValueError("source_name must be non-empty and trimmed")
    if type(text) is not str:
        raise TypeError("text must be an exact str")
    return source_name, text


def _lines(text: str) -> Tuple[_Line, ...]:
    result: List[_Line] = []
    offset = 0
    for raw in text.splitlines(keepends=True):
        if raw.endswith("\r\n"):
            body = raw[:-2]
        elif raw.endswith("\n") or raw.endswith("\r"):
            body = raw[:-1]
        else:
            body = raw
        result.append(
            _Line(
                start=offset,
                end=offset + len(raw),
                body=body,
            )
        )
        offset += len(raw)
    return tuple(result)


def _line_span(source: SourceText, line: _Line) -> SourceSpan:
    return source.span(line.start, line.start + len(line.body))


def _raise_parse(
    source: SourceText,
    *,
    code: str,
    message: str,
    span: SourceSpan,
) -> None:
    raise ParseError(
        BuildDiagnostic(
            severity="error",
            code=code,
            message=message,
            stage="parse",
            span=span,
        )
    )


def _eof_span(source: SourceText) -> SourceSpan:
    offset = len(source.text)
    return source.span(offset, offset)


def parse_apex_document(source_name: str, text: str) -> ApexDocument:
    """Parse one minimal P11.13D ``.apexdoc`` document.

    Syntax is deliberately narrow::

        @apexdoc <document-id>

        @block <kind> <block-id>
        <exact block content>
        @endblock

    Blank lines are permitted between blocks. Block content is preserved
    exactly, including original line endings.
    """

    selected_name, selected_text = _require_source(source_name, text)
    source = SourceText(selected_name, selected_text)
    lines = _lines(selected_text)

    if not lines:
        _raise_parse(
            source,
            code="APXDOC-PARSE-001",
            message="Expected @apexdoc document header.",
            span=_eof_span(source),
        )

    header = lines[0]
    match = _HEADER_PATTERN.fullmatch(header.body)
    if match is None:
        _raise_parse(
            source,
            code="APXDOC-PARSE-001",
            message=(
                "The first line must be exactly "
                "'@apexdoc <document-id>'."
            ),
            span=_line_span(source, header),
        )

    document_id = match.group(1)
    blocks: List[ApexDocumentBlock] = []
    index = 1

    while index < len(lines):
        line = lines[index]

        if not line.body.strip():
            index += 1
            continue

        if line.body == "@endblock":
            _raise_parse(
                source,
                code="APXDOC-PARSE-002",
                message="Unexpected @endblock outside a block.",
                span=_line_span(source, line),
            )

        if not line.body.startswith("@block "):
            _raise_parse(
                source,
                code="APXDOC-PARSE-008",
                message=(
                    "Non-blank content outside a block is not permitted "
                    "in P11.13D."
                ),
                span=_line_span(source, line),
            )

        block_match = _BLOCK_PATTERN.fullmatch(line.body)
        if block_match is None:
            _raise_parse(
                source,
                code="APXDOC-PARSE-003",
                message=(
                    "Block opening line must be exactly "
                    "'@block <kind> <block-id>'."
                ),
                span=_line_span(source, line),
            )

        kind_id = block_match.group(1)
        block_id = block_match.group(2)

        try:
            kind = DocumentBlockKind(kind_id)
        except ValueError as error:
            _raise_parse(
                source,
                code="APXDOC-PARSE-004",
                message="Unknown document block kind {!r}.".format(kind_id),
                span=_line_span(source, line),
            )
            raise AssertionError("unreachable") from error

        content_start = line.end
        close_index = index + 1

        while close_index < len(lines):
            candidate = lines[close_index]

            if candidate.body == "@endblock":
                break

            if candidate.body.startswith("@block "):
                _raise_parse(
                    source,
                    code="APXDOC-PARSE-005",
                    message="Nested @block markers are not permitted.",
                    span=_line_span(source, candidate),
                )

            close_index += 1

        if close_index >= len(lines):
            _raise_parse(
                source,
                code="APXDOC-PARSE-006",
                message=(
                    "Block {!r} is missing its exact @endblock line.".format(
                        block_id
                    )
                ),
                span=_line_span(source, line),
            )

        close_line = lines[close_index]
        content_end = close_line.start
        block = ApexDocumentBlock(
            block_id=block_id,
            kind=kind,
            content=selected_text[content_start:content_end],
            span=source.span(content_start, content_end),
            metadata=(),
        )

        # Reuse the frozen B model's identity invariant while the opening-line
        # span is still available for a precise container diagnostic.
        try:
            ApexDocument(
                document_id=document_id,
                source_name=selected_name,
                blocks=tuple(blocks) + (block,),
                metadata=(),
            )
        except ValueError as error:
            _raise_parse(
                source,
                code="APXDOC-PARSE-007",
                message=str(error),
                span=_line_span(source, line),
            )

        blocks.append(block)
        index = close_index + 1

    return ApexDocument(
        document_id=document_id,
        source_name=selected_name,
        blocks=tuple(blocks),
        metadata=(),
    )


__all__ = ("parse_apex_document",)