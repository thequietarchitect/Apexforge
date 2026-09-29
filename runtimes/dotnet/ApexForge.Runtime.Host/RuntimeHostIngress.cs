using ApexForge.Runtime;

namespace ApexForge.Runtime.Host;

public sealed class RuntimeHostIngress
{
    private readonly ManagedRuntimeHost _runtimeHost;

    public RuntimeHostIngress(ManagedRuntimeHost runtimeHost)
    {
        ArgumentNullException.ThrowIfNull(runtimeHost);
        _runtimeHost = runtimeHost;
    }

    public TargetNeutralLoweringHandoff Admit(TargetNeutralLoweringHandoff handoff)
    {
        return _runtimeHost.AdmitTargetNeutralHandoff(handoff);
    }
}
