from __future__ import annotations

import ast
import importlib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "apexforge/p12_5_rcv_20_projection_value_object_compatibility_census.json"
RCV19 = ROOT / "apexforge/p12_5_rcv_19_projection_value_object_implementation_foundation_smoke_test.py"
PROJECTION = ROOT / "apexforge/native_backend/managed_handoff_projection.py"
PACKAGE_INIT = ROOT / "apexforge/native_backend/__init__.py"
HANDOFF = ROOT / "runtimes/dotnet/ApexForge.Runtime/TargetNeutralLoweringHandoff.cs"
HOST = ROOT / "runtimes/dotnet/ApexForge.Runtime/ManagedRuntimeHost.cs"
RUNTIME_PROJ = ROOT / "runtimes/dotnet/ApexForge.Runtime/ApexForge.Runtime.csproj"
PROBE_CS = 'using ApexForge.Runtime;\n\nvar h = new TargetNeutralLoweringHandoff(\n    "apexforge.target-neutral-lowering/v1",\n    new string(\'a\', 64),\n    new string(\'b\', 64),\n    "entry-main",\n    new[] { "owner-a", "owner-b" },\n    new string(\'C\', 64));\n\nvar host = new ManagedRuntimeHost();\nif (!ReferenceEquals(h, host.AdmitTargetNeutralHandoff(h)))\n{\n    throw new Exception("admission identity mismatch");\n}\n\nConsole.WriteLine("RCV20_MANAGED_ADMISSIBILITY=PASS");\n'

EXPECTED = [
    ("schema", "str", "Schema", "string"),
    ("verified_air_fingerprint", "str", "VerifiedAirFingerprint", "string"),
    ("routing_fingerprint", "str", "RoutingFingerprint", "string"),
    ("entry_directive", "str", "EntryDirective", "string"),
    ("directive_owner_ids", "tuple[str, ...]", "DirectiveOwnerIds", "IReadOnlyList<string>"),
    ("product_fingerprint", "str", "ProductFingerprint", "string"),
]

def req(c, m):
    if not c:
        raise AssertionError(m)

def run(*args, cwd=ROOT):
    return subprocess.run(list(args), cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def parse_python_projection():
    src = PROJECTION.read_text(encoding="utf-8-sig")
    tree = ast.parse(src)
    cls = next((n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "ManagedHandoffProjection"), None)
    req(cls is not None, "ManagedHandoffProjection missing")
    fields = []
    decorators = []
    for d in cls.decorator_list:
        try:
            decorators.append(ast.unparse(d))
        except Exception:
            pass
    for n in cls.body:
        if isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name):
            try:
                ann = ast.unparse(n.annotation)
            except Exception:
                ann = "<unparsed>"
            fields.append((n.target.id, ann))
    return fields, decorators

def parse_csharp_handoff():
    src = HANDOFF.read_text(encoding="utf-8-sig")
    m = re.search(r"public sealed record TargetNeutralLoweringHandoff\((.*?)\)\s*\{", src, re.S)
    req(m is not None, "TargetNeutralLoweringHandoff declaration missing")
    fields = []
    for raw in m.group(1).splitlines():
        line = raw.strip().rstrip(",")
        if not line:
            continue
        mm = re.match(r"(.+?)\s+([A-Za-z_][A-Za-z0-9_]*)$", line)
        req(mm is not None, f"unable to parse managed field: {line}")
        fields.append((mm.group(2), mm.group(1)))
    return fields, src

def main():
    print("=== P12.5-RCV-20 PROJECTION VALUE-OBJECT COMPATIBILITY CENSUS ===")
    for p in (CONTRACT, RCV19, PROJECTION, PACKAGE_INIT, HANDOFF, HOST, RUNTIME_PROJ):
        req(p.exists(), f"missing required file: {p}")

    cp = run(sys.executable, str(RCV19))
    req(cp.returncode == 0, "RCV-19 regression failed:\n" + cp.stdout + "\n" + cp.stderr)
    print("P12_5_RCV_20_RCV19_REGRESSION=PASS")

    data = json.loads(CONTRACT.read_text(encoding="utf-8-sig"))
    req(data["profile"] == "apexforge.p12.projection-value-object-compatibility-census/v1", "profile changed")
    req(data["predecessor"]["stage"] == "P12.5-RCV-19", "predecessor changed")
    req(data["compatibility_target"]["schema"] == "apexforge.target-neutral-lowering/v1", "schema changed")

    py_fields, decorators = parse_python_projection()
    cs_fields, cs_src = parse_csharp_handoff()

    expected_py = [(a, b) for a, b, _, _ in EXPECTED]
    expected_cs = [(c, d) for _, _, c, d in EXPECTED]
    req(py_fields == expected_py, f"Python projection shape changed: {py_fields}")
    req(cs_fields == expected_cs, f"C# handoff shape changed: {cs_fields}")
    req(any(x.startswith("dataclass") and "frozen=True" in x.replace(" ", "") for x in decorators), "Python projection is not frozen")
    req("public sealed record TargetNeutralLoweringHandoff" in cs_src, "C# handoff is not a sealed record")

    actual_contract = [(x["source"], x["source_type"], x["managed"], x["managed_type"]) for x in data["field_correspondence"]]
    req(actual_contract == EXPECTED, f"contract field correspondence changed: {actual_contract}")

    host_src = HOST.read_text(encoding="utf-8-sig")
    req("public TargetNeutralLoweringHandoff AdmitTargetNeutralHandoff(TargetNeutralLoweringHandoff handoff)" in host_src, "managed handoff admission missing")
    req("ArgumentNullException.ThrowIfNull(handoff);" in host_src, "managed null guard missing")
    req("handoff.Validate();" in host_src, "managed validation missing")
    req("return handoff;" in host_src, "managed validate-and-return missing")

    init_src = PACKAGE_INIT.read_text(encoding="utf-8-sig")
    root_exported = "ManagedHandoffProjection" in init_src or "project_managed_handoff" in init_src

    sys.path.insert(0, str(ROOT))
    try:
        projection_module = importlib.import_module("apexforge.native_backend.managed_handoff_projection")
        lowering = importlib.import_module("apexforge.native_backend.target_neutral_lowering")
        product = lowering.TargetNeutralLoweringProduct(
            binding=SimpleNamespace(
                lowering_input=SimpleNamespace(transport_fingerprint="a" * 64),
                routing_fingerprint="b" * 64,
                entry_directive="entry-main",
                directive_owner_ids=("owner-a", "owner-b"),
            ),
            canonical_json='{"excluded":true}',
            product_fingerprint="C" * 64,
            schema="apexforge.target-neutral-lowering/v1",
        )
        projected = projection_module.project_managed_handoff(product)
        req(projected.schema == "apexforge.target-neutral-lowering/v1", "projected schema mismatch")
        req(projected.directive_owner_ids == ("owner-a", "owner-b"), "projected owner list mismatch")
        req(not hasattr(projected, "canonical_json"), "canonical_json leaked into projection")
        req(not hasattr(projected, "binding"), "binding leaked into projection")
    finally:
        try:
            sys.path.remove(str(ROOT))
        except ValueError:
            pass

    with tempfile.TemporaryDirectory(prefix="apexforge-rcv20-") as td_raw:
        td = Path(td_raw)
        include = str(RUNTIME_PROJ).replace("\\", "/")
        csproj_text = (
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
        (td / "Rcv20Probe.csproj").write_text(csproj_text, encoding="utf-8")
        (td / "Program.cs").write_text(PROBE_CS, encoding="utf-8")
        cp = run("dotnet", "run", "--project", str(td / "Rcv20Probe.csproj"), "-c", "Release", "--nologo", cwd=td)
        req(cp.returncode == 0, "managed compatibility probe failed:\n" + cp.stdout + "\n" + cp.stderr)
        req("RCV20_MANAGED_ADMISSIBILITY=PASS" in cp.stdout, "managed admissibility marker missing")

    for key, value in data["unselected"].items():
        req(value == "UNSELECTED", f"{key} selected too early")

    print("P12_5_RCV_20_PROFILE=apexforge.p12.projection-value-object-compatibility-census/v1")
    print("P12_5_RCV_20_FIELD_COUNT=6")
    print("P12_5_RCV_20_FIELD_ORDER=PASS")
    print("P12_5_RCV_20_TYPE_CORRESPONDENCE=PASS")
    print("P12_5_RCV_20_SCHEMA_COMPATIBILITY=PASS")
    print("P12_5_RCV_20_MANAGED_ADMISSIBILITY=PASS")
    print(f"P12_5_RCV_20_PACKAGE_ROOT_EXPORTED={str(root_exported)}")
    print("P12_5_RCV_20_PACKAGE_ROOT_EXPORT_CHANGE_AUTHORIZED=False")
    print("P12_5_RCV_20_CANONICAL_JSON_CROSSES_BOUNDARY=False")
    print("P12_5_RCV_20_BINDING_OBJECT_CROSSES_BOUNDARY=False")
    print("P12_5_RCV_20_EXTERNAL_SERIALIZATION=UNSELECTED")
    print("P12_5_RCV_20_CROSS_RUNTIME_TRANSPORT=UNSELECTED")
    print("P12_5_RCV_20_EXECUTION_DISPATCH=DEFERRED")
    print("P12_5_RCV_20_PROJECTION_VALUE_OBJECT_COMPATIBILITY_CENSUS=PASS")
    print("P12_5_RCV_20_NEXT=P12.5-RCV-21_CROSS_RUNTIME_TRANSPORT_ARCHITECTURE_CENSUS")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
