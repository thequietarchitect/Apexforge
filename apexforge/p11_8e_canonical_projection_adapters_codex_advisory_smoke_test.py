"""P11.8E canonical projection adapters and optional Codex advisory smoke test."""

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
    from air.model import (
        AIRAuthority,
        AIRDirective,
        AIRPrincipal,
        AIRRole,
        AIRWorkflow,
        EventDefinition,
        EventRecord,
        StateDefinition,
    )
    from authority.model import AuthorityCheck, AuthorityGrant, Principal
    from language.narrative_model import NarrativeIdentity
    from quad_vector.model import QuadVectorInput, ResultantVector
    from semantic_lattice.adapters import (
        project_air_subject,
        project_authority_grant_evidence,
        project_authority_subject,
        project_narrative_subject,
        project_quad_vector_input_subject,
        project_resultant_vector_evidence,
        project_tam_traceability_parameter,
    )
    from semantic_lattice.authoring import (
        SemanticLatticeAuthoringProposal,
        SemanticLatticeAuthoringSource,
        adapt_codex_semantic_lattice_proposal,
        adapt_semantic_lattice_authoring_proposal,
    )
    from semantic_lattice.model import ParametricSemanticLattice
    from semantic_lattice.records import (
        SemanticLatticeRelationship,
        SemanticLatticeSubjectReference,
    )

    air_objects = (
        (StateDefinition("state:ready"), "state", "state:ready"),
        (EventDefinition("event:open", "Open"), "event_definition", "event:open"),
        (EventRecord("record:1", "event:open", "directive:gate", "traveler"), "event_record", "record:1"),
        (
            AIRDirective(
                "directive:gate",
                "Gate",
                "traveler",
                (),
                (),
            ),
            "directive",
            "directive:gate",
        ),
        (AIRAuthority("authority:gate", "GateAuthority", ()), "authority", "authority:gate"),
        (AIRWorkflow("workflow:gate", "GateWorkflow", ()), "workflow", "workflow:gate"),
        (AIRPrincipal("traveler", ()), "principal", "traveler"),
        (AIRRole("keeper", ()), "role", "keeper"),
    )
    for value, kind, identity in air_objects:
        projected = project_air_subject(value)
        require(
            projected.source_domain == "air"
            and projected.source_kind == kind
            and projected.source_identity == (identity,),
            "AIR identity projection changed source-owned identity",
        )
    print("AIR source-owned ID/name projection without fabricated identity: PASS")

    principal = Principal("traveler-principal")
    check = AuthorityCheck("check:gate", "traveler-principal", "enter", "gate")
    grant = AuthorityGrant("traveler-principal", "enter", "gate")
    require(
        project_authority_subject(principal).source_identity == ("traveler-principal",)
        and project_authority_subject(check).source_identity == ("check:gate",),
        "authority ID projection changed",
    )
    grant_evidence = project_authority_grant_evidence(grant)
    require(
        grant_evidence.kind == "authority_grant"
        and grant_evidence.facts
        == (
            ("principal", "traveler-principal"),
            ("capability", "enter"),
            ("resource", "gate"),
        ),
        "ID-less AuthorityGrant was not represented as evidence",
    )
    raises(
        TypeError,
        lambda: project_authority_subject(grant),
        "AuthorityGrant received a fabricated subject identity",
    )
    print("Authority canonical-ID projection and ID-less grant evidence boundary: PASS")

    narrative_identity = NarrativeIdentity("character", ("Traveler",))
    narrative_subject = project_narrative_subject(narrative_identity)
    require(
        narrative_subject.source_domain == "narrative"
        and narrative_subject.source_kind == "character"
        and narrative_subject.source_identity is narrative_identity.path,
        "NarrativeIdentity projection did not preserve canonical path tuple",
    )
    print("Narrative canonical kind/path projection preservation: PASS")

    qv_input = QuadVectorInput("quad.input:gate")
    qv_subject = project_quad_vector_input_subject(qv_input)
    resultant = ResultantVector(
        x=8,
        y=0,
        provenance=("quad.input:gate",),
    )
    resultant_evidence = project_resultant_vector_evidence(resultant)
    require(
        qv_subject.source_identity == ("quad.input:gate",)
        and resultant_evidence.kind == "quad_vector_resultant"
        and resultant_evidence.provenance is resultant.provenance
        and not hasattr(resultant, "identity"),
        "Quad-Vector projection fabricated or replaced resultant identity/provenance",
    )
    print("Quad-Vector input identity and ID-less resultant evidence projection: PASS")

    tam_parameter = project_tam_traceability_parameter(
        "continuity_token",
        ("TAM-v3", "stable"),
    )
    require(
        tam_parameter.axis_id == "tam.traceability"
        and tam_parameter.key == "continuity_token"
        and tam_parameter.value == ("TAM-v3", "stable"),
        "TAM traceability parameter projection changed",
    )
    require(
        not hasattr(tam_parameter, "source_identity"),
        "TAM traceability projection fabricated a TAM subject identity",
    )
    print("TAM traceability projection without fabricated runtime subject model: PASS")

    authority_subject = project_authority_subject(principal)
    relationship = SemanticLatticeRelationship(
        source=narrative_subject,
        relation="governed_by",
        target=authority_subject,
    )
    lattice = ParametricSemanticLattice(parameters=(tam_parameter,))
    proposal = SemanticLatticeAuthoringProposal(
        source=SemanticLatticeAuthoringSource.ADVISORY,
        author_identity="codex-session:1",
        provider_identity="codex",
        lattice=lattice,
        subjects=(narrative_subject, authority_subject),
        relationships=(relationship,),
    )
    ordinary_snapshot = adapt_semantic_lattice_authoring_proposal(proposal)
    codex_snapshot = adapt_codex_semantic_lattice_proposal(proposal)
    require(
        ordinary_snapshot == codex_snapshot
        and codex_snapshot.lattice is lattice
        and codex_snapshot.subjects is proposal.subjects
        and codex_snapshot.relationships is proposal.relationships,
        "Codex proposal did not use the ordinary P11.8D construction path",
    )
    print("Codex advisory proposal routed through ordinary P11.8D construction: PASS")

    raises(
        ValueError,
        lambda: adapt_codex_semantic_lattice_proposal(
            SemanticLatticeAuthoringProposal(
                source=SemanticLatticeAuthoringSource.TOOL,
                author_identity="tool:1",
                provider_identity="codex",
                lattice=ParametricSemanticLattice(),
            )
        ),
        "Codex accepted non-advisory authoring privilege",
    )
    raises(
        ValueError,
        lambda: adapt_codex_semantic_lattice_proposal(
            SemanticLatticeAuthoringProposal(
                source=SemanticLatticeAuthoringSource.ADVISORY,
                author_identity="advisor:1",
                provider_identity="other-provider",
                lattice=ParametricSemanticLattice(),
            )
        ),
        "Codex adapter accepted a different provider",
    )
    print("Codex advisory provenance and no-privilege contract: PASS")

    raises(
        FrozenInstanceError,
        lambda: setattr(proposal, "provider_identity", "changed"),
        "authoring proposal became mutable",
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
        "register",
        "mutate",
    ):
        require(
            not hasattr(proposal, name)
            and not hasattr(codex_snapshot, name),
            "operative privilege leaked into P11.8E: " + name,
        )
    print("Immutable passive adapter boundary with no execution/authority/import privilege: PASS")

    dangling = SemanticLatticeSubjectReference(
        source_domain="authority",
        source_kind="principal",
        source_identity=("absent-principal",),
    )
    raises(
        ValueError,
        lambda: SemanticLatticeAuthoringProposal(
            source=SemanticLatticeAuthoringSource.ADVISORY,
            author_identity="codex-session:2",
            provider_identity="codex",
            lattice=ParametricSemanticLattice(),
            subjects=(narrative_subject,),
            relationships=(
                SemanticLatticeRelationship(
                    source=narrative_subject,
                    relation="governed_by",
                    target=dangling,
                ),
            ),
        ),
        "authoring proposal bypassed P11.8D endpoint closure",
    )
    print("P11.8D structural validation remains authoritative for all authoring sources: PASS")


if __name__ == "__main__":
    main()
