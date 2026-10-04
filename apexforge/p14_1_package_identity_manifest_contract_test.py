"""Focused P14.1 identity/manifest/security and frozen-model coexistence gates."""
from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, replace
from hashlib import sha256
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import tooling.package_manifest as pm
from language.identities import ProjectDeclaredIdentity
from language.source import SourceText
from rich_documents.model import PackageDescriptor, PackageTier
from tooling.project_manifest import ProjectManifest

H1 = "A" * 64
H2 = "B" * 64


def coordinate(name="sample", version="1.2.3", namespace="apexforge.example"):
    return pm.PackageCoordinate(namespace, name, pm.ExactVersion.parse(version))


def member(path="src/main.apex", digest=H1, kind="source"):
    return pm.ContentDescriptor(pm.PackagePath(path), digest, kind)


def symbol(name="Main", kind="directive", digest=H1):
    return pm.SymbolReference(digest, kind, kind + ":" + name, "sample.module")


def rich_manifest(reverse=False):
    reverse_if = lambda xs: tuple(reversed(xs)) if reverse else tuple(xs)
    return pm.PackageManifest(coordinate(),
        content=reverse_if((member(), member("docs/guide.apexdoc", H2, "document"))),
        tier=PackageTier.DOMAIN, documents=(pm.PackagePath("docs/guide.apexdoc"),),
        dependencies=reverse_if((coordinate("alpha"), coordinate("beta"))),
        exports=reverse_if((symbol(), symbol("Helper", "function"))),
        entrypoints=(symbol(),),
        exported_capabilities=reverse_if(("state.read", "trace.inspect")),
        required_capabilities=reverse_if(("files.read", "network.observe")),
        provenance=reverse_if((pm.CanonicalReference("apexforge.trace-retention/v1", "provenance-scope", H1),
            pm.CanonicalReference("apexforge.build-artifact/v3", "artifact", H2))),
        metadata=reverse_if((("title", "Sample package"), ("description", "Read-only declaration"))))


class PackageManifestTests(unittest.TestCase):
    def rejects(self, fn, *args, code=None, **kwargs):
        with self.assertRaises(pm.PackageManifestError) as caught:
            fn(*args, **kwargs)
        if code is not None:
            self.assertEqual(caught.exception.code, code)
        return caught.exception

    def test_minimal_manifest_and_empty_explicit_boundary(self):
        manifest = pm.PackageManifest(coordinate())
        self.assertEqual(manifest.coordinate.version.text(), "1.2.3")
        self.assertEqual(manifest.canonical_record()["content"], [])
        self.assertEqual(pm.parse_manifest(manifest.to_json()), manifest)

    def test_namespace_exact_lowercase_module_compatible_grammar(self):
        self.assertEqual(coordinate(namespace="domain._tools").namespace, "domain._tools")
        for bad in ("", "Domain", "domain..tools", "org-name", "org/name", "éxample", " org", "a." ):
            with self.subTest(bad=bad):
                self.rejects(coordinate, namespace=bad, code="PACKAGE_NAMESPACE_INVALID")

    def test_name_policy_no_silent_separator_case_or_unicode_repair(self):
        self.assertNotEqual(coordinate("a-b"), coordinate("a_b"))
        for bad in ("Name", "a--b", "a__b", "a.", "a/b", "name ", "é", "1name", "a" * 65):
            with self.subTest(bad=bad):
                self.rejects(coordinate, bad, code="PACKAGE_NAME_INVALID")

    def test_exact_numeric_release_and_bounds(self):
        self.assertEqual(pm.ExactVersion.parse("0.0.0"), pm.ExactVersion(0, 0, 0))
        for bad in ("1", "2026.1", "v1", "01.2.3", "1.2.3-beta", "1.2.3+build", "^1.2.3", "1.2.3 ", "2147483648.0.0"):
            with self.subTest(bad=bad):
                self.rejects(pm.ExactVersion.parse, bad, code="PACKAGE_VERSION_INVALID")
        self.rejects(pm.ExactVersion, True, 1, 0)
        self.rejects(pm.ExactVersion, -1, 0, 0)

    def test_schema_is_not_release_version(self):
        c = coordinate()
        self.assertNotEqual(c.schema, c.version.text())
        self.rejects(replace, c, schema="apexforge.package/v2", code="MANIFEST_SCHEMA_UNKNOWN")
        self.rejects(replace, c, version="1.2.3")

    def test_coordinate_canonical_record_and_content_identity_separation(self):
        c = coordinate()
        self.assertEqual(c.record(), {"schema": pm.SCHEMA, "namespace": "apexforge.example",
                                     "name": "sample", "version": "1.2.3"})
        a = pm.PackageManifest(c, (member(),))
        b = replace(a, content=(member(digest=H2),))
        self.assertEqual(a.coordinate, b.coordinate)
        self.assertNotEqual(a.content_identity(), b.content_identity())
        self.assertNotEqual(c, a.content_identity())

    def test_safe_logical_path_is_not_host_path(self):
        path = pm.PackagePath("src/main.apex")
        self.assertEqual(path.value, "src/main.apex")
        self.assertNotEqual(path, Path("src/main.apex"))
        self.assertFalse(hasattr(path, "read_bytes"))

    def test_unsafe_paths_reject_without_normalization(self):
        for bad in ("", "/a", "//server/file", "C:/a", "C:a", "../a", "a/../b", "./a", "a//b",
                    "a\\b", "a/", "a/ b", "a/b ", "a./b", "CON.txt", "aux", "a:stream", "é.apex"):
            with self.subTest(bad=bad):
                self.rejects(pm.PackagePath, bad, code="PACKAGE_PATH_INVALID")

    def test_duplicate_and_case_colliding_member_paths(self):
        self.rejects(pm.PackageManifest, coordinate(), (member(), member()), code="PACKAGE_PATH_DUPLICATE")
        self.rejects(pm.PackageManifest, coordinate(), (member("A.apex"), member("a.apex")),
                     code="PACKAGE_PATH_DUPLICATE")

    def test_member_cannot_also_be_an_ancestor_directory(self):
        for parent in ("src", "SRC"):
            self.rejects(pm.PackageManifest, coordinate(), (member(parent), member("src/main.apex")),
                         code="PACKAGE_PATH_CONFLICT")

    def test_content_order_and_digest_reference_are_distinct(self):
        ref = pm.CanonicalReference("apexforge.metadata-identity/v1", "source", H2)
        a = pm.ContentDescriptor(pm.PackagePath("a.apex"), H1, "source", ref)
        b = member("z.apex")
        first = pm.PackageManifest(coordinate(), (b, a))
        second = pm.PackageManifest(coordinate(), (a, b))
        self.assertEqual(first, second)
        self.assertEqual(first.content[0].digest, H1)
        self.assertEqual(first.content[0].reference.fingerprint, H2)

    def test_document_order_is_semantic_and_boundary_complete(self):
        a, b = member("a.apexdoc", H1, "document"), member("b.apexdoc", H2, "document")
        first = pm.PackageManifest(coordinate(), (b, a), PackageTier.STANDARD, (a.path, b.path))
        second = replace(first, documents=(b.path, a.path))
        self.assertEqual(first.content, second.content)
        self.assertNotEqual(first.content_identity(), second.content_identity())
        self.rejects(replace, first, documents=(a.path,), code="PACKAGE_DOCUMENT_BOUNDARY_MISMATCH")
        self.rejects(replace, first, documents=(a.path, a.path), code="PACKAGE_DOCUMENT_DUPLICATE")
        self.rejects(member, "a.APEXDOC", H1, "document", code="PACKAGE_DOCUMENT_INVALID")

    def test_dependency_order_and_inert_exact_coordinates(self):
        a = pm.PackageManifest(coordinate(), dependencies=(coordinate("z"), coordinate("a")))
        b = replace(a, dependencies=tuple(reversed(a.dependencies)))
        self.assertEqual(a, b)
        self.assertEqual(a.dependencies[0].name, "a")
        self.assertFalse(hasattr(a, "resolve"))
        self.assertTrue(all(type(x) is pm.PackageCoordinate for x in a.dependencies))

    def test_duplicate_or_conflicting_dependency_versions_reject(self):
        for second in (coordinate("dependency"), coordinate("dependency", "2.0.0")):
            with self.subTest(second=second):
                self.rejects(pm.PackageManifest, coordinate(), dependencies=(coordinate("dependency"), second),
                             code="PACKAGE_DEPENDENCY_CONFLICT")

    def test_export_order_and_duplicate_symbol_reject(self):
        a = pm.PackageManifest(coordinate(), exports=(symbol("Z"), symbol("A")))
        self.assertEqual(a.exports[0].identity, "directive:A")
        self.rejects(replace, a, exports=(symbol(), symbol()), code="PACKAGE_SYMBOL_DUPLICATE")
        self.rejects(replace, a, exports=(symbol(), symbol(digest=H2)), code="PACKAGE_SYMBOL_DUPLICATE")

    def test_existing_declared_identity_adapter_does_not_relabel(self):
        source = SourceText("src/main.apex", "Main")
        declared = ProjectDeclaredIdentity("directive", "Main", "directive:Main", source.name,
            "app.main", "app.main.Main", source.span(0, 4))
        ref = pm.SymbolReference.from_declared(declared, H1)
        self.assertEqual(ref.identity, declared.current_air_id)
        self.assertEqual(ref.module, declared.module_name)
        self.assertEqual(ref.air_fingerprint, H1)
        self.rejects(pm.SymbolReference, H1, "directive", "function:Main")
        self.rejects(pm.SymbolReference, H1, "class", "class:Main")

    def test_entrypoints_are_structural_directive_references(self):
        a = pm.PackageManifest(coordinate(), entrypoints=(symbol(),))
        self.assertEqual(a.entrypoints[0].identity, "directive:Main")
        self.rejects(replace, a, entrypoints=(symbol("Func", "function"),), code="PACKAGE_ENTRYPOINT_INVALID")
        self.assertFalse(hasattr(a, "execute"))

    def test_capability_order_and_no_authority_grant(self):
        a = pm.PackageManifest(coordinate(), exported_capabilities=("state.write", "files.read"),
                               required_capabilities=("state.write",))
        self.assertEqual(a.exported_capabilities, ("files.read", "state.write"))
        self.assertEqual(a.required_capabilities, ("state.write",))
        # Exporting and requiring the same capability is not a contradiction or a grant.
        self.assertFalse(hasattr(a, "authorize"))
        self.assertFalse(hasattr(a, "principal"))
        self.rejects(replace, a, required_capabilities=("x", "x"), code="PACKAGE_CAPABILITY_DUPLICATE")
        self.rejects(replace, a, exported_capabilities=("*",), code="PACKAGE_CAPABILITY_INVALID")

    def test_independent_equivalent_records_serialization_and_identity(self):
        a, b = rich_manifest(), rich_manifest(True)
        self.assertEqual(a, b)
        self.assertEqual(a.canonical_record(), b.canonical_record())
        self.assertEqual(a.canonical_json(), b.canonical_json())
        self.assertEqual(a.to_json(), b.to_json())
        self.assertEqual(a.content_identity(), b.content_identity())
        self.assertEqual(pm.parse_manifest(a.to_json()), a)

    def test_fingerprint_domain_and_sha256_preimage(self):
        a = rich_manifest()
        expected = sha256((pm.FINGERPRINT_DOMAIN + "\0" + a.canonical_json()).encode("utf-8")).hexdigest().upper()
        self.assertEqual(a.content_identity().fingerprint, expected)
        self.assertNotEqual(expected, sha256(a.canonical_json().encode("utf-8")).hexdigest().upper())
        self.rejects(pm.PackageContentIdentity, expected, "artifact")

    def test_every_identity_field_changes_manifest_fingerprint(self):
        a = rich_manifest()
        changes = (replace(a, coordinate=coordinate("other")),
            replace(a, coordinate=coordinate(version="1.2.4")),
            replace(a, coordinate=coordinate(namespace="other")),
            replace(a, content=(member(digest=H2),) + a.content[:1]),
            replace(a, tier=PackageTier.CORE), replace(a, dependencies=(coordinate("other"),)),
            replace(a, exports=(symbol("Other"),)), replace(a, entrypoints=(symbol("Other"),)),
            replace(a, exported_capabilities=("other.export",)),
            replace(a, required_capabilities=("other.require",)), replace(a, provenance=()))
        for changed in changes:
            with self.subTest(record=changed.canonical_record()):
                self.assertNotEqual(a.content_identity(), changed.content_identity())

    def test_non_identity_metadata_preserved_but_excluded(self):
        a = rich_manifest()
        b = replace(a, metadata=(("title", "Different title"), ("authors", "Display author")))
        self.assertNotEqual(a.to_json(), b.to_json())
        self.assertEqual(a.canonical_json(), b.canonical_json())
        self.assertEqual(a.content_identity(), b.content_identity())
        self.assertEqual(pm.parse_manifest(b.to_json()).metadata, b.metadata)

    def test_volatile_fields_and_unknown_extensions_fail_closed(self):
        for key in ("timestamp", "pid", "mtime", "username", "host_path", "extensions", "signature", "kind"):
            with self.subTest(key=key):
                v = rich_manifest().to_mapping(); v[key] = "untrusted"
                self.rejects(pm.PackageManifest.from_mapping, v, code="MANIFEST_FIELD_UNKNOWN")
        v = rich_manifest().to_mapping(); v["metadata"]["timestamp"] = "now"
        self.rejects(pm.PackageManifest.from_mapping, v, code="PACKAGE_METADATA_INVALID")

    def test_malformed_hash_and_reference_validation(self):
        for bad in ("a" * 64, "A" * 63, "G" * 64, "sha256:" + H1, None):
            with self.subTest(bad=bad):
                self.rejects(member, digest=bad, code="PACKAGE_HASH_INVALID")
        self.rejects(pm.CanonicalReference, "file:///untrusted", "source", H1)
        self.rejects(pm.CanonicalReference, "apexforge.source/v1", "human-attribution", H1)
        self.rejects(pm.SymbolReference, H1, "directive", "directive:../../Main")

    def test_existing_source_fingerprint_provenance_reference_is_passive(self):
        from tooling.debug_metadata import SourceIdentity, SCHEMA as SOURCE_SCHEMA
        source = SourceIdentity.from_bytes("src/main.apex", b"directive Main {}")
        before = source.canonical_identity()
        ref = pm.CanonicalReference(SOURCE_SCHEMA, "source", source.fingerprint())
        a = pm.PackageManifest(coordinate(), content=(pm.ContentDescriptor(pm.PackagePath(source.logical_name),
            source.content_fingerprint, "source", ref),), provenance=(ref,))
        self.assertEqual(a.provenance[0].fingerprint, source.fingerprint())
        self.assertEqual(source.canonical_identity(), before)
        self.assertFalse(hasattr(ref, "verify_trust"))
        self.assertFalse(hasattr(ref, "load"))

    def test_missing_required_and_unknown_schema_reject(self):
        for key in ("schema", "namespace", "name", "version", "content"):
            v = rich_manifest().to_mapping(); del v[key]
            self.rejects(pm.PackageManifest.from_mapping, v, code="MANIFEST_FIELD_MISSING")
        v = rich_manifest().to_mapping(); v["schema"] = "apexforge.package/v999"
        self.rejects(pm.PackageManifest.from_mapping, v, code="MANIFEST_SCHEMA_UNKNOWN")
        v = rich_manifest().to_mapping(); v["tier"] = "privileged"
        self.rejects(pm.PackageManifest.from_mapping, v, code="PACKAGE_TIER_INVALID")

    def test_nested_unknown_fields_and_wrong_json_shapes_reject(self):
        for field in ("content", "dependencies", "exports", "provenance"):
            v = rich_manifest().to_mapping(); v[field][0]["unknown"] = "x"
            self.rejects(pm.PackageManifest.from_mapping, v, code="MANIFEST_FIELD_UNKNOWN")
        for field in ("content", "documents", "dependencies", "exports", "entrypoints", "provenance"):
            v = rich_manifest().to_mapping(); v[field] = {}
            self.rejects(pm.PackageManifest.from_mapping, v, code="MANIFEST_ARRAY_REQUIRED")
        self.rejects(pm.PackageManifest.from_mapping, [])
        self.rejects(pm.PackageManifest.from_mapping, {1: "unknown"})

    def test_json_duplicate_keys_root_and_nested_reject(self):
        self.rejects(pm.parse_manifest, '{"schema":"a","schema":"b"}', code="MANIFEST_JSON_DUPLICATE_KEY")
        text = rich_manifest().to_json().replace('"title":"Sample package"', '"title":"first","title":"second"')
        self.rejects(pm.parse_manifest, text, code="MANIFEST_JSON_DUPLICATE_KEY")

    def test_json_malformed_nonfinite_invalid_unicode_and_size_reject(self):
        for text in ("{", "[]", "null", '{"schema":NaN}', "\ud800"):
            with self.subTest(text=text):
                self.rejects(pm.parse_manifest, text)
        self.rejects(pm.parse_manifest, " " * (pm.MAX_JSON_BYTES + 1), code="MANIFEST_JSON_TOO_LARGE")

    def test_oversized_json_integer_has_fixed_validation_error(self):
        self.rejects(pm.parse_manifest, '{"schema":' + "9" * 5000 + '}', code="MANIFEST_JSON_INVALID")

    def test_immutable_models_and_detached_records(self):
        a = rich_manifest()
        with self.assertRaises(FrozenInstanceError):
            a.tier = PackageTier.CORE
        with self.assertRaises(FrozenInstanceError):
            a.coordinate.namespace = "other"
        record = a.canonical_record(); record["content"][0]["digest"] = H1
        self.assertNotEqual(record, a.canonical_record())
        self.rejects(replace, a, content=list(a.content), code="MANIFEST_IMMUTABLE_RECORD_REQUIRED")
        self.rejects(replace, a, metadata=[["title", "mutable"]])

    def test_identity_does_not_contain_machine_or_volatile_fields(self):
        record = rich_manifest().canonical_record()
        for forbidden in ("timestamp", "mtime", "username", "pid", "host_path", "metadata"):
            self.assertNotIn(forbidden, record)
        self.assertNotIn("\\", rich_manifest().canonical_json())
        self.assertNotIn("C:/", rich_manifest().canonical_json())

    def test_diagnostics_do_not_echo_untrusted_values(self):
        secret = "PRIVATE_PACKAGE_SENTINEL_91"
        error = self.rejects(pm.PackagePath, "../" + secret)
        self.assertNotIn(secret, str(error))
        self.assertNotIn(secret, repr(error))

    def test_frozen_p11_project_and_document_descriptor_coexist(self):
        old = PackageDescriptor("legacy-docs", PackageTier.DOMAIN, "2026.1",
                                ("docs/z.apexdoc", "docs/a.apexdoc"))
        project = ProjectManifest("Legacy", old.documents, package=old)
        before = project.canonical_json()
        p14 = pm.PackageManifest(coordinate(), (member("docs/z.apexdoc", H1, "document"),
             member("docs/a.apexdoc", H2, "document")), old.tier,
             tuple(pm.PackagePath(x) for x in old.documents))
        self.assertEqual(p14.documents[0].value, old.documents[0])
        self.assertEqual(project.canonical_json(), before)
        self.assertEqual(ProjectManifest.from_mapping(project.to_mapping()), project)
        self.assertEqual(old.version, "2026.1")
        self.assertNotEqual(old, p14)

    def test_package_not_principal_role_authority_archive_or_artifact(self):
        from authority.model import Principal, AuthorityGrant
        a = rich_manifest()
        self.assertNotEqual(a, Principal("sample"))
        self.assertNotEqual(a, AuthorityGrant("sample", "state.write"))
        self.assertNotEqual(a, a.content[0])
        self.assertNotEqual(a, a.coordinate)
        for name in ("organization", "principal", "role", "archive", "install", "publish",
                     "resolve", "sign", "grant_authority", "run", "execute"):
            self.assertFalse(hasattr(a, name))

    def test_static_and_dynamic_execution_io_separation(self):
        tree = ast.parse(Path(pm.__file__).read_text(encoding="utf-8"))
        imports = {x.module for x in ast.walk(tree) if isinstance(x, ast.ImportFrom)}
        imports.update(alias.name for x in ast.walk(tree) if isinstance(x, ast.Import) for alias in x.names)
        self.assertEqual(imports, {"__future__", "dataclasses", "hashlib", "json", "re",
                                  "language.identities", "rich_documents.model"})
        forbidden = {"eval", "exec", "__import__", "open", "run_air_program", "execute", "dispatch",
                     "Popen", "system", "load_project", "import_module", "AuthorityEngine", "RuntimeEngine"}
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                name = node.func.id if isinstance(node.func, ast.Name) else getattr(node.func, "attr", "")
                self.assertNotIn(name, forbidden)
        supplied = rich_manifest().to_json()
        with patch("builtins.open", side_effect=AssertionError("IO forbidden")), \
             patch("subprocess.run", side_effect=AssertionError("process forbidden")), \
             patch("socket.socket", side_effect=AssertionError("network forbidden")):
            a = pm.parse_manifest(supplied)
            self.assertEqual(a, rich_manifest(True))
            self.assertEqual(a.content_identity(), rich_manifest(True).content_identity())


if __name__ == "__main__":
    unittest.main()
