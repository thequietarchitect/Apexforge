namespace ApexForge.Runtime;

public readonly record struct CanonicalExecutionContract(string VerifiedAirOwner, string ExecutionPlanOwner)
{
    public static CanonicalExecutionContract Required { get; } = new(
        RuntimeIdentity.CanonicalVerifiedAirOwner,
        RuntimeIdentity.CanonicalExecutionPlanOwner);

    public bool IsCompatible =>
        string.Equals(VerifiedAirOwner, RuntimeIdentity.CanonicalVerifiedAirOwner, StringComparison.Ordinal)
        && string.Equals(ExecutionPlanOwner, RuntimeIdentity.CanonicalExecutionPlanOwner, StringComparison.Ordinal);
}
