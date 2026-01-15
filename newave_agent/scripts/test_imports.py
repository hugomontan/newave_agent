"""
Script para testar importação de todos os módulos single_deck e multi_deck.
"""

import sys
from pathlib import Path

# Adicionar raiz do projeto ao path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_single_deck_imports():
    """Testa importação de todos os módulos single_deck."""
    print("[TEST] Testando imports do Single Deck...")
    errors = []
    
    try:
        from app.agents.single_deck.state import SingleDeckState
        print("  [OK] SingleDeckState")
    except Exception as e:
        errors.append(f"SingleDeckState: {e}")
        print(f"  [FAIL] SingleDeckState: {e}")
    
    try:
        from app.agents.single_deck.graph import (
            create_single_deck_agent,
            get_single_deck_agent,
            run_query,
            run_query_stream,
        )
        print("  [OK] graph (create_single_deck_agent, get_single_deck_agent, run_query, run_query_stream)")
    except Exception as e:
        errors.append(f"graph: {e}")
        print(f"  [FAIL] graph: {e}")
    
    try:
        from app.agents.single_deck.tools import get_available_tools
        print("  [OK] tools.get_available_tools")
    except Exception as e:
        errors.append(f"tools: {e}")
        print(f"  [FAIL] tools: {e}")
    
    try:
        from app.agents.single_deck.formatters.registry import get_formatter_for_tool
        from app.agents.single_deck.formatters.base import SingleDeckFormatter
        from app.agents.single_deck.formatters.generic_formatter import GenericSingleDeckFormatter
        from app.agents.single_deck.formatters.data_formatters.clast_formatter import ClastSingleDeckFormatter
        from app.agents.single_deck.formatters.data_formatters.carga_mensal_formatter import CargaMensalSingleDeckFormatter
        print("  [OK] formatters (registry, base, generic, clast, carga)")
    except Exception as e:
        errors.append(f"formatters: {e}")
        print(f"  [FAIL] formatters: {e}")
    
    try:
        from app.agents.single_deck.nodes import (
            tool_router_node,
            coder_node,
            executor_node,
            interpreter_node,
            rag_retriever_node,
            rag_simple_node,
            rag_enhanced_node,
            llm_planner_node,
        )
        print("  [OK] nodes (tool_router, coder, executor, interpreter, rag, llm)")
    except Exception as e:
        errors.append(f"nodes: {e}")
        print(f"  [FAIL] nodes: {e}")
    
    try:
        from app.agents.single_deck.agent import SingleDeckAgent
        print("  [OK] agent.SingleDeckAgent")
    except Exception as e:
        errors.append(f"agent: {e}")
        print(f"  [FAIL] agent: {e}")
    
    return errors


def test_multi_deck_imports():
    """Testa importação de todos os módulos multi_deck."""
    print("\n[TEST] Testando imports do Multi-Deck...")
    errors = []
    
    try:
        from app.agents.multi_deck.state import MultiDeckState
        print("  [OK] MultiDeckState")
    except Exception as e:
        errors.append(f"MultiDeckState: {e}")
        print(f"  [FAIL] MultiDeckState: {e}")
    
    try:
        from app.agents.multi_deck.graph import (
            create_multi_deck_agent,
            get_multi_deck_agent,
            run_query,
            run_query_stream,
        )
        print("  [OK] graph (create_multi_deck_agent, get_multi_deck_agent, run_query, run_query_stream)")
    except Exception as e:
        errors.append(f"graph: {e}")
        print(f"  [FAIL] graph: {e}")
    
    try:
        from app.agents.multi_deck.tools import get_available_tools
        print("  [OK] tools.get_available_tools")
    except Exception as e:
        errors.append(f"tools: {e}")
        print(f"  [FAIL] tools: {e}")
    
    try:
        from app.agents.multi_deck.formatters.registry import get_formatter_for_tool
        from app.agents.multi_deck.formatters.base import ComparisonFormatter
        print("  [OK] formatters (registry, base)")
    except Exception as e:
        errors.append(f"formatters: {e}")
        print(f"  [FAIL] formatters: {e}")
    
    try:
        from app.agents.multi_deck.nodes import (
            comparison_tool_router_node,
            comparison_coder_node,
            comparison_executor_node,
            comparison_interpreter_node,
            rag_retriever_node,
            rag_simple_node,
            rag_enhanced_node,
            llm_planner_node,
        )
        print("  [OK] nodes (comparison_tool_router, comparison_coder, comparison_executor, comparison_interpreter, rag, llm)")
    except Exception as e:
        errors.append(f"nodes: {e}")
        print(f"  [FAIL] nodes: {e}")
    
    try:
        from app.agents.multi_deck.agent import MultiDeckAgent
        print("  [OK] agent.MultiDeckAgent")
    except Exception as e:
        errors.append(f"agent: {e}")
        print(f"  [FAIL] agent: {e}")
    
    return errors


def test_main_imports():
    """Testa imports do main.py."""
    print("\n[TEST] Testando imports do main.py...")
    errors = []
    
    try:
        # Verificar se main.py pode ser importado (sem executar)
        import importlib.util
        main_path = project_root / "app" / "main.py"
        spec = importlib.util.spec_from_file_location("main", main_path)
        if spec is None or spec.loader is None:
            errors.append("Não foi possível carregar main.py")
            print("  [FAIL] Não foi possível carregar main.py")
        else:
            # Verificar conteúdo do arquivo
            with open(main_path, "r", encoding="utf-8") as f:
                content = f.read()
                if "from app.agents.single_deck.graph import" in content:
                    print("  [OK] Import single_deck.graph encontrado")
                else:
                    errors.append("Import single_deck.graph não encontrado")
                    print("  [FAIL] Import single_deck.graph não encontrado")
                
                if "from app.agents.multi_deck.graph import" in content:
                    print("  [OK] Import multi_deck.graph encontrado")
                else:
                    errors.append("Import multi_deck.graph não encontrado")
                    print("  [FAIL] Import multi_deck.graph não encontrado")
    except Exception as e:
        errors.append(f"Erro ao verificar main.py: {e}")
        print(f"  [FAIL] Erro: {e}")
    
    return errors


def check_circular_imports():
    """Verifica se há imports circulares (básico)."""
    print("\n[TEST] Verificando imports circulares...")
    # Esta é uma verificação básica - imports circulares reais precisariam de análise mais profunda
    print("  [WARN] Verificação básica - imports circulares reais requerem análise mais profunda")
    return []


def main():
    """Executa todos os testes de importação."""
    print("=" * 70)
    print("TESTE DE IMPORTAÇÃO DE MÓDULOS")
    print("=" * 70)
    print()
    
    all_errors = []
    
    # Testar imports single_deck
    errors = test_single_deck_imports()
    all_errors.extend([("single_deck", e) for e in errors])
    
    # Testar imports multi_deck
    errors = test_multi_deck_imports()
    all_errors.extend([("multi_deck", e) for e in errors])
    
    # Testar imports main.py
    errors = test_main_imports()
    all_errors.extend([("main", e) for e in errors])
    
    # Verificar imports circulares
    check_circular_imports()
    
    print()
    print("=" * 70)
    print("RESUMO")
    print("=" * 70)
    
    if all_errors:
        print(f"[FAIL] {len(all_errors)} erro(s) encontrado(s):")
        for module, error in all_errors:
            print(f"  [{module}] {error}")
        print()
        print("=" * 70)
        print("[FAIL] TESTE FALHOU")
        print("=" * 70)
        return 1
    else:
        print("[PASS] TODOS OS IMPORTS FUNCIONARAM CORRETAMENTE")
        print()
        print("=" * 70)
        print("[PASS] TESTE PASSOU")
        print("=" * 70)
        return 0


if __name__ == "__main__":
    exit(main())
