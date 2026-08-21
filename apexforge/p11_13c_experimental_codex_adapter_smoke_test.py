"""P11.13-C Experimental Codex Adapter smoke test."""

from __future__ import annotations

import ast
import dataclasses
from pathlib import Path
import subprocess

import rich_documents
import rich_documents.codex_adapter as codex_adapter
from rich_documents.codex_adapter import (
    CODEX_ADVISORY_BLOCK_KINDS,
    CodexDocumentBlockAdvisory,
    CodexDocumentBlockValidationReceipt,
    adapt_codex_document_block_advisory,
    validate_codex_document_block_advisory,
)
from rich_documents.model import (
    ApexDocument,
    ApexDocumentBlock,
    DocumentBlockKind,
)
from semantic_lattice.authoring import (
    SemanticLatticeAuthoringProposal,
    SemanticLatticeAuthoringSource,
)
from semantic_lattice.construction import SemanticLatticeSnapshot
from semantic_lattice.model import ParametricSemanticLattice
from semantic_lattice.validation import (
    SemanticLatticeAuthoringValidationReceipt,
)


PREDECESSOR_TAG = "afp-p11-13b-freeze"
PREDECESSOR_COMMIT = "a59e86e3acb22ca963eb4cdc18bdd42562afdd38"

B_HASHES = {
    "apexforge/rich_documents/__init__.py":
        "1EC51D9782581A72FCAB0921A0E9AC2AFB76682621AF3F3FEA752789785ACB3A",
    "apexforge/rich_documents/model.py":
        "8D9ED5088A30B10C15ACD55DF135DE03707FCABE06A808F5FAE336274DD35BC9",
    "apexforge/p11_13b_minimal_immutable_rich_document_package_tier_model_smoke_test.py":
        "281C3731DDE0CB9EF3E9D273CDC98ED9E35980B819E8C460EB747DD13A9D6764",
    "docs/p11/P11_13B_MINIMAL_IMMUTABLE_RICH_DOCUMENT_PACKAGE_TIER_MODEL.md":
        "1B546AEC4A18D970610C5EC455EC986C5D14A53A6D3DF756807163AC1BF2BFF6",
}

EXPECTED_ARTIFACTS = (
    "apexforge/rich_documents/codex_adapter.py",
    "apexforge/p11_13c_experimental_codex_adapter_smoke_test.py",
    "docs/p11/P11_13C_EXPERIMENTAL_CODEX_ADAPTER.md",
)

EXPECTED_PUBLIC = (
    "CODEX_ADVISORY_BLOCK_KINDS",
    "CodexDocumentBlockAdvisory",
    "CodexDocumentBlockValidationReceipt",
    "adapt_codex_document_block_advisory",
    "validate_codex_document_block_advisory",
)

EXPECTED_KINDS = (
    DocumentBlockKind.SEMANTIC_TABLE,
    DocumentBlockKind.DIAGRAM,
    DocumentBlockKind.WORLD_BIBLE,
    DocumentBlockKind.CHARACTER_SHEET,
    DocumentBlockKind.SIMULATION_DESCRIPTION,
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
        "P11.13B freeze target changed",
    )
    _require(
        _git(
            "merge-base",
            "--is-ancestor",
            PREDECESSOR_TAG,
            "HEAD",
        ).returncode == 0,
        "P11.13B freeze is not ancestor of P11.13-C",
    )
    for relative, expected in B_HASHES.items():
        _require(
            _sha256(_root() / relative) == expected,
            "{} frozen P11.13B hash changed".format(relative),
        )


def _assert_public_surface() -> None:
    _require(rich_documents.__all__ == (), "package-level exports changed in C")
    _require(
        codex_adapter.__all__ == EXPECTED_PUBLIC,
        "Codex adapter public surface changed",
    )
    _require(
        CODEX_ADVISORY_BLOCK_KINDS == EXPECTED_KINDS,
        "Codex advisory block-kind order changed",
    )


def _assert_immutable_wrappers() -> None:
    expected = {
        CodexDocumentBlockAdvisory:
            ("document", "block", "proposal"),
        CodexDocumentBlockValidationReceipt:
            ("advisory", "validation"),
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


def _fixture(kind: DocumentBlockKind = DocumentBlockKind.WORLD_BIBLE):
    block = ApexDocumentBlock(
        block_id="world",
        kind=kind,
        content="This content is deliberately not interpreted by P11.13-C.",
        metadata=(("projection", "codex-advisory"),),
    )
    document = ApexDocument(
        document_id="codex-guide",
        source_name="codex-guide.apexdoc",
        blocks=(block,),
        metadata=(("title", "Codex Guide"),),
    )
    proposal = SemanticLatticeAuthoringProposal(
        source=SemanticLatticeAuthoringSource.ADVISORY,
        author_identity="codex-session:p11.13c",
        provider_identity="codex",
        lattice=ParametricSemanticLattice(),
        subjects=(),
        relationships=(),
    )
    advisory = CodexDocumentBlockAdvisory(
        document=document,
        block=block,
        proposal=proposal,
    )
    return document, block, proposal, advisory


def _assert_owner_delegation() -> None:
    document, block, proposal, advisory = _fixture()

    snapshot_a = adapt_codex_document_block_advisory(advisory)
    snapshot_b = adapt_codex_document_block_advisory(advisory)

    _require(
        type(snapshot_a) is SemanticLatticeSnapshot,
        "adapter did not return canonical SemanticLatticeSnapshot",
    )
    _require(snapshot_a == snapshot_b, "repeated Codex adaptation not deterministic")
    _require(
        snapshot_a.lattice is proposal.lattice,
        "Codex adapter did not preserve proposal lattice identity",
    )
    _require(
        snapshot_a.subjects is proposal.subjects
        and snapshot_a.relationships is proposal.relationships,
        "Codex adapter did not preserve proposal tuple identity",
    )

    wrapped_a = validate_codex_document_block_advisory(advisory)
    wrapped_b = validate_codex_document_block_advisory(advisory)

    _require(
        type(wrapped_a) is CodexDocumentBlockValidationReceipt,
        "validation did not return exact C wrapper",
    )
    _require(
        type(wrapped_a.validation) is SemanticLatticeAuthoringValidationReceipt,
        "C validation did not preserve canonical P11.8 validation type",
    )
    _require(
        wrapped_a.validation.proposal is proposal,
        "C validation lost canonical proposal identity",
    )
    _require(
        wrapped_a.advisory is advisory,
        "C validation lost advisory lineage identity",
    )
    _require(
        wrapped_a == wrapped_b,
        "repeated C validation was not deterministic",
    )
    _require(advisory.document is document, "document lineage identity changed")
    _require(advisory.block is block, "block lineage identity changed")


def _assert_block_boundary() -> None:
    for kind in EXPECTED_KINDS:
        _fixture(kind)

    for kind in (
        DocumentBlockKind.TEXT,
        DocumentBlockKind.APEX,
    ):
        block = ApexDocumentBlock(
            block_id="unsupported",
            kind=kind,
            content="ignored",
        )
        document = ApexDocument(
            document_id="unsupported",
            source_name="unsupported.apexdoc",
            blocks=(block,),
        )
        proposal = SemanticLatticeAuthoringProposal(
            source=SemanticLatticeAuthoringSource.ADVISORY,
            author_identity="codex-session:p11.13c",
            provider_identity="codex",
            lattice=ParametricSemanticLattice(),
        )
        _raises(
            ValueError,
            CodexDocumentBlockAdvisory,
            document=document,
            block=block,
            proposal=proposal,
        )

    document, block, proposal, _ = _fixture()
    equal_copy = ApexDocumentBlock(
        block_id=block.block_id,
        kind=block.kind,
        content=block.content,
        span=block.span,
        metadata=block.metadata,
    )
    _require(equal_copy == block and equal_copy is not block, "copy fixture invalid")
    _raises(
        ValueError,
        CodexDocumentBlockAdvisory,
        document=document,
        block=equal_copy,
        proposal=proposal,
    )


def _assert_canonical_codex_policy_delegation() -> None:
    document, block, _, _ = _fixture()

    non_advisory = SemanticLatticeAuthoringProposal(
        source=SemanticLatticeAuthoringSource.TOOL,
        author_identity="tool:p11.13c",
        provider_identity="codex",
        lattice=ParametricSemanticLattice(),
    )
    advisory = CodexDocumentBlockAdvisory(
        document=document,
        block=block,
        proposal=non_advisory,
    )
    _raises(ValueError, adapt_codex_document_block_advisory, advisory)
    _raises(ValueError, validate_codex_document_block_advisory, advisory)

    wrong_provider = SemanticLatticeAuthoringProposal(
        source=SemanticLatticeAuthoringSource.ADVISORY,
        author_identity="advisor:p11.13c",
        provider_identity="other-provider",
        lattice=ParametricSemanticLattice(),
    )
    advisory = CodexDocumentBlockAdvisory(
        document=document,
        block=block,
        proposal=wrong_provider,
    )
    _raises(ValueError, adapt_codex_document_block_advisory, advisory)
    _raises(ValueError, validate_codex_document_block_advisory, advisory)


def _assert_nonoperative_shape() -> None:
    path = _root() / "apexforge" / "rich_documents" / "codex_adapter.py"
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

    import_roots = set()
    definitions = set()
    called_attributes = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            import_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                import_roots.add(node.module.split(".", 1)[0])
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            definitions.add(node.name.casefold())
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                called_attributes.add(node.func.attr.casefold())

    _require(
        import_roots
        <= {
            "__future__",
            "dataclasses",
            "typing",
            "rich_documents",
            "semantic_lattice",
        },
        "C adapter acquired unexpected subsystem imports: {}".format(import_roots),
    )

    for forbidden_root in (
        "tooling",
        "incremental_cache",
        "tam",
        "tap_check",
        "runtime",
        "workflow",
        "language",
        "authority",
        "governance",
    ):
        _require(
            forbidden_root not in import_roots,
            "C adapter imported forbidden subsystem: " + forbidden_root,
        )

    for forbidden in (
        "parse",
        "compile",
        "execute",
        "run",
        "load",
        "fetch",
        "open",
        "write",
        "resolve_package",
        "register",
        "mutate",
    ):
        _require(
            forbidden not in definitions
            and forbidden not in called_attributes,
            "operative behavior leaked into C adapter: " + forbidden,
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
    )
    diff = _git("diff", "--exit-code", PREDECESSOR_TAG, "--", *protected)
    _require(diff.returncode == 0, "P11.13-C mutated frozen predecessor owners")


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
            "P11.13-C precommit artifact set changed: {}".format(actual),
        )
        return

    parent_result = _git("rev-parse", "HEAD^")
    _require(parent_result.returncode == 0, parent_result.stderr.strip())
    _require(
        parent_result.stdout.strip() == PREDECESSOR_COMMIT,
        "P11.13-C committed-head parent is not frozen P11.13B",
    )
    _require(
        not actual,
        "P11.13-C committed-head working tree must be clean: {}".format(actual),
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
        "P11.13-C committed artifact set changed: {}".format(committed),
    )


def main() -> None:
    _assert_predecessor()
    _assert_public_surface()
    _assert_immutable_wrappers()
    _assert_owner_delegation()
    _assert_block_boundary()
    _assert_canonical_codex_policy_delegation()
    _assert_nonoperative_shape()
    _assert_predecessor_owner_immutability()
    _assert_artifact_set()

    print("P11_13B_FREEZE_ANCESTRY=PASS")
    print("P11_13B_FROZEN_HASHES=PASS")
    print("RICH_DOCUMENT_PACKAGE_TOP_LEVEL_EXPORTS=UNCHANGED_EMPTY")
    print("CODEX_ADAPTER_PUBLIC_SYMBOL_COUNT=5")
    print("CODEX_ADVISORY_BLOCK_KIND_COUNT=5")
    print(
        "CODEX_ADVISORY_BLOCK_KINDS={}".format(
            ",".join(kind.value for kind in CODEX_ADVISORY_BLOCK_KINDS)
        )
    )
    print("CODEX_ADAPTER_WRAPPER_TYPE_COUNT=2")
    print("CODEX_DOCUMENT_BLOCK_ADVISORY=FROZEN")
    print("CODEX_DOCUMENT_BLOCK_VALIDATION_RECEIPT=FROZEN")
    print("DOCUMENT_LINEAGE_IDENTITY=PRESERVED")
    print("BLOCK_LINEAGE_IDENTITY=PRESERVED")
    print("BLOCK_MEMBERSHIP=EXACT_DOCUMENT_OWNED_OBJECT")
    print("APEX_BLOCKS=REJECTED_NOT_INTERPRETED")
    print("TEXT_BLOCKS=REJECTED_NOT_INTERPRETED")
    print("BLOCK_CONTENT_INTERPRETATION=NONE")
    print("CANONICAL_CODEX_ADAPTATION_OWNER=semantic_lattice.authoring")
    print("CANONICAL_CODEX_VALIDATION_OWNER=semantic_lattice.validation")
    print("CANONICAL_SEMANTIC_LATTICE_SNAPSHOT=PRESERVED")
    print("CANONICAL_AUTHORING_VALIDATION_RECEIPT=PRESERVED")
    print("CODEX_SOURCE_PROVIDER_POLICY=DELEGATED_TO_EXISTING_OWNER")
    print("REPEATED_ADAPTATION=DETERMINISTIC")
    print("REPEATED_VALIDATION=DETERMINISTIC")
    print("PROJECT_LOADER_DEPENDENCY=NONE")
    print("CLI_DEPENDENCY=NONE")
    print("APEXDOC_PARSER_DEPENDENCY=NONE")
    print("CACHE_INTEGRATION=NONE")
    print("TAM_INTEGRATION=NONE")
    print("TAP_OWNERSHIP=NONE")
    print("RUNTIME_EXECUTION=NONE")
    print("GLOBAL_MUTABLE_STATE=NONE")
    print("REMOTE_IO=NONE")
    print("SEMANTIC_LATTICE_OWNER_MUTATION=NONE")
    print("RICH_DOCUMENT_MODEL_MUTATION=NONE")
    print("DETERMINISTIC_COMPILATION_DEPENDENCY=NONE")
    print("P11_13_C_EXPERIMENTAL_CODEX_ADAPTER=PASS")


if __name__ == "__main__":
    main()