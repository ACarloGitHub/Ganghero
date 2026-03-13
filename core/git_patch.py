"""
Ganghero - git_patch tool
Applica modifiche incrementali con git patch.

Uso:
    from core.git_patch import apply_patch, create_patch
    apply_patch("diff --git a/file.py ...")
"""

import subprocess
from pathlib import Path


def apply_patch(patch_content: str, repo_path: str = ".") -> dict:
    """
    Applica una patch git.
    
    Args:
        patch_content: Contenuto della patch (formato git diff)
        repo_path: Percorso del repository (default: directory corrente)
        
    Returns:
        dict con 'success' o 'error'
    """
    try:
        result = subprocess.run(
            ["git", "apply"],
            input=patch_content,
            capture_output=True,
            text=True,
            cwd=repo_path
        )
        if result.returncode == 0:
            return {"success": True, "message": "Patch applicata con successo"}
        else:
            return {"success": False, "error": result.stderr}
    except Exception as e:
        return {"success": False, "error": str(e)}


def create_patch(file_path: str, old_content: str, new_content: str) -> str:
    """
    Crea una patch diff per un file.
    
    Args:
        file_path: Percorso del file
        old_content: Contenuto originale
        new_content: Contenuto nuovo
        
    Returns:
        Stringa con la patch in formato git diff
    """
    import difflib
    
    old_lines = old_content.splitlines(keepends=True)
    new_lines = new_content.splitlines(keepends=True)
    
    diff = difflib.unified_diff(
        old_lines,
        new_lines,
        fromfile=f"a/{file_path}",
        tofile=f"b/{file_path}",
        lineterm=""
    )
    
    return "".join(diff)


def revert_patch(patch_content: str, repo_path: str = ".") -> dict:
    """
    Reverifica una patch applicata.
    
    Args:
        patch_content: Contenuto della patch
        repo_path: Percorso del repository
        
    Returns:
        dict con 'success' o 'error'
    """
    try:
        result = subprocess.run(
            ["git", "apply", "-R"],
            input=patch_content,
            capture_output=True,
            text=True,
            cwd=repo_path
        )
        if result.returncode == 0:
            return {"success": True, "message": "Patch reversata con successo"}
        else:
            return {"success": False, "error": result.stderr}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_diff(repo_path: str = ".") -> str:
    """
    Ottiene il diff corrente del repository.
    
    Args:
        repo_path: Percorso del repository
        
    Returns:
        Stringa con il diff
    """
    result = subprocess.run(
        ["git", "diff"],
        capture_output=True,
        text=True,
        cwd=repo_path
    )
    return result.stdout