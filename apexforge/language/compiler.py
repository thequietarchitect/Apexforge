"""ApexForge AST-to-AIR compiler with sidecar source maps."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional

from role_compiler import compile_role
from air.model import (
    AIRDirective,
    AIRProgram,
    AIRRole,
    EventDefinition,
    EventEmission,
    StateAssignment,
    StateDefinition,
    DirectiveRequirement,
    DirectiveAuthority,
    AIRWhenAction,
    facts,
)
from air.types import AIR_VERSION
from authority.model import AuthorityCheck, Principal
from causality.model import CausalDecision, CausalPath, DirectiveInvocation
from language.diagnostics import BuildDiagnostic
from language.parser import (
    AddActionNode,
    DirectiveNode,
    EmitActionNode,
    InvokeActionNode,
    MessageActionNode,
    RequirementNode,
    WhenActionNode,
    ExpressionNode,
    IntegerLiteralNode,
    FloatLiteralNode,
    StringLiteralNode,
    BooleanLiteralNode,
    IdentifierNode,
    UnaryExpressionNode,
    BinaryExpressionNode,
    CallExpressionNode,
    FunctionNode,
    TypeParameterNode,
    FunctionWhenNode,
    LetNode,
    ReturnNode,
    RoleNode,
    SetActionNode,
    parse,
)
from air.expressions import (
    AIRExpression,
    AIRIntegerLiteral,
    AIRFloatLiteral,
    AIRStringLiteral,
    AIRBooleanLiteral,
    AIRIdentifierReference,
    AIRUnaryExpression,
    AIRBinaryExpression,
    AIRCallExpression,
)
from air.functions import (
    AIRFunction,
    AIRFunctionReturn,
    AIRFunctionWhen,
    AIRLocalBinding,
    AIRParameter,
)
from language.source import SourceSpan
from type_system.inference import (
    FunctionSignature,
    TypeInferenceError,
    infer_expression_type,
)
from type_system.generics import TypeIdentity, resolve_type
from type_system.model import (
    ApexType,
    BOOL,
    FLOAT,
    INT,
    STRING,
    resolve_builtin_type,
)
from standard_library.core import DEFAULT_STANDARD_LIBRARY


class CompilerError(ValueError):
    """Source-aware ApexForge compilation failure."""

    def __init__(self, diagnostic: BuildDiagnostic) -> None:
        self.diagnostic = diagnostic
        super().__init__(diagnostic.render())


@dataclass(frozen=True)
class SourceMapEntry:
    """One relationship between a sidecar compiler ID and source text."""

    air_id: str
    span: SourceSpan
    kind: str = ""
    reference: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.air_id, str) or not self.air_id.strip():
            raise ValueError("SourceMapEntry.air_id must be a non-empty string.")
        if not isinstance(self.span, SourceSpan):
            raise TypeError("SourceMapEntry.span must be SourceSpan.")
        object.__setattr__(self, "air_id", self.air_id.strip())


@dataclass(frozen=True)
class SourceMap:
    entries: tuple[SourceMapEntry, ...] = ()

    def __post_init__(self) -> None:
        normalized = tuple(self.entries)
        if any(not isinstance(entry, SourceMapEntry) for entry in normalized):
            raise TypeError("SourceMap entries must be SourceMapEntry values.")

        object.__setattr__(
            self,
            "entries",
            tuple(
                sorted(
                    normalized,
                    key=lambda entry: (
                        entry.span.source_name.casefold(),
                        entry.span.source_name,
                        entry.span.start.offset,
                        entry.span.end.offset,
                        entry.kind,
                        entry.air_id,
                        entry.reference,
                    ),
                )
            ),
        )

    @classmethod
    def merge(cls, *maps: "SourceMap") -> "SourceMap":
        return cls(
            tuple(
                entry
                for source_map in maps
                for entry in tuple(source_map.entries)
            )
        )

    def find(
        self,
        *,
        air_id: Optional[str] = None,
        kind: Optional[str] = None,
        reference: Optional[str] = None,
    ) -> tuple[SourceMapEntry, ...]:
        return tuple(
            entry
            for entry in self.entries
            if (air_id is None or entry.air_id == air_id)
            and (kind is None or entry.kind == kind)
            and (reference is None or entry.reference == reference)
        )

    def first_span(
        self,
        *,
        air_id: Optional[str] = None,
        kind: Optional[str] = None,
        reference: Optional[str] = None,
    ) -> Optional[SourceSpan]:
        matches = self.find(air_id=air_id, kind=kind, reference=reference)
        return matches[0].span if matches else None


@dataclass(frozen=True)
class CompiledSource:
    program: Any
    source_map: SourceMap


@dataclass
class _CompileContext:
    source_entries: list[SourceMapEntry]
    scope: str
    invocation_index: int = 0
    action_index: int = 0

    def child(self, suffix: str) -> "_CompileContext":
        return _CompileContext(
            source_entries=self.source_entries,
            scope=f"{self.scope}:{suffix}" if self.scope else suffix,
            invocation_index=self.invocation_index,
            action_index=self.action_index,
        )

    def next_action_id(self, kind: str) -> str:
        identifier = f"{kind}:{self.scope}:{self.action_index}"
        self.action_index += 1
        return identifier

    def next_invocation_id(self) -> str:
        identifier = f"invoke:{self.scope}:{self.invocation_index}"
        self.invocation_index += 1
        return identifier


def _append_source_entry(
    entries: list[SourceMapEntry],
    *,
    air_id: str,
    node: object,
    kind: str,
    reference: str = "",
) -> None:
    span = getattr(node, "span", None)
    if isinstance(span, SourceSpan):
        entries.append(
            SourceMapEntry(
                air_id=air_id,
                span=span,
                kind=kind,
                reference=reference,
            )
        )


def _compile_error(
    *,
    code: str,
    message: str,
    node: object,
    air_id: str = "",
) -> CompilerError:
    return CompilerError(
        BuildDiagnostic(
            severity="error",
            code=code,
            message=message,
            stage="compile",
            span=getattr(node, "span", None),
            air_id=air_id,
        )
    )


def _compile_type_annotation(
    annotation: object,
    *,
    owner: str,
    node: object,
    default: Optional[TypeIdentity] = None,
) -> Optional[TypeIdentity]:
    """Normalize one optional AST type annotation for AIR storage."""

    if annotation is None:
        return default

    apex_type = getattr(annotation, "apex_type", None)

    try:
        return resolve_type(apex_type)
    except (TypeError, ValueError) as exc:
        raise _compile_error(
            code="APX-COMPILE-014",
            message=(
                f"{owner} contains an invalid ApexForge type annotation."
            ),
            node=node,
        ) from exc



def _normalize_function_signatures(
    function_signatures: Optional[Mapping[str, FunctionSignature]],
) -> dict[str, FunctionSignature]:
    """Merge external signatures with the canonical standard library."""

    return DEFAULT_STANDARD_LIBRARY.merge_external_signatures(
        function_signatures
    )


def _expression_identifiers(
    node: ExpressionNode,
) -> tuple[str, ...]:
    """Return source-order identifier references from one expression."""

    if isinstance(node, IdentifierNode):
        return (node.name,)

    if isinstance(node, UnaryExpressionNode):
        return _expression_identifiers(node.operand)

    if isinstance(node, BinaryExpressionNode):
        return (
            _expression_identifiers(node.left)
            + _expression_identifiers(node.right)
        )

    if isinstance(node, CallExpressionNode):
        return tuple(
            name
            for argument in node.arguments
            for name in _expression_identifiers(argument)
        )

    return ()


def _expression_call_targets(
    node: ExpressionNode,
) -> tuple[str, ...]:
    """Return source-order function-call targets from one expression."""

    if isinstance(node, UnaryExpressionNode):
        return _expression_call_targets(node.operand)

    if isinstance(node, BinaryExpressionNode):
        return (
            _expression_call_targets(node.left)
            + _expression_call_targets(node.right)
        )

    if isinstance(node, CallExpressionNode):
        return (node.target,) + tuple(
            target
            for argument in node.arguments
            for target in _expression_call_targets(argument)
        )

    return ()


def _infer_source_expression_type(
    node: ExpressionNode,
    *,
    identifiers: Mapping[str, Optional[TypeIdentity]],
    functions: Mapping[str, FunctionSignature],
    deferred_identifiers: frozenset[str] = frozenset(),
) -> Optional[TypeIdentity]:
    """Infer one source expression or defer it to linked-program checking.

    A call is deferred when its external signature is absent or incomplete.
    Expressions depending on a deferred local are deferred as well. All other
    type failures become source-aware ``CompilerError`` diagnostics.
    """

    for target in _expression_call_targets(node):
        signature = functions.get(target)
        if (
            signature is None
            or signature.return_type is None
            or any(
                parameter_type is None
                for parameter_type in signature.parameter_types
            )
        ):
            return None

    for name in _expression_identifiers(node):
        if name not in identifiers:
            continue
        if identifiers[name] is not None:
            continue
        if name in deferred_identifiers:
            return None

        raise _compile_error(
            code="APX-TYPE-002",
            message=(
                f"Identifier {name!r} has no declared or inferred type."
            ),
            node=node,
        )

    try:
        return infer_expression_type(
            compile_expression(node),
            identifiers=identifiers,
            functions=functions,
        )
    except TypeInferenceError as error:
        raise _compile_error(
            code=error.code,
            message=error.message,
            node=node,
        ) from error


def _require_source_expression_type(
    node: ExpressionNode,
    *,
    expected: TypeIdentity,
    owner: str,
    identifiers: Mapping[str, Optional[TypeIdentity]],
    functions: Mapping[str, FunctionSignature],
    deferred_identifiers: frozenset[str] = frozenset(),
) -> Optional[TypeIdentity]:
    actual = _infer_source_expression_type(
        node,
        identifiers=identifiers,
        functions=functions,
        deferred_identifiers=deferred_identifiers,
    )

    if actual is None:
        return None

    if actual is not expected:
        raise _compile_error(
            code="APX-TYPE-011",
            message=(
                f"{owner} requires {expected}; received {actual}."
            ),
            node=node,
        )

    return actual


def _directive_state_types(
    node: DirectiveNode,
) -> dict[str, ApexType]:
    state_types: dict[str, ApexType] = {}

    for state in node.states:
        value_type = _compile_type_annotation(
            getattr(state, "type_annotation", None),
            owner=f"State {state.name!r}",
            node=state,
            default=INT,
        )

        if value_type is None:
            raise AssertionError(
                "state type normalization returned None"
            )

        state_types[state.name] = value_type

    return state_types


def _type_check_directive_states(
    node: DirectiveNode,
    *,
    functions: Mapping[str, FunctionSignature],
) -> dict[str, ApexType]:
    """Validate state initializers and return the canonical state environment."""

    state_types = _directive_state_types(node)

    for state in node.states:
        expected = state_types[state.name]

        _require_source_expression_type(
            state.initial,
            expected=expected,
            owner=f"State {state.name!r} initializer",
            identifiers=state_types,
            functions=functions,
        )

    return state_types


def _type_check_directive_actions(
    actions: tuple[object, ...],
    *,
    state_types: Mapping[str, ApexType],
    functions: Mapping[str, FunctionSignature],
) -> None:
    """Validate typed directive mutation and condition expressions."""

    for action in tuple(actions):
        if isinstance(action, AddActionNode):
            expected = state_types.get(
                action.state_name
            )

            if expected is None:
                continue

            if expected not in {
                INT,
                FLOAT,
            }:
                raise _compile_error(
                    code="APX-TYPE-013",
                    message=(
                        f"State {action.state_name!r} has type {expected}; "
                        "add requires int or float."
                    ),
                    node=action,
                )

            _require_source_expression_type(
                action.value,
                expected=expected,
                owner=(
                    f"Add action for state "
                    f"{action.state_name!r}"
                ),
                identifiers=state_types,
                functions=functions,
            )
            continue

        if isinstance(action, SetActionNode):
            expected = state_types.get(
                action.state_name
            )

            if expected is None:
                continue

            _require_source_expression_type(
                action.expression,
                expected=expected,
                owner=(
                    f"Set action for state "
                    f"{action.state_name!r}"
                ),
                identifiers=state_types,
                functions=functions,
            )
            continue

        if isinstance(action, MessageActionNode):
            # Message payloads remain expression-valued. Infer known payloads so
            # invalid operators are rejected, but do not require string yet.
            _infer_source_expression_type(
                action.expression,
                identifiers=state_types,
                functions=functions,
            )
            continue

        if isinstance(action, WhenActionNode):
            condition_type = _infer_source_expression_type(
                action.condition,
                identifiers=state_types,
                functions=functions,
            )

            if (
                condition_type is not None
                and condition_type is not BOOL
            ):
                raise _compile_error(
                    code="APX-TYPE-012",
                    message=(
                        "Directive when condition requires bool; "
                        f"received {condition_type}."
                    ),
                    node=action.condition,
                )

            _type_check_directive_actions(
                tuple(action.actions),
                state_types=state_types,
                functions=functions,
            )
            _type_check_directive_actions(
                tuple(
                    getattr(
                        action,
                        "otherwise_actions",
                        (),
                    ) or ()
                ),
                state_types=state_types,
                functions=functions,
            )


def _type_check_function_statements(
    statements: tuple[object, ...],
    *,
    function_name: str,
    identifiers: Mapping[str, Optional[TypeIdentity]],
    deferred_identifiers: frozenset[str],
    expected_return: Optional[TypeIdentity],
    functions: Mapping[str, FunctionSignature],
) -> None:
    """Type-check one lexical pure-function statement stream."""

    scope = dict(identifiers)
    deferred = set(deferred_identifiers)

    for statement in statements:
        if isinstance(statement, LetNode):
            inferred = _infer_source_expression_type(
                statement.expression,
                identifiers=scope,
                functions=functions,
                deferred_identifiers=frozenset(deferred),
            )
            scope[statement.name] = inferred
            if inferred is None:
                deferred.add(statement.name)
            else:
                deferred.discard(statement.name)
            continue

        if isinstance(statement, ReturnNode):
            if expected_return is None:
                _infer_source_expression_type(
                    statement.expression,
                    identifiers=scope,
                    functions=functions,
                    deferred_identifiers=frozenset(deferred),
                )
            else:
                _require_source_expression_type(
                    statement.expression,
                    expected=expected_return,
                    owner=f"Function {function_name!r} return",
                    identifiers=scope,
                    functions=functions,
                    deferred_identifiers=frozenset(deferred),
                )
            continue

        if isinstance(statement, FunctionWhenNode):
            condition_type = _infer_source_expression_type(
                statement.condition,
                identifiers=scope,
                functions=functions,
                deferred_identifiers=frozenset(deferred),
            )

            if condition_type is not None and condition_type is not BOOL:
                raise _compile_error(
                    code="APX-TYPE-012",
                    message=(
                        f"Function {function_name!r} when condition requires "
                        f"bool; received {condition_type}."
                    ),
                    node=statement.condition,
                )

            _type_check_function_statements(
                tuple(statement.actions),
                function_name=function_name,
                identifiers=dict(scope),
                deferred_identifiers=frozenset(deferred),
                expected_return=expected_return,
                functions=functions,
            )
            _type_check_function_statements(
                tuple(getattr(statement, "otherwise_actions", ()) or ()),
                function_name=function_name,
                identifiers=dict(scope),
                deferred_identifiers=frozenset(deferred),
                expected_return=expected_return,
                functions=functions,
            )


def _type_check_function(
    node: FunctionNode,
    *,
    body_nodes: tuple[object, ...],
    functions: Mapping[str, FunctionSignature],
) -> None:
    """Type-check annotated source while preserving fully legacy P7 source."""

    parameter_types = {
        parameter.name: _compile_type_annotation(
            getattr(parameter, "type_annotation", None),
            owner=(
                f"Parameter {parameter.name!r} "
                f"of function {node.name!r}"
            ),
            node=parameter,
        )
        for parameter in node.parameters
    }
    return_type = _compile_type_annotation(
        getattr(node, "return_type", None),
        owner=f"Function {node.name!r} return",
        node=node,
    )

    typed_mode = (
        return_type is not None
        or any(
            parameter_type is not None
            for parameter_type in parameter_types.values()
        )
    )
    if not typed_mode:
        return

    available_functions = dict(functions)
    if (
        return_type is not None
        and all(
            parameter_type is not None
            for parameter_type in parameter_types.values()
        )
    ):
        available_functions.setdefault(
            node.name,
            FunctionSignature(
                name=node.name,
                parameter_types=tuple(
                    parameter_types[parameter.name]
                    for parameter in node.parameters
                ),
                return_type=return_type,
                type_parameters=tuple(
                    parameter.apex_type
                    for parameter in getattr(
                        node,
                        "type_parameters",
                        (),
                    )
                ),
            ),
        )

    _type_check_function_statements(
        body_nodes,
        function_name=node.name,
        identifiers=parameter_types,
        deferred_identifiers=frozenset(),
        expected_return=return_type,
        functions=available_functions,
    )


def compile_expression(node: ExpressionNode) -> AIRExpression:
    if isinstance(node, IntegerLiteralNode):
        return AIRIntegerLiteral(value=node.value)
    if isinstance(node, FloatLiteralNode):
        return AIRFloatLiteral(value=node.value)
    if isinstance(node, StringLiteralNode):
        return AIRStringLiteral(value=node.value)
    if isinstance(node, BooleanLiteralNode):
        return AIRBooleanLiteral(value=node.value)
    if isinstance(node, IdentifierNode):
        return AIRIdentifierReference(name=node.name)
    if isinstance(node, UnaryExpressionNode):
        return AIRUnaryExpression(
            operator=node.operator,
            operand=compile_expression(node.operand),
        )
    if isinstance(node, BinaryExpressionNode):
        return AIRBinaryExpression(
            left=compile_expression(node.left),
            operator=node.operator,
            right=compile_expression(node.right),
        )
    if isinstance(node, CallExpressionNode):
        return AIRCallExpression(
            target=node.target,
            arguments=tuple(
                compile_expression(argument)
                for argument in node.arguments
            ),
            type_arguments=tuple(
                annotation.apex_type
                for annotation in tuple(
                    getattr(node, "type_arguments", ()) or ()
                )
            ),
        )

    raise _compile_error(
        code="APX-COMPILE-001",
        message=f"Unsupported expression AST node {type(node).__name__}.",
        node=node,
    )


def _record_expression_function_calls(
    node: ExpressionNode,
    entries: list[SourceMapEntry],
    *,
    scope: str,
    counter: list[int],
) -> None:
    """Record every source-level function call without changing AIR.

    AFP-P7.3 uses these sidecar entries for module visibility and linked
    validation diagnostics. The traversal is deterministic and follows source
    expression structure.
    """

    if isinstance(node, CallExpressionNode):
        call_index = counter[0]
        counter[0] += 1
        _append_source_entry(
            entries,
            air_id=f"function_call:{scope}:{call_index}",
            node=node,
            kind="function_call",
            reference=node.target,
        )
        for argument_index, argument in enumerate(node.arguments):
            _record_expression_function_calls(
                argument,
                entries,
                scope=f"{scope}:argument:{argument_index}",
                counter=counter,
            )
        return

    if isinstance(node, UnaryExpressionNode):
        _record_expression_function_calls(
            node.operand,
            entries,
            scope=f"{scope}:operand",
            counter=counter,
        )
        return

    if isinstance(node, BinaryExpressionNode):
        _record_expression_function_calls(
            node.left,
            entries,
            scope=f"{scope}:left",
            counter=counter,
        )
        _record_expression_function_calls(
            node.right,
            entries,
            scope=f"{scope}:right",
            counter=counter,
        )


def _record_function_statement_calls(
    statements: tuple[object, ...],
    entries: list[SourceMapEntry],
    *,
    scope: str,
    counter: list[int],
) -> None:
    for statement_index, statement in enumerate(tuple(statements)):
        statement_scope = f"{scope}:statement:{statement_index}"

        if isinstance(statement, LetNode):
            _record_expression_function_calls(
                statement.expression,
                entries,
                scope=f"{statement_scope}:local:{statement.name}",
                counter=counter,
            )
            continue

        if isinstance(statement, ReturnNode):
            _record_expression_function_calls(
                statement.expression,
                entries,
                scope=f"{statement_scope}:return",
                counter=counter,
            )
            continue

        if isinstance(statement, FunctionWhenNode):
            _record_expression_function_calls(
                statement.condition,
                entries,
                scope=f"{statement_scope}:condition",
                counter=counter,
            )
            _record_function_statement_calls(
                tuple(statement.actions),
                entries,
                scope=f"{statement_scope}:when",
                counter=counter,
            )
            _record_function_statement_calls(
                tuple(getattr(statement, "otherwise_actions", ()) or ()),
                entries,
                scope=f"{statement_scope}:otherwise",
                counter=counter,
            )


def _record_action_function_calls(
    actions: tuple[object, ...],
    entries: list[SourceMapEntry],
    *,
    scope: str,
    counter: list[int],
) -> None:
    for action_index, action in enumerate(tuple(actions)):
        action_scope = f"{scope}:action:{action_index}"

        if isinstance(action, AddActionNode):
            _record_expression_function_calls(
                action.value,
                entries,
                scope=f"{action_scope}:add",
                counter=counter,
            )
            continue

        if isinstance(action, SetActionNode):
            _record_expression_function_calls(
                action.expression,
                entries,
                scope=f"{action_scope}:set",
                counter=counter,
            )
            continue

        if isinstance(action, MessageActionNode):
            _record_expression_function_calls(
                action.expression,
                entries,
                scope=f"{action_scope}:message",
                counter=counter,
            )
            continue

        if isinstance(action, WhenActionNode):
            _record_expression_function_calls(
                action.condition,
                entries,
                scope=f"{action_scope}:condition",
                counter=counter,
            )
            _record_action_function_calls(
                tuple(action.actions),
                entries,
                scope=f"{action_scope}:when",
                counter=counter,
            )
            _record_action_function_calls(
                tuple(getattr(action, "otherwise_actions", ()) or ()),
                entries,
                scope=f"{action_scope}:otherwise",
                counter=counter,
            )


def _record_directive_function_calls(
    node: DirectiveNode,
    entries: list[SourceMapEntry],
) -> None:
    counter = [0]

    for state_index, state in enumerate(node.states):
        _record_expression_function_calls(
            state.initial,
            entries,
            scope=f"{node.name}:state:{state_index}:{state.name}",
            counter=counter,
        )

    for cause_index, cause in enumerate(node.causes):
        for path_index, path in enumerate(cause.paths):
            _record_action_function_calls(
                tuple(path.actions),
                entries,
                scope=(
                    f"{node.name}:cause:{cause_index}:{cause.name}:"
                    f"path:{path_index}:{path.name}"
                ),
                counter=counter,
            )


def _record_function_calls(
    node: FunctionNode,
    entries: list[SourceMapEntry],
) -> None:
    body = tuple(getattr(node, "body", ()) or ())
    if not body:
        body = tuple(getattr(node, "local_bindings", ()) or ()) + (
            node.return_statement,
        )

    _record_function_statement_calls(
        body,
        entries,
        scope=node.name,
        counter=[0],
    )


def _local_reference(
    mapping: dict[str, str],
    name: str,
    *,
    owner: str,
    node: object,
) -> str:
    try:
        return mapping[name]
    except KeyError as exc:
        raise _compile_error(
            code="APX-COMPILE-002",
            message=f"Undefined local {owner} {name!r}.",
            node=node,
        ) from exc


def compile_actions(
    actions: tuple[object, ...],
    state_ids: dict[str, str],
    event_ids: dict[str, str],
    *,
    source_entries: Optional[list[SourceMapEntry]] = None,
    scope: str = "action",
    context: Optional[_CompileContext] = None,
    state_types: Optional[Mapping[str, ApexType]] = None,
) -> tuple[object, ...]:
    """Compile one ordered parser-action stream recursively.

    The original three positional parameters remain supported for AFP-P1/P2
    compatibility. Source provenance is collected only when an entry list or
    compile context is supplied.
    """

    if context is not None:
        entries = context.source_entries
    else:
        entries = source_entries if source_entries is not None else []
        context = _CompileContext(entries, scope)

    active_state_types = dict(
        state_types or {}
    )

    compiled_actions: list[object] = []
    pending_message: Optional[MessageActionNode] = None
    pending_expression: Optional[AIRExpression] = None

    for action in actions:
        if isinstance(action, MessageActionNode):
            if pending_message is not None:
                raise _compile_error(
                    code="APX-COMPILE-003",
                    message=(
                        "A message action must be followed by an emit before "
                        "another message."
                    ),
                    node=action,
                )

            pending_message = action
            pending_expression = compile_expression(action.expression)
            continue

        if isinstance(action, EmitActionNode):
            event_id = _local_reference(
                event_ids,
                action.event_name,
                owner="event",
                node=action,
            )
            event_facts = ()
            if pending_expression is not None:
                event_facts = facts(message=pending_expression)

            compiled_actions.append(
                EventEmission(event=event_id, facts=event_facts)
            )
            action_id = context.next_action_id("emit")
            _append_source_entry(
                entries,
                air_id=action_id,
                node=action,
                kind="event_emission",
                reference=event_id,
            )
            pending_message = None
            pending_expression = None
            continue

        if pending_message is not None:
            raise _compile_error(
                code="APX-COMPILE-004",
                message="A message action must be immediately followed by emit.",
                node=pending_message,
            )

        if isinstance(action, AddActionNode):
            state_id = _local_reference(
                state_ids,
                action.state_name,
                owner="state",
                node=action,
            )
            state_type = active_state_types.get(
                action.state_name,
                INT,
            )
            operation = {
                INT: "add_int",
                FLOAT: "add_float",
            }.get(state_type)

            if operation is None:
                raise _compile_error(
                    code="APX-TYPE-013",
                    message=(
                        f"State {action.state_name!r} has type {state_type}; "
                        "add requires int or float."
                    ),
                    node=action,
                )

            compiled_actions.append(
                StateAssignment(
                    state=state_id,
                    operation=operation,
                    value=compile_expression(action.value),
                )
            )
            _append_source_entry(
                entries,
                air_id=context.next_action_id("assignment"),
                node=action,
                kind="state_assignment",
                reference=state_id,
            )
            continue

        if isinstance(action, SetActionNode):
            state_id = _local_reference(
                state_ids,
                action.state_name,
                owner="state",
                node=action,
            )
            state_type = active_state_types.get(
                action.state_name,
                INT,
            )
            operation = {
                INT: "set_int",
                BOOL: "set_bool",
                STRING: "set_string",
                FLOAT: "set_float",
            }.get(state_type)

            if operation is None:
                raise _compile_error(
                    code="APX-TYPE-013",
                    message=(
                        f"State {action.state_name!r} cannot be assigned "
                        f"with type {state_type}."
                    ),
                    node=action,
                )

            compiled_actions.append(
                StateAssignment(
                    state=state_id,
                    operation=operation,
                    value=compile_expression(action.expression),
                )
            )
            _append_source_entry(
                entries,
                air_id=context.next_action_id("assignment"),
                node=action,
                kind="state_assignment",
                reference=state_id,
            )
            continue

        if isinstance(action, InvokeActionNode):
            invocation_id = context.next_invocation_id()
            compiled_actions.append(
                DirectiveInvocation(
                    target=action.target,
                    id=invocation_id,
                )
            )
            _append_source_entry(
                entries,
                air_id=invocation_id,
                node=action,
                kind="directive_invocation",
                reference=action.target,
            )
            continue

        if isinstance(action, WhenActionNode):
            nested_context = _CompileContext(
                source_entries=entries,
                scope=f"{context.scope}:when:{context.action_index}",
                invocation_index=context.invocation_index,
                action_index=0,
            )
            true_actions = compile_actions(
                action.actions,
                state_ids=state_ids,
                event_ids=event_ids,
                context=nested_context,
                state_types=active_state_types,
            )
            false_actions = compile_actions(
                tuple(getattr(action, "otherwise_actions", ()) or ()),
                state_ids=state_ids,
                event_ids=event_ids,
                context=nested_context,
                state_types=active_state_types,
            )
            context.invocation_index = nested_context.invocation_index
            context.action_index += 1

            compiled_actions.append(
                AIRWhenAction(
                    condition=compile_expression(action.condition),
                    actions=true_actions,
                    otherwise_actions=false_actions,
                )
            )
            _append_source_entry(
                entries,
                air_id=context.next_action_id("when"),
                node=action,
                kind="conditional_action",
            )
            continue

        raise _compile_error(
            code="APX-COMPILE-005",
            message=(
                "Unsupported ordered action "
                f"{type(action).__module__}.{type(action).__name__}."
            ),
            node=action,
        )

    if pending_message is not None:
        raise _compile_error(
            code="APX-COMPILE-006",
            message="A message action must be followed by an emit action.",
            node=pending_message,
        )

    return tuple(compiled_actions)


def _compile_directive_with_map(
    node: DirectiveNode,
    *,
    function_signatures: Optional[Mapping[str, FunctionSignature]] = None,
) -> CompiledSource:
    principal_id = f"principal:{node.name}"
    directive_id = f"directive:{node.name}"
    authority_id = f"auth:{node.name}"
    entries: list[SourceMapEntry] = []
    functions = _normalize_function_signatures(function_signatures)

    state_types = _type_check_directive_states(
        node,
        functions=functions,
    )

    for cause in node.causes:
        for path in cause.paths:
            _type_check_directive_actions(
                tuple(path.actions),
                state_types=state_types,
                functions=functions,
            )

    _append_source_entry(
        entries,
        air_id=directive_id,
        node=node,
        kind="directive",
        reference=node.name,
    )
    _append_source_entry(
        entries,
        air_id=principal_id,
        node=node,
        kind="principal",
        reference=node.name,
    )
    _append_source_entry(
        entries,
        air_id=authority_id,
        node=node,
        kind="authority_check",
        reference=node.name,
    )
    _record_directive_function_calls(
        node,
        entries,
    )

    state_ids = {state.name: f"state:{state.name}" for state in node.states}
    event_ids = {event.name: f"event:{event.name}" for event in node.events}

    for state in node.states:
        _append_source_entry(
            entries,
            air_id=state_ids[state.name],
            node=state,
            kind="state",
            reference=state.name,
        )

    for event in node.events:
        _append_source_entry(
            entries,
            air_id=event_ids[event.name],
            node=event,
            kind="event",
            reference=event.name,
        )

    causal_decisions: list[CausalDecision] = []

    for cause in node.causes:
        cause_id = f"cause:{cause.name}"
        _append_source_entry(
            entries,
            air_id=cause_id,
            node=cause,
            kind="causal_decision",
            reference=cause.name,
        )
        paths: list[CausalPath] = []

        for path in cause.paths:
            path_id = f"path:{path.name}"
            _append_source_entry(
                entries,
                air_id=path_id,
                node=path,
                kind="causal_path",
                reference=path.name,
            )

            action_context = _CompileContext(
                source_entries=entries,
                scope=f"{node.name}:{cause.name}:{path.name}",
            )
            ordered_actions = compile_actions(
                path.actions,
                state_ids=state_ids,
                event_ids=event_ids,
                context=action_context,
                state_types=state_types,
            )

            assignments = tuple(
                action for action in ordered_actions if isinstance(action, StateAssignment)
            )
            emits = tuple(
                action for action in ordered_actions if isinstance(action, EventEmission)
            )
            invocations = tuple(
                action
                for action in ordered_actions
                if isinstance(action, DirectiveInvocation)
            )

            paths.append(
                CausalPath(
                    id=path_id,
                    weight=path.weight,
                    assignments=assignments,
                    emits=emits,
                    invocations=invocations,
                    effects=(),
                    rationale="",
                    actions=ordered_actions,
                )
            )

        causal_decisions.append(
            CausalDecision(
                id=cause_id,
                cause=cause.name,
                policy="max_weight",
                paths=tuple(paths),
            )
        )

    requirements = tuple(
        DirectiveRequirement(capability=requirement.capability)
        for requirement in node.requirements
    )

    for index, requirement in enumerate(node.requirements):
        _append_source_entry(
            entries,
            air_id=f"requirement:{node.name}:{index}",
            node=requirement,
            kind="requirement",
            reference=requirement.capability,
        )

    program = AIRProgram(
        version=AIR_VERSION,
        principals=(Principal(id=principal_id, display_name=node.name),),
        states=tuple(
            StateDefinition(
                id=state_ids[state.name],
                initial=compile_expression(state.initial),
                value_type=_compile_type_annotation(
                    getattr(state, "type_annotation", None),
                    owner=f"State {state.name!r}",
                    node=state,
                    default=INT,
                ),
            )
            for state in node.states
        ),
        events=tuple(
            EventDefinition(id=event_ids[event.name], name=event.name)
            for event in node.events
        ),
        authority_checks=(
            AuthorityCheck(
                id=authority_id,
                principal=principal_id,
                capability=f"directive.invoke:{node.name}",
                resource=directive_id,
            ),
        ),
        causal_decisions=tuple(causal_decisions),
        directives=(
            AIRDirective(
                id=directive_id,
                name=node.name,
                principal=principal_id,
                authority_checks=(authority_id,),
                causal_decisions=tuple(
                    decision.id for decision in causal_decisions
                ),
                order=0,
            ),
        ),
        requirements=requirements,
        authorities=tuple(
            DirectiveAuthority(name=authority.name)
            for authority in node.authorities
        ),
    )

    return CompiledSource(program=program, source_map=SourceMap(tuple(entries)))



def _validate_function_source_flow(
    statements: tuple[object, ...],
    *,
    function_name: str,
    depth: int = 0,
) -> bool:
    """Reject unreachable source statements and report definite return.

    RuntimeValidator remains the authoritative AIR-level control-flow
    validator. This source pass exists so unreachable source code receives a
    precise compile-stage diagnostic at the first unreachable statement.
    """

    if depth > 64:
        # RuntimeValidator also protects hand-authored AIR. Parser-produced
        # source reaches this guard first and receives a source-aware error.
        owner = statements[0] if statements else None
        raise _compile_error(
            code="APX-COMPILE-013",
            message=(
                f"Function {function_name!r} exceeds the maximum function "
                "conditional nesting depth of 64."
            ),
            node=owner,
            air_id=f"function:{function_name}",
        )

    definitely_returns = False

    for statement in tuple(statements):
        if definitely_returns:
            raise _compile_error(
                code="APX-COMPILE-012",
                message=(
                    f"Function {function_name!r} contains an unreachable "
                    "statement after a definite return."
                ),
                node=statement,
                air_id=f"function:{function_name}",
            )

        if isinstance(statement, ReturnNode):
            definitely_returns = True
            continue

        if isinstance(statement, FunctionWhenNode):
            true_returns = _validate_function_source_flow(
                tuple(statement.actions),
                function_name=function_name,
                depth=depth + 1,
            )

            false_returns = False
            otherwise_actions = tuple(
                getattr(statement, "otherwise_actions", ()) or ()
            )

            if otherwise_actions:
                false_returns = _validate_function_source_flow(
                    otherwise_actions,
                    function_name=function_name,
                    depth=depth + 1,
                )

            if true_returns and false_returns:
                definitely_returns = True
            continue

        # LetNode and any unsupported node continue normally here.
        # Unsupported nodes are rejected by _compile_function_statements with
        # its existing APX-COMPILE-011 diagnostic.

    return definitely_returns


def _compile_function_statements(
    statements: tuple[object, ...],
    *,
    function_name: str,
    entries: list[SourceMapEntry],
    scope: str = "body",
) -> tuple[object, ...]:
    """Compile one ordered pure-function statement stream recursively."""

    compiled: list[object] = []

    for index, statement in enumerate(statements):
        statement_scope = f"{scope}:{index}"

        if isinstance(statement, LetNode):
            air_id = f"local:{function_name}:{statement_scope}"
            compiled.append(
                AIRLocalBinding(
                    name=statement.name,
                    expression=compile_expression(statement.expression),
                )
            )
            _append_source_entry(
                entries,
                air_id=air_id,
                node=statement,
                kind="function_local",
                reference=statement.name,
            )
            continue

        if isinstance(statement, ReturnNode):
            air_id = f"return:{function_name}:{statement_scope}"
            compiled.append(
                AIRFunctionReturn(
                    expression=compile_expression(statement.expression),
                )
            )
            _append_source_entry(
                entries,
                air_id=air_id,
                node=statement,
                kind="function_return",
                reference=function_name,
            )
            continue

        if isinstance(statement, FunctionWhenNode):
            air_id = f"function_when:{function_name}:{statement_scope}"
            compiled.append(
                AIRFunctionWhen(
                    condition=compile_expression(statement.condition),
                    actions=_compile_function_statements(
                        statement.actions,
                        function_name=function_name,
                        entries=entries,
                        scope=f"{statement_scope}:when",
                    ),
                    otherwise_actions=_compile_function_statements(
                        statement.otherwise_actions,
                        function_name=function_name,
                        entries=entries,
                        scope=f"{statement_scope}:otherwise",
                    ),
                )
            )
            _append_source_entry(
                entries,
                air_id=air_id,
                node=statement,
                kind="function_conditional",
                reference=function_name,
            )
            continue

        raise _compile_error(
            code="APX-COMPILE-011",
            message=(
                "Unsupported pure-function statement "
                f"{type(statement).__module__}.{type(statement).__name__}."
            ),
            node=statement,
        )

    return tuple(compiled)


def _compile_function_with_map(
    node: FunctionNode,
    *,
    function_signatures: Optional[Mapping[str, FunctionSignature]] = None,
) -> CompiledSource:
    """Compile one pure function into an independently linkable AIR unit."""

    function_id = f"function:{node.name}"
    entries: list[SourceMapEntry] = []
    functions = _normalize_function_signatures(function_signatures)

    if DEFAULT_STANDARD_LIBRARY.contains(node.name):
        raise _compile_error(
            code="APX-COMPILE-015",
            message=(
                f"Function name {node.name!r} is reserved by the "
                "ApexForge standard library."
            ),
            node=node,
            air_id=function_id,
        )
    _append_source_entry(
        entries,
        air_id=function_id,
        node=node,
        kind="function",
        reference=node.name,
    )
    _record_function_calls(
        node,
        entries,
    )

    parameter_names = tuple(parameter.name for parameter in node.parameters)
    duplicate_parameters = tuple(
        name
        for name in dict.fromkeys(parameter_names)
        if parameter_names.count(name) > 1
    )
    if duplicate_parameters:
        raise _compile_error(
            code="APX-COMPILE-008",
            message=(
                f"Function {node.name!r} declares duplicate parameter "
                f"{duplicate_parameters[0]!r}."
            ),
            node=node,
            air_id=function_id,
        )

    for index, type_parameter in enumerate(
        tuple(getattr(node, "type_parameters", ()) or ())
    ):
        _append_source_entry(
            entries,
            air_id=f"type_parameter:{node.name}:{index}",
            node=type_parameter,
            kind="function_type_parameter",
            reference=type_parameter.name,
        )

    for index, parameter in enumerate(node.parameters):
        _append_source_entry(
            entries,
            air_id=f"parameter:{node.name}:{index}",
            node=parameter,
            kind="function_parameter",
            reference=parameter.name,
        )

    # Retain the P7.2A compile-time checks for the leading-local compatibility
    # projection. Full branch-local scope validation belongs to RuntimeValidator.
    local_nodes = tuple(
        getattr(node, "local_bindings", ()) or ()
    )
    local_names = tuple(binding.name for binding in local_nodes)
    duplicate_locals = tuple(
        name
        for name in dict.fromkeys(local_names)
        if local_names.count(name) > 1
    )

    if duplicate_locals:
        raise _compile_error(
            code="APX-COMPILE-009",
            message=(
                f"Function {node.name!r} declares duplicate local "
                f"{duplicate_locals[0]!r}."
            ),
            node=node,
            air_id=function_id,
        )

    shadowed = tuple(
        name for name in local_names if name in set(parameter_names)
    )
    if shadowed:
        raise _compile_error(
            code="APX-COMPILE-010",
            message=(
                f"Function {node.name!r} local {shadowed[0]!r} "
                "cannot shadow a parameter."
            ),
            node=node,
            air_id=function_id,
        )

    body_nodes = tuple(getattr(node, "body", ()) or ())
    if not body_nodes:
        body_nodes = local_nodes + (node.return_statement,)

    _validate_function_source_flow(
        body_nodes,
        function_name=node.name,
    )

    _type_check_function(
        node,
        body_nodes=body_nodes,
        functions=functions,
    )

    compiled_body = _compile_function_statements(
        body_nodes,
        function_name=node.name,
        entries=entries,
    )

    program = AIRProgram(
        version=AIR_VERSION,
        states=(),
        events=(),
        authority_checks=(),
        causal_decisions=(),
        directives=(),
        requirements=(),
        authorities=(),
        principals=(),
        roles=(),
        functions=(
            AIRFunction(
                id=function_id,
                name=node.name,
                parameters=tuple(
                    AIRParameter(
                        name=parameter.name,
                        value_type=_compile_type_annotation(
                            getattr(parameter, "type_annotation", None),
                            owner=(
                                f"Parameter {parameter.name!r} "
                                f"of function {node.name!r}"
                            ),
                            node=parameter,
                        ),
                    )
                    for parameter in node.parameters
                ),
                return_expression=compile_expression(
                    node.return_statement.expression
                ),
                order=0,
                local_bindings=tuple(
                    AIRLocalBinding(
                        name=binding.name,
                        expression=compile_expression(binding.expression),
                    )
                    for binding in local_nodes
                ),
                body=compiled_body,
                return_type=_compile_type_annotation(
                    getattr(node, "return_type", None),
                    owner=f"Function {node.name!r} return",
                    node=node,
                ),
                type_parameters=tuple(
                    type_parameter.apex_type
                    for type_parameter in tuple(
                        getattr(node, "type_parameters", ()) or ()
                    )
                ),
            ),
        ),
    )

    return CompiledSource(
        program=program,
        source_map=SourceMap(tuple(entries)),
    )


def compile_directive(
    node: DirectiveNode,
    *,
    function_signatures: Optional[Mapping[str, FunctionSignature]] = None,
) -> AIRProgram:
    return _compile_directive_with_map(
        node,
        function_signatures=function_signatures,
    ).program


def compile_function(
    node: FunctionNode,
    *,
    function_signatures: Optional[Mapping[str, FunctionSignature]] = None,
) -> AIRProgram:
    return _compile_function_with_map(
        node,
        function_signatures=function_signatures,
    ).program


def compile_node_with_map(
    node: DirectiveNode | RoleNode | FunctionNode,
    *,
    function_signatures: Optional[Mapping[str, FunctionSignature]] = None,
) -> CompiledSource:
    if isinstance(node, DirectiveNode):
        return _compile_directive_with_map(
            node,
            function_signatures=function_signatures,
        )

    if isinstance(node, FunctionNode):
        return _compile_function_with_map(
            node,
            function_signatures=function_signatures,
        )

    if isinstance(node, RoleNode):
        role = compile_role(node)
        entries: list[SourceMapEntry] = []
        _append_source_entry(
            entries,
            air_id=f"role:{node.name}",
            node=node,
            kind="role",
            reference=node.name,
        )
        return CompiledSource(program=role, source_map=SourceMap(tuple(entries)))

    raise _compile_error(
        code="APX-COMPILE-007",
        message=f"Unsupported top-level AST node {type(node).__name__}.",
        node=node,
    )


def compile_node(
    node: DirectiveNode | RoleNode | FunctionNode,
    *,
    function_signatures: Optional[Mapping[str, FunctionSignature]] = None,
) -> AIRProgram | AIRRole:
    return compile_node_with_map(
        node,
        function_signatures=function_signatures,
    ).program


def compile_source_with_map(
    source: str,
    *,
    source_name: str = "<memory>",
    function_signatures: Optional[Mapping[str, FunctionSignature]] = None,
) -> CompiledSource:
    node = parse(source, source_name=source_name)
    return compile_node_with_map(
        node,
        function_signatures=function_signatures,
    )


def compile_source(
    source: str,
    *,
    function_signatures: Optional[Mapping[str, FunctionSignature]] = None,
) -> AIRProgram | AIRRole:
    """Backward-compatible one-source compiler returning AIR only."""

    return compile_source_with_map(
        source,
        function_signatures=function_signatures,
    ).program


__all__ = (
    "CompiledSource",
    "CompilerError",
    "SourceMap",
    "SourceMapEntry",
    "compile_actions",
    "compile_directive",
    "compile_expression",
    "compile_function",
    "compile_node",
    "compile_node_with_map",
    "compile_source",
    "compile_source_with_map",
)