"""P14.7 explicit-root, immutable content store; cache presence never means trust."""
from dataclasses import dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
import stat
import tempfile

from tooling.package_manifest import PackageManifest, PackageContentIdentity, parse_manifest, PackageManifestError
from tooling.package_solver import ResolvedPackage, PackageUniverse
from tooling.package_lock import PackageLock, RestorePlan, plan_restore
from tooling.package_trust import ContentMember, verify_integrity

SCHEMA = "apexforge.package-cache-record/v1"
MAX_RECORD_BYTES = 16 * 1024 * 1024


class PackageCacheError(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def _require(ok, code):
    if not ok:
        raise PackageCacheError(code)


def _json(record):
    return json.dumps(record, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False)


def _regular(info, directory=False):
    return not (getattr(info, "st_file_attributes", 0) & 0x400) and (
        stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode))


@dataclass(frozen=True)
class CacheEntry:
    manifest: PackageManifest
    members: tuple[ContentMember, ...]

    def __post_init__(self):
        _require(type(self.manifest) is PackageManifest, "CACHE_RECORD_INVALID")
        _require(verify_integrity(self.manifest, self.members).valid, "CACHE_INSERT_INTEGRITY_FAILED")
        object.__setattr__(self, "manifest", ResolvedPackage(self.manifest).manifest)
        object.__setattr__(self, "members", tuple(sorted(self.members, key=lambda m: m.path.value)))

    @property
    def identity(self):
        return self.manifest.content_identity()

    def canonical_record(self):
        return {"schema": SCHEMA, "content_identity": self.identity.record(),
            "manifest": self.manifest.canonical_record()}

    def canonical_json(self):
        return _json(self.canonical_record())

    def fingerprint(self):
        return sha256((SCHEMA + "\0" + self.canonical_json()).encode("utf-8")).hexdigest().upper()


@dataclass(frozen=True)
class CachedRestoreView:
    lock: PackageLock
    entries: tuple[CacheEntry, ...]
    plan: RestorePlan

    def __post_init__(self):
        _require(type(self.lock) is PackageLock and type(self.entries) is tuple
            and all(type(e) is CacheEntry for e in self.entries) and type(self.plan) is RestorePlan
            and self.plan.lock == self.lock, "CACHE_RESTORE_VIEW_INVALID")
        _require(tuple(ResolvedPackage(e.manifest) for e in self.entries) == self.lock.resolution.nodes,
                 "CACHE_RESTORE_VIEW_INVALID")

    def canonical_json(self):
        return self.plan.canonical_json()


class PackageCache:
    """Caller-owned existing absolute root. No discovery, eviction, installation or TOFU.

    Atomic hard-link publication is put-if-absent: it never replaces an existing
    authoritative key. No hostile concurrent reparse/ancestor-swap claim is made.
    """
    def __init__(self, root):
        _require(isinstance(root, (str, Path)), "CACHE_ROOT_INVALID")
        self._root = Path(root)
        _require(self._root.is_absolute() and ".." not in self._root.parts, "CACHE_ROOT_INVALID")
        try:
            _require(_regular(self._root.lstat(), True), "CACHE_PATH_NOT_REGULAR")
        except FileNotFoundError as exc:
            raise PackageCacheError("CACHE_ROOT_MISSING") from exc

    def _path(self, parts, create=False):
        # Only fixed names, validated fingerprints and controlled temp filenames enter here.
        _require(_regular(self._root.lstat(), True), "CACHE_PATH_NOT_REGULAR")
        current = self._root
        for part in parts[:-1]:
            current = current / part
            if create:
                try:
                    current.mkdir()
                except FileExistsError:
                    pass
            _require(_regular(current.lstat(), True), "CACHE_PATH_NOT_REGULAR")
        return current / parts[-1]

    @staticmethod
    def package_key(identity):
        _require(type(identity) is PackageContentIdentity, "CACHE_KEY_INVALID")
        # Revalidate typed keys, never accept arbitrary path strings.
        PackageContentIdentity(identity.fingerprint, identity.domain)
        return ("packages", identity.fingerprint[:2], identity.fingerprint, "record.json")

    @staticmethod
    def blob_key(digest):
        PackageContentIdentity(digest)  # Same strict uppercase SHA-256 syntax; meaning is raw bytes here.
        return ("blobs", "sha256", digest[:2], digest)

    def _read(self, path, missing):
        try:
            _require(_regular(path.lstat()), "CACHE_PATH_NOT_REGULAR")
            return path.read_bytes()
        except FileNotFoundError as exc:
            raise PackageCacheError(missing) from exc

    def _publish(self, parts, data, mismatch):
        path = self._path(parts, True)
        if path.exists() or path.is_symlink():
            _require(self._read(path, "CACHE_RECORD_MISSING") == data, mismatch)
            return
        fd, temporary = tempfile.mkstemp(prefix=".cache-", suffix=".tmp", dir=path.parent)
        temporary = Path(temporary)
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            try:
                os.link(temporary, path)
            except FileExistsError:
                _require(self._read(path, "CACHE_RECORD_MISSING") == data, mismatch)
        finally:
            temporary.unlink(missing_ok=True)

    def put(self, manifest, members):
        entry = CacheEntry(manifest, members)  # Entire integrity gate before any cache writes.
        try:
            for member in entry.members:
                digest = sha256(member.data).hexdigest().upper()
                self._publish(self.blob_key(digest), member.data, "CACHE_BLOB_DIGEST_MISMATCH")
            # Package record publishes last, only after every blob is present and valid.
            self._publish(self.package_key(entry.identity), entry.canonical_json().encode("utf-8"),
                          "CACHE_RECORD_EXISTING_MISMATCH")
            return self.get(entry.identity)
        except OSError as exc:
            raise PackageCacheError("CACHE_IO_ERROR") from exc

    def get(self, identity):
        parts = self.package_key(identity)
        try:
            try:
                path = self._path(parts)
            except FileNotFoundError as exc:
                raise PackageCacheError("CACHE_MISS") from exc
            raw = self._read(path, "CACHE_RECORD_MISSING")
            _require(len(raw) <= MAX_RECORD_BYTES, "CACHE_RECORD_INVALID")
            def pairs(items):
                result = {}
                for key, value in items:
                    _require(key not in result, "CACHE_RECORD_INVALID")
                    result[key] = value
                return result
            try:
                record = json.loads(raw.decode("utf-8"), object_pairs_hook=pairs)
                _require(type(record) is dict and set(record) == {"schema", "content_identity", "manifest"}
                    and record["schema"] == SCHEMA, "CACHE_RECORD_INVALID")
                manifest = parse_manifest(_json(record["manifest"]))
                _require(manifest.content_identity() == identity and record["content_identity"] == identity.record(),
                         "CACHE_PACKAGE_IDENTITY_MISMATCH")
                _require(record["manifest"] == manifest.canonical_record(), "CACHE_RECORD_INVALID")
            except (UnicodeError, json.JSONDecodeError, PackageManifestError, RecursionError, ValueError) as exc:
                if isinstance(exc, PackageCacheError):
                    raise
                raise PackageCacheError("CACHE_RECORD_INVALID") from exc
            members = []
            for descriptor in manifest.content:
                try:
                    blob = self._path(self.blob_key(descriptor.digest))
                except FileNotFoundError as exc:
                    raise PackageCacheError("CACHE_BLOB_MISSING") from exc
                data = self._read(blob, "CACHE_BLOB_MISSING")
                _require(sha256(data).hexdigest().upper() == descriptor.digest, "CACHE_BLOB_DIGEST_MISMATCH")
                members.append(ContentMember(descriptor.path, data))
            entry = CacheEntry(manifest, tuple(members))
            _require(raw == entry.canonical_json().encode("utf-8"), "CACHE_RECORD_INVALID")
            return entry
        except OSError as exc:
            raise PackageCacheError("CACHE_IO_ERROR") from exc

    def restore_view(self, lock):
        _require(type(lock) is PackageLock, "CACHE_LOCK_INVALID")
        entries = tuple(self.get(n.content_identity) for n in lock.resolution.nodes)
        for expected, entry in zip(lock.resolution.nodes, entries):
            _require(entry.manifest.coordinate == expected.coordinate, "CACHE_COORDINATE_MISMATCH")
            _require(ResolvedPackage(entry.manifest) == expected, "CACHE_PACKAGE_IDENTITY_MISMATCH")
        plan = plan_restore(lock, PackageUniverse(tuple(e.manifest for e in entries)))
        return CachedRestoreView(lock, entries, plan)
