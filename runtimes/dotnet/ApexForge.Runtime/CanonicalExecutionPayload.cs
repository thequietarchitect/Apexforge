using System.Security.Cryptography;
using System.Text;

namespace ApexForge.Runtime;

public sealed record CanonicalExecutionPayload(IReadOnlyList<CanonicalExecutionValue> Values)
{
    public void Validate()
    {
        if (Values is null)
        {
            throw new InvalidOperationException("Canonical payload values are required.");
        }

        var names = new HashSet<string>(StringComparer.Ordinal);
        foreach (var value in Values)
        {
            value.Validate();
            if (!names.Add(value.Name))
            {
                throw new InvalidOperationException("Canonical payload contains duplicate value names.");
            }
        }
    }

    public string CanonicalForm()
    {
        Validate();
        return string.Join("\n", Values.OrderBy(value => value.Name, StringComparer.Ordinal).Select(value => value.CanonicalForm()));
    }

    public string Fingerprint()
    {
        var bytes = Encoding.UTF8.GetBytes(CanonicalForm());
        return Convert.ToHexString(SHA256.HashData(bytes));
    }
}
