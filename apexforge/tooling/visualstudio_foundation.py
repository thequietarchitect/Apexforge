"""AFP-P10-T5.1 Visual Studio extension foundation contract."""
from __future__ import annotations

import hashlib
import json
from typing import Final, Mapping

P10_T5_VISUAL_STUDIO_FOUNDATION_VERSION: Final[str] = "10-T5.1"
VISUAL_STUDIO_FOUNDATION_SCHEMA: Final[int] = 1
VISUAL_STUDIO_FOUNDATION_KIND: Final[str] = "apexforge.visual-studio-foundation"

_CONTRACT: Final[Mapping[str, object]] = {'schema': 1, 'kind': 'apexforge.visual-studio-foundation', 'foundation_version': '10-T5.1', 'required_t4_integration_sha256': 'c2fff74134a40bd335e1c04123127d4cc87df7aa2ed3accc5133d93da9066897', 'solution': 'editors/visualstudio-apexforge/ApexForge.VisualStudio.sln', 'project': 'src/ApexForge.VisualStudio/ApexForge.VisualStudio.csproj', 'target_framework': 'net472', 'platform_target': 'AnyCPU', 'visual_studio_api_line': '17.x', 'minimum_visual_studio_version': '17.0', 'installation_target': '[17.0,)', 'architectures': ('amd64', 'arm64'), 'vsix': {'id': 'GravitasStudios.ApexForge.VisualStudio', 'version': '0.1.0', 'publisher': 'Gravitas Studios', 'display_name': 'ApexForge Language Tools'}, 'nuget': {'Microsoft.VisualStudio.SDK': '17.14.40265', 'Microsoft.VSSDK.BuildTools': '18.5.40034'}, 'assets': ('Microsoft.VisualStudio.VsPackage', 'Microsoft.VisualStudio.MefComponent'), 'content_type': {'name': 'apexforge', 'base': 'text', 'extension': '.apex'}, 'package': {'guid': 'DF54A578-54A2-52F4-8643-4A85DDDFB2F2', 'background_loading': True, 'menu_resource': 'Menus.ctmenu'}, 'command': {'set_guid': '744A30FD-DF87-5104-A449-A95DF8E526FA', 'id': '0x0100', 'location': 'Tools', 'label': 'ApexForge Extension Status'}, 'features_deferred': ('syntax_classification', 'file_icon', 'language_server_process_bridge', 'document_synchronization', 'diagnostics', 'completion', 'hover', 'definition', 'references', 'rename', 'workspace_symbols', 'formatting', 'integration_hardening')}


def visual_studio_foundation_contract() -> Mapping[str, object]:
    return _CONTRACT


def visual_studio_foundation_fingerprint() -> str:
    payload = json.dumps(
        visual_studio_foundation_contract(),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


CANONICAL_VISUAL_STUDIO_FOUNDATION_SHA256: Final[str] = "4c18e2840fa7ca7d74307f8ef71dc0510a84c0c6aa5b99619eb3a522ef4c3f54"


__all__ = (
    "CANONICAL_VISUAL_STUDIO_FOUNDATION_SHA256",
    "P10_T5_VISUAL_STUDIO_FOUNDATION_VERSION",
    "VISUAL_STUDIO_FOUNDATION_KIND",
    "VISUAL_STUDIO_FOUNDATION_SCHEMA",
    "visual_studio_foundation_contract",
    "visual_studio_foundation_fingerprint",
)
