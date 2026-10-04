"""P13.7 terminal client of supplied P13 observations; no loader or transport."""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from enum import Enum
import json
import shlex
import sys

from tooling.debug_session import (PROTOCOL, Capability, ControlRequest,
    DebugSessionOwner, Lifecycle, SessionError)
from tooling.debug_inspection import (InspectionSnapshot, Availability,
    bind_inspection, InspectionError)
from tooling.debug_correlation import (CorrelationIndex, ObservedPosition,
    KnownObservationOrder, StepMode, plan_next, CorrelationError)
from tooling.debug_evidence import EvidenceKind, EvidenceError
from tooling.debug_replay import (ReplayHistory, ReplayMode, ReplayCursor, build_replay,
    ComparisonDomain, compare_histories, ReplayError, OrderingDomain)

CLIENT_VERSION = "apexforge.debug.cli/v1"
# P10-T1 conventions without importing the frozen CLI's execution adapters.
EXIT_SUCCESS, EXIT_USAGE = 0, 2


class Mode(Enum):
    RETAINED = "retained/offline"
    LIVE = "live-session"


class CLIError(ValueError):
    pass


class Parser(argparse.ArgumentParser):
    def error(self, message):
        # Never echo untrusted command or producer content into diagnostics.
        raise CLIError("malformed_command")


GRAMMAR = {
    "help": (), "status": (), "capabilities": (), "session": (), "inspect": (),
    "state": (), "directive": (), "authority": (), "result": (), "causal": (), "quit": (),
    "correlate": (("reference", {}),),
    "evidence": (("action", {"choices": ("list", "show", "predecessors", "successors")}),
                 ("reference", {"nargs": "?"})),
    "provenance": (("reference", {"nargs": "?"}),),
    "replay": (("action", {"choices": ("first", "previous", "next", "last", "seek")}),
               ("sequence", {"nargs": "?", "type": int})),
    "compare": (("domain", {"choices": ("summary", "state", "trace", "causal", "provenance")}),),
    "plan-step": (("mode", {"choices": ("semantic", "source", "native-correlation")}),),
    "request-stop": (("sequence", {"type": int}),),
    "request-continue": (("sequence", {"type": int}),),
    "request-terminate": (("sequence", {"type": int}),),
}
HELP = """ApexForge debugger CLI v1
help | status | capabilities | session | inspect | state | directive | authority | result
correlate current|<operation-id>
evidence list|show <id>|predecessors <id>|successors <id>
provenance [<id>] | causal
replay first|previous|next|last|seek <sequence>
compare summary|state|trace|causal|provenance
plan-step semantic|source|native-correlation
request-stop|request-continue|request-terminate <request-sequence>
quit
STEP_PLAN_ONLY=True; CONTROL_REQUEST_ACCEPTED != CONTROL_EFFECT_OBSERVED
Replay navigates recorded observations; comparison classifies supplied evidence.
No runtime pause/resume, breakpoint execution, raw machine stepping or live transport.
No DAP, IDE integration, host escape, evidence loader or attribution inference.
"""


def parser():
    value = Parser(prog="apexforge-debug", add_help=False)
    commands = value.add_subparsers(dest="command")
    for name, arguments in GRAMMAR.items():
        command = commands.add_parser(name, add_help=False)
        for key, options in arguments:
            command.add_argument(key, **options)
    return value


def render(rows):
    """Stable labelled terminal text; escape controls and never use producer repr."""
    return "".join(key + "=" + json.dumps(value, ensure_ascii=True, sort_keys=True,
        separators=(",", ":"), allow_nan=False) + "\n" for key, value in rows)


def state_rows(snapshot, *, redacted=False):
    hidden = ("redacted", None, "debugger_visible_state_redacted")
    return (("STATE_CAPTURE", hidden if redacted else snapshot.state.capture.record()),) + tuple(
        ("STATE", (e.key, e.declared_type.record(), hidden if redacted else e.observed_value.record()))
        for e in snapshot.state.entries)


def node_rows(nodes):
    return tuple(("EVIDENCE", (n.node_id, n.reference.kind.value,
        n.reference.producer_identity, n.payload.record())) for n in nodes)


def chain_rows(chain):
    return (("SOURCE", (chain.source.status.value,
        tuple(json.loads(v.canonical_form()) for v in chain.source.values), chain.source.reason)),
        ("AIR", ("available", json.loads(chain.air.canonical_form()))),
        ("GENERATED_NATIVE_REGION", (chain.native.status.value,
        tuple(json.loads(v.canonical_form()) for v in chain.native.values), chain.native.reason)),
        ("MACHINE_ADDRESS", "unsupported"))


@dataclass(frozen=True)
class Response:
    code: int
    stdout: str = ""
    stderr: str = ""
    quit: bool = False


class DebuggerCLI:
    """Serial client; embedding owner supplies authorized models and their lifetime.

    Only the P13 replay cursor and explicit P13.2 submission change local state.
    This application never delivers accepted requests to a control owner.
    """
    def __init__(self, *, mode=Mode.RETAINED, history=None, comparison=None,
                 owner=None, inspection=None, correlation=None, position=None,
                 known_order=None, replay_domain=OrderingDomain.TRACE_STREAM_ORDER,
                 replay_family=""):
        if type(mode) is not Mode or (owner is not None and type(owner) is not DebugSessionOwner):
            raise CLIError("invalid_client_binding")
        if mode is Mode.LIVE and owner is None:
            raise CLIError("no_active_session")
        if history is not None and type(history) is not ReplayHistory:
            raise CLIError("invalid_history_binding")
        if comparison is not None and (type(comparison) is not ReplayHistory or history is None):
            raise CLIError("invalid_comparison_binding")
        if inspection is not None and type(inspection) is not InspectionSnapshot:
            raise CLIError("invalid_inspection_binding")
        if type(replay_domain) is not OrderingDomain or type(replay_family) is not str:
            raise CLIError("invalid_replay_projection")
        if history is not None:
            if inspection is not None and inspection != history.inspection:
                raise CLIError("inspection_history_mismatch")
            inspection = history.inspection
            if owner is not None:
                history.evidence.binding.validate_session(owner.session)
        elif inspection is not None:
            if owner is None:
                raise CLIError("inspection_authorization_binding_required")
            bind_inspection(inspection, owner.session)
        if correlation is not None:
            if type(correlation) is not CorrelationIndex:
                raise CLIError("invalid_correlation_binding")
            if owner is not None:
                correlation.validate_session(owner.session)
            elif history is None or (correlation.session != history.evidence.binding.session or
                    correlation.execution != history.evidence.binding.execution):
                raise CLIError("correlation_binding_mismatch")
            if history is not None and correlation.execution != history.evidence.binding.execution:
                raise CLIError("correlation_binding_mismatch")
        if position is not None and (type(position) is not ObservedPosition or correlation is None or
            position.session != correlation.session or position.execution != correlation.execution or
            position.index_fingerprint != correlation.fingerprint()):
            raise CLIError("position_binding_mismatch")
        if known_order is not None and (type(known_order) is not KnownObservationOrder or
                known_order.position != position):
            raise CLIError("order_binding_mismatch")
        self.mode, self.history, self.comparison, self.owner = mode, history, comparison, owner
        self.inspection, self.correlation = inspection, correlation
        self.position, self.known_order = position, known_order
        self.replay_domain, self.replay_family, self.cursor = replay_domain, replay_family, None
        self._target_binding = ((owner.session.reference, owner.session.execution) if owner is not None else
            (history.evidence.binding.session, history.evidence.binding.execution) if history is not None else
            (None, None))

    def __repr__(self):
        return "DebuggerCLI(mode=" + self.mode.value + ")"

    @property
    def redacted(self):
        return bool(self.history is not None and self.history.evidence.redacted or
            self.inspection is not None and any(
                e.observed_value.status is Availability.REDACTED for e in self.inspection.state.entries))

    @property
    def capabilities(self):
        values = []
        if self.inspection is not None:
            values += ["inspection", "semantic_state", "authority_view"]
        if self.correlation is not None and not self.redacted:
            values += ["air_mapping"]
            if any(c.source.values for c in self.correlation.chains):
                values += ["source_mapping"]
            if any(c.native.values for c in self.correlation.chains):
                values += ["native_correlation"]
            if self.mode is Mode.LIVE and self.position is not None:
                values += ["step_planning"]
        if self.history is not None:
            values += ["evidence_view", "provenance_view", "replay"]
        if self.comparison is not None:
            values += ["comparison"]
        if self.mode is Mode.LIVE and any(c in self.owner.session.granted for c in (
                Capability.REQUEST_STOP, Capability.REQUEST_CONTINUE, Capability.REQUEST_TERMINATE)):
            values += ["control_request"]
        return tuple(sorted(values))

    def _snapshot(self):
        if self.inspection is None:
            raise CLIError("unavailable_inspection")
        return self.inspection

    def _evidence(self):
        if self.history is None:
            raise CLIError("no_retained_evidence")
        return self.history.evidence

    def _live(self):
        if self.mode is not Mode.LIVE:
            raise CLIError("no_active_session")
        if self.owner.session.state is not Lifecycle.ACTIVE:
            raise CLIError("closed_or_inactive_session")
        return self.owner.session

    def _validate_target_binding(self):
        """Reference integrity only; retained reads do not require a live session.

        Observation timestamps/cursors may change. The provisioned session and
        execution cannot silently change; comparison inputs remain independent.
        """
        session, execution = self._target_binding
        if execution is None and type(self.owner) is DebugSessionOwner and self.owner.session.reference == session:
            # CREATED sessions acquire their first target only through the owner.
            execution = self.owner.session.execution
            self._target_binding = (session, execution)
        if self.owner is not None and (type(self.owner) is not DebugSessionOwner or
            (self.owner.session.reference, self.owner.session.execution) != (session, execution)):
            raise CLIError("client_target_rebound")
        if self.history is not None and (type(self.history) is not ReplayHistory or
            (self.history.evidence.binding.session, self.history.evidence.binding.execution) != (session, execution)
            or self.inspection != self.history.inspection):
            raise CLIError("client_target_rebound")
        if self.inspection is not None and (type(self.inspection) is not InspectionSnapshot or
                                           self.inspection.execution != execution):
            raise CLIError("client_target_rebound")
        if self.correlation is not None and (type(self.correlation) is not CorrelationIndex or
            (self.correlation.session, self.correlation.execution) != (session, execution)):
            raise CLIError("client_target_rebound")

    def dispatch(self, arguments):
        try:
            if type(arguments) not in (tuple, list) or not all(type(v) is str for v in arguments):
                raise CLIError("malformed_command")
            if not arguments:
                raise CLIError("missing_command")
            if arguments[0] not in GRAMMAR:
                raise CLIError("unknown_command")
            args = parser().parse_args(arguments)
            if args.command not in ("help", "quit"):
                self._validate_target_binding()
            if self.mode is Mode.LIVE and args.command not in (
                    "help", "status", "capabilities", "session", "quit",
                    "request-stop", "request-continue", "request-terminate"):
                session = self._live()
                if self.history is not None:
                    self.history.evidence.binding.validate_session(session)
                if self.inspection is not None:
                    bind_inspection(self.inspection, session)
                if self.correlation is not None:
                    self.correlation.validate_session(session)
            rows = self._command(args)
            return Response(EXIT_SUCCESS, HELP if args.command == "help" else render(rows),
                            quit=args.command == "quit")
        except CLIError as error:
            return Response(EXIT_USAGE, stderr="apexforge-debug: error: " + str(error) + "\n")
        except (SessionError, InspectionError, CorrelationError, EvidenceError, ReplayError):
            return Response(EXIT_USAGE, stderr="apexforge-debug: error: debugger_contract_rejected\n")

    def _command(self, args):
        command = args.command
        if command in ("help", "quit"):
            return ()
        session = None if self.owner is None else self.owner.session
        if command in ("status", "session"):
            execution = session.execution if session is not None else (
                self.history.evidence.binding.execution if self.history is not None else None)
            return (("CLIENT", CLIENT_VERSION), ("PROTOCOL", PROTOCOL), ("MODE", self.mode.value),
                ("SESSION", "unavailable" if session is None else
                    (session.reference.session_id, session.state.value)),
                ("EXECUTION", "unavailable" if execution is None else execution.execution_id),
                ("CAPABILITIES", self.capabilities), ("LIVE_PAUSE_RESUME", "unsupported"),
                ("EXTERNAL_LIVE_TRANSPORT", False))
        if command == "capabilities":
            return (("CAPABILITIES", self.capabilities), ("GRANTED_DEBUGGER_CAPABILITIES",
                () if session is None else tuple(v.value for v in session.granted)),
                ("CAPABILITY_IS_AUTHORIZATION", False))
        if command in ("inspect", "state", "directive", "result"):
            snapshot = self._snapshot()
            if command == "state":
                return state_rows(snapshot, redacted=self.redacted)
            if self.redacted:
                return ((command.upper(), "redacted"),)
            if command == "inspect":
                return state_rows(snapshot) + tuple((name.upper(), getattr(snapshot, name).record())
                    for name in ("directive", "principal", "authority", "plan", "result", "provenance",
                                 "correlation", "diagnostics", "stack"))
            return ((command.upper(), getattr(snapshot, command).record()),)
        if command == "authority":
            observed = "redacted" if self.redacted else self._snapshot().authority.record()
            return (("OBSERVED_PROGRAM_AUTHORITY", observed),
                ("DEBUG_SESSION_CONTROL_AUTHORIZATION", "separate; checked only by debug session owner"),
                ("OBSERVED_AUTHORITY_GRANTS_DEBUGGER_CONTROL", False))
        if command == "correlate":
            if self.redacted:
                return (("CORRELATION", "redacted"),)
            if self.correlation is None:
                raise CLIError("unavailable_mapping")
            reference = args.reference
            if reference == "current":
                if self.position is None:
                    raise CLIError("observed_position_unavailable")
                reference = self.position.operation_id
            return chain_rows(self.correlation.lookup(reference))
        if command in ("evidence", "provenance", "causal"):
            view = self._evidence()
            boundary = (("EVIDENCE_BEFORE_ATTRIBUTION", True), ("ACTOR_ATTRIBUTION", "not_inferred"))
            if command == "evidence" and (args.action == "list") != (args.reference is None):
                raise CLIError("malformed_command")
            if self.redacted:
                return boundary + (("EVIDENCE", "redacted"),)
            graph = view.graph
            if command == "causal":
                nodes = tuple(n for n in graph.nodes if n.reference.kind in
                    (EvidenceKind.CAUSAL_DECISION, EvidenceKind.CAUSAL_PATH) or
                    n.node_id in {i for f, scope, ordinal, i in view.family_order if f == "causal-selection"})
                return boundary + (("CAUSAL_ASSOCIATION", "recorded only; occurrence may be ambiguous"),) + node_rows(nodes)
            if command == "provenance":
                if args.reference is not None:
                    graph.node(args.reference)
                edges = graph.edges if args.reference is None else tuple(e for e in graph.edges
                    if e.source == args.reference or e.target == args.reference)
                return boundary + (("PROVENANCE", "supplied links only; partial chains are valid"),) + tuple(
                    ("LINK", (e.source, e.relation.value, e.target, e.support)) for e in edges)
            nodes = graph.nodes if args.action == "list" else (
                (graph.node(args.reference),) if args.action == "show" else
                graph.predecessors(args.reference) if args.action == "predecessors" else
                graph.successors(args.reference))
            return boundary + node_rows(nodes)
        if command == "replay":
            self._evidence()
            if (args.action == "seek") != (args.sequence is not None):
                raise CLIError("malformed_command")
            timeline = build_replay(self.history, self.replay_domain, family=self.replay_family,
                mode=ReplayMode.LIVE_SESSION_REPLAY if self.mode is Mode.LIVE else ReplayMode.RETAINED_EVIDENCE_REPLAY,
                session=session)
            if not timeline.records:
                return (("REPLAY_AVAILABILITY", timeline.availability.value), ("REASON", timeline.reason))
            if args.action == "first":
                self.cursor = ReplayCursor.first(timeline, session)
            elif args.action == "last":
                self.cursor = ReplayCursor.last(timeline, session)
            else:
                cursor = self.cursor or ReplayCursor.first(timeline, session)
                self.cursor = cursor.seek(timeline, args.sequence, session) if args.action == "seek" else (
                    cursor.next(timeline, session) if args.action == "next" else cursor.previous(timeline, session))
            record = self.cursor.current(timeline, session)
            return (("REPLAY_AVAILABILITY", timeline.availability.value),
                ("ORDERING_DOMAIN", timeline.domain.value), ("REPLAY_SEQUENCE", record.sequence),
                ("LOGICAL_KEY", record.logical_key), ("EVIDENCE_REFERENCE", record.evidence.node_id),
                ("RE_EXECUTION", False))
        if command == "compare":
            if self.history is None or self.comparison is None:
                raise CLIError("comparison_not_supplied")
            domains = tuple(ComparisonDomain) if args.domain == "summary" else ({
                "state": ComparisonDomain.STATE, "trace": ComparisonDomain.TRACE,
                "causal": ComparisonDomain.CAUSAL, "provenance": ComparisonDomain.PROVENANCE}[args.domain],)
            result = compare_histories(self.history, self.comparison, domains,
                                      ordering=self.replay_domain, family=self.replay_family)
            return (("CAUSAL_EXPLANATION", "not_inferred"), ("ACTOR_ATTRIBUTION", "not_inferred")) + tuple(
                ("COMPARISON", r.record()) for r in result.domains) + (
                ("VOLATILE_DIFFERENCES", result.volatile_differences),)
        if command == "plan-step":
            session = self._live()
            if self.redacted:
                return (("STEP_PLAN_ONLY", True), ("PLANNED_OBSERVATION_TARGET", "redacted"))
            if self.correlation is None or self.position is None:
                raise CLIError("step_planning_unavailable")
            mode = {"semantic": StepMode.SEMANTIC_STEP, "source": StepMode.SOURCE_STEP,
                    "native-correlation": StepMode.NATIVE_CORRELATION_STEP}[args.mode]
            plan = plan_next(self.correlation, session, self.position, mode, self.known_order)
            return (("STEP_PLAN_ONLY", True), ("PLANNED_OBSERVATION_TARGET",
                (plan.status.value, plan.reason)),) + tuple(("TARGET", (
                    t.ordering_key, json.loads(t.chain.canonical_form()))) for t in plan.targets)
        if command.startswith("request-"):
            if self.mode is not Mode.LIVE:
                raise CLIError("no_active_session")
            if args.sequence < 0 or session.execution is None:
                raise CLIError("invalid_request_scope")
            action = {"request-stop": Capability.REQUEST_STOP, "request-continue": Capability.REQUEST_CONTINUE,
                      "request-terminate": Capability.REQUEST_TERMINATE}[command]
            request = ControlRequest(session.reference, session.execution, action, args.sequence,
                session.revision, self.owner.authorization_binding, expected_state=session.state)
            disposition, events = self.owner.submit(request)
            return (("CONTROL_REQUEST_DISPOSITION", (disposition.status.value, disposition.reason)),
                ("STRUCTURAL_REQUEST_ONLY", True), ("CONTROL_EFFECT_OBSERVED", False),
                ("RUNTIME_CONTROL_INTEGRATED", False))
        raise CLIError("unknown_command")


def shell(application, *, stdin, stdout, stderr):
    """Minimal stream shell; no host escape, evaluation, loader or transport."""
    while True:
        stdout.write("apexforge-debug> ")
        stdout.flush()
        line = stdin.readline()
        if line == "":
            return EXIT_SUCCESS
        try:
            arguments = tuple(shlex.split(line))
        except ValueError:
            stderr.write("apexforge-debug: error: malformed_command\n")
            continue
        if not arguments:
            continue
        response = application.dispatch(arguments)
        stdout.write(response.stdout)
        stderr.write(response.stderr)
        if response.quit:
            return EXIT_SUCCESS


def main(argv=None, *, application=None, stdin=None, stdout=None, stderr=None):
    args = tuple(sys.argv[1:] if argv is None else argv)
    application = DebuggerCLI() if application is None else application
    output = stdout if stdout is not None else sys.stdout
    errors = stderr if stderr is not None else sys.stderr
    if args == ("--interactive",):
        return shell(application, stdin=stdin if stdin is not None else sys.stdin, stdout=output, stderr=errors)
    response = application.dispatch(args)
    output.write(response.stdout)
    errors.write(response.stderr)
    return response.code


if __name__ == "__main__":
    raise SystemExit(main())
