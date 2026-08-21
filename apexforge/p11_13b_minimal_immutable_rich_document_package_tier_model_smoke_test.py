"""P11.13B minimal immutable rich-document/package-tier model smoke test."""

from __future__ import annotations

import ast
import dataclasses
from pathlib import Path
import subprocess

import rich_documents
import rich_documents.model as model
from language.source import SourcePosition, SourceSpan
from rich_documents.model import (
    ApexDocument,
    ApexDocumentBlock,
    DOCUMENT_BLOCK_KIND_IDS,
    DocumentBlockKind,
    PACKAGE_TIER_IDS,
    PackageDescriptor,
    PackageTier,
    RICH_DOCUMENT_SCHEMA_VERSION,
)


PREDECESSOR_TAG = "afp-p11-13a-freeze"
PREDECESSOR_COMMIT = "01bfdc463b46b5032c6f541391be3aef1fd9ebe9"

A_HASHES = {
    "apexforge/p11_13a_rich_documents_package_architecture_audit_smoke_test.py":
        "F9942B6138CA7E947CE887249CACCCC580DDA735D9D033A9C8167E580A534D31",
    "docs/p11/P11_13A_RICH_DOCUMENTS_PACKAGE_ARCHITECTURE_AUDIT.md":
        "55625878D298887A678C25D6BFFF1ED024810A033C2C74BDE5B9F5BE4BC951D4",
}

EXPECTED_ARTIFACTS = (
    "apexforge/rich_documents/__init__.py",
    "apexforge/rich_documents/model.py",
    "apexforge/p11_13b_minimal_immutable_rich_document_package_tier_model_smoke_test.py",
    "docs/p11/P11_13B_MINIMAL_IMMUTABLE_RICH_DOCUMENT_PACKAGE_TIER_MODEL.md",
)

EXPECTED_MODEL_PUBLIC = (
    "RICH_DOCUMENT_SCHEMA_VERSION",
    "DOCUMENT_BLOCK_KIND_IDS",
    "PACKAGE_TIER_IDS",
    "DocumentBlockKind",
    "ApexDocumentBlock",
    "ApexDocument",
    "PackageTier",
    "PackageDescriptor",
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


def _raises(error_type, function, *args, **kwargs) -> None:
    try:
        function(*args, **kwargs)
    except error_type:
        return
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
        "P11.13A freeze target changed",
    )
    _require(
        _git(
            "merge-base",
            "--is-ancestor",
            PREDECESSOR_TAG,
            "HEAD",
        ).returncode == 0,
        "P11.13A freeze is not ancestor of P11.13B",
    )

    for relative, expected in A_HASHES.items():
        _require(
            _sha256(_root() / relative) == expected,
            "{} frozen P11.13A hash changed".format(relative),
        )


def _assert_public_surface() -> None:
    _require(rich_documents.__all__ == (), "package-level exports appeared")
    _require(model.__all__ == EXPECTED_MODEL_PUBLIC, "model public surface changed")
    _require(RICH_DOCUMENT_SCHEMA_VERSION == 1, "schema version changed")
    _require(
        DOCUMENT_BLOCK_KIND_IDS
        == (
            "text",
            "apex",
            "semantic-table",
            "diagram",
            "world-bible",
            "character-sheet",
            "simulation-description",
        ),
        "document block kind IDs changed",
    )
    _require(
        PACKAGE_TIER_IDS
        == ("core", "standard", "domain", "experimental"),
        "package tier IDs changed",
    )
    _require(
        tuple(value.value for value in DocumentBlockKind)
        == DOCUMENT_BLOCK_KIND_IDS,
        "DocumentBlockKind enum order/value changed",
    )
    _require(
        tuple(value.value for value in PackageTier) == PACKAGE_TIER_IDS,
        "PackageTier enum order/value changed",
    )


def _assert_immutable_models() -> None:
    expected_fields = {
        ApexDocumentBlock:
            ("block_id", "kind", "content", "span", "metadata"),
        ApexDocument:
            ("document_id", "source_name", "blocks", "metadata"),
        PackageDescriptor:
            ("package_id", "tier", "version", "documents", "metadata"),
    }
    for value, fields in expected_fields.items():
        _require(dataclasses.is_dataclass(value), "{} not dataclass".format(value))
        _require(
            value.__dataclass_params__.frozen,
            "{} not frozen".format(value.__name__),
        )
        _require(
            tuple(value.__dataclass_fields__) == fields,
            "{} fields changed".format(value.__name__),
        )


def _assert_document_model() -> None:
    span = SourceSpan(
        source_name="guide.apexdoc",
        start=SourcePosition(line=2, column=1, offset=8),
        end=SourcePosition(line=4, column=3, offset=31),
    )
    block_a = ApexDocumentBlock(
        block_id="intro",
        kind=DocumentBlockKind.TEXT,
        content="Exact prose.\n",
        span=span,
        metadata=(("role", "introduction"),),
    )
    block_b = ApexDocumentBlock(
        block_id="main",
        kind=DocumentBlockKind.APEX,
        content="directive Main {}\n",
        metadata=(("language", "apex"),),
    )
    document = ApexDocument(
        document_id="guide",
        source_name="guide.apexdoc",
        blocks=(block_a, block_b),
        metadata=(("title", "Guide"),),
    )

    _require(document.blocks == (block_a, block_b), "block order not preserved")
    _require(block_a.content == "Exact prose.\n", "block content normalized")
    _require(block_a.span is span, "SourceSpan reference changed")
    _require(
        document.metadata == (("title", "Guide"),),
        "document metadata order/value changed",
    )

    _raises(
        ValueError,
        ApexDocument,
        document_id="guide",
        source_name="guide.apexdoc",
        blocks=(block_a, block_a),
    )
    _raises(
        TypeError,
        ApexDocument,
        document_id="guide",
        source_name="guide.apexdoc",
        blocks=[block_a],
    )
    _raises(
        TypeError,
        ApexDocumentBlock,
        block_id="bad",
        kind="apex",
        content="x",
    )
    _raises(
        TypeError,
        ApexDocumentBlock,
        block_id="bad",
        kind=DocumentBlockKind.APEX,
        content="x",
        span=("fake",),
    )
    _raises(
        ValueError,
        ApexDocumentBlock,
        block_id="bad",
        kind=DocumentBlockKind.TEXT,
        content="x",
        metadata=(("k", "1"), ("k", "2")),
    )


def _assert_package_model() -> None:
    descriptor = PackageDescriptor(
        package_id="example.docs",
        tier=PackageTier.DOMAIN,
        version="draft-1",
        documents=("guide", "world"),
        metadata=(("owner", "example"),),
    )
    _require(
        descriptor.documents == ("guide", "world"),
        "package document order changed",
    )
    _require(
        descriptor.version == "draft-1",
        "B treated version as semantic version",
    )

    _raises(
        ValueError,
        PackageDescriptor,
        package_id="example.docs",
        tier=PackageTier.DOMAIN,
        version="draft-1",
        documents=("guide", "guide"),
    )
    _raises(
        TypeError,
        PackageDescriptor,
        package_id="example.docs",
        tier="domain",
        version="draft-1",
    )
    _raises(
        TypeError,
        PackageDescriptor,
        package_id="example.docs",
        tier=PackageTier.DOMAIN,
        version="draft-1",
        documents=["guide"],
    )


def _assert_no_premature_integration() -> None:
    path = _root() / "apexforge" / "rich_documents" / "model.py"
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

    import_roots = set()
    calls = set()
    definitions = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            import_roots.update(
                alias.name.split(".", 1)[0]
                for alias in node.names
            )
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                import_roots.add(node.module.split(".", 1)[0])
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            definitions.add(node.name.casefold())
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                calls.add(node.func.id.casefold())
            elif isinstance(node.func, ast.Attribute):
                calls.add(node.func.attr.casefold())

    _require(
        import_roots <= {"__future__", "dataclasses", "enum", "typing", "language"},
        "B model acquired premature subsystem imports: {}".format(import_roots),
    )
    for forbidden_root in (
        "tooling",
        "incremental_cache",
        "tam",
        "tap_check",
        "runtime",
        "workflow",
        "semantic_lattice",
    ):
        _require(
            forbidden_root not in import_roots,
            "B model imported premature owner: " + forbidden_root,
        )

    for forbidden in (
        "parse",
        "compile",
        "build_project",
        "execute",
        "run_air_program",
        "load_project",
        "fetch",
        "resolve_package",
    ):
        _require(
            forbidden not in definitions and forbidden not in calls,
            "B model acquired premature behavior: " + forbidden,
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
    )
    diff = _git("diff", "--exit-code", PREDECESSOR_TAG, "--", *protected)
    _require(diff.returncode == 0, "P11.13B mutated predecessor semantic owners")


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
            "P11.13B precommit artifact set changed: {}".format(actual),
        )
        return

    parent_result = _git("rev-parse", "HEAD^")
    _require(parent_result.returncode == 0, parent_result.stderr.strip())
    _require(
        parent_result.stdout.strip() == PREDECESSOR_COMMIT,
        "P11.13B committed-head parent is not the frozen predecessor",
    )
    _require(
        not actual,
        "P11.13B committed-head working tree must be clean: {}".format(actual),
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
        "P11.13B committed artifact set changed: {}".format(committed),
    )


def main() -> None:
    _assert_predecessor()
    _assert_public_surface()
    _assert_immutable_models()
    _assert_document_model()
    _assert_package_model()
    _assert_no_premature_integration()
    _assert_predecessor_owner_immutability()
    _assert_artifact_set()

    print("P11_13A_FREEZE_ANCESTRY=PASS")
    print("P11_13A_FROZEN_HASHES=PASS")
    print("RICH_DOCUMENT_SCHEMA_VERSION=1")
    print("RICH_DOCUMENT_PACKAGE_TOP_LEVEL_EXPORTS=NONE")
    print("RICH_DOCUMENT_MODEL_PUBLIC_SYMBOL_COUNT=8")
    print("DOCUMENT_BLOCK_KIND_COUNT=7")
    print("DOCUMENT_BLOCK_KIND_IDS={}".format(",".join(DOCUMENT_BLOCK_KIND_IDS)))
    print("PACKAGE_TIER_COUNT=4")
    print("PACKAGE_TIER_IDS={}".format(",".join(PACKAGE_TIER_IDS)))
    print("IMMUTABLE_MODEL_TYPE_COUNT=3")
    print("APEX_DOCUMENT_BLOCK=PASS")
    print("APEX_DOCUMENT=PASS")
    print("PACKAGE_DESCRIPTOR=PASS")
    print("SOURCE_SPAN_OWNER=language.source.SourceSpan")
    print("BLOCK_CONTENT=EXACT_STRING_PRESERVED")
    print("CALLER_ORDER=PRESERVED")
    print("DUPLICATE_BLOCK_IDS=REJECTED")
    print("DUPLICATE_PACKAGE_DOCUMENT_IDS=REJECTED")
    print("METADATA=IMMUTABLE_ORDERED_STRING_PAIRS")
    print("DUPLICATE_METADATA_KEYS=REJECTED")
    print("PACKAGE_VERSION=OPAQUE_DETERMINISTIC_STRING")
    print("APEXDOC_PARSING=NONE")
    print("EXECUTABLE_BLOCK_COMPILATION=NONE")
    print("PROJECT_MANIFEST_MUTATION=NONE")
    print("CLI_MUTATION=NONE")
    print("PACKAGE_DEPENDENCY_SOLVER=NONE")
    print("REMOTE_PACKAGE_FETCH=NONE")
    print("LOCKFILE=NONE")
    print("CACHE_INTEGRATION=NONE")
    print("TAM_INTEGRATION=NONE")
    print("TAP_OWNERSHIP=NONE")
    print("RUNTIME_EXECUTION=NONE")
    print("NARRATIVE_SEMANTIC_DUPLICATION=NONE")
    print("CODEX_DEPENDENCY=NONE")
    print("PREDECESSOR_SEMANTIC_OWNER_MUTATION=NONE")
    print("P11_13B_MINIMAL_IMMUTABLE_RICH_DOCUMENT_PACKAGE_TIER_MODEL=PASS")


if __name__ == "__main__":
    main()