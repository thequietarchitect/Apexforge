"""P15.3 descriptive motion contracts, not physics or execution evidence."""
import ast
from dataclasses import FrozenInstanceError, replace
from hashlib import sha256
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tooling.apexmotion as motion
import tooling.domain_platform as sdk
import tooling.domain_interchange as exchange
import tooling.package_manifest as pm


def scalar(text):
    return motion.MotionScalar(str(text))


def vector(frame, value="0", unit="m"):
    return motion.MotionVector(scalar(value), scalar(value), scalar(value), unit, frame)


def fixture():
    manifest = pm.PackageManifest(pm.PackageCoordinate("example.motion", "motion-model", pm.ExactVersion(1, 0, 0)))
    descriptor = motion.apexmotion_platform(manifest)
    frame = motion.ReferenceFrame(motion.FrameIdentity("local"), "right")
    entity = motion.MotionEntity("entity-one")
    p = pm.CanonicalReference("apexforge.provenance/v1", "provenance-scope", "A" * 64)
    initial = motion.MotionState(entity, motion.MotionTime(scalar("0"), "timeline-one"), vector(frame), provenance=(p,))
    target = replace(initial, time=motion.MotionTime(scalar("1"), "timeline-one"), position=vector(frame, "1"))
    trajectory = motion.MotionTrajectory((target, initial), (p,))
    constraint = motion.MotionConstraint(entity, "position", vector(frame, "-2"), vector(frame, "2"), (p,))
    plan = motion.MotionPlan(initial, target, (constraint,), trajectory, (p,))
    return manifest, descriptor, initial, target, trajectory, constraint, plan


class ApexMotionTests(unittest.TestCase):
    def error(self, code, factory):
        with self.assertRaises(motion.ApexMotionError) as caught:
            factory()
        self.assertEqual(caught.exception.code, code)
        self.assertEqual(str(caught.exception), code)

    def test_platform_uses_sdk_and_exact_package(self):
        m, d, *_ = fixture()
        self.assertEqual(type(d), sdk.DomainPlatformDescriptor)
        self.assertEqual(d.identity.identifier, "apexforge.apexmotion")
        self.assertEqual(d.identity.kind, "motion")
        self.assertEqual(d.implementation.coordinate, m.coordinate)
        self.assertEqual(d.implementation.content, m.content_identity())
        self.assertNotEqual(d.identity, d.implementation)

    def test_platform_deterministic_only_descriptive_operations(self):
        m, d, *_ = fixture()
        self.assertEqual(d.fingerprint(), motion.apexmotion_platform(m).fingerprint())
        self.assertEqual(d.operations, tuple(sorted(motion.OPERATIONS)))
        self.assertTrue(all(op.endswith(".describe") for op in d.operations))
        self.error("APEXMOTION_PACKAGE_INVALID", lambda: motion.apexmotion_platform({}))

    def test_entity_and_frame_identities_immutable_distinct(self):
        _, d, state, *_ = fixture()
        self.assertNotEqual(state.entity, d.implementation)
        self.assertNotEqual(state.entity, motion.FrameIdentity(state.entity.identifier))
        for obj in (state.entity, state.frame.identity):
            with self.assertRaises(FrozenInstanceError):
                obj.identifier = "other"
        self.error("MOTION_ENTITY_INVALID", lambda: motion.MotionEntity("../host"))
        self.error("MOTION_FRAME_INVALID", lambda: motion.FrameIdentity(""))

    def test_frame_dimension_handedness_and_parent_declarative(self):
        frame = motion.ReferenceFrame(motion.FrameIdentity("child"), "left", motion.FrameIdentity("parent"))
        self.assertEqual(frame.record()["parent"], "parent")
        self.assertEqual(frame.record()["dimensions"], 3)
        self.error("MOTION_FRAME_INVALID", lambda: replace(frame, dimensions=2))
        self.error("MOTION_FRAME_INVALID", lambda: replace(frame, handedness="implicit"))
        self.error("MOTION_FRAME_PARENT_INVALID", lambda: replace(frame, parent=frame.identity))

    def test_position_requires_frame(self):
        self.error("MOTION_FRAME_REQUIRED", lambda: motion.MotionVector(scalar(0), scalar(0), scalar(0), "m", None))
        state = fixture()[2]
        self.error("MOTION_POSITION_REQUIRED", lambda: replace(state, position=None))

    def test_decimal_exact_no_float_or_nonfinite(self):
        for bad in (float("nan"), float("inf"), float("-inf"), 1.0, True, 1,
                    "NaN", "Infinity", "1e3", "+1", "01", "1.", "0.0000000001", "1" * 19):
            self.error("MOTION_SCALAR_INVALID", lambda bad=bad: motion.MotionScalar(bad))
        self.assertEqual(scalar("999999999999999999.999999999").ticks, 999999999999999999999999999)
        self.assertEqual(scalar("-0.000000001").ticks, -1)

    def test_negative_zero_and_trailing_zero_normalization(self):
        self.assertEqual(scalar("-0.000000000"), scalar("0"))
        self.assertEqual(scalar("1.230000000"), scalar("1.23"))
        self.assertEqual(scalar("100.000"), scalar("100"))

    def test_vector_explicit_unit_and_determinism(self):
        state = fixture()[2]
        a = vector(state.frame, "1.000")
        b = vector(state.frame, "1")
        self.assertEqual(a.canonical_bytes(), b.canonical_bytes())
        self.assertEqual(a.fingerprint(), b.fingerprint())
        self.assertEqual(a.record()["unit"], "m")
        self.error("MOTION_UNIT_INVALID", lambda: replace(a, unit="cm"))
        self.error("MOTION_VECTOR_INVALID", lambda: replace(a, x=1))
        with self.assertRaises(TypeError):
            motion.UNITS["position"] = "cm"

    def test_time_explicit_origin_seconds_not_wallclock(self):
        time = motion.MotionTime(scalar("-1"), "relative-origin")
        self.assertEqual(time.record()["value"], "-1")
        self.assertEqual(time.record()["unit"], "s")
        self.error("MOTION_TIME_ORIGIN_INVALID", lambda: replace(time, origin=""))
        self.error("MOTION_UNIT_INVALID", lambda: replace(time, unit="ms"))

    def test_missing_components_unavailable_not_zero(self):
        state = fixture()[2]
        self.assertIsNone(state.velocity)
        self.assertIsNone(state.acceleration)
        self.assertIsNone(state.record()["velocity"])
        self.assertIsNone(state.record()["acceleration"])
        self.assertEqual(state.record()["origin_status"], "CALLER_SUPPLIED")
        self.assertNotIn("measured", state.record())

    def test_supplied_velocity_acceleration_units_and_frame(self):
        state = fixture()[2]
        supplied = replace(state, velocity=vector(state.frame, "1", "m/s"), acceleration=vector(state.frame, "2", "m/s2"))
        self.assertEqual(supplied.record()["velocity"]["unit"], "m/s")
        self.error("MOTION_COMPONENT_UNIT_INVALID", lambda: replace(state, velocity=state.position))
        self.error("MOTION_COMPONENT_FRAME_MISMATCH", lambda: replace(state,
            velocity=vector(replace(state.frame, handedness="left"), "1", "m/s")))

    def test_trajectory_canonical_time_order(self):
        _, _, initial, target, trajectory, *_ = fixture()
        self.assertEqual(trajectory.samples, (initial, target))
        self.assertEqual(trajectory.fingerprint(), motion.MotionTrajectory((initial, target), trajectory.provenance).fingerprint())
        self.assertEqual(trajectory.record()["execution"], "NOT_PERFORMED")
        self.assertEqual(trajectory.record()["interpolation"], "NOT_IMPLEMENTED")

    def test_trajectory_duplicate_times_rejected(self):
        state = fixture()[2]
        other = replace(state, time=replace(state.time, value=scalar("-0.000")), position=vector(state.frame, "1"))
        self.error("MOTION_TRAJECTORY_TIME_DUPLICATE", lambda: motion.MotionTrajectory((state, other)))
        self.error("MOTION_TRAJECTORY_INVALID", lambda: motion.MotionTrajectory(()))

    def test_trajectory_context_cannot_change_entity_frame_origin(self):
        initial, target = fixture()[2:4]
        alternatives = (replace(target, entity=motion.MotionEntity("other")),
            replace(target, position=replace(target.position, frame=replace(target.frame, identity=motion.FrameIdentity("other")))),
            replace(target, time=replace(target.time, origin="other")))
        for other in alternatives:
            self.error("MOTION_TRAJECTORY_CONTEXT_MISMATCH", lambda other=other: motion.MotionTrajectory((initial, other)))

    def test_trajectory_numeric_order_not_lexical(self):
        state = fixture()[2]
        samples = tuple(replace(state, time=replace(state.time, value=scalar(v))) for v in ("10", "2", "-1", "0.001"))
        self.assertEqual(tuple(s.time.value.value for s in motion.MotionTrajectory(samples).samples), ("-1", "0.001", "2", "10"))

    def test_constraint_declarative_bounds_not_solution(self):
        _, _, _, _, _, constraint, _ = fixture()
        self.assertEqual(constraint.record()["satisfaction"], "NOT_EVALUATED")
        self.error("MOTION_CONSTRAINT_BOUND_INVALID", lambda: replace(constraint, lower=constraint.upper, upper=constraint.lower))
        self.error("MOTION_CONSTRAINT_INVALID", lambda: replace(constraint, component="force"))
        self.error("MOTION_CONSTRAINT_UNIT_INVALID", lambda: replace(constraint, component="velocity"))
        self.error("MOTION_CONSTRAINT_FRAME_MISMATCH", lambda: replace(constraint, upper=replace(constraint.upper,
            frame=replace(constraint.upper.frame, handedness="left"))))

    def test_plan_retains_constraints_endpoints_and_no_execution(self):
        _, _, initial, target, trajectory, constraint, plan = fixture()
        self.assertEqual(plan.constraints, (constraint,))
        self.assertEqual(plan.trajectory, trajectory)
        self.assertEqual(plan.initial, initial)
        self.assertEqual(plan.target, target)
        self.assertFalse(plan.record()["grants_authority"])
        self.assertEqual(plan.record()["execution"], "NOT_PERFORMED")

    def test_plan_context_time_and_trajectory_mismatch(self):
        plan = fixture()[-1]
        self.error("MOTION_PLAN_CONTEXT_MISMATCH", lambda: replace(plan, target=replace(plan.target, entity=motion.MotionEntity("other"))))
        self.error("MOTION_PLAN_TIME_INVALID", lambda: replace(plan, target=replace(plan.target,
            time=replace(plan.target.time, value=scalar("-1")))))
        self.error("MOTION_PLAN_TRAJECTORY_MISMATCH", lambda: replace(plan, trajectory=motion.MotionTrajectory((plan.initial,))))

    def test_plan_constraint_order_independent_and_duplicate_rejection(self):
        plan = fixture()[-1]
        extra = replace(plan.constraints[0], upper=vector(plan.initial.frame, "3"))
        a = replace(plan, constraints=(extra, *plan.constraints))
        b = replace(plan, constraints=tuple(reversed(a.constraints)))
        self.assertEqual(a.fingerprint(), b.fingerprint())
        self.error("MOTION_PLAN_CONSTRAINT_DUPLICATE", lambda: replace(plan, constraints=plan.constraints * 2))
        self.error("MOTION_PLAN_CONSTRAINT_CONTEXT_MISMATCH", lambda: replace(plan,
            constraints=(replace(extra, entity=motion.MotionEntity("other")),)))

    def test_constraints_not_automatically_evaluated(self):
        plan = fixture()[-1]
        outside = replace(plan.target, position=vector(plan.target.frame, "100"))
        described = replace(plan, target=outside, trajectory=None)
        self.assertEqual(described.constraints[0].record()["satisfaction"], "NOT_EVALUATED")

    def test_all_record_fingerprints_domain_separated(self):
        for record in fixture()[2:]:
            self.assertEqual(record.fingerprint(), sha256(record.SCHEMA.encode() + b"\0" + record.canonical_bytes()).hexdigest().upper())
        self.assertNotEqual(fixture()[2].fingerprint(), fixture()[4].fingerprint())

    def test_all_models_immutable_detached_records(self):
        _, _, state, target, trajectory, constraint, plan = fixture()
        for obj, field in ((state, "velocity"), (state.frame, "parent"), (state.position, "unit"),
                           (state.time, "origin"), (trajectory, "samples"), (constraint, "lower"), (plan, "target")):
            with self.assertRaises(FrozenInstanceError):
                setattr(obj, field, None)
            before = obj.canonical_bytes()
            obj.record().clear()
            self.assertEqual(obj.canonical_bytes(), before)

    def test_provenance_retained_without_authorship_or_truth(self):
        _, d, state, *_ = fixture()
        self.assertEqual(state.record()["provenance"], [p.record() for p in state.provenance])
        artifact = motion.motion_artifact(d, state)
        self.assertEqual(artifact.provenance, state.provenance)
        self.error("MOTION_PROVENANCE_INVALID", lambda: replace(state, provenance=("measured-by",)))
        self.error("MOTION_PROVENANCE_DUPLICATE", lambda: replace(state, provenance=state.provenance * 2))
        for key in ("trusted", "sensor_authentic", "physical_truth", "author", "measured"):
            self.assertNotIn(key, state.record())

    def test_motion_artifact_exact_platform_package_and_record_digest(self):
        _, d, state, *_ = fixture()
        artifact = motion.motion_artifact(d, state)
        self.assertEqual(type(artifact), sdk.DomainArtifact)
        self.assertEqual(artifact.implementation, d.implementation)
        self.assertEqual(artifact.platform, d.identity)
        self.assertEqual(artifact.descriptor_fingerprint, d.fingerprint())
        artifact.verify_bytes(motion.motion_payload(state))
        self.assertEqual(artifact.digest, sha256(motion.motion_payload(state)).hexdigest().upper())
        self.assertNotEqual(artifact.digest, state.fingerprint())
        self.assertNotEqual(artifact.digest, d.implementation.content.fingerprint)

    def test_profile_mismatch_rejected(self):
        _, d, state, *_ = fixture()
        for bad in (replace(d, identity=replace(d.identity, kind="simulation")),
                    replace(d, contract_version=pm.ExactVersion(2, 0, 0)), replace(d, operations=("simulate",))):
            self.error("APEXMOTION_PLATFORM_BINDING_INVALID", lambda bad=bad: motion.motion_artifact(bad, state))
        self.error("APEXMOTION_RECORD_INVALID", lambda: motion.motion_payload({}))

    def test_p15_request_result_and_interchange_all_record_kinds(self):
        _, d, state, target, trajectory, constraint, plan = fixture()
        air = pm.CanonicalReference("apexforge.air/v1", "air", "B" * 64)
        for record in (state, trajectory, constraint, plan):
            request = motion.motion_request(d, record, semantic_inputs=(air,))
            self.assertEqual(type(request), sdk.DomainRequest)
            result = sdk.DomainResult(request, "COMPLETE", request.artifacts)
            for obj in (d, request, result, request.artifacts[0]):
                parsed = exchange.parse_document(exchange.serialize_document(obj))
                self.assertEqual(parsed.document, obj)
            self.assertEqual(result.record()["semantic_authority"], "CANONICAL_AIR")
            self.assertEqual(request.semantic_inputs, (air,))
            self.assertTrue(result.record()["declaration_only"])

    def test_independent_equivalent_inputs_same_contract(self):
        for a, b in zip(fixture()[2:], fixture()[2:]):
            self.assertEqual(a.canonical_bytes(), b.canonical_bytes())
            self.assertEqual(a.fingerprint(), b.fingerprint())

    def test_large_1000_state_trajectory_deterministic(self):
        state = fixture()[2]
        samples = tuple(replace(state, time=replace(state.time, value=scalar(i))) for i in range(1000))
        a = motion.MotionTrajectory(samples)
        b = motion.MotionTrajectory(tuple(reversed(samples)))
        self.assertEqual(a.fingerprint(), b.fingerprint())
        self.assertEqual(len(a.samples), 1000)
        artifact = motion.motion_artifact(fixture()[1], a)
        artifact.verify_bytes(motion.motion_payload(a))
        self.assertEqual(exchange.parse_document(exchange.serialize_document(artifact)).document, artifact)

    def test_dynamic_no_io_authority_registry_solver(self):
        from authority.engine import AuthorityEngine
        import tooling.package_solver as solver
        import tooling.package_registry as registry
        with patch.object(AuthorityEngine, "check", side_effect=AssertionError("authority")), \
             patch.object(solver, "solve", side_effect=AssertionError("solver")), \
             patch.object(registry.RegistryCatalog, "query", side_effect=AssertionError("registry")), \
             patch("builtins.open", side_effect=AssertionError("filesystem")), \
             patch("subprocess.run", side_effect=AssertionError("process")), \
             patch("socket.socket", side_effect=AssertionError("network")):
            _, d, state, *_ = fixture()
            exchange.parse_document(exchange.serialize_document(motion.motion_request(d, state)))

    def test_static_security_no_simulator_device_runtime_or_parser(self):
        tree = ast.parse(Path(motion.__file__).read_text(encoding="utf-8"))
        imports = {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
        imports |= {a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
        self.assertEqual(imports, {"dataclasses", "hashlib", "json", "re", "types", "tooling", "tooling.package_manifest"})
        forbidden = {"loads", "load", "eval", "exec", "__import__", "open", "execute", "dispatch", "compile",
                     "run", "solve", "simulate", "integrate", "step", "actuate", "time", "now", "getenv"}
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                name = node.func.id if isinstance(node.func, ast.Name) else getattr(node.func, "attr", "")
                self.assertNotIn(name, forbidden)


if __name__ == "__main__":
    unittest.main(verbosity=2)
