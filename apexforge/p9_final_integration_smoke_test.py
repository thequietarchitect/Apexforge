"""AFP-P9.8 final source-to-runtime generics integration smoke test."""

from __future__ import annotations

from air.expressions import AIRCallExpression
from air.functions import AIRFunctionReturn
from air.linker import link_programs
from language.compiler import compile_source
from language.validation.runtime_validator import RuntimeValidator
from runtime.engine import RuntimeEngine
from runtime.state import StateSnapshot
from type_system.model import FLOAT, INT, STRING
from type_system.p9 import (
    P9_API_VERSION,
    P9_FREEZE_CANDIDATE,
    FunctionSignature,
    audit_lowered_generics,
    collect_linked_specializations,
    lower_linked_generics,
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def signature(program) -> FunctionSignature:
    return FunctionSignature.from_air_function(program.functions[0])


def return_expression(function):
    body = tuple(getattr(function, "body", ()) or ())
    if body and isinstance(body[-1], AIRFunctionReturn):
        return body[-1].expression
    return function.return_expression


def runtime_index(functions):
    index = {}
    for function in functions:
        index[function.id] = function
        index[function.name] = function
    return index


def main() -> None:
    identity_program = compile_source(
        """
        function Identity<T>(value : T) : T {
            return value
        }
        """
    )
    identity_signature = signature(identity_program)

    add_program = compile_source(
        """
        function Add<T : numeric>(left : T, right : T) : T {
            return left + right
        }
        """
    )
    add_signature = signature(add_program)

    echo_program = compile_source(
        """
        function Echo<U>(value : U) : U {
            return Identity<U>(value)
        }
        """,
        function_signatures={
            "Identity": identity_signature,
        },
    )
    echo_signature = signature(echo_program)

    use_int_program = compile_source(
        """
        function UseInt() : int {
            return Echo<int>(Identity(21))
        }
        """,
        function_signatures={
            "Identity": identity_signature,
            "Echo": echo_signature,
        },
    )

    use_float_program = compile_source(
        """
        function UseFloat() : float {
            return Add<float>(1.5, 2.5)
        }
        """,
        function_signatures={
            "Add": add_signature,
        },
    )

    use_string_program = compile_source(
        """
        function UseString() : string {
            return Identity("ready")
        }
        """,
        function_signatures={
            "Identity": identity_signature,
        },
    )

    linked = link_programs(
        identity_program,
        add_program,
        echo_program,
        use_int_program,
        use_float_program,
        use_string_program,
    )
    RuntimeValidator().validate(linked)

    manifest = collect_linked_specializations(linked)
    require(
        manifest.canonical_ids
        == (
            "Add<float>",
            "Echo<int>",
            "Identity<int>",
            "Identity<string>",
        ),
        f"unexpected final P9 closure: {manifest.canonical_ids}",
    )

    lowered = lower_linked_generics(linked)
    audit = audit_lowered_generics(lowered)
    verified = RuntimeValidator().validate(lowered.program)

    require(verified.program is lowered.program, "lowered program did not validate")
    require(audit.specialization_count == 4, "final specialization count changed")
    require(audit.concrete_function_count == 4, "concrete specialization count changed")
    require(audit.preserved_generic_count == 3, "generic declarations were not preserved")
    require(P9_API_VERSION == "9.0", "P9 public API version changed")
    require(len(P9_FREEZE_CANDIDATE.slices) == 8, "P9 freeze manifest is incomplete")

    functions = runtime_index(lowered.functions)
    by_name = {function.name: function for function in lowered.functions}
    engine = RuntimeEngine()
    empty_state = StateSnapshot()

    int_result = engine._evaluate_expression(
        return_expression(by_name["UseInt"]),
        empty_state,
        functions=functions,
    )
    float_result = engine._evaluate_expression(
        return_expression(by_name["UseFloat"]),
        empty_state,
        functions=functions,
    )
    string_result = engine._evaluate_expression(
        return_expression(by_name["UseString"]),
        empty_state,
        functions=functions,
    )

    require(type(int_result) is int and int_result == 21, "lowered int runtime changed")
    require(type(float_result) is float and float_result == 4.0, "lowered float runtime changed")
    require(type(string_result) is str and string_result == "ready", "lowered string runtime changed")

    for function in lowered.specialized_functions:
        require(not function.type_parameters, "specialized function retained type parameters")
        require(
            all(parameter.value_type in {INT, FLOAT, STRING} for parameter in function.parameters),
            "specialized parameter did not close to a built-in type",
        )

    reverse_linked = link_programs(
        use_string_program,
        use_float_program,
        use_int_program,
        echo_program,
        add_program,
        identity_program,
    )
    reverse_lowered = lower_linked_generics(reverse_linked)
    require(
        reverse_lowered.bindings == lowered.bindings,
        "final lowering depends on linked input order",
    )

    print("AFP-P9.8 final generics integration smoke test passed.")
    print("Source parsing and generic compilation: PASS")
    print("Cross-unit signature linking: PASS")
    print("Pre-lowering linked validation: PASS")
    print("Closed specialization manifest: PASS")
    print("Deterministic generic lowering: PASS")
    print("Post-lowering validation: PASS")
    print("Executable generic closure audit: PASS")
    print("Public P9 API audit: PASS")
    print("Original generic traceability: PASS")
    print("Integer runtime execution: PASS")
    print("Float runtime execution: PASS")
    print("String runtime execution: PASS")
    print("Input-order independence: PASS")


if __name__ == "__main__":
    main()