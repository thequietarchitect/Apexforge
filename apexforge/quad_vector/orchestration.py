"""Canonical end-to-end orchestration for the P11.7 Quad-Vector Engine.

P11.7G composes the already-frozen registry/binding, execution, field-matrix,
synchronization, and resultant-resolution layers. It performs no discovery,
host integration, CLI routing, implementation loading, or authoring work.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Tuple

from .execution import (
    QuadVectorExecutionContext,
    QuadVectorExecutionRecord,
    execute_quad_vector_bindings,
)
from .field_matrix import QuadVectorFieldMatrix, generate_quad_vector_field_matrix
from .model import (
    QuadVectorContribution,
    QuadVectorInput,
    QuadVectorResourceBudget,
    ResultantVector,
)
from .module import QuadVectorModuleKind
from .registry import QuadVectorModuleBinding
from .synchronizer import (
    QuadVectorSynchronization,
    synchronize_quad_vector_field_matrix,
)
from .resolver import resolve_quad_vector_synchronization


@dataclass(frozen=True)
class QuadVectorOrchestrationResult:
    """Immutable snapshot of one complete canonical Quad-Vector pipeline."""

    execution_records: Tuple[QuadVectorExecutionRecord, ...]
    field_matrix: QuadVectorFieldMatrix
    synchronization: QuadVectorSynchronization
    resultant: ResultantVector

    def __post_init__(self) -> None:
        if type(self.execution_records) is not tuple:
            raise TypeError("execution_records must be a tuple")
        if any(
            type(record) is not QuadVectorExecutionRecord
            for record in self.execution_records
        ):
            raise TypeError(
                "execution_records must contain exact QuadVectorExecutionRecord values"
            )
        if type(self.field_matrix) is not QuadVectorFieldMatrix:
            raise TypeError("field_matrix must be an exact QuadVectorFieldMatrix")
        if type(self.synchronization) is not QuadVectorSynchronization:
            raise TypeError(
                "synchronization must be an exact QuadVectorSynchronization"
            )
        if type(self.resultant) is not ResultantVector:
            raise TypeError("resultant must be an exact ResultantVector")


def _require_bindings(
    bindings: Tuple[QuadVectorModuleBinding, ...],
) -> None:
    if type(bindings) is not tuple:
        raise TypeError("bindings must be a tuple")
    if any(type(binding) is not QuadVectorModuleBinding for binding in bindings):
        raise TypeError(
            "bindings must contain exact QuadVectorModuleBinding values"
        )


def _extract_vector_contributions(
    records: Tuple[QuadVectorExecutionRecord, ...],
) -> Tuple[QuadVectorContribution, ...]:
    contributions = []

    for record in records:
        if record.spec.kind is not QuadVectorModuleKind.VECTOR_OPERATOR:
            continue

        for name, value in record.outputs:
            if name not in record.spec.produced_outputs:
                raise ValueError(
                    "execution record contains output outside its declared contract"
                )

            if type(value) is not tuple:
                raise TypeError(
                    "VECTOR_OPERATOR output must be a tuple of QuadVectorContribution values"
                )

            for contribution in value:
                if type(contribution) is not QuadVectorContribution:
                    raise TypeError(
                        "VECTOR_OPERATOR output must contain exact "
                        "QuadVectorContribution values"
                    )
                if contribution.lane not in record.spec.eligible_vectors:
                    raise ValueError(
                        "VECTOR_OPERATOR emitted a contribution on an ineligible vector lane"
                    )

                contributions.append(
                    QuadVectorContribution(
                        lane=contribution.lane,
                        magnitude=contribution.magnitude,
                        order=contribution.order,
                        provenance=record.provenance + contribution.provenance,
                    )
                )

    return tuple(contributions)


def orchestrate_quad_vector_engine(
    bindings: Tuple[QuadVectorModuleBinding, ...],
    *,
    implementations: Mapping[str, Any],
    context: QuadVectorExecutionContext,
    stimulus: QuadVectorInput,
    budget: QuadVectorResourceBudget,
) -> QuadVectorOrchestrationResult:
    """Run the canonical P11.7 execution-to-resultant pipeline."""

    _require_bindings(bindings)

    if type(context) is not QuadVectorExecutionContext:
        raise TypeError(
            "context must be an exact QuadVectorExecutionContext"
        )
    if type(stimulus) is not QuadVectorInput:
        raise TypeError("stimulus must be an exact QuadVectorInput")
    if type(budget) is not QuadVectorResourceBudget:
        raise TypeError("budget must be an exact QuadVectorResourceBudget")

    if context.inputs != stimulus.facts:
        raise ValueError(
            "execution context inputs must exactly match canonical stimulus facts"
        )

    if len(bindings) > budget.max_modules:
        raise ValueError(
            "orchestration module count exceeds canonical resource budget"
        )

    execution_records = execute_quad_vector_bindings(
        bindings,
        implementations=implementations,
        context=context,
    )

    contributions = _extract_vector_contributions(execution_records)

    field_matrix = generate_quad_vector_field_matrix(
        stimulus=stimulus,
        contributions=contributions,
        budget=budget,
    )
    synchronization = synchronize_quad_vector_field_matrix(field_matrix)
    resultant = resolve_quad_vector_synchronization(synchronization)

    return QuadVectorOrchestrationResult(
        execution_records=execution_records,
        field_matrix=field_matrix,
        synchronization=synchronization,
        resultant=resultant,
    )


__all__ = (
    "QuadVectorOrchestrationResult",
    "orchestrate_quad_vector_engine",
)
