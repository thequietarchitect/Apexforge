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
    if not condition:
        raise AssertionError(
            message
        )


def require_raises(
    expected_type: type[BaseException],
    function,
    message: str,
) -> None:
    try:
        function()
    except expected_type:
        return

    raise AssertionError(
        message
    )


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
    effects_annotation = get_type_hints(
        StateDelta
    )["effects"]

    require(
        get_origin(effects_annotation) is tuple
        and get_args(effects_annotation) == (EffectIntent, Ellipsis),
        "StateDelta does not bind effects.model.EffectIntent",
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

    boolean_state = StateSnapshot.from_mapping(
        {
            "state:flag": True,
        }
    )

    require(
        boolean_state.get_bool(
            "flag"
        ) is True,
        "bool state value was not preserved",
    )

    require_raises(
        TypeError,
        lambda: boolean_state.get_int(
            "flag"
        ),
        "bool must not be accepted through the integer state accessor",
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
    print("Duplicate and exact typed-accessor rejection: PASS")


if __name__ == "__main__":
    main()