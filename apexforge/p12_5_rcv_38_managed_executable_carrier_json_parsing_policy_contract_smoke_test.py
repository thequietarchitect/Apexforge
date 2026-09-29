from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "apexforge/p12_5_rcv_38_managed_executable_carrier_json_parsing_policy_contract.json"
RCV37 = ROOT / "apexforge/p12_5_rcv_37_canonical_air_transport_json_shape_census.json"
CARRIER = ROOT / "runtimes/dotnet/ApexForge.Runtime/ManagedExecutableCarrier.cs"
FUTURE_DECODER = ROOT / "runtimes/dotnet/ApexForge.Runtime/ManagedExecutableCarrierDecoder.cs"

def req(c, m):
    if not c:
        raise AssertionError(m)

def main():
    print("=== P12.5-RCV-38 MANAGED EXECUTABLE CARRIER JSON PARSING POLICY CONTRACT ===")
    for p in (CONTRACT, RCV37, CARRIER):
        req(p.exists(), f"missing required path: {p}")

    prev = json.loads(RCV37.read_text(encoding="utf-8-sig"))
    req(prev["profile"] == "apexforge.p12.canonical-air-transport-json-shape-census/v1", "RCV-37 profile changed")
    req(prev["fixture_revision"] == "R1_CANONICAL_CONSTRAINT_AND_TYPE_NORMALIZATION_FIX", "RCV-37 repair revision changed")
    req(prev["normalization_findings"]["observed_concrete_object_shape_count"] == 16, "RCV-37 object-shape count changed")
    req(prev["normalization_findings"]["normalized_union_form_count"] == 2, "RCV-37 normalization count changed")
    print("P12_5_RCV_38_RCV37_CONTRACT=PASS")

    data = json.loads(CONTRACT.read_text(encoding="utf-8-sig"))
    req(data["profile"] == "apexforge.p12.managed-executable-carrier-json-parsing-policy-contract/v1", "profile changed")
    req(data["predecessor"]["stage"] == "P12.5-RCV-37", "predecessor changed")

    ctx = data["decoder_context"]
    req(ctx["architecture"] == "SYSTEM_TEXT_JSON_DOM", "decoder architecture changed")
    req(ctx["mechanism"] == "System.Text.Json.JsonDocument_JsonElement", "decoder mechanism changed")
    req(ctx["future_decoder_type"] == "ApexForge.Runtime.ManagedExecutableCarrierDecoder", "future decoder type changed")
    req(ctx["canonical_source"] == "air.serialization.air_to_dict", "canonical source changed")
    req(ctx["explicit_node_discriminator"] is False, "discriminator assumption changed")
    req(ctx["manual_structural_dispatch"] is True, "manual dispatch removed")

    structural = data["structural_dispatch_policy"]
    req(structural["dispatch_basis"] == "EXACT_PROPERTY_SET_PLUS_JSON_VALUE_KIND", "dispatch basis changed")
    for key in (
        "unknown_property_policy",
        "missing_required_property_policy",
        "duplicate_property_policy",
        "unknown_shape_policy",
    ):
        req(structural[key] == "REJECT", f"closed-world policy weakened: {key}")
    req(structural["silent_default_injection"] == "FORBIDDEN", "silent defaults allowed")
    req(structural["property_name_matching"] == "ORDINAL_CASE_SENSITIVE_SNAKE_CASE", "property matching changed")
    req(structural["collection_order"] == "PRESERVE", "collection order policy changed")

    numeric = data["numeric_policy"]
    req(numeric["integer_detection"] == "NUMBER_TOKEN_WITHOUT_DECIMAL_POINT_OR_EXPONENT", "integer detection changed")
    req(numeric["integer_parse"] == "BIGINTEGER_PARSE_RAW_TEXT_INVARIANT_EXACT", "integer parse changed")
    req(numeric["integer_overflow_policy"] == "NOT_APPLICABLE_BIGINTEGER", "integer overflow policy changed")
    req(numeric["float_detection"] == "NUMBER_TOKEN_WITH_DECIMAL_POINT_OR_EXPONENT", "float detection changed")
    req(numeric["float_parse"] == "DOUBLE_PARSE_RAW_TEXT_INVARIANT_BINARY64", "float parse changed")
    req(numeric["negative_zero"] == "PRESERVE_SIGN_BIT", "negative-zero policy changed")
    for key in ("nan_transport", "positive_infinity_transport", "negative_infinity_transport"):
        req(numeric[key] == "REJECT_NON_STRICT_JSON", f"non-finite transport policy changed: {key}")
    req(numeric["nonfinite_semantic_support"] == "NOT_DENIED_BY_CARRIER_MODEL", "non-finite carrier support incorrectly removed")
    req(numeric["nonfinite_transport_status"] == "INCOMPATIBLE_WITH_SELECTED_JSON_DOM_INPUT", "non-finite compatibility status changed")
    req(numeric["nonfinite_future_resolution"] == "REQUIRES_SEPARATE_TRANSPORT_NORMALIZATION_DECISION", "future non-finite resolution changed")

    nulls = data["nullability_policy"]
    req(nulls["allowed_null_fields"] == [
        "AIRParameter.value_type",
        "AIRFunction.return_expression",
        "AIRFunction.return_type",
    ], "allowed null-field set changed")
    req(nulls["all_other_authorized_mapping_fields"] == "NON_NULL", "other fields became nullable")
    req(nulls["null_collection"] == "REJECT", "null collections allowed")
    req(nulls["null_collection_item"] == "REJECT", "null collection items allowed")

    sig = data["shape_signatures"]
    req(sig["AIRIntegerLiteral_OR_AIRFloatLiteral"] == ["value"], "numeric literal signature changed")
    req(sig["AIRStringLiteral_OR_AIRBooleanLiteral"] == ["value"], "scalar literal signature changed")
    req(sig["AIRCallExpression"] == ["target", "arguments", "type_arguments"], "call signature changed")
    req(sig["AIRFunction"] == [
        "id", "name", "parameters", "return_expression", "order",
        "local_bindings", "body", "return_type", "type_parameters"
    ], "function signature changed")

    kinds = data["value_kind_disambiguation"]
    req(kinds["value_object_string"] == "AIRStringLiteral", "string literal dispatch changed")
    req(kinds["value_object_boolean"] == "AIRBooleanLiteral", "boolean literal dispatch changed")
    req(kinds["value_object_number_integer_grammar"] == "AIRIntegerLiteral", "integer literal dispatch changed")
    req(kinds["value_object_number_float_grammar"] == "AIRFloatLiteral", "float literal dispatch changed")
    req(kinds["value_object_other"] == "REJECT", "unsupported value kind no longer rejected")

    norm = data["normalized_union_policy"]
    req(norm["generic_type_string_input"] == "NOT_EXPECTED_AFTER_CANONICAL_AIR_NORMALIZATION", "generic string policy changed")
    req(norm["constraint_string_input"] == "NOT_EXPECTED_AFTER_CANONICAL_AIR_NORMALIZATION", "constraint string policy changed")
    req(norm["managed_named_type_reference"] == "NOT_CONSTRUCTED_FROM_CANONICAL_TRANSPORT_IN_INITIAL_DECODER", "named type policy changed")
    req(norm["managed_named_constraint_reference"] == "NOT_CONSTRUCTED_FROM_CANONICAL_TRANSPORT_IN_INITIAL_DECODER", "named constraint policy changed")
    req(norm["managed_apex_type_reference"] == "PRIMARY_CANONICAL_TYPE_TARGET", "ApexType target changed")
    req(norm["managed_apex_type_constraint_reference"] == "PRIMARY_CANONICAL_CONSTRAINT_TARGET", "constraint target changed")

    if FUTURE_DECODER.exists():
        req((ROOT / "apexforge/p12_5_rcv_43_managed_executable_carrier_decoder_implementation.json").exists(), "later decoder implementation lacks RCV-43 lineage")

    boundary = data["boundary"]
    req(boundary["decoder_method_shape"] == "UNSELECTED", "decoder method shape selected too early")
    req(boundary["decoder_input_root"] == "UNSELECTED", "decoder input root selected too early")
    req(boundary["decoder_implementation"] == "DEFERRED", "decoder implementation selected")
    req(boundary["runtime_crossing"] == "NOT_AUTHORIZED", "runtime crossing authorized")
    req(boundary["external_serialization"] == "UNSELECTED", "external serialization selected")
    req(boundary["cross_runtime_transport"] == "DEFERRED_NO_TRANSPORT_AUTHORIZED", "cross-runtime transport selected")
    req(boundary["target_neutral_handoff_coupling"] is False, "handoff coupling selected")
    req(boundary["execution_dispatch"] == "DEFERRED", "execution dispatch selected")

    auth = data["authority"]
    req(auth["language_semantics"] == "CANONICAL_AIR", "semantic authority changed")
    req(auth["parser_is_structural_projection_only"] is True, "parser role widened")
    req(auth["parser_may_reinterpret_semantics"] is False, "parser gained reinterpretation authority")
    req(auth["parser_may_execute"] is False, "parser gained execution authority")
    req(auth["parser_may_dispatch"] is False, "parser gained dispatch authority")
    req(auth["parser_may_select_transport"] is False, "parser gained transport authority")

    req(data["historical_identity_claim"] is False, "historical identity improperly claimed")
    req(data["implementation"] == "DEFERRED", "implementation selected during policy gate")

    print("P12_5_RCV_38_PROFILE=apexforge.p12.managed-executable-carrier-json-parsing-policy-contract/v1")
    print("P12_5_RCV_38_DISPATCH_BASIS=EXACT_PROPERTY_SET_PLUS_JSON_VALUE_KIND")
    print("P12_5_RCV_38_UNKNOWN_PROPERTY_POLICY=REJECT")
    print("P12_5_RCV_38_DUPLICATE_PROPERTY_POLICY=REJECT")
    print("P12_5_RCV_38_INTEGER_PARSE=BIGINTEGER_PARSE_RAW_TEXT_INVARIANT_EXACT")
    print("P12_5_RCV_38_FLOAT_PARSE=DOUBLE_PARSE_RAW_TEXT_INVARIANT_BINARY64")
    print("P12_5_RCV_38_NEGATIVE_ZERO=PRESERVE_SIGN_BIT")
    print("P12_5_RCV_38_NONFINITE_TRANSPORT=REJECT_NON_STRICT_JSON")
    print("P12_5_RCV_38_NONFINITE_SEMANTIC_SUPPORT=NOT_DENIED_BY_CARRIER_MODEL")
    print("P12_5_RCV_38_ALLOWED_NULL_FIELD_COUNT=3")
    print("P12_5_RCV_38_CANONICAL_TYPE_STRING_INPUT_EXPECTED=False")
    print("P12_5_RCV_38_CANONICAL_CONSTRAINT_STRING_INPUT_EXPECTED=False")
    print("P12_5_RCV_38_DECODER_METHOD_SHAPE=UNSELECTED")
    print("P12_5_RCV_38_DECODER_INPUT_ROOT=UNSELECTED")
    print("P12_5_RCV_38_DECODER_IMPLEMENTATION=DEFERRED")
    print("P12_5_RCV_38_RUNTIME_CROSSING=NOT_AUTHORIZED")
    print("P12_5_RCV_38_LANGUAGE_SEMANTIC_AUTHORITY=CANONICAL_AIR")
    print("P12_5_RCV_38_EXECUTION_DISPATCH=DEFERRED")
    print("P12_5_RCV_38_MANAGED_EXECUTABLE_CARRIER_JSON_PARSING_POLICY_CONTRACT=PASS")
    print("P12_5_RCV_38_NEXT=P12.5-RCV-39_MANAGED_EXECUTABLE_CARRIER_DECODER_INPUT_ROOT_CENSUS")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
