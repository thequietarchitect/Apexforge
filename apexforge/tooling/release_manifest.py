"""P16.4 supplied release evidence only; integrity is not authentication."""
from dataclasses import dataclass
import re
from tooling.domain_platform import CanonicalModel
from tooling.package_manifest import CanonicalReference
from tooling import release_architecture as architecture
from tooling import release_build as build
from tooling.release_versioning import ReleaseSurfaceVersion, PRIMARY

MAX_RECORDS = 8192
KINDS = ("FROZEN_SOURCE_BASELINE", "RELEASE_IDENTITY", "RELEASE_ARCHITECTURE",
         "VERSION_MAPPING", "ARTIFACT_DESCRIPTOR", "BUILD_RECIPE", "BUILD_ARTIFACT", "ARTIFACT_CHECKSUM")


class ReleaseEvidenceError(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def require(condition, code):
    if not condition:
        raise ReleaseEvidenceError(code)


def hex_digest(value):
    require(type(value) is str and re.fullmatch(r"[0-9A-F]{64}", value) is not None,
            "RELEASE_CHECKSUM_INVALID")


def reference(model):
    """Exact structural reference to an existing canonical owner."""
    require(type(model) in (architecture.FrozenSourceBaseline, architecture.ReleaseIdentity,
                           architecture.ReleaseArtifactDescriptor, architecture.ReleaseArtifactMatrix,
                           build.ReleaseBuildRecipe, build.ReleaseBuildArtifact, ReleaseSurfaceVersion,
                           ReleaseChecksumRecord, ReleaseChecksumSet, ReleaseProvenanceRecord,
                           ReleaseProvenanceBundle, ReleaseManifest), "RELEASE_EVIDENCE_REFERENCE_INVALID")
    return CanonicalReference(model.DOMAIN, "provenance-scope", model.fingerprint())


def ref_key(value):
    return (value.schema, value.kind, value.fingerprint)


def collection(values, cls, key, code):
    require(type(values) is tuple and len(values) <= MAX_RECORDS and all(type(v) is cls for v in values), code)
    keys = tuple(key(v) for v in values)
    require(len(set(keys)) == len(keys), code)
    return tuple(v for _, v in sorted(zip(keys, values), key=lambda p: p[0]))


@dataclass(frozen=True)
class ReleaseChecksumRecord(CanonicalModel):
    release: architecture.ReleaseIdentity
    artifact: architecture.ReleaseArtifactIdentity
    descriptor: CanonicalReference
    recipe: CanonicalReference
    build_artifact: CanonicalReference
    algorithm: str
    digest: str
    length: int
    DOMAIN = "apexforge.release-checksum-record/v1"

    def __post_init__(self):
        require(type(self.release) is architecture.ReleaseIdentity and type(self.artifact) is architecture.ReleaseArtifactIdentity,
                "RELEASE_CHECKSUM_INVALID")
        for value, schema in ((self.descriptor, architecture.ReleaseArtifactDescriptor.DOMAIN),
                              (self.recipe, build.ReleaseBuildRecipe.DOMAIN),
                              (self.build_artifact, build.ReleaseBuildArtifact.DOMAIN)):
            require(type(value) is CanonicalReference and value.schema == schema and value.kind == "provenance-scope",
                    "RELEASE_CHECKSUM_BINDING_INVALID")
        require(type(self.algorithm) is str and self.algorithm == "SHA256", "RELEASE_CHECKSUM_ALGORITHM_UNSUPPORTED")
        hex_digest(self.digest)
        require(type(self.length) is int and 0 <= self.length <= build.MAX_BYTES, "RELEASE_CHECKSUM_LENGTH_INVALID")

    def record(self):
        return {"release": self.release.record(), "artifact": self.artifact.record(),
                "descriptor": self.descriptor.record(), "recipe": self.recipe.record(),
                "build_artifact": self.build_artifact.record(), "algorithm": self.algorithm,
                "digest": self.digest, "length": self.length, "authenticated": False, "trusted": False}


def checksum_for(artifact):
    require(type(artifact) is build.ReleaseBuildArtifact, "RELEASE_CHECKSUM_BINDING_INVALID")
    return ReleaseChecksumRecord(artifact.recipe.release, artifact.identity, reference(artifact._slot.descriptor),
                                 reference(artifact.recipe), reference(artifact), "SHA256", artifact.declared_digest, len(artifact.data))


def verify_checksum(record, artifact, data):
    """Return integrity-only evidence; never read, run or interpret supplied bytes."""
    require(type(record) is ReleaseChecksumRecord and type(artifact) is build.ReleaseBuildArtifact,
            "RELEASE_CHECKSUM_BINDING_INVALID")
    require(record == checksum_for(artifact), "RELEASE_CHECKSUM_BINDING_MISMATCH")
    require(type(data) is bytes and len(data) <= build.MAX_BYTES, "RELEASE_CHECKSUM_BYTES_INVALID")
    require(len(data) == record.length and build.digest(data) == record.digest, "RELEASE_CHECKSUM_MISMATCH")
    return CanonicalReference(record.DOMAIN, "artifact", record.fingerprint())


@dataclass(frozen=True)
class ReleaseChecksumSet(CanonicalModel):
    release: architecture.ReleaseIdentity
    architecture: CanonicalReference
    records: tuple
    DOMAIN = "apexforge.release-checksum-set/v1"

    def __post_init__(self):
        require(type(self.release) is architecture.ReleaseIdentity and type(self.architecture) is CanonicalReference and
                self.architecture.schema == architecture.ReleaseArtifactMatrix.DOMAIN and self.architecture.kind == "provenance-scope",
                "RELEASE_CHECKSUM_SCOPE_INVALID")
        object.__setattr__(self, "records", collection(self.records, ReleaseChecksumRecord, lambda v: v.artifact.identifier,
                                                     "RELEASE_CHECKSUM_DUPLICATE_OR_INVALID"))
        require(all(v.release == self.release for v in self.records), "RELEASE_CHECKSUM_SCOPE_INVALID")

    def record(self):
        return {"release": self.release.record(), "architecture": self.architecture.record(),
                "records": [v.record() for v in self.records], "authentication": "NOT_ESTABLISHED"}


@dataclass(frozen=True)
class ReleaseProvenanceRecord(CanonicalModel):
    identifier: str
    release: architecture.ReleaseIdentity
    kind: str
    subject: CanonicalReference
    predecessors: tuple = ()
    DOMAIN = "apexforge.release-provenance-record/v1"

    def __post_init__(self):
        require(type(self.identifier) is str and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", self.identifier) is not None,
                "RELEASE_PROVENANCE_INVALID")
        require(type(self.release) is architecture.ReleaseIdentity and type(self.kind) is str and self.kind in KINDS and
                type(self.subject) is CanonicalReference, "RELEASE_PROVENANCE_INVALID")
        object.__setattr__(self, "predecessors", collection(self.predecessors, CanonicalReference, ref_key,
                                                         "RELEASE_PROVENANCE_INVALID"))

    def record(self):
        return {"id": self.identifier, "release": self.release.record(), "kind": self.kind,
                "subject": self.subject.record(), "predecessors": [v.record() for v in self.predecessors],
                "authentication": "NOT_ESTABLISHED", "authorship": "NOT_ESTABLISHED"}


@dataclass(frozen=True)
class ReleaseProvenanceBundle(CanonicalModel):
    release: architecture.ReleaseIdentity
    records: tuple
    DOMAIN = "apexforge.release-provenance-bundle/v1"

    def __post_init__(self):
        require(type(self.release) is architecture.ReleaseIdentity, "RELEASE_PROVENANCE_SCOPE_INVALID")
        object.__setattr__(self, "records", collection(self.records, ReleaseProvenanceRecord, lambda v: v.identifier,
                                                     "RELEASE_PROVENANCE_DUPLICATE_OR_INVALID"))
        require(all(v.release == self.release for v in self.records), "RELEASE_PROVENANCE_SCOPE_INVALID")
        require(sum(len(v.predecessors) for v in self.records) <= MAX_RECORDS * 4,
                "RELEASE_PROVENANCE_SIZE_INVALID")
        subjects = tuple((v.kind, ref_key(v.subject)) for v in self.records)
        require(len(set(subjects)) == len(subjects), "RELEASE_PROVENANCE_SUBJECT_DUPLICATE")

    def record(self):
        return {"release": self.release.record(), "baseline": self.release.baseline.record(),
                "records": [v.record() for v in self.records], "authenticated": False}


def required_lineage(matrix, artifacts, checksums, versions=()):
    """Describe exact required owner links, without creating provenance evidence."""
    release = matrix.release
    release_ref, matrix_ref = reference(release), reference(matrix)
    links = [("FROZEN_SOURCE_BASELINE", reference(release.baseline), ()),
             ("RELEASE_IDENTITY", release_ref, (reference(release.baseline),)),
             ("RELEASE_ARCHITECTURE", matrix_ref, (release_ref,))]
    links.extend(("VERSION_MAPPING", reference(v), (release_ref,)) for v in versions)
    links.extend(("ARTIFACT_DESCRIPTOR", reference(d), (matrix_ref,)) for d in matrix.artifacts)
    if artifacts is not None:
        links.extend(("BUILD_RECIPE", reference(r), (reference(release),) +
                      tuple(reference(s.descriptor) for s in r.outputs)) for r in artifacts.recipes)
        links.extend(("BUILD_ARTIFACT", reference(a), (reference(a.recipe), reference(a._slot.descriptor)))
                     for a in artifacts.artifacts)
    if checksums is not None:
        links.extend(("ARTIFACT_CHECKSUM", reference(c), (c.build_artifact, c.descriptor, c.recipe)) for c in checksums.records)
    return tuple(links)


@dataclass(frozen=True)
class ReleaseManifest(CanonicalModel):
    architecture: architecture.ReleaseArtifactMatrix
    artifacts: object = None
    checksums: object = None
    provenance: object = None
    versions: tuple = ()
    schema: str = "apexforge.release-manifest/v1"
    DOMAIN = "apexforge.release-manifest/v1"

    def __post_init__(self):
        require(type(self.architecture) is architecture.ReleaseArtifactMatrix and type(self.schema) is str and self.schema == self.DOMAIN,
                "RELEASE_MANIFEST_SCHEMA_OR_MODEL_INVALID")
        for value, cls in ((self.artifacts, build.ReleaseArtifactSet), (self.checksums, ReleaseChecksumSet),
                           (self.provenance, ReleaseProvenanceBundle)):
            require(value is None or type(value) is cls, "RELEASE_MANIFEST_MODEL_INVALID")
        object.__setattr__(self, "versions", collection(self.versions, ReleaseSurfaceVersion,
                                                     lambda v: v.surface.canonical_json(), "RELEASE_VERSION_MAPPING_INVALID"))

    def evaluate(self):
        findings = set()
        invalid = False
        release = self.architecture.release
        def contradiction(code):
            nonlocal invalid
            invalid = True
            findings.add((code, "manifest"))
        if release.baseline != architecture.P15_BASELINE:
            contradiction("RELEASE_MANIFEST_BASELINE_MISMATCH")
        for value in (self.artifacts, self.checksums, self.provenance) + self.versions:
            if value is not None and value.release != release:
                contradiction("RELEASE_MANIFEST_RELEASE_MISMATCH")
        if self.checksums is not None and self.checksums.architecture != reference(self.architecture):
            contradiction("RELEASE_MANIFEST_ARCHITECTURE_MISMATCH")
        descriptors = {d.identity.identifier: d for d in self.architecture.artifacts}
        for version in self.versions:
            matching = tuple(d for d in descriptors.values() if d.target == version.surface.target)
            if not matching:
                contradiction("RELEASE_MANIFEST_VERSION_SURFACE_MISMATCH")
            elif (version.surface.target.identifier, version.surface.domain) in PRIMARY and any(
                    d.surface_version != version.version for d in matching):
                contradiction("RELEASE_MANIFEST_VERSION_MISMATCH")
        actual = {} if self.artifacts is None else {a.identity.identifier: a for a in self.artifacts.artifacts}
        sums = {} if self.checksums is None else {c.artifact.identifier: c for c in self.checksums.records}
        if (set(actual) | set(sums)) - set(descriptors):
            contradiction("RELEASE_MANIFEST_ARTIFACT_UNEXPECTED")
        if self.artifacts is not None:
            for recipe in self.artifacts.recipes:
                for slot in recipe.outputs:
                    if descriptors.get(slot.descriptor.identity.identifier) != slot.descriptor:
                        contradiction("RELEASE_MANIFEST_DESCRIPTOR_MISMATCH")
        for identity, descriptor in sorted(descriptors.items()):
            artifact, checksum = actual.get(identity), sums.get(identity)
            if artifact is None:
                findings.add(("RELEASE_MANIFEST_ARTIFACT_MISSING", identity))
            elif artifact._slot.descriptor != descriptor:
                contradiction("RELEASE_MANIFEST_DESCRIPTOR_MISMATCH")
            if checksum is None:
                findings.add(("RELEASE_MANIFEST_CHECKSUM_MISSING", identity))
            elif checksum.descriptor != reference(descriptor) or (artifact is not None and checksum != checksum_for(artifact)):
                contradiction("RELEASE_MANIFEST_CHECKSUM_MISMATCH")
        expected = {(kind, ref_key(subject)): predecessors for kind, subject, predecessors in
                    required_lineage(self.architecture, self.artifacts, self.checksums, self.versions)}
        supplied = {} if self.provenance is None else {(v.kind, ref_key(v.subject)): v for v in self.provenance.records}
        for key, predecessors in sorted(expected.items()):
            record = supplied.get(key)
            if record is None:
                findings.add(("RELEASE_MANIFEST_PROVENANCE_MISSING", key[0] + ":" + key[1][2]))
            elif record.predecessors != tuple(sorted(predecessors, key=ref_key)):
                contradiction("RELEASE_MANIFEST_PROVENANCE_MISMATCH")
        for key in set(supplied) - set(expected):
            # Missing evidence cannot validate related provenance; it remains incomplete.
            # Once its owner evidence is supplied, an unexpected subject is contradictory.
            unavailable = (key[0] in ("BUILD_RECIPE", "BUILD_ARTIFACT") and self.artifacts is None or
                           key[0] == "ARTIFACT_CHECKSUM" and self.checksums is None or
                           key[0] == "BUILD_ARTIFACT" and any(ref_key(c.build_artifact) == key[1] and
                           c.artifact.identifier not in actual for c in sums.values()))
            if not unavailable:
                contradiction("RELEASE_MANIFEST_PROVENANCE_UNEXPECTED")
        return ("INVALID" if invalid else "INCOMPLETE" if findings else "COMPLETE", tuple(sorted(findings)))

    @property
    def status(self):
        return self.evaluate()[0]

    def record(self):
        status, findings = self.evaluate()
        actual = {} if self.artifacts is None else {a.identity.identifier: a for a in self.artifacts.artifacts}
        inventory = []
        for descriptor in self.architecture.artifacts:
            artifact = actual.get(descriptor.identity.identifier)
            inventory.append({"identity": descriptor.identity.record(), "descriptor": reference(descriptor).record(),
                              "role": descriptor.role, "target": descriptor.target.record(), "format": descriptor.format,
                              "artifact": None if artifact is None else reference(artifact).record(),
                              "recipe": None if artifact is None else reference(artifact.recipe).record(),
                              "length": None if artifact is None else len(artifact.data),
                              "digest": None if artifact is None else artifact.declared_digest,
                              "state": "MISSING" if artifact is None else "SUPPLIED_BUILD_EVIDENCE"})
        return {"schema": self.schema, "release": self.architecture.release.record(),
                "baseline": self.architecture.release.baseline.record(), "architecture": reference(self.architecture).record(),
                "descriptors": [d.record() for d in self.architecture.artifacts],
                "inventory": inventory,
                "build_evidence": None if self.artifacts is None else self.artifacts.record(),
                "checksums": None if self.checksums is None else self.checksums.record(),
                "provenance": None if self.provenance is None else self.provenance.record(),
                "version_mappings": [v.record() for v in self.versions], "completeness": status,
                "findings": [{"code": code, "subject": subject} for code, subject in findings],
                "trusted": False, "authenticated": False, "release_approved": False,
                "published": False, "installed": False, "authority": False, "compatibility": "NOT_ESTABLISHED",
                "target_packaging": "NOT_ESTABLISHED", "crypto": "CRYPTO_PROVIDER_UNAVAILABLE",
                "semantic_authority": "CANONICAL_AIR"}
