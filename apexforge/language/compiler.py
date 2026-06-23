"""ApexForge AST to AIR compiler."""

from __future__ import annotations

from air.model import (
    AIRDirective,
    AIRProgram,
    StateDefinition,
)
from air.types import AIR_VERSION
from authority.model import Principal
from language.parser import DirectiveNode, parse


def compile_directive(node: DirectiveNode) -> AIRProgram:
    principal_id = f"principal:{node.name}"
    directive_id = f"directive:{node.name}"

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
        events=(),
        authority_checks=(),
        causal_decisions=(),
        directives=(
            AIRDirective(
                id=directive_id,
                name=node.name,
                principal=principal_id,
                authority_checks=(),
                causal_decisions=(),
                order=0,
            ),
        ),
    )


def compile_source(source: str) -> AIRProgram:
    return compile_directive(parse(source))