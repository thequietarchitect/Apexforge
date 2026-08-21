"""P11.11A TAP Check architecture and ownership audit.

Audit-only slice. It freezes ownership and consumer boundaries for the later
TAP Check Audit Ledger without introducing TAP production behavior.
"""

from __future__ import annotations

import dataclasses
import inspect
from pathlib import Path
import subprocess

from governance import (
    CONCORDAT_COURT,
    CONCORDAT_METHODS,
    TAP_CHECK_MODE,
    ConflictEvidence,
    ConflictPosition,
    ConflictReferral,
    route_conflict_evidence,
)
from semantic_lattice import (
    CORE_SEMANTIC_LATTICE_AXES,
    project_tam_traceability_parameter,
)
import tam


PREDECESSOR_TAG = "afp-p11-tam-l-freeze"
PREDECESSOR_COMMIT = "28022e59728f28bfbf60fbc1d811e39b4b672acd"

TAM_FROZEN_HASHES = {
    "apexforge/tam/model.py": "BF4782398D890E1D07EB9C3F6DDE5E917EE0403D33684E550CD21A318B780159",
    "apexforge/tam/production.py": "B9C8BA1E3EA1515633B2A777F425BDDB9004DCB5E6C6F5B55B9F54EF4C7F9651",
    "apexforge/tam/integration.py": "ACDAC41AF23EABEADFC39FAC42A000531DE11D64C33059A48D3615F31D6CE69D",
    "apexforge/tam/__init__.py": "64EB7E7A3F9473766AE601DDB7609F72CE46B6C77055316B82511A03C4D5611E",
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

EXPECTED_TAP_REPORT_CATEGORIES = (
    "active-directives",
    "compiler-transformations",
    "semantic-changes",
    "authority-intervention",
    "optimization-decisions",
    "continuity-effects",
    "narrative-state-changes",
    "convergence-rulings",
    "air-lowering",
    "runtime-results",
)

AUDIT_DOC = "docs/p11/P11_11A_TAP_CHECK_ARCHITECTURE_OWNERSHIP_AUDIT.md"


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
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _assert_predecessor() -> None:
    resolved = _git("rev-parse", "{}^{{}}".format(PREDECESSOR_TAG))
    _require(resolved.returncode == 0, resolved.stderr.strip())
    _require(
        resolved.stdout.strip() == PREDECESSOR_COMMIT,
        "TAM-L freeze target changed",
    )
    ancestry = _git("merge-base", "--is-ancestor", PREDECESSOR_TAG, "HEAD")
    _require(
        ancestry.returncode == 0,
        "TAM-L freeze is not an ancestor of P11.11A",
    )


def _assert_no_existing_dedicated_tap_implementation() -> None:
    package = _root() / "apexforge/tap_check"
    _require(
        not package.exists(),
        "dedicated tap_check package unexpectedly exists at P11.11A boundary",
    )

    tracked = _git("ls-files")
    _require(tracked.returncode == 0, tracked.stderr.strip())
    tap_files = tuple(
        line
        for line in tracked.stdout.splitlines()
        if (
            "/tap_check/" in line
            or line.startswith("apexforge/tap_check/")
            or "p11_11b" in line.lower()
        )
    )
    _require(
        tap_files == (),
        "future TAP implementation files already exist: {!r}".format(tap_files),
    )

    cli = (_root() / "apexforge/tooling/cli.py").read_text(encoding="utf-8")
    _require(
        "tap-check" not in cli,
        "tap-check CLI unexpectedly exists before its integration slice",
    )


def _assert_governance_precedent() -> None:
    _require(
        TAP_CHECK_MODE == "observational",
        "governance TAP_CHECK_MODE changed",
    )
    _require(dataclasses.is_dataclass(ConflictReferral), "ConflictReferral changed")
    _require(
        ConflictReferral.__dataclass_params__.frozen,
        "ConflictReferral stopped being frozen",
    )

    first_evidence = ConflictEvidence(
        id="conflict:TapArchitecture",
        kind="policy",
        subject="TAP Check passive audit ownership",
        positions=(
            ConflictPosition(
                id="position:DedicatedTapOwner",
                statement="TAP owns its audit ledger.",
                weight=60,
            ),
            ConflictPosition(
                id="position:GovernanceReuse",
                statement="Governance remains an evidence owner.",
                weight=40,
            ),
        ),
        source_nodes=("tam:TraceMap", "governance:TAP_CHECK_MODE"),
    )
    first = route_conflict_evidence(first_evidence)
    second = route_conflict_evidence(first_evidence)

    _require(first == second, "governance referral stopped being deterministic")
    _require(first.evidence is first_evidence, "governance replaced supplied evidence")
    _require(first.tap_check_mode == "observational", "TAP mode stopped being observational")
    _require(first.activates_directives is False, "governance TAP precedent became activating")
    _require(first.destination == CONCORDAT_COURT, "policy referral destination changed")
    _require(first.methods == CONCORDAT_METHODS, "policy referral methods changed")

    structural = route_conflict_evidence(
        ConflictEvidence(
            id="conflict:TapStructural",
            kind="structural",
            subject="Structural TAP boundary",
            source_nodes=("tam:TraceMap",),
        )
    )
    authorization = route_conflict_evidence(
        ConflictEvidence(
            id="conflict:TapAuthorization",
            kind="authorization",
            subject="Authorization TAP boundary",
            source_nodes=("authority:existing-owner",),
        )
    )
    _require(not structural.eligible, "TAP could override a structural conflict")
    _require(not authorization.eligible, "TAP could override an authorization denial")
    _require(not structural.activates_directives, "structural referral activated directives")
    _require(not authorization.activates_directives, "authorization referral activated directives")


def _assert_tam_handoff() -> None:
    for relative, expected in TAM_FROZEN_HASHES.items():
        _require(
            _sha256(_root() / relative) == expected,
            "{} frozen hash changed".format(relative),
        )

    _require(tam.TRACE_SCHEMA_VERSION == 1, "TAM schema version changed")
    _require(
        tam.TRACE_DOMAIN_IDS == EXPECTED_DOMAINS,
        "TAM domain taxonomy changed",
    )
    _require(
        str(inspect.signature(tam.compose_trace_maps))
        == "(trace_maps: 'Tuple[TraceMap, ...]') -> 'TraceMap'",
        "TAM whole-map composition signature changed",
    )
    _require(dataclasses.is_dataclass(tam.TraceMap), "TraceMap stopped being a dataclass")
    _require(tam.TraceMap.__dataclass_params__.frozen, "TraceMap stopped being frozen")
    _require(
        tuple(field.name for field in dataclasses.fields(tam.TraceMap)) == ("records",),
        "TraceMap storage contract changed",
    )


def _assert_semantic_lattice_boundary() -> None:
    _require(
        tuple(axis.canonical_id for axis in CORE_SEMANTIC_LATTICE_AXES).count(
            "tam.traceability"
        )
        == 1,
        "tam.traceability axis changed",
    )
    parameter = project_tam_traceability_parameter(
        key="tap-check-boundary",
        value="observational",
    )
    _require(
        parameter.axis_id == "tam.traceability",
        "TAM traceability projection changed axis ownership",
    )


def _assert_audit_contract() -> None:
    text = (_root() / AUDIT_DOC).read_text(encoding="utf-8")

    required = (
        "apexforge/tap_check/",
        "TAP_CHECK_MODE",
        "observational",
        "TraceMap",
        "TapCheckLedgerEntry",
        "TapCheckAuditLedger",
        "audit_trace_map",
        "apexforge tap-check .",
        "user-controlled",
        "diagnostic-only",
        "non-activating",
        "read-only",
        "active-directives",
        "compiler-transformations",
        "semantic-changes",
        "authority-intervention",
        "optimization-decisions",
        "continuity-effects",
        "narrative-state-changes",
        "convergence-rulings",
        "air-lowering",
        "runtime-results",
        "evidence absence",
        "must not be interpreted as a negative result",
        "structural errors",
        "authorization denials",
        "non-overridable",
        "P11.11B",
        "P11.11C",
    )
    normalized_text = " ".join(text.split())
    for token in required:
        _require(
            token in normalized_text,
            "audit contract missing {!r}".format(token),
        )

    positions = tuple(text.index(category) for category in EXPECTED_TAP_REPORT_CATEGORIES)
    _require(
        positions == tuple(sorted(positions)),
        "TAP report category order changed",
    )


def _assert_audit_only() -> None:
    paths = (
        "apexforge/tam",
        "apexforge/governance",
        "apexforge/language",
        "apexforge/air",
        "apexforge/authority",
        "apexforge/runtime",
        "apexforge/tooling",
        "apexforge/language_server",
        "apexforge/semantic_lattice",
        "apexforge/semantic_decision",
        "apexforge/aether_air",
        "apexforge/type_system",
    )
    diff = _git("diff", "--exit-code", PREDECESSOR_TAG, "--", *paths)
    _require(
        diff.returncode == 0,
        "P11.11A mutated predecessor production owners",
    )


def main() -> None:
    _assert_predecessor()
    _assert_no_existing_dedicated_tap_implementation()
    _assert_governance_precedent()
    _assert_tam_handoff()
    _assert_semantic_lattice_boundary()
    _assert_audit_contract()
    _assert_audit_only()

    print("P11_TAM_L_FREEZE_ANCESTRY=PASS")
    print("DEDICATED_TAP_IMPLEMENTATION_AT_ENTRY=NONE")
    print("GOVERNANCE_TAP_CHECK_MODE=observational")
    print("GOVERNANCE_TAP_PRECEDENT=PASSIVE_NON_ACTIVATING")
    print("STRUCTURAL_ERRORS=NON_OVERRIDABLE")
    print("AUTHORIZATION_DENIALS=NON_OVERRIDABLE")
    print("TAP_OWNER=apexforge.tap_check")
    print("TAP_CANONICAL_TRACE_INPUT=TraceMap")
    print("TAP_RESULT_MODEL=DEDICATED_PASSIVE_AUDIT_LEDGER")
    print("TAP_LEDGER_ENTRY_MODEL=TapCheckLedgerEntry")
    print("TAP_LEDGER_MODEL=TapCheckAuditLedger")
    print("TAP_CORE_TRACE_API=audit_trace_map")
    print("TAP_REPORT_CATEGORY_COUNT=10")
    print("TAP_CATEGORY_ORDER=ROADMAP_ORDER")
    print("MISSING_EVIDENCE=NOT_A_NEGATIVE_RESULT")
    print("SEMANTIC_LATTICE_TAM_AXIS=PASSIVE_EXISTING_OWNER")
    print("AUTHORITY_DECISION=EXISTING_OWNER_NOT_TAP")
    print("SEMANTIC_DECISION=EXISTING_OWNER_NOT_TAP")
    print("RUNTIME_EXECUTION=EXISTING_OWNER_NOT_TAP")
    print("CLI_CONTRACT=apexforge_tap-check_DOT")
    print("CLI_MODE=USER_CONTROLLED_DIAGNOSTIC_ONLY_NON_ACTIVATING_READ_ONLY")
    print("P11_11B=MINIMAL_IMMUTABLE_TAP_AUDIT_LEDGER_MODEL")
    print("P11_11C=TRACE_MAP_OBSERVATIONAL_AUDIT_PROJECTION")
    print("P11_11A_PRODUCTION_MUTATION=NONE")
    print("P11_11A_TAP_CHECK_ARCHITECTURE_OWNERSHIP_AUDIT=PASS")


if __name__ == "__main__":
    main()