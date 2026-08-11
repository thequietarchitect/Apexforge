"""Deterministic human-driven P11.6I narrative session interaction.

This module writes P11.6J presentation for the current scene and maps one
explicit human menu selection to one exact P11.6H step request.  It does not
evaluate conditions, apply consequences, choose paths, infer termination, or
own persistence semantics.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TextIO, Union

from language.narrative_model import NarrativeIdentity
from tooling.narrative_rendering import (
    NarrativeSessionPresentation,
    narrative_session_presentation,
    render_narrative_presentation,
)
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
    presentation = narrative_session_presentation(material, session)
    return _interactive_menu(presentation)


def _interactive_menu(
    presentation: NarrativeSessionPresentation,
) -> tuple[NarrativeInteractiveMenuItem, ...]:
    """Map J presentation entries to I's exact step-request records."""

    return tuple(
        NarrativeInteractiveMenuItem(
            number=choice.number,
            choice=choice.choice,
            path_index=choice.path_index,
            path_label=choice.path_label,
            destination=choice.destination,
        )
        for choice in presentation.choices
    )


def _write_state(
    material: NarrativeSessionMaterial,
    session: NarrativeSession,
    output_stream: TextIO,
) -> tuple[NarrativeInteractiveMenuItem, ...]:
    presentation = narrative_session_presentation(material, session)
    output_stream.write(render_narrative_presentation(presentation))
    return _interactive_menu(presentation)


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
