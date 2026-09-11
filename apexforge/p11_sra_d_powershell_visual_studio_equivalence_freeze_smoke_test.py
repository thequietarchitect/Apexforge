"""P11 SRA-D PowerShell / Visual Studio equivalence permanent freeze regression."""
import hashlib,json,subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
JP=ROOT/"docs/p11/P11_SRA_D_POWERSHELL_VISUAL_STUDIO_EQUIVALENCE.json"
MP=ROOT/"docs/p11/P11_SRA_D_POWERSHELL_VISUAL_STUDIO_EQUIVALENCE.md"
TAG="afp-p11-sra-c-visual-studio-experimental-acceptance-freeze"
BASE="34ae66b6c2fb8fefa4bfeae9661ec1eac4d6dd84"
BRANCH="p11-sra-d-powershell-visual-studio-equivalence"
SELF="apexforge/p11_sra_d_powershell_visual_studio_equivalence_freeze_smoke_test.py"
EXPECTED_JSON="A3E1B4147672BD4626CC261A5F8029112D8E2F828CF80A207A05870968E24F57"
EXPECTED_MD="29C84AB13C101F53D6801B5E73E41DF2C0E4721643D0AB25AA67CA3430EEB6B0"
ALLOWED=tuple(sorted((SELF,"docs/p11/P11_SRA_D_POWERSHELL_VISUAL_STUDIO_EQUIVALENCE.json","docs/p11/P11_SRA_D_POWERSHELL_VISUAL_STUDIO_EQUIVALENCE.md")))
ANCHORS={"apexforge/language_server/project_definition.py":"CDAD3CA55A6857096D6B3DF6CEDD0F24391A1F3F0531109E958B3F8A96B3F62B","apexforge/p11_src_h_final_integration_regression_freeze_smoke_test.py":"72AC59681E7C4411D92F3DB844E9248C635ADDBC65E27148195B833F0C89194D","examples/P11CapabilityPulse/src/main.apex":"45BD8A338F8CC82B6ED3B730B9C2DD06A9D86FC69FAB0599401CE1F421A26E57","examples/P11CapabilityPulse/src/observer.apex":"6B9D4CFDBE79AAC130F5596737E465D4970FFDF2A123ADDE637F12A404158F71"}

def req(v,m):
    if not v: raise AssertionError(m)
def git(*a):
    return subprocess.run(["git",*a],cwd=ROOT,text=True,capture_output=True,check=False)
def sha(p):
    return hashlib.sha256((ROOT/p).read_bytes()).hexdigest().upper()

d=json.loads(JP.read_text(encoding="utf-8"));m=MP.read_text(encoding="utf-8")
req(sha("docs/p11/P11_SRA_D_POWERSHELL_VISUAL_STUDIO_EQUIVALENCE.json")==EXPECTED_JSON,"JSON hash")
req(sha("docs/p11/P11_SRA_D_POWERSHELL_VISUAL_STUDIO_EQUIVALENCE.md")==EXPECTED_MD,"Markdown hash")
req(d["schema"]==1 and d["stage"]=="P11-SRA-D" and d["status"]=="FROZEN","stage/status")
req(d["scope"]=="POWERSHELL_VISUAL_STUDIO_EQUIVALENCE_ONLY","scope")
req(d["acceptance"]["D8_final_regression"]=="PASS" and d["acceptance"]["freeze_authorized"] is True,"freeze authorization")
req(all(v=="PASS" for k,v in d["acceptance"].items() if k!="freeze_authorized"),"acceptance ledger")
req(d["doctrine"]["ide_semantics_rule"]=="IDE_MUST_NOT_BECOME_SECOND_SEMANTICS_IMPLEMENTATION","IDE doctrine")
req(d["shared_surface_evidence"]["definition_negative"]["ambiguous"]["hidden_editor_winner"] is False,"hidden winner")
req(d["cli_only_canonical_semantics"]["visual_studio_competing_implementation"]=="ABSENT_PASS","competing VS semantics")
req(len(d["historical_classifications"])==5 and all(x["classification"]!="FAIL" for x in d["historical_classifications"]),"historical classifications")
q=d["review_required"];req(len(q)==1 and q[0]["id"]=="SRA-C3A" and q[0]["classification"]=="REVIEW_REQUIRED" and q[0]["regression"]=="NOT_ESTABLISHED","C3A carry")
f=d["future_scope"];req(f["SRA_E"]=="QUEUED" and f["polyplane"]=="DEFERRED_POST_RELEASE" and f["scope_leakage"]=="NOT_ESTABLISHED","future scope")
req(d["production_semantic_mutation"] is False and d["successor"]=="P11-SRA-E","mutation/successor")
z=d["sra_d_freeze"];req(z["tag"]=="afp-p11-sra-d-powershell-visual-studio-equivalence-freeze" and z["final_regression"]=="PASS" and z["governance_review"]=="PASS" and z["release_delta_artifacts"]==3 and z["production_semantic_mutation"] is False,"freeze record")
req(git("branch","--show-current").stdout.strip()==BRANCH,"branch")
r=git("rev-parse",TAG+"^{}");req(r.returncode==0 and r.stdout.strip()==BASE,"predecessor")
req(git("merge-base","--is-ancestor",TAG,"HEAD").returncode==0,"ancestry")
for p,h in ANCHORS.items(): req(sha(p)==h,"anchor "+p)
diff=git("diff","--name-only",TAG,"--");req(diff.returncode==0,"diff")
tracked=[x.strip().replace(chr(92),"/") for x in diff.stdout.splitlines() if x.strip()]
st=git("status","--porcelain=v1","--untracked-files=all");req(st.returncode==0,"status")
untracked=[x[3:].strip().replace(chr(92),"/") for x in st.stdout.splitlines() if x.startswith("?? ")]
req(tuple(sorted(set(tracked+untracked)))==ALLOWED,"release delta")
req("?" not in m and all(ord(c)<128 for c in m),"Markdown encoding")
for s in ("Status: **FROZEN**","PowerShell <-> Visual Studio behavioral and semantic equivalence","IDE must never become a second semantics implementation","| D8 final regression | PASS |","Freeze authorization is **true**","SRA-C3A","REVIEW_REQUIRED","SRA-E optimization acceptance remains queued","P12 is not entered","Polyplane expansion","The SRA-D freeze is **authorized**"): req(s in m,"marker "+s)
print("SRA_D_FREEZE_PREDECESSOR_ANCESTRY=PASS")
print("SRA_D_FREEZE_ACCEPTANCE_LEDGER=PASS")
print("SRA_D_FREEZE_DOCTRINE_ALIGNMENT=PASS")
print("SRA_D_FREEZE_HISTORICAL_CLASSIFICATION=PASS")
print("SRA_D_FREEZE_C3A_REVIEW_CARRY=PASS")
print("SRA_D_FREEZE_FUTURE_SCOPE_BOUNDARY=PASS")
print("SRA_D_FREEZE_PRODUCTION_ANCHORS=PASS")
print("SRA_D_FREEZE_RELEASE_DELTA=EXACTLY_THREE_ARTIFACTS")
print("SRA_D_FREEZE_AUTHORIZED=True")
print("P11_SRA_D_POWERSHELL_VISUAL_STUDIO_EQUIVALENCE_FREEZE=PASS")
