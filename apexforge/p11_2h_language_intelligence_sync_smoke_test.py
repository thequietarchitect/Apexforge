"AFP-P11.2H heterogeneous language-intelligence synchronization smoke test."

from __future__ import annotations

from pathlib import Path
import subprocess
import sys


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = REPOSITORY_ROOT / "apexforge"
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from language_server.completion import _inventory
from language_server.definition import _definition_index
from language_server.formatting import _formatted_text
from language_server.hover import _hover_entries


URI = "file:///C:/ApexForge/P11Validation/main.apex"
SOURCE = (
    "authority Aegis {\n"
    "    capability Execute\n"
    "}\n\n"
    "role Architect {\n"
    "    authority Aegis\n"
    "}\n\n"
    "principal Operator {\n"
    "    role Architect\n"
    "}\n\n"
    "function Helper() : int {\n"
    "    return 1\n"
    "}\n\n"
    "directive Main {\n"
    "    state count : int = 0\n"
    "    event Done\n"
    "    authority Aegis\n"
    "}\n\n"
    "workflow Start {\n"
    "    invoke Main\n"
    "}\n"
)
EXPECTED_DECLARATIONS = {
    "Aegis",
    "Architect",
    "Operator",
    "Helper",
    "Main",
    "Start",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def repository_status() -> str:
    completed = subprocess.run(
        [
            "git",
            "status",
            "--porcelain=v2",
            "--untracked-files=all",
        ],
        cwd=REPOSITORY_ROOT,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
    )
    require(completed.stderr == "", "git status wrote stderr")
    return completed.stdout


def test_completion_selects_cursor_declaration() -> None:
    cursor = SOURCE.index("directive Main") + len("directive Main {")
    inventory = _inventory(URI, SOURCE, cursor)
    require(
        inventory.states == ("count",)
        and inventory.events == ("Done",),
        "completion did not select the heterogeneous declaration containing "
        "the cursor: " + repr(inventory),
    )


def test_hover_covers_all_declarations() -> None:
    entries = _hover_entries(URI, SOURCE)
    labels = tuple(item.label for item in entries)
    require(
        any(label == "authority Aegis" for label in labels)
        and any(label == "role Architect" for label in labels)
        and any(label == "principal Operator" for label in labels)
        and any(label.startswith("function Helper") for label in labels)
        and any(label == "directive Main" for label in labels)
        and any(label == "workflow Start" for label in labels),
        "hover omitted heterogeneous declarations: " + repr(labels),
    )


def test_definition_indexes_all_declarations() -> None:
    index = _definition_index(URI, SOURCE)
    occurrence_names = {
        SOURCE[item.start:item.end]
        for item in index.occurrences
    }
    require(
        EXPECTED_DECLARATIONS.issubset(occurrence_names),
        "definition index omitted heterogeneous declarations: "
        + repr(sorted(occurrence_names)),
    )


def test_formatting_preserves_source_order_and_is_idempotent() -> None:
    options = {
        "tabSize": 4,
        "insertSpaces": True,
    }
    formatted = _formatted_text(URI, SOURCE, options)
    require(formatted is not None, "valid heterogeneous source was not formatted")
    headers = (
        "authority Aegis",
        "role Architect",
        "principal Operator",
        "function Helper",
        "directive Main",
        "workflow Start",
    )
    positions = tuple(formatted.index(header) for header in headers)
    require(
        positions == tuple(sorted(positions)),
        "formatting reordered heterogeneous declarations",
    )
    require(
        _formatted_text(URI, formatted, options) == formatted,
        "heterogeneous formatting is not idempotent",
    )


def test_invalid_source_returns_no_partial_semantics() -> None:
    malformed = SOURCE + "\nprincipal Broken {\n    role\n}\n"
    require(
        _hover_entries(URI, malformed) == (),
        "invalid source returned partial hover entries",
    )
    require(
        _definition_index(URI, malformed).occurrences == [],
        "invalid source returned partial definition occurrences",
    )
    require(
        _formatted_text(
            URI,
            malformed,
            {"tabSize": 4, "insertSpaces": True},
        )
        is None,
        "invalid source returned formatting edits",
    )


def main() -> None:
    status_before = repository_status()
    test_completion_selects_cursor_declaration()
    test_hover_covers_all_declarations()
    test_definition_indexes_all_declarations()
    test_formatting_preserves_source_order_and_is_idempotent()
    test_invalid_source_returns_no_partial_semantics()
    require(
        repository_status() == status_before,
        "smoke test changed repository status",
    )

    print("AFP-P11.2H heterogeneous language-intelligence synchronization passed.")
    print("Cursor-local completion inventory: PASS")
    print("All-declaration hover coverage: PASS")
    print("All-declaration definition index: PASS")
    print("Source-order idempotent formatting: PASS")
    print("Invalid-source no-partial boundary: PASS")
    print("Repository no-op boundary: PASS")


if __name__ == "__main__":
    main()
