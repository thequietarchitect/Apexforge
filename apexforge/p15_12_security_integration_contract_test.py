"""Exact node security gate evidence; no workload execution in this suite."""
import ast
from dataclasses import replace, fields, FrozenInstanceError
from pathlib import Path
from hashlib import sha256
import unittest
from unittest.mock import patch

from authority.engine import AuthorityEngine
from authority.model import Principal, AuthorityGrant, AuthorityCheck
from tooling import security_integration as sec
from tooling import cross_domain_orchestration as orch, domain_governance as gov, domain_platform as sdk
from tooling import package_trust as trust
from tooling.package_manifest import PackageManifest, PackageCoordinate, ExactVersion, ContentDescriptor, PackagePath
import p15_11_cross_domain_orchestration_contract_test as predecessor


def fixture(kind="parametric"):
    plan = predecessor.fixture((kind,))
    node = plan.nodes[0]
    check = AuthorityCheck("check:operation", "principal:reviewer", "domain.operation.review",
        "protected:operation-one")
    policy = sec.SecurityAdmissionPolicy("security-one", ExactVersion(1,0,0), plan.fingerprint(), node.fingerprint(),
        check, require_package_trust=False)
    authority = AuthorityEngine((AuthorityGrant(check.principal, check.capability, check.resource),))
    manifest = PackageManifest(PackageCoordinate("example.domains", kind, ExactVersion(1,0,0)))
    package = sec.PackageSecurityEvidence(manifest, ())
    return sec.SecurityAdmissionRequest(policy, plan, node, Principal(check.principal), check, authority, package,
        (predecessor.REFERENCE,))


def rebind(r, plan, node):
    return replace(r, plan=plan, node=node, policy=replace(r.policy,
        plan_fingerprint=plan.fingerprint(), node_fingerprint=node.fingerprint()))


class SecurityTests(unittest.TestCase):
    def error(self, code, fn):
        with self.assertRaises(sec.SecurityIntegrationError) as caught:
            fn()
        self.assertEqual(caught.exception.code, code)
        self.assertEqual(str(caught.exception), code)

    def outcome(self, r, status, code=None):
        d = sec.SecurityAdmissionDecision(r)
        self.assertEqual(d.status, status)
        if code:
            self.assertIn(code, {f.code for f in d.findings})
        return d

    def test_admissible_is_preexecution_only(self):
        r = fixture()
        d = self.outcome(r,"ADMISSIBLE")
        self.assertEqual(d.findings,())
        record = d.record()
        self.assertEqual(record["execution"],"NOT_PERFORMED")
        self.assertFalse(record["grants_authority"])
        self.assertFalse(record["cryptographic_trust_established"])
        self.assertEqual(record["authority_integration"],"DIRECT_CHECK")
        self.assertEqual(record["semantic_authority"],"CANONICAL_AIR")

    def test_immutable_models(self):
        r=fixture()
        d=sec.SecurityAdmissionDecision(r)
        for obj in (r,r.policy,r.package,d,sec.SecurityFinding("SECURITY_AUTHORITY_MISSING","authority","MISSING")):
            with self.subTest(model=type(obj).__name__),self.assertRaises(FrozenInstanceError):
                setattr(obj,fields(obj)[0].name,None)
        record=d.record()
        record["evidence_matrix"]["authority"]="DENIED"
        self.assertEqual(d.record()["evidence_matrix"]["authority"],"SATISFIED")

    def test_policy_bounded_fields(self):
        r=fixture()
        self.error("SECURITY_POLICY_INVALID",lambda:replace(r.policy,require_integrity=1))
        self.assertTrue(r.policy.record()["require_authority"])
        self.assertTrue(r.policy.record()["require_governance"])
        self.assertFalse(r.policy.record()["grants_authority"])
        self.assertFalse(hasattr(r.policy,"evaluate_expression"))

    def test_policy_revision_bound(self):
        r=fixture()
        q=replace(r,policy=replace(r.policy,version=ExactVersion(2,0,0)))
        self.assertNotEqual(r.policy.fingerprint(),q.policy.fingerprint())
        self.assertNotEqual(r.fingerprint(),q.fingerprint())
        self.assertNotEqual(sec.SecurityAdmissionDecision(r).fingerprint(),sec.SecurityAdmissionDecision(q).fingerprint())

    def test_exact_plan_revision(self):
        r=fixture()
        q=replace(r,plan=replace(r.plan,identity=orch.OrchestrationPlanIdentity("other-plan")))
        self.outcome(q,"DENIED","SECURITY_PLAN_MISMATCH")
        self.assertNotEqual(r.fingerprint(),q.fingerprint())

    def test_exact_node_revision(self):
        r=fixture()
        q=replace(r,node=replace(r.node,identifier="other-node"))
        self.outcome(q,"DENIED","SECURITY_NODE_MISMATCH")
        self.assertNotEqual(r.fingerprint(),q.fingerprint())

    def test_changed_operation_requires_new_admission(self):
        r=fixture()
        n=replace(r.node,operation=r.node.descriptor.operations[-1])
        self.outcome(replace(r,node=n),"DENIED","SECURITY_NODE_MISMATCH")

    def test_exact_governance(self):
        r=fixture()
        candidate=replace(r.node.registration.candidate,contract=None)
        registration=gov.evaluate(r.plan.catalog.policy,candidate)
        self.assertEqual(registration.status,"ADMISSIBLE")
        n=replace(r.node,registration=registration)
        plan=replace(r.plan,nodes=(n,))
        self.outcome(rebind(r,plan,n),"DENIED","SECURITY_GOVERNANCE_MISMATCH")

    def test_governance_absent(self):
        r=fixture()
        plan=replace(r.plan,catalog=replace(r.plan.catalog,entries=()))
        self.outcome(rebind(r,plan,r.node),"DENIED","SECURITY_GOVERNANCE_MISMATCH")

    def test_governance_rejected(self):
        r=fixture()
        registration=gov.evaluate(r.plan.catalog.policy,replace(r.node.registration.candidate,claims=("authority-grant",)))
        n=replace(r.node,registration=registration)
        plan=replace(r.plan,nodes=(n,))
        self.outcome(rebind(r,plan,n),"DENIED","SECURITY_GOVERNANCE_MISMATCH")

    def test_invalid_orchestration_not_repaired(self):
        r=fixture()
        n=replace(r.node,operation="unknown.operation")
        plan=replace(r.plan,nodes=(n,))
        self.outcome(rebind(r,plan,n),"DENIED","SECURITY_ORCHESTRATION_INVALID")
        self.assertEqual(n.operation,"unknown.operation")

    def test_incomplete_orchestration(self):
        r=fixture()
        n=replace(r.node,inputs=(orch.InputSlot("input",r.node.outputs[0].contract),))
        plan=replace(r.plan,nodes=(n,))
        self.outcome(rebind(r,plan,n),"INCOMPLETE","SECURITY_ORCHESTRATION_INCOMPLETE")

    def test_descriptor_revision_mismatch(self):
        r=fixture()
        n=replace(r.node,descriptor=replace(r.node.descriptor,contract_version=ExactVersion(2,0,0)))
        plan=replace(r.plan,nodes=(n,))
        self.outcome(rebind(r,plan,n),"DENIED","SECURITY_DESCRIPTOR_MISMATCH")

    def test_package_content_revision_mismatch(self):
        r=fixture()
        package=replace(r.node.descriptor.implementation,content=replace(r.node.descriptor.implementation.content,
            fingerprint="B"*64))
        n=replace(r.node,descriptor=replace(r.node.descriptor,implementation=package))
        plan=replace(r.plan,nodes=(n,))
        q=rebind(r,plan,n)
        self.outcome(q,"DENIED","SECURITY_PACKAGE_MISMATCH")
        self.assertNotEqual(r.fingerprint(),q.fingerprint())

    def test_package_evidence_coordinate_and_content_exact(self):
        r=fixture()
        for m in (replace(r.package.manifest,coordinate=replace(r.package.manifest.coordinate,version=ExactVersion(2,0,0))),
            replace(r.package.manifest,exported_capabilities=("other.capability",))):
            self.outcome(replace(r,package=replace(r.package,manifest=m)),"DENIED","SECURITY_PACKAGE_MISMATCH")

    def test_wrong_principal(self):
        r=fixture()
        self.outcome(replace(r,principal=Principal("principal:other")),"DENIED","SECURITY_PRINCIPAL_MISMATCH")
        self.outcome(replace(r,authority_check=replace(r.authority_check,principal="principal:other")),
            "DENIED","SECURITY_PRINCIPAL_MISMATCH")

    def test_wrong_capability(self):
        r=fixture()
        self.outcome(replace(r,authority_check=replace(r.authority_check,capability="different.capability")),
            "DENIED","SECURITY_CAPABILITY_MISMATCH")

    def test_wrong_resource(self):
        r=fixture()
        self.outcome(replace(r,authority_check=replace(r.authority_check,resource="protected:other")),
            "DENIED","SECURITY_RESOURCE_MISMATCH")

    def test_check_identity_exact(self):
        r=fixture()
        self.outcome(replace(r,authority_check=replace(r.authority_check,id="check:other")),"DENIED","SECURITY_CHECK_MISMATCH")

    def test_no_principal_inference(self):
        r=fixture("agent")
        self.outcome(replace(r,principal=None),"INCOMPLETE","SECURITY_AUTHORITY_MISSING")
        self.error("SECURITY_PRINCIPAL_INPUT_INVALID",lambda:replace(r,principal=r.node.descriptor.identity))
        self.error("SECURITY_PRINCIPAL_INPUT_INVALID",lambda:replace(r,principal="principal:reviewer"))

    def test_no_capability_inference(self):
        r=fixture()
        self.outcome(replace(r,authority_check=None),"INCOMPLETE","SECURITY_AUTHORITY_MISSING")
        self.error("SECURITY_AUTHORITY_INPUT_INVALID",lambda:replace(r,authority_check=r.node.capabilities[0]))

    def test_missing_authority_and_governance_not_permission(self):
        r=fixture()
        self.assertEqual(r.node.registration.status,"ADMISSIBLE")
        self.assertEqual(orch.OrchestrationValidation(r.plan).status,"VALID")
        self.outcome(replace(r,authority=None),"INCOMPLETE","SECURITY_AUTHORITY_MISSING")

    def test_explicit_denial_precedes_missing(self):
        r=fixture()
        self.outcome(replace(r,authority=AuthorityEngine(),package=None,provenance=()),"DENIED","SECURITY_AUTHORITY_DENIED")

    def test_wrong_grant_principal_capability_resource(self):
        r=fixture()
        grant=r.authority.grants[0]
        for g in (replace(grant,principal="principal:other"),replace(grant,capability="other.capability"),
            replace(grant,resource="protected:other")):
            self.outcome(replace(r,authority=AuthorityEngine((g,))),"DENIED","SECURITY_AUTHORITY_DENIED")

    def test_direct_check_pure_exact_arguments(self):
        r=fixture()
        grants=r.authority.grants
        original=AuthorityEngine.check
        calls=[]
        def observe(engine,**kw):
            calls.append(kw)
            return original(engine,**kw)
        with patch.object(AuthorityEngine,"check",observe):
            self.outcome(r,"ADMISSIBLE")
        self.assertEqual(calls,[{"principal":r.principal.id,"capability":r.authority_check.capability,
            "resource":r.authority_check.resource}])
        self.assertEqual(grants,r.authority.grants)

    def test_existing_wildcard_grants_consumed_not_fabricated(self):
        r=fixture()
        for resource in ("*", ""):
            engine=AuthorityEngine((AuthorityGrant(r.principal.id,"*",resource),))
            self.outcome(replace(r,authority=engine),"ADMISSIBLE")
            self.assertEqual(engine.grants[0].resource,resource)
        for field in ("principal","capability","resource"):
            self.error("SECURITY_RESOURCE_NOT_EXACT",lambda:replace(r.policy,
                authority_check=replace(r.policy.authority_check,**{field:"*"})))
        self.error("SECURITY_IDENTITY_INVALID",lambda:replace(r.policy,
            authority_check=replace(r.policy.authority_check,resource="")))

    def test_authority_snapshot_changes_request_and_decision(self):
        r=fixture()
        q=replace(r,authority=AuthorityEngine(r.authority.grants+(AuthorityGrant("principal:other","other","other"),)))
        self.assertNotEqual(r.fingerprint(),q.fingerprint())
        self.assertNotEqual(sec.SecurityAdmissionDecision(r).fingerprint(),sec.SecurityAdmissionDecision(q).fingerprint())

    def test_replay_exact_context_only(self):
        r=fixture()
        d=sec.SecurityAdmissionDecision(r)
        self.assertIs(sec.bind_decision(d,r),d)
        substitutions=(replace(r,principal=Principal("principal:other")),
            replace(r,authority_check=replace(r.authority_check,capability="other")),
            replace(r,authority_check=replace(r.authority_check,resource="other")),
            replace(r,plan=replace(r.plan,identity=orch.OrchestrationPlanIdentity("other-plan"))),
            replace(r,node=replace(r.node,identifier="other-node")),
            replace(r,node=replace(r.node,descriptor=replace(r.node.descriptor,contract_version=ExactVersion(2,0,0)))),
            replace(r,policy=replace(r.policy,require_provenance=False)),replace(r,authority=AuthorityEngine()))
        substitutions += (replace(r,package=replace(r.package,manifest=replace(r.package.manifest,
            exported_capabilities=("changed.content",)))),
            replace(r,node=replace(r.node,registration=gov.evaluate(r.plan.catalog.policy,
                replace(r.node.registration.candidate,contract=None)))))
        for q in substitutions:
            self.error("SECURITY_ADMISSION_REPLAY_MISMATCH",lambda:sec.bind_decision(d,q))

    def test_integrity_missing_not_empty(self):
        r=fixture()
        self.outcome(replace(r,package=None),"INCOMPLETE","SECURITY_INTEGRITY_MISSING")
        self.outcome(replace(r,package=replace(r.package,members=None)),"INCOMPLETE","SECURITY_INTEGRITY_MISSING")
        self.outcome(r,"ADMISSIBLE")

    def test_integrity_digest_failure(self):
        r=fixture()
        member=trust.ContentMember(PackagePath("data.bin"),b"wrong")
        # Unexpected bytes contradict the exact empty-content manifest.
        d=self.outcome(replace(r,package=replace(r.package,members=(member,))),"DENIED","SECURITY_INTEGRITY_INVALID")
        self.assertEqual(d.record()["package_verification"]["integrity"]["status"],"INVALID")

    def test_nonempty_integrity_and_member_permutation(self):
        r=fixture()
        members=tuple(trust.ContentMember(PackagePath(path),data) for path,data in
            (("a.bin",b"design evidence"),("b.bin",b"reference evidence")))
        m=replace(r.package.manifest,content=tuple(ContentDescriptor(v.path,sha256(v.data).hexdigest().upper(),"data")
            for v in members))
        descriptor=replace(r.node.descriptor,implementation=sdk.ImplementationPackage.from_manifest(m))
        registration=predecessor.admission(descriptor,r.plan.catalog.policy)
        node=replace(r.node,descriptor=descriptor,registration=registration)
        plan=replace(r.plan,nodes=(node,),catalog=gov.DomainCatalogSnapshot(r.plan.catalog.policy,(registration,)))
        r=replace(rebind(r,plan,node),package=sec.PackageSecurityEvidence(m,members))
        self.outcome(r,"ADMISSIBLE")
        q=replace(r,package=replace(r.package,members=members[::-1]))
        self.assertEqual(r.fingerprint(),q.fingerprint())
        self.assertEqual(sec.SecurityAdmissionDecision(r).fingerprint(),sec.SecurityAdmissionDecision(q).fingerprint())
        bad=replace(r,package=replace(r.package,members=(replace(members[0],data=b"substituted"),members[1])))
        d=self.outcome(bad,"DENIED","SECURITY_INTEGRITY_INVALID")
        self.assertEqual(d.record()["package_verification"]["integrity"]["diagnostics"][0]["code"],"CONTENT_DIGEST_MISMATCH")

    def test_package_digest_not_trust(self):
        r=fixture()
        d=self.outcome(replace(r,policy=replace(r.policy,require_package_trust=True)),
            "INCOMPLETE","SECURITY_CRYPTO_UNAVAILABLE")
        self.assertEqual(d.record()["evidence_matrix"]["integrity"],"SATISFIED")
        self.assertEqual(d.record()["evidence_matrix"]["trust"],"UNAVAILABLE")
        self.assertFalse(d.record()["cryptographic_trust_established"])

    def test_default_policy_requires_crypto(self):
        r=fixture()
        p=sec.SecurityAdmissionPolicy("strict",ExactVersion(1,0,0),r.plan.fingerprint(),r.node.fingerprint(),r.authority_check)
        self.outcome(replace(r,policy=p),"INCOMPLETE","SECURITY_TRUST_EVIDENCE_MISSING")

    def signed(self,r):
        key=b"k"*32
        anchor=trust.TrustAnchor(key)
        policy=trust.TrustPolicy((anchor,),(trust.NamespaceTrustRule(anchor.fingerprint,r.package.manifest.coordinate.namespace),))
        envelope=trust.SignatureEnvelope(anchor.fingerprint,trust.payload_fingerprint(r.package.manifest),b"s"*64)
        return replace(r,package=replace(r.package,public_key=key,signature=envelope,trust_policy=policy))

    def test_crypto_unavailable_with_all_structural_signature_evidence(self):
        r=self.signed(fixture())
        d=self.outcome(r,"INCOMPLETE","SECURITY_CRYPTO_UNAVAILABLE")
        record=d.record()["package_verification"]
        self.assertEqual(record["signature"],"CRYPTO_PROVIDER_UNAVAILABLE")
        self.assertEqual(record["scope_trust"],"TRUSTED_FOR_PACKAGE_SCOPE")
        self.assertFalse(record["accepted"])

    def test_signature_substitution_invalid(self):
        r=self.signed(fixture())
        for signature in (replace(r.package.signature,payload_fingerprint="B"*64),
            replace(r.package.signature,signer_fingerprint="B"*64)):
            self.outcome(replace(r,package=replace(r.package,signature=signature)),"DENIED","SECURITY_TRUST_EVIDENCE_INVALID")

    def test_untrusted_scope_denied(self):
        r=self.signed(fixture())
        package=replace(r.package,trust_policy=replace(r.package.trust_policy,rules=()))
        self.outcome(replace(r,package=package),"DENIED","SECURITY_TRUST_EVIDENCE_INVALID")

    def test_supplied_strict_trust_policy_not_weakened(self):
        r=fixture()
        self.outcome(replace(r,package=replace(r.package,trust_policy=trust.TrustPolicy())),
            "INCOMPLETE","SECURITY_TRUST_EVIDENCE_MISSING")

    def test_supplied_trust_evidence_needs_bytes_even_if_policy_integrity_optional(self):
        r=self.signed(fixture())
        r=replace(r,policy=replace(r.policy,require_integrity=False),package=replace(r.package,members=None))
        d=self.outcome(r,"INCOMPLETE","SECURITY_TRUST_EVIDENCE_MISSING")
        self.assertEqual(d.record()["evidence_matrix"]["integrity"],"MISSING")
        bad=replace(r,package=replace(r.package,signature=replace(r.package.signature,payload_fingerprint="B"*64)))
        self.outcome(bad,"DENIED","SECURITY_TRUST_EVIDENCE_INVALID")

    def test_findings_reject_arbitrary_canonical_codes(self):
        self.error("SECURITY_FINDING_INVALID",lambda:sec.SecurityFinding([],"authority","MISSING"))
        self.error("SECURITY_FINDING_INVALID",lambda:sec.SecurityFinding("exception prose","authority","MISSING"))

    def test_passive_verification_carrier_cannot_fabricate_trust(self):
        r=fixture()
        fake=trust.VerificationEvidence('{"signature":"VALID","accepted":true}')
        self.error("SECURITY_PACKAGE_INPUT_INVALID",lambda:replace(r,package=fake))
        self.error("SECURITY_TRUST_INPUT_INVALID",lambda:replace(r.package,signature=fake))

    def test_provenance_required_only_by_policy(self):
        r=fixture()
        self.outcome(replace(r,provenance=()),"INCOMPLETE","SECURITY_PROVENANCE_INCOMPLETE")
        self.outcome(replace(r,provenance=(),policy=replace(r.policy,require_provenance=False)),"ADMISSIBLE")
        self.outcome(replace(r,authority=None),"INCOMPLETE","SECURITY_AUTHORITY_MISSING")

    def test_external_authentication_not_fabricated(self):
        r=fixture("external-adapter")
        self.outcome(r,"INCOMPLETE","SECURITY_PROVIDER_AUTHENTICATION_MISSING")
        self.outcome(replace(r,policy=replace(r.policy,require_external_authentication=False)),"ADMISSIBLE")
        self.assertFalse(hasattr(r,"credential"))

    def test_agent_narrative_parametric_fabrication_no_self_authority(self):
        for kind in ("agent","narrative","parametric","fabrication","motion"):
            with self.subTest(kind=kind):
                r=fixture(kind)
                self.outcome(replace(r,authority=None),"INCOMPLETE","SECURITY_AUTHORITY_MISSING")
                self.outcome(replace(r,authority=AuthorityEngine()),"DENIED","SECURITY_AUTHORITY_DENIED")
                self.outcome(r,"ADMISSIBLE")

    def test_authority_not_propagated_across_handoff(self):
        r=fixture()
        plan=predecessor.fixture(("parametric","fabrication"))
        first,second=plan.nodes
        a=rebind(r,plan,first)
        self.outcome(a,"ADMISSIBLE")
        b=rebind(r,plan,second)
        nextcheck=replace(r.authority_check,id="check:machine",capability="machine.actuate",resource="machine:exact-one")
        b=replace(b,policy=replace(b.policy,authority_check=nextcheck),authority_check=nextcheck,
            package=sec.PackageSecurityEvidence(PackageManifest(PackageCoordinate("example.domains","fabrication",ExactVersion(1,0,0))),()))
        self.outcome(b,"DENIED","SECURITY_AUTHORITY_DENIED")
        self.error("SECURITY_ADMISSION_REPLAY_MISMATCH",lambda:sec.bind_decision(sec.SecurityAdmissionDecision(a),b))

    def test_request_and_decision_determinism(self):
        a,b=fixture(),fixture()
        self.assertEqual(a.policy.fingerprint(),b.policy.fingerprint())
        self.assertEqual(a.fingerprint(),b.fingerprint())
        da,db=sec.SecurityAdmissionDecision(a),sec.SecurityAdmissionDecision(b)
        self.assertEqual(da.record(),db.record())
        self.assertEqual(da.fingerprint(),db.fingerprint())

    def test_findings_sorted_and_deny_dominates(self):
        r=replace(fixture(),authority=AuthorityEngine(),package=None,provenance=())
        d=self.outcome(r,"DENIED")
        self.assertEqual(d.findings,tuple(sorted(d.findings,key=lambda f:(f.dimension,f.code,f.state))))
        self.assertEqual(d.record(),sec.SecurityAdmissionDecision(r).record())

    def test_evidence_matrix_not_collapsed_boolean(self):
        d=sec.SecurityAdmissionDecision(fixture())
        self.assertEqual(set(d.record()["evidence_matrix"]),set(sec.DIMENSIONS))
        self.assertEqual(d.record()["evidence_matrix"]["trust"],"NOT_REQUIRED")
        self.assertTrue(d.record()["authority_allowed"])

    def test_no_mutable_or_callback_evidence(self):
        r=fixture()
        self.error("SECURITY_AUTHORITY_INPUT_INVALID",lambda:replace(r,authority=lambda:True))
        self.error("SECURITY_PROVENANCE_INVALID",lambda:replace(r,provenance=[predecessor.REFERENCE]))
        self.error("SECURITY_PRINCIPAL_INPUT_INVALID",lambda:replace(r,principal=Principal(r.principal.id,authorities=({},))))
        self.error("SECURITY_PACKAGE_INPUT_INVALID",lambda:replace(r.package,members=[]))

    def test_domain_separated_fingerprints(self):
        r=fixture()
        d=sec.SecurityAdmissionDecision(r)
        self.assertEqual(len({r.policy.fingerprint(),r.fingerprint(),d.fingerprint(),r.plan.fingerprint(),r.node.fingerprint()}),5)
        self.assertEqual(d.DOMAIN,"apexforge.security-admission-decision/v1")

    def test_existing_owners_used_without_grant_creation(self):
        r=fixture()
        with patch.object(AuthorityEngine,"from_grants",side_effect=AssertionError("grants minted")), \
             patch.object(gov,"evaluate",side_effect=AssertionError("governance reimplemented")), \
             patch.object(sdk.DomainArtifact,"from_bytes",side_effect=AssertionError("artifact manufactured")):
            self.outcome(r,"ADMISSIBLE")

    def test_thousand_admissions_iterative_deterministic(self):
        base=fixture()
        records=[]
        for i in range(1000):
            principal="principal:caller-"+str(i)
            check=replace(base.authority_check,principal=principal)
            r=replace(base,principal=Principal(principal),authority_check=check,
                policy=replace(base.policy,authority_check=check),
                authority=AuthorityEngine((AuthorityGrant(principal,check.capability,check.resource),)))
            d=sec.SecurityAdmissionDecision(r)
            self.assertEqual(d.status,"ADMISSIBLE")
            records.append((r,d.fingerprint()))
        self.assertEqual(len({fp for _,fp in records}),1000)
        self.assertEqual([fp for _,fp in reversed(records)],
            [sec.SecurityAdmissionDecision(r).fingerprint() for r,_ in reversed(records)])

    def test_static_security_audit(self):
        tree=ast.parse(Path(sec.__file__).read_text(encoding="utf-8"))
        imports={n.module for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)}
        self.assertEqual(imports,{"dataclasses","hashlib","authority.engine","authority.model","air.model",
            "tooling","tooling.package_manifest"})
        self.assertFalse(any(isinstance(n,ast.Import) for n in ast.walk(tree)))
        tooling={a.name for n in ast.walk(tree) if isinstance(n,ast.ImportFrom) and n.module=="tooling" for a in n.names}
        self.assertEqual(tooling,{"domain_platform","cross_domain_orchestration","package_trust"})
        calls={n.func.id for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name)}
        self.assertFalse(calls & {"AuthorityGrant","AuthorityEngine","Principal","open","eval","exec","compile",
            "__import__","getattr","setattr","input"})
        attrs={n.attr for n in ast.walk(tree) if isinstance(n,ast.Attribute)}
        self.assertFalse(attrs & {"execute","run","simulate","dispatch","from_grants","connect","send",
            "read_bytes","read_text","getenv","load","loads","glob","rglob","register"})
        self.assertFalse(any(isinstance(n,(ast.AsyncFunctionDef,ast.Await,ast.AsyncFor)) for n in ast.walk(tree)))
        names={f.name for cls in (sec.SecurityAdmissionPolicy,sec.SecurityAdmissionRequest,sec.SecurityAdmissionDecision)
            for f in fields(cls)}
        self.assertFalse(names & {"token","permit","callback","predicate","expression","credential","runtime"})


if __name__ == "__main__":
    unittest.main()
