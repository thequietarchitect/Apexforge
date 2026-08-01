"""AFP-P10-T2.2 deterministic ApexForge grammar exports.

This module projects the frozen AFP-P10-T2.1 source contract into two stable
artifacts:

* ``apexforge.ebnf`` for human-readable grammar consumers.
* ``apexforge.grammar.json`` for editors, language servers, and other tooling.

It does not alter lexing, parsing, compilation, or project-loading behavior.
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

from language.grammar import (
    APEXFORGE_EBNF,
    CANONICAL_GRAMMAR_SHA256,
    CANONICAL_MAIN_FILENAME,
    CANONICAL_SOURCE_EXTENSION,
    CANONICAL_SOURCE_GLOB,
    COMMENTS_SUPPORTED,
    GRAMMAR_CONTRACT_NOTES,
    GRAMMAR_KEYWORD_TOKENS,
    GRAMMAR_ONE_CHARACTER_TOKENS,
    GRAMMAR_TWO_CHARACTER_TOKENS,
    MODULE_HEADER_KEYWORDS,
    MODULE_HEADER_SEMICOLONS_OPTIONAL,
    ORDINARY_SEMICOLONS_SUPPORTED,
    P10_T2_GRAMMAR_VERSION,
    STRING_ESCAPE_SEQUENCES,
    TOP_LEVEL_DECLARATIONS,
)


P10_T2_EXPORT_VERSION: Final[str] = "10-T2.2"
GRAMMAR_EXPORT_SCHEMA: Final[int] = 1
GRAMMAR_EXPORT_KIND: Final[str] = "apexforge.syntax-grammar"
CANONICAL_EBNF_EXPORT_FILENAME: Final[str] = "apexforge.ebnf"
CANONICAL_JSON_EXPORT_FILENAME: Final[str] = "apexforge.grammar.json"

_PRODUCTION_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9]*$")


class GrammarExportError(ValueError):
    """A deterministic grammar export could not be produced or verified."""

    code: Final[str] = "APX-GRAMMAR-001"

    def __init__(self, message: str) -> None:
        if type(message) is not str or not message:
            raise ValueError("GrammarExportError.message must be non-empty.")
        self.message = message
        super().__init__(f"[{self.code}] {message}")


@dataclass(frozen=True, order=True)
class GrammarProduction:
    """One normalized EBNF production in source order."""

    name: str
    expression: str

    def __post_init__(self) -> None:
        if type(self.name) is not str or _PRODUCTION_NAME.fullmatch(self.name) is None:
            raise GrammarExportError(
                f"Invalid EBNF production name {self.name!r}."
            )
        if type(self.expression) is not str or not self.expression.strip():
            raise GrammarExportError(
                f"EBNF production {self.name!r} requires an expression."
            )
        object.__setattr__(self, "expression", " ".join(self.expression.split()))

    def to_document(self) -> dict[str, str]:
        return {
            "name": self.name,
            "expression": self.expression,
        }


def parse_ebnf_productions(ebnf: str = APEXFORGE_EBNF) -> tuple[GrammarProduction, ...]:
    """Parse the canonical line-oriented EBNF into ordered productions."""

    if type(ebnf) is not str or not ebnf.strip():
        raise GrammarExportError("EBNF source must be a non-empty string.")

    blocks: list[str] = []
    current: list[str] = []

    for raw_line in ebnf.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        current.append(line)
        if line.endswith(";"):
            blocks.append(" ".join(current))
            current = []

    if current:
        raise GrammarExportError(
            "The final EBNF production is not terminated by a semicolon."
        )

    productions: list[GrammarProduction] = []
    seen: set[str] = set()

    for block in blocks:
        if "=" not in block:
            raise GrammarExportError(
                f"Malformed EBNF production without '=': {block!r}."
            )
        name, expression = block.split("=", 1)
        normalized_name = name.strip()
        normalized_expression = expression.strip()
        if not normalized_expression.endswith(";"):
            raise GrammarExportError(
                f"EBNF production {normalized_name!r} lacks a terminator."
            )
        normalized_expression = normalized_expression[:-1].strip()

        if normalized_name in seen:
            raise GrammarExportError(
                f"Duplicate EBNF production {normalized_name!r}."
            )

        production = GrammarProduction(
            name=normalized_name,
            expression=normalized_expression,
        )
        productions.append(production)
        seen.add(normalized_name)

    if not productions or productions[0].name != "ApexForgeSource":
        raise GrammarExportError(
            "The canonical EBNF must begin with ApexForgeSource."
        )

    return tuple(productions)


def render_grammar_ebnf() -> str:
    """Return the canonical EBNF with one terminating newline."""

    return APEXFORGE_EBNF.rstrip() + "\n"


def _token_documents(values: Mapping[str, str]) -> list[dict[str, str]]:
    return [
        {
            "lexeme": lexeme,
            "token": token,
        }
        for lexeme, token in values.items()
    ]


def grammar_export_document() -> dict[str, object]:
    """Return the schema-1 machine-readable grammar document."""

    productions = parse_ebnf_productions()
    return {
        "schema": GRAMMAR_EXPORT_SCHEMA,
        "kind": GRAMMAR_EXPORT_KIND,
        "export_version": P10_T2_EXPORT_VERSION,
        "grammar_version": P10_T2_GRAMMAR_VERSION,
        "grammar_sha256": CANONICAL_GRAMMAR_SHA256,
        "source": {
            "extension": CANONICAL_SOURCE_EXTENSION,
            "glob": CANONICAL_SOURCE_GLOB,
            "main_filename": CANONICAL_MAIN_FILENAME,
        },
        "headers": {
            "keywords": list(MODULE_HEADER_KEYWORDS),
            "optional_semicolon": MODULE_HEADER_SEMICOLONS_OPTIONAL,
        },
        "boundaries": {
            "comments_supported": COMMENTS_SUPPORTED,
            "ordinary_semicolons_supported": ORDINARY_SEMICOLONS_SUPPORTED,
            "one_top_level_declaration_per_source": True,
        },
        "top_level_declarations": list(TOP_LEVEL_DECLARATIONS),
        "tokens": {
            "keywords": _token_documents(GRAMMAR_KEYWORD_TOKENS),
            "two_character": _token_documents(GRAMMAR_TWO_CHARACTER_TOKENS),
            "one_character": _token_documents(GRAMMAR_ONE_CHARACTER_TOKENS),
            "string_escapes": list(STRING_ESCAPE_SEQUENCES),
        },
        "productions": [
            production.to_document()
            for production in productions
        ],
        "ebnf": render_grammar_ebnf(),
        "notes": list(GRAMMAR_CONTRACT_NOTES),
    }


def render_grammar_json() -> str:
    """Return deterministic UTF-8 JSON for the grammar export document."""

    return json.dumps(
        grammar_export_document(),
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ) + "\n"


def grammar_export_fingerprint() -> str:
    """Return the SHA-256 of the exact canonical JSON export bytes."""

    return hashlib.sha256(render_grammar_json().encode("utf-8")).hexdigest()


# Filled with the hash of ``render_grammar_json()``. The smoke test rejects drift.
CANONICAL_GRAMMAR_EXPORT_SHA256: Final[str] = "d2ed66345cf66569cf9c673bc2f42cb1ea62592f9f371580796f0c97995e35ea"


def _write_export(
    path: Path,
    content: str,
    *,
    overwrite: bool,
) -> None:
    if path.exists():
        if not path.is_file():
            raise GrammarExportError(
                f"Grammar export destination is not a file: {path}."
            )
        existing = path.read_text(encoding="utf-8")
        if existing == content:
            return
        if not overwrite:
            raise GrammarExportError(
                f"Refusing to replace differing grammar export {path}."
            )

    with path.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(content)


def write_grammar_exports(
    output_directory: object,
    *,
    overwrite: bool = False,
) -> tuple[Path, Path]:
    """Write the canonical EBNF and JSON artifacts into one directory."""

    if type(overwrite) is not bool:
        raise TypeError("overwrite must be a bool.")

    try:
        directory = Path(output_directory)  # type: ignore[arg-type]
    except TypeError as exc:
        raise GrammarExportError(
            "Grammar export directory must be path-like."
        ) from exc

    if directory.exists() and not directory.is_dir():
        raise GrammarExportError(
            f"Grammar export destination is not a directory: {directory}."
        )
    directory.mkdir(parents=True, exist_ok=True)

    ebnf_path = directory / CANONICAL_EBNF_EXPORT_FILENAME
    json_path = directory / CANONICAL_JSON_EXPORT_FILENAME

    _write_export(ebnf_path, render_grammar_ebnf(), overwrite=overwrite)
    _write_export(json_path, render_grammar_json(), overwrite=overwrite)

    return ebnf_path, json_path


def verify_grammar_exports(output_directory: object) -> tuple[Path, Path]:
    """Require existing exports to match the canonical generated artifacts."""

    try:
        directory = Path(output_directory)  # type: ignore[arg-type]
    except TypeError as exc:
        raise GrammarExportError(
            "Grammar export directory must be path-like."
        ) from exc

    expected = (
        (directory / CANONICAL_EBNF_EXPORT_FILENAME, render_grammar_ebnf()),
        (directory / CANONICAL_JSON_EXPORT_FILENAME, render_grammar_json()),
    )

    for path, content in expected:
        if not path.is_file():
            raise GrammarExportError(
                f"Missing canonical grammar export {path}."
            )
        if path.read_text(encoding="utf-8") != content:
            raise GrammarExportError(
                f"Grammar export does not match the canonical contract: {path}."
            )

    return expected[0][0], expected[1][0]


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m language.grammar_export",
        description="Write or verify deterministic ApexForge grammar exports.",
    )
    parser.add_argument(
        "output_directory",
        nargs="?",
        default="spec",
        help="destination directory (default: spec)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify existing artifacts instead of writing them",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="replace differing artifacts while writing",
    )
    return parser


def main(
    argv: Optional[Sequence[str]] = None,
    *,
    stdout: TextIO = sys.stdout,
    stderr: TextIO = sys.stderr,
) -> int:
    """Run the standalone grammar-export utility."""

    parser = _build_parser()
    arguments = parser.parse_args(tuple(argv) if argv is not None else None)

    try:
        if arguments.check:
            paths = verify_grammar_exports(arguments.output_directory)
            verb = "Verified"
        else:
            paths = write_grammar_exports(
                arguments.output_directory,
                overwrite=arguments.overwrite,
            )
            verb = "Wrote"
    except GrammarExportError as error:
        print(str(error), file=stderr)
        return 1

    for path in paths:
        print(f"{verb}: {path}", file=stdout)
    return 0


__all__ = (
    "CANONICAL_EBNF_EXPORT_FILENAME",
    "CANONICAL_GRAMMAR_EXPORT_SHA256",
    "CANONICAL_JSON_EXPORT_FILENAME",
    "GRAMMAR_EXPORT_KIND",
    "GRAMMAR_EXPORT_SCHEMA",
    "GrammarExportError",
    "GrammarProduction",
    "P10_T2_EXPORT_VERSION",
    "grammar_export_document",
    "grammar_export_fingerprint",
    "main",
    "parse_ebnf_productions",
    "render_grammar_ebnf",
    "render_grammar_json",
    "verify_grammar_exports",
    "write_grammar_exports",
)


if __name__ == "__main__":
    raise SystemExit(main())