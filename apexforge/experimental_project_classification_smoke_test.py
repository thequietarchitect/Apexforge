"""Experimental canonical project classification smoke test."""

from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from language.narrative_parser import is_narrative_source_document
from tooling.project_loader import (
    PROJECT_KIND_AIR,
    PROJECT_KIND_NARRATIVE,
    load_project,
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def write_project(root: Path, *, name: str, source_name: str, source: str) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / source_name).write_text(source, encoding="utf-8")
    (root / "apexforge.json").write_text(
        json.dumps(
            {
                "schema": 1,
                "name": name,
                "sources": [source_name],
                "entry": name,
            },
            separators=(",", ":"),
        ),
        encoding="utf-8",
    )


def main() -> None:
    require(
        is_narrative_source_document("story Demo {}"),
        "exact story keyword was not recognized as narrative",
    )
    require(
        is_narrative_source_document(" \n\tstory Broken {"),
        "leading whitespace or incomplete narrative changed classification",
    )
    require(
        not is_narrative_source_document("storyline Demo {}"),
        "story identifier boundary was not preserved",
    )
    require(
        not is_narrative_source_document("directive Main {}"),
        "ordinary AIR source was misclassified as narrative",
    )

    with TemporaryDirectory() as directory:
        root = Path(directory)
        air_root = root / "air"
        narrative_root = root / "narrative"

        write_project(
            air_root,
            name="AirProject",
            source_name="main.apex",
            source="directive AirProject {}",
        )
        write_project(
            narrative_root,
            name="NarrativeProject",
            source_name="story.apex",
            source="story NarrativeProject {}",
        )

        air = load_project(air_root)
        narrative = load_project(narrative_root)

        require(
            air.project_kind == PROJECT_KIND_AIR == "air",
            "AIR project classification changed",
        )
        require(
            narrative.project_kind == PROJECT_KIND_NARRATIVE == "narrative",
            "narrative project classification changed",
        )

    print("Narrative lexical classification: PASS")
    print("Loaded AIR project classification: PASS")
    print("Loaded narrative project classification: PASS")
    print("Experimental canonical project classification: PASS")


if __name__ == "__main__":
    main()
