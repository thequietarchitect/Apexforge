"""P11.13D .apexdoc parser, Apex extraction, and source-mapping smoke test."""

from __future__ import annotations

import ast
import dataclasses
from pathlib import Path
import subprocess

import rich_documents
import rich_documents.compilation as document_compilation
import rich_documents.parser as document_parser
from language.compiler import CompiledSource, compile_source_with_map
from language.parser import ParseError
from language.source import SourceSpan, SourceText
from rich_documents.compilation import (
    ApexExecutableBlockCompilation,
    ApexExecutableBlockSource,
    compile_apex_document_blocks,
    extract_apex_executable_blocks,
)
from rich_documents.model import (
    ApexDocument,
    ApexDocumentBlock,
    DocumentBlockKind,
)
from rich_documents.parser import parse_apex_document


PREDECESSOR_TAG = "afp-p11-13c-freeze"
PREDECESSOR_COMMIT = "b91cc3ea0ab47d560dff715deaf8a5d47ecf3156"

C_HASHES = {
    "apexforge/rich_documents/codex_adapter.py":
        "7050392B324CCEF128200DF478FC77DD17A90D72DBF356C084DD61F1E70899D2",
    "apexforge/p11_13c_experimental_codex_adapter_smoke_test.py":
        "15B55816663CD169D5D29D9E7FAA74F75511CCD478E85A802B7826D5FDCADCBB",
    "docs/p11/P11_13C_EXPERIMENTAL_CODEX_ADAPTER.md":
        "700829DA9F3977CBF566AC243F18E5291281F6D9AF093E032AD31E8324488EBC",
}

EXPECTED_ARTIFACTS = (
    "apexforge/rich_documents/parser.py",
    "apexforge/rich_documents/compilation.py",
    "apexforge/p11_13d_apexdoc_parser_executable_block_source_mapping_smoke_test.py",
    "docs/p11/P11_13D_APEXDOC_PARSER_EXECUTABLE_BLOCK_SOURCE_MAPPING.md",
)


def _root() -> Path:
    return Path(__file__).resolve().parents[1]


def _git(*arguments: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ("git", *arguments),
        cwd=_root(),
        check=False,
        text=True,
        encoding="utf-8",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _sha256(path: Path) -> str:
    import hashlib
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _raises(error_type, function, *args, **kwargs):
    try:
        function(*args, **kwargs)
    except error_type as error:
        return error
    except Exception as error:
        raise AssertionError(
            "expected {}, received {}: {}".format(
                error_type.__name__,
                type(error).__name__,
                error,
            )
        )
    raise AssertionError("expected {}".format(error_type.__name__))


def _assert_predecessor() -> None:
    resolved = _git("rev-parse", "{}^{{}}".format(PREDECESSOR_TAG))
    _require(resolved.returncode == 0, resolved.stderr.strip())
    _require(
        resolved.stdout.strip() == PREDECESSOR_COMMIT,
        "P11.13-C freeze target changed",
    )
    _require(
        _git(
            "merge-base",
            "--is-ancestor",
            PREDECESSOR_TAG,
            "HEAD",
        ).returncode == 0,
        "P11.13-C freeze is not ancestor of P11.13D",
    )
    for relative, expected in C_HASHES.items():
        _require(
            _sha256(_root() / relative) == expected,
            "{} frozen P11.13-C hash changed".format(relative),
        )


def _assert_public_surface() -> None:
    _require(rich_documents.__all__ == (), "package-level exports changed in D")
    _require(
        document_parser.__all__ == ("parse_apex_document",),
        "D parser public surface changed",
    )
    _require(
        document_compilation.__all__
        == (
            "ApexExecutableBlockSource",
            "ApexExecutableBlockCompilation",
            "extract_apex_executable_blocks",
            "compile_apex_document_blocks",
        ),
        "D compilation public surface changed",
    )


def _assert_immutable_compilation_models() -> None:
    expected = {
        ApexExecutableBlockSource:
            ("document_id", "block_id", "source_name", "text", "span"),
        ApexExecutableBlockCompilation:
            ("source", "compiled"),
    }
    for value, fields in expected.items():
        _require(dataclasses.is_dataclass(value), "{} not dataclass".format(value))
        _require(
            value.__dataclass_params__.frozen,
            "{} not frozen".format(value.__name__),
        )
        _require(
            tuple(value.__dataclass_fields__) == fields,
            "{} fields changed".format(value.__name__),
        )


def _fixture_source() -> str:
    return (
        "@apexdoc Guide\r\n"
        "\r\n"
        "@block text intro\r\n"
        "Hello\r\n"
        "World\r\n"
        "@endblock\r\n"
        "\r\n"
        "@block apex main\r\n"
        "directive Main {}\r\n"
        "@endblock\r\n"
    )


def _assert_parser() -> ApexDocument:
    source = _fixture_source()
    document_a = parse_apex_document("guide.apexdoc", source)
    document_b = parse_apex_document("guide.apexdoc", source)

    _require(type(document_a) is ApexDocument, "parser returned wrong document type")
    _require(document_a == document_b, "repeated parsing was not deterministic")
    _require(document_a.document_id == "Guide", "document ID changed")
    _require(document_a.source_name == "guide.apexdoc", "source name changed")
    _require(len(document_a.blocks) == 2, "block count changed")
    _require(
        tuple(block.kind for block in document_a.blocks)
        == (DocumentBlockKind.TEXT, DocumentBlockKind.APEX),
        "block order/kinds changed",
    )

    source_text = SourceText("guide.apexdoc", source)

    intro_start = source.index("Hello")
    intro_end = source.index("@endblock", intro_start)
    intro = document_a.blocks[0]
    _require(
        intro.content == source[intro_start:intro_end],
        "text block content was normalized",
    )
    _require(
        intro.content == "Hello\r\nWorld\r\n",
        "CRLF block content was not preserved",
    )
    _require(
        intro.span == source_text.span(intro_start, intro_end),
        "text block document span changed",
    )

    apex_start = source.index("directive Main {}")
    apex_end = source.index("@endblock", apex_start)
    apex = document_a.blocks[1]
    _require(
        apex.content == source[apex_start:apex_end],
        "Apex block content was normalized",
    )
    _require(
        apex.span == source_text.span(apex_start, apex_end),
        "Apex block document span changed",
    )
    _require(
        apex.span.start.line == 9
        and apex.span.start.column == 1,
        "Apex block start position changed",
    )

    return document_a


def _assert_parser_errors() -> None:
    cases = (
        (
            "APXDOC-PARSE-001",
            "",
        ),
        (
            "APXDOC-PARSE-001",
            "\n@apexdoc Guide\n",
        ),
        (
            "APXDOC-PARSE-002",
            "@apexdoc Guide\n@endblock\n",
        ),
        (
            "APXDOC-PARSE-003",
            "@apexdoc Guide\n@block  apex main\n@endblock\n",
        ),
        (
            "APXDOC-PARSE-004",
            "@apexdoc Guide\n@block unknown main\n@endblock\n",
        ),
        (
            "APXDOC-PARSE-005",
            (
                "@apexdoc Guide\n"
                "@block text outer\n"
                "@block text inner\n"
                "@endblock\n"
                "@endblock\n"
            ),
        ),
        (
            "APXDOC-PARSE-006",
            "@apexdoc Guide\n@block text main\ncontent\n",
        ),
        (
            "APXDOC-PARSE-007",
            (
                "@apexdoc Guide\n"
                "@block text same\n"
                "@endblock\n"
                "@block apex same\n"
                "directive Main {}\n"
                "@endblock\n"
            ),
        ),
        (
            "APXDOC-PARSE-008",
            "@apexdoc Guide\n# comment\n",
        ),
    )

    for code, source in cases:
        error = _raises(
            ParseError,
            parse_apex_document,
            "error.apexdoc",
            source,
        )
        _require(
            error.diagnostic.code == code,
            "expected {}, received {}".format(code, error.diagnostic.code),
        )
        _require(
            error.diagnostic.stage == "parse",
            "{} did not use parse diagnostic stage".format(code),
        )
        _require(
            error.diagnostic.span is not None
            and error.diagnostic.span.source_name == "error.apexdoc",
            "{} lost source-aware diagnostic span".format(code),
        )

    _raises(TypeError, parse_apex_document, 1, "@apexdoc Guide\n")
    _raises(ValueError, parse_apex_document, " guide.apexdoc ", "@apexdoc Guide\n")
    _raises(TypeError, parse_apex_document, "guide.apexdoc", b"bytes")


def _assert_exact_close_marker_rule() -> None:
    source = (
        "@apexdoc Guide\n"
        "@block text intro\n"
        "@endblock extra\n"
        "@endblock\n"
    )
    document = parse_apex_document("guide.apexdoc", source)
    _require(
        document.blocks[0].content == "@endblock extra\n",
        "non-exact close-marker line was treated as reserved syntax",
    )


def _assert_extraction_and_compilation(document: ApexDocument) -> None:
    extracted_a = extract_apex_executable_blocks(document)
    extracted_b = extract_apex_executable_blocks(document)

    _require(extracted_a == extracted_b, "repeated extraction not deterministic")
    _require(len(extracted_a) == 1, "extraction did not filter to Apex blocks")

    source = extracted_a[0]
    block = document.blocks[1]
    expected_virtual = "guide.apexdoc::apexdoc::Guide::main"

    _require(
        type(source) is ApexExecutableBlockSource,
        "extraction returned wrong source type",
    )
    _require(source.document_id == document.document_id, "document lineage lost")
    _require(source.block_id == block.block_id, "block lineage lost")
    _require(source.source_name == expected_virtual, "virtual source name changed")
    _require(source.text == block.content, "extracted Apex text changed")
    _require(source.span is block.span, "document block span identity changed")

    compiled_a = compile_apex_document_blocks(document)
    compiled_b = compile_apex_document_blocks(document)

    _require(compiled_a == compiled_b, "repeated block compilation not deterministic")
    _require(len(compiled_a) == 1, "compiled block count changed")
    result = compiled_a[0]
    _require(
        type(result) is ApexExecutableBlockCompilation,
        "compile adapter returned wrong wrapper type",
    )
    _require(result.source == source, "compiled wrapper source lineage changed")
    _require(
        type(result.compiled) is CompiledSource,
        "compile adapter did not return canonical CompiledSource",
    )

    direct = compile_source_with_map(
        source.text,
        source_name=source.source_name,
    )
    _require(
        result.compiled == direct,
        "D compilation diverged from canonical compile_source_with_map",
    )
    _require(
        all(
            entry.span.source_name == expected_virtual
            for entry in result.compiled.source_map.entries
        ),
        "canonical source map lost virtual block source identity",
    )
    _require(
        result.source.span == block.span,
        "original document span was not retained beside canonical source map",
    )


def _assert_compiler_error_virtual_source() -> None:
    document = parse_apex_document(
        "broken.apexdoc",
        (
            "@apexdoc Broken\n"
            "@block apex broken\n"
            "directive {\n"
            "@endblock\n"
        ),
    )
    expected = "broken.apexdoc::apexdoc::Broken::broken"

    try:
        compile_apex_document_blocks(document)
    except Exception as error:
        diagnostic = getattr(error, "diagnostic", None)
        _require(
            diagnostic is not None and diagnostic.span is not None,
            "canonical compiler error lost structured diagnostic",
        )
        _require(
            diagnostic.span.source_name == expected,
            "canonical compiler error lost virtual block source identity",
        )
    else:
        raise AssertionError("invalid Apex block unexpectedly compiled")


def _assert_empty_and_non_apex_documents() -> None:
    empty = parse_apex_document("empty.apexdoc", "@apexdoc Empty\n")
    _require(empty.blocks == (), "empty document gained blocks")
    _require(
        extract_apex_executable_blocks(empty) == (),
        "empty document gained executable sources",
    )
    _require(
        compile_apex_document_blocks(empty) == (),
        "empty document gained compiled products",
    )

    text_only = parse_apex_document(
        "text.apexdoc",
        (
            "@apexdoc Text\n"
            "@block text prose\n"
            "hello\n"
            "@endblock\n"
        ),
    )
    _require(
        extract_apex_executable_blocks(text_only) == (),
        "text block became executable",
    )


def _assert_nonoperative_boundaries() -> None:
    parser_path = _root() / "apexforge" / "rich_documents" / "parser.py"
    compilation_path = (
        _root() / "apexforge" / "rich_documents" / "compilation.py"
    )

    parser_tree = ast.parse(
        parser_path.read_text(encoding="utf-8"),
        filename=str(parser_path),
    )
    compilation_tree = ast.parse(
        compilation_path.read_text(encoding="utf-8"),
        filename=str(compilation_path),
    )

    parser_import_roots = set()
    compilation_import_roots = set()
    compilation_calls = []

    for node in ast.walk(parser_tree):
        if isinstance(node, ast.Import):
            parser_import_roots.update(
                alias.name.split(".", 1)[0] for alias in node.names
            )
        elif isinstance(node, ast.ImportFrom) and node.module:
            parser_import_roots.add(node.module.split(".", 1)[0])

    for node in ast.walk(compilation_tree):
        if isinstance(node, ast.Import):
            compilation_import_roots.update(
                alias.name.split(".", 1)[0] for alias in node.names
            )
        elif isinstance(node, ast.ImportFrom) and node.module:
            compilation_import_roots.add(node.module.split(".", 1)[0])
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                compilation_calls.append(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                compilation_calls.append(node.func.attr)

    _require(
        parser_import_roots
        <= {
            "__future__",
            "dataclasses",
            "re",
            "typing",
            "language",
            "rich_documents",
        },
        "D parser acquired unexpected imports: {}".format(parser_import_roots),
    )
    _require(
        compilation_import_roots
        <= {
            "__future__",
            "dataclasses",
            "typing",
            "language",
            "rich_documents",
        },
        "D compilation acquired unexpected imports: {}".format(
            compilation_import_roots
        ),
    )

    for forbidden in (
        "tooling",
        "incremental_cache",
        "tam",
        "tap_check",
        "runtime",
        "workflow",
        "semantic_lattice",
        "authority",
        "governance",
    ):
        _require(
            forbidden not in parser_import_roots
            and forbidden not in compilation_import_roots,
            "D imported premature subsystem: " + forbidden,
        )

    _require(
        compilation_calls.count("compile_source_with_map") == 1,
        "D compilation must contain exactly one canonical compiler call site",
    )

    for forbidden_call in (
        "build_project",
        "load_project",
        "execute",
        "run_air_program",
        "fetch",
        "open",
        "write",
        "adapt_codex_document_block_advisory",
        "validate_codex_document_block_advisory",
    ):
        _require(
            forbidden_call not in compilation_calls,
            "D compilation gained forbidden behavior: " + forbidden_call,
        )


def _assert_predecessor_owner_immutability() -> None:
    protected = (
        "apexforge/air",
        "apexforge/language",
        "apexforge/quad_vector",
        "apexforge/semantic_lattice",
        "apexforge/aether_air",
        "apexforge/tam",
        "apexforge/tap_check",
        "apexforge/runtime",
        "apexforge/workflow",
        "apexforge/tooling",
        "apexforge/type_system",
        "apexforge/governance",
        "apexforge/incremental_cache",
        "apexforge/standard_library",
        "apexforge/rich_documents/__init__.py",
        "apexforge/rich_documents/model.py",
        "apexforge/rich_documents/codex_adapter.py",
    )
    diff = _git("diff", "--exit-code", PREDECESSOR_TAG, "--", *protected)
    _require(diff.returncode == 0, "P11.13D mutated frozen predecessor owners")


def _assert_artifact_set() -> None:
    status = _git("status", "--porcelain=v1", "--untracked-files=all")
    _require(status.returncode == 0, status.stderr.strip())
    actual = tuple(
        line[3:].replace("\\", "/")
        for line in status.stdout.splitlines()
        if line.strip()
    )

    head_result = _git("rev-parse", "HEAD")
    _require(head_result.returncode == 0, head_result.stderr.strip())
    head = head_result.stdout.strip()

    if head == PREDECESSOR_COMMIT:
        _require(
            set(actual) == set(EXPECTED_ARTIFACTS),
            "P11.13D precommit artifact set changed: {}".format(actual),
        )
        return

    parent_result = _git("rev-parse", "HEAD^")
    _require(parent_result.returncode == 0, parent_result.stderr.strip())
    _require(
        parent_result.stdout.strip() == PREDECESSOR_COMMIT,
        "P11.13D committed-head parent is not frozen P11.13-C",
    )
    _require(
        not actual,
        "P11.13D committed-head working tree must be clean: {}".format(actual),
    )

    committed = tuple(
        line.strip().replace("\\", "/")
        for line in _git(
            "diff-tree",
            "--no-commit-id",
            "--name-only",
            "-r",
            "HEAD",
        ).stdout.splitlines()
        if line.strip()
    )
    _require(
        set(committed) == set(EXPECTED_ARTIFACTS),
        "P11.13D committed artifact set changed: {}".format(committed),
    )


def main() -> None:
    _assert_predecessor()
    _assert_public_surface()
    _assert_immutable_compilation_models()
    document = _assert_parser()
    _assert_parser_errors()
    _assert_exact_close_marker_rule()
    _assert_extraction_and_compilation(document)
    _assert_compiler_error_virtual_source()
    _assert_empty_and_non_apex_documents()
    _assert_nonoperative_boundaries()
    _assert_predecessor_owner_immutability()
    _assert_artifact_set()

    print("P11_13_C_FREEZE_ANCESTRY=PASS")
    print("P11_13_C_FROZEN_HASHES=PASS")
    print("RICH_DOCUMENT_PACKAGE_TOP_LEVEL_EXPORTS=UNCHANGED_EMPTY")
    print("APEXDOC_PARSER_PUBLIC_SYMBOL_COUNT=1")
    print("APEXDOC_COMPILATION_PUBLIC_SYMBOL_COUNT=4")
    print("APEXDOC_SYNTAX_HEADER=@apexdoc <document-id>")
    print("APEXDOC_SYNTAX_BLOCK_OPEN=@block <kind> <block-id>")
    print("APEXDOC_SYNTAX_BLOCK_CLOSE=@endblock")
    print("BLOCK_ORDER=SOURCE_ENCOUNTER_ORDER")
    print("BLOCK_CONTENT=EXACT_INPUT_STRING_PRESERVED")
    print("CRLF_CONTENT_PRESERVATION=PASS")
    print("BLOCK_SPAN_OWNER=language.source.SourceSpan")
    print("BLOCK_SPAN_RANGE=EXACT_CONTENT_END_EXCLUSIVE")
    print("UNKNOWN_BLOCK_KIND=PARSE_ERROR")
    print("DUPLICATE_BLOCK_ID=PARSE_ERROR")
    print("UNCLOSED_BLOCK=PARSE_ERROR")
    print("NESTED_BLOCK=PARSE_ERROR")
    print("OUTSIDE_NONBLANK_CONTENT=PARSE_ERROR")
    print("COMMENTS=NONE")
    print("EXACT_CLOSE_MARKER_RESERVATION=PASS")
    print("PARSER_RECOVERY=NONE")
    print("EXECUTABLE_SOURCE_TYPE=ApexExecutableBlockSource")
    print("EXECUTABLE_COMPILATION_TYPE=ApexExecutableBlockCompilation")
    print("EXECUTABLE_EXTRACTION_FILTER=apex")
    print("EXECUTABLE_EXTRACTION_ORDER=DOCUMENT_BLOCK_ORDER")
    print("VIRTUAL_SOURCE_NAME=DOCUMENT_SOURCE+DOCUMENT_ID+BLOCK_ID")
    print("CANONICAL_BLOCK_COMPILER=language.compiler.compile_source_with_map")
    print("CANONICAL_COMPILED_SOURCE=language.compiler.CompiledSource")
    print("CANONICAL_SOURCE_MAP=PRESERVED")
    print("ORIGINAL_DOCUMENT_BLOCK_SPAN=PRESERVED_BESIDE_SOURCE_MAP")
    print("CANONICAL_COMPILER_EQUIVALENCE=PASS")
    print("COMPILER_ERROR_VIRTUAL_SOURCE_IDENTITY=PASS")
    print("ALTERNATE_APEX_PARSER=NONE")
    print("ALTERNATE_APEX_COMPILER=NONE")
    print("PROJECT_BUILDER_MUTATION=NONE")
    print("PROJECT_LOADER_MUTATION=NONE")
    print("PROJECT_MANIFEST_MUTATION=NONE")
    print("CLI_MUTATION=NONE")
    print("CACHE_INTEGRATION=NONE")
    print("TAM_INTEGRATION=NONE")
    print("CODEX_AUTO_INVOCATION=NONE")
    print("RUNTIME_EXECUTION=NONE")
    print("PACKAGE_RESOLUTION=NONE")
    print("GLOBAL_MUTABLE_STATE=NONE")
    print("REMOTE_IO=NONE")
    print("PREDECESSOR_OWNER_MUTATION=NONE")
    print("P11_13D_APEXDOC_PARSER_EXECUTABLE_BLOCK_SOURCE_MAPPING=PASS")


if __name__ == "__main__":
    main()