"""Optional P11.13-C rich-document adapter for the existing Codex advisory path.

This module does not interpret rich-document block content and does not define a
second semantic-lattice or Codex semantics path. It only binds exact P11.13B
document/block lineage to an already-constructed P11.8 Codex advisory proposal,
then delegates adaptation and validation to the frozen semantic-lattice owners.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from rich_documents.model import (
    ApexDocument,
    ApexDocumentBlock,
    DocumentBlockKind,
)
from semantic_lattice.authoring import (
    SemanticLatticeAuthoringProposal,
    adapt_codex_semantic_lattice_proposal,
)
from semantic_lattice.construction import SemanticLatticeSnapshot
from semantic_lattice.validation import (
    SemanticLatticeAuthoringValidationReceipt,
    validate_codex_semantic_lattice_proposal,
)


CODEX_ADVISORY_BLOCK_KINDS: Tuple[DocumentBlockKind, ...] = (
    DocumentBlockKind.SEMANTIC_TABLE,
    DocumentBlockKind.DIAGRAM,
    DocumentBlockKind.WORLD_BIBLE,
    DocumentBlockKind.CHARACTER_SHEET,
    DocumentBlockKind.SIMULATION_DESCRIPTION,
)


@dataclass(frozen=True)
class CodexDocumentBlockAdvisory:
    """Caller-controlled binding of document lineage to a Codex proposal."""

    document: ApexDocument
    block: ApexDocumentBlock
    proposal: SemanticLatticeAuthoringProposal

    def __post_init__(self) -> None:
        if type(self.document) is not ApexDocument:
            raise TypeError(
                "CodexDocumentBlockAdvisory.document must be an exact "
                "ApexDocument"
            )
        if type(self.block) is not ApexDocumentBlock:
            raise TypeError(
                "CodexDocumentBlockAdvisory.block must be an exact "
                "ApexDocumentBlock"
            )
        if type(self.proposal) is not SemanticLatticeAuthoringProposal:
            raise TypeError(
                "CodexDocumentBlockAdvisory.proposal must be an exact "
                "SemanticLatticeAuthoringProposal"
            )
        if not any(candidate is self.block for candidate in self.document.blocks):
            raise ValueError(
                "CodexDocumentBlockAdvisory.block must be an exact block "
                "owned by document"
            )
        if self.block.kind not in CODEX_ADVISORY_BLOCK_KINDS:
            raise ValueError(
                "CodexDocumentBlockAdvisory.block kind is not eligible for "
                "the optional Codex advisory adapter"
            )


@dataclass(frozen=True)
class CodexDocumentBlockValidationReceipt:
    """Lineage-preserving wrapper around the canonical Codex validation receipt."""

    advisory: CodexDocumentBlockAdvisory
    validation: SemanticLatticeAuthoringValidationReceipt

    def __post_init__(self) -> None:
        if type(self.advisory) is not CodexDocumentBlockAdvisory:
            raise TypeError(
                "CodexDocumentBlockValidationReceipt.advisory must be an "
                "exact CodexDocumentBlockAdvisory"
            )
        if type(self.validation) is not SemanticLatticeAuthoringValidationReceipt:
            raise TypeError(
                "CodexDocumentBlockValidationReceipt.validation must be an "
                "exact SemanticLatticeAuthoringValidationReceipt"
            )
        if self.validation.proposal is not self.advisory.proposal:
            raise ValueError(
                "CodexDocumentBlockValidationReceipt validation proposal "
                "must preserve advisory proposal identity"
            )


def adapt_codex_document_block_advisory(
    advisory: CodexDocumentBlockAdvisory,
) -> SemanticLatticeSnapshot:
    """Adapt through the existing P11.8 Codex advisory owner."""

    if type(advisory) is not CodexDocumentBlockAdvisory:
        raise TypeError(
            "advisory must be an exact CodexDocumentBlockAdvisory"
        )
    return adapt_codex_semantic_lattice_proposal(advisory.proposal)


def validate_codex_document_block_advisory(
    advisory: CodexDocumentBlockAdvisory,
) -> CodexDocumentBlockValidationReceipt:
    """Validate through the existing P11.8 Codex validation owner."""

    if type(advisory) is not CodexDocumentBlockAdvisory:
        raise TypeError(
            "advisory must be an exact CodexDocumentBlockAdvisory"
        )
    validation = validate_codex_semantic_lattice_proposal(advisory.proposal)
    return CodexDocumentBlockValidationReceipt(
        advisory=advisory,
        validation=validation,
    )


__all__ = (
    "CODEX_ADVISORY_BLOCK_KINDS",
    "CodexDocumentBlockAdvisory",
    "CodexDocumentBlockValidationReceipt",
    "adapt_codex_document_block_advisory",
    "validate_codex_document_block_advisory",
)