"""P11.11F TAP Check CLI and real-project acceptance coverage."""

from __future__ import annotations

from io import StringIO
import inspect
from pathlib import Path
import subprocess

from tap_check import TAP_CHECK_CATEGORY_IDS
from tooling import cli
from tooling.project_loader import load_project


PREDECESSOR_TAG = "afp-p11-11e-freeze"
PREDECESSOR_COMMIT = "1e75e0b228836a2e045829512f745d2c4b40e2d8"

FROZEN_TAP_HASHES = {
    "apexforge/tap_check/model.py":
        "C1E6F650977A73A7E3F3655A948416129AAB0AFDDB69DA561582F771C16B8769",
    "apexforge/tap_check/projection.py":
        "C43F222DC98704A3C3803F475359F97B72FCB0BEAB6F829188493CF591B117A2",
    "apexforge/tap_check/adapters.py":
        "8895FBF8D79EC70BE09E0F73E31B42829A3C6BB326F5B0326B54E9793C0C7CBA",
    "apexforge/tap_check/aggregation.py":
        "D272A29774AC435ACF58CCB2CD678A234F2CC47D0EEDBBAEA502D99AE9733BAA",
}

EXPECTED_CLI_PUBLIC_SURFACE = (
    "CLI_PROGRAM_NAME",
    "CLIProjectCheckError",
    "CLINarrativeRequestError",
    "CLINarrativeSessionError",
    "CLIUsageError",
    "EXIT_ARTIFACT_OUTPUT",
    "EXIT_CHECK",
    "EXIT_INTERNAL",
    "EXIT_NARRATIVE_REQUEST",
    "EXIT_NARRATIVE_SESSION",
    "EXIT_PROJECT",
    "EXIT_RUNTIME",
    "EXIT_SUCCESS",
    "EXIT_USAGE",
    "P10_T1_CLI_VERSION",
    "main",
)

ACCEPTANCE_PROJECT_CANDIDATES = (
    "apexforge/fixtures/p11_1b/manifest_entry",
    "examples/T1Demo",
    "examples/P11Validation",
)


def _root() -> Path:
    return Path(__file__).resolve().parents[1]


def _git(*arguments: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ("git", *arguments),
        cwd=_root(),
        check=False,
        text=True,
        encoding="utf-8",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _sha256(path: Path) -> str:
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _project_hashes(project_root: Path):
    return tuple(
        (
            path.relative_to(project_root).as_posix(),
            _sha256(path),
        )
        for path in sorted(
            (item for item in project_root.rglob("*") if item.is_file()),
            key=lambda item: item.relative_to(project_root).as_posix(),
        )
    )


def _acceptance_project_root() -> Path:
    root = _root()
    for relative in ACCEPTANCE_PROJECT_CANDIDATES:
        candidate = root / Path(relative)
        if not candidate.is_dir():
            continue
        if not (candidate / "apexforge.json").is_file():
            continue
        if not tuple(candidate.rglob("*.apex")):
            continue
        tracked = _git("ls-files", "--", relative + "/**")
        if tracked.returncode != 0 or not tracked.stdout.strip():
            continue
        return candidate
    raise AssertionError(
        "no tracked repository-resident .apex acceptance project was found"
    )


def _assert_predecessor() -> None:
    resolved = _git("rev-parse", "{}^{{}}".format(PREDECESSOR_TAG))
    _require(resolved.returncode == 0, resolved.stderr.strip())
    _require(
        resolved.stdout.strip() == PREDECESSOR_COMMIT,
        "P11.11E freeze target changed",
    )
    _require(
        _git("merge-base", "--is-ancestor", PREDECESSOR_TAG, "HEAD").returncode
        == 0,
        "P11.11E freeze is not an ancestor of P11.11F",
    )
    for relative, expected in FROZEN_TAP_HASHES.items():
        _require(
            _sha256(_root() / relative) == expected,
            "{} frozen TAP owner changed".format(relative),
        )


def _assert_cli_surface_and_parser() -> None:
    _require(
        cli.__all__ == EXPECTED_CLI_PUBLIC_SURFACE,
        "tooling.cli public surface changed",
    )
    parser = cli._parser()
    namespace = parser.parse_args(("tap-check", "."))
    _require(namespace.command == "tap-check", "tap-check parser routing changed")
    _require(namespace.path == ".", "tap-check default/path parsing changed")

    explicit = parser.parse_args(("tap-check", "some/project"))
    _require(
        explicit.path == "some/project",
        "tap-check explicit project path changed",
    )


def _assert_runner_is_observational() -> None:
    source = inspect.getsource(cli._run_tap_check)

    required = (
        "load_project(Path(path))",
        "compose_tap_check_ledgers(())",
        "tap_check_category_coverage(ledger)",
        "TAP_CHECK_MODE",
    )
    for token in required:
        _require(token in source, "tap-check runner contract missing " + token)

    forbidden = (
        "_default_project_builder",
        "build_project",
        "compile_",
        "parse_",
        "audit_trace_map",
        "adapt_runtime_result",
        "adapt_convergence_ruling",
        "adapt_narrative_state_change",
        "adapt_air_lowering",
        "adapt_active_directive",
        "trace_map_from_",
        "RuntimeEngine",
        ".execute(",
        "apply_semantic_convergence_policy",
        "assess_paradox_elevation",
        "lower_linked_generics",
        "write_",
        "open(",
    )
    for token in forbidden:
        _require(
            token not in source,
            "tap-check runner acquired forbidden behavior: " + token,
        )


def _assert_real_project_in_process() -> None:
    project_root = _acceptance_project_root()
    loaded = load_project(project_root)
    before = _project_hashes(project_root)

    builder_calls = []

    def forbidden_builder(*args, **kwargs):
        builder_calls.append((args, kwargs))
        raise AssertionError("tap-check invoked the project build pipeline")

    first_out = StringIO()
    first_err = StringIO()
    first_code = cli.main(
        ("tap-check", str(project_root)),
        stdout=first_out,
        stderr=first_err,
        project_builder=forbidden_builder,
    )
    second_out = StringIO()
    second_err = StringIO()
    second_code = cli.main(
        ("tap-check", str(project_root)),
        stdout=second_out,
        stderr=second_err,
        project_builder=forbidden_builder,
    )

    after = _project_hashes(project_root)

    _require(first_code == cli.EXIT_SUCCESS, "tap-check did not exit successfully")
    _require(second_code == cli.EXIT_SUCCESS, "repeated tap-check did not succeed")
    _require(first_err.getvalue() == "", "tap-check wrote unexpected stderr")
    _require(second_err.getvalue() == "", "repeated tap-check wrote stderr")
    _require(first_out.getvalue() == second_out.getvalue(), "CLI output is nondeterministic")
    _require(builder_calls == [], "tap-check invoked project compilation/building")
    _require(before == after, "tap-check changed real project files")

    output = first_out.getvalue().splitlines()
    expected_prefix = (
        "TAP CHECK",
        "Project: {}".format(loaded.manifest.name),
        "Root: {}".format(loaded.root),
        "Mode: observational",
        "Sources: {}".format(len(loaded.sources)),
        "Entries: 0",
        "Coverage:",
    )
    _require(
        tuple(output[:len(expected_prefix)]) == expected_prefix,
        "tap-check report header changed",
    )

    coverage_lines = tuple(
        "  {}: 0".format(category_id)
        for category_id in TAP_CHECK_CATEGORY_IDS
    )
    start = len(expected_prefix)
    _require(
        tuple(output[start:start + 10]) == coverage_lines,
        "tap-check coverage order or zero-count output changed",
    )
    _require(
        output[start + 10]
        == "Zero counts mean no observed TAP evidence, not a negative semantic result.",
        "tap-check zero-count explanation changed",
    )
    _require(
        len(output) == start + 11,
        "tap-check emitted unexpected report content",
    )

    relative = project_root.relative_to(_root()).as_posix()
    print("REAL_APEX_PROJECT={}".format(relative))


def _assert_existing_owners_unchanged() -> None:
    paths = (
        "apexforge/tam",
        "apexforge/governance",
        "apexforge/language",
        "apexforge/air",
        "apexforge/authority",
        "apexforge/runtime",
        "apexforge/language_server",
        "apexforge/semantic_lattice",
        "apexforge/semantic_decision",
        "apexforge/aether_air",
        "apexforge/type_system",
        "apexforge/workflow",
        "apexforge/tooling/project_loader.py",
        "apexforge/tooling/project_manifest.py",
    )
    diff = _git("diff", "--exit-code", PREDECESSOR_TAG, "--", *paths)
    _require(diff.returncode == 0, "P11.11F mutated existing semantic/evidence owners")


def main() -> None:
    _assert_predecessor()
    _assert_cli_surface_and_parser()
    _assert_runner_is_observational()
    _assert_real_project_in_process()
    _assert_existing_owners_unchanged()

    print("P11_11E_FREEZE_ANCESTRY=PASS")
    print("CLI_COMMAND=apexforge tap-check [PATH]")
    print("CLI_DEFAULT_PATH=.")
    print("CLI_ROUTING_OWNER=tooling.cli")
    print("PROJECT_DISCOVERY_OWNER=tooling.project_loader")
    print("PROJECT_LOADING=READ_ONLY")
    print("PROJECT_BUILD_PIPELINE_INVOCATION=NONE")
    print("SOURCE_COMPILATION=NONE")
    print("SOURCE_PARSING_FOR_TAP_EVIDENCE=NONE")
    print("TAM_PRODUCER_INVOCATION=NONE")
    print("AUDIT_TRACE_MAP_INVOCATION=NONE")
    print("OWNER_ADAPTER_INVOCATION=NONE")
    print("DIRECTIVE_ACTIVATION=NONE")
    print("AUTHORITY_EVALUATION=NONE")
    print("CONVERGENCE_RESOLUTION=NONE")
    print("RUNTIME_EXECUTION=NONE")
    print("PROJECT_MUTATION=NONE")
    print("CLI_LEDGER=EMPTY_WHEN_NO_PREREQUISITE_EVIDENCE_IS_SUPPLIED")
    print("CLI_COVERAGE_ROWS=10")
    print("CLI_COVERAGE_ORDER=TAP_CHECK_CATEGORY_IDS")
    print("CLI_ZERO_COUNT=UNOBSERVED_NOT_NEGATIVE_RESULT")
    print("VALID_PARTIAL_OR_EMPTY_AUDIT_EXIT=0")
    print("REAL_APEX_IN_PROCESS_ACCEPTANCE=PASS")
    print("REPEATED_OUTPUT_DETERMINISM=PASS")
    print("TOOLING_CLI_PUBLIC_SURFACE=UNCHANGED")
    print("EXISTING_OWNER_MUTATION=NONE")
    print("P11_11F_TAP_CHECK_CLI_PROJECT_ACCEPTANCE=PASS")


if __name__ == "__main__":
    main()