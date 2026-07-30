"""ApexForge AST-to-AIR compiler with sidecar source maps."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

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
    StringLiteralNode,
    BooleanLiteralNode,
    IdentifierNode,
    UnaryExpressionNode,
    BinaryExpressionNode,
    CallExpressionNode,
    LetNode,
    FunctionNode,
    RoleNode,
    SetActionNode,
    parse,
)
from air.expressions import (
    AIRExpression,
    AIRIntegerLiteral,
    AIRStringLiteral,
    AIRBooleanLiteral,
    AIRIdentifierReference,
    AIRUnaryExpression,
    AIRBinaryExpression,
    AIRCallExpression,
)
from air.functions import AIRFunction, AIRLocalBinding, AIRParameter
from language.source import SourceSpan


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


def compile_expression(node: ExpressionNode) -> AIRExpression:
    if isinstance(node, IntegerLiteralNode):
        return AIRIntegerLiteral(value=node.value)
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
        )

    raise _compile_error(
        code="APX-COMPILE-001",
        message=f"Unsupported expression AST node {type(node).__name__}.",
        node=node,
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
            compiled_actions.append(
                StateAssignment(
                    state=state_id,
                    operation="add_int",
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
            compiled_actions.append(
                StateAssignment(
                    state=state_id,
                    operation="set_int",
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
            )
            false_actions = compile_actions(
                tuple(getattr(action, "otherwise_actions", ()) or ()),
                state_ids=state_ids,
                event_ids=event_ids,
                context=nested_context,
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
) -> CompiledSource:
    principal_id = f"principal:{node.name}"
    directive_id = f"directive:{node.name}"
    authority_id = f"auth:{node.name}"
    entries: list[SourceMapEntry] = []

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


def _compile_function_with_map(
    node: FunctionNode,
) -> CompiledSource:
    """Compile one pure function into an independently linkable AIR unit."""

    function_id = f"function:{node.name}"
    entries: list[SourceMapEntry] = []
    _append_source_entry(
        entries,
        air_id=function_id,
        node=node,
        kind="function",
        reference=node.name,
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

    for index, parameter in enumerate(node.parameters):
        _append_source_entry(
            entries,
            air_id=f"parameter:{node.name}:{index}",
            node=parameter,
            kind="function_parameter",
            reference=parameter.name,
        )

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

    for index, binding in enumerate(local_nodes):
        _append_source_entry(
            entries,
            air_id=f"local:{node.name}:{index}",
            node=binding,
            kind="function_local",
            reference=binding.name,
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
                    AIRParameter(name=parameter.name)
                    for parameter in node.parameters
                ),
                return_expression=compile_expression(
                    node.return_statement.expression
                ),
                order=0,
                local_bindings=tuple(
                    AIRLocalBinding(
                        name=binding.name,
                        expression=compile_expression(
                            binding.expression
                        ),
                    )
                    for binding in local_nodes
                ),
            ),
        ),
    )

    return CompiledSource(
        program=program,
        source_map=SourceMap(tuple(entries)),
    )


def compile_directive(node: DirectiveNode) -> AIRProgram:
    return _compile_directive_with_map(node).program


def compile_function(node: FunctionNode) -> AIRProgram:
    return _compile_function_with_map(node).program


def compile_node_with_map(
    node: DirectiveNode | RoleNode | FunctionNode,
) -> CompiledSource:
    if isinstance(node, DirectiveNode):
        return _compile_directive_with_map(node)

    if isinstance(node, FunctionNode):
        return _compile_function_with_map(node)

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
) -> AIRProgram | AIRRole:
    return compile_node_with_map(node).program


def compile_source_with_map(
    source: str,
    *,
    source_name: str = "<memory>",
) -> CompiledSource:
    node = parse(source, source_name=source_name)
    return compile_node_with_map(node)


def compile_source(source: str) -> AIRProgram | AIRRole:
    """Backward-compatible one-source compiler returning AIR only."""

    return compile_source_with_map(source).program


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