"""P15.1 passive domain SDK contracts; canonical AIR retains semantic authority.

Constructors validate supplied evidence and declarations only. No dispatch,
acquisition, authentication, package resolution or interchange parser lives here.
"""
from dataclasses import dataclass
from hashlib import sha256
import json
import re

from tooling.package_manifest import (PackageManifest, PackageCoordinate,
    PackageContentIdentity, ExactVersion, CanonicalReference, SymbolReference)

SCHEMA = "apexforge.domain-platform/v1"
KINDS = frozenset(("simulation", "motion", "narrative", "agent", "parametric",
                   "fabrication", "external-adapter"))
ARTIFACT_KINDS = frozenset(("analysis", "plan", "model", "data", "external-reference"))


class DomainContractError(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def _require(ok, code):
    if not ok:
        raise DomainContractError(code)


def _name(value, code):
    _require(type(value) is str and len(value) <= 128 and
        re.fullmatch(r"[a-z][a-z0-9_-]*(?:\.[a-z][a-z0-9_-]*)*", value, re.ASCII), code)


def _json(record):
    return json.dumps(record, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False)


def _ordered(values, cls, code):
    _require(type(values) is tuple and all(type(v) is cls for v in values), code)
    keys = tuple(_json(v.record()) for v in values)
    _require(len(set(keys)) == len(keys), code)
    return tuple(v for _, v in sorted(zip(keys, values), key=lambda p: p[0]))


def _refs(owner, field, cls, code):
    object.__setattr__(owner, field, _ordered(getattr(owner, field), cls, code))


class CanonicalModel:
    def canonical_json(self):
        return _json(self.record())

    def fingerprint(self):
        return sha256((self.DOMAIN + "\0" + self.canonical_json()).encode("utf-8")).hexdigest().upper()


@dataclass(frozen=True)
class DomainPlatformIdentity(CanonicalModel):
    identifier: str
    kind: str
    schema: str = SCHEMA
    DOMAIN = "apexforge.domain-platform-identity/v1"

    def __post_init__(self):
        _require(self.schema == SCHEMA, "DOMAIN_SCHEMA_UNSUPPORTED")
        _name(self.identifier, "DOMAIN_PLATFORM_ID_INVALID")
        _require(type(self.kind) is str and self.kind in KINDS, "DOMAIN_KIND_INVALID")

    def record(self):
        return {"schema": self.schema, "id": self.identifier, "kind": self.kind}


@dataclass(frozen=True)
class ImplementationPackage(CanonicalModel):
    """References P14 identity, without claiming actual bytes, trust or publication."""
    coordinate: PackageCoordinate
    content: PackageContentIdentity
    DOMAIN = "apexforge.domain-implementation-binding/v1"

    def __post_init__(self):
        _require(type(self.coordinate) is PackageCoordinate and
                 type(self.content) is PackageContentIdentity, "DOMAIN_PACKAGE_BINDING_INVALID")
        # Re-admit syntax using the frozen identity owners, without a new identity algorithm.
        try:
            PackageCoordinate.from_mapping(self.coordinate.record())
            PackageContentIdentity(self.content.fingerprint, self.content.domain)
        except ValueError as exc:
            raise DomainContractError("DOMAIN_PACKAGE_BINDING_INVALID") from exc

    @classmethod
    def from_manifest(cls, manifest):
        _require(type(manifest) is PackageManifest, "DOMAIN_PACKAGE_BINDING_INVALID")
        checked = PackageManifest.from_mapping(manifest.canonical_record())
        return cls(checked.coordinate, checked.content_identity())

    def record(self):
        return {"coordinate": self.coordinate.record(), "content": self.content.record()}


@dataclass(frozen=True)
class DomainCapability(CanonicalModel):
    identifier: str
    DOMAIN = "apexforge.domain-capability-declaration/v1"

    def __post_init__(self):
        _name(self.identifier, "DOMAIN_CAPABILITY_INVALID")

    def record(self):
        return {"domain_capability": self.identifier, "grants_authority": False}


@dataclass(frozen=True)
class DomainDependency(CanonicalModel):
    platform: DomainPlatformIdentity
    implementation: ImplementationPackage
    contract_version: ExactVersion
    DOMAIN = "apexforge.domain-dependency/v1"

    def __post_init__(self):
        _binding(self.platform, self.implementation)
        _require(type(self.contract_version) is ExactVersion, "DOMAIN_CONTRACT_VERSION_INVALID")

    def record(self):
        return {"platform": self.platform.record(), "implementation": self.implementation.record(),
                "contract_version": self.contract_version.text()}


def _binding(platform, implementation):
    _require(type(platform) is DomainPlatformIdentity, "DOMAIN_PLATFORM_ID_INVALID")
    _require(type(implementation) is ImplementationPackage, "DOMAIN_PACKAGE_BINDING_INVALID")


@dataclass(frozen=True)
class DomainPlatformDescriptor(CanonicalModel):
    identity: DomainPlatformIdentity
    implementation: ImplementationPackage
    contract_version: ExactVersion
    operations: tuple[str, ...]
    capabilities: tuple[DomainCapability, ...] = ()
    dependencies: tuple[DomainDependency, ...] = ()
    provenance: tuple[CanonicalReference, ...] = ()
    DOMAIN = SCHEMA

    def __post_init__(self):
        _binding(self.identity, self.implementation)
        _require(type(self.contract_version) is ExactVersion, "DOMAIN_CONTRACT_VERSION_INVALID")
        _require(type(self.operations) is tuple, "DOMAIN_OPERATION_INVALID")
        for op in self.operations:
            _name(op, "DOMAIN_OPERATION_INVALID")
        _require(len(set(self.operations)) == len(self.operations), "DOMAIN_OPERATION_DUPLICATE")
        object.__setattr__(self, "operations", tuple(sorted(self.operations)))
        _refs(self, "capabilities", DomainCapability, "DOMAIN_CAPABILITY_INVALID")
        _refs(self, "dependencies", DomainDependency, "DOMAIN_DEPENDENCY_INVALID")
        ids = tuple(d.platform.identifier for d in self.dependencies)
        _require(len(set(ids)) == len(ids) and self.identity.identifier not in ids,
                 "DOMAIN_DEPENDENCY_CONFLICT")
        _refs(self, "provenance", CanonicalReference, "DOMAIN_PROVENANCE_INVALID")

    def record(self):
        return {"schema": SCHEMA, "identity": self.identity.record(),
            "implementation": self.implementation.record(), "contract_version": self.contract_version.text(),
            "operations": list(self.operations), "capabilities": [c.record() for c in self.capabilities],
            "dependencies": [d.record() for d in self.dependencies],
            "provenance": [p.record() for p in self.provenance], "semantic_authority": "CANONICAL_AIR"}


@dataclass(frozen=True)
class DomainArtifact(CanonicalModel):
    """Domain output/reference identity; raw digest is a supplied claim unless from_bytes is used."""
    kind: str
    platform: DomainPlatformIdentity
    implementation: ImplementationPackage
    operation: str
    digest: str
    descriptor_fingerprint: str
    semantic_inputs: tuple[CanonicalReference, ...] = ()
    symbols: tuple[SymbolReference, ...] = ()
    provenance: tuple[CanonicalReference, ...] = ()
    schema: str = "apexforge.domain-artifact/v1"
    DOMAIN = "apexforge.domain-artifact/v1"

    def __post_init__(self):
        _require(self.schema == self.DOMAIN, "DOMAIN_SCHEMA_UNSUPPORTED")
        _require(type(self.kind) is str and self.kind in ARTIFACT_KINDS,
                 "DOMAIN_CORE_SEMANTIC_BOUNDARY_VIOLATION")
        _binding(self.platform, self.implementation)
        _name(self.operation, "DOMAIN_OPERATION_INVALID")
        _require(type(self.digest) is str and re.fullmatch(r"[0-9A-F]{64}", self.digest), "DOMAIN_ARTIFACT_INVALID")
        _require(type(self.descriptor_fingerprint) is str and re.fullmatch(r"[0-9A-F]{64}", self.descriptor_fingerprint),
                 "DOMAIN_ARTIFACT_INVALID")
        _refs(self, "semantic_inputs", CanonicalReference, "DOMAIN_INPUT_INVALID")
        _refs(self, "symbols", SymbolReference, "DOMAIN_INPUT_INVALID")
        _refs(self, "provenance", CanonicalReference, "DOMAIN_PROVENANCE_INVALID")

    @classmethod
    def from_bytes(cls, descriptor, operation, kind, data, **references):
        _operation(descriptor, operation)
        _require(type(data) is bytes, "DOMAIN_ARTIFACT_INVALID")
        return cls(kind, descriptor.identity, descriptor.implementation, operation,
                   sha256(data).hexdigest().upper(), descriptor.fingerprint(), **references)

    def verify_bytes(self, data):
        _require(type(data) is bytes and sha256(data).hexdigest().upper() == self.digest,
                 "DOMAIN_ARTIFACT_DIGEST_MISMATCH")

    def record(self):
        return {"schema": self.schema, "kind": self.kind, "platform": self.platform.record(),
            "implementation": self.implementation.record(), "operation": self.operation, "digest": self.digest,
            "descriptor_fingerprint": self.descriptor_fingerprint,
            "semantic_inputs": [r.record() for r in self.semantic_inputs],
            "symbols": [r.record() for r in self.symbols], "provenance": [r.record() for r in self.provenance],
            "semantic_authority": "CANONICAL_AIR", "grants_authority": False}


def _operation(descriptor, operation):
    _require(type(descriptor) is DomainPlatformDescriptor, "DOMAIN_DESCRIPTOR_INVALID")
    _name(operation, "DOMAIN_OPERATION_INVALID")
    _require(operation in descriptor.operations, "DOMAIN_OPERATION_UNDECLARED")


@dataclass(frozen=True)
class DomainRequest(CanonicalModel):
    descriptor: DomainPlatformDescriptor
    operation: str
    semantic_inputs: tuple[CanonicalReference, ...] = ()
    symbols: tuple[SymbolReference, ...] = ()
    artifacts: tuple[DomainArtifact, ...] = ()
    capabilities: tuple[DomainCapability, ...] = ()
    provenance: tuple[CanonicalReference, ...] = ()
    correlation: str | None = None
    schema: str = "apexforge.domain-request/v1"
    DOMAIN = "apexforge.domain-request/v1"

    def __post_init__(self):
        _require(self.schema == self.DOMAIN, "DOMAIN_SCHEMA_UNSUPPORTED")
        _operation(self.descriptor, self.operation)
        for field, cls, code in (("semantic_inputs", CanonicalReference, "DOMAIN_INPUT_INVALID"),
            ("symbols", SymbolReference, "DOMAIN_INPUT_INVALID"), ("artifacts", DomainArtifact, "DOMAIN_INPUT_INVALID"),
            ("capabilities", DomainCapability, "DOMAIN_CAPABILITY_INVALID"),
            ("provenance", CanonicalReference, "DOMAIN_PROVENANCE_INVALID")):
            _refs(self, field, cls, code)
        _require(set(self.capabilities) <= set(self.descriptor.capabilities), "DOMAIN_CAPABILITY_UNDECLARED")
        if self.correlation is not None:
            _name(self.correlation, "DOMAIN_CORRELATION_INVALID")

    def record(self):
        return {"schema": self.schema, "descriptor": self.descriptor.record(), "operation": self.operation,
            "semantic_inputs": [r.record() for r in self.semantic_inputs], "symbols": [r.record() for r in self.symbols],
            "artifacts": [r.record() for r in self.artifacts], "capabilities": [r.record() for r in self.capabilities],
            "provenance": [r.record() for r in self.provenance], "correlation": self.correlation,
            "grants_authority": False}


@dataclass(frozen=True)
class DomainDiagnostic(CanonicalModel):
    code: str
    subject: str
    DOMAIN = "apexforge.domain-diagnostic/v1"

    def __post_init__(self):
        _require(type(self.code) is str and self.code in ("DOMAIN_INPUT_INVALID", "DOMAIN_RESULT_INVALID",
            "DOMAIN_OPERATION_UNDECLARED", "DOMAIN_EVIDENCE_MISSING", "DOMAIN_OPERATION_NOT_EXECUTED"),
            "DOMAIN_DIAGNOSTIC_INVALID")
        _name(self.subject, "DOMAIN_DIAGNOSTIC_INVALID")

    def record(self):
        return {"code": self.code, "subject": self.subject}


@dataclass(frozen=True)
class DomainResult(CanonicalModel):
    """Caller-declared completion/evidence, never a receipt of SDK execution."""
    request: DomainRequest
    status: str
    outputs: tuple[DomainArtifact, ...] = ()
    diagnostics: tuple[DomainDiagnostic, ...] = ()
    provenance: tuple[CanonicalReference, ...] = ()
    schema: str = "apexforge.domain-result/v1"
    DOMAIN = "apexforge.domain-result/v1"

    def __post_init__(self):
        _require(self.schema == self.DOMAIN, "DOMAIN_SCHEMA_UNSUPPORTED")
        _require(type(self.request) is DomainRequest and type(self.status) is str and
            self.status in ("COMPLETE", "INCOMPLETE", "FAILED"), "DOMAIN_RESULT_INVALID")
        _refs(self, "outputs", DomainArtifact, "DOMAIN_RESULT_INVALID")
        _refs(self, "diagnostics", DomainDiagnostic, "DOMAIN_DIAGNOSTIC_INVALID")
        _refs(self, "provenance", CanonicalReference, "DOMAIN_PROVENANCE_INVALID")
        for artifact in self.outputs:
            _require(artifact.descriptor_fingerprint == self.request.descriptor.fingerprint(),
                     "DOMAIN_RESULT_CONTRACT_MISMATCH")
            _require((artifact.platform, artifact.implementation, artifact.operation) ==
                (self.request.descriptor.identity, self.request.descriptor.implementation, self.request.operation),
                "DOMAIN_RESULT_BINDING_MISMATCH")
            _require(artifact.semantic_inputs == self.request.semantic_inputs and artifact.symbols == self.request.symbols,
                     "DOMAIN_RESULT_INPUT_MISMATCH")
        _require(self.status == "COMPLETE" or bool(self.diagnostics), "DOMAIN_RESULT_DIAGNOSTIC_REQUIRED")
        _require(self.status != "FAILED" or not self.outputs, "DOMAIN_RESULT_INVALID")

    def record(self):
        return {"schema": self.schema, "request_fingerprint": self.request.fingerprint(),
            "platform": self.request.descriptor.identity.record(),
            "implementation": self.request.descriptor.implementation.record(), "operation": self.request.operation,
            "semantic_inputs": [r.record() for r in self.request.semantic_inputs],
            "symbols": [r.record() for r in self.request.symbols], "status": self.status,
            "outputs": [r.record() for r in self.outputs], "diagnostics": [r.record() for r in self.diagnostics],
            "provenance": [r.record() for r in self.provenance], "declaration_only": True,
            "semantic_authority": "CANONICAL_AIR", "grants_authority": False,
            "authenticates_provenance": False}
