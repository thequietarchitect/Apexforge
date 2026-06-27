"""ApexForge language parser."""

from __future__ import annotations

from dataclasses import dataclass

from language.lexer import Token, lex

from typing import Optional


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
class MessageActionNode:
    text: str


@dataclass(frozen=True)
class InvokeActionNode:
    target: str


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
    requirements: tuple[RequirementNode, ...] = ()
    authorities: tuple[DirectiveAuthorityNode, ...] = ()

@dataclass(frozen=True)
class WorkflowInvokeNode:
    target: str


@dataclass(frozen=True)
class WorkflowNode:
    name: str
    invocations: tuple[WorkflowInvokeNode, ...]

@dataclass(frozen=True)
class CapabilityNode:
    name: str

@dataclass(frozen=True)
class AuthorityNode:
    name: str
    capabilities: tuple[CapabilityNode, ...]
    extends: Optional[str] = None

@dataclass(frozen=True)
class RequirementNode:
    capability: str

@dataclass(frozen=True)
class DirectiveAuthorityNode:
    name: str

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.index = 0

    def current(self):
        return self.tokens[self.index]

    def consume(self, expected_kind):
        token = self.current()

        if token.kind != expected_kind:
            raise SyntaxError(f"Expected {expected_kind}, got {token.kind}")

        self.index += 1
        return token

    def parse(self):

        kind = self.current().kind

        if kind == "DIRECTIVE":
            return self.parse_directive()

        if kind == "AUTHORITY":
            return self.parse_authority()

        raise SyntaxError(
            f"Unexpected top-level token {kind}"
    )

        self.consume("RBRACE")
        self.consume("EOF")

        return DirectiveNode(
            name=name,
            states=tuple(states),
            events=tuple(events),
            causes=tuple(causes),
            requirements=tuple(requirements),
        )

    def parse_directive(self) -> DirectiveNode:
        self.consume("DIRECTIVE")
        name = self.consume("IDENT").value
        self.consume("LBRACE")

        states = []
        events = []
        causes = []
        requirements = []
        authorities = []

        while self.current().kind != "RBRACE":
            print("DIRECTIVE LOOP:", self.current(), "INDEX:", self.index)

            kind = self.current().kind

            if kind == "AUTHORITY":
                print("FOUND AUTHORITY")
                self.consume("AUTHORITY")
                authority_name = self.consume("IDENT").value
                authorities.append(DirectiveAuthorityNode(name=authority_name))
                continue

            if kind == "REQUIRES":
                print("FOUND REQUIRES")
                self.consume("REQUIRES")
                capability = self.consume("IDENT").value
                requirements.append(RequirementNode(capability=capability))
                continue

            raise SyntaxError(f"Unexpected directive token {kind}")

        self.consume("RBRACE")
        self.consume("EOF")

        return DirectiveNode(
            name=name,
            states=tuple(states),
            events=tuple(events),
            causes=tuple(causes),
            requirements=tuple(requirements),
            authorities=tuple(authorities),
    )

    def parse_workflow(self) -> WorkflowNode:
        self.consume("WORKFLOW")
        name = self.consume("IDENT").value
        self.consume("LBRACE")

        invocations: list[WorkflowInvokeNode] = []

        while self.current().kind != "RBRACE":
            self.consume("INVOKE")
            target = self.consume("IDENT").value

            invocations.append(
            WorkflowInvokeNode(target=target)
        )

        self.consume("RBRACE")
        self.consume("EOF")

        return WorkflowNode(
            name=name,
            invocations=tuple(invocations),
        )

    def parse_authority(self) -> AuthorityNode:
        self.consume("AUTHORITY")
        name = self.consume("IDENT").value

        extends = None

        if self.current().kind == "EXTENDS":
            self.consume("EXTENDS")
            extends = self.consume("IDENT").value

            self.consume("LBRACE")

            capabilities = []

            loop_count = 0

        while self.current().kind != "RBRACE":
            print("LOOP TOKEN:", self.current(), "INDEX:", self.index)

            loop_count += 1
            if loop_count > 10:
                    raise RuntimeError("Parser loop did not advance")

            if self.current().kind != "CAPABILITY":
                raise SyntaxError(
                    f"Expected CAPABILITY or RBRACE, got {self.current().kind}"
        )

            self.consume("CAPABILITY")
            capability_name = self.consume("IDENT").value

            capabilities.append(
            CapabilityNode(name=capability_name)
    )

        self.consume("RBRACE")

        return AuthorityNode(
            name=name,
            capabilities=tuple(capabilities),
            extends=extends,
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

        paths: list[PathNode] = []

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

        actions: list[object] = []

        while self.current().kind != "RBRACE":
            if self.current().kind == "ADD":
                actions.append(self.parse_add())
            elif self.current().kind == "EMIT":
                actions.append(self.parse_emit())
            elif self.current().kind == "MESSAGE":
                actions.append(self.parse_message())
            elif self.current().kind == "INVOKE":
                actions.append(self.parse_invoke())
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

        return AddActionNode(state_name=state_name, value=value)

    def parse_emit(self) -> EmitActionNode:
        self.consume("EMIT")
        event_name = self.consume("IDENT").value

        return EmitActionNode(event_name=event_name)

    def parse_message(self) -> MessageActionNode:
        self.consume("MESSAGE")
        text = self.consume("STRING").value

        return MessageActionNode(text=text)

    def parse_invoke(self) -> InvokeActionNode:
        self.consume("INVOKE")
        target = self.consume("IDENT").value

        return InvokeActionNode(target=target)

    def parse_requirement(self) -> RequirementNode:
        self.consume("REQUIRES")
        capability = self.consume("IDENT").value

        return RequirementNode(
            capability=capability,
        )


def parse(source: str):
    parser = Parser(lex(source))

    if parser.current().kind == "WORKFLOW":
        return parser.parse_workflow()

    if parser.current().kind == "AUTHORITY":
        return parser.parse_authority()

    return parser.parse()