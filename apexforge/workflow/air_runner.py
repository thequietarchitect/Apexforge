"""Run AIR programs loaded from AirRegistry."""

from __future__ import annotations

from dataclasses import dataclass, replace
from types import MappingProxyType
from typing import Mapping

from air.linker import (
    AIRProgramLinker,
    DuplicateLinkDefinitionError,
)
from air.model import AIRProgram, AIRWhenAction
from air.verify import AIRVerifier
from authority.engine import AuthorityEngine
from authority.model import AuthorityGrant
from causality.model import DirectiveInvocation
from runtime.context import ExecutionContext
from runtime.engine import RuntimeEngine, RuntimeExpressionError
from runtime.state import StateSnapshot


@dataclass(frozen=True)
class RegistryExecutionPlan:
    program: AIRProgram
    entry_directive: str
    directive_owners: Mapping[str, AIRProgram]

    def owner_of(self, directive_id: str) -> AIRProgram:
        return self.directive_owners[directive_id.casefold()]


def _canonical_directive_id(reference: str) -> str:
    canonical = (
        reference
        if reference.casefold().startswith("directive:")
        else f"directive:{reference}"
    )
    return canonical.casefold()


def _registry_name(reference: str) -> str:
    prefix = "directive:"
    value = reference

    if value.casefold().startswith(prefix):
        value = value[len(prefix):]

    return value.casefold()


def _resolve_registry_root(program, reference: str):
    canonical = _canonical_directive_id(reference)
    matches = tuple(
        directive
        for directive in program.directives
        if directive.id.casefold() == canonical
    )

    if len(matches) != 1:
        raise RuntimeExpressionError(
            f"undefined directive invocation target {reference!r}"
        )

    return matches[0]


def _resolve_program_directive(program, reference: str):
    canonical = _canonical_directive_id(reference)
    matches = tuple(
        directive
        for directive in program.directives
        if directive.id.casefold() == canonical
    )

    if len(matches) == 1:
        return matches[0]

    if len(matches) > 1:
        raise DuplicateLinkDefinitionError(
            "directive",
            canonical,
        )

    return None


def _iter_action_invocation_targets(actions):
    for action in actions:
        if isinstance(action, DirectiveInvocation):
            yield action.target
            continue

        if isinstance(action, AIRWhenAction):
            yield from _iter_action_invocation_targets(
                action.actions
            )
            yield from _iter_action_invocation_targets(
                action.otherwise_actions
            )


def _iter_directive_invocation_targets(program, directive):
    decisions = {
        decision.id: decision
        for decision in program.causal_decisions
    }

    for decision_id in directive.causal_decisions:
        decision = decisions.get(decision_id)

        if decision is None:
            continue

        for path in decision.paths:
            actions = tuple(
                getattr(path, "actions", ()) or ()
            )

            if actions:
                yield from _iter_action_invocation_targets(actions)
                continue

            for invocation in tuple(
                getattr(path, "invocations", ()) or ()
            ):
                yield invocation.target


def _coalesce_shared_principals(programs):
    prepared = []
    seen: dict[str, tuple[int, object]] = {}

    for program_index, program in enumerate(programs):
        retained = []

        for principal in program.principals:
            canonical = principal.id.casefold()
            previous = seen.get(canonical)

            if previous is None:
                seen[canonical] = (
                    program_index,
                    principal,
                )
                retained.append(principal)
                continue

            previous_program_index, previous_principal = previous

            # Same-unit duplicates remain visible to AIRProgramLinker.
            if previous_program_index == program_index:
                retained.append(principal)
                continue

            if principal == previous_principal:
                continue

            raise DuplicateLinkDefinitionError(
                "principal",
                principal.id,
            )

        prepared.append(
            replace(
                program,
                principals=tuple(retained),
            )
        )

    return tuple(prepared)


def build_registry_execution_plan(
    registry,
    name: str,
) -> RegistryExecutionPlan:
    root_program = registry.resolve(name)
    root_directive = _resolve_registry_root(
        root_program,
        name,
    )

    programs = [root_program]
    included_programs = {
        id(root_program),
    }
    resolved_registry_programs = {
        _registry_name(name): root_program,
    }
    directive_locations = {}
    directive_owners = {}
    queue = []
    queued = set()
    scanned = set()

    def index_program(program) -> None:
        for directive in program.directives:
            canonical = directive.id.casefold()
            previous = directive_locations.get(canonical)

            if previous is not None:
                previous_program, previous_directive = previous

                if (
                    previous_program is not program
                    or previous_directive is not directive
                ):
                    raise DuplicateLinkDefinitionError(
                        "directive",
                        directive.id,
                    )

            directive_locations[canonical] = (
                program,
                directive,
            )
            directive_owners[canonical] = program

    def enqueue(program, directive) -> None:
        key = (
            id(program),
            directive.id.casefold(),
        )

        if key in scanned or key in queued:
            return

        queued.add(key)
        queue.append((program, directive))

    index_program(root_program)
    enqueue(root_program, root_directive)
    queue_index = 0

    while queue_index < len(queue):
        program, directive = queue[queue_index]
        queue_index += 1

        scan_key = (
            id(program),
            directive.id.casefold(),
        )
        queued.discard(scan_key)

        if scan_key in scanned:
            continue

        scanned.add(scan_key)

        for target in _iter_directive_invocation_targets(
            program,
            directive,
        ):
            canonical_target = _canonical_directive_id(target)
            included_target = directive_locations.get(
                canonical_target
            )

            if included_target is not None:
                enqueue(*included_target)
                continue

            registry_name = _registry_name(target)
            dependency = resolved_registry_programs.get(
                registry_name
            )

            if dependency is None:
                try:
                    dependency = registry.resolve(registry_name)
                except KeyError:
                    # Selected unknown targets remain absent and become
                    # RUN002 inside RuntimeEngine.
                    continue

                resolved_registry_programs[
                    registry_name
                ] = dependency

            dependency_directive = _resolve_program_directive(
                dependency,
                target,
            )

            if dependency_directive is None:
                continue

            if id(dependency) not in included_programs:
                included_programs.add(id(dependency))
                programs.append(dependency)
                index_program(dependency)

            enqueue(
                *directive_locations[
                    dependency_directive.id.casefold()
                ]
            )

    composed = _coalesce_shared_principals(
        tuple(programs)
    )
    linked = AIRProgramLinker().link(composed)

    return RegistryExecutionPlan(
        program=linked,
        entry_directive=root_directive.id,
        directive_owners=MappingProxyType(
            dict(directive_owners)
        ),
    )


def build_default_context(program):
    grants = tuple(
        AuthorityGrant(
            principal=check.principal,
            capability=check.capability,
            resource=check.resource,
        )
        for check in program.authority_checks
    )

    return ExecutionContext(
        state=StateSnapshot.from_program_initials(program),
        authority=AuthorityEngine.from_grants(grants),
    )


def collect_invocations(program) -> tuple[str, ...]:
    targets = []

    for decision in program.causal_decisions:
        for path in decision.paths:
            for invocation in path.invocations:
                targets.append(invocation.target)

    return tuple(targets)


def run_air_program(
    program,
    *,
    entry_directives=None,
    directive_entry_guard=None,
    max_invocation_depth=None,
):
    verified = AIRVerifier().verify(program).require_verified()
    context = build_default_context(program)

    runtime = (
        RuntimeEngine()
        if max_invocation_depth is None
        else RuntimeEngine(
            max_invocation_depth=max_invocation_depth,
        )
    )

    return runtime.execute(
        verified,
        context,
        entry_directives=entry_directives,
        directive_entry_guard=directive_entry_guard,
    )


def run_air_from_registry(
    registry,
    name: str,
    *,
    directive_entry_guard=None,
    max_depth=None,
):
    plan = build_registry_execution_plan(
        registry,
        name,
    )

    if max_depth is None:
        max_invocation_depth = None
    else:
        if (
            isinstance(max_depth, bool)
            or not isinstance(max_depth, int)
            or max_depth < 0
        ):
            raise ValueError(
                "max_depth must be a non-negative integer."
            )

        max_invocation_depth = max_depth + 1

    return run_air_program(
        plan.program,
        entry_directives=(plan.entry_directive,),
        directive_entry_guard=directive_entry_guard,
        max_invocation_depth=max_invocation_depth,
    )


def run_air_with_invocation_report(program):
    result = run_air_program(program)
    invocations = collect_invocations(program)

    return result, invocations
