"""Offline external interaction contracts. Admission is neither trust nor execution."""
from dataclasses import dataclass
from hashlib import sha256
import re

from tooling import domain_platform as sdk
from tooling.package_manifest import ExactVersion, CanonicalReference

PLATFORM = sdk.DomainPlatformIdentity("apexforge.external-adapter", "external-adapter")
MAX_ITEMS = 4096
MAX_BYTES = 1048576


class ExternalContractError(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def require(condition, code):
    if not condition:
        raise ExternalContractError(code)


def name(value):
    try:
        sdk._name(value, "EXTERNAL_IDENTITY_INVALID")
    except sdk.DomainContractError as error:
        raise ExternalContractError("EXTERNAL_IDENTITY_INVALID") from error


def fingerprint(value):
    require(type(value) is str and re.fullmatch(r"[0-9A-F]{64}", value) is not None,
            "EXTERNAL_FINGERPRINT_INVALID")


def collection(owner, field, cls):
    values = getattr(owner, field)
    require(type(values) is tuple and len(values) <= MAX_ITEMS and
            all(type(v) is cls for v in values), "EXTERNAL_COLLECTION_INVALID")
    records = [v.canonical_json() if isinstance(v, sdk.CanonicalModel) else sdk._json(v.record()) for v in values]
    require(len(set(records)) == len(records), "EXTERNAL_COLLECTION_DUPLICATE")
    object.__setattr__(owner, field, tuple(v for _, v in sorted(zip(records, values), key=lambda pair: pair[0])))


def provenance(owner):
    collection(owner, "provenance", CanonicalReference)


@dataclass(frozen=True)
class ExternalProviderIdentity(sdk.CanonicalModel):
    identifier: str
    DOMAIN = "apexforge.external-provider/v1"
    def __post_init__(self):
        name(self.identifier)
    def record(self):
        return {"schema": self.DOMAIN, "id": self.identifier}


@dataclass(frozen=True)
class ExternalAdapterIdentity(sdk.CanonicalModel):
    identifier: str
    DOMAIN = "apexforge.external-adapter-identity/v1"
    def __post_init__(self):
        name(self.identifier)
    def record(self):
        return {"schema": self.DOMAIN, "id": self.identifier}


@dataclass(frozen=True)
class ExternalOperation(sdk.CanonicalModel):
    identifier: str
    idempotent: bool = False
    DOMAIN = "apexforge.external-operation/v1"
    def __post_init__(self):
        name(self.identifier)
        require(type(self.idempotent) is bool, "EXTERNAL_OPERATION_INVALID")
    def record(self):
        return {"id": self.identifier, "idempotent_declared": self.idempotent}


def external_platform(manifest):
    return sdk.DomainPlatformDescriptor(PLATFORM, sdk.ImplementationPackage.from_manifest(manifest),
        ExactVersion(1, 0, 0), ("external.request.describe", "external.response.describe"))


@dataclass(frozen=True)
class CredentialReference(sdk.CanonicalModel):
    identifier: str
    kind: str
    provider: ExternalProviderIdentity
    scopes: tuple = ()
    DOMAIN = "apexforge.external-credential-reference/v1"
    def __post_init__(self):
        name(self.identifier)
        require(type(self.kind) is str and self.kind in ("api-key-reference", "token-reference"),
                "EXTERNAL_CREDENTIAL_KIND_INVALID")
        require(type(self.provider) is ExternalProviderIdentity, "EXTERNAL_PROVIDER_INVALID")
        require(type(self.scopes) is tuple and len(self.scopes) <= MAX_ITEMS, "EXTERNAL_SCOPE_INVALID")
        for scope in self.scopes:
            name(scope)
        require(len(set(self.scopes)) == len(self.scopes), "EXTERNAL_COLLECTION_DUPLICATE")
        object.__setattr__(self, "scopes", tuple(sorted(self.scopes)))
    def record(self):
        return {"schema": self.DOMAIN, "id": self.identifier, "kind": self.kind,
                "provider": self.provider.record(), "scopes_declared": list(self.scopes)}


@dataclass(frozen=True)
class ExternalAdapterDescriptor(sdk.CanonicalModel):
    identity: ExternalAdapterIdentity
    provider: ExternalProviderIdentity
    platform: sdk.DomainPlatformDescriptor
    operations: tuple
    capabilities: tuple = ()
    credential_kinds: tuple = ()
    provenance: tuple = ()
    schema: str = "apexforge.external-adapter/v1"
    DOMAIN = "apexforge.external-adapter/v1"
    def __post_init__(self):
        require(type(self.schema) is str and self.schema == self.DOMAIN, "EXTERNAL_SCHEMA_UNSUPPORTED")
        require(type(self.identity) is ExternalAdapterIdentity and type(self.provider) is ExternalProviderIdentity,
                "EXTERNAL_IDENTITY_INVALID")
        require(type(self.platform) is sdk.DomainPlatformDescriptor and self.platform.identity == PLATFORM and
                self.platform.contract_version == ExactVersion(1, 0, 0), "EXTERNAL_PLATFORM_INVALID")
        collection(self, "operations", ExternalOperation)
        require(bool(self.operations) and len({o.identifier for o in self.operations}) == len(self.operations),
                "EXTERNAL_OPERATION_INVALID")
        collection(self, "capabilities", sdk.DomainCapability)
        require(type(self.credential_kinds) is tuple and len(self.credential_kinds) <= 2 and
                all(type(k) is str and k in ("api-key-reference", "token-reference") for k in self.credential_kinds),
                "EXTERNAL_CREDENTIAL_KIND_INVALID")
        require(len(set(self.credential_kinds)) == len(self.credential_kinds), "EXTERNAL_COLLECTION_DUPLICATE")
        object.__setattr__(self, "credential_kinds", tuple(sorted(self.credential_kinds)))
        provenance(self)
    def record(self):
        return {"schema": self.schema, "identity": self.identity.record(), "provider": self.provider.record(),
                "platform": self.platform.record(), "operations": [o.record() for o in self.operations],
                "capabilities": [c.record() for c in self.capabilities], "credential_kinds": list(self.credential_kinds),
                "request_schema": ExternalRequest.DOMAIN, "response_schema": ExternalResponse.DOMAIN,
                "provenance": [r.record() for r in self.provenance], "authority_granted": False}


@dataclass(frozen=True)
class ExternalPayload(sdk.CanonicalModel):
    digest: str
    data: bytes | None = None
    DOMAIN = "apexforge.external-payload/v1"
    def __post_init__(self):
        fingerprint(self.digest)
        require(self.data is None or type(self.data) is bytes and len(self.data) <= MAX_BYTES,
                "EXTERNAL_BYTES_INVALID")
        if self.data is not None:
            require(sha256(self.data).hexdigest().upper() == self.digest, "EXTERNAL_BYTES_INTEGRITY_FAILED")
    def record(self):
        return {"schema": self.DOMAIN, "digest": self.digest,
                "bytes_supplied": self.data is not None, "interpreted": False}


@dataclass(frozen=True)
class ExternalRequest(sdk.CanonicalModel):
    descriptor: ExternalAdapterDescriptor
    operation: str
    correlation: str
    inputs: tuple = ()
    capabilities: tuple = ()
    credential: CredentialReference | None = None
    payload: ExternalPayload | None = None
    provenance: tuple = ()
    schema: str = "apexforge.external-request/v1"
    DOMAIN = "apexforge.external-request/v1"
    def __post_init__(self):
        require(type(self.schema) is str and self.schema == self.DOMAIN, "EXTERNAL_SCHEMA_UNSUPPORTED")
        require(type(self.descriptor) is ExternalAdapterDescriptor, "EXTERNAL_DESCRIPTOR_INVALID")
        name(self.operation)
        name(self.correlation)
        require(self.operation in tuple(o.identifier for o in self.descriptor.operations), "EXTERNAL_OPERATION_UNDECLARED")
        collection(self, "inputs", CanonicalReference)
        collection(self, "capabilities", sdk.DomainCapability)
        require(self.capabilities == self.descriptor.capabilities, "EXTERNAL_CAPABILITY_REQUIREMENT_MISMATCH")
        require(self.credential is None or type(self.credential) is CredentialReference, "EXTERNAL_CREDENTIAL_INVALID")
        if self.credential is not None:
            require(self.credential.provider == self.descriptor.provider and
                    self.credential.kind in self.descriptor.credential_kinds, "EXTERNAL_CREDENTIAL_BINDING_INVALID")
        require(not self.descriptor.credential_kinds or self.credential is not None, "EXTERNAL_CREDENTIAL_REFERENCE_MISSING")
        require(self.payload is None or type(self.payload) is ExternalPayload, "EXTERNAL_PAYLOAD_INVALID")
        provenance(self)
    def record(self):
        return {"schema": self.schema, "descriptor": self.descriptor.fingerprint(),
                "adapter": self.descriptor.identity.record(), "provider": self.descriptor.provider.record(),
                "implementation": self.descriptor.platform.implementation.record(), "operation": self.operation,
                "correlation": self.correlation, "inputs": [r.record() for r in self.inputs],
                "capabilities_required": [c.record() for c in self.capabilities],
                "credential": None if self.credential is None else self.credential.record(),
                "payload": None if self.payload is None else self.payload.record(),
                "provenance": [r.record() for r in self.provenance], "execution_permission": False}


@dataclass(frozen=True)
class ExternalResponse(sdk.CanonicalModel):
    request: ExternalRequest
    request_fingerprint: str
    provider: ExternalProviderIdentity
    correlation: str
    status: str
    outputs: tuple = ()
    diagnostics: tuple = ()
    payload: ExternalPayload | None = None
    provenance: tuple = ()
    schema: str = "apexforge.external-response/v1"
    DOMAIN = "apexforge.external-response/v1"
    def __post_init__(self):
        require(type(self.schema) is str and self.schema == self.DOMAIN, "EXTERNAL_SCHEMA_UNSUPPORTED")
        require(type(self.request) is ExternalRequest and type(self.provider) is ExternalProviderIdentity,
                "EXTERNAL_RESPONSE_INVALID")
        fingerprint(self.request_fingerprint)
        name(self.correlation)
        require(self.request_fingerprint == self.request.fingerprint() and
                self.provider == self.request.descriptor.provider and self.correlation == self.request.correlation,
                "EXTERNAL_RESPONSE_BINDING_MISMATCH")
        require(type(self.status) is str and self.status in
                ("REPORTED_SUCCESS", "REPORTED_FAILURE", "REPORTED_REJECTED", "REPORTED_PENDING"),
                "EXTERNAL_RESPONSE_STATUS_INVALID")
        collection(self, "outputs", CanonicalReference)
        require(type(self.diagnostics) is tuple and len(self.diagnostics) <= MAX_ITEMS, "EXTERNAL_DIAGNOSTIC_INVALID")
        for code in self.diagnostics:
            require(type(code) is str and code in ("PROVIDER_REPORTED_FAILURE", "PROVIDER_REPORTED_REJECTION",
                    "PROVIDER_REPORTED_PENDING", "EVIDENCE_MISSING"), "EXTERNAL_DIAGNOSTIC_INVALID")
        object.__setattr__(self, "diagnostics", tuple(sorted(set(self.diagnostics))))
        require(self.payload is None or type(self.payload) is ExternalPayload, "EXTERNAL_PAYLOAD_INVALID")
        provenance(self)
    def record(self):
        return {"schema": self.schema, "request": self.request_fingerprint,
                "adapter": self.request.descriptor.identity.record(), "provider": self.provider.record(),
                "correlation": self.correlation, "status": self.status, "outputs": [r.record() for r in self.outputs],
                "diagnostics": list(self.diagnostics), "payload": None if self.payload is None else self.payload.record(),
                "provenance": [r.record() for r in self.provenance], "authenticated": False,
                "evidence": "EXTERNALLY_SUPPLIED", "semantic_authority": "CANONICAL_AIR"}


def admit_response(request, response):
    """Offline admission only; performs no transport, authentication or dispatch."""
    require(type(request) is ExternalRequest and type(response) is ExternalResponse, "EXTERNAL_RESPONSE_INVALID")
    require(response.request_fingerprint == request.fingerprint() and response.request == request,
            "EXTERNAL_RESPONSE_BINDING_MISMATCH")
    return response


def retry_request(request):
    """Exact logical retry identity; no retry is performed."""
    require(type(request) is ExternalRequest, "EXTERNAL_REQUEST_INVALID")
    return request


def domain_artifact(record):
    require(type(record) in (ExternalAdapterDescriptor, ExternalRequest, ExternalResponse), "EXTERNAL_RECORD_INVALID")
    descriptor = record if type(record) is ExternalAdapterDescriptor else (
        record.descriptor if type(record) is ExternalRequest else record.request.descriptor)
    operation = "external.response.describe" if type(record) is ExternalResponse else "external.request.describe"
    return sdk.DomainArtifact.from_bytes(descriptor.platform, operation, "external-reference",
        record.canonical_json().encode("utf-8"), provenance=record.provenance)
