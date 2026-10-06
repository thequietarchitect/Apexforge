"""P16.9 isolated file projections; no actual platform installer is invoked."""
from dataclasses import FrozenInstanceError, replace
from pathlib import Path
import ast
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'apexforge'))
sys.path.insert(0, str(ROOT))
from tooling import release_installation as i, release_architecture as r, release_build as b, release_manifest as m, release_versioning as v
from tooling.package_manifest import PackagePath, CanonicalReference


def manifest(version='1.0.0', files=(('a', b'first'),), surface='vscode', surface_version='0.1.0'):
    release = r.ReleaseIdentity('install-review', version, 'DEVELOPMENT', r.P15_BASELINE)
    target = r.ReleaseTarget(surface, r.PROFILE if surface == 'native-win-x64' else '')
    role, fmt = {'python':('PYTHON_DISTRIBUTION','sdist'), 'vscode':('VSCODE_EXTENSION','vsix'),
        'visual-studio':('VISUAL_STUDIO_EXTENSION','vsix'), 'native-win-x64':('NATIVE_COMPONENT','exe')}[surface]
    artifacts=[]
    for name, data in files:
        filename = name + ('.tar.gz' if fmt == 'sdist' else '.'+fmt)
        descriptor=r.ReleaseArtifactDescriptor(release,r.ReleaseArtifactIdentity(name),target,role,fmt,filename,surface_version,'SUPPORTED')
        inp=b.ReleaseBuildInput(release,PackagePath(filename),'SUPPLIED_DATA',data,b.digest(data))
        recipe=b.ReleaseBuildRecipe('fixture-'+name,release,'COPY_BYTES',b.ReleaseBuildEnvironment('isolated-fixture','test'),
                                   (inp,),(b.ReleaseBuildOutputSlot(descriptor,inp.identity),))
        artifacts.append(b.ReleaseBuildArtifact(recipe,descriptor.identity,data,b.digest(data)))
    matrix=r.ReleaseArtifactMatrix(release,tuple(a._slot.descriptor for a in artifacts))
    artifact_set=b.ReleaseArtifactSet(release,tuple(a.recipe for a in artifacts),tuple(artifacts))
    sums=m.ReleaseChecksumSet(release,m.reference(matrix),tuple(m.checksum_for(a) for a in artifacts))
    lineage=m.required_lineage(matrix,artifact_set,sums)
    provenance=m.ReleaseProvenanceBundle(release,tuple(m.ReleaseProvenanceRecord('p'+str(index),release,kind,subject,predecessors)
                          for index,(kind,subject,predecessors) in enumerate(lineage)))
    return m.ReleaseManifest(matrix,artifact_set,sums,provenance)


def plan(man=None, current=None, paths=None, assessment=None):
    man=manifest() if man is None else man
    kind=next(kind for kind,surface in i.TARGETS.items() if surface==man.architecture.artifacts[0].target.identifier)
    target=i.DeploymentTarget(kind,'review-slot')
    ident=i.InstallationIdentity(target,man)
    artifacts=man.artifacts.artifacts
    paths=tuple('payload/'+a._slot.descriptor.filename for a in artifacts) if paths is None else paths
    files=tuple(i.FileProjection(PackagePath(path),artifact) for path,artifact in zip(paths,artifacts))
    return i.InstallationPlan(ident,files,i.DeploymentState(target) if current is None else current,assessment)


def assessment(source, target, status='COMPATIBLE', declared=True):
    surface=v.ReleaseVersionSurface(source.architecture.artifacts[0].target,'VSCODE_EXTENSION','editor')
    old=v.ReleaseSurfaceVersion(source.architecture.release,surface,source.architecture.artifacts[0].surface_version)
    new=v.ReleaseSurfaceVersion(target.architecture.release,surface,target.architecture.artifacts[0].surface_version)
    ref=CanonicalReference('apexforge.installation-fixture/v1','source','A'*64)
    migration=v.ReleaseMigrationReference('explicit-migration',old,new,'deferred-owner') if status=='MIGRATION_REQUIRED' else None
    declaration=v.ReleaseCompatibilityDeclaration(old,new,status,() if status=='UNKNOWN' else (ref,),migration)
    policy=v.ReleaseCompatibilityPolicy('explicit-policy','1',old.release,new.release,(surface,),(old,),(new,),
                                         (declaration,) if declared else ())
    return v.ReleaseUpgradeAssessment(policy,v.compatibility_matrix(policy))


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='apexforge-install-test-')
        self.context=i.isolated_root(Path(self.temp.name),test_controlled=True)
        self.root=self.context.__enter__()

    def tearDown(self):
        self.context.__exit__(None,None,None)
        self.temp.cleanup()

    def error(self, code, callback):
        with self.assertRaises(i.InstallationError) as failure:callback()
        self.assertEqual(failure.exception.code,code)

    def install(self):
        p=plan();res=i.apply(p,self.root)
        self.assertEqual(res.status,'APPLIED')
        return p,res.receipt

    def upgrade(self):
        first,receipt=self.install()
        target=manifest('2.0.0',(('a',b'second'),('b',b'new-only')),surface_version='0.2.0')
        p=plan(target,receipt.result,assessment=assessment(first.identity.manifest,target))
        res=i.apply(p,self.root)
        self.assertEqual(res.status,'APPLIED')
        return first,receipt,p,res.receipt

    def test_immutable_target_identity_plan_state_receipt(self):
        p,receipt=self.install()
        for obj,field in ((p.identity.target,'kind'),(p.identity,'policy'),(p,'files'),(receipt,'result'),(receipt.result,'predecessor')):
            with self.assertRaises(FrozenInstanceError):setattr(obj,field,'changed')

    def test_bounded_targets(self):
        self.error('INSTALLATION_TARGET_INVALID',lambda:i.DeploymentTarget('SYSTEM_REGISTRY','review'))

    def test_release_and_manifest_binding(self):
        a,c=plan(),plan(manifest('2.0.0'))
        self.assertNotEqual(a.identity.fingerprint(),c.identity.fingerprint())
        self.assertNotEqual(a.fingerprint(),c.fingerprint())

    def test_incomplete_and_wrong_target_rejected(self):
        a=manifest()
        self.error('INSTALLATION_MANIFEST_NOT_COMPLETE',lambda:i.InstallationIdentity(i.DeploymentTarget('VSCODE_EXTENSION_ROOT','review'),replace(a,checksums=None)))
        self.error('INSTALLATION_TARGET_MISMATCH',lambda:i.InstallationIdentity(i.DeploymentTarget('PYTHON_ENVIRONMENT','review'),a))

    def test_plan_no_mutation(self):
        before=tuple(self.root.path.iterdir());plan()
        self.assertEqual(before,tuple(self.root.path.iterdir()))

    def test_filename_only_or_substituted_artifact_rejected(self):
        p=plan()
        self.error('INSTALLATION_FILE_INVALID',lambda:i.FileProjection(PackagePath('a.vsix'),'a.vsix'))
        other=manifest('2.0.0').artifacts.artifacts[0]
        self.error('INSTALLATION_EVIDENCE_MISMATCH',lambda:replace(p,files=(i.FileProjection(PackagePath('a.vsix'),other),)))

    def test_checksum_contradiction_rejected(self):
        a=manifest();bad=replace(a.checksums.records[0],digest='B'*64)
        sums=replace(a.checksums,records=(bad,))
        self.error('INSTALLATION_MANIFEST_NOT_COMPLETE',lambda:plan(replace(a,checksums=sums)))

    def test_clean_exact_bytes_and_receipt(self):
        p,receipt=self.install()
        for f in p.files:self.assertEqual((self.root.path/f.path.value).read_bytes(),f.artifact.data)
        self.assertEqual(receipt.plan,p)
        self.assertEqual(receipt.result.receipt_plan,p.fingerprint())

    def test_logical_path_safety(self):
        for path in ('../x','/x','C:/x','a/../x','CON.txt','x\\y','x//y'):
            with self.assertRaises(ValueError):PackagePath(path)

    def test_case_alias_and_directory_collisions(self):
        a=manifest(files=(('a',b'a'),('b',b'b')))
        for paths in (('dir/a','DIR/b'),('a','A'),('a','a/b')):
            self.error('INSTALLATION_PATH_CONFLICT',lambda:plan(a,paths=paths))

    def test_existing_unknown_content_not_overwritten(self):
        p=plan();path=self.root.path/p.files[0].path.value;path.parent.mkdir();path.write_bytes(b'unrelated')
        result=i.apply(p,self.root)
        self.assertEqual(result.code,'INSTALLATION_EXISTING_CONTENT_CONFLICT')
        self.assertEqual(path.read_bytes(),b'unrelated')

    def test_existing_case_alias_rejected(self):
        (self.root.path/'PAYLOAD').mkdir()
        self.assertEqual(i.apply(plan(),self.root).code,'INSTALLATION_PATH_CONFLICT')

    def test_reinstall_idempotent(self):
        p,receipt=self.install();again=replace(p,current=receipt.result)
        result=i.apply(again,self.root)
        self.assertEqual(result.status,'IDEMPOTENT')
        self.assertEqual(result.receipt.result.fingerprint(),receipt.result.fingerprint())

    def test_stale_plan_and_unknown_current_bytes(self):
        p,receipt=self.install();again=replace(p,current=receipt.result)
        path=self.root.path/p.files[0].path.value;path.write_bytes(b'changed')
        result=i.apply(again,self.root)
        self.assertEqual(result.code,'INSTALLATION_STALE_STATE')
        self.assertEqual(path.read_bytes(),b'changed')

    def test_upgrade_requires_policy_even_newer_version(self):
        p,receipt=self.install()
        self.error('UPGRADE_POLICY_BINDING_INVALID',lambda:plan(manifest('9.0.0'),receipt.result))

    def test_unknown_incompatible_and_migration_not_executable(self):
        p,receipt=self.install();target=manifest('2.0.0',surface_version='0.2.0')
        for status,expected in (('UNKNOWN','INCOMPLETE'),('INCOMPATIBLE','UNSUPPORTED'),('MIGRATION_REQUIRED','MIGRATION_REQUIRED')):
            up=plan(target,receipt.result,assessment=assessment(p.identity.manifest,target,status))
            self.assertFalse(up.executable)
            result=i.apply(up,self.root)
            self.assertEqual(result.code,'UPGRADE_'+expected)
            self.assertEqual((self.root.path/p.files[0].path.value).read_bytes(),b'first')
            if status=='MIGRATION_REQUIRED':self.assertIsNotNone(up.assessment.policy.declarations[0].migration)

    def test_exact_upgrade_policy_and_surface_versions(self):
        p,receipt=self.install();target=manifest('2.0.0',surface_version='0.2.0')
        policy=assessment(p.identity.manifest,target)
        other=assessment(manifest('7.0.0'),target)
        self.error('UPGRADE_POLICY_BINDING_INVALID',lambda:plan(target,receipt.result,assessment=other))
        wrong=assessment(manifest(surface_version='0.9.0'),target)
        self.error('UPGRADE_VERSION_BINDING_INVALID',lambda:plan(target,receipt.result,assessment=wrong))
        up=plan(target,receipt.result,assessment=policy)
        self.assertEqual(up.current.fingerprint(),receipt.result.fingerprint())

    def test_upgrade_and_exact_rollback_anchor(self):
        first,old,upgrade,new=self.upgrade()
        rollback=i.RollbackPlan(new.result,new)
        result=i.apply(rollback,self.root)
        self.assertEqual(result.status,'APPLIED')
        self.assertEqual(result.receipt.result.fingerprint(),old.result.fingerprint())
        self.assertEqual((self.root.path/first.files[0].path.value).read_bytes(),b'first')
        self.assertFalse((self.root.path/'payload/b.vsix').exists())

    def test_clean_install_rollback_removes_only_own_files(self):
        p,receipt=self.install();(self.root.path/'unrelated').write_bytes(b'keep')
        result=i.apply(i.RollbackPlan(receipt.result,receipt),self.root)
        self.assertEqual(result.receipt.result,receipt.previous)
        self.assertFalse((self.root.path/p.files[0].path.value).exists())
        self.assertEqual((self.root.path/'unrelated').read_bytes(),b'keep')

    def test_rollback_not_arbitrary_older_state(self):
        p,receipt=self.install()
        self.error('ROLLBACK_ANCHOR_INVALID',lambda:i.RollbackPlan(receipt.previous,receipt))
        reinstall=i.apply(replace(p,current=receipt.result),self.root).receipt
        self.error('ROLLBACK_ANCHOR_INVALID',lambda:i.RollbackPlan(reinstall.result,reinstall))

    def test_unrelated_file_survives_upgrade_and_rollback(self):
        (self.root.path/'caller-note').write_bytes(b'preserve')
        first,old,upgrade,new=self.upgrade()
        i.apply(i.RollbackPlan(new.result,new),self.root)
        self.assertEqual((self.root.path/'caller-note').read_bytes(),b'preserve')

    def test_failure_before_staging(self):
        with patch.object(i,'observe',side_effect=i.InstallationError('INJECTED_PRECONDITION')):
            result=i.apply(plan(),self.root)
        self.assertEqual(result.status,'REJECTED')
        self.assertEqual(tuple(self.root.path.iterdir()),())

    def test_staging_failure_preserves_state(self):
        with patch.object(Path,'write_bytes',side_effect=OSError('injected staging')):
            result=i.apply(plan(),self.root)
        self.assertEqual(result.status,'FAILED_RECOVERED')
        self.assertEqual(tuple(self.root.path.iterdir()),())

    def test_staged_byte_corruption_never_committed(self):
        write = Path.write_bytes
        def corrupt(path, data):
            return write(path, b'corrupt' if path.name.startswith('new') else data)
        with patch.object(Path, 'write_bytes', corrupt):result=i.apply(plan(),self.root)
        self.assertEqual(result.code,'INSTALLATION_STAGING_MISMATCH')
        self.assertEqual(result.status,'FAILED_RECOVERED')
        self.assertEqual(tuple(self.root.path.iterdir()),())

    def test_stale_between_staging_and_commit(self):
        p,receipt=self.install();target=manifest('2.0.0',surface_version='0.2.0')
        up=plan(target,receipt.result,assessment=assessment(p.identity.manifest,target));observe=i.observe;calls=[]
        def changed(root,state,paths):
            calls.append(1)
            if len(calls)==2:(root.path/p.files[0].path.value).write_bytes(b'concurrent')
            return observe(root,state,paths)
        with patch.object(i,'observe',side_effect=changed):result=i.apply(up,self.root)
        self.assertEqual(result.code,'INSTALLATION_STALE_STATE')
        self.assertEqual((self.root.path/p.files[0].path.value).read_bytes(),b'concurrent')

    def test_commit_failure_restores_prior_state(self):
        p,receipt=self.install();target=manifest('2.0.0',(('a',b'second'),),surface_version='0.2.0')
        up=plan(target,receipt.result,assessment=assessment(p.identity.manifest,target));replace_os=os.replace;calls=[]
        def failed(source,target):
            calls.append(1)
            if len(calls)==1:raise OSError('commit')
            return replace_os(source,target)
        with patch.object(i.os,'replace',side_effect=failed):result=i.apply(up,self.root)
        self.assertEqual(result.status,'FAILED_RECOVERED')
        self.assertEqual((self.root.path/p.files[0].path.value).read_bytes(),b'first')

    def test_partial_move_then_failure_recovers(self):
        p=plan(manifest(files=(('a',b'a'),('b',b'b'))));replace_os=os.replace;calls=[]
        def failed(source,target):
            calls.append(1);replace_os(source,target)
            if len(calls)==1:raise OSError('after partial move')
        with patch.object(i.os,'replace',side_effect=failed):result=i.apply(p,self.root)
        self.assertEqual(result.status,'FAILED_RECOVERED')
        self.assertEqual(tuple(self.root.path.iterdir()),())

    def test_post_commit_verification_failure_recovers(self):
        observe=i.observe;calls=[]
        def failed(root,state,paths):
            calls.append(1)
            if len(calls)==3:raise i.InstallationError('INJECTED_VERIFY_MISMATCH')
            return observe(root,state,paths)
        with patch.object(i,'observe',side_effect=failed):result=i.apply(plan(),self.root)
        self.assertEqual(result.status,'FAILED_RECOVERED');self.assertIsNone(result.receipt)
        self.assertEqual(tuple(self.root.path.iterdir()),())

    def test_rollback_failure_explicit_and_current_restored(self):
        first,old,up,new=self.upgrade();replace_os=os.replace;calls=[]
        def failed(source,target):
            calls.append(1)
            if len(calls)==1:raise OSError('rollback commit')
            return replace_os(source,target)
        with patch.object(i.os,'replace',side_effect=failed):result=i.apply(i.RollbackPlan(new.result,new),self.root)
        self.assertEqual(result.status,'FAILED_RECOVERED');self.assertIsNone(result.receipt)
        self.assertEqual((self.root.path/'payload/a.vsix').read_bytes(),b'second')

    def test_recovery_failure_not_masked(self):
        p,old=self.install();target=manifest('2.0.0',(('a',b'second'),),surface_version='0.2.0')
        up=plan(target,old.result,assessment=assessment(p.identity.manifest,target))
        with patch.object(i.os,'replace',side_effect=OSError('commit and recovery unavailable')):result=i.apply(up,self.root)
        self.assertEqual(result.status,'RECOVERY_FAILED');self.assertIsNone(result.receipt)
        self.assertTrue(Path(result.recovery_root).is_dir())
        self.assertEqual(i.apply(up,self.root).code,'INSTALLATION_RECOVERY_REQUIRED')

    def test_unrecorded_current_state_rejected_even_matching_bytes(self):
        p=plan();state=p.resulting_state()
        path=self.root.path/p.files[0].path.value;path.parent.mkdir();path.write_bytes(p.files[0].artifact.data)
        receipt=i.InstallationReceipt(p,p.current,state)
        self.assertEqual(i.apply(i.RollbackPlan(state,receipt),self.root).code,'INSTALLATION_STALE_STATE')

    def test_inactive_and_forged_roots_rejected(self):
        self.error('INSTALLATION_ISOLATION_REQUIRED',lambda:i.IsolatedRoot())
        self.error('INSTALLATION_ISOLATION_REQUIRED',lambda:i.root_guard(object.__new__(i.IsolatedRoot)))
        with self.assertRaises(i.InstallationError):
            with i.isolated_root(Path(self.temp.name),test_controlled=False):pass

    def test_reparse_guard_and_destination_escape(self):
        original=Path.lstat;target=self.root.path/'payload';target.mkdir()
        class Reparse:
            st_mode=0o040755;st_file_attributes=0x400
        def attrs(path,*args,**kwargs):return Reparse() if path==target else original(path,*args,**kwargs)
        with patch.object(Path,'lstat',attrs):result=i.apply(plan(),self.root)
        self.assertEqual(result.code,'INSTALLATION_DESTINATION_ESCAPE')

    def test_symlink_escape_when_supported(self):
        with tempfile.TemporaryDirectory(prefix='apexforge-install-test-outside-') as other:
            try:(self.root.path/'payload').symlink_to(other,target_is_directory=True)
            except OSError as exc:self.skipTest('host does not permit symlink creation: '+str(exc.errno))
            result=i.apply(plan(),self.root)
            self.assertEqual(result.code,'INSTALLATION_DESTINATION_ESCAPE')
            self.assertEqual(tuple(Path(other).iterdir()),())

    def test_transaction_lock_prevents_concurrent_apply(self):
        lock=self.root.path/'.apexforge-transaction-lock';lock.write_bytes(b'other transaction')
        self.assertEqual(i.apply(plan(),self.root).code,'INSTALLATION_BUSY')
        self.assertEqual(lock.read_bytes(),b'other transaction')

    def test_deterministic_across_physical_roots(self):
        p=plan();a=i.apply(p,self.root).receipt
        with tempfile.TemporaryDirectory(prefix='apexforge-install-test-') as parent:
            with i.isolated_root(Path(parent),test_controlled=True) as root:c=i.apply(plan(),root).receipt
        self.assertEqual(a.fingerprint(),c.fingerprint());self.assertEqual(a.result.fingerprint(),c.result.fingerprint())
        self.assertNotIn(self.temp.name,p.canonical_json())

    def test_size_count_and_directory_bounds(self):
        p=plan();self.error('INSTALLATION_FILES_INVALID',lambda:replace(p,files=p.files*(i.MAX_FILES+1)))
        with patch.object(i,'MAX_CHILDREN',0):result=i.apply(plan(),self.root)
        self.assertEqual(result.code,'INSTALLATION_DIRECTORY_SIZE_LIMIT')
        with patch.object(i,'MAX_TRANSACTIONS',0):result=i.apply(plan(),self.root)
        self.assertEqual(result.code,'INSTALLATION_HISTORY_SIZE_LIMIT')

    def test_all_target_categories_remain_projection_only(self):
        for surface in r.TARGETS:
            man=manifest(surface=surface,surface_version='profile-v1' if surface=='native-win-x64' else '0.1.0')
            p=plan(man);self.assertEqual(p.identity.target.record()['surface'],surface)

    def test_trust_authority_approval_not_granted(self):
        p,receipt=self.install();record=receipt.record()
        for field in ('trusted','authority','release_approved','authenticated'):self.assertFalse(record[field])
        self.assertEqual(record['crypto'],'CRYPTO_PROVIDER_UNAVAILABLE')

    def test_static_security_audit(self):
        source=(ROOT/'apexforge/tooling/release_installation.py').read_text();tree=ast.parse(source)
        imports={a.name for node in ast.walk(tree) if isinstance(node,ast.Import) for a in node.names}
        self.assertFalse(imports & {'subprocess','socket','requests','urllib','winreg','ctypes','pickle'})
        calls={node.func.attr if isinstance(node.func,ast.Attribute) else node.func.id for node in ast.walk(tree) if isinstance(node,ast.Call) and isinstance(node.func,(ast.Name,ast.Attribute))}
        self.assertFalse(calls & {'rglob','walk','rmtree','system','Popen','run','eval','exec','execute_native','install_vscode_extension','audit_visualstudio_installed_copy'})
        self.assertNotIn('site-packages',source);self.assertNotIn('ProgramFiles',source)


if __name__=='__main__':unittest.main(verbosity=2)
