"""AFP-P10-T2.3 grammar-conformance corpus and final syntax audit."""

from __future__ import annotations

import shutil
import tempfile
from io import StringIO
from pathlib import Path

from language.grammar import (
    CANONICAL_GRAMMAR_SHA256,
    P10_T2_GRAMMAR_VERSION,
)
from language.grammar_conformance import (
    CANONICAL_CONFORMANCE_MANIFEST,
    CANONICAL_CONFORMANCE_SHA256,
    CONFORMANCE_KIND,
    CONFORMANCE_SCHEMA,
    GrammarConformanceError,
    P10_T2_CONFORMANCE_VERSION,
    audit_conformance_corpus,
    corpus_fingerprint,
    load_conformance_manifest,
    main as conformance_main,
)
from language.grammar_export import (
    CANONICAL_GRAMMAR_EXPORT_SHA256,
    P10_T2_EXPORT_VERSION,
    verify_grammar_exports,
)


EXPECTED_CORPUS_SHA256 = (
    "6bc21d12b6a667ba14e384f12e9b408a8c618a5eaf11dd91824c601745170884"
)
EXPECTED_VALID_SOURCE_IDS = (
    "function",
    "constrained-generic",
    "directive",
    "workflow",
    "authority",
    "role",
    "principal",
)
EXPECTED_INVALID_CODES = (
    ("unsupported-comment", "APX-LEX-001"),
    ("ordinary-semicolon", "APX-LEX-001"),
    ("malformed-float", "APX-LEX-005"),
    ("missing-return", "APX-PARSE-006"),
    ("misplaced-module", "APX-MODULE-001"),
    ("duplicate-import", "APX-MODULE-004"),
    ("invalid-generic", "APX-PARSE-014"),
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def require_conformance_error(operation, message: str) -> GrammarConformanceError:
    try:
        operation()
    except GrammarConformanceError as error:
        require(error.code == "APX-GRAMMAR-002", "conformance error code changed")
        return error
    raise AssertionError(message)


def main() -> None:
    require(P10_T2_CONFORMANCE_VERSION == "10-T2.3", "version changed")
    require(CONFORMANCE_SCHEMA == 1, "conformance schema changed")
    require(
        CONFORMANCE_KIND == "apexforge.grammar-conformance",
        "conformance kind changed",
    )
    require(
        CANONICAL_CONFORMANCE_MANIFEST == "corpus.json",
        "conformance manifest filename changed",
    )

    require(P10_T2_GRAMMAR_VERSION == "10-T2.1", "T2.1 version changed")
    require(P10_T2_EXPORT_VERSION == "10-T2.2", "T2.2 version changed")
    require(
        CANONICAL_GRAMMAR_SHA256
        == "09abf328030692267297950d8d5894e69f3d2c9c9af6642c90b9d298f3515f18",
        "T2.1 grammar fingerprint changed",
    )
    require(
        CANONICAL_GRAMMAR_EXPORT_SHA256
        == "d2ed66345cf66569cf9c673bc2f42cb1ea62592f9f371580796f0c97995e35ea",
        "T2.2 export fingerprint changed",
    )

    repository_root = Path(__file__).resolve().parent.parent
    specification_root = repository_root / "spec"
    corpus_root = specification_root / "conformance"

    verify_grammar_exports(specification_root)
    manifest = load_conformance_manifest(corpus_root)
    require(
        tuple(case.case_id for case in manifest.valid)
        == EXPECTED_VALID_SOURCE_IDS,
        "valid source case inventory changed",
    )
    require(
        tuple(case.case_id for case in manifest.projects) == ("module-project",),
        "module project inventory changed",
    )
    require(manifest.aggregate_entry == "Main", "aggregate entry changed")
    require(
        tuple((case.case_id, case.expected_code) for case in manifest.invalid)
        == EXPECTED_INVALID_CODES,
        "invalid diagnostic inventory changed",
    )

    require(
        corpus_fingerprint(corpus_root) == CANONICAL_CONFORMANCE_SHA256,
        "declared corpus fingerprint does not match exact corpus bytes",
    )
    require(
        CANONICAL_CONFORMANCE_SHA256 == EXPECTED_CORPUS_SHA256,
        "canonical corpus fingerprint changed",
    )

    audit = audit_conformance_corpus(corpus_root)
    require(audit.valid_source_count == 7, "valid source count changed")
    require(audit.project_count == 2, "project build count changed")
    require(audit.invalid_source_count == 7, "invalid source count changed")
    require(audit.source_file_count == 16, "corpus source-file count changed")
    require(audit.corpus_sha256 == EXPECTED_CORPUS_SHA256, "audit hash changed")

    stdout = StringIO()
    stderr = StringIO()
    exit_code = conformance_main(
        (str(corpus_root), "--check"),
        stdout=stdout,
        stderr=stderr,
    )
    require(exit_code == 0, "standalone conformance check failed")
    require(stderr.getvalue() == "", "successful conformance check wrote stderr")
    require(
        f"Corpus SHA-256: {EXPECTED_CORPUS_SHA256}\n" in stdout.getvalue(),
        "standalone check omitted the corpus fingerprint",
    )

    with tempfile.TemporaryDirectory() as temporary:
        temporary_root = Path(temporary)
        copied_specification = temporary_root / "spec"
        shutil.copytree(specification_root, copied_specification)
        copied_corpus = copied_specification / "conformance"
        copied_audit = audit_conformance_corpus(copied_corpus)
        require(
            copied_audit.corpus_sha256 == EXPECTED_CORPUS_SHA256,
            "copied corpus did not remain deterministic",
        )

        drifted_source = copied_corpus / "valid" / "function.apex"
        drifted_source.write_text(
            drifted_source.read_text(encoding="utf-8") + "\n",
            encoding="utf-8",
        )
        require_conformance_error(
            lambda: audit_conformance_corpus(copied_corpus),
            "drifted conformance corpus unexpectedly passed",
        )

    print("AFP-P10-T2.3 grammar conformance and final syntax audit passed.")
    print("Versioned positive and negative corpus: PASS")
    print("Lexer and parser acceptance cases: PASS")
    print("Module-header conformance: PASS")
    print("Compiler-supported aggregate project build: PASS")
    print("Explicit module project build: PASS")
    print("Deterministic negative diagnostics: PASS")
    print("Frozen EBNF and JSON export verification: PASS")
    print("Deterministic corpus SHA-256: PASS")
    print("Standalone conformance utility: PASS")
    print("Corpus drift rejection: PASS")


if __name__ == "__main__":
    main()
