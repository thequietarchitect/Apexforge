"""P16.10 historical review snapshot and pure evidence evaluation tests."""
from dataclasses import FrozenInstanceError, replace
from hashlib import sha256
from pathlib import Path
import ast
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'apexforge'));sys.path.insert(0,str(ROOT))
from tooling import release_pipeline as p, release_architecture as r, release_manifest as m
from tooling.package_manifest import CanonicalReference
from p16_9_install_upgrade_rollback_test import manifest, plan, assessment


def report(number):
    name=next((ROOT/'docs/p16').glob('P16_'+str(number)+'_*.md'))
    return CanonicalReference('apexforge.release-review-evidence/v1','source',sha256(name.read_bytes()).hexdigest().upper())


def architecture():
    release=r.ReleaseIdentity('install-review','1.0.0','DEVELOPMENT',r.P15_BASELINE)
    declarations=(('python-wheel','python','PYTHON_DISTRIBUTION','wheel','project.whl','10.1.3'),
        ('python-sdist','python','PYTHON_DISTRIBUTION','sdist','project.tar.gz','10.1.3'),
        ('vscode-vsix','vscode','VSCODE_EXTENSION','vsix','vscode.vsix','0.1.0'),
        ('visual-studio-vsix','visual-studio','VISUAL_STUDIO_EXTENSION','vsix','visual-studio.vsix','0.1.0'),
        ('native-exe','native-win-x64','NATIVE_COMPONENT','exe','program.exe','profile-v1'))
    return r.ReleaseArtifactMatrix(release,tuple(r.ReleaseArtifactDescriptor(release,r.ReleaseArtifactIdentity(name),
        r.ReleaseTarget(surface,r.PROFILE if surface=='native-win-x64' else ''),role,fmt,filename,version,'SUPPORTED')
        for name,surface,role,fmt,filename,version in declarations))


def snapshot(pipeline=None):
    pipeline=p.pipeline_for(architecture()) if pipeline is None else pipeline
    release=pipeline.release;rows=[]
    def gate(kind,subject,status,reference,reasons=()):
        rows.append(p.GateEvidence(release,kind,subject,status,(reference,),reasons))
    gate('BASELINE','release','PASS',m.reference(r.P15_BASELINE),('BASELINE_REFERENCE_ONLY',))
    gate('SIGNING','release','BLOCKED',report(1),('CRYPTO_PROVIDER_UNAVAILABLE',))
    gate('INSTALLATION','release','PASS',report(9),('ISOLATED_CONTRACT_ONLY',))
    gate('INSTALLATION_HOST','release','SKIPPED',report(9),('P16_9_HOST_SYMLINK_SKIP',))
    gate('ACCEPTANCE','release','DEFERRED',report(1),('P16_12_ACCEPTANCE_REQUIRED',))
    owner={'python':5,'vscode':6,'visual-studio':7,'native-win-x64':8}
    for descriptor in pipeline.architecture.artifacts:
        surface=descriptor.target.identifier;ref=report(owner[surface]);subject=descriptor.identity.identifier
        built='INCOMPLETE' if subject=='python-wheel' or surface=='vscode' else 'PASS'
        reasons=('PYTHON_WHEEL_UNAVAILABLE',) if subject=='python-wheel' else ('VSCODE_REAL_VSCE_UNVERIFIED',) if surface=='vscode' else ('GENUINE_OWNER_BUILT_ARCHIVE',)
        gate('OWNER_BUILD',subject,built,ref,reasons)
        gate('ARTIFACT',subject,'INCOMPLETE',ref,('ARTIFACT_UNAVAILABLE',))
        gate('SOURCE_CONTINUITY',subject,'PASS',ref,('FROZEN_GIT_BLOB_SOURCE',) if surface in ('vscode','visual-studio') else ('SOURCE_CONTINUITY_EXACT',))
        gate('CONTENT_REPRODUCIBILITY',subject,'INCOMPLETE' if subject=='python-wheel' else 'DEFERRED' if surface=='visual-studio' else 'PASS',ref)
        raw='PASS' if surface=='native-win-x64' else 'INCOMPLETE' if subject=='python-wheel' or surface=='vscode' else 'DEFERRED'
        why=('SDIST_ARCHIVE_TIMESTAMP_GAP',) if subject=='python-sdist' else ('VISUAL_STUDIO_RAW_REPRO_DEFERRED',) if surface=='visual-studio' else ()
        gate('RAW_REPRODUCIBILITY',subject,raw,ref,why)
    for surface in r.TARGETS:
        # Historical scoped integration passes do not fabricate a unified current-release manifest.
        gate('MANIFEST',surface,'INCOMPLETE',report(4),('MANIFEST_SCOPE_UNAVAILABLE',))
        gate('COMPATIBILITY',surface,'INCOMPLETE',report(2),('COMPATIBILITY_UNRESOLVED',))
        gate('CREDENTIAL_REQUIREMENT',surface,'INCOMPLETE',report(1),('CREDENTIAL_NOT_RESOLVED',))
    gate('NATIVE_PROFILE','native-win-x64','PASS',report(8),('NATIVE_MEASURED_PROFILE_ONLY',))
    regressions=tuple(p.RegressionEvidence(release,suite,passed,skip,0,passed+skip,report(9 if suite=='P16' else 1))
        for suite,passed,skip in (('P16',309,1),('P15',428,0),('P14',330,0),('NATIVE',7,0),('AUTHORITY',1,0)))
    return p.ReleasePipelineResult(pipeline,tuple(rows),regressions)


class ContractTests(unittest.TestCase):
    def error(self,code,callback):
        with self.assertRaises(p.ReleasePipelineError) as failure:callback()
        self.assertEqual(failure.exception.code,code)

    def test_immutable_pipeline_step_evidence_and_dry_run(self):
        result=snapshot();dry=p.publication_dry_run(result)[0]
        for obj,field in ((result.pipeline,'provider'),(result.pipeline.steps[0],'phase'),(result,'evidence'),(dry,'target')):
            with self.assertRaises(FrozenInstanceError):setattr(obj,field,'changed')

    def test_release_baseline_exact(self):
        result=snapshot();wrong=replace(result.pipeline.release,baseline=replace(r.P15_BASELINE,commit='0'*40))
        self.error('PIPELINE_BASELINE_MISMATCH',lambda:p.pipeline_for(replace(result.pipeline.architecture,release=wrong,
            artifacts=tuple(replace(d,release=wrong) for d in result.pipeline.architecture.artifacts))))

    def test_provider_neutral_not_inferred_from_hosting(self):
        self.assertEqual(snapshot().pipeline.provider,'PROVIDER_NEUTRAL')
        self.error('PIPELINE_SCHEMA_INVALID',lambda:replace(snapshot().pipeline,provider='GITHUB_ACTIONS'))

    def test_independent_construction_and_order_determinism(self):
        a,c=snapshot(),snapshot()
        self.assertIsNot(a,c);self.assertEqual(a.fingerprint(),c.fingerprint())
        changed=replace(a,pipeline=replace(a.pipeline,steps=tuple(reversed(a.pipeline.steps))),evidence=tuple(reversed(a.evidence)),regressions=tuple(reversed(a.regressions)))
        self.assertEqual(a.fingerprint(),changed.fingerprint())

    def test_cycle_unknown_predecessor_duplicate(self):
        pipeline=snapshot().pipeline;steps=pipeline.steps
        for replacement,code in ((replace(steps[0],predecessors=('readiness',)),'PIPELINE_CYCLE'),
                                  (replace(steps[0],predecessors=('unknown',)),'PIPELINE_PREDECESSOR_UNKNOWN')):
            self.error(code,lambda:replace(pipeline,steps=(replacement,)+steps[1:]))
        self.error('PIPELINE_STEP_DUPLICATE',lambda:replace(pipeline,steps=steps+(steps[0],)))

    def test_required_signing_and_acceptance_cannot_be_removed(self):
        pipeline=snapshot().pipeline
        for name in ('signing','publication-python'):
            steps=tuple(replace(s,requirements=()) if s.identifier==name else s for s in pipeline.steps)
            self.error('PIPELINE_REQUIRED_GATE_MISSING',lambda:replace(pipeline,steps=steps))

    def test_publication_cannot_use_another_surfaces_artifact_gate(self):
        pipeline=snapshot().pipeline
        steps=tuple(replace(s,predecessors=tuple('artifacts-vscode' if name=='artifacts-native-win-x64' else name
                      for name in s.predecessors)) if s.identifier=='publication-native-win-x64' else s for s in pipeline.steps)
        self.error('PIPELINE_REQUIRED_DEPENDENCY_MISSING',lambda:replace(pipeline,steps=steps))

    def test_gate_graph_revision_changes_identity(self):
        pipeline=snapshot().pipeline
        steps=tuple(replace(s,predecessors=s.predecessors+('installation',)) if s.identifier=='artifacts-native-win-x64' else s for s in pipeline.steps)
        self.assertNotEqual(pipeline.fingerprint(),replace(pipeline,steps=steps).fingerprint())

    def test_bounded_status_phase_and_requirements(self):
        release=architecture().release
        self.error('PIPELINE_STATUS_INVALID',lambda:p.GateEvidence(release,'SIGNING','release','SIGNED'))
        self.error('PIPELINE_PHASE_INVALID',lambda:p.PipelineStep('execute','RUN_SHELL'))
        self.error('PIPELINE_REQUIREMENT_INVALID',lambda:p.PipelineStep('upload','SIGNING_GATE',requirements=(('UPLOAD_COMMAND','shell'),)))
        self.error('PIPELINE_GRAPH_INVALID',lambda:p.topological((p.PipelineStep('a','BASELINE_VALIDATION'),)*(p.MAX_STEPS+1)))

    def test_regression_counts_preserve_skip(self):
        result=snapshot();record=next(x.record() for x in result.regressions if x.suite=='P16')
        self.assertEqual((record['passed'],record['skipped'],record['discovered']),(309,1,310))
        self.assertEqual(record['status'],'SKIPPED')
        bad=next(x for x in result.regressions if x.suite=='P16')
        self.error('PIPELINE_REGRESSION_COUNTS_INVALID',lambda:replace(bad,passed=310))

    def test_regression_declaration_cannot_omit_counts(self):
        result=snapshot()
        value=p.GateEvidence(result.pipeline.release,'REGRESSION','P16','PASS',(report(9),))
        self.error('PIPELINE_REGRESSION_COUNTS_REQUIRED',lambda:replace(result,evidence=result.evidence+(value,),regressions=()))

    def test_baseline_pass_requires_exact_reference(self):
        self.error('PIPELINE_BASELINE_EVIDENCE_MISMATCH',lambda:p.GateEvidence(architecture().release,'BASELINE','release','PASS',(report(1),)))

    def test_artifact_pass_requires_exact_descriptor_and_build_reference(self):
        result=snapshot();values=list(result.evidence)
        index=next(index for index,e in enumerate(values) if e.kind=='ARTIFACT' and e.subject=='native-exe')
        values[index]=replace(values[index],status='PASS')
        self.error('PIPELINE_ARTIFACT_REFERENCE_MISMATCH',lambda:replace(result,evidence=tuple(values)))

    def test_manifest_pass_rejects_different_artifact_scope(self):
        result=snapshot();values=list(result.evidence)
        index=next(index for index,e in enumerate(values) if e.kind=='MANIFEST' and e.subject=='vscode')
        values[index]=p.manifest_gate(manifest(),'vscode')
        self.error('PIPELINE_MANIFEST_REFERENCE_MISMATCH',lambda:replace(result,evidence=tuple(values)))

    def test_compatibility_pass_requires_owner_decision_reference(self):
        result=snapshot();values=list(result.evidence)
        index=next(index for index,e in enumerate(values) if e.kind=='COMPATIBILITY' and e.subject=='vscode')
        values[index]=replace(values[index],status='PASS')
        self.error('PIPELINE_COMPATIBILITY_REFERENCE_MISMATCH',lambda:replace(result,evidence=tuple(values)))

    def test_five_regression_dimensions_present(self):
        self.assertEqual({x.suite for x in snapshot().regressions},set(p.SUITES))

    def test_failed_predecessor_blocks_publication(self):
        a=snapshot();failed=tuple(replace(x,passed=x.passed-1,failed=1) if x.suite=='P15' else x for x in a.regressions)
        gates=p.ReleasePipelineResult(a.pipeline,a.evidence,failed).evaluate()
        self.assertEqual(next(g for g in gates if g['id']=='regressions')['status'],'FAIL')
        self.assertTrue(all(not d.record()['would_publish_if_authorized'] for d in p.publication_dry_run(replace(a,regressions=failed))))
        values=tuple(replace(e,status='FAIL') if e.kind=='SIGNING' else e for e in a.evidence)
        self.assertEqual(next(g['status'] for g in replace(a,evidence=values).evaluate() if g['id']=='signing'),'FAIL')

    def test_target_facts_not_collapsed(self):
        result=snapshot();self.assertEqual(len(result.record()['target_readiness']),4)
        facts={(e.kind,e.subject):e for e in result.evidence}
        self.assertEqual(facts['OWNER_BUILD','python-wheel'].status,'INCOMPLETE')
        self.assertEqual(facts['RAW_REPRODUCIBILITY','python-sdist'].status,'DEFERRED')
        self.assertEqual(facts['OWNER_BUILD','vscode-vsix'].status,'INCOMPLETE')
        self.assertEqual(facts['RAW_REPRODUCIBILITY','visual-studio-vsix'].status,'DEFERRED')
        self.assertEqual(facts['RAW_REPRODUCIBILITY','native-exe'].status,'PASS')
        self.assertEqual(facts['OWNER_BUILD','native-exe'].status,'PASS')

    def test_native_profile_scope_preserved(self):
        native=next(d for d in architecture().artifacts if d.target.identifier=='native-win-x64')
        self.assertEqual(native.target.native_profile,r.PROFILE)
        self.assertFalse(native.target.record()['whole_language_native_support'])

    def test_installation_skip_and_signing_remain_visible(self):
        gates={g['id']:g for g in snapshot().evaluate()}
        self.assertIn((('INSTALLATION_HOST','release'),'SKIPPED'),[(row[0],row[1]) for row in gates['installation']['observations']])
        self.assertEqual(gates['signing']['status'],'BLOCKED')
        self.assertIn('CRYPTO_PROVIDER_UNAVAILABLE',repr(gates['signing']['blockers']))

    def test_future_gate_pass_rejected(self):
        for kind in ('SIGNING','ACCEPTANCE'):
            self.error('PIPELINE_FUTURE_GATE_PASS_UNSUPPORTED',lambda:p.GateEvidence(architecture().release,kind,'release','PASS',(report(1),)))

    def test_unknown_evidence_never_eligible(self):
        result=p.ReleasePipelineResult(p.pipeline_for(architecture()))
        self.assertTrue(any(g['status']=='INCOMPLETE' for g in result.evaluate()))
        self.assertFalse(any(d.record()['would_publish_if_authorized'] for d in p.publication_dry_run(result)))

    def test_conflicts_and_cross_release_replay_rejected(self):
        result=snapshot()
        self.error('PIPELINE_EVIDENCE_CONFLICT',lambda:replace(result,evidence=result.evidence+(replace(result.evidence[0],status='FAIL'),)))
        changed=replace(result.evidence[0],release=replace(result.pipeline.release,version='2.0.0'))
        self.error('PIPELINE_EVIDENCE_RELEASE_MISMATCH',lambda:replace(result,evidence=(changed,)+result.evidence[1:]))

    def test_stable_channel_cannot_bypass(self):
        matrix=architecture();release=replace(matrix.release,channel='STABLE')
        pipeline=p.pipeline_for(replace(matrix,release=release,artifacts=tuple(replace(d,release=release) for d in matrix.artifacts)))
        self.assertFalse(snapshot(pipeline).record()['release_ready'])

    def test_retry_and_changed_evidence_identity(self):
        a=snapshot();self.assertEqual(a.evaluate(),a.evaluate())
        index=next(i for i,e in enumerate(a.evidence) if e.kind=='RAW_REPRODUCIBILITY' and e.subject=='native-exe')
        evidence=list(a.evidence);evidence[index]=replace(evidence[index],status='FAIL')
        self.assertNotEqual(a.fingerprint(),replace(a,evidence=tuple(evidence)).fingerprint())

    def test_symbolic_credentials_no_value_interface(self):
        for surface in r.TARGETS:
            record=p.PublicationTarget(surface).record()
            self.assertTrue(record['credential_requirement'].endswith('_TOKEN'))
            self.assertEqual(record['credential_value'],'NOT_LOADED')
        with self.assertRaises(TypeError):p.PublicationTarget('python',token='secret')
        self.error('PUBLICATION_TARGET_UNSUPPORTED',lambda:p.PublicationTarget('arbitrary-endpoint'))

    def test_structured_reasons_no_arbitrary_log_values(self):
        self.error('PIPELINE_REASON_INVALID',lambda:p.GateEvidence(architecture().release,'SIGNING','release','BLOCKED',reasons=('arbitrary-secret-text',)))

    def test_dry_run_has_no_publication_authority_trust_or_approval(self):
        result=snapshot()
        for dry in p.publication_dry_run(result):
            rec=dry.record()
            self.assertFalse(rec['publication_performed']);self.assertEqual(rec['network_publication_calls'],0)
            for key in ('approved','trusted','authority','would_publish_if_authorized'):self.assertFalse(rec[key])
        self.assertFalse(result.record()['release_ready'])

    def test_artifact_and_manifest_owner_adapters(self):
        man=manifest();artifact=man.artifacts.artifacts[0]
        gate=p.artifact_gate(artifact._slot.descriptor,artifact)
        self.assertEqual(next(ref.fingerprint for ref in gate.references if ref.schema==artifact.DOMAIN),artifact.fingerprint())
        self.assertEqual(p.manifest_gate(man,'vscode').status,'PASS')
        self.assertEqual(p.manifest_gate(replace(man,checksums=None),'vscode').status,'INCOMPLETE')
        self.error('PIPELINE_ARTIFACT_BINDING_INVALID',lambda:p.artifact_gate(replace(artifact._slot.descriptor,surface_version='different'),artifact))

    def test_compatibility_owner_adapter(self):
        old,new=manifest(),manifest('2.0.0',surface_version='0.2.0')
        for status,expected in (('COMPATIBLE','PASS'),('UNKNOWN','INCOMPLETE'),('INCOMPATIBLE','FAIL'),('MIGRATION_REQUIRED','DEFERRED')):
            self.assertEqual(p.compatibility_gate(assessment(old,new,status),'vscode').status,expected)

    def test_installation_receipt_consumed_without_execution(self):
        installation=plan();receipt=p.InstallationReceipt(installation,installation.current,installation.resulting_state())
        with patch('tooling.release_installation.apply',side_effect=AssertionError('no installation')):
            self.assertEqual(p.installation_gate(receipt).references[0].fingerprint,receipt.fingerprint())

    def test_no_filesystem_process_or_environment_dependency(self):
        result=snapshot()
        with patch('builtins.open',side_effect=AssertionError('no I/O')):
            record=result.record();p.publication_dry_run(result)[0].record()
        self.assertNotIn(str(ROOT),repr(record));self.assertNotIn('timestamp',repr(record))

    def test_realistic_surface_gate_set(self):
        result=snapshot()
        self.assertEqual(len(result.pipeline.steps),13)
        self.assertEqual(len(p.publication_dry_run(result)),4)
        self.assertEqual(len(result.pipeline.architecture.artifacts),5)

    def test_static_security_audit(self):
        source=(ROOT/'apexforge/tooling/release_pipeline.py').read_text();tree=ast.parse(source)
        imports={a.name for node in ast.walk(tree) if isinstance(node,ast.Import) for a in node.names}
        imports|={node.module for node in ast.walk(tree) if isinstance(node,ast.ImportFrom)}
        self.assertFalse(imports & {'os','pathlib','subprocess','socket','requests','urllib','keyring','pickle','time','uuid'})
        calls={node.func.attr if isinstance(node.func,ast.Attribute) else node.func.id for node in ast.walk(tree) if isinstance(node,ast.Call) and isinstance(node.func,(ast.Attribute,ast.Name))}
        self.assertFalse(calls & {'open','read_text','read_bytes','getenv','Popen','run','apply','execute_native','publish','upload','eval','exec','__import__'})


if __name__=='__main__':unittest.main(verbosity=2)
