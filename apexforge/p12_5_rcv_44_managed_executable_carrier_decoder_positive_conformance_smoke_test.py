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

CONTRACT = APEX / "p12_5_rcv_44_managed_executable_carrier_decoder_positive_conformance.json"
RCV43 = APEX / "p12_5_rcv_43_managed_executable_carrier_decoder_implementation.json"
RUNTIME = ROOT / "runtimes/dotnet/ApexForge.Runtime/ApexForge.Runtime.csproj"


def req(value, message):
    if not value:
        raise AssertionError(message)


def run(*args, cwd=ROOT):
    return subprocess.run(args, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def make_transport():
    from air.expressions import (
        AIRBinaryExpression,
        AIRBooleanLiteral,
        AIRCallExpression,
        AIRFloatLiteral,
        AIRIdentifierReference,
        AIRIntegerLiteral,
        AIRStringLiteral,
        AIRUnaryExpression,
    )
    from air.functions import (
        AIRFunction,
        AIRFunctionReturn,
        AIRFunctionWhen,
        AIRLocalBinding,
        AIRParameter,
    )
    from air.model import (
        AIRProgram,
        AIRWorkflow,
        AIRWorkflowInvocation,
        VerifiedAIRProgram,
    )
    from native_backend.lowering_input import build_verified_air_lowering_input
    from type_system.constraints import NUMERIC
    from type_system.generics import ApexTypeVariable
    from type_system.model import INT

    huge = 170141183460469231731687303715884105728
    variable = ApexTypeVariable("T", "Helper", (NUMERIC,))
    identifier = AIRIdentifierReference("x")
    integer = AIRIntegerLiteral(huge)
    negative_zero = AIRFloatLiteral(-0.0)
    text = AIRStringLiteral("A😀𐐷")
    boolean = AIRBooleanLiteral(True)
    unary = AIRUnaryExpression("-", integer)
    binary = AIRBinaryExpression(integer, "+", AIRIntegerLiteral(1))
    call = AIRCallExpression(
        "Nested",
        (integer, negative_zero, text, boolean, identifier, unary, binary),
        (INT, variable),
    )
    local = AIRLocalBinding("result", call)
    when = AIRFunctionWhen(
        boolean,
        (local, AIRFunctionReturn(call)),
        (AIRFunctionReturn(text),),
    )
    first = AIRFunction(
        id="function:Helper",
        name="Helper",
        parameters=(AIRParameter("x", variable), AIRParameter("count", INT)),
        return_expression=call,
        order=0,
        local_bindings=(local,),
        body=(when,),
        return_type=variable,
        type_parameters=(variable,),
    )
    second = AIRFunction(
        id="function:Empty",
        name="Empty",
        parameters=(AIRParameter("legacy", None),),
        return_expression=None,
        order=1,
        return_type=None,
    )
    program = AIRProgram(
        version="rcv44",
        states=(),
        events=(),
        authority_checks=(),
        causal_decisions=(),
        directives=(),
        requirements=(),
        authorities=(),
        principals=(),
        roles=(),
        functions=(first, second),
        workflows=(
            AIRWorkflow(
                id="workflow:Probe",
                name="Probe",
                invocations=(AIRWorkflowInvocation(target="Helper"),),
            ),
        ),
    )
    transport = build_verified_air_lowering_input(VerifiedAIRProgram(program))
    empty = build_verified_air_lowering_input(
        VerifiedAIRProgram(
            AIRProgram(
                version="rcv44-empty",
                states=(),
                events=(),
                authority_checks=(),
                causal_decisions=(),
                directives=(),
                requirements=(),
            )
        )
    )
    return transport, empty


def main() -> int:
    previous = json.loads(RCV43.read_text(encoding="utf-8-sig"))
    data = json.loads(CONTRACT.read_text(encoding="utf-8-sig"))
    req(previous["profile"] == "apexforge.p12.managed-executable-carrier-decoder-implementation/v1", "RCV-43 profile changed")
    req(data["predecessor"]["stage"] == "P12.5-RCV-43", "predecessor changed")
    transport, empty = make_transport()
    repeated, repeated_empty = make_transport()
    req(transport.transport_json == repeated.transport_json, "live canonical fixture transport changed between builds")
    req(transport.transport_fingerprint == repeated.transport_fingerprint, "live canonical fixture fingerprint changed")
    req(empty.transport_json == repeated_empty.transport_json, "empty transport changed between builds")
    req("\"workflows\"" in transport.transport_json, "non-empty workflow was not serialized")
    req("\"workflows\"" not in empty.transport_json, "empty workflow was not compatibility-omitted")

    payload = base64.b64encode(transport.transport_json.encode("utf-8")).decode("ascii")
    empty_payload = base64.b64encode(empty.transport_json.encode("utf-8")).decode("ascii")
    probe = r'''using System.Numerics;
using System.Text;
using ApexForge.Runtime;

var json = Encoding.UTF8.GetString(Convert.FromBase64String("__PAYLOAD__"));
var emptyJson = Encoding.UTF8.GetString(Convert.FromBase64String("__EMPTY__"));
var decoder = new ManagedExecutableCarrierDecoder();
var functions = decoder.DecodeCanonicalAirTransport(json);
if (functions.Count != 2 || functions[0].Id != "function:Helper" || functions[1].Id != "function:Empty") return 10;
if (functions[0].Order != 0 || functions[1].Order != 1) return 11;
if (decoder.DecodeCanonicalAirTransport(emptyJson).Count != 0) return 12;

var first = functions[0];
if (first.Parameters.Count != 2 || first.LocalBindings.Count != 1 || first.Body.Count != 1 || first.TypeParameters.Count != 1) return 13;
if (first.Parameters[0].ValueType is not ManagedTypeVariableReference parameterType) return 14;
if (parameterType.Name != "T" || parameterType.Owner != "Helper" || parameterType.Constraints.Count != 1) return 15;
if (parameterType.Constraints[0] is not ManagedApexTypeConstraintReference constraint || constraint.Name != "numeric") return 16;
if (first.Parameters[1].ValueType is not ManagedApexTypeReference intType || intType.Name != "int" || intType.Arguments.Count != 0) return 17;
if (first.ReturnType is not ManagedTypeVariableReference || first.TypeParameters[0].Name != "T") return 18;

if (first.ReturnExpression is not ManagedCallExpression call || call.Target != "Nested" || call.Arguments.Count != 7 || call.TypeArguments.Count != 2) return 19;
var huge = BigInteger.Parse("170141183460469231731687303715884105728");
if (call.Arguments[0] is not ManagedIntegerLiteral integer || integer.Value != huge) return 20;
if (call.Arguments[1] is not ManagedFloatLiteral floating || BitConverter.DoubleToInt64Bits(floating.Value) != long.MinValue) return 21;
if (call.Arguments[2] is not ManagedStringLiteral text || text.Value != "A\U0001F600\U00010437") return 22;
if (call.Arguments[3] is not ManagedBooleanLiteral boolean || !boolean.Value) return 23;
if (call.Arguments[4] is not ManagedIdentifierReference identifier || identifier.Name != "x") return 24;
if (call.Arguments[5] is not ManagedUnaryExpression unary || unary.Operator != "-" || unary.Operand is not ManagedIntegerLiteral) return 25;
if (call.Arguments[6] is not ManagedBinaryExpression binary || binary.Operator != "+" || binary.Left is not ManagedIntegerLiteral || binary.Right is not ManagedIntegerLiteral) return 26;
if (call.TypeArguments[0] is not ManagedApexTypeReference || call.TypeArguments[1] is not ManagedTypeVariableReference) return 27;

if (first.LocalBindings[0].Name != "result" || first.LocalBindings[0].Expression is not ManagedCallExpression) return 28;
if (first.Body[0] is not ManagedFunctionWhen when || when.Actions.Count != 2 || when.OtherwiseActions.Count != 1) return 29;
if (when.Condition is not ManagedBooleanLiteral || when.Actions[0] is not ManagedLocalBinding || when.Actions[1] is not ManagedFunctionReturn || when.OtherwiseActions[0] is not ManagedFunctionReturn) return 30;

var second = functions[1];
if (second.ReturnExpression is not null || second.ReturnType is not null || second.Parameters[0].ValueType is not null) return 31;
Console.WriteLine("RCV44_ALL_AUTHORIZED_SHAPES=PASS");
Console.WriteLine("RCV44_BIG_INTEGER_EXACT=PASS");
Console.WriteLine("RCV44_NEGATIVE_ZERO=PASS");
Console.WriteLine("RCV44_UNICODE_BOOLEAN=PASS");
Console.WriteLine("RCV44_GENERIC_CONTROL_FLOW=PASS");
Console.WriteLine("RCV44_EMPTY_MULTIPLE_ORDER=PASS");
Console.WriteLine("RCV44_POSITIVE_CONFORMANCE=PASS");
return 0;
'''.replace("__PAYLOAD__", payload).replace("__EMPTY__", empty_payload)

    with tempfile.TemporaryDirectory(prefix="apexforge-rcv44-") as raw:
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
        req(result.returncode == 0, "positive managed probe failed:\n" + result.stdout + result.stderr)
        req(result.stdout.splitlines()[-1:] == ["RCV44_POSITIVE_CONFORMANCE=PASS"], "positive probe terminal output changed:\n" + result.stdout)

    req(all(data["coverage"].values()), "positive coverage flag missing")
    req(data["authority"]["no_second_semantic_implementation"] is True, "semantic duplication authorized")
    print(f"P12_5_RCV_44_CANONICAL_TRANSPORT_FINGERPRINT={transport.transport_fingerprint}")
    print("P12_5_RCV_44_AUTHORIZED_MAPPING_COUNT=18")
    print("P12_5_RCV_44_EMPTY_MULTIPLE_FUNCTION_BEHAVIOR=PASS")
    print("P12_5_RCV_44_POSITIVE_CONFORMANCE=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
