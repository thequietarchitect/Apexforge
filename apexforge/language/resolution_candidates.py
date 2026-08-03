"""Immutable passive resolver-candidate metadata for successful projects."""

from __future__ import annotations

from dataclasses import dataclass
import re

from language.declarations import ProjectDeclarationOwner
from language.identities import ProjectDeclaredIdentity


_DECLARATION_KINDS = frozenset(("directive", "function"))
_NAME_PATTERN = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")


def _require_kind(value: object) -> str:
    if not isinstance(value, str):
        raise TypeError("Declaration kind must be a string.")
    if value not in _DECLARATION_KINDS:
        raise ValueError("Declaration kind must be 'directive' or 'function'.")
    return value


def _require_query(value: object, *, label: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{label} must be a string.")
    if not value.strip():
        raise ValueError(f"{label} cannot be blank.")
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
class ProjectQualification:
    """Structured declaration qualification without a source-string form."""

    kind: str
    module_segments: tuple[str, ...]
    declaration_path: tuple[str, ...]
    legacy: bool

    def __post_init__(self) -> None:
        kind = _require_kind(self.kind)
        module_segments = _require_segments(
            self.module_segments,
            label="ProjectQualification.module_segments",
        )
        declaration_path = _require_segments(
            self.declaration_path,
            label="ProjectQualification.declaration_path",
        )
        if len(declaration_path) != 1:
            raise ValueError(
                "ProjectQualification.declaration_path must contain exactly one "
                "segment in P11.4D."
            )
        if not isinstance(self.legacy, bool):
            raise TypeError("ProjectQualification.legacy must be a bool.")
        if self.legacy and module_segments:
            raise ValueError(
                "A legacy ProjectQualification must have no module segments."
            )
        if not self.legacy and not module_segments:
            raise ValueError(
                "A module-owned ProjectQualification requires module segments."
            )
        object.__setattr__(self, "kind", kind)
        object.__setattr__(self, "module_segments", module_segments)
        object.__setattr__(self, "declaration_path", declaration_path)


@dataclass(frozen=True)
class ProjectResolutionCandidate:
    """One consistent passive identity, owner, and qualification fact."""

    identity: ProjectDeclaredIdentity
    owner: ProjectDeclarationOwner
    qualification: ProjectQualification

    def __post_init__(self) -> None:
        if not isinstance(self.identity, ProjectDeclaredIdentity):
            raise TypeError(
                "ProjectResolutionCandidate.identity must be "
                "ProjectDeclaredIdentity."
            )
        if not isinstance(self.owner, ProjectDeclarationOwner):
            raise TypeError(
                "ProjectResolutionCandidate.owner must be ProjectDeclarationOwner."
            )
        if not isinstance(self.qualification, ProjectQualification):
            raise TypeError(
                "ProjectResolutionCandidate.qualification must be "
                "ProjectQualification."
            )

        identity = self.identity
        owner = self.owner
        if identity.kind != owner.kind:
            raise ValueError("Candidate identity and owner kinds must agree.")
        if identity.current_air_id != owner.air_id:
            raise ValueError("Candidate identity and owner AIR IDs must agree.")
        if identity.source_name != owner.source_name:
            raise ValueError("Candidate identity and owner source names must agree.")
        if identity.module_name != owner.module_name:
            raise ValueError("Candidate identity and owner module names must agree.")
        if identity.span != owner.span:
            raise ValueError("Candidate identity and owner declaration spans must agree.")

        expected_qualification = ProjectQualification(
            kind=identity.kind,
            module_segments=(
                ()
                if owner.module_name is None
                else tuple(owner.module_name.split("."))
            ),
            declaration_path=(identity.declared_name,),
            legacy=owner.module_name is None,
        )
        if self.qualification != expected_qualification:
            raise ValueError(
                "Candidate qualification must exactly reflect its identity and owner."
            )


def _candidate_order(
    candidate: ProjectResolutionCandidate,
) -> tuple[object, ...]:
    qualification = candidate.qualification
    identity = candidate.identity
    return (
        qualification.kind,
        not qualification.legacy,
        qualification.module_segments,
        qualification.declaration_path,
        identity.source_name.casefold(),
        identity.source_name,
        identity.span.start.offset,
        identity.span.end.offset,
        identity.current_air_id,
    )


@dataclass(frozen=True)
class ProjectResolutionCandidateIndex:
    """Canonical tuple of passive candidates with factual filtering only."""

    candidates: tuple[ProjectResolutionCandidate, ...] = ()

    def __post_init__(self) -> None:
        candidates = tuple(self.candidates)
        if any(
            not isinstance(candidate, ProjectResolutionCandidate)
            for candidate in candidates
        ):
            raise TypeError(
                "ProjectResolutionCandidateIndex.candidates must contain "
                "ProjectResolutionCandidate values."
            )
        object.__setattr__(
            self,
            "candidates",
            tuple(sorted(candidates, key=_candidate_order)),
        )

    def find_all(
        self,
        kind: str,
        declared_name: str,
    ) -> tuple[ProjectResolutionCandidate, ...]:
        selected_kind = _require_kind(kind)
        selected_name = _require_query(declared_name, label="Declared name")
        return tuple(
            candidate
            for candidate in self.candidates
            if candidate.identity.kind == selected_kind
            and candidate.identity.declared_name == selected_name
        )

    def find_current_air_id(
        self,
        current_air_id: str,
    ) -> tuple[ProjectResolutionCandidate, ...]:
        selected = _require_query(current_air_id, label="Current AIR ID")
        return tuple(
            candidate
            for candidate in self.candidates
            if candidate.identity.current_air_id == selected
        )

    def find_qualification(
        self,
        qualification: ProjectQualification,
    ) -> tuple[ProjectResolutionCandidate, ...]:
        if not isinstance(qualification, ProjectQualification):
            raise TypeError(
                "Qualification query must be ProjectQualification."
            )
        return tuple(
            candidate
            for candidate in self.candidates
            if candidate.qualification == qualification
        )


__all__ = (
    "ProjectQualification",
    "ProjectResolutionCandidate",
    "ProjectResolutionCandidateIndex",
)
