from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NativeBackendIdentity:
    target_id: str = "NATIVE_BACKEND"
    verified_air_owner: str = "air.model.VerifiedAIRProgram"
    managed_runtime_relationship: str = "SIBLING_TARGET"
    compiler_backend: str = "UNSELECTED"
    object_format: str = "TARGET_DEPENDENT_UNSELECTED"
    linker: str = "UNSELECTED"
    llvm_required: bool = False
    defines_language_semantics: bool = False

    def is_contract_safe(self) -> bool:
        return (
            self.target_id == "NATIVE_BACKEND"
            and self.verified_air_owner == "air.model.VerifiedAIRProgram"
            and self.managed_runtime_relationship == "SIBLING_TARGET"
            and self.compiler_backend == "UNSELECTED"
            and self.llvm_required is False
            and self.defines_language_semantics is False
        )


DEFAULT_NATIVE_BACKEND_IDENTITY = NativeBackendIdentity()
