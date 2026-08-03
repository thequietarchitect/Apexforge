"""Passive use-site context and factual visibility evidence."""

from __future__ import annotations

from dataclasses import dataclass
import re

from language.resolution_candidates import (
    ProjectResolutionCandidate,
    ProjectResolutionCandidateIndex,
)
from language.resolution_queries import (
    ProjectAmbiguousResolution,
    ProjectResolutionQuery,
    ProjectResolvedBinding,
    ProjectUnresolvedResolution,
    resolve_project_query,
)


_NAME_PATTERN = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")


def _require_segments(
    value: object,
    *,
    label: str,
    allow_empty: bool,
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise TypeError(f"{label} must be an iterable of strings.")
    try:
        segments = tuple(value)  # type: ignore[arg-type]
    except TypeError as error:
        raise TypeError(f"{label} must be an iterable of strings.") from error
    if not allow_empty and not segments:
        raise ValueError(f"{label} must contain at least one segment.")
    if any(not isinstance(segment, str) for segment in segments):
        raise TypeError(f"{label} must contain only strings.")
    if any(_NAME_PATTERN.fullmatch(segment) is None for segment in segments):
        raise ValueError(f"{label} must contain only ApexForge identifiers.")
    return segments


def _require_imported_modules(
    value: object,
) -> tuple[tuple[str, ...], ...]:
    if isinstance(value, (str, bytes)):
        raise TypeError(
            "ProjectResolutionContext.imported_modules must be an iterable "
            "of module paths."
        )
    try:
        modules = tuple(value)  # type: ignore[arg-type]
    except TypeError as error:
        raise TypeError(
            "ProjectResolutionContext.imported_modules must be an iterable "
            "of module paths."
        ) from error
    normalized = tuple(
        _require_segments(
            module,
            label="ProjectResolutionContext imported module",
            allow_empty=False,
        )
        for module in modules
    )
    return tuple(sorted(normalized))


@dataclass(frozen=True)
class ProjectResolutionContext:
    """Caller-supplied physical-source, module, and import facts."""

    source_name: str
    module_segments: tuple[str, ...]
    imported_modules: tuple[tuple[str, ...], ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.source_name, str):
            raise TypeError("ProjectResolutionContext.source_name must be a string.")
        if not self.source_name:
            raise ValueError("ProjectResolutionContext.source_name cannot be empty.")
        if "\0" in self.source_name:
            raise ValueError(
                "ProjectResolutionContext.source_name cannot contain NUL."
            )
        module_segments = _require_segments(
            self.module_segments,
            label="ProjectResolutionContext.module_segments",
            allow_empty=True,
        )
        imported_modules = _require_imported_modules(self.imported_modules)
        object.__setattr__(self, "module_segments", module_segments)
        object.__setattr__(self, "imported_modules", imported_modules)


def _matching_candidates(
    candidate: ProjectResolutionCandidate,
    query: ProjectResolutionQuery,
) -> tuple[ProjectResolutionCandidate, ...]:
    outcome = resolve_project_query(
        ProjectResolutionCandidateIndex((candidate,)),
        query,
    )
    if isinstance(outcome, ProjectUnresolvedResolution):
        return ()
    if isinstance(outcome, ProjectResolvedBinding):
        return (outcome.candidate,)
    if isinstance(outcome, ProjectAmbiguousResolution):
        return outcome.candidates
    raise TypeError("Unexpected structured resolution outcome.")


def _derived_flags(
    context: ProjectResolutionContext,
    candidate: ProjectResolutionCandidate,
) -> tuple[bool, bool, bool, bool]:
    qualification = candidate.qualification
    legacy_candidate = qualification.legacy
    same_source = candidate.identity.source_name == context.source_name
    same_module = bool(context.module_segments) and not legacy_candidate and (
        qualification.module_segments == context.module_segments
    )
    imported_module = not legacy_candidate and (
        qualification.module_segments in context.imported_modules
    )
    return same_source, same_module, imported_module, legacy_candidate


@dataclass(frozen=True)
class ProjectVisibilityEvidence:
    """Exact relationship facts for one query-matching candidate."""

    query: ProjectResolutionQuery
    context: ProjectResolutionContext
    candidate: ProjectResolutionCandidate
    same_source: bool
    same_module: bool
    imported_module: bool
    legacy_candidate: bool

    def __post_init__(self) -> None:
        if type(self.query) is not ProjectResolutionQuery:
            raise TypeError(
                "ProjectVisibilityEvidence.query must be "
                "ProjectResolutionQuery."
            )
        if type(self.context) is not ProjectResolutionContext:
            raise TypeError(
                "ProjectVisibilityEvidence.context must be "
                "ProjectResolutionContext."
            )
        if type(self.candidate) is not ProjectResolutionCandidate:
            raise TypeError(
                "ProjectVisibilityEvidence.candidate must be "
                "ProjectResolutionCandidate."
            )
        if not _matching_candidates(self.candidate, self.query):
            raise ValueError(
                "ProjectVisibilityEvidence.candidate must exactly match its query."
            )
        flags = (
            self.same_source,
            self.same_module,
            self.imported_module,
            self.legacy_candidate,
        )
        if any(type(flag) is not bool for flag in flags):
            raise TypeError("ProjectVisibilityEvidence flags must be bool values.")
        if flags != _derived_flags(self.context, self.candidate):
            raise ValueError(
                "ProjectVisibilityEvidence flags must equal their derived facts."
            )


def collect_project_visibility_evidence(
    index: ProjectResolutionCandidateIndex,
    query: ProjectResolutionQuery,
    context: ProjectResolutionContext,
) -> tuple[ProjectVisibilityEvidence, ...]:
    """Return factual evidence for every exact structured-query match."""

    if type(index) is not ProjectResolutionCandidateIndex:
        raise TypeError(
            "collect_project_visibility_evidence.index must be "
            "ProjectResolutionCandidateIndex."
        )
    if type(query) is not ProjectResolutionQuery:
        raise TypeError(
            "collect_project_visibility_evidence.query must be "
            "ProjectResolutionQuery."
        )
    if type(context) is not ProjectResolutionContext:
        raise TypeError(
            "collect_project_visibility_evidence.context must be "
            "ProjectResolutionContext."
        )

    outcome = resolve_project_query(index, query)
    if isinstance(outcome, ProjectUnresolvedResolution):
        candidates: tuple[ProjectResolutionCandidate, ...] = ()
    elif isinstance(outcome, ProjectResolvedBinding):
        candidates = (outcome.candidate,)
    elif isinstance(outcome, ProjectAmbiguousResolution):
        candidates = outcome.candidates
    else:
        raise TypeError("Unexpected structured resolution outcome.")

    return tuple(
        ProjectVisibilityEvidence(
            query=query,
            context=context,
            candidate=candidate,
            same_source=_derived_flags(context, candidate)[0],
            same_module=_derived_flags(context, candidate)[1],
            imported_module=_derived_flags(context, candidate)[2],
            legacy_candidate=_derived_flags(context, candidate)[3],
        )
        for candidate in candidates
    )


__all__ = (
    "ProjectResolutionContext",
    "ProjectVisibilityEvidence",
    "collect_project_visibility_evidence",
)
