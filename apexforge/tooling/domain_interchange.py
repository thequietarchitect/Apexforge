"""P15.2 bounded passive interchange of authoritative P15.1 contract objects.

No transport, acquisition, execution or authentication. Result support carries
the exact request required by DomainResult; it does not invent execution evidence.
"""
from dataclasses import dataclass
from hashlib import sha256
import json
import re

from tooling import domain_platform as sdk
from tooling.package_manifest import (PackageCoordinate, PackageContentIdentity,
    ExactVersion, CanonicalReference, SymbolReference, PackageManifestError)

SCHEMA = "apexforge.domain-interchange/v1"
MAX_BYTES = 16 * 1024 * 1024
MAX_DEPTH = 64
MAX_STRING = 512
MAX_LIST = 4096
MAX_NODES = 200000


class DomainInterchangeError(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def _require(ok, code):
    if not ok:
        raise DomainInterchangeError(code)


def _json(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False)


def _object(value, fields):
    _require(type(value) is dict and set(value) == set(fields.split()), "DOMAIN_INTERCHANGE_FIELD_INVALID")
    return value


def _hash(value):
    _require(type(value) is str and re.fullmatch(r"[0-9A-F]{64}", value), "DOMAIN_INTERCHANGE_FINGERPRINT_INVALID")
    return value


def _array(value, constructor):
    _require(type(value) is list and len(value) <= MAX_LIST, "DOMAIN_INTERCHANGE_FIELD_INVALID")
    return tuple(constructor(v) for v in sorted(value, key=_json))


def _normalized(value):
    # Every array in supported v1 objects is an unordered declaration/reference set.
    if type(value) is dict:
        return {k: _normalized(v) for k, v in value.items()}
    if type(value) is list:
        return sorted((_normalized(v) for v in value), key=_json)
    return value


def _checked(record, obj):
    # Includes derived projections and fixed boundary flags; 0 is not false here.
    _require(_json(_normalized(record)) == _json(_normalized(obj.record())),
             "DOMAIN_INTERCHANGE_BINDING_MISMATCH")
    return obj


def _identity(v):
    _object(v, "schema id kind")
    return sdk.DomainPlatformIdentity(v["id"], v["kind"], v["schema"])


def _package(v):
    _object(v, "coordinate content")
    c = _object(v["coordinate"], "schema namespace name version")
    content = _object(v["content"], "domain fingerprint")
    return sdk.ImplementationPackage(PackageCoordinate.from_mapping(c),
        PackageContentIdentity(_hash(content["fingerprint"]), content["domain"]))


def _reference(v):
    _object(v, "schema kind fingerprint")
    return CanonicalReference.from_mapping(v)


def _symbol(v):
    _object(v, "air_fingerprint kind identity module")
    return SymbolReference.from_mapping(v)


def _capability(v):
    _object(v, "domain_capability grants_authority")
    return _checked(v, sdk.DomainCapability(v["domain_capability"]))


def _dependency(v):
    _object(v, "platform implementation contract_version")
    return sdk.DomainDependency(_identity(v["platform"]), _package(v["implementation"]),
                                ExactVersion.parse(v["contract_version"]))


def _descriptor(v):
    _object(v, "schema identity implementation contract_version operations capabilities dependencies provenance semantic_authority")
    _require(v["schema"] == sdk.SCHEMA, "DOMAIN_INTERCHANGE_SCHEMA_UNSUPPORTED")
    obj = sdk.DomainPlatformDescriptor(_identity(v["identity"]), _package(v["implementation"]),
        ExactVersion.parse(v["contract_version"]), _array(v["operations"], lambda x: x),
        _array(v["capabilities"], _capability), _array(v["dependencies"], _dependency),
        _array(v["provenance"], _reference))
    return _checked(v, obj)


def _artifact(v):
    _object(v, "schema kind platform implementation operation digest descriptor_fingerprint semantic_inputs symbols provenance semantic_authority grants_authority")
    return _checked(v, sdk.DomainArtifact(v["kind"], _identity(v["platform"]), _package(v["implementation"]),
        v["operation"], _hash(v["digest"]), _hash(v["descriptor_fingerprint"]),
        _array(v["semantic_inputs"], _reference), _array(v["symbols"], _symbol),
        _array(v["provenance"], _reference), v["schema"]))


def _request(v):
    _object(v, "schema descriptor operation semantic_inputs symbols artifacts capabilities provenance correlation grants_authority")
    return _checked(v, sdk.DomainRequest(_descriptor(v["descriptor"]), v["operation"],
        _array(v["semantic_inputs"], _reference), _array(v["symbols"], _symbol),
        _array(v["artifacts"], _artifact), _array(v["capabilities"], _capability),
        _array(v["provenance"], _reference), v["correlation"], v["schema"]))


def _diagnostic(v):
    _object(v, "code subject")
    return sdk.DomainDiagnostic(v["code"], v["subject"])


def _result(v, support):
    _object(v, "schema request_fingerprint platform implementation operation semantic_inputs symbols status outputs diagnostics provenance declaration_only semantic_authority grants_authority authenticates_provenance")
    request = _request(support)
    _require(_hash(v["request_fingerprint"]) == request.fingerprint(), "DOMAIN_INTERCHANGE_REQUEST_MISMATCH")
    # Admit redundant claims as typed identities before comparing all projections.
    _identity(v["platform"])
    _package(v["implementation"])
    _array(v["semantic_inputs"], _reference)
    _array(v["symbols"], _symbol)
    return _checked(v, sdk.DomainResult(request, v["status"], _array(v["outputs"], _artifact),
        _array(v["diagnostics"], _diagnostic), _array(v["provenance"], _reference), v["schema"]))


def _decode(kind, payload, support):
    try:
        if kind == "result":
            return _result(payload, support)
        _require(support is None, "DOMAIN_INTERCHANGE_FIELD_INVALID")
        if kind == "platform":
            return _descriptor(payload)
        if kind == "request":
            return _request(payload)
        if kind == "artifact":
            return _artifact(payload)
        raise DomainInterchangeError("DOMAIN_INTERCHANGE_KIND_UNSUPPORTED")
    except sdk.DomainContractError as exc:
        raise DomainInterchangeError(exc.code) from exc
    except PackageManifestError as exc:
        raise DomainInterchangeError("DOMAIN_INTERCHANGE_REFERENCE_OR_PACKAGE_INVALID") from exc


def _kind(document):
    if type(document) is sdk.DomainPlatformDescriptor:
        return "platform"
    if type(document) is sdk.DomainRequest:
        return "request"
    if type(document) is sdk.DomainResult:
        return "result"
    if type(document) is sdk.DomainArtifact:
        return "artifact"
    raise DomainInterchangeError("DOMAIN_INTERCHANGE_KIND_UNSUPPORTED")


def _descriptor_fingerprint(document):
    if type(document) is sdk.DomainPlatformDescriptor:
        return document.fingerprint()
    if type(document) is sdk.DomainRequest:
        return document.descriptor.fingerprint()
    if type(document) is sdk.DomainResult:
        return document.request.descriptor.fingerprint()
    return document.descriptor_fingerprint


@dataclass(frozen=True)
class DomainInterchangeEnvelope:
    document: object
    schema: str = SCHEMA

    def __post_init__(self):
        _require(self.schema == SCHEMA, "DOMAIN_INTERCHANGE_SCHEMA_UNSUPPORTED")
        kind = _kind(self.document)
        support = self.document.request.record() if kind == "result" else None
        checked = _decode(kind, self.document.record(), support)
        object.__setattr__(self, "document", checked)
        _limits(self.record())

    @property
    def kind(self):
        return _kind(self.document)

    def record(self):
        return {"schema": self.schema, "kind": self.kind, "payload": self.document.record(),
            "payload_fingerprint": self.document.fingerprint(),
            "descriptor_fingerprint": _descriptor_fingerprint(self.document),
            "support": self.document.request.record() if self.kind == "result" else None}

    def canonical_bytes(self):
        data = _json(self.record()).encode("utf-8")
        _require(len(data) <= MAX_BYTES, "DOMAIN_INTERCHANGE_LIMIT_EXCEEDED")
        return data

    def fingerprint(self):
        return sha256(SCHEMA.encode("utf-8") + b"\0" + self.canonical_bytes()).hexdigest().upper()


def serialize_document(document):
    return DomainInterchangeEnvelope(document).canonical_bytes()


def _limits(root):
    stack = [(root, 0)]
    count = 0
    while stack:
        value, depth = stack.pop()
        count += 1
        _require(count <= MAX_NODES and depth <= MAX_DEPTH, "DOMAIN_INTERCHANGE_LIMIT_EXCEEDED")
        if type(value) is str:
            _require(len(value) <= MAX_STRING, "DOMAIN_INTERCHANGE_LIMIT_EXCEEDED")
            try:
                value.encode("utf-8", "strict")
            except UnicodeError as exc:
                raise DomainInterchangeError("DOMAIN_INTERCHANGE_STRING_INVALID") from exc
        elif type(value) is dict:
            stack.extend((x, depth + 1) for key in sorted(value) for x in (key, value[key]))
        elif type(value) is list:
            _require(len(value) <= MAX_LIST, "DOMAIN_INTERCHANGE_LIMIT_EXCEEDED")
            stack.extend((x, depth + 1) for x in sorted(value, key=_json))
        else:
            _require(value is None or type(value) is bool, "DOMAIN_INTERCHANGE_NUMBER_INVALID")


def parse_document(data):
    """Caller-supplied UTF-8 bytes -> validated immutable envelope and P15.1 object."""
    _require(type(data) is bytes, "DOMAIN_INTERCHANGE_BYTES_REQUIRED")
    _require(len(data) <= MAX_BYTES, "DOMAIN_INTERCHANGE_LIMIT_EXCEEDED")
    try:
        text = data.decode("utf-8", "strict")
        # Bound JSON depth before calling a recursive JSON decoder; quoted delimiters do not count.
        depth = 0
        quoted = escaped = False
        for ch in text:
            if quoted:
                if escaped:
                    escaped = False
                elif ch == "\\":
                    escaped = True
                elif ch == '"':
                    quoted = False
            elif ch == '"':
                quoted = True
            elif ch in "[{":
                depth += 1
                _require(depth <= MAX_DEPTH, "DOMAIN_INTERCHANGE_LIMIT_EXCEEDED")
            elif ch in "]}":
                depth -= 1
        def pairs(items):
            result = {}
            for key, value in items:
                _require(key not in result, "DOMAIN_INTERCHANGE_DUPLICATE_KEY")
                result[key] = value
            return result
        def number(value):
            # All actual v1 numeric values (exact versions) are bounded strings, not JSON numbers.
            raise DomainInterchangeError("DOMAIN_INTERCHANGE_NUMBER_INVALID")
        v = json.loads(text, object_pairs_hook=pairs, parse_int=number, parse_float=number, parse_constant=number)
        _limits(v)
        _object(v, "schema kind payload payload_fingerprint descriptor_fingerprint support")
        _require(v["schema"] == SCHEMA, "DOMAIN_INTERCHANGE_SCHEMA_UNSUPPORTED")
        _require(type(v["kind"]) is str and v["kind"] in ("platform", "request", "result", "artifact"),
                 "DOMAIN_INTERCHANGE_KIND_UNSUPPORTED")
        obj = _decode(v["kind"], v["payload"], v["support"])
        _require(_hash(v["descriptor_fingerprint"]) == _descriptor_fingerprint(obj), "DOMAIN_INTERCHANGE_DESCRIPTOR_MISMATCH")
        _require(_hash(v["payload_fingerprint"]) == obj.fingerprint(), "DOMAIN_INTERCHANGE_PAYLOAD_FINGERPRINT_MISMATCH")
        return DomainInterchangeEnvelope(obj)
    except (UnicodeError, json.JSONDecodeError, RecursionError) as exc:
        raise DomainInterchangeError("DOMAIN_INTERCHANGE_MALFORMED") from exc
