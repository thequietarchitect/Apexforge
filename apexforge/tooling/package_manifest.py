"""P14.1 immutable package declarations; no resolution, IO, trust or execution.

The P11 project/rich-document descriptor remains a separate frozen contract.
All fingerprints describe supplied declarations, not verified payload contents.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import re

from language.identities import ProjectDeclaredIdentity
from rich_documents.model import PackageTier

SCHEMA = "apexforge.package/v1"
FINGERPRINT_DOMAIN = "apexforge.package-manifest-identity/v1"
MAX_JSON_BYTES = 1048576
_IDENTIFIER = r"[A-Za-z_][A-Za-z0-9_]*"
_QUALIFIED = _IDENTIFIER + r"(?:\." + _IDENTIFIER + r")*"
_REFERENCE_KINDS = frozenset(("source", "air", "source-mapping", "native-mapping",
    "artifact", "build-receipt", "provenance-scope", "result-association"))
_METADATA_KEYS = frozenset(("title", "description", "authors", "license",
    "homepage", "documentation"))


class PackageManifestError(ValueError):
    """Fixed diagnostic codes; untrusted values are not echoed in messages."""
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def _require(ok, code):
    if not ok:
        raise PackageManifestError(code)


def _match(value, pattern, code, limit=256):
    _require(type(value) is str and len(value) <= limit and
             re.fullmatch(pattern, value, flags=re.ASCII) is not None, code)


def _hash(value):
    _match(value, r"[0-9A-F]{64}", "PACKAGE_HASH_INVALID", 64)


def _json(value):
    return json.dumps(value, ensure_ascii=True, sort_keys=True,
                      separators=(",", ":"), allow_nan=False)


def _items(value, item_type, code):
    _require(type(value) is tuple and all(type(x) is item_type for x in value), code)


def _ordered(value, key, code):
    keys = tuple(key(x) for x in value)
    _require(len(set(keys)) == len(keys), code)
    return tuple(sorted(value, key=key))


def _object(value, required, optional=()):
    _require(type(value) is dict and all(type(k) is str for k in value),
             "MANIFEST_OBJECT_REQUIRED")
    _require(set(required) <= set(value), "MANIFEST_FIELD_MISSING")
    _require(set(value) <= set(required) | set(optional), "MANIFEST_FIELD_UNKNOWN")
    return value


def _array(value):
    _require(type(value) is list, "MANIFEST_ARRAY_REQUIRED")
    return value


@dataclass(frozen=True)
class ExactVersion:
    """Bounded numeric release triple, not a range or precedence algorithm."""
    major: int
    minor: int
    patch: int

    def __post_init__(self):
        _require(all(type(x) is int and 0 <= x <= 2147483647
                     for x in (self.major, self.minor, self.patch)), "PACKAGE_VERSION_INVALID")

    @classmethod
    def parse(cls, text):
        _match(text, r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)",
               "PACKAGE_VERSION_INVALID", 32)
        return cls(*(int(x) for x in text.split(".")))

    def text(self):
        return "{}.{}.{}".format(self.major, self.minor, self.patch)


@dataclass(frozen=True)
class PackageCoordinate:
    namespace: str
    name: str
    version: ExactVersion
    schema: str = SCHEMA

    def __post_init__(self):
        _require(type(self.schema) is str and self.schema == SCHEMA, "MANIFEST_SCHEMA_UNKNOWN")
        _match(self.namespace, r"[a-z_][a-z0-9_]{0,63}(?:\.[a-z_][a-z0-9_]{0,63})*",
               "PACKAGE_NAMESPACE_INVALID", 255)
        _match(self.name, r"[a-z][a-z0-9]*(?:[-_][a-z0-9]+)*", "PACKAGE_NAME_INVALID", 64)
        _require(type(self.version) is ExactVersion, "PACKAGE_VERSION_INVALID")

    def record(self):
        return {"schema": self.schema, "namespace": self.namespace,
                "name": self.name, "version": self.version.text()}

    @classmethod
    def from_mapping(cls, value):
        v = _object(value, ("namespace", "name", "version"), ("schema",))
        return cls(v["namespace"], v["name"], ExactVersion.parse(v["version"]),
                   v.get("schema", SCHEMA))


@dataclass(frozen=True)
class PackageContentIdentity:
    fingerprint: str
    domain: str = FINGERPRINT_DOMAIN

    def __post_init__(self):
        _hash(self.fingerprint)
        _require(type(self.domain) is str and self.domain == FINGERPRINT_DOMAIN,
                 "PACKAGE_IDENTITY_DOMAIN_INVALID")

    def record(self):
        return {"domain": self.domain, "fingerprint": self.fingerprint}


@dataclass(frozen=True)
class PackagePath:
    """Portable ASCII logical member name, never a host filesystem handle."""
    value: str

    def __post_init__(self):
        _require(type(self.value) is str and 0 < len(self.value) <= 512,
                 "PACKAGE_PATH_INVALID")
        for part in self.value.split("/"):
            _match(part, r"[A-Za-z0-9_-][A-Za-z0-9_.-]*", "PACKAGE_PATH_INVALID", 128)
            _require(not part.endswith("."), "PACKAGE_PATH_INVALID")
            _require(part.split(".")[0].upper() not in
                     {"CON", "PRN", "AUX", "NUL", "COM1", "COM2", "COM3", "COM4", "COM5",
                      "COM6", "COM7", "COM8", "COM9", "LPT1", "LPT2", "LPT3", "LPT4",
                      "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"}, "PACKAGE_PATH_INVALID")


@dataclass(frozen=True)
class CanonicalReference:
    """Passive schema/kind/producer fingerprint. No trust or existence assertion."""
    schema: str
    kind: str
    fingerprint: str

    def __post_init__(self):
        _match(self.schema, r"apexforge\.[a-z0-9][a-z0-9.-]*/v[1-9][0-9]*",
               "PACKAGE_REFERENCE_INVALID")
        _require(type(self.kind) is str and self.kind in _REFERENCE_KINDS,
                 "PACKAGE_REFERENCE_INVALID")
        _hash(self.fingerprint)

    def record(self):
        return {"schema": self.schema, "kind": self.kind, "fingerprint": self.fingerprint}

    @classmethod
    def from_mapping(cls, value):
        v = _object(value, ("schema", "kind", "fingerprint"))
        return cls(v["schema"], v["kind"], v["fingerprint"])


@dataclass(frozen=True)
class ContentDescriptor:
    path: PackagePath
    digest: str
    kind: str
    reference: CanonicalReference | None = None

    def __post_init__(self):
        _require(type(self.path) is PackagePath, "PACKAGE_PATH_INVALID")
        _hash(self.digest)
        _require(type(self.kind) is str and self.kind in ("source", "document", "artifact", "data"),
                 "PACKAGE_CONTENT_KIND_INVALID")
        _require(self.reference is None or type(self.reference) is CanonicalReference,
                 "PACKAGE_REFERENCE_INVALID")
        if self.kind == "document":
            _require(self.path.value.endswith(".apexdoc"), "PACKAGE_DOCUMENT_INVALID")

    def record(self):
        return {"path": self.path.value, "digest": self.digest, "kind": self.kind,
                "reference": None if self.reference is None else self.reference.record()}

    @classmethod
    def from_mapping(cls, value):
        v = _object(value, ("path", "digest", "kind"), ("reference",))
        ref = v.get("reference")
        return cls(PackagePath(v["path"]), v["digest"], v["kind"],
                   None if ref is None else CanonicalReference.from_mapping(ref))


@dataclass(frozen=True)
class SymbolReference:
    """Exact existing directive/function ID, scoped by a supplied AIR fingerprint."""
    air_fingerprint: str
    kind: str
    identity: str
    module: str | None = None

    def __post_init__(self):
        _hash(self.air_fingerprint)
        _require(type(self.kind) is str and self.kind in ("directive", "function"),
                 "PACKAGE_SYMBOL_INVALID")
        _match(self.identity, self.kind + ":" + _IDENTIFIER, "PACKAGE_SYMBOL_INVALID")
        if self.module is not None:
            _match(self.module, _QUALIFIED, "PACKAGE_SYMBOL_INVALID")

    @classmethod
    def from_declared(cls, declaration, air_fingerprint):
        _require(type(declaration) is ProjectDeclaredIdentity, "PACKAGE_SYMBOL_INVALID")
        return cls(air_fingerprint, declaration.kind, declaration.current_air_id,
                   declaration.module_name)

    def record(self):
        return {"air_fingerprint": self.air_fingerprint, "kind": self.kind,
                "identity": self.identity, "module": self.module}

    @classmethod
    def from_mapping(cls, value):
        v = _object(value, ("air_fingerprint", "kind", "identity"), ("module",))
        return cls(v["air_fingerprint"], v["kind"], v["identity"], v.get("module"))


@dataclass(frozen=True)
class PackageManifest:
    coordinate: PackageCoordinate
    content: tuple[ContentDescriptor, ...] = ()
    tier: PackageTier | None = None
    documents: tuple[PackagePath, ...] = ()
    dependencies: tuple[PackageCoordinate, ...] = ()
    exports: tuple[SymbolReference, ...] = ()
    entrypoints: tuple[SymbolReference, ...] = ()
    exported_capabilities: tuple[str, ...] = ()
    required_capabilities: tuple[str, ...] = ()
    provenance: tuple[CanonicalReference, ...] = ()
    metadata: tuple[tuple[str, str], ...] = ()

    def __post_init__(self):
        _require(type(self.coordinate) is PackageCoordinate, "PACKAGE_COORDINATE_INVALID")
        _require(self.tier is None or type(self.tier) is PackageTier, "PACKAGE_TIER_INVALID")
        for field, item_type in (("content", ContentDescriptor), ("documents", PackagePath),
                ("dependencies", PackageCoordinate), ("exports", SymbolReference),
                ("entrypoints", SymbolReference), ("provenance", CanonicalReference)):
            _items(getattr(self, field), item_type, "MANIFEST_IMMUTABLE_RECORD_REQUIRED")
        object.__setattr__(self, "content", _ordered(self.content,
                           lambda x: x.path.value.casefold(), "PACKAGE_PATH_DUPLICATE"))
        member_names = {x.path.value.casefold() for x in self.content}
        for member in self.content:
            parts = member.path.value.casefold().split("/")
            _require(not any("/".join(parts[:i]) in member_names for i in range(1, len(parts))),
                     "PACKAGE_PATH_CONFLICT")
        object.__setattr__(self, "dependencies", _ordered(self.dependencies,
                           lambda x: (x.namespace, x.name), "PACKAGE_DEPENDENCY_CONFLICT"))
        for field in ("exports", "entrypoints"):
            object.__setattr__(self, field, _ordered(getattr(self, field),
                lambda x: (x.module or "", x.kind, x.identity), "PACKAGE_SYMBOL_DUPLICATE"))
        _require(all(x.kind == "directive" for x in self.entrypoints), "PACKAGE_ENTRYPOINT_INVALID")
        document_paths = tuple(x.value for x in self.documents)
        _require(len(set(document_paths)) == len(document_paths), "PACKAGE_DOCUMENT_DUPLICATE")
        content_documents = {x.path.value for x in self.content if x.kind == "document"}
        _require(set(document_paths) == content_documents, "PACKAGE_DOCUMENT_BOUNDARY_MISMATCH")
        for field in ("exported_capabilities", "required_capabilities"):
            value = getattr(self, field)
            _items(value, str, "PACKAGE_CAPABILITY_INVALID")
            for item in value:
                _match(item, _QUALIFIED, "PACKAGE_CAPABILITY_INVALID")
            object.__setattr__(self, field, _ordered(value, lambda x: x, "PACKAGE_CAPABILITY_DUPLICATE"))
        object.__setattr__(self, "provenance", _ordered(self.provenance,
                           lambda x: _json(x.record()), "PACKAGE_REFERENCE_DUPLICATE"))
        _require(type(self.metadata) is tuple, "PACKAGE_METADATA_INVALID")
        for pair in self.metadata:
            _require(type(pair) is tuple and len(pair) == 2 and type(pair[0]) is str and
                     pair[0] in _METADATA_KEYS and type(pair[1]) is str and
                     len(pair[1]) <= 4096 and not any(ord(c) < 32 or ord(c) == 127
                     or 0xD800 <= ord(c) <= 0xDFFF for c in pair[1]), "PACKAGE_METADATA_INVALID")
        object.__setattr__(self, "metadata", _ordered(self.metadata,
                           lambda x: x[0], "PACKAGE_METADATA_DUPLICATE"))

    def canonical_record(self):
        record = self.coordinate.record()
        record.update({"content": [x.record() for x in self.content],
            "tier": None if self.tier is None else self.tier.value,
            "documents": [x.value for x in self.documents],
            "dependencies": [x.record() for x in self.dependencies],
            "exports": [x.record() for x in self.exports],
            "entrypoints": [x.record() for x in self.entrypoints],
            "capabilities": {"exports": list(self.exported_capabilities),
                             "requires": list(self.required_capabilities)},
            "provenance": [x.record() for x in self.provenance]})
        return record

    def canonical_json(self):
        """Identity preimage JSON; presentation metadata is deliberately excluded."""
        return _json(self.canonical_record())

    def content_identity(self):
        preimage = (FINGERPRINT_DOMAIN + "\0" + self.canonical_json()).encode("utf-8")
        return PackageContentIdentity(sha256(preimage).hexdigest().upper())

    def to_mapping(self):
        record = self.canonical_record()
        record["metadata"] = dict(self.metadata)
        return record

    def to_json(self):
        """Deterministic interchange JSON preserving non-identity metadata."""
        return _json(self.to_mapping())

    @classmethod
    def from_mapping(cls, value):
        v = _object(value, ("schema", "namespace", "name", "version", "content"),
            ("tier", "documents", "dependencies", "exports", "entrypoints", "capabilities",
             "provenance", "metadata"))
        coordinate = PackageCoordinate.from_mapping({k: v[k] for k in
                                                    ("schema", "namespace", "name", "version")})
        tier = v.get("tier")
        _require(tier is None or type(tier) is str and tier in tuple(x.value for x in PackageTier),
                 "PACKAGE_TIER_INVALID")
        caps = _object(v.get("capabilities", {}), (), ("exports", "requires"))
        metadata = v.get("metadata", {})
        _require(type(metadata) is dict and all(type(k) is str for k in metadata),
                 "PACKAGE_METADATA_INVALID")
        return cls(coordinate,
            content=tuple(ContentDescriptor.from_mapping(x) for x in _array(v["content"])),
            tier=None if tier is None else PackageTier(tier),
            documents=tuple(PackagePath(x) for x in _array(v.get("documents", []))),
            dependencies=tuple(PackageCoordinate.from_mapping(x) for x in _array(v.get("dependencies", []))),
            exports=tuple(SymbolReference.from_mapping(x) for x in _array(v.get("exports", []))),
            entrypoints=tuple(SymbolReference.from_mapping(x) for x in _array(v.get("entrypoints", []))),
            exported_capabilities=tuple(_array(caps.get("exports", []))),
            required_capabilities=tuple(_array(caps.get("requires", []))),
            provenance=tuple(CanonicalReference.from_mapping(x) for x in _array(v.get("provenance", []))),
            metadata=tuple(metadata.items()))


def parse_manifest(text):
    """Parse caller-supplied JSON only; duplicate keys and unknown fields reject."""
    _require(type(text) is str, "MANIFEST_JSON_INVALID")
    def pairs(items):
        result = {}
        for key, value in items:
            _require(key not in result, "MANIFEST_JSON_DUPLICATE_KEY")
            result[key] = value
        return result
    def reject_constant(_):
        raise PackageManifestError("MANIFEST_JSON_INVALID")
    def bounded_integer(raw):
        _require(len(raw.lstrip("-")) <= 10, "MANIFEST_JSON_INVALID")
        return int(raw)
    try:
        _require(len(text.encode("utf-8")) <= MAX_JSON_BYTES, "MANIFEST_JSON_TOO_LARGE")
        value = json.loads(text, object_pairs_hook=pairs, parse_constant=reject_constant,
                           parse_int=bounded_integer)
        return PackageManifest.from_mapping(value)
    except (UnicodeError, json.JSONDecodeError, RecursionError) as exc:
        raise PackageManifestError("MANIFEST_JSON_INVALID") from exc
