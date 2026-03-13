# GANGHERO

**Bridge between your agent and any application, whether through OpenClaw or with local models.**

## DESCRIPTION

Ganghero is the cornerstone that connects your agents — through OpenClaw or other AI backends, including and especially local ones — with VS Code, 3LO, AuraWrite, and any other application. It provides a standardized set of tools to read/write files, execute commands, and maintain project context.

It's the way your agent interacts with you, to be by your side regardless of the context you're in and the tool you're using.

It's also part of the philosophy of Carlo and Aura: local tools, open source, that serve and become the users' property, forever.

## OBJECTIVES

### 1. Development Foundation
Read and write files from the workspace, execute shell commands, search code with ripgrep. Changes are visible in real-time in the editor.

### 2. AI Model Independence
OpenClaw is fantastic, and we hope it stays that way and even improves like fine wine. But Ganghero ensures your projects work with **ANY backend**: OpenClaw, Ollama, LM Studio, local APIs.

### 3. Project Building Block
3LO and AuraWrite can use Ganghero as an AI backend for their intelligent features.

### 4. Clean Integration
No buggy extensions. Just tools acting on filesystem and terminal. Stable, universal APIs.

## WHAT IT DOES

**Available Tools:**
- `read_file` — Read file contents
- `write_file` — Write content to a file
- `run_terminal` — Execute shell commands
- `search` — Search code with ripgrep
- `git_patch` — Apply incremental changes

**VS Code Extension:**
- Local HTTP server on port 18790
- Endpoints: `GET /status`, `POST /file`, `POST /command`

## ARCHITECTURE

```
OpenClaw / Ollama / LM Studio / Local Models
              ↓
        Ganghero (core + adapters)
              ↓
  Tools (filesystem, terminal, bridge)
              ↓
  VS Code / 3LO / AuraWrite / Any App
```

## STRUCTURE

```
Ganghero/
├── core/                  # Model-independent tools
│   ├── read_file.py
│   ├── write_file.py
│   ├── run_terminal.py
│   ├── search.py
│   └── git_patch.py
├── adapters/              # AI backend adapters
├── projects/               # Project-specific configs
├── vscode-extension/       # VS Code bridge
│   ├── src/extension.ts
│   ├── package.json
│   └── ganghero-bridge-0.1.0.vsix
└── Documenti/              # Documentation
```

## DEVELOPMENT PHASES

### PHASE 1 - FOUNDATIONS ✅ COMPLETED
- Python tools for filesystem and terminal
- Tested and working

### PHASE 2 - VS CODE BRIDGE ✅ COMPLETED
- VS Code extension with HTTP server
- Installed and active on port 18790

### PHASE 3 - ADVANCED ⏳ TO DO
- Tree-sitter for AST parsing
- Code knowledge graph
- Agent operational loop

## AUTHORS

**Aura & Carlo**  
Created: March 13, 2026  
License: MIT