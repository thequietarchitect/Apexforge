"""P16.12 evidence evaluation; contract PASS does not accept the current candidate."""
from dataclasses import FrozenInstanceError,replace
from hashlib import sha256
from pathlib import Path
import ast
import sys
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'apexforge'));sys.path.insert(0,str(ROOT))
from tooling import release_acceptance as a, release_pipeline as p, release_architecture as r, release_manifest as m, release_security as s
from tooling.package_manifest import CanonicalReference
from p16_10_ci_release_pipeline_dry_run_test import snapshot,architecture
from p16_9_install_upgrade_rollback_test import manifest,plan,assessment
from p16_11_release_security_signing_verification_test import policy,request

COUNTS={1:(25,0),2:(31,0),3:(31,0),4:(41,0),5:(35,0),6:(33,0),7:(38,0),8:(36,0),9:(39,1),10:(34,0),11:(35,0)}


def report(number):
    file=next((ROOT/'docs/p16').glob('P16_'+str(number)+'_*.md'))
    return CanonicalReference('apexforge.release-review-evidence/v1','source',sha256(file.read_bytes()).hexdigest().upper())


def reviews(release):
    return tuple(a.ContractReview(number,p.RegressionEvidence(release,'P16',passed,skip,0,passed+skip,report(number)))
                 for number,(passed,skip) in COUNTS.items())


def evidence(pipeline=None):
    pipeline=snapshot() if pipeline is None else pipeline
    values=tuple(replace(x,passed=378,skipped=1,discovered=379,reference=report(11)) if x.suite=='P16' else x for x in pipeline.regressions)
    pipeline=replace(pipeline,regressions=values)
    return a.ReleaseCandidateEvidence(pipeline,reviews(pipeline.pipeline.release))


def candidate(evidence_=None):
    return a.ReleaseCandidateIdentity('p16-current-review',evidence() if evidence_ is None else evidence_)


def verdict(evidence_=None):
    return a.ReleaseCandidateVerdict(a.acceptance_matrix(candidate(evidence_)))


def owned_evidence():
    # Explicit generic byte fixtures exercise owner linkage, not genuine target packaging.
    man=manifest();artifact=man.artifacts.artifacts[0]
    install=plan(man);receipt=p.InstallationReceipt(install,install.current,install.resulting_state())
    compat=assessment(manifest('0.9.0',surface_version='0.0.9'),man)
    subjects=(s.SigningSubject(man),s.SigningSubject(artifact));pol=policy(subjects)
    bundle=s.ReleaseSignatureBundle(pol,tuple(s.verify(request(subject,pol)) for subject in subjects))
    gates=(p.GateEvidence(man.architecture.release,'BASELINE','release','PASS',(m.reference(r.P15_BASELINE),)),
           p.artifact_gate(artifact._slot.descriptor,artifact),p.manifest_gate(man,'vscode'),p.compatibility_gate(compat,'vscode'),
           p.installation_gate(receipt),s.signing_gate(bundle))
    pipeline=p.ReleasePipelineResult(p.pipeline_for(man.architecture),gates)
    return a.ReleaseCandidateEvidence(pipeline,reviews(man.architecture.release),bundle,(man,),(compat,),(artifact,),(receipt,))


class ContractTests(unittest.TestCase):
    def error(self,code,callback):
        with self.assertRaises(a.ReleaseAcceptanceError) as failure:callback()
        self.assertEqual(failure.exception.code,code)

    def rows(self,evidence_=None):
        return {x.criterion.identifier:x for x in a.acceptance_matrix(candidate(evidence_)).evaluate()}

    def test_candidate_snapshot_criterion_matrix_verdict_immutable(self):
        c=candidate();matrix=a.acceptance_matrix(c);v=a.ReleaseCandidateVerdict(matrix)
        for obj,field in ((c,'identifier'),(c.evidence,'reviews'),(matrix,'criteria'),(matrix.criteria[0],'level'),(v,'matrix')):
            with self.assertRaises(FrozenInstanceError):setattr(obj,field,'changed')

    def test_exact_release_and_frozen_baseline(self):
        c=candidate();self.assertEqual(c.record()['baseline']['commit'],r.P15_COMMIT)
        self.assertEqual(c.evidence.release.baseline.tag,r.P15_TAG)
        matrix=architecture();release=replace(matrix.release,version='2.0.0')
        new=replace(matrix,release=release,artifacts=tuple(replace(d,release=release) for d in matrix.artifacts))
        c2=candidate(evidence(snapshot(p.pipeline_for(new))))
        self.assertNotEqual(c.fingerprint(),c2.fingerprint())
        bad=replace(release,baseline=replace(r.P15_BASELINE,commit='0'*40))
        with self.assertRaises(p.ReleasePipelineError):p.pipeline_for(replace(new,release=bad,artifacts=tuple(replace(d,release=bad) for d in new.artifacts)))

    def test_snapshot_reference_change_reidentifies_every_layer(self):
        old=evidence();review=old.reviews[-1]
        changed=replace(review,regression=replace(review.regression,reference=replace(review.regression.reference,fingerprint='D'*64)))
        new=replace(old,reviews=old.reviews[:-1]+(changed,))
        self.assertNotEqual(old.fingerprint(),new.fingerprint())
        self.assertNotEqual(candidate(old).fingerprint(),candidate(new).fingerprint())
        self.assertNotEqual(verdict(old).fingerprint(),verdict(new).fingerprint())

    def test_duplicate_or_conflicting_review_rejected(self):
        old=evidence();review=old.reviews[-1]
        self.error('ACCEPTANCE_EVIDENCE_CONFLICT',lambda:replace(old,reviews=old.reviews+(review,)))
        changed=replace(review,regression=replace(review.regression,reference=replace(review.regression.reference,fingerprint='F'*64)))
        self.error('ACCEPTANCE_REVIEW_CONFLICT',lambda:replace(old,reviews=old.reviews+(changed,)))

    def test_criterion_category_status_and_scope_bounded(self):
        criterion=a.required_criteria(evidence())[0]
        for change in ({'category':'RUN_COMMAND'},{'scope':'real-system'},{'source':'CALLBACK'},{'level':'WAIVED'}):
            self.error('ACCEPTANCE_CRITERION_INVALID',lambda:replace(criterion,**change))
        self.error('ACCEPTANCE_STATUS_INVALID',lambda:a.CriterionResult(criterion,'UNKNOWN'))

    def test_required_pass_only_and_information_not_satisfaction(self):
        criterion=a.AcceptanceCriterion('example','BASELINE','global','BASELINE','release')
        ref=m.reference(r.P15_BASELINE)
        for status in a.STATES:
            row=a.CriterionResult(criterion,status,(ref,))
            self.assertEqual(row.satisfies_required,status=='PASS')
        self.assertFalse(a.CriterionResult(replace(criterion,level='INFORMATIONAL'),'PASS',(ref,)).satisfies_required)

    def test_missing_required_criterion_not_filled_by_information(self):
        c=candidate();required=a.required_criteria(c.evidence)
        missing=next(x for x in required if x.identifier=='production-signing')
        info=replace(next(x for x in required if x.identifier=='baseline'),identifier='informational-pass',level='INFORMATIONAL')
        matrix=a.ReleaseAcceptanceMatrix(c,tuple(x for x in required if x!=missing)+(info,))
        row=next(x for x in matrix.evaluate() if x.criterion.identifier=='production-signing')
        self.assertEqual(row.status,'INCOMPLETE');self.assertIn('ACCEPTANCE_REQUIRED_CRITERION_MISSING',row.reasons)
        self.assertNotEqual(a.ReleaseCandidateVerdict(matrix).status,'ACCEPTED')

    def test_required_criterion_cannot_be_demoted_or_relabelled(self):
        c=candidate();rows=list(a.required_criteria(c.evidence));rows[0]=replace(rows[0],level='INFORMATIONAL')
        self.error('ACCEPTANCE_REQUIRED_CRITERION_CHANGED',lambda:a.ReleaseAcceptanceMatrix(c,tuple(rows)))
        self.error('ACCEPTANCE_CRITERION_CONFLICT',lambda:a.ReleaseAcceptanceMatrix(c,(rows[0],rows[0])))

    def test_missing_required_evidence_incomplete(self):
        result=p.ReleasePipelineResult(p.pipeline_for(architecture()))
        rows=self.rows(a.ReleaseCandidateEvidence(result))
        self.assertEqual(rows['baseline'].status,'INCOMPLETE')
        self.assertEqual(rows['regression-P15'].status,'INCOMPLETE')
        self.assertNotEqual(verdict(a.ReleaseCandidateEvidence(result)).status,'ACCEPTED')

    def test_skip_deferred_blocked_preserved(self):
        rows=self.rows()
        self.assertEqual(rows['regression-P16'].status,'SKIPPED')
        self.assertEqual(rows['contract-P16-9'].status,'SKIPPED')
        self.assertEqual(rows['installation-host-coverage'].status,'SKIPPED')
        self.assertEqual(rows['raw-reproducibility-visual-studio-vsix'].status,'DEFERRED')
        self.assertEqual(rows['production-signing'].status,'BLOCKED')
        self.assertTrue(all(not rows[key].satisfies_required for key in ('regression-P16','installation-host-coverage','production-signing')))

    def test_pending_is_incomplete_not_pass(self):
        old=evidence();values=tuple(replace(x,status='PENDING') if x.kind=='OWNER_BUILD' and x.subject=='python-wheel' else x for x in old.pipeline.evidence)
        rows=self.rows(replace(old,pipeline=replace(old.pipeline,evidence=values)))
        self.assertEqual(rows['owner-build-python-wheel'].status,'INCOMPLETE')

    def test_all_four_surface_matrices_preserved(self):
        record=verdict().matrix.record()
        self.assertEqual(set(record['surface_matrix']),set(r.TARGETS))
        self.assertTrue(all(record['surface_matrix'][surface] for surface in r.TARGETS))

    def test_python_missing_wheel_and_raw_sdist_visible(self):
        rows=self.rows()
        self.assertEqual(rows['owner-build-python-wheel'].status,'INCOMPLETE')
        self.assertEqual(rows['owner-build-python-sdist'].status,'PASS')
        self.assertEqual(rows['raw-reproducibility-python-sdist'].status,'DEFERRED')
        self.assertFalse(rows['artifact-python-wheel'].satisfies_required)

    def test_deleting_wheel_requirement_does_not_make_surface_complete(self):
        matrix=architecture();matrix=replace(matrix,artifacts=tuple(d for d in matrix.artifacts if d.format!='wheel'))
        rows=self.rows(evidence(snapshot(p.pipeline_for(matrix))))
        self.assertEqual(rows['surface-coverage-python'].status,'INCOMPLETE')
        self.assertIn('ACCEPTANCE_REQUIRED_FORMAT_MISSING',rows['surface-coverage-python'].reasons)

    def test_vscode_unverified_build_and_visual_studio_distinction(self):
        rows=self.rows()
        self.assertEqual(rows['owner-build-vscode-vsix'].status,'INCOMPLETE')
        self.assertEqual(rows['owner-build-visual-studio-vsix'].status,'PASS')
        self.assertEqual(rows['raw-reproducibility-visual-studio-vsix'].status,'DEFERRED')

    def test_native_pass_is_only_frozen_profile(self):
        c=candidate();native=next(d for d in c.evidence.pipeline.pipeline.architecture.artifacts if d.target.identifier=='native-win-x64')
        self.assertEqual(native.target.native_profile,r.PROFILE)
        self.assertFalse(native.target.record()['whole_language_native_support'])
        self.assertEqual(self.rows()['native-profile'].status,'PASS')
        self.assertEqual(self.rows()['raw-reproducibility-native-exe'].status,'PASS')

    def test_owned_models_exactly_bound_without_execution(self):
        with patch('tooling.release_installation.apply',side_effect=AssertionError('no execution')):
            owned=owned_evidence();v=verdict(owned)
        self.assertEqual(len(owned.manifests),1);self.assertEqual(len(owned.builds),1)
        self.assertEqual(len(owned.compatibility),1);self.assertEqual(len(owned.receipts),1)
        self.assertEqual(v.status,'BLOCKED')

    def test_foreign_build_manifest_receipt_cannot_substitute(self):
        owned=owned_evidence();foreign=manifest('2.0.0')
        self.error('ACCEPTANCE_BUILD_BINDING_MISMATCH',lambda:replace(owned,builds=(foreign.artifacts.artifacts[0],)))
        self.error('ACCEPTANCE_RELEASE_MISMATCH',lambda:replace(owned,manifests=(foreign,)))
        other=plan(foreign);receipt=p.InstallationReceipt(other,other.current,other.resulting_state())
        self.error('ACCEPTANCE_RECEIPT_BINDING_MISMATCH',lambda:replace(owned,receipts=(receipt,)))

    def test_security_architecture_pass_not_signature_pass(self):
        rows=self.rows()
        self.assertEqual(rows['security-architecture'].status,'PASS')
        self.assertEqual(rows['production-signing'].status,'BLOCKED')
        owned=owned_evidence();self.assertEqual(owned.security.status,'UNAVAILABLE')
        self.assertFalse(owned.security.record()['production_signed'])
        self.assertEqual(verdict(owned).status,'BLOCKED')
        empty=replace(owned.security,results=())
        values=tuple(x for x in owned.pipeline.evidence if x.kind!='SIGNING')+(s.signing_gate(empty),)
        missing=replace(owned,pipeline=replace(owned.pipeline,evidence=values),security=empty)
        self.assertEqual(self.rows(missing)['production-signing'].status,'INCOMPLETE')

    def test_changed_security_evidence_reidentifies_snapshot(self):
        old=owned_evidence();bundle=old.security
        pol=replace(bundle.policy,revision='2')
        results=tuple(s.verify(replace(result.request,policy=pol)) for result in bundle.results)
        changed=s.ReleaseSignatureBundle(pol,results)
        values=tuple(x for x in old.pipeline.evidence if x.kind!='SIGNING')+(s.signing_gate(changed),)
        new=replace(old,pipeline=replace(old.pipeline,evidence=values),security=changed)
        self.assertNotEqual(old.fingerprint(),new.fingerprint())

    def test_conflicting_security_pipeline_evidence_rejected(self):
        old=owned_evidence();changed=replace(old.security,results=())
        self.error('ACCEPTANCE_SECURITY_BINDING_MISMATCH',lambda:replace(old,security=changed))

    def test_pipeline_blockers_preserved(self):
        v=verdict();rows=v.matrix.evaluate()
        publications=[x for x in rows if x.criterion.source=='PUBLICATION']
        self.assertEqual(len(publications),4)
        self.assertTrue(all(x.status=='BLOCKED' for x in publications))
        self.assertEqual(next(x.status for x in rows if x.criterion.identifier=='pipeline-readiness'),'BLOCKED')

    def test_explicit_failure_rejected_not_downgraded(self):
        old=evidence();regs=tuple(replace(x,passed=x.passed-1,failed=1) if x.suite=='P15' else x for x in old.pipeline.regressions)
        self.assertEqual(verdict(replace(old,pipeline=replace(old.pipeline,regressions=regs))).status,'REJECTED')
        values=tuple(replace(x,status='FAIL') if x.kind=='SIGNING' else x for x in old.pipeline.evidence)
        self.assertEqual(verdict(replace(old,pipeline=replace(old.pipeline,evidence=values))).status,'REJECTED')

    def test_verdict_exact_matrix_bound_and_stale_invalid(self):
        old=verdict();self.assertTrue(old.valid_for(old.matrix))
        ev=old.matrix.candidate.evidence;review=ev.reviews[0]
        changed=replace(review,regression=replace(review.regression,reference=replace(review.regression.reference,fingerprint='E'*64)))
        matrix=a.acceptance_matrix(candidate(replace(ev,reviews=(changed,)+ev.reviews[1:])))
        self.assertFalse(old.valid_for(matrix))
        self.assertEqual(old.record()['matrix'],old.matrix.fingerprint())

    def test_blocker_order_and_independent_determinism(self):
        ev=evidence();other=replace(ev,reviews=tuple(reversed(ev.reviews)),pipeline=replace(ev.pipeline,evidence=tuple(reversed(ev.pipeline.evidence)),regressions=tuple(reversed(ev.pipeline.regressions))))
        left,right=verdict(ev),verdict(other)
        self.assertEqual(left.fingerprint(),right.fingerprint())
        self.assertEqual(left.record()['blocker_codes'],right.record()['blocker_codes'])
        self.assertIsNot(left,right)

    def test_arbitrary_waiver_and_callback_unavailable(self):
        c=candidate()
        with self.assertRaises(TypeError):a.ReleaseAcceptanceMatrix(c,a.required_criteria(c.evidence),waive=('production-signing',))
        with self.assertRaises(TypeError):a.AcceptanceCriterion('callback','BASELINE','global','BASELINE','release',predicate=lambda:True)
        required=a.required_criteria(c.evidence)
        extra=replace(required[0],identifier='unowned-required-rule')
        self.error('ACCEPTANCE_ARBITRARY_POLICY_UNSUPPORTED',lambda:a.ReleaseAcceptanceMatrix(c,required+(extra,)))

    def test_engine_pass_distinct_from_blocked_current_candidate(self):
        v=verdict();record=v.record()
        self.assertEqual(v.status,'BLOCKED');self.assertFalse(record['grants_release_approval'])
        self.assertTrue(record['unsatisfied_required'])
        self.assertTrue(record['satisfied_required'])

    def test_no_trust_authority_publication_installation_signing_freeze(self):
        record=verdict().record()
        for key in ('grants_authority','grants_trust','publication_performed','installation_performed','signing_performed','freeze_performed'):
            self.assertFalse(record[key])
        self.assertEqual(record['approval_scope'],'EVIDENCE_ONLY')

    def test_no_filesystem_host_clock_dependency(self):
        ev=evidence()
        with patch('builtins.open',side_effect=AssertionError('no I/O')):record=verdict(ev).record()
        self.assertNotIn(str(ROOT),str(record));self.assertNotIn('timestamp',candidate(ev).canonical_json())

    def test_size_count_and_reference_limits(self):
        c=candidate();criteria=a.required_criteria(c.evidence)
        self.error('ACCEPTANCE_MATRIX_INVALID',lambda:a.ReleaseAcceptanceMatrix(c,criteria*(a.MAX_CRITERIA+1)))
        with patch.object(a,'MAX_REFERENCES',0):
            self.error('ACCEPTANCE_REFERENCE_SIZE_LIMIT',lambda:evidence())
        self.error('ACCEPTANCE_STATUS_INVALID',lambda:a.CriterionResult(criteria[0],'ACCEPTED'))

    def test_missing_criteria_matrix_cannot_be_accepted(self):
        c=candidate();matrix=a.ReleaseAcceptanceMatrix(c,())
        self.assertTrue(all(x.status=='INCOMPLETE' for x in matrix.evaluate()))
        self.assertEqual(a.ReleaseCandidateVerdict(matrix).status,'INCOMPLETE')

    def test_static_security_audit(self):
        source=(ROOT/'apexforge/tooling/release_acceptance.py').read_text();tree=ast.parse(source)
        imports={x.name for node in ast.walk(tree) if isinstance(node,ast.Import) for x in node.names}
        imports|={node.module for node in ast.walk(tree) if isinstance(node,ast.ImportFrom)}
        self.assertFalse(imports & {'os','pathlib','subprocess','socket','requests','urllib','time','uuid','keyring','ctypes','pickle'})
        calls={node.func.attr if isinstance(node.func,ast.Attribute) else node.func.id for node in ast.walk(tree) if isinstance(node,ast.Call) and isinstance(node.func,(ast.Attribute,ast.Name))}
        self.assertFalse(calls & {'open','read_bytes','getenv','Popen','run','apply','sign','verify','upload','publish','eval','exec','__import__'})


if __name__=='__main__':unittest.main(verbosity=2)
