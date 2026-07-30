"""Cross-platform ApexForge smoke-test regression harness.

The harness discovers test paths from the filesystem rather than accepting a
copied filename list. This prevents embedded newlines and other control
characters from becoming invalid paths.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import argparse
import subprocess
import sys
import time
from typing import Iterable


_PHASE_PREFIXES = {
    "all": (),
    "p7": ("p7_",),
    "p8": ("p8_",),
    "p9": ("p9_",),
    "p10": ("p10_",),
}


@dataclass(frozen=True)
class RegressionResult:
    name: str
    path: Path
    return_code: int
    elapsed_seconds: float


class RegressionHarnessError(RuntimeError):
    """Raised for malformed test layouts or invalid harness arguments."""


def _has_control_character(value: str) -> bool:
    return any(ord(character) < 32 or ord(character) == 127 for character in value)


def discover_smoke_tests(
    package_directory: Path,
    *,
    phase: str = "all",
) -> tuple[Path, ...]:
    """Discover canonical smoke tests directly from the package directory."""

    package_directory = Path(package_directory)

    if not package_directory.is_dir():
        raise RegressionHarnessError(
            f"lowercase ApexForge package folder not found: {package_directory}"
        )

    if phase not in _PHASE_PREFIXES:
        raise RegressionHarnessError(
            f"unknown regression phase {phase!r}; "
            f"expected one of {tuple(_PHASE_PREFIXES)}"
        )

    prefixes = _PHASE_PREFIXES[phase]
    discovered = []

    for path in package_directory.glob("*_smoke_test.py"):
        if not path.is_file():
            continue

        if prefixes and not path.name.startswith(prefixes):
            continue

        if _has_control_character(path.name):
            raise RegressionHarnessError(
                f"illegal control character in test filename: {path.name!r}"
            )

        if path.name != path.name.strip():
            raise RegressionHarnessError(
                f"leading or trailing whitespace in test filename: {path.name!r}"
            )

        discovered.append(path.resolve())

    discovered.sort(key=lambda item: item.name.casefold())

    if not discovered:
        raise RegressionHarnessError(
            f"no smoke tests found for phase {phase!r} in {package_directory}"
        )

    folded_names: set[str] = set()
    for path in discovered:
        folded = path.name.casefold()
        if folded in folded_names:
            raise RegressionHarnessError(
                f"duplicate smoke-test filename detected: {path.name}"
            )
        folded_names.add(folded)

    return tuple(discovered)


def run_smoke_tests(
    tests: Iterable[Path],
    *,
    python_executable: str = sys.executable,
) -> tuple[RegressionResult, ...]:
    """Run tests sequentially and stop immediately on the first failure."""

    results: list[RegressionResult] = []

    for test in tuple(tests):
        started = time.monotonic()
        completed = subprocess.run(
            [python_executable, str(test)],
            cwd=str(test.parent.parent),
            check=False,
        )
        elapsed = time.monotonic() - started

        result = RegressionResult(
            name=test.name,
            path=test,
            return_code=completed.returncode,
            elapsed_seconds=elapsed,
        )
        results.append(result)

        if completed.returncode != 0:
            break

    return tuple(results)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Discover and run ApexForge smoke tests without copied path lists."
        )
    )
    parser.add_argument(
        "--repository-root",
        type=Path,
        default=Path.cwd(),
        help="Repository root containing the lowercase apexforge package.",
    )
    parser.add_argument(
        "--phase",
        choices=tuple(_PHASE_PREFIXES),
        default="all",
        help="Run all tests or only one numbered phase.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List discovered tests without executing them.",
    )
    arguments = parser.parse_args(argv)

    package_directory = arguments.repository_root / "apexforge"

    try:
        tests = discover_smoke_tests(
            package_directory,
            phase=arguments.phase,
        )
    except RegressionHarnessError as error:
        print(f"REGRESSION HARNESS ERROR: {error}", file=sys.stderr)
        return 2

    print(f"Discovered {len(tests)} smoke test(s).")

    if arguments.list:
        for test in tests:
            print(test)
        return 0

    results = run_smoke_tests(tests)

    for result in results:
        status = "PASS" if result.return_code == 0 else "FAIL"
        print(
            f"{status}: {result.name} "
            f"({result.elapsed_seconds:.3f}s)"
        )

    if len(results) != len(tests) or any(
        result.return_code != 0
        for result in results
    ):
        return 1

    print(f"All {len(results)} smoke tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())