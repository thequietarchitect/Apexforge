from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json

from .execution_plan_binding import RegistryExecutionPlanBinding


TARGET_NEUTRAL_LOWERING_SCHEMA = "apexforge.target-neutral-lowering/v1"


@dataclass(frozen=True)
class TargetNeutralLoweringProduct:
    binding: RegistryExecutionPlanBinding
    canonical_json: str
    product_fingerprint: str
    schema: str = TARGET_NEUTRAL_LOWERING_SCHEMA

    @property
    def verified_air_fingerprint(self) -> str:
        return self.binding.lowering_input.transport_fingerprint

    @property
    def routing_fingerprint(self) -> str:
        return self.binding.routing_fingerprint

    @property
    def entry_directive(self) -> str:
        return self.binding.entry_directive

    @property
    def directive_owner_ids(self) -> tuple[str, ...]:
        return self.binding.directive_owner_ids


def lower_target_neutral(binding: RegistryExecutionPlanBinding) -> TargetNeutralLoweringProduct:
    if not isinstance(binding, RegistryExecutionPlanBinding):
        raise TypeError("Target-neutral lowering requires RegistryExecutionPlanBinding.")

    if len(binding.lowering_input.transport_fingerprint) != 64:
        raise ValueError("Verified AIR transport fingerprint is invalid.")
    if len(binding.routing_fingerprint) != 64:
        raise ValueError("Execution-plan routing fingerprint is invalid.")

    record = {
        "schema": TARGET_NEUTRAL_LOWERING_SCHEMA,
        "verified_air_fingerprint": binding.lowering_input.transport_fingerprint,
        "routing_fingerprint": binding.routing_fingerprint,
        "entry_directive": binding.entry_directive,
        "directive_owner_ids": list(binding.directive_owner_ids),
        "canonical_air_transport": binding.lowering_input.transport_json,
    }
    canonical_json = json.dumps(
        record,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    product_fingerprint = sha256(canonical_json.encode("utf-8")).hexdigest().upper()
    return TargetNeutralLoweringProduct(
        binding=binding,
        canonical_json=canonical_json,
        product_fingerprint=product_fingerprint,
    )
