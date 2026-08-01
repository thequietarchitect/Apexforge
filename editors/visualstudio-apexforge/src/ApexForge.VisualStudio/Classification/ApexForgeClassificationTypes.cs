using System.ComponentModel.Composition;
using Microsoft.VisualStudio.Language.StandardClassification;
using Microsoft.VisualStudio.Text.Classification;
using Microsoft.VisualStudio.Utilities;

namespace GravitasStudios.ApexForge.VisualStudio.Classification
{
    internal static class ApexForgeClassificationTypes
    {
        [Export(typeof(ClassificationTypeDefinition))]
        [Name(ApexForgeClassificationNames.Keyword)]
        [BaseDefinition(PredefinedClassificationTypeNames.Keyword)]
        internal static ClassificationTypeDefinition Keyword = null;

        [Export(typeof(ClassificationTypeDefinition))]
        [Name(ApexForgeClassificationNames.Declaration)]
        [BaseDefinition(PredefinedClassificationTypeNames.SymbolDefinition)]
        internal static ClassificationTypeDefinition Declaration = null;

        [Export(typeof(ClassificationTypeDefinition))]
        [Name(ApexForgeClassificationNames.Function)]
        [BaseDefinition(PredefinedClassificationTypeNames.Method)]
        internal static ClassificationTypeDefinition Function = null;

        [Export(typeof(ClassificationTypeDefinition))]
        [Name(ApexForgeClassificationNames.Type)]
        [BaseDefinition(PredefinedClassificationTypeNames.Identifier)]
        internal static ClassificationTypeDefinition Type = null;

        [Export(typeof(ClassificationTypeDefinition))]
        [Name(ApexForgeClassificationNames.String)]
        [BaseDefinition(PredefinedClassificationTypeNames.String)]
        internal static ClassificationTypeDefinition String = null;

        [Export(typeof(ClassificationTypeDefinition))]
        [Name(ApexForgeClassificationNames.Number)]
        [BaseDefinition(PredefinedClassificationTypeNames.Number)]
        internal static ClassificationTypeDefinition Number = null;

        [Export(typeof(ClassificationTypeDefinition))]
        [Name(ApexForgeClassificationNames.Boolean)]
        [BaseDefinition(PredefinedClassificationTypeNames.Keyword)]
        internal static ClassificationTypeDefinition Boolean = null;

        [Export(typeof(ClassificationTypeDefinition))]
        [Name(ApexForgeClassificationNames.Operator)]
        [BaseDefinition(PredefinedClassificationTypeNames.Operator)]
        internal static ClassificationTypeDefinition Operator = null;

        [Export(typeof(ClassificationTypeDefinition))]
        [Name(ApexForgeClassificationNames.Punctuation)]
        [BaseDefinition(PredefinedClassificationTypeNames.Punctuation)]
        internal static ClassificationTypeDefinition Punctuation = null;
    }
}
