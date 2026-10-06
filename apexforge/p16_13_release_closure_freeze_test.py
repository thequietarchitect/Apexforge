"""P16.13 phase closure; no Git mutation or product-release action in these tests."""
from dataclasses import FrozenInstanceError,replace
from hashlib import sha256
from pathlib import Path
import ast
import json
import sys
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'apexforge'));sys.path.insert(0,str(ROOT))
from tooling import release_closure as c,release_acceptance as a,release_architecture as r,release_pipeline as p
from tooling.package_manifest import CanonicalReference
from p16_12_release_candidate_acceptance_test import evidence,candidate


def accepted_review_verdict():
    old=evidence()
    counts={'suite':'P16','passed':410,'skipped':1,'failed':0,'discovered':411,'baseline':old.release.baseline.commit}
    ref=CanonicalReference('apexforge.regression-count-review/v1','source',sha256(json.dumps(counts,sort_keys=True,separators=(',',':')).encode()).hexdigest().upper())
    regs=tuple(replace(x,passed=410,discovered=411,reference=ref) if x.suite=='P16' else x for x in old.pipeline.regressions)
    new=replace(old,pipeline=replace(old.pipeline,regressions=regs))
    return a.ReleaseCandidateVerdict(a.acceptance_matrix(candidate(new)))


def source_census():
    # Test harness only: explicit reviewed paths; production does not read a filesystem.
    return tuple(c.ClosureSourceFile(path,sha256((ROOT/path).read_bytes()).hexdigest().upper()) for path in c.INCOMING_PATHS)


def closure():
    verdict=accepted_review_verdict()
    return c.ReleaseClosureRecord(verdict,source_census(),verdict.matrix.candidate.evidence.pipeline.regressions)


class ContractTests(unittest.TestCase):
    def error(self,code,callback):
        with self.assertRaises(c.ReleaseClosureError) as failure:callback()
        self.assertEqual(failure.exception.code,code)

    def test_record_and_source_immutable(self):
        record=closure()
        for obj,field in ((record,'tag'),(record.sources[0],'sha256')):
            with self.assertRaises(FrozenInstanceError):setattr(obj,field,'changed')

    def test_exact_release_and_predecessor(self):
        record=closure()
        self.assertEqual(record.release,record.verdict.matrix.candidate.evidence.release)
        self.assertEqual(record.predecessor,r.P15_BASELINE)
        self.assertEqual(record.record()['predecessor']['commit'],r.P15_COMMIT)

    def test_changed_predecessor_reidentifies_and_not_ready(self):
        old=closure();new=replace(old,predecessor=replace(old.predecessor,commit='0'*40))
        self.assertNotEqual(old.fingerprint(),new.fingerprint())
        self.assertFalse(new.ready_for_freeze)

    def test_independent_and_permuted_determinism(self):
        old,new=closure(),closure()
        self.assertIsNot(old,new);self.assertEqual(old.fingerprint(),new.fingerprint())
        changed=replace(old,sources=tuple(reversed(old.sources)),regressions=tuple(reversed(old.regressions)))
        self.assertEqual(old.fingerprint(),changed.fingerprint())

    def test_changed_source_reidentifies(self):
        old=closure();sources=(replace(old.sources[0],sha256='E'*64),)+old.sources[1:]
        self.assertNotEqual(old.fingerprint(),replace(old,sources=sources).fingerprint())

    def test_changed_verdict_and_blockers_reidentify(self):
        old=closure();ev=old.verdict.matrix.candidate.evidence
        values=tuple(replace(x,status='FAIL',reasons=('ARTIFACT_UNAVAILABLE',)) if x.kind=='OWNER_BUILD' and x.subject=='python-wheel' else x for x in ev.pipeline.evidence)
        ev=replace(ev,pipeline=replace(ev.pipeline,evidence=values));verdict=a.ReleaseCandidateVerdict(a.acceptance_matrix(candidate(ev)))
        new=c.ReleaseClosureRecord(verdict,old.sources,old.regressions)
        self.assertNotEqual(old.fingerprint(),new.fingerprint());self.assertNotEqual(old.blockers,new.blockers)
        self.assertFalse(new.ready_for_freeze)

    def test_blocker_suppression_rejected(self):
        old=closure()
        self.error('CLOSURE_BLOCKER_SUPPRESSION_REJECTED',lambda:replace(old,blockers=()))
        self.error('CLOSURE_BLOCKER_SUPPRESSION_REJECTED',lambda:replace(old,blockers=old.blockers[:-1]))

    def test_contract_evidence_for_all_twelve_slices(self):
        record=closure().record()
        self.assertEqual([x['slice'] for x in record['contracts']],list(range(1,13)))
        self.assertTrue(all(len(x['files'])==3 for x in record['contracts']))
        self.assertEqual(len(record['sources']),36)

    def test_blocked_candidate_exact_counts_preserved(self):
        record=closure();data=record.record()['acceptance_state']
        self.assertEqual(record.verdict.status,'BLOCKED')
        self.assertEqual(len(data['satisfied_required']),35);self.assertEqual(len(data['unsatisfied_required']),30)
        self.assertFalse(data['grants_release_approval'])

    def test_implementation_complete_distinct_from_product(self):
        record=closure();self.assertTrue(record.ready_for_freeze)
        data=record.record();self.assertTrue(data['implementation_complete'])
        for key in ('candidate_accepted','product_ready','product_published','production_signed','grants_authority',
                    'product_installation_performed','product_signing_performed'):
            self.assertFalse(data[key])

    def test_pipeline_security_and_publication_blocked(self):
        record=closure().record()
        self.assertFalse(record['pipeline_release_ready'])
        self.assertEqual(record['crypto'],'CRYPTO_PROVIDER_UNAVAILABLE')
        self.assertEqual(record['trust'],'NOT_EVALUATED')
        self.assertTrue(all(status=='BLOCKED' for _,status in record['publication_targets']))

    def test_all_limitations_present(self):
        data=closure().record();facts={(x['kind'],x['subject']):x for x in data['limitation_history']}
        self.assertEqual(facts['OWNER_BUILD','python-wheel']['status'],'INCOMPLETE')
        self.assertEqual(facts['RAW_REPRODUCIBILITY','python-sdist']['status'],'DEFERRED')
        self.assertEqual(facts['OWNER_BUILD','vscode-vsix']['status'],'INCOMPLETE')
        self.assertEqual(facts['RAW_REPRODUCIBILITY','visual-studio-vsix']['status'],'DEFERRED')
        self.assertEqual(facts['RAW_REPRODUCIBILITY','native-exe']['status'],'PASS')
        self.assertEqual(facts['INSTALLATION_HOST','release']['status'],'SKIPPED')
        self.assertEqual(facts['SIGNING','release']['status'],'BLOCKED')

    def test_native_scope_and_exe_correction(self):
        record=closure();native=next(d for d in record.verdict.matrix.candidate.evidence.pipeline.pipeline.architecture.artifacts if d.target.identifier=='native-win-x64')
        self.assertEqual(native.target.native_profile,r.PROFILE)
        self.assertFalse(native.target.record()['whole_language_native_support'])
        self.assertEqual(next(row[2] for row in r.SURFACES if row[0]=='native-win-x64'),('dll','exe'))
        source=(ROOT/'apexforge/p16_1_release_architecture_contract_test.py').read_text()
        self.assertIn('format="wasm"',source)

    def test_skip_is_not_pass_and_regressions_exact(self):
        record=closure();p16=next(x for x in record.regressions if x.suite=='P16')
        self.assertEqual((p16.passed,p16.skipped,p16.discovered),(410,1,411))
        self.assertEqual(p16.status,'SKIPPED')
        bad=tuple(replace(x,passed=411,skipped=0) if x.suite=='P16' else x for x in record.regressions)
        self.assertFalse(replace(record,regressions=bad).ready_for_freeze)

    def test_changed_regression_reidentifies(self):
        old=closure();regs=tuple(replace(x,passed=x.passed+1,discovered=x.discovered+1) if x.suite=='P16' else x for x in old.regressions)
        self.assertNotEqual(old.fingerprint(),replace(old,regressions=regs).fingerprint())
        failed=tuple(replace(x,passed=x.passed-1,failed=1) if x.suite=='P16' else x for x in old.regressions)
        self.assertFalse(replace(old,regressions=failed).ready_for_freeze)

    def test_phase_tag_not_product_tag(self):
        record=closure();self.assertEqual(record.tag,'afp-p16.13-freeze')
        self.assertFalse(record.record()['phase_tag_is_product_release'])
        self.error('CLOSURE_SCHEMA_INVALID',lambda:replace(record,tag='v1.0.0'))

    def test_exact_39_path_inventory_no_predecessor_or_residue(self):
        self.assertEqual(len(c.FREEZE_PATHS),39);self.assertEqual(len(set(c.FREEZE_PATHS)),39)
        self.assertEqual(len(c.INCOMING_PATHS),36)
        self.assertTrue(all(path.startswith(('apexforge/p16_','apexforge/tooling/','docs/p16/')) for path in c.FREEZE_PATHS))
        self.assertFalse(any('p15_' in path or '/build/' in path or '/dist/' in path or path.endswith(('.exe','.obj','.pdb')) for path in c.FREEZE_PATHS))

    def test_unexpected_missing_or_duplicate_source_rejected(self):
        old=closure()
        self.error('CLOSURE_SOURCE_INVENTORY_INVALID',lambda:replace(old,sources=old.sources[:-1]))
        self.error('CLOSURE_SOURCE_INVENTORY_INVALID',lambda:replace(old,sources=old.sources[:-1]+(old.sources[0],)))
        self.error('CLOSURE_SOURCE_PATH_INVALID',lambda:c.ClosureSourceFile('apexforge/p15_wrong.py','A'*64))

    def test_no_waiver_and_no_operations_in_model(self):
        record=closure().record()
        self.assertFalse(record['waivers_added'])
        self.assertEqual(record['source_control_operation'],'EXTERNAL_CLOSURE_PROCEDURE_ONLY')
        with self.assertRaises(TypeError):c.ReleaseClosureRecord(closure().verdict,source_census(),closure().regressions,waive=True)

    def test_no_io_host_or_wall_clock_identity(self):
        record=closure()
        with patch('builtins.open',side_effect=AssertionError('no I/O')):data=record.canonical_json()
        self.assertNotIn(str(ROOT),data);self.assertNotIn('timestamp',data)

    def test_static_security_audit(self):
        source=(ROOT/'apexforge/tooling/release_closure.py').read_text();tree=ast.parse(source)
        imports={x.name for node in ast.walk(tree) if isinstance(node,ast.Import) for x in node.names}
        imports|={node.module for node in ast.walk(tree) if isinstance(node,ast.ImportFrom)}
        self.assertFalse(imports & {'os','pathlib','subprocess','socket','requests','urllib','time','uuid','keyring','ctypes','pickle'})
        calls={node.func.attr if isinstance(node.func,ast.Attribute) else node.func.id for node in ast.walk(tree) if isinstance(node,ast.Call) and isinstance(node.func,(ast.Name,ast.Attribute))}
        self.assertFalse(calls & {'open','read_bytes','getenv','run','Popen','apply','sign','verify','upload','publish','eval','exec','__import__'})


if __name__=='__main__':unittest.main(verbosity=2)
