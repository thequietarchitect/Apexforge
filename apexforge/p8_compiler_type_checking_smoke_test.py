"""AFP-P8.4B compiler type-checking integration smoke test."""

from __future__ import annotations

import language.compiler as compiler_module
import type_system.inference as inference_module
from type_system.model import BOOL, STRING


def require(
    condition: bool,
    message: str,
) -> None:
    if not condition:
        raise AssertionError(message)


def require_compiler_error(
    source: str,
    expected_code: str,
    *,
    function_signatures=None,
) -> compiler_module.CompilerError:
    try:
        compiler_module.compile_source_with_map(
            source,
            source_name="p8_type_check.apex",
            function_signatures=function_signatures,
        )
    except compiler_module.CompilerError as error:
        require(
            error.diagnostic.code == expected_code,
            (
                f"expected compiler diagnostic {expected_code}, "
                f"received {error.diagnostic.code}: "
                f"{error.diagnostic.message}"
            ),
        )
        require(
            error.diagnostic.stage == "compile",
            "type failure did not remain a compile-stage diagnostic",
        )
        require(
            error.diagnostic.span is not None,
            "type failure lost source provenance",
        )
        require(
            error.diagnostic.span.source_name == "p8_type_check.apex",
            "type failure changed its source name",
        )
        return error

    raise AssertionError(
        f"expected compiler diagnostic {expected_code}, but source compiled"
    )


def main() -> None:
    typed_states = compiler_module.compile_source(
        "directive Profile { "
        "state count : int = 1 "
        "state enabled : bool = true "
        'state label : string = "ready" '
        "}"
    )
    require(
        len(typed_states.states) == 3,
        "valid typed state initializers did not compile",
    )

    state_mismatch = require_compiler_error(
        "directive Bad { "
        'state count : int = "wrong" '
        "}",
        "APX-TYPE-011",
    )
    require(
        "State 'count' initializer" in state_mismatch.diagnostic.message,
        "state mismatch diagnostic omitted its owner",
    )

    valid_function = compiler_module.compile_source(
        "function Normalize(value : int, enabled : bool) : int { "
        "let adjusted = value + 1 "
        "when enabled { "
        "return adjusted "
        "} otherwise { "
        "return value "
        "} "
        "}"
    )
    require(
        len(valid_function.functions) == 1,
        "valid typed function did not compile",
    )

    require_compiler_error(
        "function Bad(value : string) : string { "
        "return -value "
        "}",
        "APX-TYPE-003",
    )

    require_compiler_error(
        "function Bad(value : int) : int { "
        "when value { "
        "return value "
        "} otherwise { "
        "return 0 "
        "} "
        "}",
        "APX-TYPE-012",
    )

    require_compiler_error(
        "function Bad(value : int) : string { "
        "return value "
        "}",
        "APX-TYPE-011",
    )

    require_compiler_error(
        "function Bad(flag : bool) : int { "
        "when flag { "
        "return 1 "
        "} otherwise { "
        'return "wrong" '
        "} "
        "}",
        "APX-TYPE-011",
    )

    require_compiler_error(
        "function Bad(value) : int { "
        "return value "
        "}",
        "APX-TYPE-002",
    )

    legacy = compiler_module.compile_source(
        "function legacy_passthrough(value) { "
        "return value "
        "}"
    )
    require(
        len(legacy.functions) == 1,
        "fully legacy P7 function lost source compatibility",
    )

    deferred_external = compiler_module.compile_source(
        "function UseExternal(value : int) : int { "
        "return external(value) "
        "}"
    )
    require(
        len(deferred_external.functions) == 1,
        "unresolved external call was not deferred",
    )

    external_text_signature = inference_module.FunctionSignature(
        name="external_text",
        parameter_types=(BOOL,),
        return_type=STRING,
    )
    require_compiler_error(
        "function UseExternalText() : string { "
        "return external_text(1) "
        "}",
        "APX-TYPE-008",
        function_signatures={
            "external_text": external_text_signature,
        },
    )

    known_external = compiler_module.compile_source(
        "function UseExternalText(flag : bool) : string { "
        "return external_text(flag) "
        "}",
        function_signatures={
            "external_text": external_text_signature,
        },
    )
    require(
        len(known_external.functions) == 1,
        "known external signature did not type-check",
    )

    require_compiler_error(
        "function BranchScope(flag : bool) : int { "
        "when flag { "
        "let inner = 1 "
        "return inner "
        "} otherwise { "
        "return inner "
        "} "
        "}",
        "APX-TYPE-001",
    )

    print("AFP-P8.4B compiler type-checking smoke test passed.")
    print("Typed state initializer checking: PASS")
    print("Typed local inference: PASS")
    print("Function condition checking: PASS")
    print("Declared return checking: PASS")
    print("Branch return consistency: PASS")
    print("Source-aware type diagnostics: PASS")
    print("Legacy P7 compatibility: PASS")
    print("Deferred external calls: PASS")
    print("Explicit signature checking: PASS")


if __name__ == "__main__":
    main()