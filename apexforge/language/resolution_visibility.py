"""Fixed visibility policy over passive project visibility evidence."""

from __future__ import annotations

from dataclasses import dataclass

from language.resolution_candidates import (
    ProjectResolutionCandidate,
    ProjectResolutionCandidateIndex,
)
from language.resolution_context import (
    ProjectResolutionContext,
    ProjectVisibilityEvidence,
    collect_project_visibility_evidence,
)
from language.resolution_queries import ProjectResolutionQuery


_VISIBILITY_BASIS_ORDER = (
    "same_source",
    "same_module",
    "imported_module",
    "legacy_context",
)
_VISIBILITY_BASIS_SET = frozenset(_VISIBILITY_BASIS_ORDER)


def _derive_visibility_basis(
    evidence: ProjectVisibilityEvidence,
) -> tuple[str, ...]:
    applicable = {
        "same_source": evidence.same_source,
        "same_module": evidence.same_module,
        "imported_module": evidence.imported_module,
        "legacy_context": (
            evidence.legacy_candidate
            and evidence.context.module_segments == ()
        ),
    }
    return tuple(
        basis for basis in _VISIBILITY_BASIS_ORDER if applicable[basis]
    )


def _require_basis(value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise TypeError(
            "ProjectVisibilityDecision.visibility_basis must be an iterable "
            "of strings."
        )
    try:
        basis = tuple(value)  # type: ignore[arg-type]
    except TypeError as error:
        raise TypeError(
            "ProjectVisibilityDecision.visibility_basis must be an iterable "
            "of strings."
        ) from error
    if any(type(item) is not str for item in basis):
        raise TypeError(
            "ProjectVisibilityDecision.visibility_basis must contain only "
            "strings."
        )
    if any(item not in _VISIBILITY_BASIS_SET for item in basis):
        raise ValueError(
            "ProjectVisibilityDecision.visibility_basis contains an unknown "
            "basis."
        )
    if len(set(basis)) != len(basis):
        raise ValueError(
            "ProjectVisibilityDecision.visibility_basis cannot contain "
            "duplicates."
        )
    canonical = tuple(item for item in _VISIBILITY_BASIS_ORDER if item in basis)
    if basis != canonical:
        raise ValueError(
            "ProjectVisibilityDecision.visibility_basis must use canonical "
            "presentation order."
        )
    return basis


@dataclass(frozen=True)
class ProjectVisibilityDecision:
    """A fixed visibility result and every applicable factual basis."""

    evidence: ProjectVisibilityEvidence
    visible: bool
    visibility_basis: tuple[str, ...]

    def __post_init__(self) -> None:
        if type(self.evidence) is not ProjectVisibilityEvidence:
            raise TypeError(
                "ProjectVisibilityDecision.evidence must be "
                "ProjectVisibilityEvidence."
            )
        if type(self.visible) is not bool:
            raise TypeError("ProjectVisibilityDecision.visible must be a bool.")
        visibility_basis = _require_basis(self.visibility_basis)
        expected_basis = _derive_visibility_basis(self.evidence)
        if visibility_basis != expected_basis:
            raise ValueError(
                "ProjectVisibilityDecision.visibility_basis must exactly "
                "reflect its evidence."
            )
        if self.visible != bool(visibility_basis):
            raise ValueError(
                "ProjectVisibilityDecision.visible must equal whether a "
                "visibility basis exists."
            )
        object.__setattr__(self, "visibility_basis", visibility_basis)


def evaluate_project_visibility(
    evidence: ProjectVisibilityEvidence,
) -> ProjectVisibilityDecision:
    """Evaluate the single fixed P11.4G visibility policy."""

    if type(evidence) is not ProjectVisibilityEvidence:
        raise TypeError(
            "evaluate_project_visibility.evidence must be "
            "ProjectVisibilityEvidence."
        )
    visibility_basis = _derive_visibility_basis(evidence)
    return ProjectVisibilityDecision(
        evidence=evidence,
        visible=bool(visibility_basis),
        visibility_basis=visibility_basis,
    )


def filter_project_visible_candidates(
    index: ProjectResolutionCandidateIndex,
    query: ProjectResolutionQuery,
    context: ProjectResolutionContext,
) -> tuple[ProjectResolutionCandidate, ...]:
    """Retain every query-matching candidate visible under the fixed policy."""

    if type(index) is not ProjectResolutionCandidateIndex:
        raise TypeError(
            "filter_project_visible_candidates.index must be "
            "ProjectResolutionCandidateIndex."
        )
    if type(query) is not ProjectResolutionQuery:
        raise TypeError(
            "filter_project_visible_candidates.query must be "
            "ProjectResolutionQuery."
        )
    if type(context) is not ProjectResolutionContext:
        raise TypeError(
            "filter_project_visible_candidates.context must be "
            "ProjectResolutionContext."
        )
    evidence_records = collect_project_visibility_evidence(index, query, context)
    return tuple(
        evidence.candidate
        for evidence in evidence_records
        if evaluate_project_visibility(evidence).visible
    )


__all__ = (
    "ProjectVisibilityDecision",
    "evaluate_project_visibility",
    "filter_project_visible_candidates",
)
