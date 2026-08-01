"""AFP-P10-T2.1 canonical .apex source and grammar-contract smoke test."""

from __future__ import annotations

from language.grammar import (
    APEXFORGE_EBNF,
    ApexSourceNameError,
    CANONICAL_GRAMMAR_SHA256,
    CANONICAL_MAIN_FILENAME,
    CANONICAL_SOURCE_EXTENSION,
    CANONICAL_SOURCE_GLOB,
    COMMENTS_SUPPORTED,
    GRAMMAR_KEYWORD_TOKENS,
    GRAMMAR_ONE_CHARACTER_TOKENS,
    GRAMMAR_TWO_CHARACTER_TOKENS,
    MODULE_HEADER_KEYWORDS,
    P10_T2_GRAMMAR_VERSION,
    TOP_LEVEL_DECLARATIONS,
    canonicalize_source_name,
    grammar_fingerprint,
    is_canonical_source_name,
)
from language.lexer import (
    KEYWORDS,
    ONE_CHARACTER_TOKENS,
    TWO_CHARACTER_TOKENS,
    LexError,
    lex,
)
from language.modules import parse_module_source
from language.parser import parse
from tooling import DEFAULT_PROJECT_SOURCE, ProjectManifest


EXPECTED_GRAMMAR_SHA256 = (
    "09abf328030692267297950d8d5894e69f3d2c9c9af6642c90b9d298f3515f18"
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def require_source_error(operation, message: str) -> ApexSourceNameError:
    try:
        operation()
    except ApexSourceNameError as error:
        require(error.code == "APX-SOURCE-001", "source error code changed")
        return error
    raise AssertionError(message)


def require_lex_error(source: str) -> LexError:
    try:
        lex(source, source_name="GrammarFailure.apex")
    except LexError as error:
        return error
    raise AssertionError(f"source unexpectedly lexed: {source!r}")


def main() -> None:
    require(P10_T2_GRAMMAR_VERSION == "10-T2.1", "grammar version changed")
    require(CANONICAL_SOURCE_EXTENSION == ".apex", "source extension changed")
    require(CANONICAL_SOURCE_GLOB == "*.apex", "source glob changed")
    require(CANONICAL_MAIN_FILENAME == "main.apex", "main filename changed")
    require(DEFAULT_PROJECT_SOURCE == "src/main.apex", "scaffold drifted")

    require(
        canonicalize_source_name(r"src\main.apex") == "src/main.apex",
        "source-name slash normalization changed",
    )
    require(
        is_canonical_source_name("src/main.apex"),
        "canonical source name was rejected",
    )
    require(
        not is_canonical_source_name(r"src\main.apex"),
        "backslash spelling was treated as canonical",
    )
    require(
        not is_canonical_source_name("src/main.apx"),
        "legacy .apx spelling was treated as canonical",
    )
    require(
        not is_canonical_source_name("src/main.APEX"),
        "uppercase extension was treated as canonical",
    )
    require_source_error(
        lambda: canonicalize_source_name("src/main.apx"),
        "noncanonical extension unexpectedly succeeded",
    )
    require_source_error(
        lambda: canonicalize_source_name(" src/main.apex"),
        "edge whitespace unexpectedly succeeded",
    )

    require(dict(GRAMMAR_KEYWORD_TOKENS) == KEYWORDS, "keyword inventory drifted")
    require(
        dict(GRAMMAR_TWO_CHARACTER_TOKENS) == TWO_CHARACTER_TOKENS,
        "two-character token inventory drifted",
    )
    require(
        dict(GRAMMAR_ONE_CHARACTER_TOKENS) == ONE_CHARACTER_TOKENS,
        "one-character token inventory drifted",
    )
    require(MODULE_HEADER_KEYWORDS == ("module", "import"), "headers drifted")
    require(
        TOP_LEVEL_DECLARATIONS
        == ("function", "directive", "workflow", "authority", "principal", "role"),
        "top-level declaration inventory drifted",
    )

    require(
        grammar_fingerprint() == CANONICAL_GRAMMAR_SHA256,
        "declared grammar fingerprint does not match the grammar payload",
    )
    require(
        CANONICAL_GRAMMAR_SHA256 == EXPECTED_GRAMMAR_SHA256,
        "canonical grammar fingerprint changed",
    )
    require("FunctionDeclaration" in APEXFORGE_EBNF, "function grammar omitted")
    require("DirectiveDeclaration" in APEXFORGE_EBNF, "directive grammar omitted")
    require("Expression" in APEXFORGE_EBNF, "expression grammar omitted")

    declarations = (
        "function Identity<T>(value : T) : T { return value }",
        "function Add<T : numeric>(left : T, right : T) : T { return left + right }",
        """directive Main {
            state count : int = 0
            event ready
            authority Root
            requires run
            cause start {
                path primary @ 10 {
                    when count == 0 {
                        message \"ready\"
                        emit ready
                    } otherwise {
                        add count 1
                    }
                }
            }
        }""",
        "workflow Start { invoke Main }",
        "authority Root { capability run }",
        "role Operator { authority Root }",
        "principal Alice { role Operator authority Root }",
        """function Evaluate(a : int, b : int) : bool {
            return not false and (a + 2 * b >= 4) or true
        }""",
        """function Forward<T>(value : T) : T {
            return Identity<T>(value)
        }""",
        "function Ratio() : float { return 1.25 }",
    )
    for source in declarations:
        parsed = parse(source, source_name="GrammarAcceptance.apex")
        require(parsed is not None, f"grammar example did not parse: {source!r}")

    module_source = parse_module_source(
        "ModuleMain.apex",
        """module app.main;
import app.shared

workflow Start {
    invoke Main
}
""",
    )
    require(module_source.module_name == "app.main", "module name changed")
    require(
        tuple(item.name for item in module_source.imports) == ("app.shared",),
        "module import parsing changed",
    )
    require(
        parse(module_source.masked_source, source_name="ModuleMain.apex") is not None,
        "masked module body did not parse",
    )

    require(not COMMENTS_SUPPORTED, "comment support changed without a grammar revision")
    comment_error = require_lex_error("# not a comment")
    require(comment_error.diagnostic.code == "APX-LEX-001", "comment lex code changed")

    compatibility_manifest = ProjectManifest(
        name="Compatibility",
        sources=("src/legacy.future",),
    )
    require(
        compatibility_manifest.sources == ("src/legacy.future",),
        "T1 extension-neutral manifest compatibility was removed",
    )

    print("AFP-P10-T2.1 canonical source and grammar smoke test passed.")
    print("Canonical lowercase .apex extension: PASS")
    print("Slash-normalized source-name contract: PASS")
    print("Lexer inventory synchronization: PASS")
    print("Top-level declaration grammar: PASS")
    print("Function, directive, and expression grammar: PASS")
    print("Line-oriented module/import headers: PASS")
    print("No-comment grammar boundary: PASS")
    print("Deterministic grammar fingerprint: PASS")
    print("Frozen T1 extension-neutral compatibility: PASS")


if __name__ == "__main__":
    main()