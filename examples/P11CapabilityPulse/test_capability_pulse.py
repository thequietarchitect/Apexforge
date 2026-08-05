"""Visual Studio-compatible end-to-end P11 Capability Pulse test."""

from __future__ import annotations

from io import StringIO
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from unittest.mock import patch


PROJECT_ROOT = Path(__file__).resolve().parent
REPOSITORY_ROOT = PROJECT_ROOT.parents[1]
PACKAGE_ROOT = REPOSITORY_ROOT / "apexforge"

if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from air.serialization import air_to_dict
from language.project import build_project
from tooling.cli import main as cli_main
from tooling.project_loader import load_project
from workflow.air_runner import build_default_context


CANONICAL_PULSE = (
    "VARENIC-CREST-PULSE: APEXFORGE-P11 / TAM-v3 / "
    "QV-AETHER / STORY-SEMANTICS / APEXMOTION"
)

EXPECTED_SOURCE_NAMES = {
    "src/continuity_architect.apex",
    "src/continuity_core.apex",
    "src/continuity_flow.apex",
    "src/foundation.apex",
    "src/main.apex",
    "src/math.apex",
    "src/observer.apex",
    "src/operator.apex",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def invoke_cli(arguments: tuple[str, ...]):
    stdout = StringIO()
    stderr = StringIO()
    code = cli_main(
        arguments,
        stdout=stdout,
        stderr=stderr,
    )
    return code, stdout.getvalue(), stderr.getvalue()


def repository_status() -> str:
    completed = subprocess.run(
        [
            "git",
            "status",
            "--porcelain=v2",
            "--untracked-files=all",
        ],
        cwd=REPOSITORY_ROOT,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
    )
    require(
        completed.stderr == "",
        "git status wrote unexpected stderr",
    )
    return completed.stdout


def repository_bytecode_state() -> tuple[tuple[str, int, int], ...]:
    values: list[tuple[str, int, int]] = []

    for path in REPOSITORY_ROOT.rglob("*"):
        if (
            not path.is_file()
            or path.suffix.casefold() not in {".pyc", ".pyo"}
        ):
            continue

        details = path.stat()
        values.append(
            (
                path.relative_to(REPOSITORY_ROOT).as_posix(),
                details.st_size,
                details.st_mtime_ns,
            )
        )

    return tuple(sorted(values))


def main() -> None:
    original_directory = Path.cwd().resolve()
    status_before = repository_status()
    bytecode_before = repository_bytecode_state()

    require(
        sys.dont_write_bytecode,
        "run with -B or PYTHONDONTWRITEBYTECODE=1",
    )

    def forbidden_network(*_args, **_kwargs):
        raise AssertionError(
            "capability-pulse demonstration attempted network access"
        )

    with patch(
        "socket.create_connection",
        side_effect=forbidden_network,
    ), patch(
        "socket.socket",
        side_effect=forbidden_network,
    ):
        loaded = load_project(PROJECT_ROOT)
        require(
            set(loaded.source_mapping()) == EXPECTED_SOURCE_NAMES,
            "Visual Studio source inventory changed",
        )

        project = build_project(
            loaded.source_mapping(),
            entry=loaded.manifest.entry,
        )
        program = project.program

        require(
            {item.id for item in program.functions}
            == {"function:strengthen"},
            "pure function declaration or identity changed",
        )
        require(
            {item.id for item in program.directives}
            == {"directive:Observer", "directive:Main"},
            "directive declarations or identities changed",
        )
        require(
            {item.id for item in program.workflows}
            == {"workflow:ContinuityFlow"},
            "workflow declaration was not promoted",
        )
        require(
            {item.name for item in program.authorities}
            == {"Foundation", "ContinuityCore"},
            "authority declarations changed",
        )

        authority_by_name = {
            item.name: item
            for item in program.authorities
        }
        require(
            authority_by_name["ContinuityCore"].inherits
            == ("Foundation",),
            "authority inheritance was not preserved",
        )
        require(
            {item.name for item in program.roles}
            == {"ContinuityArchitect"},
            "role declaration was not promoted",
        )
        require(
            any(
                item.id == "principal:Operator"
                and item.roles == ("ContinuityArchitect",)
                for item in program.principals
            ),
            "explicit principal role assignment was not preserved",
        )
        require(
            tuple(
                item.capability
                for item in program.requirements
            )
            == ("Execute",),
            "directive requirement was not preserved",
        )

        workflow = next(
            item
            for item in program.workflows
            if item.id == "workflow:ContinuityFlow"
        )
        require(
            tuple(
                item.target
                for item in workflow.invocations
            )
            == ("Main",),
            "workflow invocation target changed",
        )
        require(
            set(
                project.module_graph.direct_imports(
                    "continuity.main"
                )
            )
            == {
                "continuity.core",
                "continuity.math",
                "continuity.observer",
            },
            "Main module imports were not preserved",
        )
        require(
            project.module_graph.direct_imports(
                "continuity.core"
            )
            == ("continuity.foundation",),
            "authority inheritance import changed",
        )
        require(
            project.resolve_entry() == "directive:Main",
            "entry resolution changed",
        )
        require(
            air_to_dict(project.program)
            == air_to_dict(project.verified.program),
            "verified AIR differs from the linked program",
        )

        context = build_default_context(program)
        result = project.execute(
            context,
            entry="Main",
        )

        require(
            result.ok,
            "runtime failed: " + repr(result.diagnostics),
        )
        require(
            result.final_state.get_int("pulse_count") == 7,
            "function/local/conditional execution produced the wrong pulse count",
        )
        require(
            result.final_state.get_int("observer_count") == 3,
            "linked directive invocation produced the wrong observer count",
        )
        require(
            len(result.delta.events) == 2,
            "expected Main and Observer to emit one event each",
        )
        require(
            not result.diagnostics,
            "runtime produced diagnostics: " + repr(result.diagnostics),
        )

        project_cli = invoke_cli(
            ("project", str(PROJECT_ROOT))
        )
        check_cli = invoke_cli(
            ("check", str(PROJECT_ROOT))
        )
        run_main_cli = invoke_cli(
            ("run", str(PROJECT_ROOT))
        )
        run_observer_cli = invoke_cli(
            (
                "run",
                str(PROJECT_ROOT),
                "--entry",
                "Observer",
            )
        )

        with TemporaryDirectory(
            prefix="apexforge-capability-pulse-"
        ) as temporary:
            artifact = Path(temporary) / "artifact.json"
            build_cli = invoke_cli(
                (
                    "build",
                    str(PROJECT_ROOT),
                    "--output",
                    str(artifact),
                )
            )
            require(
                artifact.is_file()
                and artifact.read_bytes(),
                "CLI build did not produce an artifact",
            )

        require(
            project_cli[0] == 0
            and "Project: P11CapabilityPulse\n"
            in project_cli[1]
            and "Sources: 8\n" in project_cli[1]
            and project_cli[2] == "",
            "CLI project inventory failed: "
            + repr(project_cli),
        )
        require(
            check_cli
            == (
                0,
                "ApexForge check passed: "
                "P11CapabilityPulse (8 source(s)).\n",
                "",
            ),
            "CLI check failed: " + repr(check_cli),
        )
        require(
            run_main_cli
            == (
                30,
                "",
                (
                    "directive:Observer [RUN001] authority denied: "
                    "principal:Observer lacks "
                    "directive.invoke:Observer on "
                    "directive:Observer\n"
                ),
            ),
            "CLI downstream authority boundary changed: "
            + repr(run_main_cli),
        )
        require(
            run_observer_cli[0] == 0
            and (
                "ApexForge run succeeded: "
                "P11CapabilityPulse\n"
            )
            in run_observer_cli[1]
            and (
                "Entry: directive:Observer\n"
                in run_observer_cli[1]
            )
            and (
                "Runtime diagnostics: 0\n"
                in run_observer_cli[1]
            )
            and run_observer_cli[2] == "",
            "CLI selected-entry run failed: "
            + repr(run_observer_cli),
        )
        require(
            build_cli[0] == 0
            and (
                "ApexForge build succeeded: "
                "P11CapabilityPulse\n"
            )
            in build_cli[1]
            and (
                "Schema: apexforge.build-artifact/v1\n"
            )
            in build_cli[1]
            and build_cli[2] == "",
            "CLI build failed: " + repr(build_cli),
        )

    require(
        Path.cwd().resolve() == original_directory,
        "demonstration changed the working directory",
    )
    require(
        repository_status() == status_before,
        "demonstration changed repository status",
    )
    require(
        repository_bytecode_state() == bytecode_before,
        "demonstration changed repository bytecode state",
    )

    print("AFP P11 Capability Pulse Visual Studio project passed.")
    print("Eight single-declaration module sources: PASS")
    print("Visual Studio one-node diagnostic compatibility: PASS")
    print("All six top-level declaration families: PASS")
    print("Module and import graph: PASS")
    print("Authority inheritance, role, principal, and requirement graph: PASS")
    print("Pure function, local binding, conditional, and return: PASS")
    print("State set/add, message, event emission, and directive invocation: PASS")
    print("Workflow declaration and entry resolution: PASS")
    print("CLI project/check/build: PASS")
    print("CLI Main downstream authority denial: PASS")
    print("CLI explicit Observer entry execution: PASS")
    print("Final pulse_count: 7")
    print("Final observer_count: 3")
    print("Emitted events: 2")
    print(f"Canonical pulse: {CANONICAL_PULSE}")
    print("Network, Git, bytecode, cwd, and source-tree no-op boundary: PASS")


if __name__ == "__main__":
    main()
