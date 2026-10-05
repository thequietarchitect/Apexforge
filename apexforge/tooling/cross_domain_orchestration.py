"""Bounded caller-evidence orchestration plans. Validation never executes nodes."""
from dataclasses import dataclass
import heapq

from tooling import domain_platform as sdk
from tooling import domain_governance as gov
from tooling.package_manifest import CanonicalReference

MAX_ITEMS = 4096


class OrchestrationError(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def require(ok, code):
    if not ok:
        raise OrchestrationError(code)


def name(value):
    try:
        sdk._name(value, "ORCHESTRATION_ID_INVALID")
    except sdk.DomainContractError as error:
        raise OrchestrationError(error.code) from error


def records(owner, field, values, cls, code="ORCHESTRATION_MODEL_INVALID"):
    require(type(values) is tuple and len(values) <= MAX_ITEMS and
            all(type(v) is cls for v in values), code)
    keys = [sdk._json(v.record()) for v in values]
    require(len(set(keys)) == len(keys), code)
    object.__setattr__(owner, field, tuple(v for _, v in sorted(zip(keys, values), key=lambda p: p[0])))


def provenance(owner):
    records(owner, "provenance", owner.provenance, CanonicalReference)


@dataclass(frozen=True)
class OrchestrationPlanIdentity(sdk.CanonicalModel):
    identifier: str
    DOMAIN = "apexforge.orchestration-plan-identity/v1"

    def __post_init__(self):
        name(self.identifier)

    def record(self):
        return {"schema": self.DOMAIN, "id": self.identifier}


@dataclass(frozen=True)
class ArtifactContract(sdk.CanonicalModel):
    """Explicit structural declaration; schema references are claims, not byte inference."""
    kind: str
    schema_reference: CanonicalReference | None = None
    provenance: tuple = ()
    DOMAIN = "apexforge.orchestration-artifact-contract/v1"

    def __post_init__(self):
        require(type(self.kind) is str and self.kind in sdk.ARTIFACT_KINDS, "ORCHESTRATION_SLOT_INVALID")
        require(self.schema_reference is None or type(self.schema_reference) is CanonicalReference,
                "ORCHESTRATION_SLOT_INVALID")
        provenance(self)

    def record(self):
        return {"kind": self.kind, "schema_reference": None if self.schema_reference is None else
                self.schema_reference.record(), "provenance": [r.record() for r in self.provenance]}


@dataclass(frozen=True)
class InputSlot(sdk.CanonicalModel):
    identifier: str
    contract: ArtifactContract
    required: bool = True
    DOMAIN = "apexforge.orchestration-input-slot/v1"

    def __post_init__(self):
        name(self.identifier)
        require(type(self.contract) is ArtifactContract and type(self.required) is bool,
                "ORCHESTRATION_SLOT_INVALID")

    def record(self):
        return {"id": self.identifier, "contract": self.contract.record(), "required": self.required,
                "exclusive": True}


@dataclass(frozen=True)
class OutputSlot(sdk.CanonicalModel):
    identifier: str
    contract: ArtifactContract
    DOMAIN = "apexforge.orchestration-output-slot/v1"

    def __post_init__(self):
        name(self.identifier)
        require(type(self.contract) is ArtifactContract, "ORCHESTRATION_SLOT_INVALID")

    def record(self):
        return {"id": self.identifier, "contract": self.contract.record(), "evidence": "PLANNED_ONLY"}


@dataclass(frozen=True)
class OrchestrationNode(sdk.CanonicalModel):
    identifier: str
    registration: gov.DomainGovernanceDecision
    descriptor: sdk.DomainPlatformDescriptor
    operation: str
    inputs: tuple = ()
    outputs: tuple = ()
    capabilities: tuple = ()
    provenance: tuple = ()
    DOMAIN = "apexforge.orchestration-node/v1"

    def __post_init__(self):
        name(self.identifier)
        name(self.operation)
        require(type(self.registration) is gov.DomainGovernanceDecision and
                type(self.descriptor) is sdk.DomainPlatformDescriptor, "ORCHESTRATION_NODE_INVALID")
        records(self, "inputs", self.inputs, InputSlot, "ORCHESTRATION_SLOT_INVALID")
        records(self, "outputs", self.outputs, OutputSlot, "ORCHESTRATION_SLOT_INVALID")
        for slots in (self.inputs, self.outputs):
            require(len({s.identifier for s in slots}) == len(slots), "ORCHESTRATION_SLOT_INVALID")
        records(self, "capabilities", self.capabilities, sdk.DomainCapability)
        provenance(self)

    def record(self):
        return {"id": self.identifier, "registration": self.registration.candidate.fingerprint(),
                "decision": self.registration.fingerprint(), "platform": self.descriptor.identity.record(),
                "descriptor": self.descriptor.fingerprint(), "implementation": self.descriptor.implementation.record(),
                "operation": self.operation, "inputs": [s.record() for s in self.inputs],
                "outputs": [s.record() for s in self.outputs], "capabilities": [c.record() for c in self.capabilities],
                "provenance": [r.record() for r in self.provenance], "executes_operation": False}


@dataclass(frozen=True)
class SlotReference(sdk.CanonicalModel):
    node: str
    slot: str
    DOMAIN = "apexforge.orchestration-slot-reference/v1"

    def __post_init__(self):
        name(self.node)
        name(self.slot)

    def record(self):
        return {"node": self.node, "slot": self.slot}


@dataclass(frozen=True)
class ArtifactHandoff(sdk.CanonicalModel):
    identifier: str
    producer: SlotReference
    consumer: SlotReference
    contract: ArtifactContract
    provenance: tuple = ()
    DOMAIN = "apexforge.orchestration-handoff/v1"

    def __post_init__(self):
        name(self.identifier)
        require(type(self.producer) is SlotReference and type(self.consumer) is SlotReference and
                type(self.contract) is ArtifactContract, "ORCHESTRATION_HANDOFF_INVALID")
        provenance(self)

    def record(self):
        return {"id": self.identifier, "producer": self.producer.record(), "consumer": self.consumer.record(),
                "contract": self.contract.record(), "provenance": [r.record() for r in self.provenance],
                "artifact_exists": False, "origin": "PRODUCER_DOMAIN_RETAINED", "transfer_executed": False}


@dataclass(frozen=True)
class InitialInput(sdk.CanonicalModel):
    target: SlotReference
    artifact: sdk.DomainArtifact
    schema_reference: CanonicalReference | None = None
    DOMAIN = "apexforge.orchestration-initial-input/v1"

    def __post_init__(self):
        require(type(self.target) is SlotReference and type(self.artifact) is sdk.DomainArtifact and
                (self.schema_reference is None or type(self.schema_reference) is CanonicalReference),
                "ORCHESTRATION_INPUT_INVALID")

    def record(self):
        return {"target": self.target.record(), "artifact": self.artifact.record(),
                "schema_reference": None if self.schema_reference is None else self.schema_reference.record(),
                "origin": "CALLER_SUPPLIED_EVIDENCE", "bytes_verified": False}


@dataclass(frozen=True)
class CrossDomainOrchestrationPlan(sdk.CanonicalModel):
    identity: OrchestrationPlanIdentity
    catalog: gov.DomainCatalogSnapshot
    nodes: tuple
    handoffs: tuple = ()
    initial_inputs: tuple = ()
    terminal_outputs: tuple = ()
    provenance: tuple = ()
    DOMAIN = "apexforge.cross-domain-orchestration/v1"

    def __post_init__(self):
        require(type(self.identity) is OrchestrationPlanIdentity and type(self.catalog) is gov.DomainCatalogSnapshot,
                "ORCHESTRATION_PLAN_INVALID")
        records(self, "nodes", self.nodes, OrchestrationNode, "ORCHESTRATION_DUPLICATE_NODE")
        records(self, "handoffs", self.handoffs, ArtifactHandoff, "ORCHESTRATION_DUPLICATE_EDGE")
        records(self, "initial_inputs", self.initial_inputs, InitialInput, "ORCHESTRATION_INPUT_INVALID")
        records(self, "terminal_outputs", self.terminal_outputs, SlotReference, "ORCHESTRATION_OUTPUT_UNRESOLVED")
        provenance(self)
        require(len({n.identifier for n in self.nodes}) == len(self.nodes), "ORCHESTRATION_DUPLICATE_NODE")
        require(len({e.identifier for e in self.handoffs}) == len(self.handoffs), "ORCHESTRATION_DUPLICATE_EDGE")
        object.__setattr__(self, "nodes", tuple(sorted(self.nodes, key=lambda n: n.identifier)))
        object.__setattr__(self, "handoffs", tuple(sorted(self.handoffs, key=lambda e: e.identifier)))

    def record(self):
        return {"schema": self.DOMAIN, "identity": self.identity.record(), "catalog": self.catalog.fingerprint(),
                "policy": self.catalog.policy.fingerprint(), "nodes": [n.record() for n in self.nodes],
                "handoffs": [e.record() for e in self.handoffs], "initial_inputs": [i.record() for i in self.initial_inputs],
                "terminal_outputs": [s.record() for s in self.terminal_outputs],
                "provenance": [r.record() for r in self.provenance], "semantic_authority": "CANONICAL_AIR",
                "execution": "NOT_PERFORMED", "grants_authority": False, "grants_trust": False}


CODES = frozenset(("ORCHESTRATION_DOMAIN_NOT_GOVERNED", "ORCHESTRATION_DESCRIPTOR_MISMATCH",
    "ORCHESTRATION_PACKAGE_MISMATCH", "ORCHESTRATION_OPERATION_UNDECLARED", "ORCHESTRATION_INPUT_MISSING",
    "ORCHESTRATION_HANDOFF_DANGLING", "ORCHESTRATION_HANDOFF_INCOMPATIBLE", "ORCHESTRATION_INPUT_AMBIGUOUS",
    "ORCHESTRATION_CYCLE", "ORCHESTRATION_OUTPUT_UNRESOLVED", "ORCHESTRATION_CAPABILITY_UNDECLARED"))


@dataclass(frozen=True)
class OrchestrationFinding(sdk.CanonicalModel):
    code: str
    subject: str
    slot: str | None = None
    DOMAIN = "apexforge.orchestration-finding/v1"

    def __post_init__(self):
        require(type(self.code) is str and self.code in CODES, "ORCHESTRATION_DIAGNOSTIC_INVALID")
        name(self.subject)
        if self.slot is not None:
            name(self.slot)

    def record(self):
        return {"code": self.code, "subject": self.subject, "slot": self.slot}


@dataclass(frozen=True)
class OrchestrationValidation(sdk.CanonicalModel):
    """Derived structural assessment, never a successful-run receipt."""
    plan: CrossDomainOrchestrationPlan
    DOMAIN = "apexforge.orchestration-validation/v1"

    def __post_init__(self):
        require(type(self.plan) is CrossDomainOrchestrationPlan, "ORCHESTRATION_PLAN_INVALID")

    def _assessment(self):
        p = self.plan
        found = set()
        def finding(code, subject, slot=None):
            found.add(OrchestrationFinding(code, subject, slot))
        nodes = {n.identifier: n for n in p.nodes}
        inputs = {SlotReference(n.identifier, s.identifier): s for n in p.nodes for s in n.inputs}
        outputs = {SlotReference(n.identifier, s.identifier): s for n in p.nodes for s in n.outputs}
        entries = set(p.catalog.entries)
        for n in p.nodes:
            d = n.registration.candidate.descriptor
            if n.registration not in entries or n.registration.status != "ADMISSIBLE":
                finding("ORCHESTRATION_DOMAIN_NOT_GOVERNED", n.identifier)
            if n.descriptor != d:
                finding("ORCHESTRATION_DESCRIPTOR_MISMATCH", n.identifier)
            if n.descriptor.implementation != d.implementation:
                finding("ORCHESTRATION_PACKAGE_MISMATCH", n.identifier)
            if n.operation not in n.descriptor.operations or n.operation not in d.operations:
                finding("ORCHESTRATION_OPERATION_UNDECLARED", n.identifier)
            if not set(n.capabilities) <= set(d.capabilities):
                finding("ORCHESTRATION_CAPABILITY_UNDECLARED", n.identifier)
        supplied = {}
        adjacency = {n: set() for n in nodes}
        indegree = {n: 0 for n in nodes}
        def compatible(source, target):
            return source.kind == target.kind and (target.schema_reference is None or
                source.schema_reference == target.schema_reference) and set(target.provenance) <= set(source.provenance)
        for e in p.handoffs:
            supplied[e.consumer] = supplied.get(e.consumer, 0) + 1
            source, target = outputs.get(e.producer), inputs.get(e.consumer)
            if source is None or target is None:
                finding("ORCHESTRATION_HANDOFF_DANGLING", e.identifier)
            elif not compatible(source.contract, e.contract) or not compatible(e.contract, target.contract):
                finding("ORCHESTRATION_HANDOFF_INCOMPATIBLE", e.identifier)
            if e.producer.node in nodes and e.consumer.node in nodes:
                a, b = e.producer.node, e.consumer.node
                if b not in adjacency[a]:
                    adjacency[a].add(b)
                    indegree[b] += 1
        for i in p.initial_inputs:
            supplied[i.target] = supplied.get(i.target, 0) + 1
            target = inputs.get(i.target)
            if target is None:
                finding("ORCHESTRATION_HANDOFF_DANGLING", i.target.node)
            elif not compatible(ArtifactContract(i.artifact.kind, i.schema_reference, i.artifact.provenance), target.contract):
                finding("ORCHESTRATION_HANDOFF_INCOMPATIBLE", i.target.node)
        for ref, slot in inputs.items():
            count = supplied.get(ref, 0)
            if count > 1:
                finding("ORCHESTRATION_INPUT_AMBIGUOUS", ref.node, ref.slot)
            elif count == 0 and slot.required:
                finding("ORCHESTRATION_INPUT_MISSING", ref.node, ref.slot)
        for ref in p.terminal_outputs:
            if ref not in outputs:
                finding("ORCHESTRATION_OUTPUT_UNRESOLVED", ref.node)
        ready = [n for n in nodes if indegree[n] == 0]
        heapq.heapify(ready)
        order = []
        while ready:
            node = heapq.heappop(ready)
            order.append(node)
            for child in sorted(adjacency[node]):
                indegree[child] -= 1
                if indegree[child] == 0:
                    heapq.heappush(ready, child)
        if len(order) != len(nodes):
            finding("ORCHESTRATION_CYCLE", p.identity.identifier)
        findings = tuple(sorted(found, key=lambda f: (f.code, f.subject, f.slot or "")))
        status = "INVALID" if any(f.code != "ORCHESTRATION_INPUT_MISSING" for f in findings) else (
            "INCOMPLETE" if findings else "VALID")
        return status, findings, tuple(order) if status == "VALID" else ()

    @property
    def status(self):
        return self._assessment()[0]

    @property
    def findings(self):
        return self._assessment()[1]

    @property
    def topological_order(self):
        return self._assessment()[2]

    def record(self):
        status, findings, order = self._assessment()
        return {"schema": self.DOMAIN, "plan": self.plan.fingerprint(), "status": status,
                "findings": [f.record() for f in findings], "topological_plan_order": list(order),
                "execution_evidence": False, "grants_authority": False, "grants_trust": False}
