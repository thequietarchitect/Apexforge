"""Compiler Token Analysis Map (TAM) immutable trace contracts."""

from .model import (
    CANONICAL_TRACE_DOMAINS,
    TRACE_DOMAIN_IDS,
    TRACE_SCHEMA_VERSION,
    TraceDomain,
    TraceIdentity,
    TraceMap,
    TraceRecord,
)
from .production import (
    trace_identity_for_source_map_entry,
    trace_identity_for_source_span,
    trace_map_from_declaration_identity_indexes,
    trace_map_from_source_map,
    trace_record_from_declaration_owner,
    trace_record_from_declared_identity,
)

__all__ = (
    "CANONICAL_TRACE_DOMAINS",
    "TRACE_DOMAIN_IDS",
    "TRACE_SCHEMA_VERSION",
    "TraceDomain",
    "TraceIdentity",
    "TraceMap",
    "TraceRecord",
    "trace_identity_for_source_map_entry",
    "trace_identity_for_source_span",
    "trace_map_from_source_map",
    "trace_map_from_declaration_identity_indexes",
    "trace_record_from_declaration_owner",
    "trace_record_from_declared_identity",
)