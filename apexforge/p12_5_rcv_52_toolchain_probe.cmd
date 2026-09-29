@echo off
setlocal
rem Capability probe only: this does not execute an ApexForge program.
set "AF_VS_ROOT="
for /f "usebackq tokens=*" %%I in (`"%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe" -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath`) do set "AF_VS_ROOT=%%I"
if not defined AF_VS_ROOT exit /b 2
call "%AF_VS_ROOT%\Common7\Tools\VsDevCmd.bat" -no_logo -arch=x64 -host_arch=x64
if errorlevel 1 exit /b 3
where cl >nul 2>nul
if errorlevel 1 exit /b 4
cl
exit /b 0
