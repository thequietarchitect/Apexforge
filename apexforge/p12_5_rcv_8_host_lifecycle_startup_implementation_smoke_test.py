from __future__ import annotations
import json, subprocess, tempfile, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "apexforge/p12_5_rcv_8_host_lifecycle_startup_implementation.json"
HOST_DIR = ROOT / "runtimes/dotnet/ApexForge.Runtime.Host"
PROJ = HOST_DIR / "ApexForge.Runtime.Host.csproj"
PROGRAM = HOST_DIR / "Program.cs"
LIFECYCLE = HOST_DIR / "RuntimeHostLifecycle.cs"

def req(c, m):
    if not c:
        raise AssertionError(m)

def main():
    print("=== P12.5-RCV-8 HOST LIFECYCLE AND STARTUP IMPLEMENTATION FOUNDATION ===")
    req(CONTRACT.exists() and PROJ.exists() and PROGRAM.exists() and LIFECYCLE.exists(), "RCV-8 files missing")
    data = json.loads(CONTRACT.read_text(encoding="utf-8"))
    req(data["profile"] == "apexforge.p12.host-lifecycle-startup-implementation/v1", "profile changed")
    req(data["predecessor"]["stage"] == "P12.5-RCV-7", "predecessor changed")
    req(data["authority"]["language_semantics"] == "CANONICAL_AIR", "semantic authority changed")
    req(data["authority"]["host_defines_language_semantics"] is False, "host gained language semantics")
    deferred = set(data["deferred"])
    for name in ("HOST_INGRESS","EXTERNAL_SERIALIZATION","TARGET_NEUTRAL_HANDOFF_RECONSTRUCTION","MANAGED_EXECUTABLE_CARRIER","MANAGED_EXECUTION_DISPATCH","NATIVE_EXECUTION_DISPATCH","QSI_COUPLING"):
        req(name in deferred, f"{name} selected too early")
    lifecycle = LIFECYCLE.read_text(encoding="utf-8")
    program = PROGRAM.read_text(encoding="utf-8")
    for token in ("RuntimeHostLifecycleState","Created","Starting","Ready","Quiescing","Stopped","Failed","BeginStartup","MarkReady","BeginShutdown","MarkStopped","MarkFailed"):
        req(token in lifecycle, f"lifecycle token missing: {token}")
    req("new ManagedRuntimeHost()" in program, "existing ManagedRuntimeHost not preserved")
    req("new RuntimeHostLifecycle()" in program, "lifecycle implementation not used")
    req("lifecycle.BeginStartup()" in program, "startup transition missing")
    req("lifecycle.MarkReady()" in program, "ready transition missing")
    req("lifecycle.BeginShutdown()" in program, "shutdown transition missing")
    req("lifecycle.MarkStopped()" in program, "stopped transition missing")
    for forbidden in ("JsonSerializer","TargetNeutralLoweringHandoff","ManagedExecutableCarrier","TcpListener","HttpListener","Socket"):
        req(forbidden not in program + lifecycle, f"premature concern entered RCV-8: {forbidden}")
    with tempfile.TemporaryDirectory(prefix="apexforge-p12-5-rcv-8-") as td:
        td = Path(td)
        temp_runtime = td / "ApexForge.Runtime"
        temp_host = td / "ApexForge.Runtime.Host"
        shutil.copytree(ROOT / "runtimes/dotnet/ApexForge.Runtime", temp_runtime, ignore=shutil.ignore_patterns("bin","obj"))
        shutil.copytree(HOST_DIR, temp_host, ignore=shutil.ignore_patterns("bin","obj"))
        cp = subprocess.run(["dotnet","run","--project",str(temp_host / "ApexForge.Runtime.Host.csproj"),"-c","Release","--nologo"], cwd=td, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        req(cp.returncode == 0, "host lifecycle build/execution failed:\n" + cp.stdout + "\n" + cp.stderr)
        out = cp.stdout
        req("TARGET=CSHARP_DOTNET_MANAGED_RUNTIME" in out, "runtime identity missing")
        req("SEMANTICS=False" in out, "host semantic authority changed")
        req("STATE=Ready" in out, "ready state not observed")
        req("STATE=Stopped" in out, "stopped state not observed")
    print("P12_5_RCV_8_PROFILE=apexforge.p12.host-lifecycle-startup-implementation/v1")
    print("P12_5_RCV_8_HOST_PROJECT=ApexForge.Runtime.Host")
    print("P12_5_RCV_8_LIFECYCLE=CREATED_STARTING_READY_QUIESCING_STOPPED_FAILED")
    print("P12_5_RCV_8_LANGUAGE_SEMANTIC_AUTHORITY=CANONICAL_AIR")
    print("P12_5_RCV_8_HOST_INGRESS=DEFERRED")
    print("P12_5_RCV_8_EXECUTION_DISPATCH=DEFERRED")
    print("P12_5_RCV_8_HOST_BUILD=PASS")
    print("P12_5_RCV_8_HOST_EXECUTION=PASS")
    print("P12_5_RCV_8_HOST_LIFECYCLE_AND_STARTUP_IMPLEMENTATION_FOUNDATION=PASS")
    print("P12_5_RCV_8_NEXT=P12.5-RCV-9_HOST_INGRESS_ARCHITECTURE_CENSUS")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
