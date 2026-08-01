"""AFP-P10.5 generic standard-library utility smoke test."""

from __future__ import annotations

from air.expressions import (
    AIRBooleanLiteral,
    AIRCallExpression,
    AIRIntegerLiteral,
    AIRStringLiteral,
)
from air.linker import link_programs
from language.compiler import CompilerError, compile_source
from language.validation.runtime_validator import RuntimeValidator
from runtime.engine import RuntimeEngine
from runtime.state import StateSnapshot
from standard_library import (
    DEFAULT_STANDARD_LIBRARY,
    GENERIC_VALUE_BUILTINS,
    P10_STANDARD_LIBRARY_VERSION,
    BuiltinFunction,
    StandardLibraryInvocationError,
)
from type_system.generics import ApexTypeVariable
from type_system.inference import (
    FunctionSignature,
    TypeInferenceError,
    infer_expression_type,
)
from type_system.model import BOOL, INT, STRING


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def require_compile_error(source: str, code: str) -> CompilerError:
    try:
        compile_source(source)
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


def require_invocation_error(
    operation,
    code: str,
) -> StandardLibraryInvocationError:
    try:
        operation()
    except StandardLibraryInvocationError as error:
        require(
            error.code == code,
            f"expected {code}, received {error.code}: {error}",
        )
        return error
    raise AssertionError(
        f"operation unexpectedly passed; expected {code}"
    )


def main() -> None:
    require(
        P10_STANDARD_LIBRARY_VERSION == "10.12",
        "P10 standard-library version changed",
    )
    require(
        len(GENERIC_VALUE_BUILTINS) == 4,
        "generic utility count changed",
    )
    require(
        all(
            isinstance(entry, BuiltinFunction)
            for entry in GENERIC_VALUE_BUILTINS
        ),
        "generic utility registry contains a non-built-in",
    )
    require(
        DEFAULT_STANDARD_LIBRARY.names
        == tuple(sorted(DEFAULT_STANDARD_LIBRARY.names)),
        "default registry ordering is not canonical",
    )
    for name in ("identity", "choose", "first", "second"):
        require(
            DEFAULT_STANDARD_LIBRARY.contains(name),
            f"missing generic standard-library function {name}",
        )
        require(
            DEFAULT_STANDARD_LIBRARY.require(name).is_generic,
            f"{name} is not marked generic",
        )

    identity = DEFAULT_STANDARD_LIBRARY.require("identity")
    identity_signature = identity.signature
    require(
        len(identity_signature.type_parameters) == 1,
        "identity generic parameter count changed",
    )
    require(
        identity_signature.parameter_types[0]
        is identity_signature.type_parameters[0],
        "identity parameter lost canonical T identity",
    )
    require(
        identity_signature.return_type
        is identity_signature.type_parameters[0],
        "identity return lost canonical T identity",
    )

    concrete_units = tuple(
        compile_source(source)
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
        )
    )
    program = link_programs(*concrete_units)
    RuntimeValidator().validate(program)

    concrete_return_types = {
        function.name: function.return_type
        for function in program.functions
    }
    require(
        concrete_return_types
        == {
            "KeepInt": INT,
            "PickText": STRING,
            "LeftValue": INT,
            "RightValue": STRING,
            "Explicit": INT,
        },
        "generic built-in return projection changed",
    )

    generic_units = (
        compile_source(
            """
            function Preserve<T>(value : T) : T {
                return identity<T>(value)
            }
            """
        ),
        compile_source(
            """
            function Select<T>(
                condition : bool,
                left : T,
                right : T
            ) : T {
                return choose<T>(condition, left, right)
            }
            """
        ),
    )
    generic_program = link_programs(*generic_units)
    RuntimeValidator().validate(generic_program)

    generic_functions = {
        function.name: function
        for function in generic_program.functions
    }
    preserve = generic_functions["Preserve"]
    select = generic_functions["Select"]

    require(
        preserve.return_type is preserve.type_parameters[0],
        "generic-to-generic identity propagation changed",
    )
    require(
        select.return_type is select.type_parameters[0],
        "generic choose return propagation changed",
    )

    require_compile_error(
        """
        function Bad() : int {
            return choose(true, 1, "wrong")
        }
        """,
        "APX-TYPE-016",
    )
    require_compile_error(
        """
        function Bad() : int {
            return identity<float>(1)
        }
        """,
        "APX-TYPE-008",
    )
    require_compile_error(
        """
        function identity(value : int) : int {
            return value
        }
        """,
        "APX-COMPILE-015",
    )

    require(
        infer_expression_type(
            AIRCallExpression(
                target="identity",
                arguments=(AIRIntegerLiteral(8),),
            ),
            functions=DEFAULT_STANDARD_LIBRARY.signatures(),
        )
        is INT,
        "identity<int> inference failed",
    )
    require(
        infer_expression_type(
            AIRCallExpression(
                target="choose",
                arguments=(
                    AIRBooleanLiteral(True),
                    AIRStringLiteral("left"),
                    AIRStringLiteral("right"),
                ),
            ),
            functions=DEFAULT_STANDARD_LIBRARY.signatures(),
        )
        is STRING,
        "choose<string> inference failed",
    )

    require(
        DEFAULT_STANDARD_LIBRARY.invoke(
            "identity",
            (17,),
        )
        == 17,
        "runtime identity<int> failed",
    )
    require(
        DEFAULT_STANDARD_LIBRARY.invoke(
            "identity",
            ("forge",),
            type_arguments=(STRING,),
        )
        == "forge",
        "explicit runtime identity<string> failed",
    )
    require(
        DEFAULT_STANDARD_LIBRARY.invoke(
            "choose",
            (False, "left", "right"),
        )
        == "right",
        "runtime choose<string> failed",
    )
    require(
        DEFAULT_STANDARD_LIBRARY.invoke(
            "first",
            (10, "ten"),
        )
        == 10,
        "runtime first<int,string> failed",
    )
    require(
        DEFAULT_STANDARD_LIBRARY.invoke(
            "second",
            (10, "ten"),
        )
        == "ten",
        "runtime second<int,string> failed",
    )

    require_invocation_error(
        lambda: DEFAULT_STANDARD_LIBRARY.invoke(
            "choose",
            (True, 1, "wrong"),
        ),
        "APX-STDLIB-002",
    )
    require_invocation_error(
        lambda: DEFAULT_STANDARD_LIBRARY.invoke(
            "identity",
            (1,),
            type_arguments=(STRING,),
        ),
        "APX-STDLIB-002",
    )
    require_invocation_error(
        lambda: DEFAULT_STANDARD_LIBRARY.invoke(
            "identity",
            (1,),
            type_arguments=(INT, STRING),
        ),
        "APX-STDLIB-009",
    )

    runtime_result = RuntimeEngine()._evaluate_expression(
        AIRCallExpression(
            target="choose",
            arguments=(
                AIRBooleanLiteral(True),
                AIRStringLiteral("selected"),
                AIRStringLiteral("ignored"),
            ),
            type_arguments=(STRING,),
        ),
        StateSnapshot(),
        functions={},
    )
    require(
        runtime_result == "selected",
        "runtime engine did not forward generic type metadata",
    )

    # bool remains separate from int at the generic runtime boundary.
    require(
        DEFAULT_STANDARD_LIBRARY.invoke(
            "identity",
            (True,),
        )
        is True,
        "identity<bool> failed",
    )
    require_invocation_error(
        lambda: DEFAULT_STANDARD_LIBRARY.invoke(
            "choose",
            (True, True, 1),
        ),
        "APX-STDLIB-002",
    )

    print("AFP-P10.5 generic standard-library utility smoke test passed.")
    print("Generic built-in model: PASS")
    print("Canonical generic registry ordering: PASS")
    print("Automatic generic compiler signatures: PASS")
    print("Linked generic validation: PASS")
    print("Inferred generic built-ins: PASS")
    print("Explicit generic built-ins: PASS")
    print("Generic-to-generic propagation: PASS")
    print("Identity and selection semantics: PASS")
    print("First and second projection: PASS")
    print("Compile-time generic conflict rejection: PASS")
    print("Runtime generic contract enforcement: PASS")
    print("Explicit runtime type metadata: PASS")
    print("Exact bool/int separation: PASS")
    print("Reserved generic names: PASS")
    print("Pure runtime dispatch: PASS")


if __name__ == "__main__":
    main()