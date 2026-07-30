"""ApexForge recursive-descent parser with source-aware AST spans."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Optional, Sequence

from language.diagnostics import BuildDiagnostic
from language.lexer import Token, lex
from language.source import SourceSpan, cover_spans


class ParseError(SyntaxError):
    """Source-aware ApexForge parse failure."""

    def __init__(self, diagnostic: BuildDiagnostic) -> None:
        self.diagnostic = diagnostic
        super().__init__(diagnostic.render())


# ============================================================================
# AST declarations
# ============================================================================


class ExpressionNode:
    """Base class for every parsed expression."""


@dataclass(frozen=True)
class IntegerLiteralNode(ExpressionNode):
    value: int
    span: Optional[SourceSpan] = field(default=None, compare=False)


@dataclass(frozen=True)
class StringLiteralNode(ExpressionNode):
    value: str
    span: Optional[SourceSpan] = field(default=None, compare=False)


@dataclass(frozen=True)
class BooleanLiteralNode(ExpressionNode):
    value: bool
    span: Optional[SourceSpan] = field(default=None, compare=False)


@dataclass(frozen=True)
class IdentifierNode(ExpressionNode):
    name: str
    span: Optional[SourceSpan] = field(default=None, compare=False)


@dataclass(frozen=True)
class UnaryExpressionNode(ExpressionNode):
    operator: str
    operand: ExpressionNode
    span: Optional[SourceSpan] = field(default=None, compare=False)


@dataclass(frozen=True)
class BinaryExpressionNode(ExpressionNode):
    left: ExpressionNode
    operator: str
    right: ExpressionNode
    span: Optional[SourceSpan] = field(default=None, compare=False)


@dataclass(frozen=True)
class CallExpressionNode(ExpressionNode):
    target: str
    arguments: tuple[ExpressionNode, ...]
    span: Optional[SourceSpan] = field(default=None, compare=False)


@dataclass(frozen=True)
class ParameterNode:
    name: str
    span: Optional[SourceSpan] = field(default=None, compare=False)


@dataclass(frozen=True)
class LetNode:
    name: str
    expression: ExpressionNode
    span: Optional[SourceSpan] = field(default=None, compare=False)


@dataclass(frozen=True)
class ReturnNode:
    expression: ExpressionNode
    span: Optional[SourceSpan] = field(default=None, compare=False)


@dataclass(frozen=True)
class FunctionNode:
    name: str
    parameters: tuple[ParameterNode, ...]
    return_statement: ReturnNode
    # Added after the P7.1 fields for positional-constructor compatibility.
    local_bindings: tuple[LetNode, ...] = ()
    span: Optional[SourceSpan] = field(default=None, compare=False)


@dataclass(frozen=True)
class StateNode:
    name: str
    initial: ExpressionNode
    span: Optional[SourceSpan] = field(default=None, compare=False)


@dataclass(frozen=True)
class EventNode:
    name: str
    span: Optional[SourceSpan] = field(default=None, compare=False)


@dataclass(frozen=True)
class AddActionNode:
    state_name: str
    value: ExpressionNode
    span: Optional[SourceSpan] = field(default=None, compare=False)


@dataclass(frozen=True)
class SetActionNode:
    state_name: str
    expression: ExpressionNode
    span: Optional[SourceSpan] = field(default=None, compare=False)


@dataclass(frozen=True)
class EmitActionNode:
    event_name: str
    span: Optional[SourceSpan] = field(default=None, compare=False)


@dataclass(frozen=True)
class MessageActionNode:
    expression: ExpressionNode
    span: Optional[SourceSpan] = field(default=None, compare=False)


@dataclass(frozen=True)
class InvokeActionNode:
    target: str
    span: Optional[SourceSpan] = field(default=None, compare=False)


@dataclass(frozen=True)
class WhenActionNode:
    condition: ExpressionNode
    actions: tuple[object, ...]
    otherwise_actions: tuple[object, ...] = ()
    span: Optional[SourceSpan] = field(default=None, compare=False)


@dataclass(frozen=True)
class PathNode:
    name: str
    weight: int
    actions: tuple[object, ...]
    span: Optional[SourceSpan] = field(default=None, compare=False)


@dataclass(frozen=True)
class CauseNode:
    name: str
    paths: tuple[PathNode, ...]
    span: Optional[SourceSpan] = field(default=None, compare=False)


@dataclass(frozen=True)
class RequirementNode:
    capability: str
    span: Optional[SourceSpan] = field(default=None, compare=False)


@dataclass(frozen=True)
class DirectiveAuthorityNode:
    name: str
    span: Optional[SourceSpan] = field(default=None, compare=False)


@dataclass(frozen=True)
class DirectiveNode:
    name: str
    states: tuple[StateNode, ...]
    events: tuple[EventNode, ...]
    causes: tuple[CauseNode, ...]
    requirements: tuple[RequirementNode, ...] = ()
    authorities: tuple[DirectiveAuthorityNode, ...] = ()
    span: Optional[SourceSpan] = field(default=None, compare=False)


@dataclass(frozen=True)
class WorkflowInvokeNode:
    target: str
    span: Optional[SourceSpan] = field(default=None, compare=False)


@dataclass(frozen=True)
class WorkflowNode:
    name: str
    invocations: tuple[WorkflowInvokeNode, ...]
    span: Optional[SourceSpan] = field(default=None, compare=False)


@dataclass(frozen=True)
class CapabilityNode:
    name: str
    span: Optional[SourceSpan] = field(default=None, compare=False)


@dataclass(frozen=True)
class AuthorityNode:
    name: str
    capabilities: tuple[CapabilityNode, ...]
    extends: Optional[str] = None
    span: Optional[SourceSpan] = field(default=None, compare=False)


@dataclass(frozen=True)
class PrincipalAuthorityNode:
    name: str
    span: Optional[SourceSpan] = field(default=None, compare=False)


@dataclass(frozen=True)
class RoleAuthorityNode:
    name: str
    span: Optional[SourceSpan] = field(default=None, compare=False)


@dataclass(frozen=True)
class RoleNode:
    name: str
    authorities: tuple[RoleAuthorityNode, ...]
    span: Optional[SourceSpan] = field(default=None, compare=False)


@dataclass(frozen=True)
class PrincipalRoleNode:
    name: str
    span: Optional[SourceSpan] = field(default=None, compare=False)


@dataclass(frozen=True)
class PrincipalNode:
    name: str
    authorities: tuple[PrincipalAuthorityNode, ...]
    roles: tuple[PrincipalRoleNode, ...]
    span: Optional[SourceSpan] = field(default=None, compare=False)


# ============================================================================
# Parser
# ============================================================================


def _span_of(value: object) -> Optional[SourceSpan]:
    if isinstance(value, Token):
        return value.span
    return getattr(value, "span", None)


def _cover(first: object, second: object) -> Optional[SourceSpan]:
    return cover_spans(_span_of(first), _span_of(second))


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

    def __init__(
        self,
        tokens: Sequence[Token],
        *,
        source_name: str = "<memory>",
    ) -> None:
        self.tokens = tuple(tokens)
        if not self.tokens:
            raise ValueError("Parser requires at least an EOF token.")
        self.index = 0
        self.source_name = source_name

    def current(self) -> Token:
        return self.tokens[self.index]

    def _raise(
        self,
        *,
        code: str,
        message: str,
        token: Optional[Token] = None,
    ) -> None:
        selected = token or self.current()
        raise ParseError(
            BuildDiagnostic(
                severity="error",
                code=code,
                message=message,
                stage="parse",
                span=selected.span,
            )
        )

    def consume(self, expected_kind: str) -> Token:
        token = self.current()
        if token.kind != expected_kind:
            self._raise(
                code="APX-PARSE-001",
                message=(
                    f"Expected token {expected_kind}, got {token.kind} "
                    f"with value {token.value!r}."
                ),
                token=token,
            )
        self.index += 1
        return token

    def consume_any(self, *expected_kinds: str) -> Token:
        token = self.current()
        if token.kind not in expected_kinds:
            expected = " or ".join(expected_kinds)
            self._raise(
                code="APX-PARSE-001",
                message=(
                    f"Expected token {expected}, got {token.kind} "
                    f"with value {token.value!r}."
                ),
                token=token,
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
        if kind == "FUNCTION":
            return self.parse_function()
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

        self._raise(
            code="APX-PARSE-002",
            message=f"Unexpected top-level token {kind!r}.",
        )
        raise AssertionError("unreachable")

    # ======================================================================
    # Top-level declarations
    # ======================================================================

    def parse_function(self) -> FunctionNode:
        """Parse a pure function with ordered immutable local bindings."""

        start = self.consume("FUNCTION")
        name = self.consume("IDENT")
        self.consume_any(*self._LEFT_PAREN_KINDS)

        parameters: list[ParameterNode] = []
        if self.current().kind not in self._RIGHT_PAREN_KINDS:
            while True:
                parameter = self.consume("IDENT")
                parameters.append(
                    ParameterNode(
                        name=parameter.value,
                        span=parameter.span,
                    )
                )
                if self.match("COMMA") is None:
                    break

        self.consume_any(*self._RIGHT_PAREN_KINDS)
        self.consume("LBRACE")

        local_bindings: list[LetNode] = []

        while self.current().kind == "LET":
            binding_start = self.consume("LET")
            binding_name = self.consume("IDENT")
            self.consume("EQUAL")
            expression = self.parse_expression()
            local_bindings.append(
                LetNode(
                    name=binding_name.value,
                    expression=expression,
                    span=_cover(binding_start, expression),
                )
            )

        if self.current().kind != "RETURN":
            self._raise(
                code="APX-PARSE-006",
                message=(
                    f"Function {name.value!r} must end with a return "
                    "expression after any let bindings."
                ),
            )

        return_start = self.consume("RETURN")
        expression = self.parse_expression()
        return_statement = ReturnNode(
            expression=expression,
            span=_cover(return_start, expression),
        )
        closing = self.consume("RBRACE")

        return FunctionNode(
            name=name.value,
            parameters=tuple(parameters),
            return_statement=return_statement,
            local_bindings=tuple(local_bindings),
            span=_cover(start, closing),
        )

    def parse_directive(self) -> DirectiveNode:
        start = self.consume("DIRECTIVE")
        name = self.consume("IDENT").value
        self.consume("LBRACE")

        states: list[StateNode] = []
        events: list[EventNode] = []
        causes: list[CauseNode] = []
        requirements: list[RequirementNode] = []
        authorities: list[DirectiveAuthorityNode] = []

        while self.current().kind != "RBRACE":
            kind = self.current().kind
            if kind == "EOF":
                self._raise(
                    code="APX-PARSE-003",
                    message=f"Unterminated directive {name!r}; expected RBRACE.",
                )
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
                authority_start = self.consume("AUTHORITY")
                authority_name = self.consume("IDENT")
                authorities.append(
                    DirectiveAuthorityNode(
                        name=authority_name.value,
                        span=_cover(authority_start, authority_name),
                    )
                )
                continue
            if kind == "REQUIRES":
                requirements.append(self.parse_requirement())
                continue

            token = self.current()
            self._raise(
                code="APX-PARSE-003",
                message=(
                    "Unexpected token inside directive: "
                    f"kind={token.kind!r}, value={token.value!r}."
                ),
                token=token,
            )

        closing = self.consume("RBRACE")
        return DirectiveNode(
            name=name,
            states=tuple(states),
            events=tuple(events),
            causes=tuple(causes),
            requirements=tuple(requirements),
            authorities=tuple(authorities),
            span=_cover(start, closing),
        )

    def parse_workflow(self) -> WorkflowNode:
        start = self.consume("WORKFLOW")
        name = self.consume("IDENT").value
        self.consume("LBRACE")
        invocations: list[WorkflowInvokeNode] = []

        while self.current().kind != "RBRACE":
            invoke_start = self.consume("INVOKE")
            target = self.consume("IDENT")
            invocations.append(
                WorkflowInvokeNode(
                    target=target.value,
                    span=_cover(invoke_start, target),
                )
            )

        closing = self.consume("RBRACE")
        return WorkflowNode(
            name=name,
            invocations=tuple(invocations),
            span=_cover(start, closing),
        )

    def parse_authority(self) -> AuthorityNode:
        start = self.consume("AUTHORITY")
        name = self.consume("IDENT").value
        extends: Optional[str] = None

        if self.current().kind == "EXTENDS":
            self.consume("EXTENDS")
            extends = self.consume("IDENT").value

        self.consume("LBRACE")
        capabilities: list[CapabilityNode] = []

        while self.current().kind != "RBRACE":
            capability_start = self.consume("CAPABILITY")
            capability_name = self.consume("IDENT")
            capabilities.append(
                CapabilityNode(
                    name=capability_name.value,
                    span=_cover(capability_start, capability_name),
                )
            )

        closing = self.consume("RBRACE")
        return AuthorityNode(
            name=name,
            capabilities=tuple(capabilities),
            extends=extends,
            span=_cover(start, closing),
        )

    def parse_role(self) -> RoleNode:
        start = self.consume("ROLE")
        name = self.consume("IDENT").value
        self.consume("LBRACE")
        authorities: list[RoleAuthorityNode] = []

        while self.current().kind != "RBRACE":
            authority_start = self.consume("AUTHORITY")
            authority_name = self.consume("IDENT")
            authorities.append(
                RoleAuthorityNode(
                    name=authority_name.value,
                    span=_cover(authority_start, authority_name),
                )
            )

        closing = self.consume("RBRACE")
        return RoleNode(
            name=name,
            authorities=tuple(authorities),
            span=_cover(start, closing),
        )

    def parse_principal(self) -> PrincipalNode:
        start = self.consume("PRINCIPAL")
        name = self.consume("IDENT").value
        self.consume("LBRACE")
        authorities: list[PrincipalAuthorityNode] = []
        roles: list[PrincipalRoleNode] = []

        while self.current().kind != "RBRACE":
            kind = self.current().kind
            if kind == "AUTHORITY":
                item_start = self.consume("AUTHORITY")
                item_name = self.consume("IDENT")
                authorities.append(
                    PrincipalAuthorityNode(
                        name=item_name.value,
                        span=_cover(item_start, item_name),
                    )
                )
                continue
            if kind == "ROLE":
                item_start = self.consume("ROLE")
                item_name = self.consume("IDENT")
                roles.append(
                    PrincipalRoleNode(
                        name=item_name.value,
                        span=_cover(item_start, item_name),
                    )
                )
                continue

            self._raise(
                code="APX-PARSE-003",
                message=f"Unexpected principal token {kind!r}.",
            )

        closing = self.consume("RBRACE")
        return PrincipalNode(
            name=name,
            authorities=tuple(authorities),
            roles=tuple(roles),
            span=_cover(start, closing),
        )

    # ======================================================================
    # Directive contents
    # ======================================================================

    def parse_state(self) -> StateNode:
        start = self.consume("STATE")
        name = self.consume("IDENT").value
        self.consume("EQUAL")
        initial = self.parse_expression()
        return StateNode(name=name, initial=initial, span=_cover(start, initial))

    def parse_event(self) -> EventNode:
        start = self.consume("EVENT")
        name = self.consume("IDENT")
        return EventNode(name=name.value, span=_cover(start, name))

    def parse_requirement(self) -> RequirementNode:
        start = self.consume("REQUIRES")
        capability = self.consume("IDENT")
        return RequirementNode(
            capability=capability.value,
            span=_cover(start, capability),
        )

    def parse_cause(self) -> CauseNode:
        start = self.consume("CAUSE")
        name = self.consume("IDENT").value
        self.consume("LBRACE")
        paths: list[PathNode] = []

        while self.current().kind != "RBRACE":
            if self.current().kind == "EOF":
                self._raise(
                    code="APX-PARSE-003",
                    message=f"Unterminated cause {name!r}; expected RBRACE.",
                )
            paths.append(self.parse_path())

        closing = self.consume("RBRACE")
        return CauseNode(
            name=name,
            paths=tuple(paths),
            span=_cover(start, closing),
        )

    def parse_path(self) -> PathNode:
        start = self.consume("PATH")
        name = self.consume("IDENT").value
        self.consume("AT")
        weight = int(self.consume("NUMBER").value)
        self.consume("LBRACE")
        actions: list[object] = []

        while self.current().kind != "RBRACE":
            if self.current().kind == "EOF":
                self._raise(
                    code="APX-PARSE-003",
                    message=f"Unterminated path {name!r}; expected RBRACE.",
                )
            actions.append(self.parse_action())

        closing = self.consume("RBRACE")
        return PathNode(
            name=name,
            weight=weight,
            actions=tuple(actions),
            span=_cover(start, closing),
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
        self._raise(
            code="APX-PARSE-005",
            message=(
                "Unexpected path action: "
                f"kind={token.kind!r}, value={token.value!r}."
            ),
            token=token,
        )
        raise AssertionError("unreachable")

    def parse_add(self) -> AddActionNode:
        start = self.consume("ADD")
        state_name = self.consume("IDENT").value
        value = self.parse_expression()
        return AddActionNode(
            state_name=state_name,
            value=value,
            span=_cover(start, value),
        )

    def parse_set(self) -> SetActionNode:
        start = self.consume("SET")
        state_name = self.consume("IDENT").value
        self.consume("EQUAL")
        expression = self.parse_expression()
        return SetActionNode(
            state_name=state_name,
            expression=expression,
            span=_cover(start, expression),
        )

    def parse_emit(self) -> EmitActionNode:
        start = self.consume("EMIT")
        event_name = self.consume("IDENT")
        return EmitActionNode(
            event_name=event_name.value,
            span=_cover(start, event_name),
        )

    def parse_message(self) -> MessageActionNode:
        start = self.consume("MESSAGE")
        expression = self.parse_expression()
        return MessageActionNode(
            expression=expression,
            span=_cover(start, expression),
        )

    def parse_invoke(self) -> InvokeActionNode:
        start = self.consume("INVOKE")
        target = self.consume("IDENT")
        return InvokeActionNode(
            target=target.value,
            span=_cover(start, target),
        )

    def parse_when(self) -> WhenActionNode:
        start = self.consume("WHEN")
        condition = self.parse_expression()
        self.consume("LBRACE")
        actions: list[object] = []

        while self.current().kind != "RBRACE":
            actions.append(self.parse_action())

        final_token = self.consume("RBRACE")
        otherwise_actions: list[object] = []

        if self.match("OTHERWISE") is not None:
            self.consume("LBRACE")
            while self.current().kind != "RBRACE":
                otherwise_actions.append(self.parse_action())
            final_token = self.consume("RBRACE")

        return WhenActionNode(
            condition=condition,
            actions=tuple(actions),
            otherwise_actions=tuple(otherwise_actions),
            span=_cover(start, final_token),
        )

    def parse_authority_list(self) -> tuple[str, ...]:
        authorities: list[str] = []
        while self.current().kind != "RBRACE":
            self.consume("AUTHORITY")
            authorities.append(self.consume("IDENT").value)
        return tuple(authorities)

    # ======================================================================
    # Expressions
    # ======================================================================

    def parse_expression(self) -> ExpressionNode:
        return self.parse_or()

    def parse_or(self) -> ExpressionNode:
        expression = self.parse_and()
        while self.current().kind == "OR":
            token = self.consume("OR")
            right = self.parse_and()
            expression = BinaryExpressionNode(
                left=expression,
                operator="or",
                right=right,
                span=_cover(expression, right),
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
                span=_cover(expression, right),
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
                span=_cover(expression, right),
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
                span=_cover(expression, right),
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
                span=_cover(expression, right),
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
                span=_cover(expression, right),
            )
        return expression

    def parse_unary(self) -> ExpressionNode:
        kind = self.current().kind
        if kind in {"NOT", "PLUS", "MINUS"}:
            token = self.current()
            self.index += 1
            operator = {"NOT": "not", "PLUS": "+", "MINUS": "-"}[kind]
            operand = self.parse_unary()
            return UnaryExpressionNode(
                operator=operator,
                operand=operand,
                span=_cover(token, operand),
            )
        return self.parse_primary()

    def parse_primary(self) -> ExpressionNode:
        token = self.current()

        if token.kind == "NUMBER":
            number = self.consume("NUMBER")
            return IntegerLiteralNode(value=int(number.value), span=number.span)

        if token.kind == "STRING":
            string = self.consume("STRING")
            return StringLiteralNode(value=string.value, span=string.span)

        if token.kind == "TRUE":
            boolean = self.consume("TRUE")
            return BooleanLiteralNode(value=True, span=boolean.span)

        if token.kind == "FALSE":
            boolean = self.consume("FALSE")
            return BooleanLiteralNode(value=False, span=boolean.span)

        if token.kind == "IDENT":
            identifier = self.consume("IDENT")
            if identifier.value == "true":
                return BooleanLiteralNode(value=True, span=identifier.span)
            if identifier.value == "false":
                return BooleanLiteralNode(value=False, span=identifier.span)

            if self.current().kind in self._LEFT_PAREN_KINDS:
                self.consume_any(*self._LEFT_PAREN_KINDS)
                arguments: list[ExpressionNode] = []

                if self.current().kind not in self._RIGHT_PAREN_KINDS:
                    while True:
                        arguments.append(self.parse_expression())
                        if self.match("COMMA") is None:
                            break

                closing = self.consume_any(*self._RIGHT_PAREN_KINDS)
                return CallExpressionNode(
                    target=identifier.value,
                    arguments=tuple(arguments),
                    span=_cover(identifier, closing),
                )

            return IdentifierNode(name=identifier.value, span=identifier.span)

        if token.kind in self._LEFT_PAREN_KINDS:
            opening = self.consume_any(*self._LEFT_PAREN_KINDS)
            expression = self.parse_expression()
            closing = self.consume_any(*self._RIGHT_PAREN_KINDS)
            return replace(expression, span=_cover(opening, closing))

        self._raise(
            code="APX-PARSE-004",
            message=(
                "Expected expression, got "
                f"kind={token.kind!r}, value={token.value!r}."
            ),
            token=token,
        )
        raise AssertionError("unreachable")


# ============================================================================
# Public entry point
# ============================================================================


def parse(
    source: str,
    *,
    source_name: str = "<memory>",
) -> object:
    parser = Parser(
        lex(source, source_name=source_name),
        source_name=source_name,
    )
    node = parser.parse()
    parser.consume("EOF")
    return node


__all__ = [
    "ParseError",
    "ExpressionNode",
    "IntegerLiteralNode",
    "StringLiteralNode",
    "BooleanLiteralNode",
    "IdentifierNode",
    "UnaryExpressionNode",
    "BinaryExpressionNode",
    "CallExpressionNode",
    "ParameterNode",
    "LetNode",
    "ReturnNode",
    "FunctionNode",
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