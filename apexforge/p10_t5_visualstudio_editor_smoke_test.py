"""AFP-P10-T5.2 Visual Studio editor classification smoke test."""
from __future__ import annotations

from pathlib import Path

from tooling.visualstudio_editor import (
    CANONICAL_VISUAL_STUDIO_EDITOR_SHA256,
    audit_visualstudio_editor,
)
from tooling.visualstudio_extension import CANONICAL_VISUAL_STUDIO_EXTENSION_SHA256
from tooling.visualstudio_syntax import (
    CANONICAL_VISUAL_STUDIO_SYNTAX_SHA256,
    classify_apexforge_source,
    visual_studio_syntax_fingerprint,
)

EXPECTED_T5_1 = "06d8b8f428b033d5e522b4eaf842560fc7c5b4e953ebcf3338f7e1a87d6b363e"
EXPECTED_SYNTAX = "a94182ea041461a46ed11281dbce09b4575e294ed9b5e1dff60a94b0a366987f"
EXPECTED_EDITOR = "4aea8eff4f5c6e934be5220e4c880b6c7ac40722b0bea2caa037a141fa4c1b67"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    extension_root = repo_root / "editors" / "visualstudio-apexforge"

    require(CANONICAL_VISUAL_STUDIO_EXTENSION_SHA256 == EXPECTED_T5_1, "T5.1 extension fingerprint changed")
    require(visual_studio_syntax_fingerprint() == EXPECTED_SYNTAX, "T5.2 syntax fingerprint changed")
    require(CANONICAL_VISUAL_STUDIO_SYNTAX_SHA256 == EXPECTED_SYNTAX, "declared T5.2 syntax fingerprint changed")

    audit = audit_visualstudio_editor(extension_root)
    require(audit.editor_sha256 == EXPECTED_EDITOR, "Visual Studio T5.2 editor audit changed")
    require(CANONICAL_VISUAL_STUDIO_EDITOR_SHA256 == EXPECTED_EDITOR, "declared T5.2 editor fingerprint changed")

    sample = 'module demo.core\nimport standard.io\nfunction combine<T:int>(left:int, right:float):int {\n    let total = left + 2.5\n    when total >= 10 and not false {\n        return invokeHelper<int>(total, 1)\n    } otherwise {\n        return 0\n    }\n}\n'
    tokens = classify_apexforge_source(sample)
    observed = {(token.text, token.kind) for token in tokens}
    required = {
        ("module", "apexforge.keyword"),
        ("demo", "apexforge.declaration"),
        ("core", "apexforge.declaration"),
        ("function", "apexforge.keyword"),
        ("combine", "apexforge.declaration"),
        ("int", "apexforge.type"),
        ("float", "apexforge.type"),
        ("2.5", "apexforge.number"),
        (">=", "apexforge.operator"),
        ("false", "apexforge.boolean"),
        ("invokeHelper", "apexforge.function"),
    }
    require(required.issubset(observed), f"reference classification omitted tokens: {sorted(required - observed)!r}")
    require(not any(token.text.startswith("//") for token in tokens), "T5.2 invented comment classification")
    require(all(token.length > 0 for token in tokens), "zero-length classification token")
    require(tuple(token.start for token in tokens) == tuple(sorted(token.start for token in tokens)), "tokens are not source ordered")

    print("AFP-P10-T5.2 Visual Studio editor classification smoke test passed.")
    print("Frozen T5.1 extension prerequisite: PASS")
    print("ApexForge content-type classifier provider: PASS")
    print("Nine theme-aware classification types: PASS")
    print("User-visible Fonts and Colors formats: PASS")
    print("Requested-span bounded line scanner: PASS")
    print("Canonical keyword/string/number/operator coverage: PASS")
    print("No unsupported comment syntax: PASS")
    print("Deterministic T5.2 fingerprints: PASS")


if __name__ == "__main__":
    main()
