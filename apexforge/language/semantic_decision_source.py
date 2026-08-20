"""Immutable source-provenance AST records for semantic-decision syntax."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from language.source import SourceSpan


__all__ = (
    "SemanticDecisionSourceIdentifier",
    "SemanticDecisionSourceScalar",
    "SemanticDecisionSourceCandidate",
    "SemanticDecisionSourceIncompatibility",
    "SemanticDecisionSourceConvergence",
    "SemanticDecisionSourceParadoxElevation",
    "SemanticDecisionSourceDeclaration",
    "SemanticDecisionSourceDocument",
)


_SCALAR_KINDS = frozenset({"identifier", "string", "boolean", "expression"})


def _require_span(value: Any, field_name: str) -> SourceSpan:
    if not isinstance(value, SourceSpan):
        raise TypeError(f"{field_name} must be SourceSpan.")
    return value


def _require_exact_text(
    value: Any,
    field_name: str,
    *,
    allow_empty: bool = False,
) -> str:
    if type(value) is not str:
        raise TypeError(f"{field_name} must be an exact str.")
    if not allow_empty and not value:
        raise ValueError(f"{field_name} must not be empty.")
    if value != value.strip():
        raise ValueError(f"{field_name} must not contain surrounding whitespace.")
    return value


def _require_exact_record(
    value: Any,
    expected_type: type,
    field_name: str,
):
    if type(value) is not expected_type:
        raise TypeError(
            f"{field_name} must be an exact {expected_type.__name__}."
        )
    return value


def _require_tuple(
    value: Any,
    item_type: type,
    field_name: str,
) -> tuple:
    if type(value) is not tuple:
        raise TypeError(f"{field_name} must be an exact tuple.")
    if any(type(item) is not item_type for item in value):
        raise TypeError(
            f"{field_name} must contain exact {item_type.__name__} values."
        )
    return value


def _require_optional_scalar_pair(
    keyword_span: Optional[SourceSpan],
    value: Optional["SemanticDecisionSourceScalar"],
    *,
    owner: str,
    field_name: str,
) -> None:
    if keyword_span is None and value is None:
        return
    if keyword_span is None or value is None:
        raise ValueError(
            f"{owner}.{field_name} keyword span and value must be present together."
        )
    _require_span(keyword_span, f"{owner}.{field_name}_keyword_span")
    _require_exact_record(
        value,
        SemanticDecisionSourceScalar,
        f"{owner}.{field_name}",
    )


@dataclass(frozen=True)
class SemanticDecisionSourceIdentifier:
    """One exact bare source identifier and its complete token span."""

    text: str
    span: SourceSpan

    def __post_init__(self) -> None:
        _require_exact_text(self.text, "SemanticDecisionSourceIdentifier.text")
        _require_span(self.span, "SemanticDecisionSourceIdentifier.span")


@dataclass(frozen=True)
class SemanticDecisionSourceScalar:
    """One exact passive source scalar or preserved expression text."""

    kind: str
    text: str
    span: SourceSpan

    def __post_init__(self) -> None:
        _require_exact_text(self.kind, "SemanticDecisionSourceScalar.kind")
        if self.kind not in _SCALAR_KINDS:
            raise ValueError(
                f"unsupported semantic-decision source scalar kind {self.kind!r}."
            )
        if type(self.text) is not str:
            raise TypeError("SemanticDecisionSourceScalar.text must be an exact str.")
        if self.kind == "string":
            pass
        else:
            _require_exact_text(
                self.text,
                "SemanticDecisionSourceScalar.text",
            )
        if self.kind == "boolean" and self.text not in {"true", "false"}:
            raise ValueError(
                "SemanticDecisionSourceScalar boolean text must be 'true' or 'false'."
            )
        _require_span(self.span, "SemanticDecisionSourceScalar.span")


@dataclass(frozen=True)
class SemanticDecisionSourceCandidate:
    """One authored candidate and optional passive authored condition."""

    keyword_span: SourceSpan
    name: SemanticDecisionSourceIdentifier
    span: SourceSpan
    when_keyword_span: Optional[SourceSpan] = None
    condition: Optional[SemanticDecisionSourceScalar] = None

    def __post_init__(self) -> None:
        _require_span(
            self.keyword_span,
            "SemanticDecisionSourceCandidate.keyword_span",
        )
        _require_exact_record(
            self.name,
            SemanticDecisionSourceIdentifier,
            "SemanticDecisionSourceCandidate.name",
        )
        _require_span(self.span, "SemanticDecisionSourceCandidate.span")
        _require_optional_scalar_pair(
            self.when_keyword_span,
            self.condition,
            owner="SemanticDecisionSourceCandidate",
            field_name="condition",
        )


@dataclass(frozen=True)
class SemanticDecisionSourceIncompatibility:
    """One passive authored incompatibility assertion between candidate names."""

    keyword_span: SourceSpan
    left: SemanticDecisionSourceIdentifier
    right: SemanticDecisionSourceIdentifier
    span: SourceSpan

    def __post_init__(self) -> None:
        _require_span(
            self.keyword_span,
            "SemanticDecisionSourceIncompatibility.keyword_span",
        )
        _require_exact_record(
            self.left,
            SemanticDecisionSourceIdentifier,
            "SemanticDecisionSourceIncompatibility.left",
        )
        _require_exact_record(
            self.right,
            SemanticDecisionSourceIdentifier,
            "SemanticDecisionSourceIncompatibility.right",
        )
        _require_span(self.span, "SemanticDecisionSourceIncompatibility.span")


@dataclass(frozen=True)
class SemanticDecisionSourceConvergence:
    """One authored policy reference and deterministic candidate order."""

    keyword_span: SourceSpan
    using_keyword_span: SourceSpan
    policy: SemanticDecisionSourceScalar
    candidates: tuple[SemanticDecisionSourceIdentifier, ...]
    span: SourceSpan

    def __post_init__(self) -> None:
        _require_span(
            self.keyword_span,
            "SemanticDecisionSourceConvergence.keyword_span",
        )
        _require_span(
            self.using_keyword_span,
            "SemanticDecisionSourceConvergence.using_keyword_span",
        )
        _require_exact_record(
            self.policy,
            SemanticDecisionSourceScalar,
            "SemanticDecisionSourceConvergence.policy",
        )
        if self.policy.kind not in {"identifier", "string"}:
            raise ValueError(
                "SemanticDecisionSourceConvergence.policy must be identifier or string."
            )
        _require_tuple(
            self.candidates,
            SemanticDecisionSourceIdentifier,
            "SemanticDecisionSourceConvergence.candidates",
        )
        if not self.candidates:
            raise ValueError(
                "SemanticDecisionSourceConvergence.candidates must not be empty."
            )
        _require_span(self.span, "SemanticDecisionSourceConvergence.span")


@dataclass(frozen=True)
class SemanticDecisionSourceParadoxElevation:
    """One passive authored request to assess/elevate a paradox condition."""

    paradox_keyword_span: SourceSpan
    elevate_keyword_span: SourceSpan
    span: SourceSpan
    when_keyword_span: Optional[SourceSpan] = None
    condition: Optional[SemanticDecisionSourceScalar] = None
    requires_keyword_span: Optional[SourceSpan] = None
    requirement: Optional[SemanticDecisionSourceScalar] = None

    def __post_init__(self) -> None:
        _require_span(
            self.paradox_keyword_span,
            "SemanticDecisionSourceParadoxElevation.paradox_keyword_span",
        )
        _require_span(
            self.elevate_keyword_span,
            "SemanticDecisionSourceParadoxElevation.elevate_keyword_span",
        )
        _require_span(self.span, "SemanticDecisionSourceParadoxElevation.span")
        _require_optional_scalar_pair(
            self.when_keyword_span,
            self.condition,
            owner="SemanticDecisionSourceParadoxElevation",
            field_name="condition",
        )
        _require_optional_scalar_pair(
            self.requires_keyword_span,
            self.requirement,
            owner="SemanticDecisionSourceParadoxElevation",
            field_name="requirement",
        )


@dataclass(frozen=True)
class SemanticDecisionSourceDeclaration:
    """One passive authored semantic-decision declaration."""

    keyword_span: SourceSpan
    name: SemanticDecisionSourceIdentifier
    candidates: tuple[SemanticDecisionSourceCandidate, ...]
    incompatibilities: tuple[SemanticDecisionSourceIncompatibility, ...]
    span: SourceSpan
    convergence: Optional[SemanticDecisionSourceConvergence] = None
    paradox_elevation: Optional[SemanticDecisionSourceParadoxElevation] = None

    def __post_init__(self) -> None:
        _require_span(
            self.keyword_span,
            "SemanticDecisionSourceDeclaration.keyword_span",
        )
        _require_exact_record(
            self.name,
            SemanticDecisionSourceIdentifier,
            "SemanticDecisionSourceDeclaration.name",
        )
        _require_tuple(
            self.candidates,
            SemanticDecisionSourceCandidate,
            "SemanticDecisionSourceDeclaration.candidates",
        )
        _require_tuple(
            self.incompatibilities,
            SemanticDecisionSourceIncompatibility,
            "SemanticDecisionSourceDeclaration.incompatibilities",
        )
        _require_span(self.span, "SemanticDecisionSourceDeclaration.span")
        if self.convergence is not None:
            _require_exact_record(
                self.convergence,
                SemanticDecisionSourceConvergence,
                "SemanticDecisionSourceDeclaration.convergence",
            )
        if self.paradox_elevation is not None:
            _require_exact_record(
                self.paradox_elevation,
                SemanticDecisionSourceParadoxElevation,
                "SemanticDecisionSourceDeclaration.paradox_elevation",
            )


@dataclass(frozen=True)
class SemanticDecisionSourceDocument:
    """One immutable semantic-decision source document."""

    decisions: tuple[SemanticDecisionSourceDeclaration, ...]
    span: SourceSpan

    def __post_init__(self) -> None:
        _require_tuple(
            self.decisions,
            SemanticDecisionSourceDeclaration,
            "SemanticDecisionSourceDocument.decisions",
        )
        if not self.decisions:
            raise ValueError(
                "SemanticDecisionSourceDocument.decisions must not be empty."
            )
        _require_span(self.span, "SemanticDecisionSourceDocument.span")