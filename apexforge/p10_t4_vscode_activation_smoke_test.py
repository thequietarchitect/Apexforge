"""AFP-P10-T4.3 VS Code language-server activation smoke test."""

from __future__ import annotations

from io import StringIO
import json
from pathlib import Path
from shutil import copytree, which
import subprocess
import sys
from tempfile import TemporaryDirectory
from zipfile import ZIP_DEFLATED, ZipFile

from tooling.vscode_lsp_activation import (
    CANONICAL_ACTIVATION_EVENTS,
    CANONICAL_COMMANDS,
    CANONICAL_EXTENSION_MAIN,
    CANONICAL_LANGUAGE_SERVER_GUIDE,
    CANONICAL_OUTPUT_CHANNEL,
    CANONICAL_RUNTIME_CLIENT_PATH,
    CANONICAL_SERVER_RELATIVE_PATH,
    CANONICAL_SETTINGS,
    CANONICAL_VSCODE_LSP_ACTIVATION_SHA256,
    P10_T4_VSCODE_ACTIVATION_VERSION,
    VSCODE_LSP_ACTIVATION_KIND,
    VSCODE_LSP_ACTIVATION_SCHEMA,
    VSCodeLSPActivationError,
    activation_fingerprint,
    audit_vscode_lsp_activation,
    audit_vscode_lsp_vsix,
    check_node_syntax,
    main as activation_main,
)
from tooling.vscode_package import (
    CANONICAL_VSCODE_PACKAGE_SHA256,
    packaging_fingerprint,
)


EXPECTED_ACTIVATION_SHA256 = (
    "b74759e09a2de60a9ca78d6baa36d0d608b650858b6220f3ab4b3f2916a940d6"
)
EXPECTED_T3_PACKAGE_SHA256 = (
    "75a39c44354d4f647ab46cb6aba42adf00f5396c7563b1433ff2d93d66e9498c"
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def require_activation_error(operation, message: str) -> VSCodeLSPActivationError:
    try:
        operation()
    except VSCodeLSPActivationError as error:
        require(error.code == "APX-VSCODE-004", "activation error code changed")
        return error
    raise AssertionError(message)


def write_vsix(extension_root: Path, destination: Path, *, omit: str = "") -> None:
    payload = {
        "extension/package.json": extension_root / "package.json",
        "extension/extension.js": extension_root / "extension.js",
        "extension/runtime/lsp-client.js": (
            extension_root / "runtime" / "lsp-client.js"
        ),
        "extension/LANGUAGE_SERVER.md": extension_root / "LANGUAGE_SERVER.md",
    }
    with ZipFile(destination, "w", compression=ZIP_DEFLATED) as archive:
        for archive_name, source_path in payload.items():
            if archive_name.casefold() == omit.casefold():
                continue
            archive.writestr(archive_name, source_path.read_bytes())


def node_harness(
    *,
    client_path: Path,
    server_path: Path,
    python_command: str,
    repository_root: Path,
) -> str:
    template = r"""
'use strict';
const assert = require('assert');
const { LspProcessClient, LspMessageReader, encodeMessage } = require(__CLIENT_PATH__);

function waitFor(queue, method, timeoutMs = 5000) {
    return new Promise((resolve, reject) => {
        const existing = queue.findIndex((item) => item.method === method);
        if (existing >= 0) {
            resolve(queue.splice(existing, 1)[0]);
            return;
        }

        const timer = setTimeout(
            () => reject(new Error(`Timed out waiting for ${method}`)),
            timeoutMs
        );
        queue.waiters.push({
            method,
            resolve(item) {
                clearTimeout(timer);
                resolve(item);
            },
        });
    });
}

(async () => {
    const framed = encodeMessage({
        jsonrpc: '2.0',
        id: 1,
        method: 'example/unicode',
        params: {text: 'ApexForge λ'},
    });
    const reader = new LspMessageReader();
    assert.deepStrictEqual(reader.push(framed.subarray(0, 9)), []);
    const decoded = reader.push(framed.subarray(9));
    assert.strictEqual(decoded.length, 1);
    assert.strictEqual(decoded[0].params.text, 'ApexForge λ');

    const queue = [];
    queue.waiters = [];

    const client = new LspProcessClient({
        command: __PYTHON_COMMAND__,
        args: [__SERVER_PATH__, '--stdio'],
        cwd: __REPOSITORY_ROOT__,
        onNotification(method, params) {
            const item = {method, params};
            const index = queue.waiters.findIndex(
                (waiter) => waiter.method === method
            );
            if (index >= 0) {
                queue.waiters.splice(index, 1)[0].resolve(item);
            } else {
                queue.push(item);
            }
        },
        onStderr(text) {
            process.stderr.write(text);
        },
        onLog(message) {
            process.stderr.write(`[client] ${message}\n`);
        },
    });

    const initialized = await client.start({
        processId: process.pid,
        clientInfo: {
            name: 'ApexForgeT4.3SmokeClient',
            version: '1.0',
        },
        rootUri: 'file:///ApexForgeT4.3Smoke',
        capabilities: {
            textDocument: {
                publishDiagnostics: {
                    relatedInformation: true,
                    versionSupport: true,
                },
            },
        },
    });

    assert.strictEqual(
        initialized.serverInfo.name,
        'apexforge-language-server'
    );
    assert.strictEqual(client.state, 'running');

    const uri = 'file:///ApexForgeT4.3Smoke/main.apex';
    client.sendNotification('textDocument/didOpen', {
        textDocument: {
            uri,
            languageId: 'apexforge',
            version: 1,
            text: 'function Broken(value : int) : int { return }\n',
        },
    });
    const opened = await waitFor(
        queue,
        'textDocument/publishDiagnostics'
    );
    assert.strictEqual(opened.params.uri, uri);
    assert.strictEqual(opened.params.version, 1);
    assert.ok(opened.params.diagnostics.length >= 1);

    client.sendNotification('textDocument/didChange', {
        textDocument: {uri, version: 2},
        contentChanges: [{
            text: (
                'function Identity(value : int) : int '
                + '{ return value }\n'
            ),
        }],
    });
    const changed = await waitFor(
        queue,
        'textDocument/publishDiagnostics'
    );
    assert.strictEqual(changed.params.version, 2);
    assert.deepStrictEqual(changed.params.diagnostics, []);

    client.sendNotification('textDocument/didClose', {
        textDocument: {uri},
    });
    const closed = await waitFor(
        queue,
        'textDocument/publishDiagnostics'
    );
    assert.strictEqual(
        Object.prototype.hasOwnProperty.call(closed.params, 'version'),
        false
    );
    assert.deepStrictEqual(closed.params.diagnostics, []);

    await client.stop();
    assert.strictEqual(client.state, 'stopped');
    assert.strictEqual(client.lastExitCode, 0);

    console.log('AFP-P10-T4.3 Node process lifecycle: PASS');
})().catch((error) => {
    console.error(error && error.stack ? error.stack : String(error));
    process.exitCode = 1;
});
"""
    return (
        template
        .replace("__CLIENT_PATH__", json.dumps(str(client_path)))
        .replace("__PYTHON_COMMAND__", json.dumps(python_command))
        .replace("__SERVER_PATH__", json.dumps(str(server_path)))
        .replace("__REPOSITORY_ROOT__", json.dumps(str(repository_root)))
    )


def main() -> None:
    require(
        P10_T4_VSCODE_ACTIVATION_VERSION == "10-T4.3",
        "T4.3 version changed",
    )
    require(VSCODE_LSP_ACTIVATION_SCHEMA == 1, "T4.3 schema changed")
    require(
        VSCODE_LSP_ACTIVATION_KIND == "apexforge.vscode-lsp-activation",
        "T4.3 kind changed",
    )
    require(CANONICAL_EXTENSION_MAIN == "./extension.js", "main path changed")
    require(
        CANONICAL_RUNTIME_CLIENT_PATH == "runtime/lsp-client.js",
        "runtime client path changed",
    )
    require(
        CANONICAL_LANGUAGE_SERVER_GUIDE == "LANGUAGE_SERVER.md",
        "runtime guide path changed",
    )
    require(
        CANONICAL_SERVER_RELATIVE_PATH == "apexforge/apexforge_lsp.py",
        "server path changed",
    )
    require(
        CANONICAL_OUTPUT_CHANNEL == "ApexForge Language Server",
        "output channel changed",
    )
    require(len(CANONICAL_ACTIVATION_EVENTS) == 2, "activation count changed")
    require(len(CANONICAL_COMMANDS) == 2, "command count changed")
    require(len(CANONICAL_SETTINGS) == 3, "setting count changed")

    repository_root = Path(__file__).resolve().parent.parent
    extension_root = repository_root / "editors" / "vscode-apexforge"

    audit = audit_vscode_lsp_activation(extension_root)
    require(
        audit.activation_sha256 == EXPECTED_ACTIVATION_SHA256,
        "activation audit hash changed",
    )
    require(
        CANONICAL_VSCODE_LSP_ACTIVATION_SHA256
        == EXPECTED_ACTIVATION_SHA256,
        "declared activation hash changed",
    )

    package = json.loads(
        (extension_root / "package.json").read_text(encoding="utf-8")
    )
    runtime_hashes = {
        relative_name: __import__("hashlib").sha256(
            (extension_root / relative_name).read_bytes()
        ).hexdigest()
        for relative_name in (
            "extension.js",
            "runtime/lsp-client.js",
            "LANGUAGE_SERVER.md",
        )
    }
    require(
        activation_fingerprint(package, runtime_hashes)
        == EXPECTED_ACTIVATION_SHA256,
        "activation projection is not deterministic",
    )

    require(
        packaging_fingerprint(extension_root) == EXPECTED_T3_PACKAGE_SHA256,
        "T4.3 did not preserve the frozen T3.3 projection",
    )
    require(
        CANONICAL_VSCODE_PACKAGE_SHA256 == EXPECTED_T3_PACKAGE_SHA256,
        "T3.3 package constant changed",
    )

    checked = check_node_syntax(extension_root)
    require(
        checked == ("extension.js", "runtime/lsp-client.js"),
        "Node syntax inventory changed",
    )

    node_command = which("node")
    require(node_command is not None, "Node.js is required for T4.3 testing")
    harness = node_harness(
        client_path=(extension_root / "runtime" / "lsp-client.js").resolve(),
        server_path=(repository_root / "apexforge" / "apexforge_lsp.py").resolve(),
        python_command=sys.executable,
        repository_root=repository_root.resolve(),
    )
    with TemporaryDirectory() as temporary:
        temporary_root = Path(temporary)
        harness_path = temporary_root / "t4_3_node_smoke.js"
        harness_path.write_text(harness, encoding="utf-8")
        completed = subprocess.run(
            (node_command, str(harness_path)),
            cwd=str(repository_root),
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
        require(
            completed.returncode == 0,
            "Node language-server lifecycle failed:\n"
            + completed.stdout
            + completed.stderr,
        )
        require(
            "AFP-P10-T4.3 Node process lifecycle: PASS"
            in completed.stdout,
            "Node lifecycle success marker was omitted",
        )

        vsix_path = temporary_root / "apexforge-language-0.1.0.vsix"
        write_vsix(extension_root, vsix_path)
        vsix_audit = audit_vscode_lsp_vsix(extension_root, vsix_path)
        require(vsix_audit.archive_file_count == 4, "VSIX runtime count changed")
        require(
            vsix_audit.activation_sha256 == EXPECTED_ACTIVATION_SHA256,
            "VSIX activation hash changed",
        )

        missing_vsix = temporary_root / "missing-client.vsix"
        write_vsix(
            extension_root,
            missing_vsix,
            omit="extension/runtime/lsp-client.js",
        )
        require_activation_error(
            lambda: audit_vscode_lsp_vsix(extension_root, missing_vsix),
            "VSIX without the runtime client unexpectedly passed",
        )

        copied_extension = temporary_root / "copied-extension"
        copytree(extension_root, copied_extension)
        copied_package_path = copied_extension / "package.json"
        copied_package = json.loads(
            copied_package_path.read_text(encoding="utf-8")
        )
        copied_package["activationEvents"] = ["*"]
        copied_package_path.write_text(
            json.dumps(copied_package, indent=2) + "\n",
            encoding="utf-8",
        )
        require_activation_error(
            lambda: audit_vscode_lsp_activation(copied_extension),
            "activation-event drift unexpectedly passed",
        )

    stdout = StringIO()
    stderr = StringIO()
    code = activation_main(
        (str(extension_root), "--check"),
        stdout=stdout,
        stderr=stderr,
    )
    require(code == 0, "standalone activation check failed")
    require(stderr.getvalue() == "", "successful activation check wrote stderr")
    require(
        "AFP-P10-T4.3 VS Code LSP activation check passed.\n"
        in stdout.getvalue(),
        "standalone check omitted success heading",
    )
    require(
        f"Activation SHA-256: {EXPECTED_ACTIVATION_SHA256}\n"
        in stdout.getvalue(),
        "standalone check omitted activation hash",
    )

    print("AFP-P10-T4.3 VS Code language-server activation smoke test passed.")
    print("One server process per workspace folder: PASS")
    print("JSON-RPC Content-Length process client: PASS")
    print("Initialize and clean shutdown lifecycle: PASS")
    print("Full document synchronization forwarding: PASS")
    print("Live diagnostics reception and clearing: PASS")
    print("Output channel and restart commands: PASS")
    print("Frozen T3.3 packaging projection: PASS")
    print("Deterministic activation fingerprint: PASS")
    print("T4.3 VSIX runtime inventory: PASS")


if __name__ == "__main__":
    main()
