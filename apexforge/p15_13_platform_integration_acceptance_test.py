"""Cross-owner passive acceptance; no simulator, agent, runtime or provider run."""
import ast
from dataclasses import replace, FrozenInstanceError, fields
from pathlib import Path
import unittest
from unittest.mock import patch

from authority.engine import AuthorityEngine
from authority.model import Principal
from tooling import platform_acceptance as acceptance
from tooling import domain_platform as sdk, domain_interchange as wire, domain_governance as gov
from tooling import cross_domain_orchestration as orch, security_integration as sec
from tooling import parametric_domain as param, fabrication_domain as fab, agent_domain as agent
from tooling import external_adapter as ext, narrative_domain as narrative, apexmotion as motion, apexmotion_simulation as sim
from tooling.package_manifest import CanonicalReference, ExactVersion
import p15_3_apexmotion_domain_contract_test as motion_fixture
import p15_4_apexmotion_simulation_kernel_test as simulation_fixture
import p15_5_narrative_domain_contract_test as narrative_fixture
import p15_6_agent_domain_contract_test as agent_fixture
import p15_7_parametric_domain_contract_test as param_fixture
import p15_8_fabrication_domain_contract_test as fab_fixture
import p15_9_external_adapter_contract_test as external_fixture
import p15_12_security_integration_contract_test as security_fixture


def reference(record):
    schema = record.schema if type(record) is wire.DomainInterchangeEnvelope else (
        record.DOMAIN if isinstance(record,sdk.CanonicalModel) else record.SCHEMA)
    return CanonicalReference(schema,"artifact",record.fingerprint())


def fixture():
    manifest, motion_descriptor, state, *_ = motion_fixture.fixture()
    scope=state.provenance[0]
    variant=param_fixture.fixture()[2]
    fabrication,machine=fab_fixture.fixture()
    fabrication=replace(fabrication,input=replace(fabrication.input,variant=variant,provenance=(scope,)))
    story,narrative_descriptor=narrative_fixture.fixture()
    story=replace(story,provenance=(scope,))
    specification=simulation_fixture.specification(step_count=0)
    # Explicit zero-step owner record; no evolve/simulate call and no computed states.
    trace=sim.SimulationTrace(specification,())
    session,observation,decision,intent,_=agent_fixture.fixture()
    inputs=(reference(fabrication),reference(story),reference(trace))
    intent=replace(intent,arguments=inputs,provenance=(scope,))
    session=replace(session,task=replace(session.task,inputs=inputs),ledger=(observation,decision,intent))
    adapter,request,_=external_fixture.fixture()
    request=replace(request,inputs=(reference(intent),))
    response=ext.ExternalResponse(request,request.fingerprint(),adapter.provider,request.correlation,
        "REPORTED_SUCCESS",outputs=(reference(intent),),provenance=(scope,))
    ext.admit_response(request,response)
    records=(variant,fabrication,session,request,story,state,trace,response,intent)
    artifacts=(param.parametric_artifact(variant,semantic_inputs=(reference(variant),)),
        fab.fabrication_artifact(fabrication,semantic_inputs=(reference(fabrication),)),
        agent.agent_artifact(session,semantic_inputs=inputs),ext.domain_artifact(request),
        narrative.narrative_artifact(narrative_descriptor,story,semantic_inputs=(reference(story),)),
        motion.motion_artifact(motion_descriptor,state,semantic_inputs=(reference(state),)),
        sim.simulation_artifact(trace),ext.domain_artifact(response))
    descriptors=(variant.parameters.design.platform,fabrication.platform,session.context.descriptor.platform,
        adapter.platform,narrative_descriptor,motion_descriptor)
    names=("parametric","fabrication","agent","external","narrative","motion")
    policy=gov.DomainGovernancePolicy(gov.DomainGovernancePolicyIdentity("integration-governance"),ExactVersion(1,0,0),tuple(sdk.KINDS))
    registrations=[]
    for d,a in zip(descriptors,artifacts):
        candidate=gov.DomainRegistrationCandidate(d,tuple(gov.GovernanceEvidence(k,reference(a),d.fingerprint())
            for k in gov.EVIDENCE_KINDS),(scope,reference(a)),reference(d))
        registrations.append(gov.evaluate(policy,candidate))
    catalog=gov.DomainCatalogSnapshot(policy,tuple(registrations))
    contract=orch.ArtifactContract("model",provenance=(scope,))
    input_names=(("initial",),("design",),("fabrication","story","motion"),("intent",),("initial",),("initial",))
    operations=("parametric.variant.describe","fabrication.plan.describe","agent.session.describe",
        "external.request.describe","narrative.graph.describe","motion.trajectory.describe")
    nodes=tuple(orch.OrchestrationNode(name,registration,d,op,
        tuple(orch.InputSlot(slot,contract) for slot in slots),
        (orch.OutputSlot("output",contract if name != "external" else orch.ArtifactContract("external-reference",provenance=(scope,))),),
        d.capabilities,(scope,reference(a))) for name,registration,d,op,slots,a in
        zip(names,registrations,descriptors,operations,input_names,artifacts))
    edges=tuple(orch.ArtifactHandoff("handoff-"+str(n),orch.SlotReference(producer,"output"),
        orch.SlotReference(consumer,slot),contract,(scope,)) for n,(producer,consumer,slot) in enumerate((
        ("parametric","fabrication","design"),("fabrication","agent","fabrication"),
        ("agent","external","intent"),("narrative","agent","story"),("motion","agent","motion"))))
    initial=tuple(orch.InitialInput(orch.SlotReference(name,"initial"),artifacts[n])
        for name,n in (("parametric",0),("narrative",4),("motion",5)))
    plan=orch.CrossDomainOrchestrationPlan(orch.OrchestrationPlanIdentity("integrated-plan"),catalog,nodes,edges,initial,
        (orch.SlotReference("external","output"),),(scope,))
    base=security_fixture.fixture()
    cases=[]
    for n in nodes:
        security_policy=sec.SecurityAdmissionPolicy("admission-"+n.identifier,ExactVersion(1,0,0),plan.fingerprint(),
            n.fingerprint(),base.authority_check,require_package_trust=False)
        security_request=sec.SecurityAdmissionRequest(security_policy,plan,n,base.principal,base.authority_check,
            base.authority,sec.PackageSecurityEvidence(manifest,()),n.provenance)
        cases.append(acceptance.AdmissionExpectation("case-"+n.identifier,security_request,
            sec.SecurityAdmissionDecision(security_request),"INCOMPLETE" if n.identifier=="external" else "ADMISSIBLE"))
    # Observations refer to actual owning records/envelopes; they are not suite receipts.
    layer_sources=(descriptors[0],wire.DomainInterchangeEnvelope(artifacts[0]),state,trace,story,session,variant,
        fabrication,request,catalog,plan,cases[0].decision)
    evidence=tuple(acceptance.AcceptanceEvidence(area,"PASS",reference(source)) for area,source in
        zip(acceptance.LAYERS,layer_sources))
    boundary_sources=(descriptors[0],cases[0].decision,cases[0].decision,session,adapter,variant,fabrication,
        response,request,request,intent)
    evidence+=tuple(acceptance.AcceptanceEvidence(area,"PASS",reference(source)) for area,source in
        zip(acceptance.BOUNDARIES,boundary_sources))
    scenario=acceptance.PlatformAcceptanceScenario("platform-integration",plan,(descriptors[0].implementation,),
        tuple(cases),artifacts,tuple(reference(r) for r in records),evidence,(scope,))
    return scenario,dict(zip(("variant","fabrication","session","request","story","state","trace","response","intent"),records))


class IntegrationTests(unittest.TestCase):
    def error(self,code,fn):
        with self.assertRaises(acceptance.AcceptanceError) as caught:
            fn()
        self.assertEqual(caught.exception.code,code)

    def failed(self,scenario,code):
        result=acceptance.PlatformAcceptanceResult(scenario)
        self.assertEqual(result.status,"FAIL")
        self.assertIn(code,{f["code"] for f in result.record()["findings"]})

    def test_end_to_end_contract_acceptance(self):
        s,_=fixture()
        result=acceptance.PlatformAcceptanceResult(s)
        self.assertEqual(result.status,"PASS")
        self.assertEqual(result.record()["findings"],[])
        self.assertEqual(len(s.plan.nodes),6)
        pairs={(e.producer.node,e.consumer.node) for e in s.plan.handoffs}
        self.assertTrue({("parametric","fabrication"),("fabrication","agent"),("agent","external"),
            ("narrative","agent"),("motion","agent")} <= pairs)
        self.assertEqual(orch.OrchestrationValidation(s.plan).status,"VALID")
        self.assertEqual(len(result.record()["admissions"]),6)

    def test_all_twelve_owners_and_boundary_matrix(self):
        s,_=fixture()
        record=acceptance.PlatformAcceptanceResult(s).record()
        self.assertEqual({r["area"] for r in record["acceptance_matrix"]},set(acceptance.LAYERS))
        self.assertEqual({r["area"] for r in record["boundary_matrix"]},set(acceptance.BOUNDARIES))
        self.assertTrue(all(r["status"]=="PASS" for r in record["acceptance_matrix"]+record["boundary_matrix"]))
        self.assertEqual(sdk.KINDS,frozenset(("simulation","motion","narrative","agent","parametric","fabrication","external-adapter")))

    def test_scenario_case_evidence_result_immutable(self):
        s,_=fixture()
        for obj in (s,s.admissions[0],s.evidence[0],acceptance.PlatformAcceptanceResult(s)):
            with self.assertRaises(FrozenInstanceError):
                setattr(obj,fields(obj)[0].name,None)
        record=s.record()
        record["artifacts"].clear()
        self.assertEqual(len(s.artifacts),8)

    def test_exact_identity_chain(self):
        s,_=fixture()
        manifest=motion_fixture.fixture()[0]
        for c in s.admissions:
            n=c.request.node
            self.assertEqual(n.descriptor.implementation,sdk.ImplementationPackage.from_manifest(manifest))
            self.assertEqual(n.registration.candidate.descriptor,n.descriptor)
            self.assertIn(n.registration,s.plan.catalog.entries)
            self.assertEqual(c.request.plan,s.plan)
            self.assertEqual(c.request.policy.plan_fingerprint,s.plan.fingerprint())
            self.assertEqual(c.request.policy.node_fingerprint,n.fingerprint())
            self.assertEqual(c.decision.record()["policy"],c.request.policy.fingerprint())
            self.assertEqual(c.decision.record()["bindings"]["descriptor"],n.descriptor.fingerprint())
            self.assertEqual(c.decision.record()["bindings"]["governance"],n.registration.fingerprint())
        for a in s.artifacts:
            d=next(n.descriptor for n in s.plan.nodes if n.descriptor.identity==a.platform)
            self.assertEqual(a.descriptor_fingerprint,d.fingerprint())
            self.assertEqual(a.implementation,d.implementation)

    def test_interchange_supported_roundtrips(self):
        s,_=fixture()
        for obj in tuple(n.descriptor for n in s.plan.nodes)+s.artifacts:
            restored=wire.parse_document(wire.serialize_document(obj)).document
            self.assertEqual(restored,obj)
            self.assertEqual(restored.fingerprint(),obj.fingerprint())
        n=s.plan.nodes[0]
        request=sdk.DomainRequest(n.descriptor,n.operation,artifacts=s.artifacts,provenance=s.provenance)
        self.assertEqual(wire.parse_document(wire.serialize_document(request)).document,request)

    def test_record_to_artifact_and_provenance_continuity(self):
        s,records=fixture()
        scope=s.provenance[0]
        for a in s.artifacts:
            self.assertIn(scope,a.provenance)
        for n in s.plan.nodes:
            self.assertIn(scope,n.registration.candidate.provenance)
            self.assertIn(scope,n.provenance)
        for e in s.plan.handoffs:
            self.assertIn(scope,e.provenance)
        for c in s.admissions:
            self.assertIn(scope,c.request.provenance)
        self.assertEqual(records["fabrication"].input.variant.fingerprint(),records["variant"].fingerprint())
        self.assertEqual(records["session"].task.inputs,tuple(sorted((reference(records["fabrication"]),
            reference(records["story"]),reference(records["trace"])),key=lambda r:sdk._json(r.record()))))
        self.assertEqual(records["request"].inputs,(reference(records["intent"]),))

    def test_existing_artifact_and_planned_output_distinct(self):
        s,_=fixture()
        for initial in s.plan.initial_inputs:
            self.assertIn(initial.artifact,s.artifacts)
            self.assertNotEqual(initial.artifact.platform.kind,"agent")
        for n in s.plan.nodes:
            self.assertIs(type(n.outputs[0]),orch.OutputSlot)
            self.assertNotIn("digest",n.outputs[0].record())
        self.assertTrue(all(not e.record()["artifact_exists"] for e in s.plan.handoffs))

    def test_motion_simulation_records_without_evolution(self):
        with patch.object(sim,"simulate",side_effect=AssertionError("simulation executed")), \
             patch.object(sim,"evolve",side_effect=AssertionError("evolution executed")):
            s,r=fixture()
            self.assertEqual(r["trace"].steps,())
            self.assertEqual(r["trace"].specification.step_count,0)
            self.assertFalse(r["trace"].record()["physical_event_proven"])
            self.assertEqual(r["state"].record()["origin_status"],"CALLER_SUPPLIED")
            self.assertEqual(acceptance.PlatformAcceptanceResult(s).status,"PASS")

    def test_narrative_origin_not_external_fact(self):
        s,r=fixture()
        self.assertFalse(r["story"].record()["external_fact_verified"])
        self.assertTrue(all(e.record()["assertion_status"]=="NARRATIVE_DECLARATION" for e in r["story"].events))
        a=next(i.artifact for i in s.plan.initial_inputs if i.target.node=="narrative")
        self.assertEqual(a.platform.kind,"narrative")
        self.assertIn(reference(r["story"]),r["session"].task.inputs)

    def test_agent_identity_intent_and_principal_distinct(self):
        s,r=fixture()
        identity=r["session"].context.descriptor.identity
        principal=s.admissions[0].request.principal
        self.assertNotEqual(identity,principal)
        self.assertNotIsInstance(identity,Principal)
        self.assertEqual(r["intent"].record()["execution"],"NOT_PERFORMED")
        self.assertFalse(r["intent"].record()["grants_authority"])
        self.assertEqual(r["session"].context.descriptor.identity,agent_fixture.fixture()[0].context.descriptor.identity)

    def test_parametric_fabrication_boundaries(self):
        _,r=fixture()
        self.assertFalse(r["variant"].record()["geometry_generated"])
        self.assertFalse(r["variant"].record()["engineering_safety_proven"])
        self.assertEqual(r["fabrication"].record()["execution"],"NOT_PERFORMED")
        self.assertFalse(r["fabrication"].record()["grants_authority"])
        self.assertNotEqual(r["variant"],r["fabrication"])
        self.assertEqual(fab.FabricationValidation(r["fabrication"],fab_fixture.fixture()[1]).status,"VALID")

    def test_external_report_is_not_verified_truth_or_authentication(self):
        s,r=fixture()
        self.assertEqual(r["response"].record()["evidence"],"EXTERNALLY_SUPPLIED")
        self.assertFalse(r["response"].record()["authenticated"])
        self.assertFalse(r["request"].record()["execution_permission"])
        case=next(c for c in s.admissions if c.request.node.identifier=="external")
        self.assertEqual(case.decision.status,"INCOMPLETE")
        self.assertIn("SECURITY_PROVIDER_AUTHENTICATION_MISSING",{f.code for f in case.decision.findings})
        self.assertFalse(hasattr(r["response"].provider,"organization"))
        self.assertNotEqual(r["response"].provider,r["session"].context.descriptor.identity)

    def test_governance_plus_plan_not_authority(self):
        s,_=fixture()
        c=next(c for c in s.admissions if c.request.node.identifier=="parametric")
        request=replace(c.request,authority=None)
        self.assertEqual(request.node.registration.status,"ADMISSIBLE")
        self.assertEqual(orch.OrchestrationValidation(request.plan).status,"VALID")
        decision=sec.SecurityAdmissionDecision(request)
        self.assertEqual(decision.status,"INCOMPLETE")
        self.assertIn("SECURITY_AUTHORITY_MISSING",{f.code for f in decision.findings})

    def test_wrong_principal_capability_resource_denial_chain(self):
        s,_=fixture()
        c=next(c for c in s.admissions if c.request.node.identifier=="fabrication")
        before=(s.plan.fingerprint(),s.plan.catalog.fingerprint())
        for field in ("principal","capability","resource"):
            grant=replace(c.request.authority.grants[0],**{field:"wrong:identity"})
            request=replace(c.request,authority=AuthorityEngine((grant,)))
            decision=sec.SecurityAdmissionDecision(request)
            self.assertEqual(decision.status,"DENIED")
            self.assertIn("SECURITY_AUTHORITY_DENIED",{f.code for f in decision.findings})
            newcase=replace(c,request=request,decision=decision,expected_status="DENIED")
            negative=replace(s,admissions=tuple(newcase if v==c else v for v in s.admissions))
            self.assertEqual(acceptance.PlatformAcceptanceResult(negative).status,"PASS")
            self.assertEqual(before,(s.plan.fingerprint(),s.plan.catalog.fingerprint()))

    def test_package_content_substitution_rejected_and_identity_changes(self):
        s,_=fixture()
        original=s.packages[0]
        wrong=replace(original,content=replace(original.content,fingerprint="B"*64))
        self.assertEqual(original.coordinate,wrong.coordinate)
        self.failed(replace(s,packages=(wrong,)),"ACCEPTANCE_PACKAGE_BASELINE_MISMATCH")
        c=s.admissions[0]
        package=replace(c.request.package,manifest=replace(c.request.package.manifest,exported_capabilities=("changed.content",)))
        request=replace(c.request,package=package)
        decision=sec.SecurityAdmissionDecision(request)
        self.assertEqual(decision.status,"DENIED")
        self.assertIn("SECURITY_PACKAGE_MISMATCH",{f.code for f in decision.findings})
        self.assertNotEqual(c.request.fingerprint(),request.fingerprint())
        self.assertNotEqual(c.decision.fingerprint(),decision.fingerprint())

    def test_descriptor_substitution_rejected(self):
        s,_=fixture()
        c=s.admissions[0]
        revised=replace(c.request.node.descriptor,contract_version=ExactVersion(2,0,0))
        request=replace(c.request,node=replace(c.request.node,descriptor=revised))
        self.assertEqual(revised.identity.identifier,c.request.node.descriptor.identity.identifier)
        self.assertEqual(sec.SecurityAdmissionDecision(request).status,"DENIED")
        self.assertNotEqual(request.fingerprint(),c.request.fingerprint())
        with self.assertRaises(sec.SecurityIntegrationError) as caught:
            sec.bind_decision(c.decision,request)
        self.assertEqual(caught.exception.code,"SECURITY_ADMISSION_REPLAY_MISMATCH")

    def test_legitimate_package_revision_reidentifies_dependent_chain(self):
        s,records=fixture()
        c=next(v for v in s.admissions if v.request.node.identifier=="agent")
        original=c.request.node
        manifest=replace(c.request.package.manifest,exported_capabilities=("revised.package",))
        descriptor=replace(original.descriptor,implementation=sdk.ImplementationPackage.from_manifest(manifest))
        domain_record=replace(records["session"].context.descriptor,platform=descriptor)
        artifact=agent.agent_artifact(domain_record)
        candidate=replace(original.registration.candidate,descriptor=descriptor,
            evidence=tuple(replace(e,descriptor_fingerprint=descriptor.fingerprint()) for e in original.registration.candidate.evidence))
        registration=gov.evaluate(s.plan.catalog.policy,candidate)
        self.assertEqual(registration.status,"ADMISSIBLE")
        node=replace(original,descriptor=descriptor,registration=registration)
        catalog=gov.DomainCatalogSnapshot(s.plan.catalog.policy,tuple(registration if d==original.registration else d for d in s.plan.catalog.entries))
        plan=replace(s.plan,catalog=catalog,nodes=tuple(node if n==original else n for n in s.plan.nodes))
        self.assertEqual(orch.OrchestrationValidation(plan).status,"VALID")
        request=replace(c.request,plan=plan,node=node,package=sec.PackageSecurityEvidence(manifest,()))
        self.assertEqual(sec.SecurityAdmissionDecision(request).status,"DENIED")
        request=replace(request,policy=replace(request.policy,plan_fingerprint=plan.fingerprint(),node_fingerprint=node.fingerprint()))
        decision=sec.SecurityAdmissionDecision(request)
        self.assertEqual(decision.status,"ADMISSIBLE")
        for old,new in ((original.descriptor.implementation.content.fingerprint,descriptor.implementation.content.fingerprint),
            (original.descriptor.fingerprint(),descriptor.fingerprint()),
            (records["session"].context.descriptor.fingerprint(),domain_record.fingerprint()),
            (original.registration.candidate.fingerprint(),candidate.fingerprint()),
            (original.registration.fingerprint(),registration.fingerprint()),(s.plan.catalog.fingerprint(),catalog.fingerprint()),
            (s.plan.fingerprint(),plan.fingerprint()),(original.fingerprint(),node.fingerprint()),
            (c.request.fingerprint(),request.fingerprint()),(c.decision.fingerprint(),decision.fingerprint())):
            self.assertNotEqual(old,new)
        self.assertEqual(artifact.implementation,descriptor.implementation)
        with self.assertRaises(sec.SecurityIntegrationError) as caught:
            sec.bind_decision(c.decision,request)
        self.assertEqual(caught.exception.code,"SECURITY_ADMISSION_REPLAY_MISMATCH")

    def test_acceptance_projection_reuses_frozen_owner_evidence(self):
        s,_=fixture()
        before=s.record()
        with patch.object(sec.SecurityAdmissionDecision,"_assessment",side_effect=AssertionError("admission re-evaluated")):
            self.assertEqual(s.record(),before)
            self.assertEqual(acceptance.PlatformAcceptanceResult(s).status,"PASS")

    def test_governance_and_catalog_substitution_rejected(self):
        s,_=fixture()
        c=s.admissions[0]
        candidate=replace(c.request.node.registration.candidate,contract=None)
        alternative=gov.evaluate(s.plan.catalog.policy,candidate)
        self.assertEqual(alternative.status,"ADMISSIBLE")
        request=replace(c.request,node=replace(c.request.node,registration=alternative))
        self.assertEqual(sec.SecurityAdmissionDecision(request).status,"DENIED")
        catalog=replace(s.plan.catalog,predecessor="B"*64)
        request=replace(c.request,plan=replace(s.plan,catalog=catalog))
        self.assertEqual(sec.SecurityAdmissionDecision(request).status,"DENIED")

    def test_cross_node_plan_operation_handoff_replay_rejected(self):
        s,_=fixture()
        c=s.admissions[0]
        another=s.admissions[1].request
        requests=(another,replace(c.request,plan=replace(s.plan,identity=orch.OrchestrationPlanIdentity("other-plan"))),
            replace(c.request,node=replace(c.request.node,operation="unknown.operation")),
            replace(c.request,plan=replace(s.plan,handoffs=s.plan.handoffs[:-1])))
        for request in requests:
            with self.assertRaises(sec.SecurityIntegrationError) as caught:
                sec.bind_decision(c.decision,request)
            self.assertEqual(caught.exception.code,"SECURITY_ADMISSION_REPLAY_MISMATCH")
        case=replace(c,request=another)
        self.failed(replace(s,admissions=tuple(case if v==c else v for v in s.admissions)),"ACCEPTANCE_ADMISSION_REPLAY_MISMATCH")

    def test_artifact_origin_and_descriptor_substitution(self):
        s,_=fixture()
        for a in s.artifacts:
            self.assertIn(a.platform.kind,("motion","parametric","fabrication","agent","narrative","external-adapter"))
        a=s.artifacts[0]
        wrong=replace(a,descriptor_fingerprint="B"*64)
        self.failed(replace(s,artifacts=tuple(wrong if v==a else v for v in s.artifacts)),"ACCEPTANCE_ARTIFACT_BINDING_MISMATCH")

    def test_identity_separation_matrix(self):
        s,r=fixture()
        self.assertNotEqual(r["session"].context.descriptor.identity,s.admissions[0].request.principal)
        self.assertNotEqual(r["story"].story.characters[0].identity,r["session"].context.descriptor.identity)
        self.assertNotEqual(r["variant"],r["fabrication"])
        self.assertFalse(hasattr(r["fabrication"],"physical_object"))
        self.assertNotEqual(s.plan.nodes[0].registration,s.admissions[0].decision)
        self.assertNotEqual(type(s.admissions[0].decision).__name__,"ExecutionResult")
        self.assertEqual(acceptance.PlatformAcceptanceResult(s).record()["execution"],"NOT_PERFORMED")

    def test_trust_boundary_and_crypto_unavailable(self):
        s,_=fixture()
        c=s.admissions[0]
        strict=replace(c.request,policy=replace(c.request.policy,require_package_trust=True))
        decision=sec.SecurityAdmissionDecision(strict)
        self.assertEqual(decision.status,"INCOMPLETE")
        self.assertIn("SECURITY_CRYPTO_UNAVAILABLE",{f.code for f in decision.findings})
        self.assertFalse(decision.record()["cryptographic_trust_established"])
        self.assertFalse(acceptance.PlatformAcceptanceResult(s).record()["grants_trust"])

    def test_acceptance_result_not_execution_or_release(self):
        s,_=fixture()
        result=acceptance.PlatformAcceptanceResult(s)
        self.assertFalse(result.record()["grants_authority"])
        self.assertFalse(result.record()["freeze_performed"])
        for field in ("run","execute","schedule","credential","model","release","token"):
            self.assertFalse(hasattr(result,field))

    def test_missing_and_failed_matrix_observations(self):
        s,_=fixture()
        incomplete=replace(s,evidence=s.evidence[1:])
        self.assertEqual(acceptance.PlatformAcceptanceResult(incomplete).status,"INCOMPLETE")
        self.failed(replace(s,evidence=(replace(s.evidence[0],status="FAIL"),)+s.evidence[1:]),"ACCEPTANCE_OBSERVATION_FAILED")
        self.assertEqual(acceptance.PlatformAcceptanceResult(replace(s,admissions=())).status,"INCOMPLETE")

    def test_missing_initial_evidence_and_unexpected_admission(self):
        s,_=fixture()
        initial=s.plan.initial_inputs[0].artifact
        incomplete=replace(s,artifacts=tuple(a for a in s.artifacts if a!=initial))
        self.assertEqual(acceptance.PlatformAcceptanceResult(incomplete).status,"INCOMPLETE")
        c=s.admissions[0]
        self.failed(replace(s,admissions=(replace(c,expected_status="DENIED"),)+s.admissions[1:]),"ACCEPTANCE_ADMISSION_UNEXPECTED")

    def test_explicit_evidence_and_no_callbacks_or_duplicate_rows(self):
        s,_=fixture()
        self.error("ACCEPTANCE_EVIDENCE_INVALID",lambda:replace(s,evidence=list(s.evidence)))
        self.error("ACCEPTANCE_DUPLICATE_EVIDENCE",lambda:replace(s,evidence=s.evidence+(s.evidence[0],)))
        self.error("ACCEPTANCE_ADMISSION_INVALID",lambda:replace(s,admissions=(lambda:True,)))
        self.error("ACCEPTANCE_EVIDENCE_INVALID",lambda:replace(s.evidence[0],status=True))

    def test_equivalent_complete_scenarios_deterministic(self):
        a,_=fixture()
        b,_=fixture()
        b=replace(b,admissions=b.admissions[::-1],artifacts=b.artifacts[::-1],domain_records=b.domain_records[::-1],
            evidence=b.evidence[::-1],plan=replace(b.plan,nodes=b.plan.nodes[::-1],handoffs=b.plan.handoffs[::-1]))
        self.assertEqual(a.record(),b.record())
        self.assertEqual(a.fingerprint(),b.fingerprint())
        self.assertEqual(acceptance.PlatformAcceptanceResult(a).record(),acceptance.PlatformAcceptanceResult(b).record())
        self.assertEqual(acceptance.PlatformAcceptanceResult(a).fingerprint(),acceptance.PlatformAcceptanceResult(b).fingerprint())

    def test_security_admission_and_acceptance_do_not_execute(self):
        s,_=fixture()
        with patch.object(sim,"simulate",side_effect=AssertionError("simulation executed")), \
             patch.object(sim,"evolve",side_effect=AssertionError("evolution executed")), \
             patch.object(gov,"evaluate",side_effect=AssertionError("governance redefined")), \
             patch.object(AuthorityEngine,"from_grants",side_effect=AssertionError("authority minted")), \
             patch.object(sdk.DomainArtifact,"from_bytes",side_effect=AssertionError("output fabricated")):
            self.assertEqual(acceptance.PlatformAcceptanceResult(s).status,"PASS")
            self.assertEqual(acceptance.PlatformAcceptanceResult(s).record()["execution"],"NOT_PERFORMED")

    def test_substantial_plan_and_admission_matrix(self):
        s,_=fixture()
        base=next(c for c in s.admissions if c.request.node.identifier=="agent")
        contract=orch.ArtifactContract("model",provenance=s.provenance)
        nodes=tuple(replace(base.request.node,identifier="node-"+str(i).zfill(3),
            inputs=() if i==0 else (orch.InputSlot("input",contract),),outputs=(orch.OutputSlot("output",contract),)) for i in range(128))
        edges=tuple(orch.ArtifactHandoff("edge-"+str(i).zfill(3),orch.SlotReference(nodes[i].identifier,"output"),
            orch.SlotReference(nodes[i+1].identifier,"input"),contract,s.provenance) for i in range(127))
        plan=replace(s.plan,nodes=nodes,handoffs=edges,initial_inputs=(),terminal_outputs=(orch.SlotReference(nodes[-1].identifier,"output"),))
        cases=[]
        for node in nodes:
            request=replace(base.request,plan=plan,node=node,policy=replace(base.request.policy,
                plan_fingerprint=plan.fingerprint(),node_fingerprint=node.fingerprint()))
            cases.append(acceptance.AdmissionExpectation("case-"+node.identifier,request,sec.SecurityAdmissionDecision(request),"ADMISSIBLE"))
        scenario=replace(s,plan=plan,admissions=tuple(cases),artifacts=())
        self.assertEqual(orch.OrchestrationValidation(plan).topological_order,tuple(n.identifier for n in nodes))
        self.assertEqual(acceptance.PlatformAcceptanceResult(scenario).status,"PASS")
        reversed_scenario=replace(scenario,admissions=scenario.admissions[::-1])
        self.assertEqual(scenario.fingerprint(),reversed_scenario.fingerprint())

    def test_static_security_and_ownership_audit(self):
        tree=ast.parse(Path(acceptance.__file__).read_text(encoding="utf-8"))
        imports={n.module for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)}
        self.assertEqual(imports,{"dataclasses","tooling","tooling.package_manifest"})
        self.assertFalse(any(isinstance(n,ast.Import) for n in ast.walk(tree)))
        tooling={a.name for n in ast.walk(tree) if isinstance(n,ast.ImportFrom) and n.module=="tooling" for a in n.names}
        self.assertEqual(tooling,{"domain_platform","cross_domain_orchestration","security_integration"})
        calls={n.func.id for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name)}
        self.assertFalse(calls & {"open","eval","exec","compile","__import__","getattr","AuthorityEngine","AuthorityGrant"})
        attrs={n.attr for n in ast.walk(tree) if isinstance(n,ast.Attribute)}
        self.assertFalse(attrs & {"check","execute","run","simulate","evolve","dispatch","from_grants","connect",
            "send","getenv","read_bytes","read_text","glob","load","loads","register","evaluate","from_bytes"})
        self.assertFalse(any(isinstance(n,(ast.AsyncFunctionDef,ast.Await,ast.AsyncFor)) for n in ast.walk(tree)))
        self.assertEqual({n.name for n in tree.body if isinstance(n,ast.ClassDef)},
            {"AcceptanceError","AcceptanceEvidence","AdmissionExpectation","PlatformAcceptanceScenario","PlatformAcceptanceResult"})


if __name__=="__main__":
    unittest.main()
