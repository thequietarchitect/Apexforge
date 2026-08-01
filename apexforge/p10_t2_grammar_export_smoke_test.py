"""AFP-P10-T2.2 deterministic formal-grammar export smoke test."""

from __future__ import annotations

import json
import tempfile
from io import StringIO
from pathlib import Path

from language.grammar import (
    CANONICAL_GRAMMAR_SHA256,
    P10_T2_GRAMMAR_VERSION,
)
from language.grammar_export import (
    CANONICAL_EBNF_EXPORT_FILENAME,
    CANONICAL_GRAMMAR_EXPORT_SHA256,
    CANONICAL_JSON_EXPORT_FILENAME,
    GRAMMAR_EXPORT_KIND,
    GRAMMAR_EXPORT_SCHEMA,
    GrammarExportError,
    P10_T2_EXPORT_VERSION,
    grammar_export_document,
    grammar_export_fingerprint,
    main as export_main,
    parse_ebnf_productions,
    render_grammar_ebnf,
    render_grammar_json,
    verify_grammar_exports,
    write_grammar_exports,
)


EXPECTED_EXPORT_SHA256 = (
    "d2ed66345cf66569cf9c673bc2f42cb1ea62592f9f371580796f0c97995e35ea"
)
EXPECTED_PRODUCTION_COUNT = 55


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def require_export_error(operation, message: str) -> GrammarExportError:
    try:
        operation()
    except GrammarExportError as error:
        require(error.code == "APX-GRAMMAR-001", "grammar error code changed")
        return error
    raise AssertionError(message)


def main() -> None:
    require(P10_T2_EXPORT_VERSION == "10-T2.2", "export version changed")
    require(P10_T2_GRAMMAR_VERSION == "10-T2.1", "T2.1 grammar contract changed")
    require(GRAMMAR_EXPORT_SCHEMA == 1, "grammar export schema changed")
    require(
        GRAMMAR_EXPORT_KIND == "apexforge.syntax-grammar",
        "grammar export kind changed",
    )
    require(
        CANONICAL_EBNF_EXPORT_FILENAME == "apexforge.ebnf",
        "canonical EBNF filename changed",
    )
    require(
        CANONICAL_JSON_EXPORT_FILENAME == "apexforge.grammar.json",
        "canonical JSON filename changed",
    )

    productions = parse_ebnf_productions()
    require(
        len(productions) == EXPECTED_PRODUCTION_COUNT,
        "formal production inventory changed",
    )
    require(
        productions[0].name == "ApexForgeSource",
        "grammar root production changed",
    )
    names = tuple(production.name for production in productions)
    require(len(names) == len(set(names)), "duplicate formal production detected")
    for required_name in (
        "FunctionDeclaration",
        "DirectiveDeclaration",
        "PathAction",
        "Expression",
        "Primary",
        "String",
    ):
        require(required_name in names, f"missing grammar production {required_name}")

    require_export_error(
        lambda: parse_ebnf_productions("Root = Value ;\nRoot = Other ;\n"),
        "duplicate production unexpectedly succeeded",
    )
    require_export_error(
        lambda: parse_ebnf_productions("Root = Value\n"),
        "unterminated production unexpectedly succeeded",
    )

    document = grammar_export_document()
    require(document["schema"] == 1, "document schema changed")
    require(document["kind"] == GRAMMAR_EXPORT_KIND, "document kind changed")
    require(document["export_version"] == "10-T2.2", "document version changed")
    require(document["grammar_version"] == "10-T2.1", "grammar version changed")
    require(
        document["grammar_sha256"] == CANONICAL_GRAMMAR_SHA256,
        "T2.1 grammar fingerprint was not preserved",
    )
    require(
        document["source"]["extension"] == ".apex",  # type: ignore[index]
        "canonical source extension changed",
    )
    require(
        len(document["productions"]) == EXPECTED_PRODUCTION_COUNT,  # type: ignore[arg-type]
        "JSON production inventory changed",
    )

    rendered_json = render_grammar_json()
    decoded = json.loads(rendered_json)
    require(decoded == document, "rendered JSON does not match its document")
    require(render_grammar_ebnf().endswith("\n"), "EBNF lacks final newline")
    require(
        grammar_export_fingerprint() == CANONICAL_GRAMMAR_EXPORT_SHA256,
        "declared export fingerprint does not match rendered JSON",
    )
    require(
        CANONICAL_GRAMMAR_EXPORT_SHA256 == EXPECTED_EXPORT_SHA256,
        "canonical export fingerprint changed",
    )

    repository_root = Path(__file__).resolve().parent.parent
    specification_directory = repository_root / "spec"
    ebnf_path, json_path = verify_grammar_exports(specification_directory)
    require(
        ebnf_path.read_text(encoding="utf-8") == render_grammar_ebnf(),
        "repository EBNF artifact drifted",
    )
    require(
        json_path.read_text(encoding="utf-8") == rendered_json,
        "repository JSON artifact drifted",
    )

    with tempfile.TemporaryDirectory() as temporary:
        output_directory = Path(temporary) / "nested" / "spec"
        generated_ebnf, generated_json = write_grammar_exports(output_directory)
        require(generated_ebnf.is_file(), "generated EBNF file is missing")
        require(generated_json.is_file(), "generated JSON file is missing")
        verify_grammar_exports(output_directory)

        stdout = StringIO()
        stderr = StringIO()
        exit_code = export_main(
            (str(output_directory), "--check"),
            stdout=stdout,
            stderr=stderr,
        )
        require(exit_code == 0, "standalone export check failed")
        require(stderr.getvalue() == "", "successful export check wrote stderr")
        require(
            stdout.getvalue().count("Verified:") == 2,
            "standalone export check omitted artifact paths",
        )

        generated_json.write_text("{}\n", encoding="utf-8")
        require_export_error(
            lambda: verify_grammar_exports(output_directory),
            "drifted JSON export unexpectedly verified",
        )
        require_export_error(
            lambda: write_grammar_exports(output_directory),
            "differing JSON export was replaced without permission",
        )
        write_grammar_exports(output_directory, overwrite=True)
        verify_grammar_exports(output_directory)

    print("AFP-P10-T2.2 formal grammar export smoke test passed.")
    print("Ordered EBNF production model: PASS")
    print("Schema-1 JSON grammar document: PASS")
    print("Canonical EBNF artifact: PASS")
    print("Canonical JSON artifact: PASS")
    print("Deterministic export SHA-256: PASS")
    print("Write, verify, and overwrite controls: PASS")
    print("Standalone export utility: PASS")
    print("Frozen T2.1 grammar preservation: PASS")


if __name__ == "__main__":
    main()