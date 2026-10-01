"""Fixed-workload Scale A/B observations; sequential native builds, no Scale C."""
from __future__ import annotations

import ast
from dataclasses import dataclass, FrozenInstanceError, replace
import json
import os
from pathlib import Path
from statistics import median
import sys
import tempfile
from time import perf_counter_ns
import tracemalloc
import unittest
from unittest.mock import patch
import weakref

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tooling.resource_observability import (
    ResourceClass, EvidenceStatus, OwnershipEvidence, ResourceOwnership,
    Availability, PressureDimension as D, ResourceSnapshot, LifecycleBoundary,
    DeltaDirection, observe_count, observe_bytes, observe_current_process,
    observe_python_memory, inventory_artifacts, compare_snapshots, elapsed, unavailable,
)
from tooling.trace_integration import (
    associate_plan, execute_managed_retained, dispatch_native_retained, managed_result_fingerprint,
)
from air.verify import AIRVerifier
from runtime.engine import RuntimeEngine
from workflow.air_runner import run_air_program, build_default_context
from apexforge.native_backend import native_execution as native
from apexforge.native_backend.source_mapping import build_native_with_mapping
from apexforge.native_backend.lowering_input import build_verified_air_lowering_input
from apexforge.native_backend.native_execution_contract import admit_native_profile, PROFILE
from p12_5_native_profile_contract_test import fixture, plan_for
from p12_7_2_bounded_behavioral_equivalence_test import managed_projection, native_projection


BUILD = ROOT / "build"


def ownership(scope, kind, owner, purpose, lifetime, boundary):
    known = lambda value: OwnershipEvidence(EvidenceStatus.KNOWN, value)
    return ResourceOwnership(scope, kind, known(owner), known(purpose),
                             known("explicit P12.8-3 test invocation"), known(lifetime), known(boundary))


PROCESS = ownership("current-python", ResourceClass.DHF, "current Python test process",
    "aggregate process readings, constituent owners unresolved", "test process lifetime", "process exit")
ARTIFACTS = ownership("native-build-root", ResourceClass.IRR, "P12.8-3 test-owned TemporaryDirectory",
    "one fresh native build/dispatch", "one pulse through dispatch/provenance validation", "temporary child scope exits")
PRODUCTS = ownership("pulse-products", ResourceClass.DHF, "P12.8-3 pulse function",
    "owner results, context and artifact wrappers for validation", "one pulse", "explicit local reference release")
ISSUANCE = ownership("native-issuance", ResourceClass.DHF, "native backend weak issuance table",
    "current-process artifact admission", "while artifact ticket is reachable", "last artifact/ticket reference released")
REPORT = ownership("test-evidence-ledger", ResourceClass.DHF, "P12.8-3 sequence test",
    "bounded immutable measurement records, never live owner products", "declared sequence/test lifetime", "test returns")


def metric_values(snapshot):
    return {v.metric: v.value for v in snapshot.observations}


def live_readings(enabled):
    return ResourceSnapshot(observe_current_process(PROCESS) + observe_python_memory(PROCESS, enabled=enabled))


def issuance_count():
    # The only process-retained artifact registry in this path; no cache created.
    return observe_count(ISSUANCE, D.Cb, "issued_artifacts", tuple(native._issued.keys()))


def root_snapshot(root):
    inventory = inventory_artifacts(ARTIFACTS, root, authorized_root=root, dimension=D.Pc)
    if any(v.availability is not Availability.AVAILABLE for v in inventory.snapshot.observations):
        raise AssertionError("MEASUREMENT_GAP: test-owned root inventory unavailable")
    # Directory entry count catches even empty orphan directories, unlike file totals.
    return ResourceSnapshot(inventory.snapshot.observations + (
        observe_count(ARTIFACTS, D.Pc, "root_entries", tuple(root.iterdir())),))


@dataclass(frozen=True)
class Pulse:
    path: str
    identities: tuple
    projection: tuple
    provenance: tuple
    pre: ResourceSnapshot
    post: ResourceSnapshot
    footprint: ResourceSnapshot
    release: ResourceSnapshot
    artifacts: ResourceSnapshot | None
    residue: ResourceSnapshot | None
    timing: object

    def deterministic_evidence(self):
        return (self.identities, self.projection, self.provenance, self.footprint.fingerprint(),
                self.release.fingerprint(), None if self.artifacts is None else self.artifacts.fingerprint(),
                None if self.residue is None else self.residue.fingerprint())


class ContinuityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        BUILD.mkdir(exist_ok=True)
        cls.program = fixture()  # P12.7 repeated_overwrite_untouched, two states/two stores.
        cls.verified = AIRVerifier().verify(cls.program).require_verified()
        cls.plan = plan_for(cls.program)
        cls.binding = associate_plan(cls.verified, cls.plan)
        cls.canonical = run_air_program(cls.program, entry_directives=(cls.plan.entry_directive,))
        cls.expected = managed_projection(cls.canonical)

    def stability(self):
        admission = admit_native_profile(self.verified, self.plan)
        return (build_verified_air_lowering_input(self.verified).transport_fingerprint,
                self.program.directives[0].id, self.program.principals[0].id,
                admission.routing_fingerprint, admission.profile, self.binding.fingerprint())

    def pulse(self, path, root, *, python_enabled=False):
        identities = self.stability()
        pre = live_readings(python_enabled)
        initial_issuance = issuance_count()
        started = perf_counter_ns()
        retained = mapped = context = runtime = None
        artifacts = residue = None
        if path == "canonical":
            result = run_air_program(self.program, entry_directives=(self.plan.entry_directive,))
            footprint = ResourceSnapshot((
                observe_count(PRODUCTS, D.Tb, "trace_steps", result.trace.steps),
                observe_count(PRODUCTS, D.Tb, "diagnostics", result.diagnostics),
                unavailable(PRODUCTS, D.Tb, "trace_canonical_bytes", "bytes", "existing.Trace",
                            "no public canonical textual representation"),))
            projection = managed_projection(result)
            provenance = (managed_result_fingerprint(result),)
        elif path == "managed-retained":
            context, runtime = build_default_context(self.program), RuntimeEngine()
            retained = execute_managed_retained(self.binding, context=context, runtime=runtime)
            retained.validate(self.binding, context, runtime, self.canonical)
            result = retained.result
            footprint = ResourceSnapshot((
                observe_count(PRODUCTS, D.Tb, "trace_steps", result.trace.steps),
                observe_count(PRODUCTS, D.Tb, "trace_collections", retained.collections),
                observe_count(PRODUCTS, D.Tb, "retained_trace_records", tuple(r for c in retained.collections for r in c.records)),
                observe_count(PRODUCTS, D.Tb, "plan_associations", (self.binding.association,)),
                observe_count(PRODUCTS, D.Tb, "interleaving_references", retained.interleaving),
                unavailable(PRODUCTS, D.Tb, "trace_canonical_bytes", "bytes", "existing.TraceCollection",
                            "public fingerprint exists, no canonical textual representation"),))
            projection = managed_projection(result)
            provenance = (retained.fingerprint(), retained.context.fingerprint(), retained.scope.fingerprint())
        elif path == "native":
            baseline = root_snapshot(root)
            self.assertEqual(metric_values(baseline)["root_entries"], 0)
            # Real owner APIs are unmocked; only interpreter fallback is prohibited.
            with patch.object(RuntimeEngine, "execute", side_effect=AssertionError("native fallback")):
                with tempfile.TemporaryDirectory(prefix="pulse-", dir=root) as directory:
                    child = Path(directory)
                    self.assertEqual(list(child.iterdir()), [])
                    mapped = build_native_with_mapping(self.verified, self.plan, child)
                    self.assertEqual(mapped.artifact.image.parent, child)
                    self.assertEqual(issuance_count().value, initial_issuance.value + 1)
                    inventory = inventory_artifacts(ARTIFACTS, child, authorized_root=root)
                    artifacts = inventory.snapshot
                    self.assertTrue(all(v.availability is Availability.AVAILABLE for v in artifacts.observations))
                    sizes = metric_values(artifacts)
                    self.assertGreater(sizes["generated_c_bytes"], 0)
                    self.assertGreater(sizes["native_image_bytes"], 0)
                    self.assertGreaterEqual(sizes["files"], 3)
                    before_dbl = root_snapshot(root)
                    retained = dispatch_native_retained(self.binding, mapped)
                    retained.validate_snapshot(self.binding, retained.evidence)
                    self.assertEqual(inventory, inventory_artifacts(ARTIFACTS, child, authorized_root=root))
                residue = root_snapshot(root)
                boundary = LifecycleBoundary("native.child-scope-exit", ARTIFACTS, before_dbl, residue)
                self.assertEqual(baseline, residue, "RESOURCE_LIFECYCLE_GAP: native scope residue")
                self.assertTrue(any(v.direction is DeltaDirection.DECREASE for v in boundary.delta()))
                self.assertFalse(child.exists())
                retained.validate_snapshot(self.binding, retained.evidence)
            result = retained.evidence.result
            receipt = json.loads(retained.evidence.receipt_json)
            self.assertEqual(receipt["air"], identities[0])
            self.assertEqual(receipt["routing"], identities[3])
            self.assertEqual(receipt["profile"], PROFILE)
            self.assertEqual(receipt["entry"], identities[1])
            self.assertEqual(retained.mapping.source_mapping_fingerprint, "UNMAPPED_SOURCE")
            footprint = ResourceSnapshot((
                observe_count(PRODUCTS, D.Tb, "native_evidence_records", retained.collection.records),
                observe_count(PRODUCTS, D.Tb, "metadata_operations", retained.mapping.sidecar.operations),
                observe_count(PRODUCTS, D.Tb, "mapping_regions", retained.mapping.regions),
                observe_count(PRODUCTS, D.Tb, "plan_mapping_result_associations",
                              (self.binding.association, retained.mapping.association, retained.post)),
                observe_bytes(PRODUCTS, D.Tb, "mapping_canonical_bytes", retained.mapping.canonical_form()),
                observe_bytes(PRODUCTS, D.Tb, "result_canonical_bytes", result.canonical_form()),
                observe_bytes(PRODUCTS, D.At, "receipt_bytes", retained.evidence.receipt_json),))
            projection = native_projection(result)
            provenance = (retained.fingerprint(), retained.pre.fingerprint(), retained.post.fingerprint(),
                          retained.evidence.output_fingerprint, result.fingerprint())
        else:
            raise ValueError("unknown execution path")
        self.assertEqual(projection, self.expected, "DETERMINISM_GAP: owner projection changed")
        self.assertTrue(projection[0])
        self.assertEqual(identities, self.stability(), "DETERMINISM_GAP: stability set changed")
        refs = tuple(weakref.ref(v) for v in (result, retained, mapped, context, runtime) if v is not None)
        ticket = weakref.ref(mapped.artifact._ticket) if mapped is not None else None
        del result, retained, mapped, context, runtime
        live = observe_count(PRODUCTS, D.Pc, "live_pulse_products", tuple(ref for ref in refs if ref() is not None))
        self.assertEqual(live.value, 0, "RESOURCE_LIFECYCLE_GAP: pulse product still owned")
        if ticket is not None:
            self.assertIsNone(ticket(), "RESOURCE_LIFECYCLE_GAP: native issuance ticket survived release")
        final_issuance = issuance_count()
        self.assertEqual(initial_issuance, final_issuance)
        release = ResourceSnapshot((live, final_issuance))
        timing = elapsed(PRODUCTS, started)
        post = live_readings(python_enabled)
        self.assertTrue(all(v.volatile for v in pre.observations + post.observations))
        self.assertTrue(all(v.ownership.owner.status is EvidenceStatus.KNOWN and
                            v.ownership.purpose.status is EvidenceStatus.KNOWN and
                            v.ownership.intended_lifetime.status is EvidenceStatus.KNOWN
                            for s in (pre, footprint, release) for v in s.observations))
        return Pulse(path, identities, projection, provenance, pre, post, footprint, release, artifacts, residue, timing)

    def emit(self, scale, path, round_number, pulses, baseline, post):
        times = [p.timing.value for p in pulses]
        record = dict(scale=scale, path=path, round=round_number, count=len(pulses),
            timing_ns=dict(min=min(times), median=median(times), max=max(times)),
            baseline=metric_values(baseline), post=metric_values(post),
            post_sequences={name: [metric_values(p.post)[name] for p in pulses] for name in metric_values(post)},
            available={v.metric: v.availability.value for v in post.observations},
            footprint=metric_values(pulses[0].footprint), release=metric_values(pulses[0].release),
            footprint_fingerprint=pulses[0].footprint.fingerprint(),
            artifacts=None if pulses[0].artifacts is None else metric_values(pulses[0].artifacts),
            residue=None if pulses[0].residue is None else metric_values(pulses[0].residue),
            residue_fingerprint=None if pulses[0].residue is None else pulses[0].residue.fingerprint(),
            identities=pulses[0].identities, projection=pulses[0].projection,
            evidence_ledger_records=observe_count(REPORT, D.Cb, "pulse_reports", pulses).value,
            leak_claim=False, child_process_peak="MEASUREMENT_GAP")
        print("P12_8_3_OBSERVATION=" + json.dumps(record, sort_keys=True), flush=True)

    def scale_a(self, path):
        with tempfile.TemporaryDirectory(prefix="p12-8-3-a-", dir=BUILD) as directory:
            root = Path(directory)
            baseline = live_readings(False)
            pulse = self.pulse(path, root)
            self.assertEqual(list(root.iterdir()), [])
            self.emit("A", path, 1, (pulse,), baseline, live_readings(False))

    def sequence(self, path, count, round_number):
        # Fixed evidence ledger is intentionally retained until this sequence test ends.
        owned_tracing = not tracemalloc.is_tracing()
        if owned_tracing:
            tracemalloc.start()
        try:
            with tempfile.TemporaryDirectory(prefix="p12-8-3-b-", dir=BUILD) as directory:
                root = Path(directory)
                root_baseline = root_snapshot(root)
                baseline = live_readings(owned_tracing)
                pulses = []
                for index in range(count):
                    pulse = self.pulse(path, root, python_enabled=owned_tracing)
                    if pulses:
                        self.assertEqual(pulses[0].deterministic_evidence(), pulse.deterministic_evidence(),
                                         "DETERMINISM_GAP: deterministic continuity changed")
                    pulses.append(pulse)
                    self.assertEqual(root_snapshot(root), root_baseline)
                    if path == "native":
                        print("P12_8_3_NATIVE_PULSE=" + str(round_number) + ":" + str(index + 1) + "|PASS", flush=True)
                post = live_readings(owned_tracing)
                self.emit("B", path, round_number, tuple(pulses), baseline, post)
                return tuple(p.deterministic_evidence() for p in pulses)
        finally:
            if owned_tracing:
                tracemalloc.stop()

    def continuity(self, path, count):
        first = self.sequence(path, count, 1)
        second = self.sequence(path, count, 2)
        self.assertEqual(first, second, "REPRODUCIBILITY_GAP: clean-root deterministic evidence changed")
        print("P12_8_3_CLEAN_ROOT_REPEAT=" + path + "|PASS", flush=True)

    def test_scale_a_canonical(self):
        self.scale_a("canonical")

    def test_scale_a_managed_retained(self):
        self.scale_a("managed-retained")

    @unittest.skipUnless(os.name == "nt", "UNSUPPORTED_TARGET: Windows native v1 required")
    def test_scale_a_real_native(self):
        self.scale_a("native")

    def test_scale_b_canonical_twenty_twice(self):
        self.continuity("canonical", 20)

    def test_scale_b_managed_retained_twenty_twice(self):
        self.continuity("managed-retained", 20)

    @unittest.skipUnless(os.name == "nt", "UNSUPPORTED_TARGET: Windows native v1 required")
    def test_scale_b_real_native_ten_twice_sequential(self):
        self.continuity("native", 10)

    def test_volatile_growth_is_not_residue_or_leak(self):
        reading = live_readings(False)
        changed = ResourceSnapshot(tuple(replace(v, value=v.value + 10 ** 6)
            if v.availability is Availability.AVAILABLE else v for v in reading.observations))
        self.assertEqual(reading.fingerprint(), changed.fingerprint())
        delta = compare_snapshots(reading, changed)
        self.assertFalse(any(hasattr(v, "leak") or hasattr(v, "cleanup_success") for v in delta))
        self.assertTrue(all(v.direction in (DeltaDirection.INCREASE, DeltaDirection.UNAVAILABLE) for v in delta))

    def test_snapshot_ledger_is_structural_and_immutable(self):
        snapshot = ResourceSnapshot((observe_count(REPORT, D.Cb, "pulse_reports", (1, 2)),))
        with self.assertRaises(FrozenInstanceError):
            snapshot.observations = ()
        self.assertTrue(all(type(v.value) is int for v in snapshot.observations))
        self.assertEqual(snapshot, ResourceSnapshot(tuple(reversed(snapshot.observations))))
        observer_path = ROOT / "apexforge/tooling/resource_observability.py"
        tree = ast.parse(observer_path.read_text(encoding="utf-8"))
        imports = {n.module or "" for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
        imports.update(alias.name for n in ast.walk(tree) if isinstance(n, ast.Import) for alias in n.names)
        self.assertFalse(any(name.startswith(("air", "runtime", "workflow", "subprocess")) for name in imports))


if __name__ == "__main__":
    unittest.main(verbosity=2)
