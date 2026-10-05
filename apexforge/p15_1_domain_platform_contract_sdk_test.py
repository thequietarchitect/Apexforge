"""P15.1 passive SDK foundation, exact frozen package references and boundaries."""
import ast
from dataclasses import FrozenInstanceError, replace
from hashlib import sha256
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tooling.domain_platform as sdk
import tooling.package_manifest as pm


def fixture():
    manifest = pm.PackageManifest(pm.PackageCoordinate("example.sdk", "domain", pm.ExactVersion(1, 0, 0)))
    binding = sdk.ImplementationPackage.from_manifest(manifest)
    descriptor = sdk.DomainPlatformDescriptor(sdk.DomainPlatformIdentity("platform-one", "simulation"),
        binding, pm.ExactVersion(2, 0, 0), ("inspect", "analyze"),
        (sdk.DomainCapability("model.read"), sdk.DomainCapability("model.analyze")))
    air = pm.CanonicalReference("apexforge.air/v1", "air", "A" * 64)
    symbol = pm.SymbolReference("A" * 64, "function", "function:Sample")
    provenance = pm.CanonicalReference("apexforge.provenance/v1", "provenance-scope", "B" * 64)
    request = sdk.DomainRequest(descriptor, "inspect", (air,), (symbol,),
        capabilities=(sdk.DomainCapability("model.read"),), provenance=(provenance,))
    artifact = sdk.DomainArtifact.from_bytes(descriptor, "inspect", "analysis", b"supplied analysis",
        semantic_inputs=request.semantic_inputs, symbols=request.symbols, provenance=(provenance,))
    return manifest, descriptor, request, artifact


class ContractTests(unittest.TestCase):
    def error(self, code, factory):
        with self.assertRaises(sdk.DomainContractError) as caught:
            factory()
        self.assertEqual(caught.exception.code, code)
        self.assertEqual(str(caught.exception), code)

    def test_schema_version_and_unknown_schema(self):
        _, d, r, a = fixture()
        self.assertEqual(d.record()["schema"], "apexforge.domain-platform/v1")
        for obj in (d.identity, r, a, sdk.DomainResult(r, "COMPLETE", (a,))):
            self.error("DOMAIN_SCHEMA_UNSUPPORTED", lambda obj=obj: replace(obj, schema="apexforge.unknown/v2"))

    def test_identity_immutable_and_opaque(self):
        _, d, _, _ = fixture()
        with self.assertRaises(FrozenInstanceError):
            d.identity.identifier = "other"
        for bad in ("", "a@company.org", "https://host", "C:/host", "../host", 1, "é", "name with space"):
            self.error("DOMAIN_PLATFORM_ID_INVALID", lambda bad=bad: sdk.DomainPlatformIdentity(bad, "motion"))

    def test_kinds_are_declarations_only(self):
        for kind in sdk.KINDS:
            self.assertEqual(sdk.DomainPlatformIdentity("fixture", kind).kind, kind)
        self.error("DOMAIN_KIND_INVALID", lambda: sdk.DomainPlatformIdentity("fixture", "unknown"))

    def test_package_binding_exact(self):
        m, d, _, _ = fixture()
        self.assertEqual(d.implementation.coordinate, m.coordinate)
        self.assertEqual(d.implementation.content, m.content_identity())
        self.assertNotEqual(d.identity, d.implementation)
        changed = replace(m, exported_capabilities=("Other.Contract",))
        self.assertNotEqual(sdk.ImplementationPackage.from_manifest(changed), d.implementation)

    def test_invalid_package_binding(self):
        m, d, _, _ = fixture()
        self.error("DOMAIN_PACKAGE_BINDING_INVALID", lambda: sdk.ImplementationPackage(m.coordinate, "A" * 64))
        self.error("DOMAIN_PACKAGE_BINDING_INVALID", lambda: sdk.ImplementationPackage("domain", d.implementation.content))
        self.error("DOMAIN_PACKAGE_BINDING_INVALID", lambda: sdk.ImplementationPackage.from_manifest({}))

    def test_contract_version_distinct_from_package_version(self):
        m, d, _, _ = fixture()
        self.assertNotEqual(d.contract_version, m.coordinate.version)
        self.error("DOMAIN_CONTRACT_VERSION_INVALID", lambda: replace(d, contract_version="2.0.0"))

    def test_descriptor_order_independent(self):
        _, d, _, _ = fixture()
        reversed_d = replace(d, operations=tuple(reversed(d.operations)), capabilities=tuple(reversed(d.capabilities)))
        self.assertEqual(d.canonical_json(), reversed_d.canonical_json())
        self.assertEqual(d.fingerprint(), reversed_d.fingerprint())

    def test_equivalent_independent_inputs(self):
        for a, b in zip(fixture()[1:], fixture()[1:]):
            self.assertEqual(a.canonical_json(), b.canonical_json())
            self.assertEqual(a.fingerprint(), b.fingerprint())

    def test_duplicate_and_malformed_operations(self):
        _, d, _, _ = fixture()
        self.error("DOMAIN_OPERATION_DUPLICATE", lambda: replace(d, operations=("inspect", "inspect")))
        self.error("DOMAIN_OPERATION_INVALID", lambda: replace(d, operations=("../run",)))
        self.error("DOMAIN_OPERATION_INVALID", lambda: replace(d, operations=["inspect"]))

    def test_unknown_operation_does_not_execute(self):
        _, d, r, _ = fixture()
        self.error("DOMAIN_OPERATION_UNDECLARED", lambda: replace(r, operation="execute"))
        self.error("DOMAIN_OPERATION_INVALID", lambda: replace(r, operation=""))
        self.error("DOMAIN_OPERATION_UNDECLARED", lambda: sdk.DomainArtifact.from_bytes(d, "execute", "data", b"x"))

    def test_domain_dependencies_exact_and_unresolved(self):
        _, d, _, _ = fixture()
        dependency = sdk.DomainDependency(sdk.DomainPlatformIdentity("other", "motion"), d.implementation, pm.ExactVersion(1, 0, 0))
        with_dep = replace(d, dependencies=(dependency,))
        self.assertEqual(with_dep.dependencies[0].implementation, d.implementation)
        self.error("DOMAIN_DEPENDENCY_CONFLICT", lambda: replace(d, dependencies=(replace(dependency, platform=d.identity),)))
        self.error("DOMAIN_DEPENDENCY_CONFLICT", lambda: replace(d, dependencies=(dependency, replace(dependency, contract_version=pm.ExactVersion(2, 0, 0)))))

    def test_canonical_semantic_and_symbol_references_preserved(self):
        _, _, r, a = fixture()
        result = sdk.DomainResult(r, "COMPLETE", (a,))
        self.assertEqual(result.record()["semantic_inputs"], [x.record() for x in r.semantic_inputs])
        self.assertEqual(a.symbols[0].identity, "function:Sample")
        self.assertEqual(result.record()["semantic_authority"], "CANONICAL_AIR")

    def test_domain_output_cannot_masquerade_as_air_or_source(self):
        _, _, _, a = fixture()
        for kind in ("air", "source", "native", "unknown"):
            self.error("DOMAIN_CORE_SEMANTIC_BOUNDARY_VIOLATION", lambda kind=kind: replace(a, kind=kind))

    def test_capability_typed_membership_without_grants(self):
        _, d, r, _ = fixture()
        self.assertFalse(r.record()["grants_authority"])
        self.error("DOMAIN_CAPABILITY_INVALID", lambda: replace(d, capabilities=("model.read",)))
        self.error("DOMAIN_CAPABILITY_UNDECLARED", lambda: replace(r, capabilities=(sdk.DomainCapability("other.contract"),)))
        self.error("DOMAIN_CAPABILITY_INVALID", lambda: sdk.DomainCapability("*"))

    def test_agent_principal_and_organization_not_platform_identity(self):
        from agents.model import AgentIdentity
        from authority.model import Principal
        _, d, _, _ = fixture()
        self.assertNotEqual(d.identity, AgentIdentity(d.identity.identifier))
        self.error("DOMAIN_PLATFORM_ID_INVALID", lambda: replace(d, identity=Principal("platform-one")))
        self.assertNotIn("organization", d.record())
        self.assertNotIn("owner", d.record())

    def test_request_input_order_and_immutable_collections(self):
        _, _, r, _ = fixture()
        extra = pm.CanonicalReference("apexforge.source/v1", "source", "C" * 64)
        a = replace(r, semantic_inputs=(extra, *r.semantic_inputs))
        b = replace(r, semantic_inputs=tuple(reversed(a.semantic_inputs)))
        self.assertEqual(a.fingerprint(), b.fingerprint())
        self.error("DOMAIN_INPUT_INVALID", lambda: replace(r, semantic_inputs=[]))
        self.error("DOMAIN_INPUT_INVALID", lambda: replace(r, semantic_inputs=(*r.semantic_inputs, *r.semantic_inputs)))

    def test_provenance_retained_without_attribution(self):
        _, _, r, a = fixture()
        result = sdk.DomainResult(r, "COMPLETE", (a,), provenance=r.provenance)
        self.assertEqual(result.provenance, r.provenance)
        self.assertFalse(result.record()["authenticates_provenance"])
        self.assertNotIn("author", result.record())
        self.error("DOMAIN_PROVENANCE_INVALID", lambda: replace(r, provenance=("publisher",)))

    def test_artifact_integrity(self):
        _, _, _, a = fixture()
        a.verify_bytes(b"supplied analysis")
        self.error("DOMAIN_ARTIFACT_DIGEST_MISMATCH", lambda: a.verify_bytes(b"tampered"))
        self.error("DOMAIN_ARTIFACT_INVALID", lambda: replace(a, digest="a" * 64))
        self.assertEqual(a.digest, sha256(b"supplied analysis").hexdigest().upper())

    def test_artifact_domain_separated_fingerprint(self):
        _, d, _, a = fixture()
        self.assertNotEqual(a.fingerprint(), a.digest)
        self.assertNotEqual(a.fingerprint(), d.implementation.content.fingerprint)
        self.assertEqual(a.fingerprint(), sha256((sdk.DomainArtifact.DOMAIN + "\0" + a.canonical_json()).encode()).hexdigest().upper())

    def test_result_binding_same_coordinate_different_content_rejected(self):
        m, _, r, a = fixture()
        changed = sdk.ImplementationPackage.from_manifest(replace(m, required_capabilities=("Other.Contract",)))
        self.error("DOMAIN_RESULT_BINDING_MISMATCH", lambda: sdk.DomainResult(r, "COMPLETE", (replace(a, implementation=changed),)))
        self.error("DOMAIN_RESULT_BINDING_MISMATCH", lambda: sdk.DomainResult(r, "COMPLETE", (replace(a, operation="analyze"),)))

    def test_result_input_lineage_mismatch(self):
        _, _, r, a = fixture()
        self.error("DOMAIN_RESULT_INPUT_MISMATCH", lambda: sdk.DomainResult(r, "COMPLETE", (replace(a, symbols=()),)))

    def test_result_cannot_cross_contract_revisions(self):
        _, d, r, a = fixture()
        changed = replace(d, contract_version=pm.ExactVersion(3, 0, 0))
        self.error("DOMAIN_RESULT_CONTRACT_MISMATCH", lambda: sdk.DomainResult(replace(r, descriptor=changed), "COMPLETE", (a,)))
        self.error("DOMAIN_RESULT_CONTRACT_MISMATCH", lambda: sdk.DomainResult(r, "COMPLETE", (replace(a, descriptor_fingerprint="C" * 64),)))

    def test_result_status_diagnostics(self):
        _, _, r, a = fixture()
        diagnostic = sdk.DomainDiagnostic("DOMAIN_EVIDENCE_MISSING", "input")
        self.assertEqual(sdk.DomainResult(r, "INCOMPLETE", diagnostics=(diagnostic,)).status, "INCOMPLETE")
        self.error("DOMAIN_RESULT_DIAGNOSTIC_REQUIRED", lambda: sdk.DomainResult(r, "INCOMPLETE"))
        self.error("DOMAIN_RESULT_INVALID", lambda: sdk.DomainResult(r, "FAILED", (a,), (diagnostic,)))
        self.error("DOMAIN_RESULT_INVALID", lambda: sdk.DomainResult(r, "TRUSTED"))
        self.error("DOMAIN_DIAGNOSTIC_INVALID", lambda: sdk.DomainDiagnostic("free-form exception", "input"))

    def test_result_deterministic_diagnostics(self):
        _, _, r, _ = fixture()
        a = sdk.DomainDiagnostic("DOMAIN_EVIDENCE_MISSING", "input")
        b = sdk.DomainDiagnostic("DOMAIN_OPERATION_NOT_EXECUTED", "inspect")
        self.assertEqual(sdk.DomainResult(r, "INCOMPLETE", diagnostics=(a, b)).fingerprint(),
                         sdk.DomainResult(r, "INCOMPLETE", diagnostics=(b, a)).fingerprint())

    def test_models_immutable_records_detached(self):
        _, d, r, a = fixture()
        for obj, field in ((d, "operations"), (r, "operation"), (a, "digest"), (sdk.DomainResult(r, "COMPLETE", (a,)), "status")):
            with self.assertRaises(FrozenInstanceError):
                setattr(obj, field, None)
            before = obj.canonical_json()
            record = obj.record()
            record.clear()
            self.assertEqual(obj.canonical_json(), before)

    def test_correlation_caller_supplied(self):
        _, _, r, _ = fixture()
        self.assertIsNone(r.correlation)
        self.assertEqual(replace(r, correlation="request-one").record()["correlation"], "request-one")
        self.error("DOMAIN_CORRELATION_INVALID", lambda: replace(r, correlation="C:/host"))

    def test_no_hidden_trust_publication_compatibility(self):
        _, d, r, a = fixture()
        result = sdk.DomainResult(r, "COMPLETE", (a,)).record()
        for key in ("trusted", "signature_valid", "published", "authorized", "compatible", "owner"):
            self.assertNotIn(key, result)
            self.assertNotIn(key, d.record())
        self.assertTrue(result["declaration_only"])

    def test_dynamic_no_authority_runtime_solver_registry_process_or_io(self):
        import tooling.package_registry as registry
        import tooling.package_solver as solver
        from authority.engine import AuthorityEngine
        with patch.object(AuthorityEngine, "check", side_effect=AssertionError("authority")), \
             patch.object(registry.RegistryCatalog, "query", side_effect=AssertionError("registry")), \
             patch.object(solver, "solve", side_effect=AssertionError("solver")), \
             patch("builtins.open", side_effect=AssertionError("filesystem")), \
             patch("subprocess.run", side_effect=AssertionError("process")), \
             patch("socket.socket", side_effect=AssertionError("network")):
            m, d, r, a = fixture()
            before = m.canonical_json()
            sdk.DomainResult(r, "COMPLETE", (a,)).fingerprint()
            self.assertEqual(m.canonical_json(), before)

    def test_security_static_audit(self):
        tree = ast.parse(Path(sdk.__file__).read_text(encoding="utf-8"))
        imports = {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
        imports |= {a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
        self.assertEqual(imports, {"dataclasses", "hashlib", "json", "re", "tooling.package_manifest"})
        forbidden = {"open", "exec", "eval", "__import__", "execute", "dispatch", "solve", "publish", "compile", "run", "getenv"}
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                name = node.func.id if isinstance(node.func, ast.Name) else getattr(node.func, "attr", "")
                self.assertNotIn(name, forbidden)

    def test_large_request_and_descriptor_deterministic(self):
        _, d, r, _ = fixture()
        caps = tuple(sdk.DomainCapability("operation.c" + str(i)) for i in range(1000))
        d = replace(d, capabilities=caps, operations=tuple("operation" + str(i) for i in range(1000)))
        other = replace(d, capabilities=tuple(reversed(caps)), operations=tuple(reversed(d.operations)))
        self.assertEqual(d.fingerprint(), other.fingerprint())
        inputs = tuple(pm.CanonicalReference("apexforge.air/v1", "air", sha256(str(i).encode()).hexdigest().upper()) for i in range(1000))
        a = replace(r, descriptor=d, operation="operation0", capabilities=caps, semantic_inputs=inputs)
        b = replace(a, descriptor=other, capabilities=tuple(reversed(caps)), semantic_inputs=tuple(reversed(inputs)))
        self.assertEqual(a.fingerprint(), b.fingerprint())


if __name__ == "__main__":
    unittest.main(verbosity=2)
