# apexforge_runtime.py
# ApexForge v0.1 — Foundation Runtime

from dataclasses import dataclass, field
from typing import List, Dict, Callable, Optional


AUTHORITY_LEVELS = {
    "minimal": 1,
    "standard": 2,
    "elevated": 3,
    "root": 4,
    "sovereign": 5
}


@dataclass
class Directive:
    name: str
    rules: List[str] = field(default_factory=list)
    enforced: bool = False

    def enforce(self):
        self.enforced = True


@dataclass
class Identity:
    name: str
    role: str
    authority: str
    traits: List[str] = field(default_factory=list)

    def authority_value(self) -> int:
        return AUTHORITY_LEVELS.get(self.authority, 0)


@dataclass
class State:
    name: str
    enters: str
    exits: str
    actions: List[str] = field(default_factory=list)
    active: bool = False


@dataclass
class CausePath:
    label: str
    condition: str
    weight: int
    action: str


@dataclass
class Cause:
    name: str
    input_event: str
    paths: List[CausePath] = field(default_factory=list)

    def resolve(self) -> CausePath:
        if not self.paths:
            raise ValueError(f"Cause '{self.name}' has no paths.")

        return max(self.paths, key=lambda path: path.weight)


class ApexForgeRuntime:
    def __init__(self):
        self.directives: Dict[str, Directive] = {}
        self.identities: Dict[str, Identity] = {}
        self.states: Dict[str, State] = {}
        self.causes: Dict[str, Cause] = {}
        self.event_log: List[str] = []

    def add_directive(self, directive: Directive):
        self.directives[directive.name] = directive

    def add_identity(self, identity: Identity):
        self.identities[identity.name] = identity

    def add_state(self, state: State):
        self.states[state.name] = state

    def add_cause(self, cause: Cause):
        self.causes[cause.name] = cause

    def emit(self, event: str):
        self.event_log.append(event)

        for state in self.states.values():
            if state.enters == event:
                state.active = True

            if state.exits == event:
                state.active = False

    def enforced_directives(self):
        return [d for d in self.directives.values() if d.enforced]

    def resolve_cause(self, name: str) -> Optional[CausePath]:
        cause = self.causes.get(name)
        if not cause:
            return None

        return cause.resolve()

    def status(self):
        return {
            "directives": self.directives,
            "identities": self.identities,
            "states": self.states,
            "causes": self.causes,
            "events": self.event_log
        }


# Demo Program: Identity Engine Seed

if __name__ == "__main__":
    runtime = ApexForgeRuntime()

    gravitas = Directive(
        name="Gravitas",
        rules=[
            "prioritize(weight.highest)",
            "reject(inconsistency)"
        ]
    )
    gravitas.enforce()
    runtime.add_directive(gravitas)

    sentinel = Identity(
        name="Sentinel",
        role="Guardian",
        authority="elevated",
        traits=["stable", "observant", "incorruptible"]
    )
    runtime.add_identity(sentinel)

    vigilance = State(
        name="Vigilance",
        enters="threat.detected",
        exits="threat.resolved",
        actions=["escalate(awareness)"]
    )
    runtime.add_state(vigilance)

    response = Cause(
        name="Response",
        input_event="intrusion.event",
        paths=[
            CausePath("A", "system.secure", 9, "secure_system"),
            CausePath("B", "isolate.node", 5, "isolate_node"),
            CausePath("C", "observe.silently", 2, "observe")
        ]
    )
    runtime.add_cause(response)

    runtime.emit("threat.detected")

    result = runtime.resolve_cause("Response")

    print("APEXFORGE v0.1 — RUNTIME ACTIVE")
    print("--------------------------------")
    print("Enforced Directives:", [d.name for d in runtime.enforced_directives()])
    print("Active States:", [s.name for s in runtime.states.values() if s.active])
    print("Resolved Cause:", result.label, result.action, "weight =", result.weight)

    # apexforge_runtime.py
# ApexForge v0.1 — Foundation Runtime

from dataclasses import dataclass, field
from typing import List, Dict, Callable, Optional


AUTHORITY_LEVELS = {
    "minimal": 1,
    "standard": 2,
    "elevated": 3,
    "root": 4,
    "sovereign": 5
}


@dataclass
class Directive:
    name: str
    rules: List[str] = field(default_factory=list)
    enforced: bool = False

    def enforce(self):
        self.enforced = True


@dataclass
class Identity:
    name: str
    role: str
    authority: str
    traits: List[str] = field(default_factory=list)

    def authority_value(self) -> int:
        return AUTHORITY_LEVELS.get(self.authority, 0)


@dataclass
class State:
    name: str
    enters: str
    exits: str
    actions: List[str] = field(default_factory=list)
    active: bool = False


@dataclass
class CausePath:
    label: str
    condition: str
    weight: int
    action: str


@dataclass
class Cause:
    name: str
    input_event: str
    paths: List[CausePath] = field(default_factory=list)

    def resolve(self) -> CausePath:
        if not self.paths:
            raise ValueError(f"Cause '{self.name}' has no paths.")

        return max(self.paths, key=lambda path: path.weight)


class ApexForgeRuntime:
    def __init__(self):
        self.directives: Dict[str, Directive] = {}
        self.identities: Dict[str, Identity] = {}
        self.states: Dict[str, State] = {}
        self.causes: Dict[str, Cause] = {}
        self.event_log: List[str] = []

    def add_directive(self, directive: Directive):
        self.directives[directive.name] = directive

    def add_identity(self, identity: Identity):
        self.identities[identity.name] = identity

    def add_state(self, state: State):
        self.states[state.name] = state

    def add_cause(self, cause: Cause):
        self.causes[cause.name] = cause

    def emit(self, event: str):
        self.event_log.append(event)

        for state in self.states.values():
            if state.enters == event:
                state.active = True

            if state.exits == event:
                state.active = False

    def enforced_directives(self):
        return [d for d in self.directives.values() if d.enforced]

    def resolve_cause(self, name: str) -> Optional[CausePath]:
        cause = self.causes.get(name)
        if not cause:
            return None

        return cause.resolve()

    def status(self):
        return {
            "directives": self.directives,
            "identities": self.identities,
            "states": self.states,
            "causes": self.causes,
            "events": self.event_log
        }


# Demo Program: Identity Engine Seed

if __name__ == "__main__":
    runtime = ApexForgeRuntime()

    gravitas = Directive(
        name="Gravitas",
        rules=[
            "prioritize(weight.highest)",
            "reject(inconsistency)"
        ]
    )
    gravitas.enforce()
    runtime.add_directive(gravitas)

    sentinel = Identity(
        name="Sentinel",
        role="Guardian",
        authority="elevated",
        traits=["stable", "observant", "incorruptible"]
    )
    runtime.add_identity(sentinel)

    vigilance = State(
        name="Vigilance",
        enters="threat.detected",
        exits="threat.resolved",
        actions=["escalate(awareness)"]
    )
    runtime.add_state(vigilance)

    response = Cause(
        name="Response",
        input_event="intrusion.event",
        paths=[
            CausePath("A", "system.secure", 9, "secure_system"),
            CausePath("B", "isolate.node", 5, "isolate_node"),
            CausePath("C", "observe.silently", 2, "observe")
        ]
    )
    runtime.add_cause(response)

    runtime.emit("threat.detected")

    result = runtime.resolve_cause("Response")

    print("APEXFORGE v0.1 — RUNTIME ACTIVE")
    print("--------------------------------")
    print("Enforced Directives:", [d.name for d in runtime.enforced_directives()])
    print("Active States:", [s.name for s in runtime.states.values() if s.active])
    print("Resolved Cause:", result.label, result.action, "weight =", result.weight)

   