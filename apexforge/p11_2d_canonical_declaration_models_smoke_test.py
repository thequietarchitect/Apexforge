"""Focused coverage for P11.2D canonical declaration lowering."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, is_dataclass

from air.model import (
    AIRAuthority,
    AIRDirective,
    AIRPrincipal,
    AIRProgram,
    AIRRole,
    AIRWorkflow,
    AIRWorkflowInvocation,
    AuthorityCheck as AirAuthorityCheck,
    AuthorityGrant as AirAuthorityGrant,
    Principal as AirPrincipal,
    PrincipalAuthority,
)
from air.serialization import air_to_dict
from authority.compiler import compile_authority
from authority.engine import AuthorityEngine
from authority.model import AuthorityCheck, AuthorityGrant, Principal
from authority.registry import (
    AuthorityInheritanceError,
    AuthorityRegistry,
    UnknownAuthorityError,
)
from language.parser import (
    AuthorityNode,
    PrincipalNode,
    RoleNode,
    WorkflowNode,
    parse,
    parse_source_unit,
)
from principal_compiler import compile_principal
from role_compiler import compile_role
from workflow.compiler import compile_workflow


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def require_raises(expected_type, operation, message: str):
    try:
        operation()
    except expected_type as error:
        return error
    raise AssertionError(message)


def field_names(model_type) -> tuple[str, ...]:
    return tuple(field.name for field in fields(model_type))


def test_passive_frozen_model_contracts() -> None:
    contracts = {
        AIRAuthority: ("id", "name", "capabilities", "inherits"),
        AIRWorkflowInvocation: ("target",),
        AIRWorkflow: ("id", "name", "invocations"),
    }
    for model_type, expected_fields in contracts.items():
        require(is_dataclass(model_type), f"{model_type.__name__} is not a dataclass")
        require(model_type.__dataclass_params__.frozen, f"{model_type.__name__} is not frozen")
        require(field_names(model_type) == expected_fields, f"{model_type.__name__} fields changed")

    authority = AIRAuthority("authority:Sentinel", "Sentinel", ("Observe",))
    require_raises(
        FrozenInstanceError,
        lambda: setattr(authority, "name", "Changed"),
        "AIRAuthority accepted mutation",
    )


def test_authority_compilation_and_registry() -> None:
    sentinel_node = parse(
        "authority Sentinel { capability Observe capability Investigate }"
    )
    child_node = parse("authority Child extends Sentinel {}")
    require(isinstance(sentinel_node, AuthorityNode), "authority parser shape changed")
    require(isinstance(child_node, AuthorityNode), "extended authority parser shape changed")

    sentinel = compile_authority(sentinel_node)
    child = compile_authority(child_node)
    require(
        sentinel == AIRAuthority(
            id="authority:Sentinel",
            name="Sentinel",
            capabilities=("Observe", "Investigate"),
            inherits=(),
        ),
        "authority identity, capabilities, or declared order changed",
    )
    require(
        child == AIRAuthority(
            id="authority:Child",
            name="Child",
            capabilities=(),
            inherits=("Sentinel",),
        ),
        "authority inheritance lowering changed",
    )
    require(
        compile_authority(sentinel_node) == sentinel
        and compile_authority(child_node) == child,
        "repeated authority compilation was nondeterministic",
    )

    registry = AuthorityRegistry()
    registry.register(sentinel)
    registry.register(child)
    require(registry.get("SENTINEL") is sentinel, "authority lookup lost case folding")
    require(
        registry.resolve_capabilities("child") == {"Observe", "Investigate"},
        "compiled authority inheritance did not resolve",
    )
    require(registry.has_capability("CHILD", "Investigate"), "capability lookup failed")
    require(
        registry.list_authorities() == ("sentinel", "child"),
        "authority listing changed deterministic registration order",
    )

    cycle = AuthorityRegistry()
    cycle.register(AIRAuthority("authority:A", "A", (), ("B",)))
    cycle.register(AIRAuthority("authority:B", "B", (), ("A",)))
    cycle_error = require_raises(
        AuthorityInheritanceError,
        lambda: cycle.resolve_capabilities("A"),
        "authority inheritance cycle was accepted",
    )
    require("cycle" in str(cycle_error).lower(), "cycle diagnostic changed category")
    unknown_error = require_raises(
        UnknownAuthorityError,
        lambda: registry.resolve_capabilities("Missing"),
        "unknown authority resolution was accepted",
    )
    require("Missing" in str(unknown_error), "unknown-authority diagnostic lost its name")


def test_runtime_authority_contract_is_unchanged() -> None:
    require(
        field_names(AuthorityGrant) == ("principal", "capability", "resource"),
        "runtime AuthorityGrant shape changed",
    )
    require(
        AirPrincipal is Principal
        and AirAuthorityCheck is AuthorityCheck
        and AirAuthorityGrant is AuthorityGrant,
        "runtime authority consolidation class identities changed",
    )
    grant = AuthorityGrant(
        principal="principal:Operator",
        capability="Observe",
        resource="resource:Report",
    )
    require(
        AuthorityEngine.from_grants((grant,)).check(
            principal="principal:Operator",
            capability="Observe",
            resource="resource:Report",
        ),
        "runtime AuthorityGrant no longer authorizes its exact permission",
    )


def test_principal_and_role_compilation() -> None:
    principal_node = parse(
        "principal Operator { role Architect role Auditor "
        "authority Aegis authority Sentinel }"
    )
    require(isinstance(principal_node, PrincipalNode), "principal parser shape changed")
    principal = compile_principal(principal_node)
    require(isinstance(principal, Principal), "principal lowering is not canonical Principal")
    require(not isinstance(principal, AIRPrincipal), "principal lowering returned legacy AIRPrincipal")
    require(
        principal == Principal(
            id="principal:Operator",
            display_name="Operator",
            roles=("Architect", "Auditor"),
            authorities=(
                PrincipalAuthority(name="Aegis"),
                PrincipalAuthority(name="Sentinel"),
            ),
        ),
        "principal identity, display name, roles, or authorities changed",
    )
    require(compile_principal(principal_node) == principal, "principal lowering was nondeterministic")

    role_node = parse("role Architect { authority Aegis authority Sentinel }")
    require(isinstance(role_node, RoleNode), "role parser shape changed")
    role = compile_role(role_node)
    require(isinstance(role, AIRRole), "role lowering stopped returning AIRRole")
    require(
        tuple(item.name for item in role.authorities) == ("Aegis", "Sentinel"),
        "role authority order changed",
    )
    require(compile_role(role_node) == role, "role lowering was nondeterministic")


def test_workflow_compilation() -> None:
    workflow_node = parse(
        "workflow Response { invoke Detect invoke Contain invoke Recover }"
    )
    require(isinstance(workflow_node, WorkflowNode), "workflow parser shape changed")
    workflow = compile_workflow(workflow_node)
    require(
        workflow == AIRWorkflow(
            id="workflow:Response",
            name="Response",
            invocations=(
                AIRWorkflowInvocation(target="Detect"),
                AIRWorkflowInvocation(target="Contain"),
                AIRWorkflowInvocation(target="Recover"),
            ),
        ),
        "workflow identity or exact invocation order changed",
    )
    require(compile_workflow(workflow_node) == workflow, "workflow lowering was nondeterministic")


def test_program_serialization_and_parser_boundaries() -> None:
    program_fields = (
        "version", "states", "events", "authority_checks", "causal_decisions",
        "directives", "requirements", "authorities", "principals", "roles", "functions",
        "workflows",
    )
    directive_fields = (
        "id", "name", "principal", "authority_checks", "causal_decisions", "order",
        "authorities",
    )
    require(
        field_names(AIRProgram) == program_fields,
        "AIRProgram fields changed outside the intentional P11.2E append",
    )
    require(
        field_names(AIRDirective) == directive_fields,
        "AIRDirective fields changed outside the intentional P11.2E append",
    )
    empty_program = AIRProgram(
        version="test",
        states=(),
        events=(),
        authority_checks=(),
        causal_decisions=(),
        directives=(),
        requirements=(),
    )
    require(
        tuple(air_to_dict(empty_program)) == program_fields[:-1],
        "empty P11.2E workflow collection changed historical serialization",
    )

    source_unit = parse_source_unit(
        "authority Aegis {}\nprincipal Operator {}\n"
        "role Architect {}\nworkflow Response {}\n",
        source_name="p11-2d-parser-compat.apex",
    )
    require(
        tuple(type(item) for item in source_unit.declarations)
        == (AuthorityNode, PrincipalNode, RoleNode, WorkflowNode),
        "P11.2C heterogeneous parser order or declaration coverage changed",
    )


def main() -> None:
    test_passive_frozen_model_contracts()
    test_authority_compilation_and_registry()
    test_runtime_authority_contract_is_unchanged()
    test_principal_and_role_compilation()
    test_workflow_compilation()
    test_program_serialization_and_parser_boundaries()
    print("AFP-P11.2D canonical declaration models smoke test passed.")
    print("Passive frozen authority and workflow AIR models: PASS")
    print("Authority lowering, registry, inheritance, and errors: PASS")
    print("Runtime authority identities and grant shape: PASS")
    print("Canonical principal and preserved role lowering: PASS")
    print("Passive deterministic workflow lowering: PASS")
    print("AIRProgram, serialization, and P11.2C parser boundaries: PASS")


if __name__ == "__main__":
    main()
