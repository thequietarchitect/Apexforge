"""Canonical descriptor canonicalization for the P11.7 Quad-Vector Engine.

P11.7N translates one semantically validated descriptor into the existing
immutable QuadVectorModuleSpec contract. It does not register, bind, execute,
import, or load module implementations.
"""

from __future__ import annotations

from dataclasses import dataclass

from .module import QuadVectorModuleSpec
from .validation import QuadVectorValidatedDescriptor


@dataclass(frozen=True)
class QuadVectorCanonicalDescriptor:
    """Immutable provenance-bearing result of descriptor canonicalization."""

    validated: QuadVectorValidatedDescriptor
    spec: QuadVectorModuleSpec

    def __post_init__(self) -> None:
        if type(self.validated) is not QuadVectorValidatedDescriptor:
            raise TypeError(
                "validated must be an exact QuadVectorValidatedDescriptor"
            )
        if type(self.spec) is not QuadVectorModuleSpec:
            raise TypeError("spec must be an exact QuadVectorModuleSpec")

        expected = (
            self.validated.canonical_id,
            self.validated.version,
            self.validated.kind,
            self.validated.determinism_contract,
            self.validated.implementation_reference,
            self.validated.accepted_inputs,
            self.validated.produced_outputs,
            self.validated.eligible_vectors,
            self.validated.dependencies,
            self.validated.authority_requirements,
            self.validated.resource_budget,
        )
        actual = (
            self.spec.canonical_id,
            self.spec.version,
            self.spec.kind,
            self.spec.determinism_contract,
            self.spec.implementation_reference,
            self.spec.accepted_inputs,
            self.spec.produced_outputs,
            self.spec.eligible_vectors,
            self.spec.dependencies,
            self.spec.authority_requirements,
            self.spec.resource_budget,
        )
        if actual != expected:
            raise ValueError(
                "canonical spec must preserve the validated descriptor contract"
            )


def canonicalize_quad_vector_descriptor(
    validated: QuadVectorValidatedDescriptor,
) -> QuadVectorCanonicalDescriptor:
    """Translate one validated descriptor into the canonical module spec."""

    if type(validated) is not QuadVectorValidatedDescriptor:
        raise TypeError(
            "validated must be an exact QuadVectorValidatedDescriptor"
        )

    spec = QuadVectorModuleSpec(
        canonical_id=validated.canonical_id,
        version=validated.version,
        kind=validated.kind,
        determinism_contract=validated.determinism_contract,
        implementation_reference=validated.implementation_reference,
        accepted_inputs=validated.accepted_inputs,
        produced_outputs=validated.produced_outputs,
        eligible_vectors=validated.eligible_vectors,
        dependencies=validated.dependencies,
        authority_requirements=validated.authority_requirements,
        resource_budget=validated.resource_budget,
    )

    return QuadVectorCanonicalDescriptor(validated=validated, spec=spec)


__all__ = (
    "QuadVectorCanonicalDescriptor",
    "canonicalize_quad_vector_descriptor",
)
