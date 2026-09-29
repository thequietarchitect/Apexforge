from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APEXFORGE = ROOT / "apexforge"
CONTRACT = APEXFORGE / "p12_5_rcv_50_recovery_closure_audit.json"
RCV49 = APEXFORGE / "p12_5_rcv_49_managed_carrier_representational_equivalence_acceptance.json"
RUNTIME = ROOT / "runtimes/dotnet/ApexForge.Runtime/ApexForge.Runtime.csproj"
HOST = ROOT / "runtimes/dotnet/ApexForge.Runtime.Host/ApexForge.Runtime.Host.csproj"
SMOKE = ROOT / "runtimes/dotnet/ApexForge.Runtime.Smoke/ApexForge.Runtime.Smoke.csproj"
P12_5_PRODUCTION = (
    ROOT / "runtimes/dotnet/ApexForge.Runtime/ManagedExecutableCarrier.cs",
    ROOT / "runtimes/dotnet/ApexForge.Runtime/ManagedExecutableCarrierDecoder.cs",
    ROOT / "runtimes/dotnet/ApexForge.Runtime/TargetNeutralLoweringHandoff.cs",
    ROOT / "runtimes/dotnet/ApexForge.Runtime/ManagedRuntimeHost.cs",
    ROOT / "runtimes/dotnet/ApexForge.Runtime.Host/Program.cs",
)


def req(value, message):
    if not value:
        raise AssertionError(message)


def run(*args: str, cwd: Path = ROOT) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    return subprocess.run(
        args,
        cwd=cwd,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def run_smoke(path: Path) -> None:
    result = run(sys.executable, "-B", str(path))
    req(result.returncode == 0, f"smoke failed: {path.name}\n{result.stdout}{result.stderr}")


def git(*args: str) -> str:
    result = run("git", *args)
    req(result.returncode == 0, f"git {' '.join(args)} failed\n{result.stdout}{result.stderr}")
    return result.stdout.strip()


def main() -> int:
    previous = json.loads(RCV49.read_text(encoding="utf-8-sig"))
    data = json.loads(CONTRACT.read_text(encoding="utf-8-sig"))
    req(previous["result"] == "PASS", "RCV-49 acceptance changed")
    req(data["predecessor"]["stage"] == "P12.5-RCV-49", "predecessor changed")

    recovery = []
    for path in APEXFORGE.glob("p12_5_rcv_*_smoke_test.py"):
        match = re.match(r"p12_5_rcv_(\d+)_", path.name)
        if match and int(match.group(1)) < 50:
            recovery.append(path)
    recovery.sort(key=lambda path: int(re.match(r"p12_5_rcv_(\d+)_", path.name).group(1)))
    req(len(recovery) == 46, f"recovery predecessor count changed: {len(recovery)}")
    for path in recovery:
        run_smoke(path)

    p12_predecessors = sorted(
        path for path in APEXFORGE.glob("p12_*_smoke_test.py")
        if not path.name.startswith("p12_5_rcv_")
    )
    req(len(p12_predecessors) == 25, f"P12 predecessor count changed: {len(p12_predecessors)}")
    for path in p12_predecessors:
        run_smoke(path)

    for project in (RUNTIME, HOST, SMOKE):
        result = run("dotnet", "build", str(project), "-c", "Release", "--nologo", "--no-restore")
        req(result.returncode == 0, f"managed build failed: {project}\n{result.stdout}{result.stderr}")
    host_run = run("dotnet", "run", "--project", str(HOST), "-c", "Release", "--no-build", "--nologo")
    req(host_run.returncode == 0, "managed host run failed\n" + host_run.stdout + host_run.stderr)
    req("APEXFORGE_RUNTIME_HOST" in host_run.stdout, "managed host marker missing")
    smoke_run = run("dotnet", "run", "--project", str(SMOKE), "-c", "Release", "--no-build", "--nologo")
    req(smoke_run.returncode == 0, "managed smoke run failed\n" + smoke_run.stdout + smoke_run.stderr)
    req("P12_1E_MANAGED_CANONICAL_RESULT=PASS" in smoke_run.stdout, "managed smoke marker missing")

    freeze_tags = {
        "afp-p10-t5-final-freeze": "38a377824a92d8b8e2f3876ff9bdf8593fa60547",
        "afp-p11-sra-f-full-regression-release-closure-freeze": "322ba125495ad7b4f3d6b2dcc447e5e383d067f9",
        "afp-p12.0c-freeze": "0350816742e6035b37ff790ef2b575e3b994228d",
        "afp-p12.1-freeze": "eae9c365b933a75e3fa7174e25bd97e9149cc777",
        "afp-p12.2-freeze": "9caffc16d25e4e1176a44e1de6309fc4c499ee55",
        "afp-p12.3-freeze": "b6a99918d91aa1c35d82b360cccf112575595111",
        "afp-p12.4-freeze": "13f7646f1052746f54f906076d66d29117ee2718",
    }
    for tag, expected in freeze_tags.items():
        req(git("rev-list", "-n", "1", tag) == expected, f"freeze commit changed: {tag}")
        ancestor = run("git", "merge-base", "--is-ancestor", expected, "HEAD")
        req(ancestor.returncode == 0, f"freeze is not an ancestor: {tag}")
    req(git("rev-parse", "refs/tags/afp-p12.4-freeze") == "7c475986ed3ed1d58cc30148603fbfe8b09529ee", "P12.4 tag object changed")

    source = "\n".join(path.read_text(encoding="utf-8-sig") for path in P12_5_PRODUCTION)
    forbidden = (
        "JsonSerializer.Deserialize", "Utf8JsonReader", "HttpClient", "TcpClient", "UdpClient",
        "NamedPipe", "Console.Read", "Console.In", "File.Read", "File.Write", "Python.Runtime",
    )
    for token in forbidden:
        req(token not in source, f"unauthorized capability appeared: {token}")
    decoder_and_carrier = "\n".join(path.read_text(encoding="utf-8-sig") for path in P12_5_PRODUCTION[:2])
    for token in ("Execute(", "Dispatch(", "Evaluate(", "Interpret("):
        req(token not in decoder_and_carrier, f"hidden semantic/execution path appeared: {token}")

    tracked = git("ls-files").splitlines()
    artifact_pattern = re.compile(r"(^|/)(bin|obj)/|\.(dll|exe|pdb|obj)$", re.IGNORECASE)
    req(not [path for path in tracked if artifact_pattern.search(path)], "generated binary became tracked")
    req(git("diff", "--cached", "--name-only") == "", "files are staged")

    current = data["current_regression_stack"]
    req(current["recovery_gate_tests"] == {"count": 46, "passed": 46, "failed": 0, "result": "PASS"}, "recovery result changed")
    req(current["p12_predecessor_tests"] == {"count": 25, "passed": 25, "failed": 0, "result": "PASS"}, "P12 result changed")
    req(data["supplemental_historical_discovery"]["decoder_related_failure_count"] == 0, "decoder failure recorded")
    req(data["authority"]["language_semantics"] == "CANONICAL_AIR", "semantic authority changed")
    req(data["authority"]["no_second_semantic_implementation"] is True, "second semantics authorized")
    req(data["git_actions"] == {"files_staged": False, "commit_created": False, "tag_created": False, "push_attempted": False}, "Git action policy changed")
    print("P12_5_RCV_50_RECOVERY_TESTS=46/46")
    print("P12_5_RCV_50_P12_PREDECESSOR_TESTS=25/25")
    print("P12_5_RCV_50_MANAGED_BUILD_AND_RUN=PASS")
    print("P12_5_RCV_50_P10_P11_P12_FREEZE_ANCESTRY=PASS")
    print("P12_5_RCV_50_PROVENANCE_OWNERSHIP_SECURITY_AUDIT=PASS")
    print("P12_5_RCV_50_RECOVERY_CLOSURE_AUDIT=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
