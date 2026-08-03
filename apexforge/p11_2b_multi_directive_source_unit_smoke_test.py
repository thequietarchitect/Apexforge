"""Focused production-slice coverage for P11.2B headerless directives."""

from __future__ import annotations

import hashlib
from io import StringIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from air.serialization import air_to_dict
from authority.engine import AuthorityEngine
from authority.model import AuthorityGrant
from language.compiler import compile_source_with_map
from language.grammar import (
    P11_2B_GRAMMAR_COMPATIBILITY_NOTES,
    P11_2B_HEADERLESS_DIRECTIVE_SOURCE_EBNF,
)
from language.parser import DirectiveNode, parse, parse_headerless_directive_source_unit
from language.project import (
    ProjectCompilationError,
    ProjectEntryPointError,
    ProjectLinkError,
    ProjectValidationError,
    build_project,
)
from runtime.context import ExecutionContext
from runtime.state import StateSnapshot
from tooling.build_artifact import canonical_json_bytes
from tooling.cli import main as cli_main


FIRST_SOURCE = """directive First {
    state first_count = 0
    event first_done

    cause first_flow {
        path shared @ 10 {
            add first_count 1
            invoke Second
            emit first_done
        }
    }
}
"""

SECOND_SOURCE = """directive Second {
    state second_count = 2
    event second_done

    cause second_flow {
        path shared @ 10 {
            add second_count 3
            emit second_done
        }
    }
}
"""

THIRD_SOURCE = """directive Third {
    state third_count = 5
    event third_done

    cause third_flow {
        path third_path @ 10 {
            add third_count 4
            emit third_done
        }
    }
}
"""

REVERSE_SOURCE = """directive ReverseCaller {
    state reverse_count = 0

    cause reverse_flow {
        path reverse_path @ 10 {
            invoke Later
        }
    }
}

directive Later {
    state later_count = 1
}
"""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def require_raises(expected_type, operation, message: str):
    try:
        operation()
    except expected_type as error:
        return error
    raise AssertionError(message)


def diagnostic_of(error):
    diagnostics = tuple(getattr(error, "diagnostics", ()) or ())
    require(len(diagnostics) == 1, "expected one deterministic diagnostic")
    return diagnostics[0]


def semantic_fingerprint(program) -> str:
    projection = {"air": air_to_dict(program)}
    return hashlib.sha256(canonical_json_bytes(projection)).hexdigest()


def context_for(build, *directive_names: str) -> ExecutionContext:
    return ExecutionContext(
        state=StateSnapshot.from_program_initials(build.program),
        authority=AuthorityEngine.from_grants(
            tuple(
                AuthorityGrant(
                    principal=f"principal:{name}",
                    capability=f"directive.invoke:{name}",
                    resource=f"directive:{name}",
                )
                for name in directive_names
            )
        ),
    )


def test_parser_shape_order_comments_and_single_compatibility() -> None:
    single = parse(FIRST_SOURCE, source_name="single.apex")
    require(isinstance(single, DirectiveNode), "parse() return shape changed")

    multi_source = FIRST_SOURCE + "\n// retained separator trivia\n\n" + SECOND_SOURCE
    nodes = parse_headerless_directive_source_unit(
        multi_source,
        source_name="combined.apex",
    )
    require(
        tuple(node.name for node in nodes) == ("First", "Second"),
        "directive source order changed",
    )
    require(
        tuple(node.span.source_name for node in nodes if node.span is not None)
        == ("combined.apex", "combined.apex"),
        "directive spans lost source provenance",
    )
    require(
        nodes[0].span is not None
        and nodes[1].span is not None
        and nodes[0].span.start.line == 1
        and nodes[1].span.start.line > nodes[0].span.end.line,
        "directive spans lost physical source positions",
    )

    current = compile_source_with_map(FIRST_SOURCE, source_name="single.apex")
    frozen = compile_source_with_map(
        FIRST_SOURCE,
        source_name="single.apex",
        allow_headerless_multi_directive=False,
    )
    require(
        air_to_dict(current.program) == air_to_dict(frozen.program)
        and current.source_map == frozen.source_map,
        "single-directive semantic AIR or source maps changed",
    )
    require(
        "HeaderlessDirectiveSequence" in P11_2B_HEADERLESS_DIRECTIVE_SOURCE_EBNF
        and any("module/import" in note for note in P11_2B_GRAMMAR_COMPATIBILITY_NOTES),
        "grammar compatibility overlay does not state the narrow asymmetry",
    )


def test_linking_order_forward_reverse_and_equivalence() -> None:
    combined_source = FIRST_SOURCE + "\n" + SECOND_SOURCE
    combined = build_project({"10-combined.apex": combined_source})
    split = build_project(
        {"10-first.apex": FIRST_SOURCE, "20-second.apex": SECOND_SOURCE}
    )
    three = build_project({"three.apex": combined_source + "\n" + THIRD_SOURCE})

    require(
        tuple((item.id, item.order) for item in combined.program.directives)
        == (("directive:First", 0), ("directive:Second", 1)),
        "two-directive local or linked order changed",
    )
    require(
        tuple((item.id, item.order) for item in three.program.directives)
        == (("directive:First", 0), ("directive:Second", 1), ("directive:Third", 2)),
        "three-directive source order changed",
    )
    require(
        combined.program.causal_decisions[0].paths[0].invocations[0].target == "Second",
        "forward invocation did not retain its short reference",
    )
    reverse = build_project({"reverse.apex": REVERSE_SOURCE})
    require(
        reverse.program.causal_decisions[0].paths[0].invocations[0].target == "Later",
        "reverse invocation did not link after complete compilation",
    )
    require(
        air_to_dict(combined.program) == air_to_dict(split.program),
        "one-source and adjacent split-source semantic AIR differ",
    )
    require(
        semantic_fingerprint(combined.program) == semantic_fingerprint(split.program),
        "source-metadata-free semantic fingerprints differ",
    )
    require(
        tuple(path.id for decision in combined.program.causal_decisions for path in decision.paths)
        == ("path:shared", "path:shared"),
        "the same path name in distinct causes stopped being cause-local",
    )

    result = combined.execute(context_for(combined, "First", "Second"), entry="First")
    require(result.ok, "fully authorized forward invocation failed")
    require(
        result.final_state.get_int("first_count") == 1
        and result.final_state.get_int("second_count") == 5,
        "multi-directive runtime state differs from linked behavior",
    )


def test_duplicates_collisions_entries_and_authority() -> None:
    duplicate = require_raises(
        ProjectLinkError,
        lambda: build_project({"same.apex": FIRST_SOURCE + "\n" + FIRST_SOURCE}),
        "same-source duplicate directive was accepted",
    )
    diagnostic = diagnostic_of(duplicate)
    require(
        diagnostic.stage == "link"
        and diagnostic.code == "APX-LINK-001"
        and diagnostic.air_id == "principal:First"
        and diagnostic.span is not None
        and diagnostic.span.source_name == "same.apex"
        and len(diagnostic.related_spans) == 1
        and diagnostic.related_spans[0].source_name == "same.apex",
        "same-source duplicate lost stable link identity or related span",
    )

    collision_templates = {
        "state": (
            "directive A { state shared = 0 }\ndirective B { state shared = 1 }\n",
            "state:shared",
        ),
        "event": (
            "directive A { event shared }\ndirective B { event shared }\n",
            "event:shared",
        ),
        "cause": (
            "directive A { cause shared { path a @ 1 {} } }\n"
            "directive B { cause shared { path b @ 1 {} } }\n",
            "cause:shared",
        ),
    }
    for kind, (source, expected_id) in collision_templates.items():
        error = require_raises(
            ProjectLinkError,
            lambda source=source: build_project({"collision.apex": source}),
            f"flat {kind} collision was accepted",
        )
        item = diagnostic_of(error)
        require(
            item.stage == "link" and item.code == "APX-LINK-001" and item.air_id == expected_id,
            f"flat {kind} collision identity changed",
        )

    cross_kind = build_project(
        {
            "cross-kind.apex": (
                "directive Cross {\n state shared = 0\n event shared\n"
                " cause shared { path shared @ 1 {} }\n}"
            )
        }
    )
    require(
        cross_kind.program.states[0].id == "state:shared"
        and cross_kind.program.events[0].id == "event:shared"
        and cross_kind.program.causal_decisions[0].id == "cause:shared",
        "cross-kind canonical prefixes changed",
    )

    single = build_project({"single.apex": SECOND_SOURCE})
    require(single.resolve_entry() == "directive:Second", "single fallback changed")
    combined = build_project({"combined.apex": FIRST_SOURCE + SECOND_SOURCE})
    require_raises(
        ProjectEntryPointError, combined.resolve_entry, "multi-directive ambiguity was accepted"
    )
    require(
        combined.resolve_entry("Second") == "directive:Second"
        and combined.resolve_entry("directive:First") == "directive:First",
        "short or canonical explicit entry resolution changed",
    )

    denied = combined.execute(context_for(combined, "First"), entry="First")
    require(
        not denied.ok
        and any(item.code == "RUN001" for item in denied.diagnostics)
        and denied.delta.is_empty,
        "downstream authority denial or transaction rollback changed",
    )


def test_source_aware_rejections() -> None:
    scenarios = (
        ("malformed-second.apex", "directive Good {}\ndirective Broken { state value = }\n", "APX-PARSE-004", 2),
        ("nested.apex", "directive Outer {\n directive Inner {}\n}\n", "APX-PARSE-003", 2),
        ("mixed.apex", "directive One {}\nfunction Two() { return 2 }\n", "APX-PARSE-001", 2),
        ("function-first.apex", "function One() { return 1 }\ndirective Two {}\n", "APX-PARSE-001", 2),
        ("headered.apex", "module sample.headered\n\ndirective One {}\ndirective Two {}\n", "APX-PARSE-001", 4),
        ("trailing.apex", "directive One {}\ndirective Two {}\ntrailing\n", "APX-PARSE-001", 3),
    )
    for source_name, source, code, line in scenarios:
        error = require_raises(
            ProjectCompilationError,
            lambda source_name=source_name, source=source: build_project({source_name: source}),
            f"invalid source {source_name} was accepted",
        )
        diagnostic = diagnostic_of(error)
        require(
            diagnostic.stage == "parse"
            and diagnostic.code == code
            and diagnostic.span is not None
            and diagnostic.span.source_name == source_name
            and diagnostic.span.start.line == line,
            f"{source_name} lost stable source-aware first-error behavior",
        )

    undefined = require_raises(
        ProjectValidationError,
        lambda: build_project(
            {
                "undefined.apex": (
                    "directive Caller { cause flow { path p @ 1 { invoke Missing } } }\n"
                    "directive Other {}\n"
                )
            }
        ),
        "undefined cross-directive invocation was accepted",
    )
    diagnostic = diagnostic_of(undefined)
    require(
        diagnostic.stage == "validate"
        and diagnostic.code == "APX-VALIDATE-002"
        and diagnostic.span is not None
        and diagnostic.span.source_name == "undefined.apex",
        "undefined invocation lost its call-site diagnostic",
    )


def run_cli(arguments: tuple[str, ...]):
    stdout = StringIO()
    stderr = StringIO()
    code = cli_main(arguments, stdout=stdout, stderr=stderr)
    return code, stdout.getvalue(), stderr.getvalue()


def test_public_cli_artifacts_and_temporary_integrity() -> None:
    temporary_path: Path
    with TemporaryDirectory(prefix="apexforge-p11-2b-") as temporary:
        temporary_path = Path(temporary)
        source_root = temporary_path / "src"
        source_root.mkdir()
        (source_root / "main.apex").write_text(
            FIRST_SOURCE + "\n// public path separator\n" + SECOND_SOURCE,
            encoding="utf-8",
        )
        (temporary_path / "apexforge.json").write_text(
            json.dumps(
                {"schema": 1, "name": "P11_2B_Public", "sources": ["src/main.apex"], "entry": "Second"},
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        check_code, check_out, check_err = run_cli(("check", str(temporary_path)))
        require(
            check_code == 0 and "check passed" in check_out and check_err == "",
            "public check failed for a multi-directive source",
        )
        short_code, short_out, short_err = run_cli(("run", str(temporary_path), "--entry", "Second"))
        canonical_code, canonical_out, canonical_err = run_cli(
            ("run", str(temporary_path), "--entry", "directive:Second")
        )
        require(
            short_code == canonical_code == 0
            and "Entry: directive:Second" in short_out
            and "Entry: directive:Second" in canonical_out
            and short_err == canonical_err == "",
            "public short or canonical multi-directive run failed",
        )

        denied_code, denied_out, denied_err = run_cli(
            ("run", str(temporary_path), "--entry", "First")
        )
        require(
            denied_code == 30 and denied_out == "" and "[RUN001]" in denied_err,
            "public entry-only authority boundary changed",
        )

        first_artifact = temporary_path / "first.json"
        second_artifact = temporary_path / "second.json"
        first_code, first_out, first_err = run_cli(
            ("build", str(temporary_path), "--output", str(first_artifact), "--entry", "First")
        )
        second_code, second_out, second_err = run_cli(
            ("build", str(temporary_path), "--output", str(second_artifact), "--entry", "First")
        )
        require(
            first_code == second_code == 0
            and "Schema: apexforge.build-artifact/v1" in first_out
            and first_err == second_err == "",
            "public non-executing build failed",
        )
        require(
            first_artifact.read_bytes() == second_artifact.read_bytes()
            and first_out == second_out,
            "repeated build artifacts or public output were nondeterministic",
        )
        document = json.loads(first_artifact.read_text(encoding="utf-8"))
        require(
            set(document) == {"schema", "project", "air", "fingerprint"}
            and document["project"]["entry"] == "directive:First"
            and tuple(item["id"] for item in document["air"]["directives"])
            == ("directive:First", "directive:Second"),
            "artifact schema, entry, or canonical AIR content changed",
        )
        require(not tuple(temporary_path.glob(".*.tmp")), "artifact writing left temporary residue")

    require(not temporary_path.exists(), "TemporaryDirectory left project residue")


def main() -> None:
    test_parser_shape_order_comments_and_single_compatibility()
    test_linking_order_forward_reverse_and_equivalence()
    test_duplicates_collisions_entries_and_authority()
    test_source_aware_rejections()
    test_public_cli_artifacts_and_temporary_integrity()

    print("AFP-P11.2B multi-directive source-unit smoke test passed.")
    print("Directive sequences, trivia, spans, and ordering: PASS")
    print("Single-source/split-source semantic equivalence: PASS")
    print("Identities, duplicates, collisions, and entries: PASS")
    print("Forward/reverse linking and authority/runtime behavior: PASS")
    print("Source-aware invalid-boundary diagnostics: PASS")
    print("Public check/run/build and deterministic artifacts: PASS")
    print("Temporary-residue and network-free fixture boundary: PASS")


if __name__ == "__main__":
    main()
