"""Canonical integration adapters for the P11.7 Quad-Vector Engine.

P11.7H translates external ApexForge source envelopes into canonical
QuadVectorInput and QuadVectorExecutionContext snapshots and translates a
canonical ResultantVector back into an immutable integration response.
The adapter layer does not execute, orchestrate, discover, import, or load
engine modules.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Tuple

from .execution import QuadVectorExecutionContext
from .model import QuadVectorInput, ResultantVector


class QuadVectorIntegrationSource(Enum):
    """Canonical external source taxonomy."""

    AIR = "air"
    RUNTIME = "runtime"
    NARRATIVE = "narrative"
    TOOLING = "tooling"


def _require_text(value: Any, *, owner: str) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{owner} must be a non-empty string")
    return value


def _require_pairs(
    value: Any,
    *,
    owner: str,
) -> Tuple[Tuple[str, Any], ...]:
    if type(value) is not tuple:
        raise TypeError(f"{owner} must be a tuple")

    keys = []
    for item in value:
        if type(item) is not tuple or len(item) != 2:
            raise TypeError(
                f"{owner} must contain exact two-item tuples"
            )
        key = item[0]
        _require_text(key, owner=f"{owner} key")
        keys.append(key)

    if len(set(keys)) != len(keys):
        raise ValueError(f"{owner} must not contain duplicate keys")

    return value


def _require_authorities(value: Any) -> Tuple[str, ...]:
    if type(value) is not tuple:
        raise TypeError("authorities must be a tuple")
    for authority in value:
        _require_text(authority, owner="authority")
    if len(set(value)) != len(value):
        raise ValueError("authorities must not contain duplicates")
    return value


@dataclass(frozen=True)
class QuadVectorIntegrationRequest:
    """Immutable external request envelope for canonical adaptation."""

    source: QuadVectorIntegrationSource
    source_identity: str
    facts: Tuple[Tuple[str, Any], ...]
    authorities: Tuple[str, ...]
    max_invocations: int

    def __post_init__(self) -> None:
        if type(self.source) is not QuadVectorIntegrationSource:
            raise TypeError("source must be an exact QuadVectorIntegrationSource")
        _require_text(self.source_identity, owner="source_identity")
        _require_pairs(self.facts, owner="facts")
        _require_authorities(self.authorities)
        if type(self.max_invocations) is not int or self.max_invocations < 0:
            raise ValueError("max_invocations must be a non-negative int")


@dataclass(frozen=True)
class QuadVectorIntegrationInput:
    """Canonical input snapshot produced from an integration request."""

    source: QuadVectorIntegrationSource
    source_identity: str
    stimulus: QuadVectorInput
    context: QuadVectorExecutionContext

    def __post_init__(self) -> None:
        if type(self.source) is not QuadVectorIntegrationSource:
            raise TypeError("source must be an exact QuadVectorIntegrationSource")
        _require_text(self.source_identity, owner="source_identity")
        if type(self.stimulus) is not QuadVectorInput:
            raise TypeError("stimulus must be an exact QuadVectorInput")
        if type(self.context) is not QuadVectorExecutionContext:
            raise TypeError("context must be an exact QuadVectorExecutionContext")
        if self.stimulus.identity != self.source_identity:
            raise ValueError("stimulus identity must match source_identity")
        if self.context.inputs != self.stimulus.facts:
            raise ValueError("execution context inputs must match stimulus facts")


@dataclass(frozen=True)
class QuadVectorIntegrationResponse:
    """Immutable external response snapshot for a canonical resultant."""

    source: QuadVectorIntegrationSource
    source_identity: str
    resultant: ResultantVector
    payload: Tuple[Tuple[str, Any], ...]
    provenance: Tuple[str, ...]

    def __post_init__(self) -> None:
        if type(self.source) is not QuadVectorIntegrationSource:
            raise TypeError("source must be an exact QuadVectorIntegrationSource")
        _require_text(self.source_identity, owner="source_identity")
        if type(self.resultant) is not ResultantVector:
            raise TypeError("resultant must be an exact ResultantVector")
        _require_pairs(self.payload, owner="payload")
        if type(self.provenance) is not tuple:
            raise TypeError("provenance must be a tuple")
        if any(type(item) is not str or not item.strip() for item in self.provenance):
            raise ValueError("provenance entries must be non-empty strings")


def adapt_quad_vector_integration_request(
    request: QuadVectorIntegrationRequest,
) -> QuadVectorIntegrationInput:
    """Translate one validated external request into canonical engine inputs."""

    if type(request) is not QuadVectorIntegrationRequest:
        raise TypeError(
            "request must be an exact QuadVectorIntegrationRequest"
        )

    stimulus = QuadVectorInput(
        identity=request.source_identity,
        facts=request.facts,
    )
    context = QuadVectorExecutionContext(
        authorities=request.authorities,
        inputs=request.facts,
        max_invocations=request.max_invocations,
    )
    return QuadVectorIntegrationInput(
        source=request.source,
        source_identity=request.source_identity,
        stimulus=stimulus,
        context=context,
    )


def adapt_quad_vector_integration_result(
    integration_input: QuadVectorIntegrationInput,
    resultant: ResultantVector,
) -> QuadVectorIntegrationResponse:
    """Translate one canonical resultant into an immutable external response."""

    if type(integration_input) is not QuadVectorIntegrationInput:
        raise TypeError(
            "integration_input must be an exact QuadVectorIntegrationInput"
        )
    if type(resultant) is not ResultantVector:
        raise TypeError("resultant must be an exact ResultantVector")

    return QuadVectorIntegrationResponse(
        source=integration_input.source,
        source_identity=integration_input.source_identity,
        resultant=resultant,
        payload=(("x", resultant.x), ("y", resultant.y)),
        provenance=resultant.provenance,
    )


__all__ = (
    "QuadVectorIntegrationInput",
    "QuadVectorIntegrationRequest",
    "QuadVectorIntegrationResponse",
    "QuadVectorIntegrationSource",
    "adapt_quad_vector_integration_request",
    "adapt_quad_vector_integration_result",
)
