"""Exact bounded evolution and frozen-boundary coexistence tests."""
import ast
from dataclasses import FrozenInstanceError, replace
from pathlib import Path
import unittest

import p15_3_apexmotion_domain_contract_test as fixtures
from tooling import apexmotion as motion
from tooling import apexmotion_simulation as sim
from tooling import domain_interchange as interchange
from tooling import domain_platform as sdk


def specification(**changes):
    _, descriptor, initial, *_ = fixtures.fixture()
    initial = replace(initial, velocity=fixtures.vector(initial.frame, "1", "m/s"),
        acceleration=fixtures.vector(initial.frame, "2", "m/s2"))
    fields = dict(descriptor=descriptor, initial=initial,
        time_step=motion.MotionScalar("1"), step_count=2)
    fields.update(changes)
    return sim.SimulationSpec(**fields)


class SimulationTests(unittest.TestCase):
    def rejected(self, code, fn):
        with self.assertRaises(sim.SimulationError) as context:
            fn()
        self.assertEqual(context.exception.code, code)

    def test_profile(self):
        self.assertEqual(specification().profile, sim.PROFILE)
        self.rejected("SIMULATION_MODEL_UNSUPPORTED", lambda: specification(profile="physics"))

    def test_immutable_spec(self):
        with self.assertRaises(FrozenInstanceError):
            specification().step_count = 3

    def test_time_step(self):
        for value in ("0", "-1"):
            self.rejected("SIMULATION_TIME_STEP_INVALID", lambda: specification(time_step=motion.MotionScalar(value)))
        self.rejected("SIMULATION_TIME_STEP_INVALID", lambda: specification(time_step_unit="ms"))

    def test_count_bounds(self):
        for count in (-1, True, sim.MAX_STEPS + 1):
            self.rejected("SIMULATION_STEP_COUNT_INVALID", lambda: specification(step_count=count))
        self.assertEqual(sim.simulate(specification(step_count=0)).steps, ())

    def test_missing_components(self):
        spec = specification()
        for component, code in (("velocity", "SIMULATION_VELOCITY_REQUIRED"),
            ("acceleration", "SIMULATION_ACCELERATION_REQUIRED")):
            self.rejected(code, lambda: replace(spec, initial=replace(spec.initial, **{component: None})))

    def test_exact_acceleration(self):
        trace = sim.simulate(specification())
        self.assertEqual(trace.status, "COMPLETED")
        self.assertEqual([s.state.position.x.value for s in trace.steps], ["2", "6"])
        self.assertEqual([s.state.velocity.x.value for s in trace.steps], ["3", "5"])

    def test_fractional_step(self):
        trace = sim.simulate(specification(time_step=motion.MotionScalar("0.5")))
        self.assertEqual(trace.steps[0].state.position.x.value, "0.75")
        self.assertEqual(trace.steps[-1].state.position.x.value, "2")

    def test_multi_axis(self):
        spec = specification()
        v = motion.MotionVector(*(motion.MotionScalar(x) for x in ("1", "-2", "0")), "m/s", spec.initial.frame)
        trace = sim.simulate(replace(spec, initial=replace(spec.initial, velocity=v)))
        self.assertEqual(tuple(getattr(trace.steps[0].state.position, x).value for x in "xyz"), ("2", "-1", "1"))

    def test_precision_failure(self):
        trace = sim.simulate(specification(time_step=motion.MotionScalar("0.000000001")))
        self.assertEqual(trace.status, "NUMERIC_PRECISION_ERROR")
        self.assertEqual(trace.steps, ())

    def test_range_failure(self):
        spec = specification()
        state = replace(spec.initial, position=fixtures.vector(spec.initial.frame, "999999999999999999"))
        trace = sim.simulate(replace(spec, initial=state))
        self.assertEqual(trace.status, "NUMERIC_RANGE_ERROR")
        self.assertEqual(trace.record()["diagnostics"][0]["failed_step"], 1)

    def test_partial_trace_failure(self):
        spec = specification(step_count=4)
        state = replace(spec.initial, position=fixtures.vector(spec.initial.frame, "999999999999999996"))
        trace = sim.simulate(replace(spec, initial=state))
        self.assertEqual(len(trace.steps), 1)
        self.assertEqual(trace.status, "NUMERIC_RANGE_ERROR")

    def test_frame_and_time_preserved(self):
        spec = specification()
        trace = sim.simulate(spec)
        self.assertEqual([s.state.time.value.value for s in trace.steps], ["1", "2"])
        self.assertTrue(all(s.state.frame == spec.initial.frame and s.state.time.origin == spec.initial.time.origin for s in trace.steps))

    def test_step_bindings(self):
        spec = specification()
        trace = sim.simulate(spec)
        self.assertEqual(trace.steps[0].prior_state_fingerprint, spec.initial.fingerprint())
        self.assertEqual(trace.steps[1].prior_state_fingerprint, trace.steps[0].state.fingerprint())
        with self.assertRaises(FrozenInstanceError):
            trace.steps[0].index = 5

    def test_trace_cannot_forge_steps(self):
        trace = sim.simulate(specification())
        self.rejected("SIMULATION_TRACE_INVALID", lambda: replace(trace, steps=tuple(reversed(trace.steps))))
        self.rejected("SIMULATION_TRACE_INCOMPLETE", lambda: replace(trace, steps=()))

    def test_trace_provenance(self):
        spec = specification()
        trace = sim.simulate(spec)
        self.assertEqual(trace.record()["origin_status"], "SIMULATED")
        self.assertEqual(trace.steps[0].record()["origin_status"], "SIMULATED")
        self.assertNotIn("origin_status", trace.steps[0].record()["state_fields"])
        self.assertEqual(trace.steps[0].state.provenance, spec.initial.provenance)
        self.assertNotIsInstance(trace, motion.MotionTrajectory)
        self.assertFalse(trace.record()["physical_event_proven"])

    def test_constraint_continue_not_clamp(self):
        spec = specification()
        constraint = motion.MotionConstraint(spec.initial.entity, "position",
            fixtures.vector(spec.initial.frame, "-2"), fixtures.vector(spec.initial.frame, "2"))
        trace = sim.simulate(replace(spec, constraints=(constraint,)))
        self.assertEqual(trace.status, "CONSTRAINT_VIOLATION")
        self.assertEqual(trace.steps[-1].state.position.x.value, "6")
        self.assertEqual(trace.steps[-1].checks[0].violated_axes, ("x", "y", "z"))

    def test_all_constraint_components(self):
        spec = specification()
        for component, unit in motion.UNITS.items():
            c = motion.MotionConstraint(spec.initial.entity, component,
                fixtures.vector(spec.initial.frame, "-1", unit), fixtures.vector(spec.initial.frame, "1", unit))
            self.assertEqual(sim.simulate(replace(spec, constraints=(c,))).status, "CONSTRAINT_VIOLATION")

    def test_cross_frame_constraint_rejected(self):
        spec = specification()
        frame = motion.ReferenceFrame(motion.FrameIdentity("another"), "right")
        c = motion.MotionConstraint(spec.initial.entity, "position", fixtures.vector(frame), fixtures.vector(frame, "1"))
        self.rejected("SIMULATION_CONSTRAINT_CONTEXT_MISMATCH", lambda: replace(spec, constraints=(c,)))

    def test_constraint_order(self):
        spec = specification()
        cs = tuple(motion.MotionConstraint(spec.initial.entity, "position",
            fixtures.vector(spec.initial.frame, "-1"), fixtures.vector(spec.initial.frame, str(n))) for n in (1, 2))
        a, b = replace(spec, constraints=cs), replace(spec, constraints=tuple(reversed(cs)))
        self.assertEqual(sim.simulate(a).canonical_bytes(), sim.simulate(b).canonical_bytes())

    def test_fingerprints_and_repetition(self):
        a, b = specification(), specification()
        self.assertEqual(a.fingerprint(), b.fingerprint())
        self.assertEqual(sim.simulate(a).fingerprint(), sim.simulate(b).fingerprint())
        self.assertNotEqual(a.fingerprint(), a.initial.fingerprint())
        self.assertNotEqual(a.fingerprint(), replace(a, step_count=1).fingerprint())

    def test_thousand_steps(self):
        spec = specification(step_count=1000)
        a, b = sim.simulate(spec), sim.simulate(spec)
        self.assertEqual(len(a.steps), 1000)
        self.assertEqual(a.canonical_bytes(), b.canonical_bytes())
        self.assertEqual(a.steps[-1].state.position.x.value, "1001000")

    def test_artifact_interchange(self):
        spec = specification()
        trace = sim.simulate(spec)
        artifact = sim.simulation_artifact(trace)
        self.assertEqual(artifact.implementation, spec.descriptor.implementation)
        self.assertEqual(artifact.platform, spec.descriptor.identity)
        self.assertEqual(interchange.parse_document(interchange.serialize_document(artifact)).document, artifact)
        artifact.verify_bytes(trace.canonical_bytes())
        request = sdk.DomainRequest(spec.descriptor, artifact.operation, artifacts=(artifact,))
        result = sdk.DomainResult(request, "COMPLETE", outputs=(artifact,))
        self.assertEqual(interchange.parse_document(interchange.serialize_document(result)).document, result)

    def test_security_static_audit(self):
        tree = ast.parse(Path(sim.__file__).read_text(encoding="utf-8"))
        imports = {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
        self.assertEqual(imports, {"dataclasses", "fractions", "tooling"})
        forbidden = {"eval", "exec", "open", "__import__", "compile", "RuntimeEngine", "AuthorityEngine", "subprocess"}
        calls = {n.func.id for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
        self.assertFalse(calls & forbidden)
        self.assertNotIn("float", calls)


if __name__ == "__main__":
    unittest.main()
