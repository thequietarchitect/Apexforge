"""P16.4 exact supplied evidence, integrity and passive boundaries."""
import ast
from dataclasses import FrozenInstanceError, replace
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tooling import release_manifest as m
from tooling import release_architecture as r
from tooling import release_build as b
from tooling import release_versioning as v
from tooling.package_manifest import CanonicalReference, PackageCoordinate, PackageContentIdentity, ExactVersion
from p16_3_reproducible_release_build_test import fixture


def evidence(data=b"opaque\r\nbytes\0", count=1):
    recipe = fixture(data, count)
    artifacts = b.assemble(recipe)  # Owning P16.3 fixture preparation only.
    matrix = r.ReleaseArtifactMatrix(recipe.release, tuple(o.descriptor for o in recipe.outputs))
    checksums = m.ReleaseChecksumSet(recipe.release, m.reference(matrix), tuple(m.checksum_for(a) for a in artifacts.artifacts))
    records = tuple(m.ReleaseProvenanceRecord("evidence-" + str(i), recipe.release, kind, subject, predecessors)
                    for i, (kind, subject, predecessors) in enumerate(m.required_lineage(matrix, artifacts, checksums)))
    bundle = m.ReleaseProvenanceBundle(recipe.release, records)
    return m.ReleaseManifest(matrix, artifacts, checksums, bundle)


class ContractTests(unittest.TestCase):
    def error(self, code, callback):
        with self.assertRaises(m.ReleaseEvidenceError) as caught:
            callback()
        self.assertEqual(caught.exception.code, code)
        self.assertEqual(str(caught.exception), code)

    def test_immutable_models(self):
        x = evidence()
        for obj in (x, x.checksums, x.checksums.records[0], x.provenance, x.provenance.records[0]):
            with self.assertRaises(FrozenInstanceError):
                setattr(obj, next(iter(obj.__dataclass_fields__)), None)

    def test_complete_exact_release_and_baseline(self):
        x = evidence()
        self.assertEqual(x.status, "COMPLETE")
        self.assertEqual(x.record()["baseline"], r.P15_BASELINE.record())
        self.assertEqual(x.architecture.release.baseline.commit, r.P15_COMMIT)
        self.assertEqual(x.record()["architecture"], m.reference(x.architecture).record())

    def test_independent_construction_determinism(self):
        a, z = evidence(), evidence()
        self.assertIsNot(a, z)
        self.assertIsNot(a.artifacts.artifacts[0].data, z.artifacts.artifacts[0].data)
        self.assertEqual(a.canonical_json(), z.canonical_json())
        self.assertEqual(a.fingerprint(), z.fingerprint())

    def test_checksum_algorithm_explicit(self):
        c = evidence().checksums.records[0]
        for algorithm in (None, "", "sha256", "SHA1"):
            self.error("RELEASE_CHECKSUM_ALGORITHM_UNSUPPORTED", lambda: replace(c, algorithm=algorithm))

    def test_malformed_digest_rejected(self):
        c = evidence().checksums.records[0]
        for digest in ("", "a" * 64, "G" * 64, "A" * 63, None):
            self.error("RELEASE_CHECKSUM_INVALID", lambda: replace(c, digest=digest))

    def test_length_strict_and_bounded(self):
        c = evidence().checksums.records[0]
        for length in (-1, True, 1.0, b.MAX_BYTES + 1):
            self.error("RELEASE_CHECKSUM_LENGTH_INVALID", lambda: replace(c, length=length))

    def test_supplied_bytes_integrity_only(self):
        x = evidence()
        c, a = x.checksums.records[0], x.artifacts.artifacts[0]
        result = m.verify_checksum(c, a, bytes(bytearray(a.data)))
        self.assertEqual(result.fingerprint, c.fingerprint())
        self.assertFalse(c.record()["authenticated"])
        self.assertFalse(c.record()["trusted"])

    def test_byte_and_length_mismatch_fail_closed(self):
        x = evidence()
        c, a = x.checksums.records[0], x.artifacts.artifacts[0]
        for data in (a.data + b"x", b"x" * len(a.data), b""):
            self.error("RELEASE_CHECKSUM_MISMATCH", lambda: m.verify_checksum(c, a, data))
        self.error("RELEASE_CHECKSUM_BYTES_INVALID", lambda: m.verify_checksum(c, a, bytearray(a.data)))

    def test_verification_exact_artifact_binding(self):
        x, y = evidence(), evidence(b"different")
        self.error("RELEASE_CHECKSUM_BINDING_MISMATCH", lambda: m.verify_checksum(x.checksums.records[0], y.artifacts.artifacts[0], y.artifacts.artifacts[0].data))
        self.error("RELEASE_CHECKSUM_BINDING_MISMATCH", lambda: m.verify_checksum(replace(x.checksums.records[0], length=0), x.artifacts.artifacts[0], b""))

    def test_checksum_references_strict(self):
        c = evidence().checksums.records[0]
        self.error("RELEASE_CHECKSUM_BINDING_INVALID", lambda: replace(c, descriptor=c.recipe))
        self.error("RELEASE_CHECKSUM_BINDING_INVALID", lambda: replace(c, recipe="command"))

    def test_checksum_order_independent(self):
        x = evidence(count=3)
        z = replace(x.checksums, records=tuple(reversed(x.checksums.records)))
        self.assertEqual(x.checksums.fingerprint(), z.fingerprint())

    def test_conflicting_checksum_duplicates_rejected(self):
        c = evidence().checksums
        for other in (c.records[0], replace(c.records[0], digest="A" * 64)):
            self.error("RELEASE_CHECKSUM_DUPLICATE_OR_INVALID", lambda: replace(c, records=c.records + (other,)))

    def test_provenance_kinds_bounded(self):
        p = evidence().provenance.records[0]
        self.error("RELEASE_PROVENANCE_INVALID", lambda: replace(p, kind="EXECUTE_CALLBACK"))
        self.error("RELEASE_PROVENANCE_INVALID", lambda: replace(p, predecessors=(lambda: True,)))

    def test_provenance_order_independent(self):
        x = evidence(count=3)
        z = replace(x.provenance, records=tuple(reversed(x.provenance.records)))
        self.assertEqual(x.provenance.fingerprint(), z.fingerprint())
        self.assertEqual(x.fingerprint(), replace(x, provenance=z).fingerprint())

    def test_conflicting_provenance_duplicates_rejected(self):
        p = evidence().provenance
        self.error("RELEASE_PROVENANCE_DUPLICATE_OR_INVALID", lambda: replace(p, records=p.records + (replace(p.records[0], predecessors=(m.reference(p.release),)),)))
        self.error("RELEASE_PROVENANCE_SUBJECT_DUPLICATE", lambda: replace(p, records=p.records + (replace(p.records[0], identifier="other"),)))

    def test_explicit_lineage_owner_links(self):
        x = evidence()
        supplied = {(p.kind, m.ref_key(p.subject)): p.predecessors for p in x.provenance.records}
        for kind, subject, predecessors in m.required_lineage(x.architecture, x.artifacts, x.checksums):
            self.assertEqual(supplied[(kind, m.ref_key(subject))], tuple(sorted(predecessors, key=m.ref_key)))
        self.assertEqual(set(p.kind for p in x.provenance.records), set(m.KINDS) - {"VERSION_MAPPING"})

    def test_missing_artifact_not_empty(self):
        x = evidence()
        incomplete = replace(x, artifacts=None)
        self.assertIn("RELEASE_MANIFEST_ARTIFACT_MISSING", {code for code, _ in incomplete.evaluate()[1]})
        self.assertEqual(incomplete.status, "INCOMPLETE")
        missing = replace(x.artifacts, artifacts=())
        self.assertEqual(replace(x, artifacts=missing).status, "INCOMPLETE")

    def test_missing_checksum_incomplete(self):
        x = evidence()
        self.assertEqual(replace(x, checksums=None).status, "INCOMPLETE")

    def test_missing_provenance_incomplete(self):
        x = evidence()
        self.assertEqual(replace(x, provenance=None).status, "INCOMPLETE")
        self.assertEqual(m.ReleaseManifest(x.architecture).status, "INCOMPLETE")

    def test_contradictory_checksum_invalid(self):
        x = evidence()
        c = replace(x.checksums, records=(replace(x.checksums.records[0], digest="A" * 64),))
        self.assertEqual(replace(x, checksums=c).status, "INVALID")

    def test_contradictory_descriptor_invalid(self):
        x = evidence()
        matrix = replace(x.architecture, artifacts=(replace(x.architecture.artifacts[0], surface_version="0.2.0"),))
        self.assertEqual(replace(x, architecture=matrix).status, "INVALID")

    def test_contradictory_lineage_invalid(self):
        x = evidence()
        records = tuple(replace(p, predecessors=()) if p.kind == "BUILD_ARTIFACT" else p for p in x.provenance.records)
        self.assertEqual(replace(x, provenance=replace(x.provenance, records=records)).status, "INVALID")

    def test_changed_provenance_reidentifies(self):
        x = evidence()
        records = tuple(replace(p, identifier="changed") if p.kind == "BUILD_ARTIFACT" else p for p in x.provenance.records)
        z = replace(x, provenance=replace(x.provenance, records=records))
        self.assertEqual(z.status, "COMPLETE")
        self.assertNotEqual(x.fingerprint(), z.fingerprint())

    def test_changed_content_reidentifies_evidence(self):
        x, z = evidence(), evidence(b"other bytes")
        for a, c in ((x, z), (x.checksums, z.checksums), (x.provenance, z.provenance)):
            self.assertNotEqual(a.fingerprint(), c.fingerprint())

    def test_release_substitution_invalid_and_reidentifies(self):
        x = evidence()
        other = replace(x.architecture.release, version="other-declared")
        matrix = r.ReleaseArtifactMatrix(other, tuple(replace(d, release=other) for d in x.architecture.artifacts))
        z = replace(x, architecture=matrix)
        self.assertEqual(z.status, "INVALID")
        self.assertNotEqual(x.fingerprint(), z.fingerprint())

    def test_unknown_schema_rejected(self):
        self.error("RELEASE_MANIFEST_SCHEMA_OR_MODEL_INVALID", lambda: replace(evidence(), schema="apexforge.release-manifest/v2"))
        class HostileSchema:
            def __eq__(self, other):
                raise AssertionError("caller code must not be evaluated")
        self.error("RELEASE_MANIFEST_SCHEMA_OR_MODEL_INVALID", lambda: replace(evidence(), schema=HostileSchema()))

    def test_other_frozen_baseline_invalid_and_reidentifies(self):
        x = evidence()
        release = replace(x.architecture.release, baseline=replace(r.P15_BASELINE, commit="a" * 40))
        matrix = r.ReleaseArtifactMatrix(release, tuple(replace(d, release=release) for d in x.architecture.artifacts))
        z = m.ReleaseManifest(matrix)
        self.assertEqual(z.status, "INVALID")
        self.assertIn("RELEASE_MANIFEST_BASELINE_MISMATCH", {code for code, _ in z.evaluate()[1]})
        self.assertNotEqual(x.fingerprint(), z.fingerprint())

    def test_inventory_exact_owner_fingerprints_and_content(self):
        x = evidence()
        item = x.record()["inventory"][0]
        a, d = x.artifacts.artifacts[0], x.architecture.artifacts[0]
        self.assertEqual(item["artifact"], m.reference(a).record())
        self.assertEqual(item["descriptor"], m.reference(d).record())
        self.assertEqual(item["recipe"], m.reference(a.recipe).record())
        self.assertEqual(item["length"], len(a.data))
        self.assertEqual(item["digest"], b.digest(a.data))
        self.assertIsNone(m.ReleaseManifest(x.architecture).record()["inventory"][0]["length"])

    def test_exact_version_mapping_owner_and_lineage(self):
        x = evidence()
        mapping = v.ReleaseSurfaceVersion(x.architecture.release,
                    v.ReleaseVersionSurface(r.ReleaseTarget("vscode"), "VSCODE_EXTENSION", "extension"), "0.1.0")
        added = m.ReleaseProvenanceRecord("version", mapping.release, "VERSION_MAPPING", m.reference(mapping), (m.reference(mapping.release),))
        z = replace(x, versions=(mapping,), provenance=replace(x.provenance, records=x.provenance.records + (added,)))
        self.assertEqual(z.status, "COMPLETE")
        self.assertNotEqual(x.fingerprint(), z.fingerprint())
        self.assertEqual(replace(z, versions=(replace(mapping, version="0.2.0"),)).status, "INVALID")
        self.assertEqual(replace(x, versions=(mapping,)).status, "INCOMPLETE")

    def test_package_coordinate_content_preserved(self):
        recipe = fixture()
        coordinate = PackageCoordinate("apexforge", "evidence", ExactVersion.parse("1.0.0"))
        content = PackageContentIdentity("A" * 64)
        descriptor = replace(recipe.outputs[0].descriptor, package_coordinate=coordinate, package_content=content)
        matrix = r.ReleaseArtifactMatrix(recipe.release, (descriptor,))
        x = m.ReleaseManifest(matrix)
        self.assertEqual(x.record()["descriptors"][0], descriptor.record())
        self.assertIn(content.fingerprint, x.canonical_json())
        changed = replace(descriptor, package_content=PackageContentIdentity("B" * 64))
        self.assertNotEqual(x.fingerprint(), m.ReleaseManifest(replace(matrix, artifacts=(changed,))).fingerprint())

    def test_unexpected_artifacts_invalid(self):
        x, z = evidence(), evidence(count=2)
        self.assertEqual(replace(x, artifacts=z.artifacts).status, "INVALID")

    def test_filename_not_identity(self):
        x = evidence()
        d = x.architecture.artifacts[0]
        changed = replace(d, identity=r.ReleaseArtifactIdentity("other-identity"))
        self.assertEqual(d.filename, changed.filename)
        self.assertEqual(replace(x, architecture=replace(x.architecture, artifacts=(changed,))).status, "INVALID")

    def test_scope_mismatch_invalid(self):
        x = evidence()
        other = CanonicalReference(r.ReleaseArtifactMatrix.DOMAIN, "provenance-scope", "A" * 64)
        self.assertEqual(replace(x, checksums=replace(x.checksums, architecture=other)).status, "INVALID")

    def test_descriptor_distinct_and_not_final_package(self):
        x = evidence()
        self.assertIsNot(type(x.architecture.artifacts[0]), type(x.artifacts.artifacts[0]))
        self.assertEqual(x.record()["target_packaging"], "NOT_ESTABLISHED")
        a = x.artifacts.artifacts[0]
        self.assertNotEqual(m.reference(a), m.reference(a._slot.descriptor))

    def test_no_trust_authority_approval_compatibility(self):
        record = evidence().record()
        for key in ("trusted", "authenticated", "release_approved", "published", "installed", "authority"):
            self.assertFalse(record[key])
        self.assertEqual(record["compatibility"], "NOT_ESTABLISHED")
        self.assertEqual(record["crypto"], "CRYPTO_PROVIDER_UNAVAILABLE")
        self.assertEqual(record["semantic_authority"], "CANONICAL_AIR")

    def test_provenance_not_authorship_or_authentication(self):
        x = evidence()
        self.assertFalse(x.provenance.record()["authenticated"])
        for p in x.provenance.records:
            self.assertEqual(p.record()["authorship"], "NOT_ESTABLISHED")
            self.assertEqual(p.record()["authentication"], "NOT_ESTABLISHED")

    def test_no_build_during_manifest_or_verification(self):
        x = evidence(b"import os; raise Exception('never run')")
        with patch.object(b, "assemble", side_effect=AssertionError("build forbidden")):
            self.assertEqual(x.status, "COMPLETE")
            self.assertTrue(x.fingerprint())
            m.verify_checksum(x.checksums.records[0], x.artifacts.artifacts[0], x.artifacts.artifacts[0].data)

    def test_canonical_serialization_no_host_metadata(self):
        x = evidence()
        encoded = x.canonical_json().encode("utf-8")
        self.assertEqual(encoded, evidence().canonical_json().encode("utf-8"))
        for key in ('"timestamp"', '"hostname"', '"cwd"', '"pid"', '"environment"'):
            self.assertNotIn(key, x.canonical_json())
        # Opaque supplied bytes never enter manifest serialization.
        self.assertNotIn("C:\\host\\secret", evidence(b"C:\\host\\secret").canonical_json())

    def test_bounds_and_exact_types(self):
        x = evidence()
        self.error("RELEASE_CHECKSUM_DUPLICATE_OR_INVALID", lambda: replace(x.checksums, records=x.checksums.records * (m.MAX_RECORDS + 1)))
        self.error("RELEASE_PROVENANCE_DUPLICATE_OR_INVALID", lambda: replace(x.provenance, records=list(x.provenance.records)))
        self.error("RELEASE_MANIFEST_MODEL_INVALID", lambda: replace(x, artifacts=lambda: True))
        class CallerCode:
            def fingerprint(self):
                raise AssertionError("caller method must not run")
        self.error("RELEASE_EVIDENCE_REFERENCE_INVALID", lambda: m.reference(CallerCode()))

    def test_static_security_audit(self):
        tree = ast.parse(Path(m.__file__).read_text(encoding="utf-8"))
        allowed = {"dataclasses", "re", "tooling.domain_platform", "tooling.package_manifest", "tooling", "tooling.release_versioning"}
        forbidden = {"eval", "exec", "open", "compile", "__import__", "assemble", "getenv", "system", "popen"}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                self.assertTrue(all(a.name in allowed for a in node.names))
            elif isinstance(node, ast.ImportFrom):
                self.assertIn(node.module, allowed)
            elif isinstance(node, ast.Call):
                name = node.func.id if isinstance(node.func, ast.Name) else node.func.attr if isinstance(node.func, ast.Attribute) else ""
                self.assertNotIn(name, forbidden)

    def test_thousand_artifact_evidence_independent_determinism(self):
        x, z = evidence(b"tiny", 1000), evidence(b"tiny", 1000)
        self.assertEqual(len(x.checksums.records), 1000)
        self.assertEqual(x.status, "COMPLETE")
        self.assertEqual(x.fingerprint(), z.fingerprint())


if __name__ == "__main__":
    unittest.main()
