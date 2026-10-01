"""Opt-in resource observations. No imports of semantic or execution owners.

MSC classes label evidence only. Callers own observation scopes and resources.
Filesystem inventories reject links/reparse points; they are not atomic against
concurrent hostile namespace changes. Quiescent trusted test roots are required.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import stat
from time import perf_counter_ns
import tracemalloc


class ResourceClass(Enum):
    IRR = "IRR"
    CER = "CER"
    DHF = "DHF"
    SHR = "SHR"


class EvidenceStatus(Enum):
    KNOWN = "known"
    UNKNOWN = "unknown"
    UNAVAILABLE = "unavailable"


class Availability(Enum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"


class PressureDimension(Enum):
    Wp = "Wp"
    H = "H"
    At = "At"
    Tb = "Tb"
    Cb = "Cb"
    Pc = "Pc"


def _text(value):
    if type(value) is not str or not value.strip() or value != value.strip():
        raise ValueError("nonempty trimmed evidence text required")


def _label(value):
    if type(value) is not str or re.fullmatch(r"[a-z][a-z0-9_.-]*", value) is None:
        raise ValueError("portable lowercase metric/scope label required")


@dataclass(frozen=True)
class OwnershipEvidence:
    status: EvidenceStatus
    value: str | None = None
    reason: str | None = None

    def __post_init__(self):
        if type(self.status) is not EvidenceStatus:
            raise ValueError("typed evidence status required")
        if self.status is EvidenceStatus.KNOWN:
            _text(self.value)
            if self.reason is not None:
                raise ValueError("known evidence has no missing-evidence reason")
        else:
            if self.value is not None:
                raise ValueError("unresolved evidence must not invent a value")
            _text(self.reason)


@dataclass(frozen=True)
class ResourceOwnership:
    scope: str
    resource_class: ResourceClass
    owner: OwnershipEvidence
    purpose: OwnershipEvidence
    trigger: OwnershipEvidence
    intended_lifetime: OwnershipEvidence
    cleanup_boundary: OwnershipEvidence

    def __post_init__(self):
        _label(self.scope)
        if type(self.resource_class) is not ResourceClass:
            raise ValueError("analytical resource class required")
        if any(type(v) is not OwnershipEvidence for v in
               (self.owner, self.purpose, self.trigger, self.intended_lifetime, self.cleanup_boundary)):
            raise ValueError("explicit ownership evidence required")

    def canonical_record(self):
        return (self.scope, self.resource_class.value, tuple(
            (v.status.value, v.value, v.reason) for v in
            (self.owner, self.purpose, self.trigger, self.intended_lifetime, self.cleanup_boundary)))


@dataclass(frozen=True)
class Measurement:
    ownership: ResourceOwnership
    dimension: PressureDimension | None
    metric: str
    value: int | None
    unit: str
    source: str
    availability: Availability = Availability.AVAILABLE
    reason: str | None = None
    volatile: bool = False

    def __post_init__(self):
        if type(self.ownership) is not ResourceOwnership:
            raise ValueError("explicit resource ownership required")
        if self.dimension is not None and type(self.dimension) is not PressureDimension:
            raise ValueError("typed pressure coordinate required")
        _label(self.metric)
        if self.unit not in ("bytes", "count", "ns") or type(self.unit) is not str:
            raise ValueError("supported unit required")
        _text(self.source)
        if type(self.volatile) is not bool or type(self.availability) is not Availability:
            raise ValueError("explicit volatility/availability required")
        if self.availability is Availability.AVAILABLE:
            if type(self.value) is not int or self.value < 0 or self.reason is not None:
                raise ValueError("nonnegative exact integer measurement required")
        else:
            if self.value is not None:
                raise ValueError("unavailable measurement has no numeric value")
            _text(self.reason)

    def key(self):
        # All attribution fields must agree for arithmetic comparison.
        return _json((self.ownership.canonical_record(),
                      None if self.dimension is None else self.dimension.value,
                      self.metric, self.unit, self.source, self.volatile))

    def canonical_record(self):
        return (self.key(), self.availability.value, self.value, self.reason)


def _json(value):
    return json.dumps(value, ensure_ascii=True, separators=(",", ":"), allow_nan=False)


def measured(ownership, dimension, metric, value, unit, source, *, volatile=False):
    return Measurement(ownership, dimension, metric, value, unit, source, volatile=volatile)


def unavailable(ownership, dimension, metric, unit, source, reason, *, volatile=False):
    return Measurement(ownership, dimension, metric, None, unit, source,
                       Availability.UNAVAILABLE, reason, volatile)


@dataclass(frozen=True)
class ResourceSnapshot:
    observations: tuple[Measurement, ...]

    def __post_init__(self):
        if type(self.observations) is not tuple or any(type(v) is not Measurement for v in self.observations):
            raise ValueError("immutable measurement tuple required")
        ordered = tuple(sorted(self.observations, key=lambda v: v.key()))
        if len({v.key() for v in ordered}) != len(ordered):
            raise ValueError("duplicate observation key")
        object.__setattr__(self, "observations", ordered)

    def canonical_form(self):
        # This identifies deterministic observations, NOT live resource state.
        return _json(("apexforge.resource-observation/v1",
                      tuple(v.canonical_record() for v in self.observations if not v.volatile)))

    def fingerprint(self):
        return sha256(self.canonical_form().encode("utf-8")).hexdigest().upper()


class DeltaDirection(Enum):
    INCREASE = "increase"
    DECREASE = "decrease"
    UNCHANGED = "unchanged"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True)
class MeasurementDelta:
    key: str
    before: Measurement | None
    after: Measurement | None
    difference: int | None
    direction: DeltaDirection

    def __post_init__(self):
        if self.before is None and self.after is None:
            raise ValueError("at least one observation required")
        for value in (self.before, self.after):
            if value is not None and (type(value) is not Measurement or value.key() != self.key):
                raise ValueError("delta attribution mismatch")
        available = (self.before is not None and self.after is not None and
                     self.before.availability is self.after.availability is Availability.AVAILABLE)
        difference = self.after.value - self.before.value if available else None
        direction = (DeltaDirection.UNAVAILABLE if difference is None else
                     DeltaDirection.INCREASE if difference > 0 else
                     DeltaDirection.DECREASE if difference < 0 else DeltaDirection.UNCHANGED)
        if self.difference != difference or type(self.direction) is not DeltaDirection or self.direction is not direction:
            raise ValueError("incorrect structural delta")
        if difference is not None and type(self.difference) is not int:
            raise ValueError("exact arithmetic delta required")


def compare_snapshots(before, after):
    if type(before) is not ResourceSnapshot or type(after) is not ResourceSnapshot:
        raise ValueError("resource snapshots required")
    left = {v.key(): v for v in before.observations}
    right = {v.key(): v for v in after.observations}
    result = []
    for key in sorted(left.keys() | right.keys()):
        a, b = left.get(key), right.get(key)
        difference = (b.value - a.value if a is not None and b is not None and
                      a.availability is b.availability is Availability.AVAILABLE else None)
        direction = (DeltaDirection.UNAVAILABLE if difference is None else
                     DeltaDirection.INCREASE if difference > 0 else
                     DeltaDirection.DECREASE if difference < 0 else DeltaDirection.UNCHANGED)
        result.append(MeasurementDelta(key, a, b, difference, direction))
    return tuple(result)


@dataclass(frozen=True)
class LifecycleBoundary:
    name: str
    ownership: ResourceOwnership
    before: ResourceSnapshot
    after: ResourceSnapshot

    def __post_init__(self):
        _label(self.name)
        if type(self.ownership) is not ResourceOwnership or any(
                type(v) is not ResourceSnapshot for v in (self.before, self.after)):
            raise ValueError("explicit lifecycle evidence required")
        if self.ownership.cleanup_boundary.status is not EvidenceStatus.KNOWN:
            raise ValueError("boundary must be supported by known ownership evidence")
        if any(v.ownership != self.ownership for s in (self.before, self.after) for v in s.observations):
            raise ValueError("boundary observation ownership mismatch")

    def delta(self):
        return compare_snapshots(self.before, self.after)


def elapsed(ownership, started_ns):
    if type(started_ns) is not int or started_ns < 0:
        raise ValueError("monotonic starting reading required")
    duration = perf_counter_ns() - started_ns
    if duration < 0:
        raise ValueError("starting reading follows ending reading")
    return measured(ownership, None, "elapsed", duration, "ns", "time.perf_counter_ns", volatile=True)


@dataclass(frozen=True)
class ArtifactFile:
    relative_path: str
    bytes: int

    def __post_init__(self):
        if (type(self.relative_path) is not str or not self.relative_path or
                "\\" in self.relative_path or Path(self.relative_path).is_absolute() or
                any(p in ("..", ".") for p in self.relative_path.split("/"))):
            raise ValueError("contained relative file path required")
        if type(self.bytes) is not int or self.bytes < 0:
            raise ValueError("nonnegative file size required")


@dataclass(frozen=True)
class ArtifactInventory:
    files: tuple[ArtifactFile, ...]
    snapshot: ResourceSnapshot

    def __post_init__(self):
        if type(self.files) is not tuple or any(type(v) is not ArtifactFile for v in self.files):
            raise ValueError("immutable file rows required")
        if type(self.snapshot) is not ResourceSnapshot:
            raise ValueError("inventory snapshot required")
        ordered = tuple(sorted(self.files, key=lambda v: v.relative_path))
        if len({v.relative_path for v in ordered}) != len(ordered):
            raise ValueError("duplicate file path")
        object.__setattr__(self, "files", ordered)

    def canonical_form(self):
        return _json(("apexforge.resource-artifacts/v1", self.snapshot.canonical_form(),
                      tuple((v.relative_path, v.bytes) for v in self.files)))

    def fingerprint(self):
        return sha256(self.canonical_form().encode("utf-8")).hexdigest().upper()


class ObservationPathError(ValueError):
    """Unauthorized or link-containing namespace; no footprint is admitted."""


def _is_link(info):
    return stat.S_ISLNK(info.st_mode) or bool(getattr(info, "st_file_attributes", 0) & 0x400)


def _contained_path(root, authorized_root):
    root, authorized = Path(root), Path(authorized_root)
    if not root.is_absolute() or not authorized.is_absolute() or ".." in root.parts or ".." in authorized.parts:
        raise ObservationPathError("absolute roots without parent traversal required")
    try:
        relative = root.relative_to(authorized)
    except ValueError as exc:
        raise ObservationPathError("observation root outside authorized root") from exc
    # The supplied authority is a caller declaration, not inferred permission.
    # Check each ancestor before traversing it, rather than resolve a link and
    # inspect its target. This also rejects an authority nested below a junction.
    cursor = Path(authorized.anchor)
    for part in authorized.parts[1:]:
        cursor = cursor / part
        if _is_link(cursor.lstat()):
            raise ObservationPathError("link/reparse authority root rejected")
    cursor = authorized
    for part in relative.parts:
        cursor = cursor / part
        try:
            info = cursor.lstat()
        except FileNotFoundError:
            return root
        if _is_link(info):
            raise ObservationPathError("link/reparse traversal rejected")
    return root


def inventory_artifacts(ownership, root, *, authorized_root, dimension=PressureDimension.At):
    """Stat quiescent selected roots, never read/execute contents or follow links.

    Missing contained roots are observed absence (zero files), unlike read errors.
    Relative file rows supplement counts; supply logical scope labels, not paths.
    """
    source = "filesystem.lstat"
    metrics = (("files", "count"), ("total_bytes", "bytes"), ("generated_c_bytes", "bytes"),
               ("native_image_bytes", "bytes"), ("root_present", "count"))
    rows = []
    try:
        root = _contained_path(root, authorized_root)
        try:
            initial = root.lstat()
        except FileNotFoundError:
            initial = None
        pending = [(root, initial)] if initial is not None else []
        while pending:
            path, info = pending.pop()
            if _is_link(info):
                raise ObservationPathError("link/reparse inventory entry rejected")
            if stat.S_ISDIR(info.st_mode):
                with os.scandir(path) as children:
                    pending.extend((Path(child.path), child.stat(follow_symlinks=False)) for child in children)
            elif stat.S_ISREG(info.st_mode):
                relative = path.relative_to(root).as_posix() if path != root else path.name
                rows.append(ArtifactFile(relative, info.st_size))
            else:
                raise OSError("unsupported filesystem entry")
        values = (len(rows), sum(v.bytes for v in rows),
                  sum(v.bytes for v in rows if Path(v.relative_path).suffix.lower() == ".c"),
                  sum(v.bytes for v in rows if Path(v.relative_path).suffix.lower() in (".exe", ".dll")),
                  int(initial is not None))
        snapshot = ResourceSnapshot(tuple(measured(ownership, dimension, name, value, unit, source)
                                           for (name, unit), value in zip(metrics, values)))
        return ArtifactInventory(tuple(rows), snapshot)
    except OSError:
        # Discard partial rows; no valid zero/partial footprint on I/O failure.
        return ArtifactInventory((), ResourceSnapshot(tuple(
            unavailable(ownership, dimension, name, unit, source, "filesystem inspection unavailable")
            for name, unit in metrics)))


def observe_count(ownership, dimension, metric, items):
    """Count supplied immutable carrier members, without interpreting them."""
    if type(items) is not tuple:
        raise ValueError("existing immutable member tuple required")
    return measured(ownership, dimension, metric, len(items), "count", "supplied.tuple.length")


def observe_bytes(ownership, dimension, metric, content):
    """Size supplied bytes/existing textual representation; never serialize a carrier."""
    if type(content) is str:
        content = content.encode("utf-8")
    if type(content) is not bytes:
        raise ValueError("supplied bytes or existing representation required")
    return measured(ownership, dimension, metric, len(content), "bytes", "supplied.utf8-or-bytes.length")


def observe_python_memory(ownership, *, enabled=False):
    if type(enabled) is not bool:
        raise ValueError("explicit opt-in required")
    source = "tracemalloc.get_traced_memory"
    names = ("python_traced_current", "python_traced_peak")
    if not enabled or not tracemalloc.is_tracing():
        reason = "disabled" if not enabled else "caller-owned tracemalloc session inactive"
        return tuple(unavailable(ownership, PressureDimension.Wp, name, "bytes", source, reason, volatile=True)
                     for name in names)
    try:
        values = tracemalloc.get_traced_memory()
        return tuple(measured(ownership, PressureDimension.Wp, name, value, "bytes", source, volatile=True)
                     for name, value in zip(names, values))
    except RuntimeError:
        return tuple(unavailable(ownership, PressureDimension.Wp, name, "bytes", source,
                                 "Python allocation reading unavailable", volatile=True) for name in names)


def _windows_current_values():
    import ctypes
    from ctypes import wintypes

    class Counters(ctypes.Structure):
        _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD)] + [
            (name, ctypes.c_size_t) for name in ("PeakWorkingSetSize", "WorkingSetSize",
            "QuotaPeakPagedPoolUsage", "QuotaPagedPoolUsage", "QuotaPeakNonPagedPoolUsage",
            "QuotaNonPagedPoolUsage", "PagefileUsage", "PeakPagefileUsage")]

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    psapi = ctypes.WinDLL("psapi", use_last_error=True)
    kernel.GetCurrentProcess.argtypes = []
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    process = kernel.GetCurrentProcess()  # pseudo-handle; no OpenProcess / PID parameter
    psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD]
    psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
    kernel.GetProcessHandleCount.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
    kernel.GetProcessHandleCount.restype = wintypes.BOOL
    counters = Counters()
    counters.cb = ctypes.sizeof(counters)
    result = {}
    if psapi.GetProcessMemoryInfo(process, ctypes.byref(counters), counters.cb):
        result.update(working_set=counters.WorkingSetSize, peak_working_set=counters.PeakWorkingSetSize)
    count = wintypes.DWORD()
    if kernel.GetProcessHandleCount(process, ctypes.byref(count)):
        result["handles"] = count.value
    return result


def observe_current_process(ownership):
    """Optional Windows readings of this process only; no invasive inspection."""
    source = "windows.current-process"
    specs = ((PressureDimension.Wp, "working_set", "bytes"),
             (PressureDimension.Wp, "peak_working_set", "bytes"),
             (PressureDimension.H, "handles", "count"))
    values = {}
    reason = "unsupported platform"
    if os.name == "nt":
        reason = "OS reading unavailable"
        try:
            values = _windows_current_values()
        except (OSError, AttributeError):
            pass
    return tuple(measured(ownership, dim, name, values[name], unit, source, volatile=True)
                 if name in values else unavailable(ownership, dim, name, unit, source, reason, volatile=True)
                 for dim, name, unit in specs)
