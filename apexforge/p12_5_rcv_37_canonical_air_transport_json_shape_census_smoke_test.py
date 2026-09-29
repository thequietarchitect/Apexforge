from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APEX = ROOT / "apexforge"
sys.path.insert(0, str(APEX))

CONTRACT = ROOT / "apexforge/p12_5_rcv_37_canonical_air_transport_json_shape_census.json"
RCV36_CONTRACT = ROOT / "apexforge/p12_5_rcv_36_managed_executable_carrier_decoder_architecture_decision.json"
SERIALIZATION = ROOT / "apexforge/air/serialization.py"

def req(c, m):
    if not c:
        raise AssertionError(m)

def compact(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

def keys(value):
    req(isinstance(value, dict), f"expected dict, got {type(value).__name__}")
    return list(value.keys())

def main():
    print("=== P12.5-RCV-37 CANONICAL AIR TRANSPORT JSON SHAPE CENSUS ===")
    for p in (CONTRACT, RCV36_CONTRACT, SERIALIZATION):
        req(p.exists(), f"missing required path: {p}")

    prev = json.loads(RCV36_CONTRACT.read_text(encoding="utf-8-sig"))
    req(prev["profile"] == "apexforge.p12.managed-executable-carrier-decoder-architecture-decision/v1", "RCV-36 profile changed")
    req(prev["decision"]["decoder_architecture"] == "SYSTEM_TEXT_JSON_DOM", "RCV-36 decoder architecture changed")
    print("P12_5_RCV_37_RCV36_CONTRACT=PASS")

    data = json.loads(CONTRACT.read_text(encoding="utf-8-sig"))
    req(data["profile"] == "apexforge.p12.canonical-air-transport-json-shape-census/v1", "profile changed")
    req(data["fixture_revision"] == "R1_CANONICAL_CONSTRAINT_AND_TYPE_NORMALIZATION_FIX", "fixture revision changed")

    repair = data["repair_basis"]
    req(repair["prior_failure_class"] == "TEST_FIXTURE_DEFECT", "prior failure misclassified")
    req(repair["canonical_constraint_name"] == "numeric", "canonical constraint name changed")
    req(repair["canonical_constraint_object"] == "type_system.constraints.NUMERIC", "canonical constraint object changed")
    req(repair["canonical_type_fixture"] == "type_system.model.INT", "canonical type fixture changed")
    req(repair["semantic_regression"] is False, "fixture failure misclassified as semantic regression")

    from air.serialization import air_to_dict
    from air.expressions import (
        AIRIntegerLiteral,
        AIRFloatLiteral,
        AIRStringLiteral,
        AIRBooleanLiteral,
        AIRIdentifierReference,
        AIRUnaryExpression,
        AIRBinaryExpression,
        AIRCallExpression,
    )
    from air.functions import (
        AIRParameter,
        AIRLocalBinding,
        AIRFunctionReturn,
        AIRFunctionWhen,
        AIRFunction,
    )
    from type_system.model import INT, ApexType
    from type_system.generics import ApexTypeVariable
    from type_system.constraints import NUMERIC, ApexTypeConstraint

    huge = 170141183460469231731687303715884105728
    variable = ApexTypeVariable("T", "Helper", (NUMERIC,))

    integer = AIRIntegerLiteral(huge)
    floating = AIRFloatLiteral(1.25)
    string = AIRStringLiteral("A😀𐐷")
    boolean = AIRBooleanLiteral(True)
    identifier = AIRIdentifierReference("x")
    unary = AIRUnaryExpression("-", integer)
    binary = AIRBinaryExpression(integer, "+", AIRIntegerLiteral(1))

    # Include both a source spelling and canonical object. AIRCallExpression
    # must normalize both "int" and INT to canonical ApexType objects.
    call = AIRCallExpression(
        target="Helper",
        arguments=(identifier, unary, binary, string, boolean),
        type_arguments=("int", INT, variable),
    )
    req(isinstance(call.type_arguments[0], ApexType), "string GenericTypeLike did not normalize to ApexType")
    req(call.type_arguments[0] is INT, "string GenericTypeLike did not normalize to canonical INT")
    req(call.type_arguments[1] is INT, "canonical INT identity changed")
    req(call.type_arguments[2] is variable, "ApexTypeVariable identity changed")

    parameter = AIRParameter("x", variable)
    local = AIRLocalBinding("y", call)
    returned = AIRFunctionReturn(identifier)
    when = AIRFunctionWhen(boolean, (local, returned), ())
    function = AIRFunction(
        id="fn-1",
        name="Helper",
        parameters=(parameter,),
        return_expression=identifier,
        order=0,
        local_bindings=(local,),
        body=(when,),
        return_type=variable,
        type_parameters=(variable,),
    )

    representatives = {
        "AIRIntegerLiteral": integer,
        "AIRFloatLiteral": floating,
        "AIRStringLiteral": string,
        "AIRBooleanLiteral": boolean,
        "AIRIdentifierReference": identifier,
        "AIRUnaryExpression": unary,
        "AIRBinaryExpression": binary,
        "AIRCallExpression": call,
        "AIRParameter": parameter,
        "AIRLocalBinding": local,
        "AIRFunctionReturn": returned,
        "AIRFunctionWhen": when,
        "AIRFunction": function,
        "ApexType": INT,
        "ApexTypeVariable": variable,
        "ApexTypeConstraint": NUMERIC,
    }

    expected = data["shape_expectations"]
    observed = {}
    for name, value in representatives.items():
        shaped = air_to_dict(value)
        observed[name] = shaped
        req(keys(shaped) == expected[name], f"{name} serialized key shape changed: {keys(shaped)}")

    # Standalone strings remain strings under air_to_dict, but canonical AIR
    # object constructors normalize the two union-like string forms first.
    req(air_to_dict("int") == "int", "standalone GenericTypeLike string conversion changed")
    req(air_to_dict("numeric") == "numeric", "standalone ConstraintLike string conversion changed")
    req(variable.constraints == (NUMERIC,), "canonical constraint normalization changed")

    norm = data["normalization_findings"]
    req(norm["authorized_rcv34_mapping_count"] == 18, "RCV-34 mapping count changed")
    req(norm["observed_concrete_object_shape_count"] == 16, "observed object shape count changed")
    req(norm["normalized_union_form_count"] == 2, "normalized union form count changed")
    req(norm["generic_type_string_normalizes_to"] == "ApexType", "generic type normalization changed")
    req(norm["constraint_string_normalizes_to"] == "ApexTypeConstraint", "constraint normalization changed")
    req(norm["string_generic_type_survives_inside_canonical_air"] is False, "generic string unexpectedly survives canonicalization")
    req(norm["string_constraint_survives_inside_canonical_air"] is False, "constraint string unexpectedly survives canonicalization")
    req(norm["standalone_air_to_dict_string_remains_json_string"] is True, "standalone string behavior changed")

    serialized_text = SERIALIZATION.read_text(encoding="utf-8-sig")
    req("from dataclasses import asdict, is_dataclass" in serialized_text, "canonical structural serializer mechanism changed")
    req("asdict(value)" in serialized_text, "dataclass structural conversion changed")

    serializer = data["serializer"]
    req(serializer["delegate"] == "air.serialization.air_to_dict", "serializer delegate changed")
    req(serializer["mechanism"] == "dataclasses.asdict_recursive_structure", "serializer mechanism changed")
    req(serializer["explicit_node_discriminator"] is False, "discriminator classification changed")
    req(serializer["python_class_identity_preserved"] is False, "class identity classification changed")
    req(serializer["field_names"] == "snake_case", "field naming changed")
    req(serializer["tuple_encoding"] == "JSON_ARRAY", "tuple encoding changed")
    req(serializer["none_encoding"] == "JSON_NULL", "None encoding changed")

    call_shape = observed["AIRCallExpression"]
    req(isinstance(call_shape["arguments"], list), "call arguments did not become list")
    req(isinstance(call_shape["type_arguments"], list), "type arguments did not become list")
    req(all(isinstance(x, dict) for x in call_shape["type_arguments"]), "normalized type arguments did not serialize as structural objects")
    req(call_shape["type_arguments"][0] == call_shape["type_arguments"][1], "equivalent int type arguments diverged after normalization")

    function_shape = observed["AIRFunction"]
    req(isinstance(function_shape["parameters"], list), "function parameters not list-shaped")
    req(isinstance(function_shape["local_bindings"], list), "function local bindings not list-shaped")
    req(isinstance(function_shape["body"], list), "function body not list-shaped")
    req(isinstance(function_shape["type_parameters"], list), "function type parameters not list-shaped")

    optional_function = AIRFunction(
        id="fn-null",
        name="Nulls",
        parameters=(),
        return_expression=None,
        return_type=None,
    )
    optional_shape = air_to_dict(optional_function)
    req(optional_shape["return_expression"] is None, "return_expression None encoding changed")
    req(optional_shape["return_type"] is None, "return_type None encoding changed")

    huge_json = compact(air_to_dict(integer))
    req(str(huge) in huge_json, "arbitrary-precision integer decimal token was altered")

    float_json = compact(air_to_dict(floating))
    req("1.25" in float_json, "normal float token changed")

    negative_zero_json = compact(air_to_dict(AIRFloatLiteral(-0.0)))
    req("-0.0" in negative_zero_json, f"negative zero token not preserved: {negative_zero_json}")

    nan_json = compact(air_to_dict(AIRFloatLiteral(float("nan"))))
    pos_inf_json = compact(air_to_dict(AIRFloatLiteral(float("inf"))))
    neg_inf_json = compact(air_to_dict(AIRFloatLiteral(float("-inf"))))
    req("NaN" in nan_json, f"NaN token behavior changed: {nan_json}")
    req("Infinity" in pos_inf_json and "-Infinity" not in pos_inf_json, f"+Infinity token behavior changed: {pos_inf_json}")
    req("-Infinity" in neg_inf_json, f"-Infinity token behavior changed: {neg_inf_json}")

    decoder = data["decoder_implications"]
    req(decoder["manual_structural_dispatch_required"] is True, "manual structural dispatch removed")
    req(decoder["discriminator_based_dispatch_available"] is False, "discriminator dispatch incorrectly available")
    req(decoder["raw_number_text_required_for_big_integer"] is True, "raw big-integer token requirement removed")
    req(decoder["shape_collision_analysis_required"] is True, "shape collision analysis requirement removed")
    req(decoder["special_float_policy_required_before_decoder_implementation"] is True, "special float policy requirement removed")
    req(decoder["unknown_shape_rejection_required"] is True, "unknown-shape rejection removed")
    req(decoder["normalized_type_and_constraint_shapes_should_be_primary"] is True, "normalization implication removed")

    boundary = data["boundary"]
    req(boundary["decoder_architecture"] == "SYSTEM_TEXT_JSON_DOM", "decoder architecture changed")
    req(boundary["decoder_implementation"] == "DEFERRED", "decoder implementation selected")
    req(boundary["runtime_crossing"] == "NOT_AUTHORIZED", "runtime crossing authorized")
    req(boundary["external_serialization"] == "UNSELECTED", "external serialization selected")
    req(boundary["cross_runtime_transport"] == "DEFERRED_NO_TRANSPORT_AUTHORIZED", "cross-runtime transport selected")
    req(boundary["execution_dispatch"] == "DEFERRED", "execution dispatch selected")

    print("P12_5_RCV_37_PROFILE=apexforge.p12.canonical-air-transport-json-shape-census/v1")
    print("P12_5_RCV_37_FIXTURE_REVISION=R1_CANONICAL_CONSTRAINT_AND_TYPE_NORMALIZATION_FIX")
    print("P12_5_RCV_37_PRIOR_FAILURE_CLASS=TEST_FIXTURE_DEFECT")
    print("P12_5_RCV_37_RCV34_AUTHORIZED_MAPPING_COUNT=18")
    print("P12_5_RCV_37_OBSERVED_CONCRETE_OBJECT_SHAPE_COUNT=16")
    print("P12_5_RCV_37_NORMALIZED_UNION_FORM_COUNT=2")
    print("P12_5_RCV_37_GENERIC_TYPE_STRING_NORMALIZES_TO=ApexType")
    print("P12_5_RCV_37_CONSTRAINT_STRING_NORMALIZES_TO=ApexTypeConstraint")
    print("P12_5_RCV_37_EXPLICIT_NODE_DISCRIMINATOR=False")
    print("P12_5_RCV_37_PYTHON_CLASS_IDENTITY_PRESERVED=False")
    print("P12_5_RCV_37_FIELD_NAMES=snake_case")
    print("P12_5_RCV_37_TUPLE_ENCODING=JSON_ARRAY")
    print("P12_5_RCV_37_NONE_ENCODING=JSON_NULL")
    print("P12_5_RCV_37_BIG_INTEGER_RAW_DECIMAL_PRESERVED=True")
    print("P12_5_RCV_37_NEGATIVE_ZERO_TOKEN_PRESERVED=True")
    print("P12_5_RCV_37_NAN_TOKEN=NaN")
    print("P12_5_RCV_37_POSITIVE_INFINITY_TOKEN=Infinity")
    print("P12_5_RCV_37_NEGATIVE_INFINITY_TOKEN=-Infinity")
    print("P12_5_RCV_37_SPECIAL_FLOAT_STRICT_JSON_COMPATIBLE=False")
    print("P12_5_RCV_37_MANUAL_STRUCTURAL_DISPATCH_REQUIRED=True")
    print("P12_5_RCV_37_SHAPE_COLLISION_ANALYSIS_REQUIRED=True")
    print("P12_5_RCV_37_DECODER_IMPLEMENTATION=DEFERRED")
    print("P12_5_RCV_37_LANGUAGE_SEMANTIC_AUTHORITY=CANONICAL_AIR")
    print("P12_5_RCV_37_EXECUTION_DISPATCH=DEFERRED")
    print("P12_5_RCV_37_CANONICAL_AIR_TRANSPORT_JSON_SHAPE_CENSUS=PASS")
    print("P12_5_RCV_37_NEXT=P12.5-RCV-38_MANAGED_EXECUTABLE_CARRIER_JSON_PARSING_POLICY_CONTRACT")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
