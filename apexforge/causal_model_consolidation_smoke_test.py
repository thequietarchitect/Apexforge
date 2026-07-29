"""Smoke test for canonical causal-model ownership and compiler nesting."""

from __future__ import annotations

import air.model as air_model
import causality.model as causal_model

from language.compiler import compile_directive
from language.parser import (
    AddActionNode,
    CauseNode,
    DirectiveNode,
    IntegerLiteralNode,
    InvokeActionNode,
    PathNode,
    StateNode,
)


def main() -> None:
    assert (
        air_model.CausalPath
        is causal_model.CausalPath
    )
    assert (
        air_model.CausalDecision
        is causal_model.CausalDecision
    )
    assert (
        air_model.DirectiveInvocation
        is causal_model.DirectiveInvocation
    )

    legacy_invocation = (
        causal_model.DirectiveInvocation(
            directive="LegacyTarget",
        )
    )
    assert (
        legacy_invocation.target
        == "LegacyTarget"
    )
    assert (
        legacy_invocation.directive
        == "LegacyTarget"
    )

    node = DirectiveNode(
        name="CausalConsolidation",
        states=(
            StateNode(
                name="count",
                initial=IntegerLiteralNode(
                    value=0,
                ),
            ),
        ),
        events=(),
        causes=(
            CauseNode(
                name="Alpha",
                paths=(
                    PathNode(
                        name="Low",
                        weight=1,
                        actions=(
                            AddActionNode(
                                state_name="count",
                                value=IntegerLiteralNode(
                                    value=1,
                                ),
                            ),
                        ),
                    ),
                    PathNode(
                        name="High",
                        weight=2,
                        actions=(
                            InvokeActionNode(
                                target="OtherDirective",
                            ),
                        ),
                    ),
                ),
            ),
            CauseNode(
                name="Beta",
                paths=(
                    PathNode(
                        name="Only",
                        weight=3,
                        actions=(),
                    ),
                ),
            ),
        ),
        requirements=(),
        authorities=(),
    )

    program = compile_directive(
        node
    )

    assert len(
        program.causal_decisions
    ) == 2

    first_decision = (
        program.causal_decisions[0]
    )
    second_decision = (
        program.causal_decisions[1]
    )

    assert first_decision.id == "cause:Alpha"
    assert len(first_decision.paths) == 2
    assert second_decision.id == "cause:Beta"
    assert len(second_decision.paths) == 1

    invocation = (
        first_decision
        .paths[1]
        .invocations[0]
    )

    assert invocation.target == "OtherDirective"
    assert (
        type(invocation)
        is causal_model.DirectiveInvocation
    )

    print(
        "Causal model consolidation "
        "smoke test passed."
    )
    print(
        "Canonical identities: PASS"
    )
    print(
        "Multiple causes: PASS"
    )
    print(
        "Multiple paths: PASS"
    )
    print(
        "Directive invocation: PASS"
    )


if __name__ == "__main__":
    main()