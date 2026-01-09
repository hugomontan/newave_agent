"""
Script para verificar imports quebrados e referências a módulos antigos.
"""

import os
import re
from pathlib import Path
from typing import List, Tuple

# Diretórios a verificar
CHECK_DIRS = [
    "app/agents/single_deck",
    "app/agents/multi_deck",
    "app/main.py",
]

# Padrões proibidos (módulos deletados)
FORBIDDEN_IMPORTS = [
    r"from app\.agents\.shared",
    r"from app\.agents\.nodes",
    r"from app\.comparison",
    r"import app\.agents\.shared",
    r"import app\.agents\.nodes",
    r"import app\.comparison",
]

# Padrões que devem ser verificados
CHECK_PATTERNS = [
    (r"AgentState", "AgentState deve ser SingleDeckState ou MultiDeckState"),
    (r"analysis_mode", "analysis_mode não deve existir nos nodes"),
]

# Imports esperados no main.py
MAIN_EXPECTED_IMPORTS = [
    "from app.agents.single_deck.graph import",
    "from app.agents.multi_deck.graph import",
]


def find_python_files(directory: str) -> List[Path]:
    """Encontra todos os arquivos Python no diretório."""
    files = []
    path = Path(directory)
    if path.is_file():
        return [path] if path.suffix == ".py" else []
    
    for py_file in path.rglob("*.py"):
        files.append(py_file)
    return files


def check_file(file_path: Path) -> List[Tuple[str, int, str]]:
    """
    Verifica um arquivo Python por problemas de import.
    
    Returns:
        Lista de tuplas (tipo_problema, linha, mensagem)
    """
    issues = []
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except Exception as e:
        issues.append(("ERROR", 0, f"Não foi possível ler arquivo: {e}"))
        return issues
    
    for line_num, line in enumerate(lines, 1):
        # Verificar imports proibidos
        for pattern in FORBIDDEN_IMPORTS:
            if re.search(pattern, line):
                issues.append((
                    "FORBIDDEN_IMPORT",
                    line_num,
                    f"Import proibido encontrado: {line.strip()}"
                ))
        
        # Verificar padrões que devem ser verificados
        for pattern, message in CHECK_PATTERNS:
            if re.search(pattern, line):
                # Verificar se é um comentário ou string
                if not (line.strip().startswith("#") or '"' in line or "'" in line):
                    issues.append((
                        "CHECK_PATTERN",
                        line_num,
                        f"{message}: {line.strip()}"
                    ))
    
    return issues


def check_main_imports(file_path: Path) -> List[Tuple[str, int, str]]:
    """Verifica se main.py tem os imports esperados."""
    issues = []
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        issues.append(("ERROR", 0, f"Não foi possível ler arquivo: {e}"))
        return issues
    
    for expected_import in MAIN_EXPECTED_IMPORTS:
        if expected_import not in content:
            issues.append((
                "MISSING_IMPORT",
                0,
                f"Import esperado não encontrado: {expected_import}"
            ))
    
    return issues


def main():
    """Executa verificação de imports."""
    print("=" * 70)
    print("VERIFICAÇÃO DE IMPORTS - MODULARIZAÇÃO")
    print("=" * 70)
    print()
    
    all_issues = []
    total_files = 0
    
    # Verificar diretórios
    for check_dir in CHECK_DIRS:
        print(f"Verificando: {check_dir}")
        files = find_python_files(check_dir)
        total_files += len(files)
        
        for file_path in files:
            # Verificação especial para main.py
            if file_path.name == "main.py":
                issues = check_main_imports(file_path)
            else:
                issues = check_file(file_path)
            
            if issues:
                all_issues.append((file_path, issues))
                print(f"  [WARN] {file_path}: {len(issues)} problema(s) encontrado(s)")
            else:
                print(f"  [OK] {file_path}: OK")
    
    print()
    print("=" * 70)
    print("RESUMO")
    print("=" * 70)
    print(f"Arquivos verificados: {total_files}")
    print(f"Arquivos com problemas: {len(all_issues)}")
    print()
    
    if all_issues:
        print("PROBLEMAS ENCONTRADOS:")
        print("-" * 70)
        for file_path, issues in all_issues:
            print(f"\n[FILE] {file_path}")
            for issue_type, line_num, message in issues:
                print(f"  [{issue_type}] Linha {line_num}: {message}")
        
        print()
        print("=" * 70)
        print("[FAIL] VERIFICAÇÃO FALHOU - Corrigir problemas acima")
        print("=" * 70)
        return 1
    else:
        print("=" * 70)
        print("[PASS] TODAS AS VERIFICAÇÕES PASSARAM")
        print("=" * 70)
        return 0


if __name__ == "__main__":
    exit(main())
