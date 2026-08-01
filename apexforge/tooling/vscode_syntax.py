"""AFP-P10-T3.2 VS Code TextMate syntax validation.

This module validates the additive TextMate grammar contributed for canonical
``.apex`` files. It consumes the frozen T2 syntax export and conformance corpus,
preserves the T3.1 editor foundation, and does not alter ApexForge compilation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Final, Mapping, Optional, Sequence, TextIO

from tooling.vscode_extension import (
    CANONICAL_VSCODE_FOUNDATION_SHA256,
    CANONICAL_VSCODE_LANGUAGE_ID,
    CANONICAL_VSCODE_SOURCE_EXTENSION,
    audit_vscode_extension,
)


P10_T3_VSCODE_SYNTAX_VERSION: Final[str] = "10-T3.2"
VSCODE_SYNTAX_SCHEMA: Final[int] = 1
VSCODE_SYNTAX_KIND: Final[str] = "apexforge.vscode-syntax"

CANONICAL_TEXTMATE_NAME: Final[str] = "ApexForge"
CANONICAL_TEXTMATE_SCOPE: Final[str] = "source.apexforge"
CANONICAL_TEXTMATE_FILETYPE: Final[str] = "apex"
CANONICAL_TEXTMATE_PATH: Final[str] = (
    "./syntaxes/apexforge.tmLanguage.json"
)

_T2_GRAMMAR_VERSION: Final[str] = "10-T2.1"
_T2_GRAMMAR_SHA256: Final[str] = (
    "09abf328030692267297950d8d5894e69f3d2c9c9af6642c90b9d298f3515f18"
)
_T2_EXPORT_VERSION: Final[str] = "10-T2.2"
_T2_EXPORT_SHA256: Final[str] = (
    "d2ed66345cf66569cf9c673bc2f42cb1ea62592f9f371580796f0c97995e35ea"
)
_T2_CONFORMANCE_VERSION: Final[str] = "10-T2.3"
_T2_CONFORMANCE_SHA256: Final[str] = (
    "6bc21d12b6a667ba14e384f12e9b408a8c618a5eaf11dd91824c601745170884"
)

_EXPECTED_ROOT_INCLUDES: Final[tuple[str, ...]] = (
    "#strings",
    "#moduleHeaders",
    "#functionDeclarations",
    "#namedDeclarations",
    "#variableDeclarations",
    "#memberDeclarations",
    "#typeAnnotations",
    "#builtInTypes",
    "#booleans",
    "#logicalOperators",
    "#controlKeywords",
    "#actionKeywords",
    "#functionCalls",
    "#numbers",
    "#operators",
    "#punctuation",
    "#keywords",
)

_EXPECTED_REPOSITORIES: Final[tuple[str, ...]] = (
    "actionKeywords",
    "booleans",
    "builtInTypes",
    "controlKeywords",
    "functionCalls",
    "functionDeclarations",
    "keywords",
    "logicalOperators",
    "memberDeclarations",
    "moduleHeaders",
    "namedDeclarations",
    "numbers",
    "operators",
    "punctuation",
    "strings",
    "typeAnnotations",
    "variableDeclarations",
)

_EXPECTED_MODULE_PATTERN: Final[str] = (
    r"^\s*(module|import)\s+"
    r"([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*)"
)
_EXPECTED_FUNCTION_DECLARATION_PATTERN: Final[str] = (
    r"^\s*(function)\s+([A-Za-z_][A-Za-z0-9_]*)"
)
_EXPECTED_NAMED_DECLARATION_PATTERN: Final[str] = (
    r"^\s*(directive|workflow|authority|principal|role)\s+"
    r"([A-Za-z_][A-Za-z0-9_]*)"
)
_EXPECTED_VARIABLE_DECLARATION_PATTERN: Final[str] = (
    r"^\s*(state|let)\s+([A-Za-z_][A-Za-z0-9_]*)"
)
_EXPECTED_MEMBER_DECLARATION_PATTERN: Final[str] = (
    r"^\s*(event|cause|path|capability)\s+"
    r"([A-Za-z_][A-Za-z0-9_]*)"
)
_EXPECTED_TYPE_ANNOTATION_PATTERN: Final[str] = (
    r"(:)(\s*)([A-Za-z_][A-Za-z0-9_]*)"
)
_EXPECTED_BUILTIN_TYPE_PATTERN: Final[str] = (
    r"\b(?:int|bool|string|float|void)\b"
)
_EXPECTED_BOOLEAN_PATTERN: Final[str] = r"\b(?:true|false)\b"
_EXPECTED_LOGICAL_PATTERN: Final[str] = r"\b(?:and|or|not)\b"
_EXPECTED_CONTROL_PATTERN: Final[str] = r"\b(?:when|otherwise|return)\b"
_EXPECTED_ACTION_PATTERN: Final[str] = (
    r"\b(?:add|emit|message|invoke|set|requires|extends)\b"
)
_EXPECTED_FUNCTION_CALL_PATTERN: Final[str] = (
    r"\b([A-Za-z_][A-Za-z0-9_]*)\s*"
    r"(?=(?:<[^>\r\n]+>)?\s*\()"
)
_EXPECTED_FLOAT_PATTERN: Final[str] = r"\b\d+\.\d+\b"
_EXPECTED_INTEGER_PATTERN: Final[str] = r"\b\d+\b"
_EXPECTED_OPERATOR_PATTERN: Final[str] = r"==|!=|<=|>=|[=+\-*/%@<>]"
_EXPECTED_PUNCTUATION_PATTERN: Final[str] = r"[{}(),:;]"
_EXPECTED_ESCAPE_PATTERN: Final[str] = r'\\(?:n|r|t|"|\\)'

CANONICAL_VSCODE_SYNTAX_SHA256: Final[str] = (
    "cb8e7e35005e7ba8fe2f933cf45247aaf5a8e8a4e7cbc1dd1bbe07ef6c584466"
)


class VSCodeSyntaxError(ValueError):
    """The ApexForge VS Code TextMate syntax package is invalid."""

    code: Final[str] = "APX-VSCODE-002"

    def __init__(self, message: str) -> None:
        if type(message) is not str or not message:
            raise ValueError("VSCodeSyntaxError.message must be non-empty.")
        self.message = message
        super().__init__(f"[{self.code}] {message}")


@dataclass(frozen=True)
class VSCodeSyntaxAudit:
    extension_root: Path
    grammar_path: Path
    language_id: str
    scope_name: str
    repository_count: int
    regex_count: int
    syntax_sha256: str


@dataclass(frozen=True)
class _T2Contract:
    keyword_lexemes: tuple[str, ...]
    top_level_declarations: tuple[str, ...]


def _read_json(path: Path, owner: str) -> Mapping[str, object]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as error:
        raise VSCodeSyntaxError(
            f"Could not read {owner} at {path}: {error}."
        ) from error

    try:
        value = json.loads(text)
    except json.JSONDecodeError as error:
        raise VSCodeSyntaxError(
            f"{owner} is not valid JSON: {error}."
        ) from error

    if type(value) is not dict:
        raise VSCodeSyntaxError(f"{owner} must contain a JSON object.")
    return value


def _require_mapping(value: object, owner: str) -> Mapping[str, object]:
    if type(value) is not dict:
        raise VSCodeSyntaxError(f"{owner} must be a JSON object.")
    return value


def _require_list(value: object, owner: str) -> list[object]:
    if type(value) is not list:
        raise VSCodeSyntaxError(f"{owner} must be a JSON array.")
    return value


def _require_string(value: object, owner: str) -> str:
    if type(value) is not str or not value:
        raise VSCodeSyntaxError(f"{owner} must be a non-empty string.")
    return value


def _require_exact(value: object, expected: object, owner: str) -> None:
    if value != expected:
        raise VSCodeSyntaxError(
            f"{owner} changed; expected {expected!r}, received {value!r}."
        )


def _find_grammar_contribution(
    package: Mapping[str, object],
) -> Mapping[str, object]:
    contributes = _require_mapping(
        package.get("contributes"),
        "package contributes",
    )
    grammars = _require_list(
        contributes.get("grammars"),
        "package contributes.grammars",
    )

    matches: list[Mapping[str, object]] = []
    for index, item in enumerate(grammars):
        grammar = _require_mapping(
            item,
            f"package contributes.grammars[{index}]",
        )
        if grammar.get("language") == CANONICAL_VSCODE_LANGUAGE_ID:
            matches.append(grammar)

    if len(matches) != 1:
        raise VSCodeSyntaxError(
            "The package must contain exactly one ApexForge grammar "
            "contribution."
        )
    return matches[0]


def _validate_grammar_contribution(
    contribution: Mapping[str, object],
) -> None:
    _require_exact(
        contribution.get("language"),
        CANONICAL_VSCODE_LANGUAGE_ID,
        "TextMate contribution language",
    )
    _require_exact(
        contribution.get("scopeName"),
        CANONICAL_TEXTMATE_SCOPE,
        "TextMate contribution scopeName",
    )
    _require_exact(
        contribution.get("path"),
        CANONICAL_TEXTMATE_PATH,
        "TextMate contribution path",
    )


def _root_includes(grammar: Mapping[str, object]) -> tuple[str, ...]:
    patterns = _require_list(grammar.get("patterns"), "TextMate root patterns")
    includes: list[str] = []
    for index, item in enumerate(patterns):
        pattern = _require_mapping(item, f"TextMate patterns[{index}]")
        if set(pattern) != {"include"}:
            raise VSCodeSyntaxError(
                "Every TextMate root pattern must contain only an include."
            )
        includes.append(
            _require_string(
                pattern.get("include"),
                f"TextMate patterns[{index}].include",
            )
        )
    return tuple(includes)


def _repository(
    grammar: Mapping[str, object],
) -> Mapping[str, object]:
    return _require_mapping(
        grammar.get("repository"),
        "TextMate repository",
    )


def _repository_rule(
    repository: Mapping[str, object],
    name: str,
) -> Mapping[str, object]:
    return _require_mapping(
        repository.get(name),
        f"TextMate repository.{name}",
    )


def _require_rule_match(
    repository: Mapping[str, object],
    rule_name: str,
    expected: str,
) -> None:
    rule = _repository_rule(repository, rule_name)
    _require_exact(
        rule.get("match"),
        expected,
        f"TextMate repository.{rule_name}.match",
    )


def _keyword_pattern(keyword_lexemes: tuple[str, ...]) -> str:
    return (
        r"\b(?:"
        + "|".join(re.escape(keyword) for keyword in keyword_lexemes)
        + r")\b"
    )


def _collect_regexes(value: object) -> tuple[str, ...]:
    expressions: list[str] = []

    def visit(item: object) -> None:
        if type(item) is dict:
            for key, child in item.items():
                if key in {"match", "begin", "end", "while"}:
                    expressions.append(
                        _require_string(child, f"TextMate regex {key}")
                    )
                else:
                    visit(child)
            return
        if type(item) is list:
            for child in item:
                visit(child)

    visit(value)
    return tuple(expressions)


def _collect_scope_names(value: object) -> tuple[str, ...]:
    names: list[str] = []

    def visit(item: object) -> None:
        if type(item) is dict:
            for key, child in item.items():
                if key == "name":
                    names.append(_require_string(child, "TextMate scope name"))
                else:
                    visit(child)
            return
        if type(item) is list:
            for child in item:
                visit(child)

    visit(value)
    return tuple(names)


def _validate_regexes(grammar: Mapping[str, object]) -> int:
    expressions = _collect_regexes(grammar)
    for expression in expressions:
        try:
            re.compile(expression)
        except re.error as error:
            raise VSCodeSyntaxError(
                f"TextMate regex is invalid: {expression!r}: {error}."
            ) from error
    return len(expressions)


def _validate_no_comments(grammar: Mapping[str, object]) -> None:
    repository = _repository(grammar)
    if "comments" in repository:
        raise VSCodeSyntaxError(
            "The frozen T2 grammar does not support comments; "
            "the TextMate repository must not declare a comments rule."
        )

    for scope_name in _collect_scope_names(grammar):
        if scope_name == "comment" or scope_name.startswith("comment."):
            raise VSCodeSyntaxError(
                "The frozen T2 grammar does not support comment scopes."
            )

    for expression in _collect_regexes(grammar):
        if "#" in expression:
            raise VSCodeSyntaxError(
                "The TextMate grammar must not tokenize '#' as comment syntax."
            )


def _validate_textmate_grammar(
    grammar: Mapping[str, object],
    contract: _T2Contract,
) -> tuple[int, int]:
    _require_exact(
        grammar.get("name"),
        CANONICAL_TEXTMATE_NAME,
        "TextMate grammar name",
    )
    _require_exact(
        grammar.get("scopeName"),
        CANONICAL_TEXTMATE_SCOPE,
        "TextMate grammar scopeName",
    )
    _require_exact(
        grammar.get("fileTypes"),
        [CANONICAL_TEXTMATE_FILETYPE],
        "TextMate grammar fileTypes",
    )
    _require_exact(
        _root_includes(grammar),
        _EXPECTED_ROOT_INCLUDES,
        "TextMate root include order",
    )

    repository = _repository(grammar)
    _require_exact(
        tuple(sorted(repository)),
        _EXPECTED_REPOSITORIES,
        "TextMate repository inventory",
    )

    strings = _repository_rule(repository, "strings")
    _require_exact(strings.get("begin"), '"', "string begin")
    _require_exact(strings.get("end"), '"', "string end")
    string_patterns = _require_list(
        strings.get("patterns"),
        "TextMate repository.strings.patterns",
    )
    if len(string_patterns) != 1:
        raise VSCodeSyntaxError(
            "The string rule must contain exactly one escape pattern."
        )
    escape_rule = _require_mapping(
        string_patterns[0],
        "TextMate string escape rule",
    )
    _require_exact(
        escape_rule.get("match"),
        _EXPECTED_ESCAPE_PATTERN,
        "TextMate string escape pattern",
    )

    _require_rule_match(
        repository,
        "moduleHeaders",
        _EXPECTED_MODULE_PATTERN,
    )
    _require_rule_match(
        repository,
        "functionDeclarations",
        _EXPECTED_FUNCTION_DECLARATION_PATTERN,
    )
    _require_rule_match(
        repository,
        "namedDeclarations",
        _EXPECTED_NAMED_DECLARATION_PATTERN,
    )
    _require_rule_match(
        repository,
        "variableDeclarations",
        _EXPECTED_VARIABLE_DECLARATION_PATTERN,
    )
    _require_rule_match(
        repository,
        "memberDeclarations",
        _EXPECTED_MEMBER_DECLARATION_PATTERN,
    )
    _require_rule_match(
        repository,
        "typeAnnotations",
        _EXPECTED_TYPE_ANNOTATION_PATTERN,
    )
    _require_rule_match(
        repository,
        "builtInTypes",
        _EXPECTED_BUILTIN_TYPE_PATTERN,
    )
    _require_rule_match(
        repository,
        "booleans",
        _EXPECTED_BOOLEAN_PATTERN,
    )
    _require_rule_match(
        repository,
        "logicalOperators",
        _EXPECTED_LOGICAL_PATTERN,
    )
    _require_rule_match(
        repository,
        "controlKeywords",
        _EXPECTED_CONTROL_PATTERN,
    )
    _require_rule_match(
        repository,
        "actionKeywords",
        _EXPECTED_ACTION_PATTERN,
    )
    _require_rule_match(
        repository,
        "functionCalls",
        _EXPECTED_FUNCTION_CALL_PATTERN,
    )
    _require_rule_match(
        repository,
        "operators",
        _EXPECTED_OPERATOR_PATTERN,
    )
    _require_rule_match(
        repository,
        "punctuation",
        _EXPECTED_PUNCTUATION_PATTERN,
    )
    _require_rule_match(
        repository,
        "keywords",
        _keyword_pattern(contract.keyword_lexemes),
    )

    numbers = _repository_rule(repository, "numbers")
    number_patterns = _require_list(
        numbers.get("patterns"),
        "TextMate repository.numbers.patterns",
    )
    if len(number_patterns) != 2:
        raise VSCodeSyntaxError(
            "The numbers rule must contain float then integer patterns."
        )
    float_rule = _require_mapping(number_patterns[0], "float number rule")
    integer_rule = _require_mapping(number_patterns[1], "integer number rule")
    _require_exact(
        float_rule.get("match"),
        _EXPECTED_FLOAT_PATTERN,
        "TextMate float pattern",
    )
    _require_exact(
        integer_rule.get("match"),
        _EXPECTED_INTEGER_PATTERN,
        "TextMate integer pattern",
    )

    _require_exact(
        contract.top_level_declarations,
        (
            "function",
            "directive",
            "workflow",
            "authority",
            "principal",
            "role",
        ),
        "T2 top-level declaration inventory",
    )

    _validate_no_comments(grammar)
    regex_count = _validate_regexes(grammar)
    return len(repository), regex_count


def _load_t2_contract(repository_root: Path) -> _T2Contract:
    grammar_export = _read_json(
        repository_root / "spec" / "apexforge.grammar.json",
        "T2.2 grammar export",
    )
    _require_exact(
        grammar_export.get("grammar_version"),
        _T2_GRAMMAR_VERSION,
        "T2 grammar version",
    )
    _require_exact(
        grammar_export.get("grammar_sha256"),
        _T2_GRAMMAR_SHA256,
        "T2 grammar SHA-256",
    )
    _require_exact(
        grammar_export.get("export_version"),
        _T2_EXPORT_VERSION,
        "T2 export version",
    )

    source = _require_mapping(
        grammar_export.get("source"),
        "T2 source contract",
    )
    _require_exact(
        source.get("extension"),
        CANONICAL_VSCODE_SOURCE_EXTENSION,
        "T2 source extension",
    )

    boundaries = _require_mapping(
        grammar_export.get("boundaries"),
        "T2 syntax boundaries",
    )
    _require_exact(
        boundaries.get("comments_supported"),
        False,
        "T2 comment boundary",
    )

    tokens = _require_mapping(
        grammar_export.get("tokens"),
        "T2 token inventory",
    )
    keyword_items = _require_list(
        tokens.get("keywords"),
        "T2 keyword inventory",
    )
    keywords: list[str] = []
    for index, item in enumerate(keyword_items):
        keyword = _require_mapping(item, f"T2 keywords[{index}]")
        keywords.append(
            _require_string(
                keyword.get("lexeme"),
                f"T2 keywords[{index}].lexeme",
            )
        )

    top_level_items = _require_list(
        grammar_export.get("top_level_declarations"),
        "T2 top-level declarations",
    )
    declarations = tuple(
        _require_string(item, f"T2 top-level declarations[{index}]")
        for index, item in enumerate(top_level_items)
    )

    return _T2Contract(
        keyword_lexemes=tuple(keywords),
        top_level_declarations=declarations,
    )


def _corpus_paths(corpus: Mapping[str, object]) -> tuple[str, ...]:
    paths: list[str] = ["corpus.json"]

    valid = _require_list(corpus.get("valid"), "T2 corpus valid")
    for index, item in enumerate(valid):
        case = _require_mapping(item, f"T2 corpus valid[{index}]")
        paths.append(
            _require_string(
                case.get("path"),
                f"T2 corpus valid[{index}].path",
            )
        )

    projects = _require_list(corpus.get("projects"), "T2 corpus projects")
    for index, item in enumerate(projects):
        project = _require_mapping(item, f"T2 corpus projects[{index}]")
        directory = _require_string(
            project.get("directory"),
            f"T2 corpus projects[{index}].directory",
        )
        sources = _require_list(
            project.get("sources"),
            f"T2 corpus projects[{index}].sources",
        )
        for source_index, source in enumerate(sources):
            source_name = _require_string(
                source,
                f"T2 corpus projects[{index}].sources[{source_index}]",
            )
            paths.append(
                str(PurePosixPath(directory) / source_name)
            )

    invalid = _require_list(corpus.get("invalid"), "T2 corpus invalid")
    for index, item in enumerate(invalid):
        case = _require_mapping(item, f"T2 corpus invalid[{index}]")
        paths.append(
            _require_string(
                case.get("path"),
                f"T2 corpus invalid[{index}].path",
            )
        )

    return tuple(sorted(paths))


def _corpus_fingerprint(corpus_root: Path) -> str:
    corpus = _read_json(corpus_root / "corpus.json", "T2.3 corpus manifest")
    _require_exact(
        corpus.get("version"),
        _T2_CONFORMANCE_VERSION,
        "T2 conformance version",
    )
    _require_exact(
        corpus.get("grammar_export_sha256"),
        _T2_EXPORT_SHA256,
        "T2 grammar export SHA-256",
    )

    expected_paths = _corpus_paths(corpus)
    actual_paths = tuple(
        sorted(
            {
                "corpus.json",
                *(
                    path.relative_to(corpus_root).as_posix()
                    for path in corpus_root.rglob("*.apex")
                    if path.is_file()
                ),
            }
        )
    )
    if actual_paths != expected_paths:
        raise VSCodeSyntaxError(
            "T2 conformance corpus inventory changed; "
            f"expected={expected_paths}, received={actual_paths}."
        )

    digest = hashlib.sha256()
    for relative_name in expected_paths:
        path = corpus_root / PurePosixPath(relative_name)
        if not path.is_file():
            raise VSCodeSyntaxError(
                f"Missing T2 conformance file {relative_name!r}."
            )
        relative_bytes = relative_name.encode("utf-8")
        data = path.read_bytes()
        digest.update(len(relative_bytes).to_bytes(4, "big"))
        digest.update(relative_bytes)
        digest.update(len(data).to_bytes(8, "big"))
        digest.update(data)
    return digest.hexdigest()


def _validate_corpus_coverage(
    repository_root: Path,
    grammar: Mapping[str, object],
    contract: _T2Contract,
) -> None:
    corpus_root = repository_root / "spec" / "conformance"
    corpus = _read_json(corpus_root / "corpus.json", "T2.3 corpus manifest")

    source_paths: list[str] = []
    for item in _require_list(corpus.get("valid"), "T2 corpus valid"):
        case = _require_mapping(item, "T2 valid case")
        source_paths.append(_require_string(case.get("path"), "valid path"))
    for item in _require_list(corpus.get("projects"), "T2 corpus projects"):
        project = _require_mapping(item, "T2 project case")
        directory = _require_string(project.get("directory"), "project directory")
        for source in _require_list(project.get("sources"), "project sources"):
            source_paths.append(
                str(
                    PurePosixPath(directory)
                    / _require_string(source, "project source")
                )
            )

    texts: list[str] = []
    for relative_name in source_paths:
        path = corpus_root / PurePosixPath(relative_name)
        try:
            texts.append(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError) as error:
            raise VSCodeSyntaxError(
                f"Could not read T2 valid source {relative_name!r}: {error}."
            ) from error

    combined = "\n".join(texts)
    repository = _repository(grammar)

    module_pattern = _require_string(
        _repository_rule(repository, "moduleHeaders").get("match"),
        "module header match",
    )
    module_regex = re.compile(module_pattern, re.MULTILINE)
    observed_headers = {
        match.group(1)
        for match in module_regex.finditer(combined)
    }
    _require_exact(
        observed_headers,
        {"module", "import"},
        "module/import highlighting coverage",
    )

    for declaration in contract.top_level_declarations:
        if re.search(
            rf"^\s*{re.escape(declaration)}\s+",
            combined,
            re.MULTILINE,
        ) is None:
            raise VSCodeSyntaxError(
                f"TextMate conformance corpus lacks {declaration!r} coverage."
            )

    function_call_pattern = _require_string(
        _repository_rule(repository, "functionCalls").get("match"),
        "function-call match",
    )
    if re.search(function_call_pattern, combined) is None:
        raise VSCodeSyntaxError(
            "TextMate function-call rule did not match the valid corpus."
        )

    type_pattern = _require_string(
        _repository_rule(repository, "typeAnnotations").get("match"),
        "type-annotation match",
    )
    if re.search(type_pattern, combined) is None:
        raise VSCodeSyntaxError(
            "TextMate type-annotation rule did not match the valid corpus."
        )

    if '"' not in combined:
        raise VSCodeSyntaxError(
            "TextMate string rule has no valid-corpus example."
        )


def _syntax_projection(
    contribution: Mapping[str, object],
    grammar: Mapping[str, object],
) -> Mapping[str, object]:
    return {
        "schema": VSCODE_SYNTAX_SCHEMA,
        "kind": VSCODE_SYNTAX_KIND,
        "syntax_version": P10_T3_VSCODE_SYNTAX_VERSION,
        "foundation_sha256": CANONICAL_VSCODE_FOUNDATION_SHA256,
        "grammar_version": _T2_GRAMMAR_VERSION,
        "grammar_sha256": _T2_GRAMMAR_SHA256,
        "grammar_export_version": _T2_EXPORT_VERSION,
        "grammar_export_sha256": _T2_EXPORT_SHA256,
        "conformance_version": _T2_CONFORMANCE_VERSION,
        "conformance_sha256": _T2_CONFORMANCE_SHA256,
        "grammar_contribution": contribution,
        "textmate": grammar,
    }


def syntax_fingerprint(
    package: Mapping[str, object],
    grammar: Mapping[str, object],
) -> str:
    """Return the deterministic AFP-P10-T3.2 syntax SHA-256."""

    contribution = _find_grammar_contribution(package)
    payload = json.dumps(
        _syntax_projection(contribution, grammar),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def audit_vscode_syntax(
    extension_root: Path,
    *,
    repository_root: Optional[Path] = None,
) -> VSCodeSyntaxAudit:
    """Validate the ApexForge VS Code TextMate syntax package."""

    root = Path(extension_root).resolve()
    if not root.is_dir():
        raise VSCodeSyntaxError(
            f"VS Code extension directory does not exist: {root}."
        )

    selected_repository_root = (
        Path(repository_root).resolve()
        if repository_root is not None
        else root.parent.parent.resolve()
    )

    foundation = audit_vscode_extension(
        root,
        repository_root=selected_repository_root,
    )
    _require_exact(
        foundation.foundation_sha256,
        CANONICAL_VSCODE_FOUNDATION_SHA256,
        "T3.1 foundation SHA-256",
    )

    contract = _load_t2_contract(selected_repository_root)
    corpus_hash = _corpus_fingerprint(
        selected_repository_root / "spec" / "conformance"
    )
    _require_exact(
        corpus_hash,
        _T2_CONFORMANCE_SHA256,
        "T2.3 conformance SHA-256",
    )

    package = _read_json(root / "package.json", "VS Code package manifest")
    contribution = _find_grammar_contribution(package)
    _validate_grammar_contribution(contribution)

    grammar_path = root / CANONICAL_TEXTMATE_PATH.removeprefix("./")
    grammar = _read_json(grammar_path, "ApexForge TextMate grammar")
    repository_count, regex_count = _validate_textmate_grammar(
        grammar,
        contract,
    )
    _validate_corpus_coverage(
        selected_repository_root,
        grammar,
        contract,
    )

    observed_hash = syntax_fingerprint(package, grammar)
    if observed_hash != CANONICAL_VSCODE_SYNTAX_SHA256:
        raise VSCodeSyntaxError(
            "VS Code syntax fingerprint changed; expected "
            f"{CANONICAL_VSCODE_SYNTAX_SHA256}, received {observed_hash}."
        )

    return VSCodeSyntaxAudit(
        extension_root=root,
        grammar_path=grammar_path,
        language_id=CANONICAL_VSCODE_LANGUAGE_ID,
        scope_name=CANONICAL_TEXTMATE_SCOPE,
        repository_count=repository_count,
        regex_count=regex_count,
        syntax_sha256=observed_hash,
    )


def main(
    argv: Optional[Sequence[str]] = None,
    *,
    stdout: TextIO = sys.stdout,
    stderr: TextIO = sys.stderr,
) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m tooling.vscode_syntax",
        description="Validate AFP-P10-T3.2 VS Code TextMate syntax.",
    )
    parser.add_argument("extension_root", type=Path)
    parser.add_argument(
        "--check",
        action="store_true",
        help="validate the syntax package without modifying files",
    )
    arguments = parser.parse_args(tuple(argv) if argv is not None else None)

    if not arguments.check:
        parser.print_usage(stderr)
        print("error: --check is required", file=stderr)
        return 2

    try:
        audit = audit_vscode_syntax(arguments.extension_root)
    except (VSCodeSyntaxError, ValueError) as error:
        print(str(error), file=stderr)
        return 1

    print("AFP-P10-T3.2 VS Code TextMate syntax check passed.", file=stdout)
    print(f"Language ID: {audit.language_id}", file=stdout)
    print(f"Scope: {audit.scope_name}", file=stdout)
    print(f"Repository rules: {audit.repository_count}", file=stdout)
    print(f"Regex rules: {audit.regex_count}", file=stdout)
    print(f"Syntax SHA-256: {audit.syntax_sha256}", file=stdout)
    return 0


__all__ = (
    "CANONICAL_TEXTMATE_FILETYPE",
    "CANONICAL_TEXTMATE_NAME",
    "CANONICAL_TEXTMATE_PATH",
    "CANONICAL_TEXTMATE_SCOPE",
    "CANONICAL_VSCODE_SYNTAX_SHA256",
    "P10_T3_VSCODE_SYNTAX_VERSION",
    "VSCODE_SYNTAX_KIND",
    "VSCODE_SYNTAX_SCHEMA",
    "VSCodeSyntaxAudit",
    "VSCodeSyntaxError",
    "audit_vscode_syntax",
    "main",
    "syntax_fingerprint",
)


if __name__ == "__main__":
    raise SystemExit(main())
