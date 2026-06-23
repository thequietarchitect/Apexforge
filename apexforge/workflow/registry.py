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