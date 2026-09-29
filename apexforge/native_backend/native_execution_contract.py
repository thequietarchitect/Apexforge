"""Executable admission contract; no code generation or execution semantics."""
from __future__ import annotations

from dataclasses import dataclass, fields
from types import MappingProxyType

from air.expressions import AIRIntegerLiteral
from air.model import AIRDirective, AIRProgram, StateAssignment, StateDefinition, VerifiedAIRProgram
from air.verify import AIRVerifier
from authority.model import Principal
from causality.model import CausalDecision, CausalPath
from type_system.model import INT
from workflow.air_runner import RegistryExecutionPlan

from .execution_plan_binding import bind_registry_execution_plan
from .lowering_input import build_verified_air_lowering_input


PROFILE = "apexforge.native.win-x64.i64-literal-state-set/v1"
MIN_I64, MAX_I64 = -(2 ** 63), 2 ** 63 - 1
MAX_STATES, MAX_STORES = 256, 4096


class NativeExecutionError(ValueError):
    def __init__(self, code: str, detail: str):
        self.code = code
        super().__init__(f"{code}: {detail}")


def require(condition: bool, detail: str, code: str = "NATIVE_PROFILE_UNSUPPORTED") -> None:
    if not condition:
        raise NativeExecutionError(code, detail)


_FIELDS = {
    AIRProgram: "version states events authority_checks causal_decisions directives requirements authorities principals roles functions workflows",
    AIRDirective: "id name principal authority_checks causal_decisions order authorities",
    Principal: "id display_name roles authorities",
    StateDefinition: "id initial value_type",
    StateAssignment: "state operation value",
    CausalDecision: "id cause paths policy",
    CausalPath: "id weight assignments emits invocations effects rationale actions",
    AIRIntegerLiteral: "value",
    VerifiedAIRProgram: "program",
    RegistryExecutionPlan: "program entry_directive directive_owners",
}


def exact(value, expected) -> None:
    require(type(value) is expected, f"expected exact {expected.__name__}")
    require(tuple(field.name for field in fields(expected)) == tuple(_FIELDS[expected].split()),
            f"unreviewed {expected.__name__} schema")


def sequence(value) -> None:
    require(type(value) is tuple, "canonical tuple required")


def identity(value) -> None:
    require(type(value) is str and bool(value.strip()) and len(value) <= 256, "invalid profile ID")


def literal(value) -> int:
    if type(value) is AIRIntegerLiteral:
        exact(value, AIRIntegerLiteral)
        value = value.value
    require(type(value) is int and MIN_I64 <= value <= MAX_I64, "only signed-I64 integer literals supported")
    return value


@dataclass(frozen=True)
class NativeProfileAdmission:
    air_fingerprint: str
    routing_fingerprint: str
    entry: str
    state_ids: tuple[str, ...]
    initial_values: tuple[int, ...]
    # Exact verified-ID relocations in canonical order, not evaluated state.
    stores: tuple[tuple[int, int], ...]
    profile: str = PROFILE


def admit_native_profile(verified: VerifiedAIRProgram, plan: RegistryExecutionPlan) -> NativeProfileAdmission:
    exact(verified, VerifiedAIRProgram)
    exact(plan, RegistryExecutionPlan)
    try:
        plan = RegistryExecutionPlan(plan.program, plan.entry_directive,
                                     MappingProxyType(dict(plan.directive_owners)))
    except (TypeError, ValueError) as exc:
        raise NativeExecutionError("NATIVE_ROUTING_INVALID", "owner mapping cannot be snapshotted") from exc
    program = verified.program
    exact(program, AIRProgram)
    require(type(program.version) is str, "canonical version string required")
    for field in ("states", "events", "authority_checks", "causal_decisions", "directives",
                  "requirements", "authorities", "principals", "roles", "functions", "workflows"):
        sequence(getattr(program, field))
    for field in ("events", "authority_checks", "requirements", "authorities", "roles", "functions", "workflows"):
        require(not getattr(program, field), f"{field} unsupported")
    require(len(program.directives) == len(program.principals) == 1, "one directive and principal required")
    require(1 <= len(program.states) <= MAX_STATES, "state limit")
    require(1 <= len(program.causal_decisions) <= MAX_STORES, "decision limit")
    directive, principal = program.directives[0], program.principals[0]
    exact(directive, AIRDirective)
    exact(principal, Principal)
    for value in (directive.id, directive.principal, principal.id):
        identity(value)
    require(type(directive.name) is str and type(principal.display_name) is str, "invalid metadata")
    require(type(directive.order) is int and directive.order == 0, "directive order must be zero")
    for value in (directive.authority_checks, directive.authorities, principal.roles, principal.authorities):
        sequence(value)
        require(not value, "authority-bearing programs unsupported")
    sequence(directive.causal_decisions)
    state_ids, initials = [], []
    for state in program.states:
        exact(state, StateDefinition)
        identity(state.id)
        require(state.value_type is INT, "only explicit canonical INT states supported")
        state_ids.append(state.id)
        initials.append(literal(state.initial))
    decisions = {}
    store_count = 0
    for decision in program.causal_decisions:
        exact(decision, CausalDecision)
        identity(decision.id)
        require(type(decision.cause) is str and type(decision.policy) is str and decision.policy == "max_weight", "unsupported causal metadata/policy")
        sequence(decision.paths)
        require(len(decision.paths) == 1, "alternative paths unsupported")
        path = decision.paths[0]
        exact(path, CausalPath)
        identity(path.id)
        require(type(path.weight) is int and type(path.rationale) is str, "invalid path metadata")
        for field in ("actions", "emits", "effects", "invocations"):
            sequence(getattr(path, field))
            require(not getattr(path, field), f"path {field} unsupported")
        sequence(path.assignments)
        for assignment in path.assignments:
            exact(assignment, StateAssignment)
            identity(assignment.state)
            require(type(assignment.operation) is str and assignment.operation == "set_int", "only set_int supported")
            literal(assignment.value)
        store_count += len(path.assignments)
        decisions[decision.id] = path
    require(1 <= store_count <= MAX_STORES, "store limit")
    for key in directive.causal_decisions:
        identity(key)
    require(len(directive.causal_decisions) == len(set(directive.causal_decisions)) == len(program.causal_decisions)
            and set(directive.causal_decisions) == set(decisions), "unused/repeated decision unsupported")
    try:
        canonical = AIRVerifier().verify(program).require_verified()
    except (ValueError, TypeError, KeyError, AttributeError) as exc:
        raise NativeExecutionError("NATIVE_AIR_INVALID", "canonical verification failed") from exc
    require(type(plan.entry_directive) is str and plan.entry_directive == directive.id,
            "entry must be the exact canonical directive ID", "NATIVE_ROUTING_INVALID")
    try:
        require(tuple(plan.directive_owners) == (directive.id.casefold(),), "one canonical owner required", "NATIVE_ROUTING_INVALID")
        owner = plan.owner_of(directive.id)
        exact(owner, AIRProgram)
        # Equality is only an early check: Python considers True equal to 1.
        # Canonical transport must also match for the entire owning program.
        require(owner == program and plan.program == program, "owner/program mismatch", "NATIVE_ROUTING_INVALID")
        lowering = build_verified_air_lowering_input(canonical)
        owner_lowering = build_verified_air_lowering_input(VerifiedAIRProgram(owner))
        require(owner_lowering.transport_json == lowering.transport_json,
                "owner canonical transport mismatch", "NATIVE_ROUTING_INVALID")
        binding = bind_registry_execution_plan(lowering, plan)
    except NativeExecutionError:
        raise
    except (ValueError, TypeError, KeyError, AttributeError) as exc:
        raise NativeExecutionError("NATIVE_ROUTING_INVALID", "invalid registry routing") from exc
    relocation = {key: index for index, key in enumerate(state_ids)}
    stores = tuple((relocation[assignment.state], literal(assignment.value))
                   for key in directive.causal_decisions for assignment in decisions[key].assignments)
    return NativeProfileAdmission(lowering.transport_fingerprint, binding.routing_fingerprint,
                                  directive.id, tuple(state_ids), tuple(initials), stores)
