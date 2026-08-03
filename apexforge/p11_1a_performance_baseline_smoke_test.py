"""Focused smoke test for the P11.1A performance baseline harness."""

from __future__ import annotations

import json
from pathlib import Path

from tooling.performance_baseline import (
    BaselineConfiguration,
    DEFAULT_FIXTURES,
    DEFAULT_MEASURED_SAMPLES,
    DEFAULT_WARMUPS,
    DurationStatistics,
    PERFORMANCE_BASELINE_SCHEMA,
    PERFORMANCE_CLOCK,
    PERFORMANCE_DURATION_UNIT,
    format_console_report,
    run_baseline_suite,
)


REPOSITORY_ROOT = Path(__file__).resolve().parent.parent


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def require_raises(expected_type, operation, message: str) -> None:
    try:
        operation()
    except expected_type:
        return
    raise AssertionError(message)


def main() -> None:
    defaults = BaselineConfiguration()
    require(defaults.warmups == 1, "default warmup count changed")
    require(defaults.measured_samples == 5, "default sample count changed")
    require(DEFAULT_WARMUPS == 1, "exported default warmup count changed")
    require(
        DEFAULT_MEASURED_SAMPLES == 5,
        "exported default measured sample count changed",
    )
    require_raises(
        ValueError,
        lambda: BaselineConfiguration(warmups=-1),
        "negative warmup count unexpectedly passed",
    )
    require_raises(
        ValueError,
        lambda: BaselineConfiguration(measured_samples=0),
        "zero measured samples unexpectedly passed",
    )

    require(
        tuple(fixture.name for fixture in DEFAULT_FIXTURES)
        == ("minimal", "representative-linked"),
        "fixed fixture order changed",
    )
    for fixture in DEFAULT_FIXTURES:
        require(
            fixture.project_root.is_dir(),
            f"tracked fixture is missing: {fixture.name}",
        )
        require(
            (fixture.project_root / "apexforge.json").is_file(),
            f"tracked fixture manifest is missing: {fixture.name}",
        )

    synthetic = DurationStatistics.from_samples((30, 10, 40, 20))
    require(synthetic.minimum_ns == 10, "minimum aggregation changed")
    require(synthetic.median_ns == 25.0, "median aggregation changed")
    require(synthetic.mean_ns == 25.0, "mean aggregation changed")
    require(synthetic.maximum_ns == 40, "maximum aggregation changed")
    require(synthetic.sample_count == 4, "sample count aggregation changed")

    configuration = BaselineConfiguration(warmups=1, measured_samples=2)
    report = run_baseline_suite(configuration)
    require(
        tuple(item.fixture for item in report.benchmarks)
        == ("minimal", "representative-linked"),
        "baseline did not preserve fixed fixture order",
    )
    require(
        tuple(item.source_count for item in report.benchmarks) == (1, 3),
        "baseline did not exercise minimal and multi-source projects",
    )
    for benchmark in report.benchmarks:
        for statistics in (
            benchmark.project_load,
            benchmark.validated_project_build,
            benchmark.internal_execution,
            benchmark.total,
        ):
            require(
                statistics.sample_count == configuration.measured_samples,
                "warmups leaked into measured sample statistics",
            )
            require(
                type(statistics.minimum_ns) is int
                and type(statistics.median_ns) is float
                and type(statistics.mean_ns) is float
                and type(statistics.maximum_ns) is int,
                "duration statistics lost their stable JSON number types",
            )

    serialized = report.canonical_json()
    decoded = json.loads(serialized)
    require(serialized.endswith("\n"), "canonical JSON omitted final newline")
    require(
        decoded["schema"] == PERFORMANCE_BASELINE_SCHEMA,
        "JSON schema identifier changed",
    )
    require(decoded["clock"] == PERFORMANCE_CLOCK, "JSON clock changed")
    require(
        decoded["duration_unit"] == PERFORMANCE_DURATION_UNIT,
        "JSON duration unit changed",
    )
    require(
        set(decoded["environment"])
        == {
            "python_version",
            "operating_system_family",
            "processor_architecture",
            "logical_processor_count",
        },
        "environment metadata exceeded the approved field set",
    )
    forbidden_keys = {
        "username",
        "hostname",
        "repository_path",
        "home_directory",
        "credentials",
        "tokens",
    }
    require(
        forbidden_keys.isdisjoint(decoded),
        "JSON report exposed a forbidden top-level field",
    )
    require(
        str(REPOSITORY_ROOT) not in serialized,
        "JSON report exposed the absolute repository path",
    )

    durations = decoded["benchmarks"][0]["durations"]
    require(
        set(durations)
        == {
            "project_load",
            "validated_project_build",
            "internal_execution",
            "total",
        },
        "JSON duration phase set changed",
    )
    expected_statistics = {
        "minimum_ns",
        "median_ns",
        "mean_ns",
        "maximum_ns",
        "sample_count",
    }
    require(
        all(set(value) == expected_statistics for value in durations.values()),
        "JSON statistics schema changed",
    )

    console = format_console_report(report)
    require(
        "project load:" in console
        and "validated project build:" in console
        and "internal execution:" in console
        and "total:" in console,
        "human report omitted a measured phase",
    )
    require(
        "min=" in console
        and "median=" in console
        and "mean=" in console
        and "max=" in console
        and "n=2" in console,
        "human report omitted required summary statistics",
    )
    require(
        "no pass/fail performance threshold" in console,
        "human report omitted its advisory status",
    )
    require(
        str(REPOSITORY_ROOT) not in console,
        "human report exposed the absolute repository path",
    )

    print("AFP-P11.1A performance baseline smoke test passed.")
    print("Fixed minimal and representative linked fixtures: PASS")
    print("Warmup and measured sampling: PASS")
    print("Nanosecond phase measurement: PASS")
    print("Stable JSON schema and metadata boundary: PASS")
    print("Human-readable advisory report: PASS")
    print("No absolute performance threshold: PASS")


if __name__ == "__main__":
    main()
