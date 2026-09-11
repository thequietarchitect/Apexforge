from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json

from air.model import AIRProgram, VerifiedAIRProgram
from air.serialization import air_to_dict


CANONICAL_VERIFIED_AIR_OWNER = "air.model.VerifiedAIRProgram"
CANONICAL_SERIALIZATION_DELEGATE = "air.serialization.air_to_dict"


@dataclass(frozen=True)
class VerifiedAIRLoweringInput:
    verified: VerifiedAIRProgram
    transport_json: str
    transport_fingerprint: str
    source_owner: str = CANONICAL_VERIFIED_AIR_OWNER

    @property
    def program(self) -> AIRProgram:
        return self.verified.program


def build_verified_air_lowering_input(verified: VerifiedAIRProgram) -> VerifiedAIRLoweringInput:
    if not isinstance(verified, VerifiedAIRProgram):
        raise TypeError("Native lowering requires air.model.VerifiedAIRProgram.")

    data = air_to_dict(verified.program)
    transport_json = json.dumps(
        data,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    transport_fingerprint = sha256(transport_json.encode("utf-8")).hexdigest().upper()
    return VerifiedAIRLoweringInput(
        verified=verified,
        transport_json=transport_json,
        transport_fingerprint=transport_fingerprint,
    )
