"""Focused smoke test for runtime-state and effect ownership."""

from __future__ import annotations

from typing import get_args, get_origin, get_type_hints

from air.expressions import AIRIntegerLiteral
from air.model import EventRecord, StateAssignment, facts
from causality.model import CausalPath
from effects.model import EffectIntent
from language.compiler import compile_source
from runtime.state import (
    StateCell,
    StateDelta,
    StateSnapshot,
)


SOURCE = """
directive Counter {
    state count = 2
    event updated

    cause start {
        path primary @ 1 {
            add count 1
            message "Count updated"
            emit updated
        }
    }
}
"""


def require(
    condition: bool,
    message: str,
) -> None:
    if condition:
        print(f"PASS: {message}")
        return

    print(f"FAIL: {message}")
    raise AssertionError(message)


def require_raises(
    expected_type: type[BaseException],
    function,
    message: str,
) -> None:
    try:
        function()
    except expected_type:
        print(f"PASS: {message}")
        return
    except Exception as exc:
        print(
            f"FAIL: {message} — expected "
            f"{expected_type.__name__}, received "
            f"{type(exc).__name__}: {exc}"
        )
        raise

    print(
        f"FAIL: {message} — expected "
        f"{expected_type.__name__}, but nothing was raised"
    )
    raise AssertionError(message)

def main() -> None:
    program = compile_source(
        SOURCE
    )

    require(
        isinstance(
            program.states[0].initial,
            AIRIntegerLiteral,
        ),
        "compiler must retain AFP-P2 AIRIntegerLiteral initialization",
    )

    initial = StateSnapshot.from_program_initials(
        program
    )

    require(
        initial.get_int(
            "state:count"
        ) == 2,
        "canonical state lookup failed",
    )
    require(
        initial.get_int(
            "count"
        ) == 2,
        "plain state alias lookup failed",
    )

    effect = EffectIntent(
        id="effect:audit",
        effect_type="audit.log",
        facts=facts(
            message="state changed",
        ),
    )

    event = EventRecord(
        id="event-record:updated",
        event="event:updated",
        directive="directive:Counter",
        principal="principal:Counter",
    )

    delta = StateDelta(
        assignments=(
            StateAssignment(
                state="state:count",
                operation="add_int",
                value=3,
            ),
        ),
        events=(
            event,
        ),
        effects=(
            effect,
        ),
    )

    updated = initial.apply(
        delta
    )

    require(
        initial.get_int(
            "count"
        ) == 2,
        "StateSnapshot.apply mutated the input snapshot",
    )
    require(
        updated.get_int(
            "count"
        ) == 5,
        "StateSnapshot.apply produced the wrong value",
    )
    require(
        not delta.is_empty,
        "non-empty StateDelta reported itself as empty",
    )
    require(
        StateDelta().is_empty,
        "empty StateDelta reported itself as non-empty",
    )

    path = CausalPath(
        id="path:effect",
        weight=1,
        effects=(
            effect,
        ),
    )

    require(
        path.effects[0] is effect,
        "CausalPath did not preserve canonical EffectIntent",
    )
   
    effect_hint = get_type_hints(
        StateDelta
    )["effects"]

    effect_args = get_args(
    effect_hint
)

    require(
        get_origin(effect_hint) in (
            tuple,
        )
            and len(effect_args) == 2
        and effect_args[0] is EffectIntent
        and effect_args[1] is Ellipsis,
        (
            "StateDelta effects annotation must contain the canonical "
            "effects.model.EffectIntent; "
            f"resolved annotation: {effect_hint!r}, "
            f"origin: {get_origin(effect_hint)!r}, "
            f"arguments: {effect_args!r}"
        ),
)

    require_raises(
        ValueError,
        lambda: StateSnapshot(
            (
                StateCell(
                    "state:count",
                    1,
                ),
                StateCell(
                    "state:count",
                    2,
                ),
            )
        ),
        "duplicate state cells must be rejected",
    )

    require_raises(
        TypeError,
        lambda: StateSnapshot.from_mapping(
            {
                "state:flag": True,
            }
        ),
        "bool must not be accepted as an integer state value",
    )

    require_raises(
        TypeError,
        lambda: initial.apply(
            StateDelta(
                assignments=(
                    StateAssignment(
                        state="state:count",
                        operation="add_int",
                        value=AIRIntegerLiteral(
                            value=1,
                        ),
                    ),
                )
            )
        ),
        "raw AIR expressions must be evaluated before StateSnapshot.apply",
    )

    print("Runtime-state consolidation smoke test passed.")
    print("AIRIntegerLiteral initialization: PASS")
    print("Canonical and plain state lookup: PASS")
    print("Immutable delta application: PASS")
    print("EffectIntent ownership: PASS")
    print("Duplicate and non-int rejection: PASS")


if __name__ == "__main__":
    main()