"""Immutable integration evidence collection, never execution or authorization."""
from dataclasses import dataclass, field

from tooling import domain_platform as sdk
from tooling import cross_domain_orchestration as orch
from tooling import security_integration as security
from tooling.package_manifest import CanonicalReference

LAYERS = tuple("p15-" + str(n) for n in range(1, 13))
BOUNDARIES = ("semantic-authority", "package-trust", "runtime-authority", "identity-separation",
    "provider-affiliation", "engineering-safety", "physical-actuation", "external-facts",
    "network", "credentials", "models")
MAX_ITEMS = 4096


class AcceptanceError(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def require(ok, code):
    if not ok:
        raise AcceptanceError(code)


def collection(owner, field, values, cls):
    require(type(values) is tuple and len(values) <= MAX_ITEMS and all(type(v) is cls for v in values),
            "ACCEPTANCE_EVIDENCE_INVALID")
    keys = [sdk._json(v.record()) for v in values]
    require(len(set(keys)) == len(keys), "ACCEPTANCE_DUPLICATE_EVIDENCE")
    object.__setattr__(owner, field, tuple(v for _, v in sorted(zip(keys, values), key=lambda p: p[0])))


@dataclass(frozen=True)
class AcceptanceEvidence(sdk.CanonicalModel):
    """Caller-supplied acceptance observation; not authenticated proof or a suite runner."""
    area: str
    status: str
    reference: CanonicalReference
    DOMAIN = "apexforge.platform-acceptance-evidence/v1"

    def __post_init__(self):
        require(type(self.area) is str and self.area in LAYERS + BOUNDARIES and
                type(self.status) is str and self.status in ("PASS", "FAIL") and
                type(self.reference) is CanonicalReference, "ACCEPTANCE_EVIDENCE_INVALID")

    def record(self):
        return {"area": self.area, "status": self.status, "reference": self.reference.record(),
                "origin": "CALLER_SUPPLIED_OBSERVATION"}


@dataclass(frozen=True)
class AdmissionExpectation(sdk.CanonicalModel):
    identifier: str
    request: security.SecurityAdmissionRequest
    decision: security.SecurityAdmissionDecision
    expected_status: str
    _request_fingerprint: str = field(init=False, repr=False)
    _decision_fingerprint: str = field(init=False, repr=False)
    _observed_status: str = field(init=False, repr=False)
    _binding_matches: bool = field(init=False, repr=False)
    DOMAIN = "apexforge.platform-acceptance-admission-case/v1"

    def __post_init__(self):
        orch.name(self.identifier)
        require(type(self.request) is security.SecurityAdmissionRequest and
                type(self.decision) is security.SecurityAdmissionDecision and type(self.expected_status) is str and
                self.expected_status in ("ADMISSIBLE", "DENIED", "INCOMPLETE"), "ACCEPTANCE_ADMISSION_INVALID")
        # Freeze owner-produced evidence once; no repeat admission on projection.
        object.__setattr__(self, "_request_fingerprint", self.request.fingerprint())
        object.__setattr__(self, "_decision_fingerprint", self.decision.fingerprint())
        object.__setattr__(self, "_observed_status", self.decision.status)
        try:
            security.bind_decision(self.decision, self.request)
        except security.SecurityIntegrationError as error:
            require(error.code == "SECURITY_ADMISSION_REPLAY_MISMATCH", "ACCEPTANCE_ADMISSION_INVALID")
            object.__setattr__(self, "_binding_matches", False)
        else:
            object.__setattr__(self, "_binding_matches", True)

    def record(self):
        return {"id": self.identifier, "request": self._request_fingerprint,
                "decision": self._decision_fingerprint, "expected_status": self.expected_status}


@dataclass(frozen=True)
class PlatformAcceptanceScenario(sdk.CanonicalModel):
    identifier: str
    plan: orch.CrossDomainOrchestrationPlan
    packages: tuple
    admissions: tuple
    artifacts: tuple = ()
    domain_records: tuple = ()
    evidence: tuple = ()
    provenance: tuple = ()
    DOMAIN = "apexforge.platform-acceptance-scenario/v1"

    def __post_init__(self):
        orch.name(self.identifier)
        require(type(self.plan) is orch.CrossDomainOrchestrationPlan, "ACCEPTANCE_SCENARIO_INVALID")
        collection(self, "packages", self.packages, sdk.ImplementationPackage)
        require(type(self.admissions) is tuple and len(self.admissions) <= MAX_ITEMS and
                all(type(c) is AdmissionExpectation for c in self.admissions), "ACCEPTANCE_ADMISSION_INVALID")
        require(len({c.identifier for c in self.admissions}) == len(self.admissions), "ACCEPTANCE_DUPLICATE_EVIDENCE")
        object.__setattr__(self, "admissions", tuple(sorted(self.admissions, key=lambda c: c.identifier)))
        collection(self, "artifacts", self.artifacts, sdk.DomainArtifact)
        collection(self, "domain_records", self.domain_records, CanonicalReference)
        collection(self, "evidence", self.evidence, AcceptanceEvidence)
        require(len({c.area for c in self.evidence}) == len(self.evidence), "ACCEPTANCE_DUPLICATE_EVIDENCE")
        collection(self, "provenance", self.provenance, CanonicalReference)

    def record(self):
        return {"schema": self.DOMAIN, "id": self.identifier, "plan": self.plan.fingerprint(),
                "catalog": self.plan.catalog.fingerprint(), "packages": [p.record() for p in self.packages],
                "admissions": [c.record() for c in self.admissions], "artifacts": [a.record() for a in self.artifacts],
                "domain_records": [r.record() for r in self.domain_records],
                "evidence": [e.record() for e in self.evidence], "provenance": [r.record() for r in self.provenance]}


@dataclass(frozen=True)
class PlatformAcceptanceResult(sdk.CanonicalModel):
    """PASS means expected contract observations match; even expected denial may PASS."""
    scenario: PlatformAcceptanceScenario
    DOMAIN = "apexforge.platform-acceptance-result/v1"

    def __post_init__(self):
        require(type(self.scenario) is PlatformAcceptanceScenario, "ACCEPTANCE_SCENARIO_INVALID")

    def _assessment(self):
        s = self.scenario
        findings = set()
        def finding(code, subject):
            findings.add((code, subject))
        expected = set(LAYERS + BOUNDARIES)
        supplied = {e.area: e for e in s.evidence}
        for area in sorted(expected - supplied.keys()):
            finding("ACCEPTANCE_EVIDENCE_MISSING", area)
        for e in s.evidence:
            if e.status != "PASS":
                finding("ACCEPTANCE_OBSERVATION_FAILED", e.area)
        if set(s.packages) != {n.descriptor.implementation for n in s.plan.nodes}:
            finding("ACCEPTANCE_PACKAGE_BASELINE_MISMATCH", s.identifier)
        if orch.OrchestrationValidation(s.plan).status != "VALID":
            finding("ACCEPTANCE_ORCHESTRATION_NOT_VALID", s.identifier)
        descriptors = tuple(n.descriptor for n in s.plan.nodes)
        for a in s.artifacts:
            if not any((a.platform, a.implementation, a.descriptor_fingerprint) ==
                (d.identity, d.implementation, d.fingerprint()) and a.operation in d.operations for d in descriptors):
                finding("ACCEPTANCE_ARTIFACT_BINDING_MISMATCH", a.fingerprint())
        for i in s.plan.initial_inputs:
            if i.artifact not in s.artifacts:
                finding("ACCEPTANCE_INITIAL_ARTIFACT_MISSING", i.target.node)
        covered = set()
        observations = []
        for c in s.admissions:
            r = c.request
            if r.plan != s.plan or r.node not in s.plan.nodes:
                finding("ACCEPTANCE_ADMISSION_CONTEXT_MISMATCH", c.identifier)
            else:
                covered.add(r.node.identifier)
            if not c._binding_matches:
                finding("ACCEPTANCE_ADMISSION_REPLAY_MISMATCH", c.identifier)
            actual = c._observed_status
            observations.append({"case": c.identifier, "expected": c.expected_status, "observed": actual})
            if actual != c.expected_status:
                finding("ACCEPTANCE_ADMISSION_UNEXPECTED", c.identifier)
        for node in sorted({n.identifier for n in s.plan.nodes} - covered):
            finding("ACCEPTANCE_NODE_EVIDENCE_MISSING", node)
        missing_codes = {"ACCEPTANCE_EVIDENCE_MISSING", "ACCEPTANCE_INITIAL_ARTIFACT_MISSING", "ACCEPTANCE_NODE_EVIDENCE_MISSING"}
        status = "FAIL" if any(code not in missing_codes for code, _ in findings) else ("INCOMPLETE" if findings else "PASS")
        return status, tuple(sorted(findings)), tuple(observations)

    @property
    def status(self):
        return self._assessment()[0]

    def record(self):
        status, findings, observations = self._assessment()
        s = self.scenario
        return {"schema": self.DOMAIN, "scenario": s.fingerprint(), "status": status,
                "acceptance_matrix": [e.record() for e in s.evidence if e.area in LAYERS],
                "boundary_matrix": [e.record() for e in s.evidence if e.area in BOUNDARIES],
                "admissions": list(observations), "findings": [{"code": code, "subject": subject} for code, subject in findings],
                "provenance": [p.record() for p in s.provenance], "execution": "NOT_PERFORMED",
                "grants_authority": False, "grants_trust": False, "freeze_performed": False,
                "semantic_authority": "CANONICAL_AIR"}
