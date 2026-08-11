"""P11.7I canonical Quad-Vector authoring-adapter red-gate smoke test."""

from __future__ import annotations

from dataclasses import FrozenInstanceError


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def expect_error(error_type, callback, message: str) -> None:
    try:
        callback()
    except error_type:
        return
    raise AssertionError(message)


def main() -> None:
    from quad_vector.model import QuadVectorLane, QuadVectorResourceBudget
    from quad_vector.module import QuadVectorModuleKind, QuadVectorModuleSpec
    from quad_vector.authoring.adapter import (
        QuadVectorAuthoredModule,
        QuadVectorAuthoringSource,
        QuadVectorModuleDeclaration,
        adapt_quad_vector_module_declaration,
    )

    require(
        tuple(item.value for item in QuadVectorAuthoringSource)
        == ("human", "tool", "advisory"),
        "canonical authoring source taxonomy changed",
    )

    budget = QuadVectorResourceBudget(
        max_modules=8,
        max_contributions=32,
        max_iterations=64,
    )
    declaration = QuadVectorModuleDeclaration(
        source=QuadVectorAuthoringSource.HUMAN,
        author_identity="author:quiet-architect",
        canonical_id="quad.module:AdaptiveBalance",
        version="1.0",
        kind=QuadVectorModuleKind.WEIGHTING_RULE,
        accepted_inputs=("quad.velocity", "quad.eligibility"),
        produced_outputs=("quad.weight",),
        eligible_vectors=(
            QuadVectorLane.POSITIVE_X,
            QuadVectorLane.NEGATIVE_X,
            QuadVectorLane.POSITIVE_Y,
            QuadVectorLane.NEGATIVE_Y,
        ),
        dependencies=(
            "quad.module:BaseVelocity",
            "quad.module:HighPressure",
        ),
        determinism_contract="pure-deterministic",
        authority_requirements=("quad.vector.read",),
        resource_budget=budget,
        implementation_reference="python:quad_plugins.adaptive_balance",
    )

    authored = adapt_quad_vector_module_declaration(declaration)

    require(
        type(authored) is QuadVectorAuthoredModule,
        "authoring adapter returned a non-canonical authored snapshot",
    )
    require(
        authored.source is QuadVectorAuthoringSource.HUMAN
        and authored.author_identity == "author:quiet-architect",
        "authoring provenance identity changed",
    )
    require(
        authored.declaration is declaration,
        "authoring adapter did not preserve the validated declaration object",
    )
    require(
        type(authored.spec) is QuadVectorModuleSpec,
        "authoring adapter did not produce a canonical module specification",
    )
    require(
        authored.spec.canonical_id == declaration.canonical_id
        and authored.spec.version == declaration.version
        and authored.spec.kind is declaration.kind
        and authored.spec.accepted_inputs == declaration.accepted_inputs
        and authored.spec.produced_outputs == declaration.produced_outputs
        and authored.spec.eligible_vectors == declaration.eligible_vectors
        and authored.spec.dependencies == declaration.dependencies
        and authored.spec.determinism_contract == declaration.determinism_contract
        and authored.spec.authority_requirements == declaration.authority_requirements
        and authored.spec.resource_budget is budget
        and authored.spec.implementation_reference == declaration.implementation_reference,
        "authoring adapter changed canonical module contract fields",
    )

    advisory = adapt_quad_vector_module_declaration(
        QuadVectorModuleDeclaration(
            source=QuadVectorAuthoringSource.ADVISORY,
            author_identity="advisor:codex-proposal",
            canonical_id="quad.module:AdvisoryCandidate",
            version="0.1",
            kind=QuadVectorModuleKind.FUNCTION,
            accepted_inputs=("quad.input",),
            produced_outputs=("quad.proposal",),
            eligible_vectors=(QuadVectorLane.POSITIVE_X,),
            dependencies=(),
            determinism_contract="pure-deterministic",
            authority_requirements=(),
            resource_budget=budget,
            implementation_reference="python:quad_plugins.advisory_candidate",
        )
    )
    require(
        advisory.spec.canonical_id == "quad.module:AdvisoryCandidate",
        "advisory source did not use the same canonical spec path",
    )

    expect_error(
        ValueError,
        lambda: QuadVectorModuleDeclaration(
            source=QuadVectorAuthoringSource.TOOL,
            author_identity="",
            canonical_id="quad.module:InvalidAuthor",
            version="1.0",
            kind=QuadVectorModuleKind.FUNCTION,
            accepted_inputs=(),
            produced_outputs=(),
            eligible_vectors=(),
            dependencies=(),
            determinism_contract="pure-deterministic",
            authority_requirements=(),
            resource_budget=budget,
            implementation_reference="python:quad_plugins.invalid",
        ),
        "authoring declaration accepted an empty author identity",
    )

    expect_error(
        ValueError,
        lambda: QuadVectorModuleDeclaration(
            source=QuadVectorAuthoringSource.TOOL,
            author_identity="tool:builder",
            canonical_id="quad.module:DuplicateDependency",
            version="1.0",
            kind=QuadVectorModuleKind.FUNCTION,
            accepted_inputs=(),
            produced_outputs=(),
            eligible_vectors=(),
            dependencies=("quad.module:Base", "quad.module:Base"),
            determinism_contract="pure-deterministic",
            authority_requirements=(),
            resource_budget=budget,
            implementation_reference="python:quad_plugins.duplicate_dependency",
        ),
        "authoring declaration accepted duplicate dependencies",
    )

    expect_error(
        TypeError,
        lambda: adapt_quad_vector_module_declaration(object()),
        "authoring adapter accepted a non-canonical declaration",
    )

    expect_error(
        FrozenInstanceError,
        lambda: setattr(authored, "author_identity", "mutated"),
        "authored module snapshot became mutable",
    )
    expect_error(
        FrozenInstanceError,
        lambda: setattr(declaration, "version", "2.0"),
        "module declaration became mutable",
   )

    for item in (declaration, authored):
        require(
            not hasattr(item, "register")
            and not hasattr(item, "bind")
            and not hasattr(item, "execute")
            and not hasattr(item, "run")
            and not hasattr(item, "load")
            and not hasattr(item, "import_module")
            and not hasattr(item, "codex"),
            "P11.7I authoring snapshot gained registry/runtime/loader privilege",
        )

    print("Canonical human/tool/advisory authoring source taxonomy: PASS")
    print("Authoring declaration-to-ModuleSpec translation: PASS")
    print("Author identity and source provenance preservation: PASS")
    print("Canonical module contract field preservation: PASS")
    print("Shared advisory-source validation path: PASS")
    print("Authoring declaration validation boundary: PASS")
    print("Immutable authoring snapshot boundary: PASS")
    print("P11.7I registry/binding/execution/loader privilege exclusion: PASS")


if __name__ == "__main__":
    main()
