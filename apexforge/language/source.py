"""Canonical source-position and source-span models for ApexForge."""

from __future__ import annotations

from bisect import bisect_right
from dataclasses import dataclass
from typing import Iterable, Optional


@dataclass(frozen=True, order=True)
class SourcePosition:
    """One position in source text.

    Lines and columns are one-based. Offsets are zero-based character offsets.
    """

    line: int
    column: int
    offset: int

    def __post_init__(self) -> None:
        if isinstance(self.line, bool) or not isinstance(self.line, int):
            raise TypeError("SourcePosition.line must be an integer.")
        if isinstance(self.column, bool) or not isinstance(self.column, int):
            raise TypeError("SourcePosition.column must be an integer.")
        if isinstance(self.offset, bool) or not isinstance(self.offset, int):
            raise TypeError("SourcePosition.offset must be an integer.")
        if self.line < 1:
            raise ValueError("SourcePosition.line must be at least 1.")
        if self.column < 1:
            raise ValueError("SourcePosition.column must be at least 1.")
        if self.offset < 0:
            raise ValueError("SourcePosition.offset cannot be negative.")


@dataclass(frozen=True, order=True)
class SourceSpan:
    """An end-exclusive range in one named source unit."""

    source_name: str
    start: SourcePosition
    end: SourcePosition

    def __post_init__(self) -> None:
        if not isinstance(self.source_name, str):
            raise TypeError("SourceSpan.source_name must be a string.")

        normalized = self.source_name.strip()
        if not normalized:
            raise ValueError("SourceSpan.source_name cannot be empty.")

        if not isinstance(self.start, SourcePosition):
            raise TypeError("SourceSpan.start must be SourcePosition.")
        if not isinstance(self.end, SourcePosition):
            raise TypeError("SourceSpan.end must be SourcePosition.")
        if self.end.offset < self.start.offset:
            raise ValueError("SourceSpan end cannot precede its start.")

        object.__setattr__(self, "source_name", normalized)

    @property
    def is_empty(self) -> bool:
        return self.start.offset == self.end.offset

    def render_start(self) -> str:
        return f"{self.source_name}:{self.start.line}:{self.start.column}"

    def contains_offset(self, offset: int) -> bool:
        if self.is_empty:
            return offset == self.start.offset
        return self.start.offset <= offset < self.end.offset


@dataclass(frozen=True)
class SourceText:
    """A named source string with deterministic offset-to-position mapping."""

    name: str
    text: str
    _line_starts: tuple[int, ...]

    def __init__(self, name: str, text: str) -> None:
        if not isinstance(name, str) or not name.strip():
            raise ValueError("SourceText name must be a non-empty string.")
        if not isinstance(text, str):
            raise TypeError("SourceText text must be a string.")

        starts = [0]
        for index, character in enumerate(text):
            if character == "\n":
                starts.append(index + 1)

        object.__setattr__(self, "name", name.strip())
        object.__setattr__(self, "text", text)
        object.__setattr__(self, "_line_starts", tuple(starts))

    def position(self, offset: int) -> SourcePosition:
        if isinstance(offset, bool) or not isinstance(offset, int):
            raise TypeError("Source offset must be an integer.")
        if offset < 0 or offset > len(self.text):
            raise ValueError(
                f"Source offset {offset} lies outside 0..{len(self.text)}."
            )

        line_index = bisect_right(self._line_starts, offset) - 1
        line_start = self._line_starts[line_index]

        return SourcePosition(
            line=line_index + 1,
            column=offset - line_start + 1,
            offset=offset,
        )

    def span(self, start_offset: int, end_offset: int) -> SourceSpan:
        if end_offset < start_offset:
            raise ValueError("Source span end cannot precede its start.")
        return SourceSpan(
            source_name=self.name,
            start=self.position(start_offset),
            end=self.position(end_offset),
        )


def cover_spans(
    *spans: Optional[SourceSpan],
) -> Optional[SourceSpan]:
    """Return the smallest span covering every non-None input span."""

    present = tuple(span for span in spans if span is not None)
    if not present:
        return None

    source_name = present[0].source_name
    if any(span.source_name != source_name for span in present[1:]):
        raise ValueError("Cannot cover spans from different source units.")

    start = min((span.start for span in present), key=lambda value: value.offset)
    end = max((span.end for span in present), key=lambda value: value.offset)

    return SourceSpan(source_name=source_name, start=start, end=end)


def first_span(spans: Iterable[Optional[SourceSpan]]) -> Optional[SourceSpan]:
    """Return the earliest non-None span in deterministic source order."""

    present = tuple(span for span in spans if span is not None)
    if not present:
        return None

    return min(
        present,
        key=lambda span: (
            span.source_name.casefold(),
            span.source_name,
            span.start.offset,
            span.end.offset,
        ),
    )


__all__ = (
    "SourcePosition",
    "SourceSpan",
    "SourceText",
    "cover_spans",
    "first_span",
)