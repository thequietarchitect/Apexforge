"""
Top-level ApexForge execution pipeline.

This module coordinates the major ApexForge phases:

    Source
        ↓
    Lexer
        ↓
    Parser
        ↓
    AST
        ↓
    Compiler
        ↓
    AIRProgram
        ↓
    Runtime validation
        ↓
    VerifiedAIRProgram
        ↓
    Runtime execution
        ↓
    ExecutionResult

The pipeline coordinates subsystems but does not implement their internal
logic.
"""

from __future__ import annotations

from typing import Any

# Adjust these imports to match your project.
from language.compiler import compile_directive
from runtime.engine import RuntimeEngine
from language.validation.runtime_validator import (
    RuntimeValidator,
    VerifiedAIRProgram,
)

# Replace these imports with your actual lexer and parser entry points.
from language.lexer import lex
from language.parser import parse


class ExecutionPipeline:
    """
    Coordinates compilation, validation, and runtime execution.

    Dependencies may be injected for testing or customization.
    """

    def __init__(
        self,
        runtime: RuntimeEngine | None = None,
        validator: RuntimeValidator | None = None,
    ) -> None:
        self._runtime = runtime or RuntimeEngine()
        self._validator = validator or RuntimeValidator()

    def compile_source(
        self,
        source: str,
    ):
        """
        Convert ApexForge source text into an AIRProgram.
        """

        if not isinstance(source, str):
            raise TypeError(
                "ExecutionPipeline.compile_source requires a string; "
                f"received {type(source).__name__}."
            )
        node = parse(source)

        return compile_directive(node)

    def verify_source(
        self,
        source: str,
    ) -> VerifiedAIRProgram:
        """
        Compile and validate source without executing it.
        """

        program = self.compile_source(source)

        return self._validator.validate(program)

    def execute_source(
        self,
        source: str,
        context: Any,
    ):
        """
        Compile, validate, and execute ApexForge source.
        """

        verified = self.verify_source(source)

        return self._runtime.execute(
            verified,
            context,
        )

    def execute_node(
        self,
        node: Any,
        context: Any,
    ):
        """
        Compile, validate, and execute an already parsed directive node.
        """

        program = compile_directive(node)
        verified = self._validator.validate(program)

        return self._runtime.execute(
            verified,
            context,
        )

    def execute_program(
        self,
        program: Any,
        context: Any,
    ):
        """
        Validate and execute an already compiled AIRProgram.
        """

        verified = self._validator.validate(program)

        return self._runtime.execute(
            verified,
            context,
        )