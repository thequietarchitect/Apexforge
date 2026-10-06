"""Generic byte build, independent reproducibility and frozen boundaries."""
import ast
from dataclasses import FrozenInstanceError, replace
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parent))
from tooling import release_architecture as r
from tooling import release_build as b
from tooling.package_manifest import PackagePath, CanonicalReference
from tooling import release_versioning as v

PROVENANCE=CanonicalReference("apexforge.provenance/v1","provenance-scope","A"*64)


def fixture(data=b"opaque\r\nbytes\x00",count=1):
    release=r.ReleaseIdentity("generic-review","declared-1","DEVELOPMENT",r.P15_BASELINE)
    inputs=tuple(b.ReleaseBuildInput(release,PackagePath("input-"+str(i)),"SUPPLIED_DATA",
                                   bytes(bytearray(data))+i.to_bytes(2,"big"),b.digest(bytes(bytearray(data))+i.to_bytes(2,"big")),
                                   provenance=(PROVENANCE,)) for i in range(count))
    outputs=tuple(b.ReleaseBuildOutputSlot(r.ReleaseArtifactDescriptor(release,r.ReleaseArtifactIdentity("artifact-"+str(i)),
         r.ReleaseTarget("vscode"),"VSCODE_EXTENSION","vsix","artifact-"+str(i)+".vsix","0.1.0","PLANNED",
         provenance=(PROVENANCE,)),inputs[i].identity) for i in range(count))
    env=b.ReleaseBuildEnvironment("opaque-copy-v1","p16.generic-byte-copy")
    return b.ReleaseBuildRecipe("copy-review",release,"COPY_BYTES",env,inputs,outputs,(PROVENANCE,))


class ContractTests(unittest.TestCase):
    def error(self,code,factory):
        with self.assertRaises(b.ReleaseBuildError) as caught:
            factory()
        self.assertEqual(caught.exception.code,code)
        self.assertEqual(str(caught.exception),code)

    def test_all_models_immutable(self):
        recipe=fixture()
        result=b.assemble(recipe)
        evidence=b.BuildReproducibilityEvidence(result,b.assemble(fixture()))
        for obj in (recipe.inputs[0],recipe.environment,recipe.outputs[0],recipe,result.artifacts[0],result,evidence):
            field=next(iter(obj.__dataclass_fields__))
            with self.assertRaises(FrozenInstanceError):
                setattr(obj,field,None)

    def test_input_digest_exact_and_mismatch_fails_closed(self):
        i=fixture().inputs[0]
        self.assertEqual(i.declared_digest,b.digest(i.data))
        for declared in ("B"*64,"",None,"a"*64):
            self.error("RELEASE_BUILD_INPUT_DIGEST_MISMATCH",lambda declared=declared:replace(i,declared_digest=declared))
        self.error("RELEASE_BUILD_BYTES_INVALID",lambda:replace(i,data=bytearray(i.data)))

    def test_inputs_content_sensitive_and_explicit(self):
        i=fixture().inputs[0]
        changed=replace(i,data=b"changed",declared_digest=b.digest(b"changed"))
        self.assertNotEqual(i.fingerprint(),changed.fingerprint())
        self.assertEqual(i.record()["evidence"],"CALLER_SUPPLIED_BYTES")
        self.assertNotEqual(i.fingerprint(),replace(i,identity=PackagePath("other")).fingerprint())
        self.error("RELEASE_BUILD_INPUT_INVALID",lambda:replace(i,identity="host-file"))

    def test_input_roles_and_references_bounded(self):
        i=fixture().inputs[0]
        for role in b.INPUT_ROLES:
            self.assertEqual(replace(i,role=role).role,role)
        self.error("RELEASE_BUILD_INPUT_INVALID",lambda:replace(i,role="RUN_SCRIPT"))
        self.error("RELEASE_BUILD_INPUT_INVALID",lambda:replace(i,source=object()))
        self.error("RELEASE_BUILD_PROVENANCE_INVALID",lambda:replace(i,provenance=list(i.provenance)))

    def test_recipe_exact_release_context(self):
        recipe=fixture()
        other=replace(recipe.release,baseline=replace(r.P15_BASELINE,commit="a"*40))
        self.error("RELEASE_BUILD_RELEASE_MISMATCH",lambda:replace(recipe,release=other))
        inputs=tuple(replace(i,release=other) for i in recipe.inputs)
        outputs=tuple(replace(o,descriptor=replace(o.descriptor,release=other)) for o in recipe.outputs)
        changed=replace(recipe,release=other,inputs=inputs,outputs=outputs)
        self.assertNotEqual(recipe.fingerprint(),changed.fingerprint())

    def test_arbitrary_commands_and_callbacks_rejected(self):
        recipe=fixture()
        for operation in ("dotnet build","npm","eval","ASSEMBLE_ARCHIVE",lambda:True,None):
            self.error("RELEASE_BUILD_OPERATION_UNSUPPORTED",lambda operation=operation:replace(recipe,operation=operation))
        self.error("RELEASE_BUILD_ENVIRONMENT_INVALID",lambda:replace(recipe,environment=lambda:True))
        self.assertEqual(b.OPERATIONS,("COPY_BYTES",))

    def test_recipe_identity_binds_semantics_and_explicit_metadata(self):
        recipe=fixture()
        self.assertEqual(recipe.fingerprint(),fixture().fingerprint())
        self.assertNotEqual(recipe.fingerprint(),replace(recipe,identifier="other").fingerprint())
        changed=replace(recipe,environment=replace(recipe.environment,identifier="copy-v2"))
        self.assertNotEqual(recipe.fingerprint(),changed.fingerprint())
        changed=replace(recipe,outputs=(replace(recipe.outputs[0],descriptor=replace(recipe.outputs[0].descriptor,
                           surface_version="declared-other")),))
        self.assertNotEqual(recipe.fingerprint(),changed.fingerprint())
        self.assertFalse(recipe.record()["execution_authority"])

    def test_environment_passive_and_bounded(self):
        env=fixture().environment
        self.assertEqual(env.record()["host_state"],"NOT_INSPECTED")
        for field,value in (("owner","C:/host"),("byte_policy","HOST_DEFAULT"),("line_endings","HOST_DEFAULT"),
                            ("locale","host"),("metadata_encoding","default")):
            self.error("RELEASE_BUILD_ENVIRONMENT_INVALID",lambda field=field,value=value:replace(env,**{field:value}))

    def test_no_host_time_path_environment_process_or_network_reads(self):
        with patch("os.getcwd",side_effect=AssertionError("cwd")), \
             patch("os.getpid",side_effect=AssertionError("pid")), \
             patch("os.getenv",side_effect=AssertionError("env")), \
             patch("socket.gethostname",side_effect=AssertionError("hostname")), \
             patch("socket.socket",side_effect=AssertionError("network")), \
             patch("time.time",side_effect=AssertionError("time")), \
             patch("subprocess.run",side_effect=AssertionError("subprocess")), \
             patch("subprocess.Popen",side_effect=AssertionError("subprocess")), \
             patch("os.walk",side_effect=AssertionError("scan")), \
             patch("builtins.open",side_effect=AssertionError("file")):
            first=b.assemble(fixture())
            second=b.assemble(fixture())
            self.assertEqual(b.BuildReproducibilityEvidence(first,second).status,"PASS")

    def test_logical_paths_only_in_owned_metadata(self):
        recipe=fixture(b"opaque")
        for bad in ("C:/host/input","/tmp/input","../input","bad\\input"):
            with self.assertRaises(ValueError):
                PackagePath(bad)
        text=recipe.canonical_json()+b.assemble(recipe).canonical_json()
        self.assertNotIn(str(Path.cwd()),text)
        self.assertNotIn("timestamp",text)
        self.assertIn("input-0",text)

    def test_exact_line_endings_no_implicit_conversion(self):
        crlf=fixture(b"a\r\nb\r\n")
        lf=fixture(b"a\nb\n")
        result=b.assemble(crlf)
        self.assertEqual(result.artifacts[0].data,crlf.inputs[0].data)
        self.assertNotEqual(result.artifacts[0].data,b.assemble(lf).artifacts[0].data)
        self.assertEqual(crlf.environment.line_endings,"PRESERVE_SUPPLIED_BYTES")
        self.assertEqual(b.BuildReproducibilityEvidence(result,b.assemble(fixture(b"a\r\nb\r\n"))).status,"PASS")

    def test_output_actual_bytes_content_and_recipe_bound(self):
        recipe=fixture()
        artifact=b.assemble(recipe).artifacts[0]
        self.assertEqual(artifact.record()["recipe"],recipe.fingerprint())
        self.assertEqual(artifact.data,recipe.inputs[0].data)
        self.assertEqual(artifact.record()["length"],len(artifact.data))
        self.assertEqual(artifact.declared_digest,b.digest(artifact.data))
        changed=b.assemble(fixture(b"changed")).artifacts[0]
        self.assertNotEqual(artifact.declared_digest,changed.declared_digest)
        self.assertNotEqual(artifact.fingerprint(),changed.fingerprint())

    def test_output_digest_and_copy_content_fail_closed(self):
        artifact=b.assemble(fixture()).artifacts[0]
        self.error("RELEASE_BUILD_OUTPUT_DIGEST_MISMATCH",lambda:replace(artifact,declared_digest="B"*64))
        self.error("RELEASE_BUILD_OUTPUT_CONTENT_MISMATCH",lambda:replace(artifact,data=b"wrong",declared_digest=b.digest(b"wrong")))
        self.error("RELEASE_BUILD_OUTPUT_UNEXPECTED",lambda:replace(artifact,identity=r.ReleaseArtifactIdentity("missing")))

    def test_recipe_missing_duplicate_and_unavailable_slots_rejected(self):
        recipe=fixture()
        self.error("RELEASE_BUILD_INPUT_MISSING",lambda:replace(recipe,outputs=(replace(recipe.outputs[0],input_identity=PackagePath("absent")),)))
        self.error("RELEASE_BUILD_OUTPUT_UNAVAILABLE",lambda:replace(recipe.outputs[0],
                           descriptor=replace(recipe.outputs[0].descriptor,availability="UNAVAILABLE")))
        changed=replace(recipe.inputs[0],data=b"x",declared_digest=b.digest(b"x"))
        self.error("RELEASE_BUILD_INPUT_CONFLICT",lambda:replace(recipe,inputs=recipe.inputs+(changed,)))
        changed=replace(recipe.outputs[0],descriptor=replace(recipe.outputs[0].descriptor,surface_version="different"))
        self.error("RELEASE_BUILD_OUTPUT_CONFLICT",lambda:replace(recipe,outputs=recipe.outputs+(changed,)))

    def test_missing_output_never_fabricates_empty_artifact(self):
        recipe=fixture()
        missing=b.ReleaseArtifactSet(recipe.release,(recipe,),())
        self.assertEqual(missing.status,"INCOMPLETE")
        self.assertEqual(missing.artifacts,())
        self.assertEqual(missing.missing,("artifact-0",))
        self.assertEqual(missing.record()["findings"],[{"code":"RELEASE_BUILD_OUTPUT_MISSING","artifact":"artifact-0"}])
        empty=fixture(b"")
        # Explicit empty caller input remains a legitimate input, not inferred missing evidence.
        i=replace(empty.inputs[0],data=b"",declared_digest=b.digest(b""))
        empty=replace(empty,inputs=(i,))
        self.assertEqual(b.assemble(empty).artifacts[0].data,b"")

    def test_recipe_construction_not_build_success(self):
        recipe=fixture()
        self.assertFalse(hasattr(recipe,"status"))
        self.assertEqual(recipe.outputs[0].record()["bytes"],"NOT_ASSEMBLED_BY_SLOT_CONSTRUCTION")
        self.assertEqual(b.assemble(recipe).status,"BUILT")

    def test_artifact_set_and_recipe_order_independent(self):
        recipe=fixture(count=3)
        reordered=replace(recipe,inputs=tuple(reversed(recipe.inputs)),outputs=tuple(reversed(recipe.outputs)))
        self.assertEqual(recipe.fingerprint(),reordered.fingerprint())
        first=b.assemble(recipe)
        second=b.ReleaseArtifactSet(reordered.release,(reordered,),tuple(reversed(b.assemble(reordered).artifacts)),reordered.provenance)
        self.assertEqual(first.fingerprint(),second.fingerprint())

    def test_conflicting_artifact_duplicate_rejected(self):
        first=b.assemble(fixture(b"first"))
        second=b.assemble(fixture(b"second"))
        self.error("RELEASE_BUILD_OUTPUT_CONFLICT",lambda:b.ReleaseArtifactSet(first.release,first.recipes,
                   first.artifacts+second.artifacts))
        self.error("RELEASE_BUILD_OUTPUT_CONFLICT",lambda:b.ReleaseArtifactSet(first.release,
                   first.recipes+second.recipes,first.artifacts+second.artifacts))

    def test_multiple_recipes_canonical_set(self):
        one=fixture()
        identity=r.ReleaseArtifactIdentity("second")
        descriptor=replace(one.outputs[0].descriptor,identity=identity,filename="second.vsix")
        two=replace(one,identifier="second-recipe",outputs=(replace(one.outputs[0],descriptor=descriptor),))
        first=b.ReleaseArtifactSet(one.release,(one,two),b.assemble(one).artifacts+b.assemble(two).artifacts)
        second=b.ReleaseArtifactSet(one.release,(two,one),tuple(reversed(first.artifacts)))
        self.assertEqual(first.fingerprint(),second.fingerprint())

    def test_independently_constructed_recipes_and_bytes_reproduce(self):
        one=fixture()
        two=fixture()
        self.assertIsNot(one,two)
        self.assertIsNot(one.inputs[0],two.inputs[0])
        self.assertIsNot(one.inputs[0].data,two.inputs[0].data)
        first=b.assemble(one)
        second=b.assemble(two)
        self.assertIsNot(first.artifacts[0],second.artifacts[0])
        evidence=b.BuildReproducibilityEvidence(first,second)
        self.assertEqual(evidence.status,"PASS")
        self.assertFalse(evidence.record()["authenticity_proven"])
        self.assertFalse(evidence.record()["signed"])

    def test_changed_input_recipe_or_missing_output_breaks_reproducibility(self):
        recipe=fixture()
        result=b.assemble(recipe)
        for changed in (fixture(b"other"),replace(recipe,environment=replace(recipe.environment,identifier="other"))):
            evidence=b.BuildReproducibilityEvidence(result,b.assemble(changed))
            self.assertEqual(evidence.status,"MISMATCH")
            self.assertIn("RELEASE_BUILD_RECIPE_MISMATCH",evidence.findings)
        missing=b.ReleaseArtifactSet(recipe.release,(recipe,),())
        self.assertIn("RELEASE_BUILD_OUTPUT_MISSING",b.BuildReproducibilityEvidence(result,missing).findings)

    def test_source_provenance_and_release_references_retained(self):
        recipe=fixture()
        source=CanonicalReference("apexforge.source/v1","source","B"*64)
        recipe=replace(recipe,inputs=(replace(recipe.inputs[0],source=source),),references=(PROVENANCE,))
        artifact=b.assemble(recipe).artifacts[0]
        self.assertEqual(artifact.record()["provenance"]["input"]["source"],source.record())
        self.assertEqual(recipe.release.baseline,r.P15_BASELINE)
        self.assertEqual(artifact.record()["descriptor"],recipe.outputs[0].descriptor.record())
        self.assertEqual(recipe.record()["references"],[PROVENANCE.record()])
        self.assertEqual(artifact.record()["provenance"]["recipe"],[PROVENANCE.record()])

    def test_version_policy_reference_not_compatibility_grant(self):
        recipe=fixture()
        surface=v.ReleaseVersionSurface(r.ReleaseTarget("vscode"),"VSCODE_EXTENSION","apexforge")
        mapping=v.ReleaseSurfaceVersion(recipe.release,surface,"0.1.0")
        ref=CanonicalReference(mapping.DOMAIN,"provenance-scope",mapping.fingerprint())
        recipe=replace(recipe,references=(ref,))
        self.assertEqual(recipe.references,(ref,))
        self.assertFalse(b.assemble(recipe).artifacts[0].record()["grants_compatibility"])

    def test_no_trust_authority_semantic_or_packaging_claim(self):
        result=b.assemble(fixture())
        rec=result.artifacts[0].record()
        self.assertFalse(rec["grants_authority"])
        self.assertEqual(rec["authentication"],"CRYPTO_PROVIDER_UNAVAILABLE")
        self.assertEqual(rec["semantic_authority"],"CANONICAL_AIR")
        self.assertEqual(rec["packaging_validation"],"NOT_PERFORMED")
        self.assertFalse(result.record()["published"])
        self.assertFalse(result.record()["installed"])
        self.assertFalse(result.record()["final_release_manifest"])

    def test_target_neutral_copy_does_not_certify_packaging(self):
        recipe=fixture()
        for target,role,formats,owner,slice_name,scope in r.SURFACES:
            format_name=formats[0]
            suffix={"wheel":"whl","sdist":"tar.gz"}.get(format_name,format_name)
            descriptor=replace(recipe.outputs[0].descriptor,target=r.ReleaseTarget(target,r.PROFILE if target=="native-win-x64" else ""),
                               role=role,format=format_name,filename="opaque."+suffix)
            other=replace(recipe,outputs=(replace(recipe.outputs[0],descriptor=descriptor),))
            artifact=b.assemble(other).artifacts[0]
            self.assertEqual(artifact.data,recipe.inputs[0].data)
            self.assertEqual(artifact.record()["packaging_validation"],"NOT_PERFORMED")
            self.assertNotEqual(recipe.fingerprint(),other.fingerprint())

    def test_binary_bytes_never_interpreted_or_executed(self):
        data=b"__import__('os').system('forbidden')\x00\xff\x80\x04pickle"
        with patch("builtins.eval",side_effect=AssertionError("eval")), \
             patch("builtins.exec",side_effect=AssertionError("exec")):
            recipe=fixture(data)
            self.assertEqual(b.assemble(recipe).artifacts[0].data,recipe.inputs[0].data)

    def test_collection_and_byte_limits(self):
        recipe=fixture()
        self.error("RELEASE_BUILD_BYTES_INVALID",lambda:b.digest(b"x"*(b.MAX_BYTES+1)))
        self.error("RELEASE_BUILD_INPUT_INVALID",lambda:replace(recipe,inputs=list(recipe.inputs)))
        self.error("RELEASE_BUILD_OUTPUT_INVALID",lambda:replace(recipe,outputs=recipe.outputs*(b.MAX_ITEMS+1)))
        self.error("RELEASE_BUILD_RECIPE_INVALID",lambda:replace(recipe,inputs=()))
        self.error("RELEASE_BUILD_RECIPE_CONFLICT",lambda:b.ReleaseArtifactSet(recipe.release,(recipe,recipe),()))
        self.error("RELEASE_BUILD_RECIPE_MISMATCH",lambda:b.ReleaseArtifactSet(recipe.release,(recipe,),
                   b.assemble(fixture(b"other")).artifacts))

    def test_aggregate_byte_limits_fail_before_assembly(self):
        recipe=fixture()
        i=recipe.inputs[0]
        inputs=tuple(replace(i,identity=PackagePath("big-"+str(n)),data=b"x"*b.MAX_BYTES,
                            declared_digest=b.digest(b"x"*b.MAX_BYTES)) for n in range(9))
        self.error("RELEASE_BUILD_SIZE_LIMIT",lambda:replace(recipe,inputs=inputs))
        outputs=tuple(replace(recipe.outputs[0],descriptor=replace(recipe.outputs[0].descriptor,
                            identity=r.ReleaseArtifactIdentity("out-"+str(n)),filename="out-"+str(n)+".vsix"))
                            for n in range(9))
        i=replace(i,data=b"x"*b.MAX_BYTES,declared_digest=b.digest(b"x"*b.MAX_BYTES))
        self.error("RELEASE_BUILD_SIZE_LIMIT",lambda:replace(recipe,inputs=(i,),outputs=outputs))

    def test_1000_input_output_assembly_independent_and_ordered(self):
        one=fixture(b"small",1000)
        two=fixture(b"small",1000)
        two=replace(two,inputs=tuple(reversed(two.inputs)),outputs=tuple(reversed(two.outputs)))
        self.assertIsNot(one,two)
        self.assertEqual(len(one.inputs),1000)
        first=b.assemble(one)
        second=b.assemble(two)
        self.assertEqual(len(first.artifacts),1000)
        self.assertEqual(first.status,"BUILT")
        self.assertEqual([a.data for a in first.artifacts],[a.data for a in second.artifacts])
        self.assertEqual(b.BuildReproducibilityEvidence(first,second).status,"PASS")
        self.assertEqual(first.fingerprint(),second.fingerprint())

    def test_multi_recipe_global_limits(self):
        base=fixture(count=600)
        one=replace(base,outputs=base.outputs[:1])
        descriptor=replace(one.outputs[0].descriptor,identity=r.ReleaseArtifactIdentity("second"),filename="second.vsix")
        two=replace(one,identifier="second",outputs=(replace(one.outputs[0],descriptor=descriptor),))
        self.error("RELEASE_BUILD_SIZE_LIMIT",lambda:b.ReleaseArtifactSet(one.release,(one,two),()))
        base=fixture()
        i=replace(base.inputs[0],data=b"x"*b.MAX_BYTES,declared_digest=b.digest(b"x"*b.MAX_BYTES))
        def outputs(prefix):
            return tuple(replace(base.outputs[0],descriptor=replace(base.outputs[0].descriptor,
                identity=r.ReleaseArtifactIdentity(prefix+str(n)),filename=prefix+str(n)+".vsix")) for n in range(5))
        one=replace(base,inputs=(i,),outputs=outputs("first"))
        two=replace(base,identifier="second",inputs=(i,),outputs=outputs("second"))
        self.error("RELEASE_BUILD_SIZE_LIMIT",lambda:b.ReleaseArtifactSet(one.release,(one,two),()))

    def test_static_security_audit(self):
        tree=ast.parse(Path(b.__file__).read_text(encoding="utf-8"))
        imports=set()
        for node in ast.walk(tree):
            if isinstance(node,ast.Import):
                imports.update(a.name for a in node.names)
            if isinstance(node,ast.ImportFrom):
                imports.add(node.module)
            if isinstance(node,ast.Call) and isinstance(node.func,ast.Name):
                self.assertNotIn(node.func.id,{"eval","exec","open","compile","__import__"})
        self.assertEqual(imports,{"dataclasses","hashlib","re","tooling","tooling.domain_platform","tooling.package_manifest"})
        self.assertEqual({n.name for n in tree.body if isinstance(n,ast.ClassDef)},
            {"ReleaseBuildError","ReleaseBuildInput","ReleaseBuildEnvironment","ReleaseBuildOutputSlot",
             "ReleaseBuildRecipe","ReleaseBuildArtifact","ReleaseArtifactSet","BuildReproducibilityEvidence"})
        self.assertFalse(any(isinstance(n,(ast.AsyncFunctionDef,ast.Await)) for n in ast.walk(tree)))


if __name__=="__main__":
    unittest.main()
