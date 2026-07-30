"""ApexForge language lexer with source provenance."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from language.diagnostics import BuildDiagnostic
from language.source import SourceSpan, SourceText


@dataclass(frozen=True)
class Token:
    kind: str
    value: str
    span: Optional[SourceSpan] = None


class LexError(SyntaxError):
    """Source-aware ApexForge lexical failure."""

    def __init__(self, diagnostic: BuildDiagnostic) -> None:
        self.diagnostic = diagnostic
        super().__init__(diagnostic.render())


KEYWORDS = {
    "directive": "DIRECTIVE",
    "workflow": "WORKFLOW",
    "authority": "AUTHORITY",
    "capability": "CAPABILITY",
    "state": "STATE",
    "event": "EVENT",
    "cause": "CAUSE",
    "path": "PATH",
    "add": "ADD",
    "emit": "EMIT",
    "message": "MESSAGE",
    "invoke": "INVOKE",
    "requires": "REQUIRES",
    "extends": "EXTENDS",
    "principal": "PRINCIPAL",
    "role": "ROLE",
    "set": "SET",
    "when": "WHEN",
    "otherwise": "OTHERWISE",
    "and": "AND",
    "or": "OR",
    "not": "NOT",
    "true": "TRUE",
    "false": "FALSE",
    # AFP-P7.1 pure-function core.
    "function": "FUNCTION",
    "return": "RETURN",
}


TWO_CHARACTER_TOKENS = {
    "==": "EQEQ",
    "!=": "NE",
    "<=": "LTE",
    ">=": "GTE",
}


ONE_CHARACTER_TOKENS = {
    "{": "LBRACE",
    "}": "RBRACE",
    "=": "EQUAL",
    "@": "AT",
    "+": "PLUS",
    "-": "MINUS",
    "*": "STAR",
    "/": "SLASH",
    "%": "PERCENT",
    "(": "LPAREN",
    ")": "RPAREN",
    ",": "COMMA",
    "<": "LT",
    ">": "GT",
}


def _lex_error(
    source_text: SourceText,
    *,
    code: str,
    message: str,
    start: int,
    end: int,
) -> LexError:
    return LexError(
        BuildDiagnostic(
            severity="error",
            code=code,
            message=message,
            stage="lex",
            span=source_text.span(start, end),
        )
    )


def scan_string(
    source: str,
    opening_quote_index: int,
    *,
    source_name: str = "<memory>",
) -> tuple[str, int]:
    """Read a quoted string and return its decoded value and end offset."""

    source_text = SourceText(source_name, source)
    i = opening_quote_index + 1
    characters: list[str] = []

    while i < len(source):
        current = source[i]

        if current == '"':
            return "".join(characters), i + 1

        if current == "\\":
            if i + 1 >= len(source):
                raise _lex_error(
                    source_text,
                    code="APX-LEX-002",
                    message="Unterminated escape sequence inside string literal.",
                    start=i,
                    end=len(source),
                )

            escaped = source[i + 1]
            escape_values = {
                "n": "\n",
                "r": "\r",
                "t": "\t",
                '"': '"',
                "\\": "\\",
            }

            if escaped not in escape_values:
                raise _lex_error(
                    source_text,
                    code="APX-LEX-003",
                    message=f"Unsupported escape sequence \\{escaped}.",
                    start=i,
                    end=min(i + 2, len(source)),
                )

            characters.append(escape_values[escaped])
            i += 2
            continue

        characters.append(current)
        i += 1

    raise _lex_error(
        source_text,
        code="APX-LEX-004",
        message="Unterminated string literal.",
        start=opening_quote_index,
        end=len(source),
    )


def lex(
    source: str,
    *,
    source_name: str = "<memory>",
) -> List[Token]:
    if not isinstance(source, str):
        raise TypeError(
            "ApexForge lex source must be a string; "
            f"received {type(source).__name__}."
        )

    source_text = SourceText(source_name, source)
    tokens: List[Token] = []
    i = 0

    while i < len(source):
        char = source[i]

        if char.isspace():
            i += 1
            continue

        if char == '"':
            start = i
            value, i = scan_string(
                source,
                start,
                source_name=source_name,
            )
            tokens.append(
                Token(
                    kind="STRING",
                    value=value,
                    span=source_text.span(start, i),
                )
            )
            continue

        two_character = source[i : i + 2]
        if two_character in TWO_CHARACTER_TOKENS:
            tokens.append(
                Token(
                    kind=TWO_CHARACTER_TOKENS[two_character],
                    value=two_character,
                    span=source_text.span(i, i + 2),
                )
            )
            i += 2
            continue

        if char in ONE_CHARACTER_TOKENS:
            tokens.append(
                Token(
                    kind=ONE_CHARACTER_TOKENS[char],
                    value=char,
                    span=source_text.span(i, i + 1),
                )
            )
            i += 1
            continue

        if char.isdigit():
            start = i
            while i < len(source) and source[i].isdigit():
                i += 1

            number_text = source[start:i]
            tokens.append(
                Token(
                    kind="NUMBER",
                    value=number_text,
                    span=source_text.span(start, i),
                )
            )
            continue

        if char.isalpha() or char == "_":
            start = i
            while i < len(source) and (
                source[i].isalnum() or source[i] == "_"
            ):
                i += 1

            value = source[start:i]
            kind = KEYWORDS.get(value, "IDENT")
            tokens.append(
                Token(
                    kind=kind,
                    value=value,
                    span=source_text.span(start, i),
                )
            )
            continue

        raise _lex_error(
            source_text,
            code="APX-LEX-001",
            message=f"Unexpected character {char!r}.",
            start=i,
            end=i + 1,
        )

    eof_span = source_text.span(len(source), len(source))
    tokens.append(Token("EOF", "", eof_span))
    return tokens


__all__ = (
    "KEYWORDS",
    "LexError",
    "ONE_CHARACTER_TOKENS",
    "TWO_CHARACTER_TOKENS",
    "Token",
    "lex",
    "scan_string",
)