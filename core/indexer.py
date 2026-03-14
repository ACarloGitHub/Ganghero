"""
Ganghero - indexer tool
Monitora i file del progetto e aggiorna automaticamente il knowledge graph.

Uso:
    from core.indexer import ProjectIndexer
    indexer = ProjectIndexer("/path/to/project")
    indexer.start()  # Inizia monitoraggio
    indexer.stop()   # Ferma monitoraggio
"""

import json
import time
import threading
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent, FileDeletedEvent
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False

from core.knowledge_graph import build_graph, export_graph


class ProjectEventHandler(FileSystemEventHandler):
    """Gestisce eventi filesystem per il progetto."""
    
    def __init__(self, callback: Callable[[str, str], None]):
        """
        Args:
            callback: Funzione chiamata su evento (event_type, file_path)
        """
        self.callback = callback
        self._last_modified: Dict[str, float] = {}
        self._debounce_seconds = 1.0
    
    def on_modified(self, event):
        if event.is_directory:
            return
        if self._should_process(event.src_path):
            self.callback("modified", event.src_path)
    
    def on_created(self, event):
        if event.is_directory:
            return
        self.callback("created", event.src_path)
    
    def on_deleted(self, event):
        if event.is_directory:
            return
        self.callback("deleted", event.src_path)
    
    def _should_process(self, file_path: str) -> bool:
        """Evita eventi duplicati con debounce."""
        now = time.time()
        last = self._last_modified.get(file_path, 0)
        if now - last < self._debounce_seconds:
            return False
        self._last_modified[file_path] = now
        return True


class ProjectIndexer:
    """
    Indicizzatore automatico del progetto.
    Monitora i file e aggiorna il knowledge graph.
    """
    
    def __init__(self, project_path: str, output_path: Optional[str] = None, 
                 languages: Optional[List[str]] = None,
                 on_change: Optional[Callable[[Dict], None]] = None):
        """
        Args:
            project_path: Percorso del progetto da monitorare
            output_path: Dove salvare il grafo aggiornato (default: projects/{name}_auto.json)
            languages: Linguaggi da monitorare (None = tutti)
            on_change: Callback chiamato quando il grafo cambia
        """
        self.project_path = Path(project_path)
        self.languages = languages
        self.on_change = on_change
        self._running = False
        self._observer: Optional[Observer] = None
        self._last_graph: Optional[Dict] = None
        
        if output_path is None:
            self.output_path = self.project_path.parent / "projects" / f"{self.project_path.name}_auto.json"
        else:
            self.output_path = Path(output_path)
        
        # Assicura che la directory esista
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Log file
        self.log_path = self.output_path.parent / f"{self.project_path.name}_indexer.log"
    
    def _log(self, message: str):
        """Scrive nel log."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] {message}\n"
        with open(self.log_path, "a") as f:
            f.write(log_line)
        print(log_line.strip())
    
    def _handle_event(self, event_type: str, file_path: str):
        """Gestisce un evento filesystem."""
        self._log(f"Evento: {event_type} - {file_path}")
        
        # Ricostruisci il grafo
        self._rebuild_graph()
    
    def _rebuild_graph(self):
        """Ricostruisce il knowledge graph."""
        self._log("Ricostruzione knowledge graph...")
        
        result = build_graph(str(self.project_path), self.languages)
        
        if not result["success"]:
            self._log(f"Errore: {result['error']}")
            return
        
        # Confronta con il grafo precedente
        new_graph = result["graph"]
        changes = self._detect_changes(new_graph)
        
        # Salva il nuovo grafo
        export_result = export_graph(new_graph, str(self.output_path))
        if export_result["success"]:
            self._log(f"Grafo salvato: {self.output_path}")
        else:
            self._log(f"Errore salvataggio: {export_result['error']}")
        
        # Notifica cambiamenti
        if changes and self.on_change:
            self.on_change(changes)
        
        self._last_graph = new_graph
    
    def _detect_changes(self, new_graph: Dict) -> Dict[str, Any]:
        """Rileva cosa è cambiato rispetto al grafo precedente."""
        if self._last_graph is None:
            return {"type": "initial", "files": list(new_graph.get("files", {}).keys())}
        
        old_files = set(self._last_graph.get("files", {}).keys())
        new_files = set(new_graph.get("files", {}).keys())
        
        added = new_files - old_files
        removed = old_files - new_files
        
        # Controlla modifiche nei simboli
        modified = []
        for file_path in old_files & new_files:
            old_count = self._last_graph["files"][file_path].get("symbol_count", 0)
            new_count = new_graph["files"][file_path].get("symbol_count", 0)
            if old_count != new_count:
                modified.append(file_path)
        
        return {
            "type": "update",
            "added": list(added),
            "removed": list(removed),
            "modified": modified,
            "timestamp": datetime.now().isoformat()
        }
    
    def start(self) -> bool:
        """
        Avvia il monitoraggio del progetto.
        
        Returns:
            True se avviato con successo
        """
        if not WATCHDOG_AVAILABLE:
            self._log("Errore: watchdog non installato. Usa: pip install watchdog")
            return False
        
        if self._running:
            self._log("Indexer già in esecuzione")
            return True
        
        self._log(f"Avvio monitoraggio: {self.project_path}")
        
        # Indicizzazione iniziale
        self._rebuild_graph()
        
        # Avvia observer
        event_handler = ProjectEventHandler(self._handle_event)
        self._observer = Observer()
        self._observer.schedule(event_handler, str(self.project_path), recursive=True)
        self._observer.start()
        
        self._running = True
        self._log("Monitoraggio attivo")
        return True
    
    def stop(self):
        """Ferma il monitoraggio."""
        if not self._running:
            return
        
        self._log("Arresto monitoraggio...")
        
        if self._observer:
            self._observer.stop()
            self._observer.join()
        
        self._running = False
        self._log("Monitoraggio fermato")
    
    def is_running(self) -> bool:
        """Restituisce True se il monitoraggio è attivo."""
        return self._running
    
    def get_status(self) -> Dict[str, Any]:
        """Restituisce lo stato corrente."""
        return {
            "running": self._running,
            "project_path": str(self.project_path),
            "output_path": str(self.output_path),
            "log_path": str(self.log_path),
            "languages": self.languages
        }


class SimpleIndexer:
    """
    Versione semplificata senza watchdog (usa polling).
    Utile se watchdog non è disponibile.
    """
    
    def __init__(self, project_path: str, interval: int = 30,
                 output_path: Optional[str] = None,
                 languages: Optional[List[str]] = None):
        """
        Args:
            project_path: Percorso del progetto
            interval: Intervallo di polling in secondi (default: 30)
            output_path: Dove salvare il grafo
            languages: Linguaggi da monitorare
        """
        self.project_path = Path(project_path)
        self.interval = interval
        self.languages = languages
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._last_hashes: Dict[str, str] = {}
        
        if output_path is None:
            self.output_path = self.project_path.parent / "projects" / f"{self.project_path.name}_auto.json"
        else:
            self.output_path = Path(output_path)
        
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
    
    def _get_file_hash(self, path: Path) -> str:
        """Calcola hash semplice del file."""
        try:
            content = path.read_bytes()
            return str(hash(content))
        except:
            return ""
    
    def _scan(self):
        """Scansiona i file e rileva modifiche."""
        from core.knowledge_graph import get_project_files
        
        files = get_project_files(str(self.project_path), self.languages)
        changed = False
        
        for file_path in files:
            file_hash = self._get_file_hash(file_path)
            rel_path = str(file_path.relative_to(self.project_path))
            
            if rel_path not in self._last_hashes:
                print(f"[INDEXER] Nuovo file: {rel_path}")
                changed = True
            elif self._last_hashes[rel_path] != file_hash:
                print(f"[INDEXER] Modificato: {rel_path}")
                changed = True
            
            self._last_hashes[rel_path] = file_hash
        
        # Rimuovi file cancellati
        current_files = {str(f.relative_to(self.project_path)) for f in files}
        removed = set(self._last_hashes.keys()) - current_files
        for rel_path in removed:
            print(f"[INDEXER] Rimosso: {rel_path}")
            del self._last_hashes[rel_path]
            changed = True
        
        if changed:
            print("[INDEXER] Aggiornamento grafo...")
            result = build_graph(str(self.project_path), self.languages)
            if result["success"]:
                export_graph(result["graph"], str(self.output_path))
                print(f"[INDEXER] Grafo aggiornato: {self.output_path}")
    
    def _run(self):
        """Loop di polling."""
        while self._running:
            self._scan()
            time.sleep(self.interval)
    
    def start(self) -> bool:
        """Avvia il polling."""
        if self._running:
            return True
        
        print(f"[INDEXER] Avvio polling ogni {self.interval}s: {self.project_path}")
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        return True
    
    def stop(self):
        """Ferma il polling."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        print("[INDEXER] Fermato")


def run_indexer(project_path: str, duration: Optional[int] = None) -> Dict[str, Any]:
    """
    Esegue l'indicizzatore per un periodo specificato.
    
    Args:
        project_path: Percorso del progetto
        duration: Secondi di esecuzione (None = infinito, usa Ctrl+C)
    
    Returns:
        dict con 'success', 'output_path', 'duration', o 'error'
    """
    indexer = ProjectIndexer(project_path)
    
    if not indexer.start():
        # Fallback a SimpleIndexer
        print("Uso SimpleIndexer (polling)...")
        indexer = SimpleIndexer(project_path)
        indexer.start()
    
    try:
        if duration:
            print(f"Monitoraggio per {duration} secondi...")
            time.sleep(duration)
        else:
            print("Monitoraggio attivo. Premi Ctrl+C per fermare.")
            while True:
                time.sleep(1)
    except KeyboardInterrupt:
        print("\nInterrotto da utente")
    finally:
        indexer.stop()
    
    return {
        "success": True,
        "output_path": str(indexer.output_path),
        "duration": duration
    }


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Uso: python3 indexer.py /path/to/project [duration_seconds]")
        sys.exit(1)
    
    project = sys.argv[1]
    duration = int(sys.argv[2]) if len(sys.argv) > 2 else None
    
    result = run_indexer(project, duration)
    print(json.dumps(result, indent=2))
