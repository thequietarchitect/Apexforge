"""Experimental CLI semantic error-color smoke test."""

from __future__ import annotations

from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

from tooling.cli import EXIT_PROJECT, EXIT_USAGE, main
from tooling.cli_presentation import ANSI_RED, ANSI_RESET


class FakeTTY(StringIO):
    def __init__(self, *, tty: bool) -> None:
        super().__init__()
        self._tty = tty

    def isatty(self) -> bool:
        return self._tty


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run(argv: tuple[str, ...], *, tty: bool) -> tuple[int, str, str]:
    stdout = FakeTTY(tty=tty)
    stderr = FakeTTY(tty=tty)
    status = main(argv, stdout=stdout, stderr=stderr)
    return status, stdout.getvalue(), stderr.getvalue()


def main_test() -> None:
    status, output, errors = run(("--color", "always", "unknown-command"), tty=False)
    require(status == EXIT_USAGE, "forced-color usage error exit changed")
    require(output == "", "usage error wrote unexpected stdout")
    require(ANSI_RED in errors and ANSI_RESET in errors, "forced-color usage error was not red")

    with TemporaryDirectory() as directory:
        missing = Path(directory) / "missing-project"

        status, output, errors = run(("--color", "always", "check", str(missing)), tty=False)
        require(status == EXIT_PROJECT, "forced-color project error exit changed")
        require(output == "", "project error wrote unexpected stdout")
        require(errors.startswith(ANSI_RED) and errors.endswith(ANSI_RESET + "\n"), "forced-color project error was not red")

        status, output, errors = run(("--color", "never", "check", str(missing)), tty=True)
        require(status == EXIT_PROJECT, "never-color project error exit changed")
        require("\x1b[" not in errors, "never-color project error emitted ANSI")

        status, output, errors = run(("--color", "auto", "check", str(missing)), tty=True)
        require(status == EXIT_PROJECT, "auto TTY project error exit changed")
        require(errors.startswith(ANSI_RED) and errors.endswith(ANSI_RESET + "\n"), "auto TTY project error was not red")

    print("Forced usage-error color: PASS")
    print("Forced command-error color: PASS")
    print("Never-color stderr stability: PASS")
    print("Auto TTY stderr color: PASS")
    print("Experimental CLI semantic error styling: PASS")


if __name__ == "__main__":
    main_test()
