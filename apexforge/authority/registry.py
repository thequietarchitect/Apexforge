from typing import Optional

from authority.model import AuthorityGrant

class AuthorityInheritanceError(Exception):
    pass



class AuthorityRegistry:
    def __init__(self):
        self._grants: dict[str, AuthorityGrant] = {}

    def register(self, grant: AuthorityGrant) -> None:
        self._grants[grant.name.lower()] = grant

    def get(self, name: str) -> Optional[AuthorityGrant]:
        return self._grants.get(name.lower())

    def resolve_capabilities(self, authority_name, seen=None):
        if seen is None:
            seen = set()

        key = authority_name

        if key in seen:
            raise AuthorityInheritanceError(
            f"Authority inheritance cycle detected at '{key}'"
        )

        seen.add(key)

        grant = self.get(authority_name)

        if grant is None:
            return set()

        inherited = set()

        if grant.extends is not None:
            inherited = self.resolve_capabilities(
                grant.extends,
                seen,
        )

        return inherited | set(grant.capabilities)

    def has_capability(self, authority_name: str, capability: str) -> bool:
        return capability in self.resolve_capabilities(authority_name)

    def list_authorities(self) -> tuple[str, ...]:
        return tuple(self._grants.keys())