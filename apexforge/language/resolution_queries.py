"""Pure structured resolution queries over passive project candidates."""

from __future__ import annotations

from dataclasses import dataclass
import re

from language.resolution_candidates import (
    ProjectResolutionCandidate,
    ProjectResolutionCandidateIndex,
)


_DECLARATION_KINDS = frozenset(("directive", "function"))
_NAME_PATTERN = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")


def _require_kind(value: object) -> str:
    if not isinstance(value, str):
        raise TypeError("ProjectResolutionQuery.kind must be a string.")
    if value not in _DECLARATION_KINDS:
        raise ValueError(
            "ProjectResolutionQuery.kind must be 'directive' or 'function'."
        )
    return value


def _require_segments(value: object, *, label: str) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise TypeError(f"{label} must be an iterable of strings.")
    try:
        segments = tuple(value)  # type: ignore[arg-type]
    except TypeError as error:
        raise TypeError(f"{label} must be an iterable of strings.") from error
    if any(not isinstance(segment, str) for segment in segments):
        raise TypeError(f"{label} must contain only strings.")
    if any(_NAME_PATTERN.fullmatch(segment) is None for segment in segments):
        raise ValueError(f"{label} must contain only ApexForge identifiers.")
    return segments


@dataclass(frozen=True)
class ProjectResolutionQuery:
    """One structured declaration request with an explicit module mode."""

    kind: str
    declaration_path: tuple[str, ...]
    module_segments: tuple[str, ...] | None = None

    def __post_init__(self) -> None:
        kind = _require_kind(self.kind)
        declaration_path = _require_segments(
            self.declaration_path,
            label="ProjectResolutionQuery.declaration_path",
        )
        if len(declaration_path) != 1:
            raise ValueError(
                "ProjectResolutionQuery.declaration_path must contain exactly "
                "one segment in P11.4E."
            )
        module_segments = (
            None
            if self.module_segments is None
            else _require_segments(
                self.module_segments,
                label="ProjectResolutionQuery.module_segments",
            )
        )
        object.__setattr__(self, "kind", kind)
        object.__setattr__(self, "declaration_path", declaration_path)
        object.__setattr__(self, "module_segments", module_segments)


def _candidate_matches_query(
    candidate: ProjectResolutionCandidate,
    query: ProjectResolutionQuery,
) -> bool:
    qualification = candidate.qualification
    if (
        qualification.kind != query.kind
        or qualification.declaration_path != query.declaration_path
    ):
        return False
    if query.module_segments is None:
        return True
    if not query.module_segments:
        return qualification.legacy and qualification.module_segments == ()
    return (
        not qualification.legacy
        and qualification.module_segments == query.module_segments
    )


@dataclass(frozen=True)
class ProjectResolvedBinding:
    """A matching candidate returned only for a unique indexed match."""

    query: ProjectResolutionQuery
    candidate: ProjectResolutionCandidate

    def __post_init__(self) -> None:
        if not isinstance(self.query, ProjectResolutionQuery):
            raise TypeError(
                "ProjectResolvedBinding.query must be ProjectResolutionQuery."
            )
        if not isinstance(self.candidate, ProjectResolutionCandidate):
            raise TypeError(
                "ProjectResolvedBinding.candidate must be "
                "ProjectResolutionCandidate."
            )
        if not _candidate_matches_query(self.candidate, self.query):
            raise ValueError(
                "ProjectResolvedBinding.candidate must exactly match its query."
            )


@dataclass(frozen=True)
class ProjectUnresolvedResolution:
    """An explicit zero-match result without a diagnostic."""

    query: ProjectResolutionQuery

    def __post_init__(self) -> None:
        if not isinstance(self.query, ProjectResolutionQuery):
            raise TypeError(
                "ProjectUnresolvedResolution.query must be "
                "ProjectResolutionQuery."
            )


@dataclass(frozen=True)
class ProjectAmbiguousResolution:
    """Canonical two-or-more-match evidence without winner selection."""

    query: ProjectResolutionQuery
    candidates: tuple[ProjectResolutionCandidate, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.query, ProjectResolutionQuery):
            raise TypeError(
                "ProjectAmbiguousResolution.query must be ProjectResolutionQuery."
            )
        candidates = ProjectResolutionCandidateIndex(
            tuple(self.candidates)
        ).candidates
        if len(candidates) < 2:
            raise ValueError(
                "ProjectAmbiguousResolution requires at least two candidates."
            )
        if any(
            not _candidate_matches_query(candidate, self.query)
            for candidate in candidates
        ):
            raise ValueError(
                "Every ambiguous candidate must exactly match the query."
            )
        object.__setattr__(self, "candidates", candidates)


def resolve_project_query(
    index: ProjectResolutionCandidateIndex,
    query: ProjectResolutionQuery,
) -> (
    ProjectResolvedBinding
    | ProjectUnresolvedResolution
    | ProjectAmbiguousResolution
):
    """Return an outcome determined only by the exact matching fact count."""

    if not isinstance(index, ProjectResolutionCandidateIndex):
        raise TypeError(
            "resolve_project_query.index must be "
            "ProjectResolutionCandidateIndex."
        )
    if not isinstance(query, ProjectResolutionQuery):
        raise TypeError(
            "resolve_project_query.query must be ProjectResolutionQuery."
        )
    matches = tuple(
        candidate
        for candidate in index.candidates
        if _candidate_matches_query(candidate, query)
    )
    if not matches:
        return ProjectUnresolvedResolution(query)
    if len(matches) == 1:
        return ProjectResolvedBinding(query, matches[0])
    return ProjectAmbiguousResolution(query, matches)


__all__ = (
    "ProjectResolutionQuery",
    "ProjectResolvedBinding",
    "ProjectUnresolvedResolution",
    "ProjectAmbiguousResolution",
    "resolve_project_query",
)
