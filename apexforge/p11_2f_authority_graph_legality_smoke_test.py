"""P11.2F-D authority, role, and principal graph legality coverage."""

from __future__ import annotations

from air.model import (
    AIRAuthority,
    AIRPrincipal,
    AIRProgram,
    AIRRole,
    AIRRoleAuthority,
    PrincipalAuthority,
)
from air.types import AIR_VERSION
from air.verify import AIRVerifier
from authority.model import Principal
from authority.registry import (
    AuthorityRegistry,
    DuplicateAuthorityError,
)
from authorization.role_resolver import resolve_effective_authorities
from role.registry import RoleRegistry


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def program(
    *,
    authorities=(),
    principals=(),
    roles=(),
) -> AIRProgram:
    return AIRProgram(
        version=AIR_VERSION,
        states=(),
        events=(),
        authority_checks=(),
        causal_decisions=(),
        directives=(),
        requirements=(),
        authorities=tuple(authorities),
        principals=tuple(principals),
        roles=tuple(roles),
        functions=(),
        workflows=(),
    )


def projection(result) -> tuple[tuple[str, str, str], ...]:
    return tuple(
        (item.code, item.message, item.node_id)
        for item in result.diagnostics
    )


def test_valid_graph_and_case_semantics() -> None:
    base = AIRAuthority(
        id="authority:Base",
        name="Base",
        capabilities=("Observe",),
    )
    child = AIRAuthority(
        id="authority:Child",
        name="Child",
        capabilities=("Execute",),
        inherits=("bAsE",),
    )
    role = AIRRole(
        name="Architect",
        authorities=(
            AIRRoleAuthority(name="cHiLd"),
        ),
    )
    principal = Principal(
        id="principal:Operator",
        display_name="Operator",
        roles=("Architect",),
        authorities=(
            PrincipalAuthority(name="BASE"),
        ),
    )

    result = AIRVerifier().verify(
        program(
            authorities=(base, child),
            principals=(principal,),
            roles=(role,),
        )
    )
    require(
        result.ok,
        "valid authority/principal/role graph did not verify: "
        + repr(projection(result)),
    )


def test_invalid_graph_diagnostics_are_deterministic() -> None:
    authority_a = AIRAuthority(
        id="authority:A",
        name="A",
        capabilities=(),
        inherits=("B",),
    )
    authority_b = AIRAuthority(
        id="authority:B",
        name="B",
        capabilities=(),
        inherits=("A",),
    )
    authority_c = AIRAuthority(
        id="authority:C",
        name="C",
        capabilities=(),
        inherits=("MissingParent",),
    )
    role = AIRRole(
        name="Architect",
        authorities=(
            AIRRoleAuthority(name="MissingRoleAuthority"),
        ),
    )
    principal = Principal(
        id="principal:Operator",
        display_name="Operator",
        roles=("MissingRole",),
        authorities=(
            PrincipalAuthority(name="MissingPrincipalAuthority"),
        ),
    )

    first_program = program(
        authorities=(authority_c, authority_b, authority_a),
        principals=(principal,),
        roles=(role,),
    )
    second_program = program(
        authorities=(authority_a, authority_b, authority_c),
        principals=(principal,),
        roles=(role,),
    )

    expected = (
        (
            "AIR060",
            "authority inheritance target does not exist: MissingParent",
            "authority:C",
        ),
        (
            "AIR061",
            "authority inheritance cycle: "
            "authority:a -> authority:b -> authority:a",
            "authority:a",
        ),
        (
            "AIR062",
            "principal authority does not exist: "
            "MissingPrincipalAuthority",
            "principal:Operator",
        ),
        (
            "AIR063",
            "principal role does not exist: MissingRole",
            "principal:Operator",
        ),
        (
            "AIR064",
            "role authority does not exist: MissingRoleAuthority",
            "role:Architect",
        ),
    )

    first = AIRVerifier().verify(first_program)
    second = AIRVerifier().verify(second_program)

    require(
        projection(first) == expected,
        "authority graph diagnostics changed: " + repr(projection(first)),
    )
    require(
        projection(second) == expected,
        "authority graph diagnostics depend on declaration order",
    )
    require(
        projection(AIRVerifier().verify(first_program)) == expected,
        "authority graph diagnostics changed across repeated verification",
    )


def test_authority_registry_rejects_canonical_duplicates() -> None:
    first = AIRAuthority(
        id="authority:AegisUpper",
        name="Aegis",
        capabilities=("Protect",),
    )
    second = AIRAuthority(
        id="authority:AegisLower",
        name="aegis",
        capabilities=("Override",),
    )

    messages = []

    for initial, duplicate in (
        (first, second),
        (second, first),
    ):
        registry = AuthorityRegistry()
        registry.register(initial)

        try:
            registry.register(duplicate)
        except DuplicateAuthorityError as error:
            messages.append(str(error))
            require(
                registry.get("AEGIS") is initial,
                "duplicate registration replaced the original authority",
            )
        else:
            raise AssertionError(
                "case-equivalent authority registration was accepted"
            )

    require(
        tuple(messages)
        == (
            "Authority 'aegis' is already registered.",
            "Authority 'aegis' is already registered.",
        ),
        "duplicate authority diagnostic depends on registration order",
    )


def test_registry_inheritance_and_resolver_deduplication() -> None:
    registry = AuthorityRegistry()
    registry.register(
        AIRAuthority(
            id="authority:Base",
            name="Base",
            capabilities=("Observe",),
        )
    )
    registry.register(
        AIRAuthority(
            id="authority:Child",
            name="Child",
            capabilities=("Execute",),
            inherits=("bAsE",),
        )
    )
    require(
        registry.resolve_capabilities("cHiLd")
        == {"Observe", "Execute"},
        "case-insensitive authority inheritance changed",
    )

    roles = RoleRegistry()
    roles.register(
        AIRRole(
            name="Architect",
            authorities=(
                AIRRoleAuthority(name="aegis"),
            ),
        )
    )
    principal = AIRPrincipal(
        name="Operator",
        authorities=(
            PrincipalAuthority(name="Aegis"),
        ),
        roles=("Architect",),
    )
    resolved = resolve_effective_authorities(principal, roles)
    require(
        tuple(item.name for item in resolved) == ("Aegis",),
        "case-equivalent effective authorities were not deduplicated",
    )


def main() -> None:
    test_valid_graph_and_case_semantics()
    test_invalid_graph_diagnostics_are_deterministic()
    test_authority_registry_rejects_canonical_duplicates()
    test_registry_inheritance_and_resolver_deduplication()
    print("P11.2F-D authority graph legality smoke test passed.")
    print("Valid authority/principal/role graph: PASS")
    print("Unknown references and deterministic cycles: PASS")
    print("Duplicate-safe authority registration: PASS")
    print("Registry inheritance and resolver deduplication: PASS")


if __name__ == "__main__":
    main()
