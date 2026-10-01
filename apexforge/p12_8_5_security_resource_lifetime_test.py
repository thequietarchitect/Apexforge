"""Defensive lifetime composition within trusted native-v1 custody contracts."""
from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import weakref

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from air.model import StateAssignment
from air.verify import AIRVerifier
from runtime.engine import RuntimeEngine
from workflow.air_runner import run_air_program
from apexforge.native_backend import native_execution as native
from apexforge.native_backend.native_execution_contract import NativeExecutionError, PROFILE, admit_native_profile
from apexforge.native_backend.source_mapping import build_native_with_mapping, emit_native_source_mapping
from tooling.trace_integration import associate_plan, dispatch_native_retained
from tooling.resource_observability import (
    ResourceClass, EvidenceStatus, OwnershipEvidence, ResourceOwnership,
    ResourceSnapshot, PressureDimension as D, Availability, ObservationPathError,
    inventory_artifacts, observe_count, LifecycleBoundary,
)
from p12_5_native_profile_contract_test import fixture, plan_for, with_path
from p12_7_2_bounded_behavioral_equivalence_test import managed_projection, native_projection

BUILD = ROOT / "build"


class Lifetime(Enum):
    ACTIVE = "ACTIVE"
    RETAINED_AUTHORIZED = "RETAINED_AUTHORIZED"
    RELEASED = "RELEASED"
    STALE = "STALE"


@dataclass(frozen=True)
class LifetimeWitness:
    """Test evidence label, never an admission/authority implementation."""
    scope: str
    state: Lifetime
    snapshot: ResourceSnapshot


def ownership(scope, kind=ResourceClass.IRR):
    known = lambda value: OwnershipEvidence(EvidenceStatus.KNOWN, value)
    return ResourceOwnership(scope, kind, known("P12.8-5 test scope"),
        known("validate native artifact custody and release"), known("explicit test invocation"),
        known("one native sample or explicit retained evidence ledger"), known("owned scope exits / references released"))


def values(snapshot):
    return {v.metric: v.value for v in snapshot.observations}


def bound(program):
    verified = AIRVerifier().verify(program).require_verified()
    plan = plan_for(program)
    return associate_plan(verified, plan)


def other_principal(program):
    principal = replace(program.principals[0], id="principal:other")
    return replace(program, principals=(principal,),
                   directives=(replace(program.directives[0], principal=principal.id),))


class SecurityLifetimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        BUILD.mkdir(exist_ok=True)

    def test_three_real_lifecycles_substitution_release_and_retained_binding(self):
        a = fixture()
        b = with_path(a, assignments=(StateAssignment("state:value", "set_int", 99),))
        programs = (a, b, a)  # Identical content may legitimately recur; custody must be fresh.
        bindings = tuple(bound(program) for program in programs)
        principal_binding = bound(other_principal(a))
        self.assertNotEqual(bindings[0].association.fingerprint(), principal_binding.association.fingerprint())
        baseline_issued = len(native._issued)
        ledger, old_roots, tickets, witnesses = [], [], [], []
        with tempfile.TemporaryDirectory(prefix="security-lifetime-", dir=BUILD) as parent_name:
            parent = Path(parent_name)
            sentinel = parent / "sentinel.bin"
            sentinel.write_bytes(b"neighbor outside child custody")
            for index, binding in enumerate(bindings):
                canonical = run_air_program(binding.verified.program, entry_directives=(binding.plan.entry_directive,))
                expected = managed_projection(canonical)
                different = bindings[1] if index != 1 else bindings[0]
                with patch.object(RuntimeEngine, "execute", side_effect=AssertionError("native fallback")):
                    with tempfile.TemporaryDirectory(prefix="owned-", dir=parent) as child_name:
                        child = Path(child_name)
                        owner = ownership("native-lifecycle-%d" % index)
                        self.assertFalse(any(p.exists() for p in old_roots))
                        self.assertTrue(all(t() is None for t in tickets))
                        self.assertEqual(tuple(child.iterdir()), ())
                        mapped = build_native_with_mapping(binding.verified, binding.plan, child)
                        self.assertEqual(mapped.artifact.image.parent, child)
                        ticket = weakref.ref(mapped.artifact._ticket)
                        tickets.append(ticket)
                        self.assertEqual(len(native._issued), baseline_issued + 1)
                        active = inventory_artifacts(owner, child, authorized_root=parent)
                        self.assertTrue(all(v.availability is Availability.AVAILABLE for v in active.snapshot.observations))
                        self.assertGreater(values(active.snapshot)["native_image_bytes"], 0)
                        witnesses.append(LifetimeWitness(owner.scope, Lifetime.ACTIVE, active.snapshot))

                        # Negative seams prohibit actual launch; positives below are real execution.
                        with patch.object(native, "_run", side_effect=AssertionError("untrusted image launched")):
                            for mismatched in (different, principal_binding):
                                if mismatched == binding:
                                    continue
                                with self.assertRaises(NativeExecutionError) as failure:
                                    native.dispatch_native(mapped.artifact, mismatched.verified, mismatched.plan)
                                self.assertEqual(failure.exception.code, "NATIVE_PROVENANCE_MISMATCH")
                            with self.assertRaises(ValueError):
                                native.dispatch_native(mapped.artifact, binding.verified, different.plan)
                            receipt = json.loads(mapped.artifact.receipt_json)
                            for field, value in (("profile", "not-the-native-profile"), ("routing", "0" * 64)):
                                changed = native.canonical(dict(receipt, **{field: value}))
                                forged = replace(mapped.artifact, receipt_json=changed,
                                    receipt_fingerprint=native.digest(changed.encode()))
                                with self.assertRaises(NativeExecutionError) as failure:
                                    native.dispatch_native(forged, binding.verified, binding.plan)
                                self.assertEqual(failure.exception.code, "NATIVE_ARTIFACT_INVALID")
                                del forged
                            if ledger:
                                prior = ledger[-1][1].evidence
                                forged = replace(mapped.artifact, receipt_json=prior.receipt_json,
                                    receipt_fingerprint=prior.result.input_fingerprint)
                                with self.assertRaises(NativeExecutionError):
                                    native.dispatch_native(forged, binding.verified, binding.plan)
                                del forged
                            original = mapped.artifact.image.read_bytes()
                            try:
                                mapped.artifact.image.write_bytes(original + b"owned-test-substitution")
                                with self.assertRaises(NativeExecutionError) as failure:
                                    native.dispatch_native(mapped.artifact, binding.verified, binding.plan)
                                self.assertEqual(failure.exception.code, "NATIVE_ARTIFACT_SUBSTITUTED")
                            finally:
                                mapped.artifact.image.write_bytes(original)

                        _, wrong_map = emit_native_source_mapping(different.verified, different.plan)
                        with patch.object(native, "dispatch_native", side_effect=AssertionError("stale mapping dispatched")):
                            with self.assertRaises(ValueError):
                                dispatch_native_retained(binding, replace(mapped, mapping=wrong_map,
                                    mapping_fingerprint=wrong_map.fingerprint()))
                            with self.assertRaises(ValueError):
                                replace(binding, association=different.association).validate()

                        retained = dispatch_native_retained(binding, mapped)
                        self.assertEqual(native_projection(retained.evidence.result), expected)
                        retained.validate_snapshot(binding, retained.evidence)
                        self.assertEqual(json.loads(retained.evidence.receipt_json)["profile"], PROFILE)
                        self.assertEqual(admit_native_profile(binding.verified, binding.plan).profile, PROFILE)
                        self.assertEqual(inventory_artifacts(owner, child, authorized_root=parent), active)
                    # Files expired even while the wrapper is still intentionally reachable.
                    missing = inventory_artifacts(owner, child, authorized_root=parent, dimension=D.Pc)
                    self.assertEqual(values(missing.snapshot)["root_present"], 0)
                    self.assertEqual(values(missing.snapshot)["files"], 0)
                    before = ResourceSnapshot(tuple(replace(v, dimension=D.Pc) for v in active.snapshot.observations))
                    LifecycleBoundary("owned-native-root-exit", owner, before, missing.snapshot)
                    witnesses.append(LifetimeWitness(owner.scope, Lifetime.RELEASED, missing.snapshot))
                    with patch.object(native, "_run", side_effect=AssertionError("released image launched")):
                        with self.assertRaises(NativeExecutionError) as failure:
                            native.dispatch_native(mapped.artifact, binding.verified, binding.plan)
                        self.assertEqual(failure.exception.code, "NATIVE_ARTIFACT_UNAVAILABLE")
                    with self.assertRaises(FileNotFoundError):
                        mapped.validate(binding.verified, binding.plan)
                    del mapped
                    self.assertIsNone(ticket())
                    self.assertEqual(len(native._issued), baseline_issued)
                    self.assertEqual(sentinel.read_bytes(), b"neighbor outside child custody")
                    retained.validate_snapshot(binding, retained.evidence)  # Evidence is intentionally persistent.
                    with self.assertRaises(ValueError):
                        retained.validate_snapshot(different, retained.evidence)
                    with self.assertRaises(ValueError):
                        replace(retained, post=replace(retained.post, result_fingerprint="0" * 64)).validate_snapshot(binding, retained.evidence)
                    if ledger:
                        previous_binding, previous = ledger[-1]
                        with self.assertRaises(ValueError):
                            previous.validate_snapshot(binding, retained.evidence)
                        with self.assertRaises(ValueError):
                            replace(retained, collection=previous.collection).validate_snapshot(binding, retained.evidence)
                        previous.validate_snapshot(previous_binding, previous.evidence)
                    retained_snapshot = ResourceSnapshot((observe_count(ownership("retained-evidence", ResourceClass.CER),
                        D.Tb, "native_records", retained.collection.records),))
                    witnesses.append(LifetimeWitness(owner.scope, Lifetime.RETAINED_AUTHORIZED, retained_snapshot))
                    witnesses.append(LifetimeWitness(owner.scope, Lifetime.STALE, missing.snapshot))
                    ledger.append((binding, retained))
                    old_roots.append(child)
                    print("P12_8_5_NATIVE_LIFECYCLE=%d|PASS|MISSING_IMAGE_REJECTED|TICKET_RELEASED|RETAINED_VALID" % (index + 1), flush=True)
            self.assertEqual(len(ledger), 3)
            self.assertEqual(len(witnesses), 12)
            self.assertEqual(set(w.state for w in witnesses), set(Lifetime))
            self.assertEqual(tuple(p.name for p in parent.iterdir()), ("sentinel.bin",))
            for binding, retained in ledger:
                retained.validate_snapshot(binding, retained.evidence)

    def test_observation_cannot_authorize_native_dispatch(self):
        binding = bound(fixture())
        snapshot = ResourceSnapshot((observe_count(ownership("measurement"), D.At, "files", ()),))
        with patch.object(native, "_run", side_effect=AssertionError("measurement launched")), \
             patch.object(RuntimeEngine, "execute", side_effect=AssertionError("measurement fallback")):
            with self.assertRaises(NativeExecutionError):
                native.dispatch_native(snapshot, binding.verified, binding.plan)
        self.assertFalse(hasattr(snapshot, "execute"))

    def test_composed_observer_absence_escape_redirect_and_confined_cleanup(self):
        with tempfile.TemporaryDirectory(prefix="observer-security-", dir=BUILD) as top_name:
            top = Path(top_name)
            outside = top / "neighbor"
            outside.mkdir()
            sentinel = outside / "sentinel.bin"
            sentinel.write_bytes(b"untouched")
            with tempfile.TemporaryDirectory(prefix="owned-", dir=top) as owned_name:
                root = Path(owned_name)
                owner = ownership("observer-security")
                for path in (outside, root / ".." / "neighbor"):
                    with self.assertRaises(ObservationPathError):
                        inventory_artifacts(owner, path, authorized_root=root)
                missing = inventory_artifacts(owner, root / "missing", authorized_root=root)
                present = inventory_artifacts(owner, root, authorized_root=root)
                self.assertEqual(values(missing.snapshot)["root_present"], 0)
                self.assertEqual(values(present.snapshot)["root_present"], 1)
                self.assertNotEqual(missing.snapshot.fingerprint(), present.snapshot.fingerprint())
                inert = root / "inert.exe"
                inert.write_bytes(b"not an executable")
                with patch.object(subprocess, "Popen", side_effect=AssertionError("observer executed a file")):
                    self.assertEqual(values(inventory_artifacts(owner, root, authorized_root=root).snapshot)["files"], 1)
                link = root / "redirect"
                try:
                    os.symlink(outside, link, target_is_directory=True)
                except OSError:
                    if os.name != "nt":
                        self.skipTest("UNSUPPORTED_TARGET: controlled link creation unavailable")
                    result = subprocess.run(["cmd.exe", "/d", "/c", "mklink", "/J", str(link), str(outside)], capture_output=True)
                    if result.returncode:
                        self.skipTest("ENVIRONMENTAL_CONSTRAINT: controlled junction creation unavailable")
                try:
                    for target, authority in ((root, root), (link, root), (link, link), (link / "missing", link)):
                        with self.assertRaises(ObservationPathError):
                            inventory_artifacts(owner, target, authorized_root=authority)
                finally:
                    # Remove only the redirect itself; never traverse/remove its neighbor target.
                    if link.is_symlink():
                        link.unlink()
                    else:
                        os.rmdir(link)
                self.assertEqual(sentinel.read_bytes(), b"untouched")
            self.assertFalse(root.exists())
            self.assertEqual(sentinel.read_bytes(), b"untouched")


if __name__ == "__main__":
    unittest.main(verbosity=2)
