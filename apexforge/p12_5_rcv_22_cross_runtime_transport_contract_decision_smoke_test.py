from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "apexforge/p12_5_rcv_22_cross_runtime_transport_contract_decision.json"
RCV21 = ROOT / "apexforge/p12_5_rcv_21_cross_runtime_transport_architecture_census_smoke_test.py"
RCV10 = ROOT / "apexforge/p12_5_rcv_10_host_ingress_contract_decision.json"
PROJECTION = ROOT / "apexforge/native_backend/managed_handoff_projection.py"
HANDOFF = ROOT / "runtimes/dotnet/ApexForge.Runtime/TargetNeutralLoweringHandoff.cs"
HOST_PROGRAM = ROOT / "runtimes/dotnet/ApexForge.Runtime.Host/Program.cs"

def req(c, m):
    if not c:
        raise AssertionError(m)

def run(*args):
    return subprocess.run(list(args), cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def main():
    print("=== P12.5-RCV-22 CROSS-RUNTIME TRANSPORT CONTRACT DECISION ===")
    for p in (CONTRACT, RCV21, RCV10, PROJECTION, HANDOFF, HOST_PROGRAM):
        req(p.exists(), f"missing required file: {p}")

    cp = run(sys.executable, str(RCV21))
    req(cp.returncode == 0, "RCV-21 regression failed:\n" + cp.stdout + "\n" + cp.stderr)
    print("P12_5_RCV_22_RCV21_REGRESSION=PASS")

    ingress = json.loads(RCV10.read_text(encoding="utf-8-sig"))
    req(ingress["decision"]["host_ingress_family"] == "IN_PROCESS_API", "RCV-10 ingress family changed")
    req(ingress["decision"]["network_ingress"] == "FORBIDDEN_IN_THIS_LINE", "RCV-10 network policy changed")

    data = json.loads(CONTRACT.read_text(encoding="utf-8-sig"))
    req(data["profile"] == "apexforge.p12.cross-runtime-transport-contract-decision/v1", "profile changed")
    req(data["predecessor"]["stage"] == "P12.5-RCV-21", "predecessor changed")

    d = data["decision"]
    req(d["cross_runtime_transport"] == "DEFERRED_NO_TRANSPORT_AUTHORIZED", "cross-runtime transport improperly selected")
    req(d["external_serialization"] == "UNSELECTED", "serialization selected")
    req(d["transport_encoding"] == "UNSELECTED", "encoding selected")
    req(d["bridge_process_model"] == "UNSELECTED", "process model selected")
    req(d["managed_host_ingress"] == "IN_PROCESS_API", "managed host ingress changed")
    req(d["network_ingress"] == "FORBIDDEN_IN_THIS_LINE", "network ingress policy weakened")
    req(d["projection_scope"] == "SOURCE_SIDE_STRUCTURAL_ONLY", "projection scope changed")
    req(d["managed_admission_scope"] == "IN_PROCESS_VALIDATE_AND_RETURN_ONLY", "managed admission scope changed")

    r = data["rationale"]
    for key in (
        "historical_transport_identity_recovered",
        "historical_external_serialization_selected",
        "historical_cross_runtime_process_model_selected",
        "current_projection_has_transport_behavior",
        "current_managed_handoff_has_transport_behavior",
        "current_host_has_external_transport_behavior",
    ):
        req(r[key] is False, f"unsupported transport evidence introduced: {key}")
    req(r["avoid_inventing_recovery_transport"] is True, "recovery conservatism weakened")

    projection = PROJECTION.read_text(encoding="utf-8-sig")
    handoff = HANDOFF.read_text(encoding="utf-8-sig")
    host = HOST_PROGRAM.read_text(encoding="utf-8-sig")

    for token in ("json.dumps", "json.loads", "subprocess", "socket", "requests", "NamedPipe", "FileStream", "Python.Runtime", "ctypes."):
        req(token not in projection, f"projection transport behavior appeared: {token}")

    for token in ("JsonSerializer", "FromJson", "NamedPipe", "TcpClient", "HttpClient", "FileStream"):
        req(token not in handoff, f"managed handoff transport behavior appeared: {token}")

    for token in ("Console.ReadLine", "Console.In", "NamedPipe", "TcpListener", "HttpListener", "ProcessStartInfo", "Python.Runtime"):
        req(token not in host, f"host external transport behavior appeared: {token}")

    c = data["constraints"]
    for key in (
        "no_json_handoff_serializer",
        "no_stdio_payload_transport",
        "no_file_payload_transport",
        "no_pipe_transport",
        "no_socket_or_http_transport",
        "no_shared_memory_transport",
        "no_python_embedding_or_pythonnet_selection",
        "no_new_native_ffi_transport",
        "no_execution_dispatch",
    ):
        req(c[key] is True, f"constraint weakened: {key}")

    a = data["authority"]
    req(a["language_semantics"] == "CANONICAL_AIR", "semantic authority changed")
    req(a["projection_owner"] == "apexforge.native_backend", "projection owner changed")
    req(a["managed_handoff_owner"] == "ApexForge.Runtime", "managed handoff owner changed")
    req(a["managed_admission_owner"] == "ApexForge.Runtime.ManagedRuntimeHost", "admission owner changed")
    req(a["host_shell_owner"] == "ApexForge.Runtime.Host", "host shell owner changed")
    req(a["transport_authority_created"] is False, "transport authority unexpectedly created")

    print("P12_5_RCV_22_PROFILE=apexforge.p12.cross-runtime-transport-contract-decision/v1")
    print("P12_5_RCV_22_CROSS_RUNTIME_TRANSPORT=DEFERRED_NO_TRANSPORT_AUTHORIZED")
    print("P12_5_RCV_22_MANAGED_HOST_INGRESS=IN_PROCESS_API")
    print("P12_5_RCV_22_EXTERNAL_SERIALIZATION=UNSELECTED")
    print("P12_5_RCV_22_BRIDGE_PROCESS_MODEL=UNSELECTED")
    print("P12_5_RCV_22_NETWORK_INGRESS=FORBIDDEN_IN_THIS_LINE")
    print("P12_5_RCV_22_LANGUAGE_SEMANTIC_AUTHORITY=CANONICAL_AIR")
    print("P12_5_RCV_22_EXECUTION_DISPATCH=DEFERRED")
    print("P12_5_RCV_22_CROSS_RUNTIME_TRANSPORT_CONTRACT_DECISION=PASS")
    print("P12_5_RCV_22_NEXT=P12.5-RCV-23_MANAGED_HOST_INGRESS_IMPLEMENTATION_CENSUS")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
