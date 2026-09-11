using System.Globalization;
using System.Text;

namespace ApexForge.Runtime;

public sealed record CanonicalExecutionValue(string Name, string Representation, string Data)
{
    public void Validate()
    {
        if (string.IsNullOrWhiteSpace(Name))
        {
            throw new InvalidOperationException("Canonical value name is required.");
        }

        switch (Representation)
        {
            case "BOOL":
                if (Data is not ("true" or "false"))
                {
                    throw new InvalidOperationException("Canonical BOOL representation is invalid.");
                }
                break;
            case "I64":
                if (!long.TryParse(Data, NumberStyles.AllowLeadingSign, CultureInfo.InvariantCulture, out var parsed)
                    || !string.Equals(parsed.ToString(CultureInfo.InvariantCulture), Data, StringComparison.Ordinal))
                {
                    throw new InvalidOperationException("Canonical I64 representation is invalid.");
                }
                break;
            case "UTF8":
                break;
            default:
                throw new InvalidOperationException("Canonical value representation is unsupported.");
        }
    }

    public string CanonicalForm()
    {
        Validate();
        var nameLength = Encoding.UTF8.GetByteCount(Name);
        var dataLength = Encoding.UTF8.GetByteCount(Data);
        return $"{nameLength}:{Name}|{Representation}|{dataLength}:{Data}";
    }
}
