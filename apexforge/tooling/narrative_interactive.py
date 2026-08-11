"""Deterministic human-driven P11.6I narrative session interaction.

This module presents structural P11.6C path material for the current scene and
maps one explicit human menu selection to one exact P11.6H step request.  It
does not evaluate conditions, apply consequences, choose paths, infer
termination, or own persistence semantics.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import TextIO, Union

from language.narrative_model import NarrativeIdentity
from runtime.narrative_binding import NarrativeExecutableChoicePath
from tooling.narrative_session import (
    NarrativeSession,
    NarrativeSessionError,
    NarrativeSessionMaterial,
    NarrativeSessionStepRequest,
    NarrativeSessionTerminateRequest,
    load_narrative_session,
    load_narrative_session_material,
    narrative_session_step_result_bytes,
    step_narrative_session,
    terminate_narrative_session,
    write_narrative_session_atomic,
)


INTERACTIVE_TERMINATION_REASON = "explicit_outcome"


@dataclass(frozen=True)
class NarrativeInteractiveMenuItem:
    """One numbered structural path with an exact P11.6H request mapping."""

    number: int
    choice: NarrativeIdentity
    path_index: int
    path_label: str
    destination: NarrativeIdentity

    def __post_init__(self) -> None:
        if type(self.number) is not int or self.number < 1:
            raise ValueError("menu item number must be a positive exact int.")
        if type(self.choice) is not NarrativeIdentity or self.choice.kind != "choice":
            raise TypeError("menu item choice must be a choice identity.")
        if type(self.path_index) is not int or self.path_index < 0:
            raise ValueError("menu item path index must be non-negative.")
        if type(self.path_label) is not str or not self.path_label:
            raise ValueError("menu item path label must be non-empty.")
        if (
            type(self.destination) is not NarrativeIdentity
            or self.destination.kind != "scene"
        ):
            raise TypeError("menu item destination must be a scene identity.")

    @property
    def request(self) -> NarrativeSessionStepRequest:
        return NarrativeSessionStepRequest(self.choice, self.path_index)


def _path_key(
    path: NarrativeExecutableChoicePath,
) -> tuple[str, tuple[str, ...], int]:
    return path.choice.kind, path.choice.path, path.path_index


def _identity_text(identity: NarrativeIdentity) -> str:
    return f"{identity.kind}:{'/'.join(identity.path)}"


def _require_association(
    material: NarrativeSessionMaterial,
    session: NarrativeSession,
) -> None:
    """Fail closed on the artifact/session association before interaction."""

    if type(material) is not NarrativeSessionMaterial:
        raise TypeError("material must be exact NarrativeSessionMaterial.")
    if type(session) is not NarrativeSession:
        raise TypeError("session must be exact NarrativeSession.")
    if session.artifact_fingerprint != material.artifact_fingerprint:
        raise NarrativeSessionError("artifact_mismatch")
    if session.story != material.story:
        raise NarrativeSessionError("story_mismatch")
    if session.state.current_scene not in material.scenes:
        raise NarrativeSessionError("malformed_session")


def narrative_interactive_menu(
    material: NarrativeSessionMaterial,
    session: NarrativeSession,
) -> tuple[NarrativeInteractiveMenuItem, ...]:
    """Return current-scene paths in explicit canonical identity/index order."""

    _require_association(material, session)
    current_paths = sorted(
        (
            path
            for path in material.bindings.paths
            if path.source_scene == session.state.current_scene
        ),
        key=_path_key,
    )
    return tuple(
        NarrativeInteractiveMenuItem(
            number=number,
            choice=path.choice,
            path_index=path.path_index,
            path_label=path.path_label,
            destination=path.destination,
        )
        for number, path in enumerate(current_paths, start=1)
    )


def _write_state(
    material: NarrativeSessionMaterial,
    session: NarrativeSession,
    output_stream: TextIO,
) -> tuple[NarrativeInteractiveMenuItem, ...]:
    state = session.state
    output_stream.write("ApexForge narrative session\n")
    output_stream.write(f"Story: {_identity_text(state.story)}\n")
    output_stream.write(f"Scene: {_identity_text(state.current_scene)}\n")
    output_stream.write(f"Status: {state.termination.status}\n")
    if state.termination.reason is not None:
        output_stream.write(f"Termination reason: {state.termination.reason}\n")
    output_stream.write(f"Transitions: {len(state.choice_history)}\n")
    output_stream.write("Facts:\n")
    if state.facts:
        for fact in state.facts:
            output_stream.write(
                f"  {_identity_text(fact.subject)}:{fact.name}={fact.value}\n"
            )
    else:
        output_stream.write("  (none)\n")

    if state.termination.is_terminated:
        output_stream.write("Choices:\n  (session terminated)\n")
        return ()

    menu = narrative_interactive_menu(material, session)
    output_stream.write("Choices:\n")
    if not menu:
        output_stream.write("  (none)\n")
    for item in menu:
        label = json.dumps(item.path_label, ensure_ascii=False)
        output_stream.write(
            f"  {item.number}. {_identity_text(item.choice)} "
            f"path[{item.path_index}] {label} -> "
            f"{_identity_text(item.destination)}\n"
        )
    return menu


def run_narrative_interactive_session(
    material: NarrativeSessionMaterial,
    session: NarrativeSession,
    session_path: Union[str, Path],
    *,
    input_stream: TextIO,
    output_stream: TextIO,
) -> NarrativeSession:
    """Run a human-controlled loop over one already-existing P11.6H session."""

    _require_association(material, session)
    current = session
    while True:
        menu = _write_state(material, current, output_stream)
        if current.state.termination.is_terminated:
            output_stream.write("Session is already terminated; interaction closed.\n")
            return current

        output_stream.write("Command (menu number, terminate, quit): ")
        command = input_stream.readline()
        if command == "":
            output_stream.write("Input closed; session unchanged.\n")
            return current
        command = command.strip()

        if command == "quit":
            output_stream.write("Interactive session closed.\n")
            return current

        if command == "terminate":
            terminated = terminate_narrative_session(
                material,
                current,
                NarrativeSessionTerminateRequest(
                    INTERACTIVE_TERMINATION_REASON
                ),
            )
            write_narrative_session_atomic(terminated, session_path)
            current = terminated
            _write_state(material, current, output_stream)
            output_stream.write("Narrative terminated.\n")
            return current

        if not command.isascii() or not command.isdecimal():
            output_stream.write(
                "Invalid input; enter a menu number, terminate, or quit.\n"
            )
            continue

        selection = int(command)
        if selection < 1 or selection > len(menu):
            output_stream.write("Selection out of range; no action taken.\n")
            continue

        selected = menu[selection - 1]
        result = step_narrative_session(material, current, selected.request)
        if result.session is None:
            payload = narrative_session_step_result_bytes(result).decode("utf-8")
            output_stream.write("Step failed; session unchanged.\n")
            output_stream.write(payload)
            continue

        next_session = result.session
        write_narrative_session_atomic(next_session, session_path)
        current = next_session


def interact_narrative_session(
    artifact_path: Union[str, Path],
    session_path: Union[str, Path],
    *,
    input_stream: TextIO,
    output_stream: TextIO,
) -> NarrativeSession:
    """Load and interact with one existing artifact-associated H session."""

    material = load_narrative_session_material(artifact_path)
    session = load_narrative_session(session_path)
    return run_narrative_interactive_session(
        material,
        session,
        session_path,
        input_stream=input_stream,
        output_stream=output_stream,
    )


__all__ = (
    "INTERACTIVE_TERMINATION_REASON",
    "NarrativeInteractiveMenuItem",
    "interact_narrative_session",
    "narrative_interactive_menu",
    "run_narrative_interactive_session",
)
