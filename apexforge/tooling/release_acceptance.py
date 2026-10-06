"""P16.12 exact evidence acceptance; no waiver, execution, publication or freeze."""
from dataclasses import dataclass
from hashlib import sha256
from tooling import release_architecture as r, release_build as b, release_manifest as m, release_versioning as v
from tooling import release_pipeline as p, release_security as s
from tooling.release_installation import InstallationReceipt
from tooling.package_manifest import CanonicalReference
from tooling.domain_platform import CanonicalModel, _json

POLICY_SCHEMA = 'apexforge.release-acceptance-policy/v1'
MAX_CRITERIA, MAX_MODELS, MAX_REFERENCES = 128, 64, 512
CATEGORIES = ('BASELINE','REGRESSION','ARTIFACT','REPRODUCIBILITY','COMPATIBILITY','INSTALLATION','ROLLBACK','SECURITY','SIGNING','PUBLICATION_READINESS')
STATES = ('PASS','FAIL','BLOCKED','DEFERRED','INCOMPLETE','SKIPPED','NOT_APPLICABLE')
SOURCES = ('BASELINE','REGRESSION','CONTRACT_REVIEW','ARTIFACT','OWNER_BUILD','SOURCE_CONTINUITY','CONTENT_REPRODUCIBILITY',
           'RAW_REPRODUCIBILITY','MANIFEST','COMPATIBILITY','INSTALLATION','INSTALLATION_HOST','SECURITY_ARCHITECTURE',
           'PRODUCTION_SIGNING','PUBLICATION','PIPELINE_READY','SURFACE_COVERAGE','NATIVE_PROFILE')
FORMATS = {'python':('wheel','sdist'),'vscode':('vsix',),'visual-studio':('vsix',),'native-win-x64':('exe',)}


class ReleaseAcceptanceError(ValueError):
    def __init__(self,code):
        self.code=code
        super().__init__(code)


def require(ok,code):
    if not ok:raise ReleaseAcceptanceError(code)


def reference(value):
    return CanonicalReference(value.DOMAIN,'provenance-scope',value.fingerprint())


@dataclass(frozen=True)
class ContractReview(CanonicalModel):
    slice: int
    regression: p.RegressionEvidence
    DOMAIN = 'apexforge.release-contract-review/v1'

    def __post_init__(self):
        require(type(self.slice) is int and 1 <= self.slice <= 11 and type(self.regression) is p.RegressionEvidence
                and self.regression.suite == 'P16','ACCEPTANCE_REVIEW_INVALID')

    def record(self):
        return {'slice':self.slice,'regression':self.regression.record(),'evidence_class':'SUPPLIED_REVIEW_NOT_AUTHENTICATION'}


def canonical_models(values,cls):
    require(type(values) is tuple and len(values) <= MAX_MODELS and all(type(x) is cls for x in values),'ACCEPTANCE_MODELS_INVALID')
    keys=[x.fingerprint() for x in values]
    require(len(set(keys)) == len(keys),'ACCEPTANCE_EVIDENCE_CONFLICT')
    return tuple(x for _,x in sorted(zip(keys,values),key=lambda pair:pair[0]))


@dataclass(frozen=True)
class ReleaseCandidateEvidence(CanonicalModel):
    pipeline: p.ReleasePipelineResult
    reviews: tuple = ()
    security: s.ReleaseSignatureBundle | None = None
    manifests: tuple = ()
    compatibility: tuple = ()
    builds: tuple = ()
    receipts: tuple = ()
    DOMAIN = 'apexforge.release-candidate-evidence/v1'

    def __post_init__(self):
        require(type(self.pipeline) is p.ReleasePipelineResult and self.release.baseline == r.P15_BASELINE,'ACCEPTANCE_BASELINE_MISMATCH')
        reviews=canonical_models(self.reviews,ContractReview)
        require(len({x.slice for x in reviews}) == len(reviews) and all(x.regression.release == self.release for x in reviews),
                'ACCEPTANCE_REVIEW_CONFLICT')
        object.__setattr__(self,'reviews',tuple(sorted(reviews,key=lambda x:x.slice)))
        table={(e.kind,e.subject):e for e in self.pipeline.evidence}
        descriptors={d.identity.identifier:d for d in self.pipeline.pipeline.architecture.artifacts}
        for name,cls in (('manifests',m.ReleaseManifest),('compatibility',v.ReleaseUpgradeAssessment),
                         ('builds',b.ReleaseBuildArtifact),('receipts',InstallationReceipt)):
            object.__setattr__(self,name,canonical_models(getattr(self,name),cls))
        for artifact in self.builds:
            gate=table.get(('ARTIFACT',artifact.identity.identifier))
            require(artifact.recipe.release == self.release and descriptors.get(artifact.identity.identifier) == artifact._slot.descriptor
                    and gate is not None and m.reference(artifact) in gate.references,'ACCEPTANCE_BUILD_BINDING_MISMATCH')
        for manifest in self.manifests:
            require(manifest.architecture.release == self.release,'ACCEPTANCE_RELEASE_MISMATCH')
            surface=manifest.architecture.artifacts[0].target.identifier
            gate=table.get(('MANIFEST',surface))
            expected=p.manifest_gate(manifest,surface)
            require(gate is not None and gate.status == expected.status and set(expected.references) <= set(gate.references),
                    'ACCEPTANCE_MANIFEST_BINDING_MISMATCH')
        for assessment in self.compatibility:
            require(assessment.policy.target == self.release,'ACCEPTANCE_RELEASE_MISMATCH')
            surfaces={f.target.identifier for f in assessment.policy.surfaces}
            require(len(surfaces)==1,'ACCEPTANCE_COMPATIBILITY_SCOPE_INVALID')
            surface=next(iter(surfaces));gate=table.get(('COMPATIBILITY',surface))
            expected=p.compatibility_gate(assessment,surface)
            require(gate is not None and gate.status == expected.status and set(expected.references) <= set(gate.references),
                    'ACCEPTANCE_COMPATIBILITY_BINDING_MISMATCH')
        for receipt in self.receipts:
            releases={x.identity.release for x in (receipt.previous,receipt.result) if x.identity is not None}
            gate=table.get(('INSTALLATION','release'))
            ref=CanonicalReference(receipt.DOMAIN,'artifact',receipt.fingerprint())
            require(self.release in releases and gate is not None and ref in gate.references,'ACCEPTANCE_RECEIPT_BINDING_MISMATCH')
        if self.security is not None:
            require(type(self.security) is s.ReleaseSignatureBundle and self.security.policy.release == self.release,'ACCEPTANCE_SECURITY_BINDING_MISMATCH')
            gate=table.get(('SIGNING','release'));expected=s.signing_gate(self.security)
            require(gate is not None and gate.status == expected.status and set(expected.references) <= set(gate.references),
                    'ACCEPTANCE_SECURITY_BINDING_MISMATCH')
            for subject in self.security.policy.required_subjects:
                if subject.kind == 'RELEASE_ARTIFACT':
                    artifact=subject.owner;bound=table.get(('ARTIFACT',artifact.identity.identifier))
                    require(descriptors.get(artifact.identity.identifier) == artifact._slot.descriptor and bound is not None
                            and m.reference(artifact) in bound.references,'ACCEPTANCE_SIGNED_ARTIFACT_UNBOUND')
                else:
                    require(any(m.reference(subject.owner) == m.reference(man) for man in self.manifests),
                            'ACCEPTANCE_SIGNED_MANIFEST_UNBOUND')
        require(sum(len(e.references) for e in self.pipeline.evidence)+len(self.reviews)+sum(len(getattr(self,n)) for n in
                ('manifests','compatibility','builds','receipts'))*4 <= MAX_REFERENCES,'ACCEPTANCE_REFERENCE_SIZE_LIMIT')

    @property
    def release(self):
        return self.pipeline.pipeline.release

    def record(self):
        return {'release':self.release.fingerprint(),'architecture':self.pipeline.pipeline.architecture.fingerprint(),
                'pipeline':self.pipeline.fingerprint(),'regressions':[x.fingerprint() for x in self.pipeline.regressions],
                'reviews':[x.record() for x in self.reviews],
                'packaging_build_manifest_policy_installation_references':[e.record() for e in self.pipeline.evidence],
                'security':None if self.security is None else self.security.fingerprint(),
                'manifests':[{'manifest':x.fingerprint(),'checksums':None if x.checksums is None else x.checksums.fingerprint(),
                             'provenance':None if x.provenance is None else x.provenance.fingerprint()} for x in self.manifests],
                'compatibility':[x.fingerprint() for x in self.compatibility],'builds':[x.fingerprint() for x in self.builds],
                'receipts':[x.fingerprint() for x in self.receipts],'authenticated':False}


@dataclass(frozen=True)
class AcceptanceCriterion(CanonicalModel):
    identifier: str
    category: str
    scope: str
    source: str
    subject: str
    level: str = 'REQUIRED'
    DOMAIN = 'apexforge.release-acceptance-criterion/v1'

    def __post_init__(self):
        r.text(self.identifier,'ACCEPTANCE_CRITERION_ID_INVALID');r.text(self.subject,'ACCEPTANCE_CRITERION_SUBJECT_INVALID')
        require(type(self.category) is str and self.category in CATEGORIES and type(self.scope) is str and self.scope in ('global',)+r.TARGETS
                and type(self.source) is str and self.source in SOURCES and type(self.level) is str and self.level in ('REQUIRED','INFORMATIONAL'),
                'ACCEPTANCE_CRITERION_INVALID')

    def record(self):
        return {'id':self.identifier,'category':self.category,'scope':self.scope,'source':self.source,'subject':self.subject,'level':self.level}


def required_criteria(evidence):
    require(type(evidence) is ReleaseCandidateEvidence,'ACCEPTANCE_EVIDENCE_INVALID')
    rows=[]
    def add(name,category,source,subject='release',scope='global'):
        rows.append(AcceptanceCriterion(name,category,scope,source,subject))
    add('baseline','BASELINE','BASELINE')
    for suite in p.SUITES:add('regression-'+suite,'REGRESSION','REGRESSION',suite)
    for number in range(1,12):add('contract-P16-'+str(number),'REGRESSION','CONTRACT_REVIEW',str(number))
    for d in evidence.pipeline.pipeline.architecture.artifacts:
        for source in ('ARTIFACT','OWNER_BUILD','SOURCE_CONTINUITY','CONTENT_REPRODUCIBILITY','RAW_REPRODUCIBILITY'):
            category='REPRODUCIBILITY' if 'REPRODUCIBILITY' in source else 'ARTIFACT'
            add(source.lower().replace('_','-')+'-'+d.identity.identifier,category,source,d.identity.identifier,d.target.identifier)
    for surface in r.TARGETS:
        for source,category in (('SURFACE_COVERAGE','ARTIFACT'),('MANIFEST','ARTIFACT'),('COMPATIBILITY','COMPATIBILITY'),('PUBLICATION','PUBLICATION_READINESS')):
            add(source.lower().replace('_','-')+'-'+surface,category,source,surface,surface)
    add('native-profile','ARTIFACT','NATIVE_PROFILE','native-win-x64','native-win-x64')
    add('installation-contract','INSTALLATION','INSTALLATION')
    add('installation-host-coverage','INSTALLATION','INSTALLATION_HOST')
    add('rollback-contract','ROLLBACK','INSTALLATION')
    add('security-architecture','SECURITY','SECURITY_ARCHITECTURE')
    add('production-signing','SIGNING','PRODUCTION_SIGNING')
    add('pipeline-readiness','PUBLICATION_READINESS','PIPELINE_READY')
    require(len(rows)<=MAX_CRITERIA,'ACCEPTANCE_CRITERIA_SIZE_LIMIT')
    return tuple(sorted(rows,key=lambda x:x.identifier))


@dataclass(frozen=True)
class ReleaseCandidateIdentity(CanonicalModel):
    identifier: str
    evidence: ReleaseCandidateEvidence
    schema: str = POLICY_SCHEMA
    DOMAIN = 'apexforge.release-candidate-identity/v1'

    def __post_init__(self):
        r.text(self.identifier,'ACCEPTANCE_CANDIDATE_ID_INVALID')
        require(type(self.evidence) is ReleaseCandidateEvidence and type(self.schema) is str and self.schema==POLICY_SCHEMA,'ACCEPTANCE_CANDIDATE_INVALID')

    def record(self):
        criteria=required_criteria(self.evidence)
        policy=sha256(_json({'schema':self.schema,'criteria':[c.record() for c in criteria]}).encode()).hexdigest().upper()
        return {'id':self.identifier,'release':self.evidence.release.fingerprint(),'baseline':self.evidence.release.baseline.record(),
                'snapshot':self.evidence.fingerprint(),'policy':policy,'policy_schema':self.schema,'waivers':'NOT_SUPPORTED'}


@dataclass(frozen=True)
class CriterionResult(CanonicalModel):
    criterion: AcceptanceCriterion
    status: str
    references: tuple = ()
    reasons: tuple = ()
    DOMAIN = 'apexforge.release-acceptance-criterion-result/v1'

    def __post_init__(self):
        require(type(self.criterion) is AcceptanceCriterion and type(self.status) is str and self.status in STATES,'ACCEPTANCE_STATUS_INVALID')
        require(type(self.references) is tuple and len(self.references)<=MAX_REFERENCES and all(type(x) is CanonicalReference for x in self.references),
                'ACCEPTANCE_REFERENCES_INVALID')
        require(self.status!='PASS' or bool(self.references),'ACCEPTANCE_PASS_EVIDENCE_MISSING')
        require(type(self.reasons) is tuple and len(self.reasons)<=32 and all(type(x) is str for x in self.reasons),'ACCEPTANCE_DIAGNOSTICS_INVALID')
        for code in self.reasons:r.text(code,'ACCEPTANCE_DIAGNOSTICS_INVALID')
        object.__setattr__(self,'references',tuple(sorted(set(self.references),key=m.ref_key)))
        object.__setattr__(self,'reasons',tuple(sorted(set(self.reasons))))

    @property
    def satisfies_required(self):
        return self.criterion.level=='REQUIRED' and self.status=='PASS'

    def record(self):
        return {'criterion':self.criterion.record(),'status':self.status,'references':[x.record() for x in self.references],
                'reasons':self.reasons,'satisfies_required':self.satisfies_required}


def evaluate_criterion(criterion,evidence):
    source,subject=criterion.source,criterion.subject
    pipeline=evidence.pipeline
    refs=()
    reasons=()
    if source=='SURFACE_COVERAGE':
        formats={d.format for d in pipeline.pipeline.architecture.artifacts if d.target.identifier==subject}
        status='PASS' if set(FORMATS[subject]) <= formats else 'INCOMPLETE'
        reasons=() if status=='PASS' else ('ACCEPTANCE_REQUIRED_FORMAT_MISSING',)
        refs=(m.reference(pipeline.pipeline.architecture),)
    elif source=='CONTRACT_REVIEW' or source=='SECURITY_ARCHITECTURE':
        number=11 if source=='SECURITY_ARCHITECTURE' else int(subject)
        review=next((x for x in evidence.reviews if x.slice==number),None)
        status='INCOMPLETE' if review is None else review.regression.status
        refs=() if review is None else (reference(review),review.regression.reference)
        if status=='SKIPPED':reasons=('ACCEPTANCE_SKIPPED_REQUIRED_REVIEW',)
    elif source=='REGRESSION':
        regression=next((x for x in pipeline.regressions if x.suite==subject),None)
        status='INCOMPLETE' if regression is None else regression.status
        refs=() if regression is None else (reference(regression),regression.reference)
        if status=='SKIPPED':reasons=('ACCEPTANCE_SKIPPED_REQUIRED_TEST',)
    elif source=='PRODUCTION_SIGNING':
        status='BLOCKED';reasons=('CRYPTO_PROVIDER_UNAVAILABLE','ACCEPTANCE_PRODUCTION_SIGNATURE_UNAVAILABLE')
        if evidence.security is not None:
            refs=(reference(evidence.security),)
            if evidence.security.status=='REJECTED':status='FAIL'
            elif evidence.security.status=='INCOMPLETE':
                status='INCOMPLETE';reasons=('ACCEPTANCE_REQUIRED_SIGNATURE_MISSING',)
            else:
                security=evidence.security.record()
                if all(security.get(key) is True for key in ('production_signed','cryptographically_verified','trusted')):
                    status='PASS';reasons=()
        else:refs=()
        signing=next((x for x in pipeline.evaluate() if x['id']=='signing'),None)
        if signing is not None and signing['status']=='FAIL':status='FAIL'
    elif source=='PUBLICATION':
        refs=(reference(pipeline),)
        gate=next((x for x in pipeline.evaluate() if x['id']=='publication-'+subject),None)
        status='INCOMPLETE' if gate is None else gate['status']
        reasons=('ACCEPTANCE_PIPELINE_PUBLICATION_NOT_READY',) if status!='PASS' else ()
    elif source=='PIPELINE_READY':
        refs=(reference(pipeline),)
        status='PASS' if pipeline.record()['release_ready'] else 'BLOCKED'
        reasons=() if status=='PASS' else ('ACCEPTANCE_PIPELINE_NOT_READY',)
    else:
        value=next((x for x in pipeline.evidence if (x.kind,x.subject)==(source,subject)),None)
        status='INCOMPLETE' if value is None else value.status
        refs=() if value is None else (reference(value),)+value.references
        reasons=() if value is None else value.reasons
    if status=='PENDING':status='INCOMPLETE';reasons=reasons+('ACCEPTANCE_PENDING_REQUIRED_EVIDENCE',)
    if status=='INCOMPLETE' and not reasons:reasons=('ACCEPTANCE_REQUIRED_EVIDENCE_MISSING',)
    return CriterionResult(criterion,status,refs,reasons)


@dataclass(frozen=True)
class ReleaseAcceptanceMatrix(CanonicalModel):
    candidate: ReleaseCandidateIdentity
    criteria: tuple
    DOMAIN = 'apexforge.release-acceptance-matrix/v1'

    def __post_init__(self):
        require(type(self.candidate) is ReleaseCandidateIdentity and type(self.criteria) is tuple and len(self.criteria)<=MAX_CRITERIA
                and all(type(x) is AcceptanceCriterion for x in self.criteria),'ACCEPTANCE_MATRIX_INVALID')
        require(len({x.identifier for x in self.criteria})==len(self.criteria),'ACCEPTANCE_CRITERION_CONFLICT')
        expected={x.identifier:x for x in required_criteria(self.candidate.evidence)}
        for criterion in self.criteria:
            if criterion.identifier in expected:
                require(criterion==expected[criterion.identifier],'ACCEPTANCE_REQUIRED_CRITERION_CHANGED')
            else:
                require(criterion.level=='INFORMATIONAL','ACCEPTANCE_ARBITRARY_POLICY_UNSUPPORTED')
                require(any((criterion.category,criterion.scope,criterion.source,criterion.subject)==
                            (x.category,x.scope,x.source,x.subject) for x in expected.values()),'ACCEPTANCE_CRITERION_SCOPE_INVALID')
        object.__setattr__(self,'criteria',tuple(sorted(self.criteria,key=lambda x:x.identifier)))

    def evaluate(self):
        supplied={x.identifier:x for x in self.criteria}
        rows=[]
        for criterion in required_criteria(self.candidate.evidence):
            rows.append(evaluate_criterion(criterion,self.candidate.evidence) if criterion.identifier in supplied else
                        CriterionResult(criterion,'INCOMPLETE',reasons=('ACCEPTANCE_REQUIRED_CRITERION_MISSING',)))
        expected={x.criterion.identifier for x in rows}
        rows.extend(evaluate_criterion(x,self.candidate.evidence) for x in self.criteria if x.identifier not in expected)
        return tuple(sorted(rows,key=lambda x:x.criterion.identifier))

    def record(self):
        rows=self.evaluate()
        return {'candidate':self.candidate.fingerprint(),'snapshot':self.candidate.evidence.fingerprint(),
                'criteria':[x.record() for x in self.criteria],'results':[x.record() for x in rows],
                'surface_matrix':{surface:[x.record() for x in rows if x.criterion.scope==surface] for surface in r.TARGETS}}


def acceptance_matrix(candidate,informational=()):
    require(type(candidate) is ReleaseCandidateIdentity and type(informational) is tuple,'ACCEPTANCE_CANDIDATE_INVALID')
    return ReleaseAcceptanceMatrix(candidate,required_criteria(candidate.evidence)+informational)


@dataclass(frozen=True)
class ReleaseCandidateVerdict(CanonicalModel):
    matrix: ReleaseAcceptanceMatrix
    DOMAIN = 'apexforge.release-candidate-verdict/v1'

    def __post_init__(self):
        require(type(self.matrix) is ReleaseAcceptanceMatrix,'ACCEPTANCE_VERDICT_INVALID')

    @property
    def status(self):
        statuses={x.status for x in self.matrix.evaluate() if x.criterion.level=='REQUIRED' and not x.satisfies_required}
        if 'FAIL' in statuses:return 'REJECTED'
        if statuses & {'BLOCKED','DEFERRED','SKIPPED'}:return 'BLOCKED'
        return 'INCOMPLETE' if statuses else 'ACCEPTED'

    def valid_for(self,matrix):
        return type(matrix) is ReleaseAcceptanceMatrix and matrix.fingerprint()==self.matrix.fingerprint()

    def record(self):
        rows=self.matrix.evaluate();required=tuple(x for x in rows if x.criterion.level=='REQUIRED')
        return {'candidate':self.matrix.candidate.fingerprint(),'snapshot':self.matrix.candidate.evidence.fingerprint(),
                'matrix':self.matrix.fingerprint(),'verdict':self.status,
                'satisfied_required':tuple(x.criterion.identifier for x in required if x.satisfies_required),
                'unsatisfied_required':tuple((x.criterion.identifier,x.status,x.reasons) for x in required if not x.satisfies_required),
                'blocker_codes':tuple(sorted({(x.criterion.identifier,code) for x in required if not x.satisfies_required
                                             for code in x.reasons or ('ACCEPTANCE_REQUIRED_GATE_NOT_PASS',)})),
                'deferred':tuple(x.criterion.identifier for x in rows if x.status=='DEFERRED'),
                'skipped':tuple(x.criterion.identifier for x in rows if x.status=='SKIPPED'),
                'grants_release_approval':self.status=='ACCEPTED','approval_scope':'EVIDENCE_ONLY',
                'grants_authority':False,'grants_trust':False,'publication_performed':False,
                'installation_performed':False,'signing_performed':False,'freeze_performed':False}
