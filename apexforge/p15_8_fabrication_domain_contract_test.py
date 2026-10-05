"""Offline fabrication intent and declared compatibility; no physical operations."""
import ast
from dataclasses import FrozenInstanceError, replace
from hashlib import sha256
from pathlib import Path
import unittest

from tooling import fabrication_domain as fab
from tooling import domain_platform as sdk
from tooling import domain_interchange as interchange
from tooling.parametric_domain import ParametricScalar
import p15_7_parametric_domain_contract_test as param_fixture
import p15_3_apexmotion_domain_contract_test as package_fixture


def envelope(value="100", unit="mm"):
    return fab.BuildEnvelope(*(ParametricScalar(value) for _ in "xyz"), unit)


def fixture():
    variant = param_fixture.fixture()[2]
    data = b"caller-supplied part evidence; no geometry claims"
    input_record = fab.FabricationInput("part-evidence", sha256(data).hexdigest().upper(), data, variant)
    material = fab.MaterialProfile("material-one", "declared-family", (fab.PROCESS,), variant.provenance)
    requirements = fab.MachineRequirementProfile(envelope(), ("assembly.fixture",))
    parameters = fab.ProcessParameters(ParametricScalar("0.2"), "mm")
    plan = fab.FabricationPlan(fab.FabricationJobIdentity("job-one"),
        fab.fabrication_platform(package_fixture.fixture()[0]), input_record, material, requirements, parameters,
        variant.provenance)
    machine = fab.MachineProfile("machine-one", (fab.PROCESS,), envelope("200"), ("declared-family",), ("assembly.fixture",))
    return plan, machine


class FabricationTests(unittest.TestCase):
    def rejected(self, code, fn):
        with self.assertRaises(fab.FabricationError) as context:
            fn()
        self.assertEqual(context.exception.code, code)

    def test_platform_and_package(self):
        plan, _ = fixture()
        self.assertEqual(plan.platform.identity, sdk.DomainPlatformIdentity("apexforge.fabrication", "fabrication"))
        self.assertEqual(plan.platform.implementation, sdk.ImplementationPackage.from_manifest(package_fixture.fixture()[0]))
        self.assertNotEqual(plan.job, plan.platform.identity)

    def test_explicit_bounded_process(self):
        plan, _ = fixture()
        self.assertEqual(plan.record()["process"], fab.PROCESS)
        self.rejected("FABRICATION_PROCESS_UNSUPPORTED", lambda: replace(plan.parameters, process="print.stl"))

    def test_input_integrity(self):
        plan, _ = fixture()
        self.assertEqual(plan.input.record()["integrity"], "BYTES_MATCH")
        self.assertEqual(sha256(plan.input.payload).hexdigest().upper(), plan.input.digest)
        self.rejected("FABRICATION_INPUT_INTEGRITY_FAILED", lambda: replace(plan.input, payload=b"changed"))

    def test_input_digest_invalid(self):
        plan, _ = fixture()
        self.rejected("FABRICATION_DIGEST_INVALID", lambda: replace(plan.input, digest="invalid"))

    def test_bytes_missing_is_incomplete(self):
        plan, machine = fixture()
        report = fab.FabricationValidation(replace(plan, input=replace(plan.input, payload=None)), machine)
        self.assertEqual(report.status, "INCOMPLETE")
        self.assertIn("INPUT_BYTES_MISSING", [c.code for c in report.checks])

    def test_variant_preserved_without_geometry(self):
        design, _, variant = param_fixture.fixture()
        before = (design.fingerprint(), variant.fingerprint(), variant.canonical_json())
        data = b"supplied evidence"
        reference = fab.FabricationInput("geometry-evidence", sha256(data).hexdigest().upper(), data, variant)
        self.assertEqual(reference.record()["variant_fingerprint"], before[1])
        self.assertEqual(before, (design.fingerprint(), variant.fingerprint(), variant.canonical_json()))
        self.assertFalse(variant.record()["geometry_generated"])
        self.assertFalse(reference.record()["geometry_interpreted"])

    def test_material_profile_not_certified(self):
        plan, _ = fixture()
        self.assertFalse(plan.material.record()["material_certified"])
        self.assertEqual(plan.material.family, "declared-family")

    def test_machine_profile_not_live(self):
        _, machine = fixture()
        self.assertFalse(machine.record()["live_machine_state"])
        self.assertEqual(machine.record()["evidence_origin"], "CALLER_SUPPLIED")

    def test_requirements_declarative(self):
        plan, _ = fixture()
        self.assertTrue(plan.requirements.record()["declarative_only"])
        self.assertFalse(plan.requirements.record()["grants_authority"])

    def test_units_explicit(self):
        self.rejected("FABRICATION_ENVELOPE_INVALID", lambda: envelope(unit="unknown"))
        self.rejected("FABRICATION_PARAMETER_INVALID", lambda: fab.ProcessParameters(ParametricScalar("1"), ""))
        self.rejected("FABRICATION_PARAMETER_INVALID", lambda: fab.ProcessParameters(ParametricScalar("-1"), "mm"))

    def test_plan_unit_consistency(self):
        plan, _ = fixture()
        self.rejected("FABRICATION_PARAMETER_UNIT_MISMATCH", lambda: replace(plan, parameters=replace(plan.parameters, unit="m")))

    def test_numeric_canonical(self):
        self.assertEqual(fab.ProcessParameters(ParametricScalar("0.200"), "mm").fingerprint(),
            fab.ProcessParameters(ParametricScalar("0.2"), "mm").fingerprint())

    def test_immutable_records(self):
        plan, machine = fixture()
        for record, field in ((plan, "material"), (plan.job, "identifier"), (plan.input, "payload"),
            (plan.material, "family"), (plan.requirements, "capabilities"), (plan.parameters, "clearance"),
            (machine, "envelope"), (fab.FabricationValidation(plan, machine), "machine")):
            with self.assertRaises(FrozenInstanceError):
                setattr(record, field, None)

    def test_plan_binds_exact_evidence(self):
        plan, _ = fixture()
        record = plan.record()
        self.assertEqual(record["input"], plan.input.record())
        self.assertEqual(record["material"], plan.material.record())
        self.assertEqual(record["requirements"], plan.requirements.record())
        self.assertEqual(record["parameters"], plan.parameters.record())

    def test_valid_compatibility(self):
        plan, machine = fixture()
        report = fab.FabricationValidation(plan, machine)
        self.assertEqual(report.status, "VALID")
        self.assertTrue(all(c.status == "COMPATIBLE" for c in report.checks))
        self.assertEqual(len(report.checks), 7)

    def test_material_unknown(self):
        plan, machine = fixture()
        report = fab.FabricationValidation(replace(plan, material=replace(plan.material, processes=None)), machine)
        self.assertEqual(report.status, "INCOMPLETE")
        self.assertIn("MATERIAL_PROCESS_MISSING", [c.code for c in report.checks])

    def test_material_incompatible(self):
        plan, machine = fixture()
        report = fab.FabricationValidation(replace(plan, material=replace(plan.material, processes=())), machine)
        self.assertEqual(report.status, "INVALID")
        self.assertIn("MATERIAL_PROCESS_INCOMPATIBLE", [c.code for c in report.checks])

    def test_machine_absent(self):
        plan, _ = fixture()
        report = fab.FabricationValidation(plan, None)
        self.assertEqual(report.status, "INCOMPLETE")

    def test_missing_capability_unknown(self):
        plan, machine = fixture()
        report = fab.FabricationValidation(plan, replace(machine, capabilities=None))
        self.assertEqual(report.status, "INCOMPLETE")
        self.assertEqual(next(c.status for c in report.checks if c.dimension == "machine.capabilities"), "UNKNOWN")

    def test_explicit_empty_capability_incompatible(self):
        plan, machine = fixture()
        report = fab.FabricationValidation(plan, replace(machine, capabilities=()))
        self.assertEqual(report.status, "INVALID")

    def test_empty_requirement_not_inferred_capability(self):
        plan, machine = fixture()
        plan = replace(plan, requirements=replace(plan.requirements, capabilities=()))
        report = fab.FabricationValidation(plan, replace(machine, capabilities=None))
        self.assertEqual(next(c.status for c in report.checks if c.dimension == "machine.capabilities"), "COMPATIBLE")

    def test_small_envelope_incompatible(self):
        plan, machine = fixture()
        report = fab.FabricationValidation(plan, replace(machine, envelope=envelope("50")))
        self.assertEqual(report.status, "INVALID")
        self.assertIn("MACHINE_ENVELOPE_TOO_SMALL", [c.code for c in report.checks])

    def test_envelope_absent_vs_units_unknown(self):
        plan, machine = fixture()
        for supplied, code in ((None, "MACHINE_ENVELOPE_MISSING"), (envelope("200", "m"), "UNIT_CONVERSION_UNSUPPORTED")):
            report = fab.FabricationValidation(plan, replace(machine, envelope=supplied))
            self.assertEqual(report.status, "INCOMPLETE")
            self.assertIn(code, [c.code for c in report.checks])

    def test_family_incompatibility(self):
        plan, machine = fixture()
        self.assertEqual(fab.FabricationValidation(plan, replace(machine, material_families=("other",))).status, "INVALID")

    def test_dimension_evidence_retained_on_failure(self):
        plan, machine = fixture()
        report = fab.FabricationValidation(plan, replace(machine, material_families=(), envelope=None))
        self.assertEqual(report.status, "INVALID")
        self.assertIn("UNKNOWN", [c.status for c in report.checks])
        self.assertIn("INCOMPATIBLE", [c.status for c in report.checks])
        self.assertFalse(report.record()["engineering_safety_proven"])

    def test_collection_permutation(self):
        plan, machine = fixture()
        a = replace(machine, capabilities=("extra.feature", "assembly.fixture"))
        b = replace(machine, capabilities=tuple(reversed(a.capabilities)))
        self.assertEqual(a.fingerprint(), b.fingerprint())
        self.assertEqual(fab.FabricationValidation(plan, a).fingerprint(), fab.FabricationValidation(plan, b).fingerprint())

    def test_duplicate_declaration_rejected(self):
        _, machine = fixture()
        self.rejected("FABRICATION_DECLARATION_DUPLICATE", lambda: replace(machine, capabilities=("a", "a")))

    def test_external_result_claim(self):
        plan, _ = fixture()
        result = fab.FabricationResultRecord(plan, "REPORTED_COMPLETED", provenance=plan.provenance)
        self.assertEqual(result.record()["plan_fingerprint"], plan.fingerprint())
        self.assertEqual(result.record()["evidence_origin"], "EXTERNALLY_SUPPLIED")
        self.assertFalse(result.record()["physical_fabrication_verified"])
        self.rejected("FABRICATION_RESULT_INVALID", lambda: replace(result, reported_status="VERIFIED_COMPLETED"))

    def test_artifacts_request_result_interchange(self):
        plan, machine = fixture()
        for record in (plan, fab.FabricationValidation(plan, machine), fab.FabricationResultRecord(plan, "REPORTED_FAILED")):
            artifact = fab.fabrication_artifact(record)
            artifact.verify_bytes(sdk._json({"record": record.record(), "record_fingerprint": record.fingerprint()}).encode("utf-8"))
            self.assertEqual(artifact.implementation, plan.platform.implementation)
            self.assertEqual(artifact.platform, plan.platform.identity)
            request = sdk.DomainRequest(plan.platform, artifact.operation, artifacts=(artifact,))
            result = sdk.DomainResult(request, "COMPLETE", outputs=(artifact,))
            self.assertEqual(interchange.parse_document(interchange.serialize_document(result)).document, result)

    def test_deterministic_plan_and_provenance(self):
        plan, _ = fixture()
        self.assertEqual(plan.fingerprint(), fixture()[0].fingerprint())
        self.assertEqual(plan.record()["provenance"], [r.record() for r in plan.provenance])
        self.assertEqual(plan.record()["semantic_authority"], "CANONICAL_AIR")
        self.assertFalse(plan.record()["grants_authority"])
        self.assertEqual(plan.record()["execution"], "NOT_PERFORMED")

    def test_large_requirements(self):
        plan, machine = fixture()
        capabilities = tuple("feature-" + str(i) for i in range(1000))
        a = replace(plan, requirements=replace(plan.requirements, capabilities=capabilities))
        b = replace(plan, requirements=replace(plan.requirements, capabilities=tuple(reversed(capabilities))))
        machine = replace(machine, capabilities=capabilities)
        self.assertEqual(a.fingerprint(), b.fingerprint())
        self.assertEqual(fab.FabricationValidation(a, machine).fingerprint(), fab.FabricationValidation(b, machine).fingerprint())

    def test_security_static(self):
        tree = ast.parse(Path(fab.__file__).read_text(encoding="utf-8"))
        imports = {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
        self.assertEqual(imports, {"dataclasses", "hashlib", "tooling", "tooling.parametric_domain", "tooling.package_manifest"})
        forbidden = {"eval", "exec", "open", "__import__", "compile", "RuntimeEngine", "AuthorityEngine", "float"}
        calls = {n.func.id for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
        self.assertFalse(calls & forbidden)

    def test_process_validation_never_invokes_caller_comparison(self):
        class CallerObject:
            def __eq__(self, other):
                raise AssertionError("caller comparison was invoked")
        plan, _ = fixture()
        for record in (plan.parameters, plan.requirements):
            self.rejected("FABRICATION_PROCESS_UNSUPPORTED", lambda: replace(record, process=CallerObject()))


if __name__ == "__main__":
    unittest.main()
