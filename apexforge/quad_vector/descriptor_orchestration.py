"""Canonical descriptor-binding to Quad-Vector engine orchestration adapter.

P11.7S bridges an already validated descriptor binding into the frozen P11.7G
engine orchestration path. It performs no discovery, parsing, loading, dynamic
importing, or Codex-mediated insertion, and it does not execute modules outside
the single frozen orchestration pass.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .binding import QuadVectorDescriptorBinding
from .execution import QuadVectorExecutionContext
from .model import QuadVectorInput, QuadVectorResourceBudget
from .orchestration import QuadVectorOrchestrationResult, orchestrate_quad_vector_engine


@dataclass(frozen=True)
class QuadVectorDescriptorOrchestration:
    """Immutable provenance snapshot for descriptor-driven engine orchestration."""

    binding: QuadVectorDescriptorBinding
    orchestration: QuadVectorOrchestrationResult

    def __post_init__(self) -> None:
        if type(self.binding) is not QuadVectorDescriptorBinding:
            raise TypeError("binding must be an exact QuadVectorDescriptorBinding")
        if type(self.orchestration) is not QuadVectorOrchestrationResult:
            raise TypeError(
                "orchestration must be an exact QuadVectorOrchestrationResult"
            )

        bound_specs = tuple(item.spec for item in self.binding.bindings)
        execution_specs = tuple(
            record.spec for record in self.orchestration.execution_records
        )
        if len(bound_specs) != len(execution_specs):
            raise ValueError(
                "descriptor orchestration must preserve one execution record per binding"
            )
        if any(
            bound_spec is not execution_spec
            for bound_spec, execution_spec in zip(bound_specs, execution_specs)
        ):
            raise ValueError(
                "descriptor orchestration must preserve bound canonical spec identity"
            )


def orchestrate_quad_vector_descriptor_engine(
    binding: QuadVectorDescriptorBinding,
    *,
    implementations: Mapping[str, Any],
    context: QuadVectorExecutionContext,
    stimulus: QuadVectorInput,
    budget: QuadVectorResourceBudget,
) -> QuadVectorDescriptorOrchestration:
    """Run one frozen descriptor-binding-to-resultant orchestration pass."""

    if type(binding) is not QuadVectorDescriptorBinding:
        raise TypeError("binding must be an exact QuadVectorDescriptorBinding")
    if type(context) is not QuadVectorExecutionContext:
        raise TypeError("context must be an exact QuadVectorExecutionContext")
    if type(stimulus) is not QuadVectorInput:
        raise TypeError("stimulus must be an exact QuadVectorInput")
    if type(budget) is not QuadVectorResourceBudget:
        raise TypeError("budget must be an exact QuadVectorResourceBudget")

    orchestration = orchestrate_quad_vector_engine(
        binding.bindings,
        implementations=implementations,
        context=context,
        stimulus=stimulus,
        budget=budget,
    )
    return QuadVectorDescriptorOrchestration(
        binding=binding,
        orchestration=orchestration,
    )


__all__ = (
    "QuadVectorDescriptorOrchestration",
    "orchestrate_quad_vector_descriptor_engine",
)
