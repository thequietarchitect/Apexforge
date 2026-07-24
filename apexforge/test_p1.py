from __future__ import annotations

import traceback

from language.validation.runtime_validator import (
    RuntimeValidationError,
    VerifiedAIRProgram,
)
from pipeline.execution_pipeline import ExecutionPipeline
from runtime.context import ExecutionContext

from regression.support import (
    AllowAllAuthority,
    DenyAllAuthority,
    TestState,
)


VALID_SOURCE = """
directive Hello {

    event greeted

    cause start {

        path primary @ 1 {

            message "Hello World"

            emit greeted
        }
    }
}
"""


class RegressionSuite:
    def __init__(self) -> None:
        self.passed = 0
        self.failed = 0

    def run_test(self, name: str, test_function) -> None:
        print(f"\n[TEST] {name}")

        try:
            test_function()
        except Exception as exc:
            self.failed += 1
            print(f"[FAIL] {type(exc).__name__}: {exc}")
            traceback.print_exc()
        else:
            self.passed += 1
            print("[PASS]")

    def report(self) -> None:
        total = self.passed + self.failed

        print("\n===================================")
        print(" ApexForge AFP-P1 Regression Report")
        print("===================================")
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        print(f"Total:  {total}")

        if self.failed:
            raise SystemExit(1)

        print("\nAFP-P1 baseline is healthy.")


def make_context(*, allow: bool = True) -> ExecutionContext:
    authority = (
        AllowAllAuthority()
        if allow
        else DenyAllAuthority()
    )

    return ExecutionContext(
        state=TestState(),
        authority=authority,
    )


def test_pipeline_compiles_source() -> None:
    pipeline = ExecutionPipeline()

    program = pipeline.compile_source(VALID_SOURCE)

    assert program is not None
    assert len(program.principals) == 1
    assert len(program.directives) == 1
    assert len(program.events) == 1
    assert len(program.causal_decisions) == 1
    assert len(program.authority_checks) == 1


def test_compiled_identifiers_match() -> None:
    pipeline = ExecutionPipeline()

    program = pipeline.compile_source(VALID_SOURCE)

    event = program.events[0]
    decision = program.causal_decisions[0]
    path = decision.paths[0]
    emission = path.emits[0]

    assert event.id == "event:greeted"
    assert emission.event == event.id

    directive = program.directives[0]
    principal = program.principals[0]
    authority_check = program.authority_checks[0]

    assert directive.principal == principal.id
    assert authority_check.principal == principal.id
    assert directive.authority_checks == (
        authority_check.id,
    )

    assert directive.causal_decisions == (
        decision.id,
    )


def test_runtime_validation() -> None:
    pipeline = ExecutionPipeline()

    verified = pipeline.verify_source(VALID_SOURCE)

    assert isinstance(
        verified,
        VerifiedAIRProgram,
    )

    assert verified.program.directives


def test_runtime_rejects_raw_air() -> None:
    pipeline = ExecutionPipeline()
    context = make_context()

    program = pipeline.compile_source(VALID_SOURCE)

    try:
        pipeline._runtime.execute(
            program,
            context,
        )
    except TypeError:
        return

    raise AssertionError(
        "RuntimeEngine accepted an unverified AIRProgram."
    )


def test_allowed_execution() -> None:
    pipeline = ExecutionPipeline()
    context = make_context(allow=True)

    result = pipeline.execute_source(
        VALID_SOURCE,
        context,
    )

    assert result is not None
    assert result.final_state is context.state
    assert len(result.delta.events) == 1
    assert len(result.diagnostics) == 0

    event = result.delta.events[0]

    assert event.event == "event:greeted"


def test_denied_execution() -> None:
    pipeline = ExecutionPipeline()
    context = make_context(allow=False)

    result = pipeline.execute_source(
        VALID_SOURCE,
        context,
    )

    assert len(result.delta.events) == 0
    assert len(result.diagnostics) >= 1

    diagnostic_codes = {
        diagnostic.code
        for diagnostic in result.diagnostics
    }

    assert "RUN001" in diagnostic_codes


def test_runtime_trace() -> None:
    pipeline = ExecutionPipeline()
    context = make_context(allow=True)

    result = pipeline.execute_source(
        VALID_SOURCE,
        context,
    )

    step_kinds = tuple(
        step.kind
        for step in result.trace.steps
    )

    assert "runtime.start" in step_kinds
    assert "directive.start" in step_kinds
    assert "authority.check" in step_kinds
    assert "event.emit" in step_kinds
    assert "runtime.finish" in step_kinds


def test_invalid_event_reference_is_rejected() -> None:
    pipeline = ExecutionPipeline()

    program = pipeline.compile_source(VALID_SOURCE)

    event = program.events[0]
    decision = program.causal_decisions[0]
    path = decision.paths[0]
    emission = path.emits[0]

    # These are frozen dataclasses, so use dataclasses.replace.
    from dataclasses import replace

    invalid_emission = replace(
        emission,
        event="event:undefined",
    )

    invalid_path = replace(
        path,
        emits=(invalid_emission,),
    )

    invalid_decision = replace(
        decision,
        paths=(invalid_path,),
    )

    invalid_program = replace(
        program,
        causal_decisions=(invalid_decision,),
    )

    try:
        pipeline._validator.validate(
            invalid_program
        )
    except RuntimeValidationError:
        return

    raise AssertionError(
        "RuntimeValidator accepted an undefined event reference."
    )


def main() -> None:
    suite = RegressionSuite()

    suite.run_test(
        "Compile valid source",
        test_pipeline_compiles_source,
    )

    suite.run_test(
        "Compiled IDs remain consistent",
        test_compiled_identifiers_match,
    )

    suite.run_test(
        "Validate compiled AIR",
        test_runtime_validation,
    )

    suite.run_test(
        "Reject raw AIR at runtime",
        test_runtime_rejects_raw_air,
    )

    suite.run_test(
        "Execute authorized directive",
        test_allowed_execution,
    )

    suite.run_test(
        "Skip unauthorized directive",
        test_denied_execution,
    )

    suite.run_test(
        "Generate runtime trace",
        test_runtime_trace,
    )

    suite.run_test(
        "Reject undefined event reference",
        test_invalid_event_reference_is_rejected,
    )

    suite.report()


if __name__ == "__main__":
    main()