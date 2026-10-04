"""Controlled P13.2 ownership/security fixtures; no external process control."""
from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, replace
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from authority.engine import AuthorityEngine
from authority.model import AuthorityGrant, Principal
from tooling.debug_session import (
    Capability as C, ControlRequest, ControlDisposition, DebugSessionOwner,
    Disposition as D, ExecutionReference, Lifecycle as L, SessionError,
    SessionReference, StopObservation, PROTOCOL,
)
from tooling.resource_observability import EvidenceStatus, ResourceClass


class FakeControlOwner:
    def __init__(self, execution, supported=(C.REQUEST_STOP, C.REQUEST_CONTINUE, C.REQUEST_TERMINATE)):
        self.owner_id = "fixture.control-owner"
        self.execution = execution
        self.supported = supported
        self.consumed = []
        self.observation = None
        self.failure = None

    def consume(self, request):
        self.consumed.append(request)
        if self.failure:
            raise self.failure
        return self.observation


def execution(identifier="execution:one"):
    return ExecutionReference(identifier, "A" * 64, "B" * 64,
                              "directive:Main", "canonical.fixture/v1", "C" * 64)


ALL = tuple(C)


def fixture(session_id="session:one", principal="principal:inspector", capabilities=ALL,
            grants=None, target=None, supported=None, active=True):
    target = execution() if target is None else target
    fake = FakeControlOwner(target) if supported is None else FakeControlOwner(target, supported)
    grants = tuple(AuthorityGrant(principal, c.value, target.authorization_scope)
                   for c in ALL) if grants is None else grants
    owner = DebugSessionOwner.create(session_id, Principal(principal), ALL, capabilities,
                                    AuthorityEngine(grants), target, fake)
    if active:
        owner.start_event()
        owner.attach(target)
        owner.activate()
    return owner, fake


def request(owner, sequence=0, action=C.REQUEST_STOP):
    return ControlRequest(owner.session.reference, owner.session.execution, action,
                          sequence, owner.session.revision, owner.authorization_binding)


class FoundationTests(unittest.TestCase):
    def test_deterministic_identity_and_distinct_execution_occurrences(self):
        a, _ = fixture()
        b, _ = fixture()
        self.assertEqual(a.session.canonical_form(), b.session.canonical_form())
        self.assertEqual(a.session.reference.fingerprint(), b.session.reference.fingerprint())
        self.assertNotEqual(a.session.reference.canonical_form(), a.session.execution.canonical_form())
        other = execution("execution:two")
        self.assertEqual(other.semantic_form(), execution().semantic_form())
        self.assertNotEqual(other.authorization_scope, execution().authorization_scope)
        self.assertNotEqual(SessionReference("session:two", a.session.reference.principal_id).fingerprint(),
                            a.session.reference.fingerprint())

    def test_immutable_records_and_capability_order(self):
        a, _ = fixture(active=False)
        b, _ = fixture(capabilities=tuple(reversed(ALL)), active=False)
        self.assertEqual(a.session.canonical_form(), b.session.canonical_form())
        self.assertEqual(tuple(c.value for c in a.session.granted), tuple(sorted(c.value for c in ALL)))
        with self.assertRaises(FrozenInstanceError):
            a.session.state = L.ACTIVE
        with self.assertRaises(SessionError):
            fixture(capabilities=(C.OBSERVE, C.OBSERVE))
        with self.assertRaises(SessionError):
            replace(a.session, granted=("debug.observe",))
        with self.assertRaises(SessionError):
            replace(a.session.reference, protocol="apexforge.debug.protocol/v2")

    def test_valid_lifecycle_and_events(self):
        owner, _ = fixture(active=False)
        events = [owner.start_event(), owner.attach(execution()), owner.activate(),
                  owner.begin_close(), owner.finish_close()]
        self.assertEqual([e.sequence for e in events], list(range(5)))
        self.assertEqual(owner.session.state, L.CLOSED)
        self.assertEqual(owner.session.revision, 4)
        self.assertTrue(all(e.protocol == PROTOCOL for e in events))
        self.assertEqual(events[-1].event_kind, "debug.session.finish")

    def test_illegal_transitions_and_target_changes(self):
        owner, _ = fixture(active=False)
        for transition in (owner.activate, owner.finish_close):
            with self.assertRaises(SessionError):
                transition()
        with self.assertRaises(SessionError):
            owner.attach(execution("execution:other"))
        self.assertEqual(owner.session.state, L.CREATED)
        owner.attach(execution())
        with self.assertRaises(SessionError):
            owner.attach(execution())
        owner.activate()
        with self.assertRaises(SessionError):
            owner.attach(execution("execution:other"))
        owner.begin_close()
        owner.finish_close()
        for transition in (owner.activate, owner.begin_close, owner.finish_close):
            with self.assertRaises(SessionError):
                transition()
        self.assertEqual(owner.session.execution, execution())

    def test_attachment_and_observation_authority_are_independent(self):
        target = execution()
        grants = (AuthorityGrant("principal:inspector", C.ATTACH.value, target.authorization_scope),)
        owner, _ = fixture(grants=grants, active=False)
        owner.attach(target)
        with self.assertRaises(SessionError) as denied:
            owner.activate()
        self.assertEqual(denied.exception.code, "authorization_denied")
        self.assertEqual(owner.session.state, L.ATTACHED)
        owner, _ = fixture(grants=(), active=False)
        with self.assertRaises(SessionError):
            owner.attach(target)

    def test_observer_only_and_missing_control_capability(self):
        owner, fake = fixture(capabilities=(C.ATTACH, C.OBSERVE))
        for c in (C.REQUEST_STOP, C.REQUEST_CONTINUE, C.REQUEST_TERMINATE):
            result, _ = owner.submit(request(owner, list(C).index(c), c))
            self.assertEqual(result.status, D.REJECTED)
            self.assertEqual(result.reason, "capability_not_granted")
        self.assertEqual(fake.consumed, [])

    def test_granted_capability_is_not_authority(self):
        target = execution()
        grants = tuple(AuthorityGrant("principal:inspector", c.value, target.authorization_scope)
                       for c in (C.ATTACH, C.OBSERVE))
        grants += (AuthorityGrant("principal:other", C.REQUEST_STOP.value, target.authorization_scope),)
        owner, fake = fixture(grants=grants)
        result, _ = owner.submit(request(owner))
        self.assertEqual(result.status, D.AUTHORIZATION_DENIED)
        self.assertEqual(fake.consumed, [])

    def test_authority_is_execution_scoped(self):
        target = execution()
        grants = tuple(AuthorityGrant("principal:inspector", c.value, target.authorization_scope)
                       for c in (C.ATTACH, C.OBSERVE))
        grants += (AuthorityGrant("principal:inspector", C.REQUEST_STOP.value,
                                  execution("execution:other").authorization_scope),)
        owner, _ = fixture(grants=grants)
        self.assertEqual(owner.submit(request(owner))[0].status, D.AUTHORIZATION_DENIED)

    def test_wrong_execution_and_principal_binding(self):
        owner, fake = fixture()
        original = request(owner)
        wrong = replace(original, execution=execution("execution:other"))
        self.assertEqual(owner.submit(wrong)[0].status, D.EXECUTION_MISMATCH)
        self.assertEqual(owner.submit(replace(original, authorization_binding="0" * 64))[0].status,
                         D.AUTHORIZATION_DENIED)
        self.assertEqual(fake.consumed, [])

    def test_acceptance_is_not_runtime_mutation_or_stop(self):
        owner, fake = fixture()
        initial_session = owner.session
        pending = request(owner)
        result, events = owner.submit(pending)
        self.assertEqual(result.status, D.ACCEPTED)
        self.assertEqual(owner.session, initial_session)
        self.assertEqual(fake.consumed, [])
        self.assertEqual([e.event_kind for e in events], ["debug.control.request", "debug.control.accept"])
        constructed = ControlDisposition(pending.fingerprint(), D.ACCEPTED, "fixture")
        self.assertEqual(constructed.status, D.ACCEPTED)
        self.assertEqual(fake.consumed, [])
        delivered = owner.deliver(pending)
        self.assertEqual(fake.consumed, [pending])
        self.assertEqual([e.event_kind for e in delivered], ["debug.control.deliver"])
        with self.assertRaises(SessionError):
            owner.deliver(pending)

    def test_duplicates_regression_and_fresh_sequence(self):
        owner, fake = fixture()
        accepted = request(owner, 4)
        self.assertEqual(owner.submit(accepted)[0].status, D.ACCEPTED)
        self.assertEqual(owner.submit(accepted)[0].reason, "duplicate_sequence")
        self.assertEqual(owner.submit(request(owner, 3))[0].reason, "stale_sequence")
        owner.deliver(accepted)
        self.assertEqual(owner.submit(request(owner, 5))[0].status, D.ACCEPTED)
        self.assertEqual(len(fake.consumed), 1)

    def test_pending_is_bounded_and_denied_sequence_not_reused(self):
        owner, _ = fixture()
        owner.submit(request(owner, 0))
        result, _ = owner.submit(request(owner, 1))
        self.assertEqual(result.reason, "control_pending")
        self.assertEqual(owner.submit(request(owner, 1))[0].reason, "duplicate_sequence")

    def test_cross_session_and_foreign_sequence_cannot_poison(self):
        owner, fake = fixture()
        foreign, _ = fixture(session_id="session:other")
        result, _ = owner.submit(request(foreign, 100))
        self.assertEqual(result.reason, "session_mismatch")
        self.assertEqual(owner.submit(request(owner, 0))[0].status, D.ACCEPTED)
        with self.assertRaises(SessionError):
            owner.deliver(request(foreign, 100))
        self.assertEqual(fake.consumed, [])

    def test_closing_and_closed_invalidate_pending_control(self):
        owner, fake = fixture()
        pending = request(owner)
        owner.submit(pending)
        owner.begin_close()
        self.assertEqual(owner.submit(pending)[0].status, D.SESSION_CLOSED)
        with self.assertRaises(SessionError):
            owner.deliver(pending)
        owner.finish_close()
        self.assertEqual(owner.submit(pending)[0].status, D.SESSION_CLOSED)
        self.assertEqual(fake.consumed, [])
        self.assertEqual(owner.session.execution, pending.execution)

    def test_stale_lifecycle_and_unsupported_owner(self):
        owner, _ = fixture()
        r = request(owner)
        for stale in (replace(r, expected_revision=0), replace(r, expected_state=L.ATTACHED)):
            self.assertEqual(owner.submit(stale)[0].reason, "stale_lifecycle")
        owner, fake = fixture(supported=())
        self.assertEqual(owner.submit(request(owner))[0].status, D.UNSUPPORTED)
        self.assertEqual(fake.consumed, [])

    def test_stop_observation_separate_owner_bound_and_ordered(self):
        owner, fake = fixture()
        pending = request(owner)
        fake.observation = StopObservation(execution(), fake.owner_id, 0, "fixture:stop-evidence")
        self.assertNotEqual(pending.canonical_form(), fake.observation.canonical_form())
        owner.submit(pending)
        events = owner.deliver(pending)
        self.assertEqual(events[-1].event_kind, "debug.stop.observe")
        self.assertGreater(events[-1].sequence, events[0].sequence)
        next_request = request(owner, 1)
        owner.submit(next_request)
        with self.assertRaises(SessionError) as stale:
            owner.deliver(next_request)
        self.assertEqual(stale.exception.code, "stale_stop_observation")

    def test_control_owner_substitution_and_false_stop_rejected(self):
        owner, fake = fixture()
        pending = request(owner)
        owner.submit(pending)
        fake.execution = execution("execution:other")
        with self.assertRaises(SessionError):
            owner.deliver(pending)
        self.assertEqual(fake.consumed, [])
        fake.execution = execution()
        fake.observation = StopObservation(execution("execution:other"), fake.owner_id,
                                           0, "fixture:stop-evidence")
        with self.assertRaises(SessionError) as wrong:
            owner.deliver(pending)
        self.assertEqual(wrong.exception.code, "stop_owner_mismatch")
        with self.assertRaises(SessionError):
            owner.deliver(pending)

    def test_owner_failure_is_not_retried_or_converted(self):
        owner, fake = fixture()
        pending = request(owner)
        owner.submit(pending)
        fake.failure = RuntimeError("fixture owner unavailable")
        with self.assertRaises(RuntimeError) as caught:
            owner.deliver(pending)
        self.assertIs(caught.exception, fake.failure)
        with self.assertRaises(SessionError):
            owner.deliver(pending)
        self.assertEqual(len(fake.consumed), 1)

    def test_deterministic_request_disposition_and_volatile_exclusion(self):
        a, _ = fixture()
        b, _ = fixture()
        ra, rb = request(a), replace(request(b), timestamp="different observational time")
        self.assertEqual(ra.canonical_form(), rb.canonical_form())
        self.assertEqual(ra.fingerprint(), rb.fingerprint())
        da, ea = a.submit(ra)
        db, eb = b.submit(rb)
        self.assertEqual(da.canonical_form(), db.canonical_form())
        self.assertEqual(tuple(e.canonical_form() for e in ea), tuple(e.canonical_form() for e in eb))
        self.assertNotEqual(ra.fingerprint(), replace(ra, sequence=1).fingerprint())

    def test_exact_shape_guards_and_resource_custody(self):
        owner, _ = fixture()
        for field, value in (("sequence", True), ("sequence", -1), ("action", C.OBSERVE),
                             ("expected_revision", True), ("authorization_binding", "bad")):
            with self.assertRaises(SessionError):
                replace(request(owner), **{field: value})
        custody = owner.session.ownership
        self.assertEqual(custody.resource_class, ResourceClass.DHF)
        self.assertTrue(all(v.status is EvidenceStatus.KNOWN for v in
                            (custody.owner, custody.purpose, custody.trigger,
                             custody.intended_lifetime, custody.cleanup_boundary)))
        with self.assertRaises(SessionError):
            replace(owner.session, reference=SessionReference("session:other", "principal:inspector"))
        self.assertIn(owner.session.reference.fingerprint(), custody.owner.value)

    def test_static_no_semantic_executor_or_os_control(self):
        tree = ast.parse((ROOT / "apexforge/tooling/debug_session.py").read_text(encoding="utf-8"))
        modules = {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
        modules |= {a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
        self.assertEqual(modules - {"__future__", "dataclasses", "enum", "hashlib", "json", "re", "typing"},
                         {"authority.engine", "authority.model", "tooling.resource_observability"})
        calls = {n.func.attr if isinstance(n.func, ast.Attribute) else n.func.id
                 for n in ast.walk(tree) if isinstance(n, ast.Call)
                 and isinstance(n.func, (ast.Name, ast.Attribute))}
        self.assertFalse(calls & {"execute", "dispatch_native", "run_air_program", "eval", "exec",
                                 "select_path", "_evaluate_assignment", "Popen", "SuspendThread"})


if __name__ == "__main__":
    unittest.main(verbosity=2)
