"""P16.9 exact passive projections and cooperative isolated transactions only."""
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
import os
import stat
import tempfile

from tooling import release_architecture as r, release_build as b, release_manifest as m, release_versioning as v
from tooling.domain_platform import CanonicalModel
from tooling.package_manifest import PackagePath

MAX_FILES, MAX_TOTAL, MAX_CHILDREN = 64, 8 * 1024 * 1024, 4096
MAX_TRANSACTIONS = 1024
TARGETS = {'PYTHON_ENVIRONMENT': 'python', 'VSCODE_EXTENSION_ROOT': 'vscode',
           'VISUAL_STUDIO_EXTENSION_ROOT': 'visual-studio', 'NATIVE_APPLICATION_ROOT': 'native-win-x64'}
POLICY = 'apexforge.isolated-exact-projection/v1'


class InstallationError(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def require(ok, code):
    if not ok:
        raise InstallationError(code)


@dataclass(frozen=True)
class DeploymentTarget(CanonicalModel):
    kind: str
    destination: str
    DOMAIN = 'apexforge.deployment-target/v1'

    def __post_init__(self):
        require(type(self.kind) is str and self.kind in TARGETS, 'INSTALLATION_TARGET_INVALID')
        r.text(self.destination, 'INSTALLATION_DESTINATION_INVALID')

    def record(self):
        return {'kind': self.kind, 'destination': self.destination, 'surface': TARGETS[self.kind], 'physical_path': 'NOT_CANONICAL'}


@dataclass(frozen=True)
class InstallationIdentity(CanonicalModel):
    target: DeploymentTarget
    manifest: m.ReleaseManifest
    policy: str = POLICY
    DOMAIN = 'apexforge.installation-identity/v1'

    def __post_init__(self):
        require(type(self.target) is DeploymentTarget and type(self.manifest) is m.ReleaseManifest
                and type(self.policy) is str and self.policy == POLICY, 'INSTALLATION_IDENTITY_INVALID')
        require(self.manifest.status == 'COMPLETE', 'INSTALLATION_MANIFEST_NOT_COMPLETE')
        require(all(d.target.identifier == TARGETS[self.target.kind] for d in self.manifest.architecture.artifacts),
                'INSTALLATION_TARGET_MISMATCH')

    @property
    def release(self):
        return self.manifest.architecture.release

    def record(self):
        return {'target': self.target.record(), 'release': self.release.fingerprint(),
                'manifest': self.manifest.fingerprint(), 'policy': self.policy, 'grants_authority': False, 'trusted': False}


@dataclass(frozen=True)
class FileProjection(CanonicalModel):
    path: PackagePath
    artifact: b.ReleaseBuildArtifact
    DOMAIN = 'apexforge.installation-file-projection/v1'

    def __post_init__(self):
        require(type(self.path) is PackagePath and type(self.artifact) is b.ReleaseBuildArtifact, 'INSTALLATION_FILE_INVALID')
        require(len(self.path.value.split('/')) <= 16 and not any(p.startswith('.apexforge-') for p in self.path.value.split('/')),
                'INSTALLATION_PATH_INVALID')

    def record(self):
        return {'path': self.path.value, 'artifact': self.artifact.fingerprint(), 'digest': self.artifact.declared_digest,
                'length': len(self.artifact.data)}


def inventory(files, identity):
    require(type(files) is tuple and 1 <= len(files) <= MAX_FILES and all(type(f) is FileProjection for f in files),
            'INSTALLATION_FILES_INVALID')
    require(sum(len(f.artifact.data) for f in files) <= MAX_TOTAL, 'INSTALLATION_SIZE_LIMIT')
    keys = [f.path.value.casefold() for f in files]
    require(len(set(keys)) == len(keys), 'INSTALLATION_PATH_CONFLICT')
    require(not any('/'.join(key.split('/')[:i]) in keys for key in keys for i in range(1, len(key.split('/')))),
            'INSTALLATION_PATH_CONFLICT')
    # Exact-case directory spelling must also agree across independently named files.
    prefixes = {}
    for f in files:
        parts = f.path.value.split('/')
        for i in range(1, len(parts)+1):
            prefix = '/'.join(parts[:i])
            require(prefixes.get(prefix.casefold(), prefix) == prefix, 'INSTALLATION_PATH_CONFLICT')
            prefixes[prefix.casefold()] = prefix
    expected = {a.identity.identifier: a for a in identity.manifest.artifacts.artifacts}
    require(len({f.artifact.identity.identifier for f in files}) == len(files) and
            {f.artifact.identity.identifier for f in files} == set(expected), 'INSTALLATION_EVIDENCE_MISMATCH')
    for f in files:
        require(expected[f.artifact.identity.identifier] == f.artifact, 'INSTALLATION_EVIDENCE_MISMATCH')
        checksum = next(c for c in identity.manifest.checksums.records if c.artifact == f.artifact.identity)
        m.verify_checksum(checksum, f.artifact, f.artifact.data)
    return tuple(sorted(files, key=lambda f: f.path.value))


@dataclass(frozen=True)
class DeploymentState(CanonicalModel):
    target: DeploymentTarget
    identity: InstallationIdentity | None = None
    files: tuple = ()
    receipt_plan: str = ''
    predecessor: str = ''
    DOMAIN = 'apexforge.deployment-state/v1'

    def __post_init__(self):
        require(type(self.target) is DeploymentTarget, 'INSTALLATION_STATE_INVALID')
        if self.identity is None:
            require(type(self.files) is tuple and self.files == () and type(self.receipt_plan) is str
                    and type(self.predecessor) is str and self.receipt_plan == self.predecessor == '', 'INSTALLATION_STATE_INVALID')
        else:
            require(type(self.identity) is InstallationIdentity and self.identity.target == self.target, 'INSTALLATION_STATE_INVALID')
            object.__setattr__(self, 'files', inventory(self.files, self.identity))
            try:
                m.hex_digest(self.receipt_plan); m.hex_digest(self.predecessor)
            except ValueError as exc:
                raise InstallationError('INSTALLATION_STATE_INVALID') from exc

    def record(self):
        return {'target': self.target.record(), 'identity': None if self.identity is None else self.identity.fingerprint(),
                'release': None if self.identity is None else self.identity.release.fingerprint(),
                'inventory': [f.record() for f in self.files], 'receipt_plan': self.receipt_plan, 'predecessor': self.predecessor}


@dataclass(frozen=True)
class InstallationPlan(CanonicalModel):
    identity: InstallationIdentity
    files: tuple
    current: DeploymentState
    assessment: v.ReleaseUpgradeAssessment | None = None
    DOMAIN = 'apexforge.installation-plan/v1'

    def __post_init__(self):
        require(type(self.identity) is InstallationIdentity and type(self.current) is DeploymentState
                and self.current.target == self.identity.target, 'INSTALLATION_PLAN_INVALID')
        object.__setattr__(self, 'files', inventory(self.files, self.identity))
        if self.current.identity is None or self.mode == 'EXACT_REINSTALL':
            require(self.assessment is None, 'UPGRADE_POLICY_BINDING_INVALID')
        else:
            require(type(self.assessment) is v.ReleaseUpgradeAssessment and
                    self.assessment.policy.source == self.current.identity.release and
                    self.assessment.policy.target == self.identity.release and
                    all(s.target.identifier == TARGETS[self.identity.target.kind] for s in self.assessment.policy.surfaces),
                    'UPGRADE_POLICY_BINDING_INVALID')
            primary = dict(v.PRIMARY)[TARGETS[self.identity.target.kind]]
            require(any(s.domain == primary for s in self.assessment.policy.surfaces), 'UPGRADE_POLICY_BINDING_INVALID')
            for versions, ident in ((self.assessment.policy.source_versions, self.current.identity),
                                    (self.assessment.policy.target_versions, self.identity)):
                for mapping in versions:
                    if mapping.surface.domain == primary:
                        expected = {d.target.native_profile if primary == 'NATIVE_PROFILE' else d.surface_version
                                    for d in ident.manifest.architecture.artifacts}
                        require(expected == {mapping.version}, 'UPGRADE_VERSION_BINDING_INVALID')

    @property
    def mode(self):
        return 'CLEAN_INSTALL' if self.current.identity is None else 'EXACT_REINSTALL' if (
            self.current.identity == self.identity and self.current.files == self.files) else 'UPGRADE'

    @property
    def executable(self):
        return self.mode != 'UPGRADE' or self.assessment.status == 'DIRECT'

    def record(self):
        return {'identity': self.identity.fingerprint(), 'current': self.current.fingerprint(),
                'inventory': [f.record() for f in self.files], 'mode': self.mode,
                'assessment': None if self.assessment is None else self.assessment.fingerprint(),
                'upgrade_status': None if self.assessment is None else self.assessment.status,
                'preconditions': 'EXACT_CURRENT_AND_NO_UNKNOWN_OVERWRITE', 'conflict_policy': 'REJECT',
                'executable_in_isolation': self.executable, 'migration_executed': False,
                'provenance': self.identity.manifest.provenance.fingerprint()}

    def resulting_state(self):
        if self.mode == 'EXACT_REINSTALL':
            return self.current
        return DeploymentState(self.identity.target, self.identity, self.files, self.fingerprint(), self.current.fingerprint())


@dataclass(frozen=True)
class InstallationReceipt(CanonicalModel):
    plan: object
    previous: DeploymentState
    result: DeploymentState
    DOMAIN = 'apexforge.installation-receipt/v1'

    def __post_init__(self):
        require(type(self.plan) in (InstallationPlan, RollbackPlan) and type(self.previous) is DeploymentState
                and type(self.result) is DeploymentState and self.previous == self.plan.current
                and self.result == self.plan.resulting_state(), 'INSTALLATION_RECEIPT_INVALID')

    def record(self):
        return {'plan': self.plan.fingerprint(), 'previous': self.previous.fingerprint(), 'result': self.result.fingerprint(),
                'kind': 'ROLLBACK' if type(self.plan) is RollbackPlan else self.plan.mode,
                'status': 'COMMITTED_ISOLATED', 'inventory': [f.record() for f in self.result.files],
                'trusted': False, 'authority': False, 'release_approved': False, 'authenticated': False,
                'crypto': 'CRYPTO_PROVIDER_UNAVAILABLE'}


@dataclass(frozen=True)
class RollbackPlan(CanonicalModel):
    current: DeploymentState
    anchor: InstallationReceipt
    DOMAIN = 'apexforge.rollback-plan/v1'

    def __post_init__(self):
        require(type(self.current) is DeploymentState and type(self.anchor) is InstallationReceipt
                and type(self.anchor.plan) is InstallationPlan and self.anchor.plan.mode != 'EXACT_REINSTALL'
                and self.current == self.anchor.result, 'ROLLBACK_ANCHOR_INVALID')

    @property
    def executable(self):
        return True

    def resulting_state(self):
        return self.anchor.previous

    def record(self):
        return {'current': self.current.fingerprint(), 'anchor': self.anchor.fingerprint(),
                'target': self.anchor.previous.fingerprint(), 'rollback_by_version_order': False,
                'inventory': [f.record() for f in self.anchor.previous.files]}


class IsolatedRoot:
    """Opaque, process-local active context; paths never participate in identities."""
    def __init__(self):
        raise InstallationError('INSTALLATION_ISOLATION_REQUIRED')

    @property
    def path(self):
        require(self in _ACTIVE, 'INSTALLATION_ISOLATION_REQUIRED')
        return _ACTIVE[self][0]


_ACTIVE = {}
_STATES = {}
_HISTORY = {}
_BROKEN = set()


def safe_node(path, directory=False):
    info = path.lstat()
    require(not stat.S_ISLNK(info.st_mode) and not getattr(info, 'st_file_attributes', 0) &
            getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0x400), 'INSTALLATION_DESTINATION_ESCAPE')
    require(stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode), 'INSTALLATION_PATH_CONFLICT')
    return info


@contextmanager
def isolated_root(parent, *, test_controlled=False):
    # Caller explicitly supplies a named disposable test parent, never an IDE/system root.
    require(type(parent) is type(Path()) and type(test_controlled) is bool and test_controlled and
            parent.is_absolute() and parent.name.startswith('apexforge-install-test-'), 'INSTALLATION_ISOLATION_REQUIRED')
    for component in reversed((parent,) + tuple(parent.parents)):
        safe_node(component, True)
    with tempfile.TemporaryDirectory(prefix='deployment-', dir=parent) as name:
        path = Path(name)
        root = object.__new__(IsolatedRoot)
        info = safe_node(path, True)
        _ACTIVE[root] = (path, info.st_dev, info.st_ino)
        _STATES[root] = {}
        _HISTORY[root] = set()
        try:
            yield root
        finally:
            del _ACTIVE[root]
            del _STATES[root]
            del _HISTORY[root]
            _BROKEN.discard(root)


def root_guard(root):
    require(type(root) is IsolatedRoot and root in _ACTIVE, 'INSTALLATION_ISOLATION_REQUIRED')
    path, device, inode = _ACTIVE[root]
    for component in reversed((path,) + tuple(path.parents)):
        safe_node(component, True)
    info = safe_node(path, True)
    require((info.st_dev, info.st_ino) == (device, inode), 'INSTALLATION_DESTINATION_ESCAPE')
    return path


def present(path):
    try:
        path.lstat()
        return True
    except FileNotFoundError:
        return False


def destination(root, logical):
    current = root_guard(root)
    parts = logical.split('/')
    for index, part in enumerate(parts):
        if present(current):
            safe_node(current, True)
            matches = []
            for count, item in enumerate(current.iterdir(), 1):
                require(count <= MAX_CHILDREN, 'INSTALLATION_DIRECTORY_SIZE_LIMIT')
                if item.name.casefold() == part.casefold():
                    matches.append(item.name)
            require(matches in ([], [part]), 'INSTALLATION_PATH_CONFLICT')
        current = current / part
        if present(current):
            safe_node(current, index < len(parts)-1)
    return current


def observe(root, expected, paths):
    old = {f.path.value: f.artifact.data for f in expected.files}
    for logical in paths:
        path = destination(root, logical)
        if logical not in old:
            require(not path.exists(), 'INSTALLATION_EXISTING_CONTENT_CONFLICT')
        else:
            require(path.exists(), 'INSTALLATION_STALE_STATE')
            with path.open('rb') as stream:
                data = stream.read(b.MAX_BYTES + 1)
            require(data == old[logical], 'INSTALLATION_STALE_STATE')


@dataclass(frozen=True)
class TransactionResult:
    status: str
    code: str
    receipt: InstallationReceipt | None = None
    recovery_root: str = field(default='', repr=False, compare=False)

    def __post_init__(self):
        require(type(self.status) is str and self.status in ('APPLIED', 'IDEMPOTENT', 'REJECTED', 'FAILED_RECOVERED', 'RECOVERY_FAILED'),
                'INSTALLATION_RESULT_INVALID')
        require(type(self.code) is str and type(self.recovery_root) is str and
                ((self.status in ('APPLIED', 'IDEMPOTENT') and self.code == '' and type(self.receipt) is InstallationReceipt) or
                 (self.status not in ('APPLIED', 'IDEMPOTENT') and self.receipt is None and bool(self.code))),
                'INSTALLATION_RESULT_INVALID')


def apply(plan, root):
    """Exclusive/cooperative isolated root; per-file replace plus compensating recovery.

    No crash/power-loss guarantee or hostile concurrent-filesystem guarantee.
    Recovery failure is explicit and retains only the owned scratch for inspection.
    """
    require(type(plan) in (InstallationPlan, RollbackPlan), 'INSTALLATION_PLAN_INVALID')
    if not plan.executable:
        return TransactionResult('REJECTED', 'UPGRADE_' + plan.assessment.status)
    current, result = plan.current, plan.resulting_state()
    old = {f.path.value: f.artifact.data for f in current.files}
    new = {f.path.value: f.artifact.data for f in result.files}
    paths = tuple(sorted(set(old) | set(new)))
    lock = None
    scratch = None
    made = []
    touched = []
    try:
        base = root_guard(root)
        require(root not in _BROKEN, 'INSTALLATION_RECOVERY_REQUIRED')
        lock_path = base / '.apexforge-transaction-lock'
        try:
            lock = lock_path.open('xb')
        except FileExistsError:
            return TransactionResult('REJECTED', 'INSTALLATION_BUSY')
        recorded = _STATES[root].get(current.target.fingerprint())
        require(len(_HISTORY[root]) < MAX_TRANSACTIONS and (recorded is not None or len(_STATES[root]) < MAX_FILES),
                'INSTALLATION_HISTORY_SIZE_LIMIT')
        require((recorded is None and current.identity is None) or recorded == current, 'INSTALLATION_STALE_STATE')
        if type(plan) is RollbackPlan:
            require(plan.anchor.fingerprint() in _HISTORY[root], 'ROLLBACK_ANCHOR_UNRECORDED')
        observe(root, current, paths)
        if result == current:
            receipt = InstallationReceipt(plan, current, result)
            _HISTORY[root].add(receipt.fingerprint())
            return TransactionResult('IDEMPOTENT', '', receipt)
        scratch = Path(tempfile.mkdtemp(prefix='.apexforge-install-', dir=base))
        safe_node(scratch, True)
        for index, logical in enumerate(paths):
            for prefix, values in (('old', old), ('new', new)):
                if logical in values:
                    staged = scratch / (prefix + str(index))
                    root_guard(root); safe_node(scratch, True)
                    staged.write_bytes(values[logical])
                    with staged.open('rb') as stream:
                        require(stream.read(b.MAX_BYTES+1) == values[logical], 'INSTALLATION_STAGING_MISMATCH')
        observe(root, current, paths)  # stale plan check after staging, before first mutation
        for index, logical in enumerate(paths):
            path = destination(root, logical)
            if old.get(logical) == new.get(logical):
                continue
            missing = []
            parent = path.parent
            while parent != base and not parent.exists():
                missing.append(parent); parent = parent.parent
            for parent in reversed(missing):
                root_guard(root); parent.mkdir(); made.append(parent)
            touched.append((index, logical))  # includes OS calls that move then raise in fault injection
            if logical in new:
                safe_node(scratch, True); safe_node(scratch / ('new'+str(index)))
                os.replace(scratch / ('new'+str(index)), path)
            else:
                path.unlink()
        observe(root, result, paths)
        receipt = InstallationReceipt(plan, current, result)
        _STATES[root][current.target.fingerprint()] = result
        _HISTORY[root].add(receipt.fingerprint())
        return TransactionResult('APPLIED', '', receipt)
    except (InstallationError, OSError) as exc:
        code = exc.code if isinstance(exc, InstallationError) else 'INSTALLATION_IO_FAILED'
        if not touched:
            return TransactionResult('REJECTED' if scratch is None else 'FAILED_RECOVERED', code)
        try:
            for index, logical in reversed(touched):
                path = destination(root, logical)
                if logical in old:
                    safe_node(scratch, True); safe_node(scratch / ('old'+str(index)))
                    os.replace(scratch / ('old'+str(index)), path)
                elif path.exists():
                    path.unlink()
            observe(root, current, paths)
            return TransactionResult('FAILED_RECOVERED', code)
        except (InstallationError, OSError):
            retained = str(scratch)
            scratch = None
            _BROKEN.add(root)
            return TransactionResult('RECOVERY_FAILED', 'INSTALLATION_RECOVERY_FAILED', recovery_root=retained)
    finally:
        # No recursive deletion of caller files. Scratch contains only fixed owned slots.
        if scratch is not None:
            root_guard(root); safe_node(scratch, True)
            for index in range(len(paths)):
                for prefix in ('old', 'new'):
                    slot = scratch / (prefix+str(index))
                    if slot.exists():
                        safe_node(slot); slot.unlink()
            scratch.rmdir()
        for directory in reversed(made):
            if present(directory):
                root_guard(root); safe_node(directory, True)
                if not any(directory.iterdir()):
                    directory.rmdir()
        if lock is not None:
            lock.close()
            root_guard(root); lock_path.unlink()
