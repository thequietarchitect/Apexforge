"""P11.12G ProjectBuilder/tooling incremental-cache integration.

The semantic build owner remains language.project.ProjectBuilder. This module
provides an explicit, instance-local build session that injects cache-aware
compiler, linker-alignment, and validator collaborators through ProjectBuilder's
existing extension seams.

The session owns only reuse state and CacheObservation evidence. It does not
modify ProjectBuilder semantics, cache ProjectBuild as one object, persist
entries, create a global cache, execute runtime behavior, or adapt evidence into
TAP.
"""

from __future__ import annotations

import inspect
from typing import Any, Mapping, Optional, Tuple

from air.linker import AIRProgramLinker
from air.model import AIRProgram, VerifiedAIRProgram
from incremental_cache.model import CacheEntry, cache_fingerprint
from incremental_cache.operational import CacheCollection, CacheObservation
from incremental_cache.resonance import (
    resonance_identity,
    reuse_or_produce_resonance,
)
from incremental_cache.stability import (
    reuse_or_produce_stability,
    stability_dependency,
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
        self._building = False

        self._last_compiler_owner_invocations = 0
        self._last_linker_owner_invocations = 0
        self._last_validator_owner_invocations = 0

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

    def _record(self, observation: CacheObservation) -> None:
        if type(observation) is not CacheObservation:
            raise TypeError("cache observation must be exact CacheObservation")
        self._current_observations.append(observation)

    def _lookup(self, identity):
        cached, observation = self._collection.lookup(identity)
        self._record(observation)

        if observation.outcome != "stale":
            return cached

        if observation.affected_cache_keys:
            self._collection, invalidation = self._collection.invalidate(
                observation.affected_cache_keys
            )
            self._record(invalidation)
        return None

    def _store(self, entry: CacheEntry) -> None:
        self._collection, observation = self._collection.store(entry)
        self._record(observation)

    def _compile_source(
        self,
        source: str,
        *,
        source_name: str = "<memory>",
        function_signatures: Optional[Mapping[str, Any]] = None,
        allow_headerless_multi_directive: bool = True,
    ) -> CompiledSource:
        input_fingerprint = cache_fingerprint(source.encode("utf-8"))
        configuration_fingerprint = stability_input_fingerprint(
            {
                "compiler_contract": self._compiler_contract,
                "function_signatures": _function_signature_contract(
                    function_signatures
                ),
                "allow_headerless_multi_directive":
                    allow_headerless_multi_directive,
            }
        )

        identity = resonance_identity(
            CompiledSource,
            subject=source_name,
            input_fingerprint=input_fingerprint,
            configuration_fingerprint=configuration_fingerprint,
        )
        cached = self._lookup(identity)

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
            cached=cached,
        )

        if cached is None:
            self._store(entry)

        self._current_compile_entries.append(entry)
        return entry.value

    def _compile_dependencies(self):
        return tuple(
            stability_dependency(entry)
            for entry in self._current_compile_entries
        )

    def _verified_candidate_for_current_compiles(
        self,
    ) -> Optional[CacheEntry]:
        dependencies = self._compile_dependencies()

        for entry in reversed(self._collection.entries):
            identity = entry.identity
            if (
                identity.layer_id != "stability"
                or identity.artifact_kind != "verified-air"
                or identity.owner != "air.model"
                or identity.subject != "project:verified-air"
                or identity.configuration_fingerprint
                != self._validator_contract
                or identity.dependencies != dependencies
                or type(entry.value) is not VerifiedAIRProgram
            ):
                continue

            if entry.artifact_fingerprint != stability_fingerprint(entry.value):
                continue
            return entry

        return None

    def _link_programs(
        self,
        linker: AIRProgramLinker,
        programs,
    ) -> AIRProgram:
        units = tuple(programs)
        candidate = self._verified_candidate_for_current_compiles()

        if candidate is not None:
            cached_program = candidate.value.program
            if len(units) == len(self._current_compile_entries):
                return cached_program

        self._last_linker_owner_invocations += 1
        return AIRProgramLinker.link(linker, units)

    def _validate_program(
        self,
        validator: RuntimeValidator,
        program: AIRProgram,
    ) -> VerifiedAIRProgram:
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
            cached=cached,
        )

        if cached is None:
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