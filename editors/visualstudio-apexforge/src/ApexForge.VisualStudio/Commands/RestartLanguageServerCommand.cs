using System;
using System.ComponentModel.Design;
using System.Threading.Tasks;
using GravitasStudios.ApexForge.VisualStudio.LanguageServer;
using Microsoft.VisualStudio.Shell;
using Microsoft.VisualStudio.Shell.Interop;
using Microsoft.VisualStudio.Threading;

namespace GravitasStudios.ApexForge.VisualStudio
{
    internal sealed class RestartLanguageServerCommand
    {
        public const int CommandId = 0x0101;

        public static readonly Guid CommandSet =
            new Guid("744A30FD-DF87-5104-A449-A95DF8E526FA");

        private readonly AsyncPackage package;

        private RestartLanguageServerCommand(
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

            _ = new RestartLanguageServerCommand(package, commandService);
        }

        private void Execute(object sender, EventArgs eventArgs)
        {
            package.JoinableTaskFactory.RunAsync(ExecuteAsync).Task.Forget();
        }

        private async Task ExecuteAsync()
        {
            bool restarted = false;
            string failureDetail = null;

            try
            {
                restarted = await ApexForgeLanguageClient.RequestRestartAsync();
            }
            catch (Exception error)
            {
                failureDetail = error.Message;
                ApexForgeLanguageServerTrace.Write(
                    "ApexForge restart command failed: " + error);
            }

            await package.JoinableTaskFactory.SwitchToMainThreadAsync();

            string message;
            if (restarted)
            {
                message =
                    "The ApexForge language server restarted and completed document resynchronization.";
            }
            else if (!string.IsNullOrWhiteSpace(failureDetail))
            {
                message = "The ApexForge language-server restart failed: " + failureDetail;
            }
            else
            {
                message =
                    "The ApexForge language client is not active or did not become ready. "
                    + "Open an .apex file and try again.";
            }

            VsShellUtilities.ShowMessageBox(
                package,
                message,
                "ApexForge Language Tools",
                restarted ? OLEMSGICON.OLEMSGICON_INFO : OLEMSGICON.OLEMSGICON_WARNING,
                OLEMSGBUTTON.OLEMSGBUTTON_OK,
                OLEMSGDEFBUTTON.OLEMSGDEFBUTTON_FIRST);
        }
    }
}
