using System.Globalization;
using System.Numerics;
using System.Text.Json;

namespace ApexForge.Runtime;

/// <summary>
/// Projects the functions subtree of canonical AIR transport JSON into the
/// managed executable carrier model. Canonical AIR remains the semantic owner.
/// </summary>
public sealed class ManagedExecutableCarrierDecoder
{
    private static readonly string[] RequiredProgramProperties =
    [
        "authorities",
        "authority_checks",
        "causal_decisions",
        "directives",
        "events",
        "functions",
        "principals",
        "requirements",
        "roles",
        "states",
        "version",
    ];

    private static readonly string[] OptionalProgramProperties = ["workflows"];

    public IReadOnlyList<ManagedExecutableFunction> DecodeCanonicalAirTransport(
        string canonicalAirTransportJson
    )
    {
        ArgumentNullException.ThrowIfNull(canonicalAirTransportJson);

        try
        {
            using JsonDocument document = JsonDocument.Parse(
                canonicalAirTransportJson,
                new JsonDocumentOptions
                {
                    AllowTrailingCommas = false,
                    CommentHandling = JsonCommentHandling.Disallow,
                    MaxDepth = 256,
                }
            );

            return DecodeProgram(document.RootElement);
        }
        catch (JsonException error)
        {
            throw new FormatException(
                "Canonical AIR transport is not valid strict JSON.",
                error
            );
        }
    }

    private static IReadOnlyList<ManagedExecutableFunction> DecodeProgram(
        JsonElement root
    )
    {
        Dictionary<string, JsonElement> properties = ReadObject(
            root,
            "$",
            RequiredProgramProperties,
            OptionalProgramProperties
        );

        RequireKind(properties["version"], JsonValueKind.String, "$.version");
        foreach (string name in RequiredProgramProperties)
        {
            if (name != "version" && name != "functions")
            {
                RequireKind(properties[name], JsonValueKind.Array, "$." + name);
            }
        }

        if (properties.TryGetValue("workflows", out JsonElement workflows))
        {
            RequireKind(workflows, JsonValueKind.Array, "$.workflows");
        }

        return DecodeArray(
            properties["functions"],
            "$.functions",
            DecodeFunction
        );
    }

    private static ManagedExecutableFunction DecodeFunction(
        JsonElement element,
        string path
    )
    {
        Dictionary<string, JsonElement> properties = ReadObject(
            element,
            path,
            [
                "id",
                "name",
                "parameters",
                "return_expression",
                "order",
                "local_bindings",
                "body",
                "return_type",
                "type_parameters",
            ]
        );

        return new ManagedExecutableFunction(
            ReadString(properties["id"], path + ".id"),
            ReadString(properties["name"], path + ".name"),
            DecodeArray(
                properties["parameters"],
                path + ".parameters",
                DecodeParameter
            ),
            DecodeNullableExpression(
                properties["return_expression"],
                path + ".return_expression"
            ),
            ReadInt32(properties["order"], path + ".order"),
            DecodeArray(
                properties["local_bindings"],
                path + ".local_bindings",
                DecodeLocalBinding
            ),
            DecodeArray(
                properties["body"],
                path + ".body",
                DecodeStatement
            ),
            DecodeNullableGenericType(
                properties["return_type"],
                path + ".return_type"
            ),
            DecodeArray(
                properties["type_parameters"],
                path + ".type_parameters",
                DecodeTypeVariable
            )
        );
    }

    private static ManagedFunctionParameter DecodeParameter(
        JsonElement element,
        string path
    )
    {
        Dictionary<string, JsonElement> properties = ReadObject(
            element,
            path,
            ["name", "value_type"]
        );

        return new ManagedFunctionParameter(
            ReadString(properties["name"], path + ".name"),
            DecodeNullableGenericType(
                properties["value_type"],
                path + ".value_type"
            )
        );
    }

    private static ManagedLocalBinding DecodeLocalBinding(
        JsonElement element,
        string path
    )
    {
        Dictionary<string, JsonElement> properties = ReadObject(
            element,
            path,
            ["name", "expression"]
        );

        return new ManagedLocalBinding(
            ReadString(properties["name"], path + ".name"),
            DecodeExpression(properties["expression"], path + ".expression")
        );
    }

    private static ManagedFunctionStatement DecodeStatement(
        JsonElement element,
        string path
    )
    {
        Dictionary<string, JsonElement> properties = ReadUniqueObject(element, path);

        if (HasExactProperties(properties, ["name", "expression"]))
        {
            return new ManagedLocalBinding(
                ReadString(properties["name"], path + ".name"),
                DecodeExpression(properties["expression"], path + ".expression")
            );
        }

        if (HasExactProperties(properties, ["expression"]))
        {
            return new ManagedFunctionReturn(
                DecodeExpression(properties["expression"], path + ".expression")
            );
        }

        if (HasExactProperties(
            properties,
            ["condition", "actions", "otherwise_actions"]
        ))
        {
            return new ManagedFunctionWhen(
                DecodeExpression(properties["condition"], path + ".condition"),
                DecodeArray(
                    properties["actions"],
                    path + ".actions",
                    DecodeStatement
                ),
                DecodeArray(
                    properties["otherwise_actions"],
                    path + ".otherwise_actions",
                    DecodeStatement
                )
            );
        }

        throw Fail(path, "has an unknown function-statement shape.");
    }

    private static ManagedExecutableExpression? DecodeNullableExpression(
        JsonElement element,
        string path
    )
    {
        return element.ValueKind == JsonValueKind.Null
            ? null
            : DecodeExpression(element, path);
    }

    private static ManagedExecutableExpression DecodeExpression(
        JsonElement element,
        string path
    )
    {
        Dictionary<string, JsonElement> properties = ReadUniqueObject(element, path);

        if (HasExactProperties(properties, ["value"]))
        {
            JsonElement value = properties["value"];
            return value.ValueKind switch
            {
                JsonValueKind.String => new ManagedStringLiteral(
                    ReadString(value, path + ".value")
                ),
                JsonValueKind.True or JsonValueKind.False =>
                    new ManagedBooleanLiteral(value.GetBoolean()),
                JsonValueKind.Number => DecodeNumericLiteral(
                    value,
                    path + ".value"
                ),
                _ => throw Fail(
                    path + ".value",
                    "must be a string, boolean, or number literal."
                ),
            };
        }

        if (HasExactProperties(properties, ["name"]))
        {
            return new ManagedIdentifierReference(
                ReadString(properties["name"], path + ".name")
            );
        }

        if (HasExactProperties(properties, ["operator", "operand"]))
        {
            return new ManagedUnaryExpression(
                ReadString(properties["operator"], path + ".operator"),
                DecodeExpression(properties["operand"], path + ".operand")
            );
        }

        if (HasExactProperties(properties, ["left", "operator", "right"]))
        {
            return new ManagedBinaryExpression(
                DecodeExpression(properties["left"], path + ".left"),
                ReadString(properties["operator"], path + ".operator"),
                DecodeExpression(properties["right"], path + ".right")
            );
        }

        if (HasExactProperties(properties, ["target", "arguments", "type_arguments"]))
        {
            return new ManagedCallExpression(
                ReadString(properties["target"], path + ".target"),
                DecodeArray(
                    properties["arguments"],
                    path + ".arguments",
                    DecodeExpression
                ),
                DecodeArray(
                    properties["type_arguments"],
                    path + ".type_arguments",
                    DecodeGenericType
                )
            );
        }

        throw Fail(path, "has an unknown expression shape.");
    }

    private static ManagedExecutableExpression DecodeNumericLiteral(
        JsonElement element,
        string path
    )
    {
        string raw = element.GetRawText();
        bool isFloat = raw.Contains('.', StringComparison.Ordinal)
            || raw.Contains('e', StringComparison.OrdinalIgnoreCase);

        if (!isFloat)
        {
            if (!BigInteger.TryParse(
                raw,
                NumberStyles.AllowLeadingSign,
                CultureInfo.InvariantCulture,
                out BigInteger integer
            ))
            {
                throw Fail(path, "is not an exact invariant integer token.");
            }

            return new ManagedIntegerLiteral(integer);
        }

        if (!double.TryParse(
            raw,
            NumberStyles.Float,
            CultureInfo.InvariantCulture,
            out double floating
        ) || !double.IsFinite(floating))
        {
            throw Fail(path, "is not a finite invariant binary64 token.");
        }

        return new ManagedFloatLiteral(floating);
    }

    private static ManagedGenericTypeLike? DecodeNullableGenericType(
        JsonElement element,
        string path
    )
    {
        return element.ValueKind == JsonValueKind.Null
            ? null
            : DecodeGenericType(element, path);
    }

    private static ManagedGenericTypeLike DecodeGenericType(
        JsonElement element,
        string path
    )
    {
        Dictionary<string, JsonElement> properties = ReadUniqueObject(element, path);

        if (HasExactProperties(properties, ["name", "arguments"]))
        {
            return DecodeApexType(properties, path);
        }

        if (HasExactProperties(properties, ["name", "owner", "constraints"]))
        {
            return DecodeTypeVariable(properties, path);
        }

        throw Fail(path, "has an unknown canonical generic-type shape.");
    }

    private static ManagedApexTypeReference DecodeApexType(
        JsonElement element,
        string path
    )
    {
        Dictionary<string, JsonElement> properties = ReadObject(
            element,
            path,
            ["name", "arguments"]
        );
        return DecodeApexType(properties, path);
    }

    private static ManagedApexTypeReference DecodeApexType(
        Dictionary<string, JsonElement> properties,
        string path
    )
    {
        return new ManagedApexTypeReference(
            ReadString(properties["name"], path + ".name"),
            DecodeArray(
                properties["arguments"],
                path + ".arguments",
                DecodeApexType
            )
        );
    }

    private static ManagedTypeVariableReference DecodeTypeVariable(
        JsonElement element,
        string path
    )
    {
        Dictionary<string, JsonElement> properties = ReadObject(
            element,
            path,
            ["name", "owner", "constraints"]
        );
        return DecodeTypeVariable(properties, path);
    }

    private static ManagedTypeVariableReference DecodeTypeVariable(
        Dictionary<string, JsonElement> properties,
        string path
    )
    {
        return new ManagedTypeVariableReference(
            ReadString(properties["name"], path + ".name"),
            ReadString(properties["owner"], path + ".owner"),
            DecodeArray(
                properties["constraints"],
                path + ".constraints",
                DecodeConstraint
            )
        );
    }

    private static ManagedConstraintReference DecodeConstraint(
        JsonElement element,
        string path
    )
    {
        Dictionary<string, JsonElement> properties = ReadObject(
            element,
            path,
            ["name", "description"]
        );

        return new ManagedApexTypeConstraintReference(
            ReadString(properties["name"], path + ".name"),
            ReadString(properties["description"], path + ".description")
        );
    }

    private static T[] DecodeArray<T>(
        JsonElement element,
        string path,
        Func<JsonElement, string, T> decodeItem
    )
    {
        RequireKind(element, JsonValueKind.Array, path);
        int count = element.GetArrayLength();
        if (count == 0)
        {
            return [];
        }

        T[] values = new T[count];
        int index = 0;
        foreach (JsonElement item in element.EnumerateArray())
        {
            values[index] = decodeItem(item, $"{path}[{index}]");
            index++;
        }

        return values;
    }

    private static Dictionary<string, JsonElement> ReadObject(
        JsonElement element,
        string path,
        IReadOnlyList<string> required,
        IReadOnlyList<string>? optional = null
    )
    {
        Dictionary<string, JsonElement> properties = ReadUniqueObject(element, path);
        HashSet<string> allowed = new(required, StringComparer.Ordinal);
        if (optional is not null)
        {
            allowed.UnionWith(optional);
        }

        foreach (string name in properties.Keys)
        {
            if (!allowed.Contains(name))
            {
                throw Fail(path, $"contains unknown property '{name}'.");
            }
        }

        foreach (string name in required)
        {
            if (!properties.ContainsKey(name))
            {
                throw Fail(path, $"is missing required property '{name}'.");
            }
        }

        return properties;
    }

    private static Dictionary<string, JsonElement> ReadUniqueObject(
        JsonElement element,
        string path
    )
    {
        RequireKind(element, JsonValueKind.Object, path);
        Dictionary<string, JsonElement> properties = new(StringComparer.Ordinal);

        foreach (JsonProperty property in element.EnumerateObject())
        {
            if (!properties.TryAdd(property.Name, property.Value))
            {
                throw Fail(path, $"contains duplicate property '{property.Name}'.");
            }
        }

        return properties;
    }

    private static bool HasExactProperties(
        Dictionary<string, JsonElement> properties,
        IReadOnlyList<string> expected
    )
    {
        if (properties.Count != expected.Count)
        {
            return false;
        }

        foreach (string name in expected)
        {
            if (!properties.ContainsKey(name))
            {
                return false;
            }
        }

        return true;
    }

    private static string ReadString(JsonElement element, string path)
    {
        RequireKind(element, JsonValueKind.String, path);
        return element.GetString()
            ?? throw Fail(path, "must contain a non-null string.");
    }

    private static int ReadInt32(JsonElement element, string path)
    {
        RequireKind(element, JsonValueKind.Number, path);
        string raw = element.GetRawText();
        if (raw.Contains('.', StringComparison.Ordinal)
            || raw.Contains('e', StringComparison.OrdinalIgnoreCase)
            || !int.TryParse(
                raw,
                NumberStyles.AllowLeadingSign,
                CultureInfo.InvariantCulture,
                out int value
            ))
        {
            throw Fail(path, "must be an invariant 32-bit integer token.");
        }

        return value;
    }

    private static void RequireKind(
        JsonElement element,
        JsonValueKind expected,
        string path
    )
    {
        if (element.ValueKind != expected)
        {
            throw Fail(
                path,
                $"must be {expected}; received {element.ValueKind}."
            );
        }
    }

    private static FormatException Fail(string path, string message)
    {
        return new FormatException($"Canonical AIR transport at '{path}' {message}");
    }
}
