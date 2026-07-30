"""Smoke test for AFP-P7.1B function linking and validation."""

from __future__ import annotations

from air.linker import (
    DuplicateLinkDefinitionError,
    link_programs,
)
from air.model import AIRProgram
from language.compiler import compile_source
from language.validation.runtime_validator import (
    InvalidValueError,
    RuntimeValidator,
    UndefinedReferenceError,
)


DOUBLE_SOURCE = """
function double(value) {
    return value * 2
}
"""


INCREASE_SOURCE = """
function increase(value) {
    return double(value) + 1
}
"""


COUNTER_SOURCE = """
directive Counter {
    state count = 3

    cause update {
        path normal @ 10 {
            set count = increase(count)
        }
    }
}
"""


UNDEFINED_SOURCE = """
function broken(value) {
    return missing(value)
}
"""


ARITY_SOURCE = """
function wrong(value) {
    return double(value, value)
}
"""


DIRECT_RECURSION_SOURCE = """
function loop(value) {
    return loop(value)
}
"""


INDIRECT_A_SOURCE = """
function cycle_left(value) {
    return cycle_right(value)
}
"""


INDIRECT_B_SOURCE = """
function cycle_right(value) {
    return cycle_left(value)
}
"""


STATE_LEAK_SOURCE = """
function hidden_state(value) {
    return count + value
}
"""


def require(
    condition: bool,
    message: str,
) -> None:
    if not condition:
        raise AssertionError(message)


def require_raises(
    expected_type: type[BaseException],
    operation,
    message: str,
) -> BaseException:
    try:
        operation()
    except expected_type as exc:
        return exc

    raise AssertionError(message)


def compile_program(
    source: str,
) -> AIRProgram:
    program = compile_source(source)

    require(
        isinstance(program, AIRProgram),
        "P7 source unit must compile to AIRProgram",
    )

    return program


def main() -> None:
    double = compile_program(DOUBLE_SOURCE)
    increase = compile_program(INCREASE_SOURCE)
    counter = compile_program(COUNTER_SOURCE)

    require(
        double.functions[0].order == 0,
        "separate function units must begin at local order zero",
    )
    require(
        increase.functions[0].order == 0,
        "separate function units must begin at local order zero",
    )

    linked = link_programs(
        double,
        increase,
        counter,
    )

    require(
        tuple(
            function.id
            for function in linked.functions
        ) == (
            "function:double",
            "function:increase",
        ),
        "linked function order is not deterministic",
    )
    require(
        tuple(
            function.order
            for function in linked.functions
        ) == (
            0,
            1,
        ),
        "linker did not assign unique global function orders",
    )

    verified = RuntimeValidator().validate(
        linked
    )
    require(
        verified.program is linked,
        "validator did not preserve the linked AIRProgram identity",
    )

    require_raises(
        DuplicateLinkDefinitionError,
        lambda: link_programs(
            double,
            double,
        ),
        "linker must reject duplicate function definitions",
    )

    undefined = compile_program(
        UNDEFINED_SOURCE
    )
    require_raises(
        UndefinedReferenceError,
        lambda: RuntimeValidator().validate(
            undefined
        ),
        "validator must reject undefined function calls",
    )

    wrong_arity = compile_program(
        ARITY_SOURCE
    )
    require_raises(
        InvalidValueError,
        lambda: RuntimeValidator().validate(
            link_programs(
                double,
                wrong_arity,
            )
        ),
        "validator must reject function arity mismatches",
    )

    direct_recursion = compile_program(
        DIRECT_RECURSION_SOURCE
    )
    direct_error = require_raises(
        InvalidValueError,
        lambda: RuntimeValidator().validate(
            direct_recursion
        ),
        "validator must reject direct recursion",
    )
    require(
        "Recursive function cycle" in str(direct_error),
        "direct-recursion diagnostic is not specific",
    )

    indirect_error = require_raises(
        InvalidValueError,
        lambda: RuntimeValidator().validate(
            link_programs(
                compile_program(INDIRECT_A_SOURCE),
                compile_program(INDIRECT_B_SOURCE),
            )
        ),
        "validator must reject indirect recursion",
    )
    require(
        "cycle_left -> cycle_right -> cycle_left"
        in str(indirect_error),
        "indirect-recursion diagnostic did not preserve cycle order",
    )

    state_leak = compile_program(
        STATE_LEAK_SOURCE
    )
    require_raises(
        UndefinedReferenceError,
        lambda: RuntimeValidator().validate(
            link_programs(
                counter,
                state_leak,
            )
        ),
        "pure functions must not read hidden global state",
    )

    print("AFP-P7.1B function linking/validation smoke test passed.")
    print("Deterministic function linking: PASS")
    print("Cross-unit function resolution: PASS")
    print("Arity validation: PASS")
    print("Undefined-function rejection: PASS")
    print("Direct recursion rejection: PASS")
    print("Indirect recursion rejection: PASS")
    print("Pure parameter scope: PASS")


if __name__ == "__main__":
    main()