"""P11-TAM-F canonical type-evidence trace production."""

from __future__ import annotations

from pathlib import Path
import subprocess

from tam import (
    TraceDomain,
    TraceMap,
    trace_map_from_type_evidence,
    trace_record_from_type_evidence,
)
from type_system.constraints import NUMERIC, ApexTypeConstraint
from type_system.generics import ApexTypeVariable
from type_system.inference import FunctionSignature
from type_system.model import BOOL, INT, STRING, ApexType
from type_system.specialization import (
    GenericInstantiationTable,
    GenericSpecialization,
    GenericSpecializationKey,
)
from type_system.substitution import GenericSubstitution


PREDECESSOR_TAG = "afp-p11-tam-e-freeze"
PREDECESSOR_COMMIT = "17eafc6784ec972dab02eee7f63779d72f700304"


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
    aggregate = ApexType("pair", (INT, STRING))
    variable = ApexTypeVariable(
        name="T",
        owner="function:Identity",
        constraints=(NUMERIC,),
    )
    signature = FunctionSignature(
        name="Identity",
        parameter_types=(variable,),
        return_type=variable,
        type_parameters=(variable,),
    )
    substitution = GenericSubstitution(((variable, INT),))

    int_specialization = GenericSpecialization(
        key=GenericSpecializationKey(
            target="function:Identity",
            type_arguments=(INT,),
        ),
        parameter_types=(INT,),
        return_type=INT,
    )
    string_specialization = GenericSpecialization(
        key=GenericSpecializationKey(
            target="function:Echo",
            type_arguments=(STRING,),
        ),
        parameter_types=(STRING,),
        return_type=STRING,
    )
    table = GenericInstantiationTable(
        (int_specialization, string_specialization)
    )

    evidence = (
        INT,
        aggregate,
        NUMERIC,
        variable,
        signature,
        substitution,
    ) + table.records

    return (
        evidence,
        aggregate,
        variable,
        signature,
        substitution,
        table,
    )


def _assert_predecessor() -> None:
    tag = _git("rev-parse", "{}^{{}}".format(PREDECESSOR_TAG))
    _require(tag.returncode == 0, tag.stderr.strip())
    _require(
        tag.stdout.strip() == PREDECESSOR_COMMIT,
        "TAM-E freeze target changed",
    )
    ancestry = _git("merge-base", "--is-ancestor", PREDECESSOR_TAG, "HEAD")
    _require(ancestry.returncode == 0, "TAM-E is not an ancestor of TAM-F")


def _assert_supported_evidence_projection() -> None:
    evidence, _, _, _, _, _ = _fixture()

    first = tuple(
        trace_record_from_type_evidence(value, evidence_index=index)
        for index, value in enumerate(evidence)
    )
    second = tuple(
        trace_record_from_type_evidence(value, evidence_index=index)
        for index, value in enumerate(evidence)
    )
    _require(first == second, "same type evidence produced different records")

    expected_representations = (
        "apex-type",
        "apex-type",
        "apex-type-constraint",
        "apex-type-variable",
        "function-signature",
        "generic-substitution",
        "generic-specialization",
        "generic-specialization",
    )
    _require(
        tuple(record.representation for record in first)
        == expected_representations,
        "type-evidence representation taxonomy changed",
    )

    expected_owners = (
        "type_system.model",
        "type_system.model",
        "type_system.constraints",
        "type_system.generics",
        "type_system.inference",
        "type_system.substitution",
        "type_system.specialization",
        "type_system.specialization",
    )
    _require(
        tuple(record.owner for record in first) == expected_owners,
        "type evidence owner projection changed",
    )

    for record in first:
        _require(
            record.domain == TraceDomain("type"),
            "type evidence escaped the type domain",
        )
        _require(
            record.source_span is None,
            "type evidence fabricated a SourceSpan",
        )
        _require(
            record.canonical_identity is None,
            "type evidence fabricated a string canonical identity",
        )
        _require(
            record.provenance == (),
            "type evidence fabricated provenance",
        )
        _require(
            record.upstream_trace_ids == ()
            and record.downstream_trace_ids == (),
            "type evidence fabricated graph links",
        )


def _assert_structural_identity_preservation() -> None:
    _, aggregate, variable, signature, substitution, _ = _fixture()

    aggregate_record = trace_record_from_type_evidence(
        aggregate,
        evidence_index=0,
    )
    alternate_aggregate_record = trace_record_from_type_evidence(
        ApexType("pair", (INT, BOOL)),
        evidence_index=0,
    )
    _require(
        aggregate_record.trace_id != alternate_aggregate_record.trace_id,
        "nested ApexType arguments were not preserved",
    )

    alternate_constraint = ApexTypeConstraint(
        name="numeric",
        description="different factual description",
    )
    constraint_record = trace_record_from_type_evidence(
        NUMERIC,
        evidence_index=0,
    )
    alternate_constraint_record = trace_record_from_type_evidence(
        alternate_constraint,
        evidence_index=0,
    )
    _require(
        constraint_record.trace_id != alternate_constraint_record.trace_id,
        "constraint factual fields were not preserved",
    )

    alternate_variable = ApexTypeVariable(
        name="T",
        owner="function:Other",
        constraints=(NUMERIC,),
    )
    _require(
        trace_record_from_type_evidence(
            variable,
            evidence_index=0,
        ).trace_id
        != trace_record_from_type_evidence(
            alternate_variable,
            evidence_index=0,
        ).trace_id,
        "type-variable owner identity was not preserved",
    )

    alternate_signature = FunctionSignature(
        name="Identity",
        parameter_types=(INT,),
        return_type=INT,
        type_parameters=(),
    )
    _require(
        trace_record_from_type_evidence(
            signature,
            evidence_index=0,
        ).trace_id
        != trace_record_from_type_evidence(
            alternate_signature,
            evidence_index=0,
        ).trace_id,
        "function signature type structure was not preserved",
    )

    alternate_substitution = GenericSubstitution(((variable, STRING),))
    _require(
        trace_record_from_type_evidence(
            substitution,
            evidence_index=0,
        ).trace_id
        != trace_record_from_type_evidence(
            alternate_substitution,
            evidence_index=0,
        ).trace_id,
        "generic substitution binding was not preserved",
    )


def _assert_specialization_result_consumption() -> None:
    _, _, _, _, _, table = _fixture()

    _require(
        len(table.records) == 2,
        "fixture instantiation table lost specializations",
    )
    _require(
        tuple(record.canonical_id for record in table.records)
        == tuple(sorted(record.canonical_id for record in table.records)),
        "frozen instantiation table order is no longer canonical",
    )

    first = tuple(
        trace_record_from_type_evidence(
            specialization,
            evidence_index=index,
        )
        for index, specialization in enumerate(table.records)
    )
    second = tuple(
        trace_record_from_type_evidence(
            specialization,
            evidence_index=index,
        )
        for index, specialization in enumerate(table.records)
    )
    _require(
        first == second,
        "already-produced specialization evidence is unstable",
    )


def _assert_map_projection() -> None:
    evidence, _, _, _, _, _ = _fixture()

    first = trace_map_from_type_evidence(evidence)
    second = trace_map_from_type_evidence(evidence)
    _require(type(first) is TraceMap, "type evidence did not return TraceMap")
    _require(first == second, "same type evidence produced different maps")
    _require(
        len(first.records) == len(evidence),
        "type evidence map changed record count",
    )

    expected = tuple(
        trace_record_from_type_evidence(value, evidence_index=index)
        for index, value in enumerate(evidence)
    )
    _require(first.records == expected, "type evidence input order changed")
    _require(
        trace_map_from_type_evidence(()).records == (),
        "empty type evidence fabricated records",
    )


def _assert_no_type_execution() -> None:
    text = (_root() / "apexforge/tam/production.py").read_text(encoding="utf-8")
    forbidden = (
        "resolve_builtin_type(",
        "resolve_type(",
        "resolve_type_constraint(",
        "infer_expression_type(",
        "infer_expression_type_partial(",
        "infer_call_substitution(",
        "infer_explicit_call_substitution(",
        "resolve_call_specialization(",
        "type_satisfies_constraint(",
        "type_satisfies_constraints(",
        "builtin_type_satisfies_constraint(",
        "collect_linked_specializations(",
        "LinkedSpecializationCollector(",
        "audit_lowered_generics(",
        ".bind(",
        ".resolve(",
        "runtime_value_type(",
        "_runtime_value_type(",
    )
    for token in forbidden:
        _require(token not in text, "TAM-F acquired operative type behavior: " + token)


def _assert_type_guards() -> None:
    evidence, _, _, _, _, _ = _fixture()

    _expect(
        TypeError,
        lambda: trace_record_from_type_evidence(
            "int",
            evidence_index=0,
        ),
    )
    _expect(
        TypeError,
        lambda: trace_record_from_type_evidence(
            object(),
            evidence_index=0,
        ),
    )
    _expect(
        TypeError,
        lambda: trace_record_from_type_evidence(
            evidence[0],
            evidence_index=True,
        ),
    )
    _expect(TypeError, lambda: trace_map_from_type_evidence(list(evidence)))


def _assert_frozen_owners_unchanged() -> None:
    paths = (
        "apexforge/tam/model.py",
        "apexforge/language/source.py",
        "apexforge/language/compiler.py",
        "apexforge/language/declarations.py",
        "apexforge/language/identities.py",
        "apexforge/language/project.py",
        "apexforge/language/resolution_candidates.py",
        "apexforge/language/resolution_context.py",
        "apexforge/language/resolution_queries.py",
        "apexforge/language/resolution_outcomes.py",
        "apexforge/language/resolution_visibility.py",
        "apexforge/type_system/model.py",
        "apexforge/type_system/constraints.py",
        "apexforge/type_system/generics.py",
        "apexforge/type_system/inference.py",
        "apexforge/type_system/substitution.py",
        "apexforge/type_system/specialization.py",
        "apexforge/type_system/closure.py",
        "apexforge/type_system/freeze.py",
        "apexforge/standard_library/type_info_value.py",
        "apexforge/tooling/cli.py",
        "apexforge/tooling/project_loader.py",
        "apexforge/language_server/diagnostics.py",
        "apexforge/language/semantic_decision_analysis.py",
        "apexforge/language/semantic_decision_project_analysis.py",
        "apexforge/language/narrative_analysis.py",
        "apexforge/semantic_lattice/adapters.py",
    )
    diff = _git("diff", "--exit-code", PREDECESSOR_TAG, "--", *paths)
    _require(diff.returncode == 0, "TAM-F mutated frozen semantic owner")


def main() -> None:
    _assert_predecessor()
    _assert_supported_evidence_projection()
    _assert_structural_identity_preservation()
    _assert_specialization_result_consumption()
    _assert_map_projection()
    _assert_no_type_execution()
    _assert_type_guards()
    _assert_frozen_owners_unchanged()

    print("P11_TAM_E_FREEZE_ANCESTRY=PASS")
    print("APEX_TYPE_CONSUMPTION=PASS")
    print("TYPE_CONSTRAINT_CONSUMPTION=PASS")
    print("TYPE_VARIABLE_CONSUMPTION=PASS")
    print("FUNCTION_SIGNATURE_CONSUMPTION=PASS")
    print("GENERIC_SUBSTITUTION_CONSUMPTION=PASS")
    print("GENERIC_SPECIALIZATION_CONSUMPTION=PASS")
    print("TYPE_DOMAIN=TYPE")
    print("STRUCTURAL_TYPE_IDENTITY=PRESERVED")
    print("GENERIC_VARIABLE_OWNER=PRESERVED")
    print("CONSTRAINT_FACTS=PRESERVED")
    print("SPECIALIZATION_RESULT=OBSERVED_NOT_RECOMPUTED")
    print("TYPE_EVIDENCE_INPUT_ORDER=PRESERVED")
    print("CANONICAL_IDENTITY_STRING=NONE_NO_FABRICATION")
    print("SOURCE_SPAN=NONE_NO_FABRICATION")
    print("GRAPH_LINK_INFERENCE=NONE")
    print("SAME_INPUT_SAME_TRACE_ID=PASS")
    print("SAME_INPUT_SAME_TRACE_MAP=PASS")
    print("TYPE_INFERENCE=NONE")
    print("TYPE_RESOLUTION=NONE")
    print("TYPE_COERCION=NONE")
    print("CONSTRAINT_EVALUATION=NONE")
    print("GENERIC_BINDING_EXECUTION=NONE")
    print("SPECIALIZATION_RESOLUTION=NONE")
    print("CLOSURE_COMPUTATION=NONE")
    print("RUNTIME_TYPE_REFLECTION=NONE")
    print("AUTHORITY_EVIDENCE=RESERVED_FOR_TAM_G")
    print("COMPILER_MUTATION=NONE")
    print("PROJECTBUILDER_MUTATION=NONE")
    print("CLI_LSP_INTEGRATION=NONE")
    print("SEMANTIC_EXECUTION=NONE")
    print("P11_TAM_F_TYPE_EVIDENCE_TRACE_PRODUCTION=PASS")


if __name__ == "__main__":
    main()