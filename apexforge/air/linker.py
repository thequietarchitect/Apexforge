"""Deterministic linker for separately compiled ApexForge AIR programs.

The linker combines compilation units only. It does not replace
RuntimeValidator: unresolved cross-program references and malformed AIR remain
validator responsibilities after linking.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any, Callable, Iterable, TypeVar

from air.model import AIRProgram


T = TypeVar("T")


class AIRLinkError(Exception):
    """Base class for AIR program-linking failures."""


class EmptyLinkError(AIRLinkError):
    """Raised when no AIR programs are supplied."""


class InvalidLinkInputError(AIRLinkError):
    """Raised when a linker input is not a usable AIRProgram."""


class IncompatibleAIRVersionError(AIRLinkError):
    """Raised when compilation units use different AIR versions."""


class DuplicateLinkDefinitionError(AIRLinkError):
    """Raised when two compilation units define the same global symbol."""

    def __init__(
        self,
        owner: str,
        identifier: str,
    ) -> None:
        self.owner = owner
        self.identifier = identifier
        super().__init__(
            f"Duplicate {owner} definition '{identifier}' "
            "while linking AIR programs."
        )


class AIRProgramLinker:
    """Combine separately compiled AIRProgram units deterministically."""

    def link(
        self,
        programs: Iterable[AIRProgram],
    ) -> AIRProgram:
        units = tuple(programs)

        if not units:
            raise EmptyLinkError(
                "AIRProgramLinker requires at least one AIRProgram."
            )

        for index, program in enumerate(units):
            if not isinstance(program, AIRProgram):
                raise InvalidLinkInputError(
                    "AIRProgramLinker accepts AIRProgram values only; "
                    f"unit[{index}] was {type(program).__name__}."
                )

        version = self._resolve_version(units)

        principals = self._merge_unique(
            units,
            attribute="principals",
            owner="principal",
            key=self._required_id,
        )
        states = self._merge_unique(
            units,
            attribute="states",
            owner="state",
            key=self._required_id,
        )
        events = self._merge_unique(
            units,
            attribute="events",
            owner="event",
            key=self._required_id,
        )
        authority_checks = self._merge_unique(
            units,
            attribute="authority_checks",
            owner="authority check",
            key=self._required_id,
        )
        causal_decisions = self._merge_unique(
            units,
            attribute="causal_decisions",
            owner="causal decision",
            key=self._required_id,
        )
        directives = self._merge_directives(units)
        functions = self._merge_functions(units)
        authorities = self._merge_unique(
            units,
            attribute="authorities",
            owner="authority",
            key=self._required_id,
        )
        roles = self._merge_unique(
            units,
            attribute="roles",
            owner="role",
            key=self._required_name_or_id,
        )
        workflows = self._merge_unique(
            units,
            attribute="workflows",
            owner="workflow",
            key=self._required_id,
        )

        requirements = tuple(
            requirement
            for program in units
            for requirement in tuple(
                getattr(program, "requirements", ()) or ()
            )
        )

        return AIRProgram(
            version=version,
            states=states,
            events=events,
            authority_checks=authority_checks,
            causal_decisions=causal_decisions,
            directives=directives,
            requirements=requirements,
            authorities=authorities,
            principals=principals,
            roles=roles,
            functions=functions,
            workflows=workflows,
        )

    def _resolve_version(
        self,
        programs: tuple[AIRProgram, ...],
    ) -> str:
        first = getattr(programs[0], "version", None)

        if not isinstance(first, str) or not first.strip():
            raise InvalidLinkInputError(
                "AIR link unit[0] has an invalid version."
            )

        version = first.strip()

        for index, program in enumerate(
            programs[1:],
            start=1,
        ):
            candidate = getattr(program, "version", None)

            if not isinstance(candidate, str) or not candidate.strip():
                raise InvalidLinkInputError(
                    f"AIR link unit[{index}] has an invalid version."
                )

            candidate = candidate.strip()

            if candidate != version:
                raise IncompatibleAIRVersionError(
                    "Cannot link different AIR versions: "
                    f"unit[0]={version!r}, unit[{index}]={candidate!r}."
                )

        return version

    def _merge_unique(
        self,
        programs: tuple[AIRProgram, ...],
        *,
        attribute: str,
        owner: str,
        key: Callable[[Any, str], str],
    ) -> tuple[Any, ...]:
        merged: list[Any] = []
        seen: set[str] = set()

        for program_index, program in enumerate(programs):
            values = tuple(
                getattr(program, attribute, ()) or ()
            )

            for value_index, value in enumerate(values):
                location = (
                    f"unit[{program_index}].{attribute}[{value_index}]"
                )
                identifier = key(value, location)

                if identifier in seen:
                    raise DuplicateLinkDefinitionError(
                        owner,
                        identifier,
                    )

                seen.add(identifier)
                merged.append(value)

        return tuple(merged)

    def _merge_directives(
        self,
        programs: tuple[AIRProgram, ...],
    ) -> tuple[Any, ...]:
        merged: list[Any] = []
        seen: set[str] = set()

        for program_index, program in enumerate(programs):
            local = tuple(
                getattr(program, "directives", ()) or ()
            )

            prepared: list[tuple[int, str, Any]] = []

            for directive_index, directive in enumerate(local):
                location = (
                    f"unit[{program_index}].directives"
                    f"[{directive_index}]"
                )
                identifier = self._required_id(
                    directive,
                    location,
                )
                order = getattr(directive, "order", None)

                if isinstance(order, bool) or not isinstance(order, int):
                    raise InvalidLinkInputError(
                        f"{location} order must be an integer; "
                        f"received {type(order).__name__}."
                    )

                prepared.append(
                    (order, identifier, directive)
                )

            # Preserve each unit's explicit local order, with ID as a stable
            # tie-breaker. Global order is then reassigned below.
            prepared.sort(
                key=lambda item: (
                    item[0],
                    item[1],
                )
            )

            for _, identifier, directive in prepared:
                if identifier in seen:
                    raise DuplicateLinkDefinitionError(
                        "directive",
                        identifier,
                    )

                seen.add(identifier)
                merged.append(directive)

        # Separately compiled units normally begin directive ordering at zero.
        # Renumbering creates one deterministic, validator-safe global order.
        return tuple(
            replace(
                directive,
                order=global_order,
            )
            for global_order, directive in enumerate(merged)
        )

    def _merge_functions(
        self,
        programs: tuple[AIRProgram, ...],
    ) -> tuple[Any, ...]:
        """Merge pure functions and assign deterministic global orders."""

        merged: list[Any] = []
        seen: set[str] = set()

        for program_index, program in enumerate(programs):
            local = tuple(
                getattr(program, "functions", ()) or ()
            )

            prepared: list[tuple[int, str, Any]] = []

            for function_index, function in enumerate(local):
                location = (
                    f"unit[{program_index}].functions"
                    f"[{function_index}]"
                )
                identifier = self._required_id(
                    function,
                    location,
                )
                order = getattr(function, "order", None)

                if isinstance(order, bool) or not isinstance(order, int):
                    raise InvalidLinkInputError(
                        f"{location} order must be an integer; "
                        f"received {type(order).__name__}."
                    )

                prepared.append(
                    (order, identifier, function)
                )

            # Each compilation unit owns a local function order. Preserve that
            # order within the unit and use ID only as a deterministic
            # tie-breaker for malformed equal-order inputs.
            prepared.sort(
                key=lambda item: (
                    item[0],
                    item[1],
                )
            )

            for _, identifier, function in prepared:
                if identifier in seen:
                    raise DuplicateLinkDefinitionError(
                        "function",
                        identifier,
                    )

                seen.add(identifier)
                merged.append(function)

        # Separately compiled function units begin at local order zero.
        # Renumbering creates one validator-safe global function order.
        return tuple(
            replace(
                function,
                order=global_order,
            )
            for global_order, function in enumerate(merged)
        )

    def _required_id(
        self,
        value: Any,
        location: str,
    ) -> str:
        identifier = getattr(value, "id", None)

        if not isinstance(identifier, str) or not identifier.strip():
            raise InvalidLinkInputError(
                f"{location} requires a non-empty string id."
            )

        return identifier.strip()

    def _required_name_or_id(
        self,
        value: Any,
        location: str,
    ) -> str:
        name = getattr(value, "name", None)

        if isinstance(name, str) and name.strip():
            return name.strip()

        return self._required_id(
            value,
            location,
        )


def link_programs(
    *programs: AIRProgram,
) -> AIRProgram:
    """Convenience wrapper for linking AIRProgram compilation units."""

    return AIRProgramLinker().link(programs)
