"""P16.10 provider-neutral evidence DAG; no commands, signing or publication."""
from dataclasses import dataclass
from tooling import release_architecture as r, release_build as b, release_manifest as m, release_versioning as v
from tooling.release_installation import InstallationReceipt
from tooling.domain_platform import CanonicalModel
from tooling.package_manifest import CanonicalReference

STATUSES = ('PASS', 'FAIL', 'BLOCKED', 'DEFERRED', 'SKIPPED', 'INCOMPLETE', 'PENDING')
PHASES = ('BASELINE_VALIDATION', 'REGRESSION_VALIDATION', 'ARTIFACT_EVIDENCE', 'INSTALLATION_CONTRACT',
          'SIGNING_GATE', 'PUBLICATION_DRY_RUN', 'RELEASE_READINESS_SUMMARY')
KINDS = ('BASELINE', 'REGRESSION', 'ARTIFACT', 'OWNER_BUILD', 'CONTENT_REPRODUCIBILITY', 'RAW_REPRODUCIBILITY',
         'SOURCE_CONTINUITY', 'MANIFEST', 'NATIVE_PROFILE', 'INSTALLATION', 'INSTALLATION_HOST',
         'SIGNING', 'COMPATIBILITY', 'CREDENTIAL_REQUIREMENT', 'ACCEPTANCE')
SUITES = ('P16', 'P15', 'P14', 'NATIVE', 'AUTHORITY')
PUBLICATIONS = (('python', 'PYTHON_INDEX', 'PYTHON_PUBLISH_TOKEN'),
                ('vscode', 'VSCODE_MARKETPLACE', 'VSCODE_PUBLISH_TOKEN'),
                ('visual-studio', 'VISUAL_STUDIO_MARKETPLACE', 'VISUAL_STUDIO_PUBLISH_TOKEN'),
                ('native-win-x64', 'NATIVE_RELEASE_ASSET', 'NATIVE_ASSET_PUBLISH_TOKEN'))
MAX_STEPS, MAX_EVIDENCE = 64, 512
REASONS = ('REGRESSION_SKIPPED_TESTS', 'ISOLATED_CONTRACT_ONLY', 'PYTHON_WHEEL_UNAVAILABLE',
           'SDIST_ARCHIVE_TIMESTAMP_GAP', 'VSCODE_REAL_VSCE_UNVERIFIED', 'VISUAL_STUDIO_RAW_REPRO_DEFERRED',
           'NATIVE_MEASURED_PROFILE_ONLY', 'P16_9_HOST_SYMLINK_SKIP', 'CRYPTO_PROVIDER_UNAVAILABLE',
           'P16_11_SIGNING_REQUIRED', 'P16_12_ACCEPTANCE_REQUIRED', 'CREDENTIAL_NOT_RESOLVED',
           'COMPATIBILITY_UNRESOLVED', 'MANIFEST_SCOPE_UNAVAILABLE', 'FROZEN_GIT_BLOB_SOURCE',
           'NORMALIZED_CONTENT_REPRODUCIBLE', 'GENUINE_OWNER_BUILT_ARCHIVE', 'BASELINE_REFERENCE_ONLY',
           'SOURCE_CONTINUITY_EXACT', 'ARTIFACT_UNAVAILABLE')


class ReleasePipelineError(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def require(ok, code):
    if not ok:
        raise ReleasePipelineError(code)


def pairs(values):
    require(type(values) is tuple and len(values) <= MAX_EVIDENCE and all(type(x) is tuple and len(x) == 2 and
            type(x[0]) is str and x[0] in KINDS and type(x[1]) is str for x in values), 'PIPELINE_REQUIREMENT_INVALID')
    for _, subject in values:
        r.text(subject, 'PIPELINE_SUBJECT_INVALID')
    require(len(set(values)) == len(values), 'PIPELINE_REQUIREMENT_DUPLICATE')
    return tuple(sorted(values))


@dataclass(frozen=True)
class PipelineStep(CanonicalModel):
    identifier: str
    phase: str
    predecessors: tuple = ()
    requirements: tuple = ()
    DOMAIN = 'apexforge.release-pipeline-step/v1'

    def __post_init__(self):
        r.text(self.identifier, 'PIPELINE_STEP_INVALID')
        require(type(self.phase) is str and self.phase in PHASES, 'PIPELINE_PHASE_INVALID')
        require(type(self.predecessors) is tuple and len(self.predecessors) <= MAX_STEPS and
                all(type(x) is str for x in self.predecessors), 'PIPELINE_PREDECESSOR_INVALID')
        for value in self.predecessors:
            r.text(value, 'PIPELINE_PREDECESSOR_INVALID')
        require(len(set(self.predecessors)) == len(self.predecessors), 'PIPELINE_PREDECESSOR_INVALID')
        object.__setattr__(self, 'predecessors', tuple(sorted(self.predecessors)))
        object.__setattr__(self, 'requirements', pairs(self.requirements))

    def record(self):
        return {'id': self.identifier, 'phase': self.phase, 'predecessors': self.predecessors,
                'required_evidence': self.requirements, 'commands': 'NOT_SUPPORTED'}


def topological(steps):
    require(type(steps) is tuple and 1 <= len(steps) <= MAX_STEPS and all(type(s) is PipelineStep for s in steps), 'PIPELINE_GRAPH_INVALID')
    table = {s.identifier: s for s in steps}
    require(len(table) == len(steps), 'PIPELINE_STEP_DUPLICATE')
    require(all(set(s.predecessors) <= set(table) for s in steps), 'PIPELINE_PREDECESSOR_UNKNOWN')
    result, emitted = [], set()
    while len(result) < len(steps):
        available = sorted(name for name, s in table.items() if name not in emitted and set(s.predecessors) <= emitted)
        require(bool(available), 'PIPELINE_CYCLE')
        for name in available:
            result.append(table[name]); emitted.add(name)
    return tuple(result)


@dataclass(frozen=True)
class ReleasePipelineIdentity(CanonicalModel):
    architecture: r.ReleaseArtifactMatrix
    steps: tuple
    provider: str = 'PROVIDER_NEUTRAL'
    schema: str = 'apexforge.release-pipeline/v1'
    DOMAIN = 'apexforge.release-pipeline/v1'

    def __post_init__(self):
        require(type(self.architecture) is r.ReleaseArtifactMatrix and self.architecture.release.baseline == r.P15_BASELINE,
                'PIPELINE_BASELINE_MISMATCH')
        require(type(self.provider) is str and self.provider == 'PROVIDER_NEUTRAL' and type(self.schema) is str
                and self.schema == self.DOMAIN, 'PIPELINE_SCHEMA_INVALID')
        steps = topological(self.steps)
        table = {s.identifier: s for s in steps}
        for expected in required_steps(self.architecture):
            require(expected.identifier in table and table[expected.identifier].phase == expected.phase and
                    set(expected.requirements) <= set(table[expected.identifier].requirements), 'PIPELINE_REQUIRED_GATE_MISSING')
        surfaces = {d.target.identifier for d in self.architecture.artifacts}
        artifacts = {d.identity.identifier for d in self.architecture.artifacts}
        for s in steps:
            for kind, subject in s.requirements:
                allowed = set(SUITES) if kind == 'REGRESSION' else artifacts if kind in (
                    'ARTIFACT', 'OWNER_BUILD', 'SOURCE_CONTINUITY', 'CONTENT_REPRODUCIBILITY', 'RAW_REPRODUCIBILITY') else (
                    {'native-win-x64'} & surfaces) if kind == 'NATIVE_PROFILE' else surfaces if kind in (
                    'MANIFEST', 'COMPATIBILITY', 'CREDENTIAL_REQUIREMENT') else {'release'}
                require(subject in allowed, 'PIPELINE_REQUIREMENT_SCOPE_INVALID')
        require(steps[0].phase == 'BASELINE_VALIDATION' and not steps[0].predecessors and
                sum(s.phase == 'BASELINE_VALIDATION' for s in steps) == 1, 'PIPELINE_BASELINE_GATE_REQUIRED')
        for phase in ('REGRESSION_VALIDATION', 'INSTALLATION_CONTRACT', 'SIGNING_GATE', 'RELEASE_READINESS_SUMMARY'):
            require(sum(s.phase == phase for s in steps) == 1, 'PIPELINE_GATE_REQUIRED')
        require(set(s.phase for s in steps) == set(PHASES), 'PIPELINE_GATE_REQUIRED')
        ancestors = {}
        for s in steps:
            ancestors[s.identifier] = set(s.predecessors) | set().union(*(ancestors[p] for p in s.predecessors))
            if s != steps[0]:
                require(steps[0].identifier in ancestors[s.identifier], 'PIPELINE_BASELINE_GATE_REQUIRED')
            if s.phase == 'PUBLICATION_DRY_RUN':
                require({'REGRESSION_VALIDATION', 'ARTIFACT_EVIDENCE', 'INSTALLATION_CONTRACT', 'SIGNING_GATE'} <=
                        {p.phase for p in steps if p.identifier in ancestors[s.identifier]}, 'PUBLICATION_GATE_REQUIRED')
        for expected in required_steps(self.architecture):
            require(set(expected.predecessors) <= ancestors[expected.identifier], 'PIPELINE_REQUIRED_DEPENDENCY_MISSING')
        require(all(s.identifier in ancestors['readiness'] for s in steps if s.phase == 'PUBLICATION_DRY_RUN'),
                'PIPELINE_SUMMARY_SCOPE_INVALID')
        object.__setattr__(self, 'steps', steps)

    @property
    def release(self):
        return self.architecture.release

    def record(self):
        return {'schema': self.schema, 'release': self.release.fingerprint(), 'baseline': self.release.baseline.record(),
                'architecture': self.architecture.fingerprint(), 'provider': self.provider,
                'steps': [s.record() for s in self.steps], 'required_evidence': sorted({q for s in self.steps for q in s.requirements}),
                'trigger': 'DECLARATION_ONLY_NO_REMOTE_TRIGGER', 'semantic_authority': 'CANONICAL_AIR'}


def required_steps(architecture):
    require(type(architecture) is r.ReleaseArtifactMatrix, 'PIPELINE_ARCHITECTURE_INVALID')
    steps = [PipelineStep('baseline', 'BASELINE_VALIDATION', requirements=(('BASELINE', 'release'),)),
             PipelineStep('regressions', 'REGRESSION_VALIDATION', ('baseline',), tuple(('REGRESSION', s) for s in SUITES)),
             PipelineStep('installation', 'INSTALLATION_CONTRACT', ('regressions',), (('INSTALLATION', 'release'), ('INSTALLATION_HOST', 'release'))),
             PipelineStep('signing', 'SIGNING_GATE', ('baseline',), (('SIGNING', 'release'),))]
    surfaces = sorted({d.target.identifier for d in architecture.artifacts})
    for surface in surfaces:
        requirements = [('MANIFEST', surface)]
        for d in architecture.artifacts:
            if d.target.identifier == surface:
                requirements.extend((kind, d.identity.identifier) for kind in ('ARTIFACT', 'OWNER_BUILD', 'SOURCE_CONTINUITY', 'CONTENT_REPRODUCIBILITY', 'RAW_REPRODUCIBILITY'))
        if surface == 'native-win-x64':
            requirements.append(('NATIVE_PROFILE', surface))
        steps.append(PipelineStep('artifacts-'+surface, 'ARTIFACT_EVIDENCE', ('regressions',), tuple(requirements)))
        steps.append(PipelineStep('publication-'+surface, 'PUBLICATION_DRY_RUN',
             ('artifacts-'+surface, 'installation', 'signing', 'regressions'),
             (('COMPATIBILITY', surface), ('CREDENTIAL_REQUIREMENT', surface), ('ACCEPTANCE', 'release'))))
    steps.append(PipelineStep('readiness', 'RELEASE_READINESS_SUMMARY', tuple('publication-'+s for s in surfaces)))
    return tuple(steps)


def pipeline_for(architecture):
    return ReleasePipelineIdentity(architecture, required_steps(architecture))


@dataclass(frozen=True)
class GateEvidence(CanonicalModel):
    release: r.ReleaseIdentity
    kind: str
    subject: str
    status: str
    references: tuple = ()
    reasons: tuple = ()
    DOMAIN = 'apexforge.release-pipeline-evidence/v1'

    def __post_init__(self):
        require(type(self.release) is r.ReleaseIdentity, 'PIPELINE_EVIDENCE_RELEASE_INVALID')
        pairs(((self.kind, self.subject),))
        require(type(self.status) is str and self.status in STATUSES, 'PIPELINE_STATUS_INVALID')
        object.__setattr__(self, 'references', r.ordered(self.references, CanonicalReference, 'PIPELINE_REFERENCE_INVALID'))
        require(self.status != 'PASS' or bool(self.references), 'PIPELINE_PASS_EVIDENCE_MISSING')
        if self.kind == 'BASELINE' and self.status == 'PASS':
            require(self.release.baseline == r.P15_BASELINE and m.reference(r.P15_BASELINE) in self.references,
                    'PIPELINE_BASELINE_EVIDENCE_MISMATCH')
        require(type(self.reasons) is tuple and len(self.reasons) <= 16 and all(type(x) is str for x in self.reasons), 'PIPELINE_REASON_INVALID')
        require(all(reason in REASONS for reason in self.reasons), 'PIPELINE_REASON_INVALID')
        object.__setattr__(self, 'reasons', tuple(sorted(set(self.reasons))))
        require(self.kind not in ('SIGNING', 'ACCEPTANCE') or self.status != 'PASS', 'PIPELINE_FUTURE_GATE_PASS_UNSUPPORTED')

    def record(self):
        return {'release': self.release.fingerprint(), 'kind': self.kind, 'subject': self.subject, 'status': self.status,
                'references': [x.record() for x in self.references], 'reasons': self.reasons,
                'evidence_class': 'SUPPLIED_DECLARATION_NOT_AUTHENTICATION'}


@dataclass(frozen=True)
class RegressionEvidence(CanonicalModel):
    release: r.ReleaseIdentity
    suite: str
    passed: int
    skipped: int
    failed: int
    discovered: int
    reference: CanonicalReference
    DOMAIN = 'apexforge.release-regression-evidence/v1'

    def __post_init__(self):
        require(type(self.release) is r.ReleaseIdentity and type(self.suite) is str and self.suite in SUITES
                and type(self.reference) is CanonicalReference, 'PIPELINE_REGRESSION_INVALID')
        require(all(type(x) is int and 0 <= x <= 1000000 for x in (self.passed, self.skipped, self.failed, self.discovered))
                and self.passed+self.skipped+self.failed == self.discovered, 'PIPELINE_REGRESSION_COUNTS_INVALID')

    @property
    def status(self):
        return 'FAIL' if self.failed else 'INCOMPLETE' if not self.discovered else 'SKIPPED' if self.skipped else 'PASS'

    def record(self):
        return {'release': self.release.fingerprint(), 'suite': self.suite, 'passed': self.passed, 'skipped': self.skipped,
                'failed': self.failed, 'discovered': self.discovered, 'status': self.status, 'reference': self.reference.record()}

    def gate(self):
        return GateEvidence(self.release, 'REGRESSION', self.suite, self.status, (self.reference,),
                            ('REGRESSION_SKIPPED_TESTS',) if self.skipped else ())


def manifest_gate(manifest, surface):
    require(type(manifest) is m.ReleaseManifest and type(surface) is str and surface in r.TARGETS and
            all(d.target.identifier == surface for d in manifest.architecture.artifacts), 'PIPELINE_MANIFEST_SCOPE_INVALID')
    status = {'COMPLETE': 'PASS', 'INCOMPLETE': 'INCOMPLETE', 'INVALID': 'FAIL'}[manifest.status]
    return GateEvidence(manifest.architecture.release, 'MANIFEST', surface, status,
                        (m.reference(manifest), m.reference(manifest.architecture)))


def artifact_gate(descriptor, artifact):
    require(type(descriptor) is r.ReleaseArtifactDescriptor and type(artifact) is b.ReleaseBuildArtifact and
            artifact._slot.descriptor == descriptor, 'PIPELINE_ARTIFACT_BINDING_INVALID')
    return GateEvidence(descriptor.release, 'ARTIFACT', descriptor.identity.identifier, 'PASS',
                        (m.reference(descriptor), m.reference(artifact)))


def compatibility_gate(assessment, surface):
    require(type(assessment) is v.ReleaseUpgradeAssessment and type(surface) is str and surface in r.TARGETS and
            all(s.target.identifier == surface for s in assessment.policy.surfaces) and
            all(f.surface.target.identifier == surface for f in assessment.findings), 'PIPELINE_COMPATIBILITY_SCOPE_INVALID')
    status = {'DIRECT': 'PASS', 'INCOMPLETE': 'INCOMPLETE', 'UNSUPPORTED': 'FAIL', 'MIGRATION_REQUIRED': 'DEFERRED'}[assessment.status]
    return GateEvidence(assessment.policy.target, 'COMPATIBILITY', surface, status,
                        (CanonicalReference(assessment.DOMAIN, 'artifact', assessment.fingerprint()),))


def installation_gate(receipt):
    require(type(receipt) is InstallationReceipt and receipt.result.identity is not None, 'PIPELINE_INSTALLATION_BINDING_INVALID')
    return GateEvidence(receipt.result.identity.release, 'INSTALLATION', 'release', 'PASS',
                        (CanonicalReference(receipt.DOMAIN, 'artifact', receipt.fingerprint()),), ('ISOLATED_CONTRACT_ONLY',))


def aggregate(statuses):
    for status in ('FAIL', 'BLOCKED', 'INCOMPLETE', 'DEFERRED', 'SKIPPED', 'PENDING'):
        if status in statuses:
            return status
    return 'PASS'


@dataclass(frozen=True)
class ReleasePipelineResult(CanonicalModel):
    pipeline: ReleasePipelineIdentity
    evidence: tuple = ()
    regressions: tuple = ()
    DOMAIN = 'apexforge.release-pipeline-result/v1'

    def __post_init__(self):
        require(type(self.pipeline) is ReleasePipelineIdentity and type(self.evidence) is tuple and len(self.evidence) <= MAX_EVIDENCE
                and all(type(x) is GateEvidence for x in self.evidence), 'PIPELINE_EVIDENCE_INVALID')
        require(type(self.regressions) is tuple and len(self.regressions) <= len(SUITES) and
                all(type(x) is RegressionEvidence for x in self.regressions), 'PIPELINE_REGRESSION_INVALID')
        require(all(x.kind != 'REGRESSION' for x in self.evidence), 'PIPELINE_REGRESSION_COUNTS_REQUIRED')
        gates = self.evidence + tuple(x.gate() for x in self.regressions)
        keys = [(x.kind, x.subject) for x in gates]
        require(len(set(keys)) == len(keys), 'PIPELINE_EVIDENCE_CONFLICT')
        require(all(x.release == self.pipeline.release for x in gates), 'PIPELINE_EVIDENCE_RELEASE_MISMATCH')
        required = {q for s in self.pipeline.steps for q in s.requirements}
        require(set(keys) <= required, 'PIPELINE_EVIDENCE_UNEXPECTED')
        descriptors = {d.identity.identifier: d for d in self.pipeline.architecture.artifacts}
        for value in self.evidence:
            if value.kind == 'ARTIFACT' and value.status == 'PASS':
                require(m.reference(descriptors[value.subject]) in value.references and
                        any(ref.schema == b.ReleaseBuildArtifact.DOMAIN for ref in value.references),
                        'PIPELINE_ARTIFACT_REFERENCE_MISMATCH')
            elif value.kind == 'MANIFEST' and value.status == 'PASS':
                scope = r.ReleaseArtifactMatrix(self.pipeline.release, tuple(d for d in descriptors.values() if d.target.identifier == value.subject))
                require(m.reference(scope) in value.references and any(ref.schema == m.ReleaseManifest.DOMAIN for ref in value.references),
                        'PIPELINE_MANIFEST_REFERENCE_MISMATCH')
            elif value.kind == 'COMPATIBILITY' and value.status == 'PASS':
                require(any(ref.schema == v.ReleaseUpgradeAssessment.DOMAIN for ref in value.references),
                        'PIPELINE_COMPATIBILITY_REFERENCE_MISMATCH')
        object.__setattr__(self, 'evidence', tuple(sorted(self.evidence, key=lambda x: (x.kind, x.subject))))
        object.__setattr__(self, 'regressions', tuple(sorted(self.regressions, key=lambda x: x.suite)))

    def evaluate(self):
        supplied = {(x.kind, x.subject): x for x in self.evidence + tuple(r.gate() for r in self.regressions)}
        results = {}
        for step in self.pipeline.steps:
            observations, blockers = [], set()
            for key in step.requirements:
                value = supplied.get(key)
                status = 'INCOMPLETE' if value is None else value.status
                reasons = ('PIPELINE_EVIDENCE_MISSING',) if value is None else value.reasons
                if key[0] == 'SIGNING':
                    status, reasons = 'FAIL' if status == 'FAIL' else 'BLOCKED', tuple(sorted(set(reasons) |
                                                           {'CRYPTO_PROVIDER_UNAVAILABLE', 'P16_11_SIGNING_REQUIRED'}))
                elif key[0] == 'ACCEPTANCE':
                    status, reasons = 'FAIL' if status == 'FAIL' else 'DEFERRED', tuple(sorted(set(reasons) | {'P16_12_ACCEPTANCE_REQUIRED'}))
                elif key[0] == 'ARTIFACT' and any(d.identity.identifier == key[1] and d.availability == 'UNAVAILABLE'
                                                               for d in self.pipeline.architecture.artifacts):
                    status, reasons = 'FAIL' if status == 'FAIL' else 'INCOMPLETE', tuple(sorted(set(reasons) | {'ARTIFACT_UNAVAILABLE'}))
                if status != 'PASS':
                    blockers.add((key[0], key[1], status, reasons))
                observations.append((key, status, None if value is None else value.fingerprint()))
            statuses = [row[1] for row in observations]
            for predecessor in step.predecessors:
                prior = results[predecessor]
                if prior['status'] != 'PASS':
                    statuses.append('BLOCKED')
                    blockers.add(('PREDECESSOR', predecessor, prior['status'], ('PIPELINE_DEPENDENCY_NOT_PASS',)))
            results[step.identifier] = {'id': step.identifier, 'phase': step.phase, 'status': aggregate(statuses),
                                         'observations': tuple(observations), 'blockers': tuple(sorted(blockers))}
        return tuple(results[s.identifier] for s in self.pipeline.steps)

    def record(self):
        gates = self.evaluate()
        return {'pipeline': self.pipeline.fingerprint(), 'evidence': [x.record() for x in self.evidence],
                'regressions': [x.record() for x in self.regressions], 'gates': gates,
                'target_readiness': tuple(g for g in gates if g['phase'] == 'ARTIFACT_EVIDENCE'),
                'release_ready': False, 'final_acceptance': 'DEFER_TO_P16_12', 'freeze': 'DEFER_TO_P16_13',
                'publication_performed': False, 'grants_authority': False, 'grants_trust': False,
                'crypto': 'CRYPTO_PROVIDER_UNAVAILABLE'}


@dataclass(frozen=True)
class PublicationTarget(CanonicalModel):
    surface: str
    DOMAIN = 'apexforge.release-publication-target/v1'

    def __post_init__(self):
        require(type(self.surface) is str and self.surface in r.TARGETS, 'PUBLICATION_TARGET_UNSUPPORTED')

    def record(self):
        row = next(row for row in PUBLICATIONS if row[0] == self.surface)
        return {'surface': row[0], 'target': row[1], 'credential_requirement': row[2], 'credential_value': 'NOT_LOADED',
                'signing_required': True, 'acceptance_required': True, 'channel_grants_trust': False,
                'provider_api': 'NOT_IMPLEMENTED'}


@dataclass(frozen=True)
class PublicationDryRunRecord(CanonicalModel):
    result: ReleasePipelineResult
    target: PublicationTarget
    DOMAIN = 'apexforge.publication-dry-run/v1'

    def __post_init__(self):
        require(type(self.result) is ReleasePipelineResult and type(self.target) is PublicationTarget and
                any(d.target.identifier == self.target.surface for d in self.result.pipeline.architecture.artifacts), 'PUBLICATION_RELEASE_SCOPE_INVALID')
        require(any(s.identifier == 'publication-'+self.target.surface for s in self.result.pipeline.steps), 'PUBLICATION_GATE_REQUIRED')

    def record(self):
        gate = next(g for g in self.result.evaluate() if g['id'] == 'publication-'+self.target.surface)
        ids = {d.identity.identifier for d in self.result.pipeline.architecture.artifacts if d.target.identifier == self.target.surface}
        return {'release': self.result.pipeline.release.fingerprint(), 'pipeline_result': self.result.fingerprint(),
                'target': self.target.record(), 'artifacts': [m.reference(d).record() for d in self.result.pipeline.architecture.artifacts
                                                           if d.target.identifier == self.target.surface],
                'artifact_evidence': [e.record() for e in self.result.evidence if e.kind == 'ARTIFACT' and e.subject in ids],
                'manifest_evidence': [e.record() for e in self.result.evidence if e.kind == 'MANIFEST' and e.subject == self.target.surface],
                'prerequisites': gate, 'state': 'ELIGIBLE_IF_AUTHORIZED' if gate['status'] == 'PASS' else gate['status'],
                'would_publish_if_authorized': gate['status'] == 'PASS', 'publication_performed': False,
                'network_publication_calls': 0, 'approved': False, 'trusted': False, 'authority': False}


def publication_dry_run(result):
    require(type(result) is ReleasePipelineResult, 'PUBLICATION_RESULT_INVALID')
    return tuple(PublicationDryRunRecord(result, PublicationTarget(surface)) for surface in
                 sorted({d.target.identifier for d in result.pipeline.architecture.artifacts}))
