"""Contextual classification through frozen filtering and query outcomes."""

from __future__ import annotations

from language.resolution_candidates import ProjectResolutionCandidateIndex
from language.resolution_context import ProjectResolutionContext
from language.resolution_queries import (
    ProjectAmbiguousResolution,
    ProjectResolutionQuery,
    ProjectResolvedBinding,
    ProjectUnresolvedResolution,
    resolve_project_query,
)
from language.resolution_visibility import filter_project_visible_candidates


def resolve_project_contextual_query(
    index: ProjectResolutionCandidateIndex,
    query: ProjectResolutionQuery,
    context: ProjectResolutionContext,
) -> (
    ProjectUnresolvedResolution
    | ProjectResolvedBinding
    | ProjectAmbiguousResolution
):
    """Classify the exact candidate tuple retained by contextual visibility."""

    if type(index) is not ProjectResolutionCandidateIndex:
        raise TypeError(
            "resolve_project_contextual_query.index must be "
            "ProjectResolutionCandidateIndex."
        )
    if type(query) is not ProjectResolutionQuery:
        raise TypeError(
            "resolve_project_contextual_query.query must be "
            "ProjectResolutionQuery."
        )
    if type(context) is not ProjectResolutionContext:
        raise TypeError(
            "resolve_project_contextual_query.context must be "
            "ProjectResolutionContext."
        )

    visible_candidates = filter_project_visible_candidates(
        index,
        query,
        context,
    )
    visible_index = ProjectResolutionCandidateIndex(visible_candidates)
    return resolve_project_query(visible_index, query)


__all__ = (
    "resolve_project_contextual_query",
)
