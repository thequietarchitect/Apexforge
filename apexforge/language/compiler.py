"""ApexForge AST to AIR compiler."""

from __future__ import annotations

from air.model import (
    AIRDirective,
    AIRProgram,
    EventDefinition,
    EventEmission,
    StateAssignment,
    StateDefinition,
)
from air.types import AIR_VERSION
from authority.model import AuthorityCheck, Principal
from causality.model import CausalDecision, CausalPath
from language.parser import (
    AddActionNode,
    DirectiveNode,
    EmitActionNode,
    parse,
)


def compile_directive(node: DirectiveNode) -> AIRProgram:
    principal_id = f"principal:{node.name}"
    directive_id = f"directive:{node.name}"
    authority_id = f"auth:{node.name}"

    state_ids = {
        state.name: f"state:{state.name}"
        for state in node.states
    }

    event_ids = {
        event.name: f"event:{event.name}"
        for event in node.events
    }

    causal_decisions = []

    for cause in node.causes:
        paths = []

        for path in cause.paths:
            assignments = []
            emits = []

            for action in path.actions:
                if isinstance(action, AddActionNode):
                    assignments.append(
                        StateAssignment(
                            state=state_ids[action.state_name],
                            operation="add_int",
                            value=action.value,
                        )
                    )

                elif isinstance(action, EmitActionNode):
                    emits.append(
                        EventEmission(
                            event=event_ids[action.event_name],
                            facts=(),
                        )
                    )

            paths.append(
                CausalPath(
                    id=f"path:{path.name}",
                    weight=path.weight,
                    assignments=tuple(assignments),
                    emits=tuple(emits),
                    effects=(),
                    rationale="",
                )
            )

        causal_decisions.append(
            CausalDecision(
                id=f"cause:{cause.name}",
                cause=cause.name,
                policy="max_weight",
                paths=tuple(paths),
            )
        )

    return AIRProgram(
        version=AIR_VERSION,
        principals=(
            Principal(
                id=principal_id,
                display_name=node.name,
            ),
        ),
        states=tuple(
            StateDefinition(
                id=f"state:{state.name}",
                initial=state.initial,
            )
            for state in node.states
        ),
        events=tuple(
            EventDefinition(
                id=f"event:{event.name}",
                name=event.name,
            )
            for event in node.events
        ),
        authority_checks=(
            AuthorityCheck(
                id=authority_id,
                principal=principal_id,
                capability=f"directive.invoke:{node.name}",
                resource=directive_id,
            ),
        ),
        causal_decisions=tuple(causal_decisions),
        directives=(
            AIRDirective(
                id=directive_id,
                name=node.name,
                principal=principal_id,
                authority_checks=(authority_id,),
                causal_decisions=tuple(
                    decision.id
                    for decision in causal_decisions
                ),
                order=0,
            ),
        ),
    )


def compile_source(source: str) -> AIRProgram:
    return compile_directive(parse(source))