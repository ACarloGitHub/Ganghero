"""
Ganghero - read_file tool
Legge il contenuto di un file dal filesystem.

Uso:
    from core.read_file import run
    content = run("/path/to/file")
"""

from pathlib import Path


def run(path: str) -> str:
    """
    Legge il contenuto di un file.
    
    Args:
        path: Percorso del file da leggere
        
    Returns:
        Contenuto del file come stringa
        
    Raises:
        FileNotFoundError: Se il file non esiste
        PermissionError: Se non hai i permessi di lettura
    """
    return Path(path).read_text()


def run_safe(path: str) -> dict:
    """
    Legge il contenuto di un file con gestione errori.
    
    Args:
        path: Percorso del file da leggere
        
    Returns:
        dict con 'success', 'content' o 'error'
    """
    try:
        content = Path(path).read_text()
        return {"success": True, "content": content}
    except FileNotFoundError:
        return {"success": False, "error": f"File not found: {path}"}
    except PermissionError:
        return {"success": False, "error": f"Permission denied: {path}"}
    except Exception as e:
        return {"success": False, "error": str(e)}