"""Focused synchronous registry-linked directive execution coverage."""

from __future__ import annotations

from dataclasses import replace

from air.expressions import AIRBooleanLiteral, AIRIntegerLiteral
from air.linker import DuplicateLinkDefinitionError
from air.model import (
    AIRAuthority,
    AIRDirective,
    AIRProgram,
    AIRRole,
    AIRRoleAuthority,
    AIRWhenAction,
    DirectiveAuthority,
    DirectiveRequirement,
    StateAssignment,
    StateDefinition,
)
from air.types import AIR_VERSION
from authority.model import Principal
from authority.registry import AuthorityRegistry
from authority.validator import PrincipalAuthorizationError
from causality.model import (
    CausalDecision,
    CausalPath,
    DirectiveInvocation,
)
from workflow.air_runner import (
    build_registry_execution_plan,
    run_air_from_registry,
    run_air_program,
)
from workflow.directive_engine import (
    DirectiveExecutionEngine,
    DirectiveRequirementOwnershipError,
)
from workflow.registry import PrincipalRegistry


class MemoryRegistry:
    def __init__(self, programs):
        self._programs = {
            name.casefold(): program
            for name, program in programs.items()
        }

    def resolve(self, name):
        return self._programs[name.casefold()]


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def path(name, actions, weight=10):
    return CausalPath(
        id=f"path:{name}",
        weight=weight,
        actions=tuple(actions),
    )


def declaration(name, paths, *, authorities=()):
    decision = CausalDecision(
        id=f"cause:{name}",
        cause=name,
        paths=tuple(paths),
    )
    directive = AIRDirective(
        id=f"directive:{name}",
        name=name,
        principal=f"principal:{name}",
        authority_checks=(),
        causal_decisions=(decision.id,),
        order=0,
        authorities=tuple(authorities),
    )
    return directive, decision


def program(
    *declarations,
    states=(),
    requirements=(),
    authorities=(),
    roles=(),
    extra_principals=(),
):
    directives = tuple(
        replace(directive, order=index)
        for index, (directive, _) in enumerate(declarations)
    )
    decisions = tuple(
        decision
        for _, decision in declarations
    )
    principals = tuple(
        Principal(
            id=directive.principal,
            display_name=directive.name,
        )
        for directive in directives
    ) + tuple(extra_principals)

    return AIRProgram(
        version=AIR_VERSION,
        states=tuple(states),
        events=(),
        authority_checks=(),
        causal_decisions=decisions,
        directives=directives,
        requirements=tuple(requirements),
        authorities=tuple(authorities),
        principals=principals,
        roles=tuple(roles),
        functions=(),
        workflows=(),
    )


def add(value):
    return StateAssignment(
        state="state:value",
        operation="add_int",
        value=AIRIntegerLiteral(value),
    )


def entered(result):
    return tuple(
        next(
            fact.value
            for fact in step.facts
            if fact.key == "directive"
        )
        for step in result.trace.steps
        if step.kind == "directive.start"
    )


def state():
    return StateDefinition(
        id="state:value",
        initial=AIRIntegerLiteral(0),
    )


def execute_with_principal(
    registry,
    root,
    principal,
    authorities=(),
):
    principal_registry = PrincipalRegistry()
    principal_registry.register(principal)
    authority_registry = AuthorityRegistry()

    for authority in authorities:
        authority_registry.register(authority)

    return DirectiveExecutionEngine().execute(
        registry=registry,
        authority_registry=authority_registry,
        principal_registry=principal_registry,
        principal_name=principal.id,
        root=root,
    )


def test_local_and_external_ordering_equivalence():
    child = declaration(
        "External",
        (path("External", (add(10),)),),
    )
    caller = declaration(
        "Caller",
        (
            path(
                "Caller",
                (
                    add(1),
                    DirectiveInvocation(target="External"),
                    add(2),
                ),
            ),
        ),
    )
    local_result = run_air_program(
        program(caller, child, states=(state(),)),
        entry_directives=("Caller",),
    )
    external_result = run_air_from_registry(
        MemoryRegistry(
            {
                "caller": program(
                    caller,
                    states=(state(),),
                ),
                "external": program(child),
            }
        ),
        "caller",
    )

    require(local_result.ok, "local invocation failed")
    require(external_result.ok, "registry invocation failed")
    require(
        local_result.final_state == external_result.final_state,
        "local and registry-linked states differ",
    )
    require(
        tuple(
            item.value
            for item in external_result.delta.assignments
        )
        == (1, 10, 2),
        "action after registry invocation ran out of order",
    )
    require(
        entered(external_result)
        == ("directive:Caller", "directive:External"),
        "registry target was not executed inline",
    )


def test_child_failure_rolls_back_caller_and_unknown_is_run002():
    broken = declaration(
        "Broken",
        (
            path(
                "Broken",
                (DirectiveInvocation(target="Missing"),),
            ),
        ),
    )
    caller = declaration(
        "Caller",
        (
            path(
                "Caller",
                (
                    add(1),
                    DirectiveInvocation(target="Broken"),
                    add(100),
                ),
            ),
        ),
    )
    result = run_air_from_registry(
        MemoryRegistry(
            {
                "caller": program(
                    caller,
                    states=(state(),),
                ),
                "broken": program(broken),
            }
        ),
        "caller",
    )

    require(not result.ok, "unknown target succeeded")
    require(
        result.final_state.get_int("value") == 0,
        "unknown nested target did not roll back caller",
    )
    require(result.delta.is_empty, "rollback returned a delta")
    require(
        any(
            diagnostic.code == "RUN002"
            and "Missing" in diagnostic.message
            for diagnostic in result.diagnostics
        ),
        "unknown target did not produce RUN002",
    )


def test_local_intermediate_discovers_external():
    external = declaration(
        "External",
        (path("External", (add(4),)),),
    )
    local = declaration(
        "Local",
        (
            path(
                "Local",
                (DirectiveInvocation(target="External"),),
            ),
        ),
    )
    root = declaration(
        "Root",
        (
            path(
                "Root",
                (DirectiveInvocation(target="Local"),),
            ),
        ),
    )
    result = run_air_from_registry(
        MemoryRegistry(
            {
                "root": program(
                    root,
                    local,
                    states=(state(),),
                ),
                "external": program(external),
            }
        ),
        "root",
    )

    require(result.ok, "local intermediate chain failed")
    require(
        entered(result)
        == (
            "directive:Root",
            "directive:Local",
            "directive:External",
        ),
        "local intermediate was not scanned for dependencies",
    )


def test_nested_multi_program_dependency_closure():
    d = declaration("D", (path("D", (add(8),)),))
    c = declaration(
        "C",
        (path("C", (DirectiveInvocation(target="D"),)),),
    )
    b = declaration(
        "B",
        (path("B", (DirectiveInvocation(target="C"),)),),
    )
    root = declaration(
        "Root",
        (path("Root", (DirectiveInvocation(target="B"),)),),
    )
    result = run_air_from_registry(
        MemoryRegistry(
            {
                "root": program(
                    root,
                    states=(state(),),
                ),
                "b": program(b, c),
                "d": program(d),
            }
        ),
        "root",
    )

    require(result.ok, "multi-program closure failed")
    require(
        entered(result)
        == (
            "directive:Root",
            "directive:B",
            "directive:C",
            "directive:D",
        ),
        "multi-program closure was incomplete",
    )


def test_mixed_case_reference():
    external = declaration(
        "External",
        (path("External", (add(3),)),),
    )
    root = declaration(
        "Root",
        (
            path(
                "Root",
                (
                    DirectiveInvocation(
                        target="eXtErNaL",
                    ),
                ),
            ),
        ),
    )
    result = run_air_from_registry(
        MemoryRegistry(
            {
                "root": program(
                    root,
                    states=(state(),),
                ),
                "external": program(external),
            }
        ),
        "root",
    )

    require(result.ok, "mixed-case reference failed")
    require(
        entered(result)
        == ("directive:Root", "directive:External"),
        "mixed-case target resolved inconsistently",
    )


def test_registry_cycle_preserves_run003_and_rollback():
    a = declaration(
        "A",
        (
            path(
                "A",
                (add(1), DirectiveInvocation(target="B")),
            ),
        ),
    )
    b = declaration(
        "B",
        (
            path(
                "B",
                (add(2), DirectiveInvocation(target="a")),
            ),
        ),
    )
    result = run_air_from_registry(
        MemoryRegistry(
            {
                "a": program(a, states=(state(),)),
                "b": program(b),
            }
        ),
        "a",
    )

    require(not result.ok, "registry cycle succeeded")
    require(result.delta.is_empty, "cycle returned a delta")
    require(
        result.final_state.get_int("value") == 0,
        "cycle did not roll back",
    )
    require(
        any(
            diagnostic.code == "RUN003"
            for diagnostic in result.diagnostics
        ),
        "registry cycle did not preserve RUN003",
    )


def test_unselected_paths_and_branches_do_not_execute():
    denied = AIRAuthority(
        id="authority:Denied",
        name="Denied",
        capabilities=(),
    )
    child = declaration(
        "Child",
        (path("Child", (add(100),)),),
        authorities=(DirectiveAuthority("Denied"),),
    )
    root = declaration(
        "Root",
        (
            path(
                "Selected",
                (
                    add(1),
                    AIRWhenAction(
                        condition=AIRBooleanLiteral(False),
                        actions=(
                            DirectiveInvocation(target="Child"),
                        ),
                        otherwise_actions=(add(2),),
                    ),
                ),
                weight=10,
            ),
            path(
                "Unselected",
                (DirectiveInvocation(target="Child"),),
                weight=1,
            ),
        ),
    )
    registry = MemoryRegistry(
        {
            "root": program(
                root,
                states=(state(),),
            ),
            "child": program(
                child,
                authorities=(denied,),
            ),
        }
    )
    actor = Principal("principal:Actor", "Actor")
    plan = build_registry_execution_plan(registry, "root")

    require(
        any(
            directive.id == "directive:Child"
            for directive in plan.program.directives
        ),
        "unselected known dependency was not linked",
    )

    result = execute_with_principal(
        registry,
        "root",
        actor,
        authorities=(denied,),
    ).results[0][1]

    require(result.ok, "unselected child was authorized or run")
    require(
        entered(result) == ("directive:Root",),
        "unselected linked child executed",
    )
    require(
        result.final_state.get_int("value") == 3,
        "selected conditional branch produced wrong state",
    )


def test_duplicate_invocations_execute_twice():
    child = declaration(
        "Child",
        (path("Child", (add(1),)),),
    )
    root = declaration(
        "Root",
        (
            path(
                "Root",
                (
                    DirectiveInvocation(target="Child"),
                    DirectiveInvocation(target="Child"),
                ),
            ),
        ),
    )
    result = run_air_from_registry(
        MemoryRegistry(
            {
                "root": program(
                    root,
                    states=(state(),),
                ),
                "child": program(child),
            }
        ),
        "root",
    )

    require(result.ok, "duplicate invocations failed")
    require(
        result.final_state.get_int("value") == 2,
        "duplicate invocation did not execute exactly twice",
    )
    require(
        entered(result).count("directive:Child") == 2,
        "dependency was duplicated or invocation was suppressed",
    )


def test_exact_shared_principal_coalesces():
    shared = Principal(
        id="principal:Shared",
        display_name="Shared",
    )
    child = declaration("Child", (path("Child", ()),))
    root = declaration(
        "Root",
        (path("Root", (DirectiveInvocation(target="Child"),)),),
    )
    plan = build_registry_execution_plan(
        MemoryRegistry(
            {
                "root": program(
                    root,
                    extra_principals=(shared,),
                ),
                "child": program(
                    child,
                    extra_principals=(shared,),
                ),
            }
        ),
        "root",
    )

    require(
        tuple(
            principal.id
            for principal in plan.program.principals
        ).count("principal:Shared")
        == 1,
        "exact shared principal was not coalesced",
    )


def test_conflicting_shared_principal_is_rejected():
    child = declaration("Child", (path("Child", ()),))
    root = declaration(
        "Root",
        (path("Root", (DirectiveInvocation(target="Child"),)),),
    )

    try:
        build_registry_execution_plan(
            MemoryRegistry(
                {
                    "root": program(
                        root,
                        extra_principals=(
                            Principal(
                                "principal:Shared",
                                "First",
                            ),
                        ),
                    ),
                    "child": program(
                        child,
                        extra_principals=(
                            Principal(
                                "principal:Shared",
                                "Second",
                            ),
                        ),
                    ),
                }
            ),
            "root",
        )
    except DuplicateLinkDefinitionError as error:
        require(
            error.owner == "principal"
            and error.identifier == "principal:Shared",
            "conflicting principal diagnostic changed",
        )
    else:
        raise AssertionError(
            "conflicting shared principal was accepted"
        )


def test_entered_child_authority_denial():
    denied = AIRAuthority(
        id="authority:Denied",
        name="Denied",
        capabilities=(),
    )
    child = declaration(
        "Child",
        (path("Child", (add(100),)),),
        authorities=(DirectiveAuthority("Denied"),),
    )
    root = declaration(
        "Root",
        (
            path(
                "Root",
                (
                    add(1),
                    DirectiveInvocation(target="Child"),
                    add(1000),
                ),
            ),
        ),
    )
    registry = MemoryRegistry(
        {
            "root": program(
                root,
                states=(state(),),
            ),
            "child": program(
                child,
                authorities=(denied,),
            ),
        }
    )

    try:
        execute_with_principal(
            registry,
            "root",
            Principal("principal:Actor", "Actor"),
            authorities=(denied,),
        )
    except PrincipalAuthorizationError as error:
        require(
            "principal:Actor" in str(error)
            and "Denied" in str(error),
            "child authority denial diagnostic changed",
        )
    else:
        raise AssertionError(
            "entered child bypassed authority authorization"
        )


def test_role_derived_child_capability_requirement():
    authority = AIRAuthority(
        id="authority:Executor",
        name="Executor",
        capabilities=("Execute",),
    )
    role = AIRRole(
        name="Architect",
        authorities=(
            AIRRoleAuthority(name="Executor"),
        ),
    )
    child = declaration(
        "Child",
        (path("Child", (add(5),)),),
    )
    root = declaration(
        "Root",
        (path("Root", (DirectiveInvocation(target="Child"),)),),
    )
    registry = MemoryRegistry(
        {
            "root": program(
                root,
                states=(state(),),
            ),
            "child": program(
                child,
                requirements=(
                    DirectiveRequirement(capability="Execute"),
                ),
                authorities=(authority,),
                roles=(role,),
            ),
        }
    )
    actor = Principal(
        id="principal:Actor",
        display_name="Actor",
        roles=("Architect",),
    )
    result = execute_with_principal(
        registry,
        "root",
        actor,
        authorities=(authority,),
    ).results[0][1]

    require(result.ok, "role-derived requirement failed")
    require(
        result.final_state.get_int("value") == 5,
        "authorized child did not execute",
    )


def test_multi_directive_requirement_owner_is_ambiguous():
    child = declaration("Child", (path("Child", ()),))
    sibling = declaration("Sibling", (path("Sibling", ()),))
    root = declaration(
        "Root",
        (path("Root", (DirectiveInvocation(target="Child"),)),),
    )
    registry = MemoryRegistry(
        {
            "root": program(root),
            "child": program(
                child,
                sibling,
                requirements=(
                    DirectiveRequirement(capability="Execute"),
                ),
            ),
        }
    )

    try:
        execute_with_principal(
            registry,
            "root",
            Principal("principal:Actor", "Actor"),
        )
    except DirectiveRequirementOwnershipError as error:
        require(
            "cannot determine capability requirement ownership"
            in str(error),
            "requirement ownership diagnostic changed",
        )
    else:
        raise AssertionError(
            "ambiguous requirement ownership was accepted"
        )


def main():
    test_local_and_external_ordering_equivalence()
    test_child_failure_rolls_back_caller_and_unknown_is_run002()
    test_local_intermediate_discovers_external()
    test_nested_multi_program_dependency_closure()
    test_mixed_case_reference()
    test_registry_cycle_preserves_run003_and_rollback()
    test_unselected_paths_and_branches_do_not_execute()
    test_duplicate_invocations_execute_twice()
    test_exact_shared_principal_coalesces()
    test_conflicting_shared_principal_is_rejected()
    test_entered_child_authority_denial()
    test_role_derived_child_capability_requirement()
    test_multi_directive_requirement_owner_is_ambiguous()
    print(
        "Registry-linked directive execution smoke test passed."
    )


if __name__ == "__main__":
    main()
