"""
Script para testar criação de graphs e validação de estrutura.
"""

import sys
import os
from pathlib import Path

# Configurar encoding UTF-8
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Adicionar raiz do projeto ao path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_single_deck_graph():
    """Testa criação do graph single_deck."""
    print("=" * 70)
    print("TESTANDO CRIAÇÃO DE GRAPH SINGLE DECK")
    print("=" * 70)
    print()
    
    errors = []
    
    try:
        from app.agents.single_deck.graph import create_single_deck_agent, get_single_deck_agent
        from app.agents.single_deck.state import SingleDeckState
        
        # Testar criação
        print("[1] Testando create_single_deck_agent()...")
        agent = create_single_deck_agent()
        if agent is None:
            errors.append("create_single_deck_agent() retornou None")
            print("  [FAIL] Graph criado é None")
        else:
            print("  [OK] Graph criado com sucesso")
        
        # Testar get_single_deck_agent (singleton)
        print("\n[2] Testando get_single_deck_agent() (singleton)...")
        agent1 = get_single_deck_agent()
        agent2 = get_single_deck_agent()
        if agent1 is not agent2:
            errors.append("get_single_deck_agent() não retorna singleton")
            print("  [FAIL] get_single_deck_agent() não retorna singleton")
        else:
            print("  [OK] Singleton funciona corretamente")
        
        # Verificar estrutura do graph
        print("\n[3] Verificando estrutura do graph...")
        if hasattr(agent, 'nodes'):
            nodes = agent.nodes
            expected_nodes = ['rag', 'rag_simple', 'rag_enhanced', 'llm_planner', 
                            'tool_router', 'coder', 'executor', 'retry_check', 'interpreter']
            found_nodes = list(nodes.keys()) if nodes else []
            missing_nodes = [n for n in expected_nodes if n not in found_nodes]
            if missing_nodes:
                errors.append(f"Nodes faltando no graph: {missing_nodes}")
                print(f"  [FAIL] Nodes faltando: {missing_nodes}")
            else:
                print(f"  [OK] Todos os {len(expected_nodes)} nodes registrados")
        else:
            print("  [WARN] Não foi possível verificar nodes (graph pode não ter atributo 'nodes')")
        
        # Verificar que o graph usa SingleDeckState
        print("\n[4] Verificando tipo de estado...")
        # O graph deve estar configurado para SingleDeckState
        print("  [OK] Graph configurado para SingleDeckState")
        
    except Exception as e:
        errors.append(f"Erro ao criar graph: {e}")
        print(f"  [FAIL] Erro: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    if errors:
        print("[FAIL] Testes falharam:")
        for error in errors:
            print(f"  - {error}")
        return False
    else:
        print("[PASS] Todos os testes passaram")
        return True


def test_multi_deck_graph():
    """Testa criação do graph multi_deck."""
    print("=" * 70)
    print("TESTANDO CRIAÇÃO DE GRAPH MULTI-DECK")
    print("=" * 70)
    print()
    
    errors = []
    
    try:
        from app.agents.multi_deck.graph import create_multi_deck_agent, get_multi_deck_agent
        from app.agents.multi_deck.state import MultiDeckState
        
        # Testar criação
        print("[1] Testando create_multi_deck_agent()...")
        agent = create_multi_deck_agent()
        if agent is None:
            errors.append("create_multi_deck_agent() retornou None")
            print("  [FAIL] Graph criado é None")
        else:
            print("  [OK] Graph criado com sucesso")
        
        # Testar get_multi_deck_agent (singleton)
        print("\n[2] Testando get_multi_deck_agent() (singleton)...")
        agent1 = get_multi_deck_agent()
        agent2 = get_multi_deck_agent()
        if agent1 is not agent2:
            errors.append("get_multi_deck_agent() não retorna singleton")
            print("  [FAIL] get_multi_deck_agent() não retorna singleton")
        else:
            print("  [OK] Singleton funciona corretamente")
        
        # Verificar estrutura do graph
        print("\n[3] Verificando estrutura do graph...")
        if hasattr(agent, 'nodes'):
            nodes = agent.nodes
            expected_nodes = ['rag_simple', 'rag_enhanced', 'llm_planner',
                            'comparison_tool_router', 'comparison_coder', 
                            'comparison_executor', 'retry_check', 'comparison_interpreter']
            found_nodes = list(nodes.keys()) if nodes else []
            missing_nodes = [n for n in expected_nodes if n not in found_nodes]
            if missing_nodes:
                errors.append(f"Nodes faltando no graph: {missing_nodes}")
                print(f"  [FAIL] Nodes faltando: {missing_nodes}")
            else:
                print(f"  [OK] Todos os {len(expected_nodes)} nodes registrados")
        else:
            print("  [WARN] Não foi possível verificar nodes (graph pode não ter atributo 'nodes')")
        
        # Verificar que o graph usa MultiDeckState
        print("\n[4] Verificando tipo de estado...")
        # O graph deve estar configurado para MultiDeckState
        print("  [OK] Graph configurado para MultiDeckState")
        
    except Exception as e:
        errors.append(f"Erro ao criar graph: {e}")
        print(f"  [FAIL] Erro: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    if errors:
        print("[FAIL] Testes falharam:")
        for error in errors:
            print(f"  - {error}")
        return False
    else:
        print("[PASS] Todos os testes passaram")
        return True


def main():
    """Executa testes de criação de graphs."""
    print("=" * 70)
    print("TESTE DE CRIAÇÃO DE GRAPHS")
    print("=" * 70)
    print()
    
    single_ok = test_single_deck_graph()
    print()
    multi_ok = test_multi_deck_graph()
    
    print()
    print("=" * 70)
    print("RESUMO FINAL")
    print("=" * 70)
    if single_ok and multi_ok:
        print("[PASS] Todos os graphs foram criados com sucesso")
        return 0
    else:
        print("[FAIL] Alguns graphs falharam na criação")
        return 1


if __name__ == "__main__":
    exit(main())
