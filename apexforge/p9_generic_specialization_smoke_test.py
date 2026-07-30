"AFP-P9.5 generic specialization and instantiation smoke test."""

from __future__ import annotations

from air.expressions import AIRFloatLiteral, AIRIntegerLiteral, AIRStringLiteral
from language.compiler import compile_source
from type_system.inference import (
    FunctionSignature,
    TypeInferenceError,
    resolve_call_specialization,
)
from type_system.model import FLOAT, INT, STRING
from type_system.specialization import (
    GenericInstantiationTable,
    GenericSpecialization,
    GenericSpecializationKey,
    OpenGenericSpecializationError,
)


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
    raise AssertionError(f"operation unexpectedly passed; expected {code}")


def main() -> None:
    identity_program = compile_source(
        """
        function Identity<T>(value : T) : T {
            return value
        }
        """
    )
    identity_signature = FunctionSignature.from_air_function(
        identity_program.functions[0]
    )

    int_specialization = resolve_call_specialization(
        identity_signature,
        (INT,),
        target="Identity",
        require_closed=True,
    )
    require(
        isinstance(int_specialization, GenericSpecialization),
        "generic call did not produce a specialization record",
    )
    require(
        int_specialization.canonical_id == "Identity<int>",
        "canonical int specialization id changed",
    )
    require(
        int_specialization.type_arguments == (INT,),
        "specialization type arguments changed",
    )
    require(
        int_specialization.parameter_types == (INT,),
        "specialized parameter projection changed",
    )
    require(
        int_specialization.return_type is INT,
        "specialized return projection changed",
    )
    require(int_specialization.is_closed, "int specialization was not closed")

    explicit_string = resolve_call_specialization(
        identity_signature,
        (STRING,),
        explicit_type_arguments=(STRING,),
        target="Identity",
        require_closed=True,
    )
    require(
        explicit_string.canonical_id == "Identity<string>",
        "explicit specialization id changed",
    )
    require(
        explicit_string.return_type is STRING,
        "explicit specialization return changed",
    )

    add_program = compile_source(
        """
        function Add<T : numeric>(left : T, right : T) : T {
            return left + right
        }
        """
    )
    add_signature = FunctionSignature.from_air_function(
        add_program.functions[0]
    )
    float_add = resolve_call_specialization(
        add_signature,
        (FLOAT, FLOAT),
        target="Add",
        require_closed=True,
    )
    require(
        float_add.canonical_id == "Add<float>",
        "constrained specialization id changed",
    )
    require(
        float_add.parameter_types == (FLOAT, FLOAT),
        "constrained specialized parameters changed",
    )

    require_type_error(
        lambda: resolve_call_specialization(
            add_signature,
            (STRING, STRING),
            target="Add",
            require_closed=True,
        ),
        "APX-TYPE-021",
    )

    plain_signature = FunctionSignature(
        name="Plain",
        parameter_types=(INT,),
        return_type=INT,
    )
    require_type_error(
        lambda: resolve_call_specialization(
            plain_signature,
            (INT,),
            target="Plain",
        ),
        "APX-TYPE-022",
    )

    echo_program = compile_source(
        """
        function Echo<U>(value : U) : U {
            return value
        }
        """
    )
    echo_signature = FunctionSignature.from_air_function(
        echo_program.functions[0]
    )
    outer_u = echo_signature.type_parameters[0]
    open_specialization = resolve_call_specialization(
        identity_signature,
        (outer_u,),
        explicit_type_arguments=(outer_u,),
        target="Identity",
        require_complete=True,
    )
    require(
        not open_specialization.is_closed,
        "generic-to-generic specialization was incorrectly closed",
    )
    require(
        open_specialization.canonical_id
        == "Identity<function:Echo::U>",
        "open specialization did not preserve owner identity",
    )
    require_type_error(
        lambda: resolve_call_specialization(
            identity_signature,
            (outer_u,),
            explicit_type_arguments=(outer_u,),
            target="Identity",
            require_complete=True,
            require_closed=True,
        ),
        "APX-TYPE-023",
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
    first_specialization = resolve_call_specialization(
        first_signature,
        (STRING, INT),
        target="First",
        require_closed=True,
    )
    require(
        first_specialization.canonical_id == "First<string,int>",
        "multi-parameter specialization ordering changed",
    )

    table_a = GenericInstantiationTable()
    table_a = table_a.register(explicit_string)
    table_a = table_a.register(int_specialization)
    table_a = table_a.register(first_specialization)
    table_a_again = table_a.register(int_specialization)
    require(
        table_a_again is table_a,
        "duplicate specialization registration was not idempotent",
    )
    require(
        tuple(record.canonical_id for record in table_a.records)
        == ("First<string,int>", "Identity<int>", "Identity<string>"),
        "instantiation table ordering is not canonical",
    )

    table_b = GenericInstantiationTable(
        (int_specialization, first_specialization, explicit_string)
    )
    require(
        table_b == table_a,
        "instantiation table depends on registration order",
    )
    require(
        table_a.get("Identity<int>") is int_specialization,
        "instantiation lookup failed",
    )
    require(len(table_a) == 3, "instantiation table count changed")

    try:
        GenericInstantiationTable((open_specialization,))
    except OpenGenericSpecializationError:
        pass
    else:
        raise AssertionError(
            "open specialization entered the concrete instantiation table"
        )

    # Constructor normalization remains public and deterministic.
    manual_key = GenericSpecializationKey(
        target="Identity",
        type_arguments=("int",),
    )
    require(
        manual_key == int_specialization.key,
        "manual canonical key normalization changed",
    )

    print("AFP-P9.5 generic specialization smoke test passed.")
    print("Canonical specialization keys: PASS")
    print("Inferred specialization records: PASS")
    print("Explicit specialization records: PASS")
    print("Resolved parameter projection: PASS")
    print("Resolved return projection: PASS")
    print("Constraint preservation: PASS")
    print("Non-generic rejection: PASS")
    print("Open specialization identity: PASS")
    print("Closed-instantiation enforcement: PASS")
    print("Multiple type-argument ordering: PASS")
    print("Deterministic table ordering: PASS")
    print("Idempotent registration: PASS")
    print("Order-independent table equality: PASS")


if __name__ == "__main__":
    main()