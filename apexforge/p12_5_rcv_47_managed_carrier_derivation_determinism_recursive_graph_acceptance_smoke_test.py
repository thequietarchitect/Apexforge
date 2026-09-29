from __future__ import annotations

import base64
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APEX = ROOT / "apexforge"
sys.path.insert(0, str(APEX))

CONTRACT = APEX / "p12_5_rcv_47_managed_carrier_derivation_determinism_recursive_graph_acceptance.json"
RCV45 = APEX / "p12_5_rcv_45_managed_executable_carrier_decoder_negative_conformance.json"
RCV46 = APEX / "p12_5_rcv_46_canonical_air_transport_to_managed_carrier_derivation_bridge_acceptance.json"
RUNTIME = ROOT / "runtimes/dotnet/ApexForge.Runtime/ApexForge.Runtime.csproj"


def req(value, message):
    if not value:
        raise AssertionError(message)


def run(*args, cwd=ROOT):
    return subprocess.run(args, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def main() -> int:
    negative = json.loads(RCV45.read_text(encoding="utf-8-sig"))
    previous = json.loads(RCV46.read_text(encoding="utf-8-sig"))
    data = json.loads(CONTRACT.read_text(encoding="utf-8-sig"))
    req(negative["result"] == "PASS", "negative conformance changed")
    req(previous["profile"] == "apexforge.p12.canonical-air-transport-to-managed-carrier-derivation-bridge-acceptance/v1", "RCV-46 profile changed")
    req(data["predecessor"]["stage"] == "P12.5-RCV-46", "predecessor changed")

    from p12_5_rcv_44_managed_executable_carrier_decoder_positive_conformance_smoke_test import make_transport
    first, first_empty = make_transport()
    second, second_empty = make_transport()
    req(first.transport_json == second.transport_json, "canonical transport bytes are nondeterministic")
    req(first.transport_fingerprint == second.transport_fingerprint, "canonical fingerprint is nondeterministic")
    req(first_empty.transport_json == second_empty.transport_json, "empty canonical transport is nondeterministic")

    payload = base64.b64encode(first.transport_json.encode("utf-8")).decode("ascii")
    probe = r'''using System.Globalization;
using System.Numerics;
using System.Security.Cryptography;
using System.Text;
using ApexForge.Runtime;

var json = Encoding.UTF8.GetString(Convert.FromBase64String("__PAYLOAD__"));
var decoder = new ManagedExecutableCarrierDecoder();
var first = decoder.DecodeCanonicalAirTransport(json);
var second = decoder.DecodeCanonicalAirTransport(json);
var firstSignature = Fingerprint(first);
var secondSignature = Fingerprint(second);
if (!StringComparer.Ordinal.Equals(firstSignature, secondSignature)) return 10;
if (first.Count != 2 || second.Count != 2) return 11;
Console.WriteLine("RCV47_MANAGED_PROJECTION_SIGNATURE=" + firstSignature);
Console.WriteLine("RCV47_REPEATED_STRUCTURE_EQUAL=PASS");
Console.WriteLine("RCV47_RECURSIVE_GRAPH_ACCEPTANCE=PASS");
return 0;

static string Fingerprint(IReadOnlyList<ManagedExecutableFunction> functions)
{
    var summary = Join(functions, Function);
    return Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(summary)));
}

static string Function(ManagedExecutableFunction value) =>
    "fn(" + value.Id + "," + value.Name + "," + value.Order.ToString(CultureInfo.InvariantCulture)
    + ",p[" + Join(value.Parameters, Parameter) + "]"
    + ",r=" + (value.ReturnExpression is null ? "null" : Expression(value.ReturnExpression))
    + ",l[" + Join(value.LocalBindings, Statement) + "]"
    + ",b[" + Join(value.Body, Statement) + "]"
    + ",rt=" + (value.ReturnType is null ? "null" : GenericType(value.ReturnType))
    + ",tp[" + Join(value.TypeParameters, GenericType) + "])";

static string Parameter(ManagedFunctionParameter value) =>
    value.Name + ":" + (value.ValueType is null ? "null" : GenericType(value.ValueType));

static string Statement(ManagedFunctionStatement value) => value switch
{
    ManagedLocalBinding x => "let(" + x.Name + "," + Expression(x.Expression) + ")",
    ManagedFunctionReturn x => "return(" + Expression(x.Expression) + ")",
    ManagedFunctionWhen x => "when(" + Expression(x.Condition) + ",[" + Join(x.Actions, Statement) + "],[" + Join(x.OtherwiseActions, Statement) + "])",
    _ => throw new InvalidOperationException("unknown statement")
};

static string Expression(ManagedExecutableExpression value) => value switch
{
    ManagedIntegerLiteral x => "i(" + x.Value.ToString(CultureInfo.InvariantCulture) + ")",
    ManagedFloatLiteral x => "f(" + BitConverter.DoubleToInt64Bits(x.Value).ToString(CultureInfo.InvariantCulture) + ")",
    ManagedStringLiteral x => "s(" + x.Value.Length.ToString(CultureInfo.InvariantCulture) + ":" + x.Value + ")",
    ManagedBooleanLiteral x => x.Value ? "b(1)" : "b(0)",
    ManagedIdentifierReference x => "id(" + x.Name + ")",
    ManagedUnaryExpression x => "u(" + x.Operator + "," + Expression(x.Operand) + ")",
    ManagedBinaryExpression x => "bin(" + Expression(x.Left) + "," + x.Operator + "," + Expression(x.Right) + ")",
    ManagedCallExpression x => "call(" + x.Target + ",[" + Join(x.Arguments, Expression) + "],[" + Join(x.TypeArguments, GenericType) + "])",
    _ => throw new InvalidOperationException("unknown expression")
};

static string GenericType(ManagedGenericTypeLike value) => value switch
{
    ManagedNamedTypeReference x => "named(" + x.Name + ")",
    ManagedApexTypeReference x => "type(" + x.Name + ",[" + Join(x.Arguments, GenericType) + "])",
    ManagedTypeVariableReference x => "var(" + x.Name + "," + x.Owner + ",[" + Join(x.Constraints, Constraint) + "])",
    _ => throw new InvalidOperationException("unknown type")
};

static string Constraint(ManagedConstraintReference value) => value switch
{
    ManagedNamedConstraintReference x => "named(" + x.Name + ")",
    ManagedApexTypeConstraintReference x => "constraint(" + x.Name + "," + x.Description + ")",
    _ => throw new InvalidOperationException("unknown constraint")
};

static string Join<T>(IEnumerable<T> values, Func<T, string> render) =>
    string.Join("|", values.Select(render));
'''.replace("__PAYLOAD__", payload)

    with tempfile.TemporaryDirectory(prefix="apexforge-rcv47-") as raw:
        td = Path(raw)
        reference = str(RUNTIME).replace("\\", "/")
        (td / "Probe.csproj").write_text(
            '<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><OutputType>Exe</OutputType><TargetFramework>net10.0</TargetFramework><Nullable>enable</Nullable><ImplicitUsings>enable</ImplicitUsings><TreatWarningsAsErrors>true</TreatWarningsAsErrors></PropertyGroup><ItemGroup><ProjectReference Include="'
            + reference
            + '" /></ItemGroup></Project>', encoding="utf-8")
        (td / "Program.cs").write_text(probe, encoding="utf-8")
        result = run("dotnet", "run", "--project", str(td / "Probe.csproj"), "-c", "Release", "--nologo", cwd=td)
        req(result.returncode == 0, "determinism probe failed:\n" + result.stdout + result.stderr)
        lines = result.stdout.splitlines()
        req(lines[-1:] == ["RCV47_RECURSIVE_GRAPH_ACCEPTANCE=PASS"], "determinism probe output changed:\n" + result.stdout)
        signature_line = next((line for line in lines if line.startswith("RCV47_MANAGED_PROJECTION_SIGNATURE=")), None)
        req(signature_line is not None and len(signature_line.rsplit("=", 1)[1]) == 64, "managed test signature missing")

    req(all(data["determinism"].values()), "determinism condition missing")
    req(data["fingerprints"]["production_managed_carrier_fingerprint_added"] is False, "production fingerprint invented")
    print(f"P12_5_RCV_47_CANONICAL_TRANSPORT_FINGERPRINT={first.transport_fingerprint}")
    print(signature_line)
    print("P12_5_RCV_47_DERIVATION_DETERMINISM=PASS")
    print("P12_5_RCV_47_RECURSIVE_GRAPH_ACCEPTANCE=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
