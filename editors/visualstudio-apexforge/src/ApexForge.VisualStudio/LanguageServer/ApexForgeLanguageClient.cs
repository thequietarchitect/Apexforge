using System;
using System.Collections.Generic;
using System.ComponentModel.Composition;
using System.Diagnostics;
using System.IO;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.VisualStudio.LanguageServer.Client;
using Microsoft.VisualStudio.Threading;
using Microsoft.VisualStudio.Utilities;

namespace GravitasStudios.ApexForge.VisualStudio.LanguageServer
{
    [ContentType(ApexForgeContentType.Name)]
    [Export(typeof(ILanguageClient))]
    public sealed class ApexForgeLanguageClient : ILanguageClient
    {
        private readonly object processGate = new object();
        private AsyncEventHandler<EventArgs> startAsync;
        private Process activeProcess;

        public string Name => "ApexForge Language Server";

        public IEnumerable<string> ConfigurationSections => null;

        public object InitializationOptions => new
        {
            apexforge = new
            {
                client = "visualstudio",
                milestone = "AFP-P10-T5.3"
            }
        };

        public IEnumerable<string> FilesToWatch => null;

        public bool ShowNotificationOnInitializeFailed => true;

        public event AsyncEventHandler<EventArgs> StartAsync
        {
            add { startAsync += value; }
            remove { startAsync -= value; }
        }

        public event AsyncEventHandler<EventArgs> StopAsync
        {
            add { }
            remove { }
        }

        public async Task<Connection> ActivateAsync(CancellationToken token)
        {
            token.ThrowIfCancellationRequested();
            await Task.Yield();

            ApexForgeLanguageServerLaunch launch = ApexForgeLanguageServerLocator.Resolve();
            var startInfo = new ProcessStartInfo
            {
                FileName = launch.PythonExecutable,
                Arguments = launch.Arguments,
                WorkingDirectory = launch.WorkingDirectory,
                RedirectStandardInput = true,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                UseShellExecute = false,
                CreateNoWindow = true
            };
            startInfo.EnvironmentVariables["PYTHONUTF8"] = "1";
            startInfo.EnvironmentVariables["PYTHONDONTWRITEBYTECODE"] = "1";

            var process = new Process
            {
                StartInfo = startInfo,
                EnableRaisingEvents = true
            };
            process.ErrorDataReceived += OnErrorDataReceived;
            process.Exited += OnProcessExited;

            Process previous;
            lock (processGate)
            {
                previous = activeProcess;
                activeProcess = process;
            }
            TryTerminate(previous);

            try
            {
                ApexForgeLanguageServerTrace.Write(
                    "Starting ApexForge language server: "
                    + launch.PythonExecutable
                    + " "
                    + launch.Arguments);

                if (!process.Start())
                {
                    throw new InvalidOperationException(
                        "The ApexForge language-server process did not start.");
                }

                process.BeginErrorReadLine();
                token.ThrowIfCancellationRequested();
                ApexForgeLanguageServerTrace.Write(
                    "ApexForge language-server process started with PID "
                    + process.Id
                    + ".");

                return new Connection(
                    process.StandardOutput.BaseStream,
                    process.StandardInput.BaseStream);
            }
            catch
            {
                ClearActiveProcess(process);
                TryTerminate(process);
                process.Dispose();
                throw;
            }
        }

        public async Task OnLoadedAsync()
        {
            await Task.Yield();
            AsyncEventHandler<EventArgs> handler = startAsync;
            if (handler == null)
            {
                throw new InvalidOperationException(
                    "Visual Studio did not subscribe to the ApexForge language-client start event.");
            }

            ApexForgeLanguageServerTrace.Write(
                "ApexForge language client loaded; requesting server activation.");
            await handler.InvokeAsync(this, EventArgs.Empty);
        }

        public Task OnServerInitializeFailedAsync(Exception exception)
        {
            string detail = exception == null ? "Unknown initialization failure." : exception.ToString();
            ApexForgeLanguageServerTrace.Write(
                "ApexForge language-server initialization failed: " + detail);
            StopActiveProcess();
            return Task.CompletedTask;
        }

        public Task<InitializationFailureContext> OnServerInitializeFailedAsync(
            ILanguageClientInitializationInfo initializationState)
        {
            string detail = initializationState == null
                ? "No initialization state was supplied."
                : initializationState.ToString();
            ApexForgeLanguageServerTrace.Write(
                "ApexForge language-server structured initialization failure: "
                + detail);
            StopActiveProcess();
            return Task.FromResult<InitializationFailureContext>(null);
        }

        public Task OnServerInitializedAsync()
        {
            ApexForgeLanguageServerTrace.Write(
                "ApexForge language server initialized successfully.");
            return Task.CompletedTask;
        }

        private void OnErrorDataReceived(object sender, DataReceivedEventArgs eventArgs)
        {
            if (!string.IsNullOrWhiteSpace(eventArgs.Data))
            {
                ApexForgeLanguageServerTrace.Write(
                    "server stderr: " + eventArgs.Data);
            }
        }

        private void OnProcessExited(object sender, EventArgs eventArgs)
        {
            var process = sender as Process;
            if (process == null)
            {
                return;
            }

            int exitCode;
            try
            {
                exitCode = process.ExitCode;
            }
            catch (InvalidOperationException)
            {
                exitCode = -1;
            }

            ClearActiveProcess(process);
            ApexForgeLanguageServerTrace.Write(
                "ApexForge language-server process exited with code "
                + exitCode
                + ".");
        }

        private void StopActiveProcess()
        {
            Process process;
            lock (processGate)
            {
                process = activeProcess;
                activeProcess = null;
            }
            TryTerminate(process);
        }

        private void ClearActiveProcess(Process process)
        {
            lock (processGate)
            {
                if (ReferenceEquals(activeProcess, process))
                {
                    activeProcess = null;
                }
            }
        }

        private static void TryTerminate(Process process)
        {
            if (process == null)
            {
                return;
            }

            try
            {
                if (!process.HasExited)
                {
                    process.Kill();
                    process.WaitForExit(2000);
                }
            }
            catch (Exception error) when (
                error is InvalidOperationException
                || error is System.ComponentModel.Win32Exception
                || error is NotSupportedException)
            {
                ApexForgeLanguageServerTrace.Write(
                    "Could not terminate a previous language-server process: "
                    + error.Message);
            }
        }
    }
}
