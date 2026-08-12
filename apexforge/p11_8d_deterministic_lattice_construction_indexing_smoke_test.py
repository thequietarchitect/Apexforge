"""P11.8D deterministic lattice construction/indexing smoke test."""

from dataclasses import FrozenInstanceError


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
    from semantic_lattice.construction import (
        SemanticLatticeSnapshot,
        construct_semantic_lattice_snapshot,
        relationships_for_relation,
        relationships_from_subject,
        relationships_to_subject,
        subjects_for_domain,
        subjects_for_identity,
        subjects_for_kind,
    )
    from semantic_lattice.model import (
        ParametricSemanticLattice,
        SemanticLatticeParameter,
    )
    from semantic_lattice.records import (
        SemanticLatticeEvidence,
        SemanticLatticeRelationship,
        SemanticLatticeSubjectReference,
    )

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
    air = SemanticLatticeSubjectReference(
        source_domain="air",
        source_kind="directive",
        source_identity=("directive:GateDirective",),
    )

    evidence_a = SemanticLatticeEvidence(
        kind="observed",
        facts=(("classification", "continuity"),),
        provenance=("narrative:Traveler",),
    )
    evidence_b = SemanticLatticeEvidence(
        kind="observed",
        facts=(("classification", "authority"),),
        provenance=("authority:traveler-principal",),
    )
    relation_a = SemanticLatticeRelationship(
        source=narrative,
        relation="governed_by",
        target=authority,
        evidence=(evidence_a,),
    )
    relation_b = SemanticLatticeRelationship(
        source=air,
        relation="invoked_for",
        target=narrative,
        evidence=(evidence_b,),
    )
    lattice = ParametricSemanticLattice(
        parameters=(
            SemanticLatticeParameter("continuity", "status", "stable"),
            SemanticLatticeParameter("priority", "observed", 7),
        )
    )
    subjects = (narrative, authority, air)
    relationships = (relation_a, relation_b)
    snapshot = construct_semantic_lattice_snapshot(
        lattice,
        subjects=subjects,
        relationships=relationships,
    )

    require(
        snapshot.lattice is lattice
        and snapshot.subjects is subjects
        and snapshot.relationships is relationships
        and snapshot.subjects[0] is narrative
        and snapshot.relationships[0] is relation_a,
        "construction changed supplied canonical object identity",
    )
    print("Exact P11.8B/P11.8C object identity composition: PASS")

    require(
        snapshot.subjects == (narrative, authority, air)
        and snapshot.relationships == (relation_a, relation_b),
        "construction changed encounter order",
    )
    print("Deterministic encounter-order construction preservation: PASS")

    raises(
        ValueError,
        lambda: construct_semantic_lattice_snapshot(
            lattice,
            subjects=(narrative, narrative),
        ),
        "duplicate subject reference was accepted",
    )
    print("Duplicate canonical subject collision rejection: PASS")

    raises(
        ValueError,
        lambda: construct_semantic_lattice_snapshot(
            lattice,
            subjects=(narrative,),
            relationships=(relation_a,),
        ),
        "relationship with absent endpoint was accepted",
    )
    print("Relationship endpoint closure validation: PASS")

    require(
        subjects_for_domain(snapshot, "narrative") == (narrative,)
        and subjects_for_kind(snapshot, "principal") == (authority,)
        and subjects_for_identity(snapshot, ("directive:GateDirective",)) == (air,),
        "subject index projection changed",
    )
    print("Deterministic domain/kind/source-identity indexing: PASS")

    require(
        relationships_for_relation(snapshot, "governed_by") == (relation_a,)
        and relationships_from_subject(snapshot, air) == (relation_b,)
        and relationships_to_subject(snapshot, narrative) == (relation_b,),
        "relationship index projection changed",
    )
    print("Deterministic relationship indexing: PASS")

    raises(
        FrozenInstanceError,
        lambda: setattr(snapshot, "subjects", ()),
        "snapshot became mutable",
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
        "validate_authority",
        "synchronize",
        "load",
        "import_module",
    ):
        require(
            not hasattr(snapshot, name),
            "operative behavior leaked into lattice snapshot: " + name,
        )
    print("Immutable passive non-operative construction/index boundary: PASS")

    require(
        not hasattr(snapshot, "adapt")
        and not hasattr(snapshot, "project")
        and not hasattr(snapshot, "codex")
        and not hasattr(snapshot, "advisory"),
        "P11.8E adapter/Codex boundary was preempted",
    )
    print("P11.8E adapter and optional Codex boundary preserved: PASS")


if __name__ == "__main__":
    main()
