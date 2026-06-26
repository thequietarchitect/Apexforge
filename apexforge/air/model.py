"""Passive AIR dataclasses.

No verification, execution, authority policy, causal selection, IO, or syntax
concerns belong here.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal,Union
from typing import TYPE_CHECKING, Tuple

from air.types import AIR_VERSION, Primitive, StateOperation, as_tuple, is_int

if TYPE_CHECKING:
    from runtime.diagnostics import Diagnostic


@dataclass(frozen=True)
class Fact:
    key: str
    value: Union[int,str, bool]


def sort_facts(items) -> Tuple[Fact, ...]:
    return tuple(sorted(as_tuple(items), key=lambda fact: (fact.key, type(fact.value).__name__, repr(fact.value))))


def facts(**items: Union[int,str, bool]) -> Tuple[Fact, ...]:
    return sort_facts(Fact(key, value) for key, value in items.items())


@dataclass(frozen=True, order=True)
class StateDefinition:
    id: str
    initial: int = 0
    value_type: str = "int"


@dataclass(frozen=True, order=True)
class StateAssignment:
    state: str
    operation: Literal["set_int", "add_int"]
    value: int


@dataclass(frozen=True, order=True)
class EventDefinition:
    id: str
    name: str


@dataclass(frozen=True)
class EventEmission:
    event: str
    facts: Tuple[Fact, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "facts", sort_facts(self.facts))


@dataclass(frozen=True)
class EventRecord:
    id: str
    event: str
    directive: str
    principal: str
    facts: Tuple[Fact, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "facts", sort_facts(self.facts))


@dataclass(frozen=True)
class AIRDirective:
    id: str
    name: str
    principal: str
    authority_checks: Tuple[str, ...]
    causal_decisions: Tuple[str, ...]
    order: int = 0

def validate_assignment_shape(assignment: "StateAssignment") -> bool:
    return (
        assignment.operation in ("set_int", "add_int")
        and type(assignment.value) is int
    )


def validate_state_definition_shape(state: "StateDefinition") -> bool:
    return state.value_type == "int" and type(state.initial) is int


@dataclass(frozen=True)
class AIRProgram:
    version: str
    principals: tuple["Principal", ...]
    states: tuple["StateDefinition", ...]
    events: tuple["EventDefinition", ...]
    authority_checks: tuple["AuthorityCheck", ...]
    causal_decisions: tuple["CausalDecision", ...]
    directives: tuple["AIRDirective", ...]


@dataclass(frozen=True, order=True)
class Principal:
    id: str
    display_name: str = ""


@dataclass(frozen=True, order=True)
class AuthorityCheck:
    id: str
    principal: str
    capability: str
    resource: str


@dataclass(frozen=True, order=True)
class CausalDecision:
    id: str
    cause: str
    paths: tuple
    policy: Literal["max_weight"] = "max_weight"

@dataclass(frozen=True)
class DirectiveInvocation:
    target: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "principals", tuple(sorted(as_tuple(self.principals), key=lambda item: item.id)))
        object.__setattr__(self, "states", tuple(sorted(as_tuple(self.states), key=lambda item: item.id)))
        object.__setattr__(self, "events", tuple(sorted(as_tuple(self.events), key=lambda item: item.id)))
        object.__setattr__(self, "authority_checks", tuple(sorted(as_tuple(self.authority_checks), key=lambda item: item.id)))
        object.__setattr__(self, "causal_decisions", tuple(sorted(as_tuple(self.causal_decisions), key=lambda item: item.id)))
        object.__setattr__(
            self,
            "directives",
            tuple(sorted(as_tuple(self.directives), key=lambda directive: (directive.order, directive.id))),
        )


@dataclass(frozen=True)
class VerifiedAIRProgram:
    program: AIRProgram


@dataclass(frozen=True)
class VerificationResult:
    program: AIRProgram
    diagnostics: Tuple["Diagnostic", ...]

    @property
    def ok(self) -> bool:
        return not any(diagnostic.is_error for diagnostic in self.diagnostics)

    def require_verified(self) -> VerifiedAIRProgram:
        if not self.ok:
            rendered = "\n".join(f"{diagnostic.code}: {diagnostic.message}" for diagnostic in self.diagnostics)
            raise ValueError(f"AIR verification failed:\n{rendered}")
        return VerifiedAIRProgram(self.program)


def validate_state_definition_shape(state: StateDefinition) -> bool:
    return state.value_type == "int" and is_int(state.initial)


def validate_assignment_shape(assignment: StateAssignment) -> bool:
    return assignment.operation in ("set_int", "add_int") and is_int(assignment.value)
"""Causal AIR model objects."""


from dataclasses import dataclass
from typing import Literal, Tuple

from air.model import EventEmission, StateAssignment

@dataclass(frozen=True)
class DirectiveInvocation:
    target: str


@dataclass(frozen=True)
class CausalPath:
    id: str
    weight: int
    assignments: tuple
    emits: tuple
    invocations: tuple = ()
    effects: tuple = ()
    rationale: str = ""


@dataclass(frozen=True, order=True)
class CausalDecision:
    id: str
    cause: str
    paths: Tuple[CausalPath, ...]
    policy: Literal["max_weight"] = "max_weight"