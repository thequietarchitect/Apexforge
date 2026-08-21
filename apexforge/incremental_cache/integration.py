"""P11.12G/H ProjectBuilder/tooling incremental-cache integration.

The semantic build owner remains language.project.ProjectBuilder. This module
provides an explicit, instance-local build session that injects cache-aware
compiler, linker-alignment, and validator collaborators through ProjectBuilder's
existing extension seams.

P11.12H optimizes the warm lookup path without weakening the frozen cache model:
the session maintains derived in-memory indexes over its immutable
CacheCollection and trusts artifact fingerprints only for entries it produced
itself or externally supplied entries that have been structurally verified once.

The session owns only reuse state and CacheObservation evidence. It does not
modify ProjectBuilder semantics, cache ProjectBuild as one object, persist
entries, create a global cache, execute runtime behavior, or adapt evidence into
TAP.
"""

from __future__ import annotations

import inspect
from typing import Any, Dict, Mapping, Optional, Tuple

from air.linker import AIRProgramLinker
from air.model import AIRProgram, VerifiedAIRProgram
from incremental_cache.model import (
    CACHE_SCHEMA_VERSION,
    CacheDependency,
    CacheEntry,
    CacheIdentity,
    CacheFingerprint,
    cache_fingerprint,
    cache_identity_key,
)
from incremental_cache.operational import CacheCollection, CacheObservation
from incremental_cache.resonance import (
    resonance_fingerprint,
    resonance_identity,
    reuse_or_produce_resonance,
)
from incremental_cache.stability import (
    reuse_or_produce_stability,
    stability_fingerprint,
    stability_identity,
    stability_input_fingerprint,
)
from language.compiler import CompiledSource, compile_source_with_map
from language.project import ProjectBuild, ProjectBuilder
from language.validation.runtime_validator import RuntimeValidator
from standard_library import P10_STANDARD_LIBRARY_VERSION


def _function_signature_contract(
    function_signatures: Optional[Mapping[str, Any]],
) -> object:
    if function_signatures is None:
        return None
    return tuple(
        (str(name), str(signature))
        for name, signature in sorted(
            function_signatures.items(),
            key=lambda item: str(item[0]),
        )
    )


def _identity_slot(
    identity: CacheIdentity,
) -> tuple[int, str, str, str, str]:
    return (
        identity.schema_version,
        identity.layer_id,
        identity.artifact_kind,
        identity.owner,
        identity.subject,
    )


_VERIFIED_AIR_SLOT = (
    CACHE_SCHEMA_VERSION,
    "stability",
    "verified-air",
    "air.model",
    "project:verified-air",
)


class _SessionLinker(AIRProgramLinker):
    def __init__(self, session: "IncrementalProjectBuildSession") -> None:
        super().__init__()
        self._session = session

    def link(self, programs) -> AIRProgram:
        return self._session._link_programs(self, programs)


class _SessionValidator(RuntimeValidator):
    def __init__(self, session: "IncrementalProjectBuildSession") -> None:
        super().__init__()
        self._session = session

    def validate(self, program: AIRProgram) -> VerifiedAIRProgram:
        return self._session._validate_program(self, program)


class IncrementalProjectBuildSession:
    """Explicit reusable ProjectBuilder session backed by CacheCollection."""

    def __init__(
        self,
        collection: Optional[CacheCollection] = None,
    ) -> None:
        if collection is not None and type(collection) is not CacheCollection:
            raise TypeError(
                "IncrementalProjectBuildSession collection must be "
                "None or exact CacheCollection"
            )

        self._collection = (
            CacheCollection()
            if collection is None
            else collection
        )
        self._last_observations: Tuple[CacheObservation, ...] = ()
        self._current_observations = []
        self._current_compile_entries = []
        self._current_verified_candidate: Optional[CacheEntry] = None
        self._building = False

        self._last_compiler_owner_invocations = 0
        self._last_linker_owner_invocations = 0
        self._last_validator_owner_invocations = 0

        self._entries_by_key: Dict[str, CacheEntry] = {}
        self._slot_to_key: Dict[tuple[int, str, str, str, str], str] = {}
        self._entry_key_by_id: Dict[int, str] = {}
        self._trusted_entry_keys = set()
        self._compiler_configuration_fingerprints: Dict[
            tuple[object, bool],
            CacheFingerprint,
        ] = {}
        self._rebuild_indexes()

        self._compiler_contract = stability_input_fingerprint(
            {
                "module": compile_source_with_map.__module__,
                "qualname": compile_source_with_map.__qualname__,
                "signature": str(inspect.signature(compile_source_with_map)),
                "source": inspect.getsource(compile_source_with_map),
            }
        )
        self._linker_contract = stability_input_fingerprint(
            {
                "module": AIRProgramLinker.link.__module__,
                "qualname": AIRProgramLinker.link.__qualname__,
                "signature": str(inspect.signature(AIRProgramLinker.link)),
                "source": inspect.getsource(AIRProgramLinker.link),
            }
        )

        self._validator = _SessionValidator(self)
        standard_library = self._validator._standard_library
        self._validator_contract = stability_input_fingerprint(
            {
                "module": RuntimeValidator.validate.__module__,
                "qualname": RuntimeValidator.validate.__qualname__,
                "signature": str(inspect.signature(RuntimeValidator.validate)),
                "source": inspect.getsource(RuntimeValidator.validate),
                "standard_library_version": P10_STANDARD_LIBRARY_VERSION,
                "standard_library_names": tuple(standard_library.names),
                "standard_library_signatures": tuple(
                    (name, str(signature))
                    for name, signature
                    in standard_library.signatures().items()
                ),
                "linker_contract": self._linker_contract,
            }
        )

        self._linker = _SessionLinker(self)
        self._builder = ProjectBuilder(
            compiler=self._compile_source,
            linker=self._linker,
            validator=self._validator,
        )

    @property
    def collection(self) -> CacheCollection:
        return self._collection

    @property
    def last_observations(self) -> Tuple[CacheObservation, ...]:
        return self._last_observations

    @property
    def last_compiler_owner_invocations(self) -> int:
        return self._last_compiler_owner_invocations

    @property
    def last_linker_owner_invocations(self) -> int:
        return self._last_linker_owner_invocations

    @property
    def last_validator_owner_invocations(self) -> int:
        return self._last_validator_owner_invocations

    def _rebuild_indexes(self) -> None:
        entries_by_key = {}
        slot_to_key = {}
        entry_key_by_id = {}

        for entry in self._collection.entries:
            key = entry.cache_key
            entries_by_key[key] = entry
            slot_to_key[_identity_slot(entry.identity)] = key
            entry_key_by_id[id(entry)] = key

        self._entries_by_key = entries_by_key
        self._slot_to_key = slot_to_key
        self._entry_key_by_id = entry_key_by_id
        self._trusted_entry_keys.intersection_update(entries_by_key)

    def _entry_key(self, entry: CacheEntry) -> str:
        key = self._entry_key_by_id.get(id(entry))
        if key is not None:
            return key
        return entry.cache_key

    def _record(self, observation: CacheObservation) -> None:
        if type(observation) is not CacheObservation:
            raise TypeError("cache observation must be exact CacheObservation")
        self._current_observations.append(observation)

    def _invalidate(self, cache_keys: Tuple[str, ...]) -> None:
        self._collection, observation = self._collection.invalidate(cache_keys)
        self._record(observation)
        self._trusted_entry_keys.difference_update(
            observation.affected_cache_keys
        )
        self._rebuild_indexes()

    def _lookup(
        self,
        identity: CacheIdentity,
    ) -> Optional[CacheEntry]:
        if type(identity) is not CacheIdentity:
            raise TypeError("cache lookup identity must be exact CacheIdentity")

        slot = _identity_slot(identity)
        resident_key = self._slot_to_key.get(slot)

        if resident_key is not None:
            resident = self._entries_by_key[resident_key]
            if resident.identity == identity:
                self._record(
                    CacheObservation(
                        operation="lookup",
                        outcome="hit",
                        requested_cache_keys=(resident_key,),
                        affected_cache_keys=(resident_key,),
                    )
                )
                return resident

            requested_key = cache_identity_key(identity)
            self._record(
                CacheObservation(
                    operation="lookup",
                    outcome="stale",
                    requested_cache_keys=(requested_key,),
                    affected_cache_keys=(resident_key,),
                )
            )
            self._invalidate((resident_key,))
            return None

        requested_key = cache_identity_key(identity)
        self._record(
            CacheObservation(
                operation="lookup",
                outcome="miss",
                requested_cache_keys=(requested_key,),
                affected_cache_keys=(),
            )
        )
        return None

    def _store(self, entry: CacheEntry) -> None:
        self._collection, observation = self._collection.store(entry)
        self._record(observation)
        self._rebuild_indexes()
        self._trusted_entry_keys.add(entry.cache_key)

    def _trusted_resonance_entry(
        self,
        entry: CacheEntry,
        expected_type,
    ) -> bool:
        key = self._entry_key(entry)
        if key in self._trusted_entry_keys:
            return type(entry.value) is expected_type

        if type(entry.value) is not expected_type:
            self._invalidate((key,))
            return False

        try:
            fingerprint = resonance_fingerprint(entry.value)
        except TypeError:
            self._invalidate((key,))
            return False

        if fingerprint != entry.artifact_fingerprint:
            self._invalidate((key,))
            return False

        self._trusted_entry_keys.add(key)
        return True

    def _trusted_stability_entry(
        self,
        entry: CacheEntry,
        expected_type,
    ) -> bool:
        key = self._entry_key(entry)
        if key in self._trusted_entry_keys:
            return type(entry.value) is expected_type

        if type(entry.value) is not expected_type:
            self._invalidate((key,))
            return False

        try:
            fingerprint = stability_fingerprint(entry.value)
        except TypeError:
            self._invalidate((key,))
            return False

        if fingerprint != entry.artifact_fingerprint:
            self._invalidate((key,))
            return False

        self._trusted_entry_keys.add(key)
        return True

    def _compiler_configuration_fingerprint(
        self,
        function_signatures: Optional[Mapping[str, Any]],
        allow_headerless_multi_directive: bool,
    ) -> CacheFingerprint:
        signature_contract = _function_signature_contract(
            function_signatures
        )
        cache_key = (
            signature_contract,
            allow_headerless_multi_directive,
        )
        cached = self._compiler_configuration_fingerprints.get(cache_key)
        if cached is not None:
            return cached

        fingerprint = stability_input_fingerprint(
            {
                "compiler_contract": self._compiler_contract,
                "function_signatures": signature_contract,
                "allow_headerless_multi_directive":
                    allow_headerless_multi_directive,
            }
        )
        self._compiler_configuration_fingerprints[cache_key] = fingerprint
        return fingerprint

    def _compile_source(
        self,
        source: str,
        *,
        source_name: str = "<memory>",
        function_signatures: Optional[Mapping[str, Any]] = None,
        allow_headerless_multi_directive: bool = True,
    ) -> CompiledSource:
        input_fingerprint = cache_fingerprint(source.encode("utf-8"))
        configuration_fingerprint = (
            self._compiler_configuration_fingerprint(
                function_signatures,
                allow_headerless_multi_directive,
            )
        )

        identity = resonance_identity(
            CompiledSource,
            subject=source_name,
            input_fingerprint=input_fingerprint,
            configuration_fingerprint=configuration_fingerprint,
        )
        cached = self._lookup(identity)

        if (
            cached is not None
            and self._trusted_resonance_entry(cached, CompiledSource)
        ):
            self._current_compile_entries.append(cached)
            return cached.value

        def produce() -> CompiledSource:
            self._last_compiler_owner_invocations += 1
            return compile_source_with_map(
                source,
                source_name=source_name,
                function_signatures=function_signatures,
                allow_headerless_multi_directive=
                    allow_headerless_multi_directive,
            )

        entry = reuse_or_produce_resonance(
            CompiledSource,
            subject=source_name,
            input_fingerprint=input_fingerprint,
            configuration_fingerprint=configuration_fingerprint,
            producer=produce,
            cached=None,
        )

        self._store(entry)
        self._current_compile_entries.append(entry)
        return entry.value

    def _compile_dependencies(self) -> Tuple[CacheDependency, ...]:
        return tuple(
            CacheDependency(
                cache_key=self._entry_key(entry),
                fingerprint=entry.artifact_fingerprint,
            )
            for entry in self._current_compile_entries
        )

    def _verified_candidate_for_current_compiles(
        self,
    ) -> Optional[CacheEntry]:
        resident_key = self._slot_to_key.get(_VERIFIED_AIR_SLOT)
        if resident_key is None:
            return None

        entry = self._entries_by_key[resident_key]
        identity = entry.identity
        dependencies = self._compile_dependencies()

        if (
            identity.configuration_fingerprint != self._validator_contract
            or identity.dependencies != dependencies
        ):
            return None

        if not self._trusted_stability_entry(
            entry,
            VerifiedAIRProgram,
        ):
            return None

        return entry

    def _link_programs(
        self,
        linker: AIRProgramLinker,
        programs,
    ) -> AIRProgram:
        units = tuple(programs)
        candidate = self._verified_candidate_for_current_compiles()
        self._current_verified_candidate = None

        if (
            candidate is not None
            and len(units) == len(self._current_compile_entries)
        ):
            self._current_verified_candidate = candidate
            return candidate.value.program

        self._last_linker_owner_invocations += 1
        return AIRProgramLinker.link(linker, units)

    def _validate_program(
        self,
        validator: RuntimeValidator,
        program: AIRProgram,
    ) -> VerifiedAIRProgram:
        candidate = self._current_verified_candidate
        self._current_verified_candidate = None

        if (
            candidate is not None
            and candidate.value.program is program
        ):
            cached = self._lookup(candidate.identity)
            if (
                cached is candidate
                and self._trusted_stability_entry(
                    cached,
                    VerifiedAIRProgram,
                )
            ):
                return cached.value

        dependencies = self._compile_dependencies()
        input_fingerprint = stability_input_fingerprint(program)

        identity = stability_identity(
            VerifiedAIRProgram,
            subject="project:verified-air",
            input_fingerprint=input_fingerprint,
            configuration_fingerprint=self._validator_contract,
            dependencies=dependencies,
        )
        cached = self._lookup(identity)

        if cached is not None:
            if (
                self._trusted_stability_entry(
                    cached,
                    VerifiedAIRProgram,
                )
                and cached.value.program is program
            ):
                return cached.value

            if self._entry_key(cached) in self._entries_by_key:
                self._invalidate((self._entry_key(cached),))
            cached = None

        def produce() -> VerifiedAIRProgram:
            self._last_validator_owner_invocations += 1
            return RuntimeValidator.validate(validator, program)

        entry = reuse_or_produce_stability(
            VerifiedAIRProgram,
            subject="project:verified-air",
            input_fingerprint=input_fingerprint,
            configuration_fingerprint=self._validator_contract,
            dependencies=dependencies,
            producer=produce,
            cached=None,
        )

        self._store(entry)
        return entry.value

    def build(
        self,
        sources,
        *,
        entry: Optional[str] = None,
    ) -> ProjectBuild:
        if self._building:
            raise RuntimeError(
                "IncrementalProjectBuildSession does not permit re-entrant builds"
            )

        self._building = True
        self._current_observations = []
        self._current_compile_entries = []
        self._current_verified_candidate = None
        self._last_compiler_owner_invocations = 0
        self._last_linker_owner_invocations = 0
        self._last_validator_owner_invocations = 0

        try:
            result = self._builder.build(
                sources,
                entry=entry,
            )
        finally:
            self._last_observations = tuple(self._current_observations)
            self._current_observations = []
            self._current_compile_entries = []
            self._current_verified_candidate = None
            self._building = False

        return result

    def __call__(
        self,
        sources,
        entry: Optional[str] = None,
    ) -> ProjectBuild:
        """CLI-compatible builder call surface."""

        return self.build(sources, entry=entry)


__all__ = (
    "IncrementalProjectBuildSession",
)