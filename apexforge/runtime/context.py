"""Runtime execution context."""

from __future__ import annotations

from dataclasses import dataclass

from authority.engine import AuthorityPolicy
from runtime.state import StateSnapshot


@dataclass(frozen=True)
class ExecutionContext:
    """All explicit inputs required for one runtime execution."""
    state: StateSnapshot
    authority: AuthorityPolicy