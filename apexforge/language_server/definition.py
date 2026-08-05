"""AFP-P10-T4.7 ApexForge same-document definition navigation.

The analyzer resolves declarations and syntax-level references inside one open
ApexForge document. It performs no project build, linking, cross-file lookup,
type inference, validation, references search, rename, or runtime execution.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re
from typing import Final, Iterable, Mapping, Optional

from language.diagnostics import diagnostics_from_exception
from language.modules import ModuleSource, parse_module_source
from language.parser import (
    AddActionNode,
    AuthorityNode,
    BinaryExpressionNode,
    BooleanLiteralNode,
    CallExpressionNode,
    CapabilityNode,
    CauseNode,
    DirectiveNode,
    EmitActionNode,
    EventNode,
    FloatLiteralNode,
    FunctionNode,
    FunctionWhenNode,
    IdentifierNode,
    IntegerLiteralNode,
    InvokeActionNode,
    LetNode,
    MessageActionNode,
    ParameterNode,
    PathNode,
    PrincipalNode,
    ReturnNode,
    RoleNode,
    SetActionNode,
    StateNode,
    StringLiteralNode,
    TypeAnnotationNode,
    TypeParameterNode,
    UnaryExpressionNode,
    WhenActionNode,
    WorkflowNode,
    parse_source_unit,
)
from language.source import SourceSpan
from language_server.diagnostics import offset_to_lsp_position
from language_server.hover import lsp_position_to_offset


P10_T4_DEFINITION_VERSION: Final[str] = "10-T4.7"
DEFINITION_SCHEMA: Final[int] = 1
DEFINITION_KIND: Final[str] = "apexforge.language-server-definition"
DEFINITION_METHOD: Final[str] = "textDocument/definition"

_IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


@dataclass(frozen=True, order=True)
class _Definition:
    start: int
    end: int
    name: str
    namespace: str


@dataclass(frozen=True, order=True)
class _Occurrence:
    start: int
    end: int
    target_start: int
    target_end: int
    name: str
    namespace: str


class _Index:
    def __init__(self) -> None:
        self.definitions: list[_Definition] = []
        self.occurrences: list[_Occurrence] = []

    def define(
        self,
        text: str,
        span: object,
        name: str,
        namespace: str,
        *,
        keyword: Optional[str] = None,
    ) -> Optional[_Definition]:
        offsets = _name_offsets(text, span, name, keyword=keyword)
        if offsets is None:
            return None
        definition = _Definition(offsets[0], offsets[1], name, namespace)
        self.definitions.append(definition)
        self.occurrences.append(
            _Occurrence(
                definition.start,
                definition.end,
                definition.start,
                definition.end,
                name,
                namespace,
            )
        )
        return definition

    def reference(
        self,
        start: int,
        end: int,
        definition: Optional[_Definition],
    ) -> None:
        if definition is None:
            return
        self.occurrences.append(
            _Occurrence(
                start,
                end,
                definition.start,
                definition.end,
                definition.name,
                definition.namespace,
            )
        )


def _require_uri(value: object, owner: str) -> str:
    if type(value) is not str or not value or ":" not in value:
        raise ValueError(f"{owner} must be a non-empty absolute URI.")
    return value


def _require_text(value: object, owner: str) -> str:
    if type(value) is not str:
        raise TypeError(f"{owner} must be a string.")
    return value


def _span_offsets(span: object) -> Optional[tuple[int, int]]:
    if not isinstance(span, SourceSpan):
        return None
    return span.start.offset, span.end.offset


def _name_offsets(
    text: str,
    span: object,
    name: str,
    *,
    keyword: Optional[str] = None,
) -> Optional[tuple[int, int]]:
    bounds = _span_offsets(span)
    if bounds is None or type(name) is not str or not name:
        return None
    start, end = bounds
    segment = text[start:end]
    if keyword is not None:
        pattern = re.compile(
            r"\b" + re.escape(keyword) + r"\s+(?P<name>" + re.escape(name) + r")\b"
        )
        match = pattern.search(segment)
        if match is not None:
            selected = start + match.start("name")
            return selected, selected + len(name)
    match = re.search(r"(?<![A-Za-z0-9_])" + re.escape(name) + r"(?![A-Za-z0-9_])", segment)
    if match is None:
        return None
    selected = start + match.start()
    return selected, selected + len(name)


def _expression_name_offsets(expression: object, name: str) -> Optional[tuple[int, int]]:
    span = getattr(expression, "span", None)
    bounds = _span_offsets(span)
    if bounds is None:
        return None
    start, end = bounds
    if isinstance(expression, IdentifierNode):
        return start, end
    return None


def _resolve_before(
    definitions: Iterable[_Definition],
    name: str,
    offset: int,
) -> Optional[_Definition]:
    candidates = tuple(
        definition
        for definition in definitions
        if definition.name == name and definition.start < offset
    )
    if not candidates:
        return None
    return max(candidates, key=lambda item: (item.start, item.end, item.namespace))


def _expression_references(
    index: _Index,
    text: str,
    expression: object,
    value_definitions: Iterable[_Definition],
    type_definitions: Mapping[str, _Definition],
    callable_definition: Optional[_Definition] = None,
) -> None:
    if isinstance(expression, IdentifierNode):
        bounds = _span_offsets(expression.span)
        if bounds is not None:
            index.reference(
                bounds[0],
                bounds[1],
                _resolve_before(value_definitions, expression.name, bounds[0]),
            )
        return
    if isinstance(expression, CallExpressionNode):
        target = _name_offsets(text, expression.span, expression.target)
        if target is not None and callable_definition is not None and expression.target == callable_definition.name:
            index.reference(target[0], target[1], callable_definition)
        for annotation in tuple(getattr(expression, "type_arguments", ()) or ()):
            _type_reference(index, text, annotation, type_definitions)
        for argument in expression.arguments:
            _expression_references(
                index,
                text,
                argument,
                value_definitions,
                type_definitions,
                callable_definition,
            )
        return
    if isinstance(expression, UnaryExpressionNode):
        _expression_references(
            index,
            text,
            expression.operand,
            value_definitions,
            type_definitions,
            callable_definition,
        )
        return
    if isinstance(expression, BinaryExpressionNode):
        _expression_references(
            index,
            text,
            expression.left,
            value_definitions,
            type_definitions,
            callable_definition,
        )
        _expression_references(
            index,
            text,
            expression.right,
            value_definitions,
            type_definitions,
            callable_definition,
        )
        return
    if isinstance(
        expression,
        (IntegerLiteralNode, FloatLiteralNode, StringLiteralNode, BooleanLiteralNode),
    ):
        return


def _type_reference(
    index: _Index,
    text: str,
    annotation: object,
    definitions: Mapping[str, _Definition],
) -> None:
    if not isinstance(annotation, TypeAnnotationNode):
        return
    name = annotation.name
    target = definitions.get(name)
    if target is None:
        return
    offsets = _name_offsets(text, annotation.span, name)
    if offsets is not None:
        index.reference(offsets[0], offsets[1], target)


def _function_action_references(
    index: _Index,
    text: str,
    action: object,
    values: list[_Definition],
    type_definitions: Mapping[str, _Definition],
    callable_definition: Optional[_Definition],
) -> None:
    if isinstance(action, LetNode):
        _expression_references(
            index,
            text,
            action.expression,
            values,
            type_definitions,
            callable_definition,
        )
        definition = index.define(text, action.span, action.name, "value", keyword="let")
        if definition is not None:
            values.append(definition)
        return
    if isinstance(action, ReturnNode):
        _expression_references(
            index,
            text,
            action.expression,
            values,
            type_definitions,
            callable_definition,
        )
        return
    if isinstance(action, FunctionWhenNode):
        _expression_references(
            index,
            text,
            action.condition,
            values,
            type_definitions,
            callable_definition,
        )
        when_values = list(values)
        for nested in action.actions:
            _function_action_references(
                index,
                text,
                nested,
                when_values,
                type_definitions,
                callable_definition,
            )
        otherwise_values = list(values)
        for nested in action.otherwise_actions:
            _function_action_references(
                index,
                text,
                nested,
                otherwise_values,
                type_definitions,
                callable_definition,
            )


def _function_index(index: _Index, node: FunctionNode, text: str) -> None:
    function_definition = index.define(text, node.span, node.name, "callable", keyword="function")
    type_definitions: dict[str, _Definition] = {}
    for parameter in node.type_parameters:
        assert isinstance(parameter, TypeParameterNode)
        definition = index.define(text, parameter.span, parameter.name, "type")
        if definition is not None:
            type_definitions[definition.name] = definition

    values: list[_Definition] = []
    for parameter in node.parameters:
        assert isinstance(parameter, ParameterNode)
        definition = index.define(text, parameter.span, parameter.name, "value")
        if definition is not None:
            values.append(definition)
        _type_reference(index, text, parameter.type_annotation, type_definitions)
    _type_reference(index, text, node.return_type, type_definitions)

    for action in node.body:
        _function_action_references(
            index,
            text,
            action,
            values,
            type_definitions,
            function_definition,
        )


def _action_references(
    index: _Index,
    text: str,
    action: object,
    states: Mapping[str, _Definition],
    events: Mapping[str, _Definition],
) -> None:
    value_definitions = tuple(states.values())
    if isinstance(action, AddActionNode):
        offsets = _name_offsets(text, action.span, action.state_name, keyword="add")
        if offsets is not None:
            index.reference(offsets[0], offsets[1], states.get(action.state_name))
        _expression_references(index, text, action.value, value_definitions, {})
        return
    if isinstance(action, SetActionNode):
        offsets = _name_offsets(text, action.span, action.state_name, keyword="set")
        if offsets is not None:
            index.reference(offsets[0], offsets[1], states.get(action.state_name))
        _expression_references(index, text, action.expression, value_definitions, {})
        return
    if isinstance(action, EmitActionNode):
        offsets = _name_offsets(text, action.span, action.event_name, keyword="emit")
        if offsets is not None:
            index.reference(offsets[0], offsets[1], events.get(action.event_name))
        return
    if isinstance(action, MessageActionNode):
        _expression_references(index, text, action.expression, value_definitions, {})
        return
    if isinstance(action, InvokeActionNode):
        return
    if isinstance(action, WhenActionNode):
        _expression_references(index, text, action.condition, value_definitions, {})
        for nested in action.actions:
            _action_references(index, text, nested, states, events)
        for nested in action.otherwise_actions:
            _action_references(index, text, nested, states, events)


def _directive_index(index: _Index, node: DirectiveNode, text: str) -> None:
    index.define(text, node.span, node.name, "directive", keyword="directive")
    states: dict[str, _Definition] = {}
    events: dict[str, _Definition] = {}

    for state in node.states:
        assert isinstance(state, StateNode)
        definition = index.define(text, state.span, state.name, "state", keyword="state")
        if definition is not None:
            states[definition.name] = definition
    for event in node.events:
        assert isinstance(event, EventNode)
        definition = index.define(text, event.span, event.name, "event", keyword="event")
        if definition is not None:
            events[definition.name] = definition

    for state in node.states:
        _expression_references(index, text, state.initial, tuple(states.values()), {})
    for cause in node.causes:
        assert isinstance(cause, CauseNode)
        index.define(text, cause.span, cause.name, "cause", keyword="cause")
        for path in cause.paths:
            assert isinstance(path, PathNode)
            index.define(text, path.span, path.name, "path", keyword="path")
            for action in path.actions:
                _action_references(index, text, action, states, events)


def _module_index(index: _Index, module_source: ModuleSource, text: str) -> None:
    if module_source.module_name is not None:
        index.define(
            text,
            module_source.module_span,
            module_source.module_name,
            "module",
            keyword="module",
        )


def _top_level_index(index: _Index, node: object, text: str) -> None:
    if isinstance(node, FunctionNode):
        _function_index(index, node, text)
        return
    if isinstance(node, DirectiveNode):
        _directive_index(index, node, text)
        return
    if isinstance(node, WorkflowNode):
        index.define(text, node.span, node.name, "workflow", keyword="workflow")
        return
    if isinstance(node, AuthorityNode):
        index.define(text, node.span, node.name, "authority", keyword="authority")
        for capability in node.capabilities:
            assert isinstance(capability, CapabilityNode)
            index.define(text, capability.span, capability.name, "capability", keyword="capability")
        return
    if isinstance(node, RoleNode):
        index.define(text, node.span, node.name, "role", keyword="role")
        return
    if isinstance(node, PrincipalNode):
        index.define(text, node.span, node.name, "principal", keyword="principal")


def _definition_index(uri: str, text: str) -> _Index:
    index = _Index()
    try:
        module_source = parse_module_source(uri, text)
        unit = parse_source_unit(
            module_source.masked_source,
            source_name=uri,
        )
    except Exception as error:
        if diagnostics_from_exception(error):
            return index
        raise
    _module_index(index, module_source, text)
    for node in unit.declarations:
        _top_level_index(index, node, text)
    index.occurrences.sort(
        key=lambda item: (
            item.start,
            item.end,
            item.target_start,
            item.target_end,
            item.namespace,
            item.name,
        )
    )
    return index


def definition(
    uri: str,
    text: str,
    position: Mapping[str, object],
) -> Optional[dict[str, object]]:
    """Return one same-document LSP Location for the selected occurrence."""

    selected_uri = _require_uri(uri, "uri")
    source = _require_text(text, "text")
    offset = lsp_position_to_offset(source, position)
    index = _definition_index(selected_uri, source)
    candidates = tuple(
        occurrence
        for occurrence in index.occurrences
        if occurrence.start <= offset < occurrence.end
    )
    if not candidates:
        return None
    selected = min(
        candidates,
        key=lambda item: (
            item.end - item.start,
            item.start,
            item.target_start,
            item.namespace,
            item.name,
        ),
    )
    return {
        "uri": selected_uri,
        "range": {
            "start": offset_to_lsp_position(source, selected.target_start),
            "end": offset_to_lsp_position(source, selected.target_end),
        },
    }


def definition_contract() -> dict[str, object]:
    return {
        "schema": DEFINITION_SCHEMA,
        "kind": DEFINITION_KIND,
        "definition_version": P10_T4_DEFINITION_VERSION,
        "method": DEFINITION_METHOD,
        "result": "Location | null",
        "position_encoding": "utf-16",
        "scope": "open documents",
        "navigation": "same-document declaration ranges",
        "targets": (
            "declaration_names",
            "function_type_parameters",
            "function_parameters_and_prior_locals",
            "recursive_function_calls",
            "directive_state_actions_and_expressions",
            "directive_event_emissions",
            "message_and_when_expressions",
        ),
        "invalid_source": "null; diagnostics remain T4.2 responsibility",
        "unresolved_reference": "null",
        "semantic_depth": "single-document syntax and lexical scope",
        "features_deferred": (
            "references",
            "rename",
            "workspace_symbols",
            "formatting",
            "cross_file_resolution",
            "import_resolution",
            "workflow_and_directive_target_resolution",
            "authority_role_and_capability_resolution",
            "type_inference",
        ),
    }


def definition_fingerprint() -> str:
    payload = json.dumps(
        definition_contract(),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


CANONICAL_DEFINITION_SHA256: Final[str] = "6a8c78f39e5f265bc2f8c1c9b1085834570712f4607cf09ce95d6464b1b647cd"


__all__ = (
    "CANONICAL_DEFINITION_SHA256",
    "DEFINITION_KIND",
    "DEFINITION_METHOD",
    "DEFINITION_SCHEMA",
    "P10_T4_DEFINITION_VERSION",
    "definition",
    "definition_contract",
    "definition_fingerprint",
)
