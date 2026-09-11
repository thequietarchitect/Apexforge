using ApexForge.Runtime;

var host = new ManagedRuntimeHost();
var validJson = """{"VerifiedAirOwner":"air.model.VerifiedAIRProgram","ExecutionPlanOwner":"workflow.air_runner.RegistryExecutionPlan","ProgramFingerprint":"P12-1C-CANONICAL"}""";
var accepted = host.Admit(CanonicalExecutionEnvelope.FromJson(validJson));
if (accepted.ProgramFingerprint != "P12-1C-CANONICAL")
{
    return 1;
}
Console.WriteLine("MANAGED_VALID_ENVELOPE_ACCEPTED=PASS");

var mismatchRejected = false;
try
{
    host.Admit(new CanonicalExecutionEnvelope(
        "wrong.owner",
        "workflow.air_runner.RegistryExecutionPlan",
        "P12-1C-MISMATCH"));
}
catch (InvalidOperationException)
{
    mismatchRejected = true;
}
if (!mismatchRejected)
{
    return 2;
}
Console.WriteLine("MANAGED_OWNERSHIP_MISMATCH_REJECTED=PASS");
Console.WriteLine("P12_1C_MANAGED_ENVELOPE_ADMISSION=PASS");

var payload = new CanonicalExecutionPayload(new CanonicalExecutionValue[]
{
    new("message", "UTF8", "hello"),
    new("enabled", "BOOL", "true"),
    new("count", "I64", "42"),
});
var admittedPayload = host.AdmitPayload(payload);
var payloadFingerprint = admittedPayload.Fingerprint();
Console.WriteLine($"MANAGED_PAYLOAD_FINGERPRINT={payloadFingerprint}");
Console.WriteLine("MANAGED_VALID_PAYLOAD_ACCEPTED=PASS");

var noncanonicalRejected = false;
try
{
    host.AdmitPayload(new CanonicalExecutionPayload(new CanonicalExecutionValue[]
    {
        new("count", "I64", "0042"),
    }));
}
catch (InvalidOperationException)
{
    noncanonicalRejected = true;
}
if (!noncanonicalRejected)
{
    return 3;
}
Console.WriteLine("MANAGED_NONCANONICAL_VALUE_REJECTED=PASS");
Console.WriteLine("P12_1D_MANAGED_PAYLOAD_VALUE_ADMISSION=PASS");
return 0;
