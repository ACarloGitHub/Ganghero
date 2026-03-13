import * as vscode from 'vscode';
import * as http from 'http';

let server: http.Server | null = null;
const PORT = 18790;

export function activate(context: vscode.ExtensionContext) {
    console.log('Ganghero Bridge extension activated');

    const startCommand = vscode.commands.registerCommand('ganghero.start', () => {
        startBridge();
    });

    const stopCommand = vscode.commands.registerCommand('ganghero.stop', () => {
        stopBridge();
    });

    context.subscriptions.push(startCommand, stopCommand);
    startBridge();
}

function startBridge() {
    if (server) {
        vscode.window.showWarningMessage('Ganghero Bridge is already running');
        return;
    }

    server = http.createServer((req, res) => {
        res.setHeader('Access-Control-Allow-Origin', '*');
        res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
        res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

        if (req.method === 'OPTIONS') {
            res.writeHead(200);
            res.end();
            return;
        }

        if (req.method === 'GET' && req.url === '/status') {
            res.writeHead(200, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({
                status: 'running',
                port: PORT,
                workspace: vscode.workspace.workspaceFolders?.[0]?.uri?.fsPath || null
            }));
            return;
        }

        if (req.method === 'POST' && req.url === '/file') {
            let body = '';
            req.on('data', chunk => { body += chunk; });
            req.on('end', () => {
                try {
                    const data = JSON.parse(body);
                    res.writeHead(200, { 'Content-Type': 'application/json' });
                    res.end(JSON.stringify({ success: true, data }));
                } catch (e: any) {
                    res.writeHead(400, { 'Content-Type': 'application/json' });
                    res.end(JSON.stringify({ success: false, error: e.message }));
                }
            });
            return;
        }

        if (req.method === 'POST' && req.url === '/command') {
            let body = '';
            req.on('data', chunk => { body += chunk; });
            req.on('end', () => {
                try {
                    const data = JSON.parse(body);
                    res.writeHead(200, { 'Content-Type': 'application/json' });
                    res.end(JSON.stringify({ success: true, data }));
                } catch (e: any) {
                    res.writeHead(400, { 'Content-Type': 'application/json' });
                    res.end(JSON.stringify({ success: false, error: e.message }));
                }
            });
            return;
        }

        res.writeHead(404, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ success: false, error: 'Not found' }));
    });

    server.listen(PORT, () => {
        vscode.window.showInformationMessage(`Ganghero Bridge started on port ${PORT}`);
    });

    server.on('error', (err: any) => {
        if (err.code === 'EADDRINUSE') {
            vscode.window.showErrorMessage(`Port ${PORT} already in use`);
        } else {
            vscode.window.showErrorMessage(`Bridge error: ${err.message}`);
        }
    });
}

function stopBridge() {
    if (server) {
        server.close();
        server = null;
        vscode.window.showInformationMessage('Ganghero Bridge stopped');
    } else {
        vscode.window.showWarningMessage('Ganghero Bridge is not running');
    }
}

export function deactivate() {
    stopBridge();
}