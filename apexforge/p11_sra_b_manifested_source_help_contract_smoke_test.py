"""SRA-B manifested-source CLI help-contract regression."""

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO

from tooling.cli import main


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def command_help(command: str) -> tuple[str, str]:
    stdout = StringIO()
    stderr = StringIO()
    try:
        with redirect_stdout(stdout), redirect_stderr(stderr):
            main([command, "--help"])
    except SystemExit as exc:
        require(exc.code == 0, f"{command} --help exit changed: {exc.code!r}")
    else:
        raise AssertionError(f"{command} --help did not terminate through argparse help")
    return stdout.getvalue(), stderr.getvalue()


def main_test() -> None:
    commands = ("project", "check", "run", "simulate", "build", "tap-check")
    for command in commands:
        stdout, stderr = command_help(command)
        normalized = " ".join(stdout.split())
        require(stderr == "", f"{command} --help wrote stderr: {stderr!r}")
        require(
            "source path within a manifested project" in normalized,
            f"{command} --help does not clarify manifested-source behavior: {stdout!r}",
        )

    print("P11 SRA-B manifested-source help-contract smoke test passed.")
    print("Project-locator source-path wording: PASS")
    print("Standalone-source ambiguity removed: PASS")
    print("Six public project commands covered: PASS")


if __name__ == "__main__":
    main_test()
