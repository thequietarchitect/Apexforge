from __future__ import annotations
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

def require(value: bool, message: str) -> None:
    if not value:
        raise AssertionError(message)

def main() -> int:
    from apexforge.native_backend import CanonicalExecutionEnvelope
    valid = CanonicalExecutionEnvelope.from_mapping({
        "VerifiedAirOwner": "air.model.VerifiedAIRProgram",
        "ExecutionPlanOwner": "workflow.air_runner.RegistryExecutionPlan",
        "ProgramFingerprint": "P12-1C-CANONICAL",
    })
    require(valid.is_contract_safe(), "native canonical envelope rejected")
    mismatch_rejected = False
    try:
        CanonicalExecutionEnvelope.from_mapping({
            "VerifiedAirOwner": "wrong.owner",
            "ExecutionPlanOwner": "workflow.air_runner.RegistryExecutionPlan",
            "ProgramFingerprint": "P12-1C-MISMATCH",
        })
    except ValueError:
        mismatch_rejected = True
    require(mismatch_rejected, "native ownership mismatch accepted")
    project = ET.parse(ROOT / "runtimes/dotnet/ApexForge.Runtime.Smoke/ApexForge.Runtime.Smoke.csproj").getroot()
    refs = [node.attrib.get("Include", "") for node in project.findall(".//ProjectReference")]
    require(refs == [r"..\ApexForge.Runtime\ApexForge.Runtime.csproj"], "managed smoke project reference changed")
    managed = (ROOT / "runtimes/dotnet/ApexForge.Runtime/CanonicalExecutionEnvelope.cs").read_text(encoding="utf-8")
    host_text = (ROOT / "runtimes/dotnet/ApexForge.Runtime/ManagedRuntimeHost.cs").read_text(encoding="utf-8")
    require("CanonicalExecutionEnvelope" in managed, "managed envelope missing")
    require("Canonical execution ownership mismatch." in managed, "managed ownership rejection missing")
    require("Admit(CanonicalExecutionEnvelope envelope)" in host_text, "managed admission boundary missing")
    require("ApexForge.VisualStudio" not in managed + host_text, "Visual Studio leaked into managed runtime")
    print("P12_1C_NATIVE_VALID_ENVELOPE_ACCEPTED=PASS")
    print("P12_1C_NATIVE_OWNERSHIP_MISMATCH_REJECTED=PASS")
    print("P12_1C_MANAGED_ADMISSION_BOUNDARY_PRESENT=PASS")
    print("P12_1C_VISUAL_STUDIO_SEMANTIC_DEPENDENCY=False")
    print("P12_1C_CANONICAL_EXECUTION_ENVELOPE_CROSS_TARGET=PASS")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
