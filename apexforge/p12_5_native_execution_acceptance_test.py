"""Live Windows x64 acceptance; no native execution is mocked in positive tests."""
from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from air.verify import AIRVerifier
from workflow.air_runner import build_registry_execution_plan, run_air_program
from apexforge.native_backend import native_execution as native
from apexforge.native_backend.native_execution_contract import NativeExecutionError, MIN_I64, PROFILE
from p12_5_native_profile_contract_test import ContractTests, fixture, plan_for, with_path
from air.model import StateAssignment, StateDefinition


class NativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = ROOT / "build"
        root.mkdir(exist_ok=True)
        cls.temporary = tempfile.TemporaryDirectory(prefix="p12-native-acceptance-", dir=root)
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.directory = Path(cls.temporary.name)
        program = fixture()
        class Registry:
            def resolve(self, name):
                assert name == "main"
                return program
        cls.plan = build_registry_execution_plan(Registry(), "main")
        cls.verified = AIRVerifier().verify(cls.plan.program).require_verified()
        build_dir = cls.directory / "first"
        build_dir.mkdir()
        cls.artifact = native.build_native(cls.verified, cls.plan, build_dir)

    def test_actual_execution_and_canonical_oracle(self):
        result = native.dispatch_native(self.artifact, self.verified, self.plan)
        values = {v.name: int(v.data) for v in result.result.outputs.values}
        self.assertEqual(values, {"state:value": 42, "state:unchanged": 9223372036854775807})
        oracle = run_air_program(self.plan.program, entry_directives=(self.plan.entry_directive,))
        self.assertEqual(values, {cell.key: cell.value for cell in oracle.final_state.cells})
        self.assertEqual(result.result.input_fingerprint, self.artifact.receipt_fingerprint)
        receipt = json.loads(result.receipt_json)
        admission = native.admit_native_profile(self.verified, self.plan)
        self.assertEqual(receipt["air"], admission.air_fingerprint)
        self.assertEqual(receipt["routing"], admission.routing_fingerprint)
        self.assertEqual(receipt["owner_air"], receipt["air"])
        self.assertEqual(receipt["image"], native.digest(self.artifact.image.read_bytes()))
        self.assertEqual(receipt["source"], native.digest(native._source(admission)))
        self.assertEqual(native.digest(result.receipt_json.encode()), result.result.input_fingerprint)
        type(self).provenance = {"receipt": receipt, "receipt_fingerprint": self.artifact.receipt_fingerprint,
                                 "result_fingerprint": result.result.fingerprint(),
                                 "output_fingerprint": result.output_fingerprint,
                                 "canonical_values": values}

    def test_repeated_build_and_run_determinism(self):
        directory = self.directory / "repeat"
        directory.mkdir()
        other = native.build_native(self.verified, self.plan, directory)
        self.assertEqual(other.image.read_bytes(), self.artifact.image.read_bytes())
        self.assertEqual(other.receipt_json, self.artifact.receipt_json)
        results = [native.dispatch_native(artifact, self.verified, self.plan)
                   for artifact in (self.artifact, self.artifact, other, other)]
        self.assertTrue(all(result == results[0] for result in results))
        print("P12_5_NATIVE_REPEATED_IMAGE_RECEIPT_OUTPUT_RESULT=PASS")

    def test_artifact_and_receipt_substitution(self):
        raw = self.artifact.image.read_bytes()
        try:
            self.artifact.image.write_bytes(raw + b"substitution")
            with patch.object(native, "_run", side_effect=AssertionError("substituted image launched")):
                with self.assertRaises(NativeExecutionError) as failure:
                    native.dispatch_native(self.artifact, self.verified, self.plan)
                self.assertEqual(failure.exception.code, "NATIVE_ARTIFACT_SUBSTITUTED")
        finally:
            self.artifact.image.write_bytes(raw)
        for forged in (replace(self.artifact, receipt_fingerprint="0" * 64),
                       replace(self.artifact, receipt_json="{}"),
                       replace(self.artifact, image=self.artifact.image.with_name("other.exe")),
                       replace(self.artifact, _ticket=object()),
                       replace(self.artifact, _ticket=native._Ticket())):
            with self.assertRaises(NativeExecutionError) as failure:
                native.dispatch_native(forged, self.verified, self.plan)
            self.assertEqual(failure.exception.code, "NATIVE_ARTIFACT_INVALID")

    def test_image_write_lock(self):
        with native._locked_image(self.artifact.image):
            with self.assertRaises(PermissionError):
                with self.artifact.image.open("wb"):
                    pass

    def test_malformed_results_at_dispatch_boundary(self):
        # Deliberate fault injection at the OS-observable seam; positive tests
        # above execute the real image. This is not production fallback.
        for data in (b"", b"x" * 15, b"x" * 17, "not bytes"):
            with patch.object(native, "_run", return_value=data):
                with self.assertRaises(NativeExecutionError) as failure:
                    native.dispatch_native(self.artifact, self.verified, self.plan)
                self.assertEqual(failure.exception.code, "NATIVE_RESULT_MALFORMED")

    def test_changed_input_rejected(self):
        program = with_path(self.plan.program, assignments=(StateAssignment("state:value", "set_int", 99),))
        verified = AIRVerifier().verify(program).require_verified()
        with self.assertRaises(NativeExecutionError) as failure:
            native.dispatch_native(self.artifact, verified, plan_for(program))
        self.assertEqual(failure.exception.code, "NATIVE_PROVENANCE_MISMATCH")

    def test_supported_minimum_through_public_chain(self):
        program = with_path(self.plan.program, assignments=(StateAssignment("state:value", "set_int", MIN_I64),))
        verified = AIRVerifier().verify(program).require_verified()
        result = native.execute_native(verified, plan_for(program), self.directory)
        self.assertEqual(result.result.outputs.values[0].data, str(MIN_I64))

    def test_maximum_supported_profile_and_unicode_id(self):
        program = replace(self.plan.program, states=tuple(StateDefinition(f"state:値{i}", 0) for i in range(256)))
        program = with_path(program, assignments=tuple(StateAssignment(f"state:値{i % 256}", "set_int", i) for i in range(4096)))
        verified = AIRVerifier().verify(program).require_verified()
        result = native.execute_native(verified, plan_for(program), self.directory)
        self.assertEqual(len(result.result.outputs.values), 256)
        self.assertEqual({v.name: int(v.data) for v in result.result.outputs.values},
                         {f"state:値{i}": 3840 + i for i in range(256)})

    def test_lowering_preserves_stores_without_evaluation(self):
        source = native._source(native.admit_native_profile(self.verified, self.plan)).decode("ascii")
        self.assertLess(source.index("s0 = 41LL;"), source.index("s0 = 42LL;"))
        self.assertIn("volatile __int64 s0 = -7LL;", source)
        import ast
        tree = ast.parse((ROOT / "apexforge/native_backend/native_execution.py").read_text())
        imports = [node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
        self.assertFalse(any(name.startswith(("runtime", "compiler", "causality", "type_system")) for name in imports))
        forbidden = {"eval", "exec", "compile", "select_path", "resolve_type", "infer_type"}
        calls = {node.func.attr if isinstance(node.func, ast.Attribute) else node.func.id
                 for node in ast.walk(tree) if isinstance(node, ast.Call)
                 and isinstance(node.func, (ast.Attribute, ast.Name))}
        self.assertFalse(calls & forbidden)

    def test_invalid_timeouts_fail_before_launch(self):
        for timeout in (0, -1, True, float("inf"), float("nan"), 10 ** 1000, "10"):
            with patch.object(native, "_run", side_effect=AssertionError("invalid timeout launched")):
                with self.assertRaises(NativeExecutionError) as failure:
                    native.dispatch_native(self.artifact, self.verified, self.plan, timeout=timeout)
                self.assertEqual(failure.exception.code, "NATIVE_TIMEOUT_INVALID")

    def test_complete_negative_contract_precedes_compiler(self):
        gate = ContractTests("test_verified_unsupported_surface")
        with patch("p12_5_native_profile_contract_test.admit_native_profile",
                   side_effect=lambda verified, plan: native.build_native(verified, plan, self.directory / "absent")):
            with patch.object(native, "_toolchain", side_effect=AssertionError("unsupported AIR reached compiler")) as compiler:
                gate.test_verified_unsupported_surface()
                compiler.assert_not_called()

    def test_process_failure_and_capture_policy(self):
        # Exercise the actual structured subprocess adapter with injected OS
        # outcomes, including timeout cleanup and bounded-size validation.
        import subprocess
        for behavior, expected in (("nonzero", "NATIVE_EXECUTION_FAILED"),
                                   ("stderr", "NATIVE_RESULT_MALFORMED"),
                                   ("oversize", "NATIVE_RESULT_MALFORMED"),
                                   ("timeout", "NATIVE_EXECUTION_TIMEOUT")):
            class Child:
                killed = False
                def wait(self, timeout=None):
                    if behavior == "timeout" and not self.killed:
                        raise subprocess.TimeoutExpired("native", timeout)
                    return 1 if behavior == "nonzero" else 0
                def kill(self):
                    self.killed = True
            child = Child()
            def launch(args, **kwargs):
                self.assertEqual(args, [str(self.artifact.image)])
                self.assertIs(kwargs["shell"], False)
                kwargs["stdout"].write(b"x" * (17 if behavior == "oversize" else 16))
                if behavior == "stderr":
                    kwargs["stderr"].write(b"diagnostic")
                return child
            with patch.object(native.subprocess, "Popen", side_effect=launch):
                with self.assertRaises(NativeExecutionError) as failure:
                    native._run(self.artifact.image, 1, 16)
                self.assertEqual(failure.exception.code, expected)
            if behavior == "timeout":
                self.assertTrue(child.killed)

    def test_build_failures_never_fall_back(self):
        import subprocess
        outcomes = (
            (subprocess.CompletedProcess(["cl.exe"], 1, b"", b"failure"), "NATIVE_BUILD_FAILED"),
            (subprocess.TimeoutExpired("cl.exe", 1), "NATIVE_BUILD_TIMEOUT"),
            (OSError("compiler unavailable"), "NATIVE_BUILD_FAILED"),
            (subprocess.CompletedProcess(["cl.exe"], 0, b"", b""), "NATIVE_BUILD_FAILED"),
        )
        for index, (outcome, expected) in enumerate(outcomes):
            directory = self.directory / f"failed-build-{index}"
            directory.mkdir()
            with patch.object(native, "_toolchain", return_value=("cl.exe", {}, {})):
                with patch.object(native.subprocess, "run") as run:
                    if isinstance(outcome, Exception):
                        run.side_effect = outcome
                    else:
                        run.return_value = outcome
                    with self.assertRaises(NativeExecutionError) as failure:
                        native.build_native(self.verified, self.plan, directory)
                    self.assertEqual(failure.exception.code, expected)
                    run.assert_called_once()


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(NativeTests)
    outcome = unittest.TextTestRunner(verbosity=2).run(suite)
    report = {
        "profile": PROFILE,
        "tests_run": outcome.testsRun, "failures": len(outcome.failures), "errors": len(outcome.errors),
        "native_acceptance": "PASS" if outcome.wasSuccessful() else "FAIL",
        "provenance": getattr(NativeTests, "provenance", None),
        "whole_language_native_execution": False,
        "regression_acceptance": "SEPARATE_REQUIRED_GATE",
        "source_sha256": {name: native.digest((ROOT / "apexforge" / name).read_bytes()) for name in (
            "native_backend/native_execution.py", "native_backend/native_execution_contract.py",
            "p12_5_native_profile_contract_test.py", "p12_5_native_execution_acceptance_test.py")},
    }
    (ROOT / "apexforge/p12_5_rcv_54_native_execution_acceptance.json").write_text(
        json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    raise SystemExit(0 if outcome.wasSuccessful() else 1)
