"""Audit ApexForge model ownership and Python class identity.

This script is read-only. It reports duplicate class identities and the
bindings used by compiler/runtime consumers.
"""

from __future__ import annotations

import importlib
import inspect
from collections import defaultdict
from typing import Any, DefaultDict, Dict, List, Sequence, Tuple


MODEL_MODULES: Sequence[str] = (
    "air.model",
    "causality.model",
    "authority.model",
    "runtime.state",
    "runtime.context",
    "apexforge_air",
)

CONSUMER_MODULES: Sequence[str] = (
    "language.compiler",
    "language.validation.runtime_validator",
    "runtime.engine",
    "causality.engine",
)

FOCUS_SYMBOLS: Sequence[str] = (
    "AIRProgram",
    "VerifiedAIRProgram",
    "AIRDirective",
    "StateDefinition",
    "EventDefinition",
    "StateAssignment",
    "EventEmission",
    "DirectiveInvocation",
    "AIRWhenAction",
    "CausalDecision",
    "CausalPath",
    "Principal",
    "AuthorityCheck",
    "AuthorityGrant",
    "EffectIntent",
    "StateSnapshot",
    "StateDelta",
    "ExecutionContext",
    "EventRecord",
    "Fact",
)

import sys
from pathlib import Path


PACKAGE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_DIR.parent
LEGACY_AIR_FILE = PROJECT_ROOT / "apexforge_air.py"


# Make both layouts importable:
# ApexForge/apexforge_air.py
# ApexForge/apexforge/air, runtime, causality, etc.
for import_path in (
    PROJECT_ROOT,
    PACKAGE_DIR,
):
    import_path_text = str(import_path)

    if import_path_text not in sys.path:
        sys.path.insert(
            0,
            import_path_text,
        )


print("\n=== IMPORT PATH DIAGNOSTIC ===")
print(
    "PACKAGE_DIR:",
    PACKAGE_DIR,
)
print(
    "PROJECT_ROOT:",
    PROJECT_ROOT,
)
print(
    "LEGACY_AIR_FILE:",
    LEGACY_AIR_FILE,
)
print(
    "LEGACY_AIR_EXISTS:",
    LEGACY_AIR_FILE.is_file(),
)

print("\nSYS.PATH:")
for index, path_entry in enumerate(
    sys.path
):
    print(
        f"[{index}] {path_entry}"
    )

print("\n=== LEGACY AIR IMPORT TEST ===")

try:
    import apexforge_air

    print(
        "IMPORT_SUCCESS:",
        True,
    )
    print(
        "IMPORTED_FROM:",
        apexforge_air.__file__,
    )
    print(
        "HAS_EFFECT_INTENT:",
        hasattr(
            apexforge_air,
            "EffectIntent",
        ),
    )

except Exception as exc:
    print(
        "IMPORT_SUCCESS:",
        False,
    )
    print(
        "ERROR_TYPE:",
        type(exc).__name__,
    )
    print(
        "ERROR_MESSAGE:",
        str(exc),
    )


def load_modules(names: Sequence[str]) -> Tuple[Dict[str, Any], Dict[str, str]]:
    loaded: Dict[str, Any] = {}
    failures: Dict[str, str] = {}

    for name in names:
        try:
            loaded[name] = importlib.import_module(name)
        except Exception as exc:
            failures[name] = f"{type(exc).__name__}: {exc}"

    return loaded, failures


def source_path(value: Any) -> str:
    try:
        return str(inspect.getsourcefile(value) or inspect.getfile(value))
    except (TypeError, OSError):
        return "<unknown>"


def show_failures(title: str, failures: Dict[str, str]) -> None:
    print(f"\n=== {title} ===")
    if not failures:
        print("None")
        return

    for module_name, message in failures.items():
        print(f"{module_name}: {message}")


def audit_models(modules: Dict[str, Any]) -> int:
    records: DefaultDict[str, List[Tuple[str, Any]]] = defaultdict(list)

    print("\n=== MODEL SYMBOL LOCATIONS ===")

    for module_name, module in modules.items():
        print(f"\n[{module_name}]")
        found = False

        for symbol_name in FOCUS_SYMBOLS:
            value = getattr(module, symbol_name, None)
            if not inspect.isclass(value):
                continue

            found = True
            records[symbol_name].append((module_name, value))
            kind = "definition" if value.__module__ == module_name else "re-export"

            print(
                f"{symbol_name:<24} {kind:<10} "
                f"id={hex(id(value))} "
                f"defined_by={value.__module__} "
                f"file={source_path(value)}"
            )

        if not found:
            print("No focus classes found.")

    duplicate_count = 0
    print("\n=== CLASS IDENTITY SUMMARY ===")

    for symbol_name in FOCUS_SYMBOLS:
        entries = records.get(symbol_name, [])
        if not entries:
            print(f"[MISSING]   {symbol_name}")
            continue

        identities: DefaultDict[int, List[Tuple[str, Any]]] = defaultdict(list)
        for module_name, value in entries:
            identities[id(value)].append((module_name, value))

        if len(identities) == 1:
            locations = ", ".join(name for name, _ in entries)
            status = "SINGLE" if len(entries) == 1 else "SHARED"
            print(
                f"[{status:<7}] {symbol_name}: "
                f"one class object across {locations}"
            )
            continue

        duplicate_count += 1
        print(
            f"[DUPLICATE] {symbol_name}: "
            f"{len(identities)} different class objects"
        )

        for object_id, identity_entries in identities.items():
            value = identity_entries[0][1]
            locations = ", ".join(name for name, _ in identity_entries)
            print(
                f"    id={hex(object_id)} "
                f"defined_by={value.__module__} "
                f"visible_in={locations} "
                f"file={source_path(value)}"
            )

    return duplicate_count


def audit_consumers(modules: Dict[str, Any]) -> None:
    print("\n=== CONSUMER BINDINGS ===")

    for module_name, module in modules.items():
        print(f"\n[{module_name}]")
        found = False

        for symbol_name in FOCUS_SYMBOLS:
            value = getattr(module, symbol_name, None)
            if not inspect.isclass(value):
                continue

            found = True
            print(
                f"{symbol_name:<24} "
                f"id={hex(id(value))} "
                f"defined_by={value.__module__} "
                f"file={source_path(value)}"
            )

        if not found:
            print("No focus classes are bound directly in this module.")


def main() -> None:
    print("ApexForge Model Identity Audit")
    print("==============================")

    model_modules, model_failures = load_modules(MODEL_MODULES)
    consumer_modules, consumer_failures = load_modules(CONSUMER_MODULES)

    show_failures("MODEL IMPORT FAILURES", model_failures)
    show_failures("CONSUMER IMPORT FAILURES", consumer_failures)

    duplicate_count = audit_models(model_modules)
    audit_consumers(consumer_modules)

    print("\n=== AUDIT RESULT ===")
    print(
        "The risk is one class name mapping to multiple Python class objects."
    )
    print(f"Focus symbols with duplicate identities: {duplicate_count}")

    if duplicate_count:
        print(
            "Status: consolidation required. "
            "Migrate imports one model family at a time."
        )
    else:
        print(
            "Status: no duplicate identities detected "
            "among the focus symbols."
        )


if __name__ == "__main__":
    main() 