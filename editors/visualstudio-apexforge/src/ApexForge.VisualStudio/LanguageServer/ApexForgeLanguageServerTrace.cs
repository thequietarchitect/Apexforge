using System;
using System.Diagnostics;
using System.IO;
using System.Text;

namespace GravitasStudios.ApexForge.VisualStudio.LanguageServer
{
    internal static class ApexForgeLanguageServerTrace
    {
        private static readonly object Gate = new object();

        internal static string LogPath => Path.Combine(
            Path.GetTempPath(),
            "ApexForge",
            "visualstudio-language-client.log");

        internal static void Write(string message)
        {
            if (string.IsNullOrWhiteSpace(message))
            {
                return;
            }

            string line = DateTimeOffset.UtcNow.ToString("O") + " " + message;
            Trace.WriteLine(line, "ApexForge Language Server");

            try
            {
                lock (Gate)
                {
                    string directory = Path.GetDirectoryName(LogPath);
                    Directory.CreateDirectory(directory);
                    File.AppendAllText(
                        LogPath,
                        line + Environment.NewLine,
                        new UTF8Encoding(encoderShouldEmitUTF8Identifier: false));
                }
            }
            catch (Exception error) when (
                error is IOException
                || error is UnauthorizedAccessException
                || error is ArgumentException
                || error is NotSupportedException)
            {
                Trace.WriteLine(
                    "ApexForge language-client logging failed: " + error.Message,
                    "ApexForge Language Server");
            }
        }
    }
}
