"""P16.8 native-image evidence; only the frozen P12 owner compiles, never dispatches."""
from dataclasses import dataclass, field, InitVar
from hashlib import sha256
from pathlib import Path
import json
import struct
import tempfile

from native_backend import native_execution as owner
from native_backend.native_execution_contract import PROFILE, NativeExecutionError, admit_native_profile
from native_backend.source_mapping import emit_native_source_mapping
from tooling import release_architecture as r, release_build as b, package_artifacts as p
from tooling.domain_platform import CanonicalModel
from tooling.package_manifest import CanonicalReference, PackagePath

MAX_BYTES = b.MAX_BYTES
SOURCE_HASHES = (
    ('native_execution_contract.py', '5742C08FA80A14F889C914C41959E174B782CA45A040DDDEF3C63B002E621902'),
    ('native_execution.py', '0E112B5FAB1A2305813FB7F6DBE322A7B034248DC509CFF1B34985C0591C5876'),
    ('lowering_input.py', '701ACD1A837FCEB57D6E66080E035C53E3B2C521D734B2254C159422874521B6'),
    ('execution_plan_binding.py', '0752F0AFFC2E8EE104110915FC3D7CB2F383C974E2A68902A7567D614C3A04E4'),
    ('source_mapping.py', 'C65A0F820351C0EAD0D02EE74883BDE52445E6341265BC05F496EE99925B2374'),
)


class NativeDistributionError(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def require(condition, code):
    if not condition:
        raise NativeDistributionError(code)


def digest(data):
    require(type(data) is bytes and len(data) <= MAX_BYTES, 'NATIVE_RELEASE_SIZE_INVALID')
    return sha256(data).hexdigest().upper()


@dataclass(frozen=True)
class NativeDistributionIdentity(CanonicalModel):
    release: r.ReleaseIdentity
    sources: tuple = field(repr=False)
    profile: str = PROFILE
    target: str = 'win-x64'
    format: str = 'exe'
    DOMAIN = 'apexforge.native-distribution-identity/v1'

    def __post_init__(self):
        require(type(self.release) is r.ReleaseIdentity and self.release.baseline == r.P15_BASELINE,
                'NATIVE_RELEASE_BINDING_INVALID')
        require(type(self.profile) is str and self.profile == PROFILE, 'NATIVE_PROFILE_BINDING_INVALID')
        require(type(self.target) is str and type(self.format) is str and
                (self.target, self.format) == ('win-x64', 'exe'), 'NATIVE_TARGET_BINDING_INVALID')
        require(type(self.sources) is tuple and len(self.sources) == len(SOURCE_HASHES), 'NATIVE_SOURCE_CONTINUITY_INVALID')
        require(all(type(row) is tuple and len(row) == 2 and type(row[0]) is str and type(row[1]) is bytes
                    for row in self.sources), 'NATIVE_SOURCE_CONTINUITY_INVALID')
        rows = dict(self.sources)
        require(len(rows) == len(self.sources) and set(rows) == {name for name, _ in SOURCE_HASHES},
                'NATIVE_SOURCE_CONTINUITY_INVALID')
        require(all(digest(rows[name]) == expected for name, expected in SOURCE_HASHES), 'NATIVE_SOURCE_CONTINUITY_INVALID')
        object.__setattr__(self, 'sources', tuple(sorted(self.sources)))

    def record(self):
        return {'release': self.release.record(), 'profile': self.profile, 'target': self.target,
                'platform': 'Windows', 'architecture': 'x64', 'format': self.format,
                'source_ledger': dict(SOURCE_HASHES), 'owner': 'native_backend.native_execution.build_native',
                'contract': 'P12.5', 'whole_language_native_support': False, 'semantic_authority': 'CANONICAL_AIR'}


def inspect_pe(data):
    """Bounded PE32+ console-image inspection, not a loader or execution validator."""
    digest(data)
    require(len(data) >= 64 and data[:2] == b'MZ', 'NATIVE_PE_HEADER_INVALID')
    def unpack(fmt, offset):
        size = struct.calcsize(fmt)
        require(type(offset) is int and 0 <= offset <= len(data) - size, 'NATIVE_PE_OFFSET_INVALID')
        return struct.unpack_from(fmt, data, offset)
    pe, = unpack('<I', 60)
    require(pe >= 64 and pe <= len(data) - 24 and data[pe:pe+4] == b'PE\0\0', 'NATIVE_PE_HEADER_INVALID')
    machine, count, timestamp, _, _, optional_size, flags = unpack('<HHIIIHH', pe + 4)
    require(machine == 0x8664, 'NATIVE_MACHINE_ARCHITECTURE_INVALID')
    require(1 <= count <= 96 and flags & 2 and not flags & 0x2000, 'NATIVE_PE_HEADER_INVALID')
    opt = pe + 24
    require(optional_size >= 240 and opt + optional_size + count * 40 <= len(data), 'NATIVE_PE_OFFSET_INVALID')
    require(unpack('<H', opt)[0] == 0x20b, 'NATIVE_PE_HEADER_INVALID')
    entry, = unpack('<I', opt + 16)
    section_align, file_align = unpack('<II', opt + 32)
    image_size, headers = unpack('<II', opt + 56)
    require(512 <= file_align <= 65536 and file_align & (file_align - 1) == 0 and
            section_align >= file_align and section_align & (section_align - 1) == 0,
            'NATIVE_PE_HEADER_INVALID')
    require(opt + optional_size + count * 40 <= headers <= len(data) and headers % file_align == 0 and
            image_size > headers and image_size % section_align == 0 and unpack('<H', opt+68)[0] == 3,
            'NATIVE_PE_HEADER_INVALID')
    directory_count, = unpack('<I', opt + 108)
    require(directory_count <= 16 and 112 + directory_count * 8 <= optional_size, 'NATIVE_PE_HEADER_INVALID')
    sections = []
    raw_ranges, virtual_ranges = [], []
    for index in range(count):
        offset = opt + optional_size + index * 40
        name_raw, virtual_size, address, size, pointer, _, _, _, _, characteristics = unpack('<8sIIIIIIHHI', offset)
        try:
            name = name_raw.rstrip(b'\0').decode('ascii')
        except UnicodeError as exc:
            raise NativeDistributionError('NATIVE_PE_HEADER_INVALID') from exc
        require(bool(name) and all(32 <= ord(c) < 127 for c in name), 'NATIVE_PE_HEADER_INVALID')
        require(address % section_align == 0 and address >= headers and
                address + max(virtual_size, size) <= image_size, 'NATIVE_PE_OFFSET_INVALID')
        virtual_ranges.append((address, address + max(virtual_size, size)))
        if size:
            require(pointer >= headers and pointer % file_align == 0 and size % file_align == 0 and
                    pointer <= len(data) - size, 'NATIVE_PE_OFFSET_INVALID')
            raw_ranges.append((pointer, pointer + size))
        sections.append((name, address, virtual_size, pointer, size, characteristics,
                         digest(data[pointer:pointer+size]) if size else digest(b'')))
    for ranges in (raw_ranges, virtual_ranges):
        ordered = sorted(ranges)
        require(all(a[1] <= c[0] for a, c in zip(ordered, ordered[1:])), 'NATIVE_PE_SECTION_OVERLAP')
    require(len({s[0] for s in sections}) == count, 'NATIVE_PE_HEADER_INVALID')
    require(any(s[1] <= entry < s[1] + min(s[2], s[4]) and s[5] & 0x20000000 for s in sections),
            'NATIVE_PE_ENTRY_INVALID')
    def raw(rva, size):
        matches = [s for s in sections if s[1] <= rva and rva + size <= s[1] + s[4]]
        require(len(matches) == 1, 'NATIVE_PE_OFFSET_INVALID')
        return matches[0][3] + rva - matches[0][1]
    directories = tuple(unpack('<II', opt + 112 + index * 8) for index in range(directory_count))
    for index, (address, size) in enumerate(directories):
        require(bool(address) == bool(size), 'NATIVE_PE_OFFSET_INVALID')
        if size:
            if index == 4:  # certificate table uses a file offset, not RVA
                require(address >= headers and address <= len(data) - size, 'NATIVE_PE_OFFSET_INVALID')
            else:
                raw(address, size)
    debug = []
    if directory_count > 6 and directories[6][1]:
        address, size = directories[6]
        require(size % 28 == 0 and size // 28 <= 64, 'NATIVE_PE_OFFSET_INVALID')
        offset = raw(address, size)
        for index in range(size // 28):
            _, stamp, _, _, kind, length, rva, pointer = unpack('<IIHHIIII', offset + index * 28)
            require(length <= 65536 and pointer <= len(data) - length, 'NATIVE_PE_OFFSET_INVALID')
            if length:
                require(pointer >= headers and (not rva or raw(rva, length) == pointer), 'NATIVE_PE_OFFSET_INVALID')
            payload = data[pointer:pointer+length]
            debug.append((kind, stamp, length, digest(payload), b'RSDS' in payload))
    return {'machine': 'AMD64', 'format': 'PE32_PLUS_EXE', 'subsystem': 'CONSOLE', 'timestamp_field': timestamp,
            'entry_rva': entry, 'image_size': image_size, 'headers_size': headers,
            'sections': tuple(sections), 'directories': directories, 'debug': tuple(debug),
            'pdb_packaged': False, 'executed': False}


@dataclass(frozen=True)
class NativeReleaseEvidence(CanonicalModel):
    identity: NativeDistributionIdentity
    descriptor: r.ReleaseArtifactDescriptor
    data: bytes = field(repr=False)
    receipt: bytes = field(repr=False)
    verified: InitVar[object]
    plan: InitVar[object]
    _receipt: str = field(init=False, repr=False)
    _mapping: str = field(init=False, repr=False)
    _admission: object = field(init=False, repr=False)
    _metadata: str = field(init=False, repr=False)
    DOMAIN = 'apexforge.native-release-evidence/v1'

    def __post_init__(self, verified, plan):
        require(type(self.identity) is NativeDistributionIdentity and type(self.descriptor) is r.ReleaseArtifactDescriptor
                and self.descriptor.release == self.identity.release and self.descriptor.target == r.ReleaseTarget('native-win-x64', PROFILE)
                and self.descriptor.format == 'exe' and self.descriptor.surface_version == 'profile-v1'
                and self.descriptor.availability == 'SUPPORTED', 'NATIVE_RELEASE_BINDING_INVALID')
        admission = admit_native_profile(verified, plan)
        content, mapping = emit_native_source_mapping(verified, plan)
        require(type(self.receipt) is bytes and len(self.receipt) <= MAX_BYTES, 'NATIVE_RECEIPT_INVALID')
        try:
            record = p._parse_record(self.receipt)
        except ValueError as exc:
            raise NativeDistributionError('NATIVE_RECEIPT_INVALID') from exc
        require(set(record) == {'profile', 'air', 'routing', 'entry', 'owner_air', 'states', 'source', 'toolchain', 'options', 'image'},
                'NATIVE_RECEIPT_INVALID')
        require(owner.canonical(record).encode('utf-8') == self.receipt, 'NATIVE_RECEIPT_INVALID')
        expected = {'profile': PROFILE, 'air': admission.air_fingerprint, 'routing': admission.routing_fingerprint,
                    'entry': admission.entry, 'owner_air': admission.air_fingerprint, 'states': list(admission.state_ids),
                    'source': digest(content), 'options': list(owner.OPTIONS), 'image': digest(self.data)}
        require(all(record[k] == value and type(record[k]) is type(value) for k, value in expected.items()),
                'NATIVE_ARTIFACT_CONTINUITY_INVALID')
        require(type(record['toolchain']) is dict and 3 <= len(record['toolchain']) <= 128 and
                {'cl.exe', 'link.exe', 'kernel32.lib'} <= set(record['toolchain']), 'NATIVE_RECEIPT_INVALID')
        for name, value in record['toolchain'].items():
            require(type(name) is str and len(name) <= 128 and '/' not in name and '\\' not in name and ':' not in name,
                    'NATIVE_RECEIPT_INVALID')
            try:
                p._hash(value)
            except ValueError as exc:
                raise NativeDistributionError('NATIVE_RECEIPT_INVALID') from exc
        object.__setattr__(self, '_receipt', self.receipt.decode('utf-8'))
        object.__setattr__(self, '_mapping', mapping.fingerprint())
        object.__setattr__(self, '_admission', admission)
        object.__setattr__(self, '_metadata', owner.canonical(inspect_pe(self.data)))

    def record(self):
        return {'identity': self.identity.record(), 'descriptor': self.descriptor.record(), 'digest': digest(self.data),
                'length': len(self.data), 'receipt': json.loads(self._receipt), 'receipt_fingerprint': digest(self.receipt),
                'native_mapping': self._mapping, 'mapping_owner': 'native_backend.source_mapping',
                'physical_source_mapping': 'UNMAPPED_SOURCE', 'binary': json.loads(self._metadata),
                'container': 'EXACT_OWNER_EXE_NO_ARCHIVE', 'debug_symbols': 'NOT_RELEASE_ARTIFACT',
                'evidence_origin': 'SUPPLIED_BUILD_RECEIPT_NOT_AUTHENTICATION_OR_EXECUTION_TICKET',
                'grants_authority': False, 'grants_trust': False, 'grants_compatibility': False,
                'executed': False, 'installed': False, 'published': False, 'signed': False,
                'authenticated': False, 'crypto': 'CRYPTO_PROVIDER_UNAVAILABLE'}

    def build_artifact(self):
        ref = CanonicalReference(self.DOMAIN, 'source', self.fingerprint())
        inp = b.ReleaseBuildInput(self.identity.release, PackagePath(self.descriptor.filename), 'EXISTING_ARTIFACT',
                                 self.data, digest(self.data), ref, (ref,))
        recipe = b.ReleaseBuildRecipe('native-release-evidence', self.identity.release, 'COPY_BYTES',
                   b.ReleaseBuildEnvironment('native-inspected-bytes', 'native_backend.native_execution'),
                   (inp,), (b.ReleaseBuildOutputSlot(self.descriptor, inp.identity),), (ref,))
        return b.ReleaseBuildArtifact(recipe, self.descriptor.identity, self.data, digest(self.data))


@dataclass(frozen=True)
class LocalNativeBuildResult:
    status: str
    finding: str
    evidence: NativeReleaseEvidence | None = None

    def __post_init__(self):
        require((self.status, self.finding) == ('BUILT', '') and type(self.evidence) is NativeReleaseEvidence or
                (self.status, self.finding) == ('UNAVAILABLE', 'NATIVE_RELEASE_ENVIRONMENT_DEPENDENCY') and self.evidence is None,
                'NATIVE_BUILD_RESULT_INVALID')


def local_build(identity, descriptor, verified, plan):
    """Only build_native; no dispatch/execute, installation, or publication path."""
    require(type(identity) is NativeDistributionIdentity and type(descriptor) is r.ReleaseArtifactDescriptor
            and descriptor.release == identity.release and descriptor.target == r.ReleaseTarget('native-win-x64', PROFILE)
            and descriptor.format == 'exe' and descriptor.surface_version == 'profile-v1'
            and descriptor.availability == 'SUPPORTED',
            'NATIVE_RELEASE_BINDING_INVALID')
    admit_native_profile(verified, plan)  # reject unsupported AIR before any temp/toolchain activity
    with tempfile.TemporaryDirectory(prefix='apexforge-native-release-') as root:
        try:
            artifact = owner.build_native(verified, plan, Path(root), timeout=120)
        except NativeExecutionError as exc:
            if exc.code in ('NATIVE_PLATFORM_UNSUPPORTED', 'NATIVE_TOOLCHAIN_UNAVAILABLE'):
                return LocalNativeBuildResult('UNAVAILABLE', 'NATIVE_RELEASE_ENVIRONMENT_DEPENDENCY')
            raise
        require(type(artifact) is owner.NativeArtifact and artifact.image == Path(root).resolve() / 'program.exe',
                'NATIVE_ARTIFACT_CONTINUITY_INVALID')
        with artifact.image.open('rb') as stream:
            data = stream.read(MAX_BYTES + 1)
        require(digest(artifact.receipt_json.encode('utf-8')) == artifact.receipt_fingerprint,
                'NATIVE_RECEIPT_INVALID')
        evidence = NativeReleaseEvidence(identity, descriptor, data, artifact.receipt_json.encode('utf-8'), verified, plan)
        return LocalNativeBuildResult('BUILT', '', evidence)


def compare_packages(left, right):
    require(type(left) is NativeReleaseEvidence and type(right) is NativeReleaseEvidence, 'NATIVE_EVIDENCE_INVALID')
    context = (left.identity == right.identity and left.descriptor == right.descriptor and
               left._admission == right._admission and left._mapping == right._mapping)
    return {'context_equal': context, 'raw_bytes_equal': context and left.data == right.data,
            'structural_metadata_equal': context and left._metadata == right._metadata,
            'receipt_equal': context and left.receipt == right.receipt, 'authenticated': False}
