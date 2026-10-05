"""Passive orchestration binding, graph, lineage and non-execution evidence."""
import ast
from dataclasses import replace, FrozenInstanceError, fields
from pathlib import Path
import unittest
from unittest.mock import patch

from tooling import cross_domain_orchestration as orch
from tooling import domain_platform as sdk, domain_governance as gov
from tooling import apexmotion, narrative_domain, agent_domain, parametric_domain, fabrication_domain, external_adapter
from tooling.package_manifest import PackageManifest, PackageCoordinate, ExactVersion, CanonicalReference


REFERENCE = CanonicalReference("apexforge.provenance/v1", "provenance-scope", "A" * 64)


def descriptor(kind="parametric"):
    manifest = PackageManifest(PackageCoordinate("example.domains", kind, ExactVersion(1, 0, 0)))
    factory = {"parametric": parametric_domain.parametric_platform,
        "fabrication": fabrication_domain.fabrication_platform, "agent": agent_domain.agent_platform,
        "narrative": narrative_domain.narrative_platform, "motion": apexmotion.apexmotion_platform,
        "external-adapter": external_adapter.external_platform}[kind]
    return factory(manifest)


def admission(d, policy=None):
    policy = policy or gov.DomainGovernancePolicy(gov.DomainGovernancePolicyIdentity("policy-one"),
        ExactVersion(1, 0, 0), tuple(sdk.KINDS))
    candidate = gov.DomainRegistrationCandidate(d,
        tuple(gov.GovernanceEvidence(k, REFERENCE, d.fingerprint()) for k in gov.EVIDENCE_KINDS),
        (REFERENCE,), REFERENCE)
    return gov.evaluate(policy, candidate)


def fixture(kinds=("parametric", "fabrication")):
    decisions = tuple(admission(descriptor(k)) for k in kinds)
    catalog = gov.DomainCatalogSnapshot(decisions[0].policy, decisions)
    contract = orch.ArtifactContract("model", REFERENCE, (REFERENCE,))
    nodes = tuple(orch.OrchestrationNode("node-" + str(n), d, d.candidate.descriptor,
        d.candidate.descriptor.operations[0], () if n == 0 else (orch.InputSlot("input", contract),),
        (orch.OutputSlot("output", contract),), d.candidate.descriptor.capabilities, (REFERENCE,))
        for n, d in enumerate(decisions))
    edges = tuple(orch.ArtifactHandoff("edge-" + str(n), orch.SlotReference(nodes[n].identifier, "output"),
        orch.SlotReference(nodes[n+1].identifier, "input"), contract, (REFERENCE,)) for n in range(len(nodes)-1))
    return orch.CrossDomainOrchestrationPlan(orch.OrchestrationPlanIdentity("plan-one"), catalog, nodes,
        edges, terminal_outputs=(orch.SlotReference(nodes[-1].identifier, "output"),), provenance=(REFERENCE,))


class OrchestrationTests(unittest.TestCase):
    def error(self, code, fn):
        with self.assertRaises(orch.OrchestrationError) as caught:
            fn()
        self.assertEqual(caught.exception.code, code)
        self.assertEqual(str(caught.exception), code)

    def invalid(self, plan, code):
        v = orch.OrchestrationValidation(plan)
        self.assertEqual(v.status, "INVALID")
        self.assertIn(code, {f.code for f in v.findings})
        self.assertEqual(v.topological_order, ())

    def test_valid_passive_pipeline(self):
        p = fixture()
        v = orch.OrchestrationValidation(p)
        self.assertEqual(v.status, "VALID")
        self.assertEqual(v.findings, ())
        self.assertEqual(v.topological_order, ("node-0", "node-1"))
        self.assertFalse(v.record()["execution_evidence"])

    def test_caller_identity_and_separate_namespaces(self):
        p = fixture()
        self.assertEqual(p.identity.identifier, "plan-one")
        self.assertNotEqual(p.identity.fingerprint(), p.nodes[0].descriptor.identity.fingerprint())
        self.assertNotEqual(p.identity.fingerprint(), p.nodes[0].descriptor.implementation.content.fingerprint)
        for bad in ("Display Title", "/host/path", "", 1, lambda: "id"):
            self.error("ORCHESTRATION_ID_INVALID", lambda: orch.OrchestrationPlanIdentity(bad))

    def test_all_models_immutable(self):
        p = fixture()
        artifact = sdk.DomainArtifact.from_bytes(p.nodes[0].descriptor, p.nodes[0].operation, "model", b"supplied")
        objects = (p, p.identity, p.nodes[0], p.nodes[1].inputs[0], p.nodes[0].outputs[0],
            p.handoffs[0], p.handoffs[0].producer, p.handoffs[0].contract,
            orch.InitialInput(p.handoffs[0].consumer, artifact), orch.OrchestrationValidation(p),
            orch.OrchestrationFinding("ORCHESTRATION_CYCLE", "plan-one"))
        for obj in objects:
            with self.subTest(model=type(obj).__name__), self.assertRaises(FrozenInstanceError):
                setattr(obj, fields(obj)[0].name, None)

    def test_mutable_collections_and_callbacks_rejected(self):
        p = fixture()
        self.error("ORCHESTRATION_DUPLICATE_NODE", lambda: replace(p, nodes=list(p.nodes)))
        self.error("ORCHESTRATION_MODEL_INVALID", lambda: replace(p, provenance=(lambda: None,)))
        self.error("ORCHESTRATION_SLOT_INVALID", lambda: replace(p.nodes[0].outputs[0], contract="model"))
        self.error("ORCHESTRATION_SLOT_INVALID", lambda: orch.InputSlot("in", p.handoffs[0].contract, 1))

    def test_domain_name_is_insufficient(self):
        p = fixture()
        self.invalid(replace(p, catalog=replace(p.catalog, entries=())), "ORCHESTRATION_DOMAIN_NOT_GOVERNED")

    def test_exact_registration_reference_required(self):
        p = fixture()
        n = p.nodes[0]
        c = replace(n.registration.candidate, contract=None)
        revised = gov.evaluate(n.registration.policy, c)
        self.assertEqual(revised.status, "ADMISSIBLE")
        self.invalid(replace(p, nodes=(replace(n, registration=revised), p.nodes[1])),
            "ORCHESTRATION_DOMAIN_NOT_GOVERNED")

    def test_nonadmissible_registration(self):
        p = fixture()
        n = p.nodes[0]
        for candidate, expected in ((replace(n.registration.candidate, evidence=()), "INCOMPLETE"),
            (replace(n.registration.candidate, claims=("authority-grant",)), "REJECTED")):
            d = gov.evaluate(n.registration.policy, candidate)
            self.assertEqual(d.status, expected)
            self.invalid(replace(p, nodes=(replace(n, registration=d), p.nodes[1])),
                "ORCHESTRATION_DOMAIN_NOT_GOVERNED")

    def test_exact_descriptor_required(self):
        p = fixture()
        n = p.nodes[0]
        d = replace(n.descriptor, contract_version=ExactVersion(2, 0, 0))
        self.invalid(replace(p, nodes=(replace(n, descriptor=d), p.nodes[1])), "ORCHESTRATION_DESCRIPTOR_MISMATCH")

    def test_exact_package_content_required(self):
        p = fixture()
        n = p.nodes[0]
        package = replace(n.descriptor.implementation, content=replace(n.descriptor.implementation.content, fingerprint="B"*64))
        d = replace(n.descriptor, implementation=package)
        self.invalid(replace(p, nodes=(replace(n, descriptor=d), p.nodes[1])), "ORCHESTRATION_PACKAGE_MISMATCH")

    def test_exact_package_coordinate_required(self):
        p = fixture()
        n = p.nodes[0]
        package = replace(n.descriptor.implementation, coordinate=replace(n.descriptor.implementation.coordinate,
            version=ExactVersion(2, 0, 0)))
        self.invalid(replace(p, nodes=(replace(n, descriptor=replace(n.descriptor, implementation=package)), p.nodes[1])),
            "ORCHESTRATION_PACKAGE_MISMATCH")

    def test_undeclared_operation_fails_closed(self):
        p = fixture()
        self.invalid(replace(p, nodes=(replace(p.nodes[0], operation="arbitrary.run"), p.nodes[1])),
            "ORCHESTRATION_OPERATION_UNDECLARED")

    def test_descriptor_cannot_smuggle_operation(self):
        p = fixture()
        n = p.nodes[0]
        d = replace(n.descriptor, operations=n.descriptor.operations + ("arbitrary.run",))
        self.invalid(replace(p, nodes=(replace(n, descriptor=d, operation="arbitrary.run"), p.nodes[1])),
            "ORCHESTRATION_OPERATION_UNDECLARED")

    def test_capability_declaration_not_authority(self):
        p = fixture()
        self.assertFalse(orch.OrchestrationValidation(p).record()["grants_authority"])
        n = replace(p.nodes[0], capabilities=(sdk.DomainCapability("admin.run"),))
        self.invalid(replace(p, nodes=(n, p.nodes[1])), "ORCHESTRATION_CAPABILITY_UNDECLARED")

    def test_missing_required_input_is_incomplete(self):
        p = replace(fixture(), handoffs=())
        v = orch.OrchestrationValidation(p)
        self.assertEqual(v.status, "INCOMPLETE")
        self.assertEqual(v.topological_order, ())
        self.assertEqual(v.findings[0].code, "ORCHESTRATION_INPUT_MISSING")
        self.assertEqual(v.findings[0].slot, "input")
        self.assertEqual(p.initial_inputs, ())

    def test_optional_input_no_inference(self):
        p = fixture()
        n = replace(p.nodes[1], inputs=(replace(p.nodes[1].inputs[0], required=False),))
        p = replace(p, nodes=(p.nodes[0], n), handoffs=())
        self.assertEqual(orch.OrchestrationValidation(p).status, "VALID")
        self.assertEqual(p.initial_inputs, ())

    def test_initial_input_preserves_existing_origin(self):
        p = fixture(("narrative", "agent"))
        a = sdk.DomainArtifact.from_bytes(p.nodes[0].descriptor, p.nodes[0].operation, "model", b"caller bytes",
            provenance=(REFERENCE,))
        i = orch.InitialInput(p.handoffs[0].consumer, a, REFERENCE)
        p = replace(p, handoffs=(), initial_inputs=(i,))
        self.assertEqual(orch.OrchestrationValidation(p).status, "VALID")
        self.assertIs(p.initial_inputs[0].artifact, a)
        self.assertEqual(i.artifact.platform.kind, "narrative")
        self.assertEqual(i.record()["artifact"], a.record())
        self.assertFalse(i.record()["bytes_verified"])

    def test_initial_schema_kind_and_provenance_fail_closed(self):
        p = fixture()
        a = sdk.DomainArtifact.from_bytes(p.nodes[0].descriptor, p.nodes[0].operation, "model", b"caller bytes",
            provenance=(REFERENCE,))
        i = orch.InitialInput(p.handoffs[0].consumer, a, REFERENCE)
        for wrong in (replace(i, schema_reference=None), replace(i, artifact=replace(a, kind="data")),
            replace(i, artifact=replace(a, provenance=()))):
            self.invalid(replace(p, handoffs=(), initial_inputs=(wrong,)), "ORCHESTRATION_HANDOFF_INCOMPATIBLE")

    def test_initial_target_unknown(self):
        p = fixture()
        a = sdk.DomainArtifact.from_bytes(p.nodes[0].descriptor, p.nodes[0].operation, "model", b"supplied")
        self.invalid(replace(p, initial_inputs=(orch.InitialInput(orch.SlotReference("unknown", "input"), a),)),
            "ORCHESTRATION_HANDOFF_DANGLING")

    def test_planned_outputs_are_not_artifacts(self):
        p = fixture()
        self.assertIs(type(p.nodes[0].outputs[0]), orch.OutputSlot)
        self.assertNotIsInstance(p.nodes[0].outputs[0], sdk.DomainArtifact)
        self.assertNotIn("digest", p.nodes[0].outputs[0].record())
        self.assertFalse(p.handoffs[0].record()["artifact_exists"])
        self.assertFalse(p.handoffs[0].record()["transfer_executed"])

    def test_dangling_producer(self):
        p = fixture()
        e = replace(p.handoffs[0], producer=orch.SlotReference("absent", "output"))
        self.invalid(replace(p, handoffs=(e,)), "ORCHESTRATION_HANDOFF_DANGLING")

    def test_dangling_consumer(self):
        p = fixture()
        e = replace(p.handoffs[0], consumer=orch.SlotReference("absent", "input"))
        self.invalid(replace(p, handoffs=(e,)), "ORCHESTRATION_HANDOFF_DANGLING")

    def test_unknown_slots(self):
        p = fixture()
        for field in ("producer", "consumer"):
            ref = getattr(p.handoffs[0], field)
            e = replace(p.handoffs[0], **{field: replace(ref, slot="unknown")})
            self.invalid(replace(p, handoffs=(e,)), "ORCHESTRATION_HANDOFF_DANGLING")

    def test_incompatible_kind(self):
        p = fixture()
        e = replace(p.handoffs[0], contract=replace(p.handoffs[0].contract, kind="data"))
        self.invalid(replace(p, handoffs=(e,)), "ORCHESTRATION_HANDOFF_INCOMPATIBLE")

    def test_incompatible_exact_schema(self):
        p = fixture()
        e = replace(p.handoffs[0], contract=replace(p.handoffs[0].contract,
            schema_reference=replace(REFERENCE, fingerprint="B"*64)))
        self.invalid(replace(p, handoffs=(e,)), "ORCHESTRATION_HANDOFF_INCOMPATIBLE")

    def test_missing_structural_provenance(self):
        p = fixture()
        e = replace(p.handoffs[0], contract=replace(p.handoffs[0].contract, provenance=()))
        self.invalid(replace(p, handoffs=(e,)), "ORCHESTRATION_HANDOFF_INCOMPATIBLE")

    def test_ambiguous_multiple_producers(self):
        p = fixture()
        e = replace(p.handoffs[0], identifier="edge-two")
        self.invalid(replace(p, handoffs=p.handoffs+(e,)), "ORCHESTRATION_INPUT_AMBIGUOUS")

    def test_initial_plus_handoff_ambiguous(self):
        p = fixture()
        a = sdk.DomainArtifact.from_bytes(p.nodes[0].descriptor, p.nodes[0].operation, "model", b"existing", provenance=(REFERENCE,))
        self.invalid(replace(p, initial_inputs=(orch.InitialInput(p.handoffs[0].consumer, a, REFERENCE),)),
            "ORCHESTRATION_INPUT_AMBIGUOUS")

    def test_cycle_fails_closed(self):
        p = fixture()
        c = p.handoffs[0].contract
        n = replace(p.nodes[0], inputs=(orch.InputSlot("input", c),))
        back = orch.ArtifactHandoff("back", orch.SlotReference("node-1", "output"), orch.SlotReference("node-0", "input"), c)
        self.invalid(replace(p, nodes=(n, p.nodes[1]), handoffs=p.handoffs+(back,)), "ORCHESTRATION_CYCLE")

    def test_self_cycle_fails_closed(self):
        p = fixture(("agent",))
        c = p.nodes[0].outputs[0].contract
        n = replace(p.nodes[0], inputs=(orch.InputSlot("input", c),))
        e = orch.ArtifactHandoff("self", orch.SlotReference(n.identifier, "output"), orch.SlotReference(n.identifier, "input"), c)
        self.invalid(replace(p, nodes=(n,), handoffs=(e,)), "ORCHESTRATION_CYCLE")

    def test_duplicate_and_conflicting_nodes(self):
        p = fixture()
        for n in (p.nodes[0], replace(p.nodes[0], operation=p.nodes[0].descriptor.operations[-1])):
            self.error("ORCHESTRATION_DUPLICATE_NODE", lambda: replace(p, nodes=p.nodes+(n,)))

    def test_duplicate_and_conflicting_edges(self):
        p = fixture()
        for e in (p.handoffs[0], replace(p.handoffs[0], producer=orch.SlotReference("node-1", "output"))):
            self.error("ORCHESTRATION_DUPLICATE_EDGE", lambda: replace(p, handoffs=p.handoffs+(e,)))

    def test_duplicate_slot_identity(self):
        p = fixture()
        s = p.nodes[1].inputs[0]
        self.error("ORCHESTRATION_SLOT_INVALID", lambda: replace(p.nodes[1], inputs=(s, replace(s, required=False))))

    def test_terminal_output_unresolved(self):
        p = fixture()
        for ref in (orch.SlotReference("missing", "output"), orch.SlotReference("node-0", "missing")):
            self.invalid(replace(p, terminal_outputs=(ref,)), "ORCHESTRATION_OUTPUT_UNRESOLVED")

    def test_topology_canonical_tiebreak(self):
        p = fixture()
        # Readiness changes after removing a node: newly ready 'b' precedes ready 'z'.
        base = replace(p.nodes[0], inputs=())
        a, b, z = (replace(base, identifier=s) for s in ("a", "b", "z"))
        b = replace(b, inputs=(orch.InputSlot("input", p.handoffs[0].contract),))
        e = replace(p.handoffs[0], producer=orch.SlotReference("a", "output"), consumer=orch.SlotReference("b", "input"))
        p = replace(p, nodes=(z,b,a), handoffs=(e,), terminal_outputs=())
        self.assertEqual(orch.OrchestrationValidation(p).topological_order, ("a", "b", "z"))

    def test_input_order_independent_canonical_plan(self):
        p = fixture(("parametric", "fabrication", "external-adapter"))
        q = replace(p, nodes=p.nodes[::-1], handoffs=p.handoffs[::-1], catalog=replace(p.catalog, entries=p.catalog.entries[::-1]))
        self.assertEqual(p.canonical_json(), q.canonical_json())
        self.assertEqual(p.fingerprint(), q.fingerprint())
        self.assertEqual(orch.OrchestrationValidation(p).record(), orch.OrchestrationValidation(q).record())

    def test_catalog_revision_changes_plan(self):
        p = fixture()
        q = replace(p, catalog=replace(p.catalog, predecessor="B"*64))
        self.assertNotEqual(p.fingerprint(), q.fingerprint())
        self.assertEqual(orch.OrchestrationValidation(q).status, "VALID")

    def test_policy_revision_changes_plan(self):
        p = fixture()
        policy = replace(p.catalog.policy, version=ExactVersion(2, 0, 0))
        decisions = tuple(gov.evaluate(policy, n.registration.candidate) for n in p.nodes)
        nodes = tuple(replace(n, registration=d) for n,d in zip(p.nodes, decisions))
        q = replace(p, catalog=gov.DomainCatalogSnapshot(policy, decisions), nodes=nodes)
        self.assertNotEqual(p.fingerprint(), q.fingerprint())
        self.assertEqual(orch.OrchestrationValidation(q).status, "VALID")

    def test_descriptor_and_package_revisions_change_plan(self):
        p = fixture()
        n = p.nodes[0]
        revised_package = replace(n.descriptor.implementation,
            content=replace(n.descriptor.implementation.content, fingerprint="B"*64))
        for d in (replace(n.descriptor, contract_version=ExactVersion(2,0,0)),
            replace(n.descriptor, implementation=revised_package)):
            decision = admission(d, p.catalog.policy)
            nodes = (replace(n, descriptor=d, registration=decision), p.nodes[1])
            catalog = gov.DomainCatalogSnapshot(p.catalog.policy, (decision, p.nodes[1].registration))
            q = replace(p, nodes=nodes, catalog=catalog)
            self.assertEqual(orch.OrchestrationValidation(q).status, "VALID")
            self.assertNotEqual(p.fingerprint(), q.fingerprint())

    def test_fingerprint_domain_separation(self):
        p = fixture()
        self.assertEqual(p.DOMAIN, "apexforge.cross-domain-orchestration/v1")
        self.assertNotIn(p.fingerprint(), {p.catalog.fingerprint(), p.nodes[0].descriptor.fingerprint(),
            p.nodes[0].registration.fingerprint(), p.nodes[0].descriptor.implementation.content.fingerprint})

    def test_provenance_chain_retained(self):
        p = fixture()
        record = p.record()
        self.assertEqual(record["catalog"], p.catalog.fingerprint())
        self.assertEqual(record["policy"], p.catalog.policy.fingerprint())
        self.assertEqual(record["nodes"][0]["registration"], p.nodes[0].registration.candidate.fingerprint())
        self.assertEqual(record["nodes"][0]["decision"], p.nodes[0].registration.fingerprint())
        self.assertEqual(record["nodes"][0]["implementation"], p.nodes[0].descriptor.implementation.record())
        self.assertEqual(p.handoffs[0].producer.node, p.nodes[0].identifier)
        self.assertEqual(record["handoffs"][0]["provenance"], [REFERENCE.record()])
        self.assertEqual(record["provenance"], [REFERENCE.record()])

    def test_valid_plan_grants_no_trust_or_success(self):
        p = fixture()
        v = orch.OrchestrationValidation(p)
        for record in (p.record(), v.record()):
            self.assertFalse(record["grants_authority"])
            self.assertFalse(record["grants_trust"])
        self.assertEqual(p.record()["execution"], "NOT_PERFORMED")
        self.assertFalse(v.record()["execution_evidence"])
        self.assertFalse(hasattr(v, "outputs"))
        self.assertFalse(hasattr(v, "run"))

    def test_all_domain_pipelines_passive(self):
        for kinds in (("parametric", "fabrication"), ("narrative", "agent"),
            ("agent", "external-adapter"), ("motion", "agent"),
            ("parametric", "fabrication", "external-adapter")):
            with self.subTest(pipeline=kinds):
                p = fixture(kinds)
                before = tuple(n.descriptor.fingerprint() for n in p.nodes)
                self.assertEqual(orch.OrchestrationValidation(p).status, "VALID")
                self.assertEqual(before, tuple(n.descriptor.fingerprint() for n in p.nodes))
                for e in p.handoffs:
                    producer = next(n for n in p.nodes if n.identifier == e.producer.node)
                    self.assertIn(producer.descriptor.identity.kind, kinds)
                    self.assertEqual(e.record()["origin"], "PRODUCER_DOMAIN_RETAINED")

    def test_validation_does_not_reimplement_governance_or_produce_artifacts(self):
        p = fixture()
        with patch.object(gov, "evaluate", side_effect=AssertionError("governance re-evaluated")), \
             patch.object(gov, "register", side_effect=AssertionError("registration mutated")), \
             patch.object(sdk.DomainArtifact, "from_bytes", side_effect=AssertionError("output fabricated")):
            self.assertEqual(orch.OrchestrationValidation(p).status, "VALID")
            p.fingerprint()

    def test_diagnostics_deterministic_and_invalid_dominates_missing(self):
        p = fixture()
        n = replace(p.nodes[0], operation="unknown.operation")
        p = replace(p, nodes=(n,p.nodes[1]), handoffs=())
        q = replace(p, nodes=p.nodes[::-1])
        a,b = orch.OrchestrationValidation(p), orch.OrchestrationValidation(q)
        self.assertEqual(a.status, "INVALID")
        self.assertEqual(a.record(), b.record())
        self.assertEqual({f.code for f in a.findings}, {"ORCHESTRATION_INPUT_MISSING", "ORCHESTRATION_OPERATION_UNDECLARED"})

    def test_long_valid_names_diagnostic_slots_separate(self):
        p = fixture(("agent",))
        n = replace(p.nodes[0], identifier="n"*128, inputs=(orch.InputSlot("s"*128,p.nodes[0].outputs[0].contract),))
        v = orch.OrchestrationValidation(replace(p,nodes=(n,),terminal_outputs=()))
        self.assertEqual(v.status,"INCOMPLETE")
        self.assertEqual(v.findings[0].slot,"s"*128)

    def test_thousand_node_iterative_determinism(self):
        p = fixture(("agent",))
        base = p.nodes[0]
        c = base.outputs[0].contract
        nodes = tuple(replace(base, identifier="n-"+str(i).zfill(4),
            inputs=() if i == 0 else (orch.InputSlot("input",c),)) for i in range(1000))
        edges = tuple(orch.ArtifactHandoff("e-"+str(i).zfill(4), orch.SlotReference(nodes[i].identifier,"output"),
            orch.SlotReference(nodes[i+1].identifier,"input"),c) for i in range(999))
        p = replace(p,nodes=nodes,handoffs=edges,terminal_outputs=(orch.SlotReference(nodes[-1].identifier,"output"),))
        q = replace(p,nodes=nodes[::-1],handoffs=edges[::-1])
        self.assertEqual(orch.OrchestrationValidation(p).topological_order,tuple(n.identifier for n in nodes))
        self.assertEqual(orch.OrchestrationValidation(q).status,"VALID")
        self.assertEqual(p.fingerprint(),q.fingerprint())

    def test_graph_bounds(self):
        p = fixture()
        self.error("ORCHESTRATION_DUPLICATE_NODE",lambda:replace(p,nodes=(p.nodes[0],)*(orch.MAX_ITEMS+1)))

    def test_static_security_audit(self):
        source = Path(orch.__file__).read_text(encoding="utf-8")
        tree = ast.parse(source)
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(a.name for a in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.add(node.module)
        self.assertEqual(imports,{"dataclasses","heapq","tooling","tooling.package_manifest"})
        tooling_imports = {a.name for n in ast.walk(tree) if isinstance(n,ast.ImportFrom) and n.module == "tooling" for a in n.names}
        self.assertEqual(tooling_imports,{"domain_platform","domain_governance"})
        calls = {n.func.id for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name)}
        self.assertFalse(calls & {"open","eval","exec","compile","__import__","getattr","setattr","input"})
        attributes = {n.attr for n in ast.walk(tree) if isinstance(n,ast.Attribute)}
        self.assertFalse(attributes & {"execute","run","simulate","dispatch","from_bytes","evaluate","register",
            "connect","send","load","loads","read_text","read_bytes","glob","rglob","lookup"})
        self.assertFalse(any(isinstance(n,(ast.AsyncFunctionDef,ast.Await,ast.AsyncFor)) for n in ast.walk(tree)))
        model_fields = {f.name for cls in (orch.CrossDomainOrchestrationPlan,orch.OrchestrationNode,orch.ArtifactHandoff)
            for f in fields(cls)}
        self.assertFalse(model_fields & {"condition","predicate","retry","worker","callback","runtime_state"})


if __name__ == "__main__":
    unittest.main()
