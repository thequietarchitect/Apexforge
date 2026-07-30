"""Smoke test for AFP-P7.2C pure-function control-flow hardening."""

from __future__ import annotations

from air.expressions import (
    AIRBooleanLiteral,
    AIRIdentifierReference,
    AIRIntegerLiteral,
)
from air.functions import (
    AIRFunction,
    AIRFunctionReturn,
    AIRFunctionWhen,
    AIRLocalBinding,
    AIRParameter,
)
from air.model import AIRProgram, StateAssignment
from air.types import AIR_VERSION
from language.compiler import CompilerError, compile_source
from language.validation.runtime_validator import (
    InvalidValueError,
    RuntimeValidator,
    UndefinedReferenceError,
)


UNREACHABLE_SOURCE = """
function unreachable(value) {
    return value
    let never = value + 1
}
"""


UNREACHABLE_AFTER_BRANCH_SOURCE = """
function unreachableAfterBranch(value) {
    when value > 0 {
        return value
    }
    otherwise {
        return 0
    }

    let never = value + 1
}
"""


VALID_FALLTHROUGH_SOURCE = """
function absolute(value) {
    when value >= 0 {
        return value
    }

    return 0 - value
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


def program_with(function: AIRFunction) -> AIRProgram:
    return AIRProgram(
        version=AIR_VERSION,
        states=(),
        events=(),
        authority_checks=(),
        causal_decisions=(),
        directives=(),
        requirements=(),
        functions=(function,),
    )


def function(
    name: str,
    body: tuple[object, ...],
    *,
    parameters: tuple[AIRParameter, ...] = (
        AIRParameter(name="value"),
    ),
) -> AIRFunction:
    return AIRFunction(
        id=f"function:{name}",
        name=name,
        parameters=parameters,
        return_expression=AIRIntegerLiteral(0),
        order=0,
        local_bindings=(),
        body=body,
    )


def returned(value: int = 0) -> AIRFunctionReturn:
    return AIRFunctionReturn(
        expression=AIRIntegerLiteral(value),
    )


def main() -> None:
    compiler_error = require_raises(
        CompilerError,
        lambda: compile_source(UNREACHABLE_SOURCE),
        "compiler must reject source statements after return",
    )
    require(
        compiler_error.diagnostic.code == "APX-COMPILE-012",
        "unreachable-source diagnostic code changed",
    )

    branch_compiler_error = require_raises(
        CompilerError,
        lambda: compile_source(UNREACHABLE_AFTER_BRANCH_SOURCE),
        "compiler must reject statements after a fully returning conditional",
    )
    require(
        branch_compiler_error.diagnostic.code == "APX-COMPILE-012",
        "conditional unreachable-source diagnostic code changed",
    )

    RuntimeValidator().validate(
        compile_source(VALID_FALLTHROUGH_SOURCE)
    )

    complete = function(
        "complete",
        (
            AIRFunctionWhen(
                condition=AIRBooleanLiteral(True),
                actions=(returned(1),),
                otherwise_actions=(returned(0),),
            ),
        ),
    )
    RuntimeValidator().validate(program_with(complete))

    fallthrough = function(
        "fallthrough",
        (
            AIRFunctionWhen(
                condition=AIRBooleanLiteral(True),
                actions=(returned(1),),
                otherwise_actions=(),
            ),
            returned(0),
        ),
    )
    RuntimeValidator().validate(program_with(fallthrough))

    unreachable_air = function(
        "unreachableAir",
        (
            returned(1),
            AIRLocalBinding(
                name="never",
                expression=AIRIntegerLiteral(2),
            ),
        ),
    )
    unreachable_error = require_raises(
        InvalidValueError,
        lambda: RuntimeValidator().validate(
            program_with(unreachable_air)
        ),
        "validator must reject unreachable hand-authored AIR",
    )
    require(
        "unreachable" in str(unreachable_error).lower(),
        "unreachable AIR diagnostic is not explicit",
    )

    branch_scope = function(
        "branchScope",
        (
            AIRFunctionWhen(
                condition=AIRBooleanLiteral(True),
                actions=(
                    AIRLocalBinding(
                        name="hidden",
                        expression=AIRIntegerLiteral(1),
                    ),
                ),
                otherwise_actions=(),
            ),
            AIRFunctionReturn(
                expression=AIRIdentifierReference("hidden"),
            ),
        ),
    )
    require_raises(
        UndefinedReferenceError,
        lambda: RuntimeValidator().validate(
            program_with(branch_scope)
        ),
        "branch-local names must not escape their branch",
    )

    nested: tuple[object, ...] = (returned(1),)
    for _ in range(66):
        nested = (
            AIRFunctionWhen(
                condition=AIRBooleanLiteral(True),
                actions=nested,
                otherwise_actions=(returned(0),),
            ),
        )

    too_deep = function(
        "tooDeep",
        nested,
    )
    depth_error = require_raises(
        InvalidValueError,
        lambda: RuntimeValidator().validate(
            program_with(too_deep)
        ),
        "validator must reject over-depth function conditionals",
    )
    require(
        "nesting depth" in str(depth_error),
        "conditional-depth diagnostic is not explicit",
    )

    malformed_stream = function(
        "malformedStream",
        (
            AIRFunctionWhen(
                condition=AIRBooleanLiteral(True),
                actions="not-an-action-stream",
                otherwise_actions=(returned(0),),
            ),
        ),
    )
    malformed_error = require_raises(
        InvalidValueError,
        lambda: RuntimeValidator().validate(
            program_with(malformed_stream)
        ),
        "validator must reject malformed function statement streams",
    )
    require(
        "statement stream" in str(malformed_error),
        "malformed-stream diagnostic is not explicit",
    )

    impure = function(
        "impure",
        (
            StateAssignment(
                state="state:value",
                operation="set_int",
                value=AIRIntegerLiteral(1),
            ),
            returned(0),
        ),
    )
    purity_error = require_raises(
        InvalidValueError,
        lambda: RuntimeValidator().validate(
            program_with(impure)
        ),
        "validator must reject directive actions inside pure functions",
    )
    require(
        "pure functions may contain only" in str(purity_error).lower(),
        "pure-function boundary diagnostic is not explicit",
    )

    print("AFP-P7.2C function control-flow smoke test passed.")
    print("Unreachable-source rejection: PASS")
    print("Unreachable AIR rejection: PASS")
    print("Complete-path return analysis: PASS")
    print("Fallthrough return analysis: PASS")
    print("Branch-local scope isolation: PASS")
    print("Conditional-depth enforcement: PASS")
    print("Malformed AIR rejection: PASS")
    print("Pure-function boundary enforcement: PASS")


if __name__ == "__main__":
    main()