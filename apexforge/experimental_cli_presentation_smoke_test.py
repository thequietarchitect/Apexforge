from __future__ import annotations

from io import StringIO
from typing import Mapping

from tooling.cli_presentation import (
    COLOR_ALWAYS,
    COLOR_AUTO,
    COLOR_NEVER,
    ANSI_GREEN,
    ANSI_RED,
    CLIStyler,
    resolve_color_enabled,
)


class FakeTTY(StringIO):
    def __init__(self, *, tty: bool) -> None:
        super().__init__()
        self._tty = tty

    def isatty(self) -> bool:
        return self._tty


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def env(**values: str) -> Mapping[str, str]:
    return values


def main() -> None:
    tty = FakeTTY(tty=True)
    redirected = FakeTTY(tty=False)

    require(resolve_color_enabled(COLOR_AUTO, tty, env()), "auto did not enable color for TTY")
    require(not resolve_color_enabled(COLOR_AUTO, redirected, env()), "auto enabled color for redirected stream")
    require(not resolve_color_enabled(COLOR_AUTO, tty, env(NO_COLOR="1")), "NO_COLOR did not suppress auto color")
    require(resolve_color_enabled(COLOR_ALWAYS, redirected, env(NO_COLOR="1")), "always did not override NO_COLOR")
    require(not resolve_color_enabled(COLOR_NEVER, tty, env()), "never enabled color")

    plain = CLIStyler(enabled=False)
    colored = CLIStyler(enabled=True)
    require(plain.success("PASS") == "PASS", "plain success output changed")
    require(plain.error("FAIL") == "FAIL", "plain error output changed")
    require(colored.success("PASS") == f"{ANSI_GREEN}PASS\x1b[0m", "success ANSI contract changed")
    require(colored.error("FAIL") == f"{ANSI_RED}FAIL\x1b[0m", "error ANSI contract changed")

    print("TTY-aware auto color policy: PASS")
    print("NO_COLOR and explicit override precedence: PASS")
    print("Plain-output byte stability: PASS")
    print("Semantic success/error styling: PASS")
    print("Experimental CLI presentation foundation: PASS")


if __name__ == "__main__":
    main()
