"""P11 SRA-C cross-file imported directive definition acceptance."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

from language_server.server import LanguageServerSession


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def request(message_id: int, method: str, params: object) -> dict:
    return {"jsonrpc": "2.0", "id": message_id, "method": method, "params": params}


def notification(method: str, params: object) -> dict:
    return {"jsonrpc": "2.0", "method": method, "params": params}


SRA_C_PREDECESSOR = "c7e389c9ee377a208f970cebba09213999ae78d2"
SRA_C_RESOLUTION_MARKERS = (
    "ProjectQualification",
    "ProjectResolutionCandidate",
    "resolution_candidate_index",
    "ProjectResolutionQuery",
    "ProjectResolvedBinding",
    "resolve_project_query",
    "ProjectResolutionContext",
    "ProjectVisibilityEvidence",
    "collect_project_visibility_evidence",
    "ProjectVisibilityDecision",
    "evaluate_project_visibility",
    "filter_project_visible_candidates",
    "resolve_project_contextual_query",
)


def _is_resolution_consumer(relative: str, text: str) -> bool:
    return (
        relative.startswith("apexforge/")
        and relative.endswith(".py")
        and not relative.endswith("_smoke_test.py")
        and "/tests/" not in relative
        and any(marker in text for marker in SRA_C_RESOLUTION_MARKERS)
    )


def test_sra_c_resolver_successor_governance() -> None:
    repository_root = Path(__file__).resolve().parents[1]
    package_directory = repository_root / "apexforge"

    current_consumers = set()
    for path in package_directory.rglob("*.py"):
        relative = path.relative_to(repository_root).as_posix()
        source = path.read_text(encoding="utf-8")
        if _is_resolution_consumer(relative, source):
            current_consumers.add(relative)

    tree = subprocess.run(
        ["git", "ls-tree", "-r", "--name-only", SRA_C_PREDECESSOR, "apexforge"],
        cwd=repository_root,
        text=True,
        capture_output=True,
        check=True,
    ).stdout.splitlines()

    predecessor_consumers = set()
    for relative in tree:
        if (
            not relative.startswith("apexforge/")
            or not relative.endswith(".py")
            or relative.endswith("_smoke_test.py")
            or "/tests/" in relative
        ):
            continue
        result = subprocess.run(
            ["git", "show", f"{SRA_C_PREDECESSOR}:{relative}"],
            cwd=repository_root,
            text=True,
            capture_output=True,
        )
        require(
            result.returncode == 0,
            f"unable to read predecessor resolver consumer candidate: {relative}",
        )
        if _is_resolution_consumer(relative, result.stdout):
            predecessor_consumers.add(relative)

    added_consumers = current_consumers - predecessor_consumers
    removed_consumers = predecessor_consumers - current_consumers
    require(
        added_consumers == {"apexforge/language_server/project_definition.py"},
        "SRA-C added a resolver consumer outside the exact reviewed language-server adapter",
    )
    require(
        not removed_consumers,
        "SRA-C removed a predecessor resolver consumer",
    )

    for relative in sorted(current_consumers & predecessor_consumers):
        result = subprocess.run(
            ["git", "diff", "--quiet", SRA_C_PREDECESSOR, "--", relative],
            cwd=repository_root,
        )
        require(
            result.returncode == 0,
            f"SRA-C mutated predecessor resolver consumer: {relative}",
        )

    adapter_text = (
        package_directory / "language_server" / "project_definition.py"
    ).read_text(encoding="utf-8")
    require(
        "ProjectResolutionContext" in adapter_text
        and "ProjectResolutionQuery" in adapter_text
        and "resolve_project_contextual_query" in adapter_text
        and "ProjectResolvedBinding" in adapter_text
        and "resolution_candidate_index" in adapter_text,
        "SRA-C project definition adapter stopped delegating to the canonical resolver",
    )
    require(
        "document_symbols" not in adapter_text
        and "len(matches)" not in adapter_text,
        "SRA-C project definition adapter reacquired editor-owned winner selection",
    )

    server_text = (
        package_directory / "language_server" / "server.py"
    ).read_text(encoding="utf-8")
    same_document = server_text.find("resolved = definition(")
    project_fallback = server_text.find("return project_definition(")
    require(
        same_document >= 0
        and project_fallback >= 0
        and same_document < project_fallback,
        "P10 same-document definition no longer precedes the SRA-C project fallback",
    )

    print("P11 SRA-C resolver successor governance: PASS")

def main() -> int:
    test_sra_c_resolver_successor_governance()
    with TemporaryDirectory() as temporary:
        project = Path(temporary) / "ModuleRuntime"
        project.mkdir()
        root = project / "root.apex"
        worker = project / "worker.apex"
        unimported = project / "unimported.apex"
        root_text = "module App.Root\nimport App.Worker\n\ndirective Root { cause run { path primary @ 1 { invoke Worker } } }\n"
        worker_text = "module App.Worker\n\ndirective Worker { state count = 1 cause work { path primary @ 1 { add count 2 } } }\n"
        unimported_text = "module App.UnimportedRoot\n\ndirective UnimportedRoot { cause run { path primary @ 1 { invoke Worker } } }\n"
        root.write_text(root_text, encoding="utf-8")
        worker.write_text(worker_text, encoding="utf-8")
        unimported.write_text(unimported_text, encoding="utf-8")
        (project / "apexforge.json").write_text(
            json.dumps(
                {
                    "schema": 1,
                    "name": "ModuleRuntime",
                    "sources": ["root.apex", "worker.apex", "unimported.apex"],
                    "entry": "Root",
                },
                separators=(",", ":"),
            )
            + "\n",
            encoding="utf-8",
        )

        session = LanguageServerSession()
        initialize = session.process(
            request(
                1,
                "initialize",
                {
                    "processId": None,
                    "rootUri": Path(temporary).as_uri(),
                    "capabilities": {
                        "textDocument": {
                            "definition": {"linkSupport": False},
                        }
                    },
                },
            )
        )
        require(
            initialize["result"]["capabilities"].get("definitionProvider") is True,
            "definition provider was not negotiated",
        )
        session.process(notification("initialized", {}))
        session.process(
            notification(
                "textDocument/didOpen",
                {
                    "textDocument": {
                        "uri": root.as_uri(),
                        "languageId": "apexforge",
                        "version": 1,
                        "text": root_text,
                    }
                },
            )
        )

        response = session.process(
            request(
                2,
                "textDocument/definition",
                {
                    "textDocument": {"uri": root.as_uri()},
                    "position": {"line": 3, "character": 55},
                },
            )
        )
        expected = {
            "uri": worker.as_uri(),
            "range": {
                "start": {"line": 2, "character": 10},
                "end": {"line": 2, "character": 16},
            },
        }
        require(
            response["result"] == expected,
            "cross-file imported directive definition did not resolve",
        )
        session.process(
            notification(
                "textDocument/didOpen",
                {
                    "textDocument": {
                        "uri": unimported.as_uri(),
                        "languageId": "apexforge",
                        "version": 1,
                        "text": unimported_text,
                    }
                },
            )
        )
        unimported_response = session.process(
            request(
                3,
                "textDocument/definition",
                {
                    "textDocument": {"uri": unimported.as_uri()},
                    "position": {"line": 2, "character": 67},
                },
            )
        )
        require(
            unimported_response["result"] is None,
            "unimported same-name directive leaked across project visibility",
        )

    print("P11 SRA-C cross-file imported directive definition: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
