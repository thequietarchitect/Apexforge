"""P11.8C canonical subject-reference/relationship/evidence smoke test."""

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
    from air.model import AIRDirective
    from authority.model import Principal
    from language.narrative_model import NarrativeIdentity
    from quad_vector.model import QuadVectorInput, ResultantVector
    from semantic_lattice.records import (
        SemanticLatticeEvidence,
        SemanticLatticeRelationship,
        SemanticLatticeSubjectReference,
    )

    narrative_identity = NarrativeIdentity(kind="character", path=("Traveler",))
    directive = AIRDirective(
        id="directive:GateDirective",
        name="GateDirective",
        principal="traveler-principal",
        authority_checks=(),
        causal_decisions=(),
    )
    principal = Principal(id="traveler-principal")
    quad_input = QuadVectorInput(identity="quad.input:gate")
    resultant = ResultantVector(
        x=10,
        y=4,
        provenance=("quad.input:gate",),
    )

    narrative = SemanticLatticeSubjectReference(
        source_domain="narrative",
        source_kind=narrative_identity.kind,
        source_identity=(narrative_identity.kind,) + narrative_identity.path,
    )
    air = SemanticLatticeSubjectReference(
        source_domain="air",
        source_kind="directive",
        source_identity=(directive.id,),
    )
    authority = SemanticLatticeSubjectReference(
        source_domain="authority",
        source_kind="principal",
        source_identity=(principal.id,),
    )
    quad = SemanticLatticeSubjectReference(
        source_domain="quad_vector",
        source_kind="input",
        source_identity=(quad_input.identity,),
    )

    require(
        narrative.source_identity == ("character", "Traveler")
        and air.source_identity == (directive.id,)
        and authority.source_identity == (principal.id,)
        and quad.source_identity == (quad_input.identity,),
        "source-domain canonical identity components changed",
    )
    print("Source-domain canonical identity reference preservation: PASS")

    evidence = SemanticLatticeEvidence(
        kind="observed",
        facts=(
            ("classification", "continuity"),
            ("resultant_coordinates", (resultant.x, resultant.y)),
            ("stable", True),
        ),
        provenance=resultant.provenance,
    )
    relation = SemanticLatticeRelationship(
        source=narrative,
        relation="governed_by",
        target=authority,
        evidence=(evidence,),
    )
    require(
        relation.source is narrative
        and relation.target is authority
        and relation.evidence[0] is evidence,
        "relationship lost exact supplied record identity",
    )
    print("Exact subject/relationship/evidence object preservation: PASS")

    require(
        "identity" not in ResultantVector.__dataclass_fields__
        and evidence.facts[1][1] == (10, 4)
        and evidence.provenance == resultant.provenance,
        "resultant evidence gained a fabricated source identity",
    )
    print("Resultant metadata projection without fabricated identity: PASS")

    raises(
        FrozenInstanceError,
        lambda: setattr(narrative, "source_kind", "changed"),
        "subject reference became mutable",
    )
    raises(
        FrozenInstanceError,
        lambda: setattr(evidence, "facts", ()),
        "evidence became mutable",
    )
    raises(
        FrozenInstanceError,
        lambda: setattr(relation, "relation", "changed"),
        "relationship became mutable",
    )
    print("Frozen subject/relationship/evidence boundary: PASS")

    raises(
        TypeError,
        lambda: SemanticLatticeSubjectReference("air", "directive", ["mutable"]),
        "mutable source identity container accepted",
    )
    raises(
        TypeError,
        lambda: SemanticLatticeEvidence("bad", facts=(("value", {"mutable": 1}),)),
        "mutable evidence value accepted",
    )
    raises(
        TypeError,
        lambda: SemanticLatticeRelationship(narrative, "bad", authority, evidence=[evidence]),
        "mutable evidence collection accepted",
    )
    print("Recursively immutable relationship-evidence contract: PASS")

    duplicate = SemanticLatticeRelationship(
        source=narrative,
        relation="related_to",
        target=air,
        evidence=(
            SemanticLatticeEvidence("first", provenance=("encounter:1",)),
            SemanticLatticeEvidence("second", provenance=("encounter:2",)),
        ),
    )
    require(
        tuple(item.kind for item in duplicate.evidence) == ("first", "second"),
        "evidence encounter order changed",
    )
    print("Deterministic encounter-order preservation: PASS")

    for name in (
        "execute",
        "run",
        "bind",
        "resolve",
        "select",
        "rank",
        "grant",
        "deny",
        "validate",
        "synchronize",
        "load",
        "import_module",
    ):
        require(
            not hasattr(relation, name)
            and not hasattr(narrative, name)
            and not hasattr(evidence, name),
            "operative behavior leaked into P11.8C records: " + name,
        )
    print("Passive non-operative lattice-record boundary: PASS")

    fields = SemanticLatticeSubjectReference.__dataclass_fields__
    require(
        tuple(fields) == ("source_domain", "source_kind", "source_identity"),
        "subject-reference shape changed or gained replacement identity",
    )
    print("Source identity indexing without replacement-identity contract: PASS")

    from semantic_lattice.model import ParametricSemanticLattice
    lattice = ParametricSemanticLattice()
    require(
        not hasattr(lattice, "subjects")
        and not hasattr(lattice, "relationships")
        and not hasattr(lattice, "evidence"),
        "P11.8D construction/indexing boundary was preempted",
    )
    print("P11.8D construction/indexing boundary preserved: PASS")


if __name__ == "__main__":
    main()
