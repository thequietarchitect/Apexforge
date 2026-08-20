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
    trace_map_from_resolution_observation,
    trace_map_from_source_map,
    trace_record_from_declaration_owner,
    trace_record_from_declared_identity,
    trace_record_from_resolution_candidate,
    trace_record_from_resolution_context,
    trace_record_from_resolution_outcome,
    trace_record_from_resolution_query,
    trace_map_from_type_evidence,
    trace_record_from_type_evidence,
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
    "trace_record_from_resolution_query",
    "trace_record_from_resolution_context",
    "trace_record_from_resolution_candidate",
    "trace_record_from_resolution_outcome",
    "trace_map_from_resolution_observation",
    "trace_record_from_type_evidence",
    "trace_map_from_type_evidence",
)