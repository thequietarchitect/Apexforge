"""AFP-P10-T4.4 ApexForge document-symbol analysis.

The analyzer reuses the frozen module-header and parser pipeline to project one
open ApexForge source document into hierarchical Language Server Protocol
``DocumentSymbol`` values. It performs no compilation, linking, validation, or
runtime execution.
"""

from __future__ import annotations

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
from language_server.diagnostics import offset_to_lsp_position, span_to_lsp_range


P10_T4_DOCUMENT_SYMBOL_VERSION: Final[str] = "10-T4.4"
DOCUMENT_SYMBOL_SCHEMA: Final[int] = 1
DOCUMENT_SYMBOL_KIND: Final[str] = "apexforge.language-server-document-symbols"
DOCUMENT_SYMBOL_METHOD: Final[str] = "textDocument/documentSymbol"

# LSP 3.18 SymbolKind values.
SYMBOL_KIND_FILE: Final[int] = 1
SYMBOL_KIND_MODULE: Final[int] = 2
SYMBOL_KIND_CLASS: Final[int] = 5
SYMBOL_KIND_METHOD: Final[int] = 6
SYMBOL_KIND_FIELD: Final[int] = 8
SYMBOL_KIND_INTERFACE: Final[int] = 11
SYMBOL_KIND_FUNCTION: Final[int] = 12
SYMBOL_KIND_VARIABLE: Final[int] = 13
SYMBOL_KIND_OBJECT: Final[int] = 19
SYMBOL_KIND_KEY: Final[int] = 20
SYMBOL_KIND_EVENT: Final[int] = 24
SYMBOL_KIND_TYPE_PARAMETER: Final[int] = 26
SYMBOL_KIND_STRUCT: Final[int] = 23


def _require_uri(value: object, owner: str) -> str:
    if type(value) is not str or not value or ":" not in value:
        raise ValueError(f"{owner} must be a non-empty absolute URI.")
    return value


def _require_text(value: object, owner: str) -> str:
    if type(value) is not str:
        raise TypeError(f"{owner} must be a string.")
    return value


def _span_start(value: object) -> int:
    span = getattr(value, "span", None)
    return span.start.offset if isinstance(span, SourceSpan) else 2**63 - 1


def _sorted_by_source(values: Iterable[object]) -> tuple[object, ...]:
    return tuple(sorted(tuple(values), key=_span_start))


def _type_name(value: object) -> str:
    annotation = getattr(value, "type_annotation", None)
    name = getattr(annotation, "name", None)
    return name if type(name) is str and name else ""


def _function_detail(node: FunctionNode) -> str:
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
    return f"function{type_parameters}({parameters}){suffix}"


def _full_range(
    text: str,
    start_span: SourceSpan,
    end_span: Optional[SourceSpan],
) -> dict[str, object]:
    end_offset = (
        end_span.end.offset
        if isinstance(end_span, SourceSpan)
        else start_span.end.offset
    )
    return {
        "start": offset_to_lsp_position(text, start_span.start.offset),
        "end": offset_to_lsp_position(text, end_offset),
    }


def _name_range(
    text: str,
    span: SourceSpan,
    name: str,
) -> dict[str, object]:
    start = text.find(name, span.start.offset, span.end.offset)
    if start < 0:
        return span_to_lsp_range(text, span)
    end = start + len(name)
    return {
        "start": offset_to_lsp_position(text, start),
        "end": offset_to_lsp_position(text, end),
    }


def _document_symbol(
    *,
    name: str,
    detail: str,
    kind: int,
    text: str,
    span: Optional[SourceSpan],
    selection_span: Optional[SourceSpan] = None,
    children: Iterable[Mapping[str, object]] = (),
    range_override: Optional[Mapping[str, object]] = None,
) -> Optional[dict[str, object]]:
    if type(name) is not str or not name or not isinstance(span, SourceSpan):
        return None

    child_values = tuple(dict(item) for item in children)
    value: dict[str, object] = {
        "name": name,
        "detail": detail,
        "kind": kind,
        "range": (
            dict(range_override)
            if range_override is not None
            else span_to_lsp_range(text, span)
        ),
        "selectionRange": (
            span_to_lsp_range(text, selection_span)
            if isinstance(selection_span, SourceSpan)
            else _name_range(text, span, name)
        ),
    }
    if child_values:
        value["children"] = list(child_values)
    return value


def _leaf(
    node: object,
    *,
    name: str,
    detail: str,
    kind: int,
    text: str,
) -> Optional[dict[str, object]]:
    return _document_symbol(
        name=name,
        detail=detail,
        kind=kind,
        text=text,
        span=getattr(node, "span", None),
    )


def _function_children(node: FunctionNode, text: str) -> tuple[dict[str, object], ...]:
    values: list[dict[str, object]] = []
    for item in _sorted_by_source(
        (*node.type_parameters, *node.parameters, *node.local_bindings)
    ):
        symbol: Optional[dict[str, object]]
        if isinstance(item, TypeParameterNode):
            constraints = tuple(
                str(value)
                for value in tuple(getattr(item, "constraints", ()) or ())
            )
            detail = (
                "type parameter : " + " & ".join(constraints)
                if constraints
                else "type parameter"
            )
            symbol = _leaf(
                item,
                name=item.name,
                detail=detail,
                kind=SYMBOL_KIND_TYPE_PARAMETER,
                text=text,
            )
        elif isinstance(item, ParameterNode):
            type_name = _type_name(item)
            symbol = _leaf(
                item,
                name=item.name,
                detail=f"parameter : {type_name}" if type_name else "parameter",
                kind=SYMBOL_KIND_VARIABLE,
                text=text,
            )
        else:
            assert isinstance(item, LetNode)
            symbol = _leaf(
                item,
                name=item.name,
                detail="local binding",
                kind=SYMBOL_KIND_VARIABLE,
                text=text,
            )
        if symbol is not None:
            values.append(symbol)
    return tuple(values)


def _cause_symbol(node: CauseNode, text: str) -> Optional[dict[str, object]]:
    children = []
    for path in _sorted_by_source(node.paths):
        assert isinstance(path, PathNode)
        symbol = _leaf(
            path,
            name=path.name,
            detail=f"path @ {path.weight}",
            kind=SYMBOL_KIND_METHOD,
            text=text,
        )
        if symbol is not None:
            children.append(symbol)
    return _document_symbol(
        name=node.name,
        detail="cause",
        kind=SYMBOL_KIND_METHOD,
        text=text,
        span=node.span,
        children=children,
    )


def _directive_children(node: DirectiveNode, text: str) -> tuple[dict[str, object], ...]:
    items = _sorted_by_source(
        (
            *node.states,
            *node.events,
            *node.causes,
            *node.requirements,
            *node.authorities,
        )
    )
    values: list[dict[str, object]] = []
    for item in items:
        symbol: Optional[dict[str, object]]
        if isinstance(item, StateNode):
            type_name = _type_name(item)
            symbol = _leaf(
                item,
                name=item.name,
                detail=f"state : {type_name}" if type_name else "state",
                kind=SYMBOL_KIND_FIELD,
                text=text,
            )
        elif isinstance(item, EventNode):
            symbol = _leaf(
                item,
                name=item.name,
                detail="event",
                kind=SYMBOL_KIND_EVENT,
                text=text,
            )
        elif isinstance(item, CauseNode):
            symbol = _cause_symbol(item, text)
        elif isinstance(item, RequirementNode):
            symbol = _leaf(
                item,
                name=item.capability,
                detail="required capability",
                kind=SYMBOL_KIND_KEY,
                text=text,
            )
        else:
            assert isinstance(item, DirectiveAuthorityNode)
            symbol = _leaf(
                item,
                name=item.name,
                detail="authority reference",
                kind=SYMBOL_KIND_INTERFACE,
                text=text,
            )
        if symbol is not None:
            values.append(symbol)
    return tuple(values)


def _top_level_symbol(node: object, text: str) -> Optional[dict[str, object]]:
    if isinstance(node, FunctionNode):
        return _document_symbol(
            name=node.name,
            detail=_function_detail(node),
            kind=SYMBOL_KIND_FUNCTION,
            text=text,
            span=node.span,
            children=_function_children(node, text),
        )
    if isinstance(node, DirectiveNode):
        return _document_symbol(
            name=node.name,
            detail="directive",
            kind=SYMBOL_KIND_OBJECT,
            text=text,
            span=node.span,
            children=_directive_children(node, text),
        )
    if isinstance(node, WorkflowNode):
        children = []
        for invocation in _sorted_by_source(node.invocations):
            assert isinstance(invocation, WorkflowInvokeNode)
            symbol = _leaf(
                invocation,
                name=invocation.target,
                detail="invoke",
                kind=SYMBOL_KIND_FUNCTION,
                text=text,
            )
            if symbol is not None:
                children.append(symbol)
        return _document_symbol(
            name=node.name,
            detail="workflow",
            kind=SYMBOL_KIND_EVENT,
            text=text,
            span=node.span,
            children=children,
        )
    if isinstance(node, AuthorityNode):
        children = []
        for capability in _sorted_by_source(node.capabilities):
            assert isinstance(capability, CapabilityNode)
            symbol = _leaf(
                capability,
                name=capability.name,
                detail="capability",
                kind=SYMBOL_KIND_KEY,
                text=text,
            )
            if symbol is not None:
                children.append(symbol)
        detail = "authority"
        if node.extends:
            detail += f" extends {node.extends}"
        return _document_symbol(
            name=node.name,
            detail=detail,
            kind=SYMBOL_KIND_INTERFACE,
            text=text,
            span=node.span,
            children=children,
        )
    if isinstance(node, RoleNode):
        children = []
        for authority in _sorted_by_source(node.authorities):
            assert isinstance(authority, RoleAuthorityNode)
            symbol = _leaf(
                authority,
                name=authority.name,
                detail="authority reference",
                kind=SYMBOL_KIND_INTERFACE,
                text=text,
            )
            if symbol is not None:
                children.append(symbol)
        return _document_symbol(
            name=node.name,
            detail="role",
            kind=SYMBOL_KIND_STRUCT,
            text=text,
            span=node.span,
            children=children,
        )
    if isinstance(node, PrincipalNode):
        items = _sorted_by_source((*node.authorities, *node.roles))
        children = []
        for item in items:
            if isinstance(item, PrincipalAuthorityNode):
                detail = "authority reference"
                kind = SYMBOL_KIND_INTERFACE
            else:
                assert isinstance(item, PrincipalRoleNode)
                detail = "role reference"
                kind = SYMBOL_KIND_STRUCT
            symbol = _leaf(
                item,
                name=item.name,
                detail=detail,
                kind=kind,
                text=text,
            )
            if symbol is not None:
                children.append(symbol)
        return _document_symbol(
            name=node.name,
            detail="principal",
            kind=SYMBOL_KIND_CLASS,
            text=text,
            span=node.span,
            children=children,
        )
    return None


def _module_symbol(
    module_source: ModuleSource,
    node: object,
    text: str,
    declaration: Mapping[str, object],
) -> Optional[dict[str, object]]:
    if module_source.module_name is None or module_source.module_span is None:
        return None

    children: list[dict[str, object]] = []
    for dependency in module_source.imports:
        symbol = _document_symbol(
            name=dependency.name,
            detail="import",
            kind=SYMBOL_KIND_MODULE,
            text=text,
            span=dependency.span,
        )
        if symbol is not None:
            children.append(symbol)
    children.append(dict(declaration))

    return _document_symbol(
        name=module_source.module_name,
        detail="module",
        kind=SYMBOL_KIND_MODULE,
        text=text,
        span=module_source.module_span,
        selection_span=module_source.module_span,
        children=children,
        range_override=_full_range(
            text,
            module_source.module_span,
            getattr(node, "span", None),
        ),
    )


def document_symbols(uri: str, text: str) -> tuple[dict[str, object], ...]:
    """Return hierarchical symbols for one syntactically valid open document.

    A syntax failure returns an empty result because T4.2 already publishes the
    canonical error diagnostics for that document.
    """

    selected_uri = _require_uri(uri, "uri")
    source = _require_text(text, "text")

    try:
        module_source = parse_module_source(selected_uri, source)
        node = parse(module_source.masked_source, source_name=selected_uri)
    except Exception as error:
        if diagnostics_from_exception(error):
            return ()
        raise

    declaration = _top_level_symbol(node, source)
    if declaration is None:
        return ()

    module = _module_symbol(module_source, node, source, declaration)
    return (module,) if module is not None else (declaration,)


def document_symbols_contract() -> dict[str, object]:
    return {
        "schema": DOCUMENT_SYMBOL_SCHEMA,
        "kind": DOCUMENT_SYMBOL_KIND,
        "document_symbol_version": P10_T4_DOCUMENT_SYMBOL_VERSION,
        "method": DOCUMENT_SYMBOL_METHOD,
        "result": "DocumentSymbol[]",
        "position_encoding": "utf-16",
        "pipeline": (
            "module_headers",
            "lexer",
            "parser",
        ),
        "scope": "open documents",
        "hierarchical": True,
        "module_root": "explicit modules only",
        "invalid_source": "empty result; diagnostics remain T4.2 responsibility",
        "top_level": (
            "function",
            "directive",
            "workflow",
            "authority",
            "principal",
            "role",
        ),
        "nested": (
            "type_parameter",
            "parameter",
            "local_binding",
            "state",
            "event",
            "cause",
            "path",
            "capability",
            "requirement",
            "authority_reference",
            "role_reference",
            "workflow_invocation",
        ),
        "features_deferred": (
            "workspace_symbols",
            "completion",
            "hover",
            "definition",
            "references",
            "rename",
            "formatting",
        ),
    }


def document_symbols_fingerprint() -> str:
    payload = json.dumps(
        document_symbols_contract(),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


CANONICAL_DOCUMENT_SYMBOLS_SHA256: Final[str] = "f4c337b1bbaab80093bb765323e27d3583609e4e0e229685a4aad9b82153484e"


__all__ = (
    "CANONICAL_DOCUMENT_SYMBOLS_SHA256",
    "DOCUMENT_SYMBOL_KIND",
    "DOCUMENT_SYMBOL_METHOD",
    "DOCUMENT_SYMBOL_SCHEMA",
    "P10_T4_DOCUMENT_SYMBOL_VERSION",
    "SYMBOL_KIND_CLASS",
    "SYMBOL_KIND_EVENT",
    "SYMBOL_KIND_FIELD",
    "SYMBOL_KIND_FUNCTION",
    "SYMBOL_KIND_INTERFACE",
    "SYMBOL_KIND_KEY",
    "SYMBOL_KIND_METHOD",
    "SYMBOL_KIND_MODULE",
    "SYMBOL_KIND_OBJECT",
    "SYMBOL_KIND_STRUCT",
    "SYMBOL_KIND_TYPE_PARAMETER",
    "SYMBOL_KIND_VARIABLE",
    "document_symbols",
    "document_symbols_contract",
    "document_symbols_fingerprint",
)
