"""P11.1A observational project-pipeline performance baseline.

This module deliberately remains separate from the public ApexForge CLI. It
measures the existing project loader, validated project builder, and internal
``ProjectBuild.execute`` path without changing any of those operations.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import os
from pathlib import Path
import platform
from statistics import mean, median
import sys
from time import perf_counter_ns
from typing import Callable, Iterable, Mapping, Optional, Sequence, TextIO, Union

from authority.engine import AuthorityEngine
from authority.model import AuthorityGrant
from language.project import ProjectBuild, build_project
from runtime.context import ExecutionContext
from runtime.state import StateSnapshot
from tooling.project_loader import load_project


PERFORMANCE_BASELINE_SCHEMA = "apexforge.performance-baseline/v1"
PERFORMANCE_CLOCK = "time.perf_counter_ns"
PERFORMANCE_DURATION_UNIT = "nanoseconds"
DEFAULT_WARMUPS = 1
DEFAULT_MEASURED_SAMPLES = 5

_FIXTURE_ROOT = Path(__file__).resolve().parent.parent / "fixtures" / "p11_1a"


class PerformanceBaselineError(RuntimeError):
    """Raised when a baseline fixture cannot complete its normal behavior."""


@dataclass(frozen=True)
class BaselineConfiguration:
    """Sampling configuration shared by every fixture in one report."""

    warmups: int = DEFAULT_WARMUPS
    measured_samples: int = DEFAULT_MEASURED_SAMPLES

    def __post_init__(self) -> None:
        if type(self.warmups) is not int or self.warmups < 0:
            raise ValueError("warmups must be a non-negative integer.")
        if (
            type(self.measured_samples) is not int
            or self.measured_samples < 1
        ):
            raise ValueError("measured_samples must be a positive integer.")

    def to_mapping(self) -> Mapping[str, int]:
        return {
            "warmups": self.warmups,
            "measured_samples": self.measured_samples,
        }


@dataclass(frozen=True)
class BaselineFixture:
    """One tracked project and its explicit, test-derived authority grants."""

    name: str
    project_root: Path
    authority_grants: tuple[AuthorityGrant, ...]

    def __post_init__(self) -> None:
        if type(self.name) is not str or not self.name:
            raise TypeError("BaselineFixture.name must be non-empty.")
        if not isinstance(self.project_root, Path):
            raise TypeError("BaselineFixture.project_root must be pathlib.Path.")
        grants = tuple(self.authority_grants)
        if any(not isinstance(grant, AuthorityGrant) for grant in grants):
            raise TypeError(
                "BaselineFixture.authority_grants must contain AuthorityGrant values."
            )
        object.__setattr__(self, "authority_grants", grants)


DEFAULT_FIXTURES = (
    BaselineFixture(
        name="minimal",
        project_root=_FIXTURE_ROOT / "minimal",
        authority_grants=(
            AuthorityGrant(
                principal="principal:Minimal",
                capability="directive.invoke:Minimal",
                resource="directive:Minimal",
            ),
        ),
    ),
    BaselineFixture(
        name="representative-linked",
        project_root=_FIXTURE_ROOT / "representative_linked",
        authority_grants=(
            AuthorityGrant(
                principal="principal:Representative",
                capability="directive.invoke:Representative",
                resource="directive:Representative",
            ),
        ),
    ),
)


@dataclass(frozen=True)
class DurationSample:
    project_load_ns: int
    validated_project_build_ns: int
    internal_execution_ns: int
    total_ns: int


@dataclass(frozen=True)
class DurationStatistics:
    minimum_ns: int
    median_ns: float
    mean_ns: float
    maximum_ns: int
    sample_count: int

    @classmethod
    def from_samples(cls, samples: Iterable[int]) -> "DurationStatistics":
        values = tuple(samples)
        if not values:
            raise ValueError("Duration statistics require at least one sample.")
        if any(type(value) is not int for value in values):
            raise TypeError("Duration samples must be integer nanoseconds.")
        return cls(
            minimum_ns=min(values),
            median_ns=float(median(values)),
            mean_ns=float(mean(values)),
            maximum_ns=max(values),
            sample_count=len(values),
        )

    def to_mapping(self) -> Mapping[str, object]:
        return {
            "minimum_ns": self.minimum_ns,
            "median_ns": self.median_ns,
            "mean_ns": self.mean_ns,
            "maximum_ns": self.maximum_ns,
            "sample_count": self.sample_count,
        }


@dataclass(frozen=True)
class FixtureBaseline:
    fixture: str
    source_count: int
    project_load: DurationStatistics
    validated_project_build: DurationStatistics
    internal_execution: DurationStatistics
    total: DurationStatistics

    def to_mapping(self) -> Mapping[str, object]:
        return {
            "fixture": self.fixture,
            "source_count": self.source_count,
            "durations": {
                "project_load": self.project_load.to_mapping(),
                "validated_project_build": (
                    self.validated_project_build.to_mapping()
                ),
                "internal_execution": self.internal_execution.to_mapping(),
                "total": self.total.to_mapping(),
            },
        }


@dataclass(frozen=True)
class BaselineReport:
    configuration: BaselineConfiguration
    environment: Mapping[str, object]
    benchmarks: tuple[FixtureBaseline, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "environment", dict(self.environment))
        object.__setattr__(self, "benchmarks", tuple(self.benchmarks))

    def to_mapping(self) -> Mapping[str, object]:
        return {
            "schema": PERFORMANCE_BASELINE_SCHEMA,
            "clock": PERFORMANCE_CLOCK,
            "duration_unit": PERFORMANCE_DURATION_UNIT,
            "configuration": self.configuration.to_mapping(),
            "environment": dict(self.environment),
            "benchmarks": [
                benchmark.to_mapping()
                for benchmark in self.benchmarks
            ],
        }

    def canonical_json(self) -> str:
        """Return the stable JSON representation for this observation."""

        return (
            json.dumps(
                self.to_mapping(),
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )


def environment_metadata() -> Mapping[str, object]:
    """Return only the approved non-personal reproducibility fields."""

    return {
        "python_version": platform.python_version(),
        "operating_system_family": platform.system(),
        "processor_architecture": platform.machine(),
        "logical_processor_count": os.cpu_count(),
    }


def _execution_context(
    build: ProjectBuild,
    fixture: BaselineFixture,
) -> ExecutionContext:
    """Reuse the established project smoke-test context construction."""

    return ExecutionContext(
        state=StateSnapshot.from_program_initials(build.program),
        authority=AuthorityEngine.from_grants(fixture.authority_grants),
    )


def _measure_sample(
    fixture: BaselineFixture,
    *,
    clock: Callable[[], int],
) -> tuple[DurationSample, int]:
    total_started = clock()

    load_started = clock()
    loaded = load_project(fixture.project_root)
    project_load_ns = clock() - load_started

    build_started = clock()
    build = build_project(
        loaded.source_mapping(),
        entry=loaded.manifest.entry,
    )
    validated_project_build_ns = clock() - build_started

    context = _execution_context(build, fixture)
    execution_started = clock()
    result = build.execute(context)
    internal_execution_ns = clock() - execution_started
    total_ns = clock() - total_started

    if not result.ok:
        raise PerformanceBaselineError(
            f"fixture {fixture.name!r} produced runtime diagnostics: "
            f"{result.diagnostics!r}"
        )

    return (
        DurationSample(
            project_load_ns=project_load_ns,
            validated_project_build_ns=validated_project_build_ns,
            internal_execution_ns=internal_execution_ns,
            total_ns=total_ns,
        ),
        len(loaded.sources),
    )


def run_fixture_baseline(
    fixture: BaselineFixture,
    configuration: BaselineConfiguration,
    *,
    clock: Callable[[], int] = perf_counter_ns,
) -> FixtureBaseline:
    """Warm a fixture, then summarize measured samples without thresholds."""

    for _ in range(configuration.warmups):
        _measure_sample(fixture, clock=clock)

    measured = tuple(
        _measure_sample(fixture, clock=clock)
        for _ in range(configuration.measured_samples)
    )
    samples = tuple(item[0] for item in measured)
    source_counts = tuple(item[1] for item in measured)

    if len(set(source_counts)) != 1:
        raise PerformanceBaselineError(
            f"fixture {fixture.name!r} changed source count between samples."
        )

    return FixtureBaseline(
        fixture=fixture.name,
        source_count=source_counts[0],
        project_load=DurationStatistics.from_samples(
            sample.project_load_ns for sample in samples
        ),
        validated_project_build=DurationStatistics.from_samples(
            sample.validated_project_build_ns for sample in samples
        ),
        internal_execution=DurationStatistics.from_samples(
            sample.internal_execution_ns for sample in samples
        ),
        total=DurationStatistics.from_samples(
            sample.total_ns for sample in samples
        ),
    )


def run_baseline_suite(
    configuration: Optional[BaselineConfiguration] = None,
    *,
    fixtures: Sequence[BaselineFixture] = DEFAULT_FIXTURES,
    clock: Callable[[], int] = perf_counter_ns,
) -> BaselineReport:
    """Run fixed fixture observations in their declared stable order."""

    selected_configuration = configuration or BaselineConfiguration()
    selected_fixtures = tuple(fixtures)
    if not selected_fixtures:
        raise ValueError("At least one baseline fixture is required.")

    return BaselineReport(
        configuration=selected_configuration,
        environment=environment_metadata(),
        benchmarks=tuple(
            run_fixture_baseline(
                fixture,
                selected_configuration,
                clock=clock,
            )
            for fixture in selected_fixtures
        ),
    )


def _milliseconds(value_ns: Union[int, float]) -> str:
    return f"{value_ns / 1_000_000:.3f} ms"


def format_console_report(report: BaselineReport) -> str:
    """Render a concise human-readable advisory report."""

    environment = report.environment
    lines = [
        "ApexForge P11.1A Performance Baseline",
        f"Clock: {PERFORMANCE_CLOCK}; unit: {PERFORMANCE_DURATION_UNIT}",
        (
            f"Warmups: {report.configuration.warmups}; measured samples: "
            f"{report.configuration.measured_samples}"
        ),
        (
            "Environment: Python "
            f"{environment['python_version']}; "
            f"{environment['operating_system_family']}; "
            f"{environment['processor_architecture']}; "
            f"logical processors={environment['logical_processor_count']}"
        ),
    ]

    labels = (
        ("project load", "project_load"),
        ("validated project build", "validated_project_build"),
        ("internal execution", "internal_execution"),
        ("total", "total"),
    )
    for benchmark in report.benchmarks:
        lines.append(
            f"Fixture: {benchmark.fixture} ({benchmark.source_count} source(s))"
        )
        for label, attribute in labels:
            statistics = getattr(benchmark, attribute)
            lines.append(
                f"  {label}: min={_milliseconds(statistics.minimum_ns)}; "
                f"median={_milliseconds(statistics.median_ns)}; "
                f"mean={_milliseconds(statistics.mean_ns)}; "
                f"max={_milliseconds(statistics.maximum_ns)}; "
                f"n={statistics.sample_count}"
            )

    lines.append("Advisory only: no pass/fail performance threshold is applied.")
    return "\n".join(lines) + "\n"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the internal P11.1A project performance baseline."
    )
    parser.add_argument(
        "--warmups",
        type=int,
        default=DEFAULT_WARMUPS,
        help=f"warmup iterations per fixture (default: {DEFAULT_WARMUPS})",
    )
    parser.add_argument(
        "--samples",
        type=int,
        default=DEFAULT_MEASURED_SAMPLES,
        help=(
            "measured iterations per fixture "
            f"(default: {DEFAULT_MEASURED_SAMPLES})"
        ),
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        help="optional file that receives the stable JSON report",
    )
    return parser


def main(
    argv: Optional[Sequence[str]] = None,
    *,
    stdout: Optional[TextIO] = None,
) -> int:
    arguments = _parser().parse_args(argv)
    configuration = BaselineConfiguration(
        warmups=arguments.warmups,
        measured_samples=arguments.samples,
    )
    report = run_baseline_suite(configuration)
    output = stdout or sys.stdout
    output.write(format_console_report(report))

    if arguments.json_output is not None:
        arguments.json_output.write_text(
            report.canonical_json(),
            encoding="utf-8",
        )
        print("JSON report written.", file=output)

    return 0


__all__ = (
    "BaselineConfiguration",
    "BaselineFixture",
    "BaselineReport",
    "DEFAULT_FIXTURES",
    "DEFAULT_MEASURED_SAMPLES",
    "DEFAULT_WARMUPS",
    "DurationStatistics",
    "FixtureBaseline",
    "PERFORMANCE_BASELINE_SCHEMA",
    "PERFORMANCE_CLOCK",
    "PERFORMANCE_DURATION_UNIT",
    "PerformanceBaselineError",
    "environment_metadata",
    "format_console_report",
    "main",
    "run_baseline_suite",
    "run_fixture_baseline",
)


if __name__ == "__main__":
    raise SystemExit(main())
