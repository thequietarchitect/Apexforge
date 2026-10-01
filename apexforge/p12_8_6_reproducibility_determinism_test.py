"""Independent reconstruction, process/root variation; existing owners execute."""
from __future__ import annotations

from dataclasses import replace
import json
import os
from pathlib import Path
import platform
import re
import struct
import subprocess
import sys
import tempfile
from time import perf_counter_ns
import unittest
from unittest.mock import patch
import weakref

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from air.model import StateDefinition, StateAssignment
from air.verify import AIRVerifier
from runtime.engine import RuntimeEngine
from type_system.model import BOOL
from workflow.air_runner import run_air_program, build_default_context
from apexforge.native_backend import native_execution as native
from apexforge.native_backend.native_execution_contract import admit_native_profile, NativeExecutionError, PROFILE
from apexforge.native_backend.lowering_input import build_verified_air_lowering_input
from apexforge.native_backend.source_mapping import emit_native_source_mapping, build_native_with_mapping
from tooling.trace_integration import (
    associate_plan, execute_managed_retained, dispatch_native_retained,
    compile_with_metadata, managed_result_fingerprint,
)
from tooling.resource_observability import (
    ResourceClass, OwnershipEvidence, EvidenceStatus, ResourceOwnership, ResourceSnapshot,
    PressureDimension as D, Availability, inventory_artifacts, observe_current_process, elapsed,
)
from p12_5_native_profile_contract_test import fixture, plan_for, with_path
from p12_7_2_bounded_behavioral_equivalence_test import managed_projection, native_projection
from p12_8_4_scale_c_load_performance_resource_test import workload
from p12_6_3_metadata_identity_association_test import SOURCE

BUILD = ROOT / "build"


def owner(scope, kind=ResourceClass.IRR):
    known = lambda value: OwnershipEvidence(EvidenceStatus.KNOWN, value)
    return ResourceOwnership(scope, kind, known("P12.8-6 reconstruction test"),
        known("compare existing canonical identities and verify owned release"),
        known("independent reconstruction"), known("sample / explicitly retained report lifetime"),
        known("TemporaryDirectory exit and artifact reference release"))


def identity(program):
    verified = AIRVerifier().verify(program).require_verified()
    plan = plan_for(program)
    binding = associate_plan(verified, plan)
    admitted = admit_native_profile(verified, plan)
    lowering = build_verified_air_lowering_input(verified)
    source, mapping = emit_native_source_mapping(verified, plan)
    return verified, plan, binding, source, mapping, dict(
        air_form=lowering.transport_json, air=lowering.transport_fingerprint,
        plan=binding.fingerprint(), routing=admitted.routing_fingerprint, profile=admitted.profile,
        directive=program.directives[0].id, principal=program.principals[0].id,
        source=source.decode("ascii"), source_hash=native.digest(source),
        mapping_form=mapping.canonical_form(), mapping=mapping.fingerprint())


def metadata_identity():
    # Existing compiler-owned source contains causal actions; never send it to native.
    metadata = compile_with_metadata(SOURCE.encode("utf-8"), "src/main.apex")
    metadata.validate()
    return dict(source_map=metadata.mapping.canonical_form(), sidecar=metadata.mapping.sidecar.canonical_identity(),
        compiler=metadata.fingerprint(), mapping=metadata.mapping.fingerprint(),
        tam=metadata.tam.fingerprint(), tam_records=tuple(r.identity() for r in metadata.tam.records))


def probe(root):
    """One fresh bounded native lifecycle; returns numbers/text, never live artifacts."""
    if tuple(root.iterdir()):
        raise AssertionError("TEST_FIXTURE_DEFECT: probe root must start empty")
    program = fixture()
    verified, plan, binding, source, mapping, deterministic = identity(program)
    canonical = run_air_program(program, entry_directives=(plan.entry_directive,))
    context, runtime = build_default_context(program), RuntimeEngine()
    managed = execute_managed_retained(binding, context=context, runtime=runtime)
    managed.validate(binding, context, runtime, canonical)
    expected = managed_projection(canonical)
    if managed_projection(managed.result) != expected:
        raise AssertionError("DETERMINISM_GAP: managed projection")
    deterministic.update(canonical=expected, canonical_order=tuple(c.key for c in canonical.final_state.cells),
        canonical_result=managed_result_fingerprint(canonical), managed_result=managed.result_fingerprint,
        managed=managed.fingerprint(), managed_trace=tuple(c.fingerprint() for c in managed.collections),
        metadata=metadata_identity())
    baseline_issued = len(native._issued)
    started = perf_counter_ns()
    process = owner("process-readings", ResourceClass.DHF)
    before = ResourceSnapshot(observe_current_process(process))
    artifact_owner = owner("reconstruction-native-root")
    with patch.object(RuntimeEngine, "execute", side_effect=AssertionError("native fallback")):
        with tempfile.TemporaryDirectory(prefix="native-", dir=root) as directory:
            child = Path(directory)
            mapped = build_native_with_mapping(verified, plan, child)
            ticket = weakref.ref(mapped.artifact._ticket)
            if len(native._issued) != baseline_issued + 1:
                raise AssertionError("RESOURCE_LIFECYCLE_GAP: issuance")
            image = mapped.artifact.image.read_bytes()
            retained = dispatch_native_retained(binding, mapped)
            retained.validate_snapshot(binding, retained.evidence)
            if native_projection(retained.evidence.result) != expected:
                raise AssertionError("DETERMINISM_GAP: native projection")
            receipt = json.loads(retained.evidence.receipt_json)
            compiler, environment, tools = native._toolchain(child)  # Existing discovery, no replacement.
            if tools != receipt["toolchain"]:
                raise AssertionError("REPRODUCIBILITY_GAP: active tools differ from receipt")
            banner = subprocess.run([compiler], cwd=child, env=environment, capture_output=True, timeout=30)
            version = re.search(r"Compiler Version [^\r\n]+", (banner.stdout + banner.stderr).decode("mbcs", errors="replace"))
            if version is None:
                raise AssertionError("MEASUREMENT_GAP: compiler version unavailable")
            deterministic.update(image_hash=native.digest(image), image_hex=image.hex(),
                receipt_form=retained.evidence.receipt_json, receipt= mapped.artifact.receipt_fingerprint,
                native_result_form=retained.evidence.result.canonical_form(),
                native_result=retained.evidence.result.fingerprint(), output=retained.evidence.output_fingerprint,
                native_trace=retained.collection.fingerprint(), native_pre=retained.pre.fingerprint(),
                native_post=retained.post.fingerprint(), native_retained=retained.fingerprint(),
                toolchain=tools, compiler_version=version.group(0))
            if (child / "program.c").read_bytes() != source or mapped.mapping != mapping:
                raise AssertionError("DETERMINISM_GAP: generated content/mapping")
        retained.validate_snapshot(binding, retained.evidence)
        del mapped, retained
    if ticket() is not None or len(native._issued) != baseline_issued:
        raise AssertionError("RESOURCE_LIFECYCLE_GAP: ticket survived")
    residue = inventory_artifacts(artifact_owner, root, authorized_root=root, dimension=D.Pc)
    if tuple(root.iterdir()) or any(v.availability is not Availability.AVAILABLE for v in residue.snapshot.observations):
        raise AssertionError("RESOURCE_LIFECYCLE_GAP: root residue unavailable/nonempty")
    numbers = {v.metric: v.value for v in residue.snapshot.observations}
    if numbers["files"] != 0 or numbers["total_bytes"] != 0:
        raise AssertionError("RESOURCE_LIFECYCLE_GAP: residue")
    deterministic.update(residue=residue.fingerprint(), residue_values=numbers)
    after = ResourceSnapshot(observe_current_process(process))
    if before.fingerprint() != after.fingerprint() or before.fingerprint() != ResourceSnapshot(()).fingerprint():
        raise AssertionError("DETERMINISM_GAP: volatile identity included")
    return dict(deterministic=deterministic,
        incidental=dict(pid=os.getpid(), root=str(root), elapsed_ns=elapsed(process, started).value,
            before={v.metric: v.value for v in before.observations}, after={v.metric: v.value for v in after.observations}),
        python=dict(version=sys.version, implementation=platform.python_implementation(), bits=struct.calcsize("P") * 8))


class ReconstructionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        BUILD.mkdir(exist_ok=True)

    def test_fresh_process_clean_root_reconstruction(self):
        reports = []
        with tempfile.TemporaryDirectory(prefix="reconstruction-", dir=BUILD) as hierarchy:
            for index in range(3):
                with tempfile.TemporaryDirectory(prefix="root-%d-" % index, dir=hierarchy) as root_name:
                    root = Path(root_name)
                    if index == 0:
                        report = probe(root)
                    else:
                        environment = dict(os.environ, PYTHONHASHSEED=str(index * 97))
                        child = subprocess.run([sys.executable, "-X", "utf8", "-B", str(Path(__file__).resolve()), "--probe", str(root)],
                            cwd=ROOT, env=environment, capture_output=True, text=True, encoding="utf-8", timeout=300)
                        self.assertEqual(child.returncode, 0, child.stderr)
                        report = json.loads(child.stdout)
                    # JSON transport only of supplied report; no semantic serialization/evaluation.
                    reports.append(json.loads(json.dumps(report)))
                    self.assertEqual(tuple(root.iterdir()), ())
                self.assertFalse(root.exists())
            self.assertEqual(tuple(Path(hierarchy).iterdir()), ())
        self.assertEqual(len({r["incidental"]["pid"] for r in reports}), 3)
        self.assertEqual(len({r["incidental"]["root"] for r in reports}), 3)
        for report in reports[1:]:
            self.assertEqual(report["deterministic"], reports[0]["deterministic"])
            self.assertEqual(report["python"], reports[0]["python"])
        # Compact evidence excludes image bytes/full canonical forms from console, not comparisons.
        stable = reports[0]["deterministic"]
        print("P12_8_6_PROCESS_RECONSTRUCTION=" + json.dumps(dict(pids=[r["incidental"]["pid"] for r in reports],
            elapsed_ns=[r["incidental"]["elapsed_ns"] for r in reports],
            resource_readings=[r["incidental"] for r in reports], python=reports[0]["python"],
            compiler=stable["compiler_version"], toolchain=stable["toolchain"],
            hashes={k: stable[k] for k in ("air", "routing", "mapping", "source_hash", "image_hash", "receipt", "native_retained", "residue")}), sort_keys=True), flush=True)

    def test_fresh_objects_load_points_and_three_path_determinism(self):
        for count in (1, 64, 256):
            rows, programs, images = [], [], []
            baseline = len(native._issued)
            for repetition in range(2):
                program = workload(count, count)
                if programs:
                    self.assertIsNot(program, programs[0])
                    self.assertIsNot(program.states[0], programs[0].states[0])
                programs.append(program)
                verified, plan, binding, source, mapping, deterministic = identity(program)
                canonical = run_air_program(program, entry_directives=(plan.entry_directive,))
                expected = managed_projection(canonical)
                context, runtime = build_default_context(program), RuntimeEngine()
                managed = execute_managed_retained(binding, context=context, runtime=runtime)
                managed.validate(binding, context, runtime, canonical)
                self.assertEqual(managed_projection(managed.result), expected)
                self.assertTrue(expected[0])
                deterministic.update(projection=expected, order=tuple(c.key for c in canonical.final_state.cells),
                    canonical_result=managed_result_fingerprint(canonical), managed=managed.fingerprint())
                with tempfile.TemporaryDirectory(prefix="load-reconstruct-", dir=BUILD) as parent_name:
                    parent = Path(parent_name)
                    with patch.object(RuntimeEngine, "execute", side_effect=AssertionError("native fallback")):
                        with tempfile.TemporaryDirectory(prefix="native-", dir=parent) as child_name:
                            child = Path(child_name)
                            mapped = build_native_with_mapping(verified, plan, child)
                            ticket = weakref.ref(mapped.artifact._ticket)
                            evidence = native.dispatch_native(mapped.artifact, verified, plan)
                            self.assertEqual(native_projection(evidence.result), expected)
                            self.assertEqual((child / "program.c").read_bytes(), source)
                            self.assertEqual(mapped.mapping, mapping)
                            images.append(mapped.artifact.image.read_bytes())
                            deterministic.update(receipt=evidence.receipt_json, native_result=evidence.result.canonical_form(),
                                output=evidence.output_fingerprint)
                        del mapped
                    self.assertIsNone(ticket())
                    self.assertEqual(len(native._issued), baseline)
                    self.assertEqual(tuple(parent.iterdir()), ())
                    residue = inventory_artifacts(owner("load-cleanup"), parent, authorized_root=parent, dimension=D.Pc)
                    self.assertEqual({v.metric: v.value for v in residue.snapshot.observations}["total_bytes"], 0)
                    deterministic["residue"] = residue.fingerprint()
                rows.append(deterministic)
            self.assertEqual(rows[0], rows[1])
            self.assertEqual(images[0], images[1])
            print("P12_8_6_LOAD_POINT=%d|TWO_FRESH_BUILDS|THREE_PATH_DETERMINISM=PASS|IMAGE_BYTES_EQUAL|ZERO_RESIDUE" % count, flush=True)

    def test_fresh_metadata_source_mapping_and_trace_order(self):
        records = [metadata_identity() for _ in range(3)]
        self.assertEqual(records[0], records[1])
        self.assertEqual(records[1], records[2])
        programs = [fixture() for _ in range(3)]
        self.assertEqual(len({id(p) for p in programs}), 3)
        rows = [identity(p)[-1] for p in programs]
        self.assertTrue(all(r == rows[0] for r in rows))
        mapping = identity(programs[0])[4]
        self.assertEqual(tuple(r.operation.ordinal for r in mapping.regions), tuple(range(len(mapping.regions))))

    def test_rejection_classification_deterministic_no_issuance_or_fallback(self):
        constructors = (
            lambda: replace(fixture(), states=fixture().states + (StateDefinition("state:bool", True, BOOL),)),
            lambda: with_path(fixture(), assignments=(StateAssignment("state:value", "add_int", 1),)),
        )
        for constructor in constructors:
            codes = []
            for _ in range(3):
                program = constructor()
                verified = AIRVerifier().verify(program).require_verified()
                before = build_verified_air_lowering_input(verified).transport_json
                issued = len(native._issued)
                with tempfile.TemporaryDirectory(prefix="rejected-", dir=BUILD) as root_name:
                    root = Path(root_name)
                    with patch.object(native, "_toolchain", side_effect=AssertionError("rejection reached compiler")), \
                         patch.object(RuntimeEngine, "execute", side_effect=AssertionError("rejection fallback")):
                        with self.assertRaises(NativeExecutionError) as caught:
                            native.build_native(verified, plan_for(program), root)
                    self.assertEqual(tuple(root.iterdir()), ())
                    codes.append(caught.exception.code)
                self.assertEqual(len(native._issued), issued)
                self.assertEqual(build_verified_air_lowering_input(verified).transport_json, before)
            self.assertEqual(codes, ["NATIVE_PROFILE_UNSUPPORTED"] * 3)


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--probe":
        print(json.dumps(probe(Path(sys.argv[2])), sort_keys=True), flush=True)
    else:
        unittest.main(verbosity=2)
