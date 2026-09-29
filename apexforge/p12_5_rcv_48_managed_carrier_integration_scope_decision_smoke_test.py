from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "apexforge/p12_5_rcv_48_managed_carrier_integration_scope_decision.json"
RCV22 = ROOT / "apexforge/p12_5_rcv_22_cross_runtime_transport_contract_decision.json"
RCV27 = ROOT / "apexforge/p12_5_rcv_27_managed_host_program_integration_contract.json"
RCV47 = ROOT / "apexforge/p12_5_rcv_47_managed_carrier_derivation_determinism_recursive_graph_acceptance.json"
DECODER = ROOT / "runtimes/dotnet/ApexForge.Runtime/ManagedExecutableCarrierDecoder.cs"
RUNTIME_HOST = ROOT / "runtimes/dotnet/ApexForge.Runtime/ManagedRuntimeHost.cs"
HOST_DIR = ROOT / "runtimes/dotnet/ApexForge.Runtime.Host"


def req(value, message):
    if not value:
        raise AssertionError(message)


def main() -> int:
    transport = json.loads(RCV22.read_text(encoding="utf-8-sig"))
    host = json.loads(RCV27.read_text(encoding="utf-8-sig"))
    previous = json.loads(RCV47.read_text(encoding="utf-8-sig"))
    data = json.loads(CONTRACT.read_text(encoding="utf-8-sig"))
    req(transport["decision"]["cross_runtime_transport"] == "DEFERRED_NO_TRANSPORT_AUTHORIZED", "RCV-22 transport decision changed")
    req(host["decision"]["program_ingress_wiring"] == "DEFERRED_NO_PAYLOAD_SOURCE", "RCV-27 program decision changed")
    req(previous["acceptance"]["result"] == "PASS", "RCV-47 acceptance changed")
    req(data["predecessor"]["stage"] == "P12.5-RCV-47", "predecessor changed")

    decision = data["decision"]
    req(decision["separate_managed_runtime_carrier_admission"] == "DEFERRED_NO_CONSUMER_AUTHORITY", "carrier admission selected")
    req(decision["managed_host_ingress_integration"] == "DEFERRED_NO_PAYLOAD_SOURCE", "host ingress selected")
    req(decision["execution_dispatch"] == "DEFERRED_NO_EXECUTION_CONTRACT", "execution selected")
    req(decision["target_neutral_handoff_coupling"] == "NOT_AUTHORIZED", "target-neutral coupling selected")
    req(decision["cross_runtime_transport"] == "DEFERRED_NO_TRANSPORT_AUTHORIZED", "transport selected")
    req(decision["network_ingress"] == "FORBIDDEN", "network ingress selected")

    decoder = DECODER.read_text(encoding="utf-8-sig")
    runtime_host = RUNTIME_HOST.read_text(encoding="utf-8-sig")
    host_sources = "\n".join(path.read_text(encoding="utf-8-sig") for path in sorted(HOST_DIR.glob("*.cs")))
    req("ManagedExecutableCarrierDecoder" not in runtime_host, "decoder wired into ManagedRuntimeHost")
    req("ManagedExecutableCarrierDecoder" not in host_sources, "decoder wired into host")
    req("TargetNeutralLoweringHandoff" not in decoder, "decoder coupled to target-neutral handoff")
    for token in ("HttpClient", "TcpClient", "NamedPipe", "Console.In", "File.ReadAll"):
        req(token not in decoder and token not in host_sources, f"unauthorized ingress token present: {token}")

    req(data["production_change"] == "NONE", "integration production change authorized")
    req(data["authority"]["decision_expands_capability"] is False, "capability expansion authorized")
    print("P12_5_RCV_48_DECODER_ROLE=IN_PROCESS_STRUCTURAL_CONSTRUCTION_API_ONLY")
    print("P12_5_RCV_48_MANAGED_CARRIER_ADMISSION=DEFERRED_NO_CONSUMER_AUTHORITY")
    print("P12_5_RCV_48_EXECUTION_DISPATCH=DEFERRED_NO_EXECUTION_CONTRACT")
    print("P12_5_RCV_48_CROSS_RUNTIME_TRANSPORT=DEFERRED_NO_TRANSPORT_AUTHORIZED")
    print("P12_5_RCV_48_INTEGRATION_SCOPE_DECISION=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
