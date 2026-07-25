"""ApexForge language parser with AFP-P2 expression support."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence

from language.lexer import Token, lex


# ---------------------------------------------------------------------------
# Expression AST
# ---------------------------------------------------------------------------


class ExpressionNode:
    """Base class for all expression AST nodes."""


@dataclass(frozen=True)
class IntegerLiteralNode(ExpressionNode):
    value: int


@dataclass(frozen=True)
class StringLiteralNode(ExpressionNode):
    value: str


@dataclass(frozen=True)
class BooleanLiteralNode(ExpressionNode):
    value: bool


@dataclass(frozen=True)
class IdentifierNode(ExpressionNode):
    name: str


@dataclass(frozen=True)
class UnaryExpressionNode(ExpressionNode):
    operator: str
    operand: ExpressionNode


@dataclass(frozen=True)
class BinaryExpressionNode(ExpressionNode):
    left: ExpressionNode
    operator: str
    right: ExpressionNode


# ---------------------------------------------------------------------------
# Existing ApexForge AST
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class StateNode:
    name: str
    initial: ExpressionNode


@dataclass(frozen=True)
class EventNode:
    name: str


@dataclass(frozen=True)
class AddActionNode:
    state_name: str
    value: ExpressionNode


@dataclass(frozen=True)
class EmitActionNode:
    event_name: str


@dataclass(frozen=True)
class MessageActionNode:
    # Keep the original field name so existing compiler code can still locate it.
    # Its value is now an expression rather than only a raw string.
    expression: ExpressionNode


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
class RequirementNode:
    capability: str


@dataclass(frozen=True)
class DirectiveAuthorityNode:
    name: str


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
class PrincipalAuthorityNode:
    name: str


@dataclass(frozen=True)
class RoleAuthorityNode:
    name: str


@dataclass(frozen=True)
class RoleNode:
    name: str
    authorities: tuple[RoleAuthorityNode, ...]


@dataclass(frozen=True)
class PrincipalRoleNode:
    name: str


@dataclass(frozen=True)
class PrincipalNode:
    name: str
    authorities: tuple[PrincipalAuthorityNode, ...]
    roles: tuple[PrincipalRoleNode, ...]


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------


class Parser:
    def __init__(self, tokens: Sequence[Token]):
        self.tokens = tokens
        self.index = 0

    def current(self) -> Token:
        return self.tokens[self.index]

    def consume(self, expected_kind: str) -> Token:
        token = self.current()

        if token.kind != expected_kind:
            raise SyntaxError(
                f"Expected {expected_kind}, got {token.kind} "
                f"at token index {self.index}"
            )

        self.index += 1
        return token

    def consume_one_of(self, *expected_kinds: str) -> Token:
        token = self.current()

        if token.kind not in expected_kinds:
            expected = ", ".join(expected_kinds)
            raise SyntaxError(
                f"Expected one of ({expected}), got {token.kind} "
                f"at token index {self.index}"
            )

        self.index += 1
        return token

    def match(self, *kinds: str) -> Optional[Token]:
        if self.current().kind not in kinds:
            return None

        token = self.current()
        self.index += 1
        return token

    def parse(self):
        kind = self.current().kind

        if kind == "DIRECTIVE":
            return self.parse_directive()
        if kind == "AUTHORITY":
            return self.parse_authority()
        if kind == "PRINCIPAL":
            return self.parse_principal()
        if kind == "ROLE":
            return self.parse_role()
        if kind == "WORKFLOW":
            return self.parse_workflow()

        raise SyntaxError(f"Unexpected top-level token {kind}")

    # ------------------------------------------------------------------
    # Top-level declarations
    # ------------------------------------------------------------------

    def parse_directive(self) -> DirectiveNode:
        self.consume("DIRECTIVE")
        name = self.consume("IDENT").value
        self.consume("LBRACE")

        states: list[StateNode] = []
        events: list[EventNode] = []
        causes: list[CauseNode] = []
        requirements: list[RequirementNode] = []
        authorities: list[DirectiveAuthorityNode] = []

        while self.current().kind != "RBRACE":
            kind = self.current().kind

            if kind == "STATE":
                states.append(self.parse_state())
                continue

            if kind == "EVENT":
                events.append(self.parse_event())
                continue

            if kind == "CAUSE":
                causes.append(self.parse_cause())
                continue

            if kind == "AUTHORITY":
                self.consume("AUTHORITY")
                authority_name = self.consume("IDENT").value
                authorities.append(DirectiveAuthorityNode(name=authority_name))
                continue

            if kind == "REQUIRES":
                requirements.append(self.parse_requirement())
                continue

            token = self.current()
            raise SyntaxError(
                "Unexpected token inside directive: "
                f"kind={token.kind!r}, value={token.value!r}, "
                f"index={self.index}"
            )

        self.consume("RBRACE")

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
            invocations.append(WorkflowInvokeNode(target=target))

        self.consume("RBRACE")

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

        capabilities: list[CapabilityNode] = []

        while self.current().kind != "RBRACE":
            self.consume("CAPABILITY")
            capability_name = self.consume("IDENT").value
            capabilities.append(CapabilityNode(name=capability_name))

        self.consume("RBRACE")

        return AuthorityNode(
            name=name,
            capabilities=tuple(capabilities),
            extends=extends,
        )

    def parse_role(self) -> RoleNode:
        self.consume("ROLE")
        name = self.consume("IDENT").value
        self.consume("LBRACE")

        authorities: list[RoleAuthorityNode] = []

        while self.current().kind != "RBRACE":
            kind = self.current().kind
            if kind != "AUTHORITY":
                raise SyntaxError(
                    f"Unexpected role token {kind!r}; expected AUTHORITY"
                )

            self.consume("AUTHORITY")
            authority_name = self.consume("IDENT").value
            authorities.append(RoleAuthorityNode(name=authority_name))

        self.consume("RBRACE")

        return RoleNode(
            name=name,
            authorities=tuple(authorities),
        )

    def parse_principal(self) -> PrincipalNode:
        self.consume("PRINCIPAL")
        name = self.consume("IDENT").value
        self.consume("LBRACE")

        authorities: list[PrincipalAuthorityNode] = []
        roles: list[PrincipalRoleNode] = []

        while self.current().kind != "RBRACE":
            kind = self.current().kind

            if kind == "AUTHORITY":
                self.consume("AUTHORITY")
                authority_name = self.consume("IDENT").value
                authorities.append(PrincipalAuthorityNode(name=authority_name))
                continue

            if kind == "ROLE":
                self.consume("ROLE")
                role_name = self.consume("IDENT").value
                roles.append(PrincipalRoleNode(name=role_name))
                continue

            raise SyntaxError(f"Unexpected principal token {kind!r}")

        self.consume("RBRACE")

        return PrincipalNode(
            name=name,
            roles=tuple(roles),
            authorities=tuple(authorities),
        )

    # ------------------------------------------------------------------
    # Directive members and path actions
    # ------------------------------------------------------------------

    def parse_state(self) -> StateNode:
        self.consume("STATE")
        name = self.consume("IDENT").value
        self.consume("EQUAL")
        initial = self.parse_expression()

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

        # Path weights remain plain integers in AFP-P2.1. They can become
        # expressions after AIR/runtime expression evaluation is implemented.
        weight = int(self.consume("NUMBER").value)

        self.consume("LBRACE")
        actions: list[object] = []

        while self.current().kind != "RBRACE":
            kind = self.current().kind

            if kind == "ADD":
                actions.append(self.parse_add())
            elif kind == "EMIT":
                actions.append(self.parse_emit())
            elif kind == "MESSAGE":
                actions.append(self.parse_message())
            elif kind == "INVOKE":
                actions.append(self.parse_invoke())
            else:
                raise SyntaxError(f"Unexpected path token: {kind}")

        self.consume("RBRACE")

        return PathNode(
            name=name,
            weight=weight,
            actions=tuple(actions),
        )

    def parse_add(self) -> AddActionNode:
        self.consume("ADD")
        state_name = self.consume("IDENT").value
        value = self.parse_expression()

        return AddActionNode(
            state_name=state_name,
            value=value,
        )

    def parse_emit(self) -> EmitActionNode:
        self.consume("EMIT")
        event_name = self.consume("IDENT").value
        return EmitActionNode(event_name=event_name)

    def parse_message(self) -> MessageActionNode:
        self.consume("MESSAGE")
        expression = self.parse_expression()
        return MessageActionNode(expression=expression)

    def parse_invoke(self) -> InvokeActionNode:
        self.consume("INVOKE")
        target = self.consume("IDENT").value
        return InvokeActionNode(target=target)

    def parse_requirement(self) -> RequirementNode:
        self.consume("REQUIRES")
        capability = self.consume("IDENT").value
        return RequirementNode(capability=capability)

    # ------------------------------------------------------------------
    # Expression grammar
    #
    # expression  -> or
    # or          -> and ("or" and)*
    # and         -> equality ("and" equality)*
    # equality    -> comparison (("==" | "!=") comparison)*
    # comparison  -> term (("<" | "<=" | ">" | ">=") term)*
    # term        -> factor (("+" | "-") factor)*
    # factor      -> unary (("*" | "/" | "%") unary)*
    # unary       -> ("not" | "-" | "+") unary | primary
    # primary     -> NUMBER | STRING | true | false | IDENT | "(" expression ")"
    # ------------------------------------------------------------------

    def parse_expression(self) -> ExpressionNode:
        return self.parse_or()

    def parse_or(self) -> ExpressionNode:
        expression = self.parse_and()

        while self.current().kind == "OR":
            operator = self.consume("OR")
            right = self.parse_and()
            expression = BinaryExpressionNode(
                left=expression,
                operator=self._operator_text(operator, "or"),
                right=right,
            )

        return expression

    def parse_and(self) -> ExpressionNode:
        expression = self.parse_equality()

        while self.current().kind == "AND":
            operator = self.consume("AND")
            right = self.parse_equality()
            expression = BinaryExpressionNode(
                left=expression,
                operator=self._operator_text(operator, "and"),
                right=right,
            )

        return expression

    def parse_equality(self) -> ExpressionNode:
        expression = self.parse_comparison()

        while self.current().kind in ("EQUAL_EQUAL", "BANG_EQUAL", "EQEQ", "NE"):
            operator = self.consume_one_of(
                "EQUAL_EQUAL",
                "BANG_EQUAL",
                "EQEQ",
                "NE",
            )
            right = self.parse_comparison()
            expression = BinaryExpressionNode(
                left=expression,
                operator=self._operator_text(operator),
                right=right,
            )

        return expression

    def parse_comparison(self) -> ExpressionNode:
        expression = self.parse_term()

        comparison_kinds = (
            "LESS",
            "LESS_EQUAL",
            "GREATER",
            "GREATER_EQUAL",
            "LT",
            "LTE",
            "GT",
            "GTE",
        )

        while self.current().kind in comparison_kinds:
            operator = self.consume_one_of(*comparison_kinds)
            right = self.parse_term()
            expression = BinaryExpressionNode(
                left=expression,
                operator=self._operator_text(operator),
                right=right,
            )

        return expression

    def parse_term(self) -> ExpressionNode:
        expression = self.parse_factor()

        while self.current().kind in ("PLUS", "MINUS"):
            operator = self.consume_one_of("PLUS", "MINUS")
            right = self.parse_factor()
            expression = BinaryExpressionNode(
                left=expression,
                operator=self._operator_text(operator),
                right=right,
            )

        return expression

    def parse_factor(self) -> ExpressionNode:
        expression = self.parse_unary()

        while self.current().kind in ("STAR", "SLASH", "PERCENT"):
            operator = self.consume_one_of("STAR", "SLASH", "PERCENT")
            right = self.parse_unary()
            expression = BinaryExpressionNode(
                left=expression,
                operator=self._operator_text(operator),
                right=right,
            )

        return expression

    def parse_unary(self) -> ExpressionNode:
        if self.current().kind in ("NOT", "MINUS", "PLUS"):
            operator = self.consume_one_of("NOT", "MINUS", "PLUS")
            operand = self.parse_unary()
            return UnaryExpressionNode(
                operator=self._operator_text(operator),
                operand=operand,
            )

        return self.parse_primary()

    def parse_primary(self) -> ExpressionNode:
        token = self.current()

        if token.kind == "NUMBER":
            self.consume("NUMBER")
            return IntegerLiteralNode(value=int(token.value))

        if token.kind == "STRING":
            self.consume("STRING")
            return StringLiteralNode(value=token.value)

        if token.kind == "TRUE":
            self.consume("TRUE")
            return BooleanLiteralNode(value=True)

        if token.kind == "FALSE":
            self.consume("FALSE")
            return BooleanLiteralNode(value=False)

        # This fallback lets expressions recognize true/false even if the
        # lexer still classifies them as ordinary identifiers.
        if token.kind == "IDENT" and str(token.value).lower() in ("true", "false"):
            self.consume("IDENT")
            return BooleanLiteralNode(value=str(token.value).lower() == "true")

        if token.kind == "IDENT":
            self.consume("IDENT")
            return IdentifierNode(name=token.value)

        if token.kind in ("LPAREN", "LPAR"):
            opening = self.consume_one_of("LPAREN", "LPAR")
            expression = self.parse_expression()

            if opening.kind == "LPAREN":
                self.consume("RPAREN")
            else:
                self.consume("RPAR")

            return expression

        raise SyntaxError(
            "Expected expression, got "
            f"kind={token.kind!r}, value={token.value!r}, "
            f"index={self.index}"
        )

    @staticmethod
    def _operator_text(token: Token, fallback: Optional[str] = None) -> str:
        """Return the source operator text, with a safe token-kind fallback."""
        if token.value not in (None, ""):
            return str(token.value)

        if fallback is not None:
            return fallback

        operator_by_kind = {
            "PLUS": "+",
            "MINUS": "-",
            "STAR": "*",
            "SLASH": "/",
            "PERCENT": "%",
            "EQUAL_EQUAL": "==",
            "EQEQ": "==",
            "BANG_EQUAL": "!=",
            "NE": "!=",
            "LESS": "<",
            "LT": "<",
            "LESS_EQUAL": "<=",
            "LTE": "<=",
            "GREATER": ">",
            "GT": ">",
            "GREATER_EQUAL": ">=",
            "GTE": ">=",
            "AND": "and",
            "OR": "or",
            "NOT": "not",
        }

        return operator_by_kind[token.kind]


def parse(source: str):
    parser = Parser(lex(source))
    node = parser.parse()
    parser.consume("EOF")
    return node