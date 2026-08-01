"""AFP-P10-T5.2 Visual Studio editor classification source auditor."""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import sys
from typing import Final, Mapping, Optional, Sequence

from tooling.visualstudio_extension import (
    CANONICAL_VISUAL_STUDIO_EXTENSION_SHA256,
    VisualStudioExtensionError,
    audit_visualstudio_extension,
)
from tooling.visualstudio_syntax import CANONICAL_VISUAL_STUDIO_SYNTAX_SHA256

P10_T5_VISUAL_STUDIO_EDITOR_VERSION: Final[str] = "10-T5.2"
VISUAL_STUDIO_EDITOR_SCHEMA: Final[int] = 1
VISUAL_STUDIO_EDITOR_KIND: Final[str] = "apexforge.visual-studio-editor-classification"

_EXPECTED_CONTRACT: Final[Mapping[str, object]] = {'schema': 1, 'kind': 'apexforge.visual-studio-editor-classification', 'editor_version': '10-T5.2', 'required_t5_1_extension_sha256': '06d8b8f428b033d5e522b4eaf842560fc7c5b4e953ebcf3338f7e1a87d6b363e', 'syntax_sha256': 'a94182ea041461a46ed11281dbce09b4575e294ed9b5e1dff60a94b0a366987f', 'root': 'editors/visualstudio-apexforge', 'required_files': ('src/ApexForge.VisualStudio/Classification/ApexForgeClassificationNames.cs', 'src/ApexForge.VisualStudio/Classification/ApexForgeClassificationTypes.cs', 'src/ApexForge.VisualStudio/Classification/ApexForgeClassificationFormats.cs', 'src/ApexForge.VisualStudio/Classification/ApexForgeClassifierProvider.cs', 'src/ApexForge.VisualStudio/Classification/ApexForgeClassifier.cs'), 'file_sha256': {'src/ApexForge.VisualStudio/Classification/ApexForgeClassificationNames.cs': '85a8c67555b92ace36e3c2587aff6ba980d62d74e819e3f9f5179cf793d4b828', 'src/ApexForge.VisualStudio/Classification/ApexForgeClassificationTypes.cs': '2684c7c906a9d5e989a127daaaa0fb8ef2b2feb6197cd2e38a14ed275d468830', 'src/ApexForge.VisualStudio/Classification/ApexForgeClassificationFormats.cs': 'be7d38695e235c445b4a8fb277eb8bec10c9197e179866c79f3e5554da375267', 'src/ApexForge.VisualStudio/Classification/ApexForgeClassifierProvider.cs': 'c717263d70ee3b0d01e74f5a3abced32551c9d833bdcc7055f2b4e0da755899e', 'src/ApexForge.VisualStudio/Classification/ApexForgeClassifier.cs': 'af7bca59ba5004f9652184e8b91cec2fa1ac46efd567398c049d733a7fc16e29'}, 'content_type': 'apexforge', 'provider_contract': 'IClassifierProvider', 'classifier_contract': 'IClassifier', 'classification_count': 9, 'fonts_and_colors_entries': 9, 'requested_span_bounded': True, 'line_local_lexing': True, 'comments_supported': False, 't5_1_sources_unchanged': True}
CANONICAL_VISUAL_STUDIO_EDITOR_SHA256: Final[str] = "4aea8eff4f5c6e934be5220e4c880b6c7ac40722b0bea2caa037a141fa4c1b67"


class VisualStudioEditorError(ValueError):
    code: Final[str] = "APX-VS-002"

    def __init__(self, message: str) -> None:
        if type(message) is not str or not message:
            raise ValueError("VisualStudioEditorError.message must be non-empty.")
        self.message = message
        super().__init__(f"[{self.code}] {message}")


@dataclass(frozen=True)
class VisualStudioEditorAudit:
    root: Path
    editor_sha256: str
    file_sha256: Mapping[str, str]


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_json(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise VisualStudioEditorError(f"Could not read UTF-8 file {path}: {error}") from error


def _require_marker(text: str, marker: str, owner: str) -> None:
    if marker not in text:
        raise VisualStudioEditorError(f"{owner} omitted required marker {marker!r}.")


def audit_visualstudio_editor(root: Path | str) -> VisualStudioEditorAudit:
    selected = Path(root).resolve()
    if not selected.is_dir():
        raise VisualStudioEditorError(f"Visual Studio extension root does not exist: {selected}.")

    try:
        previous = audit_visualstudio_extension(selected)
    except VisualStudioExtensionError as error:
        raise VisualStudioEditorError(str(error)) from error
    if previous.extension_sha256 != _EXPECTED_CONTRACT["required_t5_1_extension_sha256"]:
        raise VisualStudioEditorError("T5.1 Visual Studio extension fingerprint changed.")
    if CANONICAL_VISUAL_STUDIO_EXTENSION_SHA256 != _EXPECTED_CONTRACT["required_t5_1_extension_sha256"]:
        raise VisualStudioEditorError("Declared T5.1 Visual Studio extension fingerprint changed.")
    if CANONICAL_VISUAL_STUDIO_SYNTAX_SHA256 != _EXPECTED_CONTRACT["syntax_sha256"]:
        raise VisualStudioEditorError("T5.2 syntax contract fingerprint changed.")

    hashes: dict[str, str] = {}
    for relative in _EXPECTED_CONTRACT["required_files"]:
        path = selected / str(relative)
        if not path.is_file():
            raise VisualStudioEditorError(f"T5.2 Visual Studio editor file is missing: {relative}.")
        hashes[str(relative)] = _sha256(path.read_bytes())
    if hashes != dict(_EXPECTED_CONTRACT["file_sha256"]):
        changed = tuple(name for name in _EXPECTED_CONTRACT["required_files"] if hashes.get(str(name)) != dict(_EXPECTED_CONTRACT["file_sha256"]).get(str(name)))
        raise VisualStudioEditorError("T5.2 Visual Studio editor source drifted: " + ", ".join(changed))

    names = _read_text(selected / "src/ApexForge.VisualStudio/Classification/ApexForgeClassificationNames.cs")
    for marker in (
        '"apexforge.keyword"', '"apexforge.declaration"', '"apexforge.function"',
        '"apexforge.type"', '"apexforge.string"', '"apexforge.number"',
        '"apexforge.boolean"', '"apexforge.operator"', '"apexforge.punctuation"',
    ):
        _require_marker(names, marker, "ApexForgeClassificationNames.cs")

    types = _read_text(selected / "src/ApexForge.VisualStudio/Classification/ApexForgeClassificationTypes.cs")
    for marker in (
        "PredefinedClassificationTypeNames.Keyword",
        "PredefinedClassificationTypeNames.SymbolDefinition",
        "PredefinedClassificationTypeNames.Method",
        "PredefinedClassificationTypeNames.Identifier",
        "PredefinedClassificationTypeNames.String",
        "PredefinedClassificationTypeNames.Number",
        "PredefinedClassificationTypeNames.Operator",
        "PredefinedClassificationTypeNames.Punctuation",
    ):
        _require_marker(types, marker, "ApexForgeClassificationTypes.cs")
    if types.count("[Export(typeof(ClassificationTypeDefinition))]") != 9:
        raise VisualStudioEditorError("T5.2 must export exactly nine classification types.")

    formats = _read_text(selected / "src/ApexForge.VisualStudio/Classification/ApexForgeClassificationFormats.cs")
    if formats.count("[Export(typeof(EditorFormatDefinition))]") != 9:
        raise VisualStudioEditorError("T5.2 must export exactly nine editor format definitions.")
    if formats.count("[UserVisible(true)]") != 9:
        raise VisualStudioEditorError("Every T5.2 classification must be user-visible in Fonts and Colors.")
    if formats.count('DisplayName = "ApexForge ') != 9:
        raise VisualStudioEditorError("Every T5.2 format must assign a user-visible display name.")
    if "[DisplayName(" in formats:
        raise VisualStudioEditorError("T5.2 must not use the obsolete DisplayNameAttribute.")
    _require_marker(formats, "[Order(After = Priority.Default)]", "ApexForgeClassificationFormats.cs")

    provider = _read_text(selected / "src/ApexForge.VisualStudio/Classification/ApexForgeClassifierProvider.cs")
    for marker in (
        "[Export(typeof(IClassifierProvider))]",
        "[ContentType(ApexForgeContentType.Name)]",
        "IClassificationTypeRegistryService",
        "GetOrCreateSingletonProperty",
    ):
        _require_marker(provider, marker, "ApexForgeClassifierProvider.cs")

    classifier = _read_text(selected / "src/ApexForge.VisualStudio/Classification/ApexForgeClassifier.cs")
    for marker in (
        "internal sealed class ApexForgeClassifier : IClassifier",
        "GetClassificationSpans(SnapshotSpan span)",
        "snapshot.GetLineFromPosition",
        "ScanLine(line, span, results)",
        "NextNonWhitespaceIsOpenParenthesis",
        "IsTwoCharacterOperator",
        "Missing ApexForge classification type:",
        "end <= requestedSpan.Start.Position",
        "start >= requestedSpan.End.Position",
    ):
        _require_marker(classifier, marker, "ApexForgeClassifier.cs")
    if "//" in classifier or "/*" in classifier:
        raise VisualStudioEditorError("T5.2 classifier must not invent comment syntax before the grammar supports comments.")

    contract = dict(_EXPECTED_CONTRACT)
    contract["file_sha256"] = hashes
    fingerprint = _sha256(_canonical_json(contract))
    if fingerprint != CANONICAL_VISUAL_STUDIO_EDITOR_SHA256:
        raise VisualStudioEditorError(f"Visual Studio editor fingerprint changed: {fingerprint}.")
    return VisualStudioEditorAudit(selected, fingerprint, hashes)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", help="Visual Studio extension root")
    parser.add_argument("--check", action="store_true", help="audit the Visual Studio editor source")
    parser.add_argument("--contract", action="store_true", help="print the deterministic T5.2 editor fingerprint")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    arguments = _parser().parse_args(argv)
    try:
        if arguments.contract:
            print(CANONICAL_VISUAL_STUDIO_EDITOR_SHA256)
            return 0
        if arguments.check:
            if not arguments.root:
                raise VisualStudioEditorError("--check requires the Visual Studio extension root.")
            audit = audit_visualstudio_editor(arguments.root)
            print(f"Visual Studio T5.2 editor audit passed: {audit.editor_sha256}")
            return 0
        raise VisualStudioEditorError("Choose --check or --contract.")
    except VisualStudioEditorError as error:
        print(str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
