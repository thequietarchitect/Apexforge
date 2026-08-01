using System.ComponentModel.Composition;
using Microsoft.VisualStudio.Text;
using Microsoft.VisualStudio.Text.Classification;
using Microsoft.VisualStudio.Utilities;

namespace GravitasStudios.ApexForge.VisualStudio.Classification
{
    [Export(typeof(IClassifierProvider))]
    [ContentType(ApexForgeContentType.Name)]
    internal sealed class ApexForgeClassifierProvider : IClassifierProvider
    {
        [Import]
        internal IClassificationTypeRegistryService ClassificationRegistry = null;

        public IClassifier GetClassifier(ITextBuffer textBuffer)
        {
            return textBuffer.Properties.GetOrCreateSingletonProperty(
                () => new ApexForgeClassifier(ClassificationRegistry));
        }
    }
}
