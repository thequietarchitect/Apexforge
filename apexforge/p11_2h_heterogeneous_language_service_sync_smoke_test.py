"""AFP-P11.2H heterogeneous language-service synchronization smoke test."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = REPOSITORY_ROOT / "apexforge"
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from language_server.diagnostics import analyze_document
from language_server.symbols import document_symbols


URI = "file:///C:/ApexForge/P11Validation/main.apex"
SOURCE = """authority Aegis {
    capability Execute
}

role Architect {
    authority Aegis
}

principal Operator {
    role Architect
}

function Helper() : int {
    return 1
}

directive Main {
    authority Aegis
}

workflow Start {
    invoke Main
}
"""
EXPECTED_NAMES = (
    "Aegis",
    "Architect",
    "Operator",
    "Helper",
    "Main",
    "Start",
)


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


def test_headerless() -> None:
    diagnostics = analyze_document(URI, SOURCE)
    require(
        diagnostics == (),
        "valid heterogeneous source produced diagnostics: "
        + repr(diagnostics),
    )
    symbols = document_symbols(URI, SOURCE)
    require(
        tuple(item["name"] for item in symbols) == EXPECTED_NAMES,
        "document symbols omitted or reordered declarations: "
        + repr(symbols),
    )


def test_module_root() -> None:
    source = (
        "module validation.core\n"
        "import validation.foundation\n\n"
        + SOURCE
    )
    require(
        analyze_document(URI, source) == (),
        "module heterogeneous source produced diagnostics",
    )
    symbols = document_symbols(URI, source)
    require(
        len(symbols) == 1
        and symbols[0]["name"] == "validation.core",
        "module root symbol changed: " + repr(symbols),
    )
    children = tuple(symbols[0].get("children", ()))
    require(
        tuple(item["name"] for item in children)
        == ("validation.foundation",) + EXPECTED_NAMES,
        "module root omitted import or declarations: "
        + repr(children),
    )


def test_later_error() -> None:
    malformed = SOURCE + "\nprincipal Broken {\n    role\n}\n"
    diagnostics = analyze_document(URI, malformed)
    require(
        len(diagnostics) == 1
        and diagnostics[0].get("code") == "APX-PARSE-001",
        "later malformed declaration diagnostic changed: "
        + repr(diagnostics),
    )
    require(
        diagnostics[0]["range"]["start"]["line"] >= SOURCE.count("\n"),
        "later diagnostic lost its physical source position",
    )
    require(
        document_symbols(URI, malformed) == (),
        "invalid source returned partial symbols",
    )


def main() -> None:
    status_before = repository_status()
    test_headerless()
    test_module_root()
    test_later_error()
    require(
        repository_status() == status_before,
        "smoke test changed repository status",
    )

    print("AFP-P11.2H heterogeneous language-service synchronization passed.")
    print("Heterogeneous diagnostics: PASS")
    print("Six top-level document symbols: PASS")
    print("Module root and declaration children: PASS")
    print("Later source-aware syntax diagnostics: PASS")
    print("Repository no-op boundary: PASS")


if __name__ == "__main__":
    main()
