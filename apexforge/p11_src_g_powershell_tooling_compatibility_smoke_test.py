"""P11-SRC-G PowerShell and CLI semantic-decision tooling compatibility."""

from __future__ import annotations

from io import StringIO
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

from language.semantic_decision_analysis import analyze_semantic_decision_source
from tooling.cli import EXIT_CHECK, EXIT_SUCCESS, main
from tooling.project_loader import (
    PROJECT_KIND_AIR,
    PROJECT_KIND_NARRATIVE,
    PROJECT_KIND_SEMANTIC_DECISION,
    load_project,
)


SEMANTIC_SOURCE_A = """\
decision ToolingDecision {
    candidate KeepOpen when routeOpen
    candidate Destroy
    incompatible KeepOpen, Destroy
    converge using "rank.explicit-order" {
        KeepOpen
        Destroy
    }
    paradox elevate
        requires information_loss
}
"""

SEMANTIC_SOURCE_B = """\
decision SecondaryDecision {
    candidate Alpha
    candidate Beta
    converge using "compose.all-admissible" {
        Alpha
        Beta
    }
}
"""

INVALID_SEMANTIC_SOURCE = """\
decision Broken {
    candidate
}
"""

AIR_SOURCE = "directive AirMain {}\n"

NARRATIVE_SOURCE = """\
story RoutingStory {
    character Hero
    scene Start
    scene End
    choice Decide {
        scene Start
        path "Continue" {
            destination End
        }
    }
    timeline Main {
        scenes [Start, End]
    }
}
"""


def _write_manifest(root, name, sources, entry=None):
    (root / "apexforge.json").write_text(
        json.dumps(
            {
                "schema": 1,
                "name": name,
                "sources": list(sources),
                "entry": entry,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def _write_project(
    root,
    *,
    name,
    source,
    source_name="main.apex",
    entry=None
):
    root.mkdir(parents=True, exist_ok=True)
    (root / source_name).write_text(source, encoding="utf-8")
    _write_manifest(root, name, (source_name,), entry=entry)


def _invoke(arguments, *, project_builder=None):
    stdout = StringIO()
    stderr = StringIO()
    code = main(
        tuple(arguments),
        stdout=stdout,
        stderr=stderr,
        project_builder=project_builder,
    )
    return code, stdout.getvalue(), stderr.getvalue()


def main_test():
    assert PROJECT_KIND_AIR == "air"
    assert PROJECT_KIND_NARRATIVE == "narrative"
    assert PROJECT_KIND_SEMANTIC_DECISION == "semantic_decision"

    with TemporaryDirectory(prefix="apexforge-src-g-") as temporary:
        root = Path(temporary)
        decision_root = root / "decision"
        decision_multi_root = root / "decision-multi"
        invalid_root = root / "invalid"
        air_root = root / "air"
        narrative_root = root / "narrative"
        mixed_root = root / "mixed"

        _write_project(
            decision_root,
            name="SemanticDecisionTooling",
            source=SEMANTIC_SOURCE_A,
        )
        _write_project(
            invalid_root,
            name="InvalidSemanticDecisionTooling",
            source=INVALID_SEMANTIC_SOURCE,
        )
        _write_project(
            air_root,
            name="AirTooling",
            source=AIR_SOURCE,
            entry="AirMain",
        )
        _write_project(
            narrative_root,
            name="NarrativeTooling",
            source=NARRATIVE_SOURCE,
            entry="RoutingStory",
        )

        decision_multi_root.mkdir(parents=True)
        (decision_multi_root / "a.apex").write_text(
            SEMANTIC_SOURCE_A,
            encoding="utf-8",
        )
        (decision_multi_root / "b.apex").write_text(
            SEMANTIC_SOURCE_B,
            encoding="utf-8",
        )
        _write_manifest(
            decision_multi_root,
            "SemanticDecisionMulti",
            ("a.apex", "b.apex"),
        )

        mixed_root.mkdir(parents=True)
        (mixed_root / "a.apex").write_text(
            SEMANTIC_SOURCE_A,
            encoding="utf-8",
        )
        (mixed_root / "b.apex").write_text(
            "directive MixedMain {}\n",
            encoding="utf-8",
        )
        _write_manifest(
            mixed_root,
            "MixedBoundary",
            ("a.apex", "b.apex"),
            entry="MixedMain",
        )

        decision_loaded = load_project(decision_root)
        decision_multi_loaded = load_project(decision_multi_root)
        invalid_loaded = load_project(invalid_root)
        air_loaded = load_project(air_root)
        narrative_loaded = load_project(narrative_root)
        mixed_loaded = load_project(mixed_root)

        assert decision_loaded.project_kind == PROJECT_KIND_SEMANTIC_DECISION
        assert (
            decision_multi_loaded.project_kind
            == PROJECT_KIND_SEMANTIC_DECISION
        )
        assert invalid_loaded.project_kind == PROJECT_KIND_SEMANTIC_DECISION
        assert air_loaded.project_kind == PROJECT_KIND_AIR
        assert narrative_loaded.project_kind == PROJECT_KIND_NARRATIVE
        assert mixed_loaded.project_kind == PROJECT_KIND_AIR

        expected_analysis = analyze_semantic_decision_source(
            decision_loaded.sources[0].source,
            source_name=decision_loaded.sources[0].name,
        )

        builder_calls = []

        def forbidden_builder(sources, entry):
            builder_calls.append((tuple(sources), entry))
            raise AssertionError(
                "semantic-decision check reached the AIR ProjectBuilder"
            )

        checked = _invoke(
            ("check", str(decision_root)),
            project_builder=forbidden_builder,
        )
        assert checked == (
            EXIT_SUCCESS,
            "ApexForge check passed: SemanticDecisionTooling (1 source(s)).\n",
            "",
        )
        assert builder_calls == []

        multi_checked = _invoke(
            ("check", str(decision_multi_root)),
            project_builder=forbidden_builder,
        )
        assert multi_checked == (
            EXIT_SUCCESS,
            "ApexForge check passed: SemanticDecisionMulti (2 source(s)).\n",
            "",
        )
        assert builder_calls == []

        repeated = _invoke(
            ("check", str(decision_root)),
            project_builder=forbidden_builder,
        )
        assert repeated == checked
        assert builder_calls == []

        invalid = _invoke(
            ("check", str(invalid_root)),
            project_builder=forbidden_builder,
        )
        assert invalid[0] == EXIT_CHECK
        assert invalid[1] == ""
        assert "APX-SEMANTIC-DECISION-SYNTAX" in invalid[2]
        assert "main.apex" in invalid[2]
        assert "APX-PARSE-002" not in invalid[2]
        assert builder_calls == []

        observed = {}

        def air_builder(sources, entry):
            observed["names"] = tuple(sources)
            observed["source"] = sources["main.apex"]
            observed["entry"] = entry
            return object()

        air_check = _invoke(
            ("check", str(air_root)),
            project_builder=air_builder,
        )
        assert air_check == (
            EXIT_SUCCESS,
            "ApexForge check passed: AirTooling (1 source(s)).\n",
            "",
        )
        assert observed == {
            "names": ("main.apex",),
            "source": AIR_SOURCE,
            "entry": "AirMain",
        }

        mixed_observed = {}

        def mixed_builder(sources, entry):
            mixed_observed["names"] = tuple(sources)
            mixed_observed["entry"] = entry
            return object()

        mixed_check = _invoke(
            ("check", str(mixed_root)),
            project_builder=mixed_builder,
        )
        assert mixed_check == (
            EXIT_SUCCESS,
            "ApexForge check passed: MixedBoundary (2 source(s)).\n",
            "",
        )
        assert mixed_observed == {
            "names": ("a.apex", "b.apex"),
            "entry": "MixedMain",
        }

        narrative_check = _invoke(
            ("check", str(narrative_root)),
            project_builder=forbidden_builder,
        )
        assert narrative_check == (
            EXIT_SUCCESS,
            "ApexForge check passed: NarrativeTooling (1 source(s)).\n",
            "",
        )
        assert builder_calls == []

        package_dir = Path(__file__).resolve().parent
        wrapper = package_dir / "apexforge_cli.py"
        completed = subprocess.run(
            [sys.executable, str(wrapper), "check", str(decision_root)],
            cwd=str(package_dir.parent),
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        assert completed.returncode == EXIT_SUCCESS
        assert completed.stdout == (
            "ApexForge check passed: SemanticDecisionTooling (1 source(s)).\n"
        )
        assert completed.stderr == ""

        actual_analysis = analyze_semantic_decision_source(
            decision_loaded.sources[0].source,
            source_name=decision_loaded.sources[0].name,
        )
        assert actual_analysis == expected_analysis
        assert tuple(
            item.identity
            for item in actual_analysis.semantic_bridge.decisions
        ) == ("ToolingDecision",)

    print("P11_SRC_F_CAPABILITY_REGRESSION=PASS")
    print("P11_SRC_G_POWERSHELL_TOOLING_COMPATIBILITY=PASS")
    print("SEMANTIC_DECISION_PROJECT_CLASSIFICATION=PASS")
    print("MULTI_SOURCE_SEMANTIC_DECISION_CLASSIFICATION=PASS")
    print("MALFORMED_DECISION_CLASSIFICATION=PASS")
    print("MIXED_SOURCE_AIR_BOUNDARY=PASS")
    print("SEMANTIC_DECISION_CHECK_SUCCESS=PASS")
    print("SEMANTIC_DECISION_MULTI_CHECK_SUCCESS=PASS")
    print("SEMANTIC_DECISION_CHECK_DETERMINISM=PASS")
    print("SEMANTIC_DECISION_DIAGNOSTIC_ROUTING=PASS")
    print("AIR_PROJECTBUILDER_PRESERVED=PASS")
    print("NARRATIVE_ROUTING_PRESERVED=PASS")
    print("REPOSITORY_CLI_WRAPPER=PASS")
    print("F_ANALYSIS_EQUIVALENCE=PASS")
    print("CONDITION_EVALUATION=NONE")
    print("CONVERGENCE_RESOLUTION=NONE")
    print("PARADOX_ASSESSMENT=NONE")
    print("P11_10_VALIDATION=NONE")
    print("AIR_COMPILER_MUTATION=NONE")
    print("RUNTIME_EXECUTION=NONE")


if __name__ == "__main__":
    main_test()