using System.Text.Json;

namespace ApexForge.Runtime;

public sealed record CanonicalExecutionEnvelope(
    string VerifiedAirOwner,
    string ExecutionPlanOwner,
    string ProgramFingerprint)
{
    public CanonicalExecutionContract Contract => new(VerifiedAirOwner, ExecutionPlanOwner);

    public void Validate()
    {
        if (!Contract.IsCompatible)
        {
            throw new InvalidOperationException("Canonical execution ownership mismatch.");
        }

        if (string.IsNullOrWhiteSpace(ProgramFingerprint))
        {
            throw new InvalidOperationException("Program fingerprint is required.");
        }
    }

    public static CanonicalExecutionEnvelope FromJson(string json)
    {
        var value = JsonSerializer.Deserialize<CanonicalExecutionEnvelope>(json, new JsonSerializerOptions { PropertyNameCaseInsensitive = true });

        if (value is null)
        {
            throw new InvalidOperationException("Canonical execution envelope is empty.");
        }

        value.Validate();
        return value;
    }
}
