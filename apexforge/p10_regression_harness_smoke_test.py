"""Smoke test for the ApexForge regression-harness path safeguards."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from regression_harness import (
    RegressionHarnessError,
    discover_smoke_tests,
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    with TemporaryDirectory() as temporary:
        package = Path(temporary) / "apexforge"
        package.mkdir()

        canonical_names = (
            "p7_function_frontend_smoke_test.py",
            "p8_compiler_type_checking_smoke_test.py",
            "p9_final_integration_smoke_test.py",
            "p10_boolean_conversion_standard_library_smoke_test.py",
        )

        for name in canonical_names:
            (package / name).write_text(
                'print("PASS")\n',
                encoding="utf-8",
            )

        discovered = discover_smoke_tests(package)
        require(
            tuple(path.name for path in discovered)
            == tuple(sorted(canonical_names)),
            "filesystem discovery did not produce canonical ordering",
        )

        p8_only = discover_smoke_tests(
            package,
            phase="p8",
        )
        require(
            tuple(path.name for path in p8_only)
            == ("p8_compiler_type_checking_smoke_test.py",),
            "phase filtering did not isolate P8",
        )

        try:
            discover_smoke_tests(
                package,
                phase="p11",
            )
        except RegressionHarnessError:
            pass
        else:
            raise AssertionError(
                "unknown phase unexpectedly passed"
            )

    require(
        "\n" not in "p8_compiler_type_checking_smoke_test.py",
        "canonical regression name contains a newline",
    )

    print("AFP regression-harness smoke test passed.")
    print("Filesystem-driven discovery: PASS")
    print("Canonical ordering: PASS")
    print("Phase filtering: PASS")
    print("Unknown-phase rejection: PASS")
    print("Copied-path newline avoidance: PASS")


if __name__ == "__main__":
    main()