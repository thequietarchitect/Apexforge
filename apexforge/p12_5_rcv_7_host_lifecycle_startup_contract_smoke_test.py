from __future__ import annotations
import json, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def req(c,m):
    if not c: raise AssertionError(m)

def run(*a):
    return subprocess.run(a,cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)

def main():
    print('=== P12.5-RCV-7 HOST LIFECYCLE AND STARTUP CONTRACT ===')
    r5=ROOT/'apexforge/p12_5_rcv_6_managed_host_project_skeleton_smoke_test.py'
    r6=ROOT/'apexforge/p12_5_rcv_6_managed_host_project_skeleton_smoke_test.py'
    req(r5.exists(),'RCV-5 smoke missing'); req(r6.exists(),'RCV-6 smoke missing')
    for label,p in [('RCV6_PREDECESSOR',r5),('RCV6',r6)]:
        cp=run(sys.executable,str(p))
        req(cp.returncode==0,f'{label} regression failed:\n{cp.stdout}\n{cp.stderr}')
    data=json.loads((ROOT/'apexforge/p12_5_rcv_7_host_lifecycle_startup_contract.json').read_text(encoding='utf-8'))
    req(data['profile']=='apexforge.p12.host-lifecycle-startup-contract/v1','profile changed')
    req(data['predecessor']=='P12.5-RCV-6','predecessor changed')
    req(data['host']['project']=='ApexForge.Runtime.Host','host project changed')
    req(data['host']['startup_side_effects_before_validation'] is False,'startup side effects allowed too early')
    req(data['host']['background_daemon'] is False,'daemon selected early')
    req(data['host']['network_listener'] is False,'network listener selected early')
    req(data['authority']['language_semantics']=='CANONICAL_AIR','semantic authority changed')
    req(data['authority']['host_defines_language_semantics'] is False,'host gained semantics')
    req(data['implementation_in_this_slice'] is False,'RCV-7 must remain contract-only')
    deferred=set(data['deferred'])
    for x in ['HOST_INGRESS','EXTERNAL_SERIALIZATION','MANAGED_EXECUTION_DISPATCH','NATIVE_EXECUTION_DISPATCH','MANAGED_EXECUTABLE_CARRIER','QSI_COUPLING']:
        req(x in deferred,f'{x} no longer deferred')
    hostproj=ROOT/'runtimes/dotnet/ApexForge.Runtime.Host/ApexForge.Runtime.Host.csproj'
    hostprog=ROOT/'runtimes/dotnet/ApexForge.Runtime.Host/Program.cs'
    req(hostproj.exists() and hostprog.exists(),'RCV-6 host skeleton missing')
    status=run('git','status','--porcelain=v1','--untracked-files=all')
    req(status.returncode==0,'git status failed')
    # This contract remains runnable after later recovery gates. Later authorized
    # files may be present, but the recovery line must never stage them implicitly.
    staged=run('git','diff','--cached','--quiet')
    req(staged.returncode==0,'recovery files were staged without authorization')
    print('P12_5_RCV_7_PROFILE=apexforge.p12.host-lifecycle-startup-contract/v1')
    print('P12_5_RCV_7_HOST_PROJECT=ApexForge.Runtime.Host')
    print('P12_5_RCV_7_STARTUP=DETERMINISTIC_SINGLE_PROCESS')
    print('P12_5_RCV_7_LANGUAGE_SEMANTIC_AUTHORITY=CANONICAL_AIR')
    print('P12_5_RCV_7_HOST_INGRESS=DEFERRED')
    print('P12_5_RCV_7_EXECUTION_DISPATCH=DEFERRED')
    print('P12_5_RCV_7_HOST_LIFECYCLE_AND_STARTUP_CONTRACT=PASS')
    print('P12_5_RCV_7_NEXT=P12.5-RCV-8_HOST_LIFECYCLE_AND_STARTUP_IMPLEMENTATION_FOUNDATION')
    return 0

if __name__=='__main__':
    import sys
    raise SystemExit(main())
