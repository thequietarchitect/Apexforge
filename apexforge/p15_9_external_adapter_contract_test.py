"""Offline exact provider/request/response bindings and security boundaries."""
import ast
from dataclasses import replace, FrozenInstanceError
from hashlib import sha256
from pathlib import Path
import unittest
from tooling import external_adapter as ext
from tooling import domain_platform as sdk
from tooling import domain_interchange as wire
import p15_3_apexmotion_domain_contract_test as fixtures


def fixture():
    manifest, _, state, *_ = fixtures.fixture()
    provider = ext.ExternalProviderIdentity("provider-one")
    descriptor = ext.ExternalAdapterDescriptor(ext.ExternalAdapterIdentity("adapter-one"), provider,
        ext.external_platform(manifest), (ext.ExternalOperation("external.query", True),), provenance=state.provenance)
    request = ext.ExternalRequest(descriptor, "external.query", "correlation-one", inputs=state.provenance,
        provenance=state.provenance)
    response = ext.ExternalResponse(request, request.fingerprint(), provider, request.correlation,
        "REPORTED_SUCCESS", outputs=state.provenance, provenance=state.provenance)
    return descriptor, request, response


class ExternalTests(unittest.TestCase):
    def rejected(self, code, fn):
        with self.assertRaises(ext.ExternalContractError) as caught:
            fn()
        self.assertEqual(caught.exception.code, code)

    def test_platform_package(self):
        d, _, _ = fixture()
        self.assertEqual(d.platform.identity, ext.PLATFORM)
        self.assertEqual(d.platform.implementation, sdk.ImplementationPackage.from_manifest(fixtures.fixture()[0]))

    def test_identity_domains(self):
        d, _, _ = fixture()
        self.assertNotEqual(d.identity, d.provider)
        self.assertNotEqual(d.identity, d.platform.identity)
        self.assertNotEqual(d.provider, d.platform.implementation)
        self.rejected("EXTERNAL_IDENTITY_INVALID", lambda: ext.ExternalProviderIdentity("person@email"))

    def test_immutable_models(self):
        d, q, r = fixture()
        for obj, field in ((d, "identity"), (q, "correlation"), (r, "status"), (d.provider, "identifier")):
            with self.assertRaises(FrozenInstanceError):
                setattr(obj, field, "changed")

    def test_unknown_schemas(self):
        for obj in fixture():
            self.rejected("EXTERNAL_SCHEMA_UNSUPPORTED", lambda obj=obj: replace(obj, schema="unknown"))

    def test_unknown_operation(self):
        self.rejected("EXTERNAL_OPERATION_UNDECLARED", lambda: replace(fixture()[1], operation="external.execute"))

    def test_operation_permutation(self):
        d, _, _ = fixture()
        ops = (ext.ExternalOperation("external.submit"), ext.ExternalOperation("external.query", True))
        self.assertEqual(replace(d, operations=ops).fingerprint(), replace(d, operations=ops[::-1]).fingerprint())

    def test_conflicting_operations(self):
        d, _, _ = fixture()
        self.rejected("EXTERNAL_OPERATION_INVALID", lambda: replace(d, operations=(
            ext.ExternalOperation("external.query"), ext.ExternalOperation("external.query", True))))

    def test_capability_requirement_is_explicit(self):
        d, q, _ = fixture()
        cap = sdk.DomainCapability("external.query")
        d = replace(d, capabilities=(cap,))
        self.rejected("EXTERNAL_CAPABILITY_REQUIREMENT_MISMATCH", lambda: replace(q, descriptor=d))
        admitted = replace(q, descriptor=d, capabilities=(cap,))
        self.assertFalse(admitted.record()["execution_permission"])

    def test_credential_reference(self):
        d, q, _ = fixture()
        credential = ext.CredentialReference("credential-one", "token-reference", d.provider, ("query",))
        d = replace(d, credential_kinds=("token-reference",))
        self.rejected("EXTERNAL_CREDENTIAL_REFERENCE_MISSING", lambda: replace(q, descriptor=d))
        q = replace(q, descriptor=d, credential=credential)
        self.assertEqual(q.credential.scopes, ("query",))
        self.assertNotIn("value", credential.record())
        with self.assertRaises(TypeError):
            ext.CredentialReference("credential", "token-reference", d.provider, value="secret")

    def test_cross_provider_credential(self):
        d, q, _ = fixture()
        c = ext.CredentialReference("credential", "token-reference", ext.ExternalProviderIdentity("other"))
        self.rejected("EXTERNAL_CREDENTIAL_BINDING_INVALID", lambda: replace(q,
            descriptor=replace(d, credential_kinds=("token-reference",)), credential=c))

    def test_request_exact_revision(self):
        d, q, _ = fixture()
        changed = replace(q, descriptor=replace(d, operations=(ext.ExternalOperation("external.query"),)))
        self.assertNotEqual(q.fingerprint(), changed.fingerprint())
        self.assertEqual(q.record()["descriptor"], d.fingerprint())

    def test_request_determinism(self):
        self.assertEqual(fixture()[1].canonical_json(), fixture()[1].canonical_json())
        self.assertEqual(fixture()[1].fingerprint(), fixture()[1].fingerprint())

    def test_response_admission(self):
        _, q, r = fixture()
        self.assertIs(ext.admit_response(q, r), r)
        self.assertEqual(r.record()["evidence"], "EXTERNALLY_SUPPLIED")
        self.assertFalse(r.record()["authenticated"])

    def test_cross_request_substitution(self):
        _, q, r = fixture()
        self.rejected("EXTERNAL_RESPONSE_BINDING_MISMATCH", lambda: ext.admit_response(replace(q, correlation="other"), r))

    def test_response_binding_tampering(self):
        _, _, r = fixture()
        for field, value in (("provider", ext.ExternalProviderIdentity("other")),
                ("correlation", "other"), ("request_fingerprint", "A" * 64)):
            self.rejected("EXTERNAL_RESPONSE_BINDING_MISMATCH", lambda field=field, value=value: replace(r, **{field: value}))

    def test_malformed_fingerprint(self):
        self.rejected("EXTERNAL_FINGERPRINT_INVALID", lambda: replace(fixture()[2], request_fingerprint="bad"))

    def test_status_is_reported(self):
        self.rejected("EXTERNAL_RESPONSE_STATUS_INVALID", lambda: replace(fixture()[2], status="AUTHENTICATED_SUCCESS"))
        self.assertEqual(fixture()[2].status, "REPORTED_SUCCESS")

    def test_diagnostics_bounded_codes(self):
        self.rejected("EXTERNAL_DIAGNOSTIC_INVALID", lambda: replace(fixture()[2], diagnostics=("arbitrary prose",)))
        r = replace(fixture()[2], diagnostics=("EVIDENCE_MISSING",))
        self.assertEqual(r.record()["diagnostics"], ["EVIDENCE_MISSING"])

    def test_payload_integrity(self):
        data = b"untrusted supplied bytes"
        p = ext.ExternalPayload(sha256(data).hexdigest().upper(), data)
        self.assertFalse(p.record()["interpreted"])
        self.rejected("EXTERNAL_BYTES_INTEGRITY_FAILED", lambda: replace(p, data=b"tampered"))

    def test_payload_bounds(self):
        self.rejected("EXTERNAL_BYTES_INVALID", lambda: ext.ExternalPayload("A" * 64, b"x" * (ext.MAX_BYTES + 1)))
        self.rejected("EXTERNAL_COLLECTION_INVALID", lambda: replace(fixture()[1], inputs=(None,)))

    def test_duplicate_reference(self):
        q = fixture()[1]
        self.rejected("EXTERNAL_COLLECTION_DUPLICATE", lambda: replace(q, inputs=q.inputs + q.inputs))

    def test_provenance_preserved(self):
        d, q, r = fixture()
        self.assertEqual(d.provenance, q.provenance)
        self.assertEqual(q.provenance, r.provenance)

    def test_retry_is_passive_exact_identity(self):
        q = fixture()[1]
        self.assertIs(ext.retry_request(q), q)
        self.assertEqual(ext.retry_request(q).fingerprint(), q.fingerprint())

    def test_idempotency_not_inferred(self):
        self.assertFalse(ext.ExternalOperation("external.query").idempotent)

    def test_generic_interchange_owner(self):
        for record in fixture():
            artifact = ext.domain_artifact(record)
            artifact.verify_bytes(record.canonical_json().encode("utf-8"))
            self.assertEqual(artifact.digest, sha256(record.canonical_json().encode("utf-8")).hexdigest().upper())
            restored = wire.parse_document(wire.serialize_document(artifact)).document
            self.assertEqual(artifact, restored)
            self.assertEqual(artifact.implementation, fixture()[0].platform.implementation)

    def test_fingerprints_separate(self):
        d, q, r = fixture()
        self.assertEqual(len({d.fingerprint(), q.fingerprint(), r.fingerprint(), ext.domain_artifact(r).fingerprint()}), 4)
        self.assertEqual(r.record()["semantic_authority"], "CANONICAL_AIR")

    def test_scale_determinism(self):
        _, q, _ = fixture()
        def records():
            result = []
            for index in range(1000):
                request = replace(q, correlation="correlation-" + str(index))
                response = ext.ExternalResponse(request, request.fingerprint(), request.descriptor.provider,
                    request.correlation, "REPORTED_PENDING")
                result.append(ext.admit_response(request, response).fingerprint())
            return result
        self.assertEqual(records(), records())

    def test_static_security(self):
        source = Path(ext.__file__).read_text(encoding="utf-8")
        tree = ast.parse(source)
        imports = {n.names[0].name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import)}
        self.assertTrue(imports <= {"re"})
        modules = {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
        self.assertEqual(modules, {"dataclasses", "hashlib", "tooling", "tooling.package_manifest"})
        calls = {n.func.id for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
        self.assertFalse(calls & {"eval", "exec", "open", "__import__", "getattr_secret", "print"})
        self.assertFalse(any(isinstance(n, (ast.While, ast.AsyncFunctionDef)) for n in ast.walk(tree)))


if __name__ == "__main__":
    unittest.main()
