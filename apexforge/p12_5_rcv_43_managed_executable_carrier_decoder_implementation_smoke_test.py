from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "apexforge/p12_5_rcv_43_managed_executable_carrier_decoder_implementation.json"
RCV42 = ROOT / "apexforge/p12_5_rcv_42_managed_executable_carrier_structural_ambiguity_census.json"
DECODER = ROOT / "runtimes/dotnet/ApexForge.Runtime/ManagedExecutableCarrierDecoder.cs"
RUNTIME = ROOT / "runtimes/dotnet/ApexForge.Runtime/ApexForge.Runtime.csproj"
CARRIER = ROOT / "runtimes/dotnet/ApexForge.Runtime/ManagedExecutableCarrier.cs"


def req(value, message):
    if not value:
        raise AssertionError(message)


def run(*args, cwd=ROOT):
    return subprocess.run(args, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def main() -> int:
    previous = json.loads(RCV42.read_text(encoding="utf-8-sig"))
    data = json.loads(CONTRACT.read_text(encoding="utf-8-sig"))
    req(previous["dispatch"]["unresolved_collision_count"] == 0, "RCV-42 collision census changed")
    req(data["predecessor"]["stage"] == "P12.5-RCV-42", "predecessor changed")
    req(DECODER.exists(), "decoder production source missing")
    source = DECODER.read_text(encoding="utf-8-sig")
    req("public sealed class ManagedExecutableCarrierDecoder" in source, "decoder type missing")
    req("DecodeCanonicalAirTransport" in source, "decoder public method missing")
    req("JsonDocument.Parse" in source and "JsonElement" in source, "selected DOM implementation missing")
    req("JsonSerializer.Deserialize" not in source, "polymorphic/direct serializer binding introduced")
    req("Utf8JsonReader" not in source, "unselected reader architecture introduced")
    for token in ("HttpClient", "TcpClient", "NamedPipe", "Console.In", "File.Read"):
        req(token not in source, f"unauthorized transport token entered decoder: {token}")
    impl = data["implementation"]
    req(impl["closed_world"] is True, "closed-world implementation flag changed")
    req(impl["project_file_change_required"] is False, "project file change unexpectedly required")
    req(impl["existing_carrier_file_changed"] is False, "carrier change unexpectedly authorized")

    build = run("dotnet", "build", str(RUNTIME), "-c", "Release", "--nologo")
    req(build.returncode == 0, "runtime build failed:\n" + build.stdout + build.stderr)

    probe = '''using ApexForge.Runtime;
var json = "{\\\"authorities\\\":[],\\\"authority_checks\\\":[],\\\"causal_decisions\\\":[],\\\"directives\\\":[],\\\"events\\\":[],\\\"functions\\\":[],\\\"principals\\\":[],\\\"requirements\\\":[],\\\"roles\\\":[],\\\"states\\\":[],\\\"version\\\":\\\"rcv43\\\"}";
var decoder = new ManagedExecutableCarrierDecoder();
if (decoder.DecodeCanonicalAirTransport(json).Count != 0) return 10;
try { decoder.DecodeCanonicalAirTransport(null!); return 11; }
catch (ArgumentNullException) { }
Console.WriteLine("RCV43_EMPTY_CANONICAL_DOCUMENT=PASS");
Console.WriteLine("RCV43_NULL_REJECTION=PASS");
Console.WriteLine("RCV43_DECODER_IMPLEMENTATION=PASS");
return 0;
'''
    with tempfile.TemporaryDirectory(prefix="apexforge-rcv43-") as raw:
        td = Path(raw)
        reference = str(RUNTIME).replace("\\", "/")
        (td / "Probe.csproj").write_text(
            '<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><OutputType>Exe</OutputType><TargetFramework>net10.0</TargetFramework><Nullable>enable</Nullable><ImplicitUsings>enable</ImplicitUsings><TreatWarningsAsErrors>true</TreatWarningsAsErrors></PropertyGroup><ItemGroup><ProjectReference Include="'
            + reference
            + '" /></ItemGroup></Project>',
            encoding="utf-8",
        )
        (td / "Program.cs").write_text(probe, encoding="utf-8")
        result = run("dotnet", "run", "--project", str(td / "Probe.csproj"), "-c", "Release", "--nologo", cwd=td)
        req(result.returncode == 0, "decoder probe failed:\n" + result.stdout + result.stderr)
        req(result.stdout.splitlines() == [
            "RCV43_EMPTY_CANONICAL_DOCUMENT=PASS",
            "RCV43_NULL_REJECTION=PASS",
            "RCV43_DECODER_IMPLEMENTATION=PASS",
        ], "decoder probe output changed:\n" + result.stdout)

    req(data["authority"]["language_semantics"] == "CANONICAL_AIR", "semantic authority changed")
    req(data["boundary"]["external_transport_added"] is False, "external transport added")
    req(data["boundary"]["execution_dispatch"] == "DEFERRED", "execution dispatch selected")
    req(CARRIER.exists(), "carrier source missing")
    print("P12_5_RCV_43_RUNTIME_BUILD=PASS")
    print("P12_5_RCV_43_DECODER_ARCHITECTURE=SYSTEM_TEXT_JSON_DOM")
    print("P12_5_RCV_43_CLOSED_WORLD=True")
    print("P12_5_RCV_43_NO_SECOND_SEMANTIC_IMPLEMENTATION=True")
    print("P12_5_RCV_43_DECODER_IMPLEMENTATION=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
