"""Constrained canonical module execution for the P11.7 Quad-Vector Engine.

P11.7F executes already-bound module specifications through explicitly supplied
implementation providers. It performs no import/discovery work and gives no
authoring system, including Codex, privileged runtime authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Mapping, Tuple

from .module import QuadVectorModuleSpec
from .registry import QuadVectorModuleBinding


@dataclass(frozen=True)
class QuadVectorExecutionContext:
    """Immutable authority, input, and invocation-budget envelope."""

    authorities: Tuple[str, ...]
    inputs: Tuple[Tuple[str, Any], ...]
    max_invocations: int

    def __post_init__(self) -> None:
        if type(self.authorities) is not tuple:
            raise TypeError("authorities must be a tuple")
        if any(type(item) is not str or not item.strip() for item in self.authorities):
            raise ValueError("authorities entries must be non-empty strings")
        if len(set(self.authorities)) != len(self.authorities):
            raise ValueError("authorities must not contain duplicates")

        if type(self.inputs) is not tuple:
            raise TypeError("inputs must be a tuple")
        keys = []
        for item in self.inputs:
            if type(item) is not tuple or len(item) != 2:
                raise TypeError("inputs must contain exact two-item tuples")
            key = item[0]
            if type(key) is not str or not key.strip():
                raise ValueError("input keys must be non-empty strings")
            keys.append(key)
        if len(set(keys)) != len(keys):
            raise ValueError("inputs must not contain duplicate keys")

        if type(self.max_invocations) is not int or self.max_invocations < 0:
            raise ValueError("max_invocations must be a non-negative int")


@dataclass(frozen=True)
class QuadVectorExecutionRecord:
    """Immutable record of one canonical bound-module invocation."""

    spec: QuadVectorModuleSpec
    outputs: Tuple[Tuple[str, Any], ...]
    provenance: Tuple[str, ...]

    def __post_init__(self) -> None:
        if type(self.spec) is not QuadVectorModuleSpec:
            raise TypeError("spec must be an exact QuadVectorModuleSpec")
        if type(self.outputs) is not tuple:
            raise TypeError("outputs must be a tuple")
        if any(type(item) is not tuple or len(item) != 2 for item in self.outputs):
            raise TypeError("outputs must contain exact two-item tuples")
        if type(self.provenance) is not tuple:
            raise TypeError("provenance must be a tuple")
        if any(type(item) is not str or not item.strip() for item in self.provenance):
            raise ValueError("provenance entries must be non-empty strings")


def _require_bound_sequence(
    bindings: Tuple[QuadVectorModuleBinding, ...],
) -> None:
    if type(bindings) is not tuple:
        raise TypeError("bindings must be a tuple")
    if any(type(binding) is not QuadVectorModuleBinding for binding in bindings):
        raise TypeError("bindings must contain exact QuadVectorModuleBinding values")

    prior = set()
    for binding in bindings:
        for dependency in binding.dependencies:
            if type(dependency) is not QuadVectorModuleBinding:
                raise TypeError("binding dependencies must be exact QuadVectorModuleBinding values")
            if dependency.spec.canonical_id not in prior:
                raise ValueError("bindings are not in deterministic dependency order")
        prior.add(binding.spec.canonical_id)


def _canonical_module_inputs(
    spec: QuadVectorModuleSpec,
    available: Mapping[str, Any],
) -> Dict[str, Any]:
    missing = tuple(name for name in spec.accepted_inputs if name not in available)
    if missing:
        raise ValueError(
            "module inputs are unavailable for declared contract: " + ", ".join(missing)
        )
    return {name: available[name] for name in spec.accepted_inputs}


def _canonical_outputs(
    spec: QuadVectorModuleSpec,
    result: Any,
) -> Tuple[Tuple[str, Any], ...]:
    if type(result) is not dict:
        raise TypeError("module implementation must return a dict")

    declared = spec.produced_outputs
    actual = tuple(result.keys())
    undeclared = tuple(name for name in actual if name not in declared)
    missing = tuple(name for name in declared if name not in result)
    if undeclared:
        raise ValueError(
            "module implementation produced undeclared outputs: " + ", ".join(undeclared)
        )
    if missing:
        raise ValueError(
            "module implementation omitted declared outputs: " + ", ".join(missing)
        )
    return tuple((name, result[name]) for name in declared)


def _execution_provenance(
    binding: QuadVectorModuleBinding,
    records_by_id: Mapping[str, QuadVectorExecutionRecord],
) -> Tuple[str, ...]:
    ordered = []
    seen = set()
    for dependency in binding.dependencies:
        record = records_by_id.get(dependency.spec.canonical_id)
        if record is None:
            raise ValueError("bound dependency has not executed")
        for token in record.provenance:
            if token not in seen:
                ordered.append(token)
                seen.add(token)

    own = f"{binding.spec.canonical_id}@{binding.spec.version}"
    if own not in seen:
        ordered.append(own)
    return tuple(ordered)


def execute_quad_vector_bindings(
    bindings: Tuple[QuadVectorModuleBinding, ...],
    *,
    implementations: Mapping[str, Callable[[Dict[str, Any], Tuple[QuadVectorModuleBinding, ...], QuadVectorExecutionContext], Dict[str, Any]]],
    context: QuadVectorExecutionContext,
) -> Tuple[QuadVectorExecutionRecord, ...]:
    """Execute canonical bound modules without discovery or implicit loading."""

    _require_bound_sequence(bindings)

    if type(context) is not QuadVectorExecutionContext:
        raise TypeError("context must be an exact QuadVectorExecutionContext")
    if not isinstance(implementations, Mapping):
        raise TypeError("implementations must be a mapping")

    if len(bindings) > context.max_invocations:
        raise ValueError("module execution exceeds its invocation budget")

    available = dict(context.inputs)
    authorities = set(context.authorities)
    records = []
    records_by_id = {}

    for binding in bindings:
        spec = binding.spec

        missing_authorities = tuple(
            authority
            for authority in spec.authority_requirements
            if authority not in authorities
        )
        if missing_authorities:
            raise PermissionError(
                "module execution lacks declared authorities: "
                + ", ".join(missing_authorities)
            )

        if spec.implementation_reference not in implementations:
            raise ValueError(
                "explicit implementation provider is missing for "
                + spec.implementation_reference
            )
        implementation = implementations[spec.implementation_reference]
        if not callable(implementation):
            raise TypeError("explicit implementation provider must be callable")

        module_inputs = _canonical_module_inputs(spec, available)
        result = implementation(module_inputs, binding.dependencies, context)
        outputs = _canonical_outputs(spec, result)

        for name, value in outputs:
            available[name] = value

        provenance = _execution_provenance(binding, records_by_id)
        record = QuadVectorExecutionRecord(
            spec=spec,
            outputs=outputs,
            provenance=provenance,
        )
        records.append(record)
        records_by_id[spec.canonical_id] = record

    return tuple(records)


__all__ = (
    "QuadVectorExecutionContext",
    "QuadVectorExecutionRecord",
    "execute_quad_vector_bindings",
)
