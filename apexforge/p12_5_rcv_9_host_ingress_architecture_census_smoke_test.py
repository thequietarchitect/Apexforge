from __future__ import annotations
import json, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "apexforge/p12_5_rcv_9_host_ingress_architecture_census.json"
HOST_DIR = ROOT / "runtimes/dotnet/ApexForge.Runtime.Host"
RUNTIME_DIR = ROOT / "runtimes/dotnet/ApexForge.Runtime"
LOWERING = ROOT / "apexforge/native_backend/target_neutral_lowering.py"
LOWERING_INPUT = ROOT / "apexforge/native_backend/lowering_input.py"
RCV8 = ROOT / "apexforge/p12_5_rcv_8_host_lifecycle_startup_implementation_smoke_test.py"

def req(c, m):
    if not c:
        raise AssertionError(m)

def run(*args):
    return subprocess.run(list(args), cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def read_tree(root: Path, patterns: tuple[str, ...]) -> str:
    parts = []
    for pattern in patterns:
        for p in sorted(root.rglob(pattern)):
            if p.is_file():
                try:
                    parts.append(f"\n// FILE:{p.relative_to(ROOT).as_posix()}\n")
                    parts.append(p.read_text(encoding="utf-8"))
                except UnicodeDecodeError:
                    pass
    return "".join(parts)

def main():
    print("=== P12.5-RCV-9 HOST INGRESS ARCHITECTURE CENSUS ===")

    req(CONTRACT.exists(), "RCV-9 contract missing")
    req(HOST_DIR.exists(), "managed host project missing")
    req(RUNTIME_DIR.exists(), "managed runtime library missing")
    req(LOWERING.exists(), "P12.2 target-neutral lowering missing")
    req(LOWERING_INPUT.exists(), "verified AIR lowering input missing")
    req(RCV8.exists(), "RCV-8 smoke test missing")

    cp = run(sys.executable, str(RCV8))
    req(cp.returncode == 0, "RCV-8 regression failed:\n" + cp.stdout + "\n" + cp.stderr)
    print("P12_5_RCV_9_RCV8_REGRESSION=PASS")

    data = json.loads(CONTRACT.read_text(encoding="utf-8"))
    req(data["profile"] == "apexforge.p12.host-ingress-architecture-census/v1", "profile changed")
    req(data["predecessor"]["stage"] == "P12.5-RCV-8", "predecessor changed")
    req(data["authority"]["language_semantics"] == "CANONICAL_AIR", "semantic authority changed")
    req(data["authority"]["host_defines_language_semantics"] is False, "host gained semantic authority")

    state = data["selection_state"]
    req(state["host_ingress"] == "UNSELECTED", "host ingress selected too early")
    req(state["external_serialization"] == "UNSELECTED", "serialization selected too early")
    req(state["managed_execution_dispatch"] == "DEFERRED", "managed dispatch selected too early")
    req(state["native_execution_dispatch"] == "DEFERRED", "native dispatch selected too early")

    host_text = read_tree(HOST_DIR, ("*.cs", "*.csproj"))
    runtime_text = read_tree(RUNTIME_DIR, ("*.cs", "*.csproj"))
    lower_text = LOWERING.read_text(encoding="utf-8")
    lower_input_text = LOWERING_INPUT.read_text(encoding="utf-8")

    req("RuntimeHostLifecycle" in host_text, "RCV-8 lifecycle surface missing")
    req("ManagedRuntimeHost" in host_text, "managed runtime host construction missing")
    req("apexforge.target-neutral-lowering/v1" in lower_text, "P12.2 lowering schema missing")
    req("TargetNeutralLoweringProduct" in lower_text, "P12.2 lowering product missing")
    req("VerifiedAIRLoweringInput" in lower_input_text, "verified AIR lowering input missing")

    # Census only: report possible existing ingress hints without selecting one.
    probes = {
        "COMMAND_LINE_ARGUMENTS": (r"\bargs\b", r"Environment\.GetCommandLineArgs"),
        "STANDARD_INPUT": (r"Console\.In", r"Console\.ReadLine", r"OpenStandardInput"),
        "FILE_PATH": (r"File\.Read", r"FileStream", r"Path\.GetFullPath"),
        "NETWORK_LISTENER": (r"TcpListener", r"HttpListener", r"\bSocket\b"),
        "NAMED_PIPE": (r"NamedPipeServerStream",),
        "DIRECT_NATIVE_CALL": (r"ManagedNativeAbi\.",),
    }

    combined_host = host_text
    for name, patterns in probes.items():
        count = sum(len(re.findall(pat, combined_host)) for pat in patterns)
        print(f"P12_5_RCV_9_{name}_REFERENCE_COUNT={count}")

    # The dedicated host shell must not yet contain prohibited server/dispatch behavior.
    permanently_forbidden_host_tokens = (
        "TcpListener",
        "HttpListener",
        "NamedPipeServerStream",
        "ManagedExecutableCarrier",
        "ManagedNativeAbi.",
    )
    for token in permanently_forbidden_host_tokens:
        req(token not in host_text, f"premature host ingress/dispatch surface found: {token}")
    if "TargetNeutralLoweringHandoff" in host_text:
        req((ROOT / "apexforge/p12_5_rcv_25_managed_host_ingress_implementation_foundation.json").exists(), "later authorized in-process ingress lacks RCV-25 lineage")

    # Runtime library may own ManagedNativeAbi, but the host shell must not duplicate it.
    req("internal static partial class ManagedNativeAbi" in runtime_text, "canonical managed/native ABI owner missing")
    req("internal static partial class ManagedNativeAbi" not in host_text, "host duplicated managed/native ABI")

    # Program must still be lifecycle-only.
    program = (HOST_DIR / "Program.cs").read_text(encoding="utf-8")
    req("BeginStartup" in program and "MarkReady" in program, "startup lifecycle changed")
    req("BeginShutdown" in program and "MarkStopped" in program, "shutdown lifecycle changed")

    print("P12_5_RCV_9_PROFILE=apexforge.p12.host-ingress-architecture-census/v1")
    print("P12_5_RCV_9_LANGUAGE_SEMANTIC_AUTHORITY=CANONICAL_AIR")
    print("P12_5_RCV_9_HOST_INGRESS=UNSELECTED")
    print("P12_5_RCV_9_EXTERNAL_SERIALIZATION=UNSELECTED")
    print("P12_5_RCV_9_MANAGED_EXECUTION_DISPATCH=DEFERRED")
    print("P12_5_RCV_9_NATIVE_EXECUTION_DISPATCH=DEFERRED")
    print("P12_5_RCV_9_P12_2_TARGET_NEUTRAL_BOUNDARY=PASS")
    print("P12_5_RCV_9_HOST_INGRESS_ARCHITECTURE_CENSUS=PASS")
    print("P12_5_RCV_9_NEXT=P12.5-RCV-10_HOST_INGRESS_CONTRACT_DECISION")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
