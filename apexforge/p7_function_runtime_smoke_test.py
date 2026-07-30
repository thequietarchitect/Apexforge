"""Smoke test for AFP-P7.1C immutable call frames and execution."""

from __future__ import annotations

from air.linker import link_programs
from air.model import AIRProgram, VerifiedAIRProgram
from authority.engine import AuthorityEngine
from authority.model import AuthorityGrant
from language.compiler import compile_source
from language.validation.runtime_validator import RuntimeValidator
from runtime.context import ExecutionContext
from runtime.engine import RuntimeEngine
from runtime.state import StateSnapshot


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


LEFT_SOURCE = """
function left(value) {
    return value
}
"""


RIGHT_SOURCE = """
function right(value) {
    return value
}
"""


COMBINE_SOURCE = """
function combine(first, second) {
    return first * 10 + second
}
"""


COUNTER_SOURCE = """
directive Counter {
    state count = 3
    event Updated

    cause update {
        path normal @ 10 {
            set count = increase(count)

            when combine(left(1), right(2)) == 12 {
                message "Count: " + count
                emit Updated
            }
            otherwise {
                add count 1000
            }
        }
    }
}
"""


EXPLODE_SOURCE = """
function explode(value) {
    return value / 0
}
"""


ROLLBACK_SOURCE = """
directive Rollback {
    state count = 3

    cause update {
        path normal @ 10 {
            add count 2
            set count = explode(count)
        }
    }
}
"""


WRONG_ARITY_SOURCE = """
directive WrongArity {
    state count = 3

    cause update {
        path normal @ 10 {
            set count = double(count, count)
        }
    }
}
"""


RECURSIVE_SOURCE = """
function recursive(value) {
    return recursive(value)
}
"""


RECURSIVE_DIRECTIVE_SOURCE = """
directive RecursiveCaller {
    state count = 3

    cause update {
        path normal @ 10 {
            set count = recursive(count)
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


def compile_program(
    source: str,
) -> AIRProgram:
    compiled = compile_source(source)

    require(
        isinstance(compiled, AIRProgram),
        "source unit must compile to AIRProgram",
    )

    return compiled


def grant(
    directive_name: str,
) -> AuthorityGrant:
    return AuthorityGrant(
        principal=f"principal:{directive_name}",
        capability=f"directive.invoke:{directive_name}",
        resource=f"directive:{directive_name}",
    )


def execute(
    program: AIRProgram,
    *,
    entry: str,
    validate: bool = True,
):
    verified = (
        RuntimeValidator().validate(program)
        if validate
        else VerifiedAIRProgram(program)
    )

    return RuntimeEngine().execute(
        verified,
        ExecutionContext(
            state=StateSnapshot.from_program_initials(
                program
            ),
            authority=AuthorityEngine.from_grants(
                (grant(entry),)
            ),
        ),
        entry_directives=(entry,),
    )


def step_facts(
    step,
) -> dict[str, object]:
    return {
        fact.key: fact.value
        for fact in step.facts
    }


def main() -> None:
    linked = link_programs(
        compile_program(DOUBLE_SOURCE),
        compile_program(INCREASE_SOURCE),
        compile_program(LEFT_SOURCE),
        compile_program(RIGHT_SOURCE),
        compile_program(COMBINE_SOURCE),
        compile_program(COUNTER_SOURCE),
    )

    result = execute(
        linked,
        entry="Counter",
    )

    require(
        result.ok,
        f"pure function execution failed: {result.diagnostics}",
    )
    require(
        result.final_state.get_int("count") == 7,
        "nested function result did not update state to seven",
    )
    require(
        tuple(
            assignment.value
            for assignment in result.delta.assignments
        ) == (7,),
        "evaluated function assignment was not preserved in the delta",
    )
    require(
        len(result.delta.events) == 1,
        "function-driven conditional did not emit exactly one event",
    )

    message = next(
        fact.value
        for fact in result.delta.events[0].facts
        if fact.key == "message"
    )
    require(
        message == "Count: 7",
        "function result was not visible to the following event expression",
    )

    starts = [
        step_facts(step)
        for step in result.trace.steps
        if step.kind == "function.call.start"
    ]
    finishes = [
        step_facts(step)
        for step in result.trace.steps
        if step.kind == "function.call.finish"
    ]

    require(
        tuple(item["name"] for item in starts)
        == (
            "increase",
            "double",
            "left",
            "right",
            "combine",
        ),
        "function arguments were not evaluated left-to-right",
    )
    require(
        tuple(item["depth"] for item in starts[:2])
        == (0, 1),
        "nested function call frames did not preserve stack depth",
    )
    require(
        tuple(item["name"] for item in finishes[:2])
        == (
            "double",
            "increase",
        ),
        "nested function frames did not return in stack order",
    )

    rollback_program = link_programs(
        compile_program(EXPLODE_SOURCE),
        compile_program(ROLLBACK_SOURCE),
    )
    rollback = execute(
        rollback_program,
        entry="Rollback",
    )

    require(
        not rollback.ok,
        "division-by-zero inside a function must fail its directive path",
    )
    require(
        rollback.final_state.get_int("count") == 3,
        "function failure did not roll back the earlier candidate assignment",
    )
    require(
        rollback.delta.is_empty,
        "function failure must return an empty transactional delta",
    )
    require(
        any(
            diagnostic.code == "RUN002"
            for diagnostic in rollback.diagnostics
        ),
        "function failure did not produce RUN002",
    )
    require(
        "function.call.abort"
        in tuple(step.kind for step in rollback.trace.steps),
        "function failure trace is missing function.call.abort",
    )

    # Runtime arity defense remains active even when a caller bypasses the
    # validator and constructs VerifiedAIRProgram directly.
    malformed_arity = link_programs(
        compile_program(DOUBLE_SOURCE),
        compile_program(WRONG_ARITY_SOURCE),
    )
    arity_result = execute(
        malformed_arity,
        entry="WrongArity",
        validate=False,
    )
    require(
        not arity_result.ok,
        "runtime must reject malformed function arity defensively",
    )
    require(
        arity_result.final_state.get_int("count") == 3,
        "runtime arity rejection must preserve the input state",
    )
    require(
        any(
            "expects 1 argument(s), received 2"
            in diagnostic.message
            for diagnostic in arity_result.diagnostics
        ),
        "runtime arity diagnostic is not specific",
    )

    # Runtime cycle defense is also retained even though P7.1B validation
    # rejects recursive call graphs.
    malformed_recursive = link_programs(
        compile_program(RECURSIVE_SOURCE),
        compile_program(RECURSIVE_DIRECTIVE_SOURCE),
    )
    recursive_result = execute(
        malformed_recursive,
        entry="RecursiveCaller",
        validate=False,
    )
    require(
        not recursive_result.ok,
        "runtime must reject a recursive function cycle defensively",
    )
    require(
        recursive_result.final_state.get_int("count") == 3,
        "runtime recursion rejection must preserve the input state",
    )
    require(
        any(
            "function recursion detected at runtime"
            in diagnostic.message
            for diagnostic in recursive_result.diagnostics
        ),
        "runtime recursion diagnostic is not specific",
    )

    print("AFP-P7.1C function runtime smoke test passed.")
    print("Immutable parameter binding: PASS")
    print("Nested call-frame execution: PASS")
    print("Left-to-right argument evaluation: PASS")
    print("Function trace boundaries: PASS")
    print("Transactional rollback: PASS")
    print("Runtime arity defense: PASS")
    print("Runtime recursion defense: PASS")


if __name__ == "__main__":
    main()