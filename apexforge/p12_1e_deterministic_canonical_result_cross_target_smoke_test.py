from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

def require(value: bool, message: str) -> None:
    if not value:
        raise AssertionError(message)

def main() -> int:
    from apexforge.native_backend import CanonicalExecutionPayload, CanonicalExecutionResult, CanonicalExecutionValue
    inputs = CanonicalExecutionPayload((
        CanonicalExecutionValue("message", "UTF8", "hello"),
        CanonicalExecutionValue("enabled", "BOOL", "true"),
        CanonicalExecutionValue("count", "I64", "42"),
    ))
    input_fingerprint = inputs.fingerprint()
    outputs = CanonicalExecutionPayload((
        CanonicalExecutionValue("answer", "I64", "42"),
        CanonicalExecutionValue("summary", "UTF8", "done"),
    ))
    result = CanonicalExecutionResult(input_fingerprint, "SUCCESS", outputs)
    result.validate()
    fingerprint = result.fingerprint()
    require(len(fingerprint) == 64, "native result fingerprint length changed")
    invalid_rejected = False
    try:
        CanonicalExecutionResult(input_fingerprint.lower(), "SUCCESS", outputs).validate()
    except ValueError:
        invalid_rejected = True
    require(invalid_rejected, "native lowercase input fingerprint accepted")
    status_rejected = False
    try:
        CanonicalExecutionResult(input_fingerprint, "UNKNOWN", outputs).validate()
    except ValueError:
        status_rejected = True
    require(status_rejected, "native unsupported result status accepted")
    managed = (ROOT / "runtimes/dotnet/ApexForge.Runtime/CanonicalExecutionResult.cs").read_text(encoding="utf-8")
    host_text = (ROOT / "runtimes/dotnet/ApexForge.Runtime/ManagedRuntimeHost.cs").read_text(encoding="utf-8")
    require("CanonicalExecutionResult" in managed, "managed canonical result missing")
    require('Status is not ("SUCCESS" or "FAILURE")' in managed, "managed result status contract changed")
    require("SHA256.HashData" in managed, "managed result fingerprint missing")
    require("AdmitResult(CanonicalExecutionResult result)" in host_text, "managed result admission boundary missing")
    require("ApexForge.VisualStudio" not in managed + host_text, "Visual Studio leaked into result runtime")
    print(f"NATIVE_RESULT_FINGERPRINT={fingerprint}")
    print("P12_1E_NATIVE_VALID_RESULT_ACCEPTED=PASS")
    print("P12_1E_NATIVE_NONCANONICAL_RESULT_REJECTED=PASS")
    print("P12_1E_NATIVE_INVALID_STATUS_REJECTED=PASS")
    print("P12_1E_CANONICAL_RESULT_CROSS_TARGET=PASS")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
