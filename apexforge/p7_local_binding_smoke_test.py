"""Smoke test for AFP-P7.2A ordered immutable local bindings."""

from __future__ import annotations

from air.linker import link_programs
from air.model import AIRProgram
from authority.engine import AuthorityEngine
from authority.model import AuthorityGrant
from language.compiler import CompilerError, compile_source
from language.validation.runtime_validator import (
    RuntimeValidator,
    UndefinedReferenceError,
)
from runtime.call_stack import CallFrame
from runtime.context import ExecutionContext
from runtime.engine import RuntimeEngine
from runtime.state import StateSnapshot


DOUBLE_SOURCE = """
function double(value) {
    return value * 2
}
"""


ADJUST_SOURCE = """
function adjust(value) {
    let doubled = double(value)
    let adjusted = doubled + 1
    return adjusted
}
"""


COUNTER_SOURCE = """
directive Counter {
    state count = 3

    cause update {
        path normal @ 10 {
            set count = adjust(count)
        }
    }
}
"""


FORWARD_REFERENCE_SOURCE = """
function forward(value) {
    let first = second + value
    let second = 2
    return first
}
"""


DUPLICATE_LOCAL_SOURCE = """
function duplicate(value) {
    let result = value + 1
    let result = result + 1
    return result
}
"""


SHADOW_SOURCE = """
function shadow(value) {
    let value = 7
    return value
}
"""


EXPLODE_SOURCE = """
function explode(value) {
    let zero = value - value
    let failed = value / zero
    return failed
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
    adjust = compile_program(ADJUST_SOURCE)
    function = adjust.functions[0]

    require(
        tuple(binding.name for binding in function.local_bindings)
        == ("doubled", "adjusted"),
        "compiler did not preserve local declaration order",
    )

    linked = link_programs(
        compile_program(DOUBLE_SOURCE),
        adjust,
        compile_program(COUNTER_SOURCE),
    )
    result = execute(linked, "Counter")

    require(result.ok, f"local-binding execution failed: {result.diagnostics}")
    require(
        result.final_state.get_int("count") == 7,
        "ordered local bindings did not produce count seven",
    )

    local_steps = [
        step for step in result.trace.steps
        if step.kind == "function.local.bind"
    ]
    local_names = tuple(
        next(fact.value for fact in step.facts if fact.key == "local")
        for step in local_steps
    )
    require(
        local_names == ("doubled", "adjusted"),
        "runtime did not bind locals in source order",
    )

    base_frame = CallFrame.bind(
        function=function,
        values=(3,),
        depth=0,
    )
    extended = base_frame.with_binding("doubled", 6)
    require(
        base_frame.try_resolve("doubled")[0] is False,
        "CallFrame.with_binding mutated the original frame",
    )
    require(
        extended.resolve("doubled") == 6,
        "extended frame did not contain the immutable local",
    )

    require_raises(
        UndefinedReferenceError,
        lambda: RuntimeValidator().validate(
            compile_program(FORWARD_REFERENCE_SOURCE)
        ),
        "validator must reject forward local references",
    )

    require_raises(
        CompilerError,
        lambda: compile_source(DUPLICATE_LOCAL_SOURCE),
        "compiler must reject duplicate local names",
    )
    require_raises(
        CompilerError,
        lambda: compile_source(SHADOW_SOURCE),
        "compiler must reject parameter shadowing",
    )

    rollback_program = link_programs(
        compile_program(EXPLODE_SOURCE),
        compile_program(ROLLBACK_SOURCE),
    )
    rollback = execute(rollback_program, "Rollback")
    require(not rollback.ok, "failing local expression must fail execution")
    require(
        rollback.final_state.get_int("count") == 3,
        "failing local expression did not roll back the directive path",
    )
    require(rollback.delta.is_empty, "failed local expression leaked a delta")

    print("AFP-P7.2A immutable local-binding smoke test passed.")
    print("Let syntax and AIR compilation: PASS")
    print("Ordered lexical scope: PASS")
    print("Immutable frame extension: PASS")
    print("Nested calls inside locals: PASS")
    print("Forward-reference rejection: PASS")
    print("Duplicate/shadow rejection: PASS")
    print("Transactional rollback: PASS")


if __name__ == "__main__":
    main()