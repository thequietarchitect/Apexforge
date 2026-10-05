"""P15.2 explicit portable records, strict admission and passive owner boundaries."""
import ast
from dataclasses import FrozenInstanceError, replace
from hashlib import sha256
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tooling.domain_interchange as exchange
import tooling.domain_platform as sdk
import tooling.package_manifest as pm
import p15_1_domain_platform_contract_sdk_test as fixtures


def objects():
    _, d, r, a = fixtures.fixture()
    result = sdk.DomainResult(r, "COMPLETE", (a,), provenance=r.provenance)
    return d, r, result, a


def wire(record):
    return json.dumps(record, sort_keys=True, separators=(",", ":")).encode("utf-8")


class InterchangeTests(unittest.TestCase):
    def error(self, code, data):
        with self.assertRaises(exchange.DomainInterchangeError) as caught:
            exchange.parse_document(data)
        self.assertEqual(caught.exception.code, code)
        self.assertEqual(str(caught.exception), code)

    def roundtrip(self, obj):
        data = exchange.serialize_document(obj)
        parsed = exchange.parse_document(data)
        self.assertEqual(parsed.document, obj)
        self.assertEqual(parsed.document.canonical_json(), obj.canonical_json())
        self.assertEqual(parsed.document.fingerprint(), obj.fingerprint())
        self.assertEqual(parsed.canonical_bytes(), data)
        return parsed

    def test_versioned_envelope_unknown_schema(self):
        v = exchange.DomainInterchangeEnvelope(objects()[0]).record()
        self.assertEqual(v["schema"], "apexforge.domain-interchange/v1")
        v["schema"] = "apexforge.domain-interchange/v2"
        self.error("DOMAIN_INTERCHANGE_SCHEMA_UNSUPPORTED", wire(v))

    def test_explicit_kinds_unknown_kind(self):
        self.assertEqual(tuple(exchange.DomainInterchangeEnvelope(x).kind for x in objects()),
                         ("platform", "request", "result", "artifact"))
        v = exchange.DomainInterchangeEnvelope(objects()[0]).record()
        for kind in ("simulation", "execute", 1, None, {}):
            v["kind"] = kind
            self.error("DOMAIN_INTERCHANGE_NUMBER_INVALID" if kind == 1 else "DOMAIN_INTERCHANGE_KIND_UNSUPPORTED", wire(v))

    def test_descriptor_roundtrip_dependencies_provenance(self):
        d, r, _, _ = objects()
        dep = sdk.DomainDependency(sdk.DomainPlatformIdentity("other", "motion"), d.implementation, pm.ExactVersion(1, 0, 0))
        self.roundtrip(replace(d, dependencies=(dep,), provenance=r.provenance))

    def test_request_roundtrip_all_fields(self):
        _, r, _, a = objects()
        self.roundtrip(replace(r, artifacts=(a,), correlation="caller-token"))

    def test_result_roundtrip_carries_exact_request(self):
        d, r, _, a = objects()
        r = replace(r, artifacts=(a,), correlation="caller-token")
        result = sdk.DomainResult(r, "COMPLETE", (a,), provenance=r.provenance)
        parsed = self.roundtrip(result)
        self.assertEqual(parsed.document.request, r)
        self.assertEqual(parsed.record()["support"], r.record())
        self.assertEqual(parsed.record()["descriptor_fingerprint"], d.fingerprint())

    def test_artifact_roundtrip_retains_identity(self):
        d, _, _, a = objects()
        parsed = self.roundtrip(a)
        self.assertEqual(parsed.document.descriptor_fingerprint, d.fingerprint())
        self.assertEqual(parsed.document.digest, a.digest)

    def test_independent_equivalent_construction(self):
        for a, b in zip(objects(), objects()):
            self.assertEqual(exchange.serialize_document(a), exchange.serialize_document(b))

    def test_declaration_permutation_canonicalizes(self):
        d, r, _, _ = objects()
        d = replace(d, operations=tuple(reversed(d.operations)), capabilities=tuple(reversed(d.capabilities)))
        self.assertEqual(exchange.serialize_document(d), exchange.serialize_document(objects()[0]))
        v = exchange.DomainInterchangeEnvelope(r).record()
        v["payload"]["descriptor"]["operations"].reverse()
        v["payload"]["descriptor"]["capabilities"].reverse()
        self.assertEqual(exchange.parse_document(wire(v)).canonical_bytes(), exchange.serialize_document(r))

    def test_duplicate_keys_root_nested_and_escaped(self):
        self.error("DOMAIN_INTERCHANGE_DUPLICATE_KEY", b'{"schema":"x","schema":"y"}')
        self.error("DOMAIN_INTERCHANGE_DUPLICATE_KEY", b'{"x":{"id":"one","id":"two"}}')
        self.error("DOMAIN_INTERCHANGE_DUPLICATE_KEY", b'{"x":false,"\\u0078":true}')

    def test_malformed_json_and_utf8(self):
        for raw in (b"", b"{", b"{}{}", b"[", b"\xff", b'\xef\xbb\xbf{}', b'{"x":"\x00"}'):
            self.error("DOMAIN_INTERCHANGE_MALFORMED", raw)

    def test_unknown_fields_all_levels(self):
        v = exchange.DomainInterchangeEnvelope(objects()[0]).record()
        for where in ("envelope", "payload", "identity", "coordinate"):
            copy = json.loads(json.dumps(v))
            target = copy if where == "envelope" else copy["payload"] if where == "payload" else copy["payload"]["identity"] if where == "identity" else copy["payload"]["implementation"]["coordinate"]
            target["owner"] = "untrusted"
            self.error("DOMAIN_INTERCHANGE_FIELD_INVALID", wire(copy))

    def test_missing_required_fields(self):
        v = exchange.DomainInterchangeEnvelope(objects()[0]).record()
        for field in v:
            copy = dict(v)
            del copy[field]
            self.error("DOMAIN_INTERCHANGE_FIELD_INVALID", wire(copy))
        del v["payload"]["provenance"]
        self.error("DOMAIN_INTERCHANGE_FIELD_INVALID", wire(v))

    def test_malformed_fingerprints(self):
        for key in ("payload_fingerprint", "descriptor_fingerprint"):
            v = exchange.DomainInterchangeEnvelope(objects()[0]).record()
            v[key] = "a" * 64
            self.error("DOMAIN_INTERCHANGE_FINGERPRINT_INVALID", wire(v))

    def test_descriptor_revision_tamper(self):
        v = exchange.DomainInterchangeEnvelope(objects()[1]).record()
        v["descriptor_fingerprint"] = "C" * 64
        self.error("DOMAIN_INTERCHANGE_DESCRIPTOR_MISMATCH", wire(v))
        v = exchange.DomainInterchangeEnvelope(objects()[2]).record()
        v["payload"]["outputs"][0]["descriptor_fingerprint"] = "C" * 64
        self.error("DOMAIN_RESULT_CONTRACT_MISMATCH", wire(v))

    def test_package_binding_exact_and_tamper(self):
        d = objects()[0]
        p = self.roundtrip(d).document.implementation
        self.assertEqual(p.coordinate, d.implementation.coordinate)
        self.assertEqual(p.content, d.implementation.content)
        for field, value in (("name", "different"), ("version", "1.0.1")):
            v = exchange.DomainInterchangeEnvelope(d).record()
            v["payload"]["implementation"]["coordinate"][field] = value
            self.error("DOMAIN_INTERCHANGE_DESCRIPTOR_MISMATCH", wire(v))
        v = exchange.DomainInterchangeEnvelope(d).record()
        v["payload"]["implementation"]["content"]["fingerprint"] = "C" * 64
        self.error("DOMAIN_INTERCHANGE_DESCRIPTOR_MISMATCH", wire(v))

    def test_malformed_package_rejected_by_owner(self):
        v = exchange.DomainInterchangeEnvelope(objects()[0]).record()
        v["payload"]["implementation"]["coordinate"]["version"] = "latest"
        self.error("DOMAIN_INTERCHANGE_REFERENCE_OR_PACKAGE_INVALID", wire(v))

    def test_platform_identity_kind_preserved_and_invalid(self):
        d = objects()[0]
        self.assertEqual(self.roundtrip(d).document.identity, d.identity)
        v = exchange.DomainInterchangeEnvelope(d).record()
        v["payload"]["identity"]["id"] = "../host"
        self.error("DOMAIN_PLATFORM_ID_INVALID", wire(v))
        v["payload"]["identity"]["id"] = "other"
        v["payload"]["identity"]["kind"] = "unknown"
        self.error("DOMAIN_KIND_INVALID", wire(v))

    def test_unknown_operation_validated_before_hash(self):
        v = exchange.DomainInterchangeEnvelope(objects()[1]).record()
        v["payload"]["operation"] = "execute"
        self.error("DOMAIN_OPERATION_UNDECLARED", wire(v))
        v["payload"]["operation"] = "../execute"
        self.error("DOMAIN_OPERATION_INVALID", wire(v))

    def test_air_and_symbol_identity_preserved_tamper_detected(self):
        r = objects()[1]
        parsed = self.roundtrip(r).document
        self.assertEqual(parsed.semantic_inputs, r.semantic_inputs)
        self.assertEqual(parsed.symbols, r.symbols)
        v = exchange.DomainInterchangeEnvelope(r).record()
        v["payload"]["semantic_inputs"][0]["fingerprint"] = "C" * 64
        self.error("DOMAIN_INTERCHANGE_PAYLOAD_FINGERPRINT_MISMATCH", wire(v))
        v["payload"]["semantic_inputs"][0]["fingerprint"] = "bad"
        self.error("DOMAIN_INTERCHANGE_REFERENCE_OR_PACKAGE_INVALID", wire(v))

    def test_capability_declarations_remain_typed_without_authority(self):
        r = objects()[1]
        parsed = self.roundtrip(r).document
        self.assertEqual(type(parsed.capabilities[0]), sdk.DomainCapability)
        self.assertFalse(parsed.capabilities[0].record()["grants_authority"])
        v = exchange.DomainInterchangeEnvelope(r).record()
        v["payload"]["capabilities"][0]["domain_capability"] = "other.contract"
        self.error("DOMAIN_CAPABILITY_UNDECLARED", wire(v))
        v = exchange.DomainInterchangeEnvelope(r).record()
        v["payload"]["capabilities"][0]["grants_authority"] = True
        self.error("DOMAIN_INTERCHANGE_BINDING_MISMATCH", wire(v))

    def test_provenance_preserved_tamper_no_attribution(self):
        result = objects()[2]
        parsed = self.roundtrip(result).document
        self.assertEqual(parsed.provenance, result.provenance)
        self.assertFalse(parsed.record()["authenticates_provenance"])
        v = exchange.DomainInterchangeEnvelope(result).record()
        v["payload"]["provenance"][0]["fingerprint"] = "C" * 64
        self.error("DOMAIN_INTERCHANGE_PAYLOAD_FINGERPRINT_MISMATCH", wire(v))

    def test_result_projection_contradictions_rejected(self):
        for field, value in (("operation", "analyze"), ("declaration_only", False),
                             ("semantic_authority", "DOMAIN"), ("grants_authority", True)):
            v = exchange.DomainInterchangeEnvelope(objects()[2]).record()
            v["payload"][field] = value
            self.error("DOMAIN_INTERCHANGE_BINDING_MISMATCH", wire(v))

    def test_result_status_diagnostic_roundtrip_and_tamper(self):
        r = objects()[1]
        diagnostic = sdk.DomainDiagnostic("DOMAIN_EVIDENCE_MISSING", "input")
        for status in ("INCOMPLETE", "FAILED"):
            self.roundtrip(sdk.DomainResult(r, status, diagnostics=(diagnostic,)))
        v = exchange.DomainInterchangeEnvelope(sdk.DomainResult(r, "INCOMPLETE", diagnostics=(diagnostic,))).record()
        v["payload"]["diagnostics"][0]["code"] = "unrecognized"
        self.error("DOMAIN_DIAGNOSTIC_INVALID", wire(v))

    def test_result_requires_exact_support_request(self):
        v = exchange.DomainInterchangeEnvelope(objects()[2]).record()
        v["support"] = None
        self.error("DOMAIN_INTERCHANGE_FIELD_INVALID", wire(v))
        v = exchange.DomainInterchangeEnvelope(objects()[2]).record()
        v["support"]["correlation"] = "different"
        self.error("DOMAIN_INTERCHANGE_REQUEST_MISMATCH", wire(v))
        v = exchange.DomainInterchangeEnvelope(objects()[0]).record()
        v["support"] = objects()[1].record()
        self.error("DOMAIN_INTERCHANGE_FIELD_INVALID", wire(v))

    def test_artifact_tamper_and_package_artifact_distinction(self):
        v = exchange.DomainInterchangeEnvelope(objects()[3]).record()
        v["payload"]["kind"] = "native"
        self.error("DOMAIN_CORE_SEMANTIC_BOUNDARY_VIOLATION", wire(v))
        v = exchange.DomainInterchangeEnvelope(objects()[3]).record()
        v["payload"]["digest"] = "C" * 64
        self.error("DOMAIN_INTERCHANGE_PAYLOAD_FINGERPRINT_MISMATCH", wire(v))

    def test_envelope_fingerprint_domain_separated(self):
        for obj in objects():
            e = exchange.DomainInterchangeEnvelope(obj)
            self.assertEqual(e.fingerprint(), sha256(exchange.SCHEMA.encode() + b"\0" + e.canonical_bytes()).hexdigest().upper())
            self.assertNotEqual(e.fingerprint(), obj.fingerprint())
            self.assertEqual(e.record()["payload_fingerprint"], obj.fingerprint())

    def test_payload_checksum_not_authentication(self):
        d = objects()[0]
        changed = replace(d, identity=replace(d.identity, identifier="different"))
        parsed = self.roundtrip(changed)
        self.assertNotEqual(parsed.document.fingerprint(), d.fingerprint())
        self.assertNotIn("trusted", parsed.record())
        self.assertNotIn("owner", parsed.record())
        # A coherent new document is valid data; checksums do not authenticate its origin.

    def test_immutable_parsed_models_and_detached_records(self):
        e = self.roundtrip(objects()[2])
        with self.assertRaises(FrozenInstanceError):
            e.schema = "other"
        with self.assertRaises(FrozenInstanceError):
            e.document.status = "other"
        old = e.canonical_bytes()
        e.record()["payload"].clear()
        self.assertEqual(e.canonical_bytes(), old)

    def test_only_caller_supplied_bytes(self):
        for value in ("{}", bytearray(b"{}"), memoryview(b"{}"), None, Path("file.json")):
            self.error("DOMAIN_INTERCHANGE_BYTES_REQUIRED", value)

    def test_invalid_numbers_constants_exponents(self):
        for token in ("0", "-0", "1.0", "1e3", "1e999999", "NaN", "Infinity", "-Infinity", "9" * 10000):
            self.error("DOMAIN_INTERCHANGE_NUMBER_INVALID", ('{"x":' + token + '}').encode())

    def test_string_utf8_surrogates_and_bounds(self):
        self.error("DOMAIN_INTERCHANGE_STRING_INVALID", b'{"x":"\\ud800"}')
        self.error("DOMAIN_INTERCHANGE_STRING_INVALID", b'{"\\udfff":false}')
        self.error("DOMAIN_INTERCHANGE_LIMIT_EXCEEDED", wire({"x": "a" * (exchange.MAX_STRING + 1)}))
        self.error("DOMAIN_INTERCHANGE_MALFORMED", b'{"x":"\\uZZZZ"}')

    def test_byte_depth_list_and_node_limits(self):
        self.error("DOMAIN_INTERCHANGE_LIMIT_EXCEEDED", b" " * (exchange.MAX_BYTES + 1))
        self.error("DOMAIN_INTERCHANGE_LIMIT_EXCEEDED", b"[" * (exchange.MAX_DEPTH + 1))
        self.error("DOMAIN_INTERCHANGE_LIMIT_EXCEEDED", wire([None] * (exchange.MAX_LIST + 1)))
        with patch.object(exchange, "MAX_NODES", 2):
            self.error("DOMAIN_INTERCHANGE_LIMIT_EXCEEDED", wire({"x": [None]}))

    def test_exact_version_boundary_no_arbitrary_numeric_cap(self):
        d = objects()[0]
        version = pm.ExactVersion(2147483647, 2147483647, 2147483647)
        self.roundtrip(replace(d, contract_version=version,
            implementation=replace(d.implementation, coordinate=replace(d.implementation.coordinate, version=version))))

    def test_duplicate_declarations_not_silently_deduplicated(self):
        v = exchange.DomainInterchangeEnvelope(objects()[0]).record()
        v["payload"]["operations"] = ["inspect", "inspect"]
        self.error("DOMAIN_OPERATION_DUPLICATE", wire(v))

    def test_invalid_unordered_elements_have_order_independent_diagnostics(self):
        v = exchange.DomainInterchangeEnvelope(objects()[1]).record()
        bad_reference = dict(v["payload"]["semantic_inputs"][0], fingerprint="bad")
        unknown_field = dict(v["payload"]["semantic_inputs"][0], extra="unexpected")
        codes = []
        for references in ([bad_reference, unknown_field], [unknown_field, bad_reference]):
            v["payload"]["semantic_inputs"] = references
            with self.assertRaises(exchange.DomainInterchangeError) as caught:
                exchange.parse_document(wire(v))
            codes.append(caught.exception.code)
        self.assertEqual(codes[0], codes[1])

    def test_whitespace_key_order_noncanonical_bytes_normalized(self):
        e = exchange.DomainInterchangeEnvelope(objects()[0])
        data = json.dumps(e.record(), indent=2).encode()
        self.assertNotEqual(e.canonical_bytes(), data)
        self.assertEqual(exchange.parse_document(data).canonical_bytes(), e.canonical_bytes())

    def test_boundary_flags_not_numeric_false_or_authority(self):
        v = exchange.DomainInterchangeEnvelope(objects()[1]).record()
        v["payload"]["grants_authority"] = 0
        self.error("DOMAIN_INTERCHANGE_NUMBER_INVALID", wire(v))

    def test_dynamic_no_io_authority_solver_runtime(self):
        from authority.engine import AuthorityEngine
        import tooling.package_solver as solver
        import tooling.package_registry as registry
        data = exchange.serialize_document(objects()[2])
        with patch.object(AuthorityEngine, "check", side_effect=AssertionError("authority")), \
             patch.object(solver, "solve", side_effect=AssertionError("solver")), \
             patch.object(registry.RegistryCatalog, "query", side_effect=AssertionError("registry")), \
             patch("builtins.open", side_effect=AssertionError("filesystem")), \
             patch("subprocess.run", side_effect=AssertionError("process")), \
             patch("socket.socket", side_effect=AssertionError("network")):
            self.assertTrue(exchange.parse_document(data).document.record()["declaration_only"])

    def test_security_static_audit(self):
        tree = ast.parse(Path(exchange.__file__).read_text(encoding="utf-8"))
        imports = {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
        imports |= {a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
        self.assertEqual(imports, {"dataclasses", "hashlib", "json", "re", "tooling", "tooling.package_manifest"})
        for n in ast.walk(tree):
            if isinstance(n, ast.Call):
                name = n.func.id if isinstance(n.func, ast.Name) else getattr(n.func, "attr", "")
                self.assertNotIn(name, {"eval", "exec", "__import__", "open", "execute", "dispatch", "compile", "run", "solve", "publish", "load"})

    def test_1000_reference_roundtrip_deterministic(self):
        d, r, _, _ = objects()
        references = tuple(pm.CanonicalReference("apexforge.air/v1", "air", sha256(str(i).encode()).hexdigest().upper()) for i in range(1000))
        artifacts = tuple(sdk.DomainArtifact.from_bytes(d, "inspect", "data", str(i).encode()) for i in range(1000))
        request = replace(r, semantic_inputs=references, artifacts=artifacts)
        reversed_request = replace(request, semantic_inputs=tuple(reversed(references)), artifacts=tuple(reversed(artifacts)))
        self.assertEqual(exchange.serialize_document(request), exchange.serialize_document(reversed_request))
        self.roundtrip(request)


if __name__ == "__main__":
    unittest.main(verbosity=2)
