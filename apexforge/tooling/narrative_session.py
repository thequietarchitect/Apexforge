"""Deterministic P11.6H narrative session and state lifecycle.

This module persists immutable P11.6B execution states above the canonical
P11.6F build material and the P11.6G one-shot execution route.  It requires
explicit initialization, choice/path stepping, and termination requests.  It
does not infer scenes, select transitions, loop, or own narrative semantics.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Any, Mapping, Optional, Union

from language.narrative_model import NarrativeIdentity, NarrativeStateFact
from runtime import narrative_observability
from runtime.narrative_binding import NarrativeExecutableBindingSet
from runtime.narrative_execution import (
    NarrativeChoiceEvidence,
    NarrativeExecutionResult,
    NarrativeExecutionState,
    NarrativeTermination,
)
from tooling.build_artifact import (
    BUILD_ARTIFACT_FINGERPRINT_ALGORITHM,
    BUILD_ARTIFACT_SCHEMA,
    canonical_json_bytes,
)
from tooling.narrative_execution import (
    NarrativeExecutionRequest,
    NarrativeExecutionRoutingError,
    execute_narrative_request,
    load_narrative_execution_material,
    narrative_execution_result_payload,
    narrative_execution_state_payload,
)


NARRATIVE_SESSION_SCHEMA = "apexforge.narrative-session/v1"
NARRATIVE_SESSION_CREATE_REQUEST_SCHEMA = (
    "apexforge.narrative-session-create-request/v1"
)
NARRATIVE_SESSION_STEP_REQUEST_SCHEMA = (
    "apexforge.narrative-session-step-request/v1"
)
NARRATIVE_SESSION_TERMINATE_REQUEST_SCHEMA = (
    "apexforge.narrative-session-terminate-request/v1"
)
NARRATIVE_SESSION_STEP_RESULT_SCHEMA = (
    "apexforge.narrative-session-step-result/v1"
)


_ERROR_DETAILS = {
    "invalid_request": (
        "APX-NARRATIVE-200",
        "invalid narrative session request.",
    ),
    "unavailable_session": (
        "APX-NARRATIVE-210",
        "narrative session file is unavailable.",
    ),
    "malformed_session": (
        "APX-NARRATIVE-211",
        "narrative session file is malformed or noncanonical.",
    ),
    "unavailable_build_artifact": (
        "APX-NARRATIVE-220",
        "narrative session build artifact is unavailable.",
    ),
    "malformed_build_artifact": (
        "APX-NARRATIVE-221",
        "narrative session build artifact is malformed.",
    ),
    "unavailable_narrative_material": (
        "APX-NARRATIVE-222",
        "canonical narrative build material is unavailable.",
    ),
    "artifact_mismatch": (
        "APX-NARRATIVE-230",
        "narrative session artifact fingerprint does not match.",
    ),
    "story_mismatch": (
        "APX-NARRATIVE-231",
        "narrative session story does not match the artifact.",
    ),
    "invalid_start_scene": (
        "APX-NARRATIVE-232",
        "explicit narrative session starting scene is invalid.",
    ),
    "malformed_initial_facts": (
        "APX-NARRATIVE-233",
        "explicit narrative session initial facts are malformed.",
    ),
    "termination_failure": (
        "APX-NARRATIVE-240",
        "explicit narrative session termination failed.",
    ),
}


class NarrativeSessionError(ValueError):
    """One stable P11.6H request, persistence, or association failure."""

    def __init__(self, classification: str) -> None:
        try:
            code, message = _ERROR_DETAILS[classification]
        except KeyError:
            raise ValueError(
                "unsupported narrative session error classification."
            ) from None
        self.classification = classification
        self.code = code
        super().__init__(f"[{code}] {message}")


class NarrativeSessionOutputError(OSError):
    """A fully serialized session could not be atomically persisted."""


def _validate_lifecycle_state_shape(state: NarrativeExecutionState) -> None:
    if len(state.progression) != len(state.choice_history) + 1:
        raise ValueError(
            "session progression must contain one scene per transition plus "
            "its explicit starting scene."
        )
    for index, evidence in enumerate(state.choice_history):
        if (
            evidence.source_scene != state.progression[index]
            or evidence.destination != state.progression[index + 1]
        ):
            raise ValueError(
                "session choice history must agree with progression."
            )


@dataclass(frozen=True)
class NarrativeSession:
    """One immutable state associated with one exact canonical artifact."""

    artifact_fingerprint: str
    story: NarrativeIdentity
    state: NarrativeExecutionState

    def __post_init__(self) -> None:
        if type(self.artifact_fingerprint) is not str or (
            len(self.artifact_fingerprint) != 64
            or any(
                character not in "0123456789abcdef"
                for character in self.artifact_fingerprint
            )
        ):
            raise ValueError(
                "NarrativeSession.artifact_fingerprint must be lowercase "
                "SHA-256 hexadecimal."
            )
        if type(self.story) is not NarrativeIdentity or self.story.kind != "story":
            raise TypeError("NarrativeSession.story must be a story identity.")
        if type(self.state) is not NarrativeExecutionState:
            raise TypeError(
                "NarrativeSession.state must be an exact "
                "NarrativeExecutionState."
            )
        if self.story != self.state.story:
            raise ValueError(
                "NarrativeSession.story must equal its execution-state story."
            )
        _validate_lifecycle_state_shape(self.state)


@dataclass(frozen=True)
class NarrativeSessionMaterial:
    """Validated P11.6F/P11.6G material needed by the lifecycle boundary."""

    artifact_fingerprint: str
    story: NarrativeIdentity
    scenes: frozenset[NarrativeIdentity]
    declared_identities: frozenset[NarrativeIdentity]
    bindings: NarrativeExecutableBindingSet

    def __post_init__(self) -> None:
        if type(self.artifact_fingerprint) is not str or (
            len(self.artifact_fingerprint) != 64
            or any(
                character not in "0123456789abcdef"
                for character in self.artifact_fingerprint
            )
        ):
            raise ValueError(
                "NarrativeSessionMaterial.artifact_fingerprint must be "
                "lowercase SHA-256 hexadecimal."
            )
        if type(self.story) is not NarrativeIdentity or self.story.kind != "story":
            raise TypeError(
                "NarrativeSessionMaterial.story must be a story identity."
            )
        if type(self.scenes) is not frozenset or any(
            type(scene) is not NarrativeIdentity or scene.kind != "scene"
            for scene in self.scenes
        ):
            raise TypeError(
                "NarrativeSessionMaterial.scenes must be a frozenset of scene "
                "identities."
            )
        if type(self.declared_identities) is not frozenset or any(
            type(identity) is not NarrativeIdentity
            for identity in self.declared_identities
        ):
            raise TypeError(
                "NarrativeSessionMaterial.declared_identities must be a "
                "frozenset of narrative identities."
            )
        if self.story not in self.declared_identities or not self.scenes.issubset(
            self.declared_identities
        ):
            raise ValueError(
                "NarrativeSessionMaterial identity inventory is inconsistent."
            )
        if type(self.bindings) is not NarrativeExecutableBindingSet:
            raise TypeError(
                "NarrativeSessionMaterial.bindings must be an exact "
                "NarrativeExecutableBindingSet."
            )
        if self.bindings.story != self.story:
            raise ValueError(
                "NarrativeSessionMaterial bindings and story disagree."
            )


@dataclass(frozen=True)
class NarrativeSessionCreateRequest:
    """Explicit story, starting scene, and optional initial facts."""

    story: NarrativeIdentity
    start_scene: NarrativeIdentity
    facts: tuple[NarrativeStateFact, ...] = ()

    def __post_init__(self) -> None:
        if type(self.story) is not NarrativeIdentity or self.story.kind != "story":
            raise TypeError(
                "NarrativeSessionCreateRequest.story must be a story identity."
            )
        if (
            type(self.start_scene) is not NarrativeIdentity
            or self.start_scene.kind != "scene"
        ):
            raise TypeError(
                "NarrativeSessionCreateRequest.start_scene must be a scene "
                "identity."
            )
        if type(self.facts) is not tuple:
            raise TypeError(
                "NarrativeSessionCreateRequest.facts must be an exact tuple."
            )
        for fact in self.facts:
            if type(fact) is not NarrativeStateFact:
                raise TypeError(
                    "NarrativeSessionCreateRequest.facts must contain exact "
                    "NarrativeStateFact objects."
                )


@dataclass(frozen=True)
class NarrativeSessionStepRequest:
    """Exactly one explicit choice identity and path index."""

    choice: NarrativeIdentity
    path_index: int

    def __post_init__(self) -> None:
        if type(self.choice) is not NarrativeIdentity or self.choice.kind != "choice":
            raise TypeError(
                "NarrativeSessionStepRequest.choice must be a choice identity."
            )
        if type(self.path_index) is not int or self.path_index < 0:
            raise ValueError(
                "NarrativeSessionStepRequest.path_index must be a "
                "non-negative exact int."
            )


@dataclass(frozen=True)
class NarrativeSessionTerminateRequest:
    """One explicit frozen P11.6E termination reason."""

    reason: str

    def __post_init__(self) -> None:
        if type(self.reason) is not str or not self.reason:
            raise ValueError(
                "NarrativeSessionTerminateRequest.reason must be explicit."
            )


@dataclass(frozen=True)
class NarrativeSessionStepResult:
    """The authoritative P11.6G result and optional successful next session."""

    execution_result: NarrativeExecutionResult
    session: Optional[NarrativeSession]

    def __post_init__(self) -> None:
        if type(self.execution_result) is not NarrativeExecutionResult:
            raise TypeError(
                "NarrativeSessionStepResult.execution_result must be an exact "
                "NarrativeExecutionResult."
            )
        if self.execution_result.ok != (self.session is not None):
            raise ValueError(
                "NarrativeSessionStepResult session presence must match success."
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
    unavailable: str,
    malformed: str,
    require_canonical: bool = True,
) -> tuple[bytes, Mapping[str, Any]]:
    try:
        content = Path(path).read_bytes()
    except OSError as exc:
        raise NarrativeSessionError(unavailable) from exc
    try:
        value = json.loads(
            content.decode("utf-8"),
            object_pairs_hook=_duplicate_rejecting_mapping,
            parse_constant=_reject_json_constant,
        )
        if type(value) is not dict:
            raise TypeError("top-level JSON value must be an object")
        if require_canonical and content != canonical_json_bytes(value):
            raise ValueError("JSON is not canonical")
    except (TypeError, UnicodeDecodeError, ValueError) as exc:
        raise NarrativeSessionError(malformed) from exc
    return content, value


def _mapping(value: object, keys: frozenset[str]) -> Mapping[str, Any]:
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


def _evidence(value: object) -> NarrativeChoiceEvidence:
    mapping = _mapping(
        value,
        frozenset(
            ("choice", "source_scene", "path_index", "path_label", "destination")
        ),
    )
    return NarrativeChoiceEvidence(
        choice=_identity(mapping["choice"], expected_kind="choice"),
        source_scene=_identity(mapping["source_scene"], expected_kind="scene"),
        path_index=mapping["path_index"],
        path_label=mapping["path_label"],
        destination=_identity(mapping["destination"], expected_kind="scene"),
    )


def _termination(value: object) -> NarrativeTermination:
    mapping = _mapping(value, frozenset(("status", "reason")))
    termination = NarrativeTermination(mapping["status"], mapping["reason"])
    if termination.is_terminated and termination.reason != (
        narrative_observability.NARRATIVE_TERMINATION_REASON_EXPLICIT_OUTCOME
    ):
        raise ValueError("unsupported persisted termination reason")
    return termination


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
    progression = _list(mapping["progression"])
    if not progression:
        raise ValueError("persisted progression must be explicit")
    return NarrativeExecutionState(
        story=_identity(mapping["story"], expected_kind="story"),
        current_scene=_identity(mapping["current_scene"], expected_kind="scene"),
        facts=tuple(_fact(item) for item in _list(mapping["facts"])),
        progression=tuple(
            _identity(item, expected_kind="scene") for item in progression
        ),
        choice_history=tuple(
            _evidence(item) for item in _list(mapping["choice_history"])
        ),
        termination=_termination(mapping["termination"]),
    )


def _request_value(
    path: Union[str, Path],
) -> Mapping[str, Any]:
    _, value = _read_json(
        path,
        unavailable="invalid_request",
        malformed="invalid_request",
        require_canonical=False,
    )
    return value


def _artifact_identity_inventory(
    story_value: object,
) -> tuple[
    NarrativeIdentity,
    frozenset[NarrativeIdentity],
    frozenset[NarrativeIdentity],
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
    story_identity = _identity(story["identity"], expected_kind="story")
    identities = {story_identity}
    scenes = set()
    family_kinds = {
        "characters": "character",
        "scenes": "scene",
        "dialogues": "dialogue",
        "choices": "choice",
        "perspectives": "perspective",
        "timelines": "timeline",
        "states": "narrative_state",
        "continuities": "continuity",
    }
    for family, expected_kind in family_kinds.items():
        for item in _list(story[family]):
            record = item if type(item) is dict else None
            if record is None or "identity" not in record:
                raise ValueError("narrative declaration identity is unavailable")
            identity = _identity(
                record["identity"], expected_kind=expected_kind
            )
            if identity in identities:
                raise ValueError("duplicate narrative declaration identity")
            identities.add(identity)
            if family == "scenes":
                scenes.add(identity)
    return story_identity, frozenset(scenes), frozenset(identities)


def load_narrative_session_material(
    artifact_path: Union[str, Path],
) -> NarrativeSessionMaterial:
    """Validate one canonical artifact and retain its exact association."""

    content, value = _read_json(
        artifact_path,
        unavailable="unavailable_build_artifact",
        malformed="malformed_build_artifact",
    )
    try:
        historical_keys = frozenset(("air", "fingerprint", "project", "schema"))
        if frozenset(value) not in (
            historical_keys,
            historical_keys | frozenset(("narrative",)),
        ):
            raise ValueError("build artifact shape mismatch")
        if value["schema"] != BUILD_ARTIFACT_SCHEMA:
            raise ValueError("build artifact schema mismatch")
        fingerprint = _mapping(
            value["fingerprint"], frozenset(("algorithm", "value"))
        )
        if (
            fingerprint["algorithm"] != BUILD_ARTIFACT_FINGERPRINT_ALGORITHM
            or type(fingerprint["value"]) is not str
        ):
            raise ValueError("build artifact fingerprint shape mismatch")
        payload = dict(value)
        del payload["fingerprint"]
        expected = hashlib.sha256(canonical_json_bytes(payload)).hexdigest()
        if fingerprint["value"] != expected:
            raise ValueError("build artifact fingerprint mismatch")
        if "narrative" not in value:
            raise NarrativeSessionError("unavailable_narrative_material")
        narrative = _mapping(
            value["narrative"],
            frozenset(("schema", "source", "story", "bindings")),
        )
        story, scenes, identities = _artifact_identity_inventory(
            narrative["story"]
        )
    except NarrativeSessionError:
        raise
    except (KeyError, TypeError, ValueError) as exc:
        raise NarrativeSessionError("malformed_build_artifact") from exc

    try:
        bindings = load_narrative_execution_material(artifact_path)
    except NarrativeExecutionRoutingError as exc:
        classification = {
            "unavailable_build_material": "unavailable_build_artifact",
            "malformed_build_material": "malformed_build_artifact",
            "unavailable_narrative_material": "unavailable_narrative_material",
        }.get(exc.classification, "malformed_build_artifact")
        raise NarrativeSessionError(classification) from exc
    try:
        if Path(artifact_path).read_bytes() != content or bindings.story != story:
            raise ValueError("artifact changed or material story disagrees")
    except (OSError, ValueError) as exc:
        raise NarrativeSessionError("malformed_build_artifact") from exc
    return NarrativeSessionMaterial(
        artifact_fingerprint=fingerprint["value"],
        story=story,
        scenes=scenes,
        declared_identities=identities,
        bindings=bindings,
    )


def _validate_state(
    material: NarrativeSessionMaterial,
    state: NarrativeExecutionState,
) -> None:
    if state.story != material.story:
        raise NarrativeSessionError("story_mismatch")
    if state.current_scene not in material.scenes or any(
        scene not in material.scenes for scene in state.progression
    ):
        raise NarrativeSessionError("malformed_session")
    if any(
        fact.subject not in material.declared_identities for fact in state.facts
    ):
        raise NarrativeSessionError("malformed_session")
    try:
        _validate_lifecycle_state_shape(state)
    except ValueError as exc:
        raise NarrativeSessionError("malformed_session") from exc
    for index, evidence in enumerate(state.choice_history):
        matches = tuple(
            path
            for path in material.bindings.paths
            if path.choice == evidence.choice
            and path.source_scene == evidence.source_scene
            and path.path_index == evidence.path_index
            and path.path_label == evidence.path_label
            and path.destination == evidence.destination
        )
        if len(matches) != 1:
            raise NarrativeSessionError("malformed_session")


def _validate_association(
    material: NarrativeSessionMaterial,
    session: NarrativeSession,
) -> None:
    if type(material) is not NarrativeSessionMaterial:
        raise TypeError("material must be exact NarrativeSessionMaterial.")
    if type(session) is not NarrativeSession:
        raise TypeError("session must be exact NarrativeSession.")
    if session.artifact_fingerprint != material.artifact_fingerprint:
        raise NarrativeSessionError("artifact_mismatch")
    if session.story != material.story:
        raise NarrativeSessionError("story_mismatch")
    _validate_state(material, session.state)


def load_narrative_session_create_request(
    path: Union[str, Path],
) -> NarrativeSessionCreateRequest:
    """Load one strict explicit initialization request without inference."""

    value = _request_value(path)
    if type(value) is dict and "start_scene" not in value:
        raise NarrativeSessionError("invalid_start_scene")
    try:
        request = _mapping(
            value, frozenset(("schema", "story", "start_scene", "facts"))
        )
        if request["schema"] != NARRATIVE_SESSION_CREATE_REQUEST_SCHEMA:
            raise ValueError("creation request schema mismatch")
        story = _identity(request["story"], expected_kind="story")
    except (KeyError, TypeError, ValueError) as exc:
        raise NarrativeSessionError("invalid_request") from exc
    try:
        start_scene = _identity(request["start_scene"], expected_kind="scene")
    except (KeyError, TypeError, ValueError) as exc:
        raise NarrativeSessionError("invalid_start_scene") from exc
    try:
        facts = tuple(_fact(item) for item in _list(request["facts"]))
        return NarrativeSessionCreateRequest(story, start_scene, facts)
    except (KeyError, TypeError, ValueError) as exc:
        raise NarrativeSessionError("malformed_initial_facts") from exc


def load_narrative_session_step_request(
    path: Union[str, Path],
) -> NarrativeSessionStepRequest:
    """Load exactly one explicit choice/path request."""

    value = _request_value(path)
    try:
        request = _mapping(
            value, frozenset(("schema", "choice", "path_index"))
        )
        if request["schema"] != NARRATIVE_SESSION_STEP_REQUEST_SCHEMA:
            raise ValueError("step request schema mismatch")
        return NarrativeSessionStepRequest(
            _identity(request["choice"], expected_kind="choice"),
            request["path_index"],
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise NarrativeSessionError("invalid_request") from exc


def load_narrative_session_terminate_request(
    path: Union[str, Path],
) -> NarrativeSessionTerminateRequest:
    """Load one explicit P11.6E termination request."""

    value = _request_value(path)
    try:
        request = _mapping(value, frozenset(("schema", "reason")))
        if request["schema"] != NARRATIVE_SESSION_TERMINATE_REQUEST_SCHEMA:
            raise ValueError("termination request schema mismatch")
        return NarrativeSessionTerminateRequest(request["reason"])
    except (KeyError, TypeError, ValueError) as exc:
        raise NarrativeSessionError("invalid_request") from exc


def create_narrative_session(
    material: NarrativeSessionMaterial,
    request: NarrativeSessionCreateRequest,
) -> NarrativeSession:
    """Create an active session at one explicitly supplied valid scene."""

    if type(material) is not NarrativeSessionMaterial:
        raise TypeError("material must be exact NarrativeSessionMaterial.")
    if type(request) is not NarrativeSessionCreateRequest:
        raise TypeError("request must be exact NarrativeSessionCreateRequest.")
    if request.story != material.story:
        raise NarrativeSessionError("story_mismatch")
    if request.start_scene not in material.scenes:
        raise NarrativeSessionError("invalid_start_scene")
    if any(
        fact.subject not in material.declared_identities for fact in request.facts
    ):
        raise NarrativeSessionError("malformed_initial_facts")
    try:
        state = NarrativeExecutionState(
            story=request.story,
            current_scene=request.start_scene,
            facts=request.facts,
            progression=(request.start_scene,),
            choice_history=(),
            termination=NarrativeTermination(),
        )
    except (TypeError, ValueError) as exc:
        raise NarrativeSessionError("malformed_initial_facts") from exc
    return NarrativeSession(material.artifact_fingerprint, request.story, state)


def narrative_session_payload(session: NarrativeSession) -> dict[str, Any]:
    """Project one immutable session to stable canonical JSON data."""

    if type(session) is not NarrativeSession:
        raise TypeError("session must be an exact NarrativeSession.")
    return {
        "schema": NARRATIVE_SESSION_SCHEMA,
        "artifact": {
            "algorithm": BUILD_ARTIFACT_FINGERPRINT_ALGORITHM,
            "value": session.artifact_fingerprint,
        },
        "story": _identity_payload(session.story),
        "state": narrative_execution_state_payload(session.state),
    }


def narrative_session_bytes(session: NarrativeSession) -> bytes:
    """Serialize a session with the existing canonical JSON owner."""

    return canonical_json_bytes(narrative_session_payload(session))


def load_narrative_session(path: Union[str, Path]) -> NarrativeSession:
    """Strictly rehydrate one canonical immutable session file."""

    _, value = _read_json(
        path,
        unavailable="unavailable_session",
        malformed="malformed_session",
    )
    try:
        session = _mapping(
            value, frozenset(("schema", "artifact", "story", "state"))
        )
        if session["schema"] != NARRATIVE_SESSION_SCHEMA:
            raise ValueError("session schema mismatch")
        artifact = _mapping(
            session["artifact"], frozenset(("algorithm", "value"))
        )
        if artifact["algorithm"] != BUILD_ARTIFACT_FINGERPRINT_ALGORITHM:
            raise ValueError("session artifact algorithm mismatch")
        return NarrativeSession(
            artifact_fingerprint=artifact["value"],
            story=_identity(session["story"], expected_kind="story"),
            state=_state(session["state"]),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise NarrativeSessionError("malformed_session") from exc


def step_narrative_session(
    material: NarrativeSessionMaterial,
    session: NarrativeSession,
    request: NarrativeSessionStepRequest,
) -> NarrativeSessionStepResult:
    """Delegate exactly one explicit transition through P11.6G/P11.6E."""

    if type(request) is not NarrativeSessionStepRequest:
        raise TypeError("request must be exact NarrativeSessionStepRequest.")
    _validate_association(material, session)
    execution_result = execute_narrative_request(
        material.bindings,
        NarrativeExecutionRequest(
            state=session.state,
            choice=request.choice,
            path_index=request.path_index,
        ),
    )
    next_session = None
    if execution_result.ok:
        next_session = NarrativeSession(
            artifact_fingerprint=session.artifact_fingerprint,
            story=session.story,
            state=execution_result.final_state,
        )
        _validate_association(material, next_session)
    return NarrativeSessionStepResult(execution_result, next_session)


def narrative_session_step_result_payload(
    result: NarrativeSessionStepResult,
) -> dict[str, Any]:
    """Preserve the complete P11.6G result and expose a successful session."""

    if type(result) is not NarrativeSessionStepResult:
        raise TypeError("result must be exact NarrativeSessionStepResult.")
    return {
        "schema": NARRATIVE_SESSION_STEP_RESULT_SCHEMA,
        "execution": narrative_execution_result_payload(
            result.execution_result
        ),
        "session": (
            None
            if result.session is None
            else narrative_session_payload(result.session)
        ),
    }


def narrative_session_step_result_bytes(
    result: NarrativeSessionStepResult,
) -> bytes:
    return canonical_json_bytes(narrative_session_step_result_payload(result))


def terminate_narrative_session(
    material: NarrativeSessionMaterial,
    session: NarrativeSession,
    request: NarrativeSessionTerminateRequest,
) -> NarrativeSession:
    """Delegate explicit termination to the frozen P11.6E operation."""

    if type(request) is not NarrativeSessionTerminateRequest:
        raise TypeError(
            "request must be exact NarrativeSessionTerminateRequest."
        )
    _validate_association(material, session)
    try:
        state = narrative_observability.terminate_narrative(
            session.state,
            request.reason,
        )
    except (TypeError, ValueError) as exc:
        raise NarrativeSessionError("termination_failure") from exc
    terminated = NarrativeSession(
        artifact_fingerprint=session.artifact_fingerprint,
        story=session.story,
        state=state,
    )
    _validate_association(material, terminated)
    return terminated


def write_narrative_session_atomic(
    session: NarrativeSession,
    output_path: Union[str, Path],
) -> None:
    """Write canonical session bytes through a temporary sibling."""

    output = Path(output_path)
    temporary_path: Optional[Path] = None
    file_descriptor: Optional[int] = None
    try:
        content = narrative_session_bytes(session)
        file_descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{output.name}.",
            suffix=".tmp",
            dir=str(output.parent),
        )
        temporary_path = Path(temporary_name)
        with os.fdopen(file_descriptor, "wb") as stream:
            file_descriptor = None
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_path, output)
        temporary_path = None
    except (OSError, TypeError, ValueError) as exc:
        if file_descriptor is not None:
            try:
                os.close(file_descriptor)
            except OSError:
                pass
        if temporary_path is not None:
            try:
                temporary_path.unlink()
            except OSError:
                pass
        raise NarrativeSessionOutputError(
            "[APX-NARRATIVE-250] Unable to write narrative session."
        ) from exc


__all__ = (
    "NARRATIVE_SESSION_CREATE_REQUEST_SCHEMA",
    "NARRATIVE_SESSION_SCHEMA",
    "NARRATIVE_SESSION_STEP_REQUEST_SCHEMA",
    "NARRATIVE_SESSION_STEP_RESULT_SCHEMA",
    "NARRATIVE_SESSION_TERMINATE_REQUEST_SCHEMA",
    "NarrativeSession",
    "NarrativeSessionCreateRequest",
    "NarrativeSessionError",
    "NarrativeSessionMaterial",
    "NarrativeSessionOutputError",
    "NarrativeSessionStepRequest",
    "NarrativeSessionStepResult",
    "NarrativeSessionTerminateRequest",
    "create_narrative_session",
    "load_narrative_session",
    "load_narrative_session_create_request",
    "load_narrative_session_material",
    "load_narrative_session_step_request",
    "load_narrative_session_terminate_request",
    "narrative_session_bytes",
    "narrative_session_payload",
    "narrative_session_step_result_bytes",
    "narrative_session_step_result_payload",
    "step_narrative_session",
    "terminate_narrative_session",
    "write_narrative_session_atomic",
)
