from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CanonicalExecutionValue:
    name: str
    representation: str
    data: str

    def validate(self) -> None:
        if not self.name.strip():
            raise ValueError("Canonical value name is required.")
        if self.representation == "BOOL":
            if self.data not in {"true", "false"}:
                raise ValueError("Canonical BOOL representation is invalid.")
        elif self.representation == "I64":
            try:
                parsed = int(self.data, 10)
            except ValueError as exc:
                raise ValueError("Canonical I64 representation is invalid.") from exc
            if parsed < -9223372036854775808 or parsed > 9223372036854775807 or str(parsed) != self.data:
                raise ValueError("Canonical I64 representation is invalid.")
        elif self.representation == "UTF8":
            pass
        else:
            raise ValueError("Canonical value representation is unsupported.")

    def canonical_form(self) -> str:
        self.validate()
        name_length = len(self.name.encode("utf-8"))
        data_length = len(self.data.encode("utf-8"))
        return f"{name_length}:{self.name}|{self.representation}|{data_length}:{self.data}"
