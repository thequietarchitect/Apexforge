"""ApexForge AST to AIR compiler."""

from __future__ import annotations
from typing import Optional

from role_compiler import compile_role
from language.parser import RoleNode, SetActionNode

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
    AIRWhenAction,
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
    WhenActionNode,
    parse,
)

from language.parser import (
    ExpressionNode,
    IntegerLiteralNode,
    StringLiteralNode,
    BooleanLiteralNode,
    IdentifierNode,
    UnaryExpressionNode,
    BinaryExpressionNode,
)

from air.expressions import (
    AIRExpression,
    AIRIntegerLiteral,
    AIRStringLiteral,
    AIRBooleanLiteral,
    AIRIdentifierReference,
    AIRUnaryExpression,
    AIRBinaryExpression,
)

def compile_expression(
    node: ExpressionNode,
) -> AIRExpression:
    if isinstance(node, IntegerLiteralNode):
        return AIRIntegerLiteral(
            value=node.value,
        )

    if isinstance(node, StringLiteralNode):
        return AIRStringLiteral(
            value=node.value,
        )

    if isinstance(node, BooleanLiteralNode):
        return AIRBooleanLiteral(
            value=node.value,
        )

    if isinstance(node, IdentifierNode):
        return AIRIdentifierReference(
            name=node.name,
        )

    if isinstance(node, UnaryExpressionNode):
        return AIRUnaryExpression(
            operator=node.operator,
            operand=compile_expression(
                node.operand,
            ),
        )

    if isinstance(node, BinaryExpressionNode):
        return AIRBinaryExpression(
            left=compile_expression(
                node.left,
            ),
            operator=node.operator,
            right=compile_expression(
                node.right,
            ),
        )

    raise TypeError(
        "Unsupported expression AST node: "
        f"{type(node).__name__}"
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

def compile_actions(
    actions,
    state_ids,
    event_ids,
):
    compiled = []
    pending_message = None

    for action in actions:
        if isinstance(action, AddActionNode):
            compiled.append(
                StateAssignment(
                    state=state_ids[
                    action.state_name
                    ],
                    operation="add_int",
                    value=compile_expression(
                    action.value,
                    ),
                )
            )
            continue

        if isinstance(action, SetActionNode):
            compiled.append(
                StateAssignment(
                    state=state_ids[
                    action.state_name
                    ],
                    operation="set_int",
                    value=compile_expression(
                    action.expression,
                    ),
                )
            )
            continue

        if isinstance(action, MessageActionNode):
            if pending_message is not None:
                raise ValueError(
                    "A message must be followed by "
                    "an emit before another message."
                )

                pending_message = compile_expression(
                    action.expression,
                    )
            continue

        if isinstance(action, EmitActionNode):
            if pending_message is None:
                event_facts = ()
            else:
                event_facts = facts(
                    message=pending_message,
                )

            compiled.append(
                EventEmission(
                    event=event_ids[
                    action.event_name
                    ],
                    facts=event_facts,
                )
            )

            pending_message = None
            continue

        if pending_message is not None:
            raise ValueError(
                "A message cannot cross into "
                "a when block.")
            continue

        if isinstance(action, InvokeActionNode):
        # Preserve the same constructor and field
        # that worked in your AFP-P1 compiler.
            compiled.append(
                DirectiveInvocation(
                target=action.target,
            )
            )
            continue

        if isinstance(action, WhenActionNode):
            compiled.append(
                AIRWhenAction(
                    condition=compile_expression(
                    action.condition,
                ),
                    actions=compile_actions(
                    action.actions,
                    state_ids,
                    event_ids,
                    ),
                )
            )
            continue

        raise TypeError(
            "Unsupported action node: "
            f"{type(action).__name__}"
        )

    return tuple(compiled)
    

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
            ordered_actions = compile_actions(
                path.actions,
                state_ids=state_ids,
                event_ids=event_ids,
            )

        # Preserve AFP-P1 compatibility without flattening conditional actions.
        assignments = tuple(
            action
                for action in ordered_actions
                    if isinstance(
                    action,
                    StateAssignment,
                )
            )

        emits = tuple(
            action
                for action in ordered_actions
                    if isinstance(
                        action,
                        EventEmission,
                    )
                )

        invocations = tuple(
            action
                for action in ordered_actions
                    if isinstance(
                        action,
                        DirectiveInvocation,
                    )
                )

        paths.append(
            CausalPath(
                id=f"path:{path.name}",
                weight=path.weight,
                actions=ordered_actions,
                assignments=assignments,
                emits=emits,
                invocations=invocations,
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
            capability=requirement.capability,
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
                initial=compile_expression(
                    state.initial,
                ),
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

        causal_decisions=tuple(
            causal_decisions
        ),

        directives=(
            AIRDirective(
                id=directive_id,
                name=node.name,
                principal=principal_id,
                authority_checks=(
                    authority_id,
                ),
                causal_decisions=tuple(
                    decision.id
                    for decision in causal_decisions
                ),
                order=0,
            ),
        ),

        requirements=requirements,

        authorities=tuple(
            DirectiveAuthority(
                name=authority.name,
            )
            for authority in node.authorities
        ),
    )

   


def compile_source(
        source: str,
    ) -> AIRProgram | AIRRole:
    node = parse(source)
    return compile_node(node)