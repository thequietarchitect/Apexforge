"""P13.8 bounded DAP projection of injected P13 client models.

No target loader, external live transport, execution, control delivery or logs.
DAP identities and events are adapter-local presentation, not canonical evidence.
"""
from __future__ import annotations

import json
import re

from tooling.debug_cli import DebuggerCLI, Mode, CLIError
from tooling.debug_inspection import Availability, bind_inspection, InspectionError
from tooling.debug_session import Capability, Lifecycle, SessionError
from tooling.debug_correlation import CorrelationError
from tooling.debug_evidence import EvidenceError
from tooling.debug_replay import ReplayError
from tooling.debug_metadata import SourceIdentity

VERSION = "apexforge.debug.dap/v1"
MAX_PAYLOAD, MAX_HEADER = 1024 * 1024, 4096
MAX_INT = 2 ** 31 - 1


class DAPError(ValueError):
    pass


def require(condition, code):
    if not condition:
        raise DAPError(code)


def text(value):
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False)


def frame(message):
    payload = text(message).encode("utf-8")
    require(0 < len(payload) <= MAX_PAYLOAD, "message_size_limit")
    return ("Content-Length: %d\r\n\r\n" % len(payload)).encode("ascii") + payload


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "duplicate_json_key")
        result[key] = value
    return result


def _constant(value):
    raise DAPError("invalid_json_constant")


class FramingParser:
    """Incremental strict one-header parser; failure closes this parser."""
    def __init__(self):
        self._buffer = bytearray()
        self._length = None
        self._failed = False

    def feed(self, chunk):
        require(not self._failed, "transport_closed")
        try:
            require(type(chunk) is bytes, "invalid_transport_chunk")
            require(len(self._buffer) + len(chunk) <= MAX_PAYLOAD + MAX_HEADER, "buffer_size_limit")
            self._buffer.extend(chunk)
            messages = []
            while True:
                if self._length is None:
                    end = self._buffer.find(b"\r\n\r\n")
                    if end < 0:
                        require(len(self._buffer) <= MAX_HEADER, "header_size_limit")
                        break
                    require(end + 4 <= MAX_HEADER, "header_size_limit")
                    header = bytes(self._buffer[:end + 4])
                    match = re.fullmatch(rb"Content-Length: ([0-9]{1,7})\r\n\r\n", header)
                    require(match is not None, "malformed_header")
                    length = int(match.group(1))
                    require(0 < length <= MAX_PAYLOAD, "payload_size_limit")
                    self._length = length
                    del self._buffer[:end + 4]
                if len(self._buffer) < self._length:
                    break
                payload = bytes(self._buffer[:self._length])
                del self._buffer[:self._length]
                self._length = None
                try:
                    message = json.loads(payload.decode("utf-8"), object_pairs_hook=_pairs,
                                         parse_constant=_constant)
                except (ValueError, UnicodeError, RecursionError):
                    raise DAPError("malformed_json") from None
                require(type(message) is dict, "message_object_required")
                messages.append(message)
            return tuple(messages)
        except DAPError:
            self._failed = True
            self._buffer.clear()
            self._length = None
            raise

    def finish(self):
        require(not self._failed, "transport_closed")
        if self._buffer or self._length is not None:
            self._failed = True
            self._buffer.clear()
            self._length = None
            raise DAPError("incomplete_message")


def variable(name, value, declared="observation"):
    return {"name": name, "value": value, "type": declared, "variablesReference": 0,
            "presentationHint": {"attributes": ["readOnly"]}}


def field_value(field):
    if field.status is Availability.AVAILABLE:
        return text(field.value)
    return "<" + field.status.value + ">"


CUSTOM = {
    "apexforge/evidence": "evidence", "apexforge/provenance": "provenance",
    "apexforge/causal": "causal", "apexforge/correlate": "correlate",
    "apexforge/compare": "compare", "apexforge/planStep": "plan-step",
    "apexforge/replayFirst": "first", "apexforge/replayNext": "next",
    "apexforge/replayPrevious": "previous", "apexforge/replayLast": "last",
    "apexforge/replaySeek": "seek",
}
ANCHORS = ("mode", "owner", "history", "inspection", "correlation", "position",
           "known_order", "comparison", "replay_domain", "replay_family")


class DAPAdapter:
    """One serial DAP session over one owner-provisioned debugger client.

    Adapter IDs/handles never confer authority. Retained input provisioning and
    authorization remain with the embedding owner; standard live control fails.
    """
    def __init__(self, application, *, dap_session_id="dap:inspection", source_contents=()):
        require(type(application) is DebuggerCLI, "invalid_debugger_client")
        require(type(dap_session_id) is str and re.fullmatch(r"[A-Za-z0-9_.:-]{1,96}",
                dap_session_id) is not None, "invalid_dap_session")
        require(type(source_contents) is tuple, "immutable_source_contents_required")
        self._app = application
        self._anchors = tuple(getattr(application, name) for name in ANCHORS)
        self.dap_session_id = dap_session_id
        self._state, self._out_seq, self._in_seq = "new", 0, 0
        self._issued = set()
        self._lines_one, self._columns_one = True, True
        docs = () if application.correlation is None else tuple(sorted({
            value.document for chain in application.correlation.chains for value in chain.source.values},
            key=lambda d: d.canonical_identity()))
        self._sources = tuple((100 + i, doc) for i, doc in enumerate(docs))
        require(all(type(pair) is tuple and len(pair) == 2 and type(pair[0]) is SourceIdentity
                    and type(pair[1]) is str for pair in source_contents), "invalid_source_contents")
        require(len({d for d, content in source_contents}) == len(source_contents), "duplicate_source_contents")
        for doc, content in source_contents:
            require(doc in docs, "source_outside_supplied_mapping")
            require(len(content.encode("utf-8")) <= MAX_PAYLOAD, "source_size_limit")
            try:
                doc.validate_content(content.encode("utf-8"))
            except ValueError:
                raise DAPError("source_content_mismatch") from None
        self._contents = source_contents

    def __repr__(self):
        return "DAPAdapter(state=" + self._state + ")"

    def close_projection(self):
        """Invalidate local handles only; never close/terminate a producer owner."""
        self._state = "closed"
        self._issued.clear()

    def _validate_binding(self, live=True):
        require(all(getattr(self._app, name) is value or
                    type(value) in (str, Mode) and getattr(self._app, name) == value
                    for name, value in zip(ANCHORS, self._anchors)), "client_target_rebound")
        app = self._app
        if live and app.mode is Mode.LIVE:
            session = app.owner.session
            require(session.state is Lifecycle.ACTIVE and Capability.OBSERVE in session.granted,
                    "supplied_session_unavailable")
            if app.history is not None:
                app.history.evidence.binding.validate_session(session)
            if app.inspection is not None:
                bind_inspection(app.inspection, session)
            if app.correlation is not None:
                app.correlation.validate_session(session)

    def _message(self, kind, **values):
        require(self._out_seq < MAX_INT, "adapter_sequence_exhausted")
        self._out_seq += 1
        return dict(seq=self._out_seq, type=kind, **values)

    def _event(self, name, body=None):
        return self._message("event", event=name, body={} if body is None else body)

    def handle(self, request):
        """Return response followed by any adapter-local events; no runtime events."""
        require(type(request) is dict and request.get("type") == "request" and
            type(request.get("seq")) is int and 0 < request["seq"] <= MAX_INT and
            type(request.get("command")) is str and 0 < len(request["command"]) <= 128,
            "invalid_request_envelope")
        command, sequence = request["command"], request["seq"]
        try:
            require(sequence > self._in_seq, "stale_request_sequence")
            self._in_seq = sequence
            args = request.get("arguments", {})
            require(type(args) is dict, "arguments_object_required")
            self._validate_binding(live=False)
            body, events = self._request(command, args)
            # Responses cannot quietly exceed the bounded wire contract.
            require(len(text(body).encode("utf-8")) < MAX_PAYLOAD - 512, "response_size_limit")
            response = self._message("response", request_seq=sequence, command=command, success=True, body=body)
            return (response,) + tuple(self._event(name, data) for name, data in events)
        except (DAPError, SessionError, InspectionError, CorrelationError, EvidenceError, ReplayError, CLIError) as error:
            code = str(error) if type(error) is DAPError else "debugger_contract_rejected"
            return (self._message("response", request_seq=sequence, command=command, success=False,
                message=code, body={"error": {"id": 1, "format": code, "showUser": True}}),)

    def _source(self, args):
        require(not self._app.redacted, "source_redacted")
        source = args.get("source", {})
        require(type(source) is dict and "path" not in source, "arbitrary_source_path_unsupported")
        reference = args.get("sourceReference", source.get("sourceReference"))
        require(type(reference) is int and 0 < reference <= MAX_INT, "source_reference_required")
        require("sourceReference" not in source or source["sourceReference"] == reference,
                "source_reference_mismatch")
        found = tuple(d for i, d in self._sources if i == reference)
        require(len(found) == 1, "source_unavailable")
        return found[0]

    def _source_list(self):
        return [] if self._app.redacted else [{"name": d.logical_name, "sourceReference": i,
            "origin": "ApexForge supplied mapping"} for i, d in self._sources]

    def _client_rows(self, arguments):
        response = self._app.dispatch(tuple(arguments))
        require(response.code == 0, "client_observation_unavailable")
        return [{"label": line.split("=", 1)[0], "value": json.loads(line.split("=", 1)[1])}
                for line in response.stdout.splitlines()]

    def _scopes(self):
        app = self._app
        scopes = []
        for ref, name, present in ((10, "State", app.inspection is not None),
            (11, "Directive Context", app.inspection is not None),
            (12, "Observed Program Authority", app.inspection is not None),
            (13, "Debugger Execution Context", app.owner is not None or app.history is not None),
            (14, "Evidence", app.history is not None), (15, "Provenance", app.history is not None)):
            if present:
                self._issued.add(ref)
                scopes.append({"name": name, "variablesReference": ref, "expensive": False})
        return scopes

    def _variables(self, reference):
        require(type(reference) is int and reference in self._issued, "variables_reference_unavailable")
        if reference == 10:
            return [variable(entry.key, "<redacted>" if self._app.redacted else field_value(entry.observed_value),
                text(entry.declared_type.value) if entry.declared_type.status is Availability.AVAILABLE
                else "<" + entry.declared_type.status.value + ">") for entry in self._app.inspection.state.entries]
        command = {11: ("directive",), 12: ("authority",), 13: ("status",),
                   14: ("evidence", "list"), 15: ("provenance",)}[reference]
        return [variable(row["label"], text(row["value"])) for row in self._client_rows(command)]

    def _frame(self):
        snapshot = self._app.inspection
        if snapshot is None or self._app.redacted or snapshot.stack.status is not Availability.AVAILABLE:
            return None
        value = snapshot.stack.value
        require(type(value) is tuple and len(value) == 7 and value[0] == "pure-function-frame" and
            value[1] == snapshot.execution.air_fingerprint and type(value[2]) is str and
            type(value[3]) is str and type(value[4]) is int and value[4] >= 0, "frame_evidence_unsupported")
        return {"id": 1, "name": value[3], "line": 0, "column": 0,
                "apexforge/frameReference": [value[1], value[2], value[4]],
                "apexforge/sourceAvailability": "unavailable"}

    def _request(self, command, args):
        if command == "initialize":
            require(self._state == "new", "illegal_lifecycle")
            for key in ("linesStartAt1", "columnsStartAt1"):
                require(type(args.get(key, True)) is bool, "invalid_coordinate_origin")
            self._lines_one = args.get("linesStartAt1", True)
            self._columns_one = args.get("columnsStartAt1", True)
            self._state = "initialized"
            return {"supportsConfigurationDoneRequest": True,
                "supportsEvaluateForHovers": self._app.inspection is not None,
                "supportsLoadedSourcesRequest": bool(self._sources) and not self._app.redacted,
                "supportsTerminateRequest": False, "supportsRestartRequest": False,
                "supportsSetVariable": False, "supportsSetExpression": False,
                "supportsStepBack": False, "supportsReadMemoryRequest": False,
                "supportsWriteMemoryRequest": False, "supportsInstructionBreakpoints": False,
                "supportsFunctionBreakpoints": False, "supportsConditionalBreakpoints": False,
                "supportsHitConditionalBreakpoints": False, "supportsLogPoints": False,
                "exceptionBreakpointFilters": [], "apexforge/capabilities": {
                    "version": VERSION, "runtimeControl": False, "breakpointExecution": False,
                    "readOnly": True, "customRequests": ["apexforge/inspection"] + sorted(CUSTOM)}}, [("initialized", {})]
        require(self._state != "new" and self._state != "closed", "illegal_lifecycle")
        if command in ("launch", "attach"):
            require(self._state == "initialized", "illegal_lifecycle")
            require(set(args) <= {"mode", "name", "type", "noDebug"}, "unsupported_target_fields")
            require(args.get("noDebug", False) is False, "unsupported_launch_mode")
            if command == "launch":
                require(self._app.mode is Mode.RETAINED and args.get("mode") == "retained",
                        "retained_launch_required")
                require(self._app.history is not None or self._app.inspection is not None or
                        self._app.correlation is not None, "supplied_target_unavailable")
            else:
                require(self._app.mode is Mode.LIVE and args.get("mode") == "supplied-session",
                        "authorized_supplied_session_required")
            self._validate_binding()
            self._state = "bound"
            return {"apexforge/launch": {"projectionOnly": True, "executesProgram": False,
                    "externalTargetLoading": False}}, []
        if command == "disconnect":
            require(set(args) <= {"restart", "terminateDebuggee", "suspendDebuggee"} and
                all(type(v) is bool and v is False for v in args.values()), "runtime_control_unavailable")
            self.close_projection()
            return {"apexforge/disconnect": {"executionTerminated": False}}, [("terminated", {})]
        self._validate_binding()
        if command == "configurationDone":
            require(self._state == "bound" and not args, "illegal_lifecycle")
            self._state = "ready"
            return {}, [("stopped", {"reason": "entry", "threadId": 1,
                "description": "ApexForge supplied/offline inspection position; runtime pause not observed",
                "apexforge/positionKind": "OFFLINE_INSPECTION_POSITION",
                "apexforge/runtimePauseObserved": False})]
        if command == "setBreakpoints":
            require(self._state in ("bound", "ready"), "illegal_lifecycle")
            doc = self._source(args)
            breakpoints = args.get("breakpoints", [])
            require(type(breakpoints) is list and len(breakpoints) <= 1024, "invalid_breakpoints")
            result = []
            for item in breakpoints:
                require(type(item) is dict and set(item) <= {"line", "column"} and
                    type(item.get("line")) is int and int(self._lines_one) <= item["line"] <= MAX_INT,
                    "invalid_breakpoint_location")
                require("column" not in item or type(item["column"]) is int and
                    int(self._columns_one) <= item["column"] <= MAX_INT, "invalid_breakpoint_location")
                line = item["line"] + int(not self._lines_one)
                column = None if "column" not in item else item["column"] + int(not self._columns_one)
                candidates = tuple(sorted({chain.air.operation.operation_id for chain in self._app.correlation.chains
                    if any(v.document == doc and v.span.start.line <= line <= v.span.end.line and
                        not (line == v.span.end.line and v.span.end.column == 1)
                        and (column is None or (v.span.start.line, v.span.start.column) <= (line, column) <
                             (v.span.end.line, v.span.end.column) or v.span.is_empty and
                             (line, column) == (v.span.start.line, v.span.start.column))
                        for v in chain.source.values)}))
                result.append({"verified": False, "line": item["line"],
                    "message": "runtime breakpoint execution unavailable",
                    "apexforge/planning": {"planningOnly": True, "operationReferences": candidates,
                        "granularity": "line" if column is None else "source-position",
                        "availability": "ambiguous" if len(candidates) > 1 else
                        "available" if candidates else "unavailable"}})
            return {"breakpoints": result}, []
        require(self._state == "ready", "illegal_lifecycle")
        if command in ("continue", "pause", "next", "stepIn", "stepOut", "terminate",
                       "setVariable", "setExpression", "restart", "readMemory", "writeMemory"):
            raise DAPError("runtime_control_or_mutation_unavailable")
        if command == "threads":
            return {"threads": [{"id": 1, "name": "ApexForge debugger inspection projection (not OS thread)"}]}, []
        if command == "stackTrace":
            require(args.get("threadId") == 1 and type(args.get("threadId")) is int, "projection_thread_required")
            start, count = args.get("startFrame", 0), args.get("levels", 0)
            require(type(start) is int and 0 <= start <= MAX_INT and type(count) is int and
                    0 <= count <= MAX_INT, "invalid_stack_paging")
            projected = self._frame()
            frames = [] if projected is None or start > 0 else [projected]
            return {"stackFrames": frames, "totalFrames": int(projected is not None),
                "apexforge/stackAvailability": "available" if projected is not None else
                    "redacted" if self._app.redacted else "unavailable"}, []
        if command == "scopes":
            require(type(args.get("frameId")) is int and args["frameId"] == 1 and self._frame() is not None,
                    "semantic_frame_unavailable")
            return {"scopes": self._scopes()}, []
        if command == "variables":
            values = self._variables(args.get("variablesReference"))
            start, count = args.get("start", 0), args.get("count", 0)
            require(type(start) is int and type(count) is int and 0 <= start <= MAX_INT and
                    0 <= count <= MAX_INT, "invalid_variables_paging")
            return {"variables": values[start:] if count == 0 else values[start:start + count]}, []
        if command == "evaluate":
            expression = args.get("expression")
            require(type(expression) is str and len(expression) <= 512, "invalid_lookup")
            snapshot = self._app.inspection
            require(snapshot is not None, "inspection_unavailable")
            require("frameId" not in args or type(args["frameId"]) is int and
                    args["frameId"] == 1 and self._frame() is not None, "semantic_frame_unavailable")
            found = tuple(e for e in snapshot.state.entries if e.key == expression)
            require(len(found) == 1, "known_state_lookup_only")
            return {"result": "<redacted>" if self._app.redacted else field_value(found[0].observed_value),
                    "variablesReference": 0,
                    "type": text(found[0].declared_type.value), "apexforge/lookupOnly": True}, []
        if command == "loadedSources":
            return {"sources": self._source_list()}, []
        if command == "source":
            doc = self._source(args)
            found = tuple(content for identity, content in self._contents if identity == doc)
            require(len(found) == 1, "authorized_source_content_unavailable")
            return {"content": found[0], "mimeType": "text/plain"}, []
        if command == "apexforge/inspection":
            require(not args, "invalid_custom_arguments")
            return {"projectionOnly": True, "scopes": self._scopes(),
                    "semanticStackAvailable": self._frame() is not None}, []
        if command in CUSTOM:
            cli = CUSTOM[command]
            if cli == "evidence":
                require(set(args) <= {"action", "reference"}, "invalid_custom_arguments")
                action = args.get("action", "list")
                require(action in ("list", "show", "predecessors", "successors"), "invalid_custom_arguments")
                argv = [cli, action] + ([args["reference"]] if "reference" in args else [])
            elif cli == "provenance":
                require(set(args) <= {"reference"}, "invalid_custom_arguments")
                argv = [cli] + ([args["reference"]] if "reference" in args else [])
            elif cli == "causal":
                require(not args, "invalid_custom_arguments")
                argv = [cli]
            elif cli in ("correlate", "compare", "plan-step"):
                key, default = {"correlate": ("reference", "current"), "compare": ("domain", "summary"),
                                "plan-step": ("mode", None)}[cli]
                require(set(args) <= {key}, "invalid_custom_arguments")
                argv = [cli, args.get(key, default)]
            else:
                require(set(args) <= ({"sequence"} if cli == "seek" else set()), "invalid_custom_arguments")
                argv = ["replay", cli]
                if cli == "seek":
                    require(type(args.get("sequence")) is int and 0 <= args["sequence"] <= MAX_INT,
                            "invalid_replay_seek")
                    argv.append(str(args["sequence"]))
            require(all(type(v) is str for v in argv), "invalid_custom_arguments")
            rows = self._client_rows(argv)
            return {"projectionOnly": True, "planningOnly": cli == "plan-step", "reexecution": False,
                    "rows": rows}, []
        raise DAPError("unsupported_request")


def serve(adapter, input_stream, output_stream):
    """Binary-stream transport for an embedding owner, not a target launcher."""
    require(type(adapter) is DAPAdapter, "invalid_adapter")
    parser = FramingParser()
    try:
        while True:
            chunk = getattr(input_stream, "read1", input_stream.read)(4096)
            if chunk == b"":
                parser.finish()
                return
            for request in parser.feed(chunk):
                for response in adapter.handle(request):
                    output_stream.write(frame(response))
                output_stream.flush()
    finally:
        adapter.close_projection()
