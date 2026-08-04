"""AIR JSON serialization utilities."""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from pathlib import Path

from air.model import (
    AIRAuthority,
    AIRDirective,
    AIRProgram,
    AIRRole,
    AIRRoleAuthority,
    AIRWorkflow,
    AIRWorkflowInvocation,
    DirectiveAuthority,
    DirectiveRequirement,
    EventDefinition,
    EventEmission,
    Fact,
    PrincipalAuthority,
    StateAssignment,
    StateDefinition,
)
from authority.model import AuthorityCheck, Principal
from causality.model import (
    CausalDecision,
    CausalPath,
    DirectiveInvocation,
)


class LegacyDirectiveAuthorityMigrationError(ValueError):
    """Historical flattened directive authorities cannot be migrated safely."""


class AmbiguousLegacyDirectiveAuthorityError(
    LegacyDirectiveAuthorityMigrationError
):
    """Historical authority references have more than one possible owner."""


def _to_data(value):
    if is_dataclass(value):
        return {
            key: _to_data(item)
            for key, item in asdict(value).items()
        }

    if isinstance(value, tuple):
        return [_to_data(item) for item in value]

    if isinstance(value, list):
        return [_to_data(item) for item in value]

    if isinstance(value, dict):
        return {
            key: _to_data(item)
            for key, item in value.items()
        }

    return value


def air_to_dict(program) -> dict:
    data = _to_data(program)

    if isinstance(program, AIRProgram):
        if not program.workflows:
            data.pop("workflows", None)

        for directive, directive_data in zip(
            program.directives,
            data.get("directives", ()),
        ):
            if not directive.authorities:
                directive_data.pop("authorities", None)
    elif isinstance(program, AIRDirective) and not program.authorities:
        data.pop("authorities", None)

    return data


def save_air_json(program, path: str) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)

    output.write_text(
        json.dumps(air_to_dict(program), indent=2),
        encoding="utf-8",
    )


def load_air_dict(path: str) -> dict:
    input_path = Path(path)

    return json.loads(
        input_path.read_text(encoding="utf-8")
    )


def _facts_from_data(items) -> tuple[Fact, ...]:
    return tuple(
        Fact(
            key=item["key"],
            value=item["value"],
        )
        for item in items
    )


def _invocations_from_data(items) -> tuple[DirectiveInvocation, ...]:
    return tuple(
        DirectiveInvocation(
            target=item["target"],
        )
        for item in items
    )


def _principal_authorities_from_data(items) -> tuple[PrincipalAuthority, ...]:
    return tuple(
        PrincipalAuthority(
            name=item["name"] if isinstance(item, dict) else item
        )
        for item in items
    )


def _role_authorities_from_data(items) -> tuple[AIRRoleAuthority, ...]:
    return tuple(
        AIRRoleAuthority(name=item["name"] if isinstance(item, dict) else item)
        for item in items
    )


def _directive_authorities_from_data(items) -> tuple[DirectiveAuthority, ...]:
    return tuple(
        DirectiveAuthority(
            name=item["name"] if isinstance(item, dict) else item
        )
        for item in items
    )


def _split_authority_data(items) -> tuple[tuple[dict, ...], tuple[dict, ...]]:
    canonical: list[dict] = []
    legacy: list[dict] = []

    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise ValueError(
                f"AIR authorities[{index}] must be an object."
            )

        if "id" in item and "name" in item:
            canonical.append(item)
            continue

        if (
            "name" in item
            and "id" not in item
            and "capabilities" not in item
            and "inherits" not in item
        ):
            legacy.append(item)
            continue

        raise ValueError(
            f"AIR authorities[{index}] is neither a canonical authority "
            "declaration nor a legacy directive authority reference."
        )

    return tuple(canonical), tuple(legacy)


def air_from_dict(data: dict) -> AIRProgram:
    canonical_authorities, legacy_authorities = _split_authority_data(
        data.get("authorities", ())
    )
    directive_items = tuple(data.get("directives", ()))

    if legacy_authorities:
        if len(directive_items) > 1:
            raise AmbiguousLegacyDirectiveAuthorityError(
                "Legacy program-level directive authority references require "
                "exactly one directive owner; received "
                f"{len(directive_items)} directives."
            )

        if not directive_items:
            raise LegacyDirectiveAuthorityMigrationError(
                "Legacy program-level directive authority references cannot "
                "be migrated because the program has no directive owner."
            )

        if "authorities" in directive_items[0]:
            raise LegacyDirectiveAuthorityMigrationError(
                "Legacy program-level directive authority references cannot "
                "be migrated because the sole directive already has an "
                "explicit authorities field."
            )

        migrated_directive = dict(directive_items[0])
        migrated_directive["authorities"] = legacy_authorities
        directive_items = (migrated_directive,)

    return AIRProgram(
        version=data["version"],
        principals=tuple(
            Principal(
                id=item["id"],
                display_name=item.get("display_name", ""),
                roles=tuple(item.get("roles", ())),
                authorities=_principal_authorities_from_data(
                    item.get("authorities", ())
                ),
            )
            for item in data.get("principals", ())
        ),
        states=tuple(
            StateDefinition(**item)
            for item in data.get("states", ())
        ),
        events=tuple(
            EventDefinition(**item)
            for item in data.get("events", ())
        ),
        authority_checks=tuple(
            AuthorityCheck(**item)
            for item in data.get("authority_checks", ())
        ),
        causal_decisions=tuple(
            CausalDecision(
                id=item["id"],
                cause=item["cause"],
                policy=item.get("policy", "max_weight"),
                paths=tuple(
                    CausalPath(
                        id=path["id"],
                        weight=path["weight"],
                        assignments=tuple(
                            StateAssignment(**assignment)
                            for assignment in path.get("assignments", ())
                        ),
                        emits=tuple(
                            EventEmission(
                                event=emission["event"],
                                facts=_facts_from_data(
                                    emission.get("facts", [])
                                ),
                            )
                            for emission in path.get("emits", ())
                        ),
                        invocations=_invocations_from_data(
                            path.get("invocations", [])
                        ),
                        effects=tuple(path.get("effects", ())),
                        rationale=path.get("rationale", ""),
                    )
                    for path in item.get("paths", ())
                ),
            )
            for item in data.get("causal_decisions", ())
        ),
        directives=tuple(
            AIRDirective(
                id=item["id"],
                name=item["name"],
                principal=item["principal"],
                authority_checks=tuple(item.get("authority_checks", ())),
                causal_decisions=tuple(item.get("causal_decisions", ())),
                order=item.get("order", 0),
                authorities=_directive_authorities_from_data(
                    item.get("authorities", ())
                ),
            )
            for item in directive_items
        ),
        requirements=tuple(
            DirectiveRequirement(**item)
            for item in data.get("requirements", ())
        ),
        authorities=tuple(
            AIRAuthority(
                id=item["id"],
                name=item["name"],
                capabilities=tuple(item.get("capabilities", ())),
                inherits=tuple(item.get("inherits", ())),
            )
            for item in canonical_authorities
        ),
        roles=tuple(
            AIRRole(
                name=item["name"],
                authorities=_role_authorities_from_data(
                    item.get("authorities", ())
                ),
            )
            for item in data.get("roles", ())
        ),
        workflows=tuple(
            AIRWorkflow(
                id=item["id"],
                name=item["name"],
                invocations=tuple(
                    AIRWorkflowInvocation(target=invocation["target"])
                    for invocation in item.get("invocations", ())
                ),
            )
            for item in data.get("workflows", ())
        ),
    )


def load_air_json(path: str) -> AIRProgram:
    return air_from_dict(load_air_dict(path))
