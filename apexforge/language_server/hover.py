"""AFP-P10-T4.5 ApexForge hover intelligence.

The analyzer reuses the frozen module-header and parser pipeline to provide
syntax-level information for declarations and nested members in one open
ApexForge document. It performs no compilation, linking, cross-file lookup,
type inference, validation, or runtime execution.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Final, Iterable, Mapping, Optional

from language.diagnostics import diagnostics_from_exception
from language.modules import ModuleSource, parse_module_source
from language.parser import (
    AuthorityNode,
    CapabilityNode,
    CauseNode,
    DirectiveAuthorityNode,
    DirectiveNode,
    EventNode,
    FunctionNode,
    LetNode,
    ParameterNode,
    PathNode,
    PrincipalAuthorityNode,
    PrincipalNode,
    PrincipalRoleNode,
    RequirementNode,
    RoleAuthorityNode,
    RoleNode,
    StateNode,
    TypeParameterNode,
    WorkflowInvokeNode,
    WorkflowNode,
    parse,
)
from language.source import SourceSpan
from language_server.diagnostics import offset_to_lsp_position


P10_T4_HOVER_VERSION: Final[str] = "10-T4.5"
HOVER_SCHEMA: Final[int] = 1
HOVER_KIND: Final[str] = "apexforge.language-server-hover"
HOVER_METHOD: Final[str] = "textDocument/hover"
HOVER_MARKUP_KIND: Final[str] = "markdown"


@dataclass(frozen=True, order=True)
class _HoverEntry:
    start: int
    end: int
    label: str
    description: str

    def __post_init__(self) -> None:
        if type(self.start) is not int or type(self.end) is not int:
            raise TypeError("Hover entry offsets must be integers.")
        if self.start < 0 or self.end <= self.start:
            raise ValueError("Hover entry offsets must form a non-empty range.")
        if type(self.label) is not str or not self.label:
            raise ValueError("Hover entry label must be non-empty.")
        if type(self.description) is not str or not self.description:
            raise ValueError("Hover entry description must be non-empty.")


def _require_uri(value: object, owner: str) -> str:
    if type(value) is not str or not value or ":" not in value:
        raise ValueError(f"{owner} must be a non-empty absolute URI.")
    return value


def _require_text(value: object, owner: str) -> str:
    if type(value) is not str:
        raise TypeError(f"{owner} must be a string.")
    return value


def _require_position(value: object) -> tuple[int, int]:
    if type(value) is not dict:
        raise TypeError("position must be an object.")
    line = value.get("line")
    character = value.get("character")
    if type(line) is not int or isinstance(line, bool) or line < 0:
        raise ValueError("position.line must be a non-negative integer.")
    if type(character) is not int or isinstance(character, bool) or character < 0:
        raise ValueError("position.character must be a non-negative integer.")
    return line, character


def _utf16_units(value: str) -> int:
    return len(value.encode("utf-16-le")) // 2


def lsp_position_to_offset(text: str, position: Mapping[str, object]) -> int:
    """Convert one zero-based UTF-16 LSP position to a Python offset."""

    source = _require_text(text, "text")
    line, character = _require_position(position)

    line_start = 0
    current_line = 0
    while current_line < line:
        newline = source.find("\n", line_start)
        if newline < 0:
            raise ValueError(f"position.line {line} lies outside the document.")
        line_start = newline + 1
        current_line += 1

    newline = source.find("\n", line_start)
    line_end = len(source) if newline < 0 else newline
    if line_end > line_start and source[line_end - 1] == "\r":
        line_end -= 1

    units = 0
    offset = line_start
    while offset < line_end and units < character:
        width = _utf16_units(source[offset])
        if units + width > character:
            raise ValueError(
                "position.character splits a UTF-16 surrogate pair."
            )
        units += width
        offset += 1

    if units != character:
        raise ValueError(
            f"position.character {character} lies outside line {line}."
        )
    return offset


def _type_name(value: object) -> str:
    annotation = getattr(value, "type_annotation", None)
    name = getattr(annotation, "name", None)
    return name if type(name) is str and name else ""


def _function_label(node: FunctionNode) -> str:
    type_parameters = ""
    if node.type_parameters:
        rendered = []
        for parameter in node.type_parameters:
            constraints = tuple(
                str(constraint)
                for constraint in tuple(getattr(parameter, "constraints", ()) or ())
            )
            suffix = " : " + " & ".join(constraints) if constraints else ""
            rendered.append(f"{parameter.name}{suffix}")
        type_parameters = "<" + ", ".join(rendered) + ">"

    parameters = ", ".join(
        parameter.name
        + (f" : {_type_name(parameter)}" if _type_name(parameter) else "")
        for parameter in node.parameters
    )
    return_type = getattr(getattr(node, "return_type", None), "name", None)
    suffix = f" : {return_type}" if type(return_type) is str and return_type else ""
    return f"function {node.name}{type_parameters}({parameters}){suffix}"


def _name_offsets(text: str, span: object, name: str) -> Optional[tuple[int, int]]:
    if not isinstance(span, SourceSpan) or type(name) is not str or not name:
        return None
    start = text.find(name, span.start.offset, span.end.offset)
    if start < 0:
        return None
    return start, start + len(name)


def _entry(
    text: str,
    span: object,
    name: str,
    label: str,
    description: str,
) -> Optional[_HoverEntry]:
    offsets = _name_offsets(text, span, name)
    if offsets is None:
        return None
    return _HoverEntry(offsets[0], offsets[1], label, description)


def _append(values: list[_HoverEntry], item: Optional[_HoverEntry]) -> None:
    if item is not None:
        values.append(item)


def _function_entries(node: FunctionNode, text: str) -> tuple[_HoverEntry, ...]:
    values: list[_HoverEntry] = []
    _append(
        values,
        _entry(
            text,
            node.span,
            node.name,
            _function_label(node),
            "Pure ApexForge function declaration.",
        ),
    )
    for parameter in node.type_parameters:
        assert isinstance(parameter, TypeParameterNode)
        constraints = tuple(
            str(value)
            for value in tuple(getattr(parameter, "constraints", ()) or ())
        )
        suffix = " : " + " & ".join(constraints) if constraints else ""
        _append(
            values,
            _entry(
                text,
                parameter.span,
                parameter.name,
                f"type parameter {parameter.name}{suffix}",
                "Generic type parameter declared by this function.",
            ),
        )
    for parameter in node.parameters:
        assert isinstance(parameter, ParameterNode)
        type_name = _type_name(parameter)
        suffix = f" : {type_name}" if type_name else ""
        _append(
            values,
            _entry(
                text,
                parameter.span,
                parameter.name,
                f"parameter {parameter.name}{suffix}",
                "Function parameter.",
            ),
        )
    for binding in node.local_bindings:
        assert isinstance(binding, LetNode)
        _append(
            values,
            _entry(
                text,
                binding.span,
                binding.name,
                f"let {binding.name}",
                "Function-local immutable binding.",
            ),
        )
    return tuple(values)


def _directive_entries(node: DirectiveNode, text: str) -> tuple[_HoverEntry, ...]:
    values: list[_HoverEntry] = []
    _append(
        values,
        _entry(
            text,
            node.span,
            node.name,
            f"directive {node.name}",
            "ApexForge stateful directive declaration.",
        ),
    )
    for state in node.states:
        assert isinstance(state, StateNode)
        type_name = _type_name(state)
        suffix = f" : {type_name}" if type_name else ""
        _append(
            values,
            _entry(
                text,
                state.span,
                state.name,
                f"state {state.name}{suffix}",
                "Directive state declaration.",
            ),
        )
    for event in node.events:
        assert isinstance(event, EventNode)
        _append(
            values,
            _entry(
                text,
                event.span,
                event.name,
                f"event {event.name}",
                "Directive event declaration.",
            ),
        )
    for cause in node.causes:
        assert isinstance(cause, CauseNode)
        _append(
            values,
            _entry(
                text,
                cause.span,
                cause.name,
                f"cause {cause.name}",
                "Weighted causal branch declaration.",
            ),
        )
        for path in cause.paths:
            assert isinstance(path, PathNode)
            _append(
                values,
                _entry(
                    text,
                    path.span,
                    path.name,
                    f"path {path.name} @ {path.weight}",
                    "Weighted path within a cause.",
                ),
            )
    for requirement in node.requirements:
        assert isinstance(requirement, RequirementNode)
        _append(
            values,
            _entry(
                text,
                requirement.span,
                requirement.capability,
                f"requires {requirement.capability}",
                "Required capability reference.",
            ),
        )
    for authority in node.authorities:
        assert isinstance(authority, DirectiveAuthorityNode)
        _append(
            values,
            _entry(
                text,
                authority.span,
                authority.name,
                f"authority {authority.name}",
                "Authority reference attached to this directive.",
            ),
        )
    return tuple(values)


def _top_level_entries(node: object, text: str) -> tuple[_HoverEntry, ...]:
    if isinstance(node, FunctionNode):
        return _function_entries(node, text)
    if isinstance(node, DirectiveNode):
        return _directive_entries(node, text)

    values: list[_HoverEntry] = []
    if isinstance(node, WorkflowNode):
        _append(values, _entry(text, node.span, node.name, f"workflow {node.name}", "Workflow declaration."))
        for invocation in node.invocations:
            assert isinstance(invocation, WorkflowInvokeNode)
            _append(values, _entry(text, invocation.span, invocation.target, f"invoke {invocation.target}", "Workflow invocation target."))
    elif isinstance(node, AuthorityNode):
        suffix = f" extends {node.extends}" if node.extends else ""
        _append(values, _entry(text, node.span, node.name, f"authority {node.name}{suffix}", "Authority declaration."))
        for capability in node.capabilities:
            assert isinstance(capability, CapabilityNode)
            _append(values, _entry(text, capability.span, capability.name, f"capability {capability.name}", "Capability declared by this authority."))
    elif isinstance(node, RoleNode):
        _append(values, _entry(text, node.span, node.name, f"role {node.name}", "Role declaration."))
        for authority in node.authorities:
            assert isinstance(authority, RoleAuthorityNode)
            _append(values, _entry(text, authority.span, authority.name, f"authority {authority.name}", "Authority reference attached to this role."))
    elif isinstance(node, PrincipalNode):
        _append(values, _entry(text, node.span, node.name, f"principal {node.name}", "Principal declaration."))
        for authority in node.authorities:
            assert isinstance(authority, PrincipalAuthorityNode)
            _append(values, _entry(text, authority.span, authority.name, f"authority {authority.name}", "Authority reference attached to this principal."))
        for role in node.roles:
            assert isinstance(role, PrincipalRoleNode)
            _append(values, _entry(text, role.span, role.name, f"role {role.name}", "Role reference attached to this principal."))
    return tuple(values)


def _module_entries(
    module_source: ModuleSource,
    text: str,
) -> tuple[_HoverEntry, ...]:
    values: list[_HoverEntry] = []
    if module_source.module_name is not None:
        _append(
            values,
            _entry(
                text,
                module_source.module_span,
                module_source.module_name,
                f"module {module_source.module_name}",
                "ApexForge source module declaration.",
            ),
        )
    for dependency in module_source.imports:
        _append(
            values,
            _entry(
                text,
                dependency.span,
                dependency.name,
                f"import {dependency.name}",
                "Direct module import.",
            ),
        )
    return tuple(values)


def _hover_entries(uri: str, text: str) -> tuple[_HoverEntry, ...]:
    try:
        module_source = parse_module_source(uri, text)
        node = parse(module_source.masked_source, source_name=uri)
    except Exception as error:
        if diagnostics_from_exception(error):
            return ()
        raise

    values = [*_module_entries(module_source, text), *_top_level_entries(node, text)]
    return tuple(sorted(values, key=lambda item: (item.start, item.end, item.label)))


def _hover_result(text: str, entry: _HoverEntry) -> dict[str, object]:
    markdown = (
        "```apexforge\n"
        + entry.label
        + "\n```\n\n"
        + entry.description
    )
    return {
        "contents": {
            "kind": HOVER_MARKUP_KIND,
            "value": markdown,
        },
        "range": {
            "start": offset_to_lsp_position(text, entry.start),
            "end": offset_to_lsp_position(text, entry.end),
        },
    }


def hover(
    uri: str,
    text: str,
    position: Mapping[str, object],
) -> Optional[dict[str, object]]:
    """Return syntax-level hover information for one open document position."""

    selected_uri = _require_uri(uri, "uri")
    source = _require_text(text, "text")
    offset = lsp_position_to_offset(source, position)

    candidates = tuple(
        entry
        for entry in _hover_entries(selected_uri, source)
        if entry.start <= offset < entry.end
    )
    if not candidates:
        return None
    selected = min(candidates, key=lambda item: (item.end - item.start, item.start, item.label))
    return _hover_result(source, selected)


def hover_contract() -> dict[str, object]:
    return {
        "schema": HOVER_SCHEMA,
        "kind": HOVER_KIND,
        "hover_version": P10_T4_HOVER_VERSION,
        "method": HOVER_METHOD,
        "result": "Hover | null",
        "contents": "MarkupContent(markdown)",
        "position_encoding": "utf-16",
        "pipeline": (
            "module_headers",
            "lexer",
            "parser",
        ),
        "scope": "open documents",
        "selection": "declaration and nested-member name ranges",
        "invalid_source": "null; diagnostics remain T4.2 responsibility",
        "unmatched_position": "null",
        "semantic_depth": "syntax-level only",
        "features_deferred": (
            "completion",
            "definition",
            "references",
            "rename",
            "workspace_symbols",
            "formatting",
            "cross_file_resolution",
            "type_inference",
        ),
    }


def hover_fingerprint() -> str:
    payload = json.dumps(
        hover_contract(),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


CANONICAL_HOVER_SHA256: Final[str] = "c3038a06ccd7edc573571df165063d7d2eefb471748f23c40e80b4bc7b6a6e94"


__all__ = (
    "CANONICAL_HOVER_SHA256",
    "HOVER_KIND",
    "HOVER_MARKUP_KIND",
    "HOVER_METHOD",
    "HOVER_SCHEMA",
    "P10_T4_HOVER_VERSION",
    "hover",
    "hover_contract",
    "hover_fingerprint",
    "lsp_position_to_offset",
)
