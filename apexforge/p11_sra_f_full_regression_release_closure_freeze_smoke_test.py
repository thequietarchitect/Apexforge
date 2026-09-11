from __future__ import annotations
import json
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
JSON_PATH = REPO / "docs/p11/P11_SRA_F_FULL_REGRESSION_RELEASE_CLOSURE.json"
MD_PATH = REPO / "docs/p11/P11_SRA_F_FULL_REGRESSION_RELEASE_CLOSURE.md"
SMOKE_PATH = REPO / "apexforge/p11_sra_f_full_regression_release_closure_freeze_smoke_test.py"
BRANCH = "p11-sra-f-full-regression-release-closure"
PREDECESSOR = "f7eae1949f1cc859799bb72a490ed2aa4b6ff261"
PREDECESSOR_TAG = "afp-p11-sra-e-optimization-acceptance-equivalence-freeze"
FREEZE_TAG = "afp-p11-sra-f-full-regression-release-closure-freeze"
ARTIFACTS = ("docs/p11/P11_SRA_F_FULL_REGRESSION_RELEASE_CLOSURE.json", "docs/p11/P11_SRA_F_FULL_REGRESSION_RELEASE_CLOSURE.md", "apexforge/p11_sra_f_full_regression_release_closure_freeze_smoke_test.py")

def require(value: bool, message: str) -> None:
    if not value:
        raise AssertionError(message)

def git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=REPO, text=True, capture_output=True)

def rev(*args: str) -> str:
    result = git("rev-parse", *args)
    require(result.returncode == 0, "git rev-parse failed: " + " ".join(args))
    return result.stdout.strip()

def main() -> int:
    require(JSON_PATH.is_file(), "freeze JSON missing")
    require(MD_PATH.is_file(), "freeze Markdown missing")
    require(SMOKE_PATH.is_file(), "freeze smoke missing")
    data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    require(data["schema"] == 1, "schema changed")
    require(data["kind"] == "apexforge.p11.sra-f.full-regression-release-closure", "kind changed")
    require(data["stage"] == "P11-SRA-F", "stage changed")
    require(data["state"] == "FROZEN_RELEASE_CLOSURE", "state changed")
    require(data["branch"] == BRANCH, "branch record changed")
    require(data["predecessor"]["commit"] == PREDECESSOR, "predecessor changed")
    require(data["predecessor"]["tag"] == PREDECESSOR_TAG, "predecessor tag changed")
    require(data["freeze"]["tag"] == FREEZE_TAG, "freeze tag changed")
    require(data["freeze"]["artifact_count"] == 3, "artifact count changed")
    require(data["release"]["p12"] == "NOT_ENTERED", "P12 entry changed")
    require(all(data["stages"][name] == "PASS" for name in ("F0", "F1", "F2", "F3", "F4", "F5", "F6")), "stage closure changed")
    require(data["regression"]["inventory"] == 237, "regression inventory changed")
    require(data["regression"]["reconciled_failures"] == 139, "reconciled count changed")
    require(data["regression"]["unresolved_execution_failures"] == 0, "unresolved regression count changed")
    require(data["regression"]["current_semantic_regressions"] == 0, "semantic regression count changed")
    require(data["terminal_candidate"]["permanent_sra_smokes"] == 11, "SRA smoke count changed")
    require(data["terminal_candidate"]["current_pass"] == 10, "SRA current pass count changed")
    require(data["terminal_candidate"]["historical_branch_contract"] == 1, "historical branch count changed")
    require(data["terminal_candidate"]["powershell_real_apex_acceptance"] == "PASS", "PowerShell acceptance changed")
    require(data["terminal_candidate"]["tracked_python_files"] == 624, "Python census changed")
    require(data["terminal_candidate"]["python_ast_parse_failures"] == 0, "Python parse result changed")
    review = data["carried_review"]
    require(review["id"] == "SRA-C3A", "carried review identity changed")
    require(review["classification"] == "REVIEW_REQUIRED", "SRA-C3A classification changed")
    require(review["regression"] == "NOT_ESTABLISHED", "SRA-C3A regression status changed")
    require(review["resolution"] == "NOT_CLAIMED", "SRA-C3A resolution changed")
    require(review["current_release_blocker"] == "NOT_ESTABLISHED", "SRA-C3A blocker status changed")
    require(tuple(data["freeze_artifacts"]) == ARTIFACTS, "freeze artifact inventory changed")
    markdown = MD_PATH.read_text(encoding="utf-8")
    require("SRA-F0 through SRA-F6 are closed PASS." in markdown, "Markdown closure ruling changed")
    require("REVIEW_REQUIRED" in markdown and "NOT_ESTABLISHED" in markdown and "NOT_CLAIMED" in markdown, "Markdown SRA-C3A carry changed")
    require(rev(PREDECESSOR_TAG + "^{}") == PREDECESSOR, "predecessor tag identity changed")
    head = rev("HEAD")
    status = git("status", "--porcelain=v1", "--untracked-files=all")
    require(status.returncode == 0, "git status failed")
    rows = [line for line in status.stdout.splitlines() if line]
    paths = {line[3:].replace("\\\\", "/") for line in rows}
    tag = git("rev-parse", FREEZE_TAG + "^{}")
    tag_exists = tag.returncode == 0
    mode = ""
    if tag_exists:
        require(tag.stdout.strip() == head, "freeze tag does not point at HEAD")
        require(not rows, "tagged freeze worktree is not clean")
        require(rev("HEAD^") == PREDECESSOR, "tagged freeze parent changed")
        changed = set(git("diff", "--name-only", PREDECESSOR, "HEAD", "--").stdout.splitlines())
        require(changed == set(ARTIFACTS), "tagged freeze delta changed")
        mode = "TAGGED"
    elif head == PREDECESSOR:
        require(paths == set(ARTIFACTS), "prefreeze status contains unexpected paths")
        require(all(line.startswith("?? ") for line in rows), "prefreeze artifacts must be untracked")
        mode = "PREFREEZE"
    else:
        require(not rows, "committed untagged freeze worktree is not clean")
        require(rev("HEAD^") == PREDECESSOR, "freeze commit parent changed")
        changed = set(git("diff", "--name-only", PREDECESSOR, "HEAD", "--").stdout.splitlines())
        require(changed == set(ARTIFACTS), "freeze commit delta changed")
        mode = "COMMITTED_UNTAGGED"
    print("P11_SRA_F_MODE=" + mode)
    print("P11_SRA_F_REGRESSION_INVENTORY=237")
    print("P11_SRA_F_RECONCILED_FAILURES=139")
    print("P11_SRA_F_UNRESOLVED_EXECUTION_FAILURES=0")
    print("P11_SRA_F_CURRENT_SEMANTIC_REGRESSIONS=0")
    print("P11_SRA_F_SRA_C3A=REVIEW_REQUIRED_NOT_ESTABLISHED_NOT_CLAIMED")
    print("P11_SRA_F_P12_ENTRY=NOT_ENTERED")
    print("P11_SRA_F_FULL_REGRESSION_RELEASE_CLOSURE_FREEZE_SMOKE=PASS")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
