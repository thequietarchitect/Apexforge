using ApexForge.Runtime;
using ApexForge.Runtime.Host;

var lifecycle = new RuntimeHostLifecycle();

try
{
    lifecycle.BeginStartup();

    var host = new ManagedRuntimeHost();

    lifecycle.MarkReady();
    Console.WriteLine(
        $"APEXFORGE_RUNTIME_HOST|TARGET={host.TargetId}|SEMANTICS={host.DefinesLanguageSemantics}|STATE={lifecycle.State}");

    lifecycle.BeginShutdown();
    lifecycle.MarkStopped();

    Console.WriteLine($"APEXFORGE_RUNTIME_HOST|STATE={lifecycle.State}");
}
catch
{
    lifecycle.MarkFailed();
    Console.Error.WriteLine($"APEXFORGE_RUNTIME_HOST|STATE={lifecycle.State}");
    return 1;
}

return 0;
