"""Canonical registration and dependency binding for P11.7 Quad-Vector modules.

P11.7E makes passive module specifications installable into an immutable registry
and binds their declared dependencies deterministically. It deliberately does not
load implementation references or execute modules.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

from .model import QuadVectorResourceBudget
from .module import QuadVectorModuleSpec


@dataclass(frozen=True)
class QuadVectorModuleRegistry:
    """Immutable authored-order registry of canonical module specifications."""

    specs: Tuple[QuadVectorModuleSpec, ...]
    budget: QuadVectorResourceBudget

    def __post_init__(self) -> None:
        if type(self.specs) is not tuple:
            raise TypeError("specs must be a tuple")
        if any(type(spec) is not QuadVectorModuleSpec for spec in self.specs):
            raise TypeError("specs must contain exact QuadVectorModuleSpec values")
        if type(self.budget) is not QuadVectorResourceBudget:
            raise TypeError("budget must be an exact QuadVectorResourceBudget")

    @property
    def module_count(self) -> int:
        return len(self.specs)

    def lookup(self, canonical_id: str) -> Optional[QuadVectorModuleSpec]:
        if type(canonical_id) is not str:
            raise TypeError("canonical_id must be a string")
        for spec in self.specs:
            if spec.canonical_id == canonical_id:
                return spec
        return None


@dataclass(frozen=True)
class QuadVectorModuleBinding:
    """One immutable module binding with dependencies in declared order."""

    spec: QuadVectorModuleSpec
    dependencies: Tuple["QuadVectorModuleBinding", ...]

    def __post_init__(self) -> None:
        if type(self.spec) is not QuadVectorModuleSpec:
            raise TypeError("spec must be an exact QuadVectorModuleSpec")
        if type(self.dependencies) is not tuple:
            raise TypeError("dependencies must be a tuple")
        if any(type(item) is not QuadVectorModuleBinding for item in self.dependencies):
            raise TypeError(
                "dependencies must contain exact QuadVectorModuleBinding values"
            )


def register_quad_vector_modules(
    specs: Tuple[QuadVectorModuleSpec, ...],
    *,
    budget: QuadVectorResourceBudget,
) -> QuadVectorModuleRegistry:
    """Validate and register module specifications without executing them."""

    if type(specs) is not tuple:
        raise TypeError("specs must be a tuple")
    if any(type(spec) is not QuadVectorModuleSpec for spec in specs):
        raise TypeError("specs must contain exact QuadVectorModuleSpec values")
    if type(budget) is not QuadVectorResourceBudget:
        raise TypeError("budget must be an exact QuadVectorResourceBudget")

    if len(specs) > budget.max_modules:
        raise ValueError("registry module count exceeds canonical resource budget")

    identities = tuple(spec.canonical_id for spec in specs)
    if len(set(identities)) != len(identities):
        raise ValueError("registry contains a canonical module identity collision")

    known = set(identities)
    for spec in specs:
        missing = tuple(
            dependency
            for dependency in spec.dependencies
            if dependency not in known
        )
        if missing:
            raise ValueError(
                "registry contains unresolved module dependencies: "
                + ", ".join(missing)
            )

    return QuadVectorModuleRegistry(specs=specs, budget=budget)


def bind_quad_vector_modules(
    registry: QuadVectorModuleRegistry,
) -> Tuple[QuadVectorModuleBinding, ...]:
    """Bind dependencies in deterministic authored-scan order.

    Each iteration scans the immutable authored registry from the beginning and
    binds the first unresolved module whose declared dependencies are already
    bound. This makes newly unblocked authored modules eligible before later
    independent modules while remaining deterministic.
    """

    if type(registry) is not QuadVectorModuleRegistry:
        raise TypeError("registry must be an exact QuadVectorModuleRegistry")

    bindings = []
    by_id = {}

    while len(bindings) < registry.module_count:
        bound_one = False

        for spec in registry.specs:
            if spec.canonical_id in by_id:
                continue
            if not all(dependency in by_id for dependency in spec.dependencies):
                continue

            dependency_bindings = tuple(
                by_id[dependency] for dependency in spec.dependencies
            )
            binding = QuadVectorModuleBinding(
                spec=spec,
                dependencies=dependency_bindings,
            )
            bindings.append(binding)
            by_id[spec.canonical_id] = binding
            bound_one = True
            break

        if not bound_one:
            unresolved = tuple(
                spec.canonical_id
                for spec in registry.specs
                if spec.canonical_id not in by_id
            )
            raise ValueError(
                "module dependency cycle prevents deterministic binding: "
                + ", ".join(unresolved)
            )

    return tuple(bindings)


__all__ = (
    "QuadVectorModuleBinding",
    "QuadVectorModuleRegistry",
    "bind_quad_vector_modules",
    "register_quad_vector_modules",
)
