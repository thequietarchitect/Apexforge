"""P14.12 evidence composition only; structural continuity is not authentication."""
from dataclasses import dataclass, fields
from hashlib import sha256
import json
from types import MappingProxyType

from tooling.package_manifest import PackageManifest, PackageContentIdentity, CanonicalReference, PackagePath
from tooling.package_solver import ResolutionGraph
from tooling.package_lock import PackageLock
from tooling.package_registry import RegistryRecord, RegistryCatalog
from tooling.package_publishing import (PublicationReceipt, PublicationPolicy, PublisherPrincipal,
    PublicationGrant, registry_state_fingerprint)
from tooling.package_trust import (ContentMember, SignatureEnvelope, TrustPolicy, verify_integrity,
    verify_package, payload_fingerprint)
from tooling.package_cache import CacheEntry
from tooling.package_compatibility import CompatibilityReport
from tooling.package_artifacts import (ArtifactBundle, ArtifactDescriptor, ArtifactPayload, describe_managed,
    describe_native, _parse_record, PROFILE)

SCHEMA = "apexforge.package-supply-chain-validation/v1"
REQUIREMENTS = MappingProxyType({
    "PACKAGE_INTEGRITY": ("members",),
    "LOCK_RESTORE_CHAIN": ("members", "lock"),
    "REGISTRY_PUBLICATION_CHAIN": ("members", "registry_record", "registry", "publication", "before", "after", "publication_policy"),
    "PACKAGE_ARTIFACT_CHAIN": ("members", "artifacts", "builds", "air"),
    "FULL_STRUCTURAL_SUPPLY_CHAIN": ("members", "lock", "registry_record", "registry", "publication", "before", "after",
                                      "publication_policy", "artifacts", "builds", "air"),
})


def _json(record):
    return json.dumps(record, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False)


def _digest(data):
    return sha256(data).hexdigest().upper()


def _fingerprint(domain, record):
    return _digest((domain + "\0" + _json(record)).encode("utf-8"))


@dataclass(frozen=True)
class ValidationProfile:
    name: str = "PACKAGE_INTEGRITY"
    require_authentication: bool = False

    def __post_init__(self):
        if type(self.name) is not str or self.name not in REQUIREMENTS or type(self.require_authentication) is not bool:
            raise ValueError("SUPPLY_CHAIN_PROFILE_INVALID")


@dataclass(frozen=True)
class SuppliedBuild:
    path: PackagePath
    data: bytes
    fingerprint: str
    source_bytes: bytes | None = None

    def __post_init__(self):
        if type(self.path) is not PackagePath or type(self.data) is not bytes or (
            self.source_bytes is not None and type(self.source_bytes) is not bytes):
            raise ValueError("SUPPLY_CHAIN_BUILD_INPUT_INVALID")
        PackageContentIdentity(self.fingerprint)  # Hash syntax only, not package identity.


@dataclass(frozen=True)
class SupplyChainEvidence:
    manifest: PackageManifest
    members: tuple[ContentMember, ...] | None = None
    expected_content: PackageContentIdentity | None = None
    graph: ResolutionGraph | None = None
    lock: PackageLock | None = None
    registry_record: RegistryRecord | None = None
    registry: RegistryCatalog | None = None
    publication: PublicationReceipt | None = None
    before: RegistryCatalog | None = None
    after: RegistryCatalog | None = None
    publication_policy: PublicationPolicy | None = None
    artifacts: ArtifactBundle | None = None
    builds: tuple[SuppliedBuild, ...] = ()
    air: tuple[CanonicalReference, ...] = ()
    signature: SignatureEnvelope | None = None
    public_key: bytes | None = None
    trust_policy: TrustPolicy | None = None
    cache_entry: CacheEntry | None = None
    compatibility: CompatibilityReport | None = None
    sources: tuple[ContentMember, ...] = ()


@dataclass(frozen=True)
class SupplyChainReport:
    canonical_json: str

    def record(self):
        return json.loads(self.canonical_json)

    @property
    def status(self):
        return self.record()["status"]

    def fingerprint(self):
        return _fingerprint(SCHEMA, self.record())


def validate_supply_chain(evidence, profile=ValidationProfile()):
    """Validate every supplied association; acquire no absent evidence or runtime effect."""
    if type(evidence) is not SupplyChainEvidence or type(evidence.manifest) is not PackageManifest:
        raise ValueError("SUPPLY_CHAIN_INPUT_INVALID")
    if type(profile) is not ValidationProfile:
        raise ValueError("SUPPLY_CHAIN_PROFILE_INVALID")
    m = evidence.manifest
    identity = m.content_identity()
    nodes, edges, diagnostics, checks = {}, set(), set(), set()
    def node(kind, category, record):
        content = _json(record)
        key = _fingerprint("apexforge.supply-chain-evidence-node/v1", {"kind": kind, "record": record})
        nodes[key] = {"identity": key, "kind": kind, "category": category, "record": json.loads(content)}
        return key
    def issue(code, status="INVALID", subject="package"):
        diagnostics.add((status, code, subject))
    def check(claim, ok, source, target, code):
        status = "VALID" if ok else "INVALID"
        edges.add((claim, source, target, status))
        checks.add((claim, status, target))
        if not ok:
            issue(code, subject=target)
    def missing(subject, required=False):
        issue("SUPPLY_CHAIN_REQUIRED_EVIDENCE_MISSING" if required else "MISSING_OPTIONAL_EVIDENCE",
              "INCOMPLETE" if required else "NOT_APPLICABLE", subject)
    package_node = node("PACKAGE_MANIFEST", "AUTHORITATIVE_IDENTITY_EVIDENCE", m.canonical_record())
    content_node = node("PACKAGE_CONTENT_IDENTITY", "AUTHORITATIVE_IDENTITY_EVIDENCE", identity.record())
    check("MANIFEST_BINDS_CONTENT", True, package_node, content_node, "SUPPLY_CHAIN_PACKAGE_IDENTITY_MISMATCH")
    try:
        PackageManifest.from_mapping(m.to_mapping())
    except ValueError:
        issue("SUPPLY_CHAIN_PACKAGE_IDENTITY_MISMATCH")
    if evidence.expected_content is not None and evidence.expected_content != identity:
        issue("SUPPLY_CHAIN_PACKAGE_IDENTITY_MISMATCH")
    for name in REQUIREMENTS[profile.name]:
        value = getattr(evidence, name)
        if value is None or name in ("builds", "air") and not value:
            missing(name, True)
    for name in ("lock", "registry_record", "publication", "artifacts", "cache_entry", "signature"):
        if getattr(evidence, name) is None and name not in REQUIREMENTS[profile.name]:
            missing(name)
    integrity_valid = False
    if evidence.members is not None:
        try:
            integrity = verify_integrity(m, evidence.members)
            integrity_valid = integrity.valid
            n = node("MEMBER_INTEGRITY", "INTEGRITY_EVIDENCE", integrity.record())
            check("MEMBERS_MATCH_MANIFEST", integrity.valid, n, content_node, "SUPPLY_CHAIN_CONTENT_INTEGRITY_FAILED")
        except (ValueError, TypeError):
            issue("SUPPLY_CHAIN_CONTENT_INTEGRITY_FAILED")
    for name in ("graph", "lock"):
        value = getattr(evidence, name)
        if value is None:
            continue
        try:
            if name == "lock":
                if type(value) is not PackageLock:
                    raise ValueError()
                graph = value.resolution
                n = node("LOCK", "AUTHORITATIVE_IDENTITY_EVIDENCE", {"fingerprint": value.fingerprint()})
            else:
                if type(value) is not ResolutionGraph:
                    raise ValueError()
                graph = value
                n = node("RESOLUTION_GRAPH", "AUTHORITATIVE_IDENTITY_EVIDENCE", {"fingerprint": value.fingerprint()})
            check("LOCK_BINDS_PACKAGE_CONTENT" if name == "lock" else "GRAPH_BINDS_PACKAGE_CONTENT",
                any(p.coordinate == m.coordinate and p.content_identity == identity for p in graph.nodes),
                n, content_node, "SUPPLY_CHAIN_LOCK_MISMATCH")
            for p in graph.nodes:
                pn = node("RESOLVED_PACKAGE", "AUTHORITATIVE_IDENTITY_EVIDENCE", p.reference())
                edges.add(("GRAPH_CONTAINS_PACKAGE", n, pn, "VALID"))
            indexed = {p.coordinate: node("RESOLVED_PACKAGE", "AUTHORITATIVE_IDENTITY_EVIDENCE", p.reference())
                       for p in graph.nodes}
            for dependency in graph.edges:
                edges.add(("EXACT_DEPENDENCY", indexed[dependency.requiring], indexed[dependency.required], "VALID"))
            if evidence.graph is not None and evidence.lock is not None and evidence.lock.resolution != evidence.graph:
                issue("SUPPLY_CHAIN_LOCK_MISMATCH")
        except (ValueError, TypeError, AttributeError):
            issue("SUPPLY_CHAIN_LOCK_MISMATCH")
    registry_signature = None
    if evidence.registry_record is not None:
        try:
            if type(evidence.registry_record) is not RegistryRecord:
                raise ValueError()
            record = RegistryRecord.from_mapping(evidence.registry_record.record())
            n = node("REGISTRY_RECORD", "AUTHORITATIVE_IDENTITY_EVIDENCE", record.record())
            check("REGISTRY_BINDS_PACKAGE_CONTENT", record.identity == identity and record.manifest.coordinate == m.coordinate,
                  n, content_node, "SUPPLY_CHAIN_REGISTRY_MISMATCH")
            registry_signature = record.signature
            if record.manifest.provenance != m.provenance:
                issue("SUPPLY_CHAIN_PROVENANCE_MISMATCH")
        except (ValueError, TypeError, AttributeError):
            issue("SUPPLY_CHAIN_REGISTRY_MISMATCH")
    if evidence.registry is not None:
        try:
            catalog = evidence.registry
            if type(catalog) is not RegistryCatalog:
                raise ValueError()
            n = node("REGISTRY_STATE", "INTEGRITY_EVIDENCE", {"fingerprint": registry_state_fingerprint(catalog)})
            matched = tuple(r for r in catalog.records if r.manifest.coordinate == m.coordinate)
            valid = len(matched) == 1 and matched[0].identity == identity
            if len(matched) == 1:
                admitted = RegistryRecord.from_mapping(matched[0].record())
                if registry_signature is not None and registry_signature != admitted.signature:
                    issue("SUPPLY_CHAIN_SIGNATURE_MISMATCH")
                registry_signature = admitted.signature
                if admitted.manifest.provenance != m.provenance:
                    issue("SUPPLY_CHAIN_PROVENANCE_MISMATCH")
            if evidence.registry_record is not None:
                valid = valid and matched == (evidence.registry_record,)
            blobs = {b.digest: b.data for b in catalog.blobs}
            valid = valid and all(d.digest in blobs and _digest(blobs[d.digest]) == d.digest for d in m.content)
            check("REGISTRY_BLOBS_MATCH_PACKAGE", valid, n, content_node, "SUPPLY_CHAIN_REGISTRY_MISMATCH")
        except (ValueError, TypeError, AttributeError):
            issue("SUPPLY_CHAIN_REGISTRY_MISMATCH")
    if evidence.publication is not None:
        try:
            if type(evidence.publication) is not PublicationReceipt:
                raise ValueError()
            r = _parse_record(evidence.publication.canonical_json.encode("utf-8"))
            keys = {"schema", "status", "publisher", "coordinate", "content_identity", "previous_state", "resulting_state",
                    "policy_fingerprint", "authentication", "signature_status", "provenance", "package_trust_granted",
                    "runtime_authority_granted"}
            if set(r) != keys:
                raise ValueError()
            PublisherPrincipal(r["publisher"])
            valid = (r["schema"] == "apexforge.registry-publication-receipt/v1" and
                r["coordinate"] == m.coordinate.record() and r["content_identity"] == identity.record() and
                r["authentication"] == "EXTERNAL_PRECONDITION" and r["signature_status"] in ("UNSIGNED", "NOT_VERIFIED") and
                r["package_trust_granted"] is False and r["runtime_authority_granted"] is False and
                r["provenance"] == [p.record() for p in m.provenance] and r["status"] in ("PUBLISHED_NEW", "ALREADY_PRESENT"))
            for key in ("previous_state", "resulting_state", "policy_fingerprint"):
                PackageContentIdentity(r[key])
            n = node("PUBLICATION_RECEIPT", "UNVERIFIED_EVIDENCE", r)
            check("PUBLICATION_BINDS_PACKAGE_CONTENT", valid, n, content_node, "SUPPLY_CHAIN_PUBLICATION_MISMATCH")
            if any(getattr(evidence, name) is None for name in ("before", "after", "publication_policy")):
                missing("publication_transition", "publication" in REQUIREMENTS[profile.name])
            else:
                before, after, policy = evidence.before, evidence.after, evidence.publication_policy
                if type(before) is not RegistryCatalog or type(after) is not RegistryCatalog or type(policy) is not PublicationPolicy:
                    raise ValueError()
                valid = (r["previous_state"] == registry_state_fingerprint(before) and
                    r["resulting_state"] == registry_state_fingerprint(after) and r["policy_fingerprint"] == policy.fingerprint() and
                    PublicationGrant(PublisherPrincipal(r["publisher"]), m.coordinate.namespace) in policy.grants)
                found = tuple(x for x in after.records if x.manifest.coordinate == m.coordinate)
                valid = valid and len(found) == 1 and found[0].identity == identity
                if len(found) == 1:
                    admitted = RegistryRecord.from_mapping(found[0].record())
                    if registry_signature is not None and registry_signature != admitted.signature:
                        issue("SUPPLY_CHAIN_SIGNATURE_MISMATCH")
                    registry_signature = admitted.signature
                after_blobs = {b.digest: b.data for b in after.blobs}
                valid = valid and all(d.digest in after_blobs and _digest(after_blobs[d.digest]) == d.digest for d in m.content)
                if r["status"] == "ALREADY_PRESENT":
                    valid = valid and before == after
                else:
                    valid = valid and not any(x.manifest.coordinate == m.coordinate for x in before.records)
                    valid = valid and set(after.records) == set(before.records) | set(found)
                    old_blobs = {b.digest: b.data for b in before.blobs}
                    new_blobs = {b.digest: b.data for b in after.blobs}
                    if evidence.members is None:
                        missing("publication_members", "publication" in REQUIREMENTS[profile.name])
                    else:
                        for member in evidence.members:
                            digest = _digest(member.data)
                            valid = valid and (digest not in old_blobs or old_blobs[digest] == member.data)
                        expected = dict(old_blobs)
                        expected.update({_digest(member.data): member.data for member in evidence.members})
                        valid = valid and new_blobs == expected
                if evidence.registry is not None:
                    valid = valid and after == evidence.registry
                valid = valid and r["signature_status"] == ("NOT_VERIFIED" if found and found[0].signature else "UNSIGNED")
                pn = node("PUBLICATION_POLICY", "POLICY_EVIDENCE", policy.record())
                check("PUBLICATION_BINDS_REGISTRY_TRANSITION", valid, n, pn, "SUPPLY_CHAIN_PUBLICATION_MISMATCH")
        except (ValueError, TypeError, AttributeError, KeyError):
            issue("SUPPLY_CHAIN_PUBLICATION_MISMATCH")
    if evidence.artifacts is not None:
        try:
            bundle = evidence.artifacts
            if type(bundle) is not ArtifactBundle:
                raise ValueError()
            descriptors = tuple(ArtifactDescriptor(**{f.name: getattr(d, f.name) for f in fields(ArtifactDescriptor)})
                                for d in bundle.descriptors)
            payloads = tuple(ArtifactPayload(p.digest, p.data) for p in bundle.payloads)
            ArtifactBundle(bundle.package, descriptors, payloads)
            bn = node("ARTIFACT_BUNDLE", "INTEGRITY_EVIDENCE", bundle.canonical_record())
            check("ARTIFACT_BINDS_PACKAGE_CONTENT", bundle.package == identity, bn, content_node,
                  "SUPPLY_CHAIN_ARTIFACT_PACKAGE_MISMATCH")
            if type(evidence.builds) is not tuple or not all(type(b) is SuppliedBuild for b in evidence.builds):
                raise ValueError()
            if len({b.path for b in evidence.builds}) != len(evidence.builds):
                raise ValueError()
            builds = {b.path: b for b in evidence.builds}
            if type(evidence.air) is not tuple or not all(type(a) is CanonicalReference and a.kind == "air" for a in evidence.air):
                raise ValueError()
            data = {p.digest: p.data for p in payloads}
            if type(evidence.sources) is not tuple or not all(type(s) is ContentMember for s in evidence.sources):
                raise ValueError()
            if len({s.path.value.casefold() for s in evidence.sources}) != len(evidence.sources):
                raise ValueError()
            sources = {s.path.value: s.data for s in evidence.sources}
            for d in descriptors:
                dn = node("ARTIFACT_DESCRIPTOR", "PROVENANCE_REFERENCE", d.record())
                edges.add(("BUNDLE_CONTAINS_ARTIFACT", bn, dn, "VALID"))
                check("ARTIFACT_BINDS_PACKAGE_CONTENT", d.package == identity, dn, content_node,
                      "SUPPLY_CHAIN_ARTIFACT_PACKAGE_MISMATCH")
                pn = node("ARTIFACT_PAYLOAD", "INTEGRITY_EVIDENCE", {"digest": d.digest, "observed_digest": _digest(data[d.digest])})
                check("ARTIFACT_BYTES_MATCH_DIGEST", True, pn, dn, "SUPPLY_CHAIN_ARTIFACT_DIGEST_MISMATCH")
                if d.provenance != m.provenance:
                    issue("SUPPLY_CHAIN_PROVENANCE_MISMATCH", subject=d.path.value)
                build = builds.get(d.path)
                if build is None:
                    missing("build:" + d.path.value, "builds" in REQUIREMENTS[profile.name])
                else:
                    if d.kind == "MANAGED":
                        actual = describe_managed(m, d.path, build.data, entrypoint=d.entrypoint, debug_metadata=d.debug_metadata)
                        matches = actual.digest == d.digest and build.fingerprint == actual.build.fingerprint
                    else:
                        actual = describe_native(m, d.path, data[d.digest], build.data, build.fingerprint,
                            target=d.target, profile=d.profile, entrypoint=d.entrypoint, debug_metadata=d.debug_metadata)
                        matches = True
                    build_node = node("BUILD_ARTIFACT", "INTEGRITY_EVIDENCE", {"fingerprint": build.fingerprint,
                        "bytes_digest": _digest(build.data)})
                    check("ARTIFACT_BINDS_BUILD", matches and actual.build == d.build, dn, build_node,
                          "SUPPLY_CHAIN_BUILD_BINDING_MISMATCH")
                    if d.kind == "MANAGED":
                        project = _parse_record(build.data).get("project")
                        if type(project) is not dict or type(project.get("sources")) is not list:
                            raise ValueError()
                        if type(project.get("source_count")) is not int or project["source_count"] != len(project["sources"]):
                            raise ValueError()
                        seen_sources = set()
                        for source in project["sources"]:
                            if type(source) is not dict or set(source) != {"path", "sha256"}:
                                raise ValueError()
                            path = PackagePath(source["path"])
                            if path.value.casefold() in seen_sources:
                                raise ValueError()
                            seen_sources.add(path.value.casefold())
                            if type(source["sha256"]) is not str:
                                raise ValueError()
                            PackageContentIdentity(source["sha256"].upper())
                            reference = node("BUILD_SOURCE_REFERENCE", "PROVENANCE_REFERENCE",
                                             {"path": path.value, "digest": source["sha256"].upper()})
                            edges.add(("BUILD_DECLARES_SOURCE", build_node, reference, "VALID"))
                            if path.value not in sources:
                                missing("source:" + path.value, "builds" in REQUIREMENTS[profile.name])
                            else:
                                source_node = node("SOURCE_BYTES", "INTEGRITY_EVIDENCE",
                                    {"path": path.value, "observed_digest": _digest(sources[path.value])})
                                check("SOURCE_BYTES_MATCH_BUILD_REFERENCE", _digest(sources[path.value]) == source["sha256"].upper(),
                                    source_node, reference, "SUPPLY_CHAIN_PROVENANCE_MISMATCH")
                    an = node("AIR_REFERENCE", "PROVENANCE_REFERENCE", actual.air.record())
                    check("BUILD_BINDS_AIR", actual.air == d.air, build_node, an, "SUPPLY_CHAIN_AIR_BINDING_MISMATCH")
                    if actual.source is not None:
                        source_node = node("GENERATED_SOURCE_REFERENCE", "PROVENANCE_REFERENCE", actual.source.record())
                        edges.add(("BUILD_REFERENCES_GENERATED_SOURCE", build_node, source_node, "VALID"))
                        if build.source_bytes is not None:
                            generated = node("GENERATED_SOURCE_BYTES", "INTEGRITY_EVIDENCE",
                                             {"observed_digest": _digest(build.source_bytes)})
                            check("GENERATED_SOURCE_BYTES_MATCH_BUILD", _digest(build.source_bytes) == actual.source.fingerprint,
                                  generated, source_node, "SUPPLY_CHAIN_PROVENANCE_MISMATCH")
                        else:
                            missing("generated_source_bytes:" + d.path.value)
                    if actual.source != d.source:
                        issue("SUPPLY_CHAIN_PROVENANCE_MISMATCH", subject=d.path.value)
                if not evidence.air:
                    missing("air:" + d.path.value, "air" in REQUIREMENTS[profile.name])
                else:
                    an = node("AIR_REFERENCE", "PROVENANCE_REFERENCE", d.air.record())
                    check("CANONICAL_AIR_REFERENCE_MATCHES", d.air in evidence.air, dn, an,
                          "SUPPLY_CHAIN_AIR_BINDING_MISMATCH")
            if set(builds) - {d.path for d in descriptors}:
                issue("SUPPLY_CHAIN_BUILD_BINDING_MISMATCH")
        except (ValueError, TypeError, AttributeError, KeyError) as exc:
            code = getattr(exc, "code", "")
            issue("SUPPLY_CHAIN_NATIVE_PROFILE_MISMATCH" if code == "UNSUPPORTED_TARGET" else
                  "SUPPLY_CHAIN_ARTIFACT_DIGEST_MISMATCH" if "PAYLOAD" in code else "SUPPLY_CHAIN_BUILD_BINDING_MISMATCH")
    signature_status = "NOT_SUPPLIED"
    signature = evidence.signature if evidence.signature is not None else registry_signature
    if evidence.signature is not None and registry_signature is not None and evidence.signature != registry_signature:
        issue("SUPPLY_CHAIN_SIGNATURE_MISMATCH")
    if signature is not None:
        try:
            if type(signature) is not SignatureEnvelope:
                raise ValueError()
            SignatureEnvelope(**{f.name: getattr(signature, f.name) for f in fields(SignatureEnvelope)})
            sn = node("SIGNATURE_ENVELOPE", "PASSIVE_AUTHENTICATION_EVIDENCE", signature.record())
            check("SIGNATURE_PAYLOAD_REFERENCE_MATCHES", signature.payload_fingerprint == payload_fingerprint(m),
                  sn, content_node, "SUPPLY_CHAIN_SIGNATURE_MISMATCH")
            signature_status = "UNVERIFIED"
            issue("SUPPLY_CHAIN_SIGNATURE_UNVERIFIED", "UNVERIFIED", sn)
        except (ValueError, TypeError, AttributeError):
            signature_status = "INVALID"
            issue("SUPPLY_CHAIN_SIGNATURE_MALFORMED")
    if profile.require_authentication and signature is None:
        missing("signature", True)
    if evidence.trust_policy is not None or evidence.public_key is not None:
        try:
            if evidence.trust_policy is not None and type(evidence.trust_policy) is not TrustPolicy:
                raise ValueError()
            if evidence.members is None:
                missing("trust_integrity_members", profile.require_authentication)
            else:
                result = verify_package(m, evidence.members, signature, evidence.public_key, evidence.trust_policy).record()
                node("TRUST_POLICY_OBSERVATION", "POLICY_EVIDENCE", {"policy_fingerprint": result["policy_fingerprint"],
                    "signer_scope_eligibility": result["scope_trust"], "signature": result["signature"],
                    "final_cryptographic_trust": "NOT_ESTABLISHED"})
                if result["signature"] == "SIGNER_KEY_FINGERPRINT_MISMATCH":
                    issue("SUPPLY_CHAIN_SIGNATURE_MISMATCH")
        except (ValueError, TypeError, AttributeError):
            issue("SUPPLY_CHAIN_TRUST_POLICY_INVALID")
    if evidence.cache_entry is not None:
        try:
            entry = evidence.cache_entry
            if type(entry) is not CacheEntry:
                raise ValueError()
            CacheEntry(entry.manifest, entry.members)
            n = node("CACHE_ENTRY", "INTEGRITY_EVIDENCE", entry.canonical_record())
            check("CACHE_BINDS_PACKAGE_CONTENT", entry.identity == identity, n, content_node, "SUPPLY_CHAIN_CACHE_MISMATCH")
        except (ValueError, TypeError, AttributeError):
            issue("SUPPLY_CHAIN_CACHE_MISMATCH")
    if evidence.compatibility is not None:
        try:
            if type(evidence.compatibility) is not CompatibilityReport:
                raise ValueError()
            node("COMPATIBILITY_CONTEXT", "NON_SUPPLY_CHAIN_METADATA", evidence.compatibility.canonical_record())
        except (ValueError, TypeError, AttributeError):
            issue("SUPPLY_CHAIN_CONTEXT_INVALID")
    for p in m.provenance:
        n = node("PROVENANCE_REFERENCE", "PROVENANCE_REFERENCE", p.record())
        edges.add(("PROVENANCE_REFERENCED_BY_PACKAGE", package_node, n, "VALID"))
    structural = "INVALID" if any(d[0] == "INVALID" for d in diagnostics) else (
        "INCOMPLETE" if any(d[0] == "INCOMPLETE" for d in diagnostics) else "VALID")
    status = "UNVERIFIED" if structural == "VALID" and profile.require_authentication and signature_status == "UNVERIFIED" else structural
    return SupplyChainReport(_json({"schema": SCHEMA, "profile": {"name": profile.name,
        "required": list(REQUIREMENTS[profile.name]), "require_authentication": profile.require_authentication},
        "package": {"coordinate": m.coordinate.record(), "content_identity": identity.record()},
        "status": status, "structural_status": structural, "authentication": {"signature": signature_status,
        "cryptographic_provider": "CRYPTO_PROVIDER_UNAVAILABLE", "provenance": "UNAVAILABLE",
        "publisher": "EXTERNAL_PRECONDITION", "final_trust": "NOT_ESTABLISHED"},
        "semantic_authority": "CANONICAL_AIR", "grants_authority": False, "real_world_attribution": False,
        "nodes": [nodes[k] for k in sorted(nodes)], "edges": [{"claim": c, "source": s, "target": t, "status": st}
            for c, s, t, st in sorted(edges)], "checks": [{"claim": c, "status": st, "subject": s} for c, st, s in sorted(checks)],
        "diagnostics": [{"status": st, "code": c, "subject": s} for st, c, s in sorted(diagnostics)]}))
