using System;
using System.ComponentModel.Design;
using System.Threading.Tasks;
using GravitasStudios.ApexForge.VisualStudio.LanguageServer;
using Microsoft.VisualStudio.Shell;
using Microsoft.VisualStudio.Shell.Interop;

namespace GravitasStudios.ApexForge.VisualStudio
{
    internal sealed class ShowStatusCommand
    {
        public const int CommandId = 0x0100;

        public static readonly Guid CommandSet =
            new Guid("744A30FD-DF87-5104-A449-A95DF8E526FA");

        private readonly AsyncPackage package;

        private ShowStatusCommand(
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

            _ = new ShowStatusCommand(package, commandService);
        }

        private void Execute(object sender, EventArgs eventArgs)
        {
            ThreadHelper.ThrowIfNotOnUIThread();

            VsShellUtilities.ShowMessageBox(
                package,
                "ApexForge Visual Studio foundation is active.\n\n" +
                "Content type: apexforge\n" +
                "File extension: .apex\n" +
                "Language-server bridge: active (AFP-P10-T5.3).\n" +
                "Diagnostics/document sync: active (AFP-P10-T5.4).\n" +
                "IntelliSense/navigation/formatting: active (AFP-P10-T5.5).\n" +
                "Visual Studio integration: final P10-T5 parity.\n" +
                "Log: " + ApexForgeLanguageServerTrace.LogPath,
                "ApexForge Language Tools",
                OLEMSGICON.OLEMSGICON_INFO,
                OLEMSGBUTTON.OLEMSGBUTTON_OK,
                OLEMSGDEFBUTTON.OLEMSGDEFBUTTON_FIRST);
        }
    }
}
