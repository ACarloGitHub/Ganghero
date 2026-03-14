"""
Ganghero - knowledge_graph tool
Costruisce un grafo di conoscenza del codice: simboli, relazioni, dipendenze.

Uso:
    from core.knowledge_graph import build_graph, query_symbol
    graph = build_graph("/path/to/project", language="python")
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Set, Any
from datetime import datetime

# Import condizionale di parse_ast
try:
    from core.parse_ast import extract_symbols, LANGUAGE_MAP
    PARSE_AST_AVAILABLE = True
except ImportError:
    PARSE_AST_AVAILABLE = False


def get_project_files(project_path: str, languages: Optional[List[str]] = None) -> List[Path]:
    """
    Trova tutti i file sorgente in un progetto.
    
    Args:
        project_path: Percorso radice del progetto
        languages: Lista di linguaggi da includere (es. ['python', 'javascript'])
                  Se None, include tutti i linguaggi supportati
    
    Returns:
        Lista di Path ai file sorgente
    """
    if languages is None:
        languages = list(LANGUAGE_MAP.keys())
    
    extensions = []
    for lang in languages:
        extensions.extend([ext for ext, l in LANGUAGE_MAP.items() if l == lang])
    
    project = Path(project_path)
    files = []
    
    # Pattern da escludere
    exclude_dirs = [
        'node_modules',
        'venv',
        '__pycache__',
        '.git',
        'dist',
        'build',
        '.pytest_cache',
        '.mypy_cache',
    ]
    
    exclude_patterns = [
        '**/*.min.js',
        '**/*.min.css',
    ]
    
    for ext in extensions:
        for file_path in project.rglob(f'*{ext}'):
            # Controlla se il file è in una directory da escludere
            should_exclude = False
            for part in file_path.parts:
                if part in exclude_dirs:
                    should_exclude = True
                    break
            
            # Controlla pattern
            if not should_exclude:
                for pattern in exclude_patterns:
                    if file_path.match(pattern):
                        should_exclude = True
                        break
            
            if not should_exclude:
                files.append(file_path)
    
    return sorted(files)


def build_graph(project_path: str, languages: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Costruisce il knowledge graph di un progetto.
    
    Args:
        project_path: Percorso radice del progetto
        languages: Lista di linguaggi da analizzare (None = tutti)
    
    Returns:
        dict con 'success', 'graph' (struttura), 'stats', o 'error'
    """
    if not PARSE_AST_AVAILABLE:
        return {"success": False, "error": "parse_ast not available"}
    
    try:
        project = Path(project_path)
        if not project.exists():
            return {"success": False, "error": f"Project not found: {project_path}"}
        
        # Trova tutti i file
        files = get_project_files(project_path, languages)
        
        # Struttura del grafo
        graph = {
            "metadata": {
                "project_path": str(project.absolute()),
                "created": datetime.now().isoformat(),
                "languages": languages or list(LANGUAGE_MAP.keys()),
            },
            "files": {},
            "symbols": {},
            "relations": []
        }
        
        # Analizza ogni file
        for file_path in files:
            rel_path = str(file_path.relative_to(project))
            result = extract_symbols(str(file_path))
            
            if not result["success"]:
                continue
            
            # Aggiungi file al grafo
            graph["files"][rel_path] = {
                "language": result["language"],
                "symbol_count": result["count"],
                "symbols": []
            }
            
            # Aggiungi simboli
            for symbol in result["symbols"]:
                symbol_id = f"{rel_path}::{symbol['name']}"
                symbol_data = {
                    "id": symbol_id,
                    "name": symbol["name"],
                    "type": symbol["type"],
                    "file": rel_path,
                    "line": symbol["line"],
                    "column": symbol["column"]
                }
                graph["symbols"][symbol_id] = symbol_data
                graph["files"][rel_path]["symbols"].append(symbol_id)
                
                # Relazione: file contiene simbolo
                graph["relations"].append({
                    "from": rel_path,
                    "to": symbol_id,
                    "type": "contains"
                })
        
        # Statistiche
        stats = {
            "total_files": len(graph["files"]),
            "total_symbols": len(graph["symbols"]),
            "total_relations": len(graph["relations"]),
            "files_by_language": {}
        }
        
        for file_data in graph["files"].values():
            lang = file_data["language"]
            stats["files_by_language"][lang] = stats["files_by_language"].get(lang, 0) + 1
        
        graph["metadata"]["stats"] = stats
        
        return {
            "success": True,
            "graph": graph,
            "stats": stats
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}


def query_symbol(graph: Dict, symbol_name: str) -> List[Dict]:
    """
    Cerca simboli per nome nel grafo.
    
    Args:
        graph: Knowledge graph
        symbol_name: Nome del simbolo da cercare
    
    Returns:
        Lista di simboli che corrispondono
    """
    results = []
    for symbol_id, symbol_data in graph.get("symbols", {}).items():
        if symbol_name.lower() in symbol_data["name"].lower():
            results.append(symbol_data)
    return results


def get_file_symbols(graph: Dict, file_path: str) -> List[Dict]:
    """
    Ottiene tutti i simboli di un file.
    
    Args:
        graph: Knowledge graph
        file_path: Percorso relativo del file
    
    Returns:
        Lista di simboli nel file
    """
    file_data = graph.get("files", {}).get(file_path, {})
    symbol_ids = file_data.get("symbols", [])
    
    results = []
    for sid in symbol_ids:
        if sid in graph.get("symbols", {}):
            results.append(graph["symbols"][sid])
    return results


def export_graph(graph: Dict, output_path: str) -> Dict[str, Any]:
    """
    Esporta il grafo in formato JSON.
    
    Args:
        graph: Knowledge graph
        output_path: Percorso dove salvare il JSON
    
    Returns:
        dict con 'success', 'path', o 'error'
    """
    try:
        output = Path(output_path)
        output.write_text(json.dumps(graph, indent=2, default=str))
        return {"success": True, "path": str(output)}
    except Exception as e:
        return {"success": False, "error": str(e)}


def load_graph(input_path: str) -> Dict[str, Any]:
    """
    Carica un grafo da file JSON.
    
    Args:
        input_path: Percorso del file JSON
    
    Returns:
        dict con 'success', 'graph', o 'error'
    """
    try:
        data = Path(input_path).read_text()
        graph = json.loads(data)
        return {"success": True, "graph": graph}
    except Exception as e:
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    # Test sul progetto Ganghero stesso
    import sys
    sys.path.insert(0, '.')
    
    result = build_graph(".", languages=["python"])
    if result["success"]:
        print(f"Graph built:")
        print(f"  Files: {result['stats']['total_files']}")
        print(f"  Symbols: {result['stats']['total_symbols']}")
        print(f"  By language: {result['stats']['files_by_language']}")
        
        # Salva il grafo
        export_result = export_graph(result["graph"], "projects/ganghero_graph.json")
        if export_result["success"]:
            print(f"  Saved to: {export_result['path']}")
    else:
        print(f"Error: {result['error']}")
