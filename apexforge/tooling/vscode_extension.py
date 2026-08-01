"""AFP-P10-T3.1 VS Code extension-foundation validation.

This module validates the editor package that recognizes canonical ``.apex``
source files and provides basic bracket and indentation behavior. It does not
add language syntax, alter compilation, or require the VS Code runtime API.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Mapping, Optional, Sequence, TextIO


P10_T3_VSCODE_FOUNDATION_VERSION: Final[str] = "10-T3.1"
VSCODE_EXTENSION_FOUNDATION_SCHEMA: Final[int] = 1
VSCODE_EXTENSION_KIND: Final[str] = "apexforge.vscode-foundation"

CANONICAL_VSCODE_EXTENSION_DIRECTORY: Final[str] = "editors/vscode-apexforge"
CANONICAL_VSCODE_PACKAGE_NAME: Final[str] = "apexforge-language"
CANONICAL_VSCODE_DISPLAY_NAME: Final[str] = "ApexForge Language"
CANONICAL_VSCODE_PUBLISHER: Final[str] = "gravitas-studios"
CANONICAL_VSCODE_PACKAGE_VERSION: Final[str] = "0.1.0"
CANONICAL_VSCODE_ENGINE: Final[str] = "^1.85.0"
CANONICAL_VSCODE_LANGUAGE_ID: Final[str] = "apexforge"
CANONICAL_VSCODE_LANGUAGE_NAME: Final[str] = "ApexForge"
CANONICAL_VSCODE_SOURCE_EXTENSION: Final[str] = ".apex"
CANONICAL_VSCODE_LANGUAGE_CONFIGURATION: Final[str] = (
    "./language-configuration.json"
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

_EXPECTED_BRACKETS: Final[tuple[tuple[str, str], ...]] = (
    ("{", "}"),
    ("(", ")"),
)
_EXPECTED_SURROUNDING_PAIRS: Final[tuple[tuple[str, str], ...]] = (
    ("{", "}"),
    ("(", ")"),
    ('"', '"'),
)
_EXPECTED_AUTO_CLOSING_PAIRS: Final[tuple[tuple[str, str, tuple[str, ...]], ...]] = (
    ("{", "}", ()),
    ("(", ")", ()),
    ('"', '"', ("string",)),
)
_EXPECTED_WORD_PATTERN: Final[str] = r"[A-Za-z_][A-Za-z0-9_]*"
_EXPECTED_INCREASE_INDENT: Final[str] = r"^.*\{\s*$"
_EXPECTED_DECREASE_INDENT: Final[str] = r"^\s*\}"

# Filled after the canonical projection below is serialized. The smoke test
# rejects accidental foundation drift while allowing later additive fields such
# as the T3.2 TextMate grammar contribution.
CANONICAL_VSCODE_FOUNDATION_SHA256: Final[str] = "2a8478ea163312d211556f35f8c2fa99fd16eb93db81f829c33d8d688fb685e2"


class VSCodeExtensionError(ValueError):
    """The ApexForge VS Code extension foundation is invalid."""

    code: Final[str] = "APX-VSCODE-001"

    def __init__(self, message: str) -> None:
        if type(message) is not str or not message:
            raise ValueError("VSCodeExtensionError.message must be non-empty.")
        self.message = message
        super().__init__(f"[{self.code}] {message}")


@dataclass(frozen=True)
class VSCodeExtensionAudit:
    extension_root: Path
    package_name: str
    package_version: str
    language_id: str
    source_extension: str
    foundation_sha256: str


def _read_json(path: Path, owner: str) -> Mapping[str, object]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as error:
        raise VSCodeExtensionError(
            f"Could not read {owner} at {path}: {error}."
        ) from error

    try:
        value = json.loads(text)
    except json.JSONDecodeError as error:
        raise VSCodeExtensionError(
            f"{owner} is not valid JSON: {error}."
        ) from error

    if type(value) is not dict:
        raise VSCodeExtensionError(f"{owner} must contain a JSON object.")
    return value


def _require_mapping(value: object, owner: str) -> Mapping[str, object]:
    if type(value) is not dict:
        raise VSCodeExtensionError(f"{owner} must be a JSON object.")
    return value


def _require_list(value: object, owner: str) -> list[object]:
    if type(value) is not list:
        raise VSCodeExtensionError(f"{owner} must be a JSON array.")
    return value


def _require_string(value: object, owner: str) -> str:
    if type(value) is not str or not value:
        raise VSCodeExtensionError(f"{owner} must be a non-empty string.")
    return value


def _require_exact(value: object, expected: object, owner: str) -> None:
    if value != expected:
        raise VSCodeExtensionError(
            f"{owner} changed; expected {expected!r}, received {value!r}."
        )


def _normalize_pairs(value: object, owner: str) -> tuple[tuple[str, str], ...]:
    items = _require_list(value, owner)
    normalized: list[tuple[str, str]] = []
    for index, item in enumerate(items):
        pair = _require_list(item, f"{owner}[{index}]")
        if len(pair) != 2:
            raise VSCodeExtensionError(
                f"{owner}[{index}] must contain exactly two strings."
            )
        normalized.append(
            (
                _require_string(pair[0], f"{owner}[{index}][0]"),
                _require_string(pair[1], f"{owner}[{index}][1]"),
            )
        )
    return tuple(normalized)


def _normalize_auto_closing_pairs(
    value: object,
) -> tuple[tuple[str, str, tuple[str, ...]], ...]:
    items = _require_list(value, "language configuration autoClosingPairs")
    normalized: list[tuple[str, str, tuple[str, ...]]] = []
    for index, item in enumerate(items):
        pair = _require_mapping(
            item,
            f"language configuration autoClosingPairs[{index}]",
        )
        open_value = _require_string(
            pair.get("open"),
            f"autoClosingPairs[{index}].open",
        )
        close_value = _require_string(
            pair.get("close"),
            f"autoClosingPairs[{index}].close",
        )
        not_in_value = pair.get("notIn", [])
        not_in_items = _require_list(
            not_in_value,
            f"autoClosingPairs[{index}].notIn",
        )
        not_in = tuple(
            _require_string(
                item_value,
                f"autoClosingPairs[{index}].notIn[{item_index}]",
            )
            for item_index, item_value in enumerate(not_in_items)
        )
        normalized.append((open_value, close_value, not_in))
    return tuple(normalized)


def _find_language_contribution(
    package: Mapping[str, object],
) -> Mapping[str, object]:
    contributes = _require_mapping(
        package.get("contributes"),
        "package contributes",
    )
    languages = _require_list(
        contributes.get("languages"),
        "package contributes.languages",
    )

    matches: list[Mapping[str, object]] = []
    for index, item in enumerate(languages):
        language = _require_mapping(
            item,
            f"package contributes.languages[{index}]",
        )
        if language.get("id") == CANONICAL_VSCODE_LANGUAGE_ID:
            matches.append(language)

    if len(matches) != 1:
        raise VSCodeExtensionError(
            "The package must contain exactly one ApexForge language "
            "contribution."
        )
    return matches[0]


def _validate_package(package: Mapping[str, object]) -> Mapping[str, object]:
    _require_exact(
        package.get("name"),
        CANONICAL_VSCODE_PACKAGE_NAME,
        "package name",
    )
    _require_exact(
        package.get("displayName"),
        CANONICAL_VSCODE_DISPLAY_NAME,
        "package displayName",
    )
    _require_exact(
        package.get("version"),
        CANONICAL_VSCODE_PACKAGE_VERSION,
        "package version",
    )
    _require_exact(
        package.get("publisher"),
        CANONICAL_VSCODE_PUBLISHER,
        "package publisher",
    )

    engines = _require_mapping(package.get("engines"), "package engines")
    _require_exact(
        engines.get("vscode"),
        CANONICAL_VSCODE_ENGINE,
        "package engines.vscode",
    )

    categories = _require_list(package.get("categories"), "package categories")
    if "Programming Languages" not in categories:
        raise VSCodeExtensionError(
            "The package must remain in the Programming Languages category."
        )

    language = _find_language_contribution(package)
    _require_exact(
        language.get("id"),
        CANONICAL_VSCODE_LANGUAGE_ID,
        "language id",
    )
    _require_exact(
        language.get("aliases"),
        [CANONICAL_VSCODE_LANGUAGE_NAME, CANONICAL_VSCODE_LANGUAGE_ID],
        "language aliases",
    )
    _require_exact(
        language.get("extensions"),
        [CANONICAL_VSCODE_SOURCE_EXTENSION],
        "language extensions",
    )
    _require_exact(
        language.get("configuration"),
        CANONICAL_VSCODE_LANGUAGE_CONFIGURATION,
        "language configuration path",
    )

    contributes = _require_mapping(
        package.get("contributes"),
        "package contributes",
    )
    defaults = _require_mapping(
        contributes.get("configurationDefaults"),
        "package contributes.configurationDefaults",
    )
    apex_defaults = _require_mapping(
        defaults.get("[apexforge]"),
        "ApexForge configuration defaults",
    )
    _require_exact(
        apex_defaults.get("editor.insertSpaces"),
        True,
        "ApexForge editor.insertSpaces",
    )
    _require_exact(
        apex_defaults.get("editor.tabSize"),
        4,
        "ApexForge editor.tabSize",
    )
    _require_exact(
        apex_defaults.get("editor.detectIndentation"),
        False,
        "ApexForge editor.detectIndentation",
    )
    return language


def _validate_language_configuration(
    configuration: Mapping[str, object],
) -> None:
    if "comments" in configuration:
        raise VSCodeExtensionError(
            "ApexForge comments are unsupported by the frozen T2 grammar; "
            "language-configuration.json must not declare comment syntax."
        )

    _require_exact(
        configuration.get("wordPattern"),
        _EXPECTED_WORD_PATTERN,
        "language wordPattern",
    )
    _require_exact(
        _normalize_pairs(configuration.get("brackets"), "language brackets"),
        _EXPECTED_BRACKETS,
        "language brackets",
    )
    _require_exact(
        _normalize_auto_closing_pairs(configuration.get("autoClosingPairs")),
        _EXPECTED_AUTO_CLOSING_PAIRS,
        "language autoClosingPairs",
    )
    _require_exact(
        _normalize_pairs(
            configuration.get("surroundingPairs"),
            "language surroundingPairs",
        ),
        _EXPECTED_SURROUNDING_PAIRS,
        "language surroundingPairs",
    )

    indentation = _require_mapping(
        configuration.get("indentationRules"),
        "language indentationRules",
    )
    increase = _require_string(
        indentation.get("increaseIndentPattern"),
        "increaseIndentPattern",
    )
    decrease = _require_string(
        indentation.get("decreaseIndentPattern"),
        "decreaseIndentPattern",
    )
    _require_exact(increase, _EXPECTED_INCREASE_INDENT, "increaseIndentPattern")
    _require_exact(decrease, _EXPECTED_DECREASE_INDENT, "decreaseIndentPattern")

    try:
        re.compile(increase)
        re.compile(decrease)
        re.compile(_EXPECTED_WORD_PATTERN)
    except re.error as error:
        raise VSCodeExtensionError(
            f"A VS Code language regex is invalid: {error}."
        ) from error


def _foundation_projection(
    package: Mapping[str, object],
    configuration: Mapping[str, object],
) -> Mapping[str, object]:
    language = _find_language_contribution(package)
    contributes = _require_mapping(
        package.get("contributes"),
        "package contributes",
    )
    defaults = _require_mapping(
        contributes.get("configurationDefaults"),
        "package contributes.configurationDefaults",
    )

    return {
        "schema": VSCODE_EXTENSION_FOUNDATION_SCHEMA,
        "kind": VSCODE_EXTENSION_KIND,
        "foundation_version": P10_T3_VSCODE_FOUNDATION_VERSION,
        "package": {
            "name": package.get("name"),
            "displayName": package.get("displayName"),
            "version": package.get("version"),
            "publisher": package.get("publisher"),
            "engines": package.get("engines"),
            "categories": package.get("categories"),
        },
        "language": {
            "id": language.get("id"),
            "aliases": language.get("aliases"),
            "extensions": language.get("extensions"),
            "configuration": language.get("configuration"),
            "defaults": defaults.get("[apexforge]"),
        },
        "configuration": {
            "wordPattern": configuration.get("wordPattern"),
            "brackets": configuration.get("brackets"),
            "autoClosingPairs": configuration.get("autoClosingPairs"),
            "surroundingPairs": configuration.get("surroundingPairs"),
            "indentationRules": configuration.get("indentationRules"),
            "comments_declared": "comments" in configuration,
        },
    }


def foundation_fingerprint(
    package: Mapping[str, object],
    configuration: Mapping[str, object],
) -> str:
    """Return the deterministic T3.1 foundation SHA-256."""

    payload = json.dumps(
        _foundation_projection(package, configuration),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _validate_t2_contract(repository_root: Path) -> None:
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
        "T2 grammar export version",
    )

    source = _require_mapping(
        grammar_export.get("source"),
        "T2 grammar source contract",
    )
    _require_exact(
        source.get("extension"),
        CANONICAL_VSCODE_SOURCE_EXTENSION,
        "T2 canonical source extension",
    )

    corpus = _read_json(
        repository_root / "spec" / "conformance" / "corpus.json",
        "T2.3 conformance manifest",
    )
    _require_exact(
        corpus.get("version"),
        _T2_CONFORMANCE_VERSION,
        "T2 conformance version",
    )
    _require_exact(
        corpus.get("grammar_export_sha256"),
        _T2_EXPORT_SHA256,
        "T2 export SHA-256",
    )

    # The T2.3 corpus hash is frozen by its own audit. T3.1 records the same
    # value so editor integration cannot silently point at a different corpus.
    if _T2_CONFORMANCE_SHA256 != (
        "6bc21d12b6a667ba14e384f12e9b408a8c618a5eaf11dd91824c601745170884"
    ):
        raise VSCodeExtensionError("Internal T2.3 conformance fingerprint drifted.")


def audit_vscode_extension(
    extension_root: Path,
    *,
    repository_root: Optional[Path] = None,
) -> VSCodeExtensionAudit:
    """Validate the ApexForge VS Code extension foundation."""

    root = Path(extension_root).resolve()
    if not root.is_dir():
        raise VSCodeExtensionError(
            f"VS Code extension directory does not exist: {root}."
        )

    package = _read_json(root / "package.json", "VS Code package manifest")
    configuration = _read_json(
        root / "language-configuration.json",
        "VS Code language configuration",
    )
    _validate_package(package)
    _validate_language_configuration(configuration)

    selected_repository_root = (
        Path(repository_root).resolve()
        if repository_root is not None
        else root.parent.parent.resolve()
    )
    _validate_t2_contract(selected_repository_root)

    observed_hash = foundation_fingerprint(package, configuration)
    if observed_hash != CANONICAL_VSCODE_FOUNDATION_SHA256:
        raise VSCodeExtensionError(
            "VS Code foundation fingerprint changed; expected "
            f"{CANONICAL_VSCODE_FOUNDATION_SHA256}, received {observed_hash}."
        )

    return VSCodeExtensionAudit(
        extension_root=root,
        package_name=CANONICAL_VSCODE_PACKAGE_NAME,
        package_version=CANONICAL_VSCODE_PACKAGE_VERSION,
        language_id=CANONICAL_VSCODE_LANGUAGE_ID,
        source_extension=CANONICAL_VSCODE_SOURCE_EXTENSION,
        foundation_sha256=observed_hash,
    )


def main(
    argv: Optional[Sequence[str]] = None,
    *,
    stdout: TextIO = sys.stdout,
    stderr: TextIO = sys.stderr,
) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m tooling.vscode_extension",
        description="Validate the AFP-P10-T3.1 VS Code extension foundation.",
    )
    parser.add_argument("extension_root", type=Path)
    parser.add_argument(
        "--check",
        action="store_true",
        help="validate the package without modifying files",
    )
    arguments = parser.parse_args(tuple(argv) if argv is not None else None)

    if not arguments.check:
        parser.print_usage(stderr)
        print("error: --check is required", file=stderr)
        return 2

    try:
        audit = audit_vscode_extension(arguments.extension_root)
    except VSCodeExtensionError as error:
        print(str(error), file=stderr)
        return 1

    print("AFP-P10-T3.1 VS Code extension foundation check passed.", file=stdout)
    print(f"Package: {audit.package_name} {audit.package_version}", file=stdout)
    print(f"Language ID: {audit.language_id}", file=stdout)
    print(f"Source extension: {audit.source_extension}", file=stdout)
    print(f"Foundation SHA-256: {audit.foundation_sha256}", file=stdout)
    return 0


__all__ = (
    "CANONICAL_VSCODE_DISPLAY_NAME",
    "CANONICAL_VSCODE_ENGINE",
    "CANONICAL_VSCODE_EXTENSION_DIRECTORY",
    "CANONICAL_VSCODE_FOUNDATION_SHA256",
    "CANONICAL_VSCODE_LANGUAGE_CONFIGURATION",
    "CANONICAL_VSCODE_LANGUAGE_ID",
    "CANONICAL_VSCODE_LANGUAGE_NAME",
    "CANONICAL_VSCODE_PACKAGE_NAME",
    "CANONICAL_VSCODE_PACKAGE_VERSION",
    "CANONICAL_VSCODE_PUBLISHER",
    "CANONICAL_VSCODE_SOURCE_EXTENSION",
    "P10_T3_VSCODE_FOUNDATION_VERSION",
    "VSCODE_EXTENSION_FOUNDATION_SCHEMA",
    "VSCODE_EXTENSION_KIND",
    "VSCodeExtensionAudit",
    "VSCodeExtensionError",
    "audit_vscode_extension",
    "foundation_fingerprint",
    "main",
)


if __name__ == "__main__":
    raise SystemExit(main())
