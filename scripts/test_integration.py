"""
Script para testar fluxos de integração (validação de estrutura dos fluxos).
Nota: Testes completos end-to-end requerem decks reais e são mais demorados.
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


def validate_single_deck_tool_flow():
    """Valida estrutura do fluxo Single Deck - Tool Route."""
    print("=" * 70)
    print("VALIDANDO FLUXO SINGLE DECK - TOOL ROUTE")
    print("=" * 70)
    print()
    
    errors = []
    
    try:
        from app.agents.single_deck.graph import create_single_deck_agent
        from app.agents.single_deck.nodes import tool_router_node, interpreter_node
        from app.agents.single_deck.formatters.registry import get_formatter_for_tool
        
        agent = create_single_deck_agent()
        
        # Verificar que tool_router_node existe no graph
        if hasattr(agent, 'nodes') and 'tool_router' in agent.nodes:
            print("  [OK] tool_router_node registrado no graph")
        else:
            errors.append("tool_router_node não encontrado no graph")
            print("  [FAIL] tool_router_node não encontrado")
        
        # Verificar que interpreter_node existe no graph
        if hasattr(agent, 'nodes') and 'interpreter' in agent.nodes:
            print("  [OK] interpreter_node registrado no graph")
        else:
            errors.append("interpreter_node não encontrado no graph")
            print("  [FAIL] interpreter_node não encontrado")
        
        # Verificar que tool_router não tem lógica de comparação
        import inspect
        tool_router_source = inspect.getsource(tool_router_node)
        if "deck_december" in tool_router_source.lower() or "deck_january" in tool_router_source.lower():
            errors.append("tool_router_node contém lógica de comparação")
            print("  [FAIL] tool_router_node contém lógica de comparação")
        else:
            print("  [OK] tool_router_node não tem lógica de comparação")
        
        # Verificar que formatters registry funciona
        from app.tools.clast_valores_tool import ClastValoresTool
        tool = ClastValoresTool("/fake/path")
        formatter = get_formatter_for_tool(tool, {})
        if formatter:
            print("  [OK] Formatters registry funciona")
        else:
            errors.append("Formatters registry não funciona")
            print("  [FAIL] Formatters registry não funciona")
        
    except Exception as e:
        errors.append(f"Erro: {e}")
        print(f"  [FAIL] Erro: {e}")
        import traceback
        traceback.print_exc()
    
    return errors


def validate_single_deck_code_flow():
    """Valida estrutura do fluxo Single Deck - Code Route."""
    print("=" * 70)
    print("VALIDANDO FLUXO SINGLE DECK - CODE ROUTE")
    print("=" * 70)
    print()
    
    errors = []
    
    try:
        from app.agents.single_deck.graph import create_single_deck_agent
        from app.agents.single_deck.nodes import rag_simple_node, coder_node, executor_node, interpreter_node
        
        agent = create_single_deck_agent()
        
        # Verificar que nodes existem no graph
        required_nodes = ['rag_simple', 'coder', 'executor', 'interpreter']
        if hasattr(agent, 'nodes'):
            found_nodes = [n for n in required_nodes if n in agent.nodes]
            missing_nodes = [n for n in required_nodes if n not in agent.nodes]
            if missing_nodes:
                errors.append(f"Nodes faltando: {missing_nodes}")
                print(f"  [FAIL] Nodes faltando: {missing_nodes}")
            else:
                print(f"  [OK] Todos os {len(required_nodes)} nodes registrados")
        else:
            print("  [WARN] Não foi possível verificar nodes")
        
        # Verificar que nodes são callable
        nodes_to_check = [rag_simple_node, coder_node, executor_node, interpreter_node]
        for node in nodes_to_check:
            if not callable(node):
                errors.append(f"Node {node.__name__} não é callable")
                print(f"  [FAIL] {node.__name__} não é callable")
        
        if not errors:
            print("  [OK] Todos os nodes são callable")
        
    except Exception as e:
        errors.append(f"Erro: {e}")
        print(f"  [FAIL] Erro: {e}")
        import traceback
        traceback.print_exc()
    
    return errors


def validate_multi_deck_tool_flow():
    """Valida estrutura do fluxo Multi-Deck - Tool Route."""
    print("=" * 70)
    print("VALIDANDO FLUXO MULTI-DECK - TOOL ROUTE")
    print("=" * 70)
    print()
    
    errors = []
    
    try:
        from app.agents.multi_deck.graph import create_multi_deck_agent
        from app.agents.multi_deck.nodes import comparison_tool_router_node, comparison_interpreter_node
        from app.agents.multi_deck.formatters.registry import get_formatter_for_tool
        
        agent = create_multi_deck_agent()
        
        # Verificar que comparison_tool_router_node existe no graph
        if hasattr(agent, 'nodes') and 'comparison_tool_router' in agent.nodes:
            print("  [OK] comparison_tool_router_node registrado no graph")
        else:
            errors.append("comparison_tool_router_node não encontrado no graph")
            print("  [FAIL] comparison_tool_router_node não encontrado")
        
        # Verificar que comparison_interpreter_node existe no graph
        if hasattr(agent, 'nodes') and 'comparison_interpreter' in agent.nodes:
            print("  [OK] comparison_interpreter_node registrado no graph")
        else:
            errors.append("comparison_interpreter_node não encontrado no graph")
            print("  [FAIL] comparison_interpreter_node não encontrado")
        
        # Verificar que comparison_tool_router executa em ambos os decks
        import inspect
        router_source = inspect.getsource(comparison_tool_router_node)
        if "deck_december_path" in router_source and "deck_january_path" in router_source:
            print("  [OK] comparison_tool_router_node usa ambos os decks")
        else:
            errors.append("comparison_tool_router_node não usa ambos os decks")
            print("  [FAIL] comparison_tool_router_node não usa ambos os decks")
        
        # Verificar que formatters registry funciona
        fake_result = {"dados_estruturais": {}}
        formatter = get_formatter_for_tool("ClastValoresTool", fake_result)
        if formatter:
            print("  [OK] Formatters registry funciona")
        else:
            errors.append("Formatters registry não funciona")
            print("  [FAIL] Formatters registry não funciona")
        
    except Exception as e:
        errors.append(f"Erro: {e}")
        print(f"  [FAIL] Erro: {e}")
        import traceback
        traceback.print_exc()
    
    return errors


def validate_multi_deck_code_flow():
    """Valida estrutura do fluxo Multi-Deck - Code Route."""
    print("=" * 70)
    print("VALIDANDO FLUXO MULTI-DECK - CODE ROUTE")
    print("=" * 70)
    print()
    
    errors = []
    
    try:
        from app.agents.multi_deck.graph import create_multi_deck_agent
        from app.agents.multi_deck.nodes import rag_simple_node, comparison_coder_node, comparison_executor_node, comparison_interpreter_node
        
        agent = create_multi_deck_agent()
        
        # Verificar que nodes existem no graph
        required_nodes = ['rag_simple', 'comparison_coder', 'comparison_executor', 'comparison_interpreter']
        if hasattr(agent, 'nodes'):
            found_nodes = [n for n in required_nodes if n in agent.nodes]
            missing_nodes = [n for n in required_nodes if n not in agent.nodes]
            if missing_nodes:
                errors.append(f"Nodes faltando: {missing_nodes}")
                print(f"  [FAIL] Nodes faltando: {missing_nodes}")
            else:
                print(f"  [OK] Todos os {len(required_nodes)} nodes registrados")
        else:
            print("  [WARN] Não foi possível verificar nodes")
        
        # Verificar que comparison_coder gera código para ambos os decks
        import inspect
        coder_source = inspect.getsource(comparison_coder_node)
        if "deck_december" in coder_source.lower() and "deck_january" in coder_source.lower():
            print("  [OK] comparison_coder_node gera código para ambos os decks")
        else:
            errors.append("comparison_coder_node não gera código para ambos os decks")
            print("  [FAIL] comparison_coder_node não gera código para ambos os decks")
        
        # Verificar que nodes são callable
        nodes_to_check = [rag_simple_node, comparison_coder_node, comparison_executor_node, comparison_interpreter_node]
        for node in nodes_to_check:
            if not callable(node):
                errors.append(f"Node {node.__name__} não é callable")
                print(f"  [FAIL] {node.__name__} não é callable")
        
        if not errors:
            print("  [OK] Todos os nodes são callable")
        
    except Exception as e:
        errors.append(f"Erro: {e}")
        print(f"  [FAIL] Erro: {e}")
        import traceback
        traceback.print_exc()
    
    return errors


def main():
    """Executa validação de fluxos de integração."""
    print("=" * 70)
    print("VALIDAÇÃO DE FLUXOS DE INTEGRAÇÃO")
    print("=" * 70)
    print()
    
    all_errors = []
    
    # Single Deck - Tool Route
    errors = validate_single_deck_tool_flow()
    all_errors.extend([("single_tool_flow", e) for e in errors])
    print()
    
    # Single Deck - Code Route
    errors = validate_single_deck_code_flow()
    all_errors.extend([("single_code_flow", e) for e in errors])
    print()
    
    # Multi-Deck - Tool Route
    errors = validate_multi_deck_tool_flow()
    all_errors.extend([("multi_tool_flow", e) for e in errors])
    print()
    
    # Multi-Deck - Code Route
    errors = validate_multi_deck_code_flow()
    all_errors.extend([("multi_code_flow", e) for e in errors])
    
    print()
    print("=" * 70)
    print("RESUMO FINAL")
    print("=" * 70)
    
    if all_errors:
        print(f"[FAIL] {len(all_errors)} erro(s) encontrado(s):")
        for category, error in all_errors:
            print(f"  [{category}] {error}")
        print()
        print("=" * 70)
        print("[FAIL] VALIDAÇÃO FALHOU")
        print("=" * 70)
        return 1
    else:
        print("[PASS] Todos os fluxos foram validados com sucesso")
        print()
        print("=" * 70)
        print("[PASS] VALIDAÇÃO PASSOU")
        print("=" * 70)
        return 0


if __name__ == "__main__":
    exit(main())
