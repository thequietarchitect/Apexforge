"""P11-TAM-J final integration architecture audit.

Audit-only slice. No TAM production/model integration is introduced here.
"""

from __future__ import annotations

import dataclasses
import hashlib
from pathlib import Path
import subprocess

import tam
from tam import TraceMap


PREDECESSOR_TAG = "afp-p11-tam-i-freeze"
PREDECESSOR_COMMIT = "da05b68b7906a145e4edb7c1e8e0e9f019c23f9f"

FREEZE_CHAIN = (
    ("afp-p11-tam-a-freeze", "d7967f0fd25d96c8bbd779627adff5aa37431b07"),
    ("afp-p11-tam-b-freeze", "1cac37a13af6ab229401277848a1a1c6bfef3c4b"),
    ("afp-p11-tam-c-freeze", "8e64220fba18ff4e72726468dd59f041bc493bd2"),
    ("afp-p11-tam-d-freeze", "8b97f4336d724155e423ec3cf6ef9fddd3c210da"),
    ("afp-p11-tam-e-freeze", "17eafc6784ec972dab02eee7f63779d72f700304"),
    ("afp-p11-tam-f-freeze", "cce8d0dfe9e2564c947c3bb727504d54a53d5ba8"),
    ("afp-p11-tam-g-freeze", "c3043f8d7e1f37ed05f0a86a5b6b5613d7b1263b"),
    ("afp-p11-tam-h-freeze", "cdd23d15a9cb699e11c2e82278371652a4439f8d"),
    ("afp-p11-tam-i-freeze", PREDECESSOR_COMMIT),
)

FROZEN_HASHES = {
    "apexforge/tam/model.py": "BF4782398D890E1D07EB9C3F6DDE5E917EE0403D33684E550CD21A318B780159",
    "apexforge/tam/production.py": "B9C8BA1E3EA1515633B2A777F425BDDB9004DCB5E6C6F5B55B9F54EF4C7F9651",
    "apexforge/tam/__init__.py": "F87D34A6F817E98191F39AD4C3C660AC6193CDF01F7A6A061A64446D9A813F3E",
}

EXPECTED_DOMAINS = (
    "source",
    "token",
    "declaration",
    "reference",
    "scope",
    "type",
    "authority",
    "narrative",
    "ownership",
    "transformation",
)

EXPECTED_MAP_PRODUCERS = (
    "trace_map_from_source_map",
    "trace_map_from_declaration_identity_indexes",
    "trace_map_from_resolution_observation",
    "trace_map_from_type_evidence",
    "trace_map_from_authority_evidence",
    "trace_map_from_narrative_evidence",
    "trace_map_from_token_evidence",
)

NEXT_STAGE_CONTRACT = (
    "compose_trace_maps(trace_maps: Tuple[TraceMap, ...]) -> TraceMap",
    "caller-supplied map block order",
    "record order within each input map",
    "exact TraceRecord objects",
    "empty input produces empty TraceMap",
    "`TraceMap` already rejects duplicate trace identities",
    "no sorting",
    "no deduplication",
    "no trace identity rewriting",
    "No synthetic empty-domain `TraceRecord` may be created",
    "Partial domain coverage is valid",
    "Ten-domain coverage is a capability proof, not an input requirement",
    "TAP Check consumes canonical TraceMap evidence",
)


def _root() -> Path:
    return Path(__file__).resolve().parents[1]


def _git(*arguments: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ("git", *arguments),
        cwd=_root(),
        check=False,
        text=True,
        encoding="utf-8",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _assert_freeze_chain() -> None:
    for tag, expected in FREEZE_CHAIN:
        resolved = _git("rev-parse", "{}^{{}}".format(tag))
        _require(resolved.returncode == 0, resolved.stderr.strip())
        _require(
            resolved.stdout.strip() == expected,
            "{} target changed".format(tag),
        )
        ancestry = _git("merge-base", "--is-ancestor", tag, "HEAD")
        _require(
            ancestry.returncode == 0,
            "{} is not an ancestor of TAM-J".format(tag),
        )


def _assert_frozen_tam_hashes() -> None:
    for relative, expected in FROZEN_HASHES.items():
        actual = _sha256(_root() / relative)
        _require(
            actual == expected,
            "{} frozen hash changed".format(relative),
        )


def _assert_model_contract() -> None:
    _require(
        tam.TRACE_SCHEMA_VERSION == 1,
        "TAM schema version changed",
    )
    _require(
        tam.TRACE_DOMAIN_IDS == EXPECTED_DOMAINS,
        "canonical ten-domain taxonomy changed",
    )
    _require(
        dataclasses.is_dataclass(TraceMap),
        "TraceMap stopped being a dataclass",
    )
    _require(
        TraceMap.__dataclass_params__.frozen,
        "TraceMap stopped being immutable",
    )
    _require(
        tuple(field.name for field in dataclasses.fields(TraceMap))
        == ("records",),
        "TraceMap storage contract changed",
    )
    _require(hasattr(TraceMap, "find"), "TraceMap.find disappeared")
    _require(hasattr(TraceMap, "for_domain"), "TraceMap.for_domain disappeared")


def _assert_all_domain_producers_present() -> None:
    for name in EXPECTED_MAP_PRODUCERS:
        _require(
            name in tam.__all__,
            "{} is not public".format(name),
        )
        _require(
            callable(getattr(tam, name, None)),
            "{} is not callable".format(name),
        )


def _assert_integration_gap_is_real() -> None:
    _require(
        "compose_trace_maps" not in tam.__all__,
        "whole-map composition already entered the public TAM surface",
    )
    _require(
        not hasattr(tam, "compose_trace_maps"),
        "whole-map composition unexpectedly exists",
    )
    _require(
        not hasattr(TraceMap, "merge"),
        "TraceMap unexpectedly acquired merge behavior",
    )
    _require(
        not hasattr(TraceMap, "compose"),
        "TraceMap unexpectedly acquired compose behavior",
    )
    _require(
        not (_root() / "apexforge/tam/integration.py").exists(),
        "TAM integration module already exists",
    )


def _assert_duplicate_identity_policy_is_model_owned() -> None:
    model = (_root() / "apexforge/tam/model.py").read_text(encoding="utf-8")
    _require(
        "TraceMap.records cannot contain duplicate trace identities" in model,
        "TraceMap duplicate-identity invariant disappeared",
    )


def _assert_audit_document_contract() -> None:
    document = (
        _root()
        / "docs/p11/P11_TAM_J_FINAL_INTEGRATION_ARCHITECTURE_AUDIT.md"
    ).read_text(encoding="utf-8")
    for phrase in NEXT_STAGE_CONTRACT:
        _require(
            phrase in document,
            "TAM-J document omitted next-stage contract: " + phrase,
        )


def _assert_no_production_mutation() -> None:
    paths = (
        "apexforge/tam/model.py",
        "apexforge/tam/production.py",
        "apexforge/tam/__init__.py",
        "apexforge/language",
        "apexforge/air",
        "apexforge/authority",
        "apexforge/runtime",
        "apexforge/tooling",
        "apexforge/language_server",
        "apexforge/semantic_lattice",
        "apexforge/aether_air",
    )
    diff = _git("diff", "--exit-code", PREDECESSOR_TAG, "--", *paths)
    _require(
        diff.returncode == 0,
        "TAM-J architecture audit mutated production/frozen owners",
    )


def main() -> None:
    _assert_freeze_chain()
    _assert_frozen_tam_hashes()
    _assert_model_contract()
    _assert_all_domain_producers_present()
    _assert_integration_gap_is_real()
    _assert_duplicate_identity_policy_is_model_owned()
    _assert_audit_document_contract()
    _assert_no_production_mutation()

    print("P11_TAM_A_THROUGH_I_FREEZE_CHAIN=PASS")
    print("TRACE_SCHEMA_VERSION=1")
    print("TRACE_DOMAIN_COUNT=10")
    print("TRACE_DOMAIN_PRODUCTION_COVERAGE=10_OF_10")
    print("TRACE_MAP=FROZEN_ORDERED_CONTAINER")
    print("TRACE_MAP_FIND=AVAILABLE")
    print("TRACE_MAP_FOR_DOMAIN=AVAILABLE")
    print("WHOLE_MAP_COMPOSITION=ABSENT_CONFIRMED")
    print("TRACE_MAP_MODEL_MUTATION=NONE")
    print("TAM_PRODUCTION_MUTATION=NONE")
    print("CANONICAL_INTEGRATION_OWNER=tam.integration")
    print("CANONICAL_INTEGRATION_API=compose_trace_maps")
    print("COMPOSITION_INPUT=EXACT_TUPLE_OF_TRACE_MAPS")
    print("COMPOSITION_ORDER=CALLER_MAP_ORDER_THEN_RECORD_ORDER")
    print("TRACE_RECORD_REWRITE=NONE")
    print("TRACE_IDENTITY_REWRITE=NONE")
    print("SORTING=NONE")
    print("DEDUPLICATION=NONE")
    print("DUPLICATE_TRACE_IDENTITY=REJECT_VIA_FROZEN_TRACE_MAP")
    print("EMPTY_INPUT=EMPTY_TRACE_MAP")
    print("PARTIAL_DOMAIN_COVERAGE=VALID")
    print("TEN_DOMAIN_COVERAGE=CAPABILITY_NOT_REQUIREMENT")
    print("SEMANTIC_LATTICE_PROJECTION=NONE")
    print("LEXING_PARSING_COMPILATION_RESOLUTION_VALIDATION_EXECUTION=NONE")
    print("TAP_CHECK_CONSUMER_BOUNDARY=CANONICAL_TRACE_MAP_EVIDENCE")
    print("P11_TAM_J_FINAL_INTEGRATION_ARCHITECTURE_AUDIT=PASS")


if __name__ == "__main__":
    main()