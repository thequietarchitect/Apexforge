"""Caller-evidence governance admission; never trust, authority or execution."""
from dataclasses import dataclass
import re
from tooling import domain_platform as sdk
from tooling.package_manifest import ExactVersion, CanonicalReference

MAX_ITEMS = 4096
EVIDENCE_KINDS = ("contract", "review", "boundary")
CLAIMS = ("semantic-authority", "authority-grant", "package-trust", "provider-authentication")


class GovernanceError(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def require(ok, code):
    if not ok:
        raise GovernanceError(code)


def name(value):
    try:
        sdk._name(value, "GOVERNANCE_ID_INVALID")
    except sdk.DomainContractError as error:
        raise GovernanceError("GOVERNANCE_ID_INVALID") from error


def digest(value):
    require(type(value) is str and re.fullmatch(r"[A-F0-9]{64}", value) is not None,
            "GOVERNANCE_FINGERPRINT_INVALID")


def strings(values, allowed):
    require(type(values) is tuple and len(values) <= MAX_ITEMS and
            all(type(v) is str and v in allowed for v in values), "GOVERNANCE_RULE_INVALID")
    require(len(set(values)) == len(values), "GOVERNANCE_DUPLICATE")
    return tuple(sorted(values))


def records(owner, field, cls):
    values = getattr(owner, field)
    require(type(values) is tuple and len(values) <= MAX_ITEMS and all(type(v) is cls for v in values),
            "GOVERNANCE_EVIDENCE_INVALID")
    keys = [sdk._json(v.record()) for v in values]
    require(len(set(keys)) == len(keys), "GOVERNANCE_DUPLICATE")
    object.__setattr__(owner, field, tuple(v for _, v in sorted(zip(keys, values), key=lambda pair: pair[0])))


@dataclass(frozen=True)
class DomainGovernancePolicyIdentity(sdk.CanonicalModel):
    identifier: str
    DOMAIN = "apexforge.domain-governance-policy-identity/v1"
    def __post_init__(self):
        name(self.identifier)
    def record(self):
        return {"schema": self.DOMAIN, "id": self.identifier}


@dataclass(frozen=True)
class DomainGovernancePolicy(sdk.CanonicalModel):
    identity: DomainGovernancePolicyIdentity
    version: ExactVersion
    permitted_kinds: tuple
    required_evidence: tuple = ("contract", "review", "boundary")
    require_provenance: bool = True
    schema: str = "apexforge.domain-governance-policy/v1"
    DOMAIN = "apexforge.domain-governance-policy/v1"
    def __post_init__(self):
        require(type(self.schema) is str and self.schema == self.DOMAIN, "GOVERNANCE_SCHEMA_UNSUPPORTED")
        require(type(self.identity) is DomainGovernancePolicyIdentity and type(self.version) is ExactVersion,
                "GOVERNANCE_POLICY_INVALID")
        require(type(self.require_provenance) is bool, "GOVERNANCE_RULE_INVALID")
        object.__setattr__(self, "permitted_kinds", strings(self.permitted_kinds, sdk.KINDS))
        object.__setattr__(self, "required_evidence", strings(self.required_evidence, EVIDENCE_KINDS))
    def record(self):
        return {"schema": self.schema, "identity": self.identity.record(), "version": self.version.text(),
                "permitted_kinds": list(self.permitted_kinds), "required_evidence": list(self.required_evidence),
                "require_provenance": self.require_provenance, "descriptor_schema": sdk.SCHEMA,
                "exact_package_required": True, "forbidden_claims": list(CLAIMS), "conflict_policy": "FAIL_CLOSED"}


@dataclass(frozen=True)
class GovernanceEvidence(sdk.CanonicalModel):
    category: str
    reference: CanonicalReference
    descriptor_fingerprint: str
    DOMAIN = "apexforge.domain-governance-evidence/v1"
    def __post_init__(self):
        require(type(self.category) is str and self.category in EVIDENCE_KINDS, "GOVERNANCE_EVIDENCE_INVALID")
        require(type(self.reference) is CanonicalReference, "GOVERNANCE_EVIDENCE_INVALID")
        digest(self.descriptor_fingerprint)
    def record(self):
        return {"category": self.category, "reference": self.reference.record(),
                "descriptor": self.descriptor_fingerprint}


@dataclass(frozen=True)
class DomainRegistrationCandidate(sdk.CanonicalModel):
    descriptor: sdk.DomainPlatformDescriptor
    evidence: tuple = ()
    provenance: tuple = ()
    contract: CanonicalReference | None = None
    claims: tuple = ()
    DOMAIN = "apexforge.domain-registration/v1"
    def __post_init__(self):
        require(type(self.descriptor) is sdk.DomainPlatformDescriptor, "GOVERNANCE_DESCRIPTOR_BINDING_INVALID")
        records(self, "evidence", GovernanceEvidence)
        records(self, "provenance", CanonicalReference)
        require(self.contract is None or type(self.contract) is CanonicalReference, "GOVERNANCE_EVIDENCE_INVALID")
        object.__setattr__(self, "claims", strings(self.claims, CLAIMS))
    @property
    def key(self):
        return (self.descriptor.identity.identifier, self.descriptor.contract_version.text())
    def record(self):
        return {"schema": self.DOMAIN, "descriptor": self.descriptor.record(),
                "descriptor_fingerprint": self.descriptor.fingerprint(),
                "implementation": self.descriptor.implementation.record(),
                "contract": None if self.contract is None else self.contract.record(),
                "evidence": [e.record() for e in self.evidence], "claims": list(self.claims),
                "provenance": [r.record() for r in self.provenance]}


@dataclass(frozen=True)
class GovernanceFinding(sdk.CanonicalModel):
    code: str
    subject: str
    DOMAIN = "apexforge.domain-governance-finding/v1"
    def __post_init__(self):
        require(type(self.code) is str and self.code in ("GOVERNANCE_DOMAIN_KIND_NOT_ALLOWED",
            "GOVERNANCE_DESCRIPTOR_BINDING_INVALID", "GOVERNANCE_REQUIRED_EVIDENCE_MISSING",
            "GOVERNANCE_PROHIBITED_CLAIM", "GOVERNANCE_REGISTRATION_CONFLICT",
            "GOVERNANCE_PROVENANCE_INCOMPLETE"), "GOVERNANCE_FINDING_INVALID")
        name(self.subject)
    def record(self):
        return {"code": self.code, "subject": self.subject}


@dataclass(frozen=True)
class DomainGovernanceDecision(sdk.CanonicalModel):
    policy: DomainGovernancePolicy
    candidate: DomainRegistrationCandidate
    existing: DomainRegistrationCandidate | None = None
    DOMAIN = "apexforge.domain-governance-decision/v1"
    def __post_init__(self):
        require(type(self.policy) is DomainGovernancePolicy and type(self.candidate) is DomainRegistrationCandidate,
                "GOVERNANCE_DECISION_INVALID")
        require(self.existing is None or type(self.existing) is DomainRegistrationCandidate and
                self.existing.key == self.candidate.key, "GOVERNANCE_CONFLICT_BINDING_INVALID")
    @property
    def findings(self):
        p, c = self.policy, self.candidate
        found = []
        if c.descriptor.identity.kind not in p.permitted_kinds:
            found.append(GovernanceFinding("GOVERNANCE_DOMAIN_KIND_NOT_ALLOWED", c.descriptor.identity.kind))
        for evidence in c.evidence:
            if evidence.descriptor_fingerprint != c.descriptor.fingerprint():
                found.append(GovernanceFinding("GOVERNANCE_DESCRIPTOR_BINDING_INVALID", evidence.category))
        for claim in c.claims:
            found.append(GovernanceFinding("GOVERNANCE_PROHIBITED_CLAIM", claim))
        for missing in sorted(set(p.required_evidence) - {e.category for e in c.evidence}):
            found.append(GovernanceFinding("GOVERNANCE_REQUIRED_EVIDENCE_MISSING", missing))
        if p.require_provenance and not c.provenance:
            found.append(GovernanceFinding("GOVERNANCE_PROVENANCE_INCOMPLETE", "provenance"))
        if self.existing is not None and self.existing != c:
            found.append(GovernanceFinding("GOVERNANCE_REGISTRATION_CONFLICT", "registration"))
        return tuple(sorted(set(found), key=lambda f: (f.code, f.subject)))
    @property
    def status(self):
        codes = {f.code for f in self.findings}
        if codes & {"GOVERNANCE_DOMAIN_KIND_NOT_ALLOWED", "GOVERNANCE_DESCRIPTOR_BINDING_INVALID", "GOVERNANCE_PROHIBITED_CLAIM"}:
            return "REJECTED"
        if "GOVERNANCE_REGISTRATION_CONFLICT" in codes:
            return "CONFLICT"
        return "INCOMPLETE" if codes else "ADMISSIBLE"
    def record(self):
        return {"schema": self.DOMAIN, "policy": self.policy.fingerprint(), "candidate": self.candidate.fingerprint(),
                "descriptor": self.candidate.descriptor.fingerprint(),
                "implementation": self.candidate.descriptor.implementation.record(), "status": self.status,
                "findings": [f.record() for f in self.findings], "evidence": [e.record() for e in self.candidate.evidence],
                "existing": None if self.existing is None else self.existing.fingerprint(),
                "authority_granted": False, "trust_granted": False, "semantic_authority": "CANONICAL_AIR"}


@dataclass(frozen=True)
class DomainCatalogSnapshot(sdk.CanonicalModel):
    policy: DomainGovernancePolicy
    entries: tuple = ()
    predecessor: str | None = None
    DOMAIN = "apexforge.domain-catalog/v1"
    def __post_init__(self):
        require(type(self.policy) is DomainGovernancePolicy, "GOVERNANCE_POLICY_INVALID")
        require(type(self.entries) is tuple and len(self.entries) <= MAX_ITEMS and
                all(type(e) is DomainGovernanceDecision for e in self.entries), "GOVERNANCE_CATALOG_INVALID")
        if self.predecessor is not None:
            digest(self.predecessor)
        by_key = {}
        for entry in self.entries:
            require(entry.policy == self.policy, "GOVERNANCE_POLICY_MISMATCH")
            require(entry.status == "ADMISSIBLE", "GOVERNANCE_CATALOG_NOT_ADMISSIBLE")
            key = entry.candidate.key
            require(key not in by_key or by_key[key] == entry, "GOVERNANCE_REGISTRATION_CONFLICT")
            by_key[key] = entry
        object.__setattr__(self, "entries", tuple(by_key[k] for k in sorted(by_key)))
    def lookup(self, identifier, version):
        name(identifier)
        require(type(version) is ExactVersion, "GOVERNANCE_VERSION_INVALID")
        return next((e for e in self.entries if e.candidate.key == (identifier, version.text())), None)
    def record(self):
        return {"schema": self.DOMAIN, "policy": self.policy.fingerprint(), "predecessor": self.predecessor,
                "entries": [{"candidate": e.candidate.record(), "decision": e.record(),
                    "decision_fingerprint": e.fingerprint()} for e in self.entries], "package_registry": False}


def evaluate(policy, candidate, catalog=None):
    require(type(policy) is DomainGovernancePolicy and type(candidate) is DomainRegistrationCandidate,
            "GOVERNANCE_DECISION_INVALID")
    require(catalog is None or type(catalog) is DomainCatalogSnapshot, "GOVERNANCE_CATALOG_INVALID")
    if catalog is not None:
        require(catalog.policy == policy, "GOVERNANCE_POLICY_MISMATCH")
        entry = catalog.lookup(candidate.descriptor.identity.identifier, candidate.descriptor.contract_version)
    else:
        entry = None
    return DomainGovernanceDecision(policy, candidate, None if entry is None else entry.candidate)


def register(catalog, candidate):
    require(type(catalog) is DomainCatalogSnapshot, "GOVERNANCE_CATALOG_INVALID")
    decision = evaluate(catalog.policy, candidate, catalog)
    require(decision.status == "ADMISSIBLE", "GOVERNANCE_CATALOG_NOT_ADMISSIBLE")
    if any(e.candidate == candidate for e in catalog.entries):
        return catalog
    return DomainCatalogSnapshot(catalog.policy, catalog.entries + (decision,), catalog.fingerprint())
