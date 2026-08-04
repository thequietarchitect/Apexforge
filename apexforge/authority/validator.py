from authority.registry import AuthorityRegistry, UnknownAuthorityError
from authority.model import Principal
from air.model import AIRProgram, AIRPrincipal, PrincipalAuthority
from authorization.role_resolver import resolve_effective_authorities
from role.registry import RoleRegistry

class AuthorityValidationError(Exception):
    pass


def validate_authorities(program, registry):
    for authority in program.authorities:
        grant = registry.get(authority.name)

        if grant is None:
            raise AuthorityValidationError(
                f"Missing directive authority: {authority.name}"
            )

class AuthorizationError(Exception):
    pass

def validate_requirements(
    program,
    registry: AuthorityRegistry,
    principal: Principal,
) -> None:
    for requirement in program.requirements:
        for authority in principal.authorities:
            if registry.has_capability(
                authority.name,
                requirement.capability,
            ):
                break
        else:
            raise AuthorizationError(
                f"{principal.id} lacks capability "
                f"'{requirement.capability}'"
            )

class UnknownPrincipalAuthorityError(Exception):
    pass


def validate_principal_authorities(
    program: AIRProgram,
    authority_registry,
) -> None:
    for principal in program.principals:
        for authority in principal.authorities:
            if authority_registry.get(authority.name) is None:
                raise UnknownPrincipalAuthorityError(
                    f"Principal {principal.id} references "
                    f"unknown authority {authority.name}"
                )

class PrincipalAuthorizationError(Exception):
    pass


class PrincipalAuthorizationError(Exception):
    """Raised when a principal lacks a requested authority."""

def authorize_principal(
    principal: AIRPrincipal,
    authority: PrincipalAuthority,
    role_registry: RoleRegistry,
    authority_registry: AuthorityRegistry,
    program: AIRProgram,
) -> bool:
    requested_grant = authority_registry.get(authority.name)

    if requested_grant is None:
        raise UnknownAuthorityError(
            f"Requested authority '{authority.name}' "
            f"is not registered."
        )

    effective_authorities = resolve_principal_authorities(
        principal=principal,
        role_registry=role_registry,
        authority_registry=authority_registry,
    )

    requested_name = authority.name.lower()

    for effective_authority in effective_authorities:
        if effective_authority.name.lower() == requested_name:
            return True

    raise PrincipalAuthorizationError(
        f"Principal '{principal.id}' lacks "
        f"authority '{authority.name}'."
    )

class PrincipalCapabilityAuthorizationError(Exception):
    pass


def authorize_principal_capabilities(
    principal: AIRPrincipal,
    required_capabilities: set[str],
    role_registry: RoleRegistry,
    authority_registry: AuthorityRegistry,
    program: AIRProgram,
) -> bool:
    resolved_capabilities = resolve_principal_capabilities(
        principal=principal,
        role_registry=role_registry,
        authority_registry=authority_registry,
    )

    normalized_resolved = {
        capability.lower()
        for capability in resolved_capabilities
    }

    missing = {
        capability
        for capability in required_capabilities
        if capability.lower() not in normalized_resolved
    }

    if missing:
        missing_list = ", ".join(sorted(missing))

        raise PrincipalCapabilityAuthorizationError(
            f"Principal '{principal.id}' lacks required "
            f"capabilities: {missing_list}."
        )

    return True

class UnknownEffectiveAuthorityError(Exception):
    """Raised when a resolved authority is not registered."""

def validate_effective_authorities(
    principal: AIRPrincipal,
    effective_authorities: tuple[PrincipalAuthority, ...],
    authority_registry: AuthorityRegistry,
) -> None:
    for authority in effective_authorities:
        if authority_registry.get(authority.name) is None:
            raise UnknownAuthorityError(
                f"Principal '{principal.name}' references "
                f"unknown authority '{authority.name}'."
            )

class AuthorityInheritanceError(Exception):
    """Raised when authority inheritance contains a cycle."""

def resolve_principal_authorities(
    principal: AIRPrincipal,
    role_registry: RoleRegistry,
    authority_registry: AuthorityRegistry,
) -> tuple[PrincipalAuthority, ...]:
    effective_authorities = resolve_effective_authorities(
        principal=principal,
        role_registry=role_registry,
    )

    validate_effective_authorities(
        principal=principal,
        effective_authorities=effective_authorities,
        authority_registry=authority_registry,
    )

    return effective_authorities

def resolve_principal_capabilities(
    principal: AIRPrincipal,
    role_registry: RoleRegistry,
    authority_registry: AuthorityRegistry,
) -> frozenset[str]:
    effective_authorities = resolve_principal_authorities(
        principal=principal,
        role_registry=role_registry,
        authority_registry=authority_registry,
    )

    capabilities: set[str] = set()

    for authority in effective_authorities:
        capabilities.update(
            authority_registry.resolve_capabilities(
                authority_name=authority.name,
            )
        )

    return frozenset(capabilities)
