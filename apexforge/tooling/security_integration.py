"""Node-scoped pre-execution evidence gate; never a grant, token or executor."""
from dataclasses import dataclass
from hashlib import sha256

from authority.engine import AuthorityEngine
from authority.model import Principal, AuthorityCheck, AuthorityGrant
from air.model import PrincipalAuthority
from tooling import domain_platform as sdk
from tooling import cross_domain_orchestration as orch
from tooling import package_trust as trust
from tooling.package_manifest import PackageManifest, ExactVersion, CanonicalReference

MAX_ITEMS = 4096


class SecurityIntegrationError(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def require(ok, code):
    if not ok:
        raise SecurityIntegrationError(code)


def text(value):
    require(type(value) is str and 0 < len(value) <= 512 and
            all(32 <= ord(c) < 127 for c in value), "SECURITY_IDENTITY_INVALID")


def check_record(check):
    return {"id": check.id, "principal": check.principal, "capability": check.capability, "resource": check.resource}


def checked(check):
    require(type(check) is AuthorityCheck, "SECURITY_AUTHORITY_INPUT_INVALID")
    for value in (check.id, check.principal, check.capability, check.resource):
        text(value)
    require("*" not in check.principal and "*" not in check.capability and "*" not in check.resource,
            "SECURITY_RESOURCE_NOT_EXACT")


def refs(owner):
    try:
        require(len(owner.provenance) <= MAX_ITEMS, "SECURITY_PROVENANCE_INVALID")
        sdk._refs(owner, "provenance", CanonicalReference, "SECURITY_PROVENANCE_INVALID")
    except (TypeError, sdk.DomainContractError) as error:
        raise SecurityIntegrationError("SECURITY_PROVENANCE_INVALID") from error


@dataclass(frozen=True)
class SecurityAdmissionPolicy(sdk.CanonicalModel):
    """Requirements for one exact planned node. Requirements confer no permission."""
    identifier: str
    version: ExactVersion
    plan_fingerprint: str
    node_fingerprint: str
    authority_check: AuthorityCheck
    require_integrity: bool = True
    require_package_trust: bool = True
    require_provenance: bool = True
    require_external_authentication: bool = True
    DOMAIN = "apexforge.security-admission-policy/v1"

    def __post_init__(self):
        orch.name(self.identifier)
        require(type(self.version) is ExactVersion, "SECURITY_POLICY_INVALID")
        for value in (self.plan_fingerprint, self.node_fingerprint):
            require(type(value) is str and len(value) == 64 and all(c in "0123456789ABCDEF" for c in value),
                    "SECURITY_FINGERPRINT_INVALID")
        checked(self.authority_check)
        require(all(type(v) is bool for v in (self.require_integrity, self.require_package_trust,
            self.require_provenance, self.require_external_authentication)), "SECURITY_POLICY_INVALID")

    def record(self):
        return {"schema": self.DOMAIN, "id": self.identifier, "version": self.version.text(),
                "plan": self.plan_fingerprint, "node": self.node_fingerprint,
                "authority_check": check_record(self.authority_check), "require_governance": True,
                "require_valid_orchestration": True, "require_authority": True,
                "require_integrity": self.require_integrity, "require_package_trust": self.require_package_trust,
                "require_provenance": self.require_provenance,
                "require_external_authentication": self.require_external_authentication, "grants_authority": False}


@dataclass(frozen=True)
class PackageSecurityEvidence(sdk.CanonicalModel):
    """Inputs to the frozen verifier, not caller-assigned verification statuses."""
    manifest: PackageManifest
    members: tuple | None = None
    signature: trust.SignatureEnvelope | None = None
    public_key: bytes | None = None
    trust_policy: trust.TrustPolicy | None = None
    DOMAIN = "apexforge.security-package-evidence/v1"

    def __post_init__(self):
        require(type(self.manifest) is PackageManifest, "SECURITY_PACKAGE_INPUT_INVALID")
        require(self.members is None or type(self.members) is tuple and len(self.members) <= MAX_ITEMS and
                all(type(m) is trust.ContentMember for m in self.members), "SECURITY_PACKAGE_INPUT_INVALID")
        if self.members is not None:
            require(len({m.path.value.casefold() for m in self.members}) == len(self.members),
                    "SECURITY_PACKAGE_INPUT_INVALID")
            object.__setattr__(self, "members", tuple(sorted(self.members, key=lambda m: m.path.value)))
        require(self.signature is None or type(self.signature) is trust.SignatureEnvelope,
                "SECURITY_TRUST_INPUT_INVALID")
        require(self.public_key is None or type(self.public_key) is bytes and len(self.public_key) == 32,
                "SECURITY_TRUST_INPUT_INVALID")
        require(self.trust_policy is None or type(self.trust_policy) is trust.TrustPolicy,
                "SECURITY_TRUST_INPUT_INVALID")

    def record(self):
        return {"manifest": self.manifest.canonical_record(), "metadata": [list(x) for x in self.manifest.metadata],
                "members": None if self.members is None else [{"path": m.path.value,
                    "digest": sha256(m.data).hexdigest().upper()} for m in self.members],
                "signature": None if self.signature is None else self.signature.record(),
                "public_key": None if self.public_key is None else trust.key_fingerprint(self.public_key),
                "trust_policy": None if self.trust_policy is None else self.trust_policy.record()}


@dataclass(frozen=True)
class SecurityAdmissionRequest(sdk.CanonicalModel):
    policy: SecurityAdmissionPolicy
    plan: orch.CrossDomainOrchestrationPlan
    node: orch.OrchestrationNode
    principal: Principal | None = None
    authority_check: AuthorityCheck | None = None
    authority: AuthorityEngine | None = None
    package: PackageSecurityEvidence | None = None
    provenance: tuple = ()
    DOMAIN = "apexforge.security-admission-request/v1"

    def __post_init__(self):
        require(type(self.policy) is SecurityAdmissionPolicy and type(self.plan) is orch.CrossDomainOrchestrationPlan
                and type(self.node) is orch.OrchestrationNode, "SECURITY_REQUEST_INVALID")
        if self.principal is not None:
            require(type(self.principal) is Principal, "SECURITY_PRINCIPAL_INPUT_INVALID")
            text(self.principal.id)
            require(type(self.principal.display_name) is str and type(self.principal.roles) is tuple and
                    all(type(r) is str for r in self.principal.roles) and type(self.principal.authorities) is tuple and
                    all(type(a) is PrincipalAuthority and type(a.name) is str for a in self.principal.authorities),
                    "SECURITY_PRINCIPAL_INPUT_INVALID")
        if self.authority_check is not None:
            checked(self.authority_check)
        if self.authority is not None:
            require(type(self.authority) is AuthorityEngine and type(self.authority.grants) is tuple and
                    len(self.authority.grants) <= MAX_ITEMS and all(type(g) is AuthorityGrant for g in self.authority.grants),
                    "SECURITY_AUTHORITY_INPUT_INVALID")
            for grant in self.authority.grants:
                text(grant.principal)
                text(grant.capability)
                require(type(grant.resource) is str, "SECURITY_AUTHORITY_INPUT_INVALID")
                if grant.resource:
                    text(grant.resource)
        require(self.package is None or type(self.package) is PackageSecurityEvidence, "SECURITY_PACKAGE_INPUT_INVALID")
        refs(self)

    def record(self):
        principal = None if self.principal is None else {"id": self.principal.id,
            "display_name": self.principal.display_name, "roles": list(self.principal.roles),
            "authorities": [a.name for a in self.principal.authorities]}
        return {"schema": self.DOMAIN, "policy": self.policy.fingerprint(), "plan": self.plan.fingerprint(),
                "node": self.node.fingerprint(), "node_id": self.node.identifier, "operation": self.node.operation,
                "catalog": self.plan.catalog.fingerprint(), "governance": self.node.registration.fingerprint(),
                "descriptor": self.node.descriptor.fingerprint(), "implementation": self.node.descriptor.implementation.record(),
                "principal": principal, "check": None if self.authority_check is None else check_record(self.authority_check),
                "authority_grants": None if self.authority is None else [{"principal": g.principal,
                    "capability": g.capability, "resource": g.resource} for g in self.authority.grants],
                "package": None if self.package is None else self.package.record(),
                "provenance": [r.record() for r in self.provenance]}


CODES = frozenset(("SECURITY_PLAN_MISMATCH", "SECURITY_NODE_MISMATCH", "SECURITY_GOVERNANCE_MISMATCH",
    "SECURITY_ORCHESTRATION_INVALID", "SECURITY_ORCHESTRATION_INCOMPLETE", "SECURITY_DESCRIPTOR_MISMATCH",
    "SECURITY_PACKAGE_MISMATCH", "SECURITY_PRINCIPAL_MISMATCH", "SECURITY_CAPABILITY_MISMATCH",
    "SECURITY_RESOURCE_MISMATCH", "SECURITY_CHECK_MISMATCH", "SECURITY_AUTHORITY_MISSING",
    "SECURITY_AUTHORITY_DENIED", "SECURITY_INTEGRITY_MISSING", "SECURITY_INTEGRITY_INVALID",
    "SECURITY_TRUST_EVIDENCE_MISSING", "SECURITY_TRUST_EVIDENCE_INVALID", "SECURITY_CRYPTO_UNAVAILABLE",
    "SECURITY_PROVENANCE_INCOMPLETE", "SECURITY_PROVIDER_AUTHENTICATION_MISSING"))
DIMENSIONS = ("plan", "node", "governance", "orchestration", "descriptor", "package", "authority",
              "integrity", "trust", "provenance", "provider-authentication")


@dataclass(frozen=True)
class SecurityFinding(sdk.CanonicalModel):
    code: str
    dimension: str
    state: str
    DOMAIN = "apexforge.security-admission-finding/v1"

    def __post_init__(self):
        require(type(self.code) is str and self.code in CODES and type(self.dimension) is str and
                self.dimension in DIMENSIONS and type(self.state) is str and self.state in ("DENIED", "MISSING", "UNAVAILABLE"),
                "SECURITY_FINDING_INVALID")

    def record(self):
        return {"code": self.code, "dimension": self.dimension, "state": self.state}


@dataclass(frozen=True)
class SecurityAdmissionDecision(sdk.CanonicalModel):
    request: SecurityAdmissionRequest
    DOMAIN = "apexforge.security-admission-decision/v1"

    def __post_init__(self):
        require(type(self.request) is SecurityAdmissionRequest, "SECURITY_REQUEST_INVALID")

    def _assessment(self):
        r = self.request
        p = r.policy
        states = {d: "SATISFIED" for d in DIMENSIONS}
        findings = set()
        def issue(dimension, code, state="DENIED"):
            findings.add(SecurityFinding(code, dimension, state))
            priority = {"SATISFIED": 0, "NOT_REQUIRED": 0, "MISSING": 1, "UNAVAILABLE": 2, "DENIED": 3}
            if priority[state] > priority[states[dimension]]:
                states[dimension] = state
        if p.plan_fingerprint != r.plan.fingerprint():
            issue("plan", "SECURITY_PLAN_MISMATCH")
        if p.node_fingerprint != r.node.fingerprint() or r.node not in r.plan.nodes:
            issue("node", "SECURITY_NODE_MISMATCH")
        registered = r.node.registration.candidate.descriptor
        if r.node.registration not in r.plan.catalog.entries or r.node.registration.status != "ADMISSIBLE":
            issue("governance", "SECURITY_GOVERNANCE_MISMATCH")
        validation = orch.OrchestrationValidation(r.plan)
        if validation.status != "VALID":
            issue("orchestration", "SECURITY_ORCHESTRATION_INCOMPLETE" if validation.status == "INCOMPLETE" else
                  "SECURITY_ORCHESTRATION_INVALID", "MISSING" if validation.status == "INCOMPLETE" else "DENIED")
        if registered != r.node.descriptor:
            issue("descriptor", "SECURITY_DESCRIPTOR_MISMATCH")
        if registered.implementation != r.node.descriptor.implementation:
            issue("package", "SECURITY_PACKAGE_MISMATCH")
        if r.principal is None or r.authority_check is None or r.authority is None:
            issue("authority", "SECURITY_AUTHORITY_MISSING", "MISSING")
        if r.principal is not None and r.principal.id != p.authority_check.principal:
            issue("authority", "SECURITY_PRINCIPAL_MISMATCH")
        if r.authority_check is not None:
            for actual, expected, code in ((r.authority_check.principal, p.authority_check.principal, "SECURITY_PRINCIPAL_MISMATCH"),
                (r.authority_check.capability, p.authority_check.capability, "SECURITY_CAPABILITY_MISMATCH"),
                (r.authority_check.resource, p.authority_check.resource, "SECURITY_RESOURCE_MISMATCH"),
                (r.authority_check.id, p.authority_check.id, "SECURITY_CHECK_MISMATCH")):
                if actual != expected:
                    issue("authority", code)
        authority_result = None
        if states["authority"] == "SATISFIED":
            authority_result = r.authority.check(principal=r.authority_check.principal,
                capability=r.authority_check.capability, resource=r.authority_check.resource)
            if not authority_result:
                issue("authority", "SECURITY_AUTHORITY_DENIED")
        verification = None
        evidence = r.package
        if evidence is not None:
            if sdk.ImplementationPackage.from_manifest(evidence.manifest) != r.node.descriptor.implementation:
                issue("package", "SECURITY_PACKAGE_MISMATCH")
            if evidence.signature is not None:
                if evidence.signature.payload_fingerprint != trust.payload_fingerprint(evidence.manifest):
                    issue("trust", "SECURITY_TRUST_EVIDENCE_INVALID")
                if evidence.public_key is None:
                    issue("trust", "SECURITY_TRUST_EVIDENCE_MISSING", "MISSING")
                elif evidence.signature.signer_fingerprint != trust.key_fingerprint(evidence.public_key):
                    issue("trust", "SECURITY_TRUST_EVIDENCE_INVALID")
            if evidence.members is not None:
                verification = trust.verify_package(evidence.manifest, evidence.members,
                    evidence.signature, evidence.public_key, evidence.trust_policy).record()
                if verification["integrity"]["status"] != "VALID":
                    issue("integrity", "SECURITY_INTEGRITY_INVALID")
                if evidence.signature is not None and verification["signature"] != "CRYPTO_PROVIDER_UNAVAILABLE":
                    issue("trust", "SECURITY_TRUST_EVIDENCE_INVALID")
                if evidence.signature is not None and verification["signature"] == "CRYPTO_PROVIDER_UNAVAILABLE":
                    issue("trust", "SECURITY_CRYPTO_UNAVAILABLE", "UNAVAILABLE")
                if evidence.trust_policy is not None:
                    if evidence.trust_policy.require_signature and evidence.signature is None:
                        issue("trust", "SECURITY_TRUST_EVIDENCE_MISSING", "MISSING")
                    if evidence.trust_policy.require_scope_trust:
                        if evidence.public_key is None:
                            issue("trust", "SECURITY_TRUST_EVIDENCE_MISSING", "MISSING")
                        elif verification["scope_trust"] != "TRUSTED_FOR_PACKAGE_SCOPE":
                            issue("trust", "SECURITY_TRUST_EVIDENCE_INVALID")
        if verification is None:
            supplied_verification_requirement = evidence is not None and (evidence.signature is not None or
                evidence.public_key is not None or evidence.trust_policy is not None)
            if p.require_integrity or p.require_package_trust or supplied_verification_requirement:
                issue("integrity", "SECURITY_INTEGRITY_MISSING", "MISSING")
            else:
                states["integrity"] = "NOT_REQUIRED"
            if supplied_verification_requirement:
                issue("trust", "SECURITY_TRUST_EVIDENCE_MISSING", "MISSING")
        if p.require_package_trust:
            if evidence is None or evidence.signature is None or evidence.trust_policy is None:
                issue("trust", "SECURITY_TRUST_EVIDENCE_MISSING", "MISSING")
            # The frozen verifier cannot produce cryptographic signature validity.
            issue("trust", "SECURITY_CRYPTO_UNAVAILABLE", "UNAVAILABLE")
        elif states["trust"] == "SATISFIED":
            states["trust"] = "NOT_REQUIRED"
        if p.require_provenance and not r.provenance:
            issue("provenance", "SECURITY_PROVENANCE_INCOMPLETE", "MISSING")
        elif not p.require_provenance:
            states["provenance"] = "NOT_REQUIRED"
        if p.require_external_authentication and r.node.descriptor.identity.kind == "external-adapter":
            issue("provider-authentication", "SECURITY_PROVIDER_AUTHENTICATION_MISSING", "MISSING")
        else:
            states["provider-authentication"] = "NOT_REQUIRED"
        status = "DENIED" if "DENIED" in states.values() else (
            "INCOMPLETE" if any(s in ("MISSING", "UNAVAILABLE") for s in states.values()) else "ADMISSIBLE")
        return status, tuple(sorted(findings, key=lambda f: (f.dimension, f.code, f.state))), states, authority_result, verification

    @property
    def status(self):
        return self._assessment()[0]

    @property
    def findings(self):
        return self._assessment()[1]

    def record(self):
        status, findings, states, authority_result, verification = self._assessment()
        return {"schema": self.DOMAIN, "request": self.request.fingerprint(), "policy": self.request.policy.fingerprint(),
                "bindings": self.request.record(), "status": status, "findings": [f.record() for f in findings],
                "evidence_matrix": states, "authority_integration": "DIRECT_CHECK", "authority_allowed": authority_result,
                "package_verification": verification, "cryptographic_trust_established": False,
                "execution": "NOT_PERFORMED", "grants_authority": False, "semantic_authority": "CANONICAL_AIR"}


def bind_decision(decision, request):
    """Consume only exact-context admission evidence. This returns no execution permit."""
    require(type(decision) is SecurityAdmissionDecision and type(request) is SecurityAdmissionRequest,
            "SECURITY_REQUEST_INVALID")
    require(decision.request.fingerprint() == request.fingerprint(), "SECURITY_ADMISSION_REPLAY_MISMATCH")
    return decision
