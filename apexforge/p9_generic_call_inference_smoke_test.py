"""AFP-P9.2 generic call-site inference and substitution smoke test."""

from __future__ import annotations

from air.expressions import (
    AIRBooleanLiteral,
    AIRCallExpression,
    AIRFloatLiteral,
    AIRIdentifierReference,
    AIRIntegerLiteral,
    AIRStringLiteral,
)
from air.linker import link_programs
from language.compiler import CompilerError, compile_source
from language.validation.runtime_validator import RuntimeValidator
from runtime.engine import RuntimeEngine
from runtime.state import StateSnapshot
from type_system.generics import ApexTypeVariable
from type_system.inference import (
    FunctionSignature,
    TypeInferenceError,
    infer_call_substitution,
    infer_expression_type,
    infer_expression_type_partial,
)
from type_system.model import BOOL, FLOAT, INT, STRING
from type_system.substitution import GenericSubstitution


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def require_type_error(operation, code: str) -> TypeInferenceError:
    try:
        operation()
    except TypeInferenceError as error:
        require(
            error.code == code,
            f"expected {code}, received {error.code}: {error}",
        )
        return error
    raise AssertionError(
        f"operation unexpectedly passed; expected {code}"
    )


def require_compile_error(
    source: str,
    *,
    signatures: dict[str, FunctionSignature],
    code: str,
) -> CompilerError:
    try:
        compile_source(
            source,
            function_signatures=signatures,
        )
    except CompilerError as error:
        require(
            error.diagnostic.code == code,
            (
                f"expected {code}, received "
                f"{error.diagnostic.code}: {error}"
            ),
        )
        return error
    raise AssertionError(
        f"source unexpectedly compiled: {source!r}"
    )


def call_type(
    signature: FunctionSignature,
    *arguments,
):
    return infer_expression_type(
        AIRCallExpression(
            target=signature.name,
            arguments=tuple(arguments),
        ),
        functions={
            signature.name: signature,
        },
    )


def main() -> None:
    identity_program = compile_source(
        """
        function Identity<T>(value : T) : T {
            return value
        }
        """
    )
    identity = identity_program.functions[0]
    identity_signature = FunctionSignature.from_air_function(
        identity
    )

    require(
        call_type(identity_signature, AIRIntegerLiteral(10)) is INT,
        "Identity<int> did not resolve to int",
    )
    require(
        call_type(identity_signature, AIRStringLiteral("ready")) is STRING,
        "Identity<string> did not resolve to string",
    )
    require(
        call_type(identity_signature, AIRBooleanLiteral(True)) is BOOL,
        "Identity<bool> did not resolve to bool",
    )
    require(
        call_type(identity_signature, AIRFloatLiteral(1.5)) is FLOAT,
        "Identity<float> did not resolve to float",
    )

    identity_variable = identity_signature.type_parameters[0]
    direct_substitution = infer_call_substitution(
        identity_signature,
        (INT,),
        target="Identity",
    )
    require(
        isinstance(direct_substitution, GenericSubstitution),
        "call inference did not return GenericSubstitution",
    )
    require(
        direct_substitution.get(identity_variable) is INT,
        "direct substitution did not bind T to int",
    )
    require(
        direct_substitution.resolve(identity_variable) is INT,
        "substitution did not resolve T to int",
    )

    same_program = compile_source(
        """
        function Same<T>(left : T, right : T) : T {
            return left
        }
        """
    )
    same_signature = FunctionSignature.from_air_function(
        same_program.functions[0]
    )
    require(
        call_type(
            same_signature,
            AIRIntegerLiteral(1),
            AIRIntegerLiteral(2),
        )
        is INT,
        "repeated T did not preserve matching int inference",
    )
    conflict = require_type_error(
        lambda: call_type(
            same_signature,
            AIRIntegerLiteral(1),
            AIRStringLiteral("two"),
        ),
        "APX-TYPE-016",
    )
    require(
        "both int and string" in conflict.message,
        "generic conflict diagnostic omitted inferred types",
    )

    first_program = compile_source(
        """
        function First<T, U>(first : T, second : U) : T {
            return first
        }
        """
    )
    first_signature = FunctionSignature.from_air_function(
        first_program.functions[0]
    )
    require(
        call_type(
            first_signature,
            AIRStringLiteral("first"),
            AIRBooleanLiteral(False),
        )
        is STRING,
        "multiple-variable return substitution changed",
    )

    generic_owner = "function:Make"
    make_variable = ApexTypeVariable(
        name="T",
        owner=generic_owner,
    )
    make_signature = FunctionSignature(
        name="Make",
        parameter_types=(),
        return_type=make_variable,
        type_parameters=(make_variable,),
    )
    require_type_error(
        lambda: call_type(make_signature),
        "APX-TYPE-017",
    )

    tagged_variable = ApexTypeVariable(
        name="T",
        owner="function:Tagged",
    )
    tagged_signature = FunctionSignature(
        name="Tagged",
        parameter_types=(STRING, tagged_variable),
        return_type=tagged_variable,
        type_parameters=(tagged_variable,),
    )
    require(
        call_type(
            tagged_signature,
            AIRStringLiteral("value"),
            AIRBooleanLiteral(True),
        )
        is BOOL,
        "concrete-plus-generic signature did not infer bool",
    )
    require_type_error(
        lambda: call_type(
            tagged_signature,
            AIRIntegerLiteral(1),
            AIRBooleanLiteral(True),
        ),
        "APX-TYPE-008",
    )

    partial_call = AIRCallExpression(
        target="Identity",
        arguments=(
            AIRIdentifierReference("unknown"),
        ),
    )
    require(
        infer_expression_type_partial(
            partial_call,
            identifiers={"unknown": None},
            functions={"Identity": identity_signature},
            require_complete_arguments=False,
        )
        is None,
        "legacy unknown generic argument did not defer",
    )
    require_type_error(
        lambda: infer_expression_type_partial(
            partial_call,
            identifiers={"unknown": None},
            functions={"Identity": identity_signature},
            require_complete_arguments=True,
        ),
        "APX-TYPE-014",
    )

    use_int_program = compile_source(
        """
        function UseInt() : int {
            return Identity(10)
        }
        """,
        function_signatures={
            "Identity": identity_signature,
        },
    )
    linked_use_int = link_programs(
        identity_program,
        use_int_program,
    )
    RuntimeValidator().validate(
        linked_use_int
    )

    echo_program = compile_source(
        """
        function Echo<T>(value : T) : T {
            return Identity(value)
        }
        """,
        function_signatures={
            "Identity": identity_signature,
        },
    )
    linked_echo = link_programs(
        identity_program,
        echo_program,
    )
    RuntimeValidator().validate(
        linked_echo
    )
    echo_signature = FunctionSignature.from_air_function(
        echo_program.functions[0]
    )
    require(
        call_type(
            echo_signature,
            AIRStringLiteral("echo"),
        )
        is STRING,
        "generic-to-generic substitution did not resolve caller T",
    )

    require_compile_error(
        """
        function Bad() : int {
            return Same(1, "two")
        }
        """,
        signatures={
            "Same": same_signature,
        },
        code="APX-TYPE-016",
    )

    function_index = {
        function.id: function
        for function in linked_echo.functions
    }
    runtime_value = RuntimeEngine()._evaluate_expression(
        AIRCallExpression(
            target="Echo",
            arguments=(
                AIRStringLiteral("runtime"),
            ),
        ),
        StateSnapshot(),
        functions=function_index,
    )
    require(
        runtime_value == "runtime",
        "runtime generic call did not preserve value",
    )

    print("AFP-P9.2 generic call-site inference smoke test passed.")
    print("Built-in generic inference: PASS")
    print("Immutable substitution binding: PASS")
    print("Repeated-variable consistency: PASS")
    print("Conflict diagnostics: PASS")
    print("Multiple type variables: PASS")
    print("Unresolved-variable diagnostics: PASS")
    print("Concrete parameter checking: PASS")
    print("Partial legacy deferral: PASS")
    print("Compiler generic calls: PASS")
    print("Linked generic calls: PASS")
    print("Generic-to-generic substitution: PASS")
    print("Runtime generic execution: PASS")


if __name__ == "__main__":
    main()