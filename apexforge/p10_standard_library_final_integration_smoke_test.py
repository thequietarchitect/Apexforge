"""AFP-P10.12 final standard-library integration and freeze smoke test."""

from __future__ import annotations

from dataclasses import replace
import importlib

from air.expressions import (
    AIRCallExpression,
    AIRIntegerLiteral,
    AIRStringLiteral,
)
from air.linker import link_programs
from language.compiler import compile_source
from language.validation.runtime_validator import RuntimeValidator
from runtime.engine import RuntimeEngine
from runtime.state import StateSnapshot
from standard_library import (
    ALL_STANDARD_LIBRARY_BUILTINS,
    DEFAULT_STANDARD_LIBRARY,
    P10_FREEZE_CANDIDATE,
    P10_STANDARD_LIBRARY_VERSION,
    STANDARD_LIBRARY_GROUPS,
    RuntimeCollection,
    RuntimeDiagnostic,
    RuntimeRandom,
    RuntimeResult,
    RuntimeTime,
    RuntimeTypeInfo,
    StandardLibraryRegistry,
    audit_standard_library,
    standard_library_contract_payload,
    standard_library_contract_sha256,
)
from type_system.model import (
    BUILTIN_TYPES,
    COLLECTION,
    DIAGNOSTIC,
    INT,
    STRING,
    TIME,
    TYPE_INFO,
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def call(name: str, *arguments, type_arguments=()):
    return DEFAULT_STANDARD_LIBRARY.invoke(
        name,
        tuple(arguments),
        type_arguments=tuple(type_arguments),
    )


def runtime_index(program):
    index = {}
    for function in program.functions:
        index[function.id] = function
        index[function.name] = function
    return index


def evaluate_call(engine, program, target, *arguments):
    return engine._evaluate_expression(
        AIRCallExpression(
            target=target,
            arguments=tuple(arguments),
        ),
        StateSnapshot(),
        functions=runtime_index(program),
    )


def require_tamper_rejected() -> None:
    group_name, entries = STANDARD_LIBRARY_GROUPS[0]
    altered_entry = replace(
        entries[0],
        documentation=(
            entries[0].documentation
            + " Contract-altering text."
        ),
    )
    altered_groups = (
        (group_name, (altered_entry,) + entries[1:]),
    ) + STANDARD_LIBRARY_GROUPS[1:]
    altered_entries = tuple(
        entry
        for _, group_entries in altered_groups
        for entry in group_entries
    )
    altered_registry = StandardLibraryRegistry(altered_entries)

    try:
        audit_standard_library(
            altered_registry,
            altered_groups,
        )
    except ValueError as error:
        require(
            "fingerprint changed" in str(error),
            "contract tamper used the wrong rejection",
        )
    else:
        raise AssertionError("altered P10 contract unexpectedly passed")


def main() -> None:
    require(
        P10_STANDARD_LIBRARY_VERSION == "10.12",
        "P10 final API version changed",
    )

    audit = audit_standard_library()
    require(audit.closed, "P10 final audit did not close")
    require(audit.group_count == 12, "P10 group count changed")
    require(audit.builtin_count == 134, "P10 built-in count changed")
    require(
        audit.generic_builtin_count == 16,
        "P10 generic built-in count changed",
    )
    require(audit.signature_count == 134, "P10 signature count changed")
    require(
        audit.canonical_id_count == 134,
        "P10 canonical-ID count changed",
    )
    require(audit.builtin_type_count == 11, "P10 built-in type count changed")
    require(
        audit.contract_sha256
        == P10_FREEZE_CANDIDATE.contract_sha256,
        "P10 manifest and audit fingerprints differ",
    )
    require(
        standard_library_contract_sha256()
        == audit.contract_sha256,
        "P10 public fingerprint helper changed",
    )

    require(
        P10_FREEZE_CANDIDATE.phase == "AFP-P10",
        "P10 freeze phase changed",
    )
    require(
        P10_FREEZE_CANDIDATE.designation == "Pure Standard Library",
        "P10 freeze designation changed",
    )
    require(
        P10_FREEZE_CANDIDATE.status == "FREEZE CANDIDATE",
        "P10 freeze status changed",
    )
    require(
        len(P10_FREEZE_CANDIDATE.slices) == 13,
        "P10 freeze slice inventory changed",
    )
    require(
        P10_FREEZE_CANDIDATE.slices[-1]
        == "P10.12 Final Integration, Contract Audit, and Freeze",
        "P10.12 freeze slice disappeared",
    )
    for module_name in P10_FREEZE_CANDIDATE.public_modules:
        imported = importlib.import_module(module_name)
        require(
            imported.__name__ == module_name,
            f"P10 public module failed import: {module_name}",
        )

    require(
        tuple(name for name, _ in STANDARD_LIBRARY_GROUPS)
        == (
            "core",
            "numeric",
            "strings",
            "booleans",
            "conversions",
            "generic_values",
            "results",
            "collections",
            "time",
            "random",
            "diagnostics",
            "reflection",
        ),
        "P10 standard-library group order changed",
    )
    require(
        ALL_STANDARD_LIBRARY_BUILTINS
        == tuple(
            entry
            for _, entries in STANDARD_LIBRARY_GROUPS
            for entry in entries
        ),
        "P10 flattened composition changed",
    )
    require(
        DEFAULT_STANDARD_LIBRARY.entries
        == tuple(
            sorted(
                ALL_STANDARD_LIBRARY_BUILTINS,
                key=lambda entry: entry.name,
            )
        ),
        "P10 registry no longer exactly matches composition",
    )
    require(
        tuple(value_type.name for value_type in BUILTIN_TYPES)
        == (
            "int",
            "bool",
            "string",
            "float",
            "void",
            "result",
            "collection",
            "time",
            "random",
            "diagnostic",
            "type_info",
        ),
        "P10 built-in type inventory changed",
    )

    payload = standard_library_contract_payload()
    require(payload["version"] == "10.12", "contract payload version changed")
    require(len(payload["groups"]) == 12, "contract payload groups changed")
    require(
        len(payload["registry_names"]) == 134,
        "contract payload registry changed",
    )
    require_tamper_rejected()

    # Cross-slice deterministic value flow.
    epoch = call("time_unix_epoch")
    require(type(epoch) is RuntimeTime, "epoch did not produce RuntimeTime")
    parsed_epoch = call(
        "time_parse_iso_utc",
        "1970-01-01T00:00:00.000Z",
    )
    require(type(parsed_epoch) is RuntimeResult, "time parse lost result")
    recovered_epoch = call("result_time_or", parsed_epoch, epoch)
    require(
        recovered_epoch == epoch
        and call("time_to_iso_utc", recovered_epoch)
        == "1970-01-01T00:00:00.000Z",
        "time/result integration changed",
    )

    seed = call("random_from_seed", 1729)
    require(type(seed) is RuntimeRandom, "seed did not produce RuntimeRandom")
    first_draw = call("random_int_between", seed, 0, 1)
    repeated_draw = call("random_int_between", seed, 0, 1)
    require(
        first_draw == repeated_draw,
        "deterministic random replay changed",
    )
    index = call("result_int_or", first_draw, 0)

    pair = call(
        "collection_pair",
        11,
        29,
        type_arguments=(INT,),
    )
    require(
        type(pair) is RuntimeCollection
        and pair.element_type is INT,
        "generic collection construction changed",
    )
    selected = call(
        "collection_get_or",
        pair,
        index,
        -1,
        type_arguments=(INT,),
    )
    require(selected in (11, 29), "random collection selection changed")

    collection_info = call(
        "type_of",
        pair,
        type_arguments=(COLLECTION,),
    )
    require(
        type(collection_info) is RuntimeTypeInfo
        and call("type_name", collection_info) == "collection",
        "collection reflection changed",
    )
    reflected_info = call(
        "identity",
        collection_info,
        type_arguments=(TYPE_INFO,),
    )
    require(
        reflected_info is collection_info,
        "opaque host-generic transport changed",
    )

    diagnostic = call(
        "diagnostic_from_result",
        first_draw,
        "P10.12",
    )
    require(
        type(diagnostic) is RuntimeDiagnostic
        and call("diagnostic_is_info", diagnostic) is True,
        "result/diagnostic projection changed",
    )
    diagnostic_result = call("diagnostic_to_result", diagnostic)
    diagnostic_round_trip = call(
        "result_diagnostic_or",
        diagnostic_result,
        diagnostic,
    )
    require(
        diagnostic_round_trip == diagnostic,
        "diagnostic/result round trip changed",
    )
    diagnostic_pair = call(
        "collection_pair",
        diagnostic,
        diagnostic_round_trip,
        type_arguments=(DIAGNOSTIC,),
    )
    require(
        diagnostic_pair.element_type is DIAGNOSTIC
        and call("collection_length", diagnostic_pair) == 2,
        "diagnostic collection transport changed",
    )

    # Compiler, validator, and runtime integration across final opaque types.
    program = link_programs(
        compile_source(
            """
            function StableState(seed : int) : int {
                return random_state(random_advance(random_from_seed(seed)))
            }
            """
        ),
        compile_source(
            """
            function ReflectedName(value : int) : string {
                return type_name(type_of(value))
            }
            """
        ),
        compile_source(
            """
            function EpochText() : string {
                return time_to_iso_utc(time_unix_epoch())
            }
            """
        ),
        compile_source(
            """
            function RenderError(code : string, text : string) : string {
                return diagnostic_format(diagnostic_error(code, text))
            }
            """
        ),
    )
    verified = RuntimeValidator().validate(program)
    require(verified.program is program, "P10.12 program failed validation")

    engine = RuntimeEngine()
    state_a = evaluate_call(
        engine,
        program,
        "StableState",
        AIRIntegerLiteral(41),
    )
    state_b = evaluate_call(
        engine,
        program,
        "StableState",
        AIRIntegerLiteral(41),
    )
    require(
        type(state_a) is int and state_a == state_b,
        "compiled deterministic random flow changed",
    )
    require(
        evaluate_call(
            engine,
            program,
            "ReflectedName",
            AIRIntegerLiteral(7),
        )
        == "int",
        "compiled reflection flow changed",
    )
    require(
        evaluate_call(engine, program, "EpochText")
        == "1970-01-01T00:00:00.000Z",
        "compiled UTC time flow changed",
    )
    rendered = evaluate_call(
        engine,
        program,
        "RenderError",
        AIRStringLiteral("FINAL_CHECK"),
        AIRStringLiteral("contract verified"),
    )
    require(
        type(rendered) is str
        and "FINAL_CHECK" in rendered
        and "contract verified" in rendered,
        "compiled diagnostic flow changed",
    )

    print("AFP-P10.12 final integration and freeze smoke test passed.")
    print("Closed 12-group composition: PASS")
    print("Canonical 134-built-in registry: PASS")
    print("Canonical 11-type inventory: PASS")
    print("Generic contract inventory: PASS")
    print("Stable contract fingerprint: PASS")
    print("Contract tamper rejection: PASS")
    print("Result/time integration: PASS")
    print("Deterministic random integration: PASS")
    print("Collection/generic integration: PASS")
    print("Diagnostic/result integration: PASS")
    print("Safe reflection integration: PASS")
    print("Compiler signature integration: PASS")
    print("Validator integration: PASS")
    print("Pure runtime dispatch: PASS")
    print("AFP-P10 freeze candidate: PASS")


if __name__ == "__main__":
    main()