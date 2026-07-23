from authority.registry import AuthorityRegistry
from air.model import AIRProgram, AIRPrincipal
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
) -> None:

    authority_name = program.principals[0].name

    for requirement in program.requirements:

        if not registry.has_capability(
            authority_name,
            requirement.capability,
        ):
            raise AuthorizationError(
                f"{authority_name} lacks capability "
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
            if not authority_registry.contains(authority.name):
                raise UnknownPrincipalAuthorityError(
                    f"Principal {principal.name} references "
                    f"unknown authority {authority.name}"
                )

class PrincipalAuthorizationError(Exception):
    pass


class PrincipalAuthorizationError(Exception):
    """Raised when a principal lacks a requested authority."""


def authorize_principal(
    principal: AIRPrincipal,
    authority,
    role_registry: RoleRegistry,
    program: AIRProgram,
    ) -> bool:
        """
        Authorize a principal for one requested authority.

        The authority may be assigned directly to the principal
        or inherited through one of the principal's roles.
        """

        effective_authorities = resolve_effective_authorities(
        principal=principal,
        role_registry=role_registry,
    )

        for effective_authority in effective_authorities:
            if effective_authority.name == authority.name:
                return True

        # This must remain outside the loop.
        raise PrincipalAuthorizationError(
            f"Principal '{principal.name}' lacks "
            f"authority '{authority.name}'."
    )

class PrincipalCapabilityAuthorizationError(Exception):
    pass


def authorize_principal_capabilities(
    principal: AIRPrincipal,
    required_authorities,
    role_registry,
    program: AIRProgram,
    ):
    """
    Verify that a principal possesses every authority
    required to execute a capability.
    """

    missing = []

    for authority in required_authorities:

        try:
            PrincipalAuthorizationError.authorize_principal(
                principal=principal,
                    authority=authority,
                    role_registry=role_registry,
                    program=program,
            )

        except PrincipalAuthorizationError:
                missing.append(authority.name)

        if missing:

            missing_text = ", ".join(sorted(missing))

            raise PrincipalCapabilityAuthorizationError(
                f"Principal '{principal.name}' lacks required "
                f"capability authorities: {missing_text}"
        )

        return True