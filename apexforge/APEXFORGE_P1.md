# ApexForge Prototype 1

**Milestone ID:** AFP-P1  
**Status:** Frozen baseline  
**Runtime architecture:** Source-to-execution pipeline

## Purpose

AFP-P1 establishes the first complete ApexForge language pipeline. It
demonstrates that ApexForge source code can be parsed, compiled into AIR,
validated for runtime safety, and executed through the runtime engine.

## Canonical pipeline

Source
→ Lexer
→ Parser
→ AST
→ Compiler
→ AIRProgram
→ RuntimeValidator
→ VerifiedAIRProgram
→ RuntimeEngine
→ ExecutionResult

## Frozen capabilities

- Directive parsing
- State declarations
- Event declarations
- Causal decisions
- Weighted causal paths
- State assignments
- Event emissions
- Directive invocations
- Requirements
- Authorities
- Principals
- Roles
- Authority checks
- Runtime validation
- Runtime tracing
- Diagnostics
- Execution results

## Architectural boundaries

### Parser

Converts ApexForge source into AST nodes.

### Compiler

Converts AST nodes into AIRProgram.

### RuntimeValidator

Validates AIR structure and references and returns VerifiedAIRProgram.

### RuntimeEngine

Accepts only VerifiedAIRProgram and produces ExecutionResult.

### ExecutionPipeline

Coordinates parsing, compilation, validation, and execution.

## Stability rule

Future changes must not break the AFP-P1 regression suite.

## Deferred features

The following are not part of AFP-P1:

- Module imports
- User-defined functions
- Local variables
- General expressions
- Pattern matching
- REPL
- Optimization passes
- Host API bridge