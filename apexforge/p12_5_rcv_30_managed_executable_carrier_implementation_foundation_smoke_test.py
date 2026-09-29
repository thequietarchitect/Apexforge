from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "apexforge/p12_5_rcv_30_managed_executable_carrier_implementation_foundation.json"
RCV29_CONTRACT = ROOT / "apexforge/p12_5_rcv_29_managed_executable_carrier_corrected_type_shape_contract.json"
CARRIER = ROOT / "runtimes/dotnet/ApexForge.Runtime/ManagedExecutableCarrier.cs"
RUNTIME_PROJ = ROOT / "runtimes/dotnet/ApexForge.Runtime/ApexForge.Runtime.csproj"
PROBE_CS = 'using System;\nusing System.Numerics;\nusing ApexForge.Runtime;\n\nvar huge = BigInteger.Parse("170141183460469231731687303715884105728");\nvar integer = new ManagedIntegerLiteral(huge);\nif (integer.Value != huge) return 10;\n\nvar negativeZero = new ManagedFloatLiteral(-0.0d);\nif (BitConverter.DoubleToInt64Bits(negativeZero.Value) != long.MinValue) return 11;\nif (!double.IsNaN(new ManagedFloatLiteral(double.NaN).Value)) return 12;\nif (!double.IsPositiveInfinity(new ManagedFloatLiteral(double.PositiveInfinity).Value)) return 13;\nif (!double.IsNegativeInfinity(new ManagedFloatLiteral(double.NegativeInfinity).Value)) return 14;\n\nvar text = new ManagedStringLiteral("A😀𐐷");\nif (text.Value != "A😀𐐷") return 15;\nif (text.Value.Length != 5) return 16;\n\nvar boolean = new ManagedBooleanLiteral(true);\nif (!boolean.Value) return 17;\n\nvar named = new ManagedNamedTypeReference("Number");\nvar apex = new ManagedApexTypeReference(\n    "Vector",\n    new[] { new ManagedApexTypeReference("Scalar", Array.Empty<ManagedApexTypeReference>()) });\nvar constraint = new ManagedApexTypeConstraintReference("Numeric", "numeric constraint");\nvar variable = new ManagedTypeVariableReference(\n    "T",\n    "Helper",\n    new ManagedConstraintReference[] { constraint, new ManagedNamedConstraintReference("Comparable") });\n\nManagedGenericTypeLike genericNamed = named;\nManagedGenericTypeLike genericApex = apex;\nManagedGenericTypeLike genericVariable = variable;\nManagedTypeLike typeNamed = named;\nManagedTypeLike typeApex = apex;\nManagedTypeIdentity identityApex = apex;\nManagedTypeIdentity identityVariable = variable;\nif (genericNamed is null || genericApex is null || genericVariable is null ||\n    typeNamed is null || typeApex is null || identityApex is null || identityVariable is null)\n{\n    return 18;\n}\n\nvar identifier = new ManagedIdentifierReference("x");\nvar unary = new ManagedUnaryExpression("-", integer);\nvar binary = new ManagedBinaryExpression(integer, "+", new ManagedIntegerLiteral(BigInteger.One));\nvar call = new ManagedCallExpression(\n    "Helper",\n    new ManagedExecutableExpression[] { identifier, unary, binary, text, boolean },\n    new ManagedGenericTypeLike[] { named, apex, variable });\n\nvar parameter = new ManagedFunctionParameter("x", named);\nvar local = new ManagedLocalBinding("y", call);\nvar returned = new ManagedFunctionReturn(identifier);\nvar when = new ManagedFunctionWhen(\n    boolean,\n    new ManagedFunctionStatement[] { local, returned },\n    Array.Empty<ManagedFunctionStatement>());\nvar function = new ManagedExecutableFunction(\n    "fn-1",\n    "Helper",\n    new[] { parameter },\n    identifier,\n    0,\n    new[] { local },\n    new ManagedFunctionStatement[] { when },\n    variable,\n    new[] { variable });\n\nif (call.Arguments.Count != 5 || call.TypeArguments.Count != 3) return 19;\nif (variable.Constraints.Count != 2) return 20;\nif (function.Id != "fn-1" ||\n    function.Parameters.Count != 1 ||\n    function.LocalBindings.Count != 1 ||\n    function.Body.Count != 1 ||\n    function.TypeParameters.Count != 1)\n{\n    return 21;\n}\n\nConsole.WriteLine("RCV30_BIG_INTEGER_EXACT=PASS");\nConsole.WriteLine("RCV30_BINARY64_SPECIAL_VALUES=PASS");\nConsole.WriteLine("RCV30_STRING_STORAGE=PASS");\nConsole.WriteLine("RCV30_TYPE_GRAPH=PASS");\nConsole.WriteLine("RCV30_FUNCTION_GRAPH=PASS");\nConsole.WriteLine("RCV30_MANAGED_EXECUTABLE_CARRIER_IMPLEMENTATION_FOUNDATION=PASS");\nreturn 0;\n'

EXPECTED_NAMES = [
    "ManagedExecutableExpression",
    "ManagedIntegerLiteral",
    "ManagedFloatLiteral",
    "ManagedStringLiteral",
    "ManagedBooleanLiteral",
    "ManagedIdentifierReference",
    "ManagedUnaryExpression",
    "ManagedBinaryExpression",
    "ManagedCallExpression",
    "ManagedTypeReference",
    "ManagedGenericTypeLike",
    "ManagedTypeLike",
    "ManagedTypeIdentity",
    "ManagedNamedTypeReference",
    "ManagedApexTypeReference",
    "ManagedTypeVariableReference",
    "ManagedConstraintReference",
    "ManagedNamedConstraintReference",
    "ManagedApexTypeConstraintReference",
    "ManagedFunctionParameter",
    "ManagedFunctionStatement",
    "ManagedLocalBinding",
    "ManagedFunctionReturn",
    "ManagedFunctionWhen",
    "ManagedExecutableFunction",
]

def req(c, m):
    if not c:
        raise AssertionError(m)

def run(*args, cwd=ROOT):
    return subprocess.run(list(args), cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def main():
    print("=== P12.5-RCV-30 MANAGED EXECUTABLE CARRIER IMPLEMENTATION FOUNDATION ===")
    for p in (CONTRACT, RCV29_CONTRACT, CARRIER, RUNTIME_PROJ):
        req(p.exists(), f"missing required file: {p}")

    prev = json.loads(RCV29_CONTRACT.read_text(encoding="utf-8-sig"))
    req(prev["profile"] == "apexforge.p12.managed-executable-carrier-corrected-type-shape-contract/v1", "RCV-29 profile changed")
    req(prev["stage"] == "P12.5-RCV-29", "RCV-29 stage changed")
    req(prev["implementation"] == "DEFERRED", "RCV-29 implementation state changed")
    print("P12_5_RCV_30_RCV29_CONTRACT=PASS")

    data = json.loads(CONTRACT.read_text(encoding="utf-8-sig"))
    req(data["profile"] == "apexforge.p12.managed-executable-carrier-implementation-foundation/v1", "profile changed")
    req(data["predecessor"]["stage"] == "P12.5-RCV-29", "predecessor changed")

    source = CARRIER.read_text(encoding="utf-8-sig")
    req("IjeadOnlyList" not in source, "R1 collection transcription defect reintroduced")
    req("ManagedUnharyExpression" not in source, "R1 unary transcription defect reintroduced")
    req("IReadOnlyList<ManagedGenericTypeLike> TypeArguments" in source, "corrected TypeArguments shape missing")
    req("IReadOnlyList<ManagedConstraintReference> Constraints" in source, "corrected Constraints shape missing")
    req("public sealed record ManagedUnaryExpression(" in source, "ManagedUnaryExpression missing")

    names = re.findall(r"public\s+(?:abstract\s+record|sealed\s+record|interface)\s+([A-Za-z_][A-Za-z0-9_]*)", source)
    req(names == EXPECTED_NAMES, f"carrier declaration set/order changed: {names}")

    for token in data["forbidden_concerns"]:
        req(token not in source, f"deferred concern entered carrier: {token}")

    impl = data["implementation"]
    req(impl["path"] == "runtimes/dotnet/ApexForge.Runtime/ManagedExecutableCarrier.cs", "carrier path changed")
    req(impl["owner_project"] == "ApexForge.Runtime", "carrier owner changed")
    req(impl["declaration_count"] == 25, "declaration count changed")
    req(impl["corrected_from_r1_transcription_defects"] is True, "correction classification lost")
    req(impl["historical_identity_claim"] is False, "historical identity improperly claimed")
    req(impl["data_carrier_only"] is True, "carrier role widened")

    build = run("dotnet", "build", str(RUNTIME_PROJ), "-c", "Release", "--nologo")
    req(build.returncode == 0, "managed runtime build failed:\n" + build.stdout + "\n" + build.stderr)
    print("P12_5_RCV_30_RUNTIME_BUILD=PASS")

    with tempfile.TemporaryDirectory(prefix="apexforge-rcv30-") as td_raw:
        td = Path(td_raw)
        include = str(RUNTIME_PROJ).replace("\\", "/")
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
        with (td / "Rcv30Probe.csproj").open("w", encoding="utf-8") as f:
            f.write(csproj)
        with (td / "Program.cs").open("w", encoding="utf-8") as f:
            f.write(PROBE_CS)
        probe = run("dotnet", "run", "--project", str(td / "Rcv30Probe.csproj"), "-c", "Release", "--nologo", cwd=td)
        req(probe.returncode == 0, "carrier behavior probe failed:\n" + probe.stdout + "\n" + probe.stderr)
        expected = [
            "RCV30_BIG_INTEGER_EXACT=PASS",
            "RCV30_BINARY64_SPECIAL_VALUES=PASS",
            "RCV30_STRING_STORAGE=PASS",
            "RCV30_TYPE_GRAPH=PASS",
            "RCV30_FUNCTION_GRAPH=PASS",
            "RCV30_MANAGED_EXECUTABLE_CARRIER_IMPLEMENTATION_FOUNDATION=PASS",
        ]
        req(probe.stdout.splitlines() == expected, "carrier behavior output changed:\n" + probe.stdout)

    auth = data["authority"]
    req(auth["language_semantics"] == "CANONICAL_AIR", "semantic authority changed")
    for key in (
        "carrier_defines_language_semantics",
        "carrier_executes",
        "carrier_dispatches",
        "carrier_serializes",
        "carrier_owns_native_abi",
        "carrier_admits_handoffs",
    ):
        req(auth[key] is False, f"carrier authority widened: {key}")

    print("P12_5_RCV_30_PROFILE=apexforge.p12.managed-executable-carrier-implementation-foundation/v1")
    print("P12_5_RCV_30_DECLARATION_COUNT=25")
    print("P12_5_RCV_30_TRANSCRIPTION_CORRECTIONS=PASS")
    print("P12_5_RCV_30_BIG_INTEGER_EXACT=PASS")
    print("P12_5_RCV_30_BINARY64_SPECIAL_VALUES=PASS")
    print("P12_5_RCV_30_STRING_STORAGE=PASS")
    print("P12_5_RCV_30_TYPE_GRAPH=PASS")
    print("P12_5_RCV_30_FUNCTION_GRAPH=PASS")
    print("P12_5_RCV_30_LANGUAGE_SEMANTIC_AUTHORITY=CANONICAL_AIR")
    print("P12_5_RCV_30_EXTERNAL_SERIALIZATION=UNSELECTED")
    print("P12_5_RCV_30_CROSS_RUNTIME_TRANSPORT=DEFERRED_NO_TRANSPORT_AUTHORIZED")
    print("P12_5_RCV_30_EXECUTION_DISPATCH=DEFERRED")
    print("P12_5_RCV_30_HISTORICAL_IDENTITY_CLAIM=False")
    print("P12_5_RCV_30_MANAGED_EXECUTABLE_CARRIER_IMPLEMENTATION_FOUNDATION=PASS")
    print("P12_5_RCV_30_NEXT=P12.5-RCV-31_MANAGED_EXECUTABLE_CARRIER_DERIVATION_BOUNDARY_CENSUS")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
