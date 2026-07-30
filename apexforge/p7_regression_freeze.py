"""Run the complete known AFP-P7 and core P6 regression boundary."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parent

REQUIRED = (
    "p7_function_frontend_smoke_test.py",
    "p7_function_linking_validation_smoke_test.py",
    "p7_function_runtime_smoke_test.py",
    "p7_local_binding_smoke_test.py",
    "p7_function_conditional_smoke_test.py",
    "p7_function_control_flow_smoke_test.py",
    "p7_project_integration_smoke_test.py",
    "air_program_linker_smoke_test.py",
    "directive_invocation_runtime_smoke_test.py",
)

MODULE_TEST_ALIASES = (
    "module_import_smoke_test.py",
    "module_imports_smoke_test.py",
)


def resolve_module_test() -> str:
    for name in MODULE_TEST_ALIASES:
        if (ROOT / name).is_file():
            return name
    raise FileNotFoundError(
        "Missing module/import regression test; expected one of: "
        + ", ".join(MODULE_TEST_ALIASES)
    )


def run_script(name: str, env: dict[str, str]) -> None:
    path = ROOT / name
    if not path.is_file():
        raise FileNotFoundError(f"Missing regression test: {name}")

    print(f"\n=== {name} ===", flush=True)
    completed = subprocess.run(
        [sys.executable, str(path)],
        cwd=ROOT,
        env=env,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"Regression test {name!r} failed with exit code "
            f"{completed.returncode}."
        )


def main() -> None:
    env = os.environ.copy()
    existing_pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = (
        str(ROOT)
        if not existing_pythonpath
        else os.pathsep.join((str(ROOT), existing_pythonpath))
    )

    tests = REQUIRED + (resolve_module_test(),)
    for name in tests:
        run_script(name, env)

    print("\nAFP-P7 REGRESSION FREEZE PASSED.")
    print(f"Tests executed: {len(tests)}")


if __name__ == "__main__":
    main()