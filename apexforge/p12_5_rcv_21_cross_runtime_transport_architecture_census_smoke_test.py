from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "apexforge/p12_5_rcv_21_cross_runtime_transport_architecture_census.json"
RCV20 = ROOT / "apexforge/p12_5_rcv_20_projection_value_object_compatibility_census_smoke_test.py"
RCV10 = ROOT / "apexforge/p12_5_rcv_10_host_ingress_contract_decision.json"
PROJECTION = ROOT / "apexforge/native_backend/managed_handoff_projection.py"
HANDOFF = ROOT / "runtimes/dotnet/ApexForge.Runtime/TargetNeutralLoweringHandoff.cs"
HOST_PROGRAM = ROOT / "runtimes/dotnet/ApexForge.Runtime.Host/Program.cs"
RUNTIME_DIR = ROOT / "runtimes/dotnet/ApexForge.Runtime"
HOST_DIR = ROOT / "runtimes/dotnet/ApexForge.Runtime.Host"
NATIVE_BACKEND_DIR = ROOT / "apexforge/native_backend"

SIGNALS = {
    "JSON": ("JsonSerializer", "json.dumps", "json.loads", "System.Text.Json"),
    "STDIN": ("Console.ReadLine", "Console.In", "sys.stdin", "input("),
    "CLI_ARGS": ("Environment.GetCommandLineArgs", "args[", "sys.argv", "argparse"),
    "FILE_IO": ("File.Read", "File.Write", "FileStream", "Path.read_text", "Path.write_text", "open("),
    "NAMED_PIPE": ("NamedPipe", "NamedPipeServerStream", "NamedPipeClientStream"),
    "NETWORK": ("TcpListener", "TcpClient", "HttpListener", "HttpClient", "socket.", "requests."),
    "PROCESS": ("ProcessStartInfo", "Process.Start", "subprocess.", "Popen("),
    "SHARED_MEMORY": ("MemoryMappedFile", "shared_memory"),
    "PYTHON_EMBED": ("Python.Runtime", "Py.GIL", "pythonnet"),
    "NATIVE_FFI": ("DllImport", "LibraryImport", "ctypes.", "cffi"),
}

def req(c, m):
    if not c:
        raise AssertionError(m)

def run(*args):
    return subprocess.run(list(args), cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def production_files():
    files = []
    files.extend(sorted(NATIVE_BACKEND_DIR.glob("*.py")))
    files.extend(sorted(RUNTIME_DIR.glob("*.cs")))
    files.extend(sorted(HOST_DIR.glob("*.cs")))
    return files

def count_signals(files):
    counts = {k: 0 for k in SIGNALS}
    refs = {k: [] for k in SIGNALS}
    for p in files:
        text = p.read_text(encoding="utf-8-sig")
        rel = p.relative_to(ROOT).as_posix()
        for family, tokens in SIGNALS.items():
            for token in tokens:
                n = text.count(token)
                if n:
                    counts[family] += n
                    refs[family].append((rel, token, n))
    return counts, refs

def main():
    print("=== P12.5-RCV-21 CROSS-RUNTIME TRANSPORT ARCHITECTURE CENSUS ===")
    for p in (CONTRACT, RCV20, RCV10, PROJECTION, HANDOFF, HOST_PROGRAM):
        req(p.exists(), f"missing required file: {p}")

    cp = run(sys.executable, str(RCV20))
    req(cp.returncode == 0, "RCV-20 regression failed:\n" + cp.stdout + "\n" + cp.stderr)
    print("P12_5_RCV_21_RCV20_REGRESSION=PASS")

    ingress = json.loads(RCV10.read_text(encoding="utf-8-sig"))
    req(ingress["decision"]["host_ingress_family"] == "IN_PROCESS_API", "RCV-10 host ingress family changed")
    req(ingress["decision"]["external_serialization"] == "UNSELECTED", "RCV-10 serialization selection changed")
    req(ingress["decision"]["network_ingress"] == "FORBIDDEN_IN_THIS_LINE", "RCV-10 network policy changed")
    print("P12_5_RCV_21_RCV10_HOST_INGRESS=IN_PROCESS_API")

    data = json.loads(CONTRACT.read_text(encoding="utf-8-sig"))
    req(data["profile"] == "apexforge.p12.cross-runtime-transport-architecture-census/v1", "profile changed")
    req(data["predecessor"]["stage"] == "P12.5-RCV-20", "predecessor changed")
    req(data["historical_evidence"]["p12_5_external_serialization"] == "UNSELECTED", "historical serialization state changed")
    req(data["historical_evidence"]["p12_5_concrete_handoff_serialization"] == "UNSELECTED", "historical handoff serialization changed")

    selection = data["selection"]
    req(selection["cross_runtime_transport"] == "UNSELECTED", "transport selected during census")
    req(selection["external_serialization"] == "UNSELECTED", "serialization selected during census")
    req(selection["transport_encoding"] == "UNSELECTED", "encoding selected during census")
    req(selection["bridge_process_model"] == "UNSELECTED", "process model selected during census")
    req(selection["network_ingress"] == "FORBIDDEN_IN_THIS_LINE", "network policy weakened")

    projection_text = PROJECTION.read_text(encoding="utf-8-sig")
    handoff_text = HANDOFF.read_text(encoding="utf-8-sig")
    host_text = HOST_PROGRAM.read_text(encoding="utf-8-sig")

    for token in ("json.dumps", "json.loads", "subprocess", "socket", "requests", "NamedPipe", "FileStream", "sys.stdin", "sys.argv"):
        req(token not in projection_text, f"projection acquired transport behavior before decision gate: {token}")

    req("JsonSerializer" not in handoff_text, "target-neutral managed handoff acquired JSON serialization")
    req("FromJson" not in handoff_text, "target-neutral managed handoff acquired deserialization")
    for token in ("Console.ReadLine", "Console.In", "NamedPipe", "TcpListener", "HttpListener", "ProcessStartInfo"):
        req(token not in host_text, f"managed host acquired external transport behavior before decision gate: {token}")

    files = production_files()
    counts, refs = count_signals(files)

    # Existing signals are evidence only. In particular, JSON in CanonicalExecutionEnvelope and
    # LibraryImport in ManagedNativeAbi predate this bridge and do not select its transport.
    print(f"P12_5_RCV_21_PRODUCTION_FILE_COUNT={len(files)}")
    for family in ("JSON", "STDIN", "CLI_ARGS", "FILE_IO", "NAMED_PIPE", "NETWORK", "PROCESS", "SHARED_MEMORY", "PYTHON_EMBED", "NATIVE_FFI"):
        print(f"P12_5_RCV_21_SIGNAL_{family}_COUNT={counts[family]}")

    projection_refs = 0
    for family, rows in refs.items():
        for rel, token, n in rows:
            if rel.endswith("managed_handoff_projection.py"):
                projection_refs += n
    req(projection_refs == 0, "projection implementation contains transport signals")

    constraints = data["constraints"]
    for key in (
        "must_not_treat_canonical_execution_envelope_json_as_handoff_transport_selection",
        "must_not_promote_p12_2_canonical_json_into_managed_handoff",
        "must_preserve_in_process_host_ingress_decision",
        "must_not_enable_network_ingress",
        "census_only",
    ):
        req(constraints[key] is True, f"constraint weakened: {key}")

    auth = data["authority"]
    req(auth["language_semantics"] == "CANONICAL_AIR", "semantic authority changed")
    req(auth["transport_may_define_semantics"] is False, "transport gained semantic authority")
    req(auth["transport_may_execute"] is False, "transport gained execution authority")
    req(auth["transport_may_lower"] is False, "transport gained lowering authority")
    req(auth["transport_may_reinterpret"] is False, "transport gained reinterpretation authority")

    print("P12_5_RCV_21_PROFILE=apexforge.p12.cross-runtime-transport-architecture-census/v1")
    print("P12_5_RCV_21_PROJECTION_TRANSPORT_SIGNAL_COUNT=0")
    print("P12_5_RCV_21_HANDOFF_JSON_SERIALIZATION=False")
    print("P12_5_RCV_21_HOST_EXTERNAL_TRANSPORT=False")
    print("P12_5_RCV_21_CROSS_RUNTIME_TRANSPORT=UNSELECTED")
    print("P12_5_RCV_21_EXTERNAL_SERIALIZATION=UNSELECTED")
    print("P12_5_RCV_21_NETWORK_INGRESS=FORBIDDEN_IN_THIS_LINE")
    print("P12_5_RCV_21_EXECUTION_DISPATCH=DEFERRED")
    print("P12_5_RCV_21_CROSS_RUNTIME_TRANSPORT_ARCHITECTURE_CENSUS=PASS")
    print("P12_5_RCV_21_NEXT=P12.5-RCV-22_CROSS_RUNTIME_TRANSPORT_CONTRACT_DECISION")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
