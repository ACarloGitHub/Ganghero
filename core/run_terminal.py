"""
Ganghero - run_terminal tool
Esegue comandi shell e restituisce l'output.

Uso:
    from core.run_terminal import run
    output = run("ls -la")
"""

import subprocess


def run(cmd: str, timeout: int = 30) -> str:
    """
    Esegue un comando shell.
    
    Args:
        cmd: Comando da eseguire
        timeout: Timeout in secondi (default: 30)
        
    Returns:
        Output del comando (stdout + stderr)
        
    Raises:
        subprocess.TimeoutExpired: Se il comando supera il timeout
    """
    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=True,
        text=True,
        timeout=timeout
    )
    return result.stdout + result.stderr


def run_safe(cmd: str, timeout: int = 30) -> dict:
    """
    Esegue un comando shell con gestione errori.
    
    Args:
        cmd: Comando da eseguire
        timeout: Timeout in secondi (default: 30)
        
    Returns:
        dict con 'success', 'output', 'return_code' o 'error'
    """
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return {
            "success": result.returncode == 0,
            "output": result.stdout + result.stderr,
            "return_code": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": f"Command timed out after {timeout}s"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def run_async(cmd: str) -> subprocess.Popen:
    """
    Esegue un comando in background (non bloccante).
    
    Args:
        cmd: Comando da eseguire
        
    Returns:
        Processo Popen per monitoraggio
    """
    return subprocess.Popen(
        cmd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )