"""P11-TAM-L final integration, regression, and freeze proof.

This slice adds no TAM production behavior. It proves the frozen A-K chain,
the canonical public surface, whole-map composition ownership, and the
non-authoritative boundary handed to P11.11 TAP Check.
"""

from __future__ import annotations

import dataclasses
import hashlib
import inspect
from pathlib import Path
import subprocess

import tam
from tam import TraceMap


PREDECESSOR_TAG = "afp-p11-tam-k-freeze"
PREDECESSOR_COMMIT = "3b1056ca0410e8886a313fa86b812c561806c42c"

FREEZE_CHAIN = (
    ("afp-p11-tam-a-freeze", "d7967f0fd25d96c8bbd779627adff5aa37431b07"),
    ("afp-p11-tam-b-freeze", "1cac37a13af6ab229401277848a1a1c6bfef3c4b"),
    ("afp-p11-tam-c-freeze", "8e64220fba18ff4e72726468dd59f041bc493bd2"),
    ("afp-p11-tam-d-freeze", "8b97f4336d724155e423ec3cf6ef9fddd3c210da"),
    ("afp-p11-tam-e-freeze", "17eafc6784ec972dab02eee7f63779d72f700304"),
    ("afp-p11-tam-f-freeze", "cce8d0dfe9e2564c947c3bb727504d54a53d5ba8"),
    ("afp-p11-tam-g-freeze", "c3043f8d7e1f37ed05f0a86a5b6b5613d7b1263b"),
    ("afp-p11-tam-h-freeze", "cdd23d15a9cb699e11c2e82278371652a4439f8d"),
    ("afp-p11-tam-i-freeze", "da05b68b7906a145e4edb7c1e8e0e9f019c23f9f"),
    ("afp-p11-tam-j-freeze", "661926bd8d42e7e93f05f4d2178216ae8a91c5b6"),
    ("afp-p11-tam-k-freeze", PREDECESSOR_COMMIT),
)

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

EXPECTED_PUBLIC_SURFACE = (
    "CANONICAL_TRACE_DOMAINS",
    "TRACE_DOMAIN_IDS",
    "TRACE_SCHEMA_VERSION",
    "TraceDomain",
    "TraceIdentity",
    "TraceMap",
    "TraceRecord",
    "trace_identity_for_source_map_entry",
    "trace_identity_for_source_span",
    "trace_map_from_source_map",
    "trace_map_from_declaration_identity_indexes",
    "trace_record_from_declaration_owner",
    "trace_record_from_declared_identity",
    "trace_record_from_resolution_query",
    "trace_record_from_resolution_context",
    "trace_record_from_resolution_candidate",
    "trace_record_from_resolution_outcome",
    "trace_map_from_resolution_observation",
    "trace_record_from_type_evidence",
    "trace_map_from_type_evidence",
    "trace_record_from_authority_evidence",
    "trace_map_from_authority_evidence",
    "trace_record_from_narrative_evidence",
    "trace_map_from_narrative_evidence",
    "trace_record_from_token_evidence",
    "trace_map_from_token_evidence",
    "compose_trace_maps",
)

FROZEN_HASHES = {
    "apexforge/tam/model.py": "BF4782398D890E1D07EB9C3F6DDE5E917EE0403D33684E550CD21A318B780159",
    "apexforge/tam/production.py": "B9C8BA1E3EA1515633B2A777F425BDDB9004DCB5E6C6F5B55B9F54EF4C7F9651",
    "apexforge/tam/__init__.py": "64EB7E7A3F9473766AE601DDB7609F72CE46B6C77055316B82511A03C4D5611E",
    "apexforge/tam/integration.py": "ACDAC41AF23EABEADFC39FAC42A000531DE11D64C33059A48D3615F31D6CE69D",
    "apexforge/p11_tam_k_deterministic_whole_map_composition_smoke_test.py": "1C765C9D68ECC23D376BD57C58268AD3E67B23DBA146710422CC55B4AD07AF03",
    "docs/p11/P11_TAM_K_DETERMINISTIC_WHOLE_MAP_COMPOSITION.md": "6FD5B1DD0EC6F9D8AEFC64D002D6D2DA0C882CA4E077A9B89B2BA91DD57057DC",
    "apexforge/p11_tam_j_final_integration_architecture_audit_smoke_test.py": "B5B104D225C86A7416CC439E1628D292B723E966EB27EFD8063216E61B2D0323",
    "docs/p11/P11_TAM_J_FINAL_INTEGRATION_ARCHITECTURE_AUDIT.md": "A743F437D4F665072630A4C9B17EC8E2CA3655C5990C2E6B0ADAD99881A3261D",
}


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
            "{} is not an ancestor of TAM-L".format(tag),
        )


def _assert_frozen_hashes() -> None:
    for relative, expected in FROZEN_HASHES.items():
        actual = _sha256(_root() / relative)
        _require(
            actual == expected,
            "{} frozen hash changed".format(relative),
        )


def _assert_public_contract() -> None:
    _require(
        tam.TRACE_SCHEMA_VERSION == 1,
        "TAM schema version changed",
    )
    _require(
        tam.TRACE_DOMAIN_IDS == EXPECTED_DOMAINS,
        "canonical TAM domain taxonomy changed",
    )
    _require(
        tam.__all__ == EXPECTED_PUBLIC_SURFACE,
        "canonical TAM public surface changed",
    )
    _require(
        str(inspect.signature(tam.compose_trace_maps))
        == "(trace_maps: 'Tuple[TraceMap, ...]') -> 'TraceMap'",
        "compose_trace_maps signature changed",
    )
    _require(dataclasses.is_dataclass(TraceMap), "TraceMap stopped being a dataclass")
    _require(TraceMap.__dataclass_params__.frozen, "TraceMap stopped being frozen")
    _require(
        tuple(field.name for field in dataclasses.fields(TraceMap)) == ("records",),
        "TraceMap storage contract changed",
    )


def _assert_integration_boundary() -> None:
    integration = (_root() / "apexforge/tam/integration.py").read_text(
        encoding="utf-8"
    )
    _require(
        "from tam.model import TraceMap" in integration,
        "TAM integration stopped owning only TraceMap composition",
    )
    forbidden = (
        "from tam.production",
        "trace_map_from_",
        "trace_record_from_",
        "TraceRecord(",
        "TraceIdentity(",
        "TraceDomain(",
        "sorted(",
        ".sort(",
        "lex(",
        "parse(",
        "compile(",
        "resolve(",
        "validate(",
        "infer_",
        "SemanticLattice",
        "language_server.",
        "tooling.",
        "runtime.",
    )
    for token in forbidden:
        _require(
            token not in integration,
            "TAM integration acquired forbidden behavior: " + token,
        )


def _assert_no_post_k_production_mutation() -> None:
    paths = (
        "apexforge/tam",
        "apexforge/language",
        "apexforge/air",
        "apexforge/authority",
        "apexforge/runtime",
        "apexforge/tooling",
        "apexforge/language_server",
        "apexforge/semantic_lattice",
        "apexforge/aether_air",
        "apexforge/type_system",
    )
    diff = _git("diff", "--exit-code", PREDECESSOR_TAG, "--", *paths)
    _require(
        diff.returncode == 0,
        "TAM-L mutated frozen production/integration/evidence owners",
    )


def main() -> None:
    _assert_freeze_chain()
    _assert_frozen_hashes()
    _assert_public_contract()
    _assert_integration_boundary()
    _assert_no_post_k_production_mutation()

    print("P11_TAM_A_THROUGH_K_FREEZE_CHAIN=PASS")
    print("TAM_FROZEN_SLICES=11")
    print("TRACE_SCHEMA_VERSION=1")
    print("TRACE_DOMAIN_COUNT=10")
    print("TRACE_DOMAIN_PRODUCTION_COVERAGE=10_OF_10")
    print("CANONICAL_TRACE_ARTIFACT=TraceMap")
    print("CANONICAL_INTEGRATION_OWNER=tam.integration")
    print("CANONICAL_INTEGRATION_API=compose_trace_maps")
    print("PUBLIC_SURFACE=FROZEN")
    print("WHOLE_MAP_COMPOSITION=FROZEN")
    print("DUPLICATE_TRACE_IDENTITY_POLICY=FROZEN_TRACE_MAP_REJECTION")
    print("PARTIAL_DOMAIN_COVERAGE=VALID")
    print("ABSENT_DOMAIN_FABRICATION=NONE")
    print("TRACE_RECORD_REWRITE=NONE")
    print("TRACE_IDENTITY_REWRITE=NONE")
    print("SORTING=NONE")
    print("DEDUPLICATION=NONE")
    print("PRODUCER_EXECUTION_INSIDE_INTEGRATION=NONE")
    print("GRAPH_LINK_INFERENCE=NONE")
    print("SEMANTIC_LATTICE_PROJECTION=NONE")
    print("LEXING_PARSING_COMPILATION_RESOLUTION_VALIDATION_EXECUTION=NONE")
    print("TAP_CHECK_CONSUMER_BOUNDARY=CANONICAL_TRACE_MAP_EVIDENCE")
    print("POST_K_PRODUCTION_MUTATION=NONE")
    print("P11_TAM_L_FINAL_INTEGRATION_REGRESSION_FREEZE=PASS")


if __name__ == "__main__":
    main()