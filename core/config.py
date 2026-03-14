"""
Ganghero - config manager
Gestisce configurazione globale e memoria dei progetti.

Uso:
    from core.config import Config
    config = Config()
    config.add_trusted_folder("/path/to/project")
    config.set_active_project("3lo")
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime


class Config:
    """
    Gestisce configurazione globale di Ganghero.
    Memoria in: ~/.config/ganghero/
    """
    
    def __init__(self):
        self.config_dir = Path.home() / ".config" / "ganghero"
        self.config_file = self.config_dir / "config.json"
        self.projects_dir = self.config_dir / "projects"
        self.sessions_file = self.config_dir / "sessions" / "active.json"
        
        # Crea struttura se non esiste
        self._ensure_structure()
        
        # Carica config
        self._config = self._load_config()
    
    def _ensure_structure(self):
        """Crea directory necessarie."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.projects_dir.mkdir(exist_ok=True)
        (self.config_dir / "sessions").mkdir(exist_ok=True)
    
    def _load_config(self) -> Dict:
        """Carica configurazione da file."""
        if self.config_file.exists():
            try:
                return json.loads(self.config_file.read_text())
            except Exception:
                pass
        
        # Config default
        return {
            "version": "1.0",
            "sandbox_mode": "prompt",  # strict, prompt, permissive
            "trusted_folders": [],
            "auto_open_vscode": False,
            "notifications_enabled": True,
            "indexer_cooldown": 30,
            "created": datetime.now().isoformat(),
            "modified": datetime.now().isoformat()
        }
    
    def _save_config(self):
        """Salva configurazione su file."""
        self._config["modified"] = datetime.now().isoformat()
        self.config_file.write_text(json.dumps(self._config, indent=2))
    
    # === TRUSTED FOLDERS ===
    
    def get_trusted_folders(self) -> List[str]:
        """Restituisce lista cartelle trusted."""
        return self._config.get("trusted_folders", [])
    
    def add_trusted_folder(self, folder_path: str) -> bool:
        """
        Aggiunge cartella alla whitelist.
        
        Args:
            folder_path: Percorso assoluto della cartella
        
        Returns:
            True se aggiunta, False se già presente
        """
        folder = Path(folder_path).resolve()
        
        if not folder.exists():
            return False
        
        trusted = self.get_trusted_folders()
        str_path = str(folder)
        
        if str_path in trusted:
            return False
        
        trusted.append(str_path)
        self._config["trusted_folders"] = trusted
        self._save_config()
        return True
    
    def remove_trusted_folder(self, folder_path: str) -> bool:
        """Rimuove cartella dalla whitelist."""
        folder = Path(folder_path).resolve()
        str_path = str(folder)
        
        trusted = self.get_trusted_folders()
        if str_path not in trusted:
            return False
        
        trusted.remove(str_path)
        self._config["trusted_folders"] = trusted
        self._save_config()
        return True
    
    def is_trusted(self, path: str) -> bool:
        """
        Verifica se un percorso è trusted.
        
        Args:
            path: Percorso da verificare
        
        Returns:
            True se il percorso è in una cartella trusted
        """
        check_path = Path(path).resolve()
        
        for trusted in self.get_trusted_folders():
            trusted_path = Path(trusted)
            try:
                # Verifica se check_path è dentro trusted_path
                check_path.relative_to(trusted_path)
                return True
            except ValueError:
                continue
        
        return False
    
    # === SANDBOX MODE ===
    
    def get_sandbox_mode(self) -> str:
        """Restituisce modalità sandbox (strict, prompt, permissive)."""
        return self._config.get("sandbox_mode", "prompt")
    
    def set_sandbox_mode(self, mode: str) -> bool:
        """
        Imposta modalità sandbox.
        
        Args:
            mode: "strict", "prompt", o "permissive"
        """
        if mode not in ("strict", "prompt", "permissive"):
            return False
        
        self._config["sandbox_mode"] = mode
        self._save_config()
        return True
    
    # === ACTIVE PROJECTS ===
    
    def get_active_projects(self) -> List[Dict]:
        """Restituisce lista progetti attivi."""
        if self.sessions_file.exists():
            try:
                data = json.loads(self.sessions_file.read_text())
                return data.get("projects", [])
            except Exception:
                pass
        return []
    
    def add_active_project(self, project_path: str, name: Optional[str] = None) -> bool:
        """
        Aggiunge progetto alla lista attivi.
        
        Args:
            project_path: Percorso del progetto
            name: Nome del progetto (default: nome cartella)
        """
        project = Path(project_path).resolve()
        
        if not project.exists():
            return False
        
        if name is None:
            name = project.name
        
        projects = self.get_active_projects()
        
        # Verifica se già presente
        for p in projects:
            if p["path"] == str(project):
                return False
        
        projects.append({
            "name": name,
            "path": str(project),
            "added": datetime.now().isoformat(),
            "last_accessed": datetime.now().isoformat()
        })
        
        self._save_sessions(projects)
        return True
    
    def remove_active_project(self, project_name: str) -> bool:
        """Rimuove progetto dalla lista attivi."""
        projects = self.get_active_projects()
        
        for i, p in enumerate(projects):
            if p["name"] == project_name:
                projects.pop(i)
                self._save_sessions(projects)
                return True
        
        return False
    
    def set_current_project(self, project_name: str) -> bool:
        """Imposta progetto corrente."""
        projects = self.get_active_projects()
        
        for p in projects:
            if p["name"] == project_name:
                p["last_accessed"] = datetime.now().isoformat()
                self._save_sessions(projects, current=project_name)
                return True
        
        return False
    
    def get_current_project(self) -> Optional[Dict]:
        """Restituisce progetto corrente."""
        if self.sessions_file.exists():
            try:
                data = json.loads(self.sessions_file.read_text())
                current = data.get("current")
                if current:
                    for p in data.get("projects", []):
                        if p["name"] == current:
                            return p
            except Exception:
                pass
        return None
    
    def _save_sessions(self, projects: List[Dict], current: Optional[str] = None):
        """Salva sessioni su file."""
        if current is None and self.sessions_file.exists():
            try:
                old = json.loads(self.sessions_file.read_text())
                current = old.get("current")
            except Exception:
                pass
        
        data = {
            "current": current,
            "projects": projects,
            "updated": datetime.now().isoformat()
        }
        
        self.sessions_file.write_text(json.dumps(data, indent=2))
    
    # === PROJECT MEMORY ===
    
    def get_project_memory_path(self, project_path: str) -> Path:
        """
        Restituisce percorso memoria per un progetto.
        Usa hash del percorso per evitare caratteri speciali.
        """
        import hashlib
        
        project = Path(project_path).resolve()
        project_hash = hashlib.md5(str(project).encode()).hexdigest()[:12]
        
        return self.projects_dir / f"{project.name}_{project_hash}"
    
    def save_project_memory(self, project_path: str, data: Dict) -> bool:
        """Salva memoria di un progetto."""
        try:
            memory_path = self.get_project_memory_path(project_path)
            memory_path.mkdir(parents=True, exist_ok=True)
            
            memory_file = memory_path / "memory.json"
            memory_file.write_text(json.dumps(data, indent=2, default=str))
            return True
        except Exception:
            return False
    
    def load_project_memory(self, project_path: str) -> Optional[Dict]:
        """Carica memoria di un progetto."""
        try:
            memory_path = self.get_project_memory_path(project_path)
            memory_file = memory_path / "memory.json"
            
            if memory_file.exists():
                return json.loads(memory_file.read_text())
        except Exception:
            pass
        
        return None
    
    # === GENERIC GET/SET ===
    
    def get(self, key: str, default: Any = None) -> Any:
        """Ottiene valore di configurazione."""
        return self._config.get(key, default)
    
    def set(self, key: str, value: Any) -> bool:
        """Imposta valore di configurazione."""
        self._config[key] = value
        self._save_config()
        return True
    
    def get_all(self) -> Dict:
        """Restituisce tutta la configurazione."""
        return self._config.copy()


# === CLI COMMANDS ===

def cli_status():
    """Mostra stato di Ganghero."""
    config = Config()
    
    print("=" * 50)
    print("GANGHERO STATUS")
    print("=" * 50)
    
    # Config
    print(f"\n📁 Config directory: {config.config_dir}")
    print(f"🔒 Sandbox mode: {config.get_sandbox_mode()}")
    print(f"🔔 Notifications: {config.get('notifications_enabled', True)}")
    
    # Trusted folders
    trusted = config.get_trusted_folders()
    print(f"\n✅ Trusted folders ({len(trusted)}):")
    for folder in trusted:
        print(f"   - {folder}")
    
    # Active projects
    projects = config.get_active_projects()
    current = config.get_current_project()
    
    print(f"\n📂 Active projects ({len(projects)}):")
    for p in projects:
        marker = "👉" if current and p["name"] == current["name"] else "  "
        print(f"{marker} {p['name']}: {p['path']}")
    
    print()


def cli_trust(folder_path: str):
    """Aggiunge cartella trusted."""
    config = Config()
    
    if config.add_trusted_folder(folder_path):
        print(f"✅ Added to trust list: {folder_path}")
    else:
        print(f"❌ Already trusted or invalid path: {folder_path}")


def cli_untrust(folder_path: str):
    """Rimuove cartella trusted."""
    config = Config()
    
    if config.remove_trusted_folder(folder_path):
        print(f"✅ Removed from trust list: {folder_path}")
    else:
        print(f"❌ Not in trust list: {folder_path}")


def cli_sandbox(mode: str):
    """Imposta modalità sandbox."""
    config = Config()
    
    if config.set_sandbox_mode(mode):
        print(f"✅ Sandbox mode set to: {mode}")
    else:
        print(f"❌ Invalid mode. Use: strict, prompt, permissive")


def cli_add_project(project_path: str, name: Optional[str] = None):
    """Aggiunge progetto attivo."""
    config = Config()
    
    if config.add_active_project(project_path, name):
        print(f"✅ Added project: {name or Path(project_path).name}")
    else:
        print(f"❌ Invalid path or already added: {project_path}")


def cli_switch(project_name: str):
    """Cambia progetto corrente."""
    config = Config()
    
    if config.set_current_project(project_name):
        print(f"✅ Switched to project: {project_name}")
    else:
        print(f"❌ Project not found: {project_name}")


def cli_list_projects():
    """Lista progetti gestiti da Ganghero."""
    config = Config()
    projects = config.get_active_projects()
    
    if not projects:
        print("Nessun progetto gestito da Ganghero.")
        return
    
    print("Progetti:")
    for p in projects:
        print(f"  - {p['name']}")


def cli_remove_project(project_name: str):
    """Rimuove progetto e cancella la sua memoria."""
    config = Config()
    
    # Trova il progetto
    project = None
    for p in config.get_active_projects():
        if p['name'] == project_name:
            project = p
            break
    
    if not project:
        print(f"❌ Progetto non trovato: {project_name}")
        return
    
    # Cancella memoria del progetto
    import shutil
    memory_path = config.get_project_memory_path(project['path'])
    if memory_path.exists():
        shutil.rmtree(memory_path)
        print(f"🗑️  Memoria cancellata: {memory_path}")
    
    # Rimuovi dalla lista
    if config.remove_active_project(project_name):
        print(f"✅ Progetto eliminato: {project_name}")
    else:
        print(f"❌ Errore nella rimozione: {project_name}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        cli_status()
        sys.exit(0)
    
    command = sys.argv[1]
    
    if command == "status":
        cli_status()
    elif command == "trust" and len(sys.argv) > 2:
        cli_trust(sys.argv[2])
    elif command == "untrust" and len(sys.argv) > 2:
        cli_untrust(sys.argv[2])
    elif command == "sandbox" and len(sys.argv) > 2:
        cli_sandbox(sys.argv[2])
    elif command == "add-project" and len(sys.argv) > 2:
        name = sys.argv[3] if len(sys.argv) > 3 else None
        cli_add_project(sys.argv[2], name)
    elif command == "switch" and len(sys.argv) > 2:
        cli_switch(sys.argv[2])
    elif command in ("list-projects", "projects"):
        cli_list_projects()
    elif command in ("rm", "remove-project") and len(sys.argv) > 2:
        cli_remove_project(sys.argv[2])
    else:
        print("Usage: python3 config.py [command] [args]")
        print("Commands:")
        print("  status                    Show status")
        print("  trust <folder>            Add trusted folder")
        print("  untrust <folder>          Remove trusted folder")
        print("  sandbox <mode>            Set sandbox mode (strict/prompt/permissive)")
        print("  add-project <path> [name] Add active project")
        print("  switch <name>             Switch to project")
        print("  list-projects (projects)  List all projects")
        print("  rm <name>                 Remove project and its memory")
