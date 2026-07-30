"""AFP-P8.5 typed state operation and runtime storage smoke test."""

from __future__ import annotations

from air.expressions import (
    AIRBooleanLiteral,
    AIRIntegerLiteral,
    AIRStringLiteral,
)
from air.model import (
    AIRProgram,
    StateAssignment,
    StateDefinition,
)
from air.types import AIR_VERSION
from language.compiler import CompilerError, compile_source
from language.validation.runtime_validator import (
    InvalidValueError,
    RuntimeValidator,
)
from runtime.state import StateDelta, StateSnapshot
from type_system.model import BOOL, FLOAT, INT, STRING


TYPED_DIRECTIVE_SOURCE = """
directive TypedState {
    state enabled : bool = false
    state label : string = "idle"
    state count : int = 1

    cause update {
        path primary @ 10 {
            set enabled = true
            set label = "ready"
            add count 2

            when enabled {
                set label = "active"
            }
        }
    }
}
"""


LEGACY_DIRECTIVE_SOURCE = """
directive LegacyCounter {
    state count = 1

    cause update {
        path primary @ 10 {
            set count = 2
            add count 3
        }
    }
}
"""


def require(
    condition: bool,
    message: str,
) -> None:
    if not condition:
        raise AssertionError(message)


def require_compiler_error(
    source: str,
    expected_code: str,
) -> CompilerError:
    try:
        compile_source(source)
    except CompilerError as error:
        require(
            error.diagnostic.code == expected_code,
            (
                f"expected compiler diagnostic {expected_code}, "
                f"received {error.diagnostic.code}"
            ),
        )
        return error

    raise AssertionError(
        f"source unexpectedly compiled: {source!r}"
    )


def collect_assignment_operations(
    actions: tuple[object, ...],
) -> tuple[str, ...]:
    """Collect assignment operations from the ordered action tree."""

    operations: list[str] = []

    for action in tuple(actions):
        action_type = type(action).__name__

        if action_type == "StateAssignment":
            operations.append(action.operation)
            continue

        if action_type == "AIRWhenAction":
            operations.extend(
                collect_assignment_operations(
                    tuple(
                        getattr(
                            action,
                            "actions",
                            (),
                        ) or ()
                    )
                )
            )
            operations.extend(
                collect_assignment_operations(
                    tuple(
                        getattr(
                            action,
                            "otherwise_actions",
                            (),
                        ) or ()
                    )
                )
            )

    return tuple(operations)


def minimal_program(
    *,
    states: tuple[StateDefinition, ...],
) -> AIRProgram:
    return AIRProgram(
        version=AIR_VERSION,
        states=states,
        events=(),
        authority_checks=(),
        causal_decisions=(),
        directives=(),
        requirements=(),
    )


def main() -> None:
    typed = compile_source(
        TYPED_DIRECTIVE_SOURCE
    )
    path = typed.causal_decisions[0].paths[0]
    operations = collect_assignment_operations(
        tuple(path.actions)
    )
    require(
        operations == (
            "set_bool",
            "set_string",
            "add_int",
            "set_string",
        ),
        f"typed assignment operations changed: {operations!r}",
    )

    require(
        tuple(
            state.value_type
            for state in typed.states
        ) == (
            BOOL,
            STRING,
            INT,
        ),
        "typed state identities were not preserved",
    )

    legacy = compile_source(
        LEGACY_DIRECTIVE_SOURCE
    )
    legacy_operations = collect_assignment_operations(
        tuple(
            legacy.causal_decisions[0].paths[0].actions
        )
    )
    require(
        legacy_operations == (
            "set_int",
            "add_int",
        ),
        "legacy integer assignment operations changed",
    )

    require_compiler_error(
        """
        directive InvalidAdd {
            state enabled : bool = false
            cause update {
                path primary @ 10 {
                    add enabled true
                }
            }
        }
        """,
        "APX-TYPE-013",
    )

    require_compiler_error(
        """
        directive InvalidSet {
            state label : string = "idle"
            cause update {
                path primary @ 10 {
                    set label = true
                }
            }
        }
        """,
        "APX-TYPE-011",
    )

    require_compiler_error(
        """
        directive InvalidCondition {
            state label : string = "idle"
            cause update {
                path primary @ 10 {
                    when label {
                        set label = "ready"
                    }
                }
            }
        }
        """,
        "APX-TYPE-012",
    )

    program = minimal_program(
        states=(
            StateDefinition(
                id="state:enabled",
                initial=AIRBooleanLiteral(False),
                value_type=BOOL,
            ),
            StateDefinition(
                id="state:label",
                initial=AIRStringLiteral("idle"),
                value_type=STRING,
            ),
            StateDefinition(
                id="state:count",
                initial=AIRIntegerLiteral(1),
                value_type=INT,
            ),
            StateDefinition(
                id="state:ratio",
                initial=1.5,
                value_type=FLOAT,
            ),
        )
    )

    RuntimeValidator().validate(
        program
    )

    snapshot = StateSnapshot.from_program_initials(
        program
    )
    require(
        snapshot.get_bool("enabled") is False,
        "Boolean program initializer changed",
    )
    require(
        snapshot.get_string("label") == "idle",
        "string program initializer changed",
    )
    require(
        snapshot.get_int("count") == 1,
        "integer program initializer changed",
    )
    require(
        snapshot.get_float("ratio") == 1.5,
        "float program initializer changed",
    )

    updated = snapshot.apply(
        StateDelta(
            assignments=(
                StateAssignment(
                    state="state:enabled",
                    operation="set_bool",
                    value=True,
                ),
                StateAssignment(
                    state="state:label",
                    operation="set_string",
                    value="ready",
                ),
                StateAssignment(
                    state="state:count",
                    operation="add_int",
                    value=4,
                ),
                StateAssignment(
                    state="state:ratio",
                    operation="add_float",
                    value=0.25,
                ),
            )
        )
    )

    require(
        updated.get_bool("enabled") is True,
        "Boolean state assignment failed",
    )
    require(
        updated.get_string("label") == "ready",
        "string state assignment failed",
    )
    require(
        updated.get_int("count") == 5,
        "integer addition failed",
    )
    require(
        updated.get_float("ratio") == 1.75,
        "float addition failed",
    )

    malformed_assignment = StateAssignment(
        state="state:enabled",
        operation="set_int",
        value=AIRIntegerLiteral(1),
    )
    malformed_program = minimal_program(
        states=(
            StateDefinition(
                id="state:enabled",
                initial=AIRBooleanLiteral(False),
                value_type=BOOL,
            ),
        )
    )

    # Attach the malformed assignment through a lightweight path-shaped unit.
    from causality.model import CausalDecision, CausalPath

    malformed_program = AIRProgram(
        version=AIR_VERSION,
        states=malformed_program.states,
        events=(),
        authority_checks=(),
        causal_decisions=(
            CausalDecision(
                id="cause:bad",
                cause="bad",
                policy="max_weight",
                paths=(
                    CausalPath(
                        id="path:bad",
                        weight=1,
                        assignments=(malformed_assignment,),
                        emits=(),
                        invocations=(),
                        effects=(),
                        rationale="",
                        actions=(malformed_assignment,),
                    ),
                ),
            ),
        ),
        directives=(),
        requirements=(),
    )

    try:
        RuntimeValidator().validate(
            malformed_program
        )
    except InvalidValueError:
        pass
    else:
        raise AssertionError(
            "validator accepted an integer operation for a bool state"
        )

    print("AFP-P8.5 typed state semantics smoke test passed.")
    print("Typed AIR assignment operations: PASS")
    print("Directive mutation type checking: PASS")
    print("Directive condition type checking: PASS")
    print("Legacy integer compatibility: PASS")
    print("Typed runtime state storage: PASS")
    print("Typed state delta application: PASS")
    print("Validator operation/type agreement: PASS")


if __name__ == "__main__":
    main()