from __future__ import annotations
import json, subprocess, sys, tempfile, shutil
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
PROJ = ROOT / "runtimes/dotnet/ApexForge.Runtime.Host/ApexForge.Runtime.Host.csproj"
PROGRAM = ROOT / "runtimes/dotnet/ApexForge.Runtime.Host/Program.cs"
CONTRACT = ROOT / "apexforge/p12_5_rcv_6_managed_host_project_skeleton.json"

def require(c,m):
    if not c: raise AssertionError(m)

def run(*args):
    return subprocess.run(list(args), cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def main():
    print("=== P12.5-RCV-6 DEDICATED MANAGED HOST PROJECT SKELETON ===")
    require(PROJ.exists() and PROGRAM.exists() and CONTRACT.exists(), "RCV-6 files missing")
    c=json.loads(CONTRACT.read_text(encoding="utf-8"))
    require(c["profile"]=="apexforge.p12.runtime-host-project-skeleton/v1", "profile changed")
    require(c["predecessor"]["stage"]=="P12.5-RCV-5", "predecessor changed")
    require(c["ownership"]["host_defines_language_semantics"] is False, "host semantic authority forbidden")
    require(c["ownership"]["host_duplicates_native_interop"] is False, "native interop duplication forbidden")
    require(c["behavior"]["execution_dispatch"]=="DEFERRED", "execution dispatch selected early")
    require(c["behavior"]["host_ingress"]=="UNSELECTED", "host ingress selected early")
    proj=PROJ.read_text(encoding="utf-8")
    program=PROGRAM.read_text(encoding="utf-8")
    require("<OutputType>Exe</OutputType>" in proj, "host must be executable")
    require("<TargetFramework>net10.0</TargetFramework>" in proj, "target framework changed")
    require("../ApexForge.Runtime/ApexForge.Runtime.csproj" in proj, "runtime project reference missing")
    require("new ManagedRuntimeHost()" in program, "existing managed runtime host not used")
    for forbidden in ("ManagedNativeAbi", "JsonSerializer", "TargetNeutralLoweringHandoff", "ManagedExecutableCarrier"):
        require(forbidden not in program, f"premature host concern entered skeleton: {forbidden}")
    with tempfile.TemporaryDirectory(prefix="apexforge-p12-5-rcv-6-") as td:
        td=Path(td)
        temp_runtime=td/"ApexForge.Runtime"
        temp_host=td/"ApexForge.Runtime.Host"
        shutil.copytree(ROOT/"runtimes/dotnet/ApexForge.Runtime", temp_runtime, ignore=shutil.ignore_patterns("bin","obj"))
        shutil.copytree(PROJ.parent, temp_host, ignore=shutil.ignore_patterns("bin","obj"))
        temp_proj=temp_host/"ApexForge.Runtime.Host.csproj"
        cp=subprocess.run(["dotnet","run","--project",str(temp_proj),"-c","Release","--nologo"], cwd=td, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        require(cp.returncode==0, "host build/execution failed:\n"+cp.stdout+"\n"+cp.stderr)
        out=cp.stdout.strip()
        require("APEXFORGE_RUNTIME_HOST|TARGET=CSHARP_DOTNET_MANAGED_RUNTIME|SEMANTICS=False" in out, "host identity output mismatch: "+out)
    print("P12_5_RCV_6_PROFILE=apexforge.p12.runtime-host-project-skeleton/v1")
    print("P12_5_RCV_6_DEDICATED_HOST_PROJECT=ApexForge.Runtime.Host")
    print("P12_5_RCV_6_EXISTING_MANAGED_RUNTIME_HOST=PRESERVED")
    print("P12_5_RCV_6_LANGUAGE_SEMANTIC_AUTHORITY=CANONICAL_AIR")
    print("P12_5_RCV_6_HOST_INGRESS=UNSELECTED")
    print("P12_5_RCV_6_EXECUTION_DISPATCH=DEFERRED")
    print("P12_5_RCV_6_HOST_BUILD=PASS")
    print("P12_5_RCV_6_HOST_EXECUTION=PASS")
    print("P12_5_RCV_6_DEDICATED_MANAGED_HOST_PROJECT_SKELETON=PASS")
    print("P12_5_RCV_6_NEXT=P12.5-RCV-7_HOST_LIFECYCLE_AND_STARTUP_CONTRACT")
    return 0
if __name__ == "__main__": raise SystemExit(main())
