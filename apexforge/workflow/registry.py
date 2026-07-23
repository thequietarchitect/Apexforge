"""Directive registry for ApexForge."""

from __future__ import annotations


class DirectiveRegistry:
    def __init__(self) -> None:
        self._directives = {}

    def register(self, name: str, runner) -> None:
        self._directives[name] = runner

    def resolve(self, name: str):
        return self._directives[name]

    def names(self):
        return sorted(self._directives.keys())

class PrincipalRegistry:
    def __init__(self):
        self._principals = {}

    def register(self, principal):
        if principal.name in self._principals:
            raise ValueError(
                f"Principal already registered: {principal.name}"
            )

        self._principals[principal.name] = principal

    def get(self, name):
        try:
            return self._principals[name]
        except KeyError as exc:
            raise KeyError(
                f"Unknown principal: {name}"
            ) from exc

    def contains(self, name):
        return name in self._principals