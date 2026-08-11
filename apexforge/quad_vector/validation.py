"""Canonical descriptor semantic validation for the P11.7 Quad-Vector Engine.

P11.7M validates a parsed descriptor into a typed immutable semantic snapshot.
It does not canonicalize into QuadVectorModuleSpec, register, bind, execute,
import, or load module implementations.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Tuple

from .model import QuadVectorLane, QuadVectorResourceBudget
from .module import QuadVectorModuleKind
from .parsing import QuadVectorParsedDescriptor


_REQUIRED_FIELDS = (
    "canonical_id",
    "version",
    "kind",
    "accepted_inputs",
    "produced_outputs",
    "eligible_vectors",
    "dependencies",
    "determinism_contract",
    "authority_requirements",
    "resource_budget",
    "implementation_reference",
)

_KIND_BY_VALUE = {item.value: item for item in QuadVectorModuleKind}
_KIND_BY_VALUE.update({item.name.lower(): item for item in QuadVectorModuleKind})
_LANE_BY_VALUE = {item.value: item for item in QuadVectorLane}


def _require_text(value: Any, *, owner: str) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{owner} must be a non-empty string")
    return value


def _require_text_tuple(value: Any, *, owner: str) -> Tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{owner} must be an array")
    result = []
    for item in value:
        result.append(_require_text(item, owner=f"{owner} item"))
    if len(set(result)) != len(result):
        raise ValueError(f"{owner} must not contain duplicates")
    return tuple(result)


def _require_lane_tuple(value: Any) -> Tuple[QuadVectorLane, ...]:
    if type(value) is not tuple:
        raise ValueError("eligible_vectors must be an array")
    lanes = []
    for item in value:
        if type(item) is not str or item not in _LANE_BY_VALUE:
            raise ValueError("eligible_vectors contains an unknown Quad-Vector lane")
        lanes.append(_LANE_BY_VALUE[item])
    if len(set(lanes)) != len(lanes):
        raise ValueError("eligible_vectors must not contain duplicates")
    return tuple(lanes)


def _require_kind(value: Any) -> QuadVectorModuleKind:
    if type(value) is not str or value not in _KIND_BY_VALUE:
        raise ValueError("kind must name a recognized QuadVectorModuleKind")
    return _KIND_BY_VALUE[value]


def _require_budget(value: Any) -> QuadVectorResourceBudget:
    if type(value) is not tuple:
        raise ValueError("resource_budget must be an object")
    pairs = {}
    for item in value:
        if type(item) is not tuple or len(item) != 2 or type(item[0]) is not str:
            raise ValueError("resource_budget must contain named fields")
        key, field_value = item
        if key in pairs:
            raise ValueError("resource_budget fields must be unique")
        pairs[key] = field_value

    expected = {"max_modules", "max_contributions", "max_iterations"}
    if set(pairs) != expected:
        raise ValueError("resource_budget must declare max_modules, max_contributions, and max_iterations")
    for key in expected:
        if type(pairs[key]) is not int or pairs[key] < 0:
            raise ValueError(f"resource_budget.{key} must be a non-negative int")

    return QuadVectorResourceBudget(
        max_modules=pairs["max_modules"],
        max_contributions=pairs["max_contributions"],
        max_iterations=pairs["max_iterations"],
    )


@dataclass(frozen=True)
class QuadVectorValidatedDescriptor:
    """Immutable semantic snapshot produced from one parsed descriptor."""

    parsed: QuadVectorParsedDescriptor
    canonical_id: str
    version: str
    kind: QuadVectorModuleKind
    accepted_inputs: Tuple[str, ...]
    produced_outputs: Tuple[str, ...]
    eligible_vectors: Tuple[QuadVectorLane, ...]
    dependencies: Tuple[str, ...]
    determinism_contract: str
    authority_requirements: Tuple[str, ...]
    resource_budget: QuadVectorResourceBudget
    implementation_reference: str

    def __post_init__(self) -> None:
        if type(self.parsed) is not QuadVectorParsedDescriptor:
            raise TypeError("parsed must be an exact QuadVectorParsedDescriptor")
        _require_text(self.canonical_id, owner="canonical_id")
        _require_text(self.version, owner="version")
        if type(self.kind) is not QuadVectorModuleKind:
            raise TypeError("kind must be an exact QuadVectorModuleKind")
        _require_text_tuple(self.accepted_inputs, owner="accepted_inputs")
        _require_text_tuple(self.produced_outputs, owner="produced_outputs")
        if type(self.eligible_vectors) is not tuple or any(
            type(item) is not QuadVectorLane for item in self.eligible_vectors
        ):
            raise TypeError("eligible_vectors must contain exact QuadVectorLane values")
        if len(set(self.eligible_vectors)) != len(self.eligible_vectors):
            raise ValueError("eligible_vectors must not contain duplicates")
        _require_text_tuple(self.dependencies, owner="dependencies")
        _require_text(self.determinism_contract, owner="determinism_contract")
        _require_text_tuple(self.authority_requirements, owner="authority_requirements")
        if type(self.resource_budget) is not QuadVectorResourceBudget:
            raise TypeError("resource_budget must be an exact QuadVectorResourceBudget")
        _require_text(self.implementation_reference, owner="implementation_reference")


def validate_quad_vector_descriptor(
    parsed: QuadVectorParsedDescriptor,
) -> QuadVectorValidatedDescriptor:
    """Semantically validate one parsed descriptor without advancing lifecycle authority."""

    if type(parsed) is not QuadVectorParsedDescriptor:
        raise TypeError("parsed must be an exact QuadVectorParsedDescriptor")

    fields = dict(parsed.fields)
    missing = tuple(name for name in _REQUIRED_FIELDS if name not in fields)
    if missing:
        raise ValueError("descriptor is missing required fields: " + ", ".join(missing))

    canonical_id = _require_text(fields["canonical_id"], owner="canonical_id")
    version = _require_text(fields["version"], owner="version")
    kind = _require_kind(fields["kind"])
    accepted_inputs = _require_text_tuple(fields["accepted_inputs"], owner="accepted_inputs")
    produced_outputs = _require_text_tuple(fields["produced_outputs"], owner="produced_outputs")
    eligible_vectors = _require_lane_tuple(fields["eligible_vectors"])
    dependencies = _require_text_tuple(fields["dependencies"], owner="dependencies")
    determinism_contract = _require_text(
        fields["determinism_contract"],
        owner="determinism_contract",
    )
    authority_requirements = _require_text_tuple(
        fields["authority_requirements"],
        owner="authority_requirements",
    )
    resource_budget = _require_budget(fields["resource_budget"])
    implementation_reference = _require_text(
        fields["implementation_reference"],
        owner="implementation_reference",
    )

    return QuadVectorValidatedDescriptor(
        parsed=parsed,
        canonical_id=canonical_id,
        version=version,
        kind=kind,
        accepted_inputs=accepted_inputs,
        produced_outputs=produced_outputs,
        eligible_vectors=eligible_vectors,
        dependencies=dependencies,
        determinism_contract=determinism_contract,
        authority_requirements=authority_requirements,
        resource_budget=resource_budget,
        implementation_reference=implementation_reference,
    )


__all__ = (
    "QuadVectorValidatedDescriptor",
    "validate_quad_vector_descriptor",
)
