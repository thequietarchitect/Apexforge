using System;
using System.Runtime.InteropServices;

namespace ApexForge.Runtime;

internal static partial class ManagedNativeAbi
{
    internal const string ProfileId = "apexforge.win-x64-managed-native-abi/v1";
    internal const string LibraryName = "apexforge_native";
    internal const int Success = 0;

    internal static void EnsureSupportedHost()
    {
        if (!OperatingSystem.IsWindows() || RuntimeInformation.ProcessArchitecture != Architecture.X64 || IntPtr.Size != 8)
        {
            throw new PlatformNotSupportedException("ApexForge native ABI v1 requires Windows x64 with 64-bit pointers.");
        }
    }

    [LibraryImport(LibraryName, EntryPoint = "apexforge_release_handle")]
    internal static partial int ReleaseHandle(nint handle);

    [LibraryImport(LibraryName, EntryPoint = "apexforge_release_buffer")]
    internal static partial int ReleaseBuffer(nint data, ulong length);
}

internal sealed class ApexForgeNativeSafeHandle : SafeHandle
{
    private ApexForgeNativeSafeHandle() : base(IntPtr.Zero, ownsHandle: true)
    {
    }

    internal ApexForgeNativeSafeHandle(nint value, bool ownsHandle = true) : base(IntPtr.Zero, ownsHandle)
    {
        SetHandle(value);
    }

    public override bool IsInvalid => handle == IntPtr.Zero;

    protected override bool ReleaseHandle()
    {
        return ManagedNativeAbi.ReleaseHandle(handle) == ManagedNativeAbi.Success;
    }
}

internal sealed class ApexForgeNativeOwnedBufferHandle : SafeHandle
{
    private ApexForgeNativeOwnedBufferHandle() : base(IntPtr.Zero, ownsHandle: true)
    {
        Length = 0;
    }

    internal ApexForgeNativeOwnedBufferHandle(nint value, ulong length, bool ownsHandle = true) : base(IntPtr.Zero, ownsHandle)
    {
        Length = length;
        SetHandle(value);
    }

    internal ulong Length { get; }

    public override bool IsInvalid => handle == IntPtr.Zero;

    protected override bool ReleaseHandle()
    {
        return ManagedNativeAbi.ReleaseBuffer(handle, Length) == ManagedNativeAbi.Success;
    }
}
