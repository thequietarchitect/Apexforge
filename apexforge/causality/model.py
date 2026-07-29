"""Canonical causal AIR model objects.

This module owns causal decisions, paths, and directive-invocation actions.
It intentionally avoids importing ``air.model`` at runtime so ``air.model``
may safely re-export these classes for AFP-P1 compatibility.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional, Tuple, TYPE_CHECKING


if TYPE_CHECKING:
    from air.model import EventEmission, StateAssignment
    from effects.model import EffectIntent


@dataclass(frozen=True, init=False)
class DirectiveInvocation:
    """An ordered request to invoke another directive.

    ``target`` is the canonical field. ``directive`` remains accepted as a
    construction alias for older AFP-P1/AFP-P2 call sites.
    """

    target: str
    id: str = ""

    def __init__(
        self,
        target: Optional[str] = None,
        id: str = "",
        *,
        directive: Optional[str] = None,
    ) -> None:
        resolved_target = (
            target
            if target is not None
            else directive
        )

        if resolved_target is None:
            raise TypeError(
                "DirectiveInvocation requires "
                "'target' or legacy 'directive'."
            )

        if not isinstance(
            resolved_target,
            str,
        ) or not resolved_target:
            raise ValueError(
                "DirectiveInvocation target must "
                "be a non-empty string."
            )

        object.__setattr__(
            self,
            "target",
            resolved_target,
        )
        object.__setattr__(
            self,
            "id",
            id,
        )

    @property
    def directive(self) -> str:
        """Legacy read alias for the canonical target field."""

        return self.target


@dataclass(frozen=True)
class CausalPath:
    id: str
    weight: int
    assignments: Tuple["StateAssignment", ...] = ()
    emits: Tuple["EventEmission", ...] = ()
    invocations: Tuple[DirectiveInvocation, ...] = ()
    effects: Tuple["EffectIntent", ...] = ()
    rationale: str = ""
    actions: Tuple[object, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "assignments",
            tuple(self.assignments),
        )
        object.__setattr__(
            self,
            "emits",
            tuple(self.emits),
        )
        object.__setattr__(
            self,
            "invocations",
            tuple(self.invocations),
        )
        object.__setattr__(
            self,
            "effects",
            tuple(self.effects),
        )
        object.__setattr__(
            self,
            "actions",
            tuple(self.actions),
        )


@dataclass(frozen=True)
class CausalDecision:
    id: str
    cause: str = ""
    paths: Tuple[CausalPath, ...] = ()
    policy: Literal["max_weight"] = "max_weight"

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "paths",
            tuple(self.paths),
        )