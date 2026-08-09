"""Immutable narrative execution state and result contracts.

P11.6B defines data contracts only. It does not select scenes, evaluate
conditions, apply consequences, perform transitions, emit runtime events,
generate execution diagnostics, or decide termination.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Optional

from language.narrative_model import NarrativeIdentity, NarrativeStateFact


__all__ = (
    "NarrativeChoiceEvidence",
    "NarrativeExecutionDiagnostic",
    "NarrativeExecutionResult",
    "NarrativeExecutionState",
    "NarrativeExecutionTraceEvent",
    "NarrativeExecutionTraceFact",
    "NarrativeTermination",
)


_DIAGNOSTIC_SEVERITIES = frozenset(("error", "warning", "info"))
_TERMINATION_STATUSES = frozenset(("active", "terminated"))


def _require_trimmed_string(value: object, field_name: str) -> str:
    if type(value) is not str:
        raise TypeError(f"{field_name} must be an exact str.")
    if not value or value != value.strip():
        raise ValueError(f"{field_name} must be a non-empty trimmed string.")
    return value


def _require_optional_trimmed_string(
    value: object,
    field_name: str,
) -> Optional[str]:
    if value is None:
        return None
    return _require_trimmed_string(value, field_name)


def _require_identity(
    value: object,
    field_name: str,
    expected_kind: Optional[str] = None,
) -> NarrativeIdentity:
    if type(value) is not NarrativeIdentity:
        raise TypeError(f"{field_name} must be an exact NarrativeIdentity.")
    if expected_kind is not None and value.kind != expected_kind:
        raise ValueError(
            f"{field_name} must have narrative identity kind "
            f"{expected_kind!r}; received {value.kind!r}."
        )
    return value


def _fact_key(
    fact: NarrativeStateFact,
) -> tuple[str, tuple[str, ...], str, str]:
    return (
        fact.subject.kind,
        fact.subject.path,
        fact.name,
        fact.value,
    )


def _fact_slot_key(
    fact: NarrativeStateFact,
) -> tuple[str, tuple[str, ...], str]:
    return fact.subject.kind, fact.subject.path, fact.name


@dataclass(frozen=True)
class NarrativeChoiceEvidence:
    """Immutable evidence describing one selected narrative choice path."""

    choice: NarrativeIdentity
    source_scene: NarrativeIdentity
    path_index: int
    path_label: str
    destination: NarrativeIdentity

    def __post_init__(self) -> None:
        _require_identity(self.choice, "NarrativeChoiceEvidence.choice", "choice")
        _require_identity(
            self.source_scene,
            "NarrativeChoiceEvidence.source_scene",
            "scene",
        )
        if type(self.path_index) is not int:
            raise TypeError(
                "NarrativeChoiceEvidence.path_index must be an exact int."
            )
        if self.path_index < 0:
            raise ValueError(
                "NarrativeChoiceEvidence.path_index must be non-negative."
            )
        _require_trimmed_string(
            self.path_label,
            "NarrativeChoiceEvidence.path_label",
        )
        _require_identity(
            self.destination,
            "NarrativeChoiceEvidence.destination",
            "scene",
        )


@dataclass(frozen=True)
class NarrativeTermination:
    """Immutable termination state without P11.6E termination policy."""

    status: Literal["active", "terminated"] = "active"
    reason: Optional[str] = None

    def __post_init__(self) -> None:
        if type(self.status) is not str:
            raise TypeError("NarrativeTermination.status must be an exact str.")
        if self.status not in _TERMINATION_STATUSES:
            raise ValueError(
                "NarrativeTermination.status must be 'active' or 'terminated'."
            )
        _require_optional_trimmed_string(
            self.reason,
            "NarrativeTermination.reason",
        )
        if self.status == "active" and self.reason is not None:
            raise ValueError(
                "NarrativeTermination.reason must be None while status is active."
            )

    @property
    def is_terminated(self) -> bool:
        return self.status == "terminated"


@dataclass(frozen=True, order=True)
class NarrativeExecutionTraceFact:
    """One immutable string fact attached to narrative trace evidence."""

    key: str
    value: str

    def __post_init__(self) -> None:
        _require_trimmed_string(self.key, "NarrativeExecutionTraceFact.key")
        _require_trimmed_string(self.value, "NarrativeExecutionTraceFact.value")


@dataclass(frozen=True)
class NarrativeExecutionTraceEvent:
    """One ordered narrative trace record; production semantics are P11.6E."""

    kind: str
    message: str
    facts: tuple[NarrativeExecutionTraceFact, ...] = ()

    def __post_init__(self) -> None:
        _require_trimmed_string(
            self.kind,
            "NarrativeExecutionTraceEvent.kind",
        )
        _require_trimmed_string(
            self.message,
            "NarrativeExecutionTraceEvent.message",
        )
        if type(self.facts) is not tuple:
            raise TypeError(
                "NarrativeExecutionTraceEvent.facts must be an exact tuple."
            )
        for fact in self.facts:
            if type(fact) is not NarrativeExecutionTraceFact:
                raise TypeError(
                    "NarrativeExecutionTraceEvent.facts must contain exact "
                    "NarrativeExecutionTraceFact objects."
                )


@dataclass(frozen=True)
class NarrativeExecutionDiagnostic:
    """Immutable narrative diagnostic record; code semantics are P11.6E."""

    severity: Literal["error", "warning", "info"]
    code: str
    message: str
    subject: Optional[NarrativeIdentity] = None

    def __post_init__(self) -> None:
        if type(self.severity) is not str:
            raise TypeError(
                "NarrativeExecutionDiagnostic.severity must be an exact str."
            )
        if self.severity not in _DIAGNOSTIC_SEVERITIES:
            raise ValueError(
                "NarrativeExecutionDiagnostic.severity must be "
                "'error', 'warning', or 'info'."
            )
        _require_trimmed_string(self.code, "NarrativeExecutionDiagnostic.code")
        _require_trimmed_string(
            self.message,
            "NarrativeExecutionDiagnostic.message",
        )
        if self.subject is not None:
            _require_identity(
                self.subject,
                "NarrativeExecutionDiagnostic.subject",
            )

    @property
    def is_error(self) -> bool:
        return self.severity == "error"


@dataclass(frozen=True)
class NarrativeExecutionState:
    """One immutable, deterministic narrative execution state snapshot."""

    story: NarrativeIdentity
    current_scene: NarrativeIdentity
    facts: tuple[NarrativeStateFact, ...] = ()
    progression: tuple[NarrativeIdentity, ...] = ()
    choice_history: tuple[NarrativeChoiceEvidence, ...] = ()
    termination: NarrativeTermination = field(
        default_factory=NarrativeTermination
    )

    def __post_init__(self) -> None:
        _require_identity(
            self.story,
            "NarrativeExecutionState.story",
            "story",
        )
        _require_identity(
            self.current_scene,
            "NarrativeExecutionState.current_scene",
            "scene",
        )

        if type(self.facts) is not tuple:
            raise TypeError(
                "NarrativeExecutionState.facts must be an exact tuple."
            )
        normalized_facts = []
        seen_fact_slots = set()
        for fact in self.facts:
            if type(fact) is not NarrativeStateFact:
                raise TypeError(
                    "NarrativeExecutionState.facts must contain exact "
                    "NarrativeStateFact objects."
                )
            slot = _fact_slot_key(fact)
            if slot in seen_fact_slots:
                raise ValueError(
                    "duplicate narrative execution fact slot: "
                    f"{fact.subject.kind}:{'/'.join(fact.subject.path)}:"
                    f"{fact.name}"
                )
            seen_fact_slots.add(slot)
            normalized_facts.append(fact)
        object.__setattr__(
            self,
            "facts",
            tuple(sorted(normalized_facts, key=_fact_key)),
        )

        if type(self.progression) is not tuple:
            raise TypeError(
                "NarrativeExecutionState.progression must be an exact tuple."
            )
        progression = self.progression
        if not progression:
            progression = (self.current_scene,)
        for scene in progression:
            _require_identity(
                scene,
                "NarrativeExecutionState.progression item",
                "scene",
            )
        if progression[-1] != self.current_scene:
            raise ValueError(
                "NarrativeExecutionState.progression must end at current_scene."
            )
        object.__setattr__(self, "progression", progression)

        if type(self.choice_history) is not tuple:
            raise TypeError(
                "NarrativeExecutionState.choice_history must be an exact tuple."
            )
        for evidence in self.choice_history:
            if type(evidence) is not NarrativeChoiceEvidence:
                raise TypeError(
                    "NarrativeExecutionState.choice_history must contain exact "
                    "NarrativeChoiceEvidence objects."
                )

        if type(self.termination) is not NarrativeTermination:
            raise TypeError(
                "NarrativeExecutionState.termination must be an exact "
                "NarrativeTermination."
            )


@dataclass(frozen=True)
class NarrativeExecutionResult:
    """Immutable products of one future narrative execution."""

    initial_state: NarrativeExecutionState
    final_state: NarrativeExecutionState
    trace: tuple[NarrativeExecutionTraceEvent, ...] = ()
    diagnostics: tuple[NarrativeExecutionDiagnostic, ...] = ()
    choice_evidence: tuple[NarrativeChoiceEvidence, ...] = ()

    def __post_init__(self) -> None:
        if type(self.initial_state) is not NarrativeExecutionState:
            raise TypeError(
                "NarrativeExecutionResult.initial_state must be an exact "
                "NarrativeExecutionState."
            )
        if type(self.final_state) is not NarrativeExecutionState:
            raise TypeError(
                "NarrativeExecutionResult.final_state must be an exact "
                "NarrativeExecutionState."
            )
        if self.initial_state.story != self.final_state.story:
            raise ValueError(
                "NarrativeExecutionResult initial and final states must "
                "belong to the same story."
            )

        if type(self.trace) is not tuple:
            raise TypeError(
                "NarrativeExecutionResult.trace must be an exact tuple."
            )
        for event in self.trace:
            if type(event) is not NarrativeExecutionTraceEvent:
                raise TypeError(
                    "NarrativeExecutionResult.trace must contain exact "
                    "NarrativeExecutionTraceEvent objects."
                )

        if type(self.diagnostics) is not tuple:
            raise TypeError(
                "NarrativeExecutionResult.diagnostics must be an exact tuple."
            )
        for diagnostic in self.diagnostics:
            if type(diagnostic) is not NarrativeExecutionDiagnostic:
                raise TypeError(
                    "NarrativeExecutionResult.diagnostics must contain exact "
                    "NarrativeExecutionDiagnostic objects."
                )

        if type(self.choice_evidence) is not tuple:
            raise TypeError(
                "NarrativeExecutionResult.choice_evidence must be an exact tuple."
            )
        for evidence in self.choice_evidence:
            if type(evidence) is not NarrativeChoiceEvidence:
                raise TypeError(
                    "NarrativeExecutionResult.choice_evidence must contain exact "
                    "NarrativeChoiceEvidence objects."
                )

    @property
    def termination(self) -> NarrativeTermination:
        return self.final_state.termination

    @property
    def ok(self) -> bool:
        return not any(diagnostic.is_error for diagnostic in self.diagnostics)
