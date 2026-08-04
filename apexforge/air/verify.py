"""AIR verifier.

The runtime must consume VerifiedAIRProgram only. Verification is where missing
references, unsupported operations, version mismatches, and duplicate IDs are
rejected before execution.
"""

from __future__ import annotations

from typing import (
    Any,
    Callable,
    Iterable,
    Mapping,
    Optional,
)

from air.indexes import HasId, index_by_id
from air.model import (
    AIRProgram,
    AIRWhenAction,
    VerificationResult,
    validate_assignment_shape,
    validate_state_definition_shape,
)
from causality.model import DirectiveInvocation
from air.types import AIR_VERSION, is_int
from runtime.diagnostics import Diagnostic, append_diagnostic


class AIRVerifier:
    def verify(
        self,
        program: AIRProgram,
        *,
        allow_unresolved_directive_invocations: bool = False,
        directive_requirement_owners: Optional[
            Mapping[str, AIRProgram]
        ] = None,
    ) -> VerificationResult:
        diagnostics: list[Diagnostic] = []

        if program.version != AIR_VERSION:
            append_diagnostic(
                diagnostics,
                "error",
                "AIR001",
                f"unsupported AIR version: {program.version}",
            )

        self._check_unique(
            "principal",
            program.principals,
            diagnostics,
            canonical=str.casefold,
        )
        self._check_unique("state", program.states, diagnostics)
        self._check_unique("event", program.events, diagnostics)
        self._check_unique(
            "authority_check",
            program.authority_checks,
            diagnostics,
        )
        self._check_unique(
            "causal_decision",
            program.causal_decisions,
            diagnostics,
        )
        self._check_unique(
            "directive",
            program.directives,
            diagnostics,
            canonical=str.casefold,
        )
        self._check_unique("function", program.functions, diagnostics)
        self._check_unique("workflow", program.workflows, diagnostics)
        self._check_unique(
            "authority",
            program.authorities,
            diagnostics,
            identity=self._authority_identity,
            canonical=str.casefold,
        )
        self._check_unique(
            "role",
            program.roles,
            diagnostics,
            identity=self._role_identity,
        )

        principals = index_by_id(program.principals)
        states = index_by_id(program.states)
        events = index_by_id(program.events)
        checks = index_by_id(program.authority_checks)
        decisions = index_by_id(program.causal_decisions)
        directives = {
            directive.id.casefold(): directive
            for directive in program.directives
        }
        authorities = {
            authority.name.casefold(): authority
            for authority in program.authorities
            if isinstance(authority.name, str)
        }
        roles = {
            role.name: role
            for role in program.roles
            if isinstance(role.name, str)
        }

        self._check_authority_graph(
            tuple(program.authorities),
            authorities,
            diagnostics,
        )
        self._check_requirement_ownership(
            program,
            directive_requirement_owners,
            diagnostics,
        )

        for principal in program.principals:
            for authority in tuple(
                getattr(principal, "authorities", ()) or ()
            ):
                name = self._reference_name(authority)
                if (
                    not isinstance(name, str)
                    or name.casefold() not in authorities
                ):
                    append_diagnostic(
                        diagnostics,
                        "error",
                        "AIR062",
                        f"principal authority does not exist: {name}",
                        principal.id,
                    )

            for role_name in tuple(
                getattr(principal, "roles", ()) or ()
            ):
                if (
                    not isinstance(role_name, str)
                    or role_name not in roles
                ):
                    append_diagnostic(
                        diagnostics,
                        "error",
                        "AIR063",
                        f"principal role does not exist: {role_name}",
                        principal.id,
                    )

        for role in program.roles:
            for authority in tuple(
                getattr(role, "authorities", ()) or ()
            ):
                name = self._reference_name(authority)
                if (
                    not isinstance(name, str)
                    or name.casefold() not in authorities
                ):
                    append_diagnostic(
                        diagnostics,
                        "error",
                        "AIR064",
                        f"role authority does not exist: {name}",
                        self._role_identity(role),
                    )

        for state in program.states:
            if not validate_state_definition_shape(state):
                append_diagnostic(
                    diagnostics,
                    "error",
                    "AIR010",
                    "state must be an int state with an int initial value",
                    state.id,
                )

        for check in program.authority_checks:
            if check.principal not in principals:
                append_diagnostic(
                    diagnostics,
                    "error",
                    "AIR020",
                    f"authority principal does not exist: {check.principal}",
                    check.id,
                )

        for decision in program.causal_decisions:
            if decision.policy != "max_weight":
                append_diagnostic(
                    diagnostics,
                    "error",
                    "AIR030",
                    f"unsupported causal policy: {decision.policy}",
                    decision.id,
                )

            if not decision.paths:
                append_diagnostic(
                    diagnostics,
                    "error",
                    "AIR031",
                    "causal decision must have at least one path",
                    decision.id,
                )

            self._check_unique(f"path in {decision.id}", decision.paths, diagnostics)

            for path in decision.paths:
                if not is_int(path.weight):
                    append_diagnostic(
                        diagnostics,
                        "error",
                        "AIR032",
                        "causal path weight must be an int",
                        path.id,
                    )

                for assignment in path.assignments:
                    if assignment.state not in states:
                        append_diagnostic(
                            diagnostics,
                            "error",
                            "AIR033",
                            f"assignment state does not exist: {assignment.state}",
                            path.id,
                        )

                    if not validate_assignment_shape(assignment):
                        append_diagnostic(
                            diagnostics,
                            "error",
                            "AIR034",
                            "assignment operation/value shape is invalid",
                            path.id,
                        )

                for emission in path.emits:
                    if emission.event not in events:
                        append_diagnostic(
                            diagnostics,
                            "error",
                            "AIR036",
                            f"event does not exist: {emission.event}",
                            path.id,
                        )

                actions = tuple(
                    getattr(path, "actions", ()) or ()
                )
                invocation_targets = (
                    tuple(
                        self._iter_action_invocation_targets(actions)
                    )
                    if actions
                    else tuple(
                        invocation.target
                        for invocation in tuple(
                            getattr(path, "invocations", ()) or ()
                        )
                    )
                )

                for target in invocation_targets:
                    if (
                        not allow_unresolved_directive_invocations
                        and self._canonical_directive_reference(target)
                        not in directives
                    ):
                        append_diagnostic(
                            diagnostics,
                            "error",
                            "AIR045",
                            "directive invocation target does not exist: "
                            f"{target}",
                            path.id,
                        )

        for directive in program.directives:
            if directive.principal not in principals:
                append_diagnostic(
                    diagnostics,
                    "error",
                    "AIR040",
                    f"directive principal does not exist: {directive.principal}",
                    directive.id,
                )

            if not is_int(directive.order):
                append_diagnostic(
                    diagnostics,
                    "error",
                    "AIR041",
                    "directive order must be an int",
                    directive.id,
                )

            for check_id in directive.authority_checks:
                if check_id not in checks:
                    append_diagnostic(
                        diagnostics,
                        "error",
                        "AIR042",
                        f"authority check does not exist: {check_id}",
                        directive.id,
                    )
                    continue

                check = checks[check_id]
                if check.principal != directive.principal:
                    append_diagnostic(
                        diagnostics,
                        "error",
                        "AIR043",
                        "authority check principal must match directive principal",
                        directive.id,
                    )

            for decision_id in directive.causal_decisions:
                if decision_id not in decisions:
                    append_diagnostic(
                        diagnostics,
                        "error",
                        "AIR044",
                        f"causal decision does not exist: {decision_id}",
                        directive.id,
                    )

            for authority in tuple(
                getattr(directive, "authorities", ()) or ()
            ):
                name = getattr(authority, "name", None)
                if (
                    not isinstance(name, str)
                    or name.casefold() not in authorities
                ):
                    append_diagnostic(
                        diagnostics,
                        "error",
                        "AIR046",
                        f"directive authority does not exist: {name}",
                        directive.id,
                    )

        for workflow in program.workflows:
            for invocation in tuple(
                getattr(workflow, "invocations", ()) or ()
            ):
                target = getattr(invocation, "target", None)
                if (
                    self._canonical_directive_reference(target)
                    not in directives
                ):
                    append_diagnostic(
                        diagnostics,
                        "error",
                        "AIR050",
                        "workflow invocation target does not exist: "
                        f"{target}",
                        workflow.id,
                    )

        return VerificationResult(program, tuple(sorted(diagnostics)))

    @classmethod
    def _check_requirement_ownership(
        cls,
        program: AIRProgram,
        directive_owners: Optional[
            Mapping[str, AIRProgram]
        ],
        diagnostics: list[Diagnostic],
    ) -> None:
        owners = cls._requirement_owner_programs(
            program,
            directive_owners,
        )

        for owner in owners:
            requirements = tuple(
                getattr(owner, "requirements", ()) or ()
            )
            if not requirements:
                continue

            directives = tuple(
                getattr(owner, "directives", ()) or ()
            )
            if len(directives) == 1:
                continue

            directive_ids = tuple(
                sorted(
                    (
                        directive.id
                        for directive in directives
                        if isinstance(
                            getattr(directive, "id", None),
                            str,
                        )
                    ),
                    key=lambda identifier: (
                        identifier.casefold(),
                        identifier,
                    ),
                )
            )
            rendered = (
                ", ".join(directive_ids)
                if directive_ids
                else "<none>"
            )
            node_id = (
                directive_ids[0].casefold()
                if directive_ids
                else "requirements"
            )

            append_diagnostic(
                diagnostics,
                "error",
                "AIR065",
                "directive requirement ownership is ambiguous: "
                "expected exactly one owning directive, found "
                f"{len(directives)}: {rendered}",
                node_id,
            )

    @staticmethod
    def _requirement_owner_programs(
        program: AIRProgram,
        directive_owners: Optional[
            Mapping[str, AIRProgram]
        ],
    ) -> tuple[AIRProgram, ...]:
        if directive_owners is None:
            return (program,)

        unique: dict[int, AIRProgram] = {}

        for owner in directive_owners.values():
            if isinstance(owner, AIRProgram):
                unique[id(owner)] = owner

        if not unique:
            return (program,)

        return tuple(
            sorted(
                unique.values(),
                key=lambda owner: (
                    tuple(
                        sorted(
                            directive.id.casefold()
                            for directive in tuple(
                                getattr(
                                    owner,
                                    "directives",
                                    (),
                                )
                                or ()
                            )
                            if isinstance(
                                getattr(
                                    directive,
                                    "id",
                                    None,
                                ),
                                str,
                            )
                        )
                    ),
                    tuple(
                        requirement.capability
                        for requirement in tuple(
                            getattr(
                                owner,
                                "requirements",
                                (),
                            )
                            or ()
                        )
                    ),
                ),
            )
        )

    @staticmethod
    def _reference_name(reference: Any) -> Any:
        if isinstance(reference, str):
            return reference

        return getattr(reference, "name", None)

    @classmethod
    def _check_authority_graph(
        cls,
        declarations: tuple[Any, ...],
        authorities: dict[str, Any],
        diagnostics: list[Diagnostic],
    ) -> None:
        for authority in declarations:
            for inherited in tuple(
                getattr(authority, "inherits", ()) or ()
            ):
                if (
                    not isinstance(inherited, str)
                    or inherited.casefold() not in authorities
                ):
                    append_diagnostic(
                        diagnostics,
                        "error",
                        "AIR060",
                        "authority inheritance target does not exist: "
                        f"{inherited}",
                        authority.id,
                    )

        for cycle in cls._authority_cycles(authorities):
            closed = cycle + (cycle[0],)
            append_diagnostic(
                diagnostics,
                "error",
                "AIR061",
                "authority inheritance cycle: "
                + " -> ".join(
                    f"authority:{name}"
                    for name in closed
                ),
                f"authority:{cycle[0]}",
            )

    @classmethod
    def _authority_cycles(
        cls,
        authorities: dict[str, Any],
    ) -> tuple[tuple[str, ...], ...]:
        state: dict[str, int] = {}
        stack: list[str] = []
        positions: dict[str, int] = {}
        cycles: set[tuple[str, ...]] = set()

        def canonical_cycle(
            cycle: tuple[str, ...],
        ) -> tuple[str, ...]:
            rotations = tuple(
                cycle[index:] + cycle[:index]
                for index in range(len(cycle))
            )
            return min(rotations)

        def visit(name: str) -> None:
            state[name] = 1
            positions[name] = len(stack)
            stack.append(name)

            declaration = authorities[name]
            inherited_names = sorted(
                {
                    inherited.casefold()
                    for inherited in tuple(
                        getattr(declaration, "inherits", ()) or ()
                    )
                    if isinstance(inherited, str)
                    and inherited.casefold() in authorities
                }
            )

            for inherited in inherited_names:
                inherited_state = state.get(inherited, 0)

                if inherited_state == 0:
                    visit(inherited)
                    continue

                if inherited_state == 1:
                    start = positions[inherited]
                    cycle = tuple(stack[start:])
                    cycles.add(canonical_cycle(cycle))

            stack.pop()
            positions.pop(name)
            state[name] = 2

        for name in sorted(authorities):
            if state.get(name, 0) == 0:
                visit(name)

        return tuple(sorted(cycles))

    @staticmethod
    def _canonical_directive_reference(reference: Any) -> str:
        if not isinstance(reference, str):
            return ""

        value = reference.strip()
        if not value.casefold().startswith("directive:"):
            value = f"directive:{value}"

        return value.casefold()

    @classmethod
    def _iter_action_invocation_targets(
        cls,
        actions: Iterable[Any],
    ) -> Iterable[Any]:
        for action in actions:
            if isinstance(action, DirectiveInvocation):
                yield action.target
                continue

            if isinstance(action, AIRWhenAction):
                yield from cls._iter_action_invocation_targets(
                    tuple(action.actions)
                )
                yield from cls._iter_action_invocation_targets(
                    tuple(action.otherwise_actions)
                )

    @staticmethod
    def _item_id(item: Any) -> str:
        return item.id

    @staticmethod
    def _authority_identity(item: Any) -> str:
        return f"authority:{item.name}"

    @staticmethod
    def _role_identity(item: Any) -> str:
        return f"role:{item.name}"

    @classmethod
    def _check_unique(
        cls,
        label: str,
        items: Iterable[Any],
        diagnostics: list[Diagnostic],
        *,
        identity: Optional[Callable[[Any], str]] = None,
        canonical: Optional[Callable[[str], str]] = None,
    ) -> None:
        identity_projection = identity or cls._item_id
        seen: dict[str, str] = {}

        for item in items:
            identifier = identity_projection(item)
            collision_identity = (
                identifier
                if canonical is None
                else canonical(identifier)
            )

            if collision_identity in seen:
                first_identifier = seen[collision_identity]
                reported_identifier = (
                    identifier
                    if identifier == first_identifier
                    else collision_identity
                )
                append_diagnostic(
                    diagnostics,
                    "error",
                    "AIR000",
                    f"duplicate {label} id: {reported_identifier}",
                    reported_identifier,
                )

            seen[collision_identity] = identifier
