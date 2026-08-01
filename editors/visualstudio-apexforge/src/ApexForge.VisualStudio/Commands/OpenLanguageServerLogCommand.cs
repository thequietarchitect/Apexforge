using System;
using System.ComponentModel.Design;
using System.Diagnostics;
using System.IO;
using System.Threading.Tasks;
using GravitasStudios.ApexForge.VisualStudio.LanguageServer;
using Microsoft.VisualStudio.Shell;
using Microsoft.VisualStudio.Shell.Interop;

namespace GravitasStudios.ApexForge.VisualStudio
{
    internal sealed class OpenLanguageServerLogCommand
    {
        public const int CommandId = 0x0102;

        public static readonly Guid CommandSet =
            new Guid("744A30FD-DF87-5104-A449-A95DF8E526FA");

        private readonly AsyncPackage package;

        private OpenLanguageServerLogCommand(
            AsyncPackage package,
            OleMenuCommandService commandService)
        {
            this.package = package ?? throw new ArgumentNullException(nameof(package));
            commandService = commandService
                ?? throw new ArgumentNullException(nameof(commandService));

            var commandIdentifier = new CommandID(CommandSet, CommandId);
            commandService.AddCommand(
                new MenuCommand(Execute, commandIdentifier));
        }

        public static async Task InitializeAsync(AsyncPackage package)
        {
            if (package == null)
            {
                throw new ArgumentNullException(nameof(package));
            }

            await ThreadHelper.JoinableTaskFactory.SwitchToMainThreadAsync();
            var commandService = await package.GetServiceAsync(
                typeof(IMenuCommandService)) as OleMenuCommandService;

            if (commandService == null)
            {
                throw new InvalidOperationException(
                    "Visual Studio menu command service is unavailable.");
            }

            _ = new OpenLanguageServerLogCommand(package, commandService);
        }

        private void Execute(object sender, EventArgs eventArgs)
        {
            ThreadHelper.ThrowIfNotOnUIThread();

            string path = ApexForgeLanguageServerTrace.LogPath;
            try
            {
                string directory = Path.GetDirectoryName(path);
                Directory.CreateDirectory(directory);
                if (!File.Exists(path))
                {
                    File.WriteAllText(
                        path,
                        "ApexForge Visual Studio language-server log."
                        + Environment.NewLine);
                }

                Process.Start(new ProcessStartInfo
                {
                    FileName = path,
                    UseShellExecute = true
                });
            }
            catch (Exception error) when (
                error is IOException
                || error is UnauthorizedAccessException
                || error is ArgumentException
                || error is System.ComponentModel.Win32Exception
                || error is NotSupportedException)
            {
                VsShellUtilities.ShowMessageBox(
                    package,
                    "Could not open the ApexForge language-server log: "
                    + error.Message,
                    "ApexForge Language Tools",
                    OLEMSGICON.OLEMSGICON_WARNING,
                    OLEMSGBUTTON.OLEMSGBUTTON_OK,
                    OLEMSGDEFBUTTON.OLEMSGDEFBUTTON_FIRST);
            }
        }
    }
}
