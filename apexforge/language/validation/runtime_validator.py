"""
ApexForge runtime validation.

This module validates a compiled AIRProgram before it enters RuntimeEngine.

Pipeline:

    AIRProgram
        ↓
    RuntimeValidator
        ↓
    VerifiedAIRProgram
        ↓
    RuntimeEngine

The validator guarantees the structural assumptions made by RuntimeEngine:

- principal references exist
- authority-check references exist
- causal-decision references exist
- state assignments reference defined states
- event emissions reference defined events
- directive invocations reference defined directives
- identifiers are valid and unique
- required textual values are non-empty strings

This validator intentionally avoids importing the authority, principal, and
role registries. Runtime validation only needs the declarations contained in
the AIRProgram, and avoiding those imports prevents circular dependencies.
"""

from __future__ import annotations

from typing import Any, Iterable, Mapping, Optional, Sequence


# Adjust this import only if AIRProgram is stored somewhere else.
from air.model import (
    AIRProgram,
    VerifiedAIRProgram,
    validate_state_definition_shape,
)
from type_system.inference import (
    FunctionSignature,
    TypeInferenceError,
    infer_expression_type_partial,
)
from type_system.model import (
    ApexType,
    BOOL,
    FLOAT,
    INT,
    STRING,
    VOID,
    resolve_builtin_type,
)


class _LegacyFunctionReturn:
    """Internal adapter for P7.1 AIRFunction.return_expression."""

    def __init__(self, expression: Any) -> None:
        self.expression = expression


# ============================================================================
# Validation errors
# ============================================================================


class RuntimeValidationError(Exception):
    """Base class for all runtime-validation failures."""


class InvalidProgramError(RuntimeValidationError):
    """Raised when the supplied object is not a valid AIRProgram."""


class InvalidValueError(RuntimeValidationError):
    """Raised when a required field contains an invalid value."""


class DuplicateDefinitionError(RuntimeValidationError):
    """Raised when two declarations use the same identifier."""


class UndefinedReferenceError(RuntimeValidationError):
    """Raised when an AIR object references an undefined declaration."""


# ============================================================================
# Verified wrapper
# ============================================================================

# VerifiedAIRProgram is imported from air.model so the validator and runtime
# share one canonical wrapper class.


# ============================================================================
# Runtime validator
# ============================================================================


class RuntimeValidator:
    """Validate an AIRProgram for safe execution by RuntimeEngine."""

    def validate(
        self,
        program: AIRProgram,
    ) -> VerifiedAIRProgram:
        """
        Validate the complete program and return a verified wrapper.

        Raises:
            InvalidProgramError
            InvalidValueError
            DuplicateDefinitionError
            UndefinedReferenceError
        """

        if not isinstance(program, AIRProgram):
            raise InvalidProgramError(
                "RuntimeValidator.validate requires AIRProgram; "
                f"received {type(program).__name__}."
            )

        self._required_string(
            getattr(program, "version", None),
            description="program version",
        )

        # ------------------------------------------------------------------
        # Build canonical indexes.
        #
        # Important:
        # Event emissions reference EventDefinition.id, not .name.
        # Principal references use Principal.id.
        # ------------------------------------------------------------------

        state_index = self._index_by_id(
            getattr(program, "states", ()),
            owner="state",
        )
        self._state_index = state_index

        event_index = self._index_by_id(
            getattr(program, "events", ()),
            owner="event",
        )

        authority_check_index = self._index_by_id(
            getattr(program, "authority_checks", ()),
            owner="authority check",
        )

        causal_decision_index = self._index_by_id(
            getattr(program, "causal_decisions", ()),
            owner="causal decision",
        )

        directive_index = self._index_by_id(
            getattr(program, "directives", ()),
            owner="directive",
        )

        function_index = self._index_by_id(
            getattr(program, "functions", ()),
            owner="function",
        )

        # Expression validation uses this complete linked index so calls may
        # resolve across separately compiled function and directive units.
        self._function_index = function_index

        principal_index = self._index_by_id(
            getattr(program, "principals", ()),
            owner="principal",
        )

        authority_index = self._index_by_name_or_id(
            getattr(program, "authorities", ()),
            owner="authority",
        )

        role_index = self._index_by_name_or_id(
            getattr(program, "roles", ()),
            owner="role",
        )

        # ------------------------------------------------------------------
        # Validate declaration contents and references.
        # ------------------------------------------------------------------

        self._validate_functions(
            functions=getattr(program, "functions", ()),
            function_index=function_index,
        )

        self._validate_states(
            states=getattr(program, "states", ()),
            state_ids=set(state_index),
        )

        self._validate_events(
            events=getattr(program, "events", ()),
        )

        self._validate_authorities(
            authorities=getattr(program, "authorities", ()),
        )

        self._validate_roles(
            roles=getattr(program, "roles", ()),
            authority_index=authority_index,
            role_index=role_index,
        )

        self._validate_principals(
            principals=getattr(program, "principals", ()),
            principal_index=principal_index,
            role_index=role_index,
            authority_index=authority_index,
        )

        self._validate_authority_checks(
            checks=getattr(program, "authority_checks", ()),
            principal_index=principal_index,
        )

        self._validate_causal_decisions(
            program=program,
            state_ids=set(state_index),
            event_ids=set(event_index),
            directive_ids=set(directive_index),
        )

        self._validate_directives(
            directives=getattr(program, "directives", ()),
            principal_index=principal_index,
            authority_check_index=authority_check_index,
            causal_decision_index=causal_decision_index,
        )

        self._validate_requirements(
            requirements=getattr(program, "requirements", ()),
            directive_index=directive_index,
            principal_index=principal_index,
            authority_index=authority_index,
        )

        self._validate_linked_program_types(
            program=program,
            state_index=state_index,
            function_index=function_index,
        )

        return VerifiedAIRProgram(
            program=program,
        )

    # ======================================================================
    # Index construction
    # ======================================================================

    def _index_by_id(
        self,
        values: Iterable[Any],
        owner: str,
    ) -> dict[str, Any]:
        """Index declarations using their required .id field."""

        index: dict[str, Any] = {}

        for value in values:
            identifier = self._required_string(
                getattr(value, "id", None),
                description=f"{owner} id",
            )

            if identifier in index:
                raise DuplicateDefinitionError(
                    f"Duplicate {owner} id '{identifier}'."
                )

            index[identifier] = value

        return index

    def _index_by_name_or_id(
        self,
        values: Iterable[Any],
        owner: str,
    ) -> dict[str, Any]:
        """
        Index declarations that may use either .name or .id.

        Authorities and roles in ApexForge have historically used names,
        while AIR runtime objects generally use IDs.
        """

        index: dict[str, Any] = {}

        for value in values:
            identifier = self._declaration_name_or_id(
                value,
                description=owner,
            )

            if identifier in index:
                raise DuplicateDefinitionError(
                    f"Duplicate {owner} declaration '{identifier}'."
                )

            index[identifier] = value

        return index

    # ======================================================================
    # Pure functions
    # ======================================================================

    def _validate_functions(
        self,
        functions: Iterable[Any],
        function_index: Mapping[str, Any],
    ) -> None:
        """Validate pure-function statements, scope, returns, and calls."""

        function_values = tuple(functions)
        orders: set[int] = set()
        names: set[str] = set()

        for function in function_values:
            function_id = self._required_string(
                getattr(function, "id", None),
                description="function id",
            )
            function_name = self._required_string(
                getattr(function, "name", None),
                description=f"function '{function_id}' name",
            )

            if function_name in names:
                raise DuplicateDefinitionError(
                    f"Duplicate function name '{function_name}'."
                )
            names.add(function_name)

            parameters = tuple(
                getattr(function, "parameters", ()) or ()
            )
            visible_names: set[str] = set()

            for index, parameter in enumerate(parameters):
                parameter_name = self._required_string(
                    getattr(parameter, "name", None),
                    description=(
                        f"function '{function_id}' parameter[{index}] name"
                    ),
                )

                if parameter_name in visible_names:
                    raise DuplicateDefinitionError(
                        f"Function '{function_id}' declares duplicate "
                        f"parameter '{parameter_name}'."
                    )
                visible_names.add(parameter_name)

            order = getattr(function, "order", 0)
            if isinstance(order, bool) or not isinstance(order, int):
                raise InvalidValueError(
                    f"Function '{function_id}' order must be an integer; "
                    f"received {type(order).__name__}."
                )
            if order in orders:
                raise DuplicateDefinitionError(
                    f"Duplicate function order '{order}'."
                )
            orders.add(order)

            body = self._function_body(function)
            definitely_returns = self._validate_function_statements(
                statements=body,
                visible_names=frozenset(visible_names),
                function_id=function_id,
                owner=f"function '{function_id}' body",
                depth=0,
            )

            if not definitely_returns:
                raise InvalidValueError(
                    f"Function '{function_id}' does not return on every "
                    "reachable control-flow path."
                )

        self._validate_function_call_graph(
            functions=function_values,
            function_index=function_index,
        )

    def _function_body(
        self,
        function: Any,
    ) -> tuple[Any, ...]:
        raw_body = getattr(function, "body", ())

        body = self._function_statement_sequence(
            raw_body,
            owner=(
                f"function '{getattr(function, 'id', '<unknown>')}' body"
            ),
            required=False,
        )

        if body:
            return body

        legacy = self._function_statement_sequence(
            getattr(function, "local_bindings", ()),
            owner=(
                f"function '{getattr(function, 'id', '<unknown>')}' "
                "legacy local bindings"
            ),
            required=False,
        )

        if not hasattr(function, "return_expression"):
            raise InvalidValueError(
                f"Function '{getattr(function, 'id', '<unknown>')}' is "
                "missing its return expression."
            )

        return_expression = getattr(function, "return_expression")

        if return_expression is None:
            raise InvalidValueError(
                f"Function '{getattr(function, 'id', '<unknown>')}' is "
                "missing its return expression."
            )

        # Lightweight compatibility object so older P7.1 AIR validates through
        # the same statement pipeline without importing air.functions.
        return legacy + (_LegacyFunctionReturn(return_expression),)

    def _function_statement_sequence(
        self,
        value: Any,
        *,
        owner: str,
        required: bool = True,
    ) -> tuple[Any, ...]:
        """Normalize one pure-function statement stream defensively."""

        if value is None:
            if required:
                raise InvalidValueError(
                    f"{owner} statement stream is missing."
                )
            return ()

        if isinstance(value, (str, bytes)):
            raise InvalidValueError(
                f"{owner} statement stream must be a sequence of AIR "
                "statements, not text."
            )

        try:
            return tuple(value)
        except TypeError as exc:
            raise InvalidValueError(
                f"{owner} statement stream must be iterable."
            ) from exc

    def _validate_function_statements(
        self,
        *,
        statements: Sequence[Any],
        visible_names: frozenset[str],
        function_id: str,
        owner: str,
        depth: int,
    ) -> bool:
        """Validate lexical scope and definite return for one statement block."""

        if depth > 64:
            raise InvalidValueError(
                f"{owner} exceeds the maximum function conditional "
                "nesting depth of 64."
            )

        normalized_statements = self._function_statement_sequence(
            statements,
            owner=owner,
        )
        current_names = set(visible_names)
        definitely_returns = False

        for index, statement in enumerate(normalized_statements):
            statement_owner = f"{owner} statement[{index}]"

            if definitely_returns:
                raise InvalidValueError(
                    f"{statement_owner} is unreachable because the preceding "
                    "control-flow path definitely returns."
                )

            statement_type = type(statement).__name__

            if statement_type == "AIRLocalBinding":
                local_name = self._required_string(
                    getattr(statement, "name", None),
                    description=f"{statement_owner} local name",
                )

                if local_name in current_names:
                    raise DuplicateDefinitionError(
                        f"Function '{function_id}' local '{local_name}' "
                        "duplicates or shadows an existing binding."
                    )

                if not hasattr(statement, "expression"):
                    raise InvalidValueError(
                        f"{statement_owner} local '{local_name}' is missing "
                        "its expression."
                    )

                self._validate_expression(
                    getattr(statement, "expression"),
                    state_ids=set(),
                    owner=f"{statement_owner} expression",
                    local_names=frozenset(current_names),
                    allow_state_references=False,
                )
                current_names.add(local_name)
                continue

            if statement_type in {
                "AIRFunctionReturn",
                "_LegacyFunctionReturn",
            }:
                if not hasattr(statement, "expression"):
                    raise InvalidValueError(
                        f"{statement_owner} return is missing its expression."
                    )

                self._validate_expression(
                    getattr(statement, "expression"),
                    state_ids=set(),
                    owner=f"{statement_owner} return expression",
                    local_names=frozenset(current_names),
                    allow_state_references=False,
                )
                definitely_returns = True
                continue

            if statement_type == "AIRFunctionWhen":
                if not hasattr(statement, "condition"):
                    raise InvalidValueError(
                        f"{statement_owner} conditional is missing its "
                        "condition."
                    )

                self._validate_expression(
                    getattr(statement, "condition"),
                    state_ids=set(),
                    owner=f"{statement_owner} condition",
                    local_names=frozenset(current_names),
                    allow_state_references=False,
                )

                if not hasattr(statement, "actions"):
                    raise InvalidValueError(
                        f"{statement_owner} conditional is missing its when "
                        "statement stream."
                    )

                true_actions = self._function_statement_sequence(
                    getattr(statement, "actions"),
                    owner=f"{statement_owner} when block",
                )
                true_returns = self._validate_function_statements(
                    statements=true_actions,
                    visible_names=frozenset(current_names),
                    function_id=function_id,
                    owner=f"{statement_owner} when block",
                    depth=depth + 1,
                )

                otherwise_actions = self._function_statement_sequence(
                    getattr(statement, "otherwise_actions", ()),
                    owner=f"{statement_owner} otherwise block",
                    required=False,
                )
                false_returns = False

                if otherwise_actions:
                    false_returns = self._validate_function_statements(
                        statements=otherwise_actions,
                        visible_names=frozenset(current_names),
                        function_id=function_id,
                        owner=f"{statement_owner} otherwise block",
                        depth=depth + 1,
                    )

                if true_returns and false_returns:
                    definitely_returns = True
                continue

            raise InvalidValueError(
                f"{statement_owner} has unsupported pure-function "
                f"statement type '{statement_type}'. Pure functions may "
                "contain only immutable local bindings, conditionals, and "
                "returns."
            )

        return definitely_returns

    def _validate_function_call_graph(
        self,
        functions: Sequence[Any],
        function_index: Mapping[str, Any],
    ) -> None:
        """Reject direct and indirect recursion across full function bodies."""

        graph: dict[str, tuple[str, ...]] = {}

        for function in functions:
            function_id = self._required_string(
                getattr(function, "id", None),
                description="function id",
            )
            raw_targets = self._collect_function_statement_call_targets(
                self._function_body(function)
            )
            resolved_targets: list[str] = []

            for target in raw_targets:
                resolved = self._resolve_function_reference(
                    target,
                    function_index,
                )
                if resolved is not None:
                    resolved_targets.append(resolved)

            graph[function_id] = tuple(resolved_targets)

        visited: set[str] = set()
        active: set[str] = set()
        stack: list[str] = []

        def visit(function_id: str) -> None:
            if function_id in visited:
                return
            if function_id in active:
                cycle_start = stack.index(function_id)
                cycle = stack[cycle_start:] + [function_id]
                rendered = " -> ".join(
                    self._function_display_name(identifier, function_index)
                    for identifier in cycle
                )
                raise InvalidValueError(
                    f"Recursive function cycle detected: {rendered}."
                )

            active.add(function_id)
            stack.append(function_id)
            for target_id in graph.get(function_id, ()):
                visit(target_id)
            stack.pop()
            active.remove(function_id)
            visited.add(function_id)

        ordered_ids = tuple(
            self._required_string(
                getattr(function, "id", None),
                description="function id",
            )
            for function in sorted(
                functions,
                key=lambda value: (
                    getattr(value, "order", 0),
                    getattr(value, "id", ""),
                ),
            )
        )
        for function_id in ordered_ids:
            visit(function_id)

    def _collect_function_statement_call_targets(
        self,
        statements: Sequence[Any],
    ) -> tuple[str, ...]:
        targets: tuple[str, ...] = ()

        for statement in tuple(statements):
            statement_type = type(statement).__name__
            if statement_type == "AIRLocalBinding":
                targets += self._collect_function_call_targets(
                    getattr(statement, "expression", None)
                )
                continue
            if statement_type in {"AIRFunctionReturn", "_LegacyFunctionReturn"}:
                targets += self._collect_function_call_targets(
                    getattr(statement, "expression", None)
                )
                continue
            if statement_type == "AIRFunctionWhen":
                targets += self._collect_function_call_targets(
                    getattr(statement, "condition", None)
                )
                targets += self._collect_function_statement_call_targets(
                    tuple(getattr(statement, "actions", ()) or ())
                )
                targets += self._collect_function_statement_call_targets(
                    tuple(
                        getattr(statement, "otherwise_actions", ()) or ()
                    )
                )

        return targets

    def _collect_function_call_targets(
        self,
        expression: Any,
    ) -> tuple[str, ...]:
        """Return call targets in deterministic expression evaluation order."""

        expression_type = type(expression).__name__
        if expression_type in {
            "AIRIntegerLiteral",
            "AIRFloatLiteral",
            "AIRStringLiteral",
            "AIRBooleanLiteral",
            "AIRIdentifierReference",
        }:
            return ()
        if expression_type == "AIRUnaryExpression":
            return self._collect_function_call_targets(
                getattr(expression, "operand"),
            )
        if expression_type == "AIRBinaryExpression":
            return (
                self._collect_function_call_targets(
                    getattr(expression, "left"),
                )
                + self._collect_function_call_targets(
                    getattr(expression, "right"),
                )
            )
        if expression_type == "AIRCallExpression":
            target = self._required_string(
                getattr(expression, "target", None),
                description="function call target",
            )
            nested = tuple(
                nested_target
                for argument in tuple(
                    getattr(expression, "arguments", ()) or ()
                )
                for nested_target in self._collect_function_call_targets(
                    argument
                )
            )
            return (target,) + nested
        return ()

    def _function_display_name(
        self,
        function_id: str,
        function_index: Mapping[str, Any],
    ) -> str:
        function = function_index.get(function_id)
        name = getattr(function, "name", None)
        if isinstance(name, str) and name.strip():
            return name.strip()
        if function_id.startswith("function:"):
            return function_id[len("function:"):]
        return function_id

    # ======================================================================
    # State and event declarations
    # ======================================================================

    def _validate_states(
        self,
        states: Iterable[Any],
        state_ids: set[str],
    ) -> None:
        for state in states:
            state_id = self._required_string(
                getattr(state, "id", None),
                description="state id",
            )

            if not hasattr(state, "initial"):
                raise InvalidValueError(
                    f"State '{state_id}' is missing its initial expression."
                )

            try:
                value_type = resolve_builtin_type(
                    getattr(state, "value_type", INT)
                )
            except (TypeError, ValueError) as exc:
                raise InvalidValueError(
                    f"State '{state_id}' has an invalid ApexForge type."
                ) from exc

            if value_type is VOID:
                raise InvalidValueError(
                    f"State '{state_id}' cannot use void."
                )

            if not validate_state_definition_shape(state):
                raise InvalidValueError(
                    f"State '{state_id}' initializer is incompatible with "
                    f"declared type {value_type}."
                )

            self._validate_expression(
                getattr(state, "initial"),
                state_ids=state_ids,
                owner=f"state '{state_id}' initial expression",
            )

    def _validate_events(
        self,
        events: Iterable[Any],
    ) -> None:
        for event in events:
            event_id = self._required_string(
                getattr(event, "id", None),
                description="event id",
            )

            event_name = getattr(event, "name", None)

            if event_name is not None:
                self._required_string(
                    event_name,
                    description=f"event '{event_id}' name",
                )

    # ======================================================================
    # Authority and role declarations
    # ======================================================================

    def _validate_authorities(
        self,
        authorities: Iterable[Any],
    ) -> None:
        for authority in authorities:
            self._declaration_name_or_id(
                authority,
                description="authority",
            )

    def _validate_roles(
        self,
        roles: Iterable[Any],
        authority_index: Mapping[str, Any],
        role_index: Mapping[str, Any],
    ) -> None:
        for role in roles:
            role_name = self._declaration_name_or_id(
                role,
                description="role",
            )

            inherited_roles = getattr(
                role,
                "roles",
                getattr(role, "inherits", ()),
            )

            for reference in inherited_roles or ():
                inherited_name = self._reference_value(
                    reference,
                    description=(
                        f"role '{role_name}' inherited role reference"
                    ),
                )

                if inherited_name not in role_index:
                    raise UndefinedReferenceError(
                        f"Role '{role_name}' references undefined role "
                        f"'{inherited_name}'."
                    )

                if inherited_name == role_name:
                    raise InvalidValueError(
                        f"Role '{role_name}' cannot inherit itself."
                    )

            role_authorities = getattr(
                role,
                "authorities",
                (),
            )

            for reference in role_authorities or ():
                # A direct capability-bearing object is an inline grant,
                # rather than a reference to program.authorities.
                if self._is_inline_authority(reference):
                    continue

                authority_name = self._reference_value(
                    reference,
                    description=(
                        f"role '{role_name}' authority reference"
                    ),
                )

                if authority_name not in authority_index:
                    raise UndefinedReferenceError(
                        f"Role '{role_name}' references undefined authority "
                        f"'{authority_name}'."
                    )

    # ======================================================================
    # Principals
    # ======================================================================

    def _validate_principals(
        self,
        principals: Iterable[Any],
        principal_index: Mapping[str, Any],
        role_index: Mapping[str, Any],
        authority_index: Mapping[str, Any],
    ) -> None:
        for principal in principals:
            principal_id = self._required_string(
                getattr(principal, "id", None),
                description="principal id",
            )

            # Merely accessing the index here also documents the invariant.
            if principal_id not in principal_index:
                raise UndefinedReferenceError(
                    f"Principal '{principal_id}' is absent from its index."
                )

            display_name = getattr(
                principal,
                "display_name",
                "",
            )

            if display_name not in ("", None):
                self._required_string(
                    display_name,
                    description=(
                        f"principal '{principal_id}' display name"
                    ),
                )

            roles = getattr(
                principal,
                "roles",
                (),
            )

            self._validate_unique_references(
                roles or (),
                owner=f"principal '{principal_id}'",
                value_kind="role",
            )

            for reference in roles or ():
                role_name = self._reference_value(
                    reference,
                    description=(
                        f"principal '{principal_id}' role reference"
                    ),
                )

                if role_name not in role_index:
                    raise UndefinedReferenceError(
                        f"Principal '{principal_id}' references undefined "
                        f"role '{role_name}'."
                    )

            authorities = getattr(
                principal,
                "authorities",
                (),
            )

            for reference in authorities or ():
                # PrincipalAuthority may represent a direct grant with a
                # capability rather than a named DirectiveAuthority.
                if self._is_inline_authority(reference):
                    continue

                authority_name = self._reference_value(
                    reference,
                    description=(
                        f"principal '{principal_id}' authority reference"
                    ),
                )

                if authority_name not in authority_index:
                    raise UndefinedReferenceError(
                        f"Principal '{principal_id}' references undefined "
                        f"authority '{authority_name}'."
                    )

    # ======================================================================
    # Authority checks
    # ======================================================================

    def _validate_authority_checks(
        self,
        checks: Iterable[Any],
        principal_index: Mapping[str, Any],
    ) -> None:
        for check in checks:
            check_id = self._required_string(
                getattr(check, "id", None),
                description="authority check id",
            )

            principal_id = self._required_string(
                getattr(check, "principal", None),
                description=(
                    f"authority check '{check_id}' principal reference"
                ),
            )

            if principal_id not in principal_index:
                raise UndefinedReferenceError(
                    f"Authority check '{check_id}' references undefined "
                    f"principal '{principal_id}'."
                )

            self._required_string(
                getattr(check, "capability", None),
                description=(
                    f"authority check '{check_id}' capability"
                ),
            )

            self._required_string(
                getattr(check, "resource", None),
                description=(
                    f"authority check '{check_id}' resource"
                ),
            )

    # ======================================================================
    # Causal decisions and paths
    # ======================================================================

    def _validate_causal_decisions(
        self,
        program: AIRProgram,
        state_ids: set[str],
        event_ids: set[str],
        directive_ids: set[str],
    ) -> None:
        """
        Validate every causal decision and its paths.

        The call site must pass:

            program=program

        not:

            decisions=program.causal_decisions
        """

        for decision in getattr(
            program,
            "causal_decisions",
            (),
        ):
            decision_id = self._required_string(
                getattr(decision, "id", None),
                description="causal decision id",
            )

            cause = getattr(
                decision,
                "cause",
                None,
            )

            if cause is not None:
                self._required_string(
                    cause,
                    description=(
                        f"causal decision '{decision_id}' cause"
                    ),
                )

            self._required_string(
                getattr(decision, "policy", None),
                description=(
                    f"causal decision '{decision_id}' policy"
                ),
            )

            paths = tuple(
                getattr(decision, "paths", ()) or ()
            )

            if not paths:
                raise InvalidValueError(
                    f"Causal decision '{decision_id}' has no paths."
                )

            self._validate_unique_attribute(
                paths,
                attribute="id",
                owner=(
                    f"causal decision '{decision_id}' paths"
                ),
            )

            for path in paths:
                self._validate_path(
                    path=path,
                    state_ids=state_ids,
                    event_ids=event_ids,
                    directive_ids=directive_ids,
                )

    def _validate_path(
        self,
        path: Any,
        state_ids: set[str],
        event_ids: set[str],
        directive_ids: set[str],
    ) -> None:
        path_id = self._required_string(
            getattr(path, "id", None),
            description="causal path id",
        )

        weight = getattr(
            path,
            "weight",
            None,
        )

        if not isinstance(weight, (int, float)):
            raise InvalidValueError(
                f"Path '{path_id}' weight must be numeric; "
                f"received {type(weight).__name__}."
            )

        # ------------------------------------------------------------------
        # Ordered AFP-P2 action stream
        # ------------------------------------------------------------------
        #
        # Newer paths preserve source order in path.actions. Validate that
        # stream recursively so AIRWhenAction boundaries and nested actions
        # remain intact.
        #
        # The legacy assignments/emits/invocations collections are still
        # validated below for AFP-P1 compatibility and to catch malformed
        # compatibility projections.
        # ------------------------------------------------------------------

        ordered_actions = tuple(
            getattr(
                path,
                "actions",
                (),
            ) or ()
        )

        if ordered_actions:
            self._validate_ordered_actions(
                actions=ordered_actions,
                state_ids=state_ids,
                event_ids=event_ids,
                directive_ids=directive_ids,
                owner=f"path '{path_id}'",
                depth=0,
            )

        # ------------------------------------------------------------------
        # Legacy AFP-P1 state assignments
        # ------------------------------------------------------------------

        for assignment in getattr(
            path,
            "assignments",
            (),
        ) or ():
            self._validate_state_assignment(
                assignment=assignment,
                state_ids=state_ids,
                owner=f"path '{path_id}'",
            )

        # ------------------------------------------------------------------
        # Legacy AFP-P1 event emissions
        # ------------------------------------------------------------------

        for emission in getattr(
            path,
            "emits",
            (),
        ) or ():
            self._validate_event_emission(
                emission=emission,
                event_ids=event_ids,
                state_ids=state_ids,
                owner=f"path '{path_id}'",
            )

        # ------------------------------------------------------------------
        # Legacy AFP-P1 directive invocations
        # ------------------------------------------------------------------

        for invocation in getattr(
            path,
            "invocations",
            (),
        ) or ():
            self._validate_directive_invocation(
                invocation=invocation,
                directive_ids=directive_ids,
                owner=f"path '{path_id}'",
            )

        # ------------------------------------------------------------------
        # Host effect intents
        # ------------------------------------------------------------------

        for effect in getattr(
            path,
            "effects",
            (),
        ) or ():
            effect_id = getattr(
                effect,
                "id",
                None,
            )

            if effect_id is not None:
                self._required_string(
                    effect_id,
                    description=(
                        f"path '{path_id}' effect id"
                    ),
                )

            effect_type = getattr(
                effect,
                "effect_type",
                None,
            )

            if effect_type is not None:
                self._required_string(
                    effect_type,
                    description=(
                        f"path '{path_id}' effect type"
                    ),
                )

        rationale = getattr(
            path,
            "rationale",
            None,
        )

        if rationale is not None and not isinstance(
            rationale,
            str,
        ):
            raise InvalidValueError(
                f"Path '{path_id}' rationale must be a string; "
                f"received {type(rationale).__name__}."
            )

    def _validate_ordered_actions(
        self,
        actions: Sequence[Any],
        state_ids: set[str],
        event_ids: set[str],
        directive_ids: set[str],
        owner: str,
        depth: int,
    ) -> None:
        """Validate one ordered AIR action stream recursively."""

        if depth > 64:
            raise InvalidValueError(
                f"{owner} exceeds the maximum conditional nesting "
                "depth of 64."
            )

        for index, action in enumerate(actions):
            action_owner = (
                f"{owner} ordered action[{index}]"
            )

            action_type = type(action).__name__

            if action_type == "StateAssignment":
                self._validate_state_assignment(
                    assignment=action,
                    state_ids=state_ids,
                    owner=action_owner,
                )
                continue

            if action_type == "EventEmission":
                self._validate_event_emission(
                    emission=action,
                    event_ids=event_ids,
                    state_ids=state_ids,
                    owner=action_owner,
                )
                continue

            if action_type == "DirectiveInvocation":
                self._validate_directive_invocation(
                    invocation=action,
                    directive_ids=directive_ids,
                    owner=action_owner,
                )
                continue
            if action_type == "AIRWhenAction":
                if not hasattr(
                    action,
                    "condition",
                ):
                    raise InvalidValueError(
                        f"{action_owner} is missing its condition."
                    )

                self._validate_expression(
                    getattr(
                        action,
                        "condition",
                    ),
                    state_ids=state_ids,
                    owner=f"{action_owner} condition",
                )

                branch_specs = (
                    (
                        "actions",
                        "when block",
                        True,
                    ),
                    (
                        "otherwise_actions",
                        "otherwise block",
                        False,
                    ),
                )

                for (
                    attribute_name,
                    branch_name,
                    required,
                ) in branch_specs:
                    if required and not hasattr(
                        action,
                        attribute_name,
                    ):
                        raise InvalidValueError(
                            f"{action_owner} is missing its "
                            f"{branch_name} action stream."
                        )

                    branch_actions = getattr(
                        action,
                        attribute_name,
                        (),
                    )

                    if isinstance(
                        branch_actions,
                        (str, bytes),
                    ):
                        raise InvalidValueError(
                            f"{action_owner} {branch_name} actions "
                            "must be a sequence of AIR actions."
                        )

                    try:
                        branch_actions = tuple(
                            branch_actions
                        )
                    except TypeError as exc:
                        raise InvalidValueError(
                            f"{action_owner} {branch_name} actions "
                            "must be iterable."
                        ) from exc

                    self._validate_ordered_actions(
                        actions=branch_actions,
                        state_ids=state_ids,
                        event_ids=event_ids,
                        directive_ids=directive_ids,
                        owner=(
                            f"{action_owner} "
                            f"{branch_name}"
                        ),
                        depth=depth + 1,
                    )

                continue

            raise InvalidValueError(
                f"{action_owner} has unsupported AIR action type "
                f"'{action_type}'."
            )

    def _validate_state_assignment(
        self,
        assignment: Any,
        state_ids: set[str],
        owner: str,
    ) -> None:
        """Validate one state assignment in either AIR representation."""

        state_id = self._required_string(
            getattr(
                assignment,
                "state",
                None,
            ),
            description=f"{owner} state reference",
        )

        if state_id not in state_ids:
            raise UndefinedReferenceError(
                f"{owner} assigns undefined state "
                f"'{state_id}'."
            )

        operation = self._required_string(
            getattr(
                assignment,
                "operation",
                None,
            ),
            description=f"{owner} assignment operation",
        )

        operation_types = {
            "set_int": INT,
            "add_int": INT,
            "set_bool": BOOL,
            "set_string": STRING,
            "set_float": FLOAT,
            "add_float": FLOAT,
        }
        operation_type = operation_types.get(
            operation
        )

        if operation_type is None:
            raise InvalidValueError(
                f"{owner} uses unsupported assignment operation "
                f"'{operation}'."
            )

        state_index = getattr(
            self,
            "_state_index",
            {},
        )
        state_definition = state_index.get(
            state_id
        )

        if state_definition is None:
            canonical = (
                state_id
                if state_id.startswith("state:")
                else f"state:{state_id}"
            )
            state_definition = state_index.get(
                canonical
            )

        if state_definition is not None:
            try:
                declared_type = resolve_builtin_type(
                    getattr(
                        state_definition,
                        "value_type",
                        INT,
                    )
                )
            except (TypeError, ValueError) as exc:
                raise InvalidValueError(
                    f"{owner} targets a state with invalid type metadata."
                ) from exc

            if declared_type is not operation_type:
                raise InvalidValueError(
                    f"{owner} uses {operation!r} for state {state_id!r} "
                    f"declared as {declared_type}."
                )

        if not hasattr(
            assignment,
            "value",
        ):
            raise InvalidValueError(
                f"{owner} contains an assignment without a value."
            )

        self._validate_expression(
            getattr(
                assignment,
                "value",
            ),
            state_ids=state_ids,
            owner=(
                f"{owner} assignment to state '{state_id}'"
            ),
        )

    def _validate_event_emission(
        self,
        emission: Any,
        event_ids: set[str],
        state_ids: set[str],
        owner: str,
    ) -> None:
        """Validate one event emission and all expression-valued facts."""

        event_id = self._required_string(
            getattr(
                emission,
                "event",
                None,
            ),
            description=f"{owner} event reference",
        )

        if event_id not in event_ids:
            raise UndefinedReferenceError(
                f"{owner} emits undefined event "
                f"'{event_id}'."
            )

        self._validate_emission_facts(
            emission=emission,
            state_ids=state_ids,
            owner=(
                f"{owner} emission of event '{event_id}'"
            ),
        )

    def _validate_directive_invocation(
        self,
        invocation: Any,
        directive_ids: set[str],
        owner: str,
    ) -> None:
        """Validate one directive invocation in old or new AIR layouts."""

        target = getattr(
            invocation,
            "target",
            None,
        )

        if target is None:
            target = getattr(
                invocation,
                "directive",
                None,
            )

        target = self._required_string(
            target,
            description=(
                f"{owner} directive invocation target"
            ),
        )

        if not self._directive_reference_exists(
            target,
            directive_ids,
        ):
            raise UndefinedReferenceError(
                f"{owner} invokes undefined directive "
                f"'{target}'."
            )

    # ======================================================================
    # Directives
    # ======================================================================

    def _validate_directives(
        self,
        directives: Iterable[Any],
        principal_index: Mapping[str, Any],
        authority_check_index: Mapping[str, Any],
        causal_decision_index: Mapping[str, Any],
    ) -> None:
        orders: set[int] = set()

        for directive in directives:
            directive_id = self._required_string(
                getattr(directive, "id", None),
                description="directive id",
            )

            self._required_string(
                getattr(directive, "name", None),
                description=(
                    f"directive '{directive_id}' name"
                ),
            )

            principal_id = self._required_string(
                getattr(directive, "principal", None),
                description=(
                    f"directive '{directive_id}' principal reference"
                ),
            )

            if principal_id not in principal_index:
                raise UndefinedReferenceError(
                    f"Directive '{directive_id}' references undefined "
                    f"principal '{principal_id}'."
                )

            authority_checks = tuple(
                getattr(
                    directive,
                    "authority_checks",
                    (),
                ) or ()
            )

            self._validate_unique_strings(
                authority_checks,
                owner=(
                    f"directive '{directive_id}' authority checks"
                ),
            )

            for check_id in authority_checks:
                check_id = self._required_string(
                    check_id,
                    description=(
                        f"directive '{directive_id}' authority-check "
                        "reference"
                    ),
                )

                if check_id not in authority_check_index:
                    raise UndefinedReferenceError(
                        f"Directive '{directive_id}' references undefined "
                        f"authority check '{check_id}'."
                    )

            causal_decisions = tuple(
                getattr(
                    directive,
                    "causal_decisions",
                    (),
                ) or ()
            )

            self._validate_unique_strings(
                causal_decisions,
                owner=(
                    f"directive '{directive_id}' causal decisions"
                ),
            )

            for decision_id in causal_decisions:
                decision_id = self._required_string(
                    decision_id,
                    description=(
                        f"directive '{directive_id}' causal-decision "
                        "reference"
                    ),
                )

                if decision_id not in causal_decision_index:
                    raise UndefinedReferenceError(
                        f"Directive '{directive_id}' references undefined "
                        f"causal decision '{decision_id}'."
                    )

            order = getattr(
                directive,
                "order",
                0,
            )

            if not isinstance(order, int):
                raise InvalidValueError(
                    f"Directive '{directive_id}' order must be an integer; "
                    f"received {type(order).__name__}."
                )

            if order in orders:
                raise DuplicateDefinitionError(
                    f"Duplicate directive order '{order}'."
                )

            orders.add(order)

    # ======================================================================
    # Requirements
    # ======================================================================

    def _validate_requirements(
        self,
        requirements: Iterable[Any],
        directive_index: Mapping[str, Any],
        principal_index: Mapping[str, Any],
        authority_index: Mapping[str, Any],
    ) -> None:
        for index, requirement in enumerate(requirements):
            owner = f"requirement[{index}]"

            self._required_string(
                getattr(requirement, "capability", None),
                description=f"{owner} capability",
            )

            principal_name = getattr(
                requirement,
                "principal",
                None,
            )

            if principal_name is not None:
                principal_name = self._required_string(
                    principal_name,
                    description=(
                        f"{owner} principal reference"
                    ),
                )

                if principal_name not in principal_index:
                    raise UndefinedReferenceError(
                        f"{owner} references undefined principal "
                        f"'{principal_name}'."
                    )

            authority_name = getattr(
                requirement,
                "authority",
                None,
            )

            if authority_name is not None:
                authority_name = self._reference_value(
                    authority_name,
                    description=(
                        f"{owner} authority reference"
                    ),
                )

                if authority_name not in authority_index:
                    raise UndefinedReferenceError(
                        f"{owner} references undefined authority "
                        f"'{authority_name}'."
                    )

            directive_name = getattr(
                requirement,
                "directive",
                None,
            )

            if directive_name is not None:
                directive_name = self._required_string(
                    directive_name,
                    description=(
                        f"{owner} directive reference"
                    ),
                )

                if not self._directive_reference_exists(
                    directive_name,
                    set(directive_index),
                ):
                    raise UndefinedReferenceError(
                        f"{owner} references undefined directive "
                        f"'{directive_name}'."
                    )



    # ======================================================================
    # AFP-P8 linked-program type closure
    # ======================================================================

    def _validate_linked_program_types(
        self,
        *,
        program: AIRProgram,
        state_index: Mapping[str, Any],
        function_index: Mapping[str, Any],
    ) -> None:
        """Validate known types after separately compiled AIR units are linked."""

        function_signatures = self._linked_function_signatures(
            function_index
        )
        state_types = self._linked_state_types(
            state_index
        )

        for state_id, state in state_index.items():
            expected = state_types[state_id]
            actual = self._infer_linked_expression_type(
                getattr(state, "initial"),
                owner=(
                    f"state '{state_id}' initial expression"
                ),
                identifiers=state_types,
                functions=function_signatures,
                require_complete_arguments=False,
            )

            if (
                actual is not None
                and actual is not expected
            ):
                raise InvalidValueError(
                    f"State '{state_id}' declares {expected} but its "
                    f"initializer produces {actual}."
                )

        for function_id, function in function_index.items():
            self._validate_linked_function_type(
                function_id=function_id,
                function=function,
                functions=function_signatures,
            )

        for decision in tuple(
            getattr(
                program,
                "causal_decisions",
                (),
            ) or ()
        ):
            for path in tuple(
                getattr(
                    decision,
                    "paths",
                    (),
                ) or ()
            ):
                actions = tuple(
                    getattr(
                        path,
                        "actions",
                        (),
                    ) or ()
                )

                if actions:
                    self._validate_linked_action_types(
                        actions=actions,
                        owner=f"path '{getattr(path, 'id', '<unknown>')}'",
                        state_types=state_types,
                        functions=function_signatures,
                    )
                    continue

                for assignment in tuple(
                    getattr(
                        path,
                        "assignments",
                        (),
                    ) or ()
                ):
                    self._validate_linked_assignment_type(
                        assignment=assignment,
                        owner=(
                            f"path '{getattr(path, 'id', '<unknown>')}'"
                        ),
                        state_types=state_types,
                        functions=function_signatures,
                    )

    def _linked_function_signatures(
        self,
        function_index: Mapping[str, Any],
    ) -> dict[str, FunctionSignature]:
        signatures: dict[str, FunctionSignature] = {}

        for function_id, function in function_index.items():
            function_name = self._required_string(
                getattr(function, "name", None),
                description=f"function '{function_id}' name",
            )
            parameters = tuple(
                getattr(
                    function,
                    "parameters",
                    (),
                ) or ()
            )

            try:
                signature = FunctionSignature(
                    name=function_name,
                    parameter_types=tuple(
                        getattr(
                            parameter,
                            "value_type",
                            None,
                        )
                        for parameter in parameters
                    ),
                    return_type=getattr(
                        function,
                        "return_type",
                        None,
                    ),
                )
            except (TypeError, ValueError) as exc:
                raise InvalidValueError(
                    f"Function '{function_id}' contains invalid type metadata."
                ) from exc

            for index, parameter_type in enumerate(
                signature.parameter_types
            ):
                if parameter_type is VOID:
                    raise InvalidValueError(
                        f"Function '{function_id}' parameter[{index}] "
                        "cannot use void."
                    )

            aliases = {
                function_id,
                function_name,
            }

            if function_id.startswith(
                "function:"
            ):
                aliases.add(
                    function_id[
                        len("function:"):
                    ]
                )

            for alias in aliases:
                existing = signatures.get(
                    alias
                )

                if (
                    existing is not None
                    and existing != signature
                ):
                    raise DuplicateDefinitionError(
                        f"Function type alias '{alias}' is ambiguous."
                    )

                signatures[
                    alias
                ] = signature

        return signatures

    def _linked_state_types(
        self,
        state_index: Mapping[str, Any],
    ) -> dict[str, ApexType]:
        state_types: dict[str, ApexType] = {}

        for state_id, state in state_index.items():
            try:
                value_type = resolve_builtin_type(
                    getattr(
                        state,
                        "value_type",
                        INT,
                    )
                )
            except (TypeError, ValueError) as exc:
                raise InvalidValueError(
                    f"State '{state_id}' contains invalid type metadata."
                ) from exc

            if value_type is VOID:
                raise InvalidValueError(
                    f"State '{state_id}' cannot use void."
                )

            aliases = {
                state_id,
            }

            if state_id.startswith(
                "state:"
            ):
                aliases.add(
                    state_id[
                        len("state:"):
                    ]
                )

            for alias in aliases:
                state_types[
                    alias
                ] = value_type

        return state_types

    def _infer_linked_expression_type(
        self,
        expression: Any,
        *,
        owner: str,
        identifiers: Mapping[str, Optional[ApexType]],
        functions: Mapping[str, FunctionSignature],
        require_complete_arguments: bool,
    ) -> Optional[ApexType]:
        try:
            return infer_expression_type_partial(
                expression,
                identifiers=identifiers,
                functions=functions,
                require_complete_arguments=require_complete_arguments,
            )
        except TypeInferenceError as error:
            raise InvalidValueError(
                f"{owner}: {error.message}"
            ) from error

    def _validate_linked_function_type(
        self,
        *,
        function_id: str,
        function: Any,
        functions: Mapping[str, FunctionSignature],
    ) -> None:
        function_name = self._required_string(
            getattr(function, "name", None),
            description=f"function '{function_id}' name",
        )
        signature = functions[
            function_id
        ]
        parameters = tuple(
            getattr(
                function,
                "parameters",
                (),
            ) or ()
        )
        identifiers: dict[
            str,
            Optional[ApexType],
        ] = {
            self._required_string(
                getattr(parameter, "name", None),
                description=(
                    f"function '{function_id}' parameter name"
                ),
            ): parameter_type
            for parameter, parameter_type in zip(
                parameters,
                signature.parameter_types,
            )
        }
        typed_function = (
            signature.return_type is not None
            or any(
                parameter_type is not None
                for parameter_type in signature.parameter_types
            )
        )

        self._validate_linked_function_statement_types(
            statements=self._function_body(
                function
            ),
            owner=f"function '{function_id}' body",
            function_name=function_name,
            identifiers=identifiers,
            expected_return=signature.return_type,
            functions=functions,
            require_complete=typed_function,
        )

    def _validate_linked_function_statement_types(
        self,
        *,
        statements: Sequence[Any],
        owner: str,
        function_name: str,
        identifiers: Mapping[str, Optional[ApexType]],
        expected_return: Optional[ApexType],
        functions: Mapping[str, FunctionSignature],
        require_complete: bool,
    ) -> None:
        scope = dict(
            identifiers
        )

        for index, statement in enumerate(
            tuple(statements)
        ):
            statement_owner = (
                f"{owner} statement[{index}]"
            )
            statement_type = type(
                statement
            ).__name__

            if statement_type == "AIRLocalBinding":
                local_name = self._required_string(
                    getattr(
                        statement,
                        "name",
                        None,
                    ),
                    description=(
                        f"{statement_owner} local name"
                    ),
                )
                scope[
                    local_name
                ] = self._infer_linked_expression_type(
                    getattr(
                        statement,
                        "expression",
                    ),
                    owner=(
                        f"{statement_owner} local "
                        f"'{local_name}' expression"
                    ),
                    identifiers=scope,
                    functions=functions,
                    require_complete_arguments=require_complete,
                )
                continue

            if statement_type in {
                "AIRFunctionReturn",
                "_LegacyFunctionReturn",
            }:
                actual = self._infer_linked_expression_type(
                    getattr(
                        statement,
                        "expression",
                    ),
                    owner=(
                        f"{statement_owner} return expression"
                    ),
                    identifiers=scope,
                    functions=functions,
                    require_complete_arguments=require_complete,
                )

                if expected_return is None:
                    continue

                if actual is None:
                    raise InvalidValueError(
                        f"Function '{function_name}' declares return type "
                        f"{expected_return}, but its linked return type "
                        "cannot be determined."
                    )

                if actual is not expected_return:
                    raise InvalidValueError(
                        f"Function '{function_name}' declares return type "
                        f"{expected_return}, but returns {actual}."
                    )
                continue

            if statement_type == "AIRFunctionWhen":
                condition_type = self._infer_linked_expression_type(
                    getattr(
                        statement,
                        "condition",
                    ),
                    owner=(
                        f"{statement_owner} condition"
                    ),
                    identifiers=scope,
                    functions=functions,
                    require_complete_arguments=require_complete,
                )

                if (
                    condition_type is not None
                    and condition_type is not BOOL
                ):
                    raise InvalidValueError(
                        f"{statement_owner} condition requires bool; "
                        f"received {condition_type}."
                    )

                if (
                    require_complete
                    and condition_type is None
                ):
                    raise InvalidValueError(
                        f"{statement_owner} condition type cannot be "
                        "determined in a typed function."
                    )

                self._validate_linked_function_statement_types(
                    statements=tuple(
                        getattr(
                            statement,
                            "actions",
                            (),
                        ) or ()
                    ),
                    owner=(
                        f"{statement_owner} when block"
                    ),
                    function_name=function_name,
                    identifiers=dict(scope),
                    expected_return=expected_return,
                    functions=functions,
                    require_complete=require_complete,
                )
                self._validate_linked_function_statement_types(
                    statements=tuple(
                        getattr(
                            statement,
                            "otherwise_actions",
                            (),
                        ) or ()
                    ),
                    owner=(
                        f"{statement_owner} otherwise block"
                    ),
                    function_name=function_name,
                    identifiers=dict(scope),
                    expected_return=expected_return,
                    functions=functions,
                    require_complete=require_complete,
                )

    def _validate_linked_action_types(
        self,
        *,
        actions: Sequence[Any],
        owner: str,
        state_types: Mapping[str, ApexType],
        functions: Mapping[str, FunctionSignature],
    ) -> None:
        for index, action in enumerate(
            tuple(actions)
        ):
            action_owner = (
                f"{owner} action[{index}]"
            )
            action_type = type(
                action
            ).__name__

            if action_type == "StateAssignment":
                self._validate_linked_assignment_type(
                    assignment=action,
                    owner=action_owner,
                    state_types=state_types,
                    functions=functions,
                )
                continue

            if action_type == "AIRWhenAction":
                condition_type = self._infer_linked_expression_type(
                    getattr(
                        action,
                        "condition",
                    ),
                    owner=(
                        f"{action_owner} condition"
                    ),
                    identifiers=state_types,
                    functions=functions,
                    require_complete_arguments=False,
                )

                if (
                    condition_type is not None
                    and condition_type is not BOOL
                ):
                    raise InvalidValueError(
                        f"{action_owner} condition requires bool; "
                        f"received {condition_type}."
                    )

                self._validate_linked_action_types(
                    actions=tuple(
                        getattr(
                            action,
                            "actions",
                            (),
                        ) or ()
                    ),
                    owner=(
                        f"{action_owner} when block"
                    ),
                    state_types=state_types,
                    functions=functions,
                )
                self._validate_linked_action_types(
                    actions=tuple(
                        getattr(
                            action,
                            "otherwise_actions",
                            (),
                        ) or ()
                    ),
                    owner=(
                        f"{action_owner} otherwise block"
                    ),
                    state_types=state_types,
                    functions=functions,
                )
                continue

            if action_type == "EventEmission":
                for fact in tuple(
                    getattr(
                        action,
                        "facts",
                        (),
                    ) or ()
                ):
                    self._infer_linked_expression_type(
                        getattr(
                            fact,
                            "value",
                            None,
                        ),
                        owner=(
                            f"{action_owner} event fact"
                        ),
                        identifiers=state_types,
                        functions=functions,
                        require_complete_arguments=False,
                    )

    def _validate_linked_assignment_type(
        self,
        *,
        assignment: Any,
        owner: str,
        state_types: Mapping[str, ApexType],
        functions: Mapping[str, FunctionSignature],
    ) -> None:
        operation_types = {
            "set_int": INT,
            "add_int": INT,
            "set_bool": BOOL,
            "set_string": STRING,
            "set_float": FLOAT,
            "add_float": FLOAT,
        }
        operation = getattr(
            assignment,
            "operation",
            None,
        )
        expected = operation_types.get(
            operation
        )

        if expected is None:
            return

        actual = self._infer_linked_expression_type(
            getattr(
                assignment,
                "value",
            ),
            owner=(
                f"{owner} assignment expression"
            ),
            identifiers=state_types,
            functions=functions,
            require_complete_arguments=False,
        )

        if (
            actual is not None
            and actual is not expected
        ):
            raise InvalidValueError(
                f"{owner} uses {operation!r}, which requires {expected}; "
                f"its expression produces {actual}."
            )

    # ======================================================================
    # AIR expressions
    # ======================================================================

    def _validate_expression(
        self,
        expression: Any,
        state_ids: set[str],
        owner: str,
        local_names: frozenset[str] = frozenset(),
        allow_state_references: bool = True,
    ) -> None:
        """
        Validate one AIR expression recursively.

        P7 extends identifier resolution with immutable function parameters and
        adds linked pure-function calls. Dispatch remains class-name based to
        preserve the validator's independence from expression-module imports.
        """

        expression_type = type(expression).__name__

        # Hand-authored and legacy AIR may retain primitive literal values
        # instead of wrapping them in AIR literal expression objects.
        # Preserve exact Python type identity so bool is not treated as int.
        if type(expression) in {
            int,
            bool,
            str,
            float,
        }:
            return

        if expression_type == "AIRIntegerLiteral":
            value = getattr(expression, "value", None)

            if isinstance(value, bool) or not isinstance(value, int):
                raise InvalidValueError(
                    f"{owner} must contain an integer literal value; "
                    f"received {type(value).__name__}."
                )

            return

        if expression_type == "AIRFloatLiteral":
            value = getattr(expression, "value", None)

            if type(value) is not float:
                raise InvalidValueError(
                    f"{owner} must contain a float literal value; "
                    f"received {type(value).__name__}."
                )

            return

        if expression_type == "AIRStringLiteral":
            value = getattr(expression, "value", None)

            if not isinstance(value, str):
                raise InvalidValueError(
                    f"{owner} must contain a string literal value; "
                    f"received {type(value).__name__}."
                )

            return

        if expression_type == "AIRBooleanLiteral":
            value = getattr(expression, "value", None)

            if not isinstance(value, bool):
                raise InvalidValueError(
                    f"{owner} must contain a boolean literal value; "
                    f"received {type(value).__name__}."
                )

            return

        if expression_type == "AIRIdentifierReference":
            reference = self._required_string(
                getattr(expression, "name", None),
                description=f"{owner} identifier reference",
            )

            if reference in local_names:
                return

            if (
                allow_state_references
                and self._state_reference_exists(
                    reference,
                    state_ids,
                )
            ):
                return

            if allow_state_references:
                raise UndefinedReferenceError(
                    f"{owner} references undefined state or local "
                    f"'{reference}'."
                )

            raise UndefinedReferenceError(
                f"{owner} references undefined function-local identifier "
                f"'{reference}'."
            )

        if expression_type == "AIRUnaryExpression":
            operator = self._required_string(
                getattr(expression, "operator", None),
                description=f"{owner} unary operator",
            )

            if operator not in {"+", "-", "not"}:
                raise InvalidValueError(
                    f"{owner} uses unsupported unary operator "
                    f"'{operator}'."
                )

            if not hasattr(expression, "operand"):
                raise InvalidValueError(
                    f"{owner} is missing its unary operand."
                )

            self._validate_expression(
                getattr(expression, "operand"),
                state_ids=state_ids,
                owner=f"{owner} operand",
                local_names=local_names,
                allow_state_references=allow_state_references,
            )

            return

        if expression_type == "AIRBinaryExpression":
            operator = self._required_string(
                getattr(expression, "operator", None),
                description=f"{owner} binary operator",
            )

            supported_operators = {
                "+",
                "-",
                "*",
                "/",
                "%",
                "==",
                "!=",
                "<",
                "<=",
                ">",
                ">=",
                "and",
                "or",
            }

            if operator not in supported_operators:
                raise InvalidValueError(
                    f"{owner} uses unsupported binary operator "
                    f"'{operator}'."
                )

            if not hasattr(expression, "left"):
                raise InvalidValueError(
                    f"{owner} is missing its left operand."
                )

            if not hasattr(expression, "right"):
                raise InvalidValueError(
                    f"{owner} is missing its right operand."
                )

            self._validate_expression(
                getattr(expression, "left"),
                state_ids=state_ids,
                owner=f"{owner} left operand",
                local_names=local_names,
                allow_state_references=allow_state_references,
            )

            self._validate_expression(
                getattr(expression, "right"),
                state_ids=state_ids,
                owner=f"{owner} right operand",
                local_names=local_names,
                allow_state_references=allow_state_references,
            )

            return

        if expression_type == "AIRCallExpression":
            target = self._required_string(
                getattr(expression, "target", None),
                description=f"{owner} function call target",
            )
            function_index = getattr(
                self,
                "_function_index",
                {},
            )
            resolved_target = self._resolve_function_reference(
                target,
                function_index,
            )

            if resolved_target is None:
                raise UndefinedReferenceError(
                    f"{owner} calls undefined function '{target}'."
                )

            raw_arguments = getattr(
                expression,
                "arguments",
                (),
            )

            if isinstance(raw_arguments, (str, bytes)):
                raise InvalidValueError(
                    f"{owner} function call arguments must be a sequence "
                    "of AIR expressions."
                )

            try:
                arguments = tuple(raw_arguments or ())
            except TypeError as exc:
                raise InvalidValueError(
                    f"{owner} function call arguments must be iterable."
                ) from exc

            function = function_index[resolved_target]
            parameters = tuple(
                getattr(function, "parameters", ()) or ()
            )

            if len(arguments) != len(parameters):
                display_name = self._function_display_name(
                    resolved_target,
                    function_index,
                )
                raise InvalidValueError(
                    f"{owner} calls function '{display_name}' with "
                    f"{len(arguments)} argument(s); expected "
                    f"{len(parameters)}."
                )

            for index, argument in enumerate(arguments):
                self._validate_expression(
                    argument,
                    state_ids=state_ids,
                    owner=f"{owner} argument[{index}]",
                    local_names=local_names,
                    allow_state_references=allow_state_references,
                )

            return

        raise InvalidValueError(
            f"{owner} has unsupported AIR expression type "
            f"'{expression_type}'."
        )

    def _validate_emission_facts(
        self,
        emission: Any,
        state_ids: set[str],
        owner: str,
    ) -> None:
        """Validate expression-valued facts attached to an event emission."""

        emission_facts = getattr(
            emission,
            "facts",
            (),
        ) or ()

        if isinstance(emission_facts, Mapping):
            fact_items = tuple(emission_facts.items())
        else:
            fact_items = []

            for index, fact in enumerate(emission_facts):
                if isinstance(fact, tuple) and len(fact) == 2:
                    fact_items.append(fact)
                    continue

                fact_name = None

                for attribute in (
                    "key",
                    "name",
                    "label",
                ):
                    candidate = getattr(
                        fact,
                        attribute,
                        None,
                    )

                    if candidate is not None:
                        fact_name = candidate
                        break

                if fact_name is None:
                    fact_name = f"fact[{index}]"

                missing = object()
                fact_value = getattr(
                    fact,
                    "value",
                    missing,
                )

                if fact_value is missing:
                    fact_value = getattr(
                        fact,
                        "expression",
                        missing,
                    )

                if fact_value is missing:
                    raise InvalidValueError(
                        f"{owner} {fact_name!r} has no value."
                    )

                fact_items.append(
                    (fact_name, fact_value)
                )

        for fact_name, fact_value in fact_items:
            normalized_name = self._required_string(
                fact_name,
                description=f"{owner} fact name",
            )

            self._validate_expression(
                fact_value,
                state_ids=state_ids,
                owner=(
                    f"{owner} fact '{normalized_name}' expression"
                ),
            )

    def _state_reference_exists(
        self,
        reference: str,
        state_ids: set[str],
    ) -> bool:
        """Accept a canonical state ID or a plain state name."""

        if reference in state_ids:
            return True

        canonical = f"state:{reference}"

        return canonical in state_ids

    def _resolve_function_reference(
        self,
        reference: str,
        function_index: Mapping[str, Any],
    ) -> Any:
        """Resolve canonical IDs and plain function names to one function ID."""

        if reference in function_index:
            return reference

        canonical = (
            reference
            if reference.startswith("function:")
            else f"function:{reference}"
        )

        if canonical in function_index:
            return canonical

        for function_id, function in function_index.items():
            name = getattr(function, "name", None)

            if isinstance(name, str) and name.strip() == reference:
                return function_id

        return None

    # ======================================================================
    # Helpers
    # ======================================================================

    def _required_string(
        self,
        value: Any,
        description: str,
    ) -> str:
        if not isinstance(value, str):
            raise InvalidValueError(
                f"{description} must be a string; "
                f"received {type(value).__name__}."
            )

        normalized = value.strip()

        if not normalized:
            raise InvalidValueError(
                f"{description} cannot be empty."
            )

        return normalized

    def _declaration_name_or_id(
        self,
        value: Any,
        description: str,
    ) -> str:
        name = getattr(
            value,
            "name",
            None,
        )

        if name is not None:
            return self._required_string(
                name,
                description=f"{description} name",
            )

        identifier = getattr(
            value,
            "id",
            None,
        )

        return self._required_string(
            identifier,
            description=f"{description} id",
        )

    def _reference_value(
        self,
        value: Any,
        description: str,
    ) -> str:
        """
        Convert a string or lightweight reference object into its key.

        Supported object fields:

        - authority
        - role
        - name
        - id
        """

        if isinstance(value, str):
            return self._required_string(
                value,
                description=description,
            )

        for attribute in (
            "authority",
            "role",
            "name",
            "id",
        ):
            candidate = getattr(
                value,
                attribute,
                None,
            )

            if candidate is not None:
                return self._required_string(
                    candidate,
                    description=description,
                )

        raise InvalidValueError(
            f"{description} must be a string or reference object; "
            f"received {type(value).__name__}."
        )

    def _is_inline_authority(
        self,
        value: Any,
    ) -> bool:
        """
        Return True when an object represents an inline authority grant.

        PrincipalAuthority objects commonly contain capability information
        directly instead of referencing a named DirectiveAuthority.
        """

        return getattr(
            value,
            "capability",
            None,
        ) is not None

    def _directive_reference_exists(
        self,
        reference: str,
        directive_ids: set[str],
    ) -> bool:
        """
        Accept either a canonical directive ID or a plain directive name.

        Examples:

            directive:Hello
            Hello
        """

        if reference in directive_ids:
            return True

        canonical = f"directive:{reference}"

        return canonical in directive_ids

    def _validate_unique_strings(
        self,
        values: Sequence[Any],
        owner: str,
    ) -> None:
        seen: set[str] = set()

        for value in values:
            normalized = self._required_string(
                value,
                description=f"{owner} value",
            )

            if normalized in seen:
                raise DuplicateDefinitionError(
                    f"{owner} contains duplicate reference "
                    f"'{normalized}'."
                )

            seen.add(normalized)

    def _validate_unique_references(
        self,
        values: Sequence[Any],
        owner: str,
        value_kind: str,
    ) -> None:
        seen: set[str] = set()

        for value in values:
            reference = self._reference_value(
                value,
                description=(
                    f"{owner} {value_kind} reference"
                ),
            )

            if reference in seen:
                raise DuplicateDefinitionError(
                    f"{owner} contains duplicate {value_kind} "
                    f"reference '{reference}'."
                )

            seen.add(reference)

    def _validate_unique_attribute(
        self,
        values: Sequence[Any],
        attribute: str,
        owner: str,
    ) -> None:
        seen: set[str] = set()

        for value in values:
            identifier = self._required_string(
                getattr(value, attribute, None),
                description=f"{owner} {attribute}",
            )

            if identifier in seen:
                raise DuplicateDefinitionError(
                    f"{owner} contains duplicate {attribute} "
                    f"'{identifier}'."
                )

            seen.add(identifier)


# ============================================================================
# Functional entry point
# ============================================================================


def validate_runtime(
    program: AIRProgram,
) -> VerifiedAIRProgram:
    """Validate an AIRProgram using the default runtime validator."""

    return RuntimeValidator().validate(program)


__all__ = [
    "RuntimeValidationError",
    "InvalidProgramError",
    "InvalidValueError",
    "DuplicateDefinitionError",
    "UndefinedReferenceError",
    "VerifiedAIRProgram",
    "RuntimeValidator",
    "validate_runtime",
]