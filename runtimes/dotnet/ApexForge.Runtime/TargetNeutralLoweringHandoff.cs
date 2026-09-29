using System;
using System.Collections.Generic;
using System.Linq;

namespace ApexForge.Runtime;

public sealed record TargetNeutralLoweringHandoff(
    string Schema,
    string VerifiedAirFingerprint,
    string RoutingFingerprint,
    string EntryDirective,
    IReadOnlyList<string> DirectiveOwnerIds,
    string ProductFingerprint)
{
    public const string RequiredSchema = "apexforge.target-neutral-lowering/v1";

    public void Validate()
    {
        if (!string.Equals(Schema, RequiredSchema, StringComparison.Ordinal))
        {
            throw new InvalidOperationException("Target-neutral lowering schema is invalid.");
        }

        ValidateFingerprint(VerifiedAirFingerprint, "Verified AIR", requireUppercase: false);
        ValidateFingerprint(RoutingFingerprint, "Routing", requireUppercase: false);
        ValidateFingerprint(ProductFingerprint, "Product", requireUppercase: true);

        if (string.IsNullOrWhiteSpace(EntryDirective))
        {
            throw new InvalidOperationException("Target-neutral entry directive is required.");
        }

        if (DirectiveOwnerIds is null)
        {
            throw new InvalidOperationException("Target-neutral directive owner ids are required.");
        }

        foreach (var ownerId in DirectiveOwnerIds)
        {
            if (string.IsNullOrWhiteSpace(ownerId))
            {
                throw new InvalidOperationException("Target-neutral directive owner id is invalid.");
            }
        }
    }

    private static void ValidateFingerprint(string value, string label, bool requireUppercase)
    {
        if (value is null || value.Length != 64)
        {
            throw new InvalidOperationException($"{label} fingerprint is invalid.");
        }

        var valid = value.All(ch =>
            (ch >= '0' && ch <= '9')
            || (ch >= 'A' && ch <= 'F')
            || (!requireUppercase && ch >= 'a' && ch <= 'f'));

        if (!valid)
        {
            throw new InvalidOperationException($"{label} fingerprint is invalid.");
        }
    }
}
