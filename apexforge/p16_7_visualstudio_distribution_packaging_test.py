"""P16.7 data fixtures are not claims of actual compiled VSIX artifacts."""
import ast
from dataclasses import FrozenInstanceError, replace
from io import BytesIO
from pathlib import Path
import stat
import subprocess
import sys
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED
sys.path.insert(0, str(Path(__file__).resolve().parent))
from tooling import visualstudio_distribution as v, release_architecture as r, release_build as b, release_manifest as m

ROOT = Path(__file__).resolve().parent.parent
# Test-only fixed read-only Git projection, no production Git/discovery API.
FROZEN = tuple((name, subprocess.run(("git", "show", r.P15_COMMIT + ":editors/visualstudio-apexforge/" + name),
                 cwd=ROOT, check=True, capture_output=True).stdout) for name in v.SOURCE_FILES)
DLL = b"MZ\x90\x00P16.7 explicit synthetic assembly fixture, never load"


def identity():
    return v.VisualStudioDistributionIdentity(r.ReleaseIdentity("vs-review", "declared-release-16", "DEVELOPMENT", r.P15_BASELINE), tuple(FROZEN))


def descriptor(ident):
    return r.ReleaseArtifactDescriptor(ident.release, r.ReleaseArtifactIdentity("visual-studio-vsix"), r.ReleaseTarget("visual-studio"),
             "VISUAL_STUDIO_EXTENSION", "vsix", "ApexForge.VisualStudio.vsix", "0.1.0", "SUPPORTED")


def manifest():
    root = ET.fromstring(dict(FROZEN)[v.MANIFEST])
    for item, (_, path) in zip(v.owner._children_by_name(root, "Asset"), v.owner._PACKAGED_MANIFEST_ASSETS):
        item.set("Path", path)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def rows():
    return [("extension.vsixmanifest", manifest()), ("ApexForge.VisualStudio.dll", DLL),
            ("ApexForge.VisualStudio.pkgdef", b'[$RootKey$\\Packages\\{DF54A578-54A2-52F4-8643-4A85DDDFB2F2}]\n'),
            ("[Content_Types].xml", b'<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"/>')]


def archive(files=None, timestamp=(2000, 1, 1, 0, 0, 0), reverse=False, mode=None):
    files = rows() if files is None else list(files)
    out = BytesIO()
    with ZipFile(out, "w", compression=ZIP_DEFLATED) as z:
        for name, data in reversed(files) if reverse else files:
            info = ZipInfo(name, timestamp)
            info.filename = name  # Preserve raw hostile separators on Windows.
            info.compress_type = ZIP_DEFLATED
            if mode is not None:
                info.external_attr = mode << 16
            z.writestr(info, data)
    return out.getvalue()


def evidence(data=None, assembly=DLL):
    ident = identity()
    return v.VisualStudioVSIXEvidence(ident, descriptor(ident), archive() if data is None else data, assembly, v.digest(assembly))


class ContractTests(unittest.TestCase):
    def error(self, code, callback):
        with self.assertRaises(v.VisualStudioDistributionError) as caught:
            callback()
        self.assertEqual(caught.exception.code, code)
        self.assertEqual(str(caught.exception), code)

    def test_identity_and_evidence_immutable(self):
        e = evidence()
        for obj, attr in ((e, "data"), (e.identity, "files")):
            with self.assertRaises(FrozenInstanceError):
                setattr(obj, attr, b"no")

    def test_exact_metadata_and_distinct_version_domain(self):
        e = evidence()
        record = e.identity.record()
        self.assertEqual(record["extension_id"], "GravitasStudios.ApexForge.VisualStudio")
        self.assertEqual(record["extension_version"], "0.1.0")
        self.assertEqual(record["version_domain"], "VISUAL_STUDIO_EXTENSION")
        self.assertNotEqual(record["release"]["declared_version"], "0.1.0")
        self.assertFalse(record["publisher_authenticated"])
        source = v.xml(dict(FROZEN)[v.MANIFEST])
        self.assertEqual(v.owner._manifest_identity(source, "source").attrib["Publisher"], "Gravitas Studios")
        self.assertEqual([(e.attrib["Id"], e.attrib["Version"]) for e in v.owner._children_by_name(source, "InstallationTarget")],
                         [("Microsoft.VisualStudio.Community", "[17.0,)"), ("Microsoft.VisualStudio.Community", "[17.0,)")])

    def test_project_and_package_metadata_preserved(self):
        project = v.xml(dict(FROZEN)[v.PROJECT])
        properties = {e.tag: (e.text or "").strip() for e in project.iter()}
        self.assertEqual(properties["TargetFramework"], "net472")
        self.assertEqual(properties["Deterministic"], "true")
        self.assertEqual(properties["AssemblyName"], "ApexForge.VisualStudio")
        self.assertEqual(properties["DeployExtension"], "false")
        self.assertEqual({e.attrib["Include"]: e.attrib["Version"] for e in project.iter("PackageReference")},
                         {"Microsoft.VisualStudio.SDK": "17.14.40265", "Microsoft.VisualStudio.LanguageServer.Client": "17.14.60", "Microsoft.VSSDK.BuildTools": "18.5.40034"})

    def test_exact_p15_binding(self):
        ident = identity()
        self.error("VISUAL_STUDIO_RELEASE_BINDING_INVALID", lambda: replace(ident, release=replace(ident.release, baseline=replace(r.P15_BASELINE, commit="0" * 40))))

    def test_release_revision_changes_identity_and_rejects_replay(self):
        e = evidence()
        changed = replace(e.identity, release=replace(e.identity.release, version="declared-other"))
        self.assertNotEqual(changed.fingerprint(), e.identity.fingerprint())
        self.error("VISUAL_STUDIO_RELEASE_BINDING_INVALID", lambda: replace(e, identity=changed))

    def test_wrong_surface_version_rejected(self):
        e = evidence()
        self.error("VISUAL_STUDIO_RELEASE_BINDING_INVALID", lambda: replace(e, descriptor=replace(e.descriptor, surface_version="10.1.3")))

    def test_source_substitution_and_crlf_rejected(self):
        for transform in (lambda data: data + b"\n", lambda data: data.replace(b"\n", b"\r\n")):
            changed = tuple((name, transform(data) if name == v.PROJECT else data) for name, data in FROZEN)
            self.error("VISUAL_STUDIO_FROZEN_SOURCE_MISMATCH", lambda: replace(identity(), files=changed))

    def test_source_order_independent(self):
        a = identity()
        self.assertEqual(a.fingerprint(), replace(a, files=tuple(reversed(FROZEN))).fingerprint())

    def test_owner_source_and_vsix_audits_reused(self):
        with patch.object(v.integration, "audit_visualstudio_integration_source", wraps=v.integration.audit_visualstudio_integration_source) as source, \
             patch.object(v.integration, "audit_visualstudio_integration_vsix", wraps=v.integration.audit_visualstudio_integration_vsix) as vsix:
            evidence()
            self.assertEqual(source.call_count, 1)
            self.assertEqual(vsix.call_count, 1)

    def test_archive_structure_and_assembly_bytes(self):
        e = evidence()
        self.assertEqual(len(v.inventory(e.data)[0]), 4)
        self.assertEqual(e.record()["assembly_sha256"], v.digest(DLL))
        self.assertTrue(e.record()["assembly_continuity"])
        self.assertEqual(e.record()["installed_copy"], "NOT_EVALUATED")

    def test_build_digest_mismatch(self):
        e = evidence()
        self.error("VISUAL_STUDIO_ASSEMBLY_DIGEST_MISMATCH", lambda: replace(e, declared_assembly_digest="0" * 64))

    def test_build_to_vsix_substitution_rejected(self):
        e = evidence()
        self.error("VISUAL_STUDIO_ASSEMBLY_CONTINUITY_MISMATCH", lambda: replace(e, built_assembly=DLL + b"changed", declared_assembly_digest=v.digest(DLL + b"changed")))

    def test_missing_assembly_rejected(self):
        self.error("VISUAL_STUDIO_FROZEN_OWNER_REJECTED", lambda: evidence(archive([p for p in rows() if not p[0].endswith(".dll")])))

    def test_manifest_owner_version_rejection(self):
        changed = [(name, data.replace(b'Version="0.1.0"', b'Version="9.0.0"') if name == "extension.vsixmanifest" else data) for name, data in rows()]
        self.error("VISUAL_STUDIO_FROZEN_OWNER_REJECTED", lambda: evidence(archive(changed)))

    def test_installation_target_and_display_name_continuity(self):
        for old, new in ((b'Microsoft.VisualStudio.Community', b'Microsoft.VisualStudio.Enterprise'), (b'ApexForge Language Tools', b'Other Tools')):
            changed = [(name, data.replace(old, new) if name == "extension.vsixmanifest" else data) for name, data in rows()]
            self.error("VISUAL_STUDIO_MANIFEST_CONTINUITY_MISMATCH", lambda: evidence(archive(changed)))

    def test_unknown_asset_owner_rejection(self):
        changed = [(name, data.replace(b'ApexForge.VisualStudio.pkgdef', b'other.pkgdef') if name == "extension.vsixmanifest" else data) for name, data in rows()]
        self.error("VISUAL_STUDIO_FROZEN_OWNER_REJECTED", lambda: evidence(archive(changed)))

    def test_hosted_language_server_assembly_excluded(self):
        self.error("VISUAL_STUDIO_FROZEN_OWNER_REJECTED", lambda: evidence(archive(rows() + [("Microsoft.VisualStudio.LanguageServer.Client.dll", DLL)])))

    def test_unsafe_paths(self):
        for name in ("../x", "/x", "C:/x", "dir/../x", "dir\\x", "dir//x", "./x", "x\x00bad"):
            self.error("VISUAL_STUDIO_ARCHIVE_PATH_INVALID", lambda: v.inventory(archive([(name, b"x")])))

    def test_case_and_conflicting_duplicates(self):
        self.error("VISUAL_STUDIO_ARCHIVE_DUPLICATE", lambda: v.inventory(archive([("a", b"x"), ("A", b"y")])))

    def test_file_directory_conflicts(self):
        for items in ([('a', b'x'), ('a/b', b'y')], [('a/b', b'y'), ('a', b'x')]):
            self.error("VISUAL_STUDIO_ARCHIVE_PATH_INVALID", lambda: v.inventory(archive(items)))

    def test_link_rejected(self):
        self.error("VISUAL_STUDIO_ARCHIVE_LINK_INVALID", lambda: v.inventory(archive([("link", b"x")], mode=stat.S_IFLNK | 0o777)))

    def test_size_count_and_malformed_archive(self):
        self.error("VISUAL_STUDIO_ARCHIVE_SIZE_INVALID", lambda: v.inventory(b"x" * (v.MAX_BYTES + 1)))
        self.error("VISUAL_STUDIO_ARCHIVE_SIZE_INVALID", lambda: v.inventory(archive([(str(i), b"x") for i in range(v.MAX_ENTRIES + 1)])))
        self.error("VISUAL_STUDIO_ARCHIVE_INVALID", lambda: v.inventory(b"not zip"))

    def test_residue_excluded(self):
        for name in (".git/config", "bin/old.dll", "obj/a", "scratch/x.pyc", "a.cs", "old.vsix", "a.pdb", ".vs/a", "test-results/a"):
            self.error("VISUAL_STUDIO_ARCHIVE_RESIDUE", lambda: v.inventory(archive([(name, b"x")])))

    def test_xml_entity_and_malformed_metadata(self):
        for data in (b'<!DOCTYPE x><x/>', b'<x><y></x>', b'\xff', '<!DOCTYPE x><x/>'.encode('utf-16')):
            self.error("VISUAL_STUDIO_XML_INVALID", lambda: v.xml(data))

    def test_oversized_expanded_member(self):
        self.error("VISUAL_STUDIO_ARCHIVE_SIZE_INVALID", lambda: v.inventory(archive([("large", b"x" * (v.MAX_MEMBER + 1))])))

    def test_independent_fixture_reproducibility(self):
        left, right = evidence(archive()), evidence(archive())
        self.assertIsNot(left, right)
        self.assertEqual(left.fingerprint(), right.fingerprint())
        self.assertEqual(v.compare_packages(left, right), {"context_equal": True, "member_content_equal": True, "assembly_equal": True, "raw_bytes_equal": True, "authenticated": False})

    def test_timestamp_and_order_gaps_reported(self):
        left = evidence()
        for data in (archive(timestamp=(2001, 2, 3, 4, 5, 6)), archive(reverse=True)):
            right = evidence(data)
            result = v.compare_packages(left, right)
            self.assertTrue(result["member_content_equal"])
            self.assertTrue(result["assembly_equal"])
            self.assertFalse(result["raw_bytes_equal"])
            self.assertNotEqual(left.fingerprint(), right.fingerprint())

    def test_generic_build_and_manifest_integration(self):
        e = evidence()
        artifact = e.build_artifact()
        self.assertEqual(artifact.data, e.data)
        self.assertEqual(artifact.recipe.inputs[0].source.fingerprint, e.fingerprint())
        architecture = r.ReleaseArtifactMatrix(e.identity.release, (e.descriptor,))
        artifacts = b.ReleaseArtifactSet(e.identity.release, (artifact.recipe,), (artifact,))
        sums = m.ReleaseChecksumSet(e.identity.release, m.reference(architecture), (m.checksum_for(artifact),))
        lineage = m.required_lineage(architecture, artifacts, sums)
        provenance = m.ReleaseProvenanceBundle(e.identity.release, tuple(m.ReleaseProvenanceRecord("r" + str(i), e.identity.release, kind, subject, predecessors)
                            for i, (kind, subject, predecessors) in enumerate(lineage)))
        self.assertEqual(m.ReleaseManifest(architecture, artifacts, sums, provenance).evaluate()[0], "COMPLETE")

    def test_no_trust_authority_or_execution(self):
        record = evidence().record()
        for key in ("grants_trust", "grants_authority", "grants_compatibility", "executed", "installed", "published", "authenticated", "signed"):
            self.assertFalse(record[key])
        self.assertEqual(record["crypto"], "CRYPTO_PROVIDER_UNAVAILABLE")

    def test_installed_auditor_not_called(self):
        with patch.object(v.owner, "audit_visualstudio_installed_copy", side_effect=AssertionError("no install")):
            evidence()

    def test_local_tool_unavailable_no_fake_bytes(self):
        ident = identity()
        with patch.object(v.shutil, "which", return_value=None):
            result = v.local_build(ident, descriptor(ident))
        self.assertEqual(result.status, "UNAVAILABLE")
        self.assertIsNone(result.evidence)

    def test_local_missing_restore_and_fixed_command(self):
        ident = identity()
        completed = subprocess.CompletedProcess((), 1, "error NETSDK1004: assets missing", "")
        with patch.object(v.shutil, "which", return_value="dotnet"), patch.object(v.subprocess, "run", return_value=completed) as run:
            result = v.local_build(ident, descriptor(ident))
            argv = run.call_args.args[0]
            self.assertEqual(argv[:3], ("dotnet", "build", v.PROJECT))
            self.assertIn("--no-restore", argv)
            self.assertIn("-warnaserror", argv)
            self.assertIn("-p:UseSharedCompilation=false", argv)
            self.assertIn("-nodeReuse:false", argv)
            self.assertNotIn("restore", argv)
            self.assertFalse(run.call_args.kwargs["shell"])
            self.assertEqual(run.call_args.kwargs["timeout"], 120)
            self.assertNotIn("APPDATA", run.call_args.kwargs["env"])
            self.assertFalse(Path(run.call_args.kwargs["cwd"]).exists())
        self.assertIsNone(result.evidence)

    def test_compilation_failure_not_hidden_as_environment(self):
        ident = identity()
        completed = subprocess.CompletedProcess((), 1, "error CS0001: defect", "")
        with patch.object(v.shutil, "which", return_value="dotnet"), patch.object(v.subprocess, "run", return_value=completed):
            self.error("VISUAL_STUDIO_BUILD_REJECTED", lambda: v.local_build(ident, descriptor(ident)))

    def test_build_timeout_and_missing_outputs(self):
        ident = identity()
        for side_effect, result in ((subprocess.TimeoutExpired("dotnet", 120), None), (None, subprocess.CompletedProcess((), 0, "", ""))):
            with patch.object(v.shutil, "which", return_value="dotnet"), patch.object(v.subprocess, "run", side_effect=side_effect, return_value=result):
                self.assertEqual(v.local_build(ident, descriptor(ident)).status, "UNAVAILABLE")

    def test_cache_only_restore_has_no_public_sources(self):
        ident = identity()
        original_file, original_dir = Path.is_file, Path.is_dir
        captured = []
        def run(argv, **options):
            captured.append(argv)
            config_path = Path(next(a.split("=", 1)[1] for a in argv if a.startswith("-p:RestoreConfigFile=")))
            config = ET.fromstring(config_path.read_bytes())
            self.assertEqual(config.find("packageSources")[0].tag, "clear")
            values = [e.attrib["value"] for e in config.find("packageSources").findall("add")]
            self.assertEqual(len(values), 1)
            self.assertTrue(Path(values[0]).is_dir())
            self.assertEqual(list(Path(values[0]).iterdir()), [])
            self.assertFalse(any(value.startswith(("https:", "http:")) for value in values))
            self.assertFalse(options["shell"])
            self.assertIn("-p:NuGetAudit=false", argv)
            self.assertIn("-p:UseSharedCompilation=false", argv)
            self.assertIn("-nodeReuse:false", argv)
            self.assertEqual(options["timeout"], 120)
            self.assertNotIn("NUGET_AUTH_TOKEN", options["env"])
            return subprocess.CompletedProcess(argv, 1, "error NU1101: absent cached package", "")
        with patch.dict(v.os.environ, {"ProgramFiles": str(ROOT), "USERPROFILE": str(ROOT), "NUGET_AUTH_TOKEN": "test-do-not-forward"}), \
             patch.object(Path, "is_file", new=lambda p: p.name == "MSBuild.exe" or original_file(p)), \
             patch.object(Path, "is_dir", new=lambda p: p.name == "packages" or original_dir(p)), \
             patch.object(v.subprocess, "run", side_effect=run):
            result = v.local_cached_build(ident, descriptor(ident))
        self.assertEqual(result.status, "UNAVAILABLE")
        self.assertIsNone(result.evidence)
        self.assertEqual(len(captured), 1)

    def test_cached_builder_rejects_changed_release_before_tool_lookup(self):
        ident = identity()
        wrong = replace(descriptor(ident), release=replace(ident.release, version="other"))
        with patch.object(v.subprocess, "run", side_effect=AssertionError("must not launch")):
            self.error("VISUAL_STUDIO_RELEASE_BINDING_INVALID", lambda: v.local_cached_build(ident, wrong))

    def test_scale_inventory(self):
        inputs = [(f"resource-{i:04}.txt", b"small") for i in range(1000)]
        self.assertEqual(v.inventory(archive(inputs))[0], v.inventory(archive(inputs, reverse=True))[0])

    def test_static_security_audit(self):
        tree = ast.parse(Path(v.__file__).read_text(encoding="utf-8"))
        imports = {n.name.split('.')[0] for node in ast.walk(tree) if isinstance(node, ast.Import) for n in node.names}
        self.assertFalse(imports & {"socket", "urllib", "requests", "pickle", "importlib", "ctypes"})
        calls = {n.func.id for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
        self.assertFalse(calls & {"eval", "exec", "__import__"})
        attrs = {n.func.attr for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
        self.assertFalse(attrs & {"extract", "extractall", "rglob", "walk", "system", "Popen", "audit_visualstudio_installed_copy"})
        runs = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "run"]
        self.assertEqual(len(runs), 2)
        for run in runs:
            keywords = {kw.arg: kw.value for kw in run.keywords}
            self.assertFalse(keywords["shell"].value)
            self.assertIn("timeout", keywords)


if __name__ == "__main__":
    unittest.main()
