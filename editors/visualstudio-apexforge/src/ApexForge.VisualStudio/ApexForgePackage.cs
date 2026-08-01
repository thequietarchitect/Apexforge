using System;
using System.Runtime.InteropServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.VisualStudio.Shell;

namespace GravitasStudios.ApexForge.VisualStudio
{
    [PackageRegistration(UseManagedResourcesOnly = true, AllowsBackgroundLoading = true)]
    [InstalledProductRegistration(
        "ApexForge Language Tools",
        "Visual Studio editor foundation for ApexForge .apex source files.",
        "0.1.0")]
    [ProvideMenuResource("Menus.ctmenu", 1)]
    [Guid(PackageGuidString)]
    public sealed class ApexForgePackage : AsyncPackage
    {
        public const string PackageGuidString = "DF54A578-54A2-52F4-8643-4A85DDDFB2F2";

        protected override async Task InitializeAsync(
            CancellationToken cancellationToken,
            IProgress<ServiceProgressData> progress)
        {
            await JoinableTaskFactory.SwitchToMainThreadAsync(cancellationToken);
            await ShowStatusCommand.InitializeAsync(this);
            await RestartLanguageServerCommand.InitializeAsync(this);
            await OpenLanguageServerLogCommand.InitializeAsync(this);
        }
    }
}
