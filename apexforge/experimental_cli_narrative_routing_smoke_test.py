"""Experimental shared CLI routing smoke test for ordinary AIR and narrative projects."""

from __future__ import annotations

from io import StringIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from tooling.cli import EXIT_SUCCESS, main as cli_main


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def root() -> Path:
    return Path(__file__).resolve().parents[1]


def invoke(arguments, *, stdin_text: str = ""):
    stdout = StringIO()
    stderr = StringIO()
    code = cli_main(
        arguments,
        stdin=StringIO(stdin_text),
        stdout=stdout,
        stderr=stderr,
    )
    return code, stdout.getvalue(), stderr.getvalue()


def test_ordinary_air_cli_surface(temporary_root: Path) -> None:
    project = root() / "examples" / "P11Validation"

    code, stdout, stderr = invoke(("check", str(project)))
    require(code == EXIT_SUCCESS, f"ordinary AIR check failed: {stderr!r}")
    require("ApexForge check passed: P11Validation" in stdout, "ordinary AIR check output changed")
    require(stderr == "", "ordinary AIR check wrote to stderr")

    artifact_path = temporary_root / "ordinary-air.json"
    code, stdout, stderr = invoke(
        ("build", str(project), "--output", str(artifact_path))
    )
    require(code == EXIT_SUCCESS and artifact_path.is_file(), f"ordinary AIR build failed: {stderr!r}")
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    require("narrative" not in artifact, "ordinary AIR build unexpectedly gained narrative material")
    require(artifact["project"]["name"] == "P11Validation", "ordinary AIR project identity changed")
    require(stderr == "", "ordinary AIR build wrote to stderr")

    code, stdout, stderr = invoke(("run", str(project)))
    require(code == EXIT_SUCCESS, f"ordinary AIR run failed: {stderr!r}")
    require("ApexForge run succeeded: P11Validation" in stdout, "ordinary AIR run output changed")
    require(stderr == "", "ordinary AER run wrote to stderr")


def test_narrative_cli_surface(temporary_root: Path) -> None:
    project = temporary_root / "NarrativeCliDemo"
    project.mkdir()
    (project / "apexforge.json").write_text(
        json.dumps(
            {
                "schema": 1,
                "name": "NarrativeCliDemo",
                "sources": ["story.apex"],
                "entry": "CliStory",
            },
            separators=(",", ":"),
        )
        + "\n",
        encoding="utf-8",
    )
    (project / "story.apex").write_text(
        """story CliStory {
    character Hero
    character Guide

    scene Start {
        title "CLI Story"
        body "A road waits."
    }

    scene End {
        title "Arrival"
        body "The road has been chosen."
    }

    dialogue Greeting {
        scene Start
        speaker Guide
        participants [Hero, Guide]
        text "Choose the road."
    }

    choice StartChoice {
        scene Start
        path "Continue" {
            destination End
        }
    }

    narrative_state OpeningState {
        fact Hero.ready = yes
    }

    timeline MainTimeline {
        scenes [Start, End]
    }
}
""",
        encoding="utf-8",
    )

    code, stdout, stderr = invoke(("check", str(project)))
    require(code == EXIT_SUCCESS, f"narrative check failed: {stderr!r}")
    require("ApexForge check passed: NarrativeCliDemo" in stdout, "narrative check output changed")
    require(stderr == "", "narrative check wrote to stderr")

    artifact_path = temporary_root / "narrative.json"
    code, stdout, stderr = invoke(
        ("build", str(project), "--output", str(artifact_path))
    )
    require(code == EXIT_SUCCESS and artifact_path.is_file(), f"narrative build failed: {stderr!r}")
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    require(artifact["project"]["name"] == "NarrativeCliDemo", "narrative project identity changed")
    require(artifact["project"]["sources"][0]["path"] == "story.apex", "narrative source identity changed")
    require(artifact["project"]["entry"] == "directive:CliStory", "narrative compatibility carrier entry changed")
    require(artifact["narrative"]["schema"] == "apexforge.narrative-build-artifact/v2", "narrative artifact schema changed")
    require(len(artifact["air"]["directives"]) == 1, "narrative compatibility carrier count changed")
    require(artifact["air"]["directives"][0]["name"] == "CliStory", "narrative compatibility carrier identity changed")
    require(stderr == "", "narrative build wrote to stderr")

    code, stdout, stderr = invoke(("run", str(project)), stdin_text="1\nquit\n")
    require(code == EXIT_SUCCESS, f"narrative run failed: {stderr!r}")
    require("Scene: scene:Start" in stdout, "narrative run omitted starting scene")
    require('"Continue" -> scene:End' in stdout, "narrative run omitted authored choice")
    require("Scene: scene:End" in stdout, "narrative run did not execute selected choice")
    require(stderr == "", "narrative run wrote to stderr")


def main() -> int:
    with TemporaryDirectory() as temporary_name:
        temporary_root = Path(temporary_name)
        test_ordinary_air_cli_surface(temporary_root)
        print("Ordinary AIR shared CLI surface: PASS")
        test_narrative_cli_surface(temporary_root)
        print("Narrative shared CLI surface: PASS")
    print("Experimental shared check/build/run routing: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
