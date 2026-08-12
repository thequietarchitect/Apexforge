"""P11.8F validation, collision, provenance, and extension-contract smoke test."""

from dataclasses import FrozenInstanceError

from semantic_lattice.authoring import (
    SemanticLatticeAuthoringProposal,
    SemanticLatticeAuthoringSource,
)
from semantic_lattice.construction import construct_semantic_lattice_snapshot
from semantic_lattice.model import (
    CORE_SEMANTIC_LATTICE_AXES,
    ParametricSemanticLattice,
    SemanticLatticeAxis,
    SemanticLatticeParameter,
)
from semantic_lattice.records import (
    SemanticLatticeEvidence,
    SemanticLatticeRelationship,
    SemanticLatticeSubjectReference,
)
from semantic_lattice.validation import (
    SemanticLatticeAuthoringValidationReceipt,
    SemanticLatticeValidationReceipt,
    validate_codex_semantic_lattice_proposal,
    validate_semantic_lattice_authoring_proposal,
    validate_semantic_lattice_snapshot,
)


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def raises(exc_type, fn, message):
    try:
        fn()
    except exc_type:
        return
    raise AssertionError(message)


def main():
    narrative = SemanticLatticeSubjectReference(
        source_domain="narrative",
        source_kind="character",
        source_identity=("character", "Traveler"),
    )
    authority = SemanticLatticeSubjectReference(
        source_domain="authority",
        source_kind="principal",
        source_identity=("traveler-principal",),
    )
    evidence = SemanticLatticeEvidence(
        kind="observed",
        facts=(("classification", "continuity"),),
        provenance=("narrative:Traveler",),
    )
    relation = SemanticLatticeRelationship(
        source=narrative,
        relation="governed_by",
        target=authority,
        evidence=(evidence,),
    )

    duplicate_axis_lattice = ParametricSemanticLattice(
        axes=CORE_SEMANTIC_LATTICE_AXES + (CORE_SEMANTIC_LATTICE_AXES[0],),
    )
    duplicate_axis_snapshot = construct_semantic_lattice_snapshot(
        duplicate_axis_lattice,
        subjects=(narrative, authority),
        relationships=(relation,),
    )
    raises(
        ValueError,
        lambda: validate_semantic_lattice_snapshot(duplicate_axis_snapshot),
        "duplicate axis canonical_id was accepted",
    )
    print("Canonical axis coordinate collision rejection: PASS")

    undeclared_parameter_lattice = ParametricSemanticLattice(
        parameters=(SemanticLatticeParameter("extension.missing", "flag", True),),
    )
    undeclared_parameter_snapshot = construct_semantic_lattice_snapshot(
        undeclared_parameter_lattice,
        subjects=(narrative, authority),
        relationships=(relation,),
    )
    raises(
        ValueError,
        lambda: validate_semantic_lattice_snapshot(undeclared_parameter_snapshot),
        "parameter referencing undeclared axis was accepted",
    )
    print("Parameter-to-axis closure validation: PASS")

    duplicate_parameter_lattice = ParametricSemanticLattice(
        parameters=(
            SemanticLatticeParameter("continuity", "status", "stable"),
            SemanticLatticeParameter("continuity", "status", "observed"),
        ),
    )
    duplicate_parameter_snapshot = construct_semantic_lattice_snapshot(
        duplicate_parameter_lattice,
        subjects=(narrative, authority),
        relationships=(relation,),
    )
    raises(
        ValueError,
        lambda: validate_semantic_lattice_snapshot(duplicate_parameter_snapshot),
        "duplicate parameter coordinate was accepted",
    )
    print("Parameter coordinate collision rejection: PASS")

    kind_collision = SemanticLatticeSubjectReference(
        source_domain="narrative",
        source_kind="scene",
        source_identity=("character", "Traveler"),
    )
    kind_collision_snapshot = construct_semantic_lattice_snapshot(
        ParametricSemanticLattice(),
        subjects=(narrative, kind_collision),
    )
    raises(
        ValueError,
        lambda: validate_semantic_lattice_snapshot(kind_collision_snapshot),
        "source-owned identity collision across kinds was accepted",
    )
    print("Cross-kind source identity collision rejection: PASS")

    duplicate_relationship_snapshot = construct_semantic_lattice_snapshot(
        ParametricSemanticLattice(),
        subjects=(narrative, authority),
        relationships=(relation, relation),
    )
    raises(
        ValueError,
        lambda: validate_semantic_lattice_snapshot(duplicate_relationship_snapshot),
        "duplicate relationship coordinate was accepted",
    )
    print("Relationship coordinate collision rejection: PASS")

    duplicate_evidence_relation = SemanticLatticeRelationship(
        source=narrative,
        relation="governed_by",
        target=authority,
        evidence=(evidence, evidence),
    )
    duplicate_evidence_snapshot = construct_semantic_lattice_snapshot(
        ParametricSemanticLattice(),
        subjects=(narrative, authority),
        relationships=(duplicate_evidence_relation,),
    )
    raises(
        ValueError,
        lambda: validate_semantic_lattice_snapshot(duplicate_evidence_snapshot),
        "duplicate evidence coordinate was accepted",
    )
    print("Relationship evidence coordinate collision rejection: PASS")

    duplicate_provenance = SemanticLatticeEvidence(
        kind="observed",
        facts=(("classification", "continuity"),),
        provenance=("source:1", "source:1"),
    )
    duplicate_provenance_relation = SemanticLatticeRelationship(
        source=narrative,
        relation="governed_by",
        target=authority,
        evidence=(duplicate_provenance,),
    )
    duplicate_provenance_snapshot = construct_semantic_lattice_snapshot(
        ParametricSemanticLattice(),
        subjects=(narrative, authority),
        relationships=(duplicate_provenance_relation,),
    )
    raises(
        ValueError,
        lambda: validate_semantic_lattice_snapshot(duplicate_provenance_snapshot),
        "duplicate provenance entry was accepted",
    )
    print("Evidence provenance integrity validation: PASS")

    extension = SemanticLatticeAxis("extension.example")
    extension_lattice = ParametricSemanticLattice(
        axes=CORE_SEMANTIC_LATTICE_AXES + (extension,),
        parameters=(SemanticLatticeParameter("extension.example", "mode", "passive"),),
    )
    extension_snapshot = construct_semantic_lattice_snapshot(
        extension_lattice,
        subjects=(narrative, authority),
        relationships=(relation,),
    )
    receipt = validate_semantic_lattice_snapshot(extension_snapshot)
    require(
        type(receipt) is SemanticLatticeValidationReceipt
        and receipt.snapshot is extension_snapshot
        and receipt.extension_axis_ids == ("extension.example",)
        and receipt.provenance == evidence.provenance
        and len(receipt.checks) == 8,
        "extension/provenance receipt changed canonical objects or ordering",
    )
    print("Extension-axis preservation and provenance receipt integrity: PASS")

    proposal = SemanticLatticeAuthoringProposal(
        source=SemanticLatticeAuthoringSource.TOOL,
        author_identity="tool:test",
        provider_identity="test-provider",
        lattice=extension_lattice,
        subjects=(narrative, authority),
        relationships=(relation,),
    )
    authored_receipt = validate_semantic_lattice_authoring_proposal(proposal)
    require(
        type(authored_receipt) is SemanticLatticeAuthoringValidationReceipt
        and authored_receipt.proposal is proposal
        and authored_receipt.snapshot_receipt.snapshot.lattice is extension_lattice,
        "ordinary authoring validation bypassed the E/D canonical path",
    )
    print("Ordinary authoring validation through frozen P11.8E/P11.8D path: PASS")

    codex = SemanticLatticeAuthoringProposal(
        source=SemanticLatticeAuthoringSource.ADVISORY,
        author_identity="codex-session:f",
        provider_identity="codex",
        lattice=extension_lattice,
        subjects=(narrative, authority),
        relationships=(relation,),
    )
    codex_receipt = validate_codex_semantic_lattice_proposal(codex)
    require(
        type(codex_receipt) is SemanticLatticeAuthoringValidationReceipt
        and codex_receipt.proposal is codex
        and codex_receipt.snapshot_receipt.snapshot.subjects is codex.subjects,
        "Codex validation gained a privileged or replacement construction path",
    )
    raises(
        ValueError,
        lambda: validate_codex_semantic_lattice_proposal(
            SemanticLatticeAuthoringProposal(
                source=SemanticLatticeAuthoringSource.TOOL,
                author_identity="codex-session:f",
                provider_identity="codex",
                lattice=extension_lattice,
                subjects=(narrative, authority),
                relationships=(relation,),
            )
        ),
        "Codex validation accepted non-advisory source",
    )
    print("Codex advisory validation and no-privilege contract: PASS")

    raises(
        FrozenInstanceError,
        lambda: setattr(receipt, "checks", ()),
        "validation receipt became mutable",
    )
    for name in (
        "execute",
        "run",
        "bind",
        "resolve",
        "select",
        "rank",
        "grant",
        "deny",
        "synchronize",
        "load",
        "import_module",
        "mutate",
    ):
        require(not hasattr(receipt, name), "operative behavior leaked into receipt: " + name)
    print("Immutable passive non-operative validation/receipt boundary: PASS")


if __name__ == "__main__":
    main()
