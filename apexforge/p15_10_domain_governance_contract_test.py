"""Deterministic supplied-evidence policy admission and catalog lineage."""
import ast
from dataclasses import replace, FrozenInstanceError
from pathlib import Path
import unittest
from tooling import domain_governance as gov
from tooling import domain_platform as sdk
from tooling.package_manifest import ExactVersion
import p15_3_apexmotion_domain_contract_test as fixture_owner


def fixture():
    descriptor = fixture_owner.fixture()[1]
    reference = fixture_owner.fixture()[2].provenance[0]
    policy = gov.DomainGovernancePolicy(gov.DomainGovernancePolicyIdentity("policy-one"), ExactVersion(1,0,0),
        tuple(sdk.KINDS))
    evidence = tuple(gov.GovernanceEvidence(k, reference, descriptor.fingerprint()) for k in gov.EVIDENCE_KINDS)
    candidate = gov.DomainRegistrationCandidate(descriptor, evidence, (reference,), reference)
    return policy, candidate


class GovernanceTests(unittest.TestCase):
    def rejected(self, code, fn):
        with self.assertRaises(gov.GovernanceError) as caught:
            fn()
        self.assertEqual(caught.exception.code, code)

    def test_identity_and_version(self):
        p,c = fixture()
        self.assertNotEqual(p.identity, c.descriptor.identity)
        self.assertNotEqual(p.identity, c.descriptor.implementation)
        self.assertEqual(p.record()["version"], "1.0.0")

    def test_policy_permutation(self):
        p,_ = fixture()
        self.assertEqual(p.fingerprint(), replace(p, permitted_kinds=p.permitted_kinds[::-1],
            required_evidence=p.required_evidence[::-1]).fingerprint())

    def test_policy_revision(self):
        p,c=fixture()
        d=gov.evaluate(p,c)
        revised=replace(p,version=ExactVersion(2,0,0))
        self.assertNotEqual(d.fingerprint(),gov.evaluate(revised,c).fingerprint())
        self.assertEqual(d.policy,p)

    def test_schema_and_rules(self):
        p,_=fixture()
        self.rejected("GOVERNANCE_SCHEMA_UNSUPPORTED", lambda:replace(p,schema="unknown"))
        self.rejected("GOVERNANCE_RULE_INVALID", lambda:replace(p,permitted_kinds=("unknown",)))
        self.rejected("GOVERNANCE_RULE_INVALID", lambda:replace(p,require_provenance=lambda:True))

    def test_exact_candidate_bindings(self):
        _,c=fixture()
        self.assertEqual(c.record()["descriptor_fingerprint"],c.descriptor.fingerprint())
        self.assertEqual(c.record()["implementation"],c.descriptor.implementation.record())
        self.rejected("GOVERNANCE_DESCRIPTOR_BINDING_INVALID",lambda:gov.DomainRegistrationCandidate("package-name"))

    def test_descriptor_revision(self):
        _,c=fixture()
        self.assertNotEqual(c.fingerprint(),replace(c,descriptor=replace(c.descriptor,
            contract_version=ExactVersion(2,0,0))).fingerprint())

    def test_content_revision(self):
        _,c=fixture()
        content=c.descriptor.implementation.content
        self.assertNotEqual(c.fingerprint(),replace(c,descriptor=replace(c.descriptor,
            implementation=replace(c.descriptor.implementation,content=replace(content,fingerprint="B"*64)))).fingerprint())

    def test_admissible(self):
        p,c=fixture()
        d=gov.evaluate(p,c)
        self.assertEqual(d.status,"ADMISSIBLE")
        self.assertEqual(d.findings,())
        self.assertFalse(d.record()["authority_granted"])
        self.assertFalse(d.record()["trust_granted"])

    def test_missing_incomplete(self):
        p,c=fixture()
        d=gov.evaluate(p,replace(c,evidence=(),provenance=()))
        self.assertEqual(d.status,"INCOMPLETE")
        self.assertIn("GOVERNANCE_REQUIRED_EVIDENCE_MISSING",[f.code for f in d.findings])

    def test_contradiction_rejected(self):
        p,c=fixture()
        d=gov.evaluate(p,replace(c,evidence=(replace(c.evidence[0],descriptor_fingerprint="A"*64),)))
        self.assertEqual(d.status,"REJECTED")
        self.assertIn("GOVERNANCE_DESCRIPTOR_BINDING_INVALID",[f.code for f in d.findings])

    def test_prohibited_claims(self):
        p,c=fixture()
        for claim in gov.CLAIMS:
            self.assertEqual(gov.evaluate(p,replace(c,claims=(claim,))).status,"REJECTED")

    def test_not_allowed_kind(self):
        p,c=fixture()
        self.assertEqual(gov.evaluate(replace(p,permitted_kinds=("agent",)),c).status,"REJECTED")

    def test_evidence_permutation(self):
        p,c=fixture()
        other=replace(c,evidence=c.evidence[::-1])
        self.assertEqual(c.fingerprint(),other.fingerprint())
        self.assertEqual(gov.evaluate(p,c),gov.evaluate(p,other))

    def test_immutable_models(self):
        p,c=fixture()
        d=gov.evaluate(p,c)
        catalog=gov.DomainCatalogSnapshot(p,(d,))
        for obj,field in ((p,"version"),(c,"claims"),(d,"policy"),(catalog,"entries"),(p.identity,"identifier")):
            with self.assertRaises(FrozenInstanceError):setattr(obj,field,None)

    def test_catalog_admission(self):
        p,c=fixture()
        catalog=gov.register(gov.DomainCatalogSnapshot(p),c)
        self.assertEqual(catalog.lookup(c.descriptor.identity.identifier,c.descriptor.contract_version).candidate,c)
        for bad in (replace(c,evidence=()),replace(c,claims=("package-trust",))):
            self.rejected("GOVERNANCE_CATALOG_NOT_ADMISSIBLE",lambda bad=bad:gov.register(gov.DomainCatalogSnapshot(p),bad))

    def test_conflict_evidence(self):
        p,c=fixture()
        catalog=gov.register(gov.DomainCatalogSnapshot(p),c)
        other=replace(c,contract=None)
        self.assertEqual(gov.evaluate(p,other,catalog).status,"CONFLICT")
        self.rejected("GOVERNANCE_CATALOG_NOT_ADMISSIBLE",lambda:gov.register(catalog,other))
        self.assertEqual(catalog.entries[0].candidate,c)

    def test_conflict_descriptor(self):
        p,c=fixture()
        revised=replace(c,descriptor=replace(c.descriptor,operations=c.descriptor.operations+("motion.other.describe",)))
        revised=replace(revised,evidence=tuple(replace(e,descriptor_fingerprint=revised.descriptor.fingerprint()) for e in c.evidence))
        catalog=gov.register(gov.DomainCatalogSnapshot(p),c)
        self.assertEqual(gov.evaluate(p,revised,catalog).status,"CONFLICT")

    def test_direct_catalog_conflict(self):
        p,c=fixture()
        self.rejected("GOVERNANCE_REGISTRATION_CONFLICT",lambda:gov.DomainCatalogSnapshot(p,
            (gov.evaluate(p,c),gov.evaluate(p,replace(c,contract=None)))))

    def test_retry_idempotent(self):
        p,c=fixture()
        catalog=gov.register(gov.DomainCatalogSnapshot(p),c)
        self.assertIs(gov.register(catalog,c),catalog)

    def test_lineage(self):
        p,c=fixture()
        old=gov.DomainCatalogSnapshot(p)
        new=gov.register(old,c)
        self.assertEqual(new.predecessor,old.fingerprint())
        self.assertEqual(old.entries,())

    def test_policy_mismatch(self):
        p,c=fixture()
        changed=replace(p,version=ExactVersion(2,0,0))
        self.rejected("GOVERNANCE_POLICY_MISMATCH",lambda:gov.DomainCatalogSnapshot(changed,(gov.evaluate(p,c),)))
        self.rejected("GOVERNANCE_POLICY_MISMATCH",lambda:gov.evaluate(changed,c,gov.DomainCatalogSnapshot(p)))

    def test_provenance_and_authority(self):
        p,c=fixture()
        d=gov.evaluate(p,c)
        self.assertEqual(d.record()["evidence"],[e.record() for e in c.evidence])
        self.assertEqual(d.record()["semantic_authority"],"CANONICAL_AIR")
        self.assertFalse(gov.DomainCatalogSnapshot(p,(d,)).record()["package_registry"])

    def test_scale_catalog_determinism(self):
        p,c=fixture()
        decisions=[]
        for index in range(1000):
            descriptor=replace(c.descriptor,identity=replace(c.descriptor.identity,identifier="domain-"+str(index)))
            candidate=replace(c,descriptor=descriptor,evidence=tuple(replace(e,descriptor_fingerprint=descriptor.fingerprint()) for e in c.evidence))
            decisions.append(gov.evaluate(p,candidate))
        a=gov.DomainCatalogSnapshot(p,tuple(decisions))
        b=gov.DomainCatalogSnapshot(p,tuple(reversed(decisions)))
        self.assertEqual(a.fingerprint(),b.fingerprint())
        self.assertIsNotNone(a.lookup("domain-999",ExactVersion(1,0,0)))

    def test_static_security(self):
        tree=ast.parse(Path(gov.__file__).read_text(encoding="utf-8"))
        self.assertEqual({n.module for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)},
            {"dataclasses","tooling","tooling.package_manifest"})
        self.assertEqual({n.names[0].name for n in ast.walk(tree) if isinstance(n,ast.Import)},{"re"})
        calls={n.func.id for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name)}
        self.assertFalse(calls & {"eval","exec","open","__import__","print"})
        self.assertFalse(any(isinstance(n,(ast.While,ast.AsyncFunctionDef)) for n in ast.walk(tree)))


if __name__=="__main__":unittest.main()
