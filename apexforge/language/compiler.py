"""ApexForge AST to AIR compiler."""

from __future__ import annotations

from role_compiler import compile_role
from language.parser import RoleNode

from air.model import (
    AIRDirective,
    AIRProgram,
    AIRRole,
    EventDefinition,
    EventEmission,
    StateAssignment,
    StateDefinition,
    DirectiveRequirement,
    DirectiveAuthority,
    Principal,
    facts,
)
from air.types import AIR_VERSION
from authority.model import AuthorityCheck
from causality.model import CausalDecision, CausalPath, DirectiveInvocation
from language.parser import (
    AddActionNode,
    DirectiveNode,
    EmitActionNode,
    InvokeActionNode,
    MessageActionNode,
    RequirementNode,
    parse,
)

def compile_node(
        node: DirectiveNode | RoleNode,
    ) -> AIRProgram | AIRRole:

    if isinstance(node, DirectiveNode):
        return compile_directive(node)

    elif isinstance(node, RoleNode):
        return compile_role(node)

    raise TypeError(
        f"Unsupported AST node type: {type(node).__name__}"
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
            invocations = []
            pending_message = None

            for action in path.actions:
                if isinstance(action, MessageActionNode):
                    pending_message = action.text

                elif isinstance(action, AddActionNode):
                    assignments.append(
                        StateAssignment(
                            state=state_ids[action.state_name],
                            operation="add_int",
                            value=action.value,
                        )
                    )

                elif isinstance(action, EmitActionNode):
                    if pending_message is None:
                        event_facts = ()
                    else:
                        event_facts = facts(message=pending_message)

                    emits.append(
                        EventEmission(
                            event=event_ids[action.event_name],
                            facts=event_facts,
                        )
                    )

                elif isinstance(action, InvokeActionNode):
                    invocations.append(
                        DirectiveInvocation(
                            target=action.target,
                        )
                    )

            paths.append(
                CausalPath(
                    id=f"path:{path.name}",
                    weight=path.weight,
                    assignments=tuple(assignments),
                    emits=tuple(emits),
                    invocations=tuple(invocations),
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

        requirements = tuple(
            DirectiveRequirement(
                capability=requirement.capability
            )
            for requirement in node.requirements
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
            requirements=tuple(
                DirectiveRequirement(capability=req.capability)
                for req in node.requirements
        ),
            authorities=tuple(
                DirectiveAuthority(name=authority.name)
                for authority in node.authorities
    ),
)
    


def compile_source(
        source: str,
    ) -> AIRProgram | AIRRole:
    node = parse(source)
    return compile_node(node)