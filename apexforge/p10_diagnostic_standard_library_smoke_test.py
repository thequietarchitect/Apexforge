"""AFP-P10.10 structured diagnostic utilities smoke test."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

from air.expressions import (
    AIRCallExpression,
    AIRStringLiteral,
)
from air.linker import link_programs
from language.compiler import compile_source
from language.validation.runtime_validator import RuntimeValidator
from runtime.engine import RuntimeEngine
from runtime.state import StateSnapshot
from standard_library import (
    DEFAULT_STANDARD_LIBRARY,
    DIAGNOSTIC_BUILTINS,
    DIAGNOSTIC_SEVERITIES,
    MAX_DIAGNOSTIC_CODE_CODE_POINTS,
    MAX_DIAGNOSTIC_MESSAGE_CODE_POINTS,
    MAX_DIAGNOSTIC_SUBJECT_CODE_POINTS,
    P10_STANDARD_LIBRARY_VERSION,
    RuntimeCollection,
    RuntimeDiagnostic,
    RuntimeResult,
    StandardLibraryInvocationError,
)
from type_system.closure import collect_linked_specializations
from type_system.freeze import audit_lowered_generics
from type_system.lowering import lower_linked_generics
from type_system.model import (
    COLLECTION,
    DIAGNOSTIC,
    RANDOM,
    RESULT,
    TIME,
    is_builtin_type,
    resolve_builtin_type,
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def call(name: str, *arguments):
    return DEFAULT_STANDARD_LIBRARY.invoke(name, tuple(arguments))


def require_invocation_error(
    name: str,
    *arguments,
    code: str,
) -> StandardLibraryInvocationError:
    try:
        call(name, *arguments)
    except StandardLibraryInvocationError as exc:
        require(exc.code == code, f"{name} returned {exc.code}, not {code}")
        return exc
    raise AssertionError(f"{name} unexpectedly succeeded")


def runtime_index(program):
    index = {}
    for function in program.functions:
        index[function.id] = function
        index[function.name] = function
    return index


def main() -> None:
    require(P10_STANDARD_LIBRARY_VERSION == "10.12", "version changed")
    require(len(DIAGNOSTIC_BUILTINS) == 19, "diagnostic built-in count changed")
    require(
        DIAGNOSTIC_SEVERITIES == ("info", "warning", "error"),
        "diagnostic severity order changed",
    )
    require(MAX_DIAGNOSTIC_CODE_CODE_POINTS == 64, "code limit changed")
    require(
        MAX_DIAGNOSTIC_MESSAGE_CODE_POINTS == 2048,
        "message limit changed",
    )
    require(
        MAX_DIAGNOSTIC_SUBJECT_CODE_POINTS == 256,
        "subject limit changed",
    )
    require(
        resolve_builtin_type("diagnostic") is DIAGNOSTIC,
        "diagnostic type did not resolve",
    )
    require(is_builtin_type("diagnostic"), "diagnostic type not registered")

    expected_names = {
        "diagnostic_info",
        "diagnostic_warning",
        "diagnostic_error",
        "diagnostic_with_subject",
        "diagnostic_clear_subject",
        "diagnostic_severity",
        "diagnostic_code",
        "diagnostic_message",
        "diagnostic_subject",
        "diagnostic_rank",
        "diagnostic_is_info",
        "diagnostic_is_warning",
        "diagnostic_is_error",
        "diagnostic_format",
        "diagnostic_equal",
        "diagnostic_same_kind",
        "diagnostic_from_result",
        "diagnostic_to_result",
        "result_diagnostic_or",
    }
    require(
        expected_names.issubset(DEFAULT_STANDARD_LIBRARY.names),
        "diagnostic registry entries are incomplete",
    )

    info = call("diagnostic_info", "APX-INFO-001", "Index built.")
    warning = call(
        "diagnostic_warning",
        "APX-WARN-002",
        "Fallback selected.",
    )
    error = call(
        "diagnostic_error",
        "APX-TEST-003",
        "Value failed validation.",
    )
    require(type(info) is RuntimeDiagnostic, "info constructor changed")
    require(type(warning) is RuntimeDiagnostic, "warning constructor changed")
    require(type(error) is RuntimeDiagnostic, "error constructor changed")
    require(call("diagnostic_rank", info) == 0, "info rank changed")
    require(call("diagnostic_rank", warning) == 1, "warning rank changed")
    require(call("diagnostic_rank", error) == 2, "error rank changed")
    require(call("diagnostic_is_info", info) is True, "info predicate failed")
    require(
        call("diagnostic_is_warning", warning) is True,
        "warning predicate failed",
    )
    require(call("diagnostic_is_error", error) is True, "error predicate failed")
    require(
        call("diagnostic_severity", error) == "error",
        "severity accessor changed",
    )
    require(
        call("diagnostic_code", error) == "APX-TEST-003",
        "code accessor changed",
    )
    require(
        call("diagnostic_message", error) == "Value failed validation.",
        "message accessor changed",
    )
    require(
        call("diagnostic_subject", error) == "",
        "new diagnostic unexpectedly had a subject",
    )

    subject_error = call(
        "diagnostic_with_subject",
        error,
        "parser:input",
    )
    require(subject_error is not error, "subject operation mutated in place")
    require(
        call("diagnostic_subject", subject_error) == "parser:input",
        "subject accessor changed",
    )
    require(
        call("diagnostic_format", subject_error)
        == (
            "[error:APX-TEST-003] parser:input: "
            "Value failed validation."
        ),
        "diagnostic rendering changed",
    )
    require(
        call("diagnostic_format", error)
        == "[error:APX-TEST-003] Value failed validation.",
        "subject-free rendering changed",
    )
    cleared = call("diagnostic_clear_subject", subject_error)
    require(cleared == error, "subject clearing changed diagnostic fields")
    require(
        call("diagnostic_clear_subject", error) is error,
        "clearing an empty subject did not preserve identity",
    )

    equal_error = call(
        "diagnostic_error",
        "APX-TEST-003",
        "Value failed validation.",
    )
    related_error = call(
        "diagnostic_error",
        "APX-TEST-003",
        "A different message.",
    )
    require(
        call("diagnostic_equal", error, equal_error) is True,
        "equal diagnostics compared unequal",
    )
    require(
        call("diagnostic_equal", error, related_error) is False,
        "different diagnostics compared equal",
    )
    require(
        call("diagnostic_same_kind", error, related_error) is True,
        "same severity/code kind was not recognized",
    )
    require(
        call("diagnostic_same_kind", error, warning) is False,
        "different diagnostic kinds collapsed",
    )

    bad_code = require_invocation_error(
        "diagnostic_error",
        "bad code",
        "Message.",
        code="APX-STDLIB-010",
    )
    require(
        "RuntimeDiagnostic.code" in bad_code.message,
        "invalid-code diagnostic omitted its field",
    )
    require_invocation_error(
        "diagnostic_info",
        "EMPTY",
        "",
        code="APX-STDLIB-010",
    )
    require_invocation_error(
        "diagnostic_with_subject",
        error,
        "line\nbreak",
        code="APX-STDLIB-010",
    )

    failed_parse = call("string_to_int", "not-an-int")
    failed_diagnostic = call(
        "diagnostic_from_result",
        failed_parse,
        "integer parser",
    )
    require(
        failed_diagnostic.severity == "error"
        and failed_diagnostic.code == "INVALID_INT"
        and failed_diagnostic.message == failed_parse.error_message
        and failed_diagnostic.subject == "integer parser",
        "failed-result diagnostic projection changed",
    )
    successful_parse = call("string_to_int", "42")
    success_diagnostic = call(
        "diagnostic_from_result",
        successful_parse,
        "integer parser",
    )
    require(
        success_diagnostic.severity == "info"
        and success_diagnostic.code == "RESULT_OK"
        and "int" in success_diagnostic.message,
        "successful-result diagnostic projection changed",
    )

    wrapped = call("diagnostic_to_result", subject_error)
    require(
        type(wrapped) is RuntimeResult
        and wrapped.ok
        and wrapped.payload_type is DIAGNOSTIC
        and wrapped.value is subject_error,
        "diagnostic result wrapping changed",
    )
    require(
        call("result_diagnostic_or", wrapped, info) is subject_error,
        "diagnostic result extraction changed",
    )
    require(
        call("result_diagnostic_or", failed_parse, info) is info,
        "diagnostic fallback extraction changed",
    )

    preserved = call("identity", subject_error)
    require(preserved is subject_error, "identity did not preserve diagnostic")
    chosen = call("choose", True, subject_error, warning)
    require(chosen is subject_error, "choose did not transport diagnostic")
    diagnostic_collection = call("collection_single", subject_error)
    require(
        type(diagnostic_collection) is RuntimeCollection
        and diagnostic_collection.element_type is DIAGNOSTIC
        and diagnostic_collection.values == (subject_error,),
        "diagnostic collection transport changed",
    )

    try:
        error.code = "MUTATED"
    except (FrozenInstanceError, AttributeError):
        pass
    else:
        raise AssertionError("RuntimeDiagnostic was mutable")

    make_program = compile_source(
        """
        function MakeDiagnostic(code : string, text : string) : diagnostic {
            return diagnostic_error(code, text)
        }
        """
    )
    subject_program = compile_source(
        """
        function SubjectDiagnostic(
            value : diagnostic,
            subject : string
        ) : diagnostic {
            return diagnostic_with_subject(value, subject)
        }
        """
    )
    keep_program = compile_source(
        """
        function KeepDiagnostic(value : diagnostic) : collection {
            return collection_single(identity(value))
        }
        """
    )
    wrap_program = compile_source(
        """
        function WrapDiagnostic(value : diagnostic) : result {
            return diagnostic_to_result(value)
        }
        """
    )
    linked = link_programs(
        make_program,
        subject_program,
        keep_program,
        wrap_program,
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
        "identity<diagnostic>" in manifest.canonical_ids,
        "diagnostic identity specialization missing",
    )
    require(
        "collection_single<diagnostic>" in manifest.canonical_ids,
        "diagnostic collection specialization missing",
    )

    lowered = lower_linked_generics(
        linked,
        external_signatures=host_signatures,
        host_generic_targets=host_generic_targets,
    )
    RuntimeValidator().validate(lowered.program)
    audit = audit_lowered_generics(lowered)
    require(audit.closed, "lowered diagnostic generic closure is open")
    require(
        lowered.specialized_functions == (),
        "host diagnostic generics emitted AIR functions",
    )

    engine = RuntimeEngine()
    functions = runtime_index(lowered.program)
    compiled = engine._evaluate_expression(
        AIRCallExpression(
            target="SubjectDiagnostic",
            arguments=(
                AIRCallExpression(
                    target="MakeDiagnostic",
                    arguments=(
                        AIRStringLiteral("APX-COMPILED-001"),
                        AIRStringLiteral("Compiled diagnostic."),
                    ),
                ),
                AIRStringLiteral("compiler"),
            ),
        ),
        StateSnapshot(),
        functions=functions,
    )
    require(
        type(compiled) is RuntimeDiagnostic
        and compiled.severity == "error"
        and compiled.code == "APX-COMPILED-001"
        and compiled.subject == "compiler",
        "compiled diagnostic dispatch failed",
    )
    compiled_collection = engine._evaluate_expression(
        AIRCallExpression(
            target="KeepDiagnostic",
            arguments=(compiled,),
        ),
        StateSnapshot(),
        functions=functions,
    )
    require(
        compiled_collection.element_type is DIAGNOSTIC
        and compiled_collection.values == (compiled,),
        "compiled generic diagnostic transport failed",
    )
    compiled_result = engine._evaluate_expression(
        AIRCallExpression(
            target="WrapDiagnostic",
            arguments=(compiled,),
        ),
        StateSnapshot(),
        functions=functions,
    )
    require(
        compiled_result.ok
        and compiled_result.payload_type is DIAGNOSTIC
        and compiled_result.value is compiled,
        "compiled diagnostic result transport failed",
    )

    require(RESULT is not DIAGNOSTIC, "diagnostic collapsed into result type")
    require(
        COLLECTION is not DIAGNOSTIC,
        "diagnostic collapsed into collection type",
    )
    require(TIME is not DIAGNOSTIC, "diagnostic collapsed into time type")
    require(RANDOM is not DIAGNOSTIC, "diagnostic collapsed into random type")

    print("AFP-P10.10 structured diagnostic utilities smoke test passed.")
    print("Canonical opaque diagnostic type: PASS")
    print("Immutable severity, code, message, and subject fields: PASS")
    print("Deterministic formatting and predicates: PASS")
    print("Bounded validation and deterministic errors: PASS")
    print("Structured result projection and transport: PASS")
    print("Collection and host-generic transport: PASS")
    print("Host-generic closure and lowering: PASS")
    print("Compiled runtime dispatch: PASS")


if __name__ == "__main__":
    main()