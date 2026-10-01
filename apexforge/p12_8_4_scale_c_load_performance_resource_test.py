"""Sequential, observer-instrumented native-v1 envelope; no latency budgets."""
from __future__ import annotations

from dataclasses import replace
import json
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
    observe_count, observe_bytes, observe_current_process, observe_python_memory,
    inventory_artifacts, elapsed, compare_snapshots,
)
from tooling.trace_integration import associate_plan, execute_managed_retained, dispatch_native_retained
from air.verify import AIRVerifier
from air.model import StateDefinition, StateAssignment
from air.expressions import AIRIntegerLiteral
from runtime.engine import RuntimeEngine
from workflow.air_runner import run_air_program, build_default_context
from apexforge.native_backend import native_execution as native
from apexforge.native_backend.source_mapping import build_native_with_mapping, emit_native_source_mapping
from apexforge.native_backend.lowering_input import build_verified_air_lowering_input
from apexforge.native_backend.native_execution_contract import (
    admit_native_profile, PROFILE, MAX_STATES, MAX_STORES, MIN_I64, MAX_I64,
)
from p12_5_native_profile_contract_test import fixture, plan_for, with_path
from p12_7_2_bounded_behavioral_equivalence_test import managed_projection, native_projection

POINTS = (1, 8, 32, 64, 128, 256)


def owner(scope, kind, purpose, lifetime, boundary):
    known = lambda value: OwnershipEvidence(EvidenceStatus.KNOWN, value)
    return ResourceOwnership(scope, kind, known("P12.8-4 sequential test scope"), known(purpose),
        known("explicit scale/sample invocation"), known(lifetime), known(boundary))


ARTIFACTS = owner("scale-c-artifacts", ResourceClass.IRR, "fresh native build custody", "one sample", "TemporaryDirectory exit")
PRODUCTS = owner("scale-c-products", ResourceClass.DHF, "validation wrappers and structural observations", "one sample", "local references released")
PROCESS = owner("scale-c-process", ResourceClass.DHF, "aggregate current-process observation; constituent ownership unresolved", "test process", "process exit")
IDENTITIES = owner("scale-c-identities", ResourceClass.SHR, "canonical identity comparison", "test evidence", "review evidence retention")


def values(snapshot):
    return {v.metric: v.value for v in snapshot.observations}


def readings():
    return ResourceSnapshot(observe_current_process(PROCESS) + observe_python_memory(PROCESS, enabled=True))


def workload(states, stores):
    base = fixture()
    # Keep the frozen singleton path, principal and directive, including empty actions.
    definitions = tuple(StateDefinition("state:%03d" % i, AIRIntegerLiteral(-i - 1))
                        for i in reversed(range(states)))
    assignments = tuple(StateAssignment("state:%03d" % (i % states), "set_int",
                        AIRIntegerLiteral((i * 7919) - 100000)) for i in range(stores))
    return with_path(replace(base, states=definitions), assignments=assignments)


def stats(samples):
    return dict(count=len(samples), min=min(samples), median=median(samples), max=max(samples))


class ScaleCTests(unittest.TestCase):
    def test_live_contract_constants_and_fixture_shape(self):
        self.assertEqual((MAX_STATES, MAX_STORES, MIN_I64, MAX_I64), (256, 4096, -(2**63), 2**63 - 1))
        self.assertEqual(PROFILE, "apexforge.native.win-x64.i64-literal-state-set/v1")
        for n in POINTS:
            program = workload(n, n)
            admitted = admit_native_profile(AIRVerifier().verify(program).require_verified(), plan_for(program))
            self.assertEqual((len(admitted.state_ids), len(admitted.stores)), (n, n))
            self.assertEqual(len(program.directives), 1)
            self.assertEqual(len(program.principals), 1)
            path = program.causal_decisions[0].paths[0]
            self.assertEqual(path.actions, fixture().causal_decisions[0].paths[0].actions)
            self.assertEqual(path.actions, ())

    def measure(self, state_count, store_count, dimension):
        print("P12_8_4_PROGRESS=prepare:%d:%d" % (state_count, store_count), flush=True)
        setup = perf_counter_ns()
        program = workload(state_count, store_count)
        verified = AIRVerifier().verify(program).require_verified()
        plan = plan_for(program)
        admitted = admit_native_profile(verified, plan)
        binding = associate_plan(verified, plan)
        planning_ns = elapsed(PRODUCTS, setup).value
        lowering_start = perf_counter_ns()
        source, mapping = emit_native_source_mapping(verified, plan)
        lowering_ns = elapsed(PRODUCTS, lowering_start).value
        air_identity = build_verified_air_lowering_input(verified)
        duplicate = workload(state_count, store_count)
        duplicate_verified = AIRVerifier().verify(duplicate).require_verified()
        duplicate_plan = plan_for(duplicate)
        duplicate_air = build_verified_air_lowering_input(duplicate_verified)
        self.assertEqual(air_identity.transport_json, duplicate_air.transport_json)
        self.assertEqual(air_identity.transport_fingerprint, duplicate_air.transport_fingerprint)
        duplicate_source, duplicate_mapping = emit_native_source_mapping(duplicate_verified, duplicate_plan)
        self.assertEqual(source, duplicate_source)
        self.assertEqual(mapping.fingerprint(), duplicate_mapping.fingerprint())
        self.assertEqual(admitted.routing_fingerprint, admit_native_profile(duplicate_verified, duplicate_plan).routing_fingerprint)
        canonical = run_air_program(program, entry_directives=(plan.entry_directive,))
        canonical_order = tuple(cell.key for cell in canonical.final_state.cells)
        expected = managed_projection(canonical)  # Sole semantic oracle: canonical AIR runner.
        self.assertTrue(expected[0])
        self.assertEqual(expected, managed_projection(run_air_program(duplicate, entry_directives=(duplicate_plan.entry_directive,))))
        self.assertEqual(admitted.profile, PROFILE)
        self.assertEqual((program.directives[0].id, program.principals[0].id), ("directive:main", "principal:main"))
        times = {p: [] for p in ("canonical", "managed-retained", "native-total", "native-build-owner", "compiler", "dispatch-owner")}
        os_samples, footprints, residues = [], [], []
        managed_footprints = []
        baseline_issued = len(native._issued)
        original_run, original_dispatch = native.subprocess.run, native.dispatch_native
        compiler_times, dispatch_times = [], []

        def timed_run(*args, **kwargs):
            command = args[0] if args else kwargs.get("args")
            compiler = isinstance(command, (tuple, list)) and Path(str(command[0])).name.lower() == "cl.exe"
            started = perf_counter_ns()
            result = original_run(*args, **kwargs)
            if compiler:
                compiler_times.append(elapsed(PRODUCTS, started).value)
            return result

        def timed_dispatch(*args, **kwargs):
            started = perf_counter_ns()
            result = original_dispatch(*args, **kwargs)
            dispatch_times.append(elapsed(PRODUCTS, started).value)
            return result

        tracemalloc.start()
        try:
            print("P12_8_4_PROGRESS=process-readings", flush=True)
            os_samples.append(values(readings()))
            probe = run_air_program(program, entry_directives=(plan.entry_directive,))
            self.assertEqual(managed_projection(probe), expected)
            del probe
            python_probe = dict(before=os_samples[0], after=values(readings()))
            tracemalloc.stop()  # Bounded Python evidence; retained/native timing is untraced.
            for path in ("canonical", "managed-retained"):
                print("P12_8_4_PROGRESS=" + path, flush=True)
                for sample in range(6):  # One warm-up, five measured owner executions.
                    started = perf_counter_ns()
                    if path == "canonical":
                        result = run_air_program(program, entry_directives=(plan.entry_directive,))
                    else:
                        context, runtime = build_default_context(program), RuntimeEngine()
                        retained = execute_managed_retained(binding, context=context, runtime=runtime)
                        result = retained.result
                    duration = elapsed(PRODUCTS, started).value
                    self.assertEqual(managed_projection(result), expected)
                    self.assertEqual(tuple(cell.key for cell in result.final_state.cells), canonical_order)
                    if path == "managed-retained":
                        retained.validate(binding, context, runtime, canonical)
                        structural = ResourceSnapshot((
                            observe_count(PRODUCTS, D.Tb, "trace_steps", result.trace.steps),
                            observe_count(PRODUCTS, D.Tb, "trace_collections", retained.collections),
                            observe_count(PRODUCTS, D.Tb, "trace_records", tuple(r for c in retained.collections for r in c.records)),
                            observe_count(PRODUCTS, D.Tb, "plan_associations", (binding.association,)),))
                        managed_footprints.append(values(structural))
                        del retained, context, runtime
                    del result
                    if sample:
                        times[path].append(duration)
                    os_samples.append(values(readings()))
            build_root = ROOT / "build"
            build_root.mkdir(exist_ok=True)
            with tempfile.TemporaryDirectory(prefix="scale-c-", dir=build_root) as root_name:
                root = Path(root_name)
                baseline = inventory_artifacts(ARTIFACTS, root, authorized_root=root, dimension=D.Pc).snapshot
                for sample in range(3):
                    print("P12_8_4_PROGRESS=native:%d" % sample, flush=True)
                    started = perf_counter_ns()
                    with patch.object(RuntimeEngine, "execute", side_effect=AssertionError("native fallback")), \
                         patch.object(native.subprocess, "run", new=timed_run), \
                         patch.object(native, "dispatch_native", new=timed_dispatch):
                        with tempfile.TemporaryDirectory(prefix="build-", dir=root) as child_name:
                            child = Path(child_name)
                            build_start = perf_counter_ns()
                            mapped = build_native_with_mapping(verified, plan, child)
                            times["native-build-owner"].append(elapsed(PRODUCTS, build_start).value)
                            ticket = weakref.ref(mapped.artifact._ticket)
                            self.assertEqual(len(native._issued), baseline_issued + 1)
                            inventory = inventory_artifacts(ARTIFACTS, child, authorized_root=root)
                            self.assertTrue(all(v.availability is Availability.AVAILABLE for v in inventory.snapshot.observations))
                            sizes = values(inventory.snapshot)
                            sizes["generated_c_files"] = len(tuple(f for f in inventory.files if f.relative_path.endswith(".c")))
                            sizes["other_product_bytes"] = sizes["total_bytes"] - sizes["generated_c_bytes"] - sizes["native_image_bytes"]
                            self.assertGreater(sizes["generated_c_bytes"], 0)
                            self.assertGreater(sizes["native_image_bytes"], 0)
                            self.assertEqual((child / "program.c").read_bytes(), source)
                            native_retained = dispatch_native_retained(binding, mapped)
                            native_retained.validate_snapshot(binding, native_retained.evidence)
                            self.assertEqual(native_projection(native_retained.evidence.result), expected)
                            receipt = json.loads(native_retained.evidence.receipt_json)
                            self.assertEqual((receipt["air"], receipt["routing"], receipt["profile"], receipt["entry"]),
                                (air_identity.transport_fingerprint, admitted.routing_fingerprint, PROFILE, plan.entry_directive))
                            self.assertEqual(native_retained.mapping.fingerprint(), mapping.fingerprint())
                            footprint = ResourceSnapshot((
                                observe_count(PRODUCTS, D.Tb, "metadata_operations", mapping.sidecar.operations),
                                observe_count(PRODUCTS, D.Tb, "mapping_regions", mapping.regions),
                                observe_count(PRODUCTS, D.Tb, "native_trace_records", native_retained.collection.records),
                                observe_count(PRODUCTS, D.Tb, "plan_mapping_result_associations", (binding.association, mapping.association, native_retained.post)),
                                observe_bytes(PRODUCTS, D.Tb, "mapping_bytes", mapping.canonical_form()),
                                observe_bytes(PRODUCTS, D.Tb, "result_evidence_bytes", native_retained.evidence.result.canonical_form()),
                                observe_bytes(PRODUCTS, D.At, "receipt_bytes", native_retained.evidence.receipt_json),))
                            before = inventory_artifacts(ARTIFACTS, root, authorized_root=root, dimension=D.Pc).snapshot
                            footprints.append(dict(artifacts=sizes, metadata=values(footprint)))
                        after = inventory_artifacts(ARTIFACTS, root, authorized_root=root, dimension=D.Pc).snapshot
                        LifecycleBoundary("scale-c-native-scope-exit", ARTIFACTS, before, after)
                        self.assertEqual(after, baseline, "RESOURCE_LIFECYCLE_GAP: residue")
                        self.assertEqual(tuple(root.iterdir()), ())
                        self.assertEqual((values(after)["files"], values(after)["total_bytes"]), (0, 0))
                        native_retained.validate_snapshot(binding, native_retained.evidence)
                        del native_retained, mapped
                    self.assertIsNone(ticket())
                    self.assertEqual(len(native._issued), baseline_issued)
                    residues.append(after.fingerprint())
                    times["native-total"].append(elapsed(PRODUCTS, started).value)
                    os_samples.append(values(readings()))
                self.assertEqual(len(set(residues)), 1)
            self.assertEqual(len(compiler_times), 3)
            self.assertEqual(len(dispatch_times), 3)
            times["compiler"], times["dispatch-owner"] = compiler_times, dispatch_times
            self.assertTrue(all(v == footprints[0] for v in footprints))
            self.assertTrue(all(v == managed_footprints[0] for v in managed_footprints))
            self.assertEqual(air_identity.transport_fingerprint, build_verified_air_lowering_input(verified).transport_fingerprint)
            final = readings()
            self.assertTrue(all(v.volatile for v in final.observations))
            self.assertEqual(final.fingerprint(), ResourceSnapshot(()).fingerprint())
            record = dict(dimension=dimension, states=state_count, stores=store_count,
                timing_ns={p: stats(v) for p, v in times.items()},
                preparation_probe_ns=planning_ns, lowering_mapping_probe_ns=lowering_ns,
                footprint=footprints[0], managed_footprint=managed_footprints[0],
                os_python_sequence=os_samples, python_probe=python_probe,
                availability={v.metric: v.availability.value for v in final.observations},
                air=air_identity.transport_fingerprint, routing=admitted.routing_fingerprint,
                mapping=mapping.fingerprint(), source_bytes=len(source), residue_fingerprint=residues[0],
                residue_files=0, residue_bytes=0, issued_before=baseline_issued, issued_after=len(native._issued),
                native_fallback=False, child_process_peak="MEASUREMENT_GAP")
            print("P12_8_4_OBSERVATION=" + json.dumps(record, sort_keys=True), flush=True)
        finally:
            tracemalloc.stop()

    def test_primary_state_scale_envelope(self):
        for n in POINTS:
            with self.subTest(states=n):
                self.measure(n, n, "state-count")

    def test_secondary_store_scale_envelope(self):
        # Eight-store baseline is already the primary eight-state point.
        for stores in (128,):
            with self.subTest(stores=stores):
                self.measure(8, stores, "store-count")

    def test_volatile_observations_are_not_deterministic_growth_verdicts(self):
        reading = readings()
        changed = ResourceSnapshot(tuple(replace(v, value=v.value + 1) if v.value is not None else v
                                         for v in reading.observations))
        self.assertEqual(reading.fingerprint(), changed.fingerprint())
        self.assertFalse(any(hasattr(v, "leak") for v in compare_snapshots(reading, changed)))


if __name__ == "__main__":
    unittest.main(verbosity=2)
