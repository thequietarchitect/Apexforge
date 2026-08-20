"""P11-SRC-H final integration regression and source-surface bridge freeze proof."""

from __future__ import annotations

from io import StringIO
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

from language.semantic_decision_analysis import analyze_semantic_decision_source
from language.semantic_decision_project_analysis import (
    SemanticDecisionProjectAnalysisError,
    analyze_semantic_decision_project_sources,
)
from language_server.diagnostics import analyze_document
from semantic_decision import CandidateAlternative, ConvergencePolicy
from tooling.cli import EXIT_CHECK, EXIT_SUCCESS, main as cli_main
from tooling.project_loader import (
    PROJECT_KIND_AIR,
    PROJECT_KIND_NARRATIVE,
    PROJECT_KIND_SEMANTIC_DECISION,
    load_project,
)


SRC_FREEZES = (
    (
        "afp-p11-src-a-freeze",
        "a3826cefb0c35ce263b052de13c15ca20ed6fad1",
    ),
    (
        "afp-p11-src-b-freeze",
        "146e89185be7f27e4b25fd3b762965fc16393daf",
    ),
    (
        "afp-p11-src-c-freeze",
        "8cd2c645e183d5042aea2ab4c807c132267a69d0",
    ),
    (
        "afp-p11-src-d-freeze",
        "5754de5e1033ead24431184be311aaae9e4717af",
    ),
    (
        "afp-p11-src-e-freeze",
        "d25d3af39b9778f8b4eda8ab61bbb1ebb013685b",
    ),
    (
        "afp-p11-src-f-freeze",
        "14072c17f9ec5698f4b18b7c095ea2c7f7d81466",
    ),
    (
        "afp-p11-src-g-freeze",
        "cf84bd4c001277ecd2f4ece26095125966720b37",
    ),
)

SRC_PRODUCTION_TOUCHPOINTS = (
    "apexforge/language/semantic_decision_source.py",
    "apexforge/language/semantic_decision_parser.py",
    "apexforge/language/semantic_decision_lowering.py",
    "apexforge/language/semantic_decision_source_validation.py",
    "apexforge/language/semantic_decision_analysis.py",
    "apexforge/language/semantic_decision_project_analysis.py",
    "apexforge/tooling/project_loader.py",
    "apexforge/tooling/cli.py",
    "apexforge/language_server/diagnostics.py",
)

VALID_SOURCE = """\
decision BridgeAction {
    candidate KeepOpen
    candidate Destroy
    incompatible KeepOpen, Destroy
    converge using "rank.explicit-order" {
        KeepOpen
        Destroy
    }
    paradox elevate
        when unresolved
        requires information_loss
}
"""

SECOND_SOURCE = """\
decision ComposeAction {
    candidate Left
    candidate Right
    converge using "compose.all-admissible" {
        Left
        Right
    }
}
"""

DUPLICATE_A = """\
decision Duplicate {
    candidate A
}
"""

DUPLICATE_B = """\
decision Duplicate {
    candidate B
}
"""

INVALID_SOURCE = """\
decision Broken {
    candidate
}
"""

AIR_SOURCE = "directive Main {}\n"

NARRATIVE_SOURCE = """\
story IsolationStory {
    character Hero
    scene Start
    scene End
    choice Move {
        scene Start
        path "Continue" {
            destination End
        }
    }
    timeline Main {
        scenes [Start, End]
    }
}
"""

FORBIDDEN_OPERATIVE_NAMES = (
    "evaluate_advanced_condition",
    "construct_semantic_convergence_set",
    "apply_semantic_convergence_policy",
    "assess_paradox_elevation",
    "elevate_paradox",
    "validate_semantic_outcome",
    "project_semantic_outcome",
)


def _root() -> Path:
    return Path(__file__).resolve().parents[1]


def _git(*arguments: str) -> str:
    completed = subprocess.run(
        ("git", *arguments),
        cwd=_root(),
        check=False,
        text=True,
        encoding="utf-8",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if completed.returncode != 0:
        raise AssertionError(
            "git {} failed: {}".format(
                " ".join(arguments),
                completed.stderr.strip(),
            )
        )
    return completed.stdout.rstrip()


def _git_exit(*arguments: str) -> int:
    return subprocess.run(
        ("git", *arguments),
        cwd=_root(),
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ).returncode


def _write_text(path: Path, text: str) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(text)


def _write_project(root: Path, name: str, records) -> None:
    root.mkdir(parents=True, exist_ok=True)
    source_names = []
    for source_name, source in records:
        source_names.append(source_name)
        _write_text(root / source_name, source)
    _write_text(
        root / "apexforge.json",
        json.dumps(
            {
                "schema": 1,
                "name": name,
                "sources": source_names,
                "entry": None,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
    )


def _invoke(arguments):
    stdout = StringIO()
    stderr = StringIO()
    code = cli_main(
        tuple(arguments),
        stdout=stdout,
        stderr=stderr,
    )
    return code, stdout.getvalue(), stderr.getvalue()


def _expect(exc_type, operation):
    try:
        operation()
    except exc_type as error:
        return error
    raise AssertionError("Expected {}.".format(exc_type.__name__))


def _assert_freeze_chain() -> None:
    resolved = tuple(
        _git("rev-parse", "{}^{{}}".format(tag))
        for tag, _commit in SRC_FREEZES
    )
    expected = tuple(commit for _tag, commit in SRC_FREEZES)
    assert resolved == expected

    for index in range(len(SRC_FREEZES) - 1):
        left = SRC_FREEZES[index][0]
        right = SRC_FREEZES[index + 1][0]
        assert _git_exit("merge-base", "--is-ancestor", left, right) == 0

    assert (
        _git_exit(
            "merge-base",
            "--is-ancestor",
            SRC_FREEZES[-1][0],
            "HEAD",
        )
        == 0
    )


def _assert_capability_census() -> None:
    root = _root()
    assert len(SRC_FREEZES) == 7
    assert len(SRC_PRODUCTION_TOUCHPOINTS) == 9
    assert all((root / path).is_file() for path in SRC_PRODUCTION_TOUCHPOINTS)


def _assert_direct_source_bridge() -> None:
    first = analyze_semantic_decision_source(
        VALID_SOURCE,
        source_name="bridge.apex",
    )
    second = analyze_semantic_decision_source(
        VALID_SOURCE,
        source_name="bridge.apex",
    )
    assert first == second
    assert first.source_document.span.source_name == "bridge.apex"
    assert first.semantic_bridge.span.source_name == "bridge.apex"
    assert tuple(
        item.identity for item in first.semantic_bridge.decisions
    ) == ("BridgeAction",)

    decision = first.semantic_bridge.decisions[0]
    assert tuple(
        item.candidate.identity for item in decision.candidates
    ) == ("KeepOpen", "Destroy")
    assert all(
        type(item.candidate) is CandidateAlternative
        for item in decision.candidates
    )
    assert type(decision.policy) is ConvergencePolicy
    assert decision.policy.identity == "rank.explicit-order"
    assert decision.policy.parameters == (
        ("order", ("KeepOpen", "Destroy")),
    )
    assert decision.paradox_requested is True


def _assert_project_composition() -> None:
    first = analyze_semantic_decision_project_sources(
        (
            ("a.apex", VALID_SOURCE),
            ("b.apex", SECOND_SOURCE),
        )
    )
    second = analyze_semantic_decision_project_sources(
        (
            ("a.apex", VALID_SOURCE),
            ("b.apex", SECOND_SOURCE),
        )
    )
    assert first == second
    assert tuple(
        decision.identity
        for analysis in first.source_analyses
        for decision in analysis.semantic_bridge.decisions
    ) == ("BridgeAction", "ComposeAction")

    error = _expect(
        SemanticDecisionProjectAnalysisError,
        lambda: analyze_semantic_decision_project_sources(
            (
                ("a.apex", DUPLICATE_A),
                ("b.apex", DUPLICATE_B),
            )
        ),
    )
    assert error.diagnostic.code == "APX-SEMANTIC-DECISION-PROJECT"
    assert error.diagnostic.stage == "link"
    assert error.diagnostic.span is not None
    assert error.diagnostic.span.source_name == "b.apex"
    assert len(error.diagnostic.related_spans) == 1
    assert error.diagnostic.related_spans[0].source_name == "a.apex"


def _assert_real_apex_cli_and_lsp() -> None:
    root = _root()
    wrapper = root / "apexforge" / "apexforge_cli.py"

    with TemporaryDirectory(prefix="apexforge-src-h-") as temporary:
        temporary_root = Path(temporary)
        valid_root = temporary_root / "valid"
        duplicate_root = temporary_root / "duplicate"
        malformed_root = temporary_root / "malformed"
        air_root = temporary_root / "air"
        narrative_root = temporary_root / "narrative"

        _write_project(
            valid_root,
            "BridgeProject",
            (
                ("a.apex", VALID_SOURCE),
                ("b.apex", SECOND_SOURCE),
            ),
        )
        _write_project(
            duplicate_root,
            "DuplicateBridgeProject",
            (
                ("a.apex", DUPLICATE_A),
                ("b.apex", DUPLICATE_B),
            ),
        )
        _write_project(
            malformed_root,
            "MalformedBridgeProject",
            (("broken.apex", INVALID_SOURCE),),
        )
        _write_project(
            air_root,
            "AirIsolation",
            (("main.apex", AIR_SOURCE),),
        )
        _write_project(
            narrative_root,
            "NarrativeIsolation",
            (("story.apex", NARRATIVE_SOURCE),),
        )

        assert load_project(valid_root).project_kind == PROJECT_KIND_SEMANTIC_DECISION
        assert load_project(duplicate_root).project_kind == PROJECT_KIND_SEMANTIC_DECISION
        assert load_project(malformed_root).project_kind == PROJECT_KIND_SEMANTIC_DECISION
        assert load_project(air_root).project_kind == PROJECT_KIND_AIR
        assert load_project(narrative_root).project_kind == PROJECT_KIND_NARRATIVE

        first_valid = _invoke(("check", str(valid_root)))
        second_valid = _invoke(("check", str(valid_root)))
        assert first_valid == second_valid
        assert first_valid == (
            EXIT_SUCCESS,
            "ApexForge check passed: BridgeProject (2 source(s)).\n",
            "",
        )

        duplicate = _invoke(("check", str(duplicate_root)))
        assert duplicate[0] == EXIT_CHECK
        assert duplicate[1] == ""
        assert "APX-SEMANTIC-DECISION-PROJECT" in duplicate[2]

        malformed_cli = _invoke(("check", str(malformed_root)))
        assert malformed_cli[0] == EXIT_CHECK
        assert malformed_cli[1] == ""
        assert "APX-SEMANTIC-DECISION-SYNTAX" in malformed_cli[2]

        wrapper_first = subprocess.run(
            (sys.executable, str(wrapper), "check", str(valid_root)),
            cwd=root,
            check=False,
            text=True,
            encoding="utf-8",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        wrapper_second = subprocess.run(
            (sys.executable, str(wrapper), "check", str(valid_root)),
            cwd=root,
            check=False,
            text=True,
            encoding="utf-8",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        assert wrapper_first.returncode == EXIT_SUCCESS
        assert wrapper_second.returncode == EXIT_SUCCESS
        assert wrapper_first.stdout == wrapper_second.stdout
        assert wrapper_first.stderr == wrapper_second.stderr == ""
        assert wrapper_first.stdout == first_valid[1]

        lsp_uri = "file:///workspace/broken.apex"
        lsp_first = analyze_document(
            lsp_uri,
            INVALID_SOURCE,
            include_related_information=True,
        )
        lsp_second = analyze_document(
            lsp_uri,
            INVALID_SOURCE,
            include_related_information=True,
        )
        assert lsp_first == lsp_second
        assert len(lsp_first) == 1
        assert lsp_first[0].get("code") == "APX-SEMANTIC-DECISION-SYNTAX"
        assert "APX-SEMANTIC-DECISION-SYNTAX" in malformed_cli[2]

        assert analyze_document(
            "file:///workspace/valid.apex",
            VALID_SOURCE,
        ) == ()
        assert analyze_document(
            "file:///workspace/air.apex",
            AIR_SOURCE,
        ) == ()
        assert analyze_document(
            "file:///workspace/story.apex",
            NARRATIVE_SOURCE,
        ) == ()


def _assert_nonownership() -> None:
    root = _root()
    candidate_files = (
        root / "apexforge" / "language" / "semantic_decision_project_analysis.py",
        root / "apexforge" / "language_server" / "diagnostics.py",
        root / "apexforge" / "tooling" / "cli.py",
        root / "apexforge" / "tooling" / "project_loader.py",
    )
    text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in candidate_files
    )
    for name in FORBIDDEN_OPERATIVE_NAMES:
        assert name not in text

    analysis = analyze_semantic_decision_source(
        VALID_SOURCE,
        source_name="nonownership.apex",
    )
    assert not hasattr(analysis, "resolution")
    assert not hasattr(analysis.semantic_bridge, "resolution")
    assert not hasattr(analysis.semantic_bridge, "assessment")
    assert not hasattr(analysis.semantic_bridge, "elevated_state")
    assert not hasattr(analysis.semantic_bridge, "projection")


def main() -> None:
    _assert_freeze_chain()
    _assert_capability_census()
    _assert_direct_source_bridge()
    _assert_project_composition()
    _assert_real_apex_cli_and_lsp()
    _assert_nonownership()

    print("P11_SRC_A_THROUGH_G_FREEZE_CHAIN=PASS")
    print("P11_SRC_CAPABILITY_CENSUS=PASS")
    print("SRC_FROZEN_SLICES=7")
    print("SRC_PRODUCTION_TOUCHPOINTS=9")
    print("REAL_APEX_SOURCE_BRIDGE=PASS")
    print("PARSE_LOWER_VALIDATE_ANALYZE=PASS")
    print("P11_10_OBJECT_REUSE=PASS")
    print("DIRECT_ANALYSIS_DETERMINISM=PASS")
    print("PROJECT_COMPOSITION=PASS")
    print("PROJECT_COMPOSITION_DETERMINISM=PASS")
    print("CROSS_SOURCE_DUPLICATE_REJECTION=PASS")
    print("REAL_CLI_WRAPPER_ACCEPTANCE=PASS")
    print("CLI_DETERMINISM=PASS")
    print("CLI_LSP_DIAGNOSTIC_CODE_EQUIVALENCE=PASS")
    print("LSP_DIAGNOSTIC_DETERMINISM=PASS")
    print("AIR_SOURCE_FAMILY_ISOLATION=PASS")
    print("NARRATIVE_SOURCE_FAMILY_ISOLATION=PASS")
    print("CONDITION_EVALUATION=NONE")
    print("CONVERGENCE_RESOLUTION=NONE")
    print("PARADOX_ASSESSMENT=NONE")
    print("P11_10_VALIDATION=NONE")
    print("RUNTIME_EXECUTION=NONE")
    print("P11_SRC_H_FINAL_INTEGRATION=PASS")


if __name__ == "__main__":
    main()