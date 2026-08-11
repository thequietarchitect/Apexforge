"""Deterministic CLI presentation and ANSI color policy."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, TextIO


COLOR_AUTO = "auto"
COLOR_ALWAYS = "always"
COLOR_NEVER = "never"
COLOR_CHOICES = (COLOR_AUTO, COLOR_ALWAYS, COLOR_NEVER)

ANSI_RESET = "\x1b[0m"
ANSI_GREEN = "\x1b[32m"
ANSI_YELLOW = "\x1b[33m"
ANSI_RED = "\x1b[31m"


def _stream_is_tty(stream: TextIO) -> bool:
    """Return whether *stream* reports itself as an interactive terminal."""

    isatty = getattr(stream, "isatty", None)
    if not callable(isatty):
        return False
    try:
        return bool(isatty())
    except (OSError, ValueError):
        return False


def resolve_color_enabled(
    mode: str,
    stream: TextIO,
    environment: Mapping[str, str],
) -> bool:
    """Resolve one explicit color mode against stream and environment state."""

    if mode not in COLOR_CHOICES:
        raise ValueError(f"unsupported color mode: {mode!r}")
    if mode == COLOR_ALWAYS:
        return True
    if mode == COLOR_NEVER:
        return False
    if "NO_COLOR" in environment:
        return False
    return _stream_is_tty(stream)


@dataclass(frozen=True)
class CLIStyler:
    """Apply semantic ANSI styling without changing plain-text content."""

    enabled: bool

    def _wrap(self, text: str, ansi: str) -> str:
        if not self.enabled:
            return text
        return f"{ansi}{text}{ANSI_RESET}"

    def success(self, text: str) -> str:
        return self._wrap(text, ANSI_GREEN)

    def warning(self, text: str) -> str:
        return self._wrap(text, ANSI_YELLOW)

    def error(self, text: str) -> str:
        return self._wrap(text, ANSI_RED)


__all__ = (
    "ANSI_GREEN",
    "ANSI_RED",
    "ANSI_RESET",
    "ANSI_YELLOW",
    "CLIStyler",
    "COLOR_ALWAYS",
    "COLOR_AUTO",
    "COLOR_CHOICES",
    "COLOR_NEVER",
    "resolve_color_enabled",
)
