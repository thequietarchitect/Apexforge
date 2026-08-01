"""AFP-P10-T4.10 deterministic whole-document ApexForge formatting.

The formatter validates source through the frozen module-header and parser
pipeline, prints the resulting syntax tree without semantic reordering, and
returns at most one full-document LSP TextEdit. Invalid or already canonical
source returns no edits. Range formatting and format-on-type are deferred.
"""
from __future__ import annotations

from decimal import Decimal
import hashlib
import json
from typing import Final, Iterable, Mapping, Optional

from language.diagnostics import diagnostics_from_exception
from language.modules import ModuleSource, parse_module_source
from language.parser import (
    AddActionNode, AuthorityNode, BinaryExpressionNode, BooleanLiteralNode,
    CallExpressionNode, CapabilityNode, CauseNode, DirectiveAuthorityNode,
    DirectiveNode, EmitActionNode, EventNode, FloatLiteralNode, FunctionNode,
    FunctionWhenNode, IdentifierNode, IntegerLiteralNode, InvokeActionNode,
    LetNode, MessageActionNode, ParameterNode, PathNode, PrincipalAuthorityNode,
    PrincipalNode, PrincipalRoleNode, RequirementNode, ReturnNode,
    RoleAuthorityNode, RoleNode, SetActionNode, StateNode, StringLiteralNode,
    TypeAnnotationNode, TypeParameterNode, UnaryExpressionNode, WhenActionNode,
    WorkflowInvokeNode, WorkflowNode, parse,
)
from language_server.diagnostics import offset_to_lsp_position

P10_T4_FORMATTING_VERSION: Final[str] = "10-T4.10"
FORMATTING_SCHEMA: Final[int] = 1
FORMATTING_KIND: Final[str] = "apexforge.language-server-formatting"
FORMATTING_METHOD: Final[str] = "textDocument/formatting"
DEFAULT_TAB_SIZE: Final[int] = 4
MAX_TAB_SIZE: Final[int] = 16


def _require_uri(value: object, owner: str) -> str:
    if type(value) is not str or not value or ":" not in value:
        raise ValueError(f"{owner} must be a non-empty absolute URI.")
    return value


def _require_text(value: object, owner: str) -> str:
    if type(value) is not str:
        raise TypeError(f"{owner} must be a string.")
    return value


def _indent_unit(options: Mapping[str, object]) -> str:
    if type(options) is not dict:
        raise TypeError("formatting options must be an object.")
    tab_size = options.get("tabSize", DEFAULT_TAB_SIZE)
    insert_spaces = options.get("insertSpaces", True)
    if type(tab_size) is not int or isinstance(tab_size, bool) or not (1 <= tab_size <= MAX_TAB_SIZE):
        raise ValueError(f"formatting options.tabSize must be within 1..{MAX_TAB_SIZE}.")
    if type(insert_spaces) is not bool:
        raise TypeError("formatting options.insertSpaces must be a boolean.")
    return " " * tab_size if insert_spaces else "\t"


def _constraint_name(value: object) -> str:
    name = getattr(value, "name", None)
    if type(name) is str and name:
        return name
    text = str(value)
    return text.split(".")[-1]


def _type_name(value: Optional[TypeAnnotationNode]) -> str:
    if value is None:
        return ""
    name = getattr(value, "name", None)
    if type(name) is str and name:
        return name
    apex_type = getattr(value, "apex_type", None)
    fallback = getattr(apex_type, "name", None)
    if type(fallback) is str and fallback:
        return fallback
    raise ValueError("Type annotation has no printable name.")


def _string_literal(value: str) -> str:
    escaped = (value.replace("\\", "\\\\").replace('"', '\\"')
               .replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t"))
    return f'"{escaped}"'


def _float_literal(value: float) -> str:
    text = format(Decimal(repr(value)), "f")
    if "." not in text:
        text += ".0"
    return text


_PRECEDENCE: Final[Mapping[str, int]] = {
    "or": 1, "and": 2, "==": 3, "!=": 3,
    "<": 4, "<=": 4, ">": 4, ">=": 4,
    "+": 5, "-": 5, "*": 6, "/": 6, "%": 6,
}


def _expression(node: object, parent_precedence: int = 0, *, right_child: bool = False) -> str:
    if isinstance(node, IntegerLiteralNode): return str(node.value)
    if isinstance(node, FloatLiteralNode): return _float_literal(node.value)
    if isinstance(node, StringLiteralNode): return _string_literal(node.value)
    if isinstance(node, BooleanLiteralNode): return "true" if node.value else "false"
    if isinstance(node, IdentifierNode): return node.name
    if isinstance(node, CallExpressionNode):
        types = tuple(getattr(node, "type_arguments", ()) or ())
        generic = "<" + ", ".join(_type_name(item) for item in types) + ">" if types else ""
        return node.target + generic + "(" + ", ".join(_expression(item) for item in node.arguments) + ")"
    if isinstance(node, UnaryExpressionNode):
        rendered = _expression(node.operand, 7)
        return ("not " if node.operator == "not" else node.operator) + rendered
    if isinstance(node, BinaryExpressionNode):
        precedence = _PRECEDENCE[node.operator]
        left = _expression(node.left, precedence)
        right = _expression(node.right, precedence, right_child=True)
        rendered = f"{left} {node.operator} {right}"
        if precedence < parent_precedence or (right_child and precedence == parent_precedence):
            return f"({rendered})"
        return rendered
    raise TypeError(f"Unsupported expression node {type(node).__name__}.")


def _source_order(values: Iterable[object]) -> tuple[object, ...]:
    def key(item: object) -> tuple[int, str]:
        span = getattr(item, "span", None)
        start = getattr(getattr(span, "start", None), "offset", 2**63 - 1)
        return int(start), type(item).__name__
    return tuple(sorted(tuple(values), key=key))


class _Printer:
    def __init__(self, indent: str) -> None:
        self.indent = indent
        self.lines: list[str] = []

    def line(self, depth: int, text: str = "") -> None:
        self.lines.append(self.indent * depth + text if text else "")

    def block(self, depth: int, header: str, items: Iterable[object], writer) -> None:
        self.line(depth, header + " {")
        for item in items: writer(item, depth + 1)
        self.line(depth, "}")

    def function_statement(self, item: object, depth: int) -> None:
        if isinstance(item, LetNode): self.line(depth, f"let {item.name} = {_expression(item.expression)}"); return
        if isinstance(item, ReturnNode): self.line(depth, f"return {_expression(item.expression)}"); return
        if isinstance(item, FunctionWhenNode):
            self.line(depth, f"when {_expression(item.condition)} {{")
            for child in item.actions: self.function_statement(child, depth + 1)
            if item.otherwise_actions:
                self.line(depth, "} otherwise {")
                for child in item.otherwise_actions: self.function_statement(child, depth + 1)
            self.line(depth, "}"); return
        raise TypeError(f"Unsupported function statement {type(item).__name__}.")

    def action(self, item: object, depth: int) -> None:
        if isinstance(item, AddActionNode): self.line(depth, f"add {item.state_name} {_expression(item.value)}"); return
        if isinstance(item, SetActionNode): self.line(depth, f"set {item.state_name} = {_expression(item.expression)}"); return
        if isinstance(item, EmitActionNode): self.line(depth, f"emit {item.event_name}"); return
        if isinstance(item, MessageActionNode): self.line(depth, f"message {_expression(item.expression)}"); return
        if isinstance(item, InvokeActionNode): self.line(depth, f"invoke {item.target}"); return
        if isinstance(item, WhenActionNode):
            self.line(depth, f"when {_expression(item.condition)} {{")
            for child in item.actions: self.action(child, depth + 1)
            if item.otherwise_actions:
                self.line(depth, "} otherwise {")
                for child in item.otherwise_actions: self.action(child, depth + 1)
            self.line(depth, "}"); return
        raise TypeError(f"Unsupported path action {type(item).__name__}.")

    def path(self, item: PathNode, depth: int) -> None:
        self.line(depth, f"path {item.name} @ {item.weight} {{")
        for action in item.actions: self.action(action, depth + 1)
        self.line(depth, "}")

    def top_level(self, node: object) -> None:
        if isinstance(node, FunctionNode):
            type_parameters = ""
            if node.type_parameters:
                rendered=[]
                for item in node.type_parameters:
                    constraints=tuple(getattr(item,"constraints",()) or ())
                    if len(constraints) > 1:
                        raise ValueError("ApexForge type parameters support at most one constraint.")
                    suffix=" : " + _constraint_name(constraints[0]) if constraints else ""
                    rendered.append(item.name + suffix)
                type_parameters="<" + ", ".join(rendered) + ">"
            parameters=[]
            for item in node.parameters:
                suffix=f" : {_type_name(item.type_annotation)}" if item.type_annotation is not None else ""
                parameters.append(item.name + suffix)
            return_suffix=f" : {_type_name(node.return_type)}" if node.return_type is not None else ""
            self.line(0, f"function {node.name}{type_parameters}({', '.join(parameters)}){return_suffix} {{")
            body=tuple(getattr(node,"body",()) or ())
            if not body:
                body=tuple(getattr(node,"local_bindings",()) or ()) + (node.return_statement,)
            for item in body: self.function_statement(item,1)
            self.line(0,"}"); return
        if isinstance(node, DirectiveNode):
            self.line(0, f"directive {node.name} {{")
            members=_source_order((*node.states,*node.events,*node.authorities,*node.requirements,*node.causes))
            for item in members:
                if isinstance(item, StateNode):
                    type_suffix=f" : {_type_name(item.type_annotation)}" if item.type_annotation is not None else ""
                    self.line(1, f"state {item.name}{type_suffix} = {_expression(item.initial)}")
                elif isinstance(item, EventNode): self.line(1, f"event {item.name}")
                elif isinstance(item, DirectiveAuthorityNode): self.line(1, f"authority {item.name}")
                elif isinstance(item, RequirementNode): self.line(1, f"requires {item.capability}")
                elif isinstance(item, CauseNode):
                    self.line(1, f"cause {item.name} {{")
                    for path in item.paths: self.path(path,2)
                    self.line(1,"}")
            self.line(0,"}"); return
        if isinstance(node, WorkflowNode):
            self.line(0, f"workflow {node.name} {{")
            for item in node.invocations: self.line(1, f"invoke {item.target}")
            self.line(0,"}"); return
        if isinstance(node, AuthorityNode):
            suffix=f" extends {node.extends}" if node.extends else ""
            self.line(0, f"authority {node.name}{suffix} {{")
            for item in node.capabilities: self.line(1, f"capability {item.name}")
            self.line(0,"}"); return
        if isinstance(node, RoleNode):
            self.line(0, f"role {node.name} {{")
            for item in node.authorities: self.line(1, f"authority {item.name}")
            self.line(0,"}"); return
        if isinstance(node, PrincipalNode):
            self.line(0, f"principal {node.name} {{")
            for item in _source_order((*node.authorities,*node.roles)):
                if isinstance(item, PrincipalAuthorityNode): self.line(1, f"authority {item.name}")
                elif isinstance(item, PrincipalRoleNode): self.line(1, f"role {item.name}")
            self.line(0,"}"); return
        raise TypeError(f"Unsupported top-level node {type(node).__name__}.")


def _formatted_text(uri: str, text: str, options: Mapping[str, object]) -> Optional[str]:
    try:
        module_source = parse_module_source(uri, text)
        node = parse(module_source.masked_source, source_name=uri)
    except Exception as error:
        if diagnostics_from_exception(error): return None
        raise
    printer = _Printer(_indent_unit(options))
    if module_source.module_name is not None:
        printer.line(0, f"module {module_source.module_name}")
        for dependency in module_source.imports: printer.line(0, f"import {dependency.name}")
        printer.line(0)
    printer.top_level(node)
    return "\n".join(printer.lines).rstrip() + "\n"


def format_document(uri: str, text: str, options: Mapping[str, object]) -> tuple[dict[str, object], ...]:
    selected_uri=_require_uri(uri,"uri"); source=_require_text(text,"text")
    formatted=_formatted_text(selected_uri,source,options)
    if formatted is None or formatted == source: return ()
    return ({"range":{"start":{"line":0,"character":0},"end":offset_to_lsp_position(source,len(source))},"newText":formatted},)


def formatting_contract() -> Mapping[str, object]:
    return {'schema': 1, 'kind': 'apexforge.language-server-formatting', 'formatting_version': '10-T4.10', 'method': 'textDocument/formatting', 'document_scope': 'whole document', 'result': 'TextEdit[]', 'position_encoding': 'utf-16', 'syntax_source': 'frozen module-header and parser AST', 'style': {'line_ending': 'LF', 'terminal_newline': True, 'brace_style': 'same-line opening; own-line closing; joined otherwise', 'operator_spacing': 'single spaces around binary operators', 'type_spacing': 'single spaces around colon', 'comma_spacing': 'comma followed by one space', 'header_spacing': 'one blank line between headers and declaration', 'indentation': 'client tabSize and insertSpaces'}, 'invalid_source': 'no edits', 'idempotent_source': 'no edits', 'features_deferred': ('range_formatting', 'format_on_type', 'format_on_save_policy', 'semantic_rewrites')}


def formatting_fingerprint() -> str:
    payload=json.dumps(formatting_contract(),ensure_ascii=False,separators=(",",":"),sort_keys=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()

CANONICAL_FORMATTING_SHA256: Final[str] = "63ac984979dd14832dd7d69490176a6e877c867c00c30116636d6c6e5fef3e4b"

__all__=("CANONICAL_FORMATTING_SHA256","DEFAULT_TAB_SIZE","FORMATTING_KIND","FORMATTING_METHOD","FORMATTING_SCHEMA","MAX_TAB_SIZE","P10_T4_FORMATTING_VERSION","format_document","formatting_contract","formatting_fingerprint")
