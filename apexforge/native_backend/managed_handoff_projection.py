from __future__ import annotations

from dataclasses import dataclass

from .target_neutral_lowering import TargetNeutralLoweringProduct


@dataclass(frozen=True)
class ManagedHandoffProjection:
    schema: str
    verified_air_fingerprint: str
    routing_fingerprint: str
    entry_directive: str
    directive_owner_ids: tuple[str, ...]
    product_fingerprint: str


def project_managed_handoff(
    product: TargetNeutralLoweringProduct,
) -> ManagedHandoffProjection:
    if not isinstance(product, TargetNeutralLoweringProduct):
        raise TypeError(
            "Managed handoff projection requires TargetNeutralLoweringProduct."
        )

    return ManagedHandoffProjection(
        schema=product.schema,
        verified_air_fingerprint=product.verified_air_fingerprint,
        routing_fingerprint=product.routing_fingerprint,
        entry_directive=product.entry_directive,
        directive_owner_ids=tuple(product.directive_owner_ids),
        product_fingerprint=product.product_fingerprint,
    )
