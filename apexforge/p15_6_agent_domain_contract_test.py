"""Passive agent contract, identity domains and explicit ledger lineage."""
import ast
from dataclasses import FrozenInstanceError, replace
from pathlib import Path
import unittest

from agents.model import AgentIdentity, AgentDefinition
from authority.model import Principal, AuthorityGrant
from language.narrative_model import NarrativeIdentity
from tooling import agent_domain as agent
from tooling import domain_platform as sdk
from tooling import domain_interchange as interchange
import p15_3_apexmotion_domain_contract_test as fixtures


def fixture():
    manifest, _, motion_state, *_ = fixtures.fixture()
    descriptor = agent.AgentDescriptor(AgentDefinition(AgentIdentity("agent-one"), ("reviewer",)),
        agent.agent_platform(manifest), ("review",), ("document",), (sdk.DomainCapability("review.request"),),
        provenance=motion_state.provenance)
    context = agent.AgentContext(agent.AgentSessionIdentity("session-one"), descriptor)
    task = agent.AgentTask("task-one", "Review supplied evidence", provenance=motion_state.provenance)
    snapshot = agent.AgentSessionSnapshot(context, task, provenance=motion_state.provenance)
    observation = agent.AgentObservation("observation-one", context, "document", motion_state.provenance)
    decision = agent.AgentDecision("decision-one", context, (observation.fingerprint(),), ("review", "wait"), "review")
    intent = agent.AgentActionIntent("intent-one", context, "review", motion_state.provenance[0],
        agent.ActionCapabilityRequirement("review.request"), tool=motion_state.provenance[0],
        decision_fingerprint=decision.fingerprint())
    receipt = agent.AgentActionReceipt("receipt-one", context, intent.fingerprint(), "SUCCEEDED")
    return snapshot, observation, decision, intent, receipt


class AgentDomainTests(unittest.TestCase):
    def rejected(self, code, fn):
        with self.assertRaises(agent.AgentDomainError) as context:
            fn()
        self.assertEqual(context.exception.code, code)

    def test_platform_package_binding(self):
        snapshot, *_ = fixture()
        descriptor = snapshot.context.descriptor
        self.assertEqual(descriptor.platform.identity, sdk.DomainPlatformIdentity("apexforge.agent", "agent"))
        self.assertEqual(descriptor.platform.implementation, sdk.ImplementationPackage.from_manifest(fixtures.fixture()[0]))
        self.assertEqual(descriptor.record()["contract_version"], "1.0.0")

    def test_frozen_identity_reuse(self):
        self.assertIs(agent.AgentIdentity, AgentIdentity)
        snapshot, *_ = fixture()
        self.assertEqual(snapshot.context.descriptor.identity, AgentIdentity("agent-one"))
        self.assertNotEqual(snapshot.context.session, AgentIdentity("session-one"))

    def test_identity_domains_distinct(self):
        identity = AgentIdentity("same")
        for other in (Principal("same"), sdk.DomainCapability("same"), agent.ActionCapabilityRequirement("same"),
            agent.AgentSessionIdentity("same"), NarrativeIdentity("character", ("same",))):
            self.assertNotEqual(identity, other)
        self.assertNotEqual(sdk.DomainCapability("same"), agent.ActionCapabilityRequirement("same"))

    def test_descriptor_authority_absent(self):
        snapshot, *_ = fixture()
        self.assertFalse(snapshot.context.descriptor.record()["grants_authority"])
        self.assertEqual(snapshot.context.descriptor.definition.archetype_ids, ("reviewer",))
        self.assertNotIsInstance(snapshot.context.descriptor, AuthorityGrant)

    def test_models_immutable(self):
        snapshot, observation, decision, intent, receipt = fixture()
        for obj, field in ((snapshot, "ledger"), (snapshot.context, "session"), (snapshot.context.descriptor, "actions"),
            (snapshot.task, "objective"), (observation, "kind"), (decision, "selected"),
            (intent, "action"), (receipt, "external_status")):
            with self.assertRaises(FrozenInstanceError):
                setattr(obj, field, None)

    def test_task_passive(self):
        snapshot, *_ = fixture()
        self.assertEqual(snapshot.task.record()["execution"], "NOT_PERFORMED")
        self.assertFalse(snapshot.task.record()["grants_authority"])

    def test_observation_not_verified(self):
        _, observation, *_ = fixture()
        self.assertFalse(observation.record()["verified_fact"])
        self.assertEqual(observation.record()["origin"], "CALLER_SUPPLIED")

    def test_observation_kind_unknown(self):
        _, observation, *_ = fixture()
        self.rejected("AGENT_OBSERVATION_KIND_UNDECLARED", lambda: replace(observation, kind="sensor"))

    def test_decision_not_hidden_reasoning(self):
        _, _, decision, *_ = fixture()
        self.assertFalse(decision.record()["private_reasoning_captured"])
        self.assertEqual(decision.record()["selection_origin"], "CALLER_SUPPLIED")

    def test_decision_invalid_selection(self):
        _, _, decision, *_ = fixture()
        self.rejected("AGENT_DECISION_SELECTION_INVALID", lambda: replace(decision, selected="invented"))

    def test_action_passive_requirement(self):
        _, _, _, intent, _ = fixture()
        self.assertFalse(intent.record()["grants_authority"])
        self.assertFalse(intent.requirement.record()["grants_authority"])
        self.assertEqual(intent.record()["execution"], "NOT_PERFORMED")
        self.assertEqual(intent.record()["tool"], intent.tool.record())

    def test_action_unknown(self):
        _, _, _, intent, _ = fixture()
        self.rejected("AGENT_ACTION_UNDECLARED", lambda: replace(intent, action="execute"))

    def test_capability_typed(self):
        _, _, _, intent, _ = fixture()
        self.rejected("AGENT_ACTION_REQUIREMENT_INVALID", lambda: replace(intent, requirement=sdk.DomainCapability("review.request")))

    def test_external_receipt_is_unverified_claim(self):
        _, _, _, intent, receipt = fixture()
        self.assertEqual(receipt.intent_fingerprint, intent.fingerprint())
        self.assertEqual(receipt.record()["evidence_origin"], "EXTERNALLY_SUPPLIED")
        self.assertFalse(receipt.record()["execution_verified"])

    def test_receipt_invalid_status(self):
        *_, receipt = fixture()
        self.rejected("AGENT_RECEIPT_STATUS_INVALID", lambda: replace(receipt, external_status="VERIFIED"))

    def test_session_append_lineage(self):
        snapshot, *events = fixture()
        before = snapshot.canonical_json()
        for event in events:
            successor = agent.append_event(snapshot, event)
            self.assertEqual(successor.predecessor_fingerprint, snapshot.fingerprint())
            self.assertEqual(successor.ledger, snapshot.ledger + (event,))
            self.assertEqual(successor.context, snapshot.context)
            snapshot = successor
        self.assertEqual([e["sequence"] for e in snapshot.record()["ledger"]], [1, 2, 3, 4])
        self.assertEqual(fixture()[0].canonical_json(), before)

    def test_duplicate_event_rejected(self):
        snapshot, observation, *_ = fixture()
        snapshot = agent.append_event(snapshot, observation)
        self.rejected("AGENT_LEDGER_EVENT_DUPLICATE", lambda: agent.append_event(snapshot, observation))

    def test_conflicting_event_rejected(self):
        snapshot, observation, *_ = fixture()
        snapshot = agent.append_event(snapshot, observation)
        self.rejected("AGENT_LEDGER_EVENT_DUPLICATE", lambda: agent.append_event(snapshot, replace(observation, evidence=())))

    def test_context_mismatch(self):
        snapshot, observation, *_ = fixture()
        context = replace(observation.context, session=agent.AgentSessionIdentity("another"))
        self.rejected("AGENT_LEDGER_CONTEXT_MISMATCH", lambda: agent.append_event(snapshot, replace(observation, context=context)))

    def test_decision_requires_prior_observation(self):
        snapshot, _, decision, *_ = fixture()
        self.rejected("AGENT_DECISION_OBSERVATION_MISSING", lambda: agent.append_event(snapshot, decision))

    def test_intent_requires_prior_decision(self):
        snapshot, _, _, intent, _ = fixture()
        self.rejected("AGENT_INTENT_DECISION_MISSING", lambda: agent.append_event(snapshot, intent))

    def test_receipt_requires_prior_intent(self):
        snapshot, *_, receipt = fixture()
        self.rejected("AGENT_RECEIPT_INTENT_MISSING", lambda: agent.append_event(snapshot, receipt))

    def test_order_is_semantic(self):
        snapshot, *events = fixture()
        self.rejected("AGENT_RECEIPT_INTENT_MISSING", lambda: replace(snapshot, ledger=tuple(reversed(events))))

    def test_declaration_order_independence(self):
        snapshot, _, decision, *_ = fixture()
        other = replace(decision, alternatives=tuple(reversed(decision.alternatives)))
        self.assertEqual(decision.fingerprint(), other.fingerprint())
        self.assertEqual(snapshot.context.descriptor.fingerprint(), fixture()[0].context.descriptor.fingerprint())

    def test_provenance_retained(self):
        snapshot, *_ = fixture()
        self.assertEqual(snapshot.record()["provenance"], [r.record() for r in snapshot.provenance])
        self.assertEqual(snapshot.record()["context"]["descriptor_fingerprint"], snapshot.context.descriptor.fingerprint())

    def test_artifact_sdk_interchange(self):
        snapshot, *events = fixture()
        for event in events:
            snapshot = agent.append_event(snapshot, event)
        artifact = agent.agent_artifact(snapshot)
        artifact.verify_bytes(sdk._json({"record": snapshot.record(),
            "record_fingerprint": snapshot.fingerprint()}).encode("utf-8"))
        self.assertEqual(artifact.implementation, snapshot.context.descriptor.platform.implementation)
        request = sdk.DomainRequest(snapshot.context.descriptor.platform, artifact.operation, artifacts=(artifact,))
        result = sdk.DomainResult(request, "COMPLETE", outputs=(artifact,))
        self.assertEqual(interchange.parse_document(interchange.serialize_document(result)).document, result)
        self.assertEqual(snapshot.record()["semantic_authority"], "CANONICAL_AIR")

    def test_large_ledger(self):
        snapshot, observation, *_ = fixture()
        events = tuple(replace(observation, identifier="observation-" + str(i)) for i in range(1000))
        a, b = replace(snapshot, ledger=events), replace(snapshot, ledger=events)
        self.assertEqual(a.fingerprint(), b.fingerprint())
        self.assertEqual(len(a.record()["ledger"]), 1000)
        next_snapshot = agent.append_event(a, replace(observation, identifier="last"))
        self.assertEqual(next_snapshot.predecessor_fingerprint, a.fingerprint())

    def test_malformed_collections(self):
        snapshot, *_ = fixture()
        self.rejected("AGENT_DECLARATION_INVALID", lambda: replace(snapshot.context.descriptor, actions=([],)))
        self.rejected("AGENT_LEDGER_INVALID", lambda: replace(snapshot, ledger=[]))

    def test_security_static(self):
        tree = ast.parse(Path(agent.__file__).read_text(encoding="utf-8"))
        imports = {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
        self.assertEqual(imports, {"dataclasses", "agents.model", "tooling", "tooling.package_manifest"})
        forbidden = {"eval", "exec", "open", "__import__", "compile", "RuntimeEngine", "AuthorityEngine"}
        calls = {n.func.id for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
        self.assertFalse(calls & forbidden)


if __name__ == "__main__":
    unittest.main()
