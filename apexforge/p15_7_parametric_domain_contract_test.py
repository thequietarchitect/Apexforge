"""Bounded parameters, exact assignment identity and passive design variants."""
import ast
from dataclasses import FrozenInstanceError, replace
from pathlib import Path
import unittest

from tooling import parametric_domain as param
from tooling import domain_platform as sdk
from tooling import domain_interchange as interchange
from tooling import apexmotion
import p15_3_apexmotion_domain_contract_test as fixtures


def scalar(value):
    return param.ParametricScalar(value)


def fixture():
    manifest, _, state, *_ = fixtures.fixture()
    definitions = (
        param.ParameterDefinition(param.ParameterIdentity("width"), "scalar", "length", "mm",
            minimum=scalar("1"), maximum=scalar("100")),
        param.ParameterDefinition(param.ParameterIdentity("count"), "integer", "count", "count", minimum=1, maximum=10),
        param.ParameterDefinition(param.ParameterIdentity("enabled"), "boolean", required=False),
        param.ParameterDefinition(param.ParameterIdentity("style"), "enumeration", alternatives=("round", "square")))
    design = param.ParametricDesign(param.ParametricDesignIdentity("design-one"), param.parametric_platform(manifest),
        definitions, (param.ParameterReference(definitions[0].identity, definitions[1].identity),), provenance=state.provenance)
    assignments = (
        param.ParameterAssignment(param.ParameterIdentity("width"), param.ParameterValue("scalar", scalar("20"), "mm")),
        param.ParameterAssignment(param.ParameterIdentity("count"), param.ParameterValue("integer", 2, "count")),
        param.ParameterAssignment(param.ParameterIdentity("style"), param.ParameterValue("enumeration", "round")))
    values = param.ParameterSet(design, assignments, provenance=state.provenance)
    return design, values, param.ParametricVariant(values, state.provenance)


class ParametricTests(unittest.TestCase):
    def rejected(self, code, fn):
        with self.assertRaises(param.ParametricError) as context:
            fn()
        self.assertEqual(context.exception.code, code)

    def test_platform_package(self):
        design, *_ = fixture()
        self.assertEqual(design.platform.identity, sdk.DomainPlatformIdentity("apexforge.parametric", "parametric"))
        self.assertEqual(design.platform.implementation, sdk.ImplementationPackage.from_manifest(fixtures.fixture()[0]))
        self.assertNotEqual(design.identity, design.platform.identity)

    def test_models_immutable(self):
        design, values, variant = fixture()
        for obj, field in ((design, "parameters"), (design.identity, "identifier"), (design.parameters[0], "kind"),
            (design.parameters[0].identity, "identifier"), (values, "assignments"), (variant, "parameters")):
            with self.assertRaises(FrozenInstanceError):
                setattr(obj, field, None)

    def test_scalar_exact_canonical(self):
        self.assertEqual(scalar("-0.000").value, "0")
        self.assertEqual(scalar("2.500").ticks, 2500000000)
        self.assertEqual(scalar("2.500").fingerprint(), scalar("2.5").fingerprint())
        self.assertNotEqual(scalar("2.5"), apexmotion.MotionScalar("2.5"))

    def test_scalar_invalid(self):
        for value in (1.2, True, "NaN", "Infinity", "1e2", "+1", "01", "0.0000000001", "1000000000000000000"):
            self.rejected("PARAMETER_SCALAR_INVALID", lambda: scalar(value))

    def test_unknown_kind(self):
        self.rejected("PARAMETER_KIND_UNSUPPORTED", lambda: param.ParameterValue("callback", lambda: 1))

    def test_units_explicit(self):
        self.rejected("PARAMETER_UNIT_INVALID", lambda: param.ParameterDefinition(param.ParameterIdentity("width"), "scalar"))
        self.rejected("PARAMETER_UNIT_INVALID", lambda: param.ParameterDefinition(param.ParameterIdentity("width"), "scalar", "length", "rad"))

    def test_integer_not_bool_or_float(self):
        for value in (True, 2.0, "2", 2 ** 63):
            self.rejected("PARAMETER_VALUE_INVALID", lambda: param.ParameterValue("integer", value, "count"))

    def test_boolean_exact(self):
        self.assertFalse(param.ParameterValue("boolean", False).value)
        self.rejected("PARAMETER_VALUE_INVALID", lambda: param.ParameterValue("boolean", 0))

    def test_enum_allowed(self):
        design, values, _ = fixture()
        bad = replace(values.assignments[1], value=param.ParameterValue("enumeration", "triangle")) if values.assignments[1].identity.identifier == "style" else next(
            replace(a, value=param.ParameterValue("enumeration", "triangle")) for a in values.assignments if a.identity.identifier == "style")
        self.rejected("PARAMETER_ENUM_NOT_ALLOWED", lambda: param.ParameterSet(design, tuple(bad if a.identity == bad.identity else a for a in values.assignments)))

    def test_missing_required(self):
        design, _, _ = fixture()
        self.rejected("PARAMETER_REQUIRED_MISSING", lambda: param.ParameterSet(design, ()))

    def test_optional_missing_not_false(self):
        _, values, _ = fixture()
        self.assertEqual([p["id"] for p in values.record()["omitted_optional"]], ["enabled"])
        self.assertNotIn("enabled", [a.identity.identifier for a in values.assignments])

    def test_no_defaults(self):
        design, _, _ = fixture()
        self.assertTrue(all(p.record()["default_policy"] == "NO_DEFAULTS" for p in design.parameters))

    def test_undeclared_assignment(self):
        design, values, _ = fixture()
        extra = param.ParameterAssignment(param.ParameterIdentity("unknown"), param.ParameterValue("boolean", True))
        self.rejected("PARAMETER_ASSIGNMENT_UNDECLARED", lambda: param.ParameterSet(design, values.assignments + (extra,)))

    def test_duplicate_assignment(self):
        design, values, _ = fixture()
        for extra in (values.assignments[0], replace(values.assignments[0], value=param.ParameterValue("integer", 3, "count"))):
            self.rejected("PARAMETER_ASSIGNMENT_DUPLICATE", lambda: param.ParameterSet(design, values.assignments + (extra,)))

    def test_kind_mismatch(self):
        design, values, _ = fixture()
        assignments = tuple(replace(a, value=param.ParameterValue("boolean", True)) if a.identity.identifier == "width" else a for a in values.assignments)
        self.rejected("PARAMETER_VALUE_KIND_MISMATCH", lambda: param.ParameterSet(design, assignments))

    def test_unit_mismatch(self):
        design, values, _ = fixture()
        assignments = tuple(replace(a, value=param.ParameterValue("scalar", scalar("20"), "m")) if a.identity.identifier == "width" else a for a in values.assignments)
        self.rejected("PARAMETER_VALUE_UNIT_MISMATCH", lambda: param.ParameterSet(design, assignments))

    def test_range_checks_no_clamp(self):
        design, values, _ = fixture()
        for value in ("0", "101"):
            assignments = tuple(replace(a, value=param.ParameterValue("scalar", scalar(value), "mm")) if a.identity.identifier == "width" else a for a in values.assignments)
            before = tuple(a.record() for a in assignments)
            self.rejected("PARAMETER_RANGE_VIOLATION", lambda: param.ParameterSet(design, assignments))
            self.assertEqual(before, tuple(a.record() for a in assignments))

    def test_invalid_bounds(self):
        self.rejected("PARAMETER_BOUND_INVALID", lambda: param.ParameterDefinition(param.ParameterIdentity("x"), "integer", "count", "count", minimum=2, maximum=1))

    def test_graph_dangling(self):
        design, *_ = fixture()
        edge = param.ParameterReference(param.ParameterIdentity("width"), param.ParameterIdentity("absent"))
        self.rejected("PARAMETER_REFERENCE_MISSING", lambda: replace(design, references=(edge,)))

    def test_graph_duplicate(self):
        design, *_ = fixture()
        self.rejected("PARAMETER_EDGE_DUPLICATE", lambda: replace(design, references=design.references * 2))

    def test_reference_cycles_passive(self):
        design, *_ = fixture()
        edge = design.references[0]
        links = (edge, param.ParameterReference(edge.target, edge.source))
        a, b = replace(design, references=links), replace(design, references=tuple(reversed(links)))
        self.assertEqual(a.fingerprint(), b.fingerprint())
        self.assertTrue(all(e.record()["evaluation"] == "NOT_PERFORMED" for e in a.references))

    def test_permutation_independence(self):
        design, values, variant = fixture()
        other = replace(design, parameters=tuple(reversed(design.parameters)))
        other_values = param.ParameterSet(other, tuple(reversed(values.assignments)), values.provenance)
        self.assertEqual(design.fingerprint(), other.fingerprint())
        self.assertEqual(variant.fingerprint(), param.ParametricVariant(other_values, variant.provenance).fingerprint())

    def test_changed_assignment_new_variant(self):
        design, values, variant = fixture()
        assignments = tuple(replace(a, value=param.ParameterValue("integer", 4, "count")) if a.identity.identifier == "count" else a for a in values.assignments)
        self.assertNotEqual(variant.fingerprint(), param.ParametricVariant(param.ParameterSet(design, assignments)).fingerprint())
        self.assertEqual(values, fixture()[1])

    def test_contract_revision_changes_identity(self):
        design, *_ = fixture()
        changed = replace(design, parameters=tuple(replace(p, required=False) if p.identity.identifier == "count" else p for p in design.parameters))
        self.assertNotEqual(design.fingerprint(), changed.fingerprint())

    def test_presentation_nonsemantic(self):
        design, *_ = fixture()
        changed = replace(design, parameters=tuple(replace(p, presentation="New label") for p in design.parameters))
        self.assertEqual(design.fingerprint(), changed.fingerprint())

    def test_exact_bindings_and_provenance(self):
        design, values, variant = fixture()
        self.assertEqual(values.record()["design_fingerprint"], design.fingerprint())
        self.assertEqual(variant.record()["parameter_set_fingerprint"], values.fingerprint())
        self.assertEqual(variant.record()["provenance"], [r.record() for r in variant.provenance])
        self.assertFalse(variant.record()["geometry_generated"])
        self.assertFalse(variant.record()["engineering_safety_proven"])
        self.assertFalse(variant.record()["grants_authority"])

    def test_passive_representation_reference(self):
        design, *_ = fixture()
        design = replace(design, representations=design.provenance)
        self.assertEqual(design.record()["representations"], [r.record() for r in design.provenance])
        self.assertFalse(design.record()["geometry_generated"])

    def test_artifacts_sdk_interchange(self):
        design, values, variant = fixture()
        for record in (design, values, variant):
            artifact = param.parametric_artifact(record)
            artifact.verify_bytes(sdk._json({"record": record.record(), "record_fingerprint": record.fingerprint()}).encode("utf-8"))
            self.assertEqual(artifact.implementation, design.platform.implementation)
            request = sdk.DomainRequest(design.platform, artifact.operation, artifacts=(artifact,))
            result = sdk.DomainResult(request, "COMPLETE", outputs=(artifact,))
            self.assertEqual(interchange.parse_document(interchange.serialize_document(result)).document, result)

    def test_large_design(self):
        design, *_ = fixture()
        definitions = tuple(param.ParameterDefinition(param.ParameterIdentity("p-" + str(i)), "integer", "count", "count") for i in range(1000))
        assignments = tuple(param.ParameterAssignment(p.identity, param.ParameterValue("integer", i, "count")) for i, p in enumerate(definitions))
        a = replace(design, parameters=definitions, references=())
        b = replace(design, parameters=tuple(reversed(definitions)), references=())
        va = param.ParametricVariant(param.ParameterSet(a, assignments))
        vb = param.ParametricVariant(param.ParameterSet(b, tuple(reversed(assignments))))
        self.assertEqual(va.fingerprint(), vb.fingerprint())

    def test_invalid_diagnostics_order_independent(self):
        design, values, _ = fixture()
        assignments = tuple(replace(a, value=param.ParameterValue("boolean", True)) for a in values.assignments)
        for ordered in (assignments, tuple(reversed(assignments))):
            self.rejected("PARAMETER_VALUE_KIND_MISMATCH", lambda: param.ParameterSet(design, ordered))

    def test_security_static(self):
        tree = ast.parse(Path(param.__file__).read_text(encoding="utf-8"))
        imports = {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
        self.assertEqual(imports, {"dataclasses", "tooling", "tooling.package_manifest"})
        forbidden = {"eval", "exec", "open", "__import__", "compile", "float", "RuntimeEngine", "AuthorityEngine"}
        calls = {n.func.id for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
        self.assertFalse(calls & forbidden)


if __name__ == "__main__":
    unittest.main()
