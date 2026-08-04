"""P11.2F-C heterogeneous AIRVerifier and reference-closure coverage."""

from __future__ import annotations

from dataclasses import replace

from air.expressions import AIRBooleanLiteral
from air.model import (
    AIRAuthority,
    AIRDirective,
    AIRProgram,
    AIRWhenAction,
    AIRWorkflow,
    AIRWorkflowInvocation,
    DirectiveAuthority,
)
from air.types import AIR_VERSION
from air.verify import AIRVerifier
from authority.model import Principal
from causality.model import (
    CausalDecision,
    CausalPath,
    DirectiveInvocation,
)
from language.compiler import compile_source


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def empty_program(**changes) -> AIRProgram:
    program = AIRProgram(
        version=AIR_VERSION,
        states=(),
        events=(),
        authority_checks=(),
        causal_decisions=(),
        directives=(),
        requirements=(),
        authorities=(),
        principals=(),
        roles=(),
        functions=(),
        workflows=(),
    )
    return replace(program, **changes)


def diagnostic_projection(result) -> tuple[tuple[str, str, str], ...]:
    return tuple(
        (item.code, item.message, item.node_id)
        for item in result.diagnostics
    )


def test_valid_heterogeneous_reference_closure() -> None:
    program = compile_source(
        "authority Aegis {}\n"
        "directive Main {\n"
        "    authority Aegis\n"
        "    cause Route {\n"
        "        path Go @ 10 { invoke Child }\n"
        "    }\n"
        "}\n"
        "directive Child {}\n"
        "workflow Flow { invoke Main invoke child }\n"
        "function Helper() { return 0 }\n"
        "role Architect {}"
    )
    result = AIRVerifier().verify(program)
    require(
        result.ok,
        "valid heterogeneous references did not verify: "
        + repr(diagnostic_projection(result)),
    )


def test_promoted_family_uniqueness() -> None:
    function = compile_source(
        "function Helper() { return 0 }"
    ).functions[0]
    workflow = compile_source("workflow Flow {}").workflows[0]
    authority = compile_source("authority Aegis {}").authorities[0]
    role = compile_source("role Architect {}").roles[0]

    result = AIRVerifier().verify(
        empty_program(
            functions=(function, function),
            workflows=(workflow, workflow),
            authorities=(authority, authority),
            roles=(role, role),
        )
    )
    observed = tuple(
        (item.message, item.node_id)
        for item in result.diagnostics
        if item.code == "AIR000"
    )
    require(
        observed
        == (
            (
                "duplicate authority id: authority:Aegis",
                "authority:Aegis",
            ),
            (
                "duplicate function id: function:Helper",
                "function:Helper",
            ),
            (
                "duplicate role id: role:Architect",
                "role:Architect",
            ),
            (
                "duplicate workflow id: workflow:Flow",
                "workflow:Flow",
            ),
        ),
        "promoted declaration uniqueness diagnostics changed: "
        + repr(observed),
    )


def test_proven_casefolded_verifier_identities() -> None:
    root = Principal(
        id="principal:Root",
        display_name="Root",
    )
    principal_upper = Principal(
        id="principal:Operator",
        display_name="Operator",
    )
    principal_lower = Principal(
        id="principal:operator",
        display_name="operator",
    )
    directive_upper = AIRDirective(
        id="directive:Sentinel",
        name="Sentinel",
        principal=root.id,
        authority_checks=(),
        causal_decisions=(),
        order=0,
    )
    directive_lower = AIRDirective(
        id="directive:sentinel",
        name="sentinel",
        principal=root.id,
        authority_checks=(),
        causal_decisions=(),
        order=1,
    )
    authority_upper = AIRAuthority(
        id="authority:AegisUpper",
        name="Aegis",
        capabilities=(),
    )
    authority_lower = AIRAuthority(
        id="authority:AegisLower",
        name="aegis",
        capabilities=(),
    )

    first = AIRVerifier().verify(
        empty_program(
            principals=(root, principal_upper, principal_lower),
            directives=(directive_upper, directive_lower),
            authorities=(authority_upper, authority_lower),
        )
    )
    second = AIRVerifier().verify(
        empty_program(
            principals=(root, principal_lower, principal_upper),
            directives=(directive_lower, directive_upper),
            authorities=(authority_lower, authority_upper),
        )
    )

    expected = (
        (
            "AIR000",
            "duplicate authority id: authority:aegis",
            "authority:aegis",
        ),
        (
            "AIR000",
            "duplicate directive id: directive:sentinel",
            "directive:sentinel",
        ),
        (
            "AIR000",
            "duplicate principal id: principal:operator",
            "principal:operator",
        ),
    )
    require(
        diagnostic_projection(first) == expected,
        "casefolded verifier diagnostics changed: "
        + repr(diagnostic_projection(first)),
    )
    require(
        diagnostic_projection(second) == expected,
        "casefolded verifier diagnostics depend on declaration order",
    )


def test_closed_directive_and_workflow_targets() -> None:
    principal = Principal(
        id="principal:Root",
        display_name="Root",
    )
    nested_path = CausalPath(
        id="path:Nested",
        weight=10,
        actions=(
            AIRWhenAction(
                condition=AIRBooleanLiteral(True),
                actions=(
                    DirectiveInvocation(target="Missing"),
                ),
                otherwise_actions=(
                    DirectiveInvocation(
                        target="directive:AlsoMissing"
                    ),
                ),
            ),
        ),
    )
    legacy_path = CausalPath(
        id="path:Legacy",
        weight=5,
        invocations=(
            DirectiveInvocation(target="LegacyMissing"),
        ),
    )
    decision = CausalDecision(
        id="cause:Flow",
        cause="Flow",
        policy="max_weight",
        paths=(nested_path, legacy_path),
    )
    directive = AIRDirective(
        id="directive:Main",
        name="Main",
        principal=principal.id,
        authority_checks=(),
        causal_decisions=(decision.id,),
        order=0,
        authorities=(
            DirectiveAuthority(name="Aegis"),
        ),
    )
    workflow = AIRWorkflow(
        id="workflow:Flow",
        name="Flow",
        invocations=(
            AIRWorkflowInvocation(target="Ghost"),
        ),
    )

    result = AIRVerifier().verify(
        empty_program(
            principals=(principal,),
            causal_decisions=(decision,),
            directives=(directive,),
            workflows=(workflow,),
        )
    )
    expected = (
        (
            "AIR045",
            "directive invocation target does not exist: "
            "LegacyMissing",
            "path:Legacy",
        ),
        (
            "AIR045",
            "directive invocation target does not exist: Missing",
            "path:Nested",
        ),
        (
            "AIR045",
            "directive invocation target does not exist: "
            "directive:AlsoMissing",
            "path:Nested",
        ),
        (
            "AIR046",
            "directive authority does not exist: Aegis",
            "directive:Main",
        ),
        (
            "AIR050",
            "workflow invocation target does not exist: Ghost",
            "workflow:Flow",
        ),
    )
    require(
        diagnostic_projection(result) == expected,
        "closed-reference diagnostics changed: "
        + repr(diagnostic_projection(result)),
    )
    require(
        diagnostic_projection(AIRVerifier().verify(result.program))
        == expected,
        "closed-reference diagnostics changed across repeated verification",
    )

    deferred = AIRVerifier().verify(
        result.program,
        allow_unresolved_directive_invocations=True,
    )
    require(
        all(item.code != "AIR045" for item in deferred.diagnostics),
        "registry compatibility mode retained AIR045",
    )
    require(
        tuple(item.code for item in deferred.diagnostics)
        == ("AIR046", "AIR050"),
        "registry compatibility mode suppressed non-invocation diagnostics",
    )


def main() -> None:
    test_valid_heterogeneous_reference_closure()
    test_promoted_family_uniqueness()
    test_proven_casefolded_verifier_identities()
    test_closed_directive_and_workflow_targets()
    print("P11.2F-C heterogeneous AIRVerifier smoke test passed.")
    print("Valid heterogeneous reference closure: PASS")
    print("Promoted declaration uniqueness: PASS")
    print("Proven casefolded verifier identities: PASS")
    print("Nested, legacy, authority, and workflow references: PASS")


if __name__ == "__main__":
    main()
