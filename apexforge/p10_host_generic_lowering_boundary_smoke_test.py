"""AFP-P10.5A host-backed generic closure/lowering boundary smoke test."""

from __future__ import annotations

from air.expressions import (
    AIRBooleanLiteral,
    AIRCallExpression,
    AIRExpression,
    AIRFloatLiteral,
    AIRIdentifierReference,
    AIRIntegerLiteral,
    AIRStringLiteral,
)
from air.functions import AIRFunction, AIRFunctionReturn
from air.linker import link_programs
from language.compiler import compile_source
from language.validation.runtime_validator import RuntimeValidator
from standard_library import (
    DEFAULT_STANDARD_LIBRARY,
    GENERIC_VALUE_BUILTINS,
    P10_STANDARD_LIBRARY_VERSION,
)
from type_system.closure import collect_linked_specializations
from type_system.freeze import audit_lowered_generics
from type_system.inference import FunctionSignature
from type_system.lowering import lower_linked_generics
from type_system.model import BOOL, INT, STRING


HOST_SIGNATURES = DEFAULT_STANDARD_LIBRARY.signatures()
HOST_GENERIC_TARGETS = tuple(
    entry.name for entry in GENERIC_VALUE_BUILTINS
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def return_expression(function: AIRFunction) -> AIRExpression:
    body = tuple(getattr(function, "body", ()) or ())
    if body and isinstance(body[-1], AIRFunctionReturn):
        return body[-1].expression
    expression = function.return_expression
    if not isinstance(expression, AIRExpression):
        raise AssertionError(
            f"function {function.name!r} has no executable return expression"
        )
    return expression


def runtime_index(functions: tuple[AIRFunction, ...]) -> dict[str, AIRFunction]:
    index: dict[str, AIRFunction] = {}
    for function in functions:
        index[function.id] = function
        index[function.name] = function
    return index


def evaluate(
    expression: AIRExpression,
    functions: dict[str, AIRFunction],
    locals_: dict[str, object] | None = None,
) -> object:
    """Small deterministic evaluator for this integration boundary."""

    frame = dict(locals_ or {})

    if isinstance(expression, AIRIntegerLiteral):
        return expression.value
    if isinstance(expression, AIRFloatLiteral):
        return expression.value
    if isinstance(expression, AIRStringLiteral):
        return expression.value
    if isinstance(expression, AIRBooleanLiteral):
        return expression.value
    if isinstance(expression, AIRIdentifierReference):
        return frame[expression.name]
    if isinstance(expression, AIRCallExpression):
        values = tuple(
            evaluate(argument, functions, frame)
            for argument in expression.arguments
        )

        if DEFAULT_STANDARD_LIBRARY.contains(expression.target):
            return DEFAULT_STANDARD_LIBRARY.invoke(
                expression.target,
                values,
                type_arguments=tuple(
                    getattr(expression, "type_arguments", ()) or ()
                ),
            )

        function = functions[expression.target]
        call_frame = {
            parameter.name: value
            for parameter, value in zip(function.parameters, values)
        }
        return evaluate(
            return_expression(function),
            functions,
            call_frame,
        )

    raise AssertionError(
        f"unsupported boundary-test expression {type(expression).__name__}"
    )


def compile_unit(
    source: str,
    *,
    function_signatures: dict[str, FunctionSignature] | None = None,
):
    return compile_source(
        source,
        function_signatures=function_signatures,
    )


def main() -> None:
    require(
        P10_STANDARD_LIBRARY_VERSION == "10.12",
        "host-boundary patch must track the active P10 API version",
    )
    require(
        HOST_GENERIC_TARGETS
        == ("identity", "choose", "first", "second"),
        "P10.5 generic built-in declaration order changed",
    )

    host_units = tuple(
        compile_unit(source)
        for source in (
            """
            function KeepInt(value : int) : int {
                return identity(value)
            }
            """,
            """
            function PickText(
                condition : bool,
                left : string,
                right : string
            ) : string {
                return choose(condition, left, right)
            }
            """,
            """
            function LeftValue(
                value : int,
                text : string
            ) : int {
                return first(value, text)
            }
            """,
            """
            function RightValue(
                value : int,
                text : string
            ) : string {
                return second(value, text)
            }
            """,
            """
            function Explicit(value : int) : int {
                return identity<int>(value)
            }
            """,
            """
            function Normalize(value : int) : int {
                return int_abs(value)
            }
            """,
        )
    )
    host_program = link_programs(*host_units)
    RuntimeValidator().validate(host_program)

    host_manifest = collect_linked_specializations(
        host_program,
        external_signatures=HOST_SIGNATURES,
        host_generic_targets=HOST_GENERIC_TARGETS,
    )
    expected_host_ids = (
        "choose<string>",
        "first<int,string>",
        "identity<int>",
        "second<int,string>",
    )
    require(
        host_manifest.canonical_ids == expected_host_ids,
        f"unexpected host-generic closure: {host_manifest.canonical_ids}",
    )

    host_lowered = lower_linked_generics(
        host_program,
        external_signatures=HOST_SIGNATURES,
        host_generic_targets=HOST_GENERIC_TARGETS,
    )
    RuntimeValidator().validate(host_lowered.program)
    host_audit = audit_lowered_generics(host_lowered)

    require(
        host_lowered.bindings == (),
        "host-backed leaves were incorrectly materialized as AIR functions",
    )
    require(
        host_lowered.specialized_functions == (),
        "host-backed leaves emitted concrete AIR functions",
    )
    require(
        host_lowered.host_canonical_ids == expected_host_ids,
        "host specialization identities changed during lowering",
    )
    require(
        host_audit.specialization_count == 4
        and host_audit.concrete_function_count == 0
        and host_audit.host_specialization_count == 4
        and host_audit.closed,
        f"host-only closure audit changed: {host_audit}",
    )

    host_by_name = {
        function.name: function
        for function in host_lowered.functions
    }
    expected_call_metadata = {
        "KeepInt": ("identity", (INT,)),
        "PickText": ("choose", (STRING,)),
        "LeftValue": ("first", (INT, STRING)),
        "RightValue": ("second", (INT, STRING)),
        "Explicit": ("identity", (INT,)),
        "Normalize": ("int_abs", ()),
    }
    for function_name, (target, type_arguments) in expected_call_metadata.items():
        call = return_expression(host_by_name[function_name])
        require(
            isinstance(call, AIRCallExpression),
            f"{function_name} no longer returns a call expression",
        )
        require(
            call.target == target,
            f"{function_name} host target changed to {call.target!r}",
        )
        require(
            tuple(call.type_arguments) == type_arguments,
            f"{function_name} closed host metadata changed: "
            f"{call.type_arguments}",
        )

    host_runtime = runtime_index(host_lowered.functions)
    require(
        evaluate(
            AIRCallExpression(
                target="KeepInt",
                arguments=(AIRIntegerLiteral(-7),),
            ),
            host_runtime,
        )
        == -7,
        "lowered identity<int> host dispatch changed",
    )
    require(
        evaluate(
            AIRCallExpression(
                target="PickText",
                arguments=(
                    AIRBooleanLiteral(False),
                    AIRStringLiteral("left"),
                    AIRStringLiteral("right"),
                ),
            ),
            host_runtime,
        )
        == "right",
        "lowered choose<string> host dispatch changed",
    )
    require(
        evaluate(
            AIRCallExpression(
                target="LeftValue",
                arguments=(AIRIntegerLiteral(8), AIRStringLiteral("eight")),
            ),
            host_runtime,
        )
        == 8,
        "lowered first<int,string> host dispatch changed",
    )
    require(
        evaluate(
            AIRCallExpression(
                target="RightValue",
                arguments=(AIRIntegerLiteral(8), AIRStringLiteral("eight")),
            ),
            host_runtime,
        )
        == "eight",
        "lowered second<int,string> host dispatch changed",
    )
    require(
        evaluate(
            AIRCallExpression(
                target="Normalize",
                arguments=(AIRIntegerLiteral(-9),),
            ),
            host_runtime,
        )
        == 9,
        "non-generic host signature changed at the lowering boundary",
    )

    preserve_program = compile_unit(
        """
        function Preserve<T>(value : T) : T {
            return identity<T>(value)
        }
        """
    )
    preserve_signature = FunctionSignature.from_air_function(
        preserve_program.functions[0]
    )
    use_program = compile_unit(
        """
        function Use(value : int) : int {
            return Preserve(value)
        }
        """,
        function_signatures={"Preserve": preserve_signature},
    )
    mixed_program = link_programs(preserve_program, use_program)
    RuntimeValidator().validate(mixed_program)

    mixed_manifest = collect_linked_specializations(
        mixed_program,
        external_signatures=HOST_SIGNATURES,
        host_generic_targets=HOST_GENERIC_TARGETS,
    )
    require(
        mixed_manifest.canonical_ids
        == ("Preserve<int>", "identity<int>"),
        f"mixed closure changed: {mixed_manifest.canonical_ids}",
    )

    mixed_lowered = lower_linked_generics(
        mixed_program,
        external_signatures=HOST_SIGNATURES,
        host_generic_targets=HOST_GENERIC_TARGETS,
    )
    RuntimeValidator().validate(mixed_lowered.program)
    mixed_audit = audit_lowered_generics(mixed_lowered)

    require(
        mixed_lowered.canonical_ids == ("Preserve<int>",),
        "linked generic specialization was not materialized exactly once",
    )
    require(
        mixed_lowered.host_canonical_ids == ("identity<int>",),
        "transitive host generic leaf was not retained exactly once",
    )
    require(
        mixed_audit.specialization_count == 2
        and mixed_audit.concrete_function_count == 1
        and mixed_audit.host_specialization_count == 1
        and mixed_audit.closed,
        f"mixed closure audit changed: {mixed_audit}",
    )

    mixed_by_name = {
        function.name: function
        for function in mixed_lowered.functions
    }
    use_call = return_expression(mixed_by_name["Use"])
    require(
        isinstance(use_call, AIRCallExpression)
        and use_call.target == mixed_lowered.lowered_target("Preserve<int>")
        and use_call.type_arguments == (),
        "linked generic call was not type-erased to its concrete AIR target",
    )

    preserve_target = mixed_lowered.lowered_target("Preserve<int>")
    require(
        isinstance(preserve_target, str),
        "Preserve<int> concrete target is missing",
    )
    preserve_call = return_expression(mixed_by_name[preserve_target])
    require(
        isinstance(preserve_call, AIRCallExpression)
        and preserve_call.target == "identity"
        and preserve_call.type_arguments == (INT,),
        "specialized linked body lost closed host metadata",
    )

    mixed_runtime = runtime_index(mixed_lowered.functions)
    require(
        evaluate(
            AIRCallExpression(
                target="Use",
                arguments=(AIRIntegerLiteral(42),),
            ),
            mixed_runtime,
        )
        == 42,
        "mixed linked/host generic runtime value changed",
    )

    reverse_program = link_programs(use_program, preserve_program)
    reverse_manifest = collect_linked_specializations(
        reverse_program,
        external_signatures=HOST_SIGNATURES,
        host_generic_targets=HOST_GENERIC_TARGETS,
    )
    reverse_lowered = lower_linked_generics(
        reverse_program,
        external_signatures=HOST_SIGNATURES,
        host_generic_targets=HOST_GENERIC_TARGETS,
    )
    require(
        reverse_manifest.canonical_ids == mixed_manifest.canonical_ids,
        "host-aware closure depends on linked input order",
    )
    require(
        reverse_lowered.bindings == mixed_lowered.bindings
        and reverse_lowered.host_canonical_ids
        == mixed_lowered.host_canonical_ids,
        "host-aware lowering identities depend on linked input order",
    )

    print("AFP-P10.5A host-generic lowering boundary smoke test passed.")
    print("Frozen P10.5 API preservation: PASS")
    print("External signature environment: PASS")
    print("Host generic closure leaves: PASS")
    print("No host AIR materialization: PASS")
    print("Closed runtime type metadata: PASS")
    print("Non-generic host signature continuity: PASS")
    print("Linked generic materialization: PASS")
    print("Transitive linked-to-host lowering: PASS")
    print("Executable closure audit: PASS")
    print("Runtime semantic preservation: PASS")
    print("Input-order independence: PASS")


if __name__ == "__main__":
    main()