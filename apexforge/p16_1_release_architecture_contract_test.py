"""Passive P16.1 release architecture and frozen owner boundary tests."""
import ast
import json
from dataclasses import FrozenInstanceError, replace
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tooling import release_architecture as r
from tooling import package_manifest as pm
from native_backend.native_execution_contract import PROFILE


def fixture():
    release = r.ReleaseIdentity("apexforge-review", "declared-review-1", "DEVELOPMENT", r.P15_BASELINE)
    provenance = pm.CanonicalReference("apexforge.provenance/v1", "provenance-scope", "A" * 64)
    declarations = (
        ("python", "PYTHON_DISTRIBUTION", "sdist", "apexforge-language-10.1.3.tar.gz", "10.1.3", "SUPPORTED"),
        ("vscode", "VSCODE_EXTENSION", "vsix", "apexforge-language-0.1.0.vsix", "0.1.0", "SUPPORTED"),
        ("visual-studio", "VISUAL_STUDIO_EXTENSION", "vsix", "ApexForge.VisualStudio-0.1.0.vsix", "0.1.0", "SUPPORTED"),
        ("native-win-x64", "NATIVE_COMPONENT", "dll", "apexforge-native.dll", "profile-v1", "PLANNED"),
    )
    artifacts = tuple(r.ReleaseArtifactDescriptor(release, r.ReleaseArtifactIdentity(target),
        r.ReleaseTarget(target, PROFILE if target == "native-win-x64" else ""),
        role, fmt, filename, version, availability, provenance=(provenance,))
        for target,role,fmt,filename,version,availability in declarations)
    return r.ReleaseArtifactMatrix(release, artifacts)


class ContractTests(unittest.TestCase):
    def error(self, code, factory):
        with self.assertRaises(r.ReleaseArchitectureError) as caught:
            factory()
        self.assertEqual(caught.exception.code, code)
        self.assertEqual(str(caught.exception), code)

    def test_all_models_immutable(self):
        m = fixture()
        for obj,field in ((m,"artifacts"),(m.release,"version"),(m.release.baseline,"commit"),
                          (m.artifacts[0],"filename"),(m.artifacts[0].identity,"identifier"),
                          (m.artifacts[0].target,"identifier")):
            with self.assertRaises(FrozenInstanceError):
                setattr(obj,field,"changed")

    def test_release_version_explicit_not_surface_inferred(self):
        m=fixture()
        self.assertEqual(m.release.version,"declared-review-1")
        self.assertEqual({a.surface_version for a in m.artifacts},{"10.1.3","0.1.0","profile-v1"})
        for value in ("",None,1,"../version","time now"):
            self.error("RELEASE_VERSION_REQUIRED",lambda value=value: replace(m.release,version=value))
        self.assertNotEqual(m.release.fingerprint(),replace(m.release,version="review-2").fingerprint())

    def test_exact_frozen_baseline_and_revision_binding(self):
        m=fixture()
        b=m.release.baseline
        self.assertEqual((b.commit,b.tag,b.tag_object,b.parent),
            ("c9c5ca186c9d942ce336ac1ebfe1287b16953200","afp-p15.14-freeze",
             "d7761c04e4422bfb91d9582275a60912874678f4","0731e9c00b2858079007dbafdb0e052f497fb24c"))
        for field,value in (("commit","a"*40),("tag","other-freeze"),("tag_object","b"*40),("parent","c"*40)):
            release=replace(m.release,baseline=replace(b,**{field:value}))
            self.assertNotEqual(m.release.fingerprint(),release.fingerprint())
            a=m.artifacts[0]
            self.assertNotEqual(a.fingerprint(),replace(a,release=release).fingerprint())

    def test_invalid_baseline_fails_closed(self):
        for value in ("", "A"*40,"a"*39,None,123):
            self.error("RELEASE_BASELINE_INVALID",lambda value=value: replace(r.P15_BASELINE,commit=value))

    def test_channels_declare_no_trust(self):
        for channel in r.CHANNELS:
            release=replace(fixture().release,channel=channel)
            self.assertFalse(release.record()["channel_grants_trust"])
        self.error("RELEASE_CHANNEL_INVALID",lambda: replace(fixture().release,channel="trusted"))

    def test_only_evidenced_targets_supported(self):
        self.assertEqual({a.target.identifier for a in fixture().artifacts},set(r.TARGETS))
        for target in ("native-linux","native-macos","native-arm64","unknown",None):
            self.error("RELEASE_TARGET_UNSUPPORTED",lambda target=target:r.ReleaseTarget(target))

    def test_native_profile_exact_owner_reference(self):
        t=r.ReleaseTarget("native-win-x64",PROFILE)
        self.assertEqual(t.native_profile,PROFILE)
        self.assertFalse(t.record()["whole_language_native_support"])
        for profile in ("",PROFILE+"/expanded","linux",None):
            self.error("RELEASE_NATIVE_PROFILE_INVALID",lambda profile=profile: replace(t,native_profile=profile))
        self.error("RELEASE_NATIVE_PROFILE_INVALID",lambda:r.ReleaseTarget("python",PROFILE))

    def test_artifact_role_and_format_bounded_per_target(self):
        a=fixture().artifacts[0]
        self.error("RELEASE_ARTIFACT_ROLE_FORMAT_INVALID",lambda:replace(a,role="EXECUTABLE_WORKFLOW"))
        self.error("RELEASE_ARTIFACT_ROLE_FORMAT_INVALID",lambda:replace(a,format="wasm"))
        self.error("RELEASE_ARTIFACT_ROLE_FORMAT_INVALID",lambda:replace(a,role="VSCODE_EXTENSION"))
        wheel=replace(next(a for a in fixture().artifacts if a.target.identifier=="python"),
                      format="wheel",filename="declared.whl")
        self.assertEqual(wheel.format,"wheel")

    def test_safe_declared_filename(self):
        a=fixture().artifacts[0]
        for name in ("../out.dll","C:/out.dll","dir/out.dll","CON.dll","out.exe","bad\\out.dll",None):
            self.error("RELEASE_FILENAME_INVALID",lambda name=name:replace(a,filename=name))

    def test_descriptor_not_bytes_or_checksum(self):
        for a in fixture().artifacts:
            rec=a.record()
            self.assertEqual(rec["artifact_bytes_exist"],"NOT_ESTABLISHED")
            self.assertEqual(rec["checksum"],"REQUIRED_AFTER_ARTIFACT_ASSEMBLY")
            self.assertFalse(hasattr(a,"digest"))
            self.assertFalse(hasattr(a,"payload"))
            self.assertEqual(rec["authentication"],"NOT_ESTABLISHED")

    def test_availability_not_release_readiness(self):
        a=fixture().artifacts[0]
        for state in r.AVAILABILITY:
            rec=replace(a,availability=state).record()
            self.assertEqual(rec["availability"],state)
            self.assertEqual(rec["artifact_bytes_exist"],"NOT_ESTABLISHED")
            self.assertEqual(rec["signing"],"CRYPTO_PROVIDER_UNAVAILABLE")
        self.error("RELEASE_AVAILABILITY_INVALID",lambda:replace(a,availability="TRUSTED"))

    def test_exact_p14_package_binding_optional_pair(self):
        a=fixture().artifacts[0]
        package=pm.PackageManifest(pm.PackageCoordinate("release.fixture","part",pm.ExactVersion(1,2,3)))
        bound=replace(a,package_coordinate=package.coordinate,package_content=package.content_identity())
        self.assertEqual(bound.record()["package_content"],package.content_identity().record())
        changed=replace(package,exported_capabilities=("Changed.Contract",))
        self.assertNotEqual(bound.fingerprint(),replace(bound,package_content=changed.content_identity()).fingerprint())
        self.error("RELEASE_PACKAGE_BINDING_INVALID",lambda:replace(a,package_coordinate=package.coordinate))
        self.error("RELEASE_PACKAGE_BINDING_INVALID",lambda:replace(a,package_content=package.content_identity()))
        self.assertIsNone(a.package_coordinate)

    def test_provenance_retained_not_authenticated(self):
        a=fixture().artifacts[0]
        self.assertEqual(a.record()["provenance"],[p.record() for p in a.provenance])
        self.assertFalse(a.release.baseline.record()["authenticated"])
        self.assertNotEqual(a.fingerprint(),replace(a,provenance=()).fingerprint())
        self.error("RELEASE_PROVENANCE_INVALID",lambda:replace(a,provenance=list(a.provenance)))

    def test_matrix_determinism_and_order_independence(self):
        m=fixture()
        equivalent=r.ReleaseArtifactMatrix(m.release,tuple(reversed(m.artifacts)))
        self.assertEqual(m.record(),equivalent.record())
        self.assertEqual(m.canonical_json(),equivalent.canonical_json())
        self.assertEqual(m.fingerprint(),equivalent.fingerprint())
        self.assertEqual(m.fingerprint(),fixture().fingerprint())

    def test_matrix_rejects_mixed_baseline(self):
        m=fixture()
        other=replace(m.release,baseline=replace(m.release.baseline,commit="a"*40))
        self.error("RELEASE_MATRIX_BASELINE_MISMATCH",lambda:r.ReleaseArtifactMatrix(other,m.artifacts))

    def test_matrix_duplicate_and_mutable_inputs_rejected(self):
        m=fixture()
        self.error("RELEASE_MATRIX_INVALID",lambda:r.ReleaseArtifactMatrix(m.release,m.artifacts*2))
        self.error("RELEASE_MATRIX_INVALID",lambda:r.ReleaseArtifactMatrix(m.release,list(m.artifacts)))
        self.error("RELEASE_MATRIX_EMPTY",lambda:r.ReleaseArtifactMatrix(m.release,()))
        a=m.artifacts[0]
        self.error("RELEASE_ARTIFACT_DUPLICATE",lambda:r.ReleaseArtifactMatrix(m.release,
            (a,replace(a,availability="UNAVAILABLE"))))
        self.error("RELEASE_FILENAME_DUPLICATE",lambda:r.ReleaseArtifactMatrix(m.release,
            (a,replace(a,identity=r.ReleaseArtifactIdentity("different")))))

    def test_reference_relationships_exact_and_passive(self):
        m=fixture()
        a,b=m.artifacts[:2]
        linked=replace(a,references=(b.identity,))
        matrix=r.ReleaseArtifactMatrix(m.release,(linked,)+m.artifacts[1:])
        self.assertEqual(matrix.record()["relationship_semantics"],"REFERENCE_ONLY")
        self.assertNotEqual(m.fingerprint(),matrix.fingerprint())
        self.error("RELEASE_REFERENCE_INVALID",lambda:replace(a,references=(a.identity,)))
        self.error("RELEASE_REFERENCE_DANGLING",lambda:r.ReleaseArtifactMatrix(m.release,
            (replace(a,references=(r.ReleaseArtifactIdentity("missing"),)),)))

    def test_relationship_and_provenance_order_canonical(self):
        m=fixture()
        a=m.artifacts[0]
        refs=tuple(v.identity for v in m.artifacts[1:])
        p=pm.CanonicalReference("apexforge.provenance/v1","provenance-scope","B"*64)
        first=replace(a,references=refs,provenance=a.provenance+(p,))
        second=replace(a,references=tuple(reversed(refs)),provenance=(p,)+a.provenance)
        self.assertEqual(first.fingerprint(),second.fingerprint())

    def test_packaging_owners_and_later_slices(self):
        for a in fixture().artifacts:
            row=next(row for row in r.SURFACES if row[0]==a.target.identifier)
            self.assertEqual(a.record()["packaging_owner"],row[3])
            self.assertEqual(a.record()["production_slice"],row[4])
            self.assertEqual(a.record()["signing_owner"],"P16.11")

    def test_matrix_matches_existing_surface_metadata(self):
        root=Path(__file__).resolve().parent.parent
        metadata=(root/"pyproject.toml").read_text(encoding="utf-8")
        self.assertIn('version = "10.1.3"',metadata)
        self.assertIn('requires-python = ">=3.9"',metadata)
        vscode=json.loads((root/"editors/vscode-apexforge/package.json").read_text(encoding="utf-8"))
        self.assertEqual((vscode["version"],vscode["engines"]["vscode"]),("0.1.0","^1.85.0"))
        vs=(root/"editors/visualstudio-apexforge/src/ApexForge.VisualStudio/source.extension.vsixmanifest").read_text(encoding="utf-8")
        for marker in ('Version="0.1.0"','Version="[17.0,)"','amd64','arm64'):
            self.assertIn(marker,vs)
        versions={a.target.identifier:a.surface_version for a in fixture().artifacts}
        self.assertEqual(versions["python"],"10.1.3")
        self.assertEqual(versions["vscode"],vscode["version"])
        self.assertEqual(versions["visual-studio"],"0.1.0")

    def test_owner_directed_roadmap_complete_and_deferred(self):
        root=Path(__file__).resolve().parent.parent
        doc=(root/"docs/p16/P16_1_RELEASE_ARCHITECTURE.md").read_text(encoding="utf-8")
        self.assertIn("P16: Release Engineering & Distribution",doc)
        for number in range(1,14):
            self.assertIn("| P16."+str(number)+" |",doc)
        self.assertEqual(doc.count("Deferred; not implemented"),12)

    def test_no_authority_trust_signing_or_semantic_replacement(self):
        for a in fixture().artifacts:
            record=a.record()
            self.assertFalse(record["grants_authority"])
            self.assertFalse(record["grants_trust"])
            self.assertEqual(record["semantic_authority"],"CANONICAL_AIR")
            self.assertEqual(record["signing"],"CRYPTO_PROVIDER_UNAVAILABLE")

    def test_no_build_install_publish_or_host_side_effect(self):
        with patch("subprocess.run",side_effect=AssertionError("process")), \
             patch("subprocess.Popen",side_effect=AssertionError("process")), \
             patch("socket.socket",side_effect=AssertionError("network")), \
             patch("os.getenv",side_effect=AssertionError("environment")), \
             patch("builtins.open",side_effect=AssertionError("filesystem")):
            record=fixture().record()
            self.assertEqual(record["execution"],"NOT_PERFORMED")
            self.assertEqual(record["installation"],"NOT_PERFORMED")
            self.assertEqual(record["publication"],"NOT_PERFORMED")

    def test_domain_separated_fingerprints(self):
        m=fixture()
        values=(m,m.release,m.release.baseline,m.artifacts[0],m.artifacts[0].identity,m.artifacts[0].target)
        self.assertEqual(len({v.DOMAIN for v in values}),len(values))
        self.assertEqual(len({v.fingerprint() for v in values}),len(values))

    def test_static_dependency_and_security_audit(self):
        tree=ast.parse(Path(r.__file__).read_text(encoding="utf-8"))
        imports=set()
        for node in ast.walk(tree):
            if isinstance(node,ast.Import):
                imports.update(alias.name for alias in node.names)
            if isinstance(node,ast.ImportFrom):
                imports.add(node.module)
            if isinstance(node,ast.Call) and isinstance(node.func,ast.Name):
                self.assertNotIn(node.func.id,{"eval","exec","open","compile","__import__"})
        self.assertEqual(imports,{"dataclasses","tooling.domain_platform","tooling.package_manifest",
                                  "native_backend.native_execution_contract","re"})
        self.assertEqual({node.name for node in tree.body if isinstance(node,ast.ClassDef)},
            {"ReleaseArchitectureError","FrozenSourceBaseline","ReleaseIdentity","ReleaseTarget",
             "ReleaseArtifactIdentity","ReleaseArtifactDescriptor","ReleaseArtifactMatrix"})


if __name__=="__main__":
    unittest.main()
