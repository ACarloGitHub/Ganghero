# Ganghero - Project Index

## Panoramica

**Ganghero** è il ponte tra OpenClaw e le applicazioni.
Fornisce tool standardizzati per leggere/scrivere file, eseguire comandi,
e mantenere contesto del progetto.

## Struttura

```
Ganghero/
├── core/           # Tool indipendenti dal modello
│   ├── read_file.py
│   ├── write_file.py
│   └── run_terminal.py
├── adapters/       # Adattatori per backend AI
├── projects/       # Configurazioni per progetti specifici
└── Documenti/      # Riferimenti e scaletta
```

## Tool Disponibili

| Tool | File | Funzione |
|------|------|----------|
| `read_file` | `core/read_file.py` | Legge contenuto di un file |
| `write_file` | `core/write_file.py` | Scrive contenuto in un file |
| `run_terminal` | `core/run_terminal.py` | Esegue comandi shell |
| `search` | `core/search.py` | Ricerca codice con ripgrep |
| `git_patch` | `core/git_patch.py` | Applica patch incrementali |
| `parse_ast` | `core/parse_ast.py` | Estrae simboli da codice (AST) |
| `knowledge_graph` | `core/knowledge_graph.py` | Costruisce grafo relazioni codice |
| `indexer` | `core/indexer.py` | Monitora file e aggiorna grafo automaticamente |
| `agent_loop` | `core/agent_loop.py` | Loop autonomo: plan → execute → observe → save |

## Comandi

```bash
# Test tools
cd /home/carlo/progetti/Ganghero
python3 -c "from core.read_file import run; print(run('Documenti/project_index.md'))"
python3 -c "from core.write_file import run; print(run('/tmp/test.txt', 'Hello'))"
python3 -c "from core.run_terminal import run; print(run('ls -la'))"
```

## Backend Supportati

- OpenClaw (default)
- Ollama
- LM Studio

## Integrazione Progetti

| Progetto | Stato |
|----------|-------|
| 3LO | Da integrare |
| AuraWrite | Da integrare |

## Note

- Nome scelto da Carlo: "Ganghero" = cardine che tiene insieme le parti
- Indipendente dal modello AI per continuità futura
- OpenClaw acquisito da OpenAI → Ganghero garantisce alternativa