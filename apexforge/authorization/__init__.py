from authorization.role_resolver import (
    AuthorityResolutionError,
    PrincipalUnknownRoleError,
    resolve_effective_authorities,
)

__all__ = (
    "AuthorityResolutionError",
    "PrincipalUnknownRoleError",
    "resolve_effective_authorities",
)