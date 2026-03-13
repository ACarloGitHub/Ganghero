"""
Ganghero - search tool
Ricerca veloce nel codice usando ripgrep.

Uso:
    from core.search import run
    results = run("def activate")
"""

import subprocess
from pathlib import Path


def run(query: str, path: str = ".") -> str:
    """
    Cerca nel codice usando ripgrep.
    
    Args:
        query: Termine di ricerca
        path: Percorso base (default: directory corrente)
        
    Returns:
        Output di ripgrep con risultati
        
    Raises:
        FileNotFoundError: Se ripgrep non è installato
    """
    result = subprocess.run(
        ["rg", "--line-number", "--color=never", query, path],
        capture_output=True,
        text=True
    )
    return result.stdout


def run_safe(query: str, path: str = ".") -> dict:
    """
    Cerca nel codice con gestione errori.
    
    Args:
        query: Termine di ricerca
        path: Percorso base (default: directory corrente)
        
    Returns:
        dict con 'success', 'results' o 'error'
    """
    try:
        result = subprocess.run(
            ["rg", "--line-number", "--color=never", query, path],
            capture_output=True,
            text=True
        )
        return {
            "success": True,
            "results": result.stdout,
            "return_code": result.returncode
        }
    except FileNotFoundError:
        return {"success": False, "error": "ripgrep (rg) non è installato"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def search_files(extension: str, path: str = ".") -> str:
    """
    Trova tutti i file con una certa estensione.
    
    Args:
        extension: Estensione file (es. "py", "js")
        path: Percorso base
        
    Returns:
        Lista di file trovati
    """
    result = subprocess.run(
        ["rg", "--files", f"--typeglob=*.{extension}", path],
        capture_output=True,
        text=True
    )
    return result.stdout