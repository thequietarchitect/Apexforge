"""AFP-P10-T5.3 Visual Studio language-client launch contract."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
from typing import Final, Iterable, Mapping, Optional, Sequence, Tuple

P10_T5_VISUAL_STUDIO_LANGUAGE_CLIENT_VERSION: Final[str] = "10-T5.3"
VISUAL_STUDIO_LANGUAGE_CLIENT_SCHEMA: Final[int] = 1
VISUAL_STUDIO_LANGUAGE_CLIENT_KIND: Final[str] = "apexforge.visual-studio-language-client"
REPOSITORY_ENVIRONMENT_VARIABLE: Final[str] = "APEXFORGE_REPOSITORY_ROOT"
PYTHON_ENVIRONMENT_VARIABLE: Final[str] = "APEXFORGE_PYTHON"
RELATIVE_SERVER_SCRIPT: Final[str] = "apexforge/apexforge_lsp.py"
DEFAULT_PYTHON_EXECUTABLE: Final[str] = "py.exe"

_CONTRACT: Final[Mapping[str, object]] = {
    "schema": VISUAL_STUDIO_LANGUAGE_CLIENT_SCHEMA,
    "kind": VISUAL_STUDIO_LANGUAGE_CLIENT_KIND,
    "client_version": P10_T5_VISUAL_STUDIO_LANGUAGE_CLIENT_VERSION,
    "content_type": "apexforge",
    "content_base": "code-remote",
    "client_interface": "Microsoft.VisualStudio.LanguageServer.Client.ILanguageClient",
    "client_package": "Microsoft.VisualStudio.LanguageServer.Client@17.14.60",
    "transport": "stdio",
    "server_script": RELATIVE_SERVER_SCRIPT,
    "server_arguments": ("--stdio",),
    "repository_environment_variable": REPOSITORY_ENVIRONMENT_VARIABLE,
    "python_environment_variable": PYTHON_ENVIRONMENT_VARIABLE,
    "default_python_executable": DEFAULT_PYTHON_EXECUTABLE,
    "default_repository_candidates": (
        "%USERPROFILE%/source/repos/ApexForge",
        "%USERPROFILE%/Documents/GitHub/ApexForge",
    ),
    "repository_walk_depth": 12,
    "python_utf8": True,
    "python_no_bytecode": True,
    "stderr_drained": True,
    "activation_cancellation_checked": True,
    "show_notification_on_initialize_failed": True,
    "structured_initialize_failure_callback": True,
    "legacy_exception_failure_callback": True,
    "previous_process_terminated_before_restart": True,
    "log_relative_to_temp": "ApexForge/visualstudio-language-client.log",
    "t4_server_modified": False,
}


def visual_studio_language_client_contract() -> Mapping[str, object]:
    return _CONTRACT


def visual_studio_language_client_fingerprint() -> str:
    payload = json.dumps(
        _CONTRACT,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


CANONICAL_VISUAL_STUDIO_LANGUAGE_CLIENT_SHA256: Final[str] = "6248cc0469bcaaed7a11358334e9a23fc9c1f965d38c23bb724dc9c5c9d52921"


@dataclass(frozen=True)
class LanguageServerLaunchPlan:
    repository_root: Path
    python_executable: str
    script_path: Path
    arguments: Tuple[str, ...]
    working_directory: Path


def _is_repository_root(path: Path) -> bool:
    return (
        (path / RELATIVE_SERVER_SCRIPT).is_file()
        and (path / "apexforge/language_server/server.py").is_file()
        and (path / "apexforge/language_server/integration.py").is_file()
    )


def _walk_parents(path: Path, depth: int = 12) -> Iterable[Path]:
    current = path
    for _ in range(depth):
        yield current
        if current.parent == current:
            break
        current = current.parent


def resolve_repository_root(
    seeds: Sequence[Path],
    *,
    environment_root: Optional[Path] = None,
    user_profile: Optional[Path] = None,
) -> Path:
    candidates = []
    if environment_root is not None:
        candidates.append(environment_root)
    candidates.extend(seeds)
    if user_profile is not None:
        candidates.extend((
            user_profile / "source/repos/ApexForge",
            user_profile / "Documents/GitHub/ApexForge",
        ))

    seen = set()
    for candidate in candidates:
        for expanded in _walk_parents(Path(candidate).resolve()):
            key = os.path.normcase(str(expanded))
            if key in seen:
                continue
            seen.add(key)
            if _is_repository_root(expanded):
                return expanded
    raise FileNotFoundError(
        "Could not locate the ApexForge repository; set "
        + REPOSITORY_ENVIRONMENT_VARIABLE
        + "."
    )


def build_launch_plan(
    repository_root: Path,
    *,
    python_executable: str = DEFAULT_PYTHON_EXECUTABLE,
) -> LanguageServerLaunchPlan:
    root = Path(repository_root).resolve()
    if not _is_repository_root(root):
        raise FileNotFoundError("ApexForge repository markers are missing: " + str(root))
    if type(python_executable) is not str or not python_executable.strip():
        raise ValueError("python_executable must be non-empty")
    script = root / RELATIVE_SERVER_SCRIPT
    return LanguageServerLaunchPlan(
        repository_root=root,
        python_executable=python_executable,
        script_path=script,
        arguments=(str(script), "--stdio"),
        working_directory=root / "apexforge",
    )


__all__ = (
    "CANONICAL_VISUAL_STUDIO_LANGUAGE_CLIENT_SHA256",
    "DEFAULT_PYTHON_EXECUTABLE",
    "LanguageServerLaunchPlan",
    "P10_T5_VISUAL_STUDIO_LANGUAGE_CLIENT_VERSION",
    "PYTHON_ENVIRONMENT_VARIABLE",
    "RELATIVE_SERVER_SCRIPT",
    "REPOSITORY_ENVIRONMENT_VARIABLE",
    "VISUAL_STUDIO_LANGUAGE_CLIENT_KIND",
    "VISUAL_STUDIO_LANGUAGE_CLIENT_SCHEMA",
    "build_launch_plan",
    "resolve_repository_root",
    "visual_studio_language_client_contract",
    "visual_studio_language_client_fingerprint",
)
