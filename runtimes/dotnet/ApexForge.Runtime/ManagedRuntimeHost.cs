namespace ApexForge.Runtime;

public sealed class ManagedRuntimeHost
{
    public string TargetId => RuntimeIdentity.TargetId;

    public bool DefinesLanguageSemantics => RuntimeIdentity.DefinesLanguageSemantics;

    public void ValidateContract(CanonicalExecutionContract contract)
    {
        if (!contract.IsCompatible)
        {
            throw new InvalidOperationException("Canonical execution contract mismatch.");
        }
    }

    public CanonicalExecutionEnvelope Admit(CanonicalExecutionEnvelope envelope)
    {
        envelope.Validate();
        ValidateContract(envelope.Contract);
        return envelope;
    }
}
