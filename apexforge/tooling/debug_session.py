"""P13.2 session/control values and owner boundary; never executes AIR.

AuthorityEngine owns permission evaluation. Acceptance queues one request; only
explicit delivery to the designated execution-control owner consumes it. No
runtime/native control implementation, persistence, transport, or semantic view.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
from hashlib import sha256
import json
import re
from typing import Protocol

from authority.engine import AuthorityEngine
from authority.model import AuthorityCheck, AuthorityGrant, Principal
from tooling.resource_observability import (
    EvidenceStatus, OwnershipEvidence, ResourceClass, ResourceOwnership,
)

PROTOCOL = "apexforge.debug.protocol/v1"
SCHEMA = "apexforge.debug-session/v1"


class SessionError(ValueError):
    """Stable debugger-domain lifecycle, shape, or ownership failure."""
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def _require(condition, code):
    if not condition:
        raise SessionError(code)


def _text(value):
    _require(type(value) is str and re.fullmatch(r"[A-Za-z0-9_.:/-]+", value) is not None,
             "invalid_reference")
    _require(not value.startswith("/") and ".." not in value and "\\" not in value,
             "invalid_reference")


def _hash(value):
    _require(type(value) is str and re.fullmatch(r"[0-9A-F]{64}", value) is not None,
             "invalid_fingerprint")


def _number(value):
    _require(type(value) is int and value >= 0, "invalid_sequence")


def _canonical(kind, values):
    return json.dumps((SCHEMA, kind, values), ensure_ascii=True,
                      separators=(",", ":"), allow_nan=False)


def _fingerprint(form):
    return sha256(form.encode("utf-8")).hexdigest().upper()


class Capability(Enum):
    ATTACH = "debug.attach"
    OBSERVE = "debug.observe"
    REQUEST_STOP = "debug.request_stop"
    REQUEST_CONTINUE = "debug.request_continue"
    REQUEST_TERMINATE = "debug.request_terminate"


CONTROL_CAPABILITIES = (Capability.REQUEST_STOP, Capability.REQUEST_CONTINUE,
                        Capability.REQUEST_TERMINATE)


def _capabilities(values):
    _require(type(values) is tuple and all(type(v) is Capability for v in values),
             "invalid_capabilities")
    _require(len(set(values)) == len(values), "duplicate_capability")
    return tuple(sorted(values, key=lambda v: v.value))


@dataclass(frozen=True)
class SessionReference:
    session_id: str
    principal_id: str
    creation_sequence: int = 0
    protocol: str = PROTOCOL

    def __post_init__(self):
        _text(self.session_id)
        _text(self.principal_id)
        _number(self.creation_sequence)
        _require(self.protocol == PROTOCOL, "protocol_incompatibility")

    def canonical_form(self):
        # Content-addressed LOCAL reference, never canonical semantic identity.
        return _canonical("session-reference", (self.protocol, self.session_id,
                          self.principal_id, self.creation_sequence))

    def fingerprint(self):
        return _fingerprint(self.canonical_form())


@dataclass(frozen=True)
class ExecutionReference:
    execution_id: str
    air_fingerprint: str
    routing_fingerprint: str
    entry_directive: str
    profile: str
    provenance_fingerprint: str = ""

    def __post_init__(self):
        for v in (self.execution_id, self.entry_directive, self.profile):
            _text(v)
        _hash(self.air_fingerprint)
        _hash(self.routing_fingerprint)
        if self.provenance_fingerprint:
            _hash(self.provenance_fingerprint)
        else:
            _require(type(self.provenance_fingerprint) is str, "invalid_fingerprint")

    def semantic_form(self):
        return _canonical("execution-binding", (self.air_fingerprint,
                          self.routing_fingerprint, self.entry_directive,
                          self.profile, self.provenance_fingerprint))

    def canonical_form(self):
        return _canonical("execution-reference", (self.execution_id, self.semantic_form()))

    def fingerprint(self):
        return _fingerprint(self.canonical_form())

    @property
    def authorization_scope(self):
        return "debug.execution:" + self.fingerprint()


class Lifecycle(Enum):
    CREATED = "created"
    ATTACHED = "attached"
    ACTIVE = "active"
    CLOSING = "closing"
    CLOSED = "closed"


@dataclass(frozen=True)
class DebugSession:
    reference: SessionReference
    requested: tuple[Capability, ...]
    granted: tuple[Capability, ...]
    ownership: ResourceOwnership
    state: Lifecycle = Lifecycle.CREATED
    execution: ExecutionReference | None = None
    revision: int = 0

    def __post_init__(self):
        _require(type(self.reference) is SessionReference and type(self.state) is Lifecycle,
                 "invalid_session")
        object.__setattr__(self, "requested", _capabilities(self.requested))
        object.__setattr__(self, "granted", _capabilities(self.granted))
        _require(set(self.granted) <= set(self.requested), "unrequested_capability")
        _number(self.revision)
        _require(self.execution is None or type(self.execution) is ExecutionReference,
                 "invalid_execution")
        _require(self.state is not Lifecycle.CREATED or self.execution is None,
                 "invalid_lifecycle")
        _require(self.state not in (Lifecycle.ATTACHED, Lifecycle.ACTIVE) or self.execution is not None,
                 "invalid_lifecycle")
        _require(type(self.ownership) is ResourceOwnership, "invalid_custody")
        _require(self.ownership.owner == OwnershipEvidence(EvidenceStatus.KNOWN,
                 self.reference.principal_id + "/" + self.reference.fingerprint()), "custody_mismatch")
        _require(self.ownership.resource_class is ResourceClass.DHF and all(
            v.status is EvidenceStatus.KNOWN for v in (
                self.ownership.purpose, self.ownership.trigger,
                self.ownership.intended_lifetime, self.ownership.cleanup_boundary)), "invalid_custody")

    def canonical_form(self):
        return _canonical("session", (self.reference.canonical_form(),
            tuple(v.value for v in self.requested), tuple(v.value for v in self.granted),
            self.state.value, None if self.execution is None else self.execution.canonical_form(),
            self.revision, self.ownership.canonical_record()))


@dataclass(frozen=True)
class ControlRequest:
    session: SessionReference
    execution: ExecutionReference
    action: Capability
    sequence: int
    expected_revision: int
    authorization_binding: str
    expected_state: Lifecycle = Lifecycle.ACTIVE
    timestamp: str | None = None

    def __post_init__(self):
        _require(type(self.session) is SessionReference and type(self.execution) is ExecutionReference,
                 "invalid_request")
        _require(type(self.action) is Capability and self.action in CONTROL_CAPABILITIES,
                 "unsupported_control")
        _require(type(self.expected_state) is Lifecycle, "invalid_lifecycle")
        _number(self.sequence)
        _number(self.expected_revision)
        _hash(self.authorization_binding)
        _require(self.timestamp is None or type(self.timestamp) is str, "invalid_timestamp")

    def canonical_form(self):
        return _canonical("control-request", (self.session.canonical_form(),
            self.execution.canonical_form(), self.action.value, self.sequence,
            self.expected_state.value, self.expected_revision, self.authorization_binding))

    def fingerprint(self):
        return _fingerprint(self.canonical_form())


class Disposition(Enum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    UNSUPPORTED = "unsupported"
    STALE = "stale"
    SESSION_CLOSED = "session_closed"
    EXECUTION_MISMATCH = "execution_mismatch"
    AUTHORIZATION_DENIED = "authorization_denied"


@dataclass(frozen=True)
class ControlDisposition:
    request_fingerprint: str
    status: Disposition
    reason: str

    def __post_init__(self):
        _hash(self.request_fingerprint)
        _require(type(self.status) is Disposition, "invalid_disposition")
        _text(self.reason)

    def canonical_form(self):
        return _canonical("control-disposition", (self.request_fingerprint,
                          self.status.value, self.reason))


@dataclass(frozen=True)
class StopObservation:
    execution: ExecutionReference
    control_owner_id: str
    sequence: int
    evidence_reference: str
    reason: str = "requested"

    def __post_init__(self):
        _require(type(self.execution) is ExecutionReference, "invalid_execution")
        _text(self.control_owner_id)
        _number(self.sequence)
        _text(self.evidence_reference)
        # Generic evidence reasons only; no breakpoint or stepping interpretation.
        _require(self.reason in ("requested", "diagnostic", "boundary", "execution_complete"),
                 "unsupported_stop_reason")

    def canonical_form(self):
        return _canonical("stop-observation", (self.execution.canonical_form(),
            self.control_owner_id, self.sequence, self.evidence_reference, self.reason))


@dataclass(frozen=True)
class SessionEvent:
    session: SessionReference
    sequence: int
    event_kind: str
    execution: ExecutionReference | None
    record_form: str
    protocol: str = PROTOCOL

    def __post_init__(self):
        _require(type(self.session) is SessionReference and self.protocol == PROTOCOL,
                 "protocol_incompatibility")
        _number(self.sequence)
        _require(self.event_kind in (
            "debug.session.start", "debug.session.attach", "debug.session.activate",
            "debug.session.closing", "debug.session.finish", "debug.control.request",
            "debug.control.accept", "debug.control.reject", "debug.control.deliver",
            "debug.stop.observe"), "unsupported_event")
        _require(self.execution is None or type(self.execution) is ExecutionReference,
                 "invalid_execution")
        _require(type(self.record_form) is str, "invalid_event_record")

    def canonical_form(self):
        return _canonical("session-event", (self.protocol, self.session.canonical_form(),
            self.sequence, self.event_kind,
            None if self.execution is None else self.execution.canonical_form(), self.record_form))


class ExecutionControlOwner(Protocol):
    """Trusted caller-designated owner. No production implementation in P13.2.

    consume is a handoff, not proof of stop/resume/termination. Optional returned
    stop evidence is separately validated. Owner exceptions propagate unchanged;
    consumed requests are never automatically retried.
    """
    owner_id: str
    execution: ExecutionReference
    supported: tuple[Capability, ...]

    def consume(self, request: ControlRequest) -> StopObservation | None:
        ...


class DebugSessionOwner:
    """One explicit mutable manager over immutable values; trusted in-process API.

    Session/execution IDs must be uniquely allocated by the embedding owner.
    Values/fingerprints are bindings, not bearer tokens or authentication.
    Serial use only; transport authentication and concurrency are deferred.
    """
    def __init__(self, reference, requested, granted, authority, execution, control_owner):
        _require(type(reference) is SessionReference and type(execution) is ExecutionReference,
                 "invalid_reference")
        _require(type(authority) is AuthorityEngine and all(type(g) is AuthorityGrant and
            all(type(v) is str for v in (g.principal, g.capability, g.resource))
            for g in authority.grants), "unsupported_authority_owner")
        _text(control_owner.owner_id)
        _require(control_owner.execution == execution, "control_owner_mismatch")
        supported = _capabilities(control_owner.supported)
        _require(set(supported) <= set(CONTROL_CAPABILITIES), "unsupported_control")
        self._authority = authority
        self._execution = execution
        self._control_owner = control_owner
        self._control_owner_id = control_owner.owner_id
        self._supported = supported
        known = lambda value: OwnershipEvidence(EvidenceStatus.KNOWN, value)
        ownership = ResourceOwnership("debug.session", ResourceClass.DHF,
            known(reference.principal_id + "/" + reference.fingerprint()),
            known("session lifecycle and one pending control binding"),
            known("explicit session creation"), known("manager until close; snapshots caller-owned"),
            known("close clears pending request; caller releases returned evidence"))
        self._session = DebugSession(reference, requested, granted, ownership)
        self._request_sequence = -1
        self._stop_sequence = -1
        self._event_sequence = 0
        self._pending = None

    @classmethod
    def create(cls, session_id, principal, requested, granted, authority, execution,
               control_owner, *, creation_sequence=0):
        _require(type(principal) is Principal, "invalid_principal")
        return cls(SessionReference(session_id, principal.id, creation_sequence),
                   requested, granted, authority, execution, control_owner)

    @property
    def session(self):
        return self._session

    @property
    def authorization_binding(self):
        return _fingerprint(_canonical("authorization-binding", (
            self.session.reference.canonical_form(), self._execution.authorization_scope,
            tuple((g.principal, g.capability, g.resource) for g in self._authority.grants))))

    def _allowed(self, capability):
        return self._authority.allows(AuthorityCheck(
            "debug-check:" + self.session.reference.fingerprint(),
            self.session.reference.principal_id, capability.value,
            self._execution.authorization_scope))

    def _event(self, kind, form):
        event = SessionEvent(self.session.reference, self._event_sequence, kind,
                             self.session.execution, form)
        self._event_sequence += 1
        return event

    def start_event(self):
        _require(self._event_sequence == 0 and self.session.state is Lifecycle.CREATED,
                 "invalid_lifecycle")
        return self._event("debug.session.start", self.session.canonical_form())

    def _transition(self, state):
        self._session = replace(self.session, state=state, revision=self.session.revision + 1)

    def attach(self, execution):
        _require(self.session.state is Lifecycle.CREATED, "invalid_lifecycle")
        _require(type(execution) is ExecutionReference and execution == self._execution,
                 "execution_mismatch")
        _require(Capability.ATTACH in self.session.granted, "capability_not_granted")
        _require(self._allowed(Capability.ATTACH), "authorization_denied")
        self._session = replace(self.session, state=Lifecycle.ATTACHED,
                                execution=execution, revision=self.session.revision + 1)
        return self._event("debug.session.attach", self.session.canonical_form())

    def activate(self):
        _require(self.session.state is Lifecycle.ATTACHED, "invalid_lifecycle")
        _require(Capability.OBSERVE in self.session.granted, "capability_not_granted")
        _require(self._allowed(Capability.OBSERVE), "authorization_denied")
        self._transition(Lifecycle.ACTIVE)
        return self._event("debug.session.activate", self.session.canonical_form())

    def begin_close(self):
        _require(self.session.state in (Lifecycle.CREATED, Lifecycle.ATTACHED, Lifecycle.ACTIVE),
                 "invalid_lifecycle")
        self._pending = None
        self._transition(Lifecycle.CLOSING)
        return self._event("debug.session.closing", self.session.canonical_form())

    def finish_close(self):
        _require(self.session.state is Lifecycle.CLOSING, "invalid_lifecycle")
        self._transition(Lifecycle.CLOSED)
        return self._event("debug.session.finish", self.session.canonical_form())

    def _validate(self, request):
        if request.session != self.session.reference:
            return Disposition.REJECTED, "session_mismatch"
        if self.session.state in (Lifecycle.CLOSING, Lifecycle.CLOSED):
            return Disposition.SESSION_CLOSED, "session_closed"
        if request.execution != self._execution:
            return Disposition.EXECUTION_MISMATCH, "execution_mismatch"
        if request.sequence <= self._request_sequence:
            return Disposition.STALE, ("duplicate_sequence" if request.sequence == self._request_sequence
                                      else "stale_sequence")
        if (request.expected_state is not self.session.state or
                self.session.state is not Lifecycle.ACTIVE or
                request.expected_revision != self.session.revision):
            return Disposition.STALE, "stale_lifecycle"
        if request.authorization_binding != self.authorization_binding:
            return Disposition.AUTHORIZATION_DENIED, "authorization_binding_mismatch"
        if request.action not in self.session.granted:
            return Disposition.REJECTED, "capability_not_granted"
        if not self._allowed(request.action):
            return Disposition.AUTHORIZATION_DENIED, "authorization_denied"
        if request.action not in self._supported:
            return Disposition.UNSUPPORTED, "unsupported_capability"
        if self._pending is not None:
            return Disposition.REJECTED, "control_pending"
        return Disposition.ACCEPTED, "validated_for_owner_delivery"

    def submit(self, request):
        _require(type(request) is ControlRequest, "invalid_request")
        status, reason = self._validate(request)
        # Matching ACTIVE-scope attempts consume fresh sequence numbers even if
        # denied. Foreign/malformed/stale requests cannot poison this high-water mark.
        if (request.session == self.session.reference and request.execution == self._execution
                and self.session.state is Lifecycle.ACTIVE
                and request.expected_revision == self.session.revision
                and request.expected_state is Lifecycle.ACTIVE
                and request.sequence > self._request_sequence):
            self._request_sequence = request.sequence
        disposition = ControlDisposition(request.fingerprint(), status, reason)
        if status is Disposition.ACCEPTED:
            self._pending = request
        events = (self._event("debug.control.request", request.canonical_form()),
                  self._event("debug.control.accept" if status is Disposition.ACCEPTED
                              else "debug.control.reject", disposition.canonical_form()))
        return disposition, events

    def deliver(self, request):
        """Explicit owner handoff; never triggered by acceptance construction."""
        _require(type(request) is ControlRequest and self._pending == request,
                 "request_not_pending")
        _require(self.session.state is Lifecycle.ACTIVE, "session_closed")
        _require(request.session == self.session.reference and request.execution == self._execution,
                 "execution_mismatch")
        _require(request.authorization_binding == self.authorization_binding and
                 self._allowed(request.action), "authorization_denied")
        _require(self._control_owner.owner_id == self._control_owner_id and
                 self._control_owner.execution == self._execution and
                 request.action in self._control_owner.supported, "control_owner_mismatch")
        self._pending = None  # consume before callback; no retry after owner failure
        observation = self._control_owner.consume(request)
        events = [self._event("debug.control.deliver", request.canonical_form())]
        if observation is not None:
            _require(type(observation) is StopObservation and
                     observation.execution == self._execution and
                     observation.control_owner_id == self._control_owner_id,
                     "stop_owner_mismatch")
            _require(observation.sequence > self._stop_sequence, "stale_stop_observation")
            self._stop_sequence = observation.sequence
            events.append(self._event("debug.stop.observe", observation.canonical_form()))
        return tuple(events)
