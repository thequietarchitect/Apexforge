"""Release inspection fixtures are not claims of locally built VSCE artifacts."""
import ast
from dataclasses import FrozenInstanceError, replace
from io import BytesIO
import json
from pathlib import Path
import stat
import subprocess
import sys
import unittest
from unittest.mock import patch
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED
sys.path.insert(0, str(Path(__file__).resolve().parent))
from tooling import vscode_distribution as v, release_architecture as r, release_build as b, release_manifest as m
from p10_t3_vscode_package_smoke_test import _manifest, _content_types

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "editors/vscode-apexforge"
# Test-only, fixed read-only Git projection. Production has no Git/process API.
FROZEN_SOURCE = tuple((name, subprocess.run(
    ("git", "show", r.P15_COMMIT + ":editors/vscode-apexforge/" + name),
    cwd=ROOT, check=True, capture_output=True).stdout) for name in v.SOURCE_FILES)


def descriptor():
    release = r.ReleaseIdentity("vscode-review", "declared-release-16", "DEVELOPMENT", r.P15_BASELINE)
    return r.ReleaseArtifactDescriptor(release, r.ReleaseArtifactIdentity("vscode-vsix"), r.ReleaseTarget("vscode"),
                                     "VSCODE_EXTENSION", "vsix", v.owner.CANONICAL_VSIX_FILENAME, "0.1.0", "SUPPORTED")


def files():
    return {"[Content_Types].xml": _content_types().encode(), "extension.vsixmanifest": _manifest().encode(),
            **{"extension/" + name: payload for name, payload in FROZEN_SOURCE}}


def archive(rows=None, timestamp=(2000, 1, 1, 0, 0, 0), reverse=False, mode=None):
    rows = list(files().items()) if rows is None else list(rows)
    buffer = BytesIO()
    with ZipFile(buffer, "w", compression=ZIP_DEFLATED) as z:
        for name, data in reversed(rows) if reverse else rows:
            info = ZipInfo(name, timestamp)
            # ZipInfo on Windows normalizes separators at construction. Preserve
            # hostile raw archive names so the reader, not the writer, rejects them.
            info.filename = name
            info.compress_type = ZIP_DEFLATED
            if mode is not None:
                info.external_attr = mode << 16
            z.writestr(info, data)
    return buffer.getvalue()


def evidence(data=None):
    return v.inspect_vsix(ROOT, descriptor(), archive() if data is None else data, tuple(FROZEN_SOURCE))


class ContractTests(unittest.TestCase):
    def error(self, code, callback):
        with self.assertRaises(v.VSCodeDistributionError) as caught:
            callback()
        self.assertEqual(caught.exception.code, code)
        self.assertEqual(str(caught.exception), code)

    def test_immutable_identity_and_evidence(self):
        e = evidence()
        for obj, field in ((e, "data"), (e.identity, "package_json")):
            with self.assertRaises(FrozenInstanceError):
                setattr(obj, field, b"bad")

    def test_exact_metadata_and_distinct_version(self):
        e = evidence()
        info = e.identity.record()
        self.assertEqual(info["extension_id"], "gravitas-studios.apexforge-language")
        self.assertEqual(info["metadata"], json.loads((SOURCE / "package.json").read_bytes()))
        self.assertEqual(info["metadata"]["version"], "0.1.0")
        self.assertEqual(info["metadata"]["engines"]["vscode"], "^1.85.0")
        self.assertNotEqual(e.identity.release.version, "0.1.0")
        self.assertFalse(info["publisher_authenticated"])

    def test_exact_baseline_required(self):
        changed = replace(r.P15_BASELINE, commit="0" * 40)
        release = replace(descriptor().release, baseline=changed)
        self.error("VSCODE_RELEASE_BINDING_INVALID", lambda: v.VSCodeDistributionIdentity(release, (SOURCE / "package.json").read_bytes()))

    def test_release_revision_reidentifies(self):
        e = evidence()
        other = replace(e.identity, release=replace(e.identity.release, version="other-declared"))
        self.assertNotEqual(other.fingerprint(), e.identity.fingerprint())
        self.error("VSCODE_RELEASE_BINDING_INVALID", lambda: replace(e, identity=other))

    def test_descriptor_wrong_surface_rejected(self):
        e = evidence()
        self.error("VSCODE_RELEASE_BINDING_INVALID", lambda: replace(e, descriptor=replace(e.descriptor, surface_version="0.2.0")))

    def test_dynamic_version_not_substituted(self):
        raw = json.loads((SOURCE / "package.json").read_bytes())
        raw["version"] = "16.6"
        self.error("VSCODE_METADATA_MISMATCH", lambda: v.VSCodeDistributionIdentity(descriptor().release, json.dumps(raw).encode()))

    def test_owner_audits_reused(self):
        with patch.object(v.owner, "audit_vscode_vsix", wraps=v.owner.audit_vscode_vsix) as t3, \
             patch.object(v.activation, "audit_vscode_lsp_vsix", wraps=v.activation.audit_vscode_lsp_vsix) as t4:
            evidence()
            self.assertEqual(t3.call_count, 1)
            self.assertEqual(t4.call_count, 1)

    def test_frozen_manifest_rejection(self):
        rows = files()
        rows["extension.vsixmanifest"] = _manifest().replace('Version="0.1.0"', 'Version="9.9.9"').encode()
        self.error("VSCODE_FROZEN_OWNER_REJECTED", lambda: evidence(archive(rows.items())))

    def test_expected_structure_and_source_bytes(self):
        e = evidence()
        with ZipFile(BytesIO(e.data)) as z:
            self.assertEqual(len(z.infolist()), 10)
            for name in v.SOURCE_FILES:
                self.assertEqual(z.read("extension/" + name), dict(FROZEN_SOURCE)[name])
        settings = e.identity.record()["metadata"]
        self.assertEqual(settings["main"], "./extension.js")
        self.assertIn("onLanguage:apexforge", settings["activationEvents"])
        self.assertEqual(settings["contributes"]["configuration"]["properties"]["apexforge.languageServer.serverPath"]["default"], "apexforge/apexforge_lsp.py")

    def test_source_substitution_rejected(self):
        for name in ("package.json", "extension.js", "runtime/lsp-client.js", "LANGUAGE_SERVER.md"):
            rows = files()
            rows["extension/" + name] += b"\n"
            self.error("VSCODE_SOURCE_CONTINUITY_MISMATCH", lambda: evidence(archive(rows.items())))

    def test_missing_runtime_not_fabricated(self):
        rows = files()
        del rows["extension/runtime/lsp-client.js"]
        self.error("VSCODE_SOURCE_CONTINUITY_MISMATCH", lambda: evidence(archive(rows.items())))

    def test_direct_evidence_constructor_cannot_bypass_manifest_owner(self):
        e = evidence()
        rows = files()
        rows["extension.vsixmanifest"] = _manifest().replace('Version="0.1.0"', 'Version="9.9.9"').encode()
        self.error("VSCODE_FROZEN_OWNER_REJECTED", lambda: replace(e, data=archive(rows.items())))

    def test_unsafe_paths(self):
        for path in ("../evil", "/evil", "C:/evil", "extension/../evil", "extension\\evil", "extension//evil", "./evil", "evil\x01"):
            with self.subTest(path=path):
                self.error("VSCODE_ARCHIVE_PATH_INVALID", lambda: v.inventory(archive([(path, b"x")])))

    def test_case_collisions(self):
        self.error("VSCODE_ARCHIVE_DUPLICATE", lambda: v.inventory(archive([("A", b"a"), ("a", b"b")])))

    def test_file_directory_collision(self):
        for rows in ([('a', b'x'), ('a/b', b'y')], [('a/b', b'y'), ('a', b'x')]):
            self.error("VSCODE_ARCHIVE_PATH_INVALID", lambda: v.inventory(archive(rows)))

    def test_unsafe_link_rejected(self):
        self.error("VSCODE_ARCHIVE_LINK_INVALID", lambda: v.inventory(archive([("link", b"target")], mode=stat.S_IFLNK | 0o777)))

    def test_oversized_member(self):
        self.error("VSCODE_ARCHIVE_SIZE_INVALID", lambda: v.inventory(archive([("large", b"x" * (v.MAX_MEMBER + 1))])))

    def test_bounded_archive_and_count(self):
        self.error("VSCODE_ARCHIVE_SIZE_INVALID", lambda: v.inventory(b"x" * (v.MAX_BYTES + 1)))
        self.error("VSCODE_ARCHIVE_SIZE_INVALID", lambda: v.inventory(archive([(f"n{i}", b"x") for i in range(v.MAX_MEMBERS + 1)])))

    def test_residue_rejected(self):
        for path in (".git/config", "extension/__pycache__/x", "extension/x.pyc", "extension/old.vsix", "extension/node_modules/a", "dist/a"):
            self.error("VSCODE_ARCHIVE_RESIDUE", lambda: v.inventory(archive([(path, b"x")])))

    def test_malformed_archive(self):
        self.error("VSCODE_ARCHIVE_INVALID", lambda: v.inventory(b"not zip"))

    def test_duplicate_json_and_malformed_utf8(self):
        for data in (b'{"a":1,"a":2}', b'\xff', b'{"n":NaN}', b'{"n":1.5}'):
            self.error("VSCODE_METADATA_INVALID", lambda: v.metadata(data))

    def test_xml_entity_rejected(self):
        self.error("VSCODE_XML_INVALID", lambda: v.inventory(archive([("extension.vsixmanifest", b'<!DOCTYPE x [<!ENTITY y "z">]>') ])))

    def test_independent_equivalent_construction(self):
        left, right = evidence(archive()), evidence(archive())
        self.assertIsNot(left, right)
        self.assertEqual(left.fingerprint(), right.fingerprint())
        self.assertEqual(v.compare_packages(left, right), {"context_equal": True, "member_content_equal": True, "raw_bytes_equal": True, "authentication": False})

    def test_timestamp_gap_not_hidden(self):
        left, right = evidence(), evidence(archive(timestamp=(2001, 2, 3, 4, 5, 6)))
        comparison = v.compare_packages(left, right)
        self.assertTrue(comparison["member_content_equal"])
        self.assertFalse(comparison["raw_bytes_equal"])
        self.assertNotEqual(left.fingerprint(), right.fingerprint())

    def test_order_gap_not_hidden(self):
        left, right = evidence(), evidence(archive(reverse=True))
        self.assertTrue(v.compare_packages(left, right)["member_content_equal"])
        self.assertFalse(v.compare_packages(left, right)["raw_bytes_equal"])
        self.assertNotEqual(left.record()["archive_order"], right.record()["archive_order"])

    def test_source_ledger_order_canonical(self):
        e = evidence()
        self.assertEqual(e.fingerprint(), replace(e, source_files=tuple(reversed(e.source_files))).fingerprint())

    def test_frozen_source_substitution_rejected_even_when_archive_matches(self):
        e = evidence()
        changed = tuple((name, payload + b"\n" if name == "extension.js" else payload) for name, payload in FROZEN_SOURCE)
        rows = files()
        rows["extension/extension.js"] = dict(changed)["extension.js"]
        self.error("VSCODE_FROZEN_SOURCE_MISMATCH", lambda: replace(e, source_files=changed, data=archive(rows.items())))

    def test_host_checkout_bytes_not_silently_normalized(self):
        checkout = tuple((name, (SOURCE / name).read_bytes()) for name in v.SOURCE_FILES)
        if checkout != FROZEN_SOURCE:
            rows = {"[Content_Types].xml": _content_types().encode(), "extension.vsixmanifest": _manifest().encode(),
                    **{"extension/" + name: payload for name, payload in checkout}}
            self.error("VSCODE_FROZEN_SOURCE_MISMATCH", lambda: v.inspect_vsix(ROOT, descriptor(), archive(rows.items())))
        self.assertEqual(tuple(v.digest(data) for _, data in FROZEN_SOURCE), v.FROZEN_SOURCE_DIGESTS)

    def test_build_and_manifest_integration(self):
        e = evidence()
        artifact = e.build_artifact()
        self.assertEqual(artifact.data, e.data)
        self.assertEqual(artifact.declared_digest, v.digest(e.data))
        matrix = r.ReleaseArtifactMatrix(e.identity.release, (e.descriptor,))
        artifacts = b.ReleaseArtifactSet(e.identity.release, (artifact.recipe,), (artifact,))
        checksums = m.ReleaseChecksumSet(e.identity.release, m.reference(matrix), (m.checksum_for(artifact),))
        lineage = m.required_lineage(matrix, artifacts, checksums)
        records = tuple(m.ReleaseProvenanceRecord("e" + str(i), e.identity.release, kind, subject, predecessors)
                        for i, (kind, subject, predecessors) in enumerate(lineage))
        manifest = m.ReleaseManifest(matrix, artifacts, checksums, m.ReleaseProvenanceBundle(e.identity.release, records))
        self.assertEqual(manifest.evaluate()[0], "COMPLETE")
        self.assertEqual(artifact.recipe.inputs[0].source.fingerprint, e.fingerprint())

    def test_no_trust_authority_or_execution(self):
        e = evidence()
        for name in ("grants_trust", "grants_authority", "grants_compatibility", "installed", "published", "executed"):
            self.assertFalse(e.record()[name])
        self.assertEqual(e.record()["authentication"], "CRYPTO_PROVIDER_UNAVAILABLE")

    def test_owner_execution_apis_never_called(self):
        with patch.object(v.owner, "package_vscode_extension", side_effect=AssertionError("must not fetch")), \
             patch.object(v.activation, "check_node_syntax", side_effect=AssertionError("must not execute")):
            evidence()

    def test_scale_inventory_deterministic(self):
        rows = [(f"extension/resource-{i:04}.txt", b"opaque") for i in range(1000)]
        a, _ = v.inventory(archive(rows))
        c, _ = v.inventory(archive(rows, reverse=True))
        self.assertEqual(a, c)
        self.assertEqual(len(a), 1000)

    def test_static_security_audit(self):
        tree = ast.parse(Path(v.__file__).read_text(encoding="utf-8"))
        imports = {n.name.split('.')[0] for node in ast.walk(tree) if isinstance(node, ast.Import) for n in node.names}
        self.assertFalse(imports & {"subprocess", "socket", "urllib", "requests", "pickle", "importlib", "os"})
        calls = {node.func.id for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)}
        self.assertFalse(calls & {"eval", "exec", "__import__"})
        attributes = {node.func.attr for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)}
        self.assertFalse(attributes & {"rglob", "walk", "system", "run", "Popen", "package_vscode_extension", "install_vscode_extension", "check_node_syntax"})


if __name__ == "__main__":
    unittest.main()
