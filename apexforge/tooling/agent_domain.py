"""Passive agent-domain records and explicit immutable ledger append operations."""
from dataclasses import dataclass
import re

from agents.model import AgentIdentity, AgentDefinition
from tooling import domain_platform as sdk
from tooling.package_manifest import PackageManifest, ExactVersion, CanonicalReference

PLATFORM = sdk.DomainPlatformIdentity("apexforge.agent", "agent")
OPERATIONS = ("agent.descriptor.describe", "agent.session.describe")
MAX_EVENTS = 4096


class AgentDomainError(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def require(condition, code):
    if not condition:
        raise AgentDomainError(code)


def name(value, code="AGENT_REFERENCE_INVALID"):
    try:
        sdk._name(value, code)
    except sdk.DomainContractError as error:
        raise AgentDomainError(code) from error


def digest(value):
    require(type(value) is str and re.fullmatch(r"[0-9A-F]{64}", value) is not None,
        "AGENT_FINGERPRINT_INVALID")


def refs(owner, field="provenance"):
    try:
        sdk._refs(owner, field, CanonicalReference, "AGENT_REFERENCE_INVALID")
    except sdk.DomainContractError as error:
        raise AgentDomainError("AGENT_REFERENCE_INVALID") from error


def names(values):
    require(type(values) is tuple and all(type(v) is str for v in values), "AGENT_DECLARATION_INVALID")
    require(len(set(values)) == len(values), "AGENT_DECLARATION_INVALID")
    for value in values:
        name(value, "AGENT_DECLARATION_INVALID")
    return tuple(sorted(values))


def agent_platform(manifest):
    require(type(manifest) is PackageManifest, "AGENT_PACKAGE_INVALID")
    return sdk.DomainPlatformDescriptor(PLATFORM, sdk.ImplementationPackage.from_manifest(manifest),
        ExactVersion(1, 0, 0), OPERATIONS, (sdk.DomainCapability("agent.describe"),), provenance=manifest.provenance)


@dataclass(frozen=True)
class ActionCapabilityRequirement(sdk.CanonicalModel):
    identifier: str
    DOMAIN = "apexforge.agent.action-capability-requirement/v1"

    def __post_init__(self):
        name(self.identifier, "AGENT_CAPABILITY_INVALID")

    def record(self):
        return {"schema": self.DOMAIN, "id": self.identifier, "grants_authority": False}


@dataclass(frozen=True)
class AgentDescriptor(sdk.CanonicalModel):
    definition: AgentDefinition
    platform: sdk.DomainPlatformDescriptor
    actions: tuple
    observations: tuple
    requirements: tuple = ()
    provenance: tuple = ()
    contract_version: ExactVersion = ExactVersion(1, 0, 0)
    DOMAIN = "apexforge.agent.descriptor/v1"

    def __post_init__(self):
        require(type(self.definition) is AgentDefinition, "AGENT_IDENTITY_INVALID")
        require(type(self.platform) is sdk.DomainPlatformDescriptor and self.platform.identity == PLATFORM and
            self.platform.contract_version == ExactVersion(1, 0, 0) and
            self.platform.operations == tuple(sorted(OPERATIONS)) and not self.platform.dependencies and
            self.platform.capabilities == (sdk.DomainCapability("agent.describe"),), "AGENT_PLATFORM_INVALID")
        require(type(self.contract_version) is ExactVersion and self.contract_version == ExactVersion(1, 0, 0), "AGENT_SCHEMA_UNSUPPORTED")
        object.__setattr__(self, "actions", names(self.actions))
        object.__setattr__(self, "observations", names(self.observations))
        require(type(self.requirements) is tuple and all(type(c) is sdk.DomainCapability for c in self.requirements),
            "AGENT_CAPABILITY_INVALID")
        require(len(set(self.requirements)) == len(self.requirements), "AGENT_CAPABILITY_DUPLICATE")
        object.__setattr__(self, "requirements", tuple(sorted(self.requirements, key=lambda c: c.identifier)))
        refs(self)

    @property
    def identity(self):
        return self.definition.identity

    def record(self):
        return {"schema": self.DOMAIN, "agent": {"canonical_id": self.identity.canonical_id},
            "archetype_ids": list(self.definition.archetype_ids), "platform": self.platform.record(),
            "platform_fingerprint": self.platform.fingerprint(), "contract_version": self.contract_version.text(),
            "actions": list(self.actions), "observation_kinds": list(self.observations),
            "required_domain_capabilities": [c.record() for c in self.requirements],
            "provenance": [p.record() for p in self.provenance], "grants_authority": False}


@dataclass(frozen=True)
class AgentSessionIdentity(sdk.CanonicalModel):
    identifier: str
    DOMAIN = "apexforge.agent.session-identity/v1"

    def __post_init__(self):
        name(self.identifier, "AGENT_SESSION_ID_INVALID")

    def record(self):
        return {"schema": self.DOMAIN, "id": self.identifier}


@dataclass(frozen=True)
class AgentContext(sdk.CanonicalModel):
    session: AgentSessionIdentity
    descriptor: AgentDescriptor
    DOMAIN = "apexforge.agent.context/v1"

    def __post_init__(self):
        require(type(self.session) is AgentSessionIdentity and type(self.descriptor) is AgentDescriptor,
            "AGENT_CONTEXT_INVALID")

    def record(self):
        return {"schema": self.DOMAIN, "session": self.session.record(),
            "agent": {"canonical_id": self.descriptor.identity.canonical_id},
            "descriptor_fingerprint": self.descriptor.fingerprint(),
            "implementation": self.descriptor.platform.implementation.record()}


@dataclass(frozen=True)
class AgentTask(sdk.CanonicalModel):
    identifier: str
    objective: str
    inputs: tuple = ()
    provenance: tuple = ()
    DOMAIN = "apexforge.agent.task/v1"

    def __post_init__(self):
        name(self.identifier, "AGENT_TASK_ID_INVALID")
        require(type(self.objective) is str and 0 < len(self.objective) <= 4096 and self.objective.strip(),
            "AGENT_TASK_OBJECTIVE_INVALID")
        refs(self, "inputs")
        refs(self)

    def record(self):
        return {"schema": self.DOMAIN, "id": self.identifier, "objective": self.objective,
            "inputs": [r.record() for r in self.inputs], "provenance": [r.record() for r in self.provenance],
            "grants_authority": False, "execution": "NOT_PERFORMED"}


@dataclass(frozen=True)
class AgentObservation(sdk.CanonicalModel):
    identifier: str
    context: AgentContext
    kind: str
    evidence: tuple = ()
    provenance: tuple = ()
    DOMAIN = "apexforge.agent.observation/v1"

    def __post_init__(self):
        name(self.identifier)
        require(type(self.context) is AgentContext, "AGENT_CONTEXT_INVALID")
        require(type(self.kind) is str and self.kind in self.context.descriptor.observations,
            "AGENT_OBSERVATION_KIND_UNDECLARED")
        refs(self, "evidence")
        refs(self)

    def record(self):
        return {"schema": self.DOMAIN, "id": self.identifier, "context": self.context.record(),
            "kind": self.kind, "evidence": [r.record() for r in self.evidence],
            "provenance": [r.record() for r in self.provenance], "origin": "CALLER_SUPPLIED",
            "verified_fact": False}


@dataclass(frozen=True)
class AgentDecision(sdk.CanonicalModel):
    identifier: str
    context: AgentContext
    observations: tuple
    alternatives: tuple
    selected: str | None = None
    provenance: tuple = ()
    DOMAIN = "apexforge.agent.decision/v1"

    def __post_init__(self):
        name(self.identifier)
        require(type(self.context) is AgentContext, "AGENT_CONTEXT_INVALID")
        require(type(self.observations) is tuple and all(type(v) is str for v in self.observations) and
            len(set(self.observations)) == len(self.observations),
            "AGENT_DECISION_REFERENCE_INVALID")
        for value in self.observations:
            digest(value)
        object.__setattr__(self, "observations", tuple(sorted(self.observations)))
        object.__setattr__(self, "alternatives", names(self.alternatives))
        require(bool(self.alternatives) and (self.selected is None or self.selected in self.alternatives),
            "AGENT_DECISION_SELECTION_INVALID")
        refs(self)

    def record(self):
        return {"schema": self.DOMAIN, "id": self.identifier, "context": self.context.record(),
            "observations": list(self.observations), "alternatives": list(self.alternatives),
            "selected": self.selected, "selection_origin": "CALLER_SUPPLIED", "private_reasoning_captured": False,
            "provenance": [r.record() for r in self.provenance]}


@dataclass(frozen=True)
class AgentActionIntent(sdk.CanonicalModel):
    identifier: str
    context: AgentContext
    action: str
    target: CanonicalReference
    requirement: ActionCapabilityRequirement
    arguments: tuple = ()
    tool: CanonicalReference | None = None
    decision_fingerprint: str | None = None
    provenance: tuple = ()
    DOMAIN = "apexforge.agent.action-intent/v1"

    def __post_init__(self):
        name(self.identifier)
        require(type(self.context) is AgentContext, "AGENT_CONTEXT_INVALID")
        require(type(self.action) is str and self.action in self.context.descriptor.actions, "AGENT_ACTION_UNDECLARED")
        require(type(self.target) is CanonicalReference and type(self.requirement) is ActionCapabilityRequirement,
            "AGENT_ACTION_REQUIREMENT_INVALID")
        require(self.tool is None or type(self.tool) is CanonicalReference, "AGENT_TOOL_REFERENCE_INVALID")
        if self.decision_fingerprint is not None:
            digest(self.decision_fingerprint)
        refs(self, "arguments")
        refs(self)

    def record(self):
        return {"schema": self.DOMAIN, "id": self.identifier, "context": self.context.record(),
            "action": self.action, "target": self.target.record(), "requirement": self.requirement.record(),
            "arguments": [r.record() for r in self.arguments], "tool": None if self.tool is None else self.tool.record(),
            "decision_fingerprint": self.decision_fingerprint, "provenance": [r.record() for r in self.provenance],
            "execution": "NOT_PERFORMED", "grants_authority": False}


@dataclass(frozen=True)
class AgentActionReceipt(sdk.CanonicalModel):
    identifier: str
    context: AgentContext
    intent_fingerprint: str
    external_status: str
    outputs: tuple = ()
    provenance: tuple = ()
    DOMAIN = "apexforge.agent.action-receipt/v1"

    def __post_init__(self):
        name(self.identifier)
        require(type(self.context) is AgentContext, "AGENT_CONTEXT_INVALID")
        digest(self.intent_fingerprint)
        require(type(self.external_status) is str and self.external_status in ("SUCCEEDED", "FAILED", "UNKNOWN"),
            "AGENT_RECEIPT_STATUS_INVALID")
        refs(self, "outputs")
        refs(self)

    def record(self):
        return {"schema": self.DOMAIN, "id": self.identifier, "context": self.context.record(),
            "intent_fingerprint": self.intent_fingerprint, "external_status": self.external_status,
            "outputs": [r.record() for r in self.outputs], "provenance": [r.record() for r in self.provenance],
            "evidence_origin": "EXTERNALLY_SUPPLIED", "execution_verified": False, "grants_authority": False}


_EVENT_TYPES = (AgentObservation, AgentDecision, AgentActionIntent, AgentActionReceipt)


@dataclass(frozen=True)
class AgentSessionSnapshot(sdk.CanonicalModel):
    context: AgentContext
    task: AgentTask
    ledger: tuple = ()
    predecessor_fingerprint: str | None = None
    provenance: tuple = ()
    DOMAIN = "apexforge.agent.session/v1"

    def __post_init__(self):
        require(type(self.context) is AgentContext and type(self.task) is AgentTask, "AGENT_SESSION_INVALID")
        require(type(self.ledger) is tuple and len(self.ledger) <= MAX_EVENTS and
            all(type(event) in _EVENT_TYPES for event in self.ledger), "AGENT_LEDGER_INVALID")
        if self.predecessor_fingerprint is not None:
            digest(self.predecessor_fingerprint)
            require(bool(self.ledger), "AGENT_SESSION_LINEAGE_INVALID")
        ids, observations, decisions, intents = set(), set(), set(), set()
        for event in self.ledger:
            require(event.context == self.context, "AGENT_LEDGER_CONTEXT_MISMATCH")
            require(event.identifier not in ids, "AGENT_LEDGER_EVENT_DUPLICATE")
            ids.add(event.identifier)
            if type(event) is AgentObservation:
                observations.add(event.fingerprint())
            elif type(event) is AgentDecision:
                require(all(ref in observations for ref in event.observations), "AGENT_DECISION_OBSERVATION_MISSING")
                decisions.add(event.fingerprint())
            elif type(event) is AgentActionIntent:
                require(event.decision_fingerprint is None or event.decision_fingerprint in decisions,
                    "AGENT_INTENT_DECISION_MISSING")
                intents.add(event.fingerprint())
            else:
                require(event.intent_fingerprint in intents, "AGENT_RECEIPT_INTENT_MISSING")
        refs(self)

    def record(self):
        return {"schema": self.DOMAIN, "context": self.context.record(), "task": self.task.record(),
            "predecessor_fingerprint": self.predecessor_fingerprint,
            "ledger": [{"sequence": n, "event_fingerprint": event.fingerprint(), "event": event.record()}
                for n, event in enumerate(self.ledger, 1)], "provenance": [r.record() for r in self.provenance],
            "semantic_authority": "CANONICAL_AIR", "grants_authority": False, "execution": "NOT_PERFORMED"}


def append_event(snapshot, event):
    require(type(snapshot) is AgentSessionSnapshot and type(event) in _EVENT_TYPES, "AGENT_APPEND_INVALID")
    return AgentSessionSnapshot(snapshot.context, snapshot.task, snapshot.ledger + (event,),
        snapshot.fingerprint(), snapshot.provenance)


def agent_artifact(record, *, semantic_inputs=(), symbols=()):
    require(type(record) in (AgentDescriptor, AgentSessionSnapshot), "AGENT_ARTIFACT_INVALID")
    descriptor = record if type(record) is AgentDescriptor else record.context.descriptor
    return sdk.DomainArtifact.from_bytes(descriptor.platform,
        "agent.descriptor.describe" if type(record) is AgentDescriptor else "agent.session.describe", "model",
        sdk._json({"record": record.record(), "record_fingerprint": record.fingerprint()}).encode("utf-8"),
        semantic_inputs=semantic_inputs, symbols=symbols,
        provenance=record.provenance)
