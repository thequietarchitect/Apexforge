from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json

from air.serialization import air_to_dict
from workflow.air_runner import RegistryExecutionPlan

from .lowering_input import VerifiedAIRLoweringInput


CANONICAL_EXECUTION_PLAN_OWNER = "workflow.air_runner.RegistryExecutionPlan"


def _program_transport_json(program) -> str:
    return json.dumps(
        air_to_dict(program),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


@dataclass(frozen=True)
class RegistryExecutionPlanBinding:
    lowering_input: VerifiedAIRLoweringInput
    execution_plan: RegistryExecutionPlan
    entry_directive: str
    directive_owner_ids: tuple[str, ...]
    routing_fingerprint: str
    source_owner: str = CANONICAL_EXECUTION_PLAN_OWNER


def bind_registry_execution_plan(
    lowering_input: VerifiedAIRLoweringInput,
    execution_plan: RegistryExecutionPlan,
) -> RegistryExecutionPlanBinding:
    if not isinstance(lowering_input, VerifiedAIRLoweringInput):
        raise TypeError("Execution-plan binding requires VerifiedAIRLoweringInput.")
    if not isinstance(execution_plan, RegistryExecutionPlan):
        raise TypeError("Execution-plan binding requires workflow.air_runner.RegistryExecutionPlan.")

    if _program_transport_json(execution_plan.program) != lowering_input.transport_json:
        raise ValueError("RegistryExecutionPlan program does not match the verified AIR lowering input.")

    directive_owner_ids = tuple(sorted(execution_plan.directive_owners))
    routing_record = {
        "verified_air_fingerprint": lowering_input.transport_fingerprint,
        "entry_directive": execution_plan.entry_directive,
        "directive_owner_ids": list(directive_owner_ids),
    }
    routing_json = json.dumps(
        routing_record,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    routing_fingerprint = sha256(routing_json.encode("utf-8")).hexdigest().upper()

    return RegistryExecutionPlanBinding(
        lowering_input=lowering_input,
        execution_plan=execution_plan,
        entry_directive=execution_plan.entry_directive,
        directive_owner_ids=directive_owner_ids,
        routing_fingerprint=routing_fingerprint,
    )
