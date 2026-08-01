"""AFP-P10-T5.2 Visual Studio editor syntax-classification contract."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Final, Mapping

P10_T5_VISUAL_STUDIO_SYNTAX_VERSION: Final[str] = "10-T5.2"
VISUAL_STUDIO_SYNTAX_SCHEMA: Final[int] = 1
VISUAL_STUDIO_SYNTAX_KIND: Final[str] = "apexforge.visual-studio-syntax"

KEYWORDS: Final[tuple[str, ...]] = (
    "module", "import", "function", "directive", "workflow", "authority",
    "principal", "role", "state", "event", "cause", "path", "capability",
    "requires", "extends", "add", "set", "emit", "message", "invoke",
    "when", "otherwise", "and", "or", "not", "return", "let", "true", "false",
)
DECLARATION_INTRODUCERS: Final[tuple[str, ...]] = (
    "module", "import", "function", "directive", "workflow", "authority",
    "principal", "role", "state", "event", "cause", "path", "capability", "let",
)
BUILTIN_TYPES: Final[tuple[str, ...]] = ("int", "bool", "string", "float", "void")
CLASSIFICATION_NAMES: Final[tuple[str, ...]] = (
    "apexforge.keyword", "apexforge.declaration", "apexforge.function",
    "apexforge.type", "apexforge.string", "apexforge.number",
    "apexforge.boolean", "apexforge.operator", "apexforge.punctuation",
)

_CONTRACT: Final[Mapping[str, object]] = {
    "schema": VISUAL_STUDIO_SYNTAX_SCHEMA,
    "kind": VISUAL_STUDIO_SYNTAX_KIND,
    "syntax_version": P10_T5_VISUAL_STUDIO_SYNTAX_VERSION,
    "required_t5_1_extension_sha256": "06d8b8f428b033d5e522b4eaf842560fc7c5b4e953ebcf3338f7e1a87d6b363e",
    "content_type": "apexforge",
    "source_extension": ".apex",
    "classification_names": CLASSIFICATION_NAMES,
    "keywords": KEYWORDS,
    "declaration_introducers": DECLARATION_INTRODUCERS,
    "built_in_types": BUILTIN_TYPES,
    "comments_supported": False,
    "scan_scope": "requested snapshot lines",
    "string_policy": "double quoted with escaped-character containment",
    "number_policy": "integer or digits-dot-digits float",
    "theme_policy": "custom user-visible classifications inherit Visual Studio standard classifications",
    "semantic_rewriting": False,
}


def visual_studio_syntax_contract() -> Mapping[str, object]:
    return _CONTRACT


def visual_studio_syntax_fingerprint() -> str:
    payload = json.dumps(_CONTRACT, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


CANONICAL_VISUAL_STUDIO_SYNTAX_SHA256: Final[str] = "a94182ea041461a46ed11281dbce09b4575e294ed9b5e1dff60a94b0a366987f"


@dataclass(frozen=True)
class SyntaxToken:
    start: int
    length: int
    kind: str
    text: str


def classify_apexforge_source(source: str) -> tuple[SyntaxToken, ...]:
    if type(source) is not str:
        raise TypeError("source must be a string")
    tokens: list[SyntaxToken] = []
    keyword_set = set(KEYWORDS)
    declaration_set = set(DECLARATION_INTRODUCERS)
    type_set = set(BUILTIN_TYPES)
    base = 0
    for line in source.splitlines(keepends=True):
        text = line.rstrip("\r\n")
        i = 0
        expect_declaration = False
        qualified_declaration = False
        expect_type = False
        while i < len(text):
            ch = text[i]
            if ch.isspace():
                i += 1
                continue
            if ch == '"':
                start = i
                i += 1
                escaped = False
                while i < len(text):
                    item = text[i]
                    i += 1
                    if escaped:
                        escaped = False
                    elif item == "\\":
                        escaped = True
                    elif item == '"':
                        break
                tokens.append(SyntaxToken(base + start, i - start, "apexforge.string", text[start:i]))
                expect_declaration = expect_type = False
                continue
            if ch.isdigit():
                start = i
                while i < len(text) and text[i].isdigit():
                    i += 1
                if i + 1 < len(text) and text[i] == "." and text[i + 1].isdigit():
                    i += 1
                    while i < len(text) and text[i].isdigit():
                        i += 1
                tokens.append(SyntaxToken(base + start, i - start, "apexforge.number", text[start:i]))
                expect_declaration = expect_type = False
                continue
            if ch == "_" or ch.isalpha():
                start = i
                i += 1
                while i < len(text) and (text[i] == "_" or text[i].isalnum()):
                    i += 1
                word = text[start:i]
                kind = None
                if word in ("true", "false"):
                    kind = "apexforge.boolean"
                    expect_declaration = expect_type = False
                elif word in keyword_set:
                    kind = "apexforge.keyword"
                    expect_declaration = word in declaration_set
                    qualified_declaration = word in ("module", "import")
                    expect_type = word in ("extends", "requires")
                elif word in type_set or expect_type:
                    kind = "apexforge.type"
                    expect_declaration = expect_type = False
                elif expect_declaration or qualified_declaration:
                    kind = "apexforge.declaration"
                    expect_declaration = False
                else:
                    j = i
                    while j < len(text) and text[j].isspace():
                        j += 1
                    if j < len(text) and text[j] == "<":
                        closing = text.find(">", j + 1)
                        if closing >= 0:
                            j = closing + 1
                            while j < len(text) and text[j].isspace():
                                j += 1
                    if j < len(text) and text[j] == "(":
                        kind = "apexforge.function"
                    expect_declaration = expect_type = False
                if kind is not None:
                    tokens.append(SyntaxToken(base + start, i - start, kind, word))
                continue
            if ch == ":":
                tokens.append(SyntaxToken(base + i, 1, "apexforge.punctuation", ch))
                expect_type = True
                i += 1
                continue
            if ch in "{}(),;.":
                tokens.append(SyntaxToken(base + i, 1, "apexforge.punctuation", ch))
                if ch != ".":
                    qualified_declaration = False
                i += 1
                continue
            pair = text[i:i + 2]
            if pair in ("==", "!=", "<=", ">="):
                tokens.append(SyntaxToken(base + i, 2, "apexforge.operator", pair))
                i += 2
                continue
            if ch in "=+-*/%@<>":
                tokens.append(SyntaxToken(base + i, 1, "apexforge.operator", ch))
                i += 1
                continue
            qualified_declaration = expect_declaration = expect_type = False
            i += 1
        base += len(line)
    return tuple(tokens)


__all__ = (
    "BUILTIN_TYPES", "CANONICAL_VISUAL_STUDIO_SYNTAX_SHA256", "CLASSIFICATION_NAMES",
    "DECLARATION_INTRODUCERS", "KEYWORDS", "P10_T5_VISUAL_STUDIO_SYNTAX_VERSION",
    "SyntaxToken", "VISUAL_STUDIO_SYNTAX_KIND", "VISUAL_STUDIO_SYNTAX_SCHEMA",
    "classify_apexforge_source", "visual_studio_syntax_contract", "visual_studio_syntax_fingerprint",
)
