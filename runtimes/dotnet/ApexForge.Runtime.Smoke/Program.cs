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
return 0;
