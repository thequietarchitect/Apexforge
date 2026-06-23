"""AIR JSON serialization utilities."""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from pathlib import Path


def _to_data(value):
    if is_dataclass(value):
        return {
            key: _to_data(item)
            for key, item in asdict(value).items()
        }

    if isinstance(value, tuple):
        return [_to_data(item) for item in value]

    if isinstance(value, list):
        return [_to_data(item) for item in value]

    if isinstance(value, dict):
        return {
            key: _to_data(item)
            for key, item in value.items()
        }

    return value


def air_to_dict(program) -> dict:
    return _to_data(program)


def save_air_json(program, path: str) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)

    output.write_text(
        json.dumps(air_to_dict(program), indent=2),
        encoding="utf-8",
    )

def load_air_dict(path: str) -> dict:
    input_path = Path(path)

    return json.loads(
        input_path.read_text(encoding="utf-8")
    )

from air.model import (
    AIRDirective,
    AIRProgram,
    EventDefinition,
    EventEmission,
    StateAssignment,
    StateDefinition,
    Fact,
)
from authority.model import AuthorityCheck, Principal
from causality.model import CausalDecision, CausalPath


def _facts_from_data(items) -> tuple[Fact, ...]:
    return tuple(Fact(item["key"], item["value"]) for item in items)


def air_from_dict(data: dict) -> AIRProgram:
    return AIRProgram(
        version=data["version"],
        principals=tuple(
            Principal(**item)
            for item in data["principals"]
        ),
        states=tuple(
            StateDefinition(**item)
            for item in data["states"]
        ),
        events=tuple(
            EventDefinition(**item)
            for item in data["events"]
        ),
        authority_checks=tuple(
            AuthorityCheck(**item)
            for item in data["authority_checks"]
        ),
        causal_decisions=tuple(
            CausalDecision(
                id=item["id"],
                cause=item["cause"],
                policy=item.get("policy", "max_weight"),
                paths=tuple(
                    CausalPath(
                        id=path["id"],
                        weight=path["weight"],
                        assignments=tuple(
                            StateAssignment(**assignment)
                            for assignment in path["assignments"]
                        ),
                        emits=tuple(
                            EventEmission(
                                event=emission["event"],
                                facts=_facts_from_data(emission.get("facts", [])),
                            )
                            for emission in path["emits"]
                        ),
                        effects=tuple(path.get("effects", ())),
                        rationale=path.get("rationale", ""),
                    )
                    for path in item["paths"]
                ),
            )
            for item in data["causal_decisions"]
        ),
        directives=tuple(
            AIRDirective(**item)
            for item in data["directives"]
        ),
    )


def load_air_json(path: str) -> AIRProgram:
    return air_from_dict(load_air_dict(path))