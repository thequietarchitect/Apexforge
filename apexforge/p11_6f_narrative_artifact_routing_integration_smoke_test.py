"""P11.6F narrative artifact, routing, and integration smoke test."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
import hashlib
import inspect
import json
from pathlib import Path
import subprocess

from language.narrative_analysis import analyze_narrative_source
from language.narrative_model import NarrativeIdentity
from language.project import ProjectBuild, build_project
from runtime.narrative_binding import (
    NarrativeConditionBinding,
    NarrativeConsequenceBinding,
    NarrativeFactAssignment,
    NarrativeFactPredicate,
    bind_narrative_story,
)
from tooling import (
    NARRATIVE_BUILD_ARTIFACT_SCHEMA,
    NarrativeArtifactError,
    NarrativeBuildArtifact,
    route_narrative_build_material,
)
from tooling.build_artifact import (
    BUILD_ARTIFACT_SCHEMA,
    construct_build_artifact,
)
from tooling.project_loader import load_project


EXPECTED_BRANCH = "p11.6f-narrative-artifact-routing-integration"
EXPECTED_PREDECESSOR = "ba038346e04bb1733a43c522eda8dffe54709f0d"
EXPECTED_TAG = "afp-p11.6e-freeze"
THIS_FILE = "apexforge/p11_6f_narrative_artifact_routing_integration_smoke_test.py"
MODULE_FILE = "apexforge/tooling/narrative_artifact.py"
ARTIFACT_FILE = "apexforge/tooling/build_artifact.py"
EXPORT_FILE = "apexforge/tooling/__init__.py"
DOC_FILE = "docs/p11/P11_6F_NARRATIVE_ARTIFACT_ROUTING_INTEGRATION.md"
AUTHORIZED_PATHS = (
    THIS_FILE,
    MODULE_FILE,
    ARTIFACT_FILE,
    EXPORT_FILE,
    DOC_FILE,
)
PROTECTED_FIXTURE_PATHS = (
    "examples/P11Validation/apexforge.json",
    "examples/P11Validation/main.apex",
)
PROTECTED_MAIN_SHA256 = "93662dc3891887288b9646be8ef33fa4fe7d7413b4bb0ad6918d405a4b5045a9"

NARRATIVE_SOURCE = "\n".join(
    (
        "story ArtifactStory {",
        "    character Hero",
        "    scene Start",
        "    scene End",
        "    choice Decide {",
        "        scene Start",
        '        path "Continue" {',
        "            destination End",
        "            condition hero_ready",
        "            consequence mark_done",
        "        }",
        "    }",
        "}",
    )
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def require_raises(exc_type, operation, message: str):
    try:
        operation()
    except exc_type as exc:
        return exc
    raise AssertionError(message)


def git(root: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ("git", *arguments),
        cwd=root,
        check=False,
        text=True,
        encoding="utf-8",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    require(
        completed.returncode == 0,
        f"git {' '.join(arguments)} failed: {completed.stderr.strip()}",
    )
    return completed.stdout.rstrip()


def root() -> Path:
    return Path(__file__).resolve().parents[1]


def make_artifact() -> tuple[NarrativeBuildArtifact, object, object]:
    analysis = analyze_narrative_source(
        NARRATIVE_SOURCE,
        source_name="story.apex",
    )
    hero = NarrativeIdentity("character", ("Hero",))
    bindings = bind_narrative_story(
        analysis.semantic_story,
        condition_bindings=(
            NarrativeConditionBinding(
                "hero_ready",
                NarrativeFactPredicate(hero, "ready", "equals", "yes"),
            ),
        ),
        consequence_bindings=(
            NarrativeConsequenceBinding(
                "mark_done",
                (NarrativeFactAssignment(hero, "done", "yes"),),
            ),
        ),
    )
    artifact = route_narrative_build_material(analysis, bindings)
    return artifact, analysis, bindings


def test_baseline_ownership_and_fixture() -> None:
    repository_root = root()
    require(
        git(repository_root, "branch", "--show-current") == EXPECTED_BRANCH,
        "P11.6F is running on an unexpected branch",
    )
    require(
        git(repository_root, "cat-file", "-t", EXPECTED_TAG) == "tag",
        "P11.6E freeze must be annotated",
    )
    require(
        git(repository_root, "rev-parse", EXPECTED_TAG + "^{}")
        == git(repository_root, "rev-parse", EXPECTED_PREDECESSOR),
        "P11.6E predecessor mismatch",
    )

    status_lines = tuple(
        line
        for line in git(
            repository_root,
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
        ).splitlines()
        if line
    )
    observed_paths = {
        line[3:].replace("\\", "/")
        for line in status_lines
    }
    require(
        observed_paths == set(AUTHORIZED_PATHS) | set(PROTECTED_FIXTURE_PATHS),
        f"unexpected P11.6F ownership/protected-fixture set: {observed_paths!r}",
    )
    fixture = repository_root / "examples/P11Validation/main.apex"
    require(
        hashlib.sha256(fixture.read_bytes()).hexdigest()
        == PROTECTED_MAIN_SHA256,
        "protected main.apex changed",
    )


def test_route_and_artifact_preserve_frozen_material_deterministically() -> None:
    first, analysis, bindings = make_artifact()
    second, second_analysis, second_bindings = make_artifact()

    require(type(first) is NarrativeBuildArtifact, "wrong narrative artifact type")
    require(first.story is analysis.semantic_story, "artifact copied the semantic story")
    require(first.bindings is bindings, "artifact copied the binding set")
    require(first.story.identity.kind == "story", "artifact did not identify a story")
    require(first.bindings.story == first.story.identity, "binding story identity changed")
    require(first == second, "equivalent narrative inputs produced different artifacts")
    require(first.payload() == second.payload(), "narrative payload ordering changed")
    require(
        first.payload()["schema"] == NARRATIVE_BUILD_ARTIFACT_SCHEMA,
        "narrative artifact schema changed",
    )
    require(
        first.payload()["story"]["identity"] == {"kind": "story", "path": ["ArtifactStory"]},
        "narrative story identity was not serialized canonically",
    )
    require(
        second.story == second_analysis.semantic_story
        and second.bindings is second_bindings,
        "repeated route lost canonical frozen material",
    )
    before_story = repr(first.story)
    before_bindings = repr(first.bindings)
    require_raises(
        FrozenInstanceError,
        lambda: setattr(first, "source_name", "changed.apex"),
        "narrative build artifact is mutable",
    )
    require(repr(first.story) == before_story, "artifact route mutated the story")
    require(repr(first.bindings) == before_bindings, "artifact route mutated bindings")


def test_existing_canonical_artifact_route_and_non_narrative_compatibility() -> None:
    repository_root = root()
    loaded = load_project(repository_root / "examples/P11Validation")
    build = build_project(loaded.source_mapping(), entry=loaded.manifest.entry)
    narrative, _, _ = make_artifact()

    historical = construct_build_artifact(loaded, build)
    integrated = construct_build_artifact(
        loaded,
        build,
        narrative_artifact=narrative,
    )
    historical_value = json.loads(historical.content.decode("utf-8"))
    integrated_value = json.loads(integrated.content.decode("utf-8"))
    require(historical.narrative_artifact is None, "non-narrative artifact gained narrative state")
    require("narrative" not in historical_value, "non-narrative artifact routing activated")
    require(historical_value["schema"] == BUILD_ARTIFACT_SCHEMA, "AIR artifact schema changed")
    require(integrated.narrative_artifact is narrative, "associated narrative artifact was not exposed")
    require(integrated_value["narrative"] == narrative.payload(), "narrative artifact was not routed into canonical JSON")
    require(integrated_value["air"] == historical_value["air"], "AIR payload changed during narrative packaging")
    require(integrated_value["project"] == historical_value["project"], "project metadata changed during narrative packaging")
    require(
        inspect.signature(construct_build_artifact).parameters["narrative_artifact"].default is None,
        "canonical artifact extension did not preserve its default",
    )

    legacy = build_project({"legacy.apex": "directive Main {}"}, entry="Main")
    heterogeneous = build_project(
        {
            "all.apex": "\n".join(
                (
                    "directive Main {}",
                    "function Helper() { return 0 }",
                    "workflow Flow {}",
                    "authority Aegis {}",
                    "principal Operator {}",
                    "role Architect {}",
                )
            )
        },
        entry="Main",
    )
    require(
        legacy.program.directives[0].id == "directive:Main"
        and len(heterogeneous.program.functions) == 1
        and len(heterogeneous.program.workflows) == 1,
        "legacy/module/AIR project compilation changed",
    )
    require(not hasattr(build, "narrative_artifact"), "ProjectBuild was redesigned for narrative state")


def test_boundaries_and_deterministic_failures() -> None:
    artifact, analysis, bindings = make_artifact()
    module_text = (root() / MODULE_FILE).read_text(encoding="utf-8")
    for forbidden in (
        "transition_narrative_choice",
        "execute_narrative_choice",
        "terminate_narrative",
        "NarrativeExecutionState",
        "NarrativeExecutionResult",
        "RuntimeEngine",
        "AIRProgram",
    ):
        require(forbidden not in module_text, f"artifact module crossed boundary via {forbidden!r}")

    require("initial_scene" not in artifact.payload(), "artifact inferred an initial scene")
    require("selected_choice" not in artifact.payload(), "artifact selected a choice")
    require("trace" not in artifact.payload(), "artifact duplicated P11.6E trace material")
    require("diagnostics" not in artifact.payload(), "artifact duplicated P11.6E diagnostics")
    require("termination" not in artifact.payload(), "artifact serialized runtime termination")
    require(
        route_narrative_build_material(analysis, bindings).payload() == artifact.payload(),
        "repeated route was not deterministic",
    )

    require_raises(
        TypeError,
        lambda: route_narrative_build_material(object(), bindings),
        "absent/malformed narrative material used an ad hoc route",
    )
    other = analyze_narrative_source("story Other {}", source_name="other.apex")
    other_bindings = bind_narrative_story(other.semantic_story)
    error = require_raises(
        NarrativeArtifactError,
        lambda: route_narrative_build_material(analysis, other_bindings),
        "mismatched narrative material was accepted",
    )
    require("story" in str(error) and "bindings" in str(error), "mismatch diagnostic was not deterministic")
    require_raises(
        Exception,
        lambda: analyze_narrative_source("story Broken {", source_name="broken.apex"),
        "malformed narrative source was silently routed",
    )


def main_test() -> None:
    test_baseline_ownership_and_fixture()
    test_route_and_artifact_preserve_frozen_material_deterministically()
    test_existing_canonical_artifact_route_and_non_narrative_compatibility()
    test_boundaries_and_deterministic_failures()
    print("AFP-P11.6F narrative artifact/routing/integration smoke test passed.")
    print("Frozen P11.6E predecessor, exact ownership, and protected fixture: PASS")
    print("Deterministic immutable narrative artifact routing: PASS")
    print("Existing ProjectBuild, AIR, and canonical artifact compatibility: PASS")
    print("No runtime execution, automatic choice, initial-scene, or termination behavior: PASS")


if __name__ == "__main__":
    main_test()
