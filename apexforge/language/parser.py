"""ApexForge language parser."""

from __future__ import annotations

from dataclasses import dataclass

from language.lexer import Token, lex


@dataclass(frozen=True)
class StateNode:
    name: str
    initial: int


@dataclass(frozen=True)
class EventNode:
    name: str


@dataclass(frozen=True)
class AddActionNode:
    state_name: str
    value: int


@dataclass(frozen=True)
class EmitActionNode:
    event_name: str


@dataclass(frozen=True)
class PathNode:
    name: str
    weight: int
    actions: tuple[object, ...]


@dataclass(frozen=True)
class CauseNode:
    name: str
    paths: tuple[PathNode, ...]


@dataclass(frozen=True)
class DirectiveNode:
    name: str
    states: tuple[StateNode, ...]
    events: tuple[EventNode, ...]
    causes: tuple[CauseNode, ...]


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
        events = []
        causes = []

        while self.current().kind != "RBRACE":
            if self.current().kind == "STATE":
                states.append(self.parse_state())
            elif self.current().kind == "EVENT":
                events.append(self.parse_event())
            elif self.current().kind == "CAUSE":
                causes.append(self.parse_cause())
            else:
                raise SyntaxError(f"Unexpected token: {self.current().kind}")

        self.consume("RBRACE")
        self.consume("EOF")

        return DirectiveNode(
            name=name,
            states=tuple(states),
            events=tuple(events),
            causes=tuple(causes),
        )

    def parse_state(self) -> StateNode:
        self.consume("STATE")
        name = self.consume("IDENT").value
        self.consume("EQUAL")
        initial = int(self.consume("NUMBER").value)

        return StateNode(name=name, initial=initial)

    def parse_event(self) -> EventNode:
        self.consume("EVENT")
        name = self.consume("IDENT").value

        return EventNode(name=name)

    def parse_cause(self) -> CauseNode:
        self.consume("CAUSE")
        name = self.consume("IDENT").value
        self.consume("LBRACE")

        paths = []

        while self.current().kind != "RBRACE":
            paths.append(self.parse_path())

        self.consume("RBRACE")

        return CauseNode(name=name, paths=tuple(paths))

    def parse_path(self) -> PathNode:
        self.consume("PATH")
        name = self.consume("IDENT").value
        self.consume("AT")
        weight = int(self.consume("NUMBER").value)
        self.consume("LBRACE")

        actions = []

        while self.current().kind != "RBRACE":
            if self.current().kind == "ADD":
                actions.append(self.parse_add())
            elif self.current().kind == "EMIT":
                actions.append(self.parse_emit())
            else:
                raise SyntaxError(f"Unexpected path token: {self.current().kind}")

        self.consume("RBRACE")

        return PathNode(
            name=name,
            weight=weight,
            actions=tuple(actions),
        )

    def parse_add(self) -> AddActionNode:
        self.consume("ADD")
        state_name = self.consume("IDENT").value
        value = int(self.consume("NUMBER").value)

        return AddActionNode(
            state_name=state_name,
            value=value,
        )

    def parse_emit(self) -> EmitActionNode:
        self.consume("EMIT")
        event_name = self.consume("IDENT").value

        return EmitActionNode(event_name=event_name)


def parse(source: str) -> DirectiveNode:
    return Parser(lex(source)).parse()