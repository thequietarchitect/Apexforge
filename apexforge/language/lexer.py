"""ApexForge language lexer."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class Token:
    kind: str
    value: str


SYMBOLS = {
    "{": "LBRACE",
    "}": "RBRACE",
    "=": "EQUAL",
    "@": "AT",
}

one_character_expressions = {
    "+": "PLUS",
    "-": "MINUS",
    "*": "STAR",
    "/": "SLASH",
    "%": "PERCENT",
    "(": "LPAREN",
    ")": "RPAREN",
    "<": "LESS",
    "<": "LT",
    "AND": "and",
    "OR": "or",
    "NOT": "not",
    },

two_character_expressions = {
    "==": "EQUAL_EQUAL",
    "!=": "BANG_EQUAL",
    "==": "EQEQ",         
    "!=": "NE",
    "<=": "LESS_EQUAL",
    "<=": "LTE",
    ">": "GREATER",
    ">": "GT",       "GT": ">",
    ">=": "GREATER_EQUAL",
    ">=": "GTE",
    }
    
EXPRESSIONS = one_character_expressions, two_character_expressions

KEYWORDS = (
    "directive",
    "workflow",
    "authority",
    "capability",
    "state",
    "event",
    "cause",
    "path",
    "add",
    "emit",
    "message",
    "invoke",
    "requires",
    "extends",
    "principal",
    "role",
    "set",
    "when",
)

def scan_string(
    source: str,
    opening_quote_index: int,
):
    """
    Read a quoted string and return:

        (decoded_value, index_after_closing_quote)
    """

    i = opening_quote_index + 1
    characters = []

    while i < len(source):
        current = source[i]

        # Closing quotation mark
        if current == '"':
            return "".join(characters), i + 1

        # Escape sequence
        if current == "\\":
            if i + 1 >= len(source):
                raise SyntaxError(
                    "Unterminated escape sequence "
                    "inside string literal"
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
                raise SyntaxError(
                    "Unsupported escape sequence: "
                    f"\\{escaped}"
                )

            characters.append(
                escape_values[escaped]
            )

            i += 2
            continue

        characters.append(current)
        i += 1

    raise SyntaxError(
        "Unterminated string literal"
    )

def lex(source: str) -> List[Token]:
    tokens: List[Token] = []
    i = 0

    while i < len(source):
        char = source[i]

        if char.isspace():
            i += 1
            continue

        if char == '"':
            value, i = scan_string(
                source,
                i,
        )

            tokens.append(
                Token(
                    kind="STRING",
                    value=value,
        )
    )
            continue

        if char in EXPRESSIONS:
            tokens.append(
                Token(
                    kind=EXPRESSIONS[char],
                    value=char,
            )
        )
            i += 1
            continue

        if char in SYMBOLS:
            tokens.append(Token(SYMBOLS[char], char))
            i += 1
            continue

        if char.isdigit():
            start = i
            while (
                i < len(source)
                and source[i].isdigit()
            ):
                i += 1

            number_text = source[start:i]
            tokens.append(
                Token(
                    kind="NUMBER",
                    value=number_text,
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

            if value in KEYWORDS:
                tokens.append(Token(value.upper(), value))
            else:
                tokens.append(Token("IDENT", value))

            continue

        two_character = source[i:i + 2]

        if two_character in two_character_expressions:
            tokens.append(
                Token(
                    kind=two_character_expressions[
                    two_character
                ],
                    value=two_character,
            )
        )

            i += 2
            continue

        if char in one_character_expressions:
            tokens.append(
                Token(
                    kind=one_character_expressions[
                    char
                ],
                    value=char,
            )
        )

            i += 1
            continue

        raise SyntaxError(f"Unexpected character: {char}")

    tokens.append(Token("EOF", ""))
    return tokens