"""Canonical descriptor execution adapter for the P11.7 Quad-Vector Engine.

P11.7Q advances one exact descriptor binding through the existing deterministic
P11.7F execution engine. It preserves binding provenance and does not load or
import module implementations.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Tuple

from .binding import QuadVectorDescriptorBinding
from .execution import (
    QuadVectorExecutionContext,
    QuadVectorExecutionRecord,
    execute_quad_vector_bindings,
)


@dataclass(frozen=True)
class QuadVectorDescriptorExecution:
    """Immutable provenance-bearing result of canonical descriptor execution."""

    binding: QuadVectorDescriptorBinding
    records: Tuple[QuadVectorExecutionRecord, ...]

    def __post_init__(self) -> None:
        if type(self.binding) is not QuadVectorDescriptorBinding:
            raise TypeError(
                "binding must be an exact QuadVectorDescriptorBinding"
            )
        if type(self.records) is not tuple:
            raise TypeError("records must be an exact tuple")
        if any(type(item) is not QuadVectorExecutionRecord for item in self.records):
            raise TypeError(
                "records must contain exact QuadVectorExecutionRecord values"
            )

        bound_specs = tuple(item.spec for item in self.binding.bindings)
        record_specs = tuple(item.spec for item in self.records)
        if len(record_specs) != len(bound_specs):
            raise ValueError(
                "execution records must contain every bound canonical module exactly once"
            )
        if any(
            record_spec is not bound_spec
            for record_spec, bound_spec in zip(record_specs, bound_specs)
        ):
            raise ValueError(
                "execution records must preserve dependency-order canonical spec identity"
            )


def execute_quad_vector_descriptors(
    binding: QuadVectorDescriptorBinding,
    *,
    implementations: Mapping[str, Any],
    context: QuadVectorExecutionContext,
) -> QuadVectorDescriptorExecution:
    """Execute one descriptor binding through the existing P11.7F executor."""

    if type(binding) is not QuadVectorDescriptorBinding:
        raise TypeError("binding must be an exact QuadVectorDescriptorBinding")
    if type(context) is not QuadVectorExecutionContext:
        raise TypeError("context must be an exact QuadVectorExecutionContext")

    records = execute_quad_vector_bindings(
        binding.bindings,
        implementations=implementations,
        context=context,
    )
    if type(records) is not tuple:
        raise TypeError("execution engine must return an exact tuple")

    return QuadVectorDescriptorExecution(
        binding=binding,
        records=records,
    )


__all__ = (
    "QuadVectorDescriptorExecution",
    "execute_quad_vector_descriptors",
)
