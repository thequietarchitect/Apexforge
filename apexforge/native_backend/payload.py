from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256

from .value import CanonicalExecutionValue


@dataclass(frozen=True)
class CanonicalExecutionPayload:
    values: tuple[CanonicalExecutionValue, ...]

    def validate(self) -> None:
        names: set[str] = set()
        for value in self.values:
            value.validate()
            if value.name in names:
                raise ValueError("Canonical payload contains duplicate value names.")
            names.add(value.name)

    def canonical_form(self) -> str:
        self.validate()
        ordered = sorted(self.values, key=lambda value: value.name)
        return "\n".join(value.canonical_form() for value in ordered)

    def fingerprint(self) -> str:
        return sha256(self.canonical_form().encode("utf-8")).hexdigest().upper()
