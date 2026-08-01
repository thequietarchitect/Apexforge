using System;
using System.Collections.Generic;
using System.IO;
using System.Reflection;

namespace GravitasStudios.ApexForge.VisualStudio.LanguageServer
{
    internal sealed class ApexForgeLanguageServerLaunch
    {
        internal ApexForgeLanguageServerLaunch(
            string repositoryRoot,
            string pythonExecutable,
            string scriptPath,
            string arguments)
        {
            RepositoryRoot = repositoryRoot;
            PythonExecutable = pythonExecutable;
            ScriptPath = scriptPath;
            Arguments = arguments;
        }

        internal string RepositoryRoot { get; }
        internal string PythonExecutable { get; }
        internal string ScriptPath { get; }
        internal string Arguments { get; }
        internal string WorkingDirectory => Path.Combine(RepositoryRoot, "apexforge");
    }

    internal static class ApexForgeLanguageServerLocator
    {
        internal const string RepositoryEnvironmentVariable = "APEXFORGE_REPOSITORY_ROOT";
        internal const string PythonEnvironmentVariable = "APEXFORGE_PYTHON";
        internal const string RelativeServerScript = @"apexforge\apexforge_lsp.py";

        internal static ApexForgeLanguageServerLaunch Resolve()
        {
            string repositoryRoot = ResolveRepositoryRoot();
            string pythonExecutable = Environment.GetEnvironmentVariable(PythonEnvironmentVariable);
            if (string.IsNullOrWhiteSpace(pythonExecutable))
            {
                pythonExecutable = "py.exe";
            }

            string scriptPath = Path.Combine(repositoryRoot, RelativeServerScript);
            string arguments = QuoteArgument(scriptPath) + " --stdio";
            return new ApexForgeLanguageServerLaunch(
                repositoryRoot,
                pythonExecutable,
                scriptPath,
                arguments);
        }

        internal static string ResolveRepositoryRoot()
        {
            var seen = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
            foreach (string candidate in CandidateRoots())
            {
                foreach (string expanded in ExpandCandidate(candidate))
                {
                    string normalized;
                    try
                    {
                        normalized = Path.GetFullPath(expanded);
                    }
                    catch (Exception error) when (
                        error is ArgumentException
                        || error is NotSupportedException
                        || error is PathTooLongException)
                    {
                        continue;
                    }

                    if (seen.Add(normalized) && IsRepositoryRoot(normalized))
                    {
                        return normalized;
                    }
                }
            }

            throw new DirectoryNotFoundException(
                "Could not locate the ApexForge repository. Set "
                + RepositoryEnvironmentVariable
                + " to the repository root, for example "
                + @"C:\Users\Owner\source\repos\ApexForge" + ".");
        }

        private static IEnumerable<string> CandidateRoots()
        {
            string configured = Environment.GetEnvironmentVariable(RepositoryEnvironmentVariable);
            if (!string.IsNullOrWhiteSpace(configured))
            {
                yield return configured;
            }

            yield return Environment.CurrentDirectory;
            yield return AppDomain.CurrentDomain.BaseDirectory;

            string assemblyLocation = Assembly.GetExecutingAssembly().Location;
            if (!string.IsNullOrWhiteSpace(assemblyLocation))
            {
                yield return Path.GetDirectoryName(assemblyLocation);
            }

            string profile = Environment.GetFolderPath(Environment.SpecialFolder.UserProfile);
            if (!string.IsNullOrWhiteSpace(profile))
            {
                yield return Path.Combine(profile, "source", "repos", "ApexForge");
                yield return Path.Combine(profile, "Documents", "GitHub", "ApexForge");
            }
        }

        private static IEnumerable<string> ExpandCandidate(string candidate)
        {
            if (string.IsNullOrWhiteSpace(candidate))
            {
                yield break;
            }

            DirectoryInfo current;
            try
            {
                current = new DirectoryInfo(candidate);
            }
            catch (Exception error) when (
                error is ArgumentException
                || error is NotSupportedException
                || error is PathTooLongException)
            {
                yield break;
            }

            for (int depth = 0; current != null && depth < 12; depth++)
            {
                yield return current.FullName;
                current = current.Parent;
            }
        }

        private static bool IsRepositoryRoot(string candidate)
        {
            return File.Exists(Path.Combine(candidate, RelativeServerScript))
                && File.Exists(Path.Combine(candidate, "apexforge", "language_server", "server.py"))
                && File.Exists(Path.Combine(candidate, "apexforge", "language_server", "integration.py"));
        }

        private static string QuoteArgument(string value)
        {
            if (value == null)
            {
                throw new ArgumentNullException(nameof(value));
            }

            return "\"" + value.Replace("\"", "\\\"") + "\"";
        }
    }
}
