"""Bounded Windows x64 native build and dispatch. No language evaluator."""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
from hashlib import sha256
import ctypes
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import weakref

from .native_execution_contract import NativeExecutionError, admit_native_profile, require
from .payload import CanonicalExecutionPayload
from .result import CanonicalExecutionResult
from .value import CanonicalExecutionValue


OPTIONS = ("/nologo", "/TC", "/W4", "/WX", "/Od", "/GS-", "/Zl", "/Brepro",
           "program.c", "/Foprogram.obj", "/Feprogram.exe", "/link", "/Brepro",
           "/INCREMENTAL:NO", "/MACHINE:X64", "/SUBSYSTEM:CONSOLE",
           "/ENTRY:apexforge_entry", "/NODEFAULTLIB", "kernel32.lib")


def digest(data: bytes) -> str:
    return sha256(data).hexdigest().upper()


def canonical(record) -> str:
    return json.dumps(record, sort_keys=True, ensure_ascii=True, separators=(",", ":"))


def _constant(value: int) -> str:
    return "(-9223372036854775807LL - 1LL)" if value == -(2 ** 63) else f"{value}LL"


def _source(admission, *, region_sink=None) -> bytes:
    # No AIR names enter C identifiers. Stores retain the admitted order.
    lines = [
        'typedef unsigned long DWORD;',
        '__declspec(dllimport) void * __stdcall GetStdHandle(DWORD);',
        '__declspec(dllimport) int __stdcall WriteFile(void *, const void *, DWORD, DWORD *, void *);',
        '__declspec(dllimport) void __stdcall ExitProcess(unsigned int);',
        'typedef char widths_must_match[(sizeof(__int64)==8 && sizeof(DWORD)==4) ? 1 : -1];',
        'static void emit(__int64 value) {',
        '  unsigned __int64 bits = (unsigned __int64)value;',
        '  unsigned char bytes[8]; DWORD written = 0; unsigned int i;',
        '  for (i=0; i<8; ++i) bytes[i]=(unsigned char)(bits >> (8*i));',
        '  if (!WriteFile(GetStdHandle((DWORD)-11), bytes, 8, &written, 0) || written!=8) ExitProcess(70);',
        '}',
        'void __stdcall apexforge_entry(void) {',
    ]
    # Side-channel ranges are recorded by the emitter, never reconstructed from C.
    offset = sum(len(line) + 1 for line in lines)
    ordinal = 0
    for index, value in enumerate(admission.initial_values):
        line = f'  volatile __int64 s{index} = {_constant(value)};'
        lines.append(line)
        if region_sink is not None:
            region_sink.append((ordinal, offset, offset + len(line)))
        offset += len(line) + 1
        ordinal += 1
    for index, value in admission.stores:
        line = f'  s{index} = {_constant(value)};'
        lines.append(line)
        if region_sink is not None:
            region_sink.append((ordinal, offset, offset + len(line)))
        offset += len(line) + 1
        ordinal += 1
    lines += [f'  emit(s{index});' for index in range(len(admission.state_ids))]
    lines += ['  ExitProcess(0);', '}', '']
    return '\n'.join(lines).encode('ascii')


def _timeout(value) -> float:
    require(type(value) in (int, float) and 0 < value <= 300 and math.isfinite(value),
            "timeout must be finite, positive, and at most 300 seconds", "NATIVE_TIMEOUT_INVALID")
    return float(value)


def _toolchain(directory: Path):
    require(os.name == "nt", "Windows x64 required", "NATIVE_PLATFORM_UNSUPPORTED")
    locator = Path(os.environ.get("ProgramFiles(x86)", "")) / "Microsoft Visual Studio/Installer/vswhere.exe"
    try:
        probe = subprocess.run([str(locator), "-latest", "-products", "*", "-requires",
                                "Microsoft.VisualStudio.Component.VC.Tools.x86.x64", "-property", "installationPath"],
                               capture_output=True, check=True, timeout=30)
        installation = probe.stdout.decode("utf-8-sig").strip()
        require(bool(installation) and not any(c in installation for c in '\r\n"%!^&|<>'),
                "invalid toolchain discovery", "NATIVE_TOOLCHAIN_UNAVAILABLE")
        developer = Path(installation) / "Common7/Tools/VsDevCmd.bat"
        # A batch wrapper avoids nested cmd command-line quoting. It is only
        # used for compiler discovery; artifact dispatch never invokes a shell.
        script = directory / "discover.cmd"
        script.write_text('@echo off\ncall "' + str(developer) +
                          '" -no_logo -arch=x64 -host_arch=x64 >nul\nif errorlevel 1 exit /b 1\nset\n', encoding="utf-8")
        probe = subprocess.run([os.environ.get("ComSpec", "cmd.exe"), "/d", "/c", "discover.cmd"],
                               cwd=directory, capture_output=True, check=True, timeout=60)
        environment = {}
        for line in probe.stdout.decode("mbcs").splitlines():
            if "=" in line and not line.startswith("="):
                key, value = line.split("=", 1)
                environment[key.upper()] = value
        # Ambient CL/_CL_/LINK flags must not override the bound command.
        for key in ("CL", "_CL_", "LINK", "_LINK_"):
            environment.pop(key, None)
        compiler = shutil.which("cl.exe", path=environment.get("PATH", ""))
        linker = shutil.which("link.exe", path=environment.get("PATH", ""))
        library = next((Path(part) / "kernel32.lib" for part in environment.get("LIB", "").split(";")
                        if (Path(part) / "kernel32.lib").is_file()), None)
        require(compiler is not None and linker is not None and library is not None,
                "MSVC x64 tools unavailable", "NATIVE_TOOLCHAIN_UNAVAILABLE")
        require(environment.get("VSCMD_ARG_TGT_ARCH") == "x64", "wrong target architecture", "NATIVE_TOOLCHAIN_UNAVAILABLE")
        hashes = {name: digest(Path(path).read_bytes()) for name, path in
                  (("cl.exe", compiler), ("link.exe", linker), ("kernel32.lib", library))}
        # cl.exe delegates translation to companion DLLs; bind those as well.
        for companion in sorted(Path(compiler).parent.glob("*.dll")):
            hashes[companion.name] = digest(companion.read_bytes())
        return compiler, environment, hashes
    except (OSError, subprocess.SubprocessError, UnicodeError) as exc:
        raise NativeExecutionError("NATIVE_TOOLCHAIN_UNAVAILABLE", "developer environment discovery failed") from exc


class _Ticket:
    pass


_issued = weakref.WeakKeyDictionary()


@dataclass(frozen=True)
class NativeArtifact:
    image: Path
    receipt_json: str
    receipt_fingerprint: str
    _ticket: object = field(repr=False, compare=False)


@dataclass(frozen=True)
class NativeExecutionEvidence:
    result: CanonicalExecutionResult
    receipt_json: str
    output_fingerprint: str


def build_native(verified, plan, directory: Path, *, timeout: float = 60) -> NativeArtifact:
    # Admission precedes filesystem writes, toolchain discovery, and compilation.
    admission = admit_native_profile(verified, plan)
    timeout = _timeout(timeout)
    source = _source(admission)
    directory = Path(directory).resolve()
    require(directory.is_dir() and not any(directory.iterdir()), "empty build directory required", "NATIVE_BUILD_DIRECTORY_INVALID")
    compiler, environment, hashes = _toolchain(directory)
    (directory / "program.c").write_bytes(source)
    try:
        build = subprocess.run([compiler, *OPTIONS], cwd=directory, env=environment,
                               stdin=subprocess.DEVNULL, capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        raise NativeExecutionError("NATIVE_BUILD_TIMEOUT", "compiler timed out") from exc
    except OSError as exc:
        raise NativeExecutionError("NATIVE_BUILD_FAILED", "compiler could not start") from exc
    require(build.returncode == 0, "compiler/linker rejected build", "NATIVE_BUILD_FAILED")
    image = directory / "program.exe"
    require(image.is_file(), "compiler produced no executable", "NATIVE_BUILD_FAILED")
    record = {
        "profile": admission.profile, "air": admission.air_fingerprint,
        "routing": admission.routing_fingerprint, "entry": admission.entry,
        # The admitted sole owner's content is exactly the AIR content.
        "owner_air": admission.air_fingerprint, "states": admission.state_ids,
        "source": digest(source), "toolchain": hashes, "options": OPTIONS,
        "image": digest(image.read_bytes()),
    }
    receipt = canonical(record)
    artifact = NativeArtifact(image, receipt, digest(receipt.encode("utf-8")), _Ticket())
    _issued[artifact._ticket] = (artifact.image, artifact.receipt_json, artifact.receipt_fingerprint)
    return artifact


@contextmanager
def _locked_image(path: Path):
    # FILE_SHARE_READ alone prevents image replacement or writing until exit.
    import msvcrt
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    create = kernel.CreateFileW
    create.argtypes = [ctypes.c_wchar_p, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_void_p,
                       ctypes.c_ulong, ctypes.c_ulong, ctypes.c_void_p]
    create.restype = ctypes.c_void_p
    handle = create(str(path), 0x80000000, 1, None, 3, 0x80, None)
    if handle == ctypes.c_void_p(-1).value:
        raise NativeExecutionError("NATIVE_ARTIFACT_UNAVAILABLE", "cannot lock native image")
    try:
        descriptor = msvcrt.open_osfhandle(handle, os.O_RDONLY | os.O_BINARY)
    except BaseException:
        kernel.CloseHandle.argtypes = [ctypes.c_void_p]
        kernel.CloseHandle(handle)
        raise
    with os.fdopen(descriptor, "rb") as image:
        yield image


def _run(image: Path, timeout: float, expected: int) -> bytes:
    # File-backed capture prevents unbounded memory allocation. Only the issued,
    # digest-checked fixed-output program reaches this function in production.
    environment = {key: os.environ[key] for key in ("SystemRoot", "WINDIR") if key in os.environ}
    with tempfile.TemporaryFile(dir=image.parent) as output, tempfile.TemporaryFile(dir=image.parent) as errors:
        try:
            child = subprocess.Popen([str(image)], cwd=image.parent, env=environment,
                                     stdin=subprocess.DEVNULL, stdout=output, stderr=errors, shell=False)
            try:
                code = child.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait()
                raise NativeExecutionError("NATIVE_EXECUTION_TIMEOUT", "native child timed out")
        except OSError as exc:
            raise NativeExecutionError("NATIVE_EXECUTION_LAUNCH_FAILED", "native child could not start") from exc
        require(code == 0, "native child failed", "NATIVE_EXECUTION_FAILED")
        require(errors.tell() == 0 and output.tell() == expected,
                "native observable does not match profile", "NATIVE_RESULT_MALFORMED")
        output.seek(0)
        return output.read(expected)


def _decode(raw: bytes, state_ids, fingerprint: str) -> CanonicalExecutionResult:
    require(type(raw) is bytes and len(raw) == 8 * len(state_ids), "wrong native output size", "NATIVE_RESULT_MALFORMED")
    result = CanonicalExecutionResult(fingerprint, "SUCCESS", CanonicalExecutionPayload(tuple(
        CanonicalExecutionValue(name, "I64", str(int.from_bytes(raw[index*8:index*8+8], "little", signed=True)))
        for index, name in enumerate(state_ids))))
    result.validate()
    return result


def dispatch_native(artifact: NativeArtifact, verified, plan, *, timeout: float = 10) -> NativeExecutionEvidence:
    admission = admit_native_profile(verified, plan)
    timeout = _timeout(timeout)
    require(type(artifact) is NativeArtifact, "backend-issued artifact required", "NATIVE_ARTIFACT_INVALID")
    require(type(artifact._ticket) is _Ticket, "invalid issuance ticket", "NATIVE_ARTIFACT_INVALID")
    require(_issued.get(artifact._ticket) == (artifact.image, artifact.receipt_json, artifact.receipt_fingerprint),
            "unissued or changed artifact receipt", "NATIVE_ARTIFACT_INVALID")
    record = json.loads(artifact.receipt_json)
    require(record["air"] == admission.air_fingerprint and record["routing"] == admission.routing_fingerprint
            and record["source"] == digest(_source(admission)), "artifact/input mismatch", "NATIVE_PROVENANCE_MISMATCH")
    with _locked_image(artifact.image) as image:
        hasher = sha256()
        for block in iter(lambda: image.read(65536), b""):
            hasher.update(block)
        require(hasher.hexdigest().upper() == record["image"], "native image digest mismatch", "NATIVE_ARTIFACT_SUBSTITUTED")
        raw = _run(artifact.image, timeout, 8 * len(admission.state_ids))
    result = _decode(raw, admission.state_ids, artifact.receipt_fingerprint)
    return NativeExecutionEvidence(result, artifact.receipt_json, digest(raw))


def execute_native(verified, plan, build_root: Path, *, timeout: float = 10) -> NativeExecutionEvidence:
    admit_native_profile(verified, plan)
    _timeout(timeout)
    with tempfile.TemporaryDirectory(prefix="apexforge-native-", dir=build_root) as directory:
        artifact = build_native(verified, plan, Path(directory))
        return dispatch_native(artifact, verified, plan, timeout=timeout)
