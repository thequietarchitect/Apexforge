# ApexForge Visual Studio Extension

AFP-P10-T5.1 establishes the Visual Studio extension foundation for ApexForge.

## Included in this checkpoint

- A deterministic Visual Studio SDK solution and VSIX project.
- Visual Studio 17.x installation targets for AMD64 and ARM64.
- `.apex` to `apexforge` MEF content-type registration.
- An `AsyncPackage` command shell.
- **Tools > ApexForge Extension Status** for installation verification.
- Static and built-VSIX auditing through ApexForge Python tooling.

## Deferred

- T5.2: syntax classification and editor presentation.
- T5.3: Python language-server process bridge.
- T5.4+: diagnostics, IntelliSense, navigation, formatting, and hardening.

## Build

Open `ApexForge.VisualStudio.sln` in Visual Studio with the **Visual Studio extension development** workload installed. Build the solution or press **F5** to launch the Experimental Instance.

The extension targets .NET Framework 4.7.2 and the stable Visual Studio 17.x SDK line.
