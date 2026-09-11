from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256

from .payload import CanonicalExecutionPayload


@dataclass(frozen=True)
class CanonicalExecutionResult:
    input_fingerprint: str
    status: str
    outputs: CanonicalExecutionPayload

    def validate(self) -> None:
        if len(self.input_fingerprint) != 64 or any(ch not in "0123456789ABCDEF" for ch in self.input_fingerprint):
            raise ValueError("Canonical input fingerprint is invalid.")
        if self.status not in {"SUCCESS", "FAILURE"}:
            raise ValueError("Canonical result status is invalid.")
        self.outputs.validate()

    def canonical_form(self) -> str:
        self.validate()
        return f"{self.input_fingerprint}\n{self.status}\n{self.outputs.fingerprint()}"

    def fingerprint(self) -> str:
        return sha256(self.canonical_form().encode("utf-8")).hexdigest().upper()
