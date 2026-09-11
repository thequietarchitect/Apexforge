from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

def require(value: bool, message: str) -> None:
    if not value:
        raise AssertionError(message)

def main() -> int:
    from apexforge.native_backend import CanonicalExecutionPayload, CanonicalExecutionValue
    payload = CanonicalExecutionPayload((
        CanonicalExecutionValue("message", "UTF8", "hello"),
        CanonicalExecutionValue("enabled", "BOOL", "true"),
        CanonicalExecutionValue("count", "I64", "42"),
    ))
    payload.validate()
    fingerprint = payload.fingerprint()
    require(len(fingerprint) == 64, "native payload fingerprint length changed")
    rejected = False
    try:
        CanonicalExecutionPayload((CanonicalExecutionValue("count", "I64", "0042"),)).validate()
    except ValueError:
        rejected = True
    require(rejected, "native noncanonical I64 accepted")
    duplicate_rejected = False
    try:
        CanonicalExecutionPayload((
            CanonicalExecutionValue("x", "BOOL", "true"),
            CanonicalExecutionValue("x", "BOOL", "false"),
        )).validate()
    except ValueError:
        duplicate_rejected = True
    require(duplicate_rejected, "native duplicate value name accepted")
    managed_value = (ROOT / "runtimes/dotnet/ApexForge.Runtime/CanonicalExecutionValue.cs").read_text(encoding="utf-8")
    managed_payload = (ROOT / "runtimes/dotnet/ApexForge.Runtime/CanonicalExecutionPayload.cs").read_text(encoding="utf-8")
    managed_host = (ROOT / "runtimes/dotnet/ApexForge.Runtime/ManagedRuntimeHost.cs").read_text(encoding="utf-8")
    require("CanonicalExecutionValue" in managed_value, "managed canonical value missing")
    require('case "BOOL":' in managed_value and 'case "I64":' in managed_value and 'case "UTF8":' in managed_value, "managed wire representation set changed")
    require("SHA256.HashData" in managed_payload, "managed payload fingerprint missing")
    require("AdmitPayload(CanonicalExecutionPayload payload)" in managed_host, "managed payload admission boundary missing")
    require("ApexForge.VisualStudio" not in managed_value + managed_payload + managed_host, "Visual Studio leaked into payload runtime")
    print(f"NATIVE_PAYLOAD_FINGERPRINT={fingerprint}")
    print("P12_1D_NATIVE_VALID_PAYLOAD_ACCEPTED=PASS")
    print("P12_1D_NATIVE_NONCANONICAL_VALUE_REJECTED=PASS")
    print("P12_1D_NATIVE_DUPLICATE_NAME_REJECTED=PASS")
    print("P12_1D_WIRE_REPRESENTATIONS=BOOL,I64,UTF8")
    print("P12_1D_CANONICAL_EXECUTION_PAYLOAD_VALUE_CROSS_TARGET=PASS")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
