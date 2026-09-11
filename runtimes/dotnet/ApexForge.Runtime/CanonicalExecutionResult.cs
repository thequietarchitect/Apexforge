using System.Security.Cryptography;
using System.Text;

namespace ApexForge.Runtime;

public sealed record CanonicalExecutionResult(
    string InputFingerprint,
    string Status,
    CanonicalExecutionPayload Outputs)
{
    public void Validate()
    {
        if (InputFingerprint.Length != 64 || !InputFingerprint.All(ch => (ch >= '0' && ch <= '9') || (ch >= 'A' && ch <= 'F')))
        {
            throw new InvalidOperationException("Canonical input fingerprint is invalid.");
        }

        if (Status is not ("SUCCESS" or "FAILURE"))
        {
            throw new InvalidOperationException("Canonical result status is invalid.");
        }

        Outputs.Validate();
    }

    public string CanonicalForm()
    {
        Validate();
        return $"{InputFingerprint}\n{Status}\n{Outputs.Fingerprint()}";
    }

    public string Fingerprint()
    {
        var bytes = Encoding.UTF8.GetBytes(CanonicalForm());
        return Convert.ToHexString(SHA256.HashData(bytes));
    }
}
