"""AFP-P10.11 safe reflection and introspection smoke test."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

from air.expressions import (
    AIRCallExpression,
    AIRIntegerLiteral,
)
from air.linker import link_programs
from language.compiler import compile_source
from language.validation.runtime_validator import RuntimeValidator
from runtime.engine import RuntimeEngine
from runtime.state import StateSnapshot
from standard_library import (
    DEFAULT_STANDARD_LIBRARY,
    P10_STANDARD_LIBRARY_VERSION,
    REFLECTION_BUILTINS,
    RuntimeCollection,
    RuntimeDiagnostic,
    RuntimeResult,
    RuntimeTypeInfo,
)
from type_system.closure import collect_linked_specializations
from type_system.freeze import audit_lowered_generics
from type_system.lowering import lower_linked_generics
from type_system.model import (
    BOOL,
    BUILTIN_TYPES,
    COLLECTION,
    DIAGNOSTIC,
    FLOAT,
    INT,
    RANDOM,
    RESULT,
    STRING,
    TIME,
    TYPE_INFO,
    VOID,
    is_builtin_type,
    resolve_builtin_type,
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def call(name: str, *arguments):
    return DEFAULT_STANDARD_LIBRARY.invoke(name, tuple(arguments))


def runtime_index(program):
    index = {}
    for function in program.functions:
        index[function.id] = function
        index[function.name] = function
    return index


def main() -> None:
    require(P10_STANDARD_LIBRARY_VERSION == "10.12", "version changed")
    require(len(REFLECTION_BUILTINS) == 18, "reflection built-in count changed")
    require(
        resolve_builtin_type("type_info") is TYPE_INFO,
        "type_info did not resolve to its canonical identity",
    )
    require(is_builtin_type("type_info"), "type_info was not registered")
    require(BUILTIN_TYPES[-1] is TYPE_INFO, "type_info order changed")

    expected_names = {
        "type_of",
        "type_matches",
        "type_from_name",
        "result_type_info_or",
        "type_name",
        "type_equal",
        "type_compare",
        "type_is_primitive",
        "type_is_numeric",
        "type_is_opaque",
        "type_is_container",
        "type_is_void",
        "type_is_runtime_value",
        "type_builtin_count",
        "type_builtin_at",
        "type_builtin_names",
        "type_collection_element",
        "type_result_payload",
    }
    require(
        expected_names.issubset(DEFAULT_STANDARD_LIBRARY.names),
        "reflection registry entries are incomplete",
    )

    int_info = call("type_of", 7)
    float_info = call("type_of", 1.5)
    bool_info = call("type_of", True)
    string_info = call("type_of", "value")
    require(type(int_info) is RuntimeTypeInfo, "type_of return class changed")
    require(int_info.value_type is INT, "int introspection changed")
    require(float_info.value_type is FLOAT, "float introspection changed")
    require(bool_info.value_type is BOOL, "bool introspection changed")
    require(string_info.value_type is STRING, "string introspection changed")
    require(
        call("type_of", int_info).value_type is TYPE_INFO,
        "type_info could not describe itself",
    )

    parsed = call("string_to_int", "42")
    collection = call("collection_pair", 1, 2)
    instant = call("time_unix_epoch")
    random_state = call("random_from_seed", 7)
    diagnostic = call("diagnostic_info", "TYPE_TEST", "Value inspected.")
    opaque_values = (
        (parsed, RESULT),
        (collection, COLLECTION),
        (instant, TIME),
        (random_state, RANDOM),
        (diagnostic, DIAGNOSTIC),
    )
    for value, expected_type in opaque_values:
        require(
            call("type_of", value).value_type is expected_type,
            f"type_of failed for {expected_type}",
        )

    require(
        call("type_matches", 1, int_info) is True,
        "exact int matching failed",
    )
    require(
        call("type_matches", True, int_info) is False,
        "bool incorrectly matched int",
    )
    require(
        call("type_matches", diagnostic, call("type_of", diagnostic)) is True,
        "opaque exact matching failed",
    )

    resolved = call("type_from_name", "diagnostic")
    require(
        type(resolved) is RuntimeResult
        and resolved.ok
        and resolved.payload_type is TYPE_INFO
        and resolved.value.value_type is DIAGNOSTIC,
        "type name resolution changed",
    )
    unknown = call("type_from_name", "python_object")
    require(
        unknown.is_error
        and unknown.payload_type is TYPE_INFO
        and unknown.error_code == "UNKNOWN_TYPE",
        "unknown type result changed",
    )
    require(
        call("result_type_info_or", resolved, int_info).value_type
        is DIAGNOSTIC,
        "type_info result extraction failed",
    )
    require(
        call("result_type_info_or", unknown, int_info) is int_info,
        "type_info fallback identity changed",
    )

    void_result = call("type_from_name", "void")
    void_info = call("result_type_info_or", void_result, int_info)
    require(call("type_name", void_info) == "void", "void name changed")
    require(call("type_is_void", void_info) is True, "void predicate failed")
    require(
        call("type_is_runtime_value", void_info) is False,
        "void incorrectly reported a runtime value",
    )
    require(
        call("type_is_runtime_value", int_info) is True,
        "int runtime-value predicate failed",
    )

    require(call("type_is_primitive", int_info) is True, "int not primitive")
    require(
        call("type_is_primitive", string_info) is True,
        "string not primitive",
    )
    require(
        call("type_is_primitive", call("type_of", parsed)) is False,
        "result incorrectly primitive",
    )
    require(call("type_is_numeric", int_info) is True, "int not numeric")
    require(call("type_is_numeric", float_info) is True, "float not numeric")
    require(call("type_is_numeric", bool_info) is False, "bool became numeric")
    require(
        call("type_is_opaque", call("type_of", diagnostic)) is True,
        "diagnostic not opaque",
    )
    require(
        call("type_is_opaque", int_info) is False,
        "int incorrectly opaque",
    )
    require(
        call("type_is_container", call("type_of", parsed)) is True,
        "result not recognized as a container",
    )
    require(
        call("type_is_container", call("type_of", collection)) is True,
        "collection not recognized as a container",
    )
    require(
        call("type_is_container", call("type_of", instant)) is False,
        "time incorrectly recognized as a container",
    )

    require(
        call("type_equal", int_info, call("type_of", 99)) is True,
        "canonical type equality failed",
    )
    require(
        call("type_equal", int_info, float_info) is False,
        "different types compared equal",
    )
    require(
        call("type_compare", int_info, int_info) == 0,
        "equal type comparison changed",
    )
    require(
        call("type_compare", int_info, float_info) < 0,
        "canonical forward type comparison changed",
    )
    require(
        call("type_compare", float_info, int_info) > 0,
        "canonical reverse type comparison changed",
    )

    require(
        call("type_builtin_count") == len(BUILTIN_TYPES),
        "built-in type count changed",
    )
    names = call("type_builtin_names")
    require(
        type(names) is RuntimeCollection
        and names.element_type is STRING
        and names.values
        == tuple(value_type.name for value_type in BUILTIN_TYPES),
        "built-in name enumeration changed",
    )
    require(
        call("type_builtin_at", 0, float_info).value_type is INT,
        "built-in indexed access changed",
    )
    require(
        call("type_builtin_at", -1, float_info) is float_info,
        "negative index did not use fallback",
    )
    require(
        call("type_builtin_at", len(BUILTIN_TYPES), float_info) is float_info,
        "past-end index did not use fallback",
    )

    require(
        call("type_collection_element", collection).value_type is INT,
        "collection element introspection changed",
    )
    require(
        call("type_result_payload", parsed).value_type is INT,
        "result payload introspection changed",
    )
    failed_float = call("string_to_float", "not-a-float")
    require(
        call("type_result_payload", failed_float).value_type is FLOAT,
        "failed-result payload metadata was lost",
    )

    preserved = call("identity", int_info)
    require(preserved is int_info, "identity did not preserve type_info")
    chosen = call("choose", True, int_info, float_info)
    require(chosen is int_info, "choose did not transport type_info")
    info_collection = call("collection_pair", int_info, float_info)
    require(
        info_collection.element_type is TYPE_INFO
        and info_collection.values == (int_info, float_info),
        "type_info collection transport changed",
    )

    require(
        set(RuntimeTypeInfo.__dataclass_fields__) == {"value_type"},
        "type_info exposed noncanonical implementation fields",
    )
    for forbidden in (
        "python_type",
        "module",
        "source_path",
        "memory_address",
        "callable",
    ):
        require(
            not hasattr(int_info, forbidden),
            f"type_info exposed forbidden field {forbidden}",
        )
    try:
        int_info.value_type = FLOAT
    except (FrozenInstanceError, AttributeError):
        pass
    else:
        raise AssertionError("RuntimeTypeInfo was mutable")

    describe_program = compile_source(
        """
        function DescribeInt(value : int) : string {
            return type_name(type_of(value))
        }
        """
    )
    keep_program = compile_source(
        """
        function KeepType(value : type_info) : collection {
            return collection_single(identity(value))
        }
        """
    )
    match_program = compile_source(
        """
        function MatchDiagnostic(
            value : diagnostic,
            expected : type_info
        ) : bool {
            return type_matches(value, expected)
        }
        """
    )
    element_program = compile_source(
        """
        function ElementType(value : collection) : type_info {
            return type_collection_element(value)
        }
        """
    )
    payload_program = compile_source(
        """
        function PayloadType(value : result) : type_info {
            return type_result_payload(value)
        }
        """
    )
    linked = link_programs(
        describe_program,
        keep_program,
        match_program,
        element_program,
        payload_program,
    )
    RuntimeValidator().validate(linked)

    host_signatures = DEFAULT_STANDARD_LIBRARY.signatures()
    host_generic_targets = tuple(
        entry.name
        for entry in DEFAULT_STANDARD_LIBRARY.entries
        if entry.is_generic
    )
    manifest = collect_linked_specializations(
        linked,
        external_signatures=host_signatures,
        host_generic_targets=host_generic_targets,
    )
    require(
        "type_of<int>" in manifest.canonical_ids,
        "type_of<int> specialization missing",
    )
    require(
        "type_matches<diagnostic>" in manifest.canonical_ids,
        "type_matches<diagnostic> specialization missing",
    )
    require(
        "identity<type_info>" in manifest.canonical_ids,
        "identity<type_info> specialization missing",
    )
    require(
        "collection_single<type_info>" in manifest.canonical_ids,
        "collection_single<type_info> specialization missing",
    )

    lowered = lower_linked_generics(
        linked,
        external_signatures=host_signatures,
        host_generic_targets=host_generic_targets,
    )
    RuntimeValidator().validate(lowered.program)
    audit = audit_lowered_generics(lowered)
    require(audit.closed, "lowered reflection generic closure is open")
    require(
        lowered.specialized_functions == (),
        "host reflection generics emitted AIR functions",
    )

    engine = RuntimeEngine()
    functions = runtime_index(lowered.program)
    described = engine._evaluate_expression(
        AIRCallExpression(
            target="DescribeInt",
            arguments=(AIRIntegerLiteral(12),),
        ),
        StateSnapshot(),
        functions=functions,
    )
    require(described == "int", "compiled type description failed")

    kept = engine._evaluate_expression(
        AIRCallExpression(
            target="KeepType",
            arguments=(int_info,),
        ),
        StateSnapshot(),
        functions=functions,
    )
    require(
        kept.element_type is TYPE_INFO and kept.values == (int_info,),
        "compiled type_info generic transport failed",
    )

    matched = engine._evaluate_expression(
        AIRCallExpression(
            target="MatchDiagnostic",
            arguments=(diagnostic, RuntimeTypeInfo(DIAGNOSTIC)),
        ),
        StateSnapshot(),
        functions=functions,
    )
    require(matched is True, "compiled type matching failed")

    element = engine._evaluate_expression(
        AIRCallExpression(
            target="ElementType",
            arguments=(collection,),
        ),
        StateSnapshot(),
        functions=functions,
    )
    require(
        element.value_type is INT,
        "compiled collection element introspection failed",
    )

    payload = engine._evaluate_expression(
        AIRCallExpression(
            target="PayloadType",
            arguments=(parsed,),
        ),
        StateSnapshot(),
        functions=functions,
    )
    require(
        payload.value_type is INT,
        "compiled result payload introspection failed",
    )

    require(TYPE_INFO is not RESULT, "type_info collapsed into result")
    require(TYPE_INFO is not COLLECTION, "type_info collapsed into collection")
    require(TYPE_INFO is not DIAGNOSTIC, "type_info collapsed into diagnostic")

    print("AFP-P10.11 safe reflection and introspection smoke test passed.")
    print("Canonical opaque type_info identity: PASS")
    print("Exact primitive and opaque value introspection: PASS")
    print("Safe type-name resolution and structured failure: PASS")
    print("Canonical predicates, comparison, and enumeration: PASS")
    print("Collection element and result payload inspection: PASS")
    print("No Python object or implementation reflection: PASS")
    print("Result, collection, and host-generic transport: PASS")
    print("Host-generic closure and lowering: PASS")
    print("Compiled runtime dispatch: PASS")


if __name__ == "__main__":
    main()