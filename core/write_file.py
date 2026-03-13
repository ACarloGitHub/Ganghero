"""
Ganghero - write_file tool
Scrive contenuto in un file sul filesystem.

Uso:
    from core.write_file import run
    run("/path/to/file", "contenuto")
"""

from pathlib import Path


def run(path: str, content: str) -> bool:
    """
    Scrive contenuto in un file.
    Crea le directory se non esistono.
    
    Args:
        path: Percorso del file da scrivere
        content: Contenuto da scrivere
        
    Returns:
        True se successo
        
    Raises:
        PermissionError: Se non hai i permessi di scrittura
    """
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content)
    return True


def run_safe(path: str, content: str) -> dict:
    """
    Scrive contenuto in un file con gestione errori.
    Crea le directory se non esistono.
    
    Args:
        path: Percorso del file da scrivere
        content: Contenuto da scrivere
        
    Returns:
        dict con 'success' o 'error'
    """
    try:
        file_path = Path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content)
        return {"success": True, "path": str(file_path.absolute())}
    except PermissionError:
        return {"success": False, "error": f"Permission denied: {path}"}
    except Exception as e:
        return {"success": False, "error": str(e)}