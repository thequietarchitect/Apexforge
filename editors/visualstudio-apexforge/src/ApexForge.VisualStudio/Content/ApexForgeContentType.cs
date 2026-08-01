using System.ComponentModel.Composition;
using Microsoft.VisualStudio.LanguageServer.Client;
using Microsoft.VisualStudio.Utilities;

namespace GravitasStudios.ApexForge.VisualStudio
{
    internal static class ApexForgeContentType
    {
        internal const string Name = "apexforge";
        internal const string FileExtension = ".apex";

        [Export(typeof(ContentTypeDefinition))]
        [Name(Name)]
        [BaseDefinition(CodeRemoteContentDefinition.CodeRemoteContentTypeName)]
        internal static ContentTypeDefinition ContentTypeDefinition = null;

        [Export(typeof(FileExtensionToContentTypeDefinition))]
        [FileExtension(FileExtension)]
        [ContentType(Name)]
        internal static FileExtensionToContentTypeDefinition FileExtensionDefinition = null;
    }
}
