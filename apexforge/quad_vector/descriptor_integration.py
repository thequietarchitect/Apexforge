"""Canonical descriptor integration orchestration for the P11.7 Quad-Vector Engine.

P11.7T composes an already validated descriptor binding with the frozen P11.7S
descriptor-engine orchestration adapter and the frozen P11.7H integration result
adapter. It performs no discovery, parsing, loading, dynamic importing, or Codex
mediated insertion.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .binding import QuadVectorDescriptorBinding
from .descriptor_orchestration import (
    QuadVectorDescriptorOrchestration,
    orchestrate_quad_vector_descriptor_engine,
)
from .integration import (
    QuadVectorIntegrationInput,
    QuadVectorIntegrationResponse,
    adapt_quad_vector_integration_result,
)
from .model import QuadVectorResourceBudget


@dataclass(frozen=True)
class QuadVectorDescriptorIntegrationOrchestration:
    """Immutable snapshot of descriptor orchestration adapted for one integration input."""

    integration_input: QuadVectorIntegrationInput
    descriptor_orchestration: QuadVectorDescriptorOrchestration
    response: QuadVectorIntegrationResponse

    def __post_init__(self) -> None:
        if type(self.integration_input) is not QuadVectorIntegrationInput:
            raise TypeError(
                "integration_input must be an exact QuadVectorIntegrationInput"
            )
        if type(self.descriptor_orchestration) is not QuadVectorDescriptorOrchestration:
            raise TypeError(
                "descriptor_orchestration must be an exact "
                "QuadVectorDescriptorOrchestration"
            )
        if type(self.response) is not QuadVectorIntegrationResponse:
            raise TypeError(
                "response must be an exact QuadVectorIntegrationResponse"
            )

        resultant = self.descriptor_orchestration.orchestration.resultant
        if self.response.resultant is not resultant:
            raise ValueError(
                "integration response must preserve descriptor resultant object identity"
            )
        if self.response.source is not self.integration_input.source:
            raise ValueError(
                "integration response must preserve integration source identity"
            )
        if self.response.source_identity != self.integration_input.source_identity:
            raise ValueError(
                "integration response must preserve integration source identity text"
            )


def orchestrate_quad_vector_descriptor_integration(
    binding: QuadVectorDescriptorBinding,
    *,
    integration_input: QuadVectorIntegrationInput,
    implementations: Mapping[str, Any],
    budget: QuadVectorResourceBudget,
) -> QuadVectorDescriptorIntegrationOrchestration:
    """Run one descriptor-binding-to-integration-response orchestration pass."""

    if type(binding) is not QuadVectorDescriptorBinding:
        raise TypeError("binding must be an exact QuadVectorDescriptorBinding")
    if type(integration_input) is not QuadVectorIntegrationInput:
        raise TypeError(
            "integration_input must be an exact QuadVectorIntegrationInput"
        )
    if type(budget) is not QuadVectorResourceBudget:
        raise TypeError("budget must be an exact QuadVectorResourceBudget")

    descriptor_orchestration = orchestrate_quad_vector_descriptor_engine(
        binding,
        implementations=implementations,
        context=integration_input.context,
        stimulus=integration_input.stimulus,
        budget=budget,
    )
    response = adapt_quad_vector_integration_result(
        integration_input,
        descriptor_orchestration.orchestration.resultant,
    )

    return QuadVectorDescriptorIntegrationOrchestration(
        integration_input=integration_input,
        descriptor_orchestration=descriptor_orchestration,
        response=response,
    )


__all__ = (
    "QuadVectorDescriptorIntegrationOrchestration",
    "orchestrate_quad_vector_descriptor_integration",
)
