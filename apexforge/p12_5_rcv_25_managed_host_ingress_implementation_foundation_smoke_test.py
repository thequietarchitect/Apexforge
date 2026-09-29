from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "apexforge/p12_5_rcv_25_managed_host_ingress_implementation_foundation.json"
RCV24_CONTRACT = ROOT / "apexforge/p12_5_rcv_24_managed_host_ingress_implementation_contract.json"
INGRESS = ROOT / "runtimes/dotnet/ApexForge.Runtime.Host/RuntimeHostIngress.cs"
HOST_PROJ = ROOT / "runtimes/dotnet/ApexForge.Runtime.Host/ApexForge.Runtime.Host.csproj"
HOST_PROGRAM = ROOT / "runtimes/dotnet/ApexForge.Runtime.Host/Program.cs"
HOST_LIFECYCLE = ROOT / "runtimes/dotnet/ApexForge.Runtime.Host/RuntimeHostLifecycle.cs"
MANAGED_HOST = ROOT / "runtimes/dotnet/ApexForge.Runtime/ManagedRuntimeHost.cs"
HANDOFF = ROOT / "runtimes/dotnet/ApexForge.Runtime/TargetNeutralLoweringHandoff.cs"
PROBE_CS = 'using ApexForge.Runtime;\nusing ApexForge.Runtime.Host;\n\nvar runtime = new ManagedRuntimeHost();\nvar ingress = new RuntimeHostIngress(runtime);\n\nvar valid = new TargetNeutralLoweringHandoff(\n    "apexforge.target-neutral-lowering/v1",\n    new string(\'a\', 64),\n    new string(\'b\', 64),\n    "entry-main",\n    new[] { "owner-a", "owner-b" },\n    new string(\'C\', 64));\n\nvar admitted = ingress.Admit(valid);\nif (!ReferenceEquals(valid, admitted))\n{\n    throw new Exception("ingress did not return the managed admission result unchanged");\n}\n\nvar nullCtorRejected = false;\ntry\n{\n    _ = new RuntimeHostIngress(null!);\n}\ncatch (ArgumentNullException)\n{\n    nullCtorRejected = true;\n}\n\nif (!nullCtorRejected)\n{\n    throw new Exception("null runtime dependency was accepted");\n}\n\nvar invalidRejected = false;\ntry\n{\n    ingress.Admit(valid with { Schema = "wrong" });\n}\ncatch (InvalidOperationException)\n{\n    invalidRejected = true;\n}\n\nif (!invalidRejected)\n{\n    throw new Exception("ingress bypassed managed handoff validation");\n}\n\nConsole.WriteLine("RCV25_INGRESS_DELEGATION=PASS");\nConsole.WriteLine("RCV25_CONSTRUCTOR_NULL_GUARD=PASS");\nConsole.WriteLine("RCV25_MANAGED_VALIDATION_PROPAGATION=PASS");\n'

def req(c, m):
    if not c:
        raise AssertionError(m)

def run(*args, cwd=ROOT):
    return subprocess.run(list(args), cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def main():
    print("=== P12.5-RCV-25 MANAGED HOST INGRESS IMPLEMENTATION FOUNDATION ===")
    for p in (CONTRACT, RCV24_CONTRACT, INGRESS, HOST_PROJ, HOST_PROGRAM, HOST_LIFECYCLE, MANAGED_HOST, HANDOFF):
        req(p.exists(), f"missing required file: {p}")

    prev = json.loads(RCV24_CONTRACT.read_text(encoding="utf-8-sig"))
    req(prev["profile"] == "apexforge.p12.managed-host-ingress-implementation-contract/v1", "RCV-24 profile changed")
    req(prev["stage"] == "P12.5-RCV-24", "RCV-24 stage changed")
    req(prev["decision"]["type"] == "ApexForge.Runtime.Host.RuntimeHostIngress", "RCV-24 ingress type changed")
    req(prev["decision"]["method"] == "Admit", "RCV-24 method changed")
    req(prev["decision"]["duplicates_validation"] is False, "RCV-24 validation ownership changed")
    print("P12_5_RCV_25_RCV24_CONTRACT=PASS")

    data = json.loads(CONTRACT.read_text(encoding="utf-8-sig"))
    req(data["profile"] == "apexforge.p12.managed-host-ingress-implementation-foundation/v1", "profile changed")
    req(data["predecessor"]["stage"] == "P12.5-RCV-24", "predecessor changed")

    src = INGRESS.read_text(encoding="utf-8-sig")
    required = (
        "public sealed class RuntimeHostIngress",
        "private readonly ManagedRuntimeHost _runtimeHost;",
        "public RuntimeHostIngress(ManagedRuntimeHost runtimeHost)",
        "ArgumentNullException.ThrowIfNull(runtimeHost);",
        "_runtimeHost = runtimeHost;",
        "public TargetNeutralLoweringHandoff Admit(TargetNeutralLoweringHandoff handoff)",
        "return _runtimeHost.AdmitTargetNeutralHandoff(handoff);",
    )
    for token in required:
        req(token in src, f"required ingress implementation token missing: {token}")

    forbidden = (
        "handoff.Validate()",
        "JsonSerializer",
        "Console.ReadLine",
        "Console.In",
        "File.Read",
        "FileStream",
        "NamedPipe",
        "TcpListener",
        "TcpClient",
        "HttpListener",
        "HttpClient",
        "ProcessStartInfo",
        "Python.Runtime",
        "ManagedNativeAbi",
        "RuntimeHostLifecycle",
        "ManagedExecutableCarrier",
    )
    for token in forbidden:
        req(token not in src, f"premature/duplicate ingress behavior found: {token}")

    impl = data["implementation"]
    req(impl["representation"] == "SEALED_IN_PROCESS_ADAPTER", "representation changed")
    req(impl["constructor_dependency"] == "ApexForge.Runtime.ManagedRuntimeHost", "dependency changed")
    req(impl["method"] == "Admit", "method changed")
    req(impl["delegates_to"] == "ManagedRuntimeHost.AdmitTargetNeutralHandoff", "delegate target changed")
    req(impl["duplicates_validation"] is False, "duplicate validation selected")
    req(impl["lifecycle_coupling"] == "NONE", "lifecycle coupling introduced")
    req(impl["historical_identity_claim"] is False, "historical identity improperly claimed")

    build = run("dotnet", "build", str(HOST_PROJ), "-c", "Release", "--nologo")
    req(build.returncode == 0, "host project build failed:\n" + build.stdout + "\n" + build.stderr)
    print("P12_5_RCV_25_HOST_BUILD=PASS")

    with tempfile.TemporaryDirectory(prefix="apexforge-rcv25-") as td_raw:
        td = Path(td_raw)
        include = str(HOST_PROJ).replace("\\", "/")
        csproj = (
            '<Project Sdk="Microsoft.NET.Sdk">\n'
            '  <PropertyGroup>\n'
            '    <OutputType>Exe</OutputType>\n'
            '    <TargetFramework>net10.0</TargetFramework>\n'
            '    <Nullable>enable</Nullable>\n'
            '    <ImplicitUsings>enable</ImplicitUsings>\n'
            '    <TreatWarningsAsErrors>true</TreatWarningsAsErrors>\n'
            '  </PropertyGroup>\n'
            '  <ItemGroup>\n'
            '    <ProjectReference Include="' + include + '" />\n'
            '  </ItemGroup>\n'
            '</Project>\n'
        )
        with (td / "Rcv25Probe.csproj").open("w", encoding="utf-8") as f:
            f.write(csproj)
        with (td / "Program.cs").open("w", encoding="utf-8") as f:
            f.write(PROBE_CS)

        probe = run("dotnet", "run", "--project", str(td / "Rcv25Probe.csproj"), "-c", "Release", "--nologo", cwd=td)
        req(probe.returncode == 0, "RCV-25 behavior probe failed:\n" + probe.stdout + "\n" + probe.stderr)
        for marker in (
            "RCV25_INGRESS_DELEGATION=PASS",
            "RCV25_CONSTRUCTOR_NULL_GUARD=PASS",
            "RCV25_MANAGED_VALIDATION_PROPAGATION=PASS",
        ):
            req(marker in probe.stdout, f"behavior marker missing: {marker}")

    auth = data["authority"]
    req(auth["language_semantics"] == "CANONICAL_AIR", "semantic authority changed")
    req(auth["validation_owner"] == "ApexForge.Runtime.ManagedRuntimeHost", "validation owner changed")
    req(auth["ingress_owner"] == "ApexForge.Runtime.Host", "ingress owner changed")
    for key in (
        "ingress_defines_language_semantics",
        "ingress_executes",
        "ingress_lowers",
        "ingress_reinterprets",
        "ingress_serializes",
        "ingress_selects_transport",
        "ingress_calls_native_abi",
    ):
        req(auth[key] is False, f"ingress authority widened: {key}")

    print("P12_5_RCV_25_PROFILE=apexforge.p12.managed-host-ingress-implementation-foundation/v1")
    print("P12_5_RCV_25_INGRESS_IMPLEMENTATION=PASS")
    print("P12_5_RCV_25_INGRESS_DELEGATION=PASS")
    print("P12_5_RCV_25_CONSTRUCTOR_NULL_GUARD=PASS")
    print("P12_5_RCV_25_MANAGED_VALIDATION_PROPAGATION=PASS")
    print("P12_5_RCV_25_DUPLICATES_VALIDATION=False")
    print("P12_5_RCV_25_LIFECYCLE_COUPLING=NONE")
    print("P12_5_RCV_25_EXTERNAL_SERIALIZATION=UNSELECTED")
    print("P12_5_RCV_25_CROSS_RUNTIME_TRANSPORT=DEFERRED_NO_TRANSPORT_AUTHORIZED")
    print("P12_5_RCV_25_EXECUTION_DISPATCH=DEFERRED")
    print("P12_5_RCV_25_HISTORICAL_IDENTITY_CLAIM=False")
    print("P12_5_RCV_25_MANAGED_HOST_INGRESS_IMPLEMENTATION_FOUNDATION=PASS")
    print("P12_5_RCV_25_NEXT=P12.5-RCV-26_MANAGED_HOST_INGRESS_INTEGRATION_CENSUS")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
