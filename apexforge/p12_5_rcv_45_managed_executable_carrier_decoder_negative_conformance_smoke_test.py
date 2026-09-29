from __future__ import annotations

import base64
import copy
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "apexforge/p12_5_rcv_45_managed_executable_carrier_decoder_negative_conformance.json"
RCV44 = ROOT / "apexforge/p12_5_rcv_44_managed_executable_carrier_decoder_positive_conformance.json"
RUNTIME = ROOT / "runtimes/dotnet/ApexForge.Runtime/ApexForge.Runtime.csproj"


def req(value, message):
    if not value:
        raise AssertionError(message)


def run(*args, cwd=ROOT):
    return subprocess.run(args, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def base_document():
    return {
        "authorities": [],
        "authority_checks": [],
        "causal_decisions": [],
        "directives": [],
        "events": [],
        "functions": [{
            "id": "function:Probe",
            "name": "Probe",
            "parameters": [],
            "return_expression": None,
            "order": 0,
            "local_bindings": [],
            "body": [],
            "return_type": None,
            "type_parameters": [],
        }],
        "principals": [],
        "requirements": [],
        "roles": [],
        "states": [],
        "version": "rcv45",
    }


def compact(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def cases():
    items = []

    def add(name, value, fragment):
        items.append((name, value if isinstance(value, str) else compact(value), fragment))

    add("malformed_json", "{", "not valid strict JSON")
    valid = compact(base_document())
    add("nan", valid.replace('"return_expression":null', '"return_expression":{"value":NaN}'), "not valid strict JSON")
    add("positive_infinity", valid.replace('"return_expression":null', '"return_expression":{"value":Infinity}'), "not valid strict JSON")
    add("negative_infinity", valid.replace('"return_expression":null', '"return_expression":{"value":-Infinity}'), "not valid strict JSON")
    add("wrong_root_kind", [], "'$'")

    value = base_document(); value["extra"] = []
    add("unknown_root", value, "unknown property 'extra'")
    value = base_document(); del value["functions"]
    add("missing_functions", value, "missing required property 'functions'")
    value = base_document(); value["version"] = 1
    add("wrong_version_kind", value, "'$.version'")
    value = base_document(); value["workflows"] = {}
    add("wrong_workflows_kind", value, "'$.workflows'")
    value = base_document(); value["functions"] = None
    add("null_functions", value, "'$.functions'")

    duplicate_root = valid.replace('"version":"rcv45"', '"version":"rcv45","version":"duplicate"')
    add("duplicate_root", duplicate_root, "duplicate property 'version'")
    duplicate_function = valid.replace('"id":"function:Probe"', '"id":"function:Probe","id":"duplicate"')
    add("duplicate_function", duplicate_function, "duplicate property 'id'")

    value = base_document(); del value["functions"][0]["id"]
    add("missing_function_id", value, "missing required property 'id'")
    value = base_document(); value["functions"][0]["extra"] = 1
    add("unknown_function_property", value, "unknown property 'extra'")
    value = base_document(); value["functions"][0]["Id"] = value["functions"][0].pop("id")
    add("case_mismatch", value, "unknown property 'Id'")
    value = base_document(); value["functions"][0]["order"] = 1.5
    add("float_order", value, "32-bit integer token")
    value = base_document(); value["functions"][0]["order"] = 2147483648
    add("order_overflow", value, "32-bit integer token")
    value = base_document(); value["functions"][0]["parameters"] = None
    add("null_parameter_collection", value, "'$.functions[0].parameters'")
    value = base_document(); value["functions"][0]["parameters"] = [None]
    add("null_parameter_item", value, "'$.functions[0].parameters[0]'")

    value = base_document(); value["functions"][0]["return_expression"] = {"foo": 1}
    add("unknown_expression", value, "unknown expression shape")
    value = base_document(); value["functions"][0]["return_expression"] = {"value": None}
    add("null_literal", value, "must be a string, boolean, or number literal")
    overflow_float = valid.replace('"return_expression":null', '"return_expression":{"value":1e999}')
    add("float_overflow", overflow_float, "finite invariant binary64 token")
    value = base_document(); value["functions"][0]["return_expression"] = {"target": "x", "arguments": []}
    add("missing_call_property", value, "unknown expression shape")
    value = base_document(); value["functions"][0]["body"] = [{"foo": 1}]
    add("unknown_statement", value, "unknown function-statement shape")
    value = base_document(); value["functions"][0]["body"] = [None]
    add("null_statement", value, "'$.functions[0].body[0]'")

    value = base_document(); value["functions"][0]["return_type"] = "int"
    add("normalized_alias_string", value, "must be Object; received String")
    value = base_document(); value["functions"][0]["return_type"] = {"name": "int"}
    add("unknown_generic_shape", value, "canonical generic-type shape")
    value = base_document(); value["functions"][0]["return_type"] = {"name": "int", "arguments": [], "extra": 1}
    add("extra_type_property", value, "canonical generic-type shape")
    value = base_document(); value["functions"][0]["type_parameters"] = [{"name": "T", "owner": "Probe", "constraints": [None]}]
    add("null_constraint", value, "'$.functions[0].type_parameters[0].constraints[0]'")
    value = base_document(); value["functions"][0]["type_parameters"] = [{"name": "T", "owner": "Probe", "constraints": [{"name": "numeric", "description": "x", "extra": 1}]}]
    add("extra_constraint_property", value, "unknown property 'extra'")
    return items


def main() -> int:
    previous = json.loads(RCV44.read_text(encoding="utf-8-sig"))
    data = json.loads(CONTRACT.read_text(encoding="utf-8-sig"))
    req(previous["result"] == "PASS", "RCV-44 conformance changed")
    req(data["predecessor"]["stage"] == "P12.5-RCV-44", "predecessor changed")
    invalid = cases()
    req(len(invalid) >= 25, "negative case set narrowed")

    rows = []
    for name, payload, fragment in invalid:
        encoded = base64.b64encode(payload.encode("utf-8")).decode("ascii")
        escaped_fragment = fragment.replace("\\", "\\\\").replace('"', '\\"')
        rows.append(f'    new Case("{name}", "{encoded}", "{escaped_fragment}"),')

    probe = r'''using System.Text;
using ApexForge.Runtime;
var cases = new Case[]
{
__ROWS__
};
var decoder = new ManagedExecutableCarrierDecoder();
foreach (var item in cases)
{
    var json = Encoding.UTF8.GetString(Convert.FromBase64String(item.Payload));
    string FirstMessage()
    {
        try
        {
            _ = decoder.DecodeCanonicalAirTransport(json);
            throw new InvalidOperationException("accepted:" + item.Name);
        }
        catch (FormatException error)
        {
            if (!error.Message.Contains(item.Fragment, StringComparison.Ordinal))
                throw new InvalidOperationException(item.Name + ":" + error.Message);
            return error.Message;
        }
    }
    var first = FirstMessage();
    var second = FirstMessage();
    if (!StringComparer.Ordinal.Equals(first, second)) return 20;
}
Console.WriteLine($"RCV45_REJECTED_CASE_COUNT={cases.Length}");
Console.WriteLine("RCV45_DETERMINISTIC_DIAGNOSTICS=PASS");
Console.WriteLine("RCV45_NONFINITE_FAIL_CLOSED=PASS");
Console.WriteLine("RCV45_NEGATIVE_CONFORMANCE=PASS");
return 0;
record Case(string Name, string Payload, string Fragment);
'''.replace("__ROWS__", "\n".join(rows))

    with tempfile.TemporaryDirectory(prefix="apexforge-rcv45-") as raw:
        td = Path(raw)
        reference = str(RUNTIME).replace("\\", "/")
        (td / "Probe.csproj").write_text(
            '<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><OutputType>Exe</OutputType><TargetFramework>net10.0</TargetFramework><Nullable>enable</Nullable><ImplicitUsings>enable</ImplicitUsings><TreatWarningsAsErrors>true</TreatWarningsAsErrors></PropertyGroup><ItemGroup><ProjectReference Include="'
            + reference
            + '" /></ItemGroup></Project>', encoding="utf-8")
        (td / "Program.cs").write_text(probe, encoding="utf-8")
        result = run("dotnet", "run", "--project", str(td / "Probe.csproj"), "-c", "Release", "--nologo", cwd=td)
        req(result.returncode == 0, "negative managed probe failed:\n" + result.stdout + result.stderr)
        req(result.stdout.splitlines()[-1:] == ["RCV45_NEGATIVE_CONFORMANCE=PASS"], "negative probe terminal output changed:\n" + result.stdout)

    req(all(data["coverage"].values()), "negative coverage flag missing")
    req(data["policy"]["partial_carrier_return"] is False, "partial return authorized")
    req(data["boundary"]["nonfinite_transport_normalization_added"] is False, "nonfinite normalization introduced")
    print(f"P12_5_RCV_45_REJECTED_CASE_COUNT={len(invalid)}")
    print("P12_5_RCV_45_DETERMINISTIC_DIAGNOSTICS=PASS")
    print("P12_5_RCV_45_NONFINITE_TRANSPORT=FAIL_CLOSED")
    print("P12_5_RCV_45_NEGATIVE_CONFORMANCE=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
