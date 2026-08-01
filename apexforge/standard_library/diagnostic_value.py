"""Passive AFP-P10.10 structured diagnostic runtime value.

Diagnostics are immutable data values. They do not emit output, mutate runtime
state, or enter the compiler/runtime diagnostic channels automatically.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Final


DIAGNOSTIC_SEVERITIES: Final[tuple[str, ...]] = (
    "info",
    "warning",
    "error",
)
MAX_DIAGNOSTIC_CODE_CODE_POINTS: Final[int] = 64
MAX_DIAGNOSTIC_MESSAGE_CODE_POINTS: Final[int] = 2048
MAX_DIAGNOSTIC_SUBJECT_CODE_POINTS: Final[int] = 256

_CODE_PATTERN = re.compile(r"[A-Za-z][A-Za-z0-9_.-]*\Z")
_SEVERITY_RANK = {
    "info": 0,
    "warning": 1,
    "error": 2,
}


def _require_text(
    value: object,
    *,
    owner: str,
    maximum: int,
    allow_empty: bool,
) -> str:
    if type(value) is not str:
        raise TypeError(
            f"{owner} must be a string; received {type(value).__name__}."
        )
    if not allow_empty and not value:
        raise ValueError(f"{owner} cannot be empty.")
    if len(value) > maximum:
        raise ValueError(
            f"{owner} exceeds the {maximum}-code-point limit."
        )
    if value != value.strip():
        raise ValueError(
            f"{owner} cannot contain leading or trailing whitespace."
        )
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        raise ValueError(f"{owner} cannot contain control characters.")
    return value


@dataclass(frozen=True)
class RuntimeDiagnostic:
    """One immutable structured diagnostic value."""

    severity: str
    code: str
    message: str
    subject: str = ""

    def __post_init__(self) -> None:
        severity = _require_text(
            self.severity,
            owner="RuntimeDiagnostic.severity",
            maximum=7,
            allow_empty=False,
        )
        if severity not in DIAGNOSTIC_SEVERITIES:
            supported = ", ".join(DIAGNOSTIC_SEVERITIES)
            raise ValueError(
                "RuntimeDiagnostic.severity must be one of "
                f"{supported}; received {severity!r}."
            )

        code = _require_text(
            self.code,
            owner="RuntimeDiagnostic.code",
            maximum=MAX_DIAGNOSTIC_CODE_CODE_POINTS,
            allow_empty=False,
        )
        if _CODE_PATTERN.fullmatch(code) is None:
            raise ValueError(
                "RuntimeDiagnostic.code must begin with a letter and contain "
                "letters, digits, underscores, periods, or hyphens only."
            )

        message = _require_text(
            self.message,
            owner="RuntimeDiagnostic.message",
            maximum=MAX_DIAGNOSTIC_MESSAGE_CODE_POINTS,
            allow_empty=False,
        )
        subject = _require_text(
            self.subject,
            owner="RuntimeDiagnostic.subject",
            maximum=MAX_DIAGNOSTIC_SUBJECT_CODE_POINTS,
            allow_empty=True,
        )

        object.__setattr__(self, "severity", severity)
        object.__setattr__(self, "code", code)
        object.__setattr__(self, "message", message)
        object.__setattr__(self, "subject", subject)

    @property
    def rank(self) -> int:
        """Return deterministic severity order: info < warning < error."""

        return _SEVERITY_RANK[self.severity]

    @property
    def is_info(self) -> bool:
        return self.severity == "info"

    @property
    def is_warning(self) -> bool:
        return self.severity == "warning"

    @property
    def is_error(self) -> bool:
        return self.severity == "error"

    @property
    def canonical_key(self) -> tuple[int, str, str, str]:
        """Return a stable ordering key without making diagnostics sortable."""

        return (
            self.rank,
            self.code,
            self.subject,
            self.message,
        )

    def with_subject(self, subject: str) -> "RuntimeDiagnostic":
        """Return a new diagnostic with the supplied validated subject."""

        return RuntimeDiagnostic(
            severity=self.severity,
            code=self.code,
            message=self.message,
            subject=subject,
        )

    def render(self) -> str:
        """Render one deterministic, locale-independent single line."""

        prefix = f"[{self.severity}:{self.code}]"
        if self.subject:
            return f"{prefix} {self.subject}: {self.message}"
        return f"{prefix} {self.message}"


__all__ = (
    "DIAGNOSTIC_SEVERITIES",
    "MAX_DIAGNOSTIC_CODE_CODE_POINTS",
    "MAX_DIAGNOSTIC_MESSAGE_CODE_POINTS",
    "MAX_DIAGNOSTIC_SUBJECT_CODE_POINTS",
    "RuntimeDiagnostic",
)