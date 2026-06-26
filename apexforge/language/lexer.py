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


KEYWORDS = (
    "directive",
    "state",
    "event",
    "cause",
    "path",
    "add",
    "emit",
    "message",
    "invoke",
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
            i += 1
            start = i

            while i < len(source) and source[i] != '"':
                i += 1

            if i >= len(source):
                raise SyntaxError("Unterminated string literal")

            tokens.append(Token("STRING", source[start:i]))
            i += 1
            continue

        if char in SYMBOLS:
            tokens.append(Token(SYMBOLS[char], char))
            i += 1
            continue

        if char.isdigit():
            start = i
            while i < len(source) and source[i].isdigit():
                i += 1
            tokens.append(Token("NUMBER", source[start:i]))
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

        raise SyntaxError(f"Unexpected character: {char}")

    tokens.append(Token("EOF", ""))
    return tokens