"""P16.8 byte-only contracts; synthetic PE cases are explicitly test fixtures."""
from dataclasses import FrozenInstanceError, replace
from pathlib import Path
import ast
import json
import struct
import subprocess
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'apexforge'))
sys.path.insert(0, str(ROOT))
from tooling import native_distribution as n, release_architecture as r, release_build as b, release_manifest as m
from native_backend.native_execution_contract import NativeExecutionError, admit_native_profile
from native_backend.source_mapping import emit_native_source_mapping
from p12_5_native_profile_contract_test import fixture, plan_for, with_path
from air.verify import AIRVerifier
from air.model import StateAssignment

FROZEN = tuple((name, subprocess.run(('git', 'show', r.P15_COMMIT + ':apexforge/native_backend/' + name),
               cwd=ROOT, check=True, capture_output=True).stdout) for name, _ in n.SOURCE_HASHES)


def identity():
    return n.NativeDistributionIdentity(r.ReleaseIdentity('native-review', 'declared-16', 'DEVELOPMENT', r.P15_BASELINE), FROZEN)


def descriptor(ident):
    return r.ReleaseArtifactDescriptor(ident.release, r.ReleaseArtifactIdentity('native-exe'),
        r.ReleaseTarget('native-win-x64', n.PROFILE), 'NATIVE_COMPONENT', 'exe', 'program.exe', 'profile-v1', 'SUPPORTED')


def program():
    p = fixture()
    return AIRVerifier().verify(p).require_verified(), plan_for(p)


def pe():
    # Minimal synthetic PE32+ inspection fixture; no compiled/executable acceptance claim.
    data = bytearray(1024)
    data[:2] = b'MZ'
    struct.pack_into('<I', data, 60, 128)
    data[128:132] = b'PE\0\0'
    struct.pack_into('<HHIIIHH', data, 132, 0x8664, 1, 123, 0, 0, 240, 2)
    opt = 152
    struct.pack_into('<H', data, opt, 0x20b)
    struct.pack_into('<I', data, opt + 16, 4096)
    struct.pack_into('<II', data, opt + 32, 4096, 512)
    struct.pack_into('<II', data, opt + 56, 8192, 512)
    struct.pack_into('<H', data, opt + 68, 3)
    struct.pack_into('<I', data, opt + 108, 16)
    struct.pack_into('<8sIIIIIIHHI', data, 392, b'.text\0\0\0', 512, 4096, 512, 512, 0, 0, 0, 0, 0x60000020)
    data[512:] = b'\x90' * 512
    return bytes(data)


def receipt(data, verified, plan):
    admission = admit_native_profile(verified, plan)
    content, _ = emit_native_source_mapping(verified, plan)
    record = {'profile': n.PROFILE, 'air': admission.air_fingerprint, 'routing': admission.routing_fingerprint,
        'entry': admission.entry, 'owner_air': admission.air_fingerprint, 'states': list(admission.state_ids),
        'source': n.digest(content), 'toolchain': {k: 'A'*64 for k in ('cl.exe', 'link.exe', 'kernel32.lib')},
        'options': list(n.owner.OPTIONS), 'image': n.digest(data)}
    return n.owner.canonical(record).encode('utf-8')


def evidence(data=None, receipt_override=None):
    ident = identity()
    verified, plan = program()
    data = pe() if data is None else data
    raw = receipt(data, verified, plan) if receipt_override is None else receipt_override
    return n.NativeReleaseEvidence(ident, descriptor(ident), data, raw, verified, plan)


def mutate(offset, fmt, value):
    data = bytearray(pe())
    struct.pack_into(fmt, data, offset, value)
    return bytes(data)


class ContractTests(unittest.TestCase):
    def error(self, code, callback):
        with self.assertRaises(n.NativeDistributionError) as failure:
            callback()
        self.assertEqual(failure.exception.code, code)

    def test_identity_and_evidence_immutable(self):
        for obj, field, value in ((identity(), 'profile', 'other'), (evidence(), 'data', b'other')):
            with self.assertRaises(FrozenInstanceError):
                setattr(obj, field, value)

    def test_exact_release_and_version_domain(self):
        ident = identity()
        self.assertNotEqual(ident.release.version, 'profile-v1')
        changed = replace(ident, release=replace(ident.release, version='different'))
        self.assertNotEqual(ident.fingerprint(), changed.fingerprint())
        verified, plan = program()
        self.error('NATIVE_RELEASE_BINDING_INVALID', lambda: n.NativeReleaseEvidence(changed, descriptor(ident), pe(), receipt(pe(), verified, plan), verified, plan))

    def test_exact_p15_baseline(self):
        self.error('NATIVE_RELEASE_BINDING_INVALID', lambda: replace(identity(), release=replace(identity().release,
             baseline=replace(r.P15_BASELINE, commit='0'*40))))

    def test_profile_aliases_rejected(self):
        for profile in ('win-x64', n.PROFILE + 'extra', '*', None):
            self.error('NATIVE_PROFILE_BINDING_INVALID', lambda: replace(identity(), profile=profile))

    def test_targets_and_formats_exact(self):
        for target in ('linux-x64', 'win-arm64', 'win-x86'):
            self.error('NATIVE_TARGET_BINDING_INVALID', lambda: replace(identity(), target=target))
        self.error('NATIVE_TARGET_BINDING_INVALID', lambda: replace(identity(), format='dll'))
        class HostileTarget:
            def __eq__(self, other):
                raise AssertionError('caller equality must not run')
        self.error('NATIVE_TARGET_BINDING_INVALID', lambda: replace(identity(), target=HostileTarget()))

    def test_source_bytes_exact_and_order_independent(self):
        self.assertEqual(identity().fingerprint(), replace(identity(), sources=tuple(reversed(FROZEN))).fingerprint())
        changed = ((FROZEN[0][0], FROZEN[0][1]+b'\n'),) + FROZEN[1:]
        self.error('NATIVE_SOURCE_CONTINUITY_INVALID', lambda: replace(identity(), sources=changed))

    def test_source_missing_duplicates_wrong_types(self):
        for rows in (FROZEN[:-1], FROZEN[:-1]+(FROZEN[0],), list(FROZEN), (('other', b''),)*5):
            self.error('NATIVE_SOURCE_CONTINUITY_INVALID', lambda: replace(identity(), sources=rows))

    def test_p16_1_exe_format_owning_correction(self):
        self.assertEqual(descriptor(identity()).format, 'exe')
        self.assertEqual(next(row[2] for row in r.SURFACES if row[0]=='native-win-x64'), ('dll', 'exe'))
        self.assertFalse(identity().record()['whole_language_native_support'])

    def test_unsupported_air_before_process_or_temp(self):
        p = with_path(fixture(), assignments=(StateAssignment('state:value', 'add_int', 1),))
        verified = AIRVerifier().verify(p).require_verified()
        with patch.object(n.tempfile, 'TemporaryDirectory', side_effect=AssertionError('no temp')), patch.object(n.owner, 'build_native', side_effect=AssertionError('no compiler')):
            with self.assertRaises(NativeExecutionError):
                n.local_build(identity(), descriptor(identity()), verified, plan_for(p))

    def test_wrong_descriptor_before_build(self):
        verified, plan = program()
        with patch.object(n.owner, 'build_native', side_effect=AssertionError('invalid descriptor must not build')):
            self.error('NATIVE_RELEASE_BINDING_INVALID', lambda: n.local_build(identity(),
                replace(descriptor(identity()), surface_version='other-profile-version'), verified, plan))

    def test_air_source_mapping_owner_continuity(self):
        e = evidence()
        verified, plan = program()
        _, mapping = emit_native_source_mapping(verified, plan)
        self.assertEqual(e.record()['native_mapping'], mapping.fingerprint())
        self.assertEqual(e.record()['physical_source_mapping'], 'UNMAPPED_SOURCE')
        self.assertEqual(e.record()['receipt']['air'], admit_native_profile(verified, plan).air_fingerprint)

    def test_receipt_rejects_substitution_dimensions(self):
        e = evidence()
        for key in ('profile', 'air', 'routing', 'entry', 'source', 'image', 'owner_air'):
            rec = json.loads(e.receipt)
            rec[key] = 'other'
            self.error('NATIVE_ARTIFACT_CONTINUITY_INVALID', lambda: evidence(receipt_override=n.owner.canonical(rec).encode()))

    def test_receipt_exact_options_and_states(self):
        for key in ('options', 'states'):
            rec = json.loads(evidence().receipt)
            rec[key] = []
            self.error('NATIVE_ARTIFACT_CONTINUITY_INVALID', lambda: evidence(receipt_override=n.owner.canonical(rec).encode()))

    def test_receipt_canonical_schema_toolchain_and_duplicates(self):
        raw = evidence().receipt
        for rec in ({**json.loads(raw), 'unknown': 1}, {**json.loads(raw), 'toolchain': {}},
                    {**json.loads(raw), 'toolchain': {'cl.exe':'invalid','link.exe':'A'*64,'kernel32.lib':'A'*64}}):
            self.error('NATIVE_RECEIPT_INVALID', lambda: evidence(receipt_override=n.owner.canonical(rec).encode()))
        for data in (raw+b'\n', b'{"profile":1,"profile":2}', b'\xff', b'{}'):
            self.error('NATIVE_RECEIPT_INVALID', lambda: evidence(receipt_override=data))

    def test_byte_backed_digest_length_content_identity(self):
        a = evidence()
        other = bytearray(pe()); other[-1] = 1
        c = evidence(bytes(other))
        self.assertEqual(a.record()['length'], 1024)
        self.assertEqual(a.record()['digest'], n.digest(a.data))
        self.assertNotEqual(a.fingerprint(), c.fingerprint())
        self.error('NATIVE_ARTIFACT_CONTINUITY_INVALID', lambda: evidence(bytes(other), a.receipt))

    def test_pe32_console_amd64(self):
        metadata = n.inspect_pe(pe())
        self.assertEqual((metadata['machine'], metadata['format'], metadata['subsystem']), ('AMD64','PE32_PLUS_EXE','CONSOLE'))

    def test_invalid_signatures_and_offsets(self):
        for data in (b'', b'bad', b'ZZ'+pe()[2:], mutate(60,'<I',0xffffffff)):
            self.error('NATIVE_PE_HEADER_INVALID', lambda: n.inspect_pe(data))

    def test_machine_optional_header_and_dll_rejected(self):
        self.error('NATIVE_MACHINE_ARCHITECTURE_INVALID', lambda: n.inspect_pe(mutate(132,'<H',0x14c)))
        for offset, value in ((152,0x10b),(150,0x2002)):
            self.error('NATIVE_PE_HEADER_INVALID', lambda: n.inspect_pe(mutate(offset,'<H',value)))

    def test_section_bounds_and_entry(self):
        self.error('NATIVE_PE_OFFSET_INVALID', lambda: n.inspect_pe(mutate(412,'<I',999999)))
        self.error('NATIVE_PE_ENTRY_INVALID', lambda: n.inspect_pe(mutate(168,'<I',8191)))

    def test_section_overlap(self):
        data = bytearray(pe()); struct.pack_into('<H',data,134,2); data[432:472]=data[392:432]
        self.error('NATIVE_PE_SECTION_OVERLAP', lambda:n.inspect_pe(bytes(data)))

    def test_directory_bounds(self):
        self.error('NATIVE_PE_HEADER_INVALID', lambda:n.inspect_pe(mutate(260,'<I',17)))
        data=bytearray(pe()); struct.pack_into('<II',data,264,999999,10)
        self.error('NATIVE_PE_OFFSET_INVALID', lambda:n.inspect_pe(bytes(data)))

    def test_debug_offsets_bounded(self):
        data=bytearray(pe()); struct.pack_into('<II',data,264+6*8,4096,28)
        struct.pack_into('<IIHHIIII',data,512,0,0,0,0,2,32,0,0xffffffff)
        self.error('NATIVE_PE_OFFSET_INVALID', lambda:n.inspect_pe(bytes(data)))

    def test_size_and_count_limits(self):
        self.error('NATIVE_RELEASE_SIZE_INVALID', lambda:n.inspect_pe(b'x'*(n.MAX_BYTES+1)))
        self.error('NATIVE_PE_HEADER_INVALID', lambda:n.inspect_pe(mutate(134,'<H',97)))

    def test_receipt_bound_preserves_frozen_unicode_state_limit(self):
        p = fixture()
        p = replace(p, states=tuple(replace(p.states[0], id='state:'+str(i)+'\U0001f642'*240) for i in range(256)))
        p = with_path(p, assignments=(StateAssignment(p.states[0].id, 'set_int', 1),))
        verified = AIRVerifier().verify(p).require_verified()
        plan = plan_for(p)
        raw = receipt(pe(), verified, plan)
        self.assertGreater(len(raw), 65536)
        ident = identity()
        e = n.NativeReleaseEvidence(ident, descriptor(ident), pe(), raw, verified, plan)
        self.assertEqual(len(e.record()['receipt']['states']), 256)

    def test_debug_symbol_and_container_policy(self):
        rec=evidence().record()
        self.assertEqual(rec['container'],'EXACT_OWNER_EXE_NO_ARCHIVE')
        self.assertEqual(rec['debug_symbols'],'NOT_RELEASE_ARTIFACT')
        self.assertFalse(rec['binary']['pdb_packaged'])

    def test_independent_reproducibility(self):
        a,c=evidence(),evidence()
        self.assertIsNot(a,c)
        self.assertEqual(a.fingerprint(),c.fingerprint())
        self.assertTrue(n.compare_packages(a,c)['raw_bytes_equal'])
        self.assertTrue(n.compare_packages(a,c)['receipt_equal'])

    def test_reproducibility_content_and_context_mismatch(self):
        data=bytearray(pe());data[-1]=1
        result=n.compare_packages(evidence(),evidence(bytes(data)))
        self.assertFalse(result['raw_bytes_equal']);self.assertFalse(result['structural_metadata_equal'])
        verified,plan=program(); e=evidence(); ident=replace(identity(),release=replace(identity().release,version='other'))
        c=n.NativeReleaseEvidence(ident,descriptor(ident),e.data,e.receipt,verified,plan)
        self.assertFalse(n.compare_packages(e,c)['context_equal'])

    def test_manifest_integration_existing_owners(self):
        e=evidence();artifact=e.build_artifact()
        self.assertEqual(artifact.data,e.data)
        self.assertEqual(artifact.recipe.inputs[0].source.fingerprint,e.fingerprint())
        architecture=r.ReleaseArtifactMatrix(e.identity.release,(e.descriptor,))
        artifacts=b.ReleaseArtifactSet(e.identity.release,(artifact.recipe,),(artifact,))
        sums=m.ReleaseChecksumSet(e.identity.release,m.reference(architecture),(m.checksum_for(artifact),))
        lineage=m.required_lineage(architecture,artifacts,sums)
        provenance=m.ReleaseProvenanceBundle(e.identity.release,tuple(m.ReleaseProvenanceRecord('r'+str(i),e.identity.release,kind,subject,predecessors)
                    for i,(kind,subject,predecessors) in enumerate(lineage)))
        self.assertEqual(m.ReleaseManifest(architecture,artifacts,sums,provenance).evaluate()[0],'COMPLETE')

    def test_no_authority_trust_compatibility_execution(self):
        rec=evidence().record()
        for field in ('grants_authority','grants_trust','grants_compatibility','executed','installed','published','signed','authenticated'):
            self.assertFalse(rec[field])
        self.assertEqual(rec['crypto'],'CRYPTO_PROVIDER_UNAVAILABLE')

    def test_dispatch_not_called(self):
        with patch.object(n.owner,'execute_native',side_effect=AssertionError('no execute')), patch.object(n.owner,'dispatch_native',side_effect=AssertionError('no dispatch')):
            evidence().build_artifact()

    def test_environment_unavailable_no_fake_artifact(self):
        verified,plan=program()
        with patch.object(n.owner,'build_native',side_effect=NativeExecutionError('NATIVE_TOOLCHAIN_UNAVAILABLE','unavailable')):
            result=n.local_build(identity(),descriptor(identity()),verified,plan)
        self.assertEqual(result.status,'UNAVAILABLE');self.assertIsNone(result.evidence)

    def test_build_failure_not_silently_unavailable(self):
        verified,plan=program()
        with patch.object(n.owner,'build_native',side_effect=NativeExecutionError('NATIVE_BUILD_FAILED','failed')):
            with self.assertRaises(NativeExecutionError):n.local_build(identity(),descriptor(identity()),verified,plan)

    def test_local_owner_build_bytes_and_cleanup(self):
        verified,plan=program();observed=[]
        def build(v,p,directory,timeout):
            self.assertEqual(timeout,120);self.assertEqual(v,verified)
            observed.append(directory);image=directory/'program.exe';image.write_bytes(pe())
            raw=receipt(pe(),v,p)
            return n.owner.NativeArtifact(image,raw.decode(),n.digest(raw),object())
        with patch.object(n.owner,'build_native',side_effect=build):
            result=n.local_build(identity(),descriptor(identity()),verified,plan)
        self.assertEqual(result.status,'BUILT');self.assertFalse(observed[0].exists())

    def test_diagnostics_structured_deterministic(self):
        for _ in range(2):self.error('NATIVE_PE_HEADER_INVALID',lambda:n.inspect_pe(b'bad'))

    def test_substantial_iterative_inspection(self):
        left=tuple(n.inspect_pe(pe()) for _ in range(1000))
        right=tuple(n.inspect_pe(pe()) for _ in range(1000))
        self.assertEqual(left,right)

    def test_static_security_audit(self):
        tree=ast.parse((ROOT/'apexforge/tooling/native_distribution.py').read_text())
        imports={node.module for node in ast.walk(tree) if isinstance(node,ast.ImportFrom)}|{a.name for node in ast.walk(tree) if isinstance(node,ast.Import) for a in node.names}
        self.assertFalse(imports & {'ctypes','socket','requests','urllib','subprocess','pickle','os'})
        calls={node.func.attr if isinstance(node.func,ast.Attribute) else node.func.id for node in ast.walk(tree) if isinstance(node,ast.Call) and isinstance(node.func,(ast.Attribute,ast.Name))}
        self.assertFalse(calls & {'execute_native','dispatch_native','Popen','run','eval','exec','WinDLL','rglob','extractall','install','publish'})
        self.assertEqual(sum(isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and node.func.attr=='build_native' for node in ast.walk(tree)),1)


if __name__=='__main__':unittest.main(verbosity=2)
