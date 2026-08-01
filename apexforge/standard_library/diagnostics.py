"""Pure AFP-P10.10 structured diagnostic utilities."""

from __future__ import annotations

from standard_library.diagnostic_value import RuntimeDiagnostic
from standard_library.model import (
    BuiltinFunction,
    StandardLibraryInvocationError,
)
from standard_library.result_value import RuntimeResult
from type_system.inference import FunctionSignature
from type_system.model import (
    BOOL,
    DIAGNOSTIC,
    INT,
    RESULT,
    STRING,
)


def _construct(
    severity: str,
    code: str,
    message: str,
    subject: str = "",
) -> RuntimeDiagnostic:
    try:
        return RuntimeDiagnostic(
            severity=severity,
            code=code,
            message=message,
            subject=subject,
        )
    except (TypeError, ValueError) as exc:
        raise StandardLibraryInvocationError(
            code="APX-STDLIB-010",
            message=f"Invalid structured diagnostic: {exc}",
        ) from exc


def _diagnostic_info(code: str, message: str) -> RuntimeDiagnostic:
    return _construct("info", code, message)


def _diagnostic_warning(code: str, message: str) -> RuntimeDiagnostic:
    return _construct("warning", code, message)


def _diagnostic_error(code: str, message: str) -> RuntimeDiagnostic:
    return _construct("error", code, message)


def _diagnostic_with_subject(
    value: RuntimeDiagnostic,
    subject: str,
) -> RuntimeDiagnostic:
    return _construct(
        value.severity,
        value.code,
        value.message,
        subject,
    )


def _diagnostic_clear_subject(
    value: RuntimeDiagnostic,
) -> RuntimeDiagnostic:
    if not value.subject:
        return value
    return RuntimeDiagnostic(
        value.severity,
        value.code,
        value.message,
    )


def _diagnostic_severity(value: RuntimeDiagnostic) -> str:
    return value.severity


def _diagnostic_code(value: RuntimeDiagnostic) -> str:
    return value.code


def _diagnostic_message(value: RuntimeDiagnostic) -> str:
    return value.message


def _diagnostic_subject(value: RuntimeDiagnostic) -> str:
    return value.subject


def _diagnostic_rank(value: RuntimeDiagnostic) -> int:
    return value.rank


def _diagnostic_is_info(value: RuntimeDiagnostic) -> bool:
    return value.is_info


def _diagnostic_is_warning(value: RuntimeDiagnostic) -> bool:
    return value.is_warning


def _diagnostic_is_error(value: RuntimeDiagnostic) -> bool:
    return value.is_error


def _diagnostic_format(value: RuntimeDiagnostic) -> str:
    return value.render()


def _diagnostic_equal(
    left: RuntimeDiagnostic,
    right: RuntimeDiagnostic,
) -> bool:
    return left == right


def _diagnostic_same_kind(
    left: RuntimeDiagnostic,
    right: RuntimeDiagnostic,
) -> bool:
    return (
        left.severity == right.severity
        and left.code == right.code
    )


def _diagnostic_from_result(
    value: RuntimeResult,
    subject: str,
) -> RuntimeDiagnostic:
    if value.ok:
        return _construct(
            "info",
            "RESULT_OK",
            (
                "Result succeeded with payload type "
                f"{value.payload_type.name}."
            ),
            subject,
        )
    return _construct(
        "error",
        value.error_code,
        value.error_message,
        subject,
    )


def _diagnostic_to_result(
    value: RuntimeDiagnostic,
) -> RuntimeResult:
    return RuntimeResult.success(DIAGNOSTIC, value)


def _result_diagnostic_or(
    value: RuntimeResult,
    fallback: RuntimeDiagnostic,
) -> RuntimeDiagnostic:
    if value.ok and value.payload_type is DIAGNOSTIC:
        return value.value
    return fallback


DIAGNOSTIC_BUILTINS = (
    BuiltinFunction(
        name="diagnostic_info",
        signature=FunctionSignature(
            name="diagnostic_info",
            parameter_types=(STRING, STRING),
            return_type=DIAGNOSTIC,
        ),
        implementation=_diagnostic_info,
        documentation="Create one immutable informational diagnostic.",
    ),
    BuiltinFunction(
        name="diagnostic_warning",
        signature=FunctionSignature(
            name="diagnostic_warning",
            parameter_types=(STRING, STRING),
            return_type=DIAGNOSTIC,
        ),
        implementation=_diagnostic_warning,
        documentation="Create one immutable warning diagnostic.",
    ),
    BuiltinFunction(
        name="diagnostic_error",
        signature=FunctionSignature(
            name="diagnostic_error",
            parameter_types=(STRING, STRING),
            return_type=DIAGNOSTIC,
        ),
        implementation=_diagnostic_error,
        documentation="Create one immutable error diagnostic.",
    ),
    BuiltinFunction(
        name="diagnostic_with_subject",
        signature=FunctionSignature(
            name="diagnostic_with_subject",
            parameter_types=(DIAGNOSTIC, STRING),
            return_type=DIAGNOSTIC,
        ),
        implementation=_diagnostic_with_subject,
        documentation="Return a diagnostic with one immutable subject.",
    ),
    BuiltinFunction(
        name="diagnostic_clear_subject",
        signature=FunctionSignature(
            name="diagnostic_clear_subject",
            parameter_types=(DIAGNOSTIC,),
            return_type=DIAGNOSTIC,
        ),
        implementation=_diagnostic_clear_subject,
        documentation="Return a diagnostic without its subject.",
    ),
    BuiltinFunction(
        name="diagnostic_severity",
        signature=FunctionSignature(
            name="diagnostic_severity",
            parameter_types=(DIAGNOSTIC,),
            return_type=STRING,
        ),
        implementation=_diagnostic_severity,
        documentation="Return info, warning, or error.",
    ),
    BuiltinFunction(
        name="diagnostic_code",
        signature=FunctionSignature(
            name="diagnostic_code",
            parameter_types=(DIAGNOSTIC,),
            return_type=STRING,
        ),
        implementation=_diagnostic_code,
        documentation="Return the structured diagnostic code.",
    ),
    BuiltinFunction(
        name="diagnostic_message",
        signature=FunctionSignature(
            name="diagnostic_message",
            parameter_types=(DIAGNOSTIC,),
            return_type=STRING,
        ),
        implementation=_diagnostic_message,
        documentation="Return the structured diagnostic message.",
    ),
    BuiltinFunction(
        name="diagnostic_subject",
        signature=FunctionSignature(
            name="diagnostic_subject",
            parameter_types=(DIAGNOSTIC,),
            return_type=STRING,
        ),
        implementation=_diagnostic_subject,
        documentation="Return the diagnostic subject or empty string.",
    ),
    BuiltinFunction(
        name="diagnostic_rank",
        signature=FunctionSignature(
            name="diagnostic_rank",
            parameter_types=(DIAGNOSTIC,),
            return_type=INT,
        ),
        implementation=_diagnostic_rank,
        documentation="Return info=0, warning=1, or error=2.",
    ),
    BuiltinFunction(
        name="diagnostic_is_info",
        signature=FunctionSignature(
            name="diagnostic_is_info",
            parameter_types=(DIAGNOSTIC,),
            return_type=BOOL,
        ),
        implementation=_diagnostic_is_info,
        documentation="Return whether severity is info.",
    ),
    BuiltinFunction(
        name="diagnostic_is_warning",
        signature=FunctionSignature(
            name="diagnostic_is_warning",
            parameter_types=(DIAGNOSTIC,),
            return_type=BOOL,
        ),
        implementation=_diagnostic_is_warning,
        documentation="Return whether severity is warning.",
    ),
    BuiltinFunction(
        name="diagnostic_is_error",
        signature=FunctionSignature(
            name="diagnostic_is_error",
            parameter_types=(DIAGNOSTIC,),
            return_type=BOOL,
        ),
        implementation=_diagnostic_is_error,
        documentation="Return whether severity is error.",
    ),
    BuiltinFunction(
        name="diagnostic_format",
        signature=FunctionSignature(
            name="diagnostic_format",
            parameter_types=(DIAGNOSTIC,),
            return_type=STRING,
        ),
        implementation=_diagnostic_format,
        documentation="Render a deterministic locale-independent line.",
    ),
    BuiltinFunction(
        name="diagnostic_equal",
        signature=FunctionSignature(
            name="diagnostic_equal",
            parameter_types=(DIAGNOSTIC, DIAGNOSTIC),
            return_type=BOOL,
        ),
        implementation=_diagnostic_equal,
        documentation="Return whether all diagnostic fields are equal.",
    ),
    BuiltinFunction(
        name="diagnostic_same_kind",
        signature=FunctionSignature(
            name="diagnostic_same_kind",
            parameter_types=(DIAGNOSTIC, DIAGNOSTIC),
            return_type=BOOL,
        ),
        implementation=_diagnostic_same_kind,
        documentation="Compare severity and code while ignoring text fields.",
    ),
    BuiltinFunction(
        name="diagnostic_from_result",
        signature=FunctionSignature(
            name="diagnostic_from_result",
            parameter_types=(RESULT, STRING),
            return_type=DIAGNOSTIC,
        ),
        implementation=_diagnostic_from_result,
        documentation="Project one structured result into a diagnostic.",
    ),
    BuiltinFunction(
        name="diagnostic_to_result",
        signature=FunctionSignature(
            name="diagnostic_to_result",
            parameter_types=(DIAGNOSTIC,),
            return_type=RESULT,
        ),
        implementation=_diagnostic_to_result,
        documentation="Wrap a diagnostic in a successful structured result.",
    ),
    BuiltinFunction(
        name="result_diagnostic_or",
        signature=FunctionSignature(
            name="result_diagnostic_or",
            parameter_types=(RESULT, DIAGNOSTIC),
            return_type=DIAGNOSTIC,
        ),
        implementation=_result_diagnostic_or,
        documentation="Extract a diagnostic result or return the fallback.",
    ),
)


__all__ = ("DIAGNOSTIC_BUILTINS",)