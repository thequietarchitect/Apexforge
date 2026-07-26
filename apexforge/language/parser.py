"""ApexForge language parser.

This parser supports the AFP-P1 declaration model plus AFP-P2 expressions,
explicit ``set`` reassignment, and nested ``when`` action blocks.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence

from language.lexer import Token, lex


# ============================================================================
# AST declarations
# ============================================================================


class ExpressionNode:
    """Base class for every parsed expression."""


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
class SetActionNode:
    state_name: str
    expression: ExpressionNode


@dataclass(frozen=True)
class EmitActionNode:
    event_name: str


@dataclass(frozen=True)
class MessageActionNode:
    expression: ExpressionNode


@dataclass(frozen=True)
class InvokeActionNode:
    target: str


@dataclass(frozen=True)
class WhenActionNode:
    condition: ExpressionNode
    actions: tuple[object, ...]
    otherwise_actions: tuple[object] = ()


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


# ============================================================================
# Parser
# ============================================================================


class Parser:
    """Recursive-descent parser for ApexForge source tokens."""

    _EQUALITY_OPERATORS = {
        "EQEQ": "==",
        "EQUAL_EQUAL": "==",
        "NE": "!=",
        "BANG_EQUAL": "!=",
    }

    _COMPARISON_OPERATORS = {
        "LT": "<",
        "LESS": "<",
        "LTE": "<=",
        "LESS_EQUAL": "<=",
        "GT": ">",
        "GREATER": ">",
        "GTE": ">=",
        "GREATER_EQUAL": ">=",
    }

    _TERM_OPERATORS = {
        "PLUS": "+",
        "MINUS": "-",
    }

    _FACTOR_OPERATORS = {
        "STAR": "*",
        "SLASH": "/",
        "PERCENT": "%",
    }

    _LEFT_PAREN_KINDS = ("LPAREN", "LPAR")
    _RIGHT_PAREN_KINDS = ("RPAREN", "RPAR")

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
                f"at token index {self.index}."
            )

        self.index += 1
        return token

    def consume_any(self, *expected_kinds: str) -> Token:
        token = self.current()

        if token.kind not in expected_kinds:
            expected = " or ".join(expected_kinds)
            raise SyntaxError(
                f"Expected {expected}, got {token.kind} "
                f"at token index {self.index}."
            )

        self.index += 1
        return token

    def match(self, *kinds: str) -> Optional[Token]:
        if self.current().kind not in kinds:
            return None

        token = self.current()
        self.index += 1
        return token

    def parse(self) -> object:
        kind = self.current().kind

        if kind == "DIRECTIVE":
            return self.parse_directive()

        if kind == "WORKFLOW":
            return self.parse_workflow()

        if kind == "AUTHORITY":
            return self.parse_authority()

        if kind == "PRINCIPAL":
            return self.parse_principal()

        if kind == "ROLE":
            return self.parse_role()

        raise SyntaxError(
            f"Unexpected top-level token {kind!r} "
            f"at token index {self.index}."
        )

    # ======================================================================
    # Top-level declarations
    # ======================================================================

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
                authorities.append(
                    DirectiveAuthorityNode(name=authority_name)
                )
                continue

            if kind == "REQUIRES":
                requirements.append(self.parse_requirement())
                continue

            token = self.current()
            raise SyntaxError(
                "Unexpected token inside directive: "
                f"kind={token.kind!r}, "
                f"value={token.value!r}, "
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
            invocations.append(
                WorkflowInvokeNode(target=target)
            )

        self.consume("RBRACE")

        return WorkflowNode(
            name=name,
            invocations=tuple(invocations),
        )

    def parse_authority(self) -> AuthorityNode:
        self.consume("AUTHORITY")
        name = self.consume("IDENT").value

        extends: Optional[str] = None

        if self.current().kind == "EXTENDS":
            self.consume("EXTENDS")
            extends = self.consume("IDENT").value

        self.consume("LBRACE")

        capabilities: list[CapabilityNode] = []

        while self.current().kind != "RBRACE":
            if self.current().kind != "CAPABILITY":
                raise SyntaxError(
                    "Expected CAPABILITY or RBRACE, got "
                    f"{self.current().kind} at token index {self.index}."
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

    def parse_role(self) -> RoleNode:
        self.consume("ROLE")
        name = self.consume("IDENT").value
        self.consume("LBRACE")

        authorities: list[RoleAuthorityNode] = []

        while self.current().kind != "RBRACE":
            kind = self.current().kind

            if kind != "AUTHORITY":
                raise SyntaxError(
                    f"Unexpected role token {kind!r}. "
                    "Expected AUTHORITY."
                )

            self.consume("AUTHORITY")
            authority_name = self.consume("IDENT").value
            authorities.append(
                RoleAuthorityNode(name=authority_name)
            )

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
                authorities.append(
                    PrincipalAuthorityNode(name=authority_name)
                )
                continue

            if kind == "ROLE":
                self.consume("ROLE")
                role_name = self.consume("IDENT").value
                roles.append(
                    PrincipalRoleNode(name=role_name)
                )
                continue

            raise SyntaxError(
                f"Unexpected principal token {kind!r} "
                f"at token index {self.index}."
            )

        self.consume("RBRACE")

        return PrincipalNode(
            name=name,
            authorities=tuple(authorities),
            roles=tuple(roles),
        )

    # ======================================================================
    # Directive contents
    # ======================================================================

    def parse_state(self) -> StateNode:
        self.consume("STATE")
        name = self.consume("IDENT").value
        self.consume("EQUAL")
        initial = self.parse_expression()

        return StateNode(
            name=name,
            initial=initial,
        )

    def parse_event(self) -> EventNode:
        self.consume("EVENT")
        name = self.consume("IDENT").value
        return EventNode(name=name)

    def parse_requirement(self) -> RequirementNode:
        self.consume("REQUIRES")
        capability = self.consume("IDENT").value
        return RequirementNode(capability=capability)

    def parse_cause(self) -> CauseNode:
        self.consume("CAUSE")
        name = self.consume("IDENT").value
        self.consume("LBRACE")

        paths: list[PathNode] = []

        while self.current().kind != "RBRACE":
            paths.append(self.parse_path())

        self.consume("RBRACE")

        return CauseNode(
            name=name,
            paths=tuple(paths),
        )

    def parse_path(self) -> PathNode:
        self.consume("PATH")
        name = self.consume("IDENT").value
        self.consume("AT")
        weight = int(self.consume("NUMBER").value)
        self.consume("LBRACE")

        actions: list[object] = []

        while self.current().kind != "RBRACE":
            actions.append(self.parse_action())

        self.consume("RBRACE")

        return PathNode(
            name=name,
            weight=weight,
            actions=tuple(actions),
        )

    # ======================================================================
    # Ordered path actions
    # ======================================================================

    def parse_action(self) -> object:
        kind = self.current().kind

        if kind == "ADD":
            return self.parse_add()

        if kind == "SET":
            return self.parse_set()

        if kind == "EMIT":
            return self.parse_emit()

        if kind == "MESSAGE":
            return self.parse_message()

        if kind == "INVOKE":
            return self.parse_invoke()

        if kind == "WHEN":
            return self.parse_when()

        token = self.current()
        raise SyntaxError(
            "Unexpected path action: "
            f"kind={token.kind!r}, "
            f"value={token.value!r}, "
            f"index={self.index}"
        )

    def parse_add(self) -> AddActionNode:
        self.consume("ADD")
        state_name = self.consume("IDENT").value
        value = self.parse_expression()

        return AddActionNode(
            state_name=state_name,
            value=value,
        )

    def parse_set(self) -> SetActionNode:
        self.consume("SET")
        state_name = self.consume("IDENT").value
        self.consume("EQUAL")
        expression = self.parse_expression()

        return SetActionNode(
            state_name=state_name,
            expression=expression,
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

    def parse_when(
        self,
        ) -> WhenActionNode:
        self.consume("WHEN")

        condition = self.parse_expression()

        self.consume("LBRACE")

        actions: list[object] = []

        while self.current().kind != "RBRACE":
            actions.append(
                self.parse_action()
            )

        self.consume("RBRACE")

        otherwise_actions: list[object] = []

        if self.match("OTHERWISE") is not None:
            self.consume("LBRACE")

            while self.current().kind != "RBRACE":
                otherwise_actions.append(
                    self.parse_action()
                )

            self.consume("RBRACE")

        return WhenActionNode(
            condition=condition,
            actions=tuple(actions),
            otherwise_actions=tuple(
                otherwise_actions
            ),
        )

    def parse_authority_list(self) -> tuple[str, ...]:
        authorities: list[str] = []

        while self.current().kind != "RBRACE":
            self.consume("AUTHORITY")
            authorities.append(
                self.consume("IDENT").value
            )

        return tuple(authorities)

    # ======================================================================
    # Expressions
    # ======================================================================

    def parse_expression(self) -> ExpressionNode:
        result = self.parse_or()
        return result

    def parse_or(self) -> ExpressionNode:
        expression = self.parse_and()

        while self.current().kind == "OR":
            self.consume("OR")
            right = self.parse_and()
            expression = BinaryExpressionNode(
                left=expression,
                operator="or",
                right=right,
            )

        return expression

    def parse_and(self) -> ExpressionNode:
        expression = self.parse_equality()

        while self.current().kind == "AND":
            self.consume("AND")
            right = self.parse_equality()
            expression = BinaryExpressionNode(
                left=expression,
                operator="and",
                right=right,
            )

        return expression

    def parse_equality(self) -> ExpressionNode:
        expression = self.parse_comparison()

        while self.current().kind in self._EQUALITY_OPERATORS:
            token = self.current()
            self.index += 1
            right = self.parse_comparison()
            expression = BinaryExpressionNode(
                left=expression,
                operator=self._EQUALITY_OPERATORS[token.kind],
                right=right,
            )

        return expression

    def parse_comparison(self) -> ExpressionNode:
        expression = self.parse_term()

        while self.current().kind in self._COMPARISON_OPERATORS:
            token = self.current()
            self.index += 1
            right = self.parse_term()
            expression = BinaryExpressionNode(
                left=expression,
                operator=self._COMPARISON_OPERATORS[token.kind],
                right=right,
            )

        return expression

    def parse_term(self) -> ExpressionNode:
        expression = self.parse_factor()

        while self.current().kind in self._TERM_OPERATORS:
            token = self.current()
            self.index += 1
            right = self.parse_factor()
            expression = BinaryExpressionNode(
                left=expression,
                operator=self._TERM_OPERATORS[token.kind],
                right=right,
            )

        return expression

    def parse_factor(self) -> ExpressionNode:
        expression = self.parse_unary()

        while self.current().kind in self._FACTOR_OPERATORS:
            token = self.current()
            self.index += 1
            right = self.parse_unary()
            expression = BinaryExpressionNode(
                left=expression,
                operator=self._FACTOR_OPERATORS[token.kind],
                right=right,
            )

        return expression

    def parse_unary(self) -> ExpressionNode:
        kind = self.current().kind

        if kind == "NOT":
            self.consume("NOT")
            return UnaryExpressionNode(
                operator="not",
                operand=self.parse_unary(),
            )

        if kind == "PLUS":
            self.consume("PLUS")
            return UnaryExpressionNode(
                operator="+",
                operand=self.parse_unary(),
            )

        if kind == "MINUS":
            self.consume("MINUS")
            return UnaryExpressionNode(
                operator="-",
                operand=self.parse_unary(),
            )

        return self.parse_primary()

    def parse_primary(self) -> ExpressionNode:
        token = self.current()

        if token.kind == "NUMBER":
            number = self.consume("NUMBER")
            return IntegerLiteralNode(
                value=int(number.value),
            )

        if token.kind == "STRING":
            string = self.consume("STRING")
            return StringLiteralNode(
                value=string.value,
            )

        if token.kind == "TRUE":
            self.consume("TRUE")
            return BooleanLiteralNode(value=True)

        if token.kind == "FALSE":
            self.consume("FALSE")
            return BooleanLiteralNode(value=False)

        if token.kind == "IDENT":
            identifier = self.consume("IDENT")

            # Compatibility with lexers that still emit booleans as IDENT.
            if identifier.value == "true":
                return BooleanLiteralNode(value=True)

            if identifier.value == "false":
                return BooleanLiteralNode(value=False)

            return IdentifierNode(
                name=identifier.value,
            )

        if token.kind in self._LEFT_PAREN_KINDS:
            self.consume_any(*self._LEFT_PAREN_KINDS)
            expression = self.parse_expression()
            self.consume_any(*self._RIGHT_PAREN_KINDS)
            return expression

        raise SyntaxError(
            "Expected expression, got "
            f"kind={token.kind!r}, "
            f"value={token.value!r}, "
            f"index={self.index}"
        )


# ============================================================================
# Public entry point
# ============================================================================


def parse(source: str) -> object:
    parser = Parser(lex(source))
    node = parser.parse()
    parser.consume("EOF")
    return node


__all__ = [
    "ExpressionNode",
    "IntegerLiteralNode",
    "StringLiteralNode",
    "BooleanLiteralNode",
    "IdentifierNode",
    "UnaryExpressionNode",
    "BinaryExpressionNode",
    "StateNode",
    "EventNode",
    "AddActionNode",
    "SetActionNode",
    "EmitActionNode",
    "MessageActionNode",
    "InvokeActionNode",
    "WhenActionNode",
    "PathNode",
    "CauseNode",
    "RequirementNode",
    "DirectiveAuthorityNode",
    "DirectiveNode",
    "WorkflowInvokeNode",
    "WorkflowNode",
    "CapabilityNode",
    "AuthorityNode",
    "PrincipalAuthorityNode",
    "RoleAuthorityNode",
    "RoleNode",
    "PrincipalRoleNode",
    "PrincipalNode",
    "Parser",
    "parse",
]