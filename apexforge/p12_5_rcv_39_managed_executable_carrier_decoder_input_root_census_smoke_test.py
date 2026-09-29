from __future__ import annotations

import json
import sys
from dataclasses import fields
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APEX = ROOT / "apexforge"
sys.path.insert(0, str(APEX))

CONTRACT = ROOT / "apexforge/p12_5_rcv_39_managed_executable_carrier_decoder_input_root_census.json"
RCV38 = ROOT / "apexforge/p12_5_rcv_38_managed_executable_carrier_json_parsing_policy_contract.json"
LOWERING = ROOT / "apexforge/native_backend/lowering_input.py"
HANDOFF = ROOT / "runtimes/dotnet/ApexForge.Runtime/TargetNeutralLoweringHandoff.cs"
FUTURE_DECODER = ROOT / "runtimes/dotnet/ApexForge.Runtime/ManagedExecutableCarrierDecoder.cs"
RUNTIME_DIR = ROOT / "runtimes/dotnet/ApexForge.Runtime"
HOST_DIR = ROOT / "runtimes/dotnet/ApexForge.Runtime.Host"

EXPECTED_DATACLASS_FIELDS = [
    "version",
    "states",
    "events",
    "authority_checks",
    "causal_decisions",
    "directives",
    "requirements",
    "authorities",
    "principals",
    "roles",
    "functions",
    "workflows",
]

EXPECTED_EMPTY_SERIALIZED_FIELDS = EXPECTED_DATACLASS_FIELDS[:-1]

EXPECTED_EMPTY_TRANSPORT_FIELDS = [
    "authorities",
    "authority_checks",
    "causal_decisions",
    "directives",
    "events",
    "functions",
    "principals",
    "requirements",
    "roles",
    "states",
    "version",
]

EXPECTED_WORKFLOW_TRANSPORT_FIELDS = sorted(EXPECTED_DATACLASS_FIELDS)

def req(c, m):
    if not c:
        raise AssertionError(m)

def main():
    print("=== P12.5-RCV-39 MANAGED EXECUTABLE CARRIER DECODER INPUT ROOT CENSUS ===")
    for p in (CONTRACT, RCV38, LOWERING, HANDOFF, RUNTIME_DIR, HOST_DIR):
        req(p.exists(), f"missing required path: {p}")

    prev = json.loads(RCV38.read_text(encoding="utf-8-sig"))
    req(prev["profile"] == "apexforge.p12.managed-executable-carrier-json-parsing-policy-contract/v1", "RCV-38 profile changed")
    req(prev["boundary"]["decoder_input_root"] == "UNSELECTED", "RCV-38 input root unexpectedly selected")
    print("P12_5_RCV_39_RCV38_CONTRACT=PASS")

    data = json.loads(CONTRACT.read_text(encoding="utf-8-sig"))
    req(data["profile"] == "apexforge.p12.managed-executable-carrier-decoder-input-root-census/v1", "profile changed")
    req(data["predecessor"]["stage"] == "P12.5-RCV-38", "predecessor changed")

    from air.model import (
        AIRProgram,
        AIRWorkflow,
        AIRWorkflowInvocation,
        VerifiedAIRProgram,
    )
    from air.serialization import air_to_dict
    from air.functions import AIRFunction
    from native_backend.lowering_input import build_verified_air_lowering_input

    root_fields = [f.name for f in fields(AIRProgram)]
    req(root_fields == EXPECTED_DATACLASS_FIELDS, f"AIRProgram root field topology changed: {root_fields}")

    empty_program = AIRProgram(
        version="rcv39",
        states=(),
        events=(),
        authority_checks=(),
        causal_decisions=(),
        directives=(),
        requirements=(),
        authorities=(),
        principals=(),
        roles=(),
        functions=(),
    )
    verified_empty = VerifiedAIRProgram(empty_program)
    lowering_empty = build_verified_air_lowering_input(verified_empty)
    serialized_empty = air_to_dict(empty_program)
    root_empty = json.loads(lowering_empty.transport_json)

    req(isinstance(root_empty, dict), "canonical transport root is not a JSON object")
    req(list(serialized_empty.keys()) == EXPECTED_EMPTY_SERIALIZED_FIELDS, f"empty air_to_dict root keys changed: {list(serialized_empty.keys())}")
    req("workflows" not in serialized_empty, "empty workflows field was not compatibility-omitted")
    req(list(root_empty.keys()) == EXPECTED_EMPTY_TRANSPORT_FIELDS, f"empty canonical transport root keys changed: {list(root_empty.keys())}")
    req(list(root_empty.keys()) == sorted(root_empty), "empty canonical transport root keys are not sorted")
    req(isinstance(root_empty["functions"], list), "functions subtree is not a JSON array")
    req(root_empty["functions"] == [], "empty functions tuple did not serialize to empty JSON array")

    one_function = AIRFunction(
        id="fn-root",
        name="RootProbe",
        parameters=(),
        return_expression=None,
    )
    one_program = AIRProgram(
        version="rcv39",
        states=(),
        events=(),
        authority_checks=(),
        causal_decisions=(),
        directives=(),
        requirements=(),
        authorities=(),
        principals=(),
        roles=(),
        functions=(one_function,),
    )
    lowering_one = build_verified_air_lowering_input(VerifiedAIRProgram(one_program))
    root_one = json.loads(lowering_one.transport_json)

    req(isinstance(root_one["functions"], list), "functions subtree changed JSON kind")
    req(len(root_one["functions"]) == 1, "single function transport count changed")
    req(isinstance(root_one["functions"][0], dict), "individual function is not a JSON object")
    req(root_one["functions"][0]["id"] == "fn-root", "function identity field changed")
    req(root_one["functions"][0]["name"] == "RootProbe", "function name field changed")

    workflow_program = AIRProgram(
        version="rcv39",
        states=(),
        events=(),
        authority_checks=(),
        causal_decisions=(),
        directives=(),
        requirements=(),
        authorities=(),
        principals=(),
        roles=(),
        functions=(one_function,),
        workflows=(
            AIRWorkflow(
                id="workflow:RootProbe",
                name="RootProbe",
                invocations=(AIRWorkflowInvocation(target="RootProbe"),),
            ),
        ),
    )
    serialized_workflow = air_to_dict(workflow_program)
    lowering_workflow = build_verified_air_lowering_input(
        VerifiedAIRProgram(workflow_program)
    )
    root_workflow = json.loads(lowering_workflow.transport_json)

    req(list(serialized_workflow.keys()) == EXPECTED_DATACLASS_FIELDS, f"non-empty workflow air_to_dict root keys changed: {list(serialized_workflow.keys())}")
    req(list(root_workflow.keys()) == EXPECTED_WORKFLOW_TRANSPORT_FIELDS, f"non-empty workflow transport root keys changed: {list(root_workflow.keys())}")
    req(root_workflow["workflows"] == [{"id": "workflow:RootProbe", "invocations": [{"target": "RootProbe"}], "name": "RootProbe"}], "non-empty workflow transport shape changed")

    lowering_text = LOWERING.read_text(encoding="utf-8-sig")
    req("data = air_to_dict(verified.program)" in lowering_text, "canonical lowering root source changed")
    req("transport_json = json.dumps(" in lowering_text, "canonical transport encoder missing")
    req("sort_keys=True" in lowering_text, "canonical transport key sorting changed")

    transport = data["canonical_transport"]
    req(transport["producer"] == "apexforge.native_backend.build_verified_air_lowering_input", "transport producer changed")
    req(transport["source_expression"] == "air_to_dict(verified.program)", "transport source expression changed")
    req(transport["container"] == "VerifiedAIRLoweringInput.transport_json", "transport container changed")
    req(transport["root_semantic_type"] == "air.model.AIRProgram", "root semantic type changed")
    req(transport["root_json_kind"] == "OBJECT", "root JSON kind changed")
    req(transport["whole_program_transport"] is True, "whole-program transport classification changed")

    root_contract = data["air_program_root_expectations"]
    req(root_contract["dataclass_field_count"] == 12, "AIRProgram dataclass field count changed")
    req(root_contract["dataclass_fields"] == EXPECTED_DATACLASS_FIELDS, "AIRProgram dataclass root field contract changed")
    req(root_contract["empty_air_to_dict_field_count"] == 11, "empty air_to_dict field count changed")
    req(root_contract["empty_air_to_dict_fields"] == EXPECTED_EMPTY_SERIALIZED_FIELDS, "empty air_to_dict field contract changed")
    req(root_contract["empty_transport_fields"] == EXPECTED_EMPTY_TRANSPORT_FIELDS, "empty transport field contract changed")
    req(root_contract["nonempty_workflow_transport_fields"] == EXPECTED_WORKFLOW_TRANSPORT_FIELDS, "non-empty workflow transport field contract changed")
    req(root_contract["empty_workflows_omitted_for_historical_compatibility"] is True, "workflow compatibility policy changed")
    req(root_contract["nonempty_workflows_serialized"] is True, "non-empty workflow serialization policy changed")
    req(root_contract["transport_keys_sorted"] is True, "transport sorting policy changed")
    req(root_contract["functions_field_json_kind"] == "ARRAY", "functions JSON kind changed")
    req(root_contract["functions_field_required_in_structural_serialization"] is True, "functions field requirement changed")

    subtree = data["carrier_relevant_subtree"]
    req(subtree["json_path"] == "$.functions", "carrier subtree path changed")
    req(subtree["semantic_type"] == "tuple[AIRFunction,...]", "carrier subtree semantic type changed")
    req(subtree["json_kind"] == "ARRAY", "carrier subtree JSON kind changed")
    req(subtree["individual_item_semantic_type"] == "AIRFunction", "carrier item type changed")
    req(subtree["individual_item_json_kind"] == "OBJECT", "carrier item JSON kind changed")
    req(subtree["carrier_primary_target"] == "ManagedExecutableFunction", "carrier primary target changed")

    handoff = HANDOFF.read_text(encoding="utf-8-sig")
    req("ManagedExecutableFunction" not in handoff, "target-neutral handoff unexpectedly contains functions")
    req("functions" not in handoff.casefold(), "target-neutral handoff unexpectedly contains functions payload")

    seams = data["existing_seam_census"]
    req(seams["whole_program_transport_exists"] is True, "whole-program seam disappeared")
    for key in (
        "functions_only_transport_exists",
        "individual_function_transport_exists",
        "managed_decoder_exists",
        "managed_decoder_method_exists",
        "program_to_functions_extraction_bridge_exists",
        "target_neutral_handoff_contains_functions",
    ):
        req(seams[key] is False, f"unexpected seam appeared: {key}")

    if FUTURE_DECODER.exists():
        req((ROOT / "apexforge/p12_5_rcv_43_managed_executable_carrier_decoder_implementation.json").exists(), "later decoder implementation lacks RCV-43 lineage")

    refs = []
    for directory in (RUNTIME_DIR, HOST_DIR):
        for p in sorted(directory.glob("*.cs")):
            text = p.read_text(encoding="utf-8-sig")
            hits = [token for token in ("ManagedExecutableCarrierDecoder", "ManagedExecutableFunction[]", "IReadOnlyList<ManagedExecutableFunction>") if token in text]
            if hits:
                refs.append((p.relative_to(ROOT).as_posix(), hits))
    if refs:
        req({path for path, _ in refs} == {"runtimes/dotnet/ApexForge.Runtime/ManagedExecutableCarrierDecoder.cs"}, f"decoder entered unauthorized surfaces: {refs[:8]}")
        req((ROOT / "apexforge/p12_5_rcv_43_managed_executable_carrier_decoder_implementation.json").exists(), "later decoder implementation lacks RCV-43 lineage")

    candidates = data["candidate_input_roots"]
    req([x["id"] for x in candidates] == [
        "WHOLE_CANONICAL_AIR_DOCUMENT",
        "FUNCTIONS_ARRAY_SUBTREE",
        "INDIVIDUAL_FUNCTION_OBJECT",
    ], "candidate input-root set changed")
    req(candidates[0]["status"] == "CANDIDATE_EXISTING_CANONICAL_SEAM", "whole-document seam classification changed")
    req(candidates[1]["status"] == "CANDIDATE_NO_EXISTING_TRANSPORT_SEAM", "functions-subtree classification changed")
    req(candidates[2]["status"] == "CANDIDATE_NO_EXISTING_TRANSPORT_SEAM", "individual-function classification changed")

    unresolved = data["unresolved"]
    for key in (
        "decoder_input_root",
        "decoder_method_shape",
        "program_metadata_validation_scope",
        "empty_functions_behavior",
        "multiple_functions_behavior",
        "function_selection_behavior",
    ):
        req(unresolved[key] == "UNSELECTED", f"root policy selected during census: {key}")
    req(unresolved["decoder_implementation"] == "DEFERRED", "decoder implementation selected")

    boundary = data["boundary"]
    req(boundary["runtime_crossing"] == "NOT_AUTHORIZED", "runtime crossing authorized")
    req(boundary["external_serialization"] == "UNSELECTED", "external serialization selected")
    req(boundary["cross_runtime_transport"] == "DEFERRED_NO_TRANSPORT_AUTHORIZED", "transport selected")
    req(boundary["target_neutral_handoff_coupling"] is False, "handoff coupling selected")
    req(boundary["execution_dispatch"] == "DEFERRED", "execution dispatch selected")

    auth = data["authority"]
    req(auth["language_semantics"] == "CANONICAL_AIR", "semantic authority changed")
    req(auth["census_changes_transport"] is False, "census changed transport")
    req(auth["census_changes_serializer"] is False, "census changed serializer")
    req(auth["census_changes_carrier"] is False, "census changed carrier")
    req(auth["census_selects_input_root"] is False, "census selected input root")

    print("P12_5_RCV_39_PROFILE=apexforge.p12.managed-executable-carrier-decoder-input-root-census/v1")
    print("P12_5_RCV_39_CANONICAL_TRANSPORT_ROOT=WHOLE_AIR_PROGRAM")
    print("P12_5_RCV_39_CANONICAL_TRANSPORT_ROOT_JSON_KIND=OBJECT")
    print("P12_5_RCV_39_FIXTURE_REVISION=R2_DATACLASS_SERIALIZATION_TRANSPORT_TOPOLOGY_FIX")
    print("P12_5_RCV_39_PRIOR_FAILURE_CLASS=TEST_FIXTURE_DEFECT")
    print("P12_5_RCV_39_AIR_PROGRAM_DATACLASS_FIELD_COUNT=12")
    print("P12_5_RCV_39_EMPTY_AIR_TO_DICT_FIELD_COUNT=11")
    print("P12_5_RCV_39_EMPTY_WORKFLOWS_COMPATIBILITY_OMITTED=True")
    print("P12_5_RCV_39_NONEMPTY_WORKFLOWS_SERIALIZED=True")
    print("P12_5_RCV_39_TRANSPORT_KEYS_SORTED=True")
    print("P12_5_RCV_39_CARRIER_RELEVANT_SUBTREE=$.functions")
    print("P12_5_RCV_39_FUNCTIONS_SUBTREE_JSON_KIND=ARRAY")
    print("P12_5_RCV_39_INDIVIDUAL_FUNCTION_JSON_KIND=OBJECT")
    print("P12_5_RCV_39_WHOLE_PROGRAM_TRANSPORT_EXISTS=True")
    print("P12_5_RCV_39_FUNCTIONS_ONLY_TRANSPORT_EXISTS=False")
    print("P12_5_RCV_39_INDIVIDUAL_FUNCTION_TRANSPORT_EXISTS=False")
    print("P12_5_RCV_39_PROGRAM_TO_FUNCTIONS_EXTRACTION_BRIDGE_EXISTS=False")
    print("P12_5_RCV_39_DECODER_INPUT_ROOT=UNSELECTED")
    print("P12_5_RCV_39_DECODER_METHOD_SHAPE=UNSELECTED")
    print("P12_5_RCV_39_DECODER_IMPLEMENTATION=DEFERRED")
    print("P12_5_RCV_39_RUNTIME_CROSSING=NOT_AUTHORIZED")
    print("P12_5_RCV_39_LANGUAGE_SEMANTIC_AUTHORITY=CANONICAL_AIR")
    print("P12_5_RCV_39_EXECUTION_DISPATCH=DEFERRED")
    print("P12_5_RCV_39_MANAGED_EXECUTABLE_CARRIER_DECODER_INPUT_ROOT_CENSUS=PASS")
    print("P12_5_RCV_39_NEXT=P12.5-RCV-40_MANAGED_EXECUTABLE_CARRIER_DECODER_INPUT_ROOT_DECISION")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
