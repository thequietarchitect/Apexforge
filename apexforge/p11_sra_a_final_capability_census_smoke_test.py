# P11 SRA-A frozen final capability census regression.
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs/p11/P11_SRA_A_FINAL_CAPABILITY_CENSUS.json"

def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)

def main() -> int:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    require(data["schema"] == "apexforge.p11-sra-final-capability-census/v2", "schema changed")
    require(data["stage"] == "P11-SRA-A", "stage changed")
    require(data["status"] == "FROZEN", "census is not frozen")
    census = data["census"]
    require(census["source_language"]["core_source_word_union"] == 29, "source word count changed")
    require(census["standard_library"]["version"] == "10.12", "stdlib version changed")
    require(census["standard_library"]["builtin_functions"] == 134, "builtin count changed")
    require(census["standard_library"]["generic_builtins"] == 16, "generic builtin count changed")
    require(census["standard_library"]["builtin_types"] == 11, "builtin type count changed")
    require(census["standard_library"]["groups"] == 12, "stdlib group count changed")
    require(census["cli"]["top_level_command_count"] == 9, "top-level CLI count changed")
    require(census["cli"]["nested_action_count"] == 4, "nested CLI action count changed")
    require(census["cli"]["public_route_count"] == 13, "CLI public route count changed")
    require(census["public_package_exports"]["explicit_qualified_exports"] == 423, "public export count changed")
    require(census["schemas"]["explicit_literal_contracts"] == 55, "schema contract count changed")
    require(census["diagnostics"]["production_code_union"] == 160, "diagnostic count changed")
    require(census["semantic_lattice"]["core_axes"] == 8, "semantic axis count changed")
    require(census["quad_vector"]["operational_capability_modules"] == 19, "QV operational count changed")
    require(census["aether_air"]["core_behavior_kinds"] == 4, "AETHER behavior count changed")
    require(census["semantic_decisions"]["core_convergence_policies"] == 3, "policy count changed")
    require(census["packages_and_rich_documents"]["package_tiers"] == 4, "package tier count changed")
    require(census["packages_and_rich_documents"]["rich_document_block_kinds"] == 7, "rich-document kind count changed")
    require(census["interchange"]["operations"] == 2, "interchange operation count changed")
    require(census["tam"]["implementation_modules"] == 3, "TAM module count changed")
    require(census["tam"]["root_public_exports"] == 27, "TAM export count changed")
    require(census["tam"]["trace_domains"] == 10, "TAM domain count changed")
    require(census["incremental_cache"]["implementation_modules"] == 6, "cache module count changed")
    require(census["incremental_cache"]["layers"] == 3, "cache layer count changed")
    require(census["agents"]["implementation_modules"] == 7, "agent module count changed")
    require(census["agents"]["module_public_contract_elements"] == 10, "agent contract count changed")
    require(census["identity_nesting_resolution"]["owner_files"] == 6, "identity owner count changed")
    require(census["identity_nesting_resolution"]["explicit_exports"] == 17, "identity export count changed")
    require(census["authority_workflow_governance"]["owner_files"] == 24, "authority/workflow owner count changed")
    require(census["authority_workflow_governance"]["public_class_declarations"] == 45, "authority/workflow class count changed")
    require(census["authority_workflow_governance"]["public_function_declarations"] == 23, "authority/workflow function count changed")
    require(census["freeze_tags"]["total"] == 166, "pre-SRA freeze-tag census changed")
    require(census["freeze_tags"]["p10"] == 7, "P10 freeze-tag census changed")
    require(census["freeze_tags"]["p11"] == 157, "P11 freeze-tag census changed")
    require(census["contract_fingerprints"]["canonical_public_hash_anchors"] == 37, "hash anchor count changed")
    require(census["contract_fingerprints"]["public_fingerprint_functions"] == 44, "fingerprint function count changed")
    require(census["repository_scale"]["tracked_python"] == 612, "terminal-P11 tracked Python baseline changed")
    require(census["repository_scale"]["python_parse_pass"] == 612, "terminal-P11 Python parse baseline changed")
    require(census["repository_scale"]["discoverable_smoke_tests_at_terminal_p11"] == 277, "terminal-P11 smoke baseline changed")
    require(census["repository_scale"]["routed_verification_surfaces"] == 178, "routed verification baseline changed")
    for key in ("builtin_functions", "generic_builtins", "builtin_types", "standard_library_groups"):
        require(data["p10_reconciliation"][key]["delta"] == 0, "P10 reconciliation drift: " + key)
    require(data["milestone_gap_expansion"]["original_gap_count"] == 5, "original gap count changed")
    require(data["milestone_gap_expansion"]["status"] == "APPLIED", "five-gap expansion not applied")
    release = data["release_acceptance"]
    require(release["current_state_census"] == "PASS", "current-state census not PASS")
    require(release["p10_standard_library_reconciliation"] == "PASS", "P10 reconciliation not PASS")
    require(release["per_milestone_p11_reconciliation"] == "PASS", "P11 milestone reconciliation not PASS")
    require(release["final_capability_census"] == "PASS", "final capability census not PASS")
    require(release["freeze_authorized"] is True, "SRA-A freeze not authorized")
    require(release["scope"] == "FINAL_CAPABILITY_CENSUS_ONLY", "SRA-A scope changed")
    freeze = data["sra_a_freeze"]
    require(freeze["tag"] == "afp-p11-sra-a-final-capability-census-freeze", "freeze tag changed")
    require(freeze["baseline_terminal_p11_commit"] == "1d2a6b8fc43eeb361b684f89f6486c9c90a7b14c", "terminal P11 baseline changed")
    require(freeze["expanded_census_gap_count"] == 0, "census gaps reopened")
    require(freeze["expanded_census_gaps"] == [], "census gap list reopened")
    require(freeze["compiler_tam_reconciliation"] == "ACCOUNTED_DEDICATED", "Compiler TAM reconciliation changed")
    require(freeze["production_mutation"] is False, "production mutation recorded")
    require(freeze["preexisting_tracked_file_mutation"] is False, "preexisting tracked-file mutation recorded")
    print("P11_SRA_A_FINAL_CAPABILITY_CENSUS=PASS")
    print("P11_SRA_A_CURRENT_STATE_CENSUS=PASS")
    print("P11_SRA_A_P10_RECONCILIATION=PASS")
    print("P11_SRA_A_P11_MILESTONE_RECONCILIATION=PASS")
    print("P11_SRA_A_CENSUS_GAPS=0")
    print("P11_SRA_A_COMPILER_TAM=ACCOUNTED_DEDICATED")
    print("P11_SRA_A_FREEZE_SCOPE=FINAL_CAPABILITY_CENSUS_ONLY")
    print("P11_SRA_A_FREEZE=PASS")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
