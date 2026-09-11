from pathlib import Path
import ast, hashlib, json, runpy, subprocess

ROOT = Path(__file__).resolve().parent.parent
EXPECTED_BRANCH = "p11-sra-e-optimization-acceptance-equivalence"
PREDECESSOR_TAG = "afp-p11-sra-d-powershell-visual-studio-equivalence-freeze"
PREDECESSOR_COMMIT = "01364c7a65280371e07f3b37ebe1a7f92a87040e"
EXPECTED_FREEZE_TAG = "afp-p11-sra-e-optimization-acceptance-equivalence-freeze"
JSON_PATH = "docs/p11/P11_SRA_E_OPTIMIZATION_ACCEPTANCE_EQUIVALENCE.json"
MD_PATH = "docs/p11/P11_SRA_E_OPTIMIZATION_ACCEPTANCE_EQUIVALENCE.md"
SMOKE_PATH = "apexforge/p11_sra_e_optimization_acceptance_equivalence_freeze_smoke_test.py"
FINAL_JSON_SHA256 = "E558A1F5AA81AD407BAB94A06506A41AA878387FB9883EA8363D0F28136868A6"
FINAL_MD_SHA256 = "1EFB7EEA77B6ED9CA3A3440B4B96E3923F843C80721A29774BB4268CF82A86E4"
RELEASE_FILES = tuple(sorted((JSON_PATH, MD_PATH, SMOKE_PATH)))

def require(value, message):
    if not value:
        raise AssertionError(message)

def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True, check=False)

def sha256(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest().upper()

def repository_status():
    return git("status", "--porcelain=v1", "--untracked-files=all").stdout

def assert_release_shape():
    branch = git("branch", "--show-current").stdout.strip()
    head = git("rev-parse", "HEAD").stdout.strip()
    predecessor = git("rev-parse", PREDECESSOR_TAG + "^{}").stdout.strip()
    require(branch != "", "repository is detached or branch cannot be determined")
    require(predecessor == PREDECESSOR_COMMIT, "SRA-D predecessor identity changed")
    tag_probe = git("rev-parse", "--verify", EXPECTED_FREEZE_TAG + "^{}")
    if tag_probe.returncode == 0:
        freeze = tag_probe.stdout.strip()
        parent = git("rev-parse", freeze + "^").stdout.strip()
        require(parent == PREDECESSOR_COMMIT, "SRA-E freeze parent is not exact SRA-D freeze")
        changed = tuple(sorted(x for x in git("diff", "--name-only", PREDECESSOR_COMMIT, freeze, "--").stdout.splitlines() if x.strip()))
        require(changed == RELEASE_FILES, "tagged SRA-E release delta changed: " + repr(changed))
        require(git("merge-base", "--is-ancestor", freeze, "HEAD").returncode == 0, "tagged SRA-E freeze is not an ancestor of HEAD")
        return "TAGGED", freeze
    if head == PREDECESSOR_COMMIT:
        require(branch == EXPECTED_BRANCH, "prefreeze execution is on unexpected branch")
        expected = tuple(sorted("?? " + x for x in RELEASE_FILES))
        observed = tuple(sorted(x for x in repository_status().splitlines() if x.strip()))
        require(observed == expected, "prefreeze release delta changed: " + repr(observed))
        return "PREFREEZE", head
    parent = git("rev-parse", "HEAD^").stdout.strip()
    require(parent == PREDECESSOR_COMMIT, "committed untagged SRA-E parent is not exact SRA-D freeze")
    changed = tuple(sorted(x for x in git("diff", "--name-only", PREDECESSOR_COMMIT, "HEAD", "--").stdout.splitlines() if x.strip()))
    require(changed == RELEASE_FILES, "committed SRA-E release delta changed: " + repr(changed))
    require(repository_status() == "", "committed SRA-E worktree is not clean")
    return "COMMITTED_UNTAGGED", head

def assert_governance_documents():
    require(sha256(JSON_PATH) == FINAL_JSON_SHA256, "final SRA-E JSON hash changed")
    require(sha256(MD_PATH) == FINAL_MD_SHA256, "final SRA-E Markdown hash changed")
    jb = (ROOT / JSON_PATH).read_bytes()
    mb = (ROOT / MD_PATH).read_bytes()
    require(all(b < 128 for b in jb) and all(b < 128 for b in mb), "SRA-E governance artifacts lost ASCII stability")
    data = json.loads(jb.decode("ascii"))
    require(data.get("status") == "FROZEN", "SRA-E governance status is not FROZEN")
    acceptance = data.get("acceptance", {})
    require(acceptance.get("E7_final_regression") == "PASS", "SRA-E E7 final regression is not PASS")
    require(acceptance.get("freeze_authorized") is True, "SRA-E freeze authorization is not true")
    require(data.get("production_semantic_mutation") is False, "SRA-E governance claims production semantic mutation")
    require(data.get("tracked_delta_from_sra_d") == 0, "SRA-E governance tracked-delta claim changed")
    future = data.get("future_scope", {})
    require(future.get("SRA_F") == "QUEUED", "SRA-F state changed")
    require(future.get("P12") == "NOT_ENTERED", "P12 entered during SRA-E")
    require(future.get("polyplane") == "DEFERRED_POST_RELEASE", "Polyplane entered during SRA-E")
    return data

def assert_anchor_hashes(data):
    anchors = data.get("anchors", {})
    require(len(anchors) == 15, "unexpected SRA-E anchor count")
    for relative, expected in sorted(anchors.items()):
        require((ROOT / relative).is_file(), "missing SRA-E anchor: " + relative)
        require(sha256(relative) == expected, "SRA-E anchor hash changed: " + relative)

def assert_cache_boundary():
    ns = runpy.run_path(str(ROOT / "apexforge/p11_12h_three_layer_incremental_cache_final_acceptance_smoke_test.py"))
    ns["_assert_surface_census"]()
    ns["_assert_fixed_corpus_equivalence"]()
    ns["_assert_optimization_shape"]()
    report, loaded, sources, selected, uncached, warm, reduction, ratio = ns["_paired_performance_acceptance"]()
    changed_uncached, changed_cached, outcomes = ns["_changed_build_acceptance"](loaded, sources, selected)
    require(tuple(outcomes) == ("hit", "stale", "invalidated", "stored", "hit", "miss", "stored"), "cache invalidation sequence changed")
    print("CACHE_FIXED_CORPUS_EQUIVALENCE=PASS")
    print("CACHE_INVALIDATION_SEQUENCE=" + ",".join(outcomes))

def assert_tap_boundary():
    ns = runpy.run_path(str(ROOT / "apexforge/p11_11g_final_tap_check_integration_regression_freeze_smoke_test.py"))
    ns["_assert_final_public_contract"]()
    ns["_assert_final_capability_census"]()
    ns["_assert_cli_boundary"]()
    observable = tuple(ns["OBSERVABLE_CATEGORIES"])
    deferred = tuple(ns["DEFERRED_CATEGORIES"])
    require("optimization-decisions" in deferred, "optimization-decisions is no longer deferred")
    require("optimization-decisions" not in observable, "optimization-decisions became directly observable")
    print("TAP_OBSERVATIONAL_NEUTRALITY=PASS")

def assert_optimized_air_boundary():
    ns = runpy.run_path(str(ROOT / "apexforge/p11_9i_final_aether_air_2_integration_regression_freeze_smoke_test.py"))
    ns["test_public_surface_exactness"]()
    ns["test_integrated_b_through_h_lineage"]()
    ns["test_non_operational_production_boundary"]()
    projection = (ROOT / "apexforge/aether_air/projection.py").read_text(encoding="utf-8")
    tree = ast.parse(projection, filename="apexforge/aether_air/projection.py")
    forbidden = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            name = func.id if isinstance(func, ast.Name) else func.attr if isinstance(func, ast.Attribute) else ""
            if name in ("compile", "exec", "eval"):
                forbidden.append(name)
    require(not forbidden, "optimized-air projection gained executable primitives")
    print("OPTIMIZED_AIR_NON_OPERATIONAL_BOUNDARY=PASS")

def assert_python_parse():
    listed = git("ls-files", "*.py")
    require(listed.returncode == 0, "unable to enumerate tracked Python files")
    files = set(x for x in listed.stdout.splitlines() if x.strip())
    files.add(SMOKE_PATH)
    failures = []
    for relative in sorted(files):
        path = ROOT / relative
        if not path.is_file():
            continue
        try:
            ast.parse(path.read_text(encoding="utf-8-sig"), filename=relative)
        except Exception as exc:
            failures.append((relative, type(exc).__name__, str(exc)))
    print("PYTHON_PARSE_FILE_COUNT=" + str(len(files)))
    print("PYTHON_PARSE_FAILURE_COUNT=" + str(len(failures)))
    for relative, kind, message in failures:
        print("PYTHON_PARSE_FAILURE=" + relative + "|" + kind + "|" + message)
    require(not failures, "Python parse regression detected")

def main():
    before = repository_status()
    mode, identity = assert_release_shape()
    print("SRA_E_RELEASE_SHAPE_MODE=" + mode)
    print("SRA_E_RELEASE_IDENTITY=" + identity)
    data = assert_governance_documents()
    print("SRA_E_GOVERNANCE_DOCUMENTS=PASS")
    assert_anchor_hashes(data)
    print("SRA_E_RECORDED_ANCHORS=PASS")
    assert_cache_boundary()
    assert_tap_boundary()
    assert_optimized_air_boundary()
    assert_python_parse()
    require(git("diff", "--check").returncode == 0, "git diff --check failed")
    source = (ROOT / SMOKE_PATH).read_text(encoding="ascii")
    require(not any(line.endswith(" ") or line.endswith(chr(9)) for line in source.splitlines()), "freeze smoke contains trailing whitespace")
    after = repository_status()
    require(after == before, "SRA-E freeze smoke mutated repository status")
    print("PRODUCTION_SEMANTIC_MUTATION=False")
    print("P12_ENTERED=False")
    print("POLYPLANE_ENTERED=False")
    print("REPOSITORY_STATUS_UNCHANGED=True")
    print("P11_SRA_E_OPTIMIZATION_ACCEPTANCE_EQUIVALENCE_FREEZE_SMOKE=PASS")

if __name__ == "__main__":
    main()
