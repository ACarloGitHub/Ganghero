# Ganghero Bridge - Estensione VS Code

## Installazione

1. Compilare l'estensione:
   ```bash
   cd /home/carlo/progetti/Ganghero/vscode-extension
   npm install
   npm run compile
   ```

2. Creare il pacchetto:
   ```bash
   npm install -g @vscode/vsce
   vsce package
   ```

3. Installare in VS Code:
   - `Ctrl+Shift+P` → "Extensions: Install from VSIX..."
   - Selezionare `ganghero-bridge-0.1.0.vsix`

4. Ricaricare VS Code

## Comandi

- `Ganghero: Avvia Bridge` - Avvia il server HTTP
- `Ganghero: Ferma Bridge` - Ferma il server HTTP

Il bridge si avvia automaticamente all'apertura di VS Code.

## API REST

Il server HTTP gira su `http://localhost:18790`

### GET /status
Restituisce lo stato del bridge e il workspace corrente.

### POST /file
Operazioni sui file (da integrare con Ganghero core).
Body: `{ "action": "read|write", "path": "...", "content": "..." }`

### POST /command
Esegue comandi terminale (da integrare con Ganghero core).
Body: `{ "command": "ls -la" }`

## Integrazione con Ganghero

L'estensione è il bridge tra VS Code e i tool Python in `Ganghero/core/`.
Quando OpenClaw invia richieste al bridge, questo:
1. Riceve la richiesta HTTP
2. Chiama i tool Python appropriati
3. Restituisce il risultato

## Porta

Default: 18790
Modificabile in `src/extension.ts` (variabile `PORT`)