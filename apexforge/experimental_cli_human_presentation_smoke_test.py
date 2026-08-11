"""Experimental human-readable CLI presentation routing smoke test."""

from __future__ import annotations

import json
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

from tooling.cli import EXIT_SUCCESS, main as cli_main
from tooling.cli_presentation import ANSI_GREEN, ANSI_RESET


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def invoke(arguments, *, stdin_text: str = ""):
    stdout = StringIO()
    stderr = StringIO()
    code = cli_main(
        arguments,
        stdin=StringIO(stdin_text),
        stdout=stdout,
        stderr=stderr,
    )
    return code, stdout.getvalue(), stderr.getvalue()


def write_narrative_project(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    first = """story PresentationDemo {
scene Start {
body "Start."
}
timeline Main {
scenes [Start, End]
}
}
"""
    second = """story PresentationDemo {
scene End {
body "End."
}
}
"""
    (root / "01-start.apex").write_text(first, encoding="utf-8")
    (root / "02-end.apex").write_text(second, encoding="utf-8")
    (root / "apexforge.json").write_text(
        json.dumps(
            {
                "schema": 1,
                "name": "PresentationDemo",
                "sources": ["01-start.apex", "02-end.apex"],
                "entry": "PresentationDemo",
            },
            separators=(",", ":"),
        ),
        encoding="utf-8",
    )


def main_test() -> None:
    air_project = repo_root() / "examples" / "P11Validation"

    code, stdout, stderr = invoke(("--color", "always", "run", str(air_project)))
    require(code == EXIT_SUCCESS, f"forced-color run failed: {stderr!r}")
    require(stderr == "", "forced-color run wrote unexpected stderr")
    require(
        f"{ANSI_GREEN}ApexForge run succeeded: P11Validation{ANSI_RESET}\n" in stdout,
        "run success summary was not green",
    )

    with TemporaryDirectory() as directory:
        temporary_root = Path(directory)
        artifact_path = temporary_root / "air-build.json"
        code, stdout, stderr = invoke(
            (
                "--color",
                "always",
                "build",
                str(air_project),
                "--output",
                str(artifact_path),
            )
        )
        require(code == EXIT_SUCCESS and artifact_path.is_file(), f"forced-color build failed: {stderr!r}")
        require(stderr == "", "forced-color build wrote unexpected stderr")
        require(
            f"{ANSI_GREEN}ApexForge build succeeded: P11Validation{ANSI_RESET}\n" in stdout,
            "build success summary was not green",
        )
        require(
            f"{ANSI_GREEN}Artifact written.{ANSI_RESET}\n" in stdout,
            "artifact completion summary was not green",
        )

        narrative_project = temporary_root / "narrative"
        write_narrative_project(narrative_project)
        code, stdout, stderr = invoke(
            (
                "--color",
                "always",
                "simulate",
                str(narrative_project),
                "--observer",
                "--max-steps",
                "1",
            )
        )
        require(code == EXIT_SUCCESS, f"forced-color simulate failed: {stderr!r}")
        require(stderr == "", "forced-color simulate wrote unexpected stderr")
        require(
            stdout.startswith(f"{ANSI_GREEN}ApexForge narrative simulation{ANSI_RESET}\n"),
            "simulation heading was not green",
         )

    print("Run success presentation routing: PASS")
    print("Build success presentation routing: PASS")
    print("Build completion presentation routing: PASS")
    print("Simulation heading presentation routing: PASS")
    print("Experimental human-readable CLI presentation routing: PASS")


if __name__ == "__main__":
    main_test()
