"""Measurement integrity and one small real native passivity fixture; no stress."""
from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, replace
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from time import perf_counter_ns
import tracemalloc
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tooling import resource_observability as observer
from tooling.resource_observability import (
    ResourceClass, EvidenceStatus, Availability, PressureDimension as D,
    OwnershipEvidence, ResourceOwnership, ResourceSnapshot, LifecycleBoundary,
    DeltaDirection, MeasurementDelta, ObservationPathError, measured, unavailable,
    compare_snapshots, inventory_artifacts, observe_count, observe_bytes,
    observe_python_memory, observe_current_process, elapsed,
)
from tooling.trace_integration import (
    compile_with_metadata, associate_plan, execute_managed_retained,
    execute_native_retained, dispatch_native_retained,
)
from air.verify import AIRVerifier
from runtime.engine import RuntimeEngine
from workflow.air_runner import run_air_program
from apexforge.native_backend.source_mapping import build_native_with_mapping
from apexforge.native_backend.lowering_input import build_verified_air_lowering_input
from apexforge.native_backend.native_execution_contract import admit_native_profile, PROFILE
from p12_5_native_profile_contract_test import fixture, plan_for
from p12_6_3_metadata_identity_association_test import SOURCE
from p12_7_2_bounded_behavioral_equivalence_test import managed_projection, native_projection


BUILD = ROOT / "build"


def owned(scope="fixture", resource_class=ResourceClass.IRR):
    known = lambda value: OwnershipEvidence(EvidenceStatus.KNOWN, value)
    return ResourceOwnership(scope, resource_class, known("P12.8-2 test caller"),
        known("controlled observation fixture"), known("explicit test setup"),
        known("until test-owned scope exits"), known("test-owned scope exits"))


def values(snapshot):
    return {v.metric: v.value for v in snapshot.observations}


class ObservationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        BUILD.mkdir(exist_ok=True)

    def test_immutable_records_and_all_resource_classes(self):
        for kind in ResourceClass:
            owner = owned(resource_class=kind)
            record = measured(owner, D.Cb, "entries", 2, "count", "test.length")
            self.assertEqual(record, measured(owner, D.Cb, "entries", 2, "count", "test.length"))
            with self.assertRaises(FrozenInstanceError):
                record.value = 3
            with self.assertRaises(FrozenInstanceError):
                owner.owner.value = "different"
        self.assertEqual({v.value for v in ResourceClass}, {"IRR", "CER", "DHF", "SHR"})

    def test_invalid_measurement_names_units_and_sizes(self):
        good = measured(owned(), D.At, "bytes", 1, "bytes", "test")
        for change in ({"metric": "../bad"}, {"metric": ""}, {"metric": "Bad Name"},
                       {"unit": "seconds"}, {"value": -1}, {"value": True},
                       {"value": 1.2}, {"value": None}, {"volatile": 1},
                       {"dimension": "Wp"}, {"ownership": object()}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                replace(good, **change)

    def test_ownership_known_unknown_and_unavailable(self):
        unknown = OwnershipEvidence(EvidenceStatus.UNKNOWN, reason="caller custody unresolved")
        missing = OwnershipEvidence(EvidenceStatus.UNAVAILABLE, reason="owner evidence inaccessible")
        owner = replace(owned(), owner=unknown, intended_lifetime=missing)
        self.assertIs(owner.owner.status, EvidenceStatus.UNKNOWN)
        self.assertIs(owner.intended_lifetime.status, EvidenceStatus.UNAVAILABLE)
        for args in ((EvidenceStatus.KNOWN, None, None), (EvidenceStatus.UNKNOWN, "guessed", "missing"),
                     (EvidenceStatus.UNAVAILABLE, None, None)):
            with self.assertRaises(ValueError):
                OwnershipEvidence(*args)

    def test_unavailable_is_not_zero(self):
        record = unavailable(owned(), D.H, "handles", "count", "test", "unavailable")
        self.assertIsNone(record.value)
        self.assertIs(record.availability, Availability.UNAVAILABLE)
        with self.assertRaises(ValueError):
            replace(record, value=0)
        zero = measured(owned(), D.H, "handles", 0, "count", "test")
        self.assertNotEqual(ResourceSnapshot((record,)).fingerprint(), ResourceSnapshot((zero,)).fingerprint())

    def test_snapshot_order_identity_and_duplicates(self):
        a = measured(owned(), D.Tb, "records", 3, "count", "test")
        b = measured(owned(), D.Cb, "cache", 4, "count", "test")
        first, second = ResourceSnapshot((a, b)), ResourceSnapshot((b, a))
        self.assertEqual(first, second)
        self.assertEqual(first.canonical_form(), second.canonical_form())
        self.assertEqual(first.fingerprint(), second.fingerprint())
        with self.assertRaises(ValueError):
            ResourceSnapshot((a, a))
        with self.assertRaises(ValueError):
            ResourceSnapshot([a])
        with self.assertRaises(FrozenInstanceError):
            first.observations = ()

    def test_volatile_metrics_excluded_from_identity(self):
        stable = measured(owned(), D.At, "files", 1, "count", "test")
        live = measured(owned(), D.Wp, "working_set", 100, "bytes", "test", volatile=True)
        absent = unavailable(owned(), D.Wp, "working_set", "bytes", "test", "missing", volatile=True)
        snapshots = [ResourceSnapshot((stable, v)) for v in (live, replace(live, value=200), absent)]
        self.assertEqual(len({s.fingerprint() for s in snapshots}), 1)
        self.assertNotEqual(snapshots[0], snapshots[1])
        self.assertEqual(snapshots[0].fingerprint(), ResourceSnapshot((stable,)).fingerprint())

    def test_structural_deltas_no_leak_or_cleanup_verdict(self):
        records = tuple(measured(owned(), D.Cb, name, 5, "count", "test") for name in ("a", "b", "c", "d"))
        after = (replace(records[0], value=7), replace(records[1], value=3), records[2],
                 unavailable(owned(), D.Cb, "d", "count", "test", "missing"))
        delta = compare_snapshots(ResourceSnapshot(records), ResourceSnapshot(after))
        self.assertEqual({d.direction for d in delta}, set(DeltaDirection))
        self.assertEqual({d.difference for d in delta}, {2, -2, 0, None})
        self.assertFalse(any(hasattr(d, "leak") or hasattr(d, "cleanup_success") for d in delta))
        missing = compare_snapshots(ResourceSnapshot(records), ResourceSnapshot(()))
        self.assertTrue(all(d.direction is DeltaDirection.UNAVAILABLE for d in missing))
        with self.assertRaises(ValueError):
            replace(delta[0], difference=999)

    def test_filesystem_deterministic_tree_and_sizes(self):
        with tempfile.TemporaryDirectory(dir=BUILD) as tmp:
            root = Path(tmp)
            (root / "nested").mkdir()
            (root / "nested/data.bin").write_bytes(b"123")
            (root / "program.c").write_bytes(b"abcde")
            (root / "program.exe").write_bytes(b"1234567")
            first = inventory_artifacts(owned(), root, authorized_root=root)
            second = inventory_artifacts(owned(), root, authorized_root=root)
            self.assertEqual(first, second)
            self.assertEqual(first.fingerprint(), second.fingerprint())
            self.assertEqual([r.relative_path for r in first.files], ["nested/data.bin", "program.c", "program.exe"])
            self.assertEqual(values(first.snapshot), dict(files=3, total_bytes=15, generated_c_bytes=5,
                                                         native_image_bytes=7, root_present=1))
            # No content trust/execute operation: .exe is just seven supplied bytes.
            (root / "program.exe").rename(root / "renamed.exe")
            changed = inventory_artifacts(owned(), root, authorized_root=root)
            self.assertEqual(first.snapshot, changed.snapshot)
            self.assertNotEqual(first.fingerprint(), changed.fingerprint())

    def test_path_containment_parent_and_outside(self):
        with tempfile.TemporaryDirectory(dir=BUILD) as tmp:
            root = Path(tmp)
            authority = root / "allowed"
            authority.mkdir()
            for target in (root, authority / ".." / "outside", Path("relative")):
                with self.subTest(target=target), self.assertRaises(ObservationPathError):
                    inventory_artifacts(owned(), target, authorized_root=authority)

    def test_real_link_or_windows_junction_rejected(self):
        with tempfile.TemporaryDirectory(dir=BUILD) as tmp:
            root = Path(tmp)
            authority, outside = root / "allowed", root / "outside"
            authority.mkdir()
            outside.mkdir()
            link = authority / "link"
            try:
                os.symlink(outside, link, target_is_directory=True)
            except OSError:
                if os.name != "nt":
                    self.skipTest("test environment cannot create a link")
                result = subprocess.run(["cmd.exe", "/d", "/c", "mklink", "/J", str(link), str(outside)],
                                        capture_output=True)
                if result.returncode:
                    self.skipTest("test environment cannot create link/junction")
            try:
                for target in (authority, link, link / "missing", root):
                    with self.subTest(target=target), self.assertRaises(ObservationPathError):
                        inventory_artifacts(owned(), target, authorized_root=authority if target != root else root)
                with self.assertRaises(ObservationPathError):
                    inventory_artifacts(owned(), link, authorized_root=link)
                with self.assertRaises(ObservationPathError):
                    inventory_artifacts(owned(), link / "missing", authorized_root=link / "missing")
            finally:
                if link.is_symlink():
                    link.unlink()
                else:
                    os.rmdir(link)

    def test_reparse_flag_and_io_failure_explicit(self):
        class Reparse:
            st_mode = 0
            st_file_attributes = 0x400
        self.assertTrue(observer._is_link(Reparse()))
        with tempfile.TemporaryDirectory(dir=BUILD) as tmp:
            with patch.object(observer.os, "scandir", side_effect=PermissionError("denied")):
                inventory = inventory_artifacts(owned(), Path(tmp), authorized_root=Path(tmp))
            self.assertEqual(inventory.files, ())
            self.assertTrue(all(v.value is None and v.availability is Availability.UNAVAILABLE
                                for v in inventory.snapshot.observations))

    def test_lifecycle_boundary_and_residue(self):
        with tempfile.TemporaryDirectory(dir=BUILD) as tmp:
            root = Path(tmp)
            owner = owned("cleanup")
            with tempfile.TemporaryDirectory(dir=root) as child:
                target = Path(child)
                (target / "file").write_bytes(b"data")
                before = inventory_artifacts(owner, target, authorized_root=root, dimension=D.Pc)
            after = inventory_artifacts(owner, target, authorized_root=root, dimension=D.Pc)
            boundary = LifecycleBoundary("test.scope-exit", owner, before.snapshot, after.snapshot)
            self.assertEqual(values(after.snapshot)["total_bytes"], 0)
            self.assertEqual(values(after.snapshot)["root_present"], 0)
            self.assertTrue(any(d.direction is DeltaDirection.DECREASE for d in boundary.delta()))
            target.mkdir()
            (target / "residue").write_bytes(b"left")
            self.assertEqual(values(inventory_artifacts(owner, target, authorized_root=root,
                                                       dimension=D.Pc).snapshot)["total_bytes"], 4)
            with self.assertRaises(ValueError):
                LifecycleBoundary("exit", replace(owner, cleanup_boundary=OwnershipEvidence(
                    EvidenceStatus.UNKNOWN, reason="no boundary evidence")), before.snapshot, after.snapshot)

    def test_current_process_elapsed(self):
        reading = elapsed(owned(), perf_counter_ns())
        self.assertGreaterEqual(reading.value, 0)
        self.assertEqual(reading.unit, "ns")
        self.assertTrue(reading.volatile)
        with self.assertRaises(ValueError):
            elapsed(owned(), -1)
        with patch.object(observer, "perf_counter_ns", return_value=10):
            self.assertEqual(elapsed(owned(), 7).value, 3)

    def test_current_process_os_readings(self):
        readings = observe_current_process(owned("observer-process", ResourceClass.DHF))
        self.assertEqual({v.metric for v in readings}, {"working_set", "peak_working_set", "handles"})
        for reading in readings:
            self.assertTrue(reading.volatile)
            if reading.availability is Availability.AVAILABLE:
                self.assertGreaterEqual(reading.value, 0)
            else:
                self.assertIsNone(reading.value)
            print("P12_8_2_OS|" + reading.metric + "|" + reading.availability.value + "|" + str(reading.value))
        if os.name == "nt" and all(v.availability is Availability.AVAILABLE for v in readings):
            by_name = {v.metric: v.value for v in readings}
            self.assertGreaterEqual(by_name["peak_working_set"], by_name["working_set"])

    def test_os_partial_and_failed_readings(self):
        with patch.object(observer.os, "name", "nt"), patch.object(observer, "_windows_current_values", return_value={"handles": 0}):
            readings = observe_current_process(owned())
            self.assertEqual(sum(v.availability is Availability.AVAILABLE for v in readings), 1)
            self.assertEqual(next(v.value for v in readings if v.metric == "handles"), 0)
        with patch.object(observer.os, "name", "nt"), patch.object(observer, "_windows_current_values", side_effect=OSError("denied")):
            self.assertTrue(all(v.value is None for v in observe_current_process(owned())))

    def test_python_memory_explicit_session_ownership(self):
        self.assertTrue(all(v.value is None for v in observe_python_memory(owned())))
        if tracemalloc.is_tracing():
            self.skipTest("existing caller-owned tracing session; test will not interfere")
        self.assertTrue(all(v.value is None for v in observe_python_memory(owned(), enabled=True)))
        tracemalloc.start()
        try:
            buffer = bytearray(2048)
            readings = observe_python_memory(owned(), enabled=True)
            self.assertTrue(tracemalloc.is_tracing())
            self.assertTrue(all(v.availability is Availability.AVAILABLE and v.volatile for v in readings))
            self.assertGreaterEqual(readings[1].value, readings[0].value)
            self.assertEqual(len(buffer), 2048)
        finally:
            tracemalloc.stop()
        self.assertFalse(tracemalloc.is_tracing())

    def test_existing_metadata_trace_and_cache_structure(self):
        metadata = compile_with_metadata(SOURCE.encode(), "src/main.apex")
        binding = associate_plan(metadata.verified, plan_for(metadata.compiled.program), metadata)
        retained = execute_managed_retained(binding)
        original = retained.fingerprint()
        owner = owned("metadata", ResourceClass.DHF)
        records = (observe_count(owner, D.Tb, "trace_steps", retained.result.trace.steps),
                   observe_count(owner, D.Tb, "metadata_entries", metadata.compiled.source_map.entries),
                   observe_count(owner, D.Tb, "trace_collections", retained.collections),
                   observe_count(owner, D.Tb, "associations", (binding.association,)),
                   observe_bytes(owner, D.Tb, "source_bytes", metadata.content),
                   observe_count(owner, D.Cb, "retained_results", (retained,)))
        self.assertEqual(values(ResourceSnapshot(records))["trace_steps"], len(retained.result.trace.steps))
        self.assertEqual(original, retained.fingerprint())
        with self.assertRaises(ValueError):
            observe_bytes(owner, D.Tb, "invented_serialization", retained)
        with self.assertRaises(ValueError):
            observe_count(owner, D.Cb, "mutable", [])

    def test_observer_has_no_execution_or_semantic_dependencies(self):
        tree = ast.parse(Path(observer.__file__).read_text(encoding="utf-8"))
        imports = {n.module or "" for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
        imports.update(alias.name for n in ast.walk(tree) if isinstance(n, ast.Import) for alias in n.names)
        self.assertFalse(any(name.startswith(("air", "runtime", "workflow", "native_backend", "subprocess")) for name in imports))
        calls = {n.func.attr if isinstance(n.func, ast.Attribute) else n.func.id for n in ast.walk(tree)
                 if isinstance(n, ast.Call) and isinstance(n.func, (ast.Attribute, ast.Name))}
        self.assertFalse(calls & {"eval", "exec", "execute", "dispatch_native", "Popen", "OpenProcess", "read_bytes"})
        self.assertNotIn("pid", __import__("inspect").signature(observe_current_process).parameters)

    @unittest.skipUnless(os.name == "nt", "bounded native execution requires Windows x64")
    def test_real_native_artifacts_cleanup_and_semantic_passivity(self):
        program = fixture()
        verified = AIRVerifier().verify(program).require_verified()
        plan = plan_for(program)
        binding = associate_plan(verified, plan)
        admission = admit_native_profile(verified, plan)
        before_identity = (build_verified_air_lowering_input(verified).transport_fingerprint,
                           program.directives[0].id, program.principals[0].id,
                           admission.routing_fingerprint, PROFILE, binding.fingerprint())
        canonical = run_air_program(program, entry_directives=(plan.entry_directive,))
        owner = owned("native-test-scope")
        with tempfile.TemporaryDirectory(dir=BUILD, prefix="p12-8-2-") as tmp:
            root = Path(tmp)
            # Both native executions are real. Only the fallback is failure-trapped.
            with patch.object(RuntimeEngine, "execute", side_effect=AssertionError("native fallback")):
                baseline = execute_native_retained(binding, root)
                with tempfile.TemporaryDirectory(dir=root, prefix="observed-") as child:
                    target = Path(child)
                    started = perf_counter_ns()
                    mapped = build_native_with_mapping(verified, plan, target)
                    before = inventory_artifacts(owner, target, authorized_root=root, dimension=D.Pc)
                    footprint = values(before.snapshot)
                    self.assertGreater(footprint["generated_c_bytes"], 0)
                    self.assertGreater(footprint["native_image_bytes"], 0)
                    self.assertGreaterEqual(footprint["files"], 3)
                    records = (observe_bytes(owner, D.At, "receipt_bytes", mapped.artifact.receipt_json),
                               observe_bytes(owner, D.Tb, "mapping_bytes", mapped.mapping.canonical_form()),
                               observe_count(owner, D.Tb, "regions", mapped.mapping.regions), elapsed(owner, started))
                    self.assertGreater(values(ResourceSnapshot(records))["receipt_bytes"], 0)
                    # Optional OS observation cannot decide execution behavior.
                    ResourceSnapshot(observe_current_process(owner) + observe_python_memory(owner))
                    observed = dispatch_native_retained(binding, mapped)
                    observed.validate_snapshot(binding, observed.evidence)
                    self.assertEqual(before, inventory_artifacts(owner, target, authorized_root=root, dimension=D.Pc))
                after = inventory_artifacts(owner, target, authorized_root=root, dimension=D.Pc)
                boundary = LifecycleBoundary("native.test-scope-exit", owner, before.snapshot, after.snapshot)
                self.assertEqual(values(after.snapshot)["files"], 0)
                self.assertEqual(values(after.snapshot)["root_present"], 0)
                self.assertTrue(any(v.direction is DeltaDirection.DECREASE for v in boundary.delta()))
            self.assertEqual(list(root.iterdir()), [])
            observed.validate_snapshot(binding, observed.evidence)
            baseline.validate_snapshot(binding, baseline.evidence)
            self.assertEqual(baseline.evidence, observed.evidence)
            self.assertEqual(baseline.fingerprint(), observed.fingerprint())
            self.assertEqual(managed_projection(canonical), native_projection(observed.evidence.result))
            self.assertEqual(before_identity, (build_verified_air_lowering_input(verified).transport_fingerprint,
                program.directives[0].id, program.principals[0].id,
                admit_native_profile(verified, plan).routing_fingerprint, PROFILE, binding.fingerprint()))
            print("P12_8_2_REAL_NATIVE_PASSIVITY=PASS|TWO_REAL_EXECUTIONS|NO_FALLBACK")


if __name__ == "__main__":
    unittest.main(verbosity=2)
