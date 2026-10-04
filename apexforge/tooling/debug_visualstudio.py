"""P13.9 in-process Visual Studio command-client foundation.

This is not a registered VS extension, debug engine or native VS DAP bridge.
An embedding owner supplies authorized P13 material; no target loader exists.
All debugger algorithms remain in P13.2--P13.8. Local selection is presentation.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import re

from tooling.debug_cli import Mode
from tooling.debug_dap import DAPAdapter, DAPError, text

VERSION = "apexforge.debug.visualstudio/v1"
MECHANISM = "VISUAL_STUDIO_COMMAND_CLIENT"

# Names deliberately distinguish plans/replay from IDE runtime stepping buttons.
COMMANDS = {
    "Inspect": "apexforge/inspection",
    "Projection Threads": "threads",
    "Semantic Stack": "stackTrace",
    "Watch Lookup": "evaluate",
    "Tooltip Lookup": "evaluate",
    "Sources": "loadedSources",
    "Source Content": "source",
    "Plan Breakpoints": "setBreakpoints",
    "Correlate": "apexforge/correlate",
    "Evidence": "apexforge/evidence",
    "Provenance": "apexforge/provenance",
    "Causal Evidence": "apexforge/causal",
    "Compare": "apexforge/compare",
    "Replay First": "apexforge/replayFirst",
    "Replay Previous": "apexforge/replayPrevious",
    "Replay Next": "apexforge/replayNext",
    "Replay Last": "apexforge/replayLast",
    "Replay Seek": "apexforge/replaySeek",
}
SCOPES = {"State": "State", "Directive Context": "Directive Context",
          "Observed Program Authority": "Observed Program Authority",
          "Debugger Session Authorization": "Debugger Execution Context"}
PLANS = {"Plan Semantic Step": "semantic", "Plan Source Step": "source",
         "Plan Native Correlation": "native-correlation"}


@dataclass(frozen=True)
class Projection:
    """Immutable client presentation, never new canonical evidence.

    JSON contains only the existing adapter's redaction-safe response body.
    Connection sequences, producer objects and request text are not retained.
    """
    success: bool
    code: str
    payload: str

    def view(self):
        """A fresh presentation copy; editing it cannot change producer evidence."""
        return json.loads(self.payload)


def rejected(code):
    return Projection(False, code, "{}")


class VisualStudioClient:
    """Serial owner-injected command surface for a future VS embedding.

    VS session, DAP connection, debug session and execution are distinct.
    No arbitrary transport, executable, process ID or filesystem provisioning.
    Closing releases only this client's adapter handles; evidence survives.
    """
    def __init__(self, application, *, vs_session_id="vs:inspection", source_contents=()):
        if type(vs_session_id) is not str or re.fullmatch(r"[A-Za-z0-9_.:-]{1,64}", vs_session_id) is None:
            raise ValueError("invalid_vs_projection_identity")
        self._vs_session_id = vs_session_id
        self._mode = application.mode
        self._adapter = DAPAdapter(application, dap_session_id="dap:" + vs_session_id,
                                   source_contents=source_contents)
        self._sequence = 0
        self._state = "created"

    @property
    def vs_session_id(self):
        return self._vs_session_id

    @property
    def state(self):
        return self._state

    def __repr__(self):
        return "VisualStudioClient(state=" + self._state + ")"

    def _ask(self, command, arguments):
        self._sequence += 1
        try:
            response = self._adapter.handle(dict(seq=self._sequence, type="request",
                                                 command=command, arguments=arguments))[0]
        except DAPError:
            return rejected("projection_request_rejected")
        if not response["success"]:
            # Existing DAP diagnostics are fixed codes, never producer repr/input.
            return rejected(response["message"])
        return Projection(True, "ok", text(response["body"]))

    def connect(self):
        if self._state != "created":
            return rejected("illegal_client_lifecycle")
        capabilities = self._ask("initialize", {})
        if capabilities.success:
            bound = self._ask("attach" if self._mode is Mode.LIVE else "launch",
                              {"mode": "supplied-session" if self._mode is Mode.LIVE else "retained"})
            ready = self._ask("configurationDone", {}) if bound.success else bound
            if ready.success:
                self._state = "connected"
                return capabilities
            capabilities = ready
        self._adapter.close_projection()
        self._state = "closed"
        return capabilities

    def command(self, name, **arguments):
        if self._state != "connected":
            return rejected("projection_not_connected")
        if type(name) is not str:
            return rejected("unsupported_vs_command")
        if name in SCOPES:
            if arguments:
                return rejected("invalid_vs_arguments")
            context = self._ask("apexforge/inspection", {})
            if not context.success:
                return context
            scopes = [s for s in context.view()["scopes"] if s["name"] == SCOPES[name]]
            if len(scopes) != 1:
                return rejected("scope_unavailable")
            return self._ask("variables", {"variablesReference": scopes[0]["variablesReference"]})
        if name in PLANS:
            if arguments:
                return rejected("invalid_vs_arguments")
            return self._ask("apexforge/planStep", {"mode": PLANS[name]})
        if name not in COMMANDS:
            return rejected("unsupported_vs_command")
        return self._ask(COMMANDS[name], arguments)

    def disconnect(self):
        if self._state != "connected":
            return rejected("illegal_client_lifecycle")
        result = self._ask("disconnect", {})
        self._adapter.close_projection()
        self._state = "closed"
        return result
