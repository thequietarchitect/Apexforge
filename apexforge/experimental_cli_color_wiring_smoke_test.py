"""Experimental CLI color option wiring smoke test."""

from __future__ import annotations

import json
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

from tooling.cli import EXIT_SUCCESS, main
from tooling.cli_presentation import ANSI_GREEN, ANSI_RESET


class FakeTTY(StringIO):
    def __init__(self, *, tty: bool) -> None:
        super().__init__()
        self._tty = tty

    def isatty(self) -> bool:
        return self._tty


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def write_project(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "main.apex").write_text("directive AirProject {}", encoding="utf-8")
    (root / "apexforge.json").write_text(
        json.dumps(
            {
                "schema": 1,
                "name": "AirProject",
                "sources": ["main.apex"],
                "entry": "AirProject",
            },
            separators=(",", ":"),
        ),
        encoding="utf-8",
    )


def run_check(root: Path, mode: str, *, tty: bool) -> tuple[int, str, str]:
    stdout = FakeTTY(tty=tty)
    stderr = FakeTTY(tty=tty)
    status = main(
        ("--color", mode, "check", str(root)),
        stdout=stdout,
        stderr=stderr,
        project_builder=lambda sources, entry: object(),
    )
    return status, stdout.getvalue(), stderr.getvalue()


def main_test() -> None:
    with TemporaryDirectory() as directory:
        root = Path(directory) / "project"
        write_project(root)

        status, output, errors = run_check(root, "always", tty=False)
        require(status == EXIT_SUCCESS, "global --color always was not accepted")
        require(errors == "", "forced-color check wrote unexpected stderr")
        expected_plain = "ApexForge check passed: AirProject (1 source(s)).\n"
        require(
            output == f"{ANSI_GREEN}{expected_plain.rstrip()}{ANSI_RESET}\n",
            "forced-color check success was not styled green",
        )

        status, output, errors = run_check(root, "never", tty=True)
        require(status == EXIT_SUCCESS, "global --color never was not accepted")
        require(errors == "", "never-color check wrote unexpected stderr")
        require(output == expected_plain, "never-color output changed plain bytes")

        status, output, errors = run_check(root, "auto", tty=False)
        require(status == EXIT_SUCCESS, "global --color auto was not accepted")
        require(errors == "", "auto redirected check wrote unexpected stderr")
        require(output == expected_plain, "auto redirected output was not plain")

    print("Global --color parser wiring: PASS")
    print("Forced semantic success color: PASS")
    print("Never-color plain output stability: PASS")
    print("Auto redirected plain output: PASS")
    print("Experimental CLI color wiring: PASS")


if __name__ == "__main__":
    main_test()
