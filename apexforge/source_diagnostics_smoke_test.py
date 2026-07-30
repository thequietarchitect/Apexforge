"""AFP-P5 smoke test for source provenance and structured diagnostics."""

from __future__ import annotations

from dataclasses import fields

from air.model import AIRProgram
from causality.model import DirectiveInvocation
from language.compiler import compile_source, compile_source_with_map
from language.lexer import LexError, lex
from language.parser import ParseError, parse
from language.project import (
    ProjectCompilationError,
    ProjectLinkError,
    ProjectValidationError,
    build_project,
)


VALID_CALLEE = """directive Callee {
    state count = 1
    event done

    cause Work {
        path primary @ 10 {
            add count 1
            emit done
        }
    }
}
"""


UNDEFINED_CALLER = """directive Caller {
    state count = 0

    cause Work {
        path primary @ 10 {
            invoke MissingDirective
        }
    }
}
"""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def require_raises(expected, operation, message: str):
    try:
        operation()
    except expected as exc:
        return exc
    raise AssertionError(message)


def main() -> None:
    lex_error = require_raises(
        LexError,
        lambda: lex(
            "directive A {\n    #\n}\n",
            source_name="LexFailure.apex",
        ),
        "lexer failure was not source-aware",
    )
    require(lex_error.diagnostic.code == "APX-LEX-001", "wrong lex code")
    require(
        lex_error.diagnostic.span is not None
        and lex_error.diagnostic.span.source_name == "LexFailure.apex"
        and lex_error.diagnostic.span.start.line == 2
        and lex_error.diagnostic.span.start.column == 5,
        "lexer diagnostic has the wrong source position",
    )

    parse_error = require_raises(
        ParseError,
        lambda: parse(
            "directive Broken {\n    state count =\n}\n",
            source_name="ParseFailure.apex",
        ),
        "parser failure was not source-aware",
    )
    require(parse_error.diagnostic.code == "APX-PARSE-004", "wrong parse code")
    require(
        parse_error.diagnostic.span is not None
        and parse_error.diagnostic.span.source_name == "ParseFailure.apex"
        and parse_error.diagnostic.span.start.line == 3,
        "parser diagnostic did not identify the unexpected token",
    )

    artifact = compile_source_with_map(
        VALID_CALLEE,
        source_name="Callee.apex",
    )
    require(isinstance(artifact.program, AIRProgram), "mapped compile lost AIRProgram")
    require(
        artifact.source_map.first_span(air_id="directive:Callee") is not None,
        "directive source-map entry is missing",
    )
    require(
        isinstance(compile_source(VALID_CALLEE), AIRProgram),
        "legacy compile_source API changed",
    )

    validation_error = require_raises(
        ProjectValidationError,
        lambda: build_project(
            {"Caller.apex": UNDEFINED_CALLER},
            entry="Caller",
        ),
        "undefined invocation did not fail validation",
    )
    validation_diagnostic = validation_error.diagnostics[0]
    require(
        validation_diagnostic.code == "APX-VALIDATE-002",
        "undefined invocation has the wrong validation code",
    )
    require(
        validation_diagnostic.span is not None
        and validation_diagnostic.span.source_name == "Caller.apex"
        and validation_diagnostic.span.start.line == 6,
        "undefined invocation did not map to the invoke statement",
    )

    duplicate_one = require_raises(
        ProjectLinkError,
        lambda: build_project(
            {
                "A-Callee.apex": VALID_CALLEE,
                "B-Callee.apex": VALID_CALLEE,
            },
            entry="Callee",
        ),
        "duplicate declaration did not fail linking",
    )
    duplicate_two = require_raises(
        ProjectLinkError,
        lambda: build_project(
            {
                "B-Callee.apex": VALID_CALLEE,
                "A-Callee.apex": VALID_CALLEE,
            },
            entry="Callee",
        ),
        "reversed duplicate declaration did not fail linking",
    )

    rendered_one = duplicate_one.diagnostics[0].render()
    rendered_two = duplicate_two.diagnostics[0].render()
    require(rendered_one == rendered_two, "diagnostic order depends on source insertion")
    require(
        "A-Callee.apex" in str(duplicate_one)
        and "B-Callee.apex" in str(duplicate_one),
        "duplicate diagnostic does not identify both source files",
    )

    compilation_error = require_raises(
        ProjectCompilationError,
        lambda: build_project(
            {"Broken.apex": "directive Broken { state count = }"}
        ),
        "project compilation failure was not structured",
    )
    require(
        compilation_error.diagnostics
        and compilation_error.diagnostics[0].span is not None
        and compilation_error.diagnostics[0].span.source_name == "Broken.apex",
        "project compilation diagnostic lost its filename",
    )

    require(
        "span" not in {field.name for field in fields(DirectiveInvocation)},
        "AIR model was contaminated with mandatory source-location fields",
    )

    print("ApexForge source diagnostics smoke test passed.")
    print("Lexer source position: PASS")
    print("Parser unexpected-token position: PASS")
    print("Compiler sidecar source map: PASS")
    print("Undefined invocation source mapping: PASS")
    print("Duplicate declaration provenance: PASS")
    print("Deterministic diagnostic ordering: PASS")
    print("AIR/source separation: PASS")


if __name__ == "__main__":
    main()