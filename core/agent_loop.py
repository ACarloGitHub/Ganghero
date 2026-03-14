"""
Ganghero - agent_loop
Loop operativo agente: plan → execute → observe → save

Uso:
    from core.agent_loop import AgentLoop
    agent = AgentLoop()
    result = agent.run_task("Rifattorizza tutte le funzioni confirm in 3LO")
"""

import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import Config
from core.read_file import run as read_file
from core.write_file import run as write_file
from core.run_terminal import run as run_terminal
from core.search import run as search_code
from core.parse_ast import extract_symbols
from core.knowledge_graph import build_graph
from core.git_patch import create_patch, apply_patch


@dataclass
class Step:
    """Singolo passo del piano."""
    id: int
    action: str  # read, write, search, exec, analyze
    target: str  # file path, search query, command
    description: str
    status: str = "pending"  # pending, running, completed, failed
    result: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


@dataclass
class Task:
    """Task completo da eseguire."""
    id: str
    description: str
    project_path: str
    steps: List[Step]
    status: str = "pending"  # pending, running, completed, failed
    created_at: str = ""
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


class AgentLoop:
    """
    Agente autonomo che esegue task complessi.
    
    Ciclo:
    1. PLAN: Analizza il task e crea passi
    2. EXECUTE: Esegue ogni passo con i tool
    3. OBSERVE: Verifica risultati e adatta piano
    4. SAVE: Memorizza stato e risultati
    """
    
    def __init__(self, project_path: Optional[str] = None):
        """
        Args:
            project_path: Percorso progetto (default: current project da config)
        """
        self.config = Config()
        
        if project_path is None:
            current = self.config.get_current_project()
            if current:
                self.project_path = Path(current['path'])
            else:
                self.project_path = Path.cwd()
        else:
            self.project_path = Path(project_path)
        
        self.current_task: Optional[Task] = None
        self.history: List[Task] = []
        
        # Tool disponibili
        self.tools = {
            'read': self._tool_read,
            'write': self._tool_write,
            'search': self._tool_search,
            'exec': self._tool_exec,
            'analyze': self._tool_analyze,
        }
    
    # === TOOL WRAPPERS ===
    
    def _tool_read(self, target: str) -> Dict:
        """Legge un file."""
        path = self._resolve_path(target)
        try:
            content = read_file(str(path))
            return {"success": True, "content": content, "path": str(path)}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _tool_write(self, target: str, content: str) -> Dict:
        """Scrive un file."""
        path = self._resolve_path(target)
        try:
            write_file(str(path), content)
            return {"success": True, "path": str(path)}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _tool_search(self, target: str) -> Dict:
        """Cerca nel codice."""
        try:
            results = search_code(target, path=str(self.project_path))
            return {"success": True, "results": results}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _tool_exec(self, target: str) -> Dict:
        """Esegue comando shell."""
        try:
            result = run_terminal(target)
            return {"success": True, "output": result}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _tool_analyze(self, target: str) -> Dict:
        """Analizza file con AST."""
        path = self._resolve_path(target)
        try:
            result = extract_symbols(str(path))
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _resolve_path(self, target: str) -> Path:
        """Risolve percorso relativo al progetto."""
        path = Path(target)
        if not path.is_absolute():
            path = self.project_path / path
        return path.resolve()
    
    # === CORE LOOP ===
    
    def plan(self, description: str) -> Task:
        """
        Crea piano per il task.
        
        Args:
            description: Descrizione del task da completare
        
        Returns:
            Task con steps pianificati
        """
        task_id = f"task_{int(time.time())}"
        
        # Analisi semplice del task per creare steps
        steps = self._create_plan_from_description(description)
        
        task = Task(
            id=task_id,
            description=description,
            project_path=str(self.project_path),
            steps=steps
        )
        
        return task
    
    def _create_plan_from_description(self, description: str) -> List[Step]:
        """
        Crea steps da descrizione task.
        Questa è una versione semplificata — in futuro potrebbe usare LLM.
        """
        steps = []
        desc_lower = description.lower()
        
        # Pattern matching semplice per task comuni
        if "rifattorizza" in desc_lower or "refactor" in desc_lower:
            # Esempio: "Rifattorizza tutte le funzioni confirm"
            if "funzioni" in desc_lower or "functions" in desc_lower:
                # Cerca funzioni
                steps.append(Step(
                    id=1,
                    action="search",
                    target="def confirm",
                    description="Trova tutte le funzioni confirm"
                ))
                steps.append(Step(
                    id=2,
                    action="analyze",
                    target="src/home.js",  # Esempio
                    description="Analizza struttura funzioni"
                ))
        
        elif "trova" in desc_lower or "find" in desc_lower:
            # Task di ricerca
            query = description.split("trova")[-1].strip() if "trova" in desc_lower else description
            steps.append(Step(
                id=1,
                action="search",
                target=query,
                description=f"Cerca: {query}"
            ))
        
        elif "analizza" in desc_lower or "analyze" in desc_lower:
            # Task di analisi
            steps.append(Step(
                id=1,
                action="analyze",
                target=".",
                description="Analizza progetto"
            ))
        
        else:
            # Piano generico
            steps.append(Step(
                id=1,
                action="search",
                target=description,
                description=f"Cerca informazioni su: {description}"
            ))
        
        return steps
    
    def execute_step(self, step: Step) -> Step:
        """Esegue un singolo step."""
        step.started_at = datetime.now().isoformat()
        step.status = "running"
        
        tool = self.tools.get(step.action)
        if not tool:
            step.status = "failed"
            step.result = f"Tool non trovato: {step.action}"
            step.completed_at = datetime.now().isoformat()
            return step
        
        try:
            if step.action == "write":
                # Per write serve anche il contenuto
                # In una versione completa, il contenuto verrebbe dal planning
                result = tool(step.target, "# TODO: contenuto da generare")
            else:
                result = tool(step.target)
            
            step.result = json.dumps(result, indent=2, default=str)
            step.status = "completed"
        except Exception as e:
            step.status = "failed"
            step.result = str(e)
        
        step.completed_at = datetime.now().isoformat()
        return step
    
    def observe(self, step: Step) -> bool:
        """
        Osserva risultato e decide se continuare o adattare.
        
        Returns:
            True se procedere, False se fermarsi
        """
        if step.status == "failed":
            # In versione avanzata: potrebbe riprovare o adattare piano
            return False
        return True
    
    def save(self, task: Task):
        """Salva task e risultati."""
        # Salva in memoria progetto
        memory = self.config.load_project_memory(str(self.project_path)) or {}
        
        if "tasks" not in memory:
            memory["tasks"] = []
        
        memory["tasks"].append(asdict(task))
        memory["last_task"] = asdict(task)
        
        self.config.save_project_memory(str(self.project_path), memory)
        
        # Aggiungi a history
        self.history.append(task)
    
    def run_task(self, description: str, auto_execute: bool = True) -> Task:
        """
        Esegue task completo: plan → execute → observe → save
        
        Args:
            description: Descrizione del task
            auto_execute: Se True, esegue automaticamente i passi
        
        Returns:
            Task completato
        """
        print(f"🎯 TASK: {description}")
        print(f"📁 Progetto: {self.project_path}")
        print()
        
        # 1. PLAN
        print("📋 PIANIFICAZIONE...")
        task = self.plan(description)
        print(f"   Creato piano con {len(task.steps)} passi:")
        for step in task.steps:
            print(f"   {step.id}. [{step.action}] {step.description}")
        print()
        
        task.status = "running"
        task.started_at = datetime.now().isoformat()
        self.current_task = task
        
        if not auto_execute:
            return task
        
        # 2. EXECUTE + 3. OBSERVE
        print("⚙️  ESECUZIONE...")
        for i, step in enumerate(task.steps):
            print(f"\n   Passo {step.id}: {step.description}")
            print(f"   Azione: {step.action}({step.target})")
            
            step = self.execute_step(step)
            task.steps[i] = step
            
            if step.status == "completed":
                print(f"   ✅ Completato")
                if step.result:
                    # Tronca risultato lungo
                    result_preview = step.result[:200] + "..." if len(step.result) > 200 else step.result
                    print(f"   Risultato: {result_preview}")
            else:
                print(f"   ❌ Fallito: {step.result}")
            
            # OBSERVE
            if not self.observe(step):
                print(f"\n⛔ Interrotto per errore al passo {step.id}")
                task.status = "failed"
                break
            
            # Piccola pausa tra passi
            time.sleep(0.5)
        
        if task.status != "failed":
            task.status = "completed"
        
        task.completed_at = datetime.now().isoformat()
        
        # 4. SAVE
        print(f"\n💾 SALVATAGGIO...")
        self.save(task)
        print(f"   Task salvato in memoria progetto")
        
        print(f"\n✅ TASK COMPLETATO: {task.status}")
        return task
    
    def get_task_history(self) -> List[Task]:
        """Restituisce storico task."""
        memory = self.config.load_project_memory(str(self.project_path))
        if memory and "tasks" in memory:
            return [Task(**t) for t in memory["tasks"]]
        return []
    
    def get_last_task(self) -> Optional[Task]:
        """Restituisce ultimo task."""
        memory = self.config.load_project_memory(str(self.project_path))
        if memory and "last_task" in memory:
            return Task(**memory["last_task"])
        return None


def demo():
    """Demo del agent loop."""
    print("=" * 70)
    print("GANGHERO AGENT LOOP - DEMO")
    print("=" * 70)
    print()
    
    # Crea agente per 3LO
    agent = AgentLoop("/home/carlo/progetti/3lo")
    
    # Esegui task di ricerca
    task = agent.run_task("Trova tutte le funzioni confirm nel progetto")
    
    print()
    print("=" * 70)
    print("RIEPILOGO FINALE")
    print("=" * 70)
    print(f"Task ID: {task.id}")
    print(f"Status: {task.status}")
    print(f"Passi completati: {sum(1 for s in task.steps if s.status == 'completed')}/{len(task.steps)}")


if __name__ == "__main__":
    demo()
