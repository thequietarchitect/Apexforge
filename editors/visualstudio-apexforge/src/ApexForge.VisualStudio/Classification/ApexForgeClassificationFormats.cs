using System.ComponentModel.Composition;
using Microsoft.VisualStudio.Text.Classification;
using Microsoft.VisualStudio.Utilities;

namespace GravitasStudios.ApexForge.VisualStudio.Classification
{
    [Export(typeof(EditorFormatDefinition))]
    [ClassificationType(ClassificationTypeNames = ApexForgeClassificationNames.Keyword)]
    [Name(ApexForgeClassificationNames.Keyword)]
    [UserVisible(true)]
    [Order(After = Priority.Default)]
    internal sealed class ApexForgeKeywordFormat : ClassificationFormatDefinition
    {
        public ApexForgeKeywordFormat()
        {
            DisplayName = "ApexForge Keyword";
        }
    }

    [Export(typeof(EditorFormatDefinition))]
    [ClassificationType(ClassificationTypeNames = ApexForgeClassificationNames.Declaration)]
    [Name(ApexForgeClassificationNames.Declaration)]
    [UserVisible(true)]
    [Order(After = Priority.Default)]
    internal sealed class ApexForgeDeclarationFormat : ClassificationFormatDefinition
    {
        public ApexForgeDeclarationFormat()
        {
            DisplayName = "ApexForge Declaration";
        }
    }

    [Export(typeof(EditorFormatDefinition))]
    [ClassificationType(ClassificationTypeNames = ApexForgeClassificationNames.Function)]
    [Name(ApexForgeClassificationNames.Function)]
    [UserVisible(true)]
    [Order(After = Priority.Default)]
    internal sealed class ApexForgeFunctionFormat : ClassificationFormatDefinition
    {
        public ApexForgeFunctionFormat()
        {
            DisplayName = "ApexForge Function";
        }
    }

    [Export(typeof(EditorFormatDefinition))]
    [ClassificationType(ClassificationTypeNames = ApexForgeClassificationNames.Type)]
    [Name(ApexForgeClassificationNames.Type)]
    [UserVisible(true)]
    [Order(After = Priority.Default)]
    internal sealed class ApexForgeTypeFormat : ClassificationFormatDefinition
    {
        public ApexForgeTypeFormat()
        {
            DisplayName = "ApexForge Type";
        }
    }

    [Export(typeof(EditorFormatDefinition))]
    [ClassificationType(ClassificationTypeNames = ApexForgeClassificationNames.String)]
    [Name(ApexForgeClassificationNames.String)]
    [UserVisible(true)]
    [Order(After = Priority.Default)]
    internal sealed class ApexForgeStringFormat : ClassificationFormatDefinition
    {
        public ApexForgeStringFormat()
        {
            DisplayName = "ApexForge String";
        }
    }

    [Export(typeof(EditorFormatDefinition))]
    [ClassificationType(ClassificationTypeNames = ApexForgeClassificationNames.Number)]
    [Name(ApexForgeClassificationNames.Number)]
    [UserVisible(true)]
    [Order(After = Priority.Default)]
    internal sealed class ApexForgeNumberFormat : ClassificationFormatDefinition
    {
        public ApexForgeNumberFormat()
        {
            DisplayName = "ApexForge Number";
        }
    }

    [Export(typeof(EditorFormatDefinition))]
    [ClassificationType(ClassificationTypeNames = ApexForgeClassificationNames.Boolean)]
    [Name(ApexForgeClassificationNames.Boolean)]
    [UserVisible(true)]
    [Order(After = Priority.Default)]
    internal sealed class ApexForgeBooleanFormat : ClassificationFormatDefinition
    {
        public ApexForgeBooleanFormat()
        {
            DisplayName = "ApexForge Boolean";
        }
    }

    [Export(typeof(EditorFormatDefinition))]
    [ClassificationType(ClassificationTypeNames = ApexForgeClassificationNames.Operator)]
    [Name(ApexForgeClassificationNames.Operator)]
    [UserVisible(true)]
    [Order(After = Priority.Default)]
    internal sealed class ApexForgeOperatorFormat : ClassificationFormatDefinition
    {
        public ApexForgeOperatorFormat()
        {
            DisplayName = "ApexForge Operator";
        }
    }

    [Export(typeof(EditorFormatDefinition))]
    [ClassificationType(ClassificationTypeNames = ApexForgeClassificationNames.Punctuation)]
    [Name(ApexForgeClassificationNames.Punctuation)]
    [UserVisible(true)]
    [Order(After = Priority.Default)]
    internal sealed class ApexForgePunctuationFormat : ClassificationFormatDefinition
    {
        public ApexForgePunctuationFormat()
        {
            DisplayName = "ApexForge Punctuation";
        }
    }
}
