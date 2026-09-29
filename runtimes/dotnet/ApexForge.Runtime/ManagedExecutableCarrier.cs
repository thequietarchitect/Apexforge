using System.Collections.Generic;
using System.Numerics;

namespace ApexForge.Runtime;

public abstract record ManagedExecutableExpression
{
}

public sealed record ManagedIntegerLiteral(BigInteger Value) : ManagedExecutableExpression;

public sealed record ManagedFloatLiteral(double Value) : ManagedExecutableExpression;

public sealed record ManagedStringLiteral(string Value) : ManagedExecutableExpression;

public sealed record ManagedBooleanLiteral(bool Value) : ManagedExecutableExpression;

public sealed record ManagedIdentifierReference(string Name) : ManagedExecutableExpression;

public sealed record ManagedUnaryExpression(
    string Operator,
    ManagedExecutableExpression Operand
) : ManagedExecutableExpression;

public sealed record ManagedBinaryExpression(
    ManagedExecutableExpression Left,
    string Operator,
    ManagedExecutableExpression Right
) : ManagedExecutableExpression;

public sealed record ManagedCallExpression(
    string Target,
    IReadOnlyList<ManagedExecutableExpression> Arguments,
    IReadOnlyList<ManagedGenericTypeLike> TypeArguments
) : ManagedExecutableExpression;

public abstract record ManagedTypeReference;

public interface ManagedGenericTypeLike
{
}

public interface ManagedTypeLike : ManagedGenericTypeLike
{
}

public interface ManagedTypeIdentity
{
}

public sealed record ManagedNamedTypeReference(string Name)
    : ManagedTypeReference, ManagedTypeLike;

public sealed record ManagedApexTypeReference(
    string Name,
    IReadOnlyList<ManagedApexTypeReference> Arguments
) : ManagedTypeReference, ManagedTypeLike, ManagedTypeIdentity;

public sealed record ManagedTypeVariableReference(
    string Name,
    string Owner,
    IReadOnlyList<ManagedConstraintReference> Constraints
) : ManagedTypeReference, ManagedGenericTypeLike, ManagedTypeIdentity;

public abstract record ManagedConstraintReference
{
}

public sealed record ManagedNamedConstraintReference(string Name)
    : ManagedConstraintReference;

public sealed record ManagedApexTypeConstraintReference(
    string Name,
    string Description
) : ManagedConstraintReference;

public sealed record ManagedFunctionParameter(
    string Name,
    ManagedGenericTypeLike? ValueType
);

public abstract record ManagedFunctionStatement
{
}

public sealed record ManagedLocalBinding(
    string Name,
    ManagedExecutableExpression Expression
) : ManagedFunctionStatement;

public sealed record ManagedFunctionReturn(
    ManagedExecutableExpression Expression
) : ManagedFunctionStatement;

public sealed record ManagedFunctionWhen(
    ManagedExecutableExpression Condition,
    IReadOnlyList<ManagedFunctionStatement> Actions,
    IReadOnlyList<ManagedFunctionStatement> OtherwiseActions
) : ManagedFunctionStatement;

public sealed record ManagedExecutableFunction(
    string Id,
    string Name,
    IReadOnlyList<ManagedFunctionParameter> Parameters,
    ManagedExecutableExpression? ReturnExpression,
    int Order,
    IReadOnlyList<ManagedLocalBinding> LocalBindings,
    IReadOnlyList<ManagedFunctionStatement> Body,
    ManagedGenericTypeLike? ReturnType,
    IReadOnlyList<ManagedTypeVariableReference> TypeParameters
);
