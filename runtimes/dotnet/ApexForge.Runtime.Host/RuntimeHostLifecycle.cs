namespace ApexForge.Runtime.Host;

public enum RuntimeHostLifecycleState
{
    Created = 0,
    Starting = 1,
    Ready = 2,
    Quiescing = 3,
    Stopped = 4,
    Failed = 5
}

public sealed class RuntimeHostLifecycle
{
    public RuntimeHostLifecycleState State { get; private set; } = RuntimeHostLifecycleState.Created;

    public void BeginStartup()
    {
        Require(RuntimeHostLifecycleState.Created);
        State = RuntimeHostLifecycleState.Starting;
    }

    public void MarkReady()
    {
        Require(RuntimeHostLifecycleState.Starting);
        State = RuntimeHostLifecycleState.Ready;
    }

    public void BeginShutdown()
    {
        Require(RuntimeHostLifecycleState.Ready);
        State = RuntimeHostLifecycleState.Quiescing;
    }

    public void MarkStopped()
    {
        Require(RuntimeHostLifecycleState.Quiescing);
        State = RuntimeHostLifecycleState.Stopped;
    }

    public void MarkFailed()
    {
        if (State is RuntimeHostLifecycleState.Stopped)
        {
            throw new InvalidOperationException("A stopped host cannot transition to failed.");
        }

        State = RuntimeHostLifecycleState.Failed;
    }

    private void Require(RuntimeHostLifecycleState expected)
    {
        if (State != expected)
        {
            throw new InvalidOperationException(
                $"Invalid runtime-host lifecycle transition: expected {expected}, actual {State}.");
        }
    }
}
