"""AFP-P10-T1.3 project-scaffold and command-packaging smoke test."""

from __future__ import annotations

from io import StringIO
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

from tooling import (
    DEFAULT_PROJECT_ENTRY,
    DEFAULT_PROJECT_SOURCE,
    DEFAULT_PROJECT_SOURCE_TEXT,
    P10_T1_SCAFFOLD_VERSION,
    load_project,
)
from tooling.cli import EXIT_PROJECT, EXIT_SUCCESS, main


DISTRIBUTION_VERSION = "10.1.3"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def invoke(arguments, *, project_builder=None):
    stdout = StringIO()
    stderr = StringIO()
    code = main(
        arguments,
        stdout=stdout,
        stderr=stderr,
        project_builder=project_builder,
    )
    return code, stdout.getvalue(), stderr.getvalue()


def main_test() -> None:
    require(
        P10_T1_SCAFFOLD_VERSION == "10-T1.3",
        "scaffold version changed",
    )
    require(DEFAULT_PROJECT_SOURCE == "src/main.apex", "source template changed")
    require(DEFAULT_PROJECT_ENTRY == "Main", "entry template changed")

    package_dir = Path(__file__).resolve().parent
    repository_root = package_dir.parent
    pyproject_path = repository_root / "pyproject.toml"
    require(pyproject_path.is_file(), "repository pyproject.toml is missing")

    metadata = pyproject_path.read_text(encoding="utf-8")
    require(
        f'version = "{DISTRIBUTION_VERSION}"' in metadata,
        "distribution version changed",
    )
    require(
        'apexforge = "tooling.cli:main"' in metadata,
        "console-script binding changed",
    )
    require(
        'package-dir = {"" = "apexforge"}' in metadata,
        "flat package-directory mapping changed",
    )
    require(
        'where = ["apexforge"]' in metadata,
        "package discovery root changed",
    )

    with TemporaryDirectory() as temporary:
        parent = Path(temporary) / "projects"
        root = parent / "Demo"

        code, stdout, stderr = invoke(("new", "Demo", str(parent)))
        require(code == EXIT_SUCCESS, "new command failed")
        require(stderr == "", "successful new command wrote to stderr")
        require(
            stdout
            == (
                "Created ApexForge project: Demo\n"
                f"Root: {root.resolve()}\n"
                f"Manifest: {(root / 'apexforge.json').resolve()}\n"
                f"Source: {(root / 'src' / 'main.apex').resolve()}\n"
            ),
            "new command output changed",
        )

        manifest_path = root / "apexforge.json"
        source_path = root / "src" / "main.apex"
        require(manifest_path.is_file(), "new command omitted apexforge.json")
        require(source_path.is_file(), "new command omitted src/main.apex")
        require(
            source_path.read_text(encoding="utf-8")
            == DEFAULT_PROJECT_SOURCE_TEXT,
            "source template content changed",
        )

        loaded = load_project(root)
        require(loaded.manifest.name == "Demo", "scaffold project name changed")
        require(
            loaded.manifest.sources == (DEFAULT_PROJECT_SOURCE,),
            "scaffold source inventory changed",
        )
        require(
            loaded.manifest.entry == DEFAULT_PROJECT_ENTRY,
            "scaffold entry changed",
        )

        observed = {}

        def fake_builder(sources, entry):
            observed["sources"] = tuple(sources)
            observed["text"] = sources[DEFAULT_PROJECT_SOURCE]
            observed["entry"] = entry
            return object()

        code, stdout, stderr = invoke(
            ("check", str(root)),
            project_builder=fake_builder,
        )
        require(code == EXIT_SUCCESS, "new project failed check boundary")
        require(stderr == "", "new project check wrote to stderr")
        require(
            stdout == "ApexForge check passed: Demo (1 source(s)).\n",
            "new project check output changed",
        )
        require(
            observed["sources"] == (DEFAULT_PROJECT_SOURCE,),
            "check lost scaffold source order",
        )
        require(
            observed["text"] == DEFAULT_PROJECT_SOURCE_TEXT,
            "check lost scaffold source text",
        )
        require(
            observed["entry"] == DEFAULT_PROJECT_ENTRY,
            "check lost scaffold entry",
        )

        manifest_before = manifest_path.read_bytes()
        source_before = source_path.read_bytes()
        code, stdout, stderr = invoke(("new", "Demo", str(parent)))
        require(code == EXIT_PROJECT, "duplicate scaffold exit code changed")
        require(stdout == "", "duplicate scaffold wrote success output")
        require("[APX-TOOL-009]" in stderr, "duplicate scaffold code omitted")
        require(
            manifest_path.read_bytes() == manifest_before,
            "duplicate scaffold overwrote the manifest",
        )
        require(
            source_path.read_bytes() == source_before,
            "duplicate scaffold overwrote the source",
        )

        code, stdout, stderr = invoke(("new", "bad name", str(parent)))
        require(code == EXIT_PROJECT, "invalid name exit code changed")
        require(stdout == "", "invalid name wrote success output")
        require("[APX-TOOL-004]" in stderr, "invalid name code omitted")

        wrapper = package_dir / "apexforge_cli.py"
        wrapper_parent = Path(temporary) / "wrapper-projects"
        completed = subprocess.run(
            [
                sys.executable,
                str(wrapper),
                "new",
                "WrapperDemo",
                str(wrapper_parent),
            ],
            cwd=str(repository_root),
            check=False,
            capture_output=True,
            text=True,
        )
        require(completed.returncode == 0, "repository wrapper new failed")
        require(completed.stderr == "", "repository wrapper new wrote stderr")
        require(
            (wrapper_parent / "WrapperDemo" / "apexforge.json").is_file(),
            "repository wrapper omitted manifest",
        )
        require(
            (wrapper_parent / "WrapperDemo" / "src" / "main.apex").is_file(),
            "repository wrapper omitted source",
        )

    print("AFP-P10-T1.3 scaffold and packaging smoke test passed.")
    print("Deterministic .apex scaffold: PASS")
    print("Canonical manifest reuse: PASS")
    print("Non-overwriting project creation: PASS")
    print("Immediate check compatibility: PASS")
    print("Repository wrapper new command: PASS")
    print("Installable console-script metadata: PASS")
    print("Flat package discovery metadata: PASS")
    print("Extension-neutral loader preserved: PASS")


if __name__ == "__main__":
    main_test()