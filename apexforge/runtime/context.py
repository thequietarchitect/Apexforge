"""Runtime execution context."""

from __future__ import annotations

from dataclasses import dataclass

from authority.engine import AuthorityEngine
from runtime.state import StateSnapshot


@dataclass(frozen=True)
class ExecutionContext:
    state: StateSnapshot
    authority: AuthorityEngine