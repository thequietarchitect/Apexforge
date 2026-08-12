"""Canonical descriptor lifecycle orchestration for the P11.7 Quad-Vector Engine.

P11.7R composes the frozen Discover -> Parse -> Validate -> Canonicalize ->
Register -> Bind -> Execute stages. Descriptor text and implementation
providers remain caller-supplied; this layer performs no file loading,
dynamic importing, or Codex-mediated runtime insertion.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Tuple

from .binding import QuadVectorDescriptorBinding, bind_quad_vector_descriptors
from .canonicalization import (
    QuadVectorCanonicalDescriptor,
    canonicalize_quad_vector_descriptor,
)
from .descriptor_execution import (
    QuadVectorDescriptorExecution,
    execute_quad_vector_descriptors,
)
from .discovery import (
    QuadVectorDiscoveryCandidate,
    QuadVectorDiscoveryInventory,
    discover_quad_vector_modules,
)
from .execution import QuadVectorExecutionContext
from .model import QuadVectorResourceBudget
from .parsing import QuadVectorParsedDescriptor, parse_quad_vector_descriptor
from .registration import (
    QuadVectorDescriptorRegistration,
    register_quad_vector_descriptors,
)
from .validation import (
    QuadVectorValidatedDescriptor,
    validate_quad_vector_descriptor,
)


@dataclass(frozen=True)
class QuadVectorDescriptorLifecycle:
    """Immutable snapshot of every canonical descriptor lifecycle stage."""

    inventory: QuadVectorDiscoveryInventory
    parsed: Tuple[QuadVectorParsedDescriptor, ...]
    validated: Tuple[QuadVectorValidatedDescriptor, ...]
    canonicalized: Tuple[QuadVectorCanonicalDescriptor, ...]
    registration: QuadVectorDescriptorRegistration
    binding: QuadVectorDescriptorBinding
    execution: QuadVectorDescriptorExecution

    def __post_init__(self) -> None:
        if type(self.inventory) is not QuadVectorDiscoveryInventory:
            raise TypeError("inventory must be an exact QuadVectorDiscoveryInventory")
        if type(self.parsed) is not tuple or any(
            type(item) is not QuadVectorParsedDescriptor for item in self.parsed
        ):
            raise TypeError("parsed must contain exact QuadVectorParsedDescriptor values")
        if type(self.validated) is not tuple or any(
            type(item) is not QuadVectorValidatedDescriptor for item in self.validated
        ):
            raise TypeError("validated must contain exact QuadVectorValidatedDescriptor values")
        if type(self.canonicalized) is not tuple or any(
            type(item) is not QuadVectorCanonicalDescriptor for item in self.canonicalized
        ):
            raise TypeError("canonicalized must contain exact QuadVectorCanonicalDescriptor values")
        if type(self.registration) is not QuadVectorDescriptorRegistration:
            raise TypeError("registration must be an exact QuadVectorDescriptorRegistration")
        if type(self.binding) is not QuadVectorDescriptorBinding:
            raise TypeError("binding must be an exact QuadVectorDescriptorBinding")
        if type(self.execution) is not QuadVectorDescriptorExecution:
            raise TypeError("execution must be an exact QuadVectorDescriptorExecution")

        if tuple(item.candidate for item in self.parsed) != self.inventory.candidates:
            raise ValueError("parse stage must preserve discovered candidate order and identity")
        if tuple(item.parsed for item in self.validated) != self.parsed:
            raise ValueError("validation stage must preserve parsed descriptor order and identity")
        if tuple(item.validated for item in self.canonicalized) != self.validated:
            raise ValueError(
                "canonicalization stage must preserve validated descriptor order and identity"
            )
        if self.registration.canonical_descriptors != self.canonicalized:
            raise ValueError("registration stage must preserve canonical descriptor order and identity")
        if self.binding.registration is not self.registration:
            raise ValueError("binding stage must preserve registration provenance identity")
        if self.execution.binding is not self.binding:
            raise ValueError("execution stage must preserve binding provenance identity")


def _descriptor_text_map(
    descriptor_texts: Tuple[Tuple[str, str], ...],
) -> Mapping[str, str]:
    if type(descriptor_texts) is not tuple:
        raise TypeError("descriptor_texts must be an exact tuple")

    result = {}
    for item in descriptor_texts:
        if type(item) is not tuple or len(item) != 2:
            raise TypeError("descriptor_texts items must be exact two-tuples")
        descriptor_identity, descriptor_text = item
        if type(descriptor_identity) is not str or not descriptor_identity.strip():
            raise TypeError("descriptor text identity must be a non-empty string")
        if type(descriptor_text) is not str:
            raise TypeError("descriptor text must be an exact string")
        if descriptor_identity in result:
            raise ValueError("descriptor text identities must be unique")
        result[descriptor_identity] = descriptor_text
    return result


def run_quad_vector_descriptor_lifecycle(
    candidates: Tuple[QuadVectorDiscoveryCandidate, ...],
    *,
    descriptor_texts: Tuple[Tuple[str, str], ...],
    budget: QuadVectorResourceBudget,
    implementations: Mapping[str, Any],
    context: QuadVectorExecutionContext,
) -> QuadVectorDescriptorLifecycle:
    """Run the complete canonical descriptor lifecycle without implicit loading."""

    if type(candidates) is not tuple:
        raise TypeError("candidates must be an exact tuple")
    if type(budget) is not QuadVectorResourceBudget:
        raise TypeError("budget must be an exact QuadVectorResourceBudget")
    if type(context) is not QuadVectorExecutionContext:
        raise TypeError("context must be an exact QuadVectorExecutionContext")

    inventory = discover_quad_vector_modules(candidates)
    texts = _descriptor_text_map(descriptor_texts)

    discovered_ids = tuple(item.descriptor_identity for item in inventory.candidates)
    if set(texts) != set(discovered_ids) or len(texts) != len(discovered_ids):
        raise ValueError(
            "descriptor_texts must provide exact coverage for discovered descriptor identities"
        )

    parsed = tuple(
        parse_quad_vector_descriptor(candidate, texts[candidate.descriptor_identity])
        for candidate in inventory.candidates
    )
    validated = tuple(validate_quad_vector_descriptor(item) for item in parsed)
    canonicalized = tuple(canonicalize_quad_vector_descriptor(item) for item in validated)
    registration = register_quad_vector_descriptors(canonicalized, budget=budget)
    binding = bind_quad_vector_descriptors(registration)
    execution = execute_quad_vector_descriptors(
        binding,
        implementations=implementations,
        context=context,
    )

    return QuadVectorDescriptorLifecycle(
        inventory=inventory,
        parsed=parsed,
        validated=validated,
        canonicalized=canonicalized,
        registration=registration,
        binding=binding,
        execution=execution,
    )


__all__ = (
    "QuadVectorDescriptorLifecycle",
    "run_quad_vector_descriptor_lifecycle",
)
