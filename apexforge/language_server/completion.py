"""AFP-P10-T4.6 ApexForge context-aware completion.

The analyzer provides deterministic open-document completion from tolerant lexical
context plus best-effort parsing of the current source snapshot. It performs no
project build, linking, cross-file lookup, runtime execution, or type inference.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re
from typing import Final, Iterable, Mapping, Optional

from language.diagnostics import diagnostics_from_exception
from language.modules import parse_module_source
from language.parser import DirectiveNode, FunctionNode, LetNode, parse_source_unit
from language_server.diagnostics import offset_to_lsp_position
from language_server.hover import lsp_position_to_offset
from type_system.model import BUILTIN_TYPES


P10_T4_COMPLETION_VERSION: Final[str] = "10-T4.6"
COMPLETION_SCHEMA: Final[int] = 1
COMPLETION_KIND: Final[str] = "apexforge.language-server-completion"
COMPLETION_METHOD: Final[str] = "textDocument/completion"
COMPLETION_TRIGGER_CHARACTERS: Final[tuple[str, ...]] = ("@", ":")

LSP_COMPLETION_FUNCTION: Final[int] = 3
LSP_COMPLETION_FIELD: Final[int] = 5
LSP_COMPLETION_VARIABLE: Final[int] = 6
LSP_COMPLETION_MODULE: Final[int] = 9
LSP_COMPLETION_VALUE: Final[int] = 12
LSP_COMPLETION_KEYWORD: Final[int] = 14
LSP_COMPLETION_REFERENCE: Final[int] = 18
LSP_COMPLETION_EVENT: Final[int] = 23
LSP_COMPLETION_TYPE_PARAMETER: Final[int] = 25

_IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")

_TOP_LEVEL_KEYWORDS: Final[tuple[str, ...]] = (
    "module",
    "import",
    "function",
    "directive",
    "workflow",
    "authority",
    "role",
    "principal",
)
_DIRECTIVE_KEYWORDS: Final[tuple[str, ...]] = (
    "state",
    "event",
    "cause",
    "requires",
    "authority",
)
_ACTION_KEYWORDS: Final[tuple[str, ...]] = (
    "add",
    "set",
    "emit",
    "message",
    "invoke",
    "when",
)
_FUNCTION_KEYWORDS: Final[tuple[str, ...]] = (
    "let",
    "return",
    "when",
)
_LITERAL_KEYWORDS: Final[tuple[str, ...]] = (
    "true",
    "false",
)
_BLOCK_STARTERS: Final[frozenset[str]] = frozenset(
    {
        "function",
        "directive",
        "workflow",
        "authority",
        "role",
        "principal",
        "cause",
        "path",
        "when",
        "otherwise",
    }
)

_KEYWORD_DOCUMENTATION: Final[Mapping[str, str]] = {
    "module": "Declare the source module name.",
    "import": "Import a directly visible ApexForge module.",
    "function": "Declare a pure ApexForge function.",
    "directive": "Declare a stateful ApexForge directive.",
    "workflow": "Declare an ordered workflow.",
    "authority": "Declare or reference an authority.",
    "role": "Declare or reference a role.",
    "principal": "Declare a principal.",
    "state": "Declare directive state.",
    "event": "Declare a directive event.",
    "cause": "Declare a weighted causal branch.",
    "requires": "Reference a required capability.",
    "path": "Declare a weighted path inside a cause.",
    "capability": "Declare an authority capability.",
    "extends": "Declare the parent authority.",
    "invoke": "Invoke a directive or workflow target.",
    "add": "Add a value to directive state.",
    "set": "Assign a value to directive state.",
    "emit": "Emit a directive event.",
    "message": "Evaluate a message expression.",
    "when": "Begin a conditional branch.",
    "otherwise": "Begin the fallback branch.",
    "let": "Declare an immutable function-local binding.",
    "return": "Return a function result.",
    "true": "Boolean true literal.",
    "false": "Boolean false literal.",
}


@dataclass(frozen=True, order=True)
class _Token:
    start: int
    end: int
    kind: str
    value: str


@dataclass(frozen=True)
class _Inventory:
    type_parameters: tuple[str, ...] = ()
    parameters: tuple[str, ...] = ()
    local_bindings: tuple[str, ...] = ()
    states: tuple[str, ...] = ()
    events: tuple[str, ...] = ()


@dataclass(frozen=True, order=True)
class _Candidate:
    rank: int
    label: str
    kind: int
    detail: str
    documentation: str


def _require_uri(value: object, owner: str) -> str:
    if type(value) is not str or not value or ":" not in value:
        raise ValueError(f"{owner} must be a non-empty absolute URI.")
    return value


def _require_text(value: object, owner: str) -> str:
    if type(value) is not str:
        raise TypeError(f"{owner} must be a string.")
    return value


def _identifier_prefix(text: str, offset: int) -> tuple[int, str]:
    start = offset
    while start > 0:
        character = text[start - 1]
        if character == "_" or character.isalnum():
            start -= 1
            continue
        break
    return start, text[start:offset]


def _scan(text: str) -> tuple[tuple[_Token, ...], bool]:
    tokens: list[_Token] = []
    index = 0
    inside_string = False
    while index < len(text):
        character = text[index]
        if character.isspace():
            index += 1
            continue
        if character == '"':
            start = index
            index += 1
            escaped = False
            while index < len(text):
                current = text[index]
                index += 1
                if escaped:
                    escaped = False
                    continue
                if current == "\\":
                    escaped = True
                    continue
                if current == '"':
                    break
            else:
                inside_string = True
            tokens.append(_Token(start, index, "string", text[start:index]))
            continue
        match = _IDENTIFIER.match(text, index)
        if match is not None:
            tokens.append(_Token(index, match.end(), "identifier", match.group(0)))
            index = match.end()
            continue
        if character.isdigit():
            start = index
            index += 1
            while index < len(text) and (text[index].isdigit() or text[index] == "."):
                index += 1
            tokens.append(_Token(start, index, "number", text[start:index]))
            continue
        tokens.append(_Token(index, index + 1, "punctuation", character))
        index += 1
    return tuple(tokens), inside_string


def _block_kind(segment: tuple[_Token, ...], parent: Optional[str]) -> str:
    for token in reversed(segment):
        if token.kind != "identifier" or token.value not in _BLOCK_STARTERS:
            continue
        if token.value == "when":
            return "function-when" if parent in {"function", "function-when", "function-otherwise"} else "action-when"
        if token.value == "otherwise":
            return "function-otherwise" if parent in {"function", "function-when", "function-otherwise"} else "action-otherwise"
        return token.value
    return "block"


def _block_stack(tokens: tuple[_Token, ...]) -> tuple[str, ...]:
    stack: list[str] = []
    segment: list[_Token] = []
    for token in tokens:
        if token.value == "{":
            parent = stack[-1] if stack else None
            stack.append(_block_kind(tuple(segment), parent))
            segment = []
            continue
        if token.value == "}":
            if stack:
                stack.pop()
            segment = []
            continue
        segment.append(token)
    return tuple(stack)


def _names(values: Iterable[str]) -> tuple[str, ...]:
    return tuple(sorted({value for value in values if type(value) is str and value}, key=lambda value: (value.casefold(), value)))


def _fallback_inventory(text: str, cursor: int) -> _Inventory:
    prefix = text[:cursor]
    type_parameters: list[str] = []
    parameters: list[str] = []

    type_match = re.search(
        r"\bfunction\s+[A-Za-z_][A-Za-z0-9_]*\s*<(?P<types>[^>]*)>?",
        prefix,
        re.DOTALL,
    )
    if type_match is not None:
        raw_types = type_match.group("types") or ""
        for part in raw_types.split(","):
            match = _IDENTIFIER.search(part)
            if match is not None:
                type_parameters.append(match.group(0))

    parameter_match = re.search(
        r"\bfunction\s+[A-Za-z_][A-Za-z0-9_]*[^({]*\((?P<params>[^)]*)",
        prefix,
        re.DOTALL,
    )
    if parameter_match is not None:
        raw_params = parameter_match.group("params") or ""
        for part in raw_params.split(","):
            match = _IDENTIFIER.search(part)
            if match is not None:
                parameters.append(match.group(0))

    return _Inventory(
        type_parameters=_names(type_parameters),
        parameters=_names(parameters),
        local_bindings=_names(re.findall(r"\blet\s+([A-Za-z_][A-Za-z0-9_]*)", prefix)),
        states=_names(re.findall(r"\bstate\s+([A-Za-z_][A-Za-z0-9_]*)", prefix)),
        events=_names(re.findall(r"\bevent\s+([A-Za-z_][A-Za-z0-9_]*)", prefix)),
    )


def _inventory(uri: str, text: str, cursor: int) -> _Inventory:
    fallback = _fallback_inventory(text, cursor)
    try:
        module_source = parse_module_source(uri, text)
        unit = parse_source_unit(
            module_source.masked_source,
            source_name=uri,
        )
    except Exception as error:
        if diagnostics_from_exception(error):
            return fallback
        raise

    selected_node: Optional[object] = None
    for declaration in unit.declarations:
        span = getattr(declaration, "span", None)
        start = getattr(getattr(span, "start", None), "offset", None)
        end = getattr(getattr(span, "end", None), "offset", None)
        if start is not None and end is not None and start <= cursor <= end:
            selected_node = declaration
            break

    if isinstance(selected_node, FunctionNode):
        local_bindings = tuple(
            binding.name
            for binding in selected_node.local_bindings
            if isinstance(binding, LetNode)
            and getattr(getattr(binding, "span", None), "start", None) is not None
            and binding.span.start.offset < cursor
        )
        return _Inventory(
            type_parameters=_names(
                parameter.name
                for parameter in selected_node.type_parameters
            ),
            parameters=_names(
                parameter.name
                for parameter in selected_node.parameters
            ),
            local_bindings=_names(
                (*fallback.local_bindings, *local_bindings)
            ),
        )
    if isinstance(selected_node, DirectiveNode):
        return _Inventory(
            states=_names(state.name for state in selected_node.states),
            events=_names(event.name for event in selected_node.events),
        )
    return fallback

def _keyword(label: str, rank: int = 0) -> _Candidate:
    return _Candidate(
        rank=rank,
        label=label,
        kind=LSP_COMPLETION_KEYWORD,
        detail="ApexForge keyword",
        documentation=_KEYWORD_DOCUMENTATION.get(label, "ApexForge language keyword."),
    )


def _named(label: str, kind: int, detail: str, documentation: str, rank: int = 1) -> _Candidate:
    return _Candidate(rank, label, kind, detail, documentation)


def _type_candidates(inventory: _Inventory) -> tuple[_Candidate, ...]:
    values = [
        _named(str(apex_type), LSP_COMPLETION_VALUE, "ApexForge built-in type", "Canonical ApexForge type identity.", 2)
        for apex_type in BUILTIN_TYPES
    ]
    values.extend(
        _named(name, LSP_COMPLETION_TYPE_PARAMETER, "Generic type parameter", "Type parameter declared by the current function.", 1)
        for name in inventory.type_parameters
    )
    return tuple(values)


def _expression_candidates(inventory: _Inventory) -> tuple[_Candidate, ...]:
    values: list[_Candidate] = [_keyword(value, 3) for value in _LITERAL_KEYWORDS]
    values.extend(
        _named(name, LSP_COMPLETION_VARIABLE, "Function parameter", "Parameter visible in the current function.", 1)
        for name in inventory.parameters
    )
    values.extend(
        _named(name, LSP_COMPLETION_VARIABLE, "Local binding", "Immutable binding declared earlier in the current function.", 1)
        for name in inventory.local_bindings
    )
    values.extend(
        _named(name, LSP_COMPLETION_FIELD, "Directive state", "State visible in the current directive.", 1)
        for name in inventory.states
    )
    return tuple(values)


def _line_context(text: str, start: int) -> tuple[tuple[_Token, ...], str]:
    line_start = text.rfind("\n", 0, start) + 1
    line_text = text[line_start:start]
    tokens, _ = _scan(line_text)
    return tokens, line_text


def _last_identifier(tokens: tuple[_Token, ...]) -> str:
    for token in reversed(tokens):
        if token.kind == "identifier":
            return token.value
    return ""


def _after_colon(line_text: str) -> bool:
    return re.search(r":\s*$", line_text) is not None


def _inside_generic_parameters(tokens: tuple[_Token, ...]) -> bool:
    depth = 0
    for token in tokens:
        if token.value == "<":
            depth += 1
        elif token.value == ">" and depth:
            depth -= 1
    return depth > 0 and any(token.value == "function" for token in tokens)


def _at_statement_start(line_text: str) -> bool:
    return not line_text.strip()


def _candidate_set(
    stack: tuple[str, ...],
    line_tokens: tuple[_Token, ...],
    line_text: str,
    inventory: _Inventory,
) -> tuple[_Candidate, ...]:
    last = _last_identifier(line_tokens)

    if _after_colon(line_text):
        if _inside_generic_parameters(line_tokens):
            return (
                _named("numeric", LSP_COMPLETION_VALUE, "Generic constraint", "Numeric generic capability.", 0),
            )
        return _type_candidates(inventory)

    if last in {"add", "set"}:
        return tuple(
            _named(name, LSP_COMPLETION_FIELD, "Directive state", "State target declared in the current directive.", 0)
            for name in inventory.states
        )
    if last == "emit":
        return tuple(
            _named(name, LSP_COMPLETION_EVENT, "Directive event", "Event declared in the current directive.", 0)
            for name in inventory.events
        )

    current = stack[-1] if stack else "top-level"
    statement_start = _at_statement_start(line_text)

    if current == "top-level":
        return tuple(_keyword(value) for value in _TOP_LEVEL_KEYWORDS)
    if current == "directive":
        return tuple(_keyword(value) for value in _DIRECTIVE_KEYWORDS)
    if current == "cause":
        return (_keyword("path"),)
    if current in {"path", "action-when", "action-otherwise"}:
        if statement_start:
            return tuple(_keyword(value) for value in _ACTION_KEYWORDS)
        return (*tuple(_keyword(value) for value in _ACTION_KEYWORDS), *_expression_candidates(inventory))
    if current == "workflow":
        return (_keyword("invoke"),)
    if current == "authority":
        return (_keyword("capability"),)
    if current == "role":
        return (_keyword("authority"),)
    if current == "principal":
        return (_keyword("authority"), _keyword("role"))
    if current in {"function", "function-when", "function-otherwise"}:
        if statement_start:
            return tuple(_keyword(value) for value in _FUNCTION_KEYWORDS)
        return (*tuple(_keyword(value) for value in _FUNCTION_KEYWORDS), *_expression_candidates(inventory), *_type_candidates(inventory))
    return ()


def _deduplicate(values: Iterable[_Candidate]) -> tuple[_Candidate, ...]:
    by_label: dict[str, _Candidate] = {}
    for value in values:
        previous = by_label.get(value.label)
        if previous is None or (value.rank, value.kind, value.detail) < (previous.rank, previous.kind, previous.detail):
            by_label[value.label] = value
    return tuple(sorted(by_label.values(), key=lambda item: (item.rank, item.label.casefold(), item.label, item.kind)))


def _completion_item(text: str, start: int, end: int, candidate: _Candidate) -> dict[str, object]:
    return {
        "label": candidate.label,
        "kind": candidate.kind,
        "detail": candidate.detail,
        "documentation": {
            "kind": "markdown",
            "value": candidate.documentation,
        },
        "insertText": candidate.label,
        "filterText": candidate.label,
        "sortText": f"{candidate.rank:02d}:{candidate.label.casefold()}:{candidate.label}",
        "textEdit": {
            "range": {
                "start": offset_to_lsp_position(text, start),
                "end": offset_to_lsp_position(text, end),
            },
            "newText": candidate.label,
        },
    }


def completion(
    uri: str,
    text: str,
    position: Mapping[str, object],
    context: Optional[Mapping[str, object]] = None,
) -> dict[str, object]:
    """Return one deterministic LSP CompletionList for an open document."""

    selected_uri = _require_uri(uri, "uri")
    source = _require_text(text, "text")
    offset = lsp_position_to_offset(source, position)
    if context is not None and type(context) is not dict:
        raise TypeError("context must be an object or None.")

    start, prefix = _identifier_prefix(source, offset)
    tokens, inside_string = _scan(source[:start])
    if inside_string:
        return {"isIncomplete": False, "items": []}

    stack = _block_stack(tokens)
    line_tokens, line_text = _line_context(source, start)
    inventory = _inventory(selected_uri, source, offset)
    candidates = _deduplicate(_candidate_set(stack, line_tokens, line_text, inventory))
    if prefix:
        folded = prefix.casefold()
        candidates = tuple(candidate for candidate in candidates if candidate.label.casefold().startswith(folded))

    return {
        "isIncomplete": False,
        "items": [
            _completion_item(source, start, offset, candidate)
            for candidate in candidates
        ],
    }


def completion_contract() -> dict[str, object]:
    return {
        "schema": COMPLETION_SCHEMA,
        "kind": COMPLETION_KIND,
        "completion_version": P10_T4_COMPLETION_VERSION,
        "method": COMPLETION_METHOD,
        "result": "CompletionList",
        "is_incomplete": False,
        "position_encoding": "utf-16",
        "trigger_characters": COMPLETION_TRIGGER_CHARACTERS,
        "scope": "open documents",
        "analysis": "tolerant lexical context plus best-effort parser inventory",
        "contexts": (
            "top_level_declarations",
            "declaration_body_keywords",
            "type_and_constraint_positions",
            "path_action_targets",
            "function_and_directive_expression_names",
        ),
        "replacement": "current identifier prefix",
        "invalid_source": "tolerant lexical completion remains available",
        "semantic_depth": "single-document syntax and lexical scope",
        "features_deferred": (
            "definition",
            "references",
            "rename",
            "workspace_symbols",
            "formatting",
            "cross_file_resolution",
            "type_inference",
            "completion_resolve",
            "snippets",
        ),
    }


def completion_fingerprint() -> str:
    payload = json.dumps(
        completion_contract(),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


CANONICAL_COMPLETION_SHA256: Final[str] = "8a6054d257a8b98c1a64584c7c8b9f9a5416a62769c11a500ab34afd333f21c5"


__all__ = (
    "CANONICAL_COMPLETION_SHA256",
    "COMPLETION_KIND",
    "COMPLETION_METHOD",
    "COMPLETION_SCHEMA",
    "COMPLETION_TRIGGER_CHARACTERS",
    "P10_T4_COMPLETION_VERSION",
    "completion",
    "completion_contract",
    "completion_fingerprint",
)
