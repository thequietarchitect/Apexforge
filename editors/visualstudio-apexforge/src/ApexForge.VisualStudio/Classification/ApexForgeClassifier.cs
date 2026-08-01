using System;
using System.Collections.Generic;
using Microsoft.VisualStudio.Text;
using Microsoft.VisualStudio.Text.Classification;

namespace GravitasStudios.ApexForge.VisualStudio.Classification
{
    internal sealed class ApexForgeClassifier : IClassifier
    {
        private static readonly HashSet<string> Keywords = new HashSet<string>(StringComparer.Ordinal)
        {
            "module", "import", "function", "directive", "workflow", "authority",
            "principal", "role", "state", "event", "cause", "path", "capability",
            "requires", "extends", "add", "set", "emit", "message", "invoke",
            "when", "otherwise", "and", "or", "not", "return", "let", "true", "false"
        };

        private static readonly HashSet<string> DeclarationIntroducers = new HashSet<string>(StringComparer.Ordinal)
        {
            "module", "import", "function", "directive", "workflow", "authority",
            "principal", "role", "state", "event", "cause", "path", "capability", "let"
        };

        private static readonly HashSet<string> BuiltInTypes = new HashSet<string>(StringComparer.Ordinal)
        {
            "int", "bool", "string", "float", "void"
        };

        private readonly IClassificationType keywordType;
        private readonly IClassificationType declarationType;
        private readonly IClassificationType functionType;
        private readonly IClassificationType typeType;
        private readonly IClassificationType stringType;
        private readonly IClassificationType numberType;
        private readonly IClassificationType booleanType;
        private readonly IClassificationType operatorType;
        private readonly IClassificationType punctuationType;

        internal ApexForgeClassifier(IClassificationTypeRegistryService registry)
        {
            if (registry == null)
            {
                throw new ArgumentNullException(nameof(registry));
            }

            keywordType = RequireType(registry, ApexForgeClassificationNames.Keyword);
            declarationType = RequireType(registry, ApexForgeClassificationNames.Declaration);
            functionType = RequireType(registry, ApexForgeClassificationNames.Function);
            typeType = RequireType(registry, ApexForgeClassificationNames.Type);
            stringType = RequireType(registry, ApexForgeClassificationNames.String);
            numberType = RequireType(registry, ApexForgeClassificationNames.Number);
            booleanType = RequireType(registry, ApexForgeClassificationNames.Boolean);
            operatorType = RequireType(registry, ApexForgeClassificationNames.Operator);
            punctuationType = RequireType(registry, ApexForgeClassificationNames.Punctuation);
        }

        public event EventHandler<ClassificationChangedEventArgs> ClassificationChanged
        {
            add { }
            remove { }
        }

        public IList<ClassificationSpan> GetClassificationSpans(SnapshotSpan span)
        {
            var results = new List<ClassificationSpan>();
            if (span.Length == 0)
            {
                return results;
            }

            ITextSnapshot snapshot = span.Snapshot;
            int firstLine = snapshot.GetLineFromPosition(span.Start.Position).LineNumber;
            int finalPosition = Math.Max(span.Start.Position, span.End.Position - 1);
            int finalLine = snapshot.GetLineFromPosition(finalPosition).LineNumber;

            for (int lineNumber = firstLine; lineNumber <= finalLine; lineNumber++)
            {
                ITextSnapshotLine line = snapshot.GetLineFromLineNumber(lineNumber);
                ScanLine(line, span, results);
            }

            return results;
        }

        private void ScanLine(
            ITextSnapshotLine line,
            SnapshotSpan requestedSpan,
            List<ClassificationSpan> results)
        {
            string text = line.GetText();
            int offset = line.Start.Position;
            bool expectDeclaration = false;
            bool qualifiedDeclaration = false;
            bool expectType = false;
            int index = 0;

            while (index < text.Length)
            {
                char current = text[index];
                if (char.IsWhiteSpace(current))
                {
                    index++;
                    continue;
                }

                if (current == '"')
                {
                    int start = index++;
                    bool escaped = false;
                    while (index < text.Length)
                    {
                        char item = text[index++];
                        if (escaped)
                        {
                            escaped = false;
                        }
                        else if (item == '\\')
                        {
                            escaped = true;
                        }
                        else if (item == '"')
                        {
                            break;
                        }
                    }
                    AddSpan(line.Snapshot, requestedSpan, results, offset + start, index - start, stringType);
                    expectDeclaration = false;
                    expectType = false;
                    continue;
                }

                if (char.IsDigit(current))
                {
                    int start = index;
                    while (index < text.Length && char.IsDigit(text[index]))
                    {
                        index++;
                    }
                    if (index + 1 < text.Length && text[index] == '.' && char.IsDigit(text[index + 1]))
                    {
                        index++;
                        while (index < text.Length && char.IsDigit(text[index]))
                        {
                            index++;
                        }
                    }
                    AddSpan(line.Snapshot, requestedSpan, results, offset + start, index - start, numberType);
                    expectDeclaration = false;
                    expectType = false;
                    continue;
                }

                if (IsIdentifierStart(current))
                {
                    int start = index++;
                    while (index < text.Length && IsIdentifierPart(text[index]))
                    {
                        index++;
                    }
                    string word = text.Substring(start, index - start);

                    if (word == "true" || word == "false")
                    {
                        AddSpan(line.Snapshot, requestedSpan, results, offset + start, word.Length, booleanType);
                        expectDeclaration = false;
                        expectType = false;
                    }
                    else if (Keywords.Contains(word))
                    {
                        AddSpan(line.Snapshot, requestedSpan, results, offset + start, word.Length, keywordType);
                        expectDeclaration = DeclarationIntroducers.Contains(word);
                        qualifiedDeclaration = word == "module" || word == "import";
                        expectType = word == "extends" || word == "requires";
                    }
                    else if (BuiltInTypes.Contains(word) || expectType)
                    {
                        AddSpan(line.Snapshot, requestedSpan, results, offset + start, word.Length, typeType);
                        expectDeclaration = false;
                        expectType = false;
                    }
                    else if (expectDeclaration || qualifiedDeclaration)
                    {
                        AddSpan(line.Snapshot, requestedSpan, results, offset + start, word.Length, declarationType);
                        expectDeclaration = false;
                    }
                    else if (NextNonWhitespaceIsOpenParenthesis(text, index))
                    {
                        AddSpan(line.Snapshot, requestedSpan, results, offset + start, word.Length, functionType);
                    }
                    else
                    {
                        expectDeclaration = false;
                        expectType = false;
                    }
                    continue;
                }

                if (current == ':' )
                {
                    AddSpan(line.Snapshot, requestedSpan, results, offset + index, 1, punctuationType);
                    expectType = true;
                    index++;
                    continue;
                }

                if (IsPunctuation(current))
                {
                    AddSpan(line.Snapshot, requestedSpan, results, offset + index, 1, punctuationType);
                    if (current != '.')
                    {
                        qualifiedDeclaration = false;
                    }
                    index++;
                    continue;
                }

                int operatorLength = IsTwoCharacterOperator(text, index) ? 2 : (IsOperator(current) ? 1 : 0);
                if (operatorLength > 0)
                {
                    AddSpan(line.Snapshot, requestedSpan, results, offset + index, operatorLength, operatorType);
                    index += operatorLength;
                    continue;
                }

                qualifiedDeclaration = false;
                expectDeclaration = false;
                expectType = false;
                index++;
            }
        }

        private static bool IsIdentifierStart(char value)
        {
            return value == '_' || char.IsLetter(value);
        }

        private static bool IsIdentifierPart(char value)
        {
            return value == '_' || char.IsLetterOrDigit(value);
        }

        private static bool NextNonWhitespaceIsOpenParenthesis(string text, int index)
        {
            while (index < text.Length && char.IsWhiteSpace(text[index]))
            {
                index++;
            }
            if (index < text.Length && text[index] == '<')
            {
                int closing = text.IndexOf('>', index + 1);
                if (closing >= 0)
                {
                    index = closing + 1;
                    while (index < text.Length && char.IsWhiteSpace(text[index]))
                    {
                        index++;
                    }
                }
            }
            return index < text.Length && text[index] == '(';
        }

        private static bool IsTwoCharacterOperator(string text, int index)
        {
            if (index + 1 >= text.Length)
            {
                return false;
            }
            char first = text[index];
            char second = text[index + 1];
            return (first == '=' && second == '=')
                || (first == '!' && second == '=')
                || (first == '<' && second == '=')
                || (first == '>' && second == '=');
        }

        private static bool IsOperator(char value)
        {
            return value == '=' || value == '+' || value == '-' || value == '*'
                || value == '/' || value == '%' || value == '@' || value == '<'
                || value == '>';
        }

        private static bool IsPunctuation(char value)
        {
            return value == '{' || value == '}' || value == '(' || value == ')'
                || value == ',' || value == ':' || value == ';' || value == '.';
        }

        private static IClassificationType RequireType(
            IClassificationTypeRegistryService registry,
            string name)
        {
            IClassificationType classificationType = registry.GetClassificationType(name);
            if (classificationType == null)
            {
                throw new InvalidOperationException("Missing ApexForge classification type: " + name);
            }
            return classificationType;
        }

        private static void AddSpan(
            ITextSnapshot snapshot,
            SnapshotSpan requestedSpan,
            List<ClassificationSpan> results,
            int start,
            int length,
            IClassificationType classificationType)
        {
            int end = start + length;
            if (length <= 0 || end <= requestedSpan.Start.Position || start >= requestedSpan.End.Position)
            {
                return;
            }

            var tokenSpan = new SnapshotSpan(snapshot, new Span(start, length));
            results.Add(new ClassificationSpan(tokenSpan, classificationType));
        }
    }
}
