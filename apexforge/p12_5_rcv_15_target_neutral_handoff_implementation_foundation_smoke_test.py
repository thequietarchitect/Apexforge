from __future__ import annotations
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "apexforge/p12_5_rcv_15_target_neutral_handoff_implementation_foundation.json"
RCV14 = ROOT / "apexforge/p12_5_rcv_14_historical_managed_type_selection_confirmation.json"
HANDOFF = ROOT / "runtimes/dotnet/ApexForge.Runtime/TargetNeutralLoweringHandoff.cs"
HOST = ROOT / "runtimes/dotnet/ApexForge.Runtime/ManagedRuntimeHost.cs"
RUNTIME_PROJ = ROOT / "runtimes/dotnet/ApexForge.Runtime/ApexForge.Runtime.csproj"
PROBE_CS = 'using ApexForge.Runtime;\n\nstatic void ExpectInvalid(Action action)\n{\n    try\n    {\n        action();\n        throw new Exception("Expected validation failure.");\n    }\n    catch (InvalidOperationException)\n    {\n    }\n}\n\nvar lower = new string(\'a\', 64);\nvar upper = new string(\'A\', 64);\nvar valid = new TargetNeutralLoweringHandoff(\n    TargetNeutralLoweringHandoff.RequiredSchema,\n    lower,\n    lower,\n    "entry",\n    new[] { "owner-a", "owner-b" },\n    upper);\n\nvalid.Validate();\nvar host = new ManagedRuntimeHost();\nvar admitted = host.AdmitTargetNeutralHandoff(valid);\nif (!ReferenceEquals(valid, admitted))\n{\n    throw new Exception("Admission did not return the same handoff instance.");\n}\n\nExpectInvalid(() => (valid with { Schema = "wrong" }).Validate());\nExpectInvalid(() => (valid with { ProductFingerprint = lower }).Validate());\nExpectInvalid(() => (valid with { EntryDirective = " " }).Validate());\nExpectInvalid(() => (valid with { DirectiveOwnerIds = new[] { "owner-a", "" } }).Validate());\n\nConsole.WriteLine("RCV15_PROBE_VALID=PASS");\nConsole.WriteLine("RCV15_PROBE_INVALID_REJECTION=PASS");\nConsole.WriteLine("RCV15_PROBE_VALIDATE_AND_RETURN=PASS");\n'

def req(c, m):
    if not c:
        raise AssertionError(m)

def run(*args, cwd=ROOT):
    return subprocess.run(list(args), cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def main():
    print("=== P12.5-RCV-15 TARGET-NEUTRAL HANDOFF IMPLEMENTATION FOUNDATION ===")
    for p in (CONTRACT, RCV14, HANDOFF, HOST, RUNTIME_PROJ):
        req(p.exists(), f"missing required file: {p}")

    prev = json.loads(RCV14.read_text(encoding="utf-8-sig"))
    req(prev["profile"] == "apexforge.p12.historical-managed-type-selection-confirmation/v1", "RCV-14 profile changed")
    req(prev["stage"] == "P12.5-RCV-14", "RCV-14 stage changed")
    print("P12_5_RCV_15_RCV14_CONTRACT=PASS")

    data = json.loads(CONTRACT.read_text(encoding="utf-8-sig"))
    req(data["profile"] == "apexforge.p12.target-neutral-handoff-implementation-foundation/v1", "profile changed")
    req(data["predecessor"]["stage"] == "P12.5-RCV-14", "predecessor changed")
    req(data["implementation"]["required_schema"] == "apexforge.target-neutral-lowering/v1", "required schema changed")
    req(data["implementation"]["admission_behavior"] == "ARGUMENT_NOT_NULL_THEN_VALIDATE_AND_RETURN", "admission behavior changed")

    handoff = HANDOFF.read_text(encoding="utf-8-sig")
    host = HOST.read_text(encoding="utf-8-sig")

    for token in (
        "public sealed record TargetNeutralLoweringHandoff(",
        "string Schema,",
        "string VerifiedAirFingerprint,",
        "string RoutingFingerprint,",
        "string EntryDirective,",
        "IReadOnlyList<string> DirectiveOwnerIds,",
        "string ProductFingerprint)",
        'public const string RequiredSchema = "apexforge.target-neutral-lowering/v1";',
        "public void Validate()",
        "StringComparison.Ordinal",
        'ValidateFingerprint(VerifiedAirFingerprint, "Verified AIR", requireUppercase: false);',
        'ValidateFingerprint(RoutingFingerprint, "Routing", requireUppercase: false);',
        'ValidateFingerprint(ProductFingerprint, "Product", requireUppercase: true);',
        "foreach (var ownerId in DirectiveOwnerIds)",
    ):
        req(token in handoff, f"historical handoff token missing: {token}")

    for token in (
        "public TargetNeutralLoweringHandoff AdmitTargetNeutralHandoff(TargetNeutralLoweringHandoff handoff)",
        "ArgumentNullException.ThrowIfNull(handoff);",
        "handoff.Validate();",
        "return handoff;",
    ):
        req(token in host, f"host admission token missing: {token}")

    for token in ("JsonSerializer", "ManagedExecutableCarrier", "ManagedNativeAbi.", "TcpListener", "HttpListener", "NamedPipeServerStream"):
        req(token not in handoff, f"premature concern in handoff: {token}")

    with tempfile.TemporaryDirectory(prefix="apexforge-rcv15-") as td_raw:
        td = Path(td_raw)
        csproj = td / "Rcv15Probe.csproj"
        program = td / "Program.cs"
        include = str(RUNTIME_PROJ).replace("\\", "/")
        csproj_text = '<Project Sdk="Microsoft.NET.Sdk">\n  <PropertyGroup>\n    <OutputType>Exe</OutputType>\n    <TargetFramework>net10.0</TargetFramework>\n    <Nullable>enable</Nullable>\n    <ImplicitUsings>enable</ImplicitUsings>\n    <TreatWarningsAsErrors>true</TreatWarningsAsErrors>\n  </PropertyGroup>\n  <ItemGroup>\n    <ProjectReference Include="' + include + '" />\n  </ItemGroup>\n</Project>\n'
        csproj.write_text(csproj_text, encoding="utf-8")
        program.write_text(PROBE_CS, encoding="utf-8")
        cp = run("dotnet", "run", "--project", str(csproj), "-c", "Release", "--nologo", cwd=td)
        req(cp.returncode == 0, "RCV-15 managed probe failed:\n" + cp.stdout + "\n" + cp.stderr)
        req("RCV15_PROBE_VALID=PASS" in cp.stdout, "valid handoff probe missing")
        req("RCV15_PROBE_INVALID_REJECTION=PASS" in cp.stdout, "invalid rejection probe missing")
        req("RCV15_PROBE_VALIDATE_AND_RETURN=PASS" in cp.stdout, "admission probe missing")

    auth = data["authority"]
    req(auth["language_semantics"] == "CANONICAL_AIR", "semantic authority changed")
    req(auth["handoff_defines_language_semantics"] is False, "handoff gained semantic authority")
    req(auth["handoff_executes"] is False, "handoff gained execution authority")
    req(auth["handoff_lowers"] is False, "handoff gained lowering authority")
    req(auth["managed_runtime_host_executes_on_admission"] is False, "admission gained execution behavior")

    print("P12_5_RCV_15_PROFILE=apexforge.p12.target-neutral-handoff-implementation-foundation/v1")
    print("P12_5_RCV_15_HANDOFF_IMPLEMENTATION=PASS")
    print("P12_5_RCV_15_HOST_ADMISSION_IMPLEMENTATION=PASS")
    print("P12_5_RCV_15_RUNTIME_BUILD_AND_BEHAVIOR=PASS")
    print("P12_5_RCV_15_REQUIRED_SCHEMA=apexforge.target-neutral-lowering/v1")
    print("P12_5_RCV_15_LANGUAGE_SEMANTIC_AUTHORITY=CANONICAL_AIR")
    print("P12_5_RCV_15_EXTERNAL_SERIALIZATION=DEFERRED")
    print("P12_5_RCV_15_EXECUTION_DISPATCH=DEFERRED")
    print("P12_5_RCV_15_TARGET_NEUTRAL_HANDOFF_IMPLEMENTATION_FOUNDATION=PASS")
    print("P12_5_RCV_15_NEXT=P12.5-RCV-16_TARGET_NEUTRAL_HANDOFF_PROJECTION_BRIDGE_CENSUS")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
