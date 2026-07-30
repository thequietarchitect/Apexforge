"""Stable public facade for the frozen AFP-P9 generics subsystem.

Importing from this module gives tooling and later compiler phases one explicit
P9 surface without requiring callers to depend on internal module layout.
"""

from __future__ import annotations

from type_system.constraints import (
    ApexTypeConstraint,
    ConstraintLike,
    NUMERIC,
    builtin_type_satisfies_constraint,
    is_type_constraint,
    resolve_type_constraint,
)
from type_system.generics import (
    ApexTypeVariable,
    GenericTypeLike,
    TypeIdentity,
    is_type_variable,
    resolve_type,
    type_satisfies_constraint,
    type_satisfies_constraints,
)
from type_system.substitution import (
    GenericSubstitution,
    GenericSubstitutionConflict,
)
from type_system.inference import (
    FunctionSignature,
    TypeInferenceError,
    infer_call_substitution,
    infer_explicit_call_substitution,
    infer_expression_type,
    infer_expression_type_partial,
    resolve_call_specialization,
    signatures_from_air_functions,
)
from type_system.specialization import (
    GenericInstantiationTable,
    GenericSpecialization,
    GenericSpecializationConflict,
    GenericSpecializationKey,
    OpenGenericSpecializationError,
)
from type_system.closure import (
    GenericSpecializationDependency,
    GenericSpecializationManifest,
    LinkedSpecializationCollector,
    collect_linked_specializations,
)
from type_system.lowering import (
    GenericLoweringError,
    GenericLoweringResult,
    LinkedGenericLowerer,
    LoweredSpecializationBinding,
    lower_linked_generics,
    specialization_function_id,
    specialization_function_name,
)
from type_system.freeze import (
    P9FreezeAudit,
    P9FreezeManifest,
    P9_FREEZE_CANDIDATE,
    audit_lowered_generics,
)

P9_API_VERSION = "9.0"
P9_PHASE = "AFP-P9"

__all__ = (
    "ApexTypeConstraint",
    "ApexTypeVariable",
    "ConstraintLike",
    "FunctionSignature",
    "GenericInstantiationTable",
    "GenericLoweringError",
    "GenericLoweringResult",
    "GenericSpecialization",
    "GenericSpecializationConflict",
    "GenericSpecializationDependency",
    "GenericSpecializationKey",
    "GenericSpecializationManifest",
    "GenericSubstitution",
    "GenericSubstitutionConflict",
    "GenericTypeLike",
    "LinkedGenericLowerer",
    "LinkedSpecializationCollector",
    "LoweredSpecializationBinding",
    "NUMERIC",
    "OpenGenericSpecializationError",
    "P9FreezeAudit",
    "P9FreezeManifest",
    "P9_API_VERSION",
    "P9_FREEZE_CANDIDATE",
    "P9_PHASE",
    "TypeIdentity",
    "TypeInferenceError",
    "audit_lowered_generics",
    "builtin_type_satisfies_constraint",
    "collect_linked_specializations",
    "infer_call_substitution",
    "infer_explicit_call_substitution",
    "infer_expression_type",
    "infer_expression_type_partial",
    "is_type_constraint",
    "is_type_variable",
    "lower_linked_generics",
    "resolve_call_specialization",
    "resolve_type",
    "resolve_type_constraint",
    "signatures_from_air_functions",
    "specialization_function_id",
    "specialization_function_name",
    "type_satisfies_constraint",
    "type_satisfies_constraints",
)