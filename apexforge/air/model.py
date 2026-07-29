"""Passive AIR dataclasses.

No verification, execution, authority policy, causal selection, IO, or syntax
concerns belong here.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional, Tuple, TYPE_CHECKING, Union

from air.expressions import AIRExpression
from air.types import as_tuple, is_int
from authority.model import AuthorityCheck, AuthorityGrant, Principal


FactValue = Union[
    str,
    int,
    bool,
    AIRExpression,
]


if TYPE_CHECKING:
    from runtime.diagnostics import Diagnostic


@dataclass(frozen=True)
class Fact:
    key: str
    value: FactValue


def sort_facts(
    items,
) -> Tuple[Fact, ...]:
    return tuple(
        sorted(
            as_tuple(items),
            key=lambda fact: (
                fact.key,
                type(fact.value).__name__,
                repr(fact.value),
            ),
        )
    )


def facts(
    **values: FactValue,
) -> tuple[Fact, ...]:
    return tuple(
        Fact(
            key=name,
            value=value,
        )
        for name, value in values.items()
    )


@dataclass(frozen=True, order=True)
class StateDefinition:
    id: str
    initial: AIRExpression = 0
    value_type: str = "AIRExpression"


@dataclass(frozen=True, order=True)
class StateAssignment:
    state: str
    operation: Literal[
        "set_int",
        "add_int",
    ]
    value: AIRExpression


@dataclass(frozen=True, order=True)
class EventDefinition:
    id: str
    name: str


@dataclass(frozen=True)
class EventEmission:
    event: str
    facts: Tuple[Fact, ...] = ()

    def __post_init__(
        self,
    ) -> None:
        object.__setattr__(
            self,
            "facts",
            sort_facts(self.facts),
        )


@dataclass(frozen=True)
class EventRecord:
    id: str
    event: str
    directive: str
    principal: str
    facts: Tuple[Fact, ...] = ()

    def __post_init__(
        self,
    ) -> None:
        object.__setattr__(
            self,
            "facts",
            sort_facts(self.facts),
        )


@dataclass(frozen=True)
class AIRDirective:
    id: str
    name: str
    principal: str
    authority_checks: Tuple[str, ...]
    causal_decisions: Tuple[str, ...]
    order: AIRExpression = 0


@dataclass(frozen=True)
class DirectiveRequirement:
    capability: str
    principal: Optional[str] = None


@dataclass(frozen=True)
class AIRProgram:
    version: str
    states: tuple[StateDefinition, ...]
    events: tuple[EventDefinition, ...]
    authority_checks: tuple[AuthorityCheck, ...]
    causal_decisions: tuple[CausalDecision, ...]
    directives: tuple[AIRDirective, ...]
    requirements: tuple[DirectiveRequirement, ...]
    authorities: tuple[DirectiveAuthority, ...] = ()
    principals: tuple[Principal, ...] = ()
    roles: tuple[AIRRole, ...] = ()


@dataclass(frozen=True)
class VerifiedAIRProgram:
    program: AIRProgram


@dataclass(frozen=True)
class VerificationResult:
    program: AIRProgram
    diagnostics: Tuple["Diagnostic", ...]

    @property
    def ok(
        self,
    ) -> bool:
        return not any(
            diagnostic.is_error
            for diagnostic in self.diagnostics
        )

    def require_verified(
        self,
    ) -> VerifiedAIRProgram:
        if not self.ok:
            rendered = "\n".join(
                f"{diagnostic.code}: "
                f"{diagnostic.message}"
                for diagnostic in self.diagnostics
            )

            raise ValueError(
                "AIR verification failed:\n"
                f"{rendered}"
            )

        return VerifiedAIRProgram(
            self.program
        )


def validate_state_definition_shape(
    state: StateDefinition,
) -> bool:
    return (
        state.value_type == "int"
        and is_int(state.initial)
    )


def validate_assignment_shape(
    assignment: StateAssignment,
) -> bool:
    return (
        assignment.operation
        in (
            "set_int",
            "add_int",
        )
        and is_int(assignment.value)
    )


@dataclass(frozen=True)
class DirectiveAuthority:
    name: str


@dataclass(frozen=True)
class PrincipalAuthorityNode:
    name: str


@dataclass(frozen=True)
class PrincipalNode:
    name: str
    authorities: tuple[
        PrincipalAuthorityNode,
        ...,
    ]


@dataclass(frozen=True)
class PrincipalAuthority:
    name: str


@dataclass(frozen=True)
class PrincipalRole:
    name: str


@dataclass(frozen=True)
class AIRPrincipal:
    name: str
    authorities: tuple[
        PrincipalAuthority,
        ...,
    ]
    roles: tuple[
        PrincipalRole,
        ...,
    ] = ()


@dataclass(frozen=True)
class AIRRoleAuthority:
    name: str


@dataclass(frozen=True)
class AIRRole:
    name: str
    authorities: tuple[
        AIRRoleAuthority,
        ...,
    ]


@dataclass(frozen=True)
class AIRWhenAction:
    condition: AIRExpression
    actions: tuple[object, ...]
    otherwise_actions: tuple[
        object,
        ...,
    ] = ()


# Backward-compatible re-exports.
#
# These classes are defined only in causality.model. Importing them here keeps
# older ``from air.model import ...`` call sites working without creating a
# second Python class identity.
from causality.model import (  # noqa: E402
    CausalDecision,
    CausalPath,
    DirectiveInvocation,
)