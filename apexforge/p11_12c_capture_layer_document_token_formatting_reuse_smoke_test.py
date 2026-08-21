"""P11.12C Capture-layer document/token/formatting reuse smoke test."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path
import inspect
import subprocess

import incremental_cache
import incremental_cache.capture as capture_module
from incremental_cache import CacheEntry, cache_identity_key
from incremental_cache.capture import (
    capture_document,
    capture_formatting,
    capture_tokens,
    document_capture_identity,
    formatting_capture_identity,
    formatting_edits_from_capture,
    token_capture_identity,
)
from language.lexer import Token
from language_server.formatting import format_document
from tooling.project_loader import LoadedProjectSource, load_project


PREDECESSOR_TAG = "afp-p11-12b-freeze"
PREDECESSOR_COMMIT = "2de18a85bc2243a9006d1ca87e511f19b84832ac"

B_HASHES = {
    "apexforge/incremental_cache/__init__.py":
        "D6F0DF0A689509F0A85662044A0B3759A9F5C494892513FCD74AB9C6D7B6AC68",
    "apexforge/incremental_cache/model.py":
        "055FF45999A452D19F7C2ECFFA473E29252F6DE3B9C7B3964C4F55BC3FCA1736",
    "apexforge/p11_12b_minimal_immutable_incremental_cache_model_smoke_test.py":
        "97AE4C7668847BD9AF0BCF5804ADD23BFFA1A49AF5AEC1A5CAB42C41F408E3C1",
    "docs/p11/P11_12B_MINIMAL_IMMUTABLE_INCREMENTAL_CACHE_MODEL.md":
        "3CCA5025A148D72F13F8B2707F6BB5928443D5121FFD1DFDC4F5CC8A74A9956C",
}

EXPECTED_CAPTURE_PUBLIC = (
    "document_capture_identity",
    "capture_document",
    "token_capture_identity",
    "capture_tokens",
    "formatting_capture_identity",
    "capture_formatting",
    "formatting_edits_from_capture",
)


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


def _sha256(path: Path) -> str:
    import hashlib
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _assert_predecessor() -> None:
    resolved = _git("rev-parse", "{}^{{}}".format(PREDECESSOR_TAG))
    _require(resolved.returncode == 0, resolved.stderr.strip())
    _require(
        resolved.stdout.strip() == PREDECESSOR_COMMIT,
        "P11.12B freeze target changed",
    )
    _require(
        _git("merge-base", "--is-ancestor", PREDECESSOR_TAG, "HEAD").returncode == 0,
        "P11.12B freeze is not ancestor of P11.12C",
    )
    for relative, expected in B_HASHES.items():
        _require(
            _sha256(_root() / relative) == expected,
            "{} P11.12B hash changed".format(relative),
        )


def _assert_b_surface_unchanged() -> None:
    _require(
        incremental_cache.__all__
        == (
            "CACHE_SCHEMA_VERSION",
            "CACHE_LAYER_IDS",
            "CACHE_FINGERPRINT_ALGORITHM",
            "CacheFingerprint",
            "CacheDependency",
            "CacheIdentity",
            "CacheEntry",
            "cache_fingerprint",
            "cache_identity_key",
        ),
        "P11.12C changed P11.12B package surface",
    )
    _require(
        capture_module.__all__ == EXPECTED_CAPTURE_PUBLIC,
        "Capture module public surface changed",
    )


def _source(
    name: str,
    path: Path,
    raw: bytes,
) -> LoadedProjectSource:
    normalized = (
        raw.decode("utf-8")
        .replace("\r\n", "\n")
        .replace("\r", "\n")
    )
    return LoadedProjectSource(
        name=name,
        path=path,
        source=normalized,
        source_bytes=raw,
    )


def _assert_document_capture() -> None:
    first = _source(
        "src/main.apex",
        Path("C:/synthetic/main.apex"),
        b"directive A {\r\n}\r\n",
    )
    second = _source(
        "src/main.apex",
        Path("C:/synthetic/main.apex"),
        b"directive A {\n}\n",
    )

    first_identity = document_capture_identity(first)
    second_identity = document_capture_identity(second)

    _require(
        cache_identity_key(first_identity)
        != cache_identity_key(second_identity),
        "raw newline change did not alter document identity",
    )

    first_entry = capture_document(first)
    _require(first_entry.value is first, "document owner reference not preserved")
    _require(
        capture_document(first, cached=first_entry) is first_entry,
        "matching document entry was not reused",
    )

    second_entry = capture_document(second, cached=first_entry)
    _require(
        second_entry is not first_entry,
        "changed raw document incorrectly reused cache entry",
    )
    _require(
        second_entry.value is second,
        "changed document did not preserve current source reference",
    )

    relocated = _source(
        "src/main.apex",
        Path("D:/relocated/main.apex"),
        first.source_bytes,
    )
    relocated_entry = capture_document(relocated, cached=first_entry)
    _require(
        relocated_entry is not first_entry,
        "document reuse leaked stale absolute path metadata",
    )


def _assert_token_capture() -> None:
    crlf = _source(
        "src/main.apex",
        Path("C:/synthetic/main.apex"),
        b"directive A {\r\n}\r\n",
    )
    lf = _source(
        "src/main.apex",
        Path("C:/synthetic/main.apex"),
        b"directive A {\n}\n",
    )

    _require(
        crlf.source == lf.source,
        "synthetic normalized sources should match",
    )
    _require(
        token_capture_identity(crlf) == token_capture_identity(lf),
        "newline-equivalent normalized token identity changed",
    )

    first = capture_tokens(crlf)
    _require(type(first.value) is tuple, "token capture value is not tuple")
    _require(first.value, "token capture produced empty tuple")
    _require(
        all(type(token) is Token for token in first.value),
        "token capture contains noncanonical token",
    )

    original_lex = capture_module._lex

    def forbidden_lex(*args, **kwargs):
        raise AssertionError("lexer invoked during exact token cache hit")

    capture_module._lex = forbidden_lex
    try:
        reused = capture_tokens(lf, cached=first)
    finally:
        capture_module._lex = original_lex

    _require(reused is first, "newline-equivalent token entry was not reused")

    changed_config = capture_tokens(
        crlf,
        inter_directive_line_comments=True,
        cached=first,
    )
    _require(
        changed_config is not first,
        "lexer configuration change incorrectly reused token entry",
    )

    renamed = _source(
        "src/renamed.apex",
        Path("C:/synthetic/main.apex"),
        crlf.source_bytes,
    )
    _require(
        token_capture_identity(renamed) != token_capture_identity(crlf),
        "source-name span identity was omitted from token subject",
    )

    corrupted = CacheEntry(
        identity=first.identity,
        artifact_fingerprint=first.artifact_fingerprint,
        value=(),
    )
    repaired = capture_tokens(crlf, cached=corrupted)
    _require(
        repaired is not corrupted and repaired.value,
        "invalid token payload was reused",
    )


def _all_immutable(value: object) -> bool:
    if value is None or type(value) in (str, int, float, bool):
        return True
    if type(value) is tuple:
        return all(_all_immutable(item) for item in value)
    return False


def _assert_formatting_capture() -> None:
    text = (
        "directive A {\n"
        "state x: Int = 0\n"
        "}\n"
    )
    uri = "file:///synthetic/main.apex"
    options = {"tabSize": 4, "insertSpaces": True}

    identity = formatting_capture_identity(uri, text, options)
    _require(
        identity.subject == uri,
        "formatter URI is not the Capture subject",
    )

    first = capture_formatting(uri, text, options)
    _require(
        _all_immutable(first.value),
        "formatting capture retained mutable list/dict values",
    )

    expected = format_document(uri, text, options)
    restored = formatting_edits_from_capture(first)
    _require(
        restored == expected,
        "formatting capture did not round-trip owner edits",
    )
    if expected:
        _require(
            restored is not expected,
            "non-empty formatting capture returned owner tuple reference",
        )
        _require(
            all(
                restored_edit is not expected_edit
                for restored_edit, expected_edit in zip(restored, expected)
            ),
            "non-empty formatting capture returned owner edit mapping reference",
        )
    else:
        _require(
            restored == (),
            "empty formatting result round-trip changed",
        )

    original_formatter = capture_module._format_document

    def forbidden_formatter(*args, **kwargs):
        raise AssertionError("formatter invoked during exact cache hit")

    capture_module._format_document = forbidden_formatter
    try:
        reused = capture_formatting(uri, text, options, cached=first)
    finally:
        capture_module._format_document = original_formatter

    _require(reused is first, "matching formatting entry was not reused")

    changed_tab = capture_formatting(
        uri,
        text,
        {"tabSize": 2, "insertSpaces": True},
        cached=first,
    )
    _require(
        changed_tab is not first,
        "tabSize change incorrectly reused formatting entry",
    )

    changed_spaces = capture_formatting(
        uri,
        text,
        {"tabSize": 4, "insertSpaces": False},
        cached=first,
    )
    _require(
        changed_spaces is not first,
        "insertSpaces change incorrectly reused formatting entry",
    )

    changed_uri_identity = formatting_capture_identity(
        "file:///synthetic/other.apex",
        text,
        options,
    )
    _require(
        changed_uri_identity != identity,
        "URI subject change did not alter formatting identity",
    )

    _require(
        formatting_capture_identity(
            uri,
            text,
            {
                "tabSize": 4,
                "insertSpaces": True,
                "irrelevantFutureClientKey": "ignored-by-capture",
            },
        )
        == identity,
        "non-output Capture option unexpectedly changed formatting identity",
    )

    bad_fingerprint = CacheEntry(
        identity=first.identity,
        artifact_fingerprint=capture_module.cache_fingerprint(b"bad"),
        value=first.value,
    )
    repaired = capture_formatting(
        uri,
        text,
        options,
        cached=bad_fingerprint,
    )
    _require(
        repaired is not bad_fingerprint,
        "corrupt formatting fingerprint was reused",
    )

    try:
        first.value += ()
    except (FrozenInstanceError, AttributeError, TypeError):
        pass


def _assert_signatures() -> None:
    expected = {
        document_capture_identity:
            "(source: 'LoadedProjectSource') -> 'CacheIdentity'",
        capture_document:
            "(source: 'LoadedProjectSource', *, cached: 'Optional[CacheEntry]' = None) -> 'CacheEntry'",
        token_capture_identity:
            "(source: 'LoadedProjectSource', *, inter_directive_line_comments: 'bool' = False) -> 'CacheIdentity'",
        capture_tokens:
            "(source: 'LoadedProjectSource', *, inter_directive_line_comments: 'bool' = False, cached: 'Optional[CacheEntry]' = None) -> 'CacheEntry'",
        formatting_capture_identity:
            "(uri: 'str', text: 'str', options: 'Mapping[str, object]') -> 'CacheIdentity'",
        capture_formatting:
            "(uri: 'str', text: 'str', options: 'Mapping[str, object]', *, cached: 'Optional[CacheEntry]' = None) -> 'CacheEntry'",
        formatting_edits_from_capture:
            "(entry: 'CacheEntry') -> 'Tuple[dict[str, object], ...]'",
    }
    for function, signature in expected.items():
        _require(
            str(inspect.signature(function)) == signature,
            "{} signature changed: {}".format(
                function.__name__,
                inspect.signature(function),
            ),
        )


def _assert_real_project() -> None:
    fixture = _root() / "apexforge" / "fixtures" / "p11_1b" / "manifest_entry"
    loaded = load_project(fixture)
    _require(len(loaded.sources) == 2, "real Capture fixture source count changed")

    for source in loaded.sources:
        document = capture_document(source)
        tokens = capture_tokens(source)
        formatting = capture_formatting(
            source.path.resolve().as_uri(),
            source.source,
            {"tabSize": 4, "insertSpaces": True},
        )

        _require(document.identity.layer_id == "capture", "document layer changed")
        _require(tokens.identity.layer_id == "capture", "token layer changed")
        _require(formatting.identity.layer_id == "capture", "format layer changed")

        _require(
            capture_document(source, cached=document) is document,
            "real document did not reuse",
        )
        _require(
            capture_tokens(source, cached=tokens) is tokens,
            "real tokens did not reuse",
        )
        _require(
            capture_formatting(
                source.path.resolve().as_uri(),
                source.source,
                {"tabSize": 4, "insertSpaces": True},
                cached=formatting,
            )
            is formatting,
            "real formatting did not reuse",
        )


def _assert_owner_immutability() -> None:
    paths = (
        "apexforge/air",
        "apexforge/language",
        "apexforge/quad_vector",
        "apexforge/semantic_lattice",
        "apexforge/aether_air",
        "apexforge/tam",
        "apexforge/tap_check",
        "apexforge/runtime",
        "apexforge/workflow",
        "apexforge/tooling",
        "apexforge/type_system",
        "apexforge/governance",
    )
    diff = _git("diff", "--exit-code", PREDECESSOR_TAG, "--", *paths)
    _require(diff.returncode == 0, "P11.12C mutated predecessor semantic owners")


def _assert_no_store_or_persistence() -> None:
    source = (
        _root() / "apexforge" / "incremental_cache" / "capture.py"
    ).read_text(encoding="utf-8")
    for token in (
        "sqlite",
        "pickle",
        "shelve",
        "tempfile",
        "ProjectBuilder",
        "build_project",
        "RuntimeEngine",
        "tap_check",
        "open(",
        "write_bytes",
        "write_text",
        "mtime",
        "datetime",
        "time.",
    ):
        _require(
            token not in source,
            "Capture layer acquired forbidden behavior: " + token,
        )


def main() -> None:
    _assert_predecessor()
    _assert_b_surface_unchanged()
    _assert_signatures()
    _assert_document_capture()
    _assert_token_capture()
    _assert_formatting_capture()
    _assert_real_project()
    _assert_owner_immutability()
    _assert_no_store_or_persistence()

    print("P11_12B_FREEZE_ANCESTRY=PASS")
    print("P11_12B_FULL_MODEL_SURFACE=UNCHANGED")
    print("CAPTURE_PUBLIC_OPERATION_COUNT=7")
    print("CAPTURE_DOCUMENT_OWNER=tooling.project_loader.LoadedProjectSource")
    print("CAPTURE_DOCUMENT_INPUT=EXACT_SOURCE_BYTES")
    print("CAPTURE_DOCUMENT_REUSE=PASS")
    print("CAPTURE_DOCUMENT_STALE_PATH_REUSE=REJECTED")
    print("CAPTURE_TOKEN_OWNER=language.lexer")
    print("CAPTURE_TOKEN_INPUT=NORMALIZED_SOURCE_TEXT_UTF8")
    print("CAPTURE_TOKEN_SUBJECT=SOURCE_NAME")
    print("CAPTURE_TOKEN_CONFIG=inter_directive_line_comments")
    print("CAPTURE_TOKEN_NEWLINE_EQUIVALENT_REUSE=PASS")
    print("CAPTURE_TOKEN_OWNER_INVOCATION_ON_HIT=NONE")
    print("CAPTURE_FORMATTING_OWNER=language_server.formatting")
    print("CAPTURE_FORMATTING_INPUT=EXACT_TEXT_UTF8")
    print("CAPTURE_FORMATTING_SUBJECT=URI")
    print("CAPTURE_FORMATTING_CONFIG=formatter fingerprint+tabSize+insertSpaces")
    print("CAPTURE_FORMATTING_VALUE=IMMUTABLE_CANONICAL_EDIT_TUPLE")
    print("CAPTURE_FORMATTING_ROUND_TRIP=PASS")
    print("CAPTURE_FORMATTING_OWNER_INVOCATION_ON_HIT=NONE")
    print("CAPTURE_CORRUPT_ENTRY_REUSE=REJECTED")
    print("CAPTURE_REAL_PROJECT_REUSE=PASS")
    print("GENERAL_CACHE_STORE=NONE")
    print("PERSISTENCE=NONE")
    print("PROJECT_BUILDER_INTEGRATION=NONE")
    print("SEMANTIC_OWNER_MUTATION=NONE")
    print("RUNTIME_EXECUTION=NONE")
    print("P11_12C_CAPTURE_LAYER_REUSE=PASS")


if __name__ == "__main__":
    main()