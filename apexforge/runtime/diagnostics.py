from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True, order=True)
class Diagnostic:
    severity: Literal["error", "warning", "info"]
    code: str
    message: str
    node_id: str = ""

    @property
    def is_error(self) -> bool:
        return self.severity == "error"