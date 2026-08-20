"""P11-TAM-G canonical authority-evidence trace production."""

from __future__ import annotations

from pathlib import Path
import subprocess

from authority.model import AuthorityCheck, AuthorityGrant, Principal
from tam import (
    TraceDomain,
    TraceMap,
    trace_map_from_authority_evidence,
    trace_record_from_authority_evidence,
)


PREDECESSOR_TAG = "afp-p11-tam-f-freeze"
PREDECESSOR_COMMIT = "cce8d0dfe9e2564c947c3bb727504d54a53d5ba8"


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


def _expect(exc_type, operation):
    try:
        operation()
    except exc_type as error:
        return error
    raise AssertionError("Expected {}.".format(exc_type.__name__))


def _fixture():
    principal = Principal(
        "principal:Operator",
        "Operator",
        ("role:Architect",),
        ("authority:Aegis",),
    )
    check = AuthorityCheck(
        "check:invoke-main",
        "principal:Operator",
        "directive.invoke",
        "directive:Main",
    )
    grant = AuthorityGrant(
        "principal:Operator",
        "directive.invoke",
        "directive:Main",
    )
    return principal, check, grant


def _assert_predecessor() -> None:
    tag = _git("rev-parse", "{}^{{}}".format(PREDECESSOR_TAG))
    _require(tag.returncode == 0, tag.stderr.strip())
    _require(
        tag.stdout.strip() == PREDECESSOR_COMMIT,
        "TAM-F freeze target changed",
    )
    ancestry = _git("merge-base", "--is-ancestor", PREDECESSOR_TAG, "HEAD")
    _require(ancestry.returncode == 0, "TAM-F is not an ancestor of TAM-G")


def _assert_authority_projection() -> None:
    principal, check, grant = _fixture()
    evidence = (principal, check, grant)

    first = tuple(
        trace_record_from_authority_evidence(value, evidence_index=index)
        for index, value in enumerate(evidence)
    )
    second = tuple(
        trace_record_from_authority_evidence(value, evidence_index=index)
        for index, value in enumerate(evidence)
    )
    _require(first == second, "same authority evidence produced different records")

    _require(
        tuple(record.domain for record in first)
        == (
            TraceDomain("authority"),
            TraceDomain("authority"),
            TraceDomain("authority"),
        ),
        "authority evidence escaped authority domain",
    )
    _require(
        tuple(record.representation for record in first)
        == ("principal", "authority-check", "authority-grant"),
        "authority representation taxonomy changed",
    )
    _require(
        tuple(record.producer for record in first)
        == ("authority.model", "authority.model", "authority.model"),
        "authority producer ownership changed",
    )
    _require(
        tuple(record.owner for record in first)
        == ("authority.model", "authority.model", "authority.model"),
        "authority semantic ownership changed",
    )

    _require(
        first[0].canonical_identity == principal.id,
        "principal canonical identity changed",
    )
    _require(
        first[1].canonical_identity == check.id,
        "authority check canonical identity changed",
    )
    _require(
        first[2].canonical_identity is None,
        "ID-less authority grant received fabricated canonical identity",
    )

    for record in first:
        _require(
            record.source_span is None,
            "authority.model evidence fabricated SourceSpan",
        )
        _require(
            record.provenance == (),
            "authority evidence fabricated provenance",
        )
        _require(
            record.upstream_trace_ids == ()
            and record.downstream_trace_ids == (),
            "authority evidence fabricated graph links",
        )


def _assert_principal_subject_boundary() -> None:
    principal, _, _ = _fixture()

    changed_projection = Principal(
        principal.id,
        "Different Display",
        ("role:Different",),
        ("authority:Different",),
    )
    first = trace_record_from_authority_evidence(
        principal,
        evidence_index=0,
    )
    second = trace_record_from_authority_evidence(
        changed_projection,
        evidence_index=0,
    )
    _require(
        first.trace_id == second.trace_id,
        "principal subject trace stopped using canonical Principal.id identity",
    )
    _require(
        first.canonical_identity == principal.id,
        "principal subject lost canonical ID",
    )


def _assert_check_facts_preserved() -> None:
    _, check, _ = _fixture()

    changed = AuthorityCheck(
        check.id,
        check.principal,
        "directive.inspect",
        check.resource,
    )
    first = trace_record_from_authority_evidence(check, evidence_index=0)
    second = trace_record_from_authority_evidence(changed, evidence_index=0)
    _require(
        first.trace_id != second.trace_id,
        "authority check capability fact was not preserved",
    )
    _require(
        first.canonical_identity == second.canonical_identity == check.id,
        "authority check subject identity changed with factual payload",
    )


def _assert_grant_evidence_boundary() -> None:
    _, _, grant = _fixture()

    same = AuthorityGrant(
        grant.principal,
        grant.capability,
        grant.resource,
    )
    changed = AuthorityGrant(
        grant.principal,
        grant.capability,
        "directive:Other",
    )

    first = trace_record_from_authority_evidence(grant, evidence_index=0)
    second = trace_record_from_authority_evidence(same, evidence_index=0)
    third = trace_record_from_authority_evidence(changed, evidence_index=0)

    _require(first == second, "same grant facts produced different TAM evidence")
    _require(
        first.trace_id != third.trace_id,
        "authority grant facts were not preserved",
    )
    _require(
        first.canonical_identity is None,
        "authority grant acquired fabricated canonical identity",
    )


def _assert_map_projection() -> None:
    principal, check, grant = _fixture()
    evidence = (principal, check, grant)

    first = trace_map_from_authority_evidence(evidence)
    second = trace_map_from_authority_evidence(evidence)
    _require(type(first) is TraceMap, "authority evidence did not return TraceMap")
    _require(first == second, "same authority evidence produced different maps")
    _require(
        first.records
        == tuple(
            trace_record_from_authority_evidence(
                value,
                evidence_index=index,
            )
            for index, value in enumerate(evidence)
        ),
        "authority evidence input order changed",
    )
    _require(
        trace_map_from_authority_evidence(()).records == (),
        "empty authority evidence fabricated records",
    )


def _assert_no_authority_execution() -> None:
    text = (_root() / "apexforge/tam/production.py").read_text(encoding="utf-8")
    forbidden = (
        "AuthorityEngine(",
        "AuthorityRegistry(",
        "RoleRegistry(",
        "resolve_effective_authorities(",
        "resolve_capabilities(",
        "has_capability(",
        "project_authority_subject(",
        "project_authority_grant_evidence(",
        "compile_authority(",
        "compile_principal(",
        ".check(",
        ".allows(",
        ".register(",
        ".register_all(",
        "runtime.context",
        "authorization.role_resolver",
    )
    for token in forbidden:
        _require(
            token not in text,
            "TAM-G acquired operative authority behavior: " + token,
        )


def _assert_air_authority_boundary() -> None:
    text = (_root() / "apexforge/tam/production.py").read_text(encoding="utf-8")
    for token in (
        "AIRAuthority",
        "AIRPrincipal",
        "AIRRole",
        "PrincipalAuthority",
        "PrincipalRole",
        "AIRRoleAuthority",
        "DirectiveAuthority",
        "DirectiveRequirement",
    ):
        _require(
            token not in text,
            "TAM-G duplicated AIR-owned authority structure: " + token,
        )


def _assert_type_guards() -> None:
    principal, check, grant = _fixture()

    _expect(
        TypeError,
        lambda: trace_record_from_authority_evidence(
            object(),
            evidence_index=0,
        ),
    )
    _expect(
        TypeError,
        lambda: trace_record_from_authority_evidence(
            principal,
            evidence_index=True,
        ),
    )
    _expect(
        TypeError,
        lambda: trace_map_from_authority_evidence([principal, check, grant]),
    )


def _assert_frozen_owners_unchanged() -> None:
    paths = (
        "apexforge/tam/model.py",
        "apexforge/authority/model.py",
        "apexforge/authority/engine.py",
        "apexforge/authority/registry.py",
        "apexforge/authority/validator.py",
        "apexforge/authorization/role_resolver.py",
        "apexforge/role/registry.py",
        "apexforge/air/model.py",
        "apexforge/air/linker.py",
        "apexforge/air/verify.py",
        "apexforge/semantic_lattice/adapters.py",
        "apexforge/language/source.py",
        "apexforge/language/compiler.py",
        "apexforge/language/declarations.py",
        "apexforge/language/identities.py",
        "apexforge/language/project.py",
        "apexforge/type_system/model.py",
        "apexforge/type_system/constraints.py",
        "apexforge/type_system/generics.py",
        "apexforge/type_system/inference.py",
        "apexforge/type_system/substitution.py",
        "apexforge/type_system/specialization.py",
        "apexforge/tooling/cli.py",
        "apexforge/tooling/project_loader.py",
        "apexforge/language_server/diagnostics.py",
        "apexforge/language/semantic_decision_analysis.py",
        "apexforge/language/semantic_decision_project_analysis.py",
        "apexforge/language/narrative_analysis.py",
    )
    diff = _git("diff", "--exit-code", PREDECESSOR_TAG, "--", *paths)
    _require(diff.returncode == 0, "TAM-G mutated frozen semantic owner")


def main() -> None:
    _assert_predecessor()
    _assert_authority_projection()
    _assert_principal_subject_boundary()
    _assert_check_facts_preserved()
    _assert_grant_evidence_boundary()
    _assert_map_projection()
    _assert_no_authority_execution()
    _assert_air_authority_boundary()
    _assert_type_guards()
    _assert_frozen_owners_unchanged()

    print("P11_TAM_F_FREEZE_ANCESTRY=PASS")
    print("PRINCIPAL_SUBJECT_CONSUMPTION=PASS")
    print("AUTHORITY_CHECK_CONSUMPTION=PASS")
    print("AUTHORITY_GRANT_CONSUMPTION=PASS")
    print("AUTHORITY_DOMAIN=AUTHORITY")
    print("PRINCIPAL_CANONICAL_ID=REFERENCE_ONLY")
    print("AUTHORITY_CHECK_CANONICAL_ID=REFERENCE_ONLY")
    print("AUTHORITY_CHECK_FACTS=PRESERVED")
    print("AUTHORITY_GRANT_FACTS=PRESERVED")
    print("AUTHORITY_GRANT_CANONICAL_IDENTITY=NONE")
    print("PRINCIPAL_SUBJECT_BOUNDARY=ID_ONLY")
    print("AIR_AUTHORITY_STRUCTURE=DISTINCT_OWNER")
    print("AUTHORITY_EVIDENCE_INPUT_ORDER=PRESERVED")
    print("SOURCE_SPAN=NONE_NO_FABRICATION")
    print("GRAPH_LINK_INFERENCE=NONE")
    print("SAME_INPUT_SAME_TRACE_ID=PASS")
    print("SAME_INPUT_SAME_TRACE_MAP=PASS")
    print("AUTHORITY_CHECK_EXECUTION=NONE")
    print("AUTHORITY_GRANT_EXECUTION=NONE")
    print("AUTHORITY_POLICY_EVALUATION=NONE")
    print("AUTHORITY_INHERITANCE_RESOLUTION=NONE")
    print("ROLE_RESOLUTION=NONE")
    print("REGISTRY_LOOKUP=NONE")
    print("AIR_AUTHORITY_DUPLICATION=NONE")
    print("COMPILER_MUTATION=NONE")
    print("PROJECTBUILDER_MUTATION=NONE")
    print("CLI_LSP_INTEGRATION=NONE")
    print("SEMANTIC_EXECUTION=NONE")
    print("P11_TAM_G_AUTHORITY_EVIDENCE_TRACE_PRODUCTION=PASS")


if __name__ == "__main__":
    main()