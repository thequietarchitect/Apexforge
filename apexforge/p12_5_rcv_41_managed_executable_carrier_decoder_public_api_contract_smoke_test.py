from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "apexforge/p12_5_rcv_41_managed_executable_carrier_decoder_public_api_contract.json"
RCV40 = ROOT / "apexforge/p12_5_rcv_40_managed_executable_carrier_decoder_input_root_decision.json"


def req(value, message):
    if not value:
        raise AssertionError(message)


def main() -> int:
    previous = json.loads(RCV40.read_text(encoding="utf-8-sig"))
    data = json.loads(CONTRACT.read_text(encoding="utf-8-sig"))
    req(previous["profile"] == "apexforge.p12.managed-executable-carrier-decoder-input-root-decision/v1", "RCV-40 profile changed")
    req(data["predecessor"]["stage"] == "P12.5-RCV-40", "predecessor changed")
    api = data["api"]
    req(api["type"] == "ApexForge.Runtime.ManagedExecutableCarrierDecoder", "decoder type changed")
    req(api["method"] == "DecodeCanonicalAirTransport", "decoder method changed")
    req(api["input_semantics"] == "WHOLE_CANONICAL_AIR_TRANSPORT_JSON", "input semantics changed")
    req(api["return_type"].endswith("IReadOnlyList<ApexForge.Runtime.ManagedExecutableFunction>"), "return type changed")
    req(api["stateful"] is False and api["executes"] is False, "decoder authority widened")
    req(data["diagnostics"]["path_qualified"] is True, "path diagnostics removed")
    req(data["diagnostics"]["deterministic"] is True, "deterministic diagnostics removed")
    req(data["boundary"]["external_ingress_api"] is False, "external ingress selected")
    req(data["authority"]["no_second_semantic_implementation"] is True, "semantic duplication allowed")
    print("P12_5_RCV_41_DECODER_TYPE=ApexForge.Runtime.ManagedExecutableCarrierDecoder")
    print("P12_5_RCV_41_METHOD=DecodeCanonicalAirTransport")
    print("P12_5_RCV_41_RESULT=IReadOnlyList<ManagedExecutableFunction>")
    print("P12_5_RCV_41_NO_SECOND_SEMANTIC_IMPLEMENTATION=True")
    print("P12_5_RCV_41_DECODER_PUBLIC_API_CONTRACT=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
