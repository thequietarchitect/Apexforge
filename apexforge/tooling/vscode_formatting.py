"""AFP-P10-T4.10 VS Code whole-document formatting integration audit."""
from __future__ import annotations
import argparse, hashlib, json, subprocess, sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Final, Mapping, Optional, Sequence, TextIO
from zipfile import BadZipFile, ZipFile
from language_server.formatting import CANONICAL_FORMATTING_SHA256
from tooling.vscode_lsp_activation import CANONICAL_LANGUAGE_SERVER_GUIDE, CANONICAL_RUNTIME_CLIENT_PATH
from tooling.vscode_package import CANONICAL_VSCODE_EXTENSION_ID, CANONICAL_VSCODE_PACKAGE_VERSION
from tooling.vscode_workspace_symbols import CANONICAL_VSCODE_WORKSPACE_SYMBOLS_SHA256, VSCodeWorkspaceSymbolsError, audit_vscode_workspace_symbols
P10_T4_VSCODE_FORMATTING_VERSION: Final[str]="10-T4.10"
VSCODE_FORMATTING_SCHEMA: Final[int]=1
VSCODE_FORMATTING_KIND: Final[str]="apexforge.vscode-formatting"
FORMATTING_METHOD: Final[str]="textDocument/formatting"
FORMATTING_PROVIDER: Final[str]="registerDocumentFormattingEditProvider"
_RUNTIME_SOURCE_PATHS: Final[tuple[str,...]]=("extension.js",CANONICAL_RUNTIME_CLIENT_PATH,CANONICAL_LANGUAGE_SERVER_GUIDE)
CANONICAL_VSCODE_FORMATTING_SHA256: Final[str]="46a4267481b3f4fabd250c7324cc3b4f7be98bb6d5b2b7a52ef05bb6fc27c6ff"
class VSCodeFormattingError(ValueError):
    code: Final[str]="APX-VSCODE-011"
    def __init__(self,message:str)->None:
        if type(message) is not str or not message: raise ValueError("VSCodeFormattingError.message must be non-empty.")
        self.message=message; super().__init__(f"[{self.code}] {message}")
@dataclass(frozen=True)
class VSCodeFormattingAudit:
    extension_root:Path; extension_id:str; package_version:str; runtime_file_count:int; formatting_sha256:str
@dataclass(frozen=True)
class VSCodeFormattingVSIXAudit:
    vsix_path:Path; archive_file_count:int; formatting_sha256:str; vsix_sha256:str
def _read_bytes(path:Path,owner:str)->bytes:
    try:return path.read_bytes()
    except OSError as error:raise VSCodeFormattingError(f"Could not read {owner} at {path}: {error}.") from error
def _sha256_bytes(data:bytes)->str:return hashlib.sha256(data).hexdigest()
def _sha256_file(path:Path)->str:return _sha256_bytes(_read_bytes(path,str(path)))
def _runtime_hashes(root:Path)->Mapping[str,str]:
    hashes={};texts={}
    for name in _RUNTIME_SOURCE_PATHS:
        data=_read_bytes(root/PurePosixPath(name),f"T4.10 runtime source {name}");hashes[name]=_sha256_bytes(data)
        try:texts[name]=data.decode("utf-8")
        except UnicodeDecodeError as error:raise VSCodeFormattingError(f"T4.10 runtime source {name!r} must be UTF-8.") from error
    for marker in ("registerDocumentFormattingEditProvider","provideDocumentFormattingEdits","textDocument/formatting","convertTextEdits","new vscode.TextEdit","formatDocument(document, options, token)","formatting: {","dynamicRegistration: false"):
        if marker not in texts["extension.js"]:raise VSCodeFormattingError(f"extension.js omitted T4.10 marker {marker!r}.")
    for marker in ("textDocument/formatting","Shift+Alt+F","Format Document","whole-document","Invalid source","Range formatting","format-on-type","T4.11"):
        if marker not in texts[CANONICAL_LANGUAGE_SERVER_GUIDE]:raise VSCodeFormattingError(f"LANGUAGE_SERVER.md omitted T4.10 marker {marker!r}.")
    return hashes
def formatting_contract(runtime_hashes:Mapping[str,str])->Mapping[str,object]:
    return dict({'schema': 1, 'kind': 'apexforge.vscode-formatting', 'formatting_version': '10-T4.10', 'extension': {'id': 'gravitas-studios.apexforge-language', 'version': '0.1.0'}, 'method': 'textDocument/formatting', 'provider': 'registerDocumentFormattingEditProvider', 'selector': {'language': 'apexforge', 'scheme': 'file'}, 'result': 'vscode.TextEdit[]', 'workspace_model': 'one server process per workspace folder', 'server_formatting_sha256': '63ac984979dd14832dd7d69490176a6e877c867c00c30116636d6c6e5fef3e4b', 'frozen_workspace_symbols_sha256': 'ddf809a166f95fed8215a2a6cbcf11f0f318199d5dfb8f719fa09ec49e60c9aa', 'features_deferred': ('range_formatting', 'format_on_type', 'cross_file_definition', 'workspace_references', 'cross_file_rename', 'integration_hardening')}, runtime_hashes=dict(runtime_hashes))
def formatting_fingerprint(runtime_hashes:Mapping[str,str])->str:
    for name in _RUNTIME_SOURCE_PATHS:
        if name not in runtime_hashes:raise VSCodeFormattingError(f"T4.10 runtime hash projection is missing {name!r}.")
    return hashlib.sha256(json.dumps(formatting_contract(runtime_hashes),ensure_ascii=False,separators=(",",":"),sort_keys=True).encode("utf-8")).hexdigest()
def audit_vscode_formatting(extension_root:Path)->VSCodeFormattingAudit:
    root=Path(extension_root).resolve()
    if not root.is_dir():raise VSCodeFormattingError(f"VS Code extension directory does not exist: {root}.")
    try:previous=audit_vscode_workspace_symbols(root)
    except VSCodeWorkspaceSymbolsError as error:raise VSCodeFormattingError(str(error)) from error
    if previous.workspace_symbols_sha256!=CANONICAL_VSCODE_WORKSPACE_SYMBOLS_SHA256:raise VSCodeFormattingError("Frozen T4.9 workspace-symbol projection changed.")
    hashes=_runtime_hashes(root);observed=formatting_fingerprint(hashes)
    if observed!=CANONICAL_VSCODE_FORMATTING_SHA256:raise VSCodeFormattingError(f"VS Code formatting fingerprint changed; expected {CANONICAL_VSCODE_FORMATTING_SHA256}, received {observed}.")
    return VSCodeFormattingAudit(root,CANONICAL_VSCODE_EXTENSION_ID,CANONICAL_VSCODE_PACKAGE_VERSION,len(_RUNTIME_SOURCE_PATHS),observed)
def _safe_archive_name(name:str)->str:
    if type(name) is not str or not name or "\\" in name:raise VSCodeFormattingError(f"Unsafe VSIX archive path {name!r}.")
    path=PurePosixPath(name)
    if path.is_absolute() or any(part in ("",".","..") for part in path.parts):raise VSCodeFormattingError(f"Unsafe VSIX archive path {name!r}.")
    return path.as_posix()
def _archive_index(archive:ZipFile)->Mapping[str,str]:
    index={}
    for info in archive.infolist():
        if info.is_dir():continue
        normalized=_safe_archive_name(info.filename);folded=normalized.casefold()
        if folded in index:raise VSCodeFormattingError(f"VSIX contains duplicate case-insensitive path {normalized!r}.")
        index[folded]=normalized
    return index
def audit_vscode_formatting_vsix(extension_root:Path,vsix_path:Path)->VSCodeFormattingVSIXAudit:
    source=audit_vscode_formatting(extension_root);package=Path(vsix_path).resolve()
    if not package.is_file():raise VSCodeFormattingError(f"VSIX file does not exist: {package}.")
    required={"extension/extension.js":"extension.js","extension/runtime/lsp-client.js":CANONICAL_RUNTIME_CLIENT_PATH,"extension/language_server.md":CANONICAL_LANGUAGE_SERVER_GUIDE}
    try:
        with ZipFile(package,"r") as archive:
            index=_archive_index(archive);missing=tuple(sorted(name for name in required if name not in index))
            if missing:raise VSCodeFormattingError(f"VSIX is missing T4.10 runtime files: {missing}.")
            for archive_name,source_name in required.items():
                if archive.read(index[archive_name])!=_read_bytes(Path(extension_root).resolve()/PurePosixPath(source_name),f"canonical T4.10 source {source_name}"):raise VSCodeFormattingError(f"VSIX payload differs from T4.10 source {source_name!r}.")
            count=len(index)
    except (BadZipFile,OSError) as error:raise VSCodeFormattingError(f"Could not audit VSIX {package}: {error}.") from error
    return VSCodeFormattingVSIXAudit(package,count,source.formatting_sha256,_sha256_file(package))
def check_node_syntax(extension_root:Path,node_command:Optional[str]=None)->tuple[str,...]:
    selected=node_command
    if not selected:
        from shutil import which
        selected=which("node")
    if not selected:raise VSCodeFormattingError("Node.js was not found on PATH.")
    checked=[]
    for name in ("extension.js",CANONICAL_RUNTIME_CLIENT_PATH):
        completed=subprocess.run((selected,"--check",str(Path(extension_root).resolve()/PurePosixPath(name))),check=False,capture_output=True,text=True)
        if completed.returncode!=0:raise VSCodeFormattingError(f"Node.js syntax check failed for {name!r}: {(completed.stderr or completed.stdout or '').strip()}.")
        checked.append(name)
    return tuple(checked)
def main(argv:Optional[Sequence[str]]=None,*,stdout:TextIO=sys.stdout,stderr:TextIO=sys.stderr)->int:
    parser=argparse.ArgumentParser(prog="python -m tooling.vscode_formatting",description="Audit AFP-P10-T4.10 VS Code formatting integration.")
    parser.add_argument("extension_root",type=Path);mode=parser.add_mutually_exclusive_group(required=True);mode.add_argument("--check",action="store_true");mode.add_argument("--check-vsix",type=Path,metavar="VSIX");mode.add_argument("--contract",action="store_true");args=parser.parse_args(tuple(argv) if argv is not None else None)
    try:
        if args.contract:audit_vscode_formatting(args.extension_root);print(CANONICAL_VSCODE_FORMATTING_SHA256,file=stdout);return 0
        if args.check_vsix is not None:
            audit=audit_vscode_formatting_vsix(args.extension_root,args.check_vsix);print("AFP-P10-T4.10 VS Code formatting VSIX audit passed.",file=stdout);print(f"Archive files: {audit.archive_file_count}",file=stdout);print(f"Formatting SHA-256: {audit.formatting_sha256}",file=stdout);print(f"VSIX SHA-256: {audit.vsix_sha256}",file=stdout);return 0
        audit=audit_vscode_formatting(args.extension_root);checked=check_node_syntax(args.extension_root);print("AFP-P10-T4.10 VS Code formatting check passed.",file=stdout);print(f"Extension ID: {audit.extension_id}",file=stdout);print(f"Runtime files: {audit.runtime_file_count}",file=stdout);print(f"Node syntax files: {len(checked)}",file=stdout);print(f"Formatting SHA-256: {audit.formatting_sha256}",file=stdout);return 0
    except VSCodeFormattingError as error:print(str(error),file=stderr);return 1
__all__=("CANONICAL_VSCODE_FORMATTING_SHA256","FORMATTING_METHOD","FORMATTING_PROVIDER","P10_T4_VSCODE_FORMATTING_VERSION","VSCODE_FORMATTING_KIND","VSCODE_FORMATTING_SCHEMA","VSCodeFormattingAudit","VSCodeFormattingError","VSCodeFormattingVSIXAudit","audit_vscode_formatting","audit_vscode_formatting_vsix","check_node_syntax","formatting_contract","formatting_fingerprint","main")
if __name__=="__main__":raise SystemExit(main())
