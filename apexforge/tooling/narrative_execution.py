"""Deterministic P11.6G user-facing narrative execution routing.

This module consumes the canonical P11.6F narrative projection from an
existing ApexForge build artifact and routes one complete, explicit request to
the P11.6E execution boundary.  It does not parse narrative source, construct
bindings from descriptive text, select a scene/choice/path, or own transition
semantics.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Optional, Union

from language.narrative_model import NarrativeIdentity, NarrativeStateFact
from runtime import narrative_observability
from runtime.narrative_binding import (
    NarrativeExecutableBindingSet,
    NarrativeExecutableChoicePath,
    NarrativeFactAssignment,
    NarrativeFactPredicate,
)
from runtime.narrative_execution import (
    NarrativeChoiceEvidence,
    NarrativeExecutionDiagnostic,
    NarrativeExecutionResult,
    NarrativeExecutionState,
    NarrativeExecutionTraceEvent,
    NarrativeTermination,
)
from tooling.build_artifact import (
    BUILD_ARTIFACT_FINGERPRINT_ALGORITHM,
    BUILD_ARTIFACT_SCHEMA,
    canonical_json_bytes,
)
from tooling.narrative_artifact import NARRATIVE_BUILD_ARTIFACT_SCHEMA


NARRATIVE_EXECUTION_REQUEST_SCHEMA = (
    "apexforge.narrative-execution-request/v1"
)
NARRATIVE_EXECUTION_RESULT_SCHEMA = (
    "apexforge.narrative-execution-result/v1"
)


_ERROR_DETAILS = {
    "invalid_request": (
        "APX-NARRATIVE-100",
        "invalid narrative execution request.",
    ),
    "unavailable_build_material": (
        "APX-NARRATIVE-110",
        "narrative build artifact is unavailable.",
    ),
    "malformed_build_material": (
        "APX-NARRATIVE-111",
        "narrative build artifact is malformed.",
    ),
    "unavailable_narrative_material": (
        "APX-NARRATIVE-112",
        "canonical narrative build material is unavailable.",
    ),
    "malformed_execution_state": (
        "APX-NARRATIVE-120",
        "explicit narrative execution state is malformed.",
    ),
}


class NarrativeExecutionRoutingError(ValueError):
    """One stable public request/material failure before P11.6E execution."""

    def __init__(self, classification: str) -> None:
        try:
            code, message = _ERROR_DETAILS[classification]
        except KeyError:
            raise ValueError(
                "unsupported narrative execution routing classification."
            ) from None
        self.classification = classification
        self.code = code
        super().__init__(f"[{code}] {message}")


@dataclass(frozen=True)
class NarrativeExecutionRequest:
    """One explicit state, choice identity, and path-index invocation."""

    state: NarrativeExecutionState
    choice: NarrativeIdentity
    path_index: int

    def __post_init__(self) -> None:
        if type(self.state) is not NarrativeExecutionState:
            raise TypeError(
                "NarrativeExecutionRequest.state must be an exact "
                "NarrativeExecutionState."
            )
        if type(self.choice) is not NarrativeIdentity or self.choice.kind != "choice":
            raise TypeError(
                "NarrativeExecutionRequest.choice must be a choice identity."
            )
        if type(self.path_index) is not int:
            raise TypeError(
                "NarrativeExecutionRequest.path_index must be an exact int."
            )
        if self.path_index < 0:
            raise ValueError(
                "NarrativeExecutionRequest.path_index must be non-negative."
            )


def _duplicate_rejecting_mapping(
    pairs: list[tuple[str, Any]],
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON object key")
        result[key] = value
    return result


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"unsupported JSON constant {value}")


def _read_json(
    path: Union[str, Path],
    *,
    unavailable_classification: str,
    malformed_classification: str,
) -> tuple[bytes, Mapping[str, Any]]:
    try:
        content = Path(path).read_bytes()
    except OSError as exc:
        raise NarrativeExecutionRoutingError(
            unavailable_classification
        ) from exc

    try:
        text = content.decode("utf-8")
        value = json.loads(
            text,
            object_pairs_hook=_duplicate_rejecting_mapping,
            parse_constant=_reject_json_constant,
        )
        if type(value) is not dict:
            raise TypeError("top-level JSON value must be an object")
    except (TypeError, UnicodeDecodeError, ValueError) as exc:
        raise NarrativeExecutionRoutingError(
            malformed_classification
        ) from exc
    return content, value


def _mapping(
    value: object,
    keys: frozenset[str],
) -> Mapping[str, Any]:
    if type(value) is not dict or frozenset(value) != keys:
        raise ValueError("mapping shape mismatch")
    return value


def _list(value: object) -> list[Any]:
    if type(value) is not list:
        raise TypeError("value must be a JSON array")
    return value


def _identity(
    value: object,
    *,
    expected_kind: Optional[str] = None,
) -> NarrativeIdentity:
    mapping = _mapping(value, frozenset(("kind", "path")))
    path = _list(mapping["path"])
    identity = NarrativeIdentity(mapping["kind"], tuple(path))
    if expected_kind is not None and identity.kind != expected_kind:
        raise ValueError("narrative identity kind mismatch")
    return identity


def _identity_payload(identity: NarrativeIdentity) -> dict[str, Any]:
    return {"kind": identity.kind, "path": list(identity.path)}


def _fact(value: object) -> NarrativeStateFact:
    mapping = _mapping(value, frozenset(("subject", "name", "value")))
    return NarrativeStateFact(
        subject=_identity(mapping["subject"]),
        name=mapping["name"],
        value=mapping["value"],
    )


def _fact_payload(fact: NarrativeStateFact) -> dict[str, Any]:
    return {
        "subject": _identity_payload(fact.subject),
        "name": fact.name,
        "value": fact.value,
    }


def _choice_evidence(value: object) -> NarrativeChoiceEvidence:
    mapping = _mapping(
        value,
        frozenset(
            (
                "choice",
                "source_scene",
                "path_index",
                "path_label",
                "destination",
            )
        ),
    )
    return NarrativeChoiceEvidence(
        choice=_identity(mapping["choice"], expected_kind="choice"),
        source_scene=_identity(
            mapping["source_scene"],
            expected_kind="scene",
        ),
        path_index=mapping["path_index"],
        path_label=mapping["path_label"],
        destination=_identity(
            mapping["destination"],
            expected_kind="scene",
        ),
    )


def _choice_evidence_payload(
    evidence: NarrativeChoiceEvidence,
) -> dict[str, Any]:
    return {
        "choice": _identity_payload(evidence.choice),
        "source_scene": _identity_payload(evidence.source_scene),
        "path_index": evidence.path_index,
        "path_label": evidence.path_label,
        "destination": _identity_payload(evidence.destination),
    }


def _termination(value: object) -> NarrativeTermination:
    mapping = _mapping(value, frozenset(("status", "reason")))
    return NarrativeTermination(
        status=mapping["status"],
        reason=mapping["reason"],
    )


def _termination_payload(termination: NarrativeTermination) -> dict[str, Any]:
    return {
        "status": termination.status,
        "reason": termination.reason,
    }


def _state(value: object) -> NarrativeExecutionState:
    mapping = _mapping(
        value,
        frozenset(
            (
                "story",
                "current_scene",
                "facts",
                "progression",
                "choice_history",
                "termination",
            )
        ),
    )
    progression_values = _list(mapping["progression"])
    if not progression_values:
        raise ValueError("explicit progression must not be empty")
    return NarrativeExecutionState(
        story=_identity(mapping["story"], expected_kind="story"),
        current_scene=_identity(
            mapping["current_scene"],
            expected_kind="scene",
        ),
        facts=tuple(_fact(item) for item in _list(mapping["facts"])),
        progression=tuple(
            _identity(item, expected_kind="scene")
            for item in progression_values
        ),
        choice_history=tuple(
            _choice_evidence(item)
            for item in _list(mapping["choice_history"])
        ),
        termination=_termination(mapping["termination"]),
    )


def narrative_execution_state_payload(
    state: NarrativeExecutionState,
) -> dict[str, Any]:
    """Project one exact immutable execution state to public JSON data."""

    if type(state) is not NarrativeExecutionState:
        raise TypeError(
            "narrative_execution_state_payload requires an exact "
            "NarrativeExecutionState."
        )
    return {
        "story": _identity_payload(state.story),
        "current_scene": _identity_payload(state.current_scene),
        "facts": [_fact_payload(fact) for fact in state.facts],
        "progression": [
            _identity_payload(scene) for scene in state.progression
        ],
        "choice_history": [
            _choice_evidence_payload(evidence)
            for evidence in state.choice_history
        ],
        "termination": _termination_payload(state.termination),
    }


def _predicate(value: object) -> NarrativeFactPredicate:
    mapping = _mapping(
        value,
        frozenset(("operator", "subject", "value", "name")),
    )
    return NarrativeFactPredicate(
        subject=_identity(mapping["subject"]),
        name=mapping["name"],
        operator=mapping["operator"],
        value=mapping["value"],
    )


def _assignment(value: object) -> NarrativeFactAssignment:
    mapping = _mapping(value, frozenset(("subject", "value", "name")))
    return NarrativeFactAssignment(
        subject=_identity(mapping["subject"]),
        name=mapping["name"],
        value=mapping["value"],
    )


def _executable_path(value: object) -> NarrativeExecutableChoicePath:
    mapping = _mapping(
        value,
        frozenset(
            (
                "choice",
                "source_scene",
                "path_index",
                "path_label",
                "destination",
                "source_condition",
                "condition",
                "source_consequence",
                "assignments",
            )
        ),
    )
    condition_value = mapping["condition"]
    return NarrativeExecutableChoicePath(
        choice=_identity(mapping["choice"], expected_kind="choice"),
        source_scene=_identity(
            mapping["source_scene"],
            expected_kind="scene",
        ),
        path_index=mapping["path_index"],
        path_label=mapping["path_label"],
        destination=_identity(
            mapping["destination"],
            expected_kind="scene",
        ),
        source_condition=mapping["source_condition"],
        condition=(
            None if condition_value is None else _predicate(condition_value)
        ),
        source_consequence=mapping["source_consequence"],
        assignments=tuple(
            _assignment(item) for item in _list(mapping["assignments"])
        ),
    )


def _story_path_records(
    story_value: object,
) -> tuple[
    NarrativeIdentity,
    dict[tuple[NarrativeIdentity, NarrativeIdentity, int], tuple[Any, ...]],
]:
    story = _mapping(
        story_value,
        frozenset(
            (
                "identity",
                "characters",
                "scenes",
                "dialogues",
                "choices",
                "perspectives",
                "timelines",
                "states",
                "continuities",
            )
        ),
    )
    for family in (
        "characters",
        "scenes",
        "dialogues",
        "choices",
        "perspectives",
        "timelines",
        "states",
        "continuities",
    ):
        _list(story[family])

    story_identity = _identity(story["identity"], expected_kind="story")
    records = {}
    for choice_value in story["choices"]:
        choice = _mapping(
            choice_value,
            frozenset(("identity", "scene", "paths")),
        )
        choice_identity = _identity(
            choice["identity"],
            expected_kind="choice",
        )
        source_scene = _identity(choice["scene"], expected_kind="scene")
        for path_index, path_value in enumerate(_list(choice["paths"])):
            path = _mapping(
                path_value,
                frozenset(
                    ("label", "destination", "condition", "consequence")
                ),
            )
            key = (choice_identity, source_scene, path_index)
            if key in records:
                raise ValueError("duplicate semantic choice path")
            records[key] = (
                path["label"],
                _identity(path["destination"], expected_kind="scene"),
                path["condition"],
                path["consequence"],
            )
    return story_identity, records


def _narrative_bindings(value: object) -> NarrativeExecutableBindingSet:
    narrative = _mapping(
        value,
        frozenset(("schema", "source", "story", "bindings")),
    )
    if narrative["schema"] != NARRATIVE_BUILD_ARTIFACT_SCHEMA:
        raise ValueError("narrative artifact schema mismatch")
    source_name = narrative["source"]
    if type(source_name) is not str:
        raise TypeError("narrative artifact source must be a string")

    story_identity, semantic_paths = _story_path_records(narrative["story"])
    binding_value = _mapping(
        narrative["bindings"],
        frozenset(("story", "paths")),
    )
    binding_story = _identity(
        binding_value["story"],
        expected_kind="story",
    )
    paths = tuple(
        _executable_path(item) for item in _list(binding_value["paths"])
    )
    if binding_story != story_identity or len(paths) != len(semantic_paths):
        raise ValueError("narrative story and bindings disagree")

    seen_keys = set()
    for path in paths:
        key = (path.choice, path.source_scene, path.path_index)
        if key in seen_keys:
            raise ValueError("duplicate executable choice path")
        seen_keys.add(key)
        if semantic_paths.get(key) != (
            path.path_label,
            path.destination,
            path.source_condition,
            path.source_consequence,
        ):
            raise ValueError("semantic and executable choice paths disagree")

    if not source_name or source_name != source_name.strip():
        raise ValueError("narrative artifact source must be trimmed")
    return NarrativeExecutableBindingSet(
        story=binding_story,
        paths=paths,
    )


def load_narrative_execution_material(
    artifact_path: Union[str, Path],
) -> NarrativeExecutableBindingSet:
    """Validate and load exact P11.6F material from canonical build JSON."""

    content, value = _read_json(
        artifact_path,
        unavailable_classification="unavailable_build_material",
        malformed_classification="malformed_build_material",
    )
    try:
        if content != canonical_json_bytes(value):
            raise ValueError("build artifact is not canonical JSON")
        historical_keys = frozenset(("air", "fingerprint", "project", "schema"))
        integrated_keys = historical_keys | frozenset(("narrative",))
        keys = frozenset(value)
        if keys not in (historical_keys, integrated_keys):
            raise ValueError("build artifact shape mismatch")
        if value["schema"] != BUILD_ARTIFACT_SCHEMA:
            raise ValueError("build artifact shape or schema mismatch")

        fingerprint = _mapping(
            value["fingerprint"],
            frozenset(("algorithm", "value")),
        )
        if (
            fingerprint["algorithm"]
            != BUILD_ARTIFACT_FINGERPRINT_ALGORITHM
            or type(fingerprint["value"]) is not str
        ):
            raise ValueError("build artifact fingerprint shape mismatch")
        payload = dict(value)
        del payload["fingerprint"]
        expected = hashlib.sha256(canonical_json_bytes(payload)).hexdigest()
        if fingerprint["value"] != expected:
            raise ValueError("build artifact fingerprint mismatch")
        if keys == historical_keys:
            raise NarrativeExecutionRoutingError(
                "unavailable_narrative_material"
            )
        return _narrative_bindings(value["narrative"])
    except NarrativeExecutionRoutingError:
        raise
    except (TypeError, ValueError) as exc:
        raise NarrativeExecutionRoutingError(
            "malformed_build_material"
        ) from exc


def load_narrative_execution_request(
    request_path: Union[str, Path],
) -> NarrativeExecutionRequest:
    """Load one complete request without inferring any execution field."""

    _, value = _read_json(
        request_path,
        unavailable_classification="invalid_request",
        malformed_classification="invalid_request",
    )
    try:
        request = _mapping(
            value,
            frozenset(("schema", "state", "choice", "path_index")),
        )
        if request["schema"] != NARRATIVE_EXECUTION_REQUEST_SCHEMA:
            raise ValueError("narrative request schema mismatch")
        try:
            state = _state(request["state"])
        except (TypeError, ValueError) as exc:
            raise NarrativeExecutionRoutingError(
                "malformed_execution_state"
            ) from exc
        return NarrativeExecutionRequest(
            state=state,
            choice=_identity(request["choice"], expected_kind="choice"),
            path_index=request["path_index"],
        )
    except NarrativeExecutionRoutingError:
        raise
    except (TypeError, ValueError) as exc:
        raise NarrativeExecutionRoutingError("invalid_request") from exc


def narrative_execution_request_payload(
    request: NarrativeExecutionRequest,
) -> dict[str, Any]:
    """Project one complete request to deterministic JSON-compatible data."""

    if type(request) is not NarrativeExecutionRequest:
        raise TypeError(
            "narrative_execution_request_payload requires an exact "
            "NarrativeExecutionRequest."
        )
    return {
        "schema": NARRATIVE_EXECUTION_REQUEST_SCHEMA,
        "state": narrative_execution_state_payload(request.state),
        "choice": _identity_payload(request.choice),
        "path_index": request.path_index,
    }


def execute_narrative_request(
    bindings: NarrativeExecutableBindingSet,
    request: NarrativeExecutionRequest,
) -> NarrativeExecutionResult:
    """Delegate one explicit choice/path request to P11.6E exactly once."""

    if type(bindings) is not NarrativeExecutableBindingSet:
        raise TypeError(
            "bindings must be an exact NarrativeExecutableBindingSet."
        )
    if type(request) is not NarrativeExecutionRequest:
        raise TypeError("request must be an exact NarrativeExecutionRequest.")
    return narrative_observability.execute_narrative_choice(
        request.state,
        bindings,
        request.choice,
        request.path_index,
    )


def _diagnostic_payload(
    diagnostic: NarrativeExecutionDiagnostic,
) -> dict[str, Any]:
    return {
        "severity": diagnostic.severity,
        "code": diagnostic.code,
        "message": diagnostic.message,
        "subject": (
            None
            if diagnostic.subject is None
            else _identity_payload(diagnostic.subject)
        ),
    }


def _trace_payload(event: NarrativeExecutionTraceEvent) -> dict[str, Any]:
    return {
        "kind": event.kind,
        "message": event.message,
        "facts": [
            {"key": fact.key, "value": fact.value}
            for fact in event.facts
        ],
    }


def narrative_execution_result_payload(
    result: NarrativeExecutionResult,
) -> dict[str, Any]:
    """Project a P11.6E result without repr, paths, clocks, or random data."""

    if type(result) is not NarrativeExecutionResult:
        raise TypeError(
            "narrative_execution_result_payload requires an exact "
            "NarrativeExecutionResult."
        )
    return {
        "schema": NARRATIVE_EXECUTION_RESULT_SCHEMA,
        "ok": result.ok,
        "initial_state": narrative_execution_state_payload(
            result.initial_state
        ),
        "final_state": narrative_execution_state_payload(result.final_state),
        "diagnostics": [
            _diagnostic_payload(diagnostic)
            for diagnostic in result.diagnostics
        ],
        "trace": [_trace_payload(event) for event in result.trace],
        "choice_evidence": [
            _choice_evidence_payload(evidence)
            for evidence in result.choice_evidence
        ],
    }


def narrative_execution_result_bytes(
    result: NarrativeExecutionResult,
) -> bytes:
    """Serialize one public result using the existing canonical JSON owner."""

    return canonical_json_bytes(narrative_execution_result_payload(result))


__all__ = (
    "NARRATIVE_EXECUTION_REQUEST_SCHEMA",
    "NARRATIVE_EXECUTION_RESULT_SCHEMA",
    "NarrativeExecutionRequest",
    "NarrativeExecutionRoutingError",
    "execute_narrative_request",
    "load_narrative_execution_material",
    "load_narrative_execution_request",
    "narrative_execution_request_payload",
    "narrative_execution_result_bytes",
    "narrative_execution_result_payload",
    "narrative_execution_state_payload",
)
