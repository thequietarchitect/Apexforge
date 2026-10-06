"""P16.13 passive phase-closure evidence; source-control operations are external."""
from dataclasses import dataclass
from tooling import release_acceptance as a, release_architecture as r, release_pipeline as p, release_manifest as m
from tooling.domain_platform import CanonicalModel
from tooling.package_manifest import PackagePath

TAG = 'afp-p16.13-freeze'
SLICES = (
 ('release_architecture','p16_1_release_architecture_contract_test','P16_1_RELEASE_ARCHITECTURE'),
 ('release_versioning','p16_2_release_versioning_compatibility_test','P16_2_VERSION_COMPATIBILITY_UPGRADE_POLICY'),
 ('release_build','p16_3_reproducible_release_build_test','P16_3_REPRODUCIBLE_RELEASE_BUILD'),
 ('release_manifest','p16_4_release_manifest_provenance_test','P16_4_RELEASE_MANIFEST_PROVENANCE'),
 ('python_distribution','p16_5_python_distribution_packaging_test','P16_5_PYTHON_DISTRIBUTION_PACKAGING'),
 ('vscode_distribution','p16_6_vscode_distribution_packaging_test','P16_6_VSCODE_DISTRIBUTION_PACKAGING'),
 ('visualstudio_distribution','p16_7_visualstudio_distribution_packaging_test','P16_7_VISUAL_STUDIO_DISTRIBUTION_PACKAGING'),
 ('native_distribution','p16_8_native_distribution_packaging_test','P16_8_NATIVE_WIN_X64_DISTRIBUTION_PACKAGING'),
 ('release_installation','p16_9_install_upgrade_rollback_test','P16_9_INSTALL_UPGRADE_ROLLBACK'),
 ('release_pipeline','p16_10_ci_release_pipeline_dry_run_test','P16_10_CI_RELEASE_PIPELINE_DRY_RUN'),
 ('release_security','p16_11_release_security_signing_verification_test','P16_11_RELEASE_SECURITY_SIGNING_VERIFICATION'),
 ('release_acceptance','p16_12_release_candidate_acceptance_test','P16_12_RELEASE_CANDIDATE_ACCEPTANCE'),
 ('release_closure','p16_13_release_closure_freeze_test','P16_13_RELEASE_CLOSURE_FREEZE'),
)
FREEZE_PATHS = tuple(sorted(path for module,test,doc in SLICES for path in
                   ('apexforge/tooling/'+module+'.py','apexforge/'+test+'.py','docs/p16/'+doc+'.md')))
INCOMING_PATHS = tuple(path for path in FREEZE_PATHS if path not in
    ('apexforge/tooling/release_closure.py','apexforge/p16_13_release_closure_freeze_test.py','docs/p16/P16_13_RELEASE_CLOSURE_FREEZE.md'))


class ReleaseClosureError(ValueError):
    def __init__(self,code):
        self.code=code
        super().__init__(code)


def require(ok,code):
    if not ok:raise ReleaseClosureError(code)


@dataclass(frozen=True)
class ClosureSourceFile(CanonicalModel):
    path: str
    sha256: str
    DOMAIN = 'apexforge.release-closure-source-file/v1'

    def __post_init__(self):
        require(type(self.path) is str and self.path in INCOMING_PATHS,'CLOSURE_SOURCE_PATH_INVALID')
        PackagePath(self.path);m.hex_digest(self.sha256)

    def record(self):
        return {'path':self.path,'sha256':self.sha256,'evidence':'SUPPLIED_WORKTREE_BYTES_NOT_AUTHENTICATION'}


@dataclass(frozen=True)
class ReleaseClosureRecord(CanonicalModel):
    verdict: a.ReleaseCandidateVerdict
    sources: tuple
    regressions: tuple
    predecessor: r.FrozenSourceBaseline = r.P15_BASELINE
    blockers: tuple | None = None
    tag: str = TAG
    schema: str = 'apexforge.release-closure/v1'
    DOMAIN = 'apexforge.release-closure/v1'

    def __post_init__(self):
        require(type(self.verdict) is a.ReleaseCandidateVerdict and type(self.predecessor) is r.FrozenSourceBaseline,
                'CLOSURE_MODEL_INVALID')
        require(type(self.tag) is str and self.tag==TAG and type(self.schema) is str and self.schema==self.DOMAIN,'CLOSURE_SCHEMA_INVALID')
        require(type(self.sources) is tuple and len(self.sources)==36 and all(type(x) is ClosureSourceFile for x in self.sources),
                'CLOSURE_SOURCE_INVENTORY_INVALID')
        require({x.path for x in self.sources}==set(INCOMING_PATHS),'CLOSURE_SOURCE_INVENTORY_INVALID')
        object.__setattr__(self,'sources',tuple(sorted(self.sources,key=lambda x:x.path)))
        require(type(self.regressions) is tuple and len(self.regressions)==5 and all(type(x) is p.RegressionEvidence for x in self.regressions)
                and {x.suite for x in self.regressions}==set(p.SUITES)
                and all(x.release==self.release for x in self.regressions),'CLOSURE_REGRESSION_BINDING_INVALID')
        object.__setattr__(self,'regressions',tuple(sorted(self.regressions,key=lambda x:x.suite)))
        exact=tuple(sorted(self.verdict.record()['blocker_codes']))
        require(self.blockers is None or type(self.blockers) is tuple and self.blockers==exact,'CLOSURE_BLOCKER_SUPPRESSION_REJECTED')
        object.__setattr__(self,'blockers',exact)

    @property
    def release(self):
        return self.verdict.matrix.candidate.evidence.release

    @property
    def implementation_complete(self):
        frozen_counts={'P15':(428,0,0,428),'P14':(330,0,0,330),'NATIVE':(7,0,0,7),'AUTHORITY':(1,0,0,1)}
        for regression in self.regressions:
            counts=(regression.passed,regression.skipped,regression.failed,regression.discovered)
            if regression.suite in frozen_counts and counts!=frozen_counts[regression.suite]:return False
            if regression.suite=='P16' and (regression.failed or regression.skipped!=1 or regression.passed<410):return False
        evidence=self.verdict.matrix.candidate.evidence
        return (self.predecessor==r.P15_BASELINE and self.release.baseline==r.P15_BASELINE and
                {x.slice for x in evidence.reviews}==set(range(1,12)))

    @property
    def ready_for_freeze(self):
        return self.implementation_complete and self.verdict.status=='BLOCKED' and not self.verdict.record()['grants_release_approval']

    def record(self):
        evidence=self.verdict.matrix.candidate.evidence
        facts=evidence.pipeline.record()
        return {'schema':self.schema,'release':self.release.fingerprint(),'predecessor':self.predecessor.record(),
                'sources':[x.record() for x in self.sources],
                'contracts':[{'slice':index+1,'files':[x.record() for x in self.sources if x.path in
                    ('apexforge/tooling/'+module+'.py','apexforge/'+test+'.py','docs/p16/'+doc+'.md')]}
                    for index,(module,test,doc) in enumerate(SLICES[:12])],
                'snapshot':evidence.fingerprint(),'acceptance':self.verdict.fingerprint(),'acceptance_state':self.verdict.record(),
                'pipeline':evidence.pipeline.fingerprint(),'pipeline_release_ready':facts['release_ready'],
                'publication_targets':[(x.target.surface,x.record()['state']) for x in p.publication_dry_run(evidence.pipeline)],
                'regressions':[x.record() for x in self.regressions],
                'limitation_history':[x.record() for x in evidence.pipeline.evidence],
                'security':None if evidence.security is None else evidence.security.fingerprint(),
                'blockers':self.blockers,'implementation_complete':self.implementation_complete,
                'ready_for_phase_freeze':self.ready_for_freeze,'phase_freeze_tag':self.tag,
                'freeze_inventory':FREEZE_PATHS,'freeze_path_count':39,'phase_tag_is_product_release':False,
                'candidate_accepted':self.verdict.status=='ACCEPTED','product_ready':facts['release_ready'],
                'product_published':False,'production_signed':False,
                'trust':'NOT_EVALUATED','crypto':'CRYPTO_PROVIDER_UNAVAILABLE','waivers_added':False,
                'grants_authority':False,'product_installation_performed':False,'product_signing_performed':False,
                'source_control_operation':'EXTERNAL_CLOSURE_PROCEDURE_ONLY','semantic_authority':'CANONICAL_AIR'}
