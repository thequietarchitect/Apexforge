"""Passive narrative-domain evidence and frozen P11 coexistence."""
import ast
from dataclasses import FrozenInstanceError, replace
from pathlib import Path
import unittest

from language import narrative_model as model
from language.narrative_graph import build_narrative_semantic_graph
from tooling import narrative_domain as domain
from tooling import domain_interchange as interchange
from tooling import domain_platform as sdk
import p15_3_apexmotion_domain_contract_test as package_fixture


def identity(kind, name):
    return model.NarrativeIdentity(kind, ("example", name))


def fixture():
    character = model.NarrativeCharacter(identity("character", "alice"))
    scenes = tuple(model.NarrativeScene(identity("scene", name)) for name in ("start", "end"))
    choice = model.NarrativeChoice(identity("choice", "route"), scenes[0].identity,
        (model.NarrativeChoicePath("stay", scenes[0].identity), model.NarrativeChoicePath("leave", scenes[1].identity)))
    state = model.NarrativeState(identity("narrative_state", "initial"),
        (model.NarrativeStateFact(character.identity, "role", "observer"),))
    story = model.NarrativeStory(identity("story", "world"), (character,), scenes, (), (choice,),
        (model.NarrativePerspective(identity("perspective", "view"), character.identity),),
        (model.NarrativeTimeline(identity("timeline", "order"), tuple(s.identity for s in scenes)),), (state,), ())
    events = tuple(domain.NarrativeEvent(name, scenes[n].identity, (character.identity,), n)
        for n, name in enumerate(("arrival", "departure")))
    snapshot = domain.NarrativeSnapshot(story, events,
        (domain.NarrativeCausalRelation("arrival", "departure"),))
    manifest = package_fixture.fixture()[0]
    return snapshot, domain.narrative_platform(manifest)


class NarrativeTests(unittest.TestCase):
    def rejected(self, code, fn):
        with self.assertRaises(domain.NarrativeDomainError) as context:
            fn()
        self.assertEqual(context.exception.code, code)

    def test_platform_and_package(self):
        _, platform = fixture()
        self.assertEqual(platform.identity, sdk.DomainPlatformIdentity("apexforge.narrative", "narrative"))
        self.assertEqual(platform.implementation, sdk.ImplementationPackage.from_manifest(package_fixture.fixture()[0]))

    def test_frozen_identities_reused(self):
        snapshot, _ = fixture()
        self.assertIs(type(snapshot.story.characters[0].identity), model.NarrativeIdentity)
        self.assertEqual(snapshot.story.characters[0].identity.kind, "character")
        self.assertNotEqual(snapshot.story.identity.kind, "narrative_state")

    def test_models_immutable(self):
        snapshot, _ = fixture()
        for obj, field in ((snapshot, "events"), (snapshot.events[0], "ordinal"), (snapshot.story.scenes[0], "body"),
            (snapshot.story.choices[0], "paths"), (snapshot.story.characters[0], "identity")):
            with self.assertRaises(FrozenInstanceError):
                setattr(obj, field, None)

    def test_frozen_order_preserved(self):
        snapshot, _ = fixture()
        record = snapshot.record()
        self.assertEqual(record["story"]["scenes"], domain.frozen_record(snapshot.story.scenes))
        graph = build_narrative_semantic_graph(snapshot.story)
        self.assertEqual([n["identity"] for n in record["frozen_graph"]["nodes"]],
            [domain.frozen_record(n.identity) for n in graph.nodes])

    def test_event_permutation(self):
        snapshot, _ = fixture()
        other = replace(snapshot, events=tuple(reversed(snapshot.events)))
        self.assertEqual(snapshot.fingerprint(), other.fingerprint())
        self.assertEqual([e.ordinal for e in other.events], [0, 1])

    def test_event_order_invalid(self):
        snapshot, _ = fixture()
        for ordinal in (-1, True, 2 ** 63):
            self.rejected("NARRATIVE_EVENT_ORDER_INVALID", lambda: replace(snapshot.events[0], ordinal=ordinal))

    def test_event_duplicate(self):
        snapshot, _ = fixture()
        self.rejected("NARRATIVE_EVENT_DUPLICATE", lambda: replace(snapshot, events=(snapshot.events[0],) * 2))

    def test_event_duplicate_order(self):
        snapshot, _ = fixture()
        self.rejected("NARRATIVE_EVENT_ORDER_DUPLICATE", lambda: replace(snapshot,
            events=(snapshot.events[0], replace(snapshot.events[1], ordinal=0))))

    def test_conflicting_node(self):
        snapshot, _ = fixture()
        story = replace(snapshot.story, scenes=(snapshot.story.scenes[0], replace(snapshot.story.scenes[0], body="conflict")))
        self.rejected("NARRATIVE_NODE_DUPLICATE", lambda: replace(snapshot, story=story))

    def test_dangling_frozen_reference(self):
        snapshot, _ = fixture()
        self.rejected("NARRATIVE_REFERENCE_MISSING", lambda: replace(snapshot,
            story=replace(snapshot.story, characters=())))

    def test_dangling_event(self):
        snapshot, _ = fixture()
        self.rejected("NARRATIVE_EVENT_REFERENCE_MISSING", lambda: replace(snapshot,
            events=(replace(snapshot.events[0], scene=identity("scene", "absent")),)))

    def test_dangling_causal_edge(self):
        snapshot, _ = fixture()
        self.rejected("NARRATIVE_EDGE_REFERENCE_MISSING", lambda: replace(snapshot,
            causal_relations=(domain.NarrativeCausalRelation("arrival", "missing"),)))

    def test_conflicting_edge(self):
        snapshot, _ = fixture()
        self.rejected("NARRATIVE_EDGE_DUPLICATE", lambda: replace(snapshot,
            causal_relations=snapshot.causal_relations * 2))

    def test_causal_cycle_is_representational(self):
        snapshot, _ = fixture()
        links = snapshot.causal_relations + (domain.NarrativeCausalRelation("departure", "arrival"),)
        a, b = replace(snapshot, causal_relations=links), replace(snapshot, causal_relations=tuple(reversed(links)))
        self.assertEqual(a.fingerprint(), b.fingerprint())
        self.assertTrue(all(not c.record()["external_causation_verified"] for c in a.causal_relations))

    def test_choice_alternatives_preserved(self):
        snapshot, _ = fixture()
        self.assertEqual([p["label"] for p in snapshot.record()["story"]["choices"][0]["paths"]], ["stay", "leave"])

    def test_duplicate_choice_alternative(self):
        snapshot, _ = fixture()
        choice = snapshot.story.choices[0]
        self.rejected("NARRATIVE_CHOICE_ALTERNATIVE_DUPLICATE", lambda: replace(snapshot,
            story=replace(snapshot.story, choices=(replace(choice, paths=choice.paths * 2),))))

    def test_branch_lineage(self):
        snapshot, _ = fixture()
        before = snapshot.canonical_json()
        branch = domain.NarrativeBranch("branch-one", snapshot, snapshot.story.choices[0].identity, 1,
            snapshot.story.states[0].identity)
        self.assertEqual(branch.record()["parent_fingerprint"], snapshot.fingerprint())
        self.assertEqual(branch.record()["alternative"]["label"], "leave")
        self.assertEqual(branch.record()["selection_origin"], "CALLER_SUPPLIED")
        self.assertEqual(snapshot.canonical_json(), before)
        with self.assertRaises(FrozenInstanceError):
            branch.alternative_index = 0

    def test_missing_branch_choice(self):
        snapshot, _ = fixture()
        self.rejected("NARRATIVE_BRANCH_CHOICE_MISSING", lambda: domain.NarrativeBranch("branch", snapshot,
            identity("choice", "absent"), 0, snapshot.story.states[0].identity))

    def test_missing_branch_alternative(self):
        snapshot, _ = fixture()
        self.rejected("NARRATIVE_BRANCH_ALTERNATIVE_MISSING", lambda: domain.NarrativeBranch("branch", snapshot,
            snapshot.story.choices[0].identity, 2, snapshot.story.states[0].identity))

    def test_perspective_and_fact_boundaries(self):
        snapshot, _ = fixture()
        self.assertEqual(snapshot.story.perspectives[0].viewpoint, snapshot.story.characters[0].identity)
        self.assertFalse(snapshot.record()["external_fact_verified"])
        self.assertFalse(snapshot.record()["grants_authority"])
        self.assertEqual(snapshot.record()["semantic_authority"], "CANONICAL_AIR")
        self.assertEqual(snapshot.events[0].record()["execution"], "NOT_PERFORMED")

    def test_provenance(self):
        snapshot, _ = fixture()
        refs = package_fixture.fixture()[2].provenance
        snapshot = replace(snapshot, provenance=refs)
        self.assertEqual(snapshot.record()["provenance"], [p.record() for p in refs])

    def test_artifact_request_result_interchange(self):
        snapshot, platform = fixture()
        artifact = domain.narrative_artifact(platform, snapshot)
        self.assertEqual(artifact.platform, platform.identity)
        self.assertEqual(artifact.implementation, platform.implementation)
        artifact.verify_bytes(snapshot.canonical_json().encode("utf-8"))
        request = sdk.DomainRequest(platform, artifact.operation, artifacts=(artifact,))
        result = sdk.DomainResult(request, "COMPLETE", outputs=(artifact,))
        self.assertEqual(interchange.parse_document(interchange.serialize_document(result)).document, result)

    def test_wrong_platform(self):
        snapshot, _ = fixture()
        self.rejected("NARRATIVE_PLATFORM_BINDING_INVALID", lambda: domain.narrative_artifact(package_fixture.fixture()[1], snapshot))

    def test_independent_construction(self):
        self.assertEqual(fixture()[0].canonical_json(), fixture()[0].canonical_json())
        snapshot, _ = fixture()
        self.assertNotEqual(snapshot.fingerprint(), snapshot.events[0].fingerprint())

    def test_authored_prose_preserved(self):
        snapshot, _ = fixture()
        scene = replace(snapshot.story.scenes[0], title="  Fiction  ", body="line one\nline two")
        snapshot = replace(snapshot, story=replace(snapshot.story, scenes=(scene, snapshot.story.scenes[1])))
        self.assertEqual(snapshot.record()["story"]["scenes"][0]["title"], "  Fiction  ")
        self.assertEqual(snapshot.record()["story"]["scenes"][0]["body"], "line one\nline two")

    def test_missing_branch_state(self):
        snapshot, _ = fixture()
        self.rejected("NARRATIVE_BRANCH_STATE_MISSING", lambda: domain.NarrativeBranch("branch", snapshot,
            snapshot.story.choices[0].identity, 0, identity("narrative_state", "absent")))

    def test_duplicate_state_fact(self):
        snapshot, _ = fixture()
        state = snapshot.story.states[0]
        self.rejected("NARRATIVE_STATE_FACT_DUPLICATE", lambda: replace(snapshot,
            story=replace(snapshot.story, states=(replace(state, facts=state.facts * 2),))))

    def test_large_iterative_graph(self):
        snapshot, _ = fixture()
        events = tuple(domain.NarrativeEvent("event-" + str(i), snapshot.story.scenes[0].identity, (), i)
            for i in range(1000))
        a = replace(snapshot, events=events, causal_relations=())
        b = replace(snapshot, events=tuple(reversed(events)), causal_relations=())
        self.assertEqual(a.fingerprint(), b.fingerprint())
        self.assertEqual(len(a.record()["events"]), 1000)

    def test_security_static(self):
        tree = ast.parse(Path(domain.__file__).read_text(encoding="utf-8"))
        imports = {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
        self.assertEqual(imports, {"dataclasses", "language", "language.narrative_graph", "tooling", "tooling.package_manifest"})
        forbidden = {"eval", "exec", "__import__", "open", "compile", "RuntimeEngine", "AuthorityEngine"}
        calls = {n.func.id for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
        self.assertFalse(calls & forbidden)


if __name__ == "__main__":
    unittest.main()
