from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "apexforge/p12_5_rcv_40_managed_executable_carrier_decoder_input_root_decision.json"
RCV39 = ROOT / "apexforge/p12_5_rcv_39_managed_executable_carrier_decoder_input_root_census.json"


def req(value, message):
    if not value:
        raise AssertionError(message)


def main() -> int:
    previous = json.loads(RCV39.read_text(encoding="utf-8-sig"))
    data = json.loads(CONTRACT.read_text(encoding="utf-8-sig"))
    req(previous["profile"] == "apexforge.p12.managed-executable-carrier-decoder-input-root-census/v1", "RCV-39 profile changed")
    req(previous["air_program_root_expectations"]["empty_workflows_omitted_for_historical_compatibility"] is True, "RCV-39 workflow compatibility evidence changed")
    req(data["predecessor"]["stage"] == "P12.5-RCV-39", "predecessor changed")
    decision = data["decision"]
    req(decision["decoder_input_root"] == "WHOLE_CANONICAL_AIR_DOCUMENT", "input root changed")
    req(decision["source_container"] == "VerifiedAIRLoweringInput.transport_json", "source seam changed")
    req(decision["carrier_subtree"] == "$.functions", "carrier subtree changed")
    req(decision["functions_only_transport_created"] is False, "functions-only transport authorized")
    req(decision["individual_function_transport_created"] is False, "individual-function transport authorized")
    req(decision["optional_compatibility_properties"] == ["workflows"], "compatibility property set changed")
    req(decision["metadata_semantic_reimplementation"] is False, "metadata semantics duplicated")
    req(decision["empty_functions_behavior"] == "RETURN_EMPTY_READ_ONLY_LIST", "empty behavior changed")
    req(decision["multiple_functions_behavior"] == "DECODE_ALL_IN_SOURCE_ORDER", "multiple behavior changed")
    req(decision["function_selection_behavior"] == "NONE", "selection behavior changed")
    req(data["authority"]["language_semantics"] == "CANONICAL_AIR", "semantic authority changed")
    req(data["boundary"]["runtime_crossing"] == "NOT_AUTHORIZED", "runtime crossing authorized")
    req(data["boundary"]["network_ingress"] == "FORBIDDEN", "network ingress authorized")
    print("P12_5_RCV_40_DECODER_INPUT_ROOT=WHOLE_CANONICAL_AIR_DOCUMENT")
    print("P12_5_RCV_40_CARRIER_SUBTREE=$.functions")
    print("P12_5_RCV_40_EMPTY_FUNCTIONS=RETURN_EMPTY_READ_ONLY_LIST")
    print("P12_5_RCV_40_MULTIPLE_FUNCTIONS=DECODE_ALL_IN_SOURCE_ORDER")
    print("P12_5_RCV_40_LANGUAGE_SEMANTIC_AUTHORITY=CANONICAL_AIR")
    print("P12_5_RCV_40_DECODER_INPUT_ROOT_DECISION=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
