"""
Script para executar todos os testes de debug da modularização.
"""

import sys
import os
import subprocess
from pathlib import Path

# Configurar encoding UTF-8
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Adicionar raiz do projeto ao path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)


def run_script(script_name):
    """Executa um script de teste e retorna o resultado."""
    script_path = project_root / "scripts" / script_name
    if not script_path.exists():
        return False, f"Script não encontrado: {script_name}"
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        return result.returncode == 0, result.stdout + result.stderr
    except Exception as e:
        return False, f"Erro ao executar script: {e}"


def main():
    """Executa todos os testes."""
    print("=" * 70)
    print("EXECUTANDO TODOS OS TESTES DE MODULARIZAÇÃO")
    print("=" * 70)
    print()
    
    tests = [
        ("check_imports.py", "Verificação de Imports"),
        ("test_imports.py", "Teste de Importação de Módulos"),
        ("test_structure.py", "Validação de Estrutura"),
        ("test_graph_creation.py", "Teste de Criação de Graphs"),
        ("test_state_init.py", "Teste de Inicialização de Estado"),
        ("test_components.py", "Teste de Componentes Individuais"),
        ("test_modularization.py", "Teste Rápido de Modularização"),
        ("test_integration.py", "Validação de Fluxos de Integração"),
    ]
    
    results = []
    
    for script, description in tests:
        print(f"\n{'=' * 70}")
        print(f"Executando: {description} ({script})")
        print("=" * 70)
        success, output = run_script(script)
        results.append((script, description, success))
        
        if success:
            print(f"[PASS] {description}")
        else:
            print(f"[FAIL] {description}")
            print("\nOutput:")
            print(output[:500])  # Mostrar primeiros 500 caracteres
            if len(output) > 500:
                print("... (output truncado)")
    
    print()
    print("=" * 70)
    print("RESUMO FINAL")
    print("=" * 70)
    print()
    
    passed = sum(1 for _, _, success in results if success)
    total = len(results)
    
    for script, description, success in results:
        status = "[PASS]" if success else "[FAIL]"
        print(f"{status} {description}")
    
    print()
    print("=" * 70)
    if passed == total:
        print(f"[PASS] TODOS OS {total} TESTES PASSARAM")
        print("=" * 70)
        return 0
    else:
        print(f"[FAIL] {passed}/{total} TESTES PASSARAM")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    exit(main())
