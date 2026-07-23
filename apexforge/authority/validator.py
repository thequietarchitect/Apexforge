from authority.registry import AuthorityRegistry
from air.model import AIRProgram, AIRPrincipal

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

    def authorize_principal(
        principal: AIRPrincipal,
        program: AIRProgram,
        ) -> None:
        principal_authorities = {
            authority.name
            for authority in principal.authorities
    }

        required_authorities = {
            authority.name
        for authority in program.authorities
    }

        missing_authorities = (
            required_authorities - principal_authorities
    )

        if missing_authorities:
            missing_text = ", ".join(
            sorted(missing_authorities)
        )

            raise PrincipalAuthorizationError(
                f"Principal '{principal.name}' lacks required "
                f"authorities: {missing_text}"
        )

class PrincipalCapabilityAuthorizationError(Exception):
    pass


    def authorize_principal_capabilities(
        principal: AIRPrincipal,
        program: AIRProgram,
        authority_registry: AuthorityRegistry,
        ) -> None:

        """
            Verify that the selected principal's directive authorities grant
            every capability required by the AIR program.
        """

        required_capabilities = {
        requirement.capability
            for requirement in program.requirements
    }

        if not required_capabilities:
            return

        principal_authorities = {
            authority.name
                for authority in principal.authorities
    }

        directive_authorities = {
            authority.name
                for authority in program.authorities
    }

        usable_authorities = (
            principal_authorities
            & directive_authorities
    )

        granted_capabilities = set()

        for authority_name in usable_authorities:
            for capability_name in required_capabilities:
                if authority_registry.has_capability(
                    authority_name,
                    capability_name,
            ):
                    granted_capabilities.add(
                    capability_name
                )

        missing_capabilities = (
            required_capabilities
            - granted_capabilities
    )

        if missing_capabilities:
            missing_text = ", ".join(
                sorted(missing_capabilities)
        )

            raise PrincipalCapabilityAuthorizationError(
                f"Principal '{principal.name}' lacks required "
                f"capabilities: {missing_text}"
        )