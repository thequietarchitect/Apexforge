"""ApexForge language parser."""

from __future__ import annotations

from dataclasses import dataclass

from language.lexer import Token, lex


@dataclass(frozen=True)
class StateNode:
    name: str
    initial: int


@dataclass(frozen=True)
class DirectiveNode:
    name: str
    states: tuple[StateNode, ...]


class Parser:
    def __init__(self, tokens: list[Token]) -> None:
        self.tokens = tokens
        self.index = 0

    def current(self) -> Token:
        return self.tokens[self.index]

    def consume(self, kind: str) -> Token:
        token = self.current()

        if token.kind != kind:
            raise SyntaxError(f"Expected {kind}, got {token.kind}")

        self.index += 1
        return token

    def parse(self) -> DirectiveNode:
        self.consume("DIRECTIVE")
        name = self.consume("IDENT").value
        self.consume("LBRACE")

        states = []

        while self.current().kind != "RBRACE":
            states.append(self.parse_state())

        self.consume("RBRACE")
        self.consume("EOF")

        return DirectiveNode(
            name=name,
            states=tuple(states),
        )

    def parse_state(self) -> StateNode:
        self.consume("STATE")
        name = self.consume("IDENT").value
        self.consume("EQUAL")
        initial = int(self.consume("NUMBER").value)

        return StateNode(
            name=name,
            initial=initial,
        )


def parse(source: str) -> DirectiveNode:
    return Parser(lex(source)).parse()