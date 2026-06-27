from authority.registry import AuthorityRegistry

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

    authority_name = program.principals[0].display_name

    for requirement in program.requirements:

        if not registry.has_capability(
            authority_name,
            requirement.capability,
        ):
            raise AuthorizationError(
                f"{authority_name} lacks capability "
                f"'{requirement.capability}'"
            )