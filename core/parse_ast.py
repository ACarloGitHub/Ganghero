"""
Ganghero - parse_ast tool
Parsa file sorgente e estrae simboli (funzioni, classi, import) usando tree-sitter.

Uso:
    from core.parse_ast import run, extract_symbols
    ast = run("/path/to/file.py")
    symbols = extract_symbols("/path/to/file.py")
"""

from pathlib import Path
from typing import Dict, List, Optional, Any

try:
    from tree_sitter import Language, Parser, Tree
    from tree_sitter_python import language as python_lang
    from tree_sitter_javascript import language as js_lang
    from tree_sitter_typescript import language_typescript, language_tsx
    from tree_sitter_rust import language as rust_lang
    TREE_SITTER_AVAILABLE = True
except ImportError as e:
    TREE_SITTER_AVAILABLE = False
    Language = Parser = Tree = None
    print(f"[DEBUG] Import error: {e}")

# Mappa estensioni -> linguaggi
LANGUAGE_MAP = {
    '.py': 'python',
    '.js': 'javascript',
    '.jsx': 'javascript',
    '.ts': 'typescript',
    '.tsx': 'typescript',
    '.rs': 'rust',
}

# Cache dei parser
_parser_cache: Dict[str, Parser] = {}


def _get_parser(language_name: str) -> Optional[Parser]:
    """Ottiene o crea un parser per il linguaggio specificato."""
    if not TREE_SITTER_AVAILABLE:
        return None
    
    if language_name in _parser_cache:
        return _parser_cache[language_name]
    
    lang_map = {
        'python': python_lang,
        'javascript': js_lang,
        'typescript': language_typescript,
        'rust': rust_lang,
    }
    
    if language_name not in lang_map:
        return None
    
    # API tree-sitter 0.25+: language() restituisce PyCapsule, 
    # dobbiamo wrapparlo in Language()
    lang = Language(lang_map[language_name]())
    parser = Parser(lang)
    _parser_cache[language_name] = parser
    return parser


def run(path: str) -> Dict[str, Any]:
    """
    Parsa un file e restituisce l'AST.
    
    Args:
        path: Percorso del file da parsare
        
    Returns:
        dict con 'success', 'ast' (tree root), 'language', o 'error'
    """
    if not TREE_SITTER_AVAILABLE:
        return {"success": False, "error": "tree-sitter not installed"}
    
    try:
        file_path = Path(path)
        if not file_path.exists():
            return {"success": False, "error": f"File not found: {path}"}
        
        ext = file_path.suffix.lower()
        language = LANGUAGE_MAP.get(ext)
        
        if not language:
            return {"success": False, "error": f"Unsupported file type: {ext}"}
        
        parser = _get_parser(language)
        if not parser:
            return {"success": False, "error": f"Parser not available for: {language}"}
        
        content = file_path.read_text()
        if not content:
            return {"success": True, "ast": None, "language": language, "empty": True}
        
        tree = parser.parse(content.encode('utf-8'))
        
        return {
            "success": True,
            "ast": tree.root_node,
            "language": language,
            "path": str(file_path),
            "content": content
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def _get_node_text(node, content: str) -> str:
    """Estrae il testo di un nodo dall'AST."""
    return content[node.start_byte:node.end_byte]


def _extract_python_symbols(root_node, content: str) -> List[Dict]:
    """Estrae simboli da file Python."""
    symbols = []
    
    def traverse(node, parent_type=None):
        # Funzioni
        if node.type == 'function_definition':
            name_node = None
            for child in node.children:
                if child.type == 'identifier':
                    name_node = child
                    break
            if name_node:
                symbols.append({
                    "type": "function",
                    "name": _get_node_text(name_node, content),
                    "line": node.start_point[0] + 1,
                    "column": node.start_point[1]
                })
        
        # Classi
        elif node.type == 'class_definition':
            name_node = None
            for child in node.children:
                if child.type == 'identifier':
                    name_node = child
                    break
            if name_node:
                symbols.append({
                    "type": "class",
                    "name": _get_node_text(name_node, content),
                    "line": node.start_point[0] + 1,
                    "column": node.start_point[1]
                })
        
        # Import
        elif node.type in ('import_statement', 'import_from_statement'):
            import_text = _get_node_text(node, content).strip()
            symbols.append({
                "type": "import",
                "name": import_text,
                "line": node.start_point[0] + 1,
                "column": node.start_point[1]
            })
        
        for child in node.children:
            traverse(child, node.type)
    
    traverse(root_node)
    return symbols


def _extract_js_ts_symbols(root_node, content: str, is_typescript: bool = False) -> List[Dict]:
    """Estrae simboli da file JavaScript/TypeScript."""
    symbols = []
    
    def traverse(node):
        # Funzioni (varie forme)
        if node.type in ('function_declaration', 'function', 'arrow_function'):
            name = None
            for child in node.children:
                if child.type == 'identifier':
                    name = _get_node_text(child, content)
                    break
            if name:
                symbols.append({
                    "type": "function",
                    "name": name,
                    "line": node.start_point[0] + 1,
                    "column": node.start_point[1]
                })
        
        # Classi
        elif node.type == 'class_declaration':
            name = None
            for child in node.children:
                if child.type == 'type_identifier' if is_typescript else child.type == 'identifier':
                    name = _get_node_text(child, content)
                    break
            if name:
                symbols.append({
                    "type": "class",
                    "name": name,
                    "line": node.start_point[0] + 1,
                    "column": node.start_point[1]
                })
        
        # Import
        elif node.type == 'import_statement':
            import_text = _get_node_text(node, content).strip()
            symbols.append({
                "type": "import",
                "name": import_text[:50] + "..." if len(import_text) > 50 else import_text,
                "line": node.start_point[0] + 1,
                "column": node.start_point[1]
            })
        
        for child in node.children:
            traverse(child)
    
    traverse(root_node)
    return symbols


def _extract_rust_symbols(root_node, content: str) -> List[Dict]:
    """Estrae simboli da file Rust."""
    symbols = []
    
    def traverse(node):
        # Funzioni
        if node.type == 'function_item':
            name = None
            for child in node.children:
                if child.type == 'identifier':
                    name = _get_node_text(child, content)
                    break
            if name:
                symbols.append({
                    "type": "function",
                    "name": name,
                    "line": node.start_point[0] + 1,
                    "column": node.start_point[1]
                })
        
        # Struct
        elif node.type == 'struct_item':
            name = None
            for child in node.children:
                if child.type == 'type_identifier':
                    name = _get_node_text(child, content)
                    break
            if name:
                symbols.append({
                    "type": "struct",
                    "name": name,
                    "line": node.start_point[0] + 1,
                    "column": node.start_point[1]
                })
        
        # Use (import)
        elif node.type == 'use_declaration':
            use_text = _get_node_text(node, content).strip()
            symbols.append({
                "type": "use",
                "name": use_text[:50] + "..." if len(use_text) > 50 else use_text,
                "line": node.start_point[0] + 1,
                "column": node.start_point[1]
            })
        
        for child in node.children:
            traverse(child)
    
    traverse(root_node)
    return symbols


def extract_symbols(path: str) -> Dict[str, Any]:
    """
    Estrae simboli (funzioni, classi, import) da un file.
    
    Args:
        path: Percorso del file da analizzare
        
    Returns:
        dict con 'success', 'symbols' (lista), 'language', o 'error'
    """
    result = run(path)
    if not result["success"]:
        return result
    
    if result.get("empty"):
        return {"success": True, "symbols": [], "language": result["language"], "path": path, "count": 0}
    
    ast = result["ast"]
    content = result["content"]
    language = result["language"]
    
    if language == 'python':
        symbols = _extract_python_symbols(ast, content)
    elif language in ('javascript', 'typescript'):
        symbols = _extract_js_ts_symbols(ast, content, is_typescript=(language == 'typescript'))
    elif language == 'rust':
        symbols = _extract_rust_symbols(ast, content)
    else:
        symbols = []
    
    return {
        "success": True,
        "symbols": symbols,
        "language": language,
        "path": path,
        "count": len(symbols)
    }


def get_file_structure(path: str) -> Dict[str, Any]:
    """
    Restituisce la struttura completa di un file (solo tipi di nodo).
    Utile per debug e per capire la struttura di un nuovo linguaggio.
    
    Args:
        path: Percorso del file
        
    Returns:
        dict con 'success', 'structure' (albero semplificato), o 'error'
    """
    result = run(path)
    if not result["success"]:
        return result
    
    def simplify_tree(node, depth=0):
        result = {
            "type": node.type,
            "line": node.start_point[0] + 1,
            "children": []
        }
        for child in node.children:
            if depth < 3:  # Limita profondità
                result["children"].append(simplify_tree(child, depth + 1))
        return result
    
    return {
        "success": True,
        "structure": simplify_tree(result["ast"]),
        "language": result["language"],
        "path": path
    }


if __name__ == "__main__":
    # Test
    import json
    
    # Test su se stesso
    result = extract_symbols(__file__)
    print(json.dumps(result, indent=2, default=str))
