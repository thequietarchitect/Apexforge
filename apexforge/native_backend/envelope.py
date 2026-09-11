from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class CanonicalExecutionEnvelope:
    verified_air_owner: str
    execution_plan_owner: str
    program_fingerprint: str

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "CanonicalExecutionEnvelope":
        value = cls(
            verified_air_owner=str(data.get("VerifiedAirOwner", "")),
            execution_plan_owner=str(data.get("ExecutionPlanOwner", "")),
            program_fingerprint=str(data.get("ProgramFingerprint", "")),
        )
        value.validate()
        return value

    def validate(self) -> None:
        if self.verified_air_owner != "air.model.VerifiedAIRProgram":
            raise ValueError("Canonical execution ownership mismatch.")
        if self.execution_plan_owner != "workflow.air_runner.RegistryExecutionPlan":
            raise ValueError("Canonical execution ownership mismatch.")
        if not self.program_fingerprint.strip():
            raise ValueError("Program fingerprint is required.")

    def is_contract_safe(self) -> bool:
        try:
            self.validate()
        except ValueError:
            return False
        return True
