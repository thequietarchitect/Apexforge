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
        private static readonly object InstanceGate = new object();
        private static ApexForgeLanguageClient currentInstance;

        private static readonly TimeSpan RestartInitializationTimeout =
            TimeSpan.FromSeconds(15);
        private static readonly TimeSpan DocumentResynchronizationDelay =
            TimeSpan.FromMilliseconds(350);
        private static readonly TimeSpan RestartReadinessPollInterval =
            TimeSpan.FromMilliseconds(50);

        private readonly object processGate = new object();
        private readonly SemaphoreSlim restartGate = new SemaphoreSlim(1, 1);
        private AsyncEventHandler<EventArgs> startAsync;
        private AsyncEventHandler<EventArgs> stopAsync;
        private Process activeProcess;
        private int initializationGeneration;
        private int successfulInitializationGeneration;

        public ApexForgeLanguageClient()
        {
            lock (InstanceGate)
            {
                currentInstance = this;
            }
        }

        public string Name => "ApexForge Language Server";

        public IEnumerable<string> ConfigurationSections => null;

        public object InitializationOptions => new
        {
            apexforge = new
            {
                client = "visualstudio",
                milestone = "AFP-P10-T5.6"
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
            add { stopAsync += value; }
            remove { stopAsync -= value; }
        }

        internal static bool IsLoaded
        {
            get
            {
                lock (InstanceGate)
                {
                    return currentInstance != null;
                }
            }
        }

        internal static async Task<bool> RequestRestartAsync()
        {
            ApexForgeLanguageClient client;
            lock (InstanceGate)
            {
                client = currentInstance;
            }

            if (client == null)
            {
                ApexForgeLanguageServerTrace.Write(
                    "ApexForge language-server restart was requested before the language client loaded.");
                return false;
            }

            return await client.RestartAsync().ConfigureAwait(false);
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
            RecordServerInitialization(false);
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
            RecordServerInitialization(false);
            StopActiveProcess();
            return Task.FromResult<InitializationFailureContext>(null);
        }

        public Task OnServerInitializedAsync()
        {
            RecordServerInitialization(true);
            ApexForgeLanguageServerTrace.Write(
                "ApexForge language server initialized successfully.");
            return Task.CompletedTask;
        }

        private async Task<bool> RestartAsync()
        {
            await restartGate.WaitAsync().ConfigureAwait(false);
            try
            {
                AsyncEventHandler<EventArgs> startHandler = startAsync;
                if (startHandler == null)
                {
                    ApexForgeLanguageServerTrace.Write(
                        "ApexForge language-server restart could not begin because StartAsync has no subscriber.");
                    return false;
                }

                ApexForgeLanguageServerTrace.Write(
                    "ApexForge language-server restart requested from Visual Studio.");

                AsyncEventHandler<EventArgs> stopHandler = stopAsync;
                if (stopHandler != null)
                {
                    await stopHandler.InvokeAsync(this, EventArgs.Empty).ConfigureAwait(false);
                }

                StopActiveProcess();
                int initializationBaseline = Volatile.Read(
                    ref initializationGeneration);
                await startHandler.InvokeAsync(this, EventArgs.Empty).ConfigureAwait(false);

                bool initialized = await WaitForServerInitializationAsync(
                    initializationBaseline).ConfigureAwait(false);
                if (!initialized)
                {
                    ApexForgeLanguageServerTrace.Write(
                        "ApexForge language-server restart did not reach initialized state within 15 seconds.");
                    StopActiveProcess();
                    return false;
                }

                await Task.Delay(DocumentResynchronizationDelay).ConfigureAwait(false);
                ApexForgeLanguageServerTrace.Write(
                    "ApexForge language-server restart sequence completed after initialization and document resynchronization.");
                return true;
            }
            catch (Exception error)
            {
                ApexForgeLanguageServerTrace.Write(
                    "ApexForge language-server restart failed: " + error);
                StopActiveProcess();
                return false;
            }
            finally
            {
                restartGate.Release();
            }
        }

        private void RecordServerInitialization(bool succeeded)
        {
            int generation = Interlocked.Increment(
                ref initializationGeneration);
            if (succeeded)
            {
                Volatile.Write(
                    ref successfulInitializationGeneration,
                    generation);
            }
        }

        private async Task<bool> WaitForServerInitializationAsync(
            int initializationBaseline)
        {
            var timer = Stopwatch.StartNew();
            while (timer.Elapsed < RestartInitializationTimeout)
            {
                int observedGeneration = Volatile.Read(
                    ref initializationGeneration);
                if (observedGeneration > initializationBaseline)
                {
                    return Volatile.Read(
                        ref successfulInitializationGeneration)
                        == observedGeneration;
                }

                await Task.Delay(RestartReadinessPollInterval)
                    .ConfigureAwait(false);
            }

            return false;
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
