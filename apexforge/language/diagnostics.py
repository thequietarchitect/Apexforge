"""Structured, source-aware diagnostics for ApexForge tooling."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional

from language.source import SourceSpan


DiagnosticSeverity = Literal["error", "warning", "info"]
DiagnosticStage = Literal[
    "lex",
    "parse",
    "compile",
    "module",
    "link",
    "validate",
    "runtime",
]


@dataclass(frozen=True)
class BuildDiagnostic:
    severity: DiagnosticSeverity
    code: str
    message: str
    stage: DiagnosticStage
    span: Optional[SourceSpan] = None
    air_id: str = ""
    related_spans: tuple[SourceSpan, ...] = ()

    def __post_init__(self) -> None:
        if self.severity not in {"error", "warning", "info"}:
            raise ValueError(
                f"Unsupported diagnostic severity {self.severity!r}."
            )

        if self.stage not in {
            "lex",
            "parse",
            "compile",
            "module",
            "link",
            "validate",
            "runtime",
        }:
            raise ValueError(
                f"Unsupported diagnostic stage {self.stage!r}."
            )

        if not isinstance(self.code, str) or not self.code.strip():
            raise ValueError(
                "BuildDiagnostic.code must be a non-empty string."
            )

        if not isinstance(self.message, str) or not self.message.strip():
            raise ValueError(
                "BuildDiagnostic.message must be a non-empty string."
            )

        if self.span is not None and not isinstance(
            self.span,
            SourceSpan,
        ):
            raise TypeError(
                "BuildDiagnostic.span must be SourceSpan or None."
            )

        related = tuple(self.related_spans)
        if any(not isinstance(span, SourceSpan) for span in related):
            raise TypeError(
                "BuildDiagnostic.related_spans must contain "
                "SourceSpan values."
            )

        object.__setattr__(
            self,
            "code",
            self.code.strip(),
        )
        object.__setattr__(
            self,
            "message",
            self.message.strip(),
        )
        object.__setattr__(
            self,
            "related_spans",
            related,
        )

    @property
    def is_error(self) -> bool:
        return self.severity == "error"

    def sort_key(self) -> tuple[object, ...]:
        if self.span is None:
            source_key = (
                "",
                "",
                -1,
                -1,
            )
        else:
            source_key = (
                self.span.source_name.casefold(),
                self.span.source_name,
                self.span.start.offset,
                self.span.end.offset,
            )

        severity_rank = {
            "error": 0,
            "warning": 1,
            "info": 2,
        }[self.severity]

        return (
            *source_key,
            severity_rank,
            self.stage,
            self.code,
            self.message,
        )

    def render(self) -> str:
        prefix = (
            self.span.render_start()
            if self.span is not None
            else "<project>"
        )

        return (
            f"{prefix} [{self.code}] "
            f"{self.message}"
        )


class DiagnosticError(Exception):
    """Exception carrying one canonical BuildDiagnostic."""

    diagnostic: BuildDiagnostic

    def __init__(
        self,
        diagnostic: BuildDiagnostic,
    ) -> None:
        if not isinstance(
            diagnostic,
            BuildDiagnostic,
        ):
            raise TypeError(
                "DiagnosticError requires BuildDiagnostic."
            )

        self.diagnostic = diagnostic
        super().__init__(
            diagnostic.render()
        )


def diagnostics_from_exception(
    error: BaseException,
) -> tuple[BuildDiagnostic, ...]:
    diagnostic = getattr(
        error,
        "diagnostic",
        None,
    )

    if isinstance(
        diagnostic,
        BuildDiagnostic,
    ):
        return (
            diagnostic,
        )

    diagnostics = getattr(
        error,
        "diagnostics",
        None,
    )

    if diagnostics is not None:
        normalized = tuple(
            item
            for item in diagnostics
            if isinstance(
                item,
                BuildDiagnostic,
            )
        )

        if normalized:
            return tuple(
                sorted(
                    normalized,
                    key=lambda item: item.sort_key(),
                )
            )

    return ()


def render_diagnostics(
    diagnostics: tuple[BuildDiagnostic, ...],
) -> str:
    return "\n".join(
        diagnostic.render()
        for diagnostic in sorted(
            diagnostics,
            key=lambda item: item.sort_key(),
        )
    )


__all__ = (
    "BuildDiagnostic",
    "DiagnosticError",
    "DiagnosticSeverity",
    "DiagnosticStage",
    "diagnostics_from_exception",
    "render_diagnostics",
)