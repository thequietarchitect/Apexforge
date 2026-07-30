"""Smoke test for AFP-P7.2B pure-function conditionals and returns."""

from __future__ import annotations

from air.linker import link_programs
from air.model import AIRProgram
from authority.engine import AuthorityEngine
from authority.model import AuthorityGrant
from language.compiler import compile_source
from language.validation.runtime_validator import (
    RuntimeValidator,
    InvalidValueError,
    UndefinedReferenceError,
)
from runtime.context import ExecutionContext
from runtime.engine import RuntimeEngine
from runtime.state import StateSnapshot


BRANCH_SOURCE = """
function branchValue(value) {
    when value > 0 {
        let doubled = value * 2
        return doubled
    }
    otherwise {
        let magnitude = 0 - value
        return magnitude
    }
}
"""

FALLTHROUGH_SOURCE = """
function nonNegative(value) {
    when value > 0 {
        return value
    }
    return 0
}
"""

NESTED_SOURCE = """
function classify(value) {
    when value == 0 {
        return 100
    }
    otherwise {
        when value > 5 {
            return value + 10
        }
        otherwise {
            return value + 1
        }
    }
}
"""

COUNTER_SOURCE = """
directive Counter {
    state count = 3

    cause update {
        path normal @ 10 {
            set count = classify(branchValue(0 - count))
        }
    }
}
"""

INCOMPLETE_SOURCE = """
function incomplete(value) {
    when value > 0 {
        return value
    }
}
"""

LEAK_SOURCE = """
function leak(value) {
    when value > 0 {
        let hidden = value + 1
    }
    return hidden
}
"""

BAD_CONDITION_SOURCE = """
function badCondition(value) {
    when value {
        return 1
    }
    otherwise {
        return 0
    }
}
"""

ROLLBACK_SOURCE = """
directive Rollback {
    state count = 3

    cause update {
        path normal @ 10 {
            add count 2
            set count = badCondition(count)
        }
    }
}
"""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def require_raises(expected_type, operation, message: str):
    try:
        operation()
    except expected_type as exc:
        return exc
    raise AssertionError(message)


def compile_program(source: str) -> AIRProgram:
    program = compile_source(source)
    require(isinstance(program, AIRProgram), "source must compile to AIRProgram")
    return program


def grant(name: str) -> AuthorityGrant:
    return AuthorityGrant(
        principal=f"principal:{name}",
        capability=f"directive.invoke:{name}",
        resource=f"directive:{name}",
    )


def execute(program: AIRProgram, entry: str):
    verified = RuntimeValidator().validate(program)
    return RuntimeEngine().execute(
        verified,
        ExecutionContext(
            state=StateSnapshot.from_program_initials(program),
            authority=AuthorityEngine.from_grants((grant(entry),)),
        ),
        entry_directives=(entry,),
    )


def main() -> None:
    branch = compile_program(BRANCH_SOURCE)
    require(
        tuple(type(statement).__name__ for statement in branch.functions[0].body)
        == ("AIRFunctionWhen",),
        "compiler did not preserve function conditional body",
    )

    linked = link_programs(
        branch,
        compile_program(FALLTHROUGH_SOURCE),
        compile_program(NESTED_SOURCE),
        compile_program(COUNTER_SOURCE),
    )
    result = execute(linked, "Counter")
    require(result.ok, f"conditional execution failed: {result.diagnostics}")
    require(
        result.final_state.get_int("count") == 4,
        "nested function conditionals did not produce count four",
    )

    branch_steps = tuple(
        step for step in result.trace.steps
        if step.kind == "function.when.evaluate"
    )
    require(len(branch_steps) >= 3, "missing function conditional trace steps")
    require(
        any(step.kind == "function.return" for step in result.trace.steps),
        "missing function return trace step",
    )

    require_raises(
        InvalidValueError,
        lambda: RuntimeValidator().validate(
            compile_program(INCOMPLETE_SOURCE)
        ),
        "validator must reject incomplete function return paths",
    )
    require_raises(
        UndefinedReferenceError,
        lambda: RuntimeValidator().validate(
            compile_program(LEAK_SOURCE)
        ),
        "branch-local bindings must not escape lexical scope",
    )

    rollback_program = link_programs(
        compile_program(BAD_CONDITION_SOURCE),
        compile_program(ROLLBACK_SOURCE),
    )
    rollback = execute(rollback_program, "Rollback")
    require(not rollback.ok, "non-boolean function condition must fail")
    require(
        rollback.final_state.get_int("count") == 3,
        "failed function conditional did not roll back the directive path",
    )
    require(rollback.delta.is_empty, "failed conditional leaked a delta")

    # Ensure a conditional without otherwise can fall through to a later return.
    RuntimeValidator().validate(compile_program(FALLTHROUGH_SOURCE))

    print("AFP-P7.2B function conditional smoke test passed.")
    print("Conditional syntax and AIR: PASS")
    print("Multiple return paths: PASS")
    print("Nested function conditionals: PASS")
    print("Lexical branch scope: PASS")
    print("Definite-return validation: PASS")
    print("Conditional trace boundaries: PASS")
    print("Transactional rollback: PASS")


if __name__ == "__main__":
    main()