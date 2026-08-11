from __future__ import annotations

import json
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

from tooling.cli import EXIT_SUCCESS, EXIT_USAGE, main


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def invoke(args):
    stdout = StringIO()
    stderr = StringIO()
    code = main(args, stdout=stdout, stderr=stderr)
    return code, stdout.getvalue(), stderr.getvalue()


def write_project(root: Path, source: str) -> None:
    (root / "apexforge.json").write_text(
        json.dumps(
            {
                "schema": 1,
                "name": "SimulateDemo",
                "sources": ["story.apex"],
                "entry": "SimStory",
            }
        ),
        encoding="utf-8",
    )
    (root / "story.apex").write_text(source, encoding="utf-8")


def main_test() -> int:
    source = """story SimStory {
    character Hero

    scene Start {
        title "Start"
        body "The simulation begins."
    }

    scene Middle {
        title "Middle"
        body "The simulation continues."
    }

    scene End {
        title "End"
        body "The simulation ends."
    }

    choice StartChoice {
        scene Start
        path "Continue" {
            destination Middle
        }
    }

    choice MiddleChoice {
        scene Middle
        path "Return" {
            destination Start
        }
        path "Finish" {
            destination End
        }
    }

    timeline MainTimeline {
        scenes [Start, Middle, End]
    }
}
"""

    with TemporaryDirectory(prefix="apexforge-simulate-smoke-") as temporary:
        project = Path(temporary)
        write_project(project, source)

        code, stdout, stderr = invoke(
            ["simulate", str(project), "--observer"]
        )
        require(code == EXIT_SUCCESS, "observer simulation did not succeed")
        require(stderr == "", "observer simulation emitted stderr")
        require(
            "ApexForge narrative simulation" in stdout,
            "simulation header missing",
        )
        require("Step 0: scene:Start" in stdout, "start scene missing")
        require(
            "Observer selected: 1 -> scene:Middle" in stdout,
            "first deterministic transition changed",
        )
        require("Step 1: scene:Middle" in stdout, "middle scene missing")
        require(
            "Observer selected: 2 -> scene:End" in stdout,
            "unvisited-scene  preference changed",
        )
        require("Step 2: scene:End" in stdout, "end scene missing")
        require(
            "Observer stop: no available paths." in stdout,
            "natural observer stop missing",
        )

        code, stdout, stderr = invoke(
            ["simulate", str(project), "--observer", "--max-steps", "1"]
        )
        require(code == EXIT_SUCCESS, "bounded simulation did not succeed")
        require(
            "Observer stop: maximum transition count 1 reached." in stdout,
            "maximum-step stop missing",
        )

        code, stdout, stderr = invoke(["simulate", str(project)])
        require(code == EXIT_USAGE, "missing --observer exit changed")
        require(
            "requires --observer" in stderr,
            "missing --observer diagnostic changed",
        )

        code, stdout, stderr = invoke(
            ["simulate", str(project), "--observer", "--max-steps", "0"]
        )
        require(code == EXIT_USAGE, "invalid --max-steps exit changed")
        require(
            "--max-steps must be a positive integer" in stderr,
            "invalid --max-steps diagnostic changed",
        )

    print("Narrative observer traversal: PASS")
    print("Unvisited-scene deterministic selection: PASS")
    print("Bounded simulation stop: PASS")
    print("Simulation usage boundaries: PASS")
    print("Experimental simulate routing: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main_test())
