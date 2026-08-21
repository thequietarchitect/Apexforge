"""Functional dependency-aware in-memory cache operations for P11.12F.

This module introduces the first operational collection over the frozen
P11.12 cache entry model. The collection is immutable and functional: every
store or invalidation returns a new CacheCollection rather than mutating a
global cache.

Correctness remains content-addressed. CacheEntry.cache_key is derived from the
complete CacheIdentity, including ordered dependency identities/fingerprints.
Physical invalidation is secondary cleanup.

This module owns cache operations and immutable cache observations only. It does
not own compiler semantics, project building, runtime execution, persistence,
TAP adaptation, or background cache management.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

from incremental_cache.model import (
    CacheDependency,
    CacheEntry,
    CacheIdentity,
    cache_identity_key,
)
from language.modules import ProjectDocumentGraph


_CACHE_OBSERVATION_OUTCOMES = {
    "store": ("stored", "existing"),
    "lookup": ("hit", "miss", "stale"),
    "invalidate": ("invalidated", "noop"),
}


def _require_cache_key(value: str, owner: str) -> str:
    if type(value) is not str:
        raise TypeError("{} must be exact str".format(owner))
    if len(value) != 64 or any(
        character not in "0123456789abcdef"
        for character in value
    ):
        raise ValueError("{} must be lowercase SHA-256 text".format(owner))
    return value


def _require_key_tuple(
    values: Tuple[str, ...],
    owner: str,
) -> Tuple[str, ...]:
    if type(values) is not tuple:
        raise TypeError("{} must be exact tuple".format(owner))
    seen = set()
    normalized = []
    for value in values:
        selected = _require_cache_key(value, owner)
        if selected in seen:
            raise ValueError("{} must not contain duplicates".format(owner))
        seen.add(selected)
        normalized.append(selected)
    return tuple(normalized)


def _logical_slot(identity: CacheIdentity) -> tuple[int, str, str, str, str]:
    return (
        identity.schema_version,
        identity.layer_id,
        identity.artifact_kind,
        identity.owner,
        identity.subject,
    )


@dataclass(frozen=True)
class CacheObservation:
    """Immutable evidence for one cache operation.

    This is cache-owned evidence only. It carries no semantic ruling and is not
    itself a TAP ledger entry.
    """

    operation: str
    outcome: str
    requested_cache_keys: Tuple[str, ...] = ()
    affected_cache_keys: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if type(self.operation) is not str:
            raise TypeError("CacheObservation.operation must be exact str")
        if self.operation not in _CACHE_OBSERVATION_OUTCOMES:
            raise ValueError("CacheObservation.operation is not canonical")
        if type(self.outcome) is not str:
            raise TypeError("CacheObservation.outcome must be exact str")
        if self.outcome not in _CACHE_OBSERVATION_OUTCOMES[self.operation]:
            raise ValueError(
                "CacheObservation.outcome is invalid for operation"
            )

        requested = _require_key_tuple(
            self.requested_cache_keys,
            "CacheObservation.requested_cache_keys",
        )
        affected = _require_key_tuple(
            self.affected_cache_keys,
            "CacheObservation.affected_cache_keys",
        )

        if self.operation in ("store", "lookup") and len(requested) != 1:
            raise ValueError(
                "store/lookup observations require one requested cache key"
            )
        if self.operation == "invalidate" and not requested:
            raise ValueError(
                "invalidate observations require at least one requested key"
            )
        if self.outcome == "hit" and affected != requested:
            raise ValueError(
                "cache hit observation must affect its requested key"
            )
        if self.outcome == "stored" and affected != requested:
            raise ValueError(
                "cache stored observation must affect its requested key"
            )
        if self.outcome == "existing" and affected != requested:
            raise ValueError(
                "cache existing observation must affect its requested key"
            )
        if self.outcome in ("miss", "noop") and affected:
            raise ValueError(
                "cache miss/noop observations cannot affect cache keys"
            )
        if self.outcome == "stale" and len(affected) != 1:
            raise ValueError(
                "cache stale observation must identify one resident key"
            )

        object.__setattr__(self, "requested_cache_keys", requested)
        object.__setattr__(self, "affected_cache_keys", affected)


@dataclass(frozen=True)
class CacheCollection:
    """One immutable dependency-first collection of CacheEntry values."""

    entries: Tuple[CacheEntry, ...] = ()

    def __post_init__(self) -> None:
        if type(self.entries) is not tuple:
            raise TypeError("CacheCollection.entries must be exact tuple")

        entries = tuple(self.entries)
        by_key = {}
        slots = {}

        for entry in entries:
            if type(entry) is not CacheEntry:
                raise TypeError(
                    "CacheCollection.entries must contain exact CacheEntry"
                )

            key = entry.cache_key
            if key in by_key:
                raise ValueError(
                    "CacheCollection.entries must have unique cache keys"
                )

            slot = _logical_slot(entry.identity)
            if slot in slots:
                raise ValueError(
                    "CacheCollection permits one resident version per logical "
                    "cache slot; invalidate the prior version before replacement"
                )

            for dependency in entry.identity.dependencies:
                resident = by_key.get(dependency.cache_key)
                if resident is None:
                    raise ValueError(
                        "CacheCollection dependencies must precede dependents"
                    )
                if resident.artifact_fingerprint != dependency.fingerprint:
                    raise ValueError(
                        "CacheCollection dependency fingerprint mismatch"
                    )

            by_key[key] = entry
            slots[slot] = key

        object.__setattr__(self, "entries", entries)

    def keys(self) -> Tuple[str, ...]:
        return tuple(entry.cache_key for entry in self.entries)

    def entry_for_key(self, cache_key: str) -> Optional[CacheEntry]:
        selected = _require_cache_key(
            cache_key,
            "CacheCollection.entry_for_key cache_key",
        )
        for entry in self.entries:
            if entry.cache_key == selected:
                return entry
        return None

    def _dependencies_valid(self, entry: CacheEntry) -> bool:
        by_key = {
            resident.cache_key: resident
            for resident in self.entries
        }
        for dependency in entry.identity.dependencies:
            resident = by_key.get(dependency.cache_key)
            if resident is None:
                return False
            if resident.artifact_fingerprint != dependency.fingerprint:
                return False
        return True

    def lookup(
        self,
        identity: CacheIdentity,
    ) -> tuple[Optional[CacheEntry], CacheObservation]:
        """Lookup one exact content-addressed identity.

        A different resident version of the same logical slot is reported as
        stale but is never returned for reuse.
        """

        if type(identity) is not CacheIdentity:
            raise TypeError("CacheCollection.lookup identity must be exact CacheIdentity")

        requested_key = cache_identity_key(identity)
        resident = self.entry_for_key(requested_key)

        if resident is not None:
            if self._dependencies_valid(resident):
                return (
                    resident,
                    CacheObservation(
                        operation="lookup",
                        outcome="hit",
                        requested_cache_keys=(requested_key,),
                        affected_cache_keys=(requested_key,),
                    ),
                )
            return (
                None,
                CacheObservation(
                    operation="lookup",
                    outcome="stale",
                    requested_cache_keys=(requested_key,),
                    affected_cache_keys=(requested_key,),
                ),
            )

        slot = _logical_slot(identity)
        stale = tuple(
            entry
            for entry in self.entries
            if _logical_slot(entry.identity) == slot
        )
        if stale:
            if len(stale) != 1:
                raise AssertionError(
                    "CacheCollection logical-slot uniqueness escaped validation"
                )
            return (
                None,
                CacheObservation(
                    operation="lookup",
                    outcome="stale",
                    requested_cache_keys=(requested_key,),
                    affected_cache_keys=(stale[0].cache_key,),
                ),
            )

        return (
            None,
            CacheObservation(
                operation="lookup",
                outcome="miss",
                requested_cache_keys=(requested_key,),
                affected_cache_keys=(),
            ),
        )

    def store(
        self,
        entry: CacheEntry,
    ) -> tuple["CacheCollection", CacheObservation]:
        """Store one entry after validating all declared dependencies."""

        if type(entry) is not CacheEntry:
            raise TypeError("CacheCollection.store entry must be exact CacheEntry")

        key = entry.cache_key
        existing = self.entry_for_key(key)
        if existing is not None:
            if (
                existing.identity != entry.identity
                or existing.artifact_fingerprint
                != entry.artifact_fingerprint
                or type(existing.value) is not type(entry.value)
                or existing.value != entry.value
            ):
                raise ValueError(
                    "cache key collision contains non-identical entry"
                )
            return (
                self,
                CacheObservation(
                    operation="store",
                    outcome="existing",
                    requested_cache_keys=(key,),
                    affected_cache_keys=(key,),
                ),
            )

        slot = _logical_slot(entry.identity)
        if any(
            _logical_slot(resident.identity) == slot
            for resident in self.entries
        ):
            raise ValueError(
                "logical cache slot already has a resident version; "
                "invalidate it before storing a replacement"
            )

        by_key = {
            resident.cache_key: resident
            for resident in self.entries
        }
        for dependency in entry.identity.dependencies:
            resident = by_key.get(dependency.cache_key)
            if resident is None:
                raise ValueError(
                    "cannot store entry with missing cache dependency"
                )
            if resident.artifact_fingerprint != dependency.fingerprint:
                raise ValueError(
                    "cannot store entry with mismatched dependency fingerprint"
                )

        updated = CacheCollection(self.entries + (entry,))
        return (
            updated,
            CacheObservation(
                operation="store",
                outcome="stored",
                requested_cache_keys=(key,),
                affected_cache_keys=(key,),
            ),
        )

    def invalidate(
        self,
        seed_cache_keys: Tuple[str, ...],
    ) -> tuple["CacheCollection", CacheObservation]:
        """Remove seed entries and all transitive cache dependents."""

        requested = _require_key_tuple(
            seed_cache_keys,
            "CacheCollection.invalidate seed_cache_keys",
        )
        if not requested:
            raise ValueError(
                "CacheCollection.invalidate requires at least one seed key"
            )

        resident_keys = set(self.keys())
        affected = {
            key
            for key in requested
            if key in resident_keys
        }

        changed = True
        while changed:
            changed = False
            for entry in self.entries:
                key = entry.cache_key
                if key in affected:
                    continue
                if any(
                    dependency.cache_key in affected
                    for dependency in entry.identity.dependencies
                ):
                    affected.add(key)
                    changed = True

        removed = tuple(
            entry.cache_key
            for entry in self.entries
            if entry.cache_key in affected
        )

        if not removed:
            return (
                self,
                CacheObservation(
                    operation="invalidate",
                    outcome="noop",
                    requested_cache_keys=requested,
                    affected_cache_keys=(),
                ),
            )

        retained = tuple(
            entry
            for entry in self.entries
            if entry.cache_key not in affected
        )
        updated = CacheCollection(retained)

        return (
            updated,
            CacheObservation(
                operation="invalidate",
                outcome="invalidated",
                requested_cache_keys=requested,
                affected_cache_keys=removed,
            ),
        )


def cache_keys_for_subjects(
    collection: CacheCollection,
    subjects: Tuple[str, ...],
) -> Tuple[str, ...]:
    """Return resident keys whose exact CacheIdentity.subject is selected."""

    if type(collection) is not CacheCollection:
        raise TypeError("collection must be exact CacheCollection")
    if type(subjects) is not tuple:
        raise TypeError("subjects must be exact tuple")

    seen = set()
    selected = []
    for subject in subjects:
        if type(subject) is not str:
            raise TypeError("subjects must contain exact str values")
        if not subject or subject.strip() != subject:
            raise ValueError("subjects must contain non-empty trimmed text")
        if subject in seen:
            raise ValueError("subjects must not contain duplicates")
        seen.add(subject)
        selected.append(subject)

    selected_set = set(selected)
    return tuple(
        entry.cache_key
        for entry in collection.entries
        if entry.identity.subject in selected_set
    )


def affected_project_sources(
    graph: ProjectDocumentGraph,
    changed_sources: Tuple[str, ...],
) -> Tuple[str, ...]:
    """Return changed sources plus transitive importers in dependency order."""

    if type(graph) is not ProjectDocumentGraph:
        raise TypeError("graph must be exact ProjectDocumentGraph")
    if type(changed_sources) is not tuple:
        raise TypeError("changed_sources must be exact tuple")
    if not changed_sources:
        raise ValueError("changed_sources must not be empty")

    known = set(graph.dependency_order)
    changed = set()

    for source_name in changed_sources:
        if type(source_name) is not str:
            raise TypeError("changed_sources must contain exact str values")
        if source_name not in known:
            raise ValueError(
                "changed source is not present in ProjectDocumentGraph"
            )
        if source_name in changed:
            raise ValueError("changed_sources must not contain duplicates")
        changed.add(source_name)

    reverse = {
        source_name: []
        for source_name in graph.dependency_order
    }
    for edge in graph.resolved_import_edges:
        reverse[edge.target_source_name].append(
            edge.importer_source_name
        )

    affected = set(changed)
    queue = list(
        source_name
        for source_name in graph.dependency_order
        if source_name in changed
    )
    index = 0
    while index < len(queue):
        source_name = queue[index]
        index += 1
        for importer in reverse[source_name]:
            if importer in affected:
                continue
            affected.add(importer)
            queue.append(importer)

    return tuple(
        source_name
        for source_name in graph.dependency_order
        if source_name in affected
    )


__all__ = (
    "CacheObservation",
    "CacheCollection",
    "cache_keys_for_subjects",
    "affected_project_sources",
)