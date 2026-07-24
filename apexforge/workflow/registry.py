"""Directive registry for ApexForge."""

from __future__ import annotations


class DirectiveRegistry:
    def __init__(self) -> None:
        self._directives = {}

    def register(self, id: str, runner) -> None:
        self._directives[id] = runner

    def resolve(self, id: str):
        return self._directives[id]

    def names(self):
        return sorted(self._directives.keys())

class PrincipalRegistry:
    def __init__(self):
        self._principals = {}

    def register(self, principal):
        if principal.id in self._principals:
            raise ValueError(
                f"Principal already registered: {principal.id}"
            )

        self._principals[principal.id] = principal

    def get(self, id):
        try:
            return self._principals[id]
        except KeyError as exc:
            raise KeyError(
                f"Unknown principal: {id}"
            ) from exc

    def contains(self, id):
        return id in self._principals