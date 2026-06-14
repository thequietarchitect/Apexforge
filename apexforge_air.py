"""
ApexForge AIR v0.1 - tight engineering brief.

This file is the first AIR-first artifact for ApexForge. It intentionally avoids
lexer/parser/AST concerns. The runtime consumes verified AIR only.

Hard boundaries:
- Authority is checked before directive evaluation and is not embedded in
  directive handlers.
- Causal evaluation uses integer weights and deterministic tie-breaking.
- Directives do not mutate state. They select causal paths that produce
  StateDelta objects.
- Runtime semantics are pure. Host effects are represented as EffectIntent
  objects and are not executed here.
- No ambient globals for time, user, authority, random, or state.

Blunt debt warning:
If syntax or AST execution arrives before this contract is stable, ApexForge
will accidentally turn parser shape into runtime semantics. Keep AIR boring,
verified, versioned, and backend-neutral.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Union


AIR_VERSION = "0.1"

Primitive = Union[int, str, bool]
Severity = Literal["error", "warning", "info"]
DecisionPolicy = Literal["max_weight"]
StateOperation = Literal["set_int", "add_int"]


PROPOSED_PYTHON_LAYOUT_V02 = """
apexforge/
  air/
    __init__.py
    model.py              # AIR dataclasses only
    verify.py             # AIR verifier
    serialize.py          # stable JSON encoding/decoding
  runtime/
    __init__.py
    context.py            # explicit execution context
    engine.py             # AIRProgram -> StateDelta + Trace
    state.py              # snapshots and deltas
    diagnostics.py
  authority/
    __init__.py
    model.py              # principals, grants, authority checks
    engine.py             # explicit policy evaluation
  causality/
    __init__.py
    model.py              # decisions, paths, weights
    engine.py             # deterministic selection and traces
  effects/
    __init__.py
    model.py              # EffectIntent only
    host.py               # optional host-side effect executor
  tests/
    test_air_verify.py
    test_runtime_execution.py
    test_authority.py
    test_causality.py
    test_determinism.py
"""


FIRST_FIVE_TESTS_BEFORE_SYNTAX = (
    "Verifier rejects missing references and duplicate IDs.",
    "Denied authority produces diagnostics and no state delta.",
    "Causal engine selects the highest integer weight deterministically.",
    "Equal causal weights tie-break by stable path ID, not collection order.",
    "Execution returns a StateDelta; the input StateSnapshot is unchanged.",
)


TECHNICAL_DEBT_RISKS = (
    "Executing AST nodes directly instead of verified AIR.",
    "Letting directives mutate StateSnapshot directly.",
    "Checking authority inside directive implementations.",
    "Using floats for causal weights when reproducibility matters.",
    "Using dict/hash iteration order as a semantic ordering rule.",
    "Using ambient current user, current time, random, or global state.",
    "Generating C# from syntax instead of from verified AIR.",
)


def _is_int(value: object) -> bool:
    return type(value) is int


def _as_tuple(values: object) -> tuple:
    if values is None:
        return ()
    if isinstance(values, tuple):
        return values
    return tuple(values)  # type: ignore[arg-type]


def _facts(**items: Primitive) -> tuple["Fact", ...]:
    return tuple(Fact(key, value) for key, value in sorted(items.items()))


def _append(diags: list["Diagnostic"], severity: Severity, code: str, message: str, node_id: str = "") -> None:
    diags.append(Diagnostic(severity, code, message, node_id))


def _index_by_id(items: tuple) -> dict[str, object]:
    return {item.id: item for item in items}


@dataclass(frozen=True, order=True)
class Fact:
    key: str
    value: Primitive


@dataclass(frozen=True, order=True)
class Diagnostic:
    severity: Severity
    code: str
    message: str
    node_id: str = ""

    @property
    def is_error(self) -> bool:
        return self.severity == "error"


@dataclass(frozen=True, order=True)
class TraceStep:
    kind: str
    message: str
    facts: tuple[Fact, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "facts", tuple(sorted(_as_tuple(self.facts))))


@dataclass(frozen=True)
class Trace:
    steps: tuple[TraceStep, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "steps", _as_tuple(self.steps))

    def render(self) -> str:
        lines: list[str] = []
        for step in self.steps:
            facts = ", ".join(f"{fact.key}={fact.value!r}" for fact in step.facts)
            suffix = f" [{facts}]" if facts else ""
            lines.append(f"{step.kind}: {step.message}{suffix}")
        return "\n".join(lines)


@dataclass(frozen=True, order=True)
class Principal:
    id: str
    display_name: str = ""


@dataclass(frozen=True, order=True)
class AuthorityGrant:
    principal: str
    capability: str
    resource: str


@dataclass(frozen=True, order=True)
class AuthorityCheck:
    id: str
    principal: str
    capability: str
    resource: str


@dataclass(frozen=True, order=True)
class StateDefinition:
    id: str
    initial: int = 0
    value_type: Literal["int"] = "int"


@dataclass(frozen=True, order=True)
class StateCell:
    key: str
    value: int


@dataclass(frozen=True)
class StateSnapshot:
    cells: tuple[StateCell, ...] = ()

    def __post_init__(self) -> None:
        cells = tuple(sorted(_as_tuple(self.cells)))
        seen: set[str] = set()
        for cell in cells:
            if cell.key in seen:
                raise ValueError(f"duplicate state cell: {cell.key}")
            if not _is_int(cell.value):
                raise TypeError(f"state cell {cell.key} must be an int")
            seen.add(cell.key)
        object.__setattr__(self, "cells", cells)

    @classmethod
    def from_mapping(cls, values: dict[str, int]) -> "StateSnapshot":
        return cls(tuple(StateCell(key, value) for key, value in values.items()))

    @classmethod
    def from_program_initials(cls, program: "AIRProgram") -> "StateSnapshot":
        return cls(tuple(StateCell(state.id, state.initial) for state in program.states))

    def get_int(self, key: str, default: int = 0) -> int:
        for cell in self.cells:
            if cell.key == key:
                return cell.value
        return default

    def apply(self, delta: "StateDelta") -> "StateSnapshot":
        values = {cell.key: cell.value for cell in self.cells}
        for assignment in delta.assignments:
            previous = values.get(assignment.state, 0)
            if assignment.operation == "set_int":
                values[assignment.state] = assignment.value
            elif assignment.operation == "add_int":
                values[assignment.state] = previous + assignment.value
            else:
                raise ValueError(f"unsupported state operation: {assignment.operation}")
        return StateSnapshot.from_mapping(values)


@dataclass(frozen=True, order=True)
class StateAssignment:
    state: str
    operation: StateOperation
    value: int


@dataclass(frozen=True, order=True)
class EventDefinition:
    id: str
    name: str


@dataclass(frozen=True, order=True)
class EventEmission:
    event: str
    facts: tuple[Fact, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "facts", tuple(sorted(_as_tuple(self.facts))))


@dataclass(frozen=True, order=True)
class EventRecord:
    id: str
    event: str
    directive: str
    principal: str
    facts: tuple[Fact, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "facts", tuple(sorted(_as_tuple(self.facts))))


@dataclass(frozen=True, order=True)
class EffectIntent:
    id: str
    effect_type: str
    facts: tuple[Fact, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "facts", tuple(sorted(_as_tuple(self.facts))))


@dataclass(frozen=True, order=True)
class CausalPath:
    id: str
    weight: int
    assignments: tuple[StateAssignment, ...] = ()
    emits: tuple[EventEmission, ...] = ()
    effects: tuple[EffectIntent, ...] = ()
    rationale: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "assignments", _as_tuple(self.assignments))
        object.__setattr__(self, "emits", tuple(sorted(_as_tuple(self.emits))))
        object.__setattr__(self, "effects", tuple(sorted(_as_tuple(self.effects))))


@dataclass(frozen=True, order=True)
class CausalDecision:
    id: str
    cause: str
    paths: tuple[CausalPath, ...]
    policy: DecisionPolicy = "max_weight"

    def __post_init__(self) -> None:
        object.__setattr__(self, "paths", tuple(sorted(_as_tuple(self.paths), key=lambda path: path.id)))


@dataclass(frozen=True, order=True)
class AIRDirective:
    id: str
    name: str
    principal: str
    authority_checks: tuple[str, ...]
    causal_decisions: tuple[str, ...]
    order: int = 0

    def __post_init__(self) -> None:
        object.__setattr__(self, "authority_checks", tuple(sorted(_as_tuple(self.authority_checks))))
        object.__setattr__(self, "causal_decisions", tuple(sorted(_as_tuple(self.causal_decisions))))


@dataclass(frozen=True)
class AIRProgram:
    version: str
    principals: tuple[Principal, ...]
    states: tuple[StateDefinition, ...]
    events: tuple[EventDefinition, ...]
    authority_checks: tuple[AuthorityCheck, ...]
    causal_decisions: tuple[CausalDecision, ...]
    directives: tuple[AIRDirective, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "principals", tuple(sorted(_as_tuple(self.principals))))
        object.__setattr__(self, "states", tuple(sorted(_as_tuple(self.states))))
        object.__setattr__(self, "events", tuple(sorted(_as_tuple(self.events))))
        object.__setattr__(self, "authority_checks", tuple(sorted(_as_tuple(self.authority_checks))))
        object.__setattr__(self, "causal_decisions", tuple(sorted(_as_tuple(self.causal_decisions))))
        directives = tuple(sorted(_as_tuple(self.directives), key=lambda directive: (directive.order, directive.id)))
        object.__setattr__(self, "directives", directives)


@dataclass(frozen=True)
class VerifiedAIRProgram:
    program: AIRProgram


@dataclass(frozen=True)
class VerificationResult:
    program: AIRProgram
    diagnostics: tuple[Diagnostic, ...]

    @property
    def ok(self) -> bool:
        return not any(diagnostic.is_error for diagnostic in self.diagnostics)

    def require_verified(self) -> VerifiedAIRProgram:
        if not self.ok:
            rendered = "\n".join(f"{d.code}: {d.message}" for d in self.diagnostics)
            raise ValueError(f"AIR verification failed:\n{rendered}")
        return VerifiedAIRProgram(self.program)


@dataclass(frozen=True)
class ExecutionContext:
    state: StateSnapshot
    grants: tuple[AuthorityGrant, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "grants", tuple(sorted(_as_tuple(self.grants))))


@dataclass(frozen=True)
class StateDelta:
    assignments: tuple[StateAssignment, ...] = ()
    events: tuple[EventRecord, ...] = ()
    effects: tuple[EffectIntent, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "assignments", _as_tuple(self.assignments))
        object.__setattr__(self, "events", _as_tuple(self.events))
        object.__setattr__(self, "effects", _as_tuple(self.effects))

    @property
    def is_empty(self) -> bool:
        return not self.assignments and not self.events and not self.effects


@dataclass(frozen=True)
class ExecutionResult:
    delta: StateDelta
    trace: Trace
    diagnostics: tuple[Diagnostic, ...]
    final_state: StateSnapshot

    @property
    def ok(self) -> bool:
        return not any(diagnostic.is_error for diagnostic in self.diagnostics)


class AIRVerifier:
    def verify(self, program: AIRProgram) -> VerificationResult:
        diagnostics: list[Diagnostic] = []

        if program.version != AIR_VERSION:
            _append(diagnostics, "error", "AIR001", f"unsupported AIR version: {program.version}")

        self._check_unique("principal", program.principals, diagnostics)
        self._check_unique("state", program.states, diagnostics)
        self._check_unique("event", program.events, diagnostics)
        self._check_unique("authority_check", program.authority_checks, diagnostics)
        self._check_unique("causal_decision", program.causal_decisions, diagnostics)
        self._check_unique("directive", program.directives, diagnostics)

        principals = set(_index_by_id(program.principals))
        states = set(_index_by_id(program.states))
        events = set(_index_by_id(program.events))
        checks = set(_index_by_id(program.authority_checks))
        decisions = set(_index_by_id(program.causal_decisions))

        for state in program.states:
            if not _is_int(state.initial):
                _append(diagnostics, "error", "AIR010", "state initial value must be an int", state.id)

        for check in program.authority_checks:
            if check.principal not in principals:
                _append(diagnostics, "error", "AIR020", f"authority principal does not exist: {check.principal}", check.id)

        for decision in program.causal_decisions:
            if decision.policy != "max_weight":
                _append(diagnostics, "error", "AIR030", f"unsupported causal policy: {decision.policy}", decision.id)
            if not decision.paths:
                _append(diagnostics, "error", "AIR031", "causal decision must have at least one path", decision.id)
            for path in decision.paths:
                if not _is_int(path.weight):
                    _append(diagnostics, "error", "AIR032", "causal path weight must be an int", path.id)
                for assignment in path.assignments:
                    if assignment.state not in states:
                        _append(diagnostics, "error", "AIR033", f"assignment state does not exist: {assignment.state}", path.id)
                    if assignment.operation not in ("set_int", "add_int"):
                        _append(diagnostics, "error", "AIR034", f"unsupported state operation: {assignment.operation}", path.id)
                    if not _is_int(assignment.value):
                        _append(diagnostics, "error", "AIR035", "assignment value must be an int", path.id)
                for emission in path.emits:
                    if emission.event not in events:
                        _append(diagnostics, "error", "AIR036", f"event does not exist: {emission.event}", path.id)

        for directive in program.directives:
            if directive.principal not in principals:
                _append(diagnostics, "error", "AIR040", f"directive principal does not exist: {directive.principal}", directive.id)
            if not _is_int(directive.order):
                _append(diagnostics, "error", "AIR041", "directive order must be an int", directive.id)
            for check_id in directive.authority_checks:
                if check_id not in checks:
                    _append(diagnostics, "error", "AIR042", f"authority check does not exist: {check_id}", directive.id)
                    continue
                check = _index_by_id(program.authority_checks)[check_id]
                if check.principal != directive.principal:  # type: ignore[attr-defined]
                    _append(
                        diagnostics,
                        "error",
                        "AIR043",
                        "authority check principal must match directive principal",
                        directive.id,
                    )
            for decision_id in directive.causal_decisions:
                if decision_id not in decisions:
                    _append(diagnostics, "error", "AIR044", f"causal decision does not exist: {decision_id}", directive.id)

        return VerificationResult(program, tuple(sorted(diagnostics)))

    @staticmethod
    def _check_unique(label: str, items: tuple, diagnostics: list[Diagnostic]) -> None:
        seen: set[str] = set()
        for item in items:
            if item.id in seen:
                _append(diagnostics, "error", "AIR000", f"duplicate {label} id: {item.id}", item.id)
            seen.add(item.id)


class AuthorityEngine:
    def __init__(self, grants: tuple[AuthorityGrant, ...]) -> None:
        self._grants = {(grant.principal, grant.capability, grant.resource) for grant in grants}

    def allows(self, check: AuthorityCheck) -> bool:
        return (check.principal, check.capability, check.resource) in self._grants


class CausalEngine:
    def select_path(self, decision: CausalDecision) -> tuple[CausalPath, tuple[TraceStep, ...]]:
        if decision.policy != "max_weight":
            raise ValueError(f"unsupported causal policy: {decision.policy}")

        ordered_paths = tuple(sorted(decision.paths, key=lambda path: (-path.weight, path.id)))
        selected = ordered_paths[0]
        facts: list[Fact] = [Fact("cause", decision.cause), Fact("selected", selected.id), Fact("weight", selected.weight)]
        for path in sorted(decision.paths, key=lambda item: item.id):
            facts.append(Fact(f"path.{path.id}.weight", path.weight))
        trace = (
            TraceStep("causal.evaluate", "evaluated weighted paths", tuple(facts)),
            TraceStep("causal.select", "selected deterministic causal path", _facts(path=selected.id, weight=selected.weight)),
        )
        return selected, trace


class RuntimeEngine:
    def execute(self, verified: VerifiedAIRProgram, context: ExecutionContext) -> ExecutionResult:
        program = verified.program
        diagnostics: list[Diagnostic] = []
        trace_steps: list[TraceStep] = []
        assignments: list[StateAssignment] = []
        events: list[EventRecord] = []
        effects: list[EffectIntent] = []

        checks = _index_by_id(program.authority_checks)
        decisions = _index_by_id(program.causal_decisions)
        authority = AuthorityEngine(context.grants)
        causality = CausalEngine()
        working_state = context.state

        trace_steps.append(TraceStep("runtime.start", "started AIR execution", _facts(version=program.version)))

        for directive in program.directives:
            trace_steps.append(
                TraceStep(
                    "directive.start",
                    "entered directive",
                    _facts(directive=directive.id, name=directive.name, principal=directive.principal),
                )
            )

            denied = False
            for check_id in directive.authority_checks:
                check = checks[check_id]
                allowed = authority.allows(check)  # type: ignore[arg-type]
                trace_steps.append(
                    TraceStep(
                        "authority.check",
                        "evaluated authority check",
                        _facts(
                            allowed=allowed,
                            capability=check.capability,  # type: ignore[attr-defined]
                            check=check.id,  # type: ignore[attr-defined]
                            principal=check.principal,  # type: ignore[attr-defined]
                            resource=check.resource,  # type: ignore[attr-defined]
                        ),
                    )
                )
                if not allowed:
                    denied = True
                    _append(
                        diagnostics,
                        "error",
                        "RUN001",
                        f"authority denied: {check.principal} lacks {check.capability} on {check.resource}",  # type: ignore[attr-defined]
                        directive.id,
                    )

            if denied:
                trace_steps.append(TraceStep("directive.skip", "skipped directive after authority denial", _facts(directive=directive.id)))
                continue

            for decision_id in directive.causal_decisions:
                decision = decisions[decision_id]
                selected, decision_trace = causality.select_path(decision)  # type: ignore[arg-type]
                trace_steps.extend(decision_trace)

                path_delta = StateDelta(selected.assignments)
                working_state = working_state.apply(path_delta)
                assignments.extend(selected.assignments)
                trace_steps.append(
                    TraceStep(
                        "state.delta",
                        "queued selected path assignments",
                        _facts(assignments=len(selected.assignments), path=selected.id),
                    )
                )

                for index, emission in enumerate(selected.emits):
                    event = EventRecord(
                        id=f"{directive.id}:{decision.id}:{selected.id}:event:{index}:{emission.event}",
                        event=emission.event,
                        directive=directive.id,
                        principal=directive.principal,
                        facts=emission.facts,
                    )
                    events.append(event)
                    trace_steps.append(
                        TraceStep(
                            "event.emit",
                            "queued event emission",
                            _facts(event=event.event, event_id=event.id),
                        )
                    )

                effects.extend(selected.effects)
                for effect in selected.effects:
                    trace_steps.append(
                        TraceStep(
                            "effect.intent",
                            "queued host effect intent without executing it",
                            _facts(effect=effect.id, effect_type=effect.effect_type),
                        )
                    )

        delta = StateDelta(tuple(assignments), tuple(events), tuple(effects))
        trace_steps.append(TraceStep("runtime.finish", "finished AIR execution", _facts(events=len(events), updates=len(assignments))))
        return ExecutionResult(delta, Trace(tuple(trace_steps)), tuple(sorted(diagnostics)), working_state)


def build_gravitas_program() -> AIRProgram:
    """Hand-authored AIR for: directive Gravitas, identity Sentinel, state Vigilance, cause Response."""
    return AIRProgram(
        version=AIR_VERSION,
        principals=(
            Principal(id="principal:Sentinel", display_name="Sentinel"),
        ),
        states=(
            StateDefinition(id="state:Vigilance", initial=10),
        ),
        events=(
            EventDefinition(id="event:Response", name="Response"),
        ),
        authority_checks=(
            AuthorityCheck(
                id="auth:Sentinel:Gravitas",
                principal="principal:Sentinel",
                capability="directive.invoke:Gravitas",
                resource="state:Vigilance",
            ),
        ),
        causal_decisions=(
            CausalDecision(
                id="cause:Response",
                cause="Response",
                paths=(
                    CausalPath(
                        id="path:Observe",
                        weight=30,
                        assignments=(StateAssignment("state:Vigilance", "add_int", 1),),
                        emits=(EventEmission("event:Response", _facts(path="Observe")),),
                        rationale="Low-pressure observation.",
                    ),
                    CausalPath(
                        id="path:Escalate",
                        weight=70,
                        assignments=(StateAssignment("state:Vigilance", "add_int", 5),),
                        emits=(EventEmission("event:Response", _facts(path="Escalate")),),
                        rationale="Highest-weight response path.",
                    ),
                    CausalPath(
                        id="path:Hold",
                        weight=40,
                        assignments=(StateAssignment("state:Vigilance", "add_int", 2),),
                        emits=(EventEmission("event:Response", _facts(path="Hold")),),
                        rationale="Moderate response path.",
                    ),
                ),
            ),
        ),
        directives=(
            AIRDirective(
                id="directive:Gravitas",
                name="Gravitas",
                principal="principal:Sentinel",
                authority_checks=("auth:Sentinel:Gravitas",),
                causal_decisions=("cause:Response",),
                order=0,
            ),
        ),
    )


def build_gravitas_context(program: AIRProgram) -> ExecutionContext:
    return ExecutionContext(
        state=StateSnapshot.from_program_initials(program),
        grants=(
            AuthorityGrant(
                principal="principal:Sentinel",
                capability="directive.invoke:Gravitas",
                resource="state:Vigilance",
            ),
        ),
    )


def run_gravitas_demo() -> ExecutionResult:
    program = build_gravitas_program()
    verified = AIRVerifier().verify(program).require_verified()
    context = build_gravitas_context(program)
    return RuntimeEngine().execute(verified, context)


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run_self_tests() -> None:
    verifier = AIRVerifier()

    program = build_gravitas_program()
    verification = verifier.verify(program)
    _assert(verification.ok, f"valid Gravitas AIR should verify: {verification.diagnostics}")

    result = RuntimeEngine().execute(verification.require_verified(), build_gravitas_context(program))
    _assert(result.ok, f"Gravitas execution should succeed: {result.diagnostics}")
    _assert(result.final_state.get_int("state:Vigilance") == 15, "highest causal path should add 5 to Vigilance")
    _assert(result.delta.events[0].id == "directive:Gravitas:cause:Response:path:Escalate:event:0:event:Response", "event ID must be deterministic")

    denied_context = ExecutionContext(state=StateSnapshot.from_program_initials(program), grants=())
    denied = RuntimeEngine().execute(verification.require_verified(), denied_context)
    _assert(not denied.ok, "denied authority should return an error diagnostic")
    _assert(denied.delta.is_empty, "denied authority should produce no state delta")

    tied = CausalDecision(
        id="cause:Tie",
        cause="Tie",
        paths=(
            CausalPath("path:B", 5, (StateAssignment("state:Vigilance", "add_int", 99),)),
            CausalPath("path:A", 5, (StateAssignment("state:Vigilance", "add_int", 1),)),
        ),
    )
    selected, _ = CausalEngine().select_path(tied)
    _assert(selected.id == "path:A", "equal weights must tie-break by stable path ID")

    original_state = StateSnapshot.from_program_initials(program)
    _ = original_state.apply(result.delta)
    _assert(original_state.get_int("state:Vigilance") == 10, "StateSnapshot must not be mutated by delta application")

    invalid = AIRProgram(
        version=AIR_VERSION,
        principals=(Principal("principal:Sentinel"),),
        states=(StateDefinition("state:Vigilance"),),
        events=(),
        authority_checks=(),
        causal_decisions=(
            CausalDecision(
                id="cause:Broken",
                cause="Broken",
                paths=(CausalPath("path:Broken", 1, (StateAssignment("state:Missing", "add_int", 1),)),),
            ),
        ),
        directives=(
            AIRDirective("directive:Broken", "Broken", "principal:Sentinel", (), ("cause:Broken",)),
        ),
    )
    invalid_result = verifier.verify(invalid)
    _assert(not invalid_result.ok, "verifier should reject missing state references")


if __name__ == "__main__":
    run_self_tests()
    demo = run_gravitas_demo()
    print("ApexForge AIR v0.1 self-tests passed.")
    print(f"Vigilance: {demo.final_state.get_int('state:Vigilance')}")
    print(demo.trace.render())

"""ApexForge AIR v0.2 runnable entrypoint.

This file stays intentionally thin. AIR, verification, authority, causality,
runtime state lives in modules under apexforge/.
"""

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

def main() -> None:
    demo = run_gravitas_demo()
    print("ApexForge AIR v0.2 self-tests passed.")
    print(f"Vigilance: {demo.final_state.get_int('state:Vigilance')}")
    print(demo.trace.render())


if __name__ == "__main__":
    main()

