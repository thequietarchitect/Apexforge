"""AFP-P10-T1.2 deterministic ApexForge command-line foundation.

The CLI is a thin host adapter. Project discovery and source loading remain in
``tooling.project_loader``; compilation, linking, and validation remain in the
canonical ``language.project`` pipeline.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any, Callable, Mapping, Optional, Sequence, TextIO

from tooling.build_artifact import (
    BUILD_ARTIFACT_SCHEMA,
    BUILD_ARTIFACT_SCHEMA_V2,
    BuildArtifactOutputError,
    construct_build_artifact,
    construct_narrative_build_artifact,
    write_build_artifact_atomic,
)
from tooling.project_loader import PROJECT_KIND_NARRATIVE, LoadedProject, load_project
from tooling.project_manifest import ProjectManifestError
from tooling.project_scaffold import create_project_scaffold


P10_T1_CLI_VERSION = "10-T1.2"
CLI_PROGRAM_NAME = "apexforge"

EXIT_SUCCESS = 0
EXIT_USAGE = 2
EXIT_PROJECT = 10
EXIT_CHECK = 20
EXIT_RUNTIME = 30
EXIT_ARTIFACT_OUTPUT = 40
EXIT_NARRATIVE_REQUEST = 50
EXIT_NARRATIVE_SESSION = 51
EXIT_INTERNAL = 70


class CLIUsageError(ValueError):
    """Invalid command-line invocation without process termination."""


class CLIProjectCheckError(RuntimeError):
    """Canonical project construction failed during ``apexforge check``."""


class CLINarrativeRequestError(ValueError):
    """A narrative request or its canonical build material was invalid."""


class CLINarrativeSessionError(ValueError):
    """A narrative session lifecycle request or material was invalid."""


class _ArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise CLIUsageError(message)


ProjectBuilder = Callable[[Mapping[str, str], Optional[str]], Any]


def _parser() -> _ArgumentParser:
    parser = _ArgumentParser(
        prog=CLI_PROGRAM_NAME,
        description="ApexForge project tooling.",
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="print the ApexForge CLI version and exit",
    )

    commands = parser.add_subparsers(dest="command")

    project = commands.add_parser(
        "project",
        help="show the canonical project manifest and source inventory",
    )
    project.add_argument(
        "path",
        nargs="?",
        default=".",
        help="project directory, source path, or apexforge.json path",
    )

    check = commands.add_parser(
        "check",
        help="compile, link, and validate a project without executing it",
    )
    check.add_argument(
        "path",
        nargs="?",
        default=".",
        help="project directory, source path, or apexforge.json path",
    )

    run = commands.add_parser(
        "run",
        help="build and execute one canonical project entry directive",
    )
    run.add_argument(
        "path",
        nargs="?",
        default=".",
        help="project directory, source path, or apexforge.json path",
    )
    run.add_argument(
        "--entry",
        help="entry directive or narrative story, overriding the manifest entry",
    )
    run.add_argument(
        "--report",
        action="store_true",
        help="append one deterministic human-readable runtime result report",
    )

    simulate = commands.add_parser(
        "simulate",
        help="perform one bounded deterministic narrative simulation",
    )
    simulate.add_argument(
        "path",
        nargs="?",
        default=".",
        help="narrative project directory, source path, or apexforge.json path",
    )
    simulate.add_argument(
        "--observer",
        action="store_true",
        help="observe deterministic narrative state and transition progression",
    )
    simulate.add_argument(
        "--max-steps",
        type=int,
        default=32,
        help="maximum narrative transitions before the bounded simulation stops",
    )

    build = commands.add_parser(
        "build",
        help="write one canonical linked multi-source build artifact",
    )
    build.add_argument(
        "path",
        nargs="?",
        default=".",
        help="project directory, source path, or apexforge.json path",
    )
    build.add_argument(
        "--output",
        required=True,
        help="explicit build-artifact output file",
    )
    build.add_argument(
        "--entry",
        help="entry directive or narrative story, overriding the manifest entry",
    )

    narrative = commands.add_parser(
        "narrative",
        help="execute one explicit narrative choice path from a build artifact",
    )
    narrative.add_argument(
        "artifact",
        help="canonical build artifact containing P11.6F narrative material",
    )
    narrative.add_argument(
        "--request",
        required=True,
        help="explicit one-transition narrative request JSON file",
    )

    session = commands.add_parser(
        "narrative-session",
        help="perform one explicit persistent narrative lifecycle action",
    )
    session_actions = session.add_subparsers(
        dest="session_action",
        required=True,
    )
    for action, help_text in (
        ("create", "create one explicitly initialized narrative session"),
        ("step", "advance one session by one explicit choice path"),
        ("terminate", "explicitly terminate one active narrative session"),
    ):
        action_parser = session_actions.add_parser(action, help=help_text)
        action_parser.add_argument(
            "artifact",
            help="canonical build artifact containing P11.6F material",
        )
        if action != "create":
            action_parser.add_argument(
                "session",
                help="canonical P11.6H narrative session file",
            )
        action_parser.add_argument(
            "--request",
            required=True,
            help=f"explicit narrative session {action} request JSON file",
        )
        action_parser.add_argument(
            "--output",
            required=True,
            help="explicit output path for the resulting session",
        )

    interact = session_actions.add_parser(
        "interact",
        help="interactively operate one existing narrative session",
    )
    interact.add_argument(
        "artifact",
        help="canonical build artifact containing P11.6F material",
    )
    interact.add_argument(
        "session",
        help="existing canonical P11.6H narrative session file",
    )

    new = commands.add_parser(
        "new",
        help="create a deterministic ApexForge project scaffold",
    )
    new.add_argument(
        "name",
        help="project name",
    )
    new.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="parent directory that will receive the project folder",
    )

    return parser


def _default_project_builder(
    sources: Mapping[str, str],
    entry: Optional[str],
) -> Any:
    """Invoke the canonical project pipeline through a lazy import."""

    from language.project import ProjectBuildError, build_project

    try:
        return build_project(sources, entry=entry)
    except ProjectBuildError as exc:
        raise CLIProjectCheckError(str(exc)) from exc


def _write_project_summary(
    project: LoadedProject,
    *,
    stream: TextIO,
) -> None:
    manifest = project.manifest
    print(f"Project: {manifest.name}", file=stream)
    print(f"Manifest: {project.manifest_path}", file=stream)
    print(f"Root: {project.root}", file=stream)
    print(f"Entry: {manifest.entry if manifest.entry is not None else '<none>'}", file=stream)
    print(f"Sources: {len(project.sources)}", file=stream)
    for source in project.sources:
        print(f"  {source.name}", file=stream)


def _run_project(path: str, *, stdout: TextIO) -> int:
    loaded = load_project(Path(path))
    _write_project_summary(loaded, stream=stdout)
    return EXIT_SUCCESS


def _run_new(
    name: str,
    directory: str,
    *,
    stdout: TextIO,
) -> int:
    scaffold = create_project_scaffold(name, Path(directory))
    print(
        f"Created ApexForge project: {scaffold.loaded.manifest.name}",
        file=stdout,
    )
    print(f"Root: {scaffold.root}", file=stdout)
    print(f"Manifest: {scaffold.manifest_path}", file=stdout)
    print(f"Source: {scaffold.source_path}", file=stdout)
    return EXIT_SUCCESS


def _analyze_loaded_narrative_project(loaded: LoadedProject) -> Any:
    # Analyze every declared narrative source in canonical manifest order.
    if loaded.project_kind != PROJECT_KIND_NARRATIVE:
        raise ValueError("loaded project is not narrative")
    if len(loaded.sources) == 1:
        from language.narrative_analysis import analyze_narrative_source

        source = loaded.sources[0]
        return analyze_narrative_source(
            source.source,
            source_name=source.name,
        )

    from language.narrative_project_analysis import (
        analyze_narrative_project_sources,
    )

    return analyze_narrative_project_sources(
        tuple((source.name, source.source) for source in loaded.sources)
    )


def _route_loaded_narrative_build_material(
    loaded: LoadedProject,
    analysis: Any,
    bindings: Any,
) -> Any:
    # Route narrative semantics to v2 single-source or v3 project material.
    if len(loaded.sources) == 1:
        from tooling.narrative_artifact import route_narrative_build_material

        return route_narrative_build_material(
            analysis,
            bindings,
            source_name=loaded.sources[0].name,
        )

    from tooling.narrative_artifact import (
        route_narrative_project_build_material,
    )

    return route_narrative_project_build_material(
        analysis,
        bindings,
        source_names=tuple(source.name for source in loaded.sources),
    )


def _run_check(
    path: str,
    *,
    stdout: TextIO,
    builder: Optional[ProjectBuilder],
) -> int:
    loaded = load_project(Path(path))
    selected_builder = builder or _default_project_builder
    try:
        if loaded.project_kind == PROJECT_KIND_NARRATIVE:
            from runtime.narrative_binding import bind_narrative_story
            from tooling.narrative_project import (
                resolve_narrative_project_entry,
                resolve_narrative_start_scene,
            )

            analysis = _analyze_loaded_narrative_project(loaded)
            story = analysis.semantic_story
            bind_narrative_story(story)
            resolve_narrative_project_entry(story, loaded.manifest.entry)
            resolve_narrative_start_scene(story)
        else:
            selected_builder(
                loaded.source_mapping(),
                loaded.manifest.entry,
            )
    except CLIProjectCheckError:
        raise
    except Exception as exc:
        # Narrative and injected/test builders share the deterministic check boundary.
        raise CLIProjectCheckError(str(exc)) from exc

    print(
        "ApexForge check passed: "
        f"{loaded.manifest.name} "
        f"({len(loaded.sources)} source(s)).",
        file=stdout,
    )
    return EXIT_SUCCESS


def _entry_execution_context(
    build: Any,
    entry_directive: str,
) -> Any:
    """Construct the deny-by-default context for one public entry run."""

    from authority.engine import AuthorityEngine
    from authority.model import AuthorityGrant
    from runtime.context import ExecutionContext
    from runtime.state import StateSnapshot

    directive = next(
        (
            item
            for item in tuple(build.program.directives)
            if item.id == entry_directive
        ),
        None,
    )

    if directive is None:
        raise ValueError(
            f"Resolved entry directive {entry_directive!r} is not linked."
        )

    capability = f"directive.invoke:{directive.name}"
    grant = AuthorityGrant(
        principal=directive.principal,
        capability=capability,
        resource=directive.id,
    )

    return ExecutionContext(
        state=StateSnapshot.from_program_initials(build.program),
        authority=AuthorityEngine.from_grants((grant,)),
    )


def _render_runtime_diagnostics(
    diagnostics: Sequence[Any],
    *,
    stream: TextIO,
) -> None:
    for diagnostic in sorted(tuple(diagnostics)):
        location = diagnostic.node_id or "<runtime>"
        print(
            f"{location} [{diagnostic.code}] {diagnostic.message}",
            file=stream,
        )


def _run_execute(
    path: str,
    entry: Optional[str],
    *,
    stdout: TextIO,
    stderr: TextIO,
    builder: Optional[ProjectBuilder],
    report: bool = False,
    stdin: Optional[TextIO] = None,
) -> int:
    from language.project import ProjectBuildError
    from tools.runtime_report import render_runtime_report

    loaded = load_project(Path(path))
    if loaded.project_kind == PROJECT_KIND_NARRATIVE:
        from tempfile import TemporaryDirectory

        from runtime.narrative_binding import bind_narrative_story
        from tooling.narrative_interactive import interact_narrative_session
        from tooling.narrative_project import (
            resolve_narrative_project_entry,
            resolve_narrative_start_scene,
        )
        from tooling.narrative_session import (
            NarrativeSessionCreateRequest,
            NarrativeSessionError,
            NarrativeSessionOutputError,
            create_narrative_session,
            load_narrative_session_material,
            write_narrative_session_atomic,
        )

        if report:
            raise CLIUsageError("--report is not supported for narrative projects.")

        try:
            analysis = _analyze_loaded_narrative_project(loaded)
            story = analysis.semantic_story
            selected_entry = (
                entry
                if entry is not None
                else loaded.manifest.entry
            )
            resolve_narrative_project_entry(story, selected_entry)
            bindings = bind_narrative_story(story)
            narrative = _route_loaded_narrative_build_material(
                loaded,
                analysis,
                bindings,
            )
            start_scene = resolve_narrative_start_scene(story)
            initial_facts = story.states[0].facts if story.states else ()
            artifact = construct_narrative_build_artifact(
                loaded,
                narrative,
            )

            with TemporaryDirectory(prefix="apexforge-narrative-run-") as temporary:
                temporary_root = Path(temporary)
                artifact_path = temporary_root / "build.json"
                session_path = temporary_root / "session.json"
                write_build_artifact_atomic(artifact, artifact_path)

                material = load_narrative_session_material(artifact_path)
                request = NarrativeSessionCreateRequest(
                    story=story.identity,
                    start_scene=start_scene,
                    facts=tuple(initial_facts),
                )
                session = create_narrative_session(material, request)
                write_narrative_session_atomic(session, session_path)
                interact_narrative_session(
                    artifact_path,
                    session_path,
                    input_stream=(stdin or sys.stdin),
                    output_stream=stdout,
                )
            return EXIT_SUCCESS
        except CLIProjectCheckError:
            raise
        except (NarrativeSessionError, NarrativeSessionOutputError) as exc:
            raise CLINarrativeSessionError(str(exc)) from exc
        except Exception as exc:
            raise CLIProjectCheckError(str(exc)) from exc

    selected_builder = builder or _default_project_builder
    selected_entry = (
        entry
        if entry is not None
        else loaded.manifest.entry
    )

    try:
        build = selected_builder(
            loaded.source_mapping(),
            selected_entry,
        )
    except CLIProjectCheckError:
        raise
    except Exception as exc:
        raise CLIProjectCheckError(str(exc)) from exc

    try:
        resolved_entry = build.resolve_entry()
    except ProjectBuildError as exc:
        raise CLIProjectCheckError(str(exc)) from exc

    context = _entry_execution_context(
        build,
        resolved_entry,
    )
    result = build.execute(
        context,
        entry=resolved_entry,
    )

    if result.diagnostics:
        _render_runtime_diagnostics(
            result.diagnostics,
            stream=stderr,
        )
        return EXIT_RUNTIME

    print(
        f"ApexForge run succeeded: {loaded.manifest.name}",
        file=stdout,
    )
    print(f"Entry: {resolved_entry}", file=stdout)
    print("Runtime diagnostics: 0", file=stdout)
    if report:
        print("", file=stdout)
        print(render_runtime_report(result), file=stdout)
    return EXIT_SUCCESS


def _run_simulate(
    path: str,
    *,
    observer: bool,
    max_steps: int,
    stdout: TextIO,
) -> int:
    # Run one bounded deterministic observer simulation for a narrative project.

    from tempfile import TemporaryDirectory

    from runtime.narrative_binding import bind_narrative_story
    from tooling.narrative_interactive import narrative_interactive_menu
    from tooling.narrative_project import (
        resolve_narrative_project_entry,
        resolve_narrative_start_scene,
    )
    from tooling.narrative_session import (
        NarrativeSessionCreateRequest,
        NarrativeSessionError,
        NarrativeSessionOutputError,
        create_narrative_session,
        load_narrative_session_material,
        step_narrative_session,
    )

    if not observer:
        raise CLIUsageError(
            "experimental narrative simulation requires --observer."
        )
    if type(max_steps) is not int or max_steps < 1:
        raise CLIUsageError("--max-steps must be a positive integer.")

    loaded = load_project(Path(path))
    if loaded.project_kind != PROJECT_KIND_NARRATIVE:
        raise CLIUsageError(
            "simulate currently supports narrative projects only."
        )

    def identity_text(identity: Any) -> str:
        return f"{identity.kind}:{'.'.join(identity.path)}"

    try:
        analysis = _analyze_loaded_narrative_project(loaded)
        story = analysis.semantic_story
        resolve_narrative_project_entry(story, loaded.manifest.entry)
        bindings = bind_narrative_story(story)
        narrative = _route_loaded_narrative_build_material(
            loaded,
            analysis,
            bindings,
        )
        start_scene = resolve_narrative_start_scene(story)
        initial_facts = story.states[0].facts if story.states else ()
        artifact = construct_narrative_build_artifact(
            loaded,
            narrative,
        )

        with TemporaryDirectory(prefix="apexforge-narrative-simulate-") as temporary:
            artifact_path = Path(temporary) / "build.json"
            write_build_artifact_atomic(artifact, artifact_path)
            material = load_narrative_session_material(artifact_path)
            session = create_narrative_session(
                material,
                NarrativeSessionCreateRequest(
                    story=story.identity,
                    start_scene=start_scene,
                    facts=tuple(initial_facts),
                ),
            )

            visited = {session.state.current_scene.path}
            transitions = 0

            print("ApexForge narrative simulation", file=stdout)
            print(f"Project: {loaded.manifest.name}", file=stdout)
            print(f"Story: {identity_text(story.identity)}", file=stdout)
            print("Observer: enabled", file=stdout)
            print(f"Maximum transitions: {max_steps}", file=stdout)

            while True:
                current_scene = session.state.current_scene
                print(
                    f"Step {transitions}: {identity_text(current_scene)}",
                    file=stdout,
                )

                if session.state.termination.is_terminated:
                    print(
                        "Observer stop: narrative terminated "
                        f"({session.state.termination.reason}).",
                        file=stdout,
                    )
                    return EXIT_SUCCESS

                menu = narrative_interactive_menu(material, session)
                print(f"Available paths: {len(menu)}", file=stdout)
                for item in menu:
                    print(
                        f"  {item.number}. {identity_text(item.choice)} "
                        f"path[{item.path_index}] "
                        f"{item.path_label!r} -> "
                        f"{identity_text(item.destination)}",
                        file=stdout,
                    )

                if not menu:
                    print("Observer stop: no available paths.", file=stdout)
                    return EXIT_SUCCESS

                if transitions >= max_steps:
                    print(
                        f"Observer stop: maximum transition count "
                        f"{max_steps} reached.",
                        file=stdout,
                    )
                    return EXIT_SUCCESS

                selected = next(
                    (
                        item
                        for item in menu
                        if item.destination.path not in visited
                    ),
                    menu[0],
                )
                print(
                    f"Observer selected: {selected.number} -> "
                    f"{identity_text(selected.destination)}",
                    file=stdout,
                )

                result = step_narrative_session(
                    material,
                    session,
                    selected.request,
                )
                if not result.execution_result.ok or result.session is None:
                    raise CLINarrativeSessionError(
                        "deterministic simulation transition failed."
                    )

                session = result.session
                visited.add(session.state.current_scene.path)
                transitions += 1
    except CLIProjectCheckError:
        raise
    except CLINarrativeSessionError:
        raise
    except (NarrativeSessionError, NarrativeSessionOutputError) as exc:
        raise CLINarrativeSessionError(str(exc)) from exc
    except Exception as exc:
        raise CLIProjectCheckError(str(exc)) from exc


def _run_build(
    path: str,
    output_path: str,
    entry: Optional[str],
    *,
    stdout: TextIO,
) -> int:
    from language.project import ProjectBuildError

    loaded = load_project(Path(path))
    selected_entry = entry if entry is not None else loaded.manifest.entry
    if loaded.project_kind == PROJECT_KIND_NARRATIVE:
        try:
            from runtime.narrative_binding import bind_narrative_story
            from tooling.narrative_project import resolve_narrative_project_entry

            analysis = _analyze_loaded_narrative_project(loaded)
            story = analysis.semantic_story
            resolve_narrative_project_entry(story, selected_entry)
            bindings = bind_narrative_story(story)
            narrative = _route_loaded_narrative_build_material(
                loaded,
                analysis,
                bindings,
            )
        except CLIProjectCheckError:
            raise
        except Exception as exc:
            raise CLIProjectCheckError(str(exc)) from exc

        try:
            artifact = construct_narrative_build_artifact(
                loaded,
                narrative,
            )
        except ProjectBuildError as exc:
            raise CLIProjectCheckError(str(exc)) from exc
    else:
        build = _default_project_builder(
            loaded.source_mapping(),
            selected_entry,
        )
        try:
            artifact = construct_build_artifact(loaded, build)
        except ProjectBuildError as exc:
            raise CLIProjectCheckError(str(exc)) from exc

    write_build_artifact_atomic(artifact, Path(output_path))

    print(
        f"ApexForge build succeeded: {loaded.manifest.name}",
        file=stdout,
    )
    print(f"Schema: {BUILD_ARTIFACT_SCHEMA_V2 if loaded.project_kind == PROJECT_KIND_NARRATIVE else BUILD_ARTIFACT_SCHEMA}", file=stdout)
    print(
        f"Entry: {artifact.entry if artifact.entry is not None else '<none>'}",
        file=stdout,
    )
    print(f"Sources: {artifact.source_count}", file=stdout)
    print(
        "Fingerprint: "
        f"sha256:{artifact.fingerprint}",
        file=stdout,
    )
    print("Artifact written.", file=stdout)
    return EXIT_SUCCESS


def _run_narrative(
    artifact_path: str,
    request_path: str,
    *,
    stdout: TextIO,
) -> int:
    """Route one explicit request through P11.6F material and P11.6E."""

    from tooling.narrative_execution import (
        NarrativeExecutionRoutingError,
        execute_narrative_request,
        load_narrative_execution_material,
        load_narrative_execution_request,
        narrative_execution_result_bytes,
    )

    try:
        bindings = load_narrative_execution_material(artifact_path)
        request = load_narrative_execution_request(request_path)
    except NarrativeExecutionRoutingError as exc:
        raise CLINarrativeRequestError(str(exc)) from exc

    result = execute_narrative_request(bindings, request)
    stdout.write(narrative_execution_result_bytes(result).decode("utf-8"))
    return EXIT_SUCCESS if result.ok else EXIT_RUNTIME


def _run_narrative_session(
    action: Optional[str],
    artifact_path: str,
    request_path: str,
    output_path: str,
    *,
    session_path: Optional[str],
    stdout: TextIO,
) -> int:
    """Perform exactly one explicit P11.6H lifecycle action."""

    from tooling.narrative_session import (
        NarrativeSessionError,
        NarrativeSessionOutputError,
        create_narrative_session,
        load_narrative_session,
        load_narrative_session_create_request,
        load_narrative_session_material,
        load_narrative_session_step_request,
        load_narrative_session_terminate_request,
        narrative_session_bytes,
        narrative_session_step_result_bytes,
        step_narrative_session,
        terminate_narrative_session,
        write_narrative_session_atomic,
    )

    if action not in ("create", "step", "terminate"):
        raise CLIUsageError("narrative-session requires an explicit action")
    try:
        material = load_narrative_session_material(artifact_path)
        if action == "create":
            request = load_narrative_session_create_request(request_path)
            next_session = create_narrative_session(material, request)
            write_narrative_session_atomic(next_session, output_path)
            stdout.write(narrative_session_bytes(next_session).decode("utf-8"))
            return EXIT_SUCCESS

        if session_path is None:
            raise NarrativeSessionError("invalid_request")
        session = load_narrative_session(session_path)
        if action == "step":
            request = load_narrative_session_step_request(request_path)
            result = step_narrative_session(material, session, request)
            if result.session is not None:
                write_narrative_session_atomic(result.session, output_path)
            stdout.write(
                narrative_session_step_result_bytes(result).decode("utf-8")
            )
            return EXIT_SUCCESS if result.execution_result.ok else EXIT_RUNTIME

        request = load_narrative_session_terminate_request(request_path)
        next_session = terminate_narrative_session(material, session, request)
        write_narrative_session_atomic(next_session, output_path)
        stdout.write(narrative_session_bytes(next_session).decode("utf-8"))
        return EXIT_SUCCESS
    except (NarrativeSessionError, NarrativeSessionOutputError) as exc:
        raise CLINarrativeSessionError(str(exc)) from exc


def _run_narrative_session_interact(
    artifact_path: str,
    session_path: str,
    *,
    stdin: TextIO,
    stdout: TextIO,
) -> int:
    """Run the P11.6I human-driven shell over one existing H session."""

    from tooling.narrative_interactive import interact_narrative_session
    from tooling.narrative_session import (
        NarrativeSessionError,
        NarrativeSessionOutputError,
    )

    try:
        interact_narrative_session(
            artifact_path,
            session_path,
            input_stream=stdin,
            output_stream=stdout,
        )
        return EXIT_SUCCESS
    except (NarrativeSessionError, NarrativeSessionOutputError) as exc:
        raise CLINarrativeSessionError(str(exc)) from exc


def main(
    argv: Optional[Sequence[str]] = None,
    *,
    stdin: Optional[TextIO] = None,
    stdout: Optional[TextIO] = None,
    stderr: Optional[TextIO] = None,
    project_builder: Optional[ProjectBuilder] = None,
) -> int:
    """Run the CLI and return one stable process exit code."""

    output = stdout or sys.stdout
    errors = stderr or sys.stderr
    input_stream = stdin or sys.stdin
    parser = _parser()
    arguments = tuple(sys.argv[1:] if argv is None else argv)

    try:
        namespace = parser.parse_args(arguments)
    except CLIUsageError as exc:
        print(parser.format_usage().rstrip(), file=errors)
        print(f"{CLI_PROGRAM_NAME}: error: {exc}", file=errors)
        return EXIT_USAGE

    if namespace.version:
        print(f"ApexForge CLI {P10_T1_CLI_VERSION}", file=output)
        return EXIT_SUCCESS

    if namespace.command is None:
        parser.print_help(file=errors)
        return EXIT_USAGE

    try:
        if namespace.command == "project":
            return _run_project(namespace.path, stdout=output)
        if namespace.command == "check":
            return _run_check(
                namespace.path,
                stdout=output,
                builder=project_builder,
            )
        if namespace.command == "run":
            return _run_execute(
                namespace.path,
                namespace.entry,
                stdout=output,
                stderr=errors,
                builder=project_builder,
                report=namespace.report,
                stdin=input_stream,
            )
        if namespace.command == "simulate":
            return _run_simulate(
                namespace.path,
                observer=namespace.observer,
                max_steps=namespace.max_steps,
                stdout=output,
            )
        if namespace.command == "build":
            return _run_build(
                namespace.path,
                namespace.output,
                namespace.entry,
                stdout=output,
            )
        if namespace.command == "narrative":
            return _run_narrative(
                namespace.artifact,
                namespace.request,
                stdout=output,
            )
        if namespace.command == "narrative-session":
            if namespace.session_action == "interact":
                return _run_narrative_session_interact(
                    namespace.artifact,
                    namespace.session,
                    stdin=input_stream,
                    stdout=output,
                )
            return _run_narrative_session(
                namespace.session_action,
                namespace.artifact,
                namespace.request,
                namespace.output,
                session_path=getattr(namespace, "session", None),
                stdout=output,
            )
        if namespace.command == "new":
            return _run_new(
                namespace.name,
                namespace.directory,
                stdout=output,
            )
    except CLIUsageError as exc:
        print(parser.format_usage().rstrip(), file=errors)
        print(f"{CLI_PROGRAM_NAME}: error: {exc}", file=errors)
        return EXIT_USAGE
    except ProjectManifestError as exc:
        print(str(exc), file=errors)
        return EXIT_PROJECT
    except CLIProjectCheckError as exc:
        print(str(exc), file=errors)
        return EXIT_CHECK
    except BuildArtifactOutputError as exc:
        print(str(exc), file=errors)
        return EXIT_ARTIFACT_OUTPUT
    except CLINarrativeRequestError as exc:
        print(str(exc), file=errors)
        return EXIT_NARRATIVE_REQUEST
    except CLINarrativeSessionError as exc:
        print(str(exc), file=errors)
        return EXIT_NARRATIVE_SESSION
    except KeyboardInterrupt:
        print("ApexForge command interrupted.", file=errors)
        return 130
    except Exception as exc:
        print(
            f"[APX-CLI-999] {type(exc).__name__}: {exc}",
            file=errors,
        )
        return EXIT_INTERNAL

    print(
        f"[APX-CLI-999] Unsupported command {namespace.command!r}.",
        file=errors,
    )
    return EXIT_INTERNAL


__all__ = (
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
