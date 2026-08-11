"""Experimental multi-source narrative project/CLI integration contract."""

from __future__ import annotations

from io import StringIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from tooling.cli import (
    EXIT_SUCCESS,
    _run_build,
    _run_check,
    _run_execute,
    _run_simulate,
)
from tooling.narrative_artifact import NARRATIVE_BUILD_ARTIFACT_SCHEMA_V3
from tooling.project_loader import PROJECT_KIND_NARRATIVE, load_project


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    first = """story MultiCli {
    scene Start {
        body "Start."
    }
    timeline Main {
        scenes [Start, End]
    }
}
"""
    second = """story MultiCli {
    scene End {
        body "End."
    }
}
"""

    with TemporaryDirectory() as directory:
        root = Path(directory)
        project_root = root / "project"
        project_root.mkdir()
        (project_root / "01-start.apex").write_text(first, encoding="utf-8")
        (project_root / "02-end.apex").write_text(second, encoding="utf-8")
        (project_root / "apexforge.json").write_text(
            json.dumps(
                {
                    "schema": 1,
                    "name": "MultiCli",
                    "sources": ["01-start.apex", "02-end.apex"],
                    "entry": "MultiCli",
                },
                separators=(",", ":"),
            ),
            encoding="utf-8",
        )

        loaded = load_project(project_root)
        require(
            loaded.project_kind == PROJECT_KIND_NARRATIVE,
            "all-narrative multi-source project was not classified as narrative",
        )
        require(
            tuple(source.name for source in loaded.sources)
            == ("01-start.apex", "02-end.apex"),
            "multi-source narrative manifest order changed",
        )
        print("Multi-source narrative project classification: PASS")

        check_stdout = StringIO()
        require(
            _run_check(
                str(project_root),
                stdout=check_stdout,
                builder=None,
            )
            == EXIT_SUCCESS,
            "multi-source narrative check failed",
        )
        require(
            "ApexForge check passed: MultiCli (2 source(s))."
            in check_stdout.getvalue(),
            "multi-source narrative check reporting changed",
        )
        print("Multi-source narrative check routing: PASS")

        build_path = root / "build.json"
        build_stdout = StringIO()
        require(
            _run_build(
                str(project_root),
                str(build_path),
                None,
                stdout=build_stdout,
            )
            == EXIT_SUCCESS,
            "multi-source narrative build failed",
        )
        value = json.loads(build_path.read_text(encoding="utf-8"))
        require(
            value["project"]["source_count"] == 2
            and [item["path"] for item in value["project"]["sources"]]
            == ["01-start.apex", "02-end.apex"],
            "multi-source narrative build project metadata changed",
        )
        require(
            value["narrative"]["schema"] == NARRATIVE_BUILD_ARTIFACT_SCHEMA_V3
            and value["narrative"]["sources"]
            == ["01-start.apex", "02-end.apex"],
            "multi-source narrative build did not route nested v3 material",
        )
        print("Multi-source narrative build routing: PASS")

        run_stdout = StringIO()
        run_stderr = StringIO()
        require(
            _run_execute(
                str(project_root),
                None,
                stdout=run_stdout,
                stderr=run_stderr,
                builder=None,
                stdin=StringIO(""),
            )
            == EXIT_SUCCESS,
            "multi-source narrative run failed",
        )
        print("Multi-source narrative run routing: PASS")

        simulate_stdout = StringIO()
        require(
            _run_simulate(
                str(project_root),
                observer=True,
                max_steps=1,
                stdout=simulate_stdout,
            )
            == EXIT_SUCCESS,
            "multi-source narrative simulate failed",
        )
        print("Multi-source narrative simulate routing: PASS")

    print("Experimental multi-source narrative CLI integration: PASS")


if __name__ == "__main__":
    main()
