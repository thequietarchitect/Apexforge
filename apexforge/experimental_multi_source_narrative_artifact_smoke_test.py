"""Experimental multi-source native narrative build-artifact contract."""

from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from language.narrative_analysis import analyze_narrative_source
from language.narrative_project_analysis import analyze_narrative_project_sources
from runtime.narrative_binding import bind_narrative_story
from tooling.build_artifact import (
    BUILD_ARTIFACT_SCHEMA_V2,
    construct_narrative_build_artifact,
    write_build_artifact_atomic,
)
from tooling.narrative_artifact import (
    NARRATIVE_BUILD_ARTIFACT_SCHEMA,
    NARRATIVE_BUILD_ARTIFACT_SCHEMA_V3,
    NarrativeProjectBuildArtifact,
    route_narrative_build_material,
    route_narrative_project_build_material,
)
from tooling.narrative_execution import load_narrative_execution_material
from tooling.narrative_session import load_narrative_session_material
from tooling.project_loader import load_project


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    first = """story SplitArtifact {
    character Traveler
    scene Start {
        body "Begin."
    }
}
"""
    second = """story SplitArtifact {
    scene End {
        body "End."
    }
    choice Advance {
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
    with TemporaryDirectory() as directory:
        root = Path(directory)
        project_root = root / "multi"
        project_root.mkdir()
        (project_root / "01-start.apex").write_text(first, encoding="utf-8")
        (project_root / "02-end.apex").write_text(second, encoding="utf-8")
        (project_root / "apexforge.json").write_text(
            json.dumps(
                {
                    "schema": 1,
                    "name": "SplitArtifact",
                    "sources": ["01-start.apex", "02-end.apex"],
                    "entry": "SplitArtifact",
                },
                separators=(",", ":"),
            ),
            encoding="utf-8",
        )

        loaded = load_project(project_root)
        analysis = analyze_narrative_project_sources(
            (
                ("01-start.apex", first),
                ("02-end.apex", second),
            )
        )
        bindings = bind_narrative_story(analysis.semantic_story)
        narrative = route_narrative_project_build_material(
            analysis,
            bindings,
            source_names=("01-start.apex", "02-end.apex"),
        )
        require(
            type(narrative) is NarrativeProjectBuildArtifact,
            "multi-source routing did not return the project artifact sibling type",
        )

        artifact = construct_narrative_build_artifact(loaded, narrative)
        value = json.loads(artifact.content.decode("utf-8"))
        require(
            value["schema"] == BUILD_ARTIFACT_SCHEMA_V2,
            "multi-source native top-level schema changed",
        )
        require(
            value["project"]["source_count"] == 2
            and [item["path"] for item in value["project"]["sources"]]
            == ["01-start.apex", "02-end.apex"],
            "multi-source top-level project metadata changed",
        )
        require(
            value["narrative"]["schema"]
            == NARRATIVE_BUILD_ARTIFACT_SCHEMA_V3
            == "apexforge.narrative-build-artifact/v3",
            "multi-source nested narrative schema changed",
        )
        require(
            frozenset(value["narrative"])
            == frozenset(("schema", "sources", "story", "bindings")),
            "multi-source nested narrative shape changed",
        )
        require(
            value["narrative"]["sources"]
            == ["01-start.apex", "02-end.apex"],
            "multi-source nested source order changed",
        )
        require(
            artifact.narrative_artifact == narrative,
            "top-level artifact lost the multi-source in-memory artifact",
        )

        artifact_path = root / "multi-build.json"
        write_build_artifact_atomic(artifact, artifact_path)
        require(
            load_narrative_execution_material(artifact_path) == bindings,
            "execution loader rejected nested narrative v3",
        )
        material = load_narrative_session_material(artifact_path)
        require(
            material.story == analysis.semantic_story.identity,
            "session loader rejected nested narrative v3",
        )
        print("Multi-source nested narrative v3 artifact: PASS")
        print("Multi-source execution/session artifact loading: PASS")

        single_analysis = analyze_narrative_source(
            """story SingleArtifact {
    scene Only
    timeline Main {
        scenes [Only]
    }
}
""",
            source_name="single.apex",
        )
        single_bindings = bind_narrative_story(single_analysis.semantic_story)
        single = route_narrative_build_material(
            single_analysis,
            single_bindings,
            source_name="single.apex",
        )
        single_payload = single.payload()
        require(
            single_payload["schema"] == NARRATIVE_BUILD_ARTIFACT_SCHEMA,
            "single-source nested v2 schema changed",
        )
        require(
            frozenset(single_payload)
            == frozenset(("schema", "source", "story", "bindings"))
            and single_payload["source"] == "single.apex"
            and "sources" not in single_payload,
            "single-source nested v2 shape changed",
        )
        print("Single-source nested narrative v2 compatibility: PASS")

    print("Experimental multi-source narrative artifact contract: PASS")


if __name__ == "__main__":
    main()
