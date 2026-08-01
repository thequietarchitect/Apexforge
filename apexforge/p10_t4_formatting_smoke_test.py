"""AFP-P10-T4.10 deterministic whole-document formatting smoke test."""
from __future__ import annotations
import json
import subprocess
import sys
from io import BytesIO
from pathlib import Path
from language.parser import parse
from language.modules import parse_module_source
from language_server.formatting import CANONICAL_FORMATTING_SHA256, FORMATTING_METHOD, P10_T4_FORMATTING_VERSION, format_document, formatting_fingerprint
from language_server.server import LanguageServerSession, active_server_capabilities, server_capabilities
from tooling.vscode_formatting import CANONICAL_VSCODE_FORMATTING_SHA256, audit_vscode_formatting, formatting_fingerprint as vscode_fingerprint
EXPECTED_SERVER="63ac984979dd14832dd7d69490176a6e877c867c00c30116636d6c6e5fef3e4b"
EXPECTED_VSCODE="46a4267481b3f4fabd250c7324cc3b4f7be98bb6d5b2b7a52ef05bb6fc27c6ff"
UGLY="""module demo.counter;\nimport demo.shared;\n\ndirective Counter{state count:int=0 event changed cause run{path primary@10{set count=count+1 when count>0{emit changed}otherwise{message \"idle\"}}}}"""
EXPECTED="""module demo.counter\nimport demo.shared\n\ndirective Counter {\n    state count : int = 0\n    event changed\n    cause run {\n        path primary @ 10 {\n            set count = count + 1\n            when count > 0 {\n                emit changed\n            } otherwise {\n                message \"idle\"\n            }\n        }\n    }\n}\n"""
FUNCTION="""function Choose<T:numeric>(value:T):T{let copy=value when value>0{return copy}otherwise{return -copy}}"""
FUNCTION_EXPECTED="""function Choose<T : numeric>(value : T) : T {\n    let copy = value\n    when value > 0 {\n        return copy\n    } otherwise {\n        return -copy\n    }\n}\n"""
def require(value:bool,message:str)->None:
    if not value:raise AssertionError(message)
def request(i:int,method:str,params=None):
    value={"jsonrpc":"2.0","id":i,"method":method}
    if params is not None:value["params"]=params
    return value
def notification(method:str,params=None):
    value={"jsonrpc":"2.0","method":method}
    if params is not None:value["params"]=params
    return value
def node_harness(client_path:Path,server_path:Path,repository_root:Path)->str:
    template=r"""
'use strict';
const assert = require('assert');
const {LspProcessClient} = require(__CLIENT_PATH__);
(async () => {
    const client = new LspProcessClient({
        command: __PYTHON_COMMAND__,
        args: [__SERVER_PATH__, '--stdio'],
        cwd: __REPOSITORY_ROOT__,
        onStderr(text) { process.stderr.write(text); },
    });
    const initialized = await client.start({
        processId: process.pid,
        rootUri: __ROOT_URI__,
        capabilities: {textDocument: {formatting: {dynamicRegistration: false}}},
    });
    assert.strictEqual(initialized.capabilities.documentFormattingProvider, true);
    const uri = 'file:///T410Formatting.apex';
    client.sendNotification('textDocument/didOpen', {
        textDocument: {
            uri, languageId: 'apexforge', version: 1,
            text: 'directive Counter{state count:int=0}',
        },
    });
    const edits = await client.sendRequest('textDocument/formatting', {
        textDocument: {uri},
        options: {tabSize: 2, insertSpaces: true},
    });
    assert.strictEqual(edits.length, 1);
    assert.strictEqual(edits[0].newText, 'directive Counter {\n  state count : int = 0\n}\n');
    await client.stop();
    process.stdout.write('node-formatting-lifecycle: PASS\n');
})().catch((error) => { console.error(error && error.stack ? error.stack : error); process.exitCode = 1; });
"""
    return (template.replace("__CLIENT_PATH__",json.dumps(str(client_path)))
        .replace("__PYTHON_COMMAND__",json.dumps(sys.executable))
        .replace("__SERVER_PATH__",json.dumps(str(server_path)))
        .replace("__REPOSITORY_ROOT__",json.dumps(str(repository_root)))
        .replace("__ROOT_URI__",json.dumps(repository_root.as_uri())))
def main()->None:
    require(P10_T4_FORMATTING_VERSION=="10-T4.10","version changed")
    require(formatting_fingerprint()==EXPECTED_SERVER,"server fingerprint changed")
    require(CANONICAL_FORMATTING_SHA256==EXPECTED_SERVER,"server constant changed")
    edits=format_document("file:///Counter.apex",UGLY,{"tabSize":4,"insertSpaces":True})
    require(len(edits)==1 and edits[0]["newText"]==EXPECTED,"directive formatting changed")
    require(format_document("file:///Counter.apex",EXPECTED,{"tabSize":4,"insertSpaces":True})==(),"idempotence changed")
    function_edits=format_document("file:///Choose.apex",FUNCTION,{"tabSize":4,"insertSpaces":True})
    require(function_edits[0]["newText"]==FUNCTION_EXPECTED,"function formatting changed")
    require(format_document("file:///Broken.apex","directive Broken {",{"tabSize":4,"insertSpaces":True})==(),"invalid source was edited")
    tabbed=format_document("file:///Counter.apex",UGLY,{"tabSize":8,"insertSpaces":False})[0]["newText"]
    require("\tstate count" in tabbed,"tab indentation changed")
    unit=parse_module_source("Counter.apex",EXPECTED);parse(unit.masked_source,source_name="Counter.apex")
    require("documentFormattingProvider" not in server_capabilities(),"frozen T4.1 capability changed")
    require(active_server_capabilities(formatting_enabled=True)["documentFormattingProvider"] is True,"active formatting capability missing")
    session=LanguageServerSession();initialized=session.process(request(1,"initialize",{"processId":None,"rootUri":"file:///workspace","capabilities":{"textDocument":{"formatting":{"dynamicRegistration":False}}}}))
    require(initialized["result"]["capabilities"]["documentFormattingProvider"] is True,"server did not advertise formatting")
    session.process(notification("textDocument/didOpen",{"textDocument":{"uri":"file:///Counter.apex","languageId":"apexforge","version":1,"text":UGLY}}))
    response=session.process(request(2,FORMATTING_METHOD,{"textDocument":{"uri":"file:///Counter.apex"},"options":{"tabSize":4,"insertSpaces":True}}))
    require(response["result"][0]["newText"]==EXPECTED,"JSON-RPC formatting changed")
    repository_root=Path(__file__).resolve().parent.parent;extension_root=repository_root/"editors"/"vscode-apexforge"
    audit=audit_vscode_formatting(extension_root);require(audit.formatting_sha256==EXPECTED_VSCODE,"VS Code audit changed")
    runtime={"extension.js":__import__('hashlib').sha256((extension_root/"extension.js").read_bytes()).hexdigest(),"runtime/lsp-client.js":__import__('hashlib').sha256((extension_root/"runtime"/"lsp-client.js").read_bytes()).hexdigest(),"LANGUAGE_SERVER.md":__import__('hashlib').sha256((extension_root/"LANGUAGE_SERVER.md").read_bytes()).hexdigest()}
    require(vscode_fingerprint(runtime)==EXPECTED_VSCODE,"VS Code projection changed")
    script=node_harness(extension_root/"runtime"/"lsp-client.js",repository_root/"apexforge"/"apexforge_lsp.py",repository_root)
    completed=subprocess.run(("node","-e",script),cwd=repository_root,check=False,capture_output=True,text=True)
    require(completed.returncode==0,f"Node formatting lifecycle failed: {completed.stderr or completed.stdout}")
    require("node-formatting-lifecycle: PASS" in completed.stdout,"Node formatting lifecycle output changed")
    print("AFP-P10-T4.10 whole-document formatting smoke test passed.")
    print("Parser-backed semantic preservation: PASS")
    print("Module/import canonicalization: PASS")
    print("Function and directive formatting: PASS")
    print("Invalid-source no-edit boundary: PASS")
    print("Idempotence and indentation options: PASS")
    print("JSON-RPC formatting lifecycle: PASS")
    print("Node client formatting lifecycle: PASS")
    print("Deterministic T4.10 fingerprints: PASS")
if __name__=="__main__":main()
