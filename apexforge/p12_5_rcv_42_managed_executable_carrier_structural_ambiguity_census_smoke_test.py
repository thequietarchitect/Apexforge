from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "apexforge/p12_5_rcv_42_managed_executable_carrier_structural_ambiguity_census.json"
RCV38 = ROOT / "apexforge/p12_5_rcv_38_managed_executable_carrier_json_parsing_policy_contract.json"
RCV41 = ROOT / "apexforge/p12_5_rcv_41_managed_executable_carrier_decoder_public_api_contract.json"


def req(value, message):
    if not value:
        raise AssertionError(message)


def main() -> int:
    parsing = json.loads(RCV38.read_text(encoding="utf-8-sig"))
    previous = json.loads(RCV41.read_text(encoding="utf-8-sig"))
    data = json.loads(CONTRACT.read_text(encoding="utf-8-sig"))
    req(parsing["structural_dispatch_policy"]["dispatch_basis"] == "EXACT_PROPERTY_SET_PLUS_JSON_VALUE_KIND", "RCV-38 dispatch basis changed")
    req(previous["profile"] == "apexforge.p12.managed-executable-carrier-decoder-public-api-contract/v1", "RCV-41 profile changed")
    req(data["predecessor"]["stage"] == "P12.5-RCV-41", "predecessor changed")
    dispatch = data["dispatch"]
    req(dispatch["unresolved_collision_count"] == 0, "unresolved structural collision")
    req(dispatch["heuristic_similarity"] is False, "heuristic dispatch authorized")
    for key in ("unknown_shape", "duplicate_property", "extra_property", "missing_property", "wrong_json_kind"):
        req(dispatch[key] == "REJECT", f"fail-closed rule changed: {key}")
    literal = data["collisions"][0]
    req(literal["shape"] == ["value"], "literal collision shape changed")
    req(literal["resolution"] == "JSON_VALUE_KIND_THEN_NUMBER_GRAMMAR", "literal resolution changed")
    req(all(item["unresolved"] is False for item in data["collisions"]), "collision unresolved")
    req(data["authority"]["semantic_inference_added"] is False, "semantic inference authorized")
    print("P12_5_RCV_42_UNRESOLVED_COLLISION_COUNT=0")
    print("P12_5_RCV_42_LITERAL_DISPATCH=JSON_VALUE_KIND_THEN_NUMBER_GRAMMAR")
    print("P12_5_RCV_42_HEURISTIC_SIMILARITY=False")
    print("P12_5_RCV_42_NO_SECOND_SEMANTIC_IMPLEMENTATION=True")
    print("P12_5_RCV_42_STRUCTURAL_AMBIGUITY_CENSUS=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
