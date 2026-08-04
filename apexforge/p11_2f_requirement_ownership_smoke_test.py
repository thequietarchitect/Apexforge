"""P11.2F-E static directive-requirement ownership coverage."""

from __future__ import annotations

from air.linker import link_programs
from air.model import (
    AIRDirective,
    AIRProgram,
    DirectiveRequirement,
)
from air.types import AIR_VERSION
from air.verify import AIRVerifier
from authority.model import Principal


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def owner_program(
    *names: str,
    requirements=(),
) -> AIRProgram:
    directives = tuple(
        AIRDirective(
            id=f"directive:{name}",
            name=name,
            principal=f"principal:{name}",
            authority_checks=(),
            causal_decisions=(),
            order=index,
        )
        for index, name in enumerate(names)
    )
    principals = tuple(
        Principal(
            id=directive.principal,
            display_name=directive.name,
        )
        for directive in directives
    )

    return AIRProgram(
        version=AIR_VERSION,
        states=(),
        events=(),
        authority_checks=(),
        causal_decisions=(),
        directives=directives,
        requirements=tuple(requirements),
        authorities=(),
        principals=principals,
        roles=(),
        functions=(),
        workflows=(),
    )


def projection(result) -> tuple[tuple[str, str, str], ...]:
    return tuple(
        (item.code, item.message, item.node_id)
        for item in result.diagnostics
    )


def test_direct_program_ownership() -> None:
    requirement = DirectiveRequirement(capability="Execute")
    single = AIRVerifier().verify(
        owner_program("Child", requirements=(requirement,))
    )
    require(single.ok, "single-directive requirement ownership failed")

    first = AIRVerifier().verify(
        owner_program(
            "Child",
            "Sibling",
            requirements=(requirement,),
        )
    )
    second = AIRVerifier().verify(
        owner_program(
            "Sibling",
            "Child",
            requirements=(requirement,),
        )
    )
    expected = (
        (
            "AIR065",
            "directive requirement ownership is ambiguous: "
            "expected exactly one owning directive, found 2: "
            "directive:Child, directive:Sibling",
            "directive:child",
        ),
    )
    require(
        projection(first) == expected,
        "direct ownership diagnostic changed: "
        + repr(projection(first)),
    )
    require(
        projection(second) == expected,
        "direct ownership diagnostic depends on directive order",
    )

    no_directive = AIRVerifier().verify(
        owner_program(requirements=(requirement,))
    )
    require(
        projection(no_directive)
        == (
            (
                "AIR065",
                "directive requirement ownership is ambiguous: "
                "expected exactly one owning directive, found 0: <none>",
                "requirements",
            ),
        ),
        "zero-directive requirement ownership was accepted",
    )


def test_owner_aware_linked_verification() -> None:
    alpha = owner_program(
        "Alpha",
        requirements=(
            DirectiveRequirement(capability="Observe"),
        ),
    )
    beta = owner_program(
        "Beta",
        requirements=(
            DirectiveRequirement(capability="Execute"),
        ),
    )
    linked = link_programs(alpha, beta)

    strict = AIRVerifier().verify(linked)
    require(
        tuple(item.code for item in strict.diagnostics) == ("AIR065",),
        "strict linked verification did not reject flattened ownership",
    )

    owners = {
        alpha.directives[0].id.casefold(): alpha,
        beta.directives[0].id.casefold(): beta,
    }
    owner_aware = AIRVerifier().verify(
        linked,
        directive_requirement_owners=owners,
    )
    require(
        owner_aware.ok,
        "owner-aware linked requirements did not verify: "
        + repr(projection(owner_aware)),
    )


def test_owner_aware_ambiguity() -> None:
    root = owner_program("Root")
    ambiguous = owner_program(
        "Child",
        "Sibling",
        requirements=(
            DirectiveRequirement(capability="Execute"),
        ),
    )
    linked = link_programs(root, ambiguous)
    owners = {
        root.directives[0].id.casefold(): root,
        ambiguous.directives[0].id.casefold(): ambiguous,
        ambiguous.directives[1].id.casefold(): ambiguous,
    }

    result = AIRVerifier().verify(
        linked,
        directive_requirement_owners=owners,
    )
    require(
        projection(result)
        == (
            (
                "AIR065",
                "directive requirement ownership is ambiguous: "
                "expected exactly one owning directive, found 2: "
                "directive:Child, directive:Sibling",
                "directive:child",
            ),
        ),
        "owner-aware ambiguity diagnostic changed: "
        + repr(projection(result)),
    )


def main() -> None:
    test_direct_program_ownership()
    test_owner_aware_linked_verification()
    test_owner_aware_ambiguity()
    print("P11.2F-E requirement ownership smoke test passed.")
    print("Direct single/ambiguous/empty ownership: PASS")
    print("Owner-aware linked verification: PASS")
    print("Owner-aware ambiguity rejection: PASS")


if __name__ == "__main__":
    main()
