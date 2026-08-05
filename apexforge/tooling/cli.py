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
    BuildArtifactOutputError,
    construct_build_artifact,
    write_build_artifact_atomic,
)
from tooling.project_loader import LoadedProject, load_project
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
EXIT_INTERNAL = 70


class CLIUsageError(ValueError):
    """Invalid command-line invocation without process termination."""


class CLIProjectCheckError(RuntimeError):
    """Canonical project construction failed during ``apexforge check``."""


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
        help="entry directive, overriding the manifest entry",
    )
    run.add_argument(
        "--report",
        action="store_true",
        help="append one deterministic human-readable runtime result report",
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
        help="entry directive, overriding the manifest entry",
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


def _run_check(
    path: str,
    *,
    stdout: TextIO,
    builder: Optional[ProjectBuilder],
) -> int:
    loaded = load_project(Path(path))
    selected_builder = builder or _default_project_builder

    try:
        selected_builder(
            loaded.source_mapping(),
            loaded.manifest.entry,
        )
    except CLIProjectCheckError:
        raise
    except Exception as exc:
        # Injected/test builders use the same deterministic check boundary.
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
) -> int:
    from language.project import ProjectBuildError
    from tools.runtime_report import render_runtime_report

    loaded = load_project(Path(path))
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
    print(f"Schema: {BUILD_ARTIFACT_SCHEMA}", file=stdout)
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


def main(
    argv: Optional[Sequence[str]] = None,
    *,
    stdout: Optional[TextIO] = None,
    stderr: Optional[TextIO] = None,
    project_builder: Optional[ProjectBuilder] = None,
) -> int:
    """Run the CLI and return one stable process exit code."""

    output = stdout or sys.stdout
    errors = stderr or sys.stderr
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
            )
        if namespace.command == "build":
            return _run_build(
                namespace.path,
                namespace.output,
                namespace.entry,
                stdout=output,
            )
        if namespace.command == "new":
            return _run_new(
                namespace.name,
                namespace.directory,
                stdout=output,
            )
    except ProjectManifestError as exc:
        print(str(exc), file=errors)
        return EXIT_PROJECT
    except CLIProjectCheckError as exc:
        print(str(exc), file=errors)
        return EXIT_CHECK
    except BuildArtifactOutputError as exc:
        print(str(exc), file=errors)
        return EXIT_ARTIFACT_OUTPUT
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
    "CLIUsageError",
    "EXIT_ARTIFACT_OUTPUT",
    "EXIT_CHECK",
    "EXIT_INTERNAL",
    "EXIT_PROJECT",
    "EXIT_RUNTIME",
    "EXIT_SUCCESS",
    "EXIT_USAGE",
    "P10_T1_CLI_VERSION",
    "main",
)
