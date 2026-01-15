"""
Script para testar componentes individuais (tools, formatters, nodes).
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


def test_tools():
    """Testa tools em ambos os módulos."""
    print("=" * 70)
    print("TESTANDO TOOLS")
    print("=" * 70)
    print()
    
    errors = []
    
    # Single Deck Tools
    print("[1] Testando Single Deck Tools...")
    try:
        from app.agents.single_deck.tools import get_available_tools
        tools = get_available_tools("/fake/path")
        
        if not tools:
            errors.append("Single deck: get_available_tools retornou lista vazia")
            print("  [FAIL] Lista vazia")
        else:
            print(f"  [OK] {len(tools)} tools carregadas")
            
            # Verificar que cada tool pode ser instanciada
            tool_names = []
            for tool in tools:
                try:
                    name = tool.get_name()
                    tool_names.append(name)
                except Exception as e:
                    errors.append(f"Erro ao obter nome da tool {tool.__class__.__name__}: {e}")
            
            # Verificar que não tem tools de comparação
            comparison_tools = ['MultiDeckComparisonTool', 'MudancasGeracoesTermicasTool']
            found_comparison = [t for t in comparison_tools if t in tool_names]
            if found_comparison:
                errors.append(f"Single deck tem tools de comparação: {found_comparison}")
                print(f"  [FAIL] Tools de comparação encontradas: {found_comparison}")
            else:
                print("  [OK] Nenhuma tool de comparação (correto)")
    except Exception as e:
        errors.append(f"Single deck tools: {e}")
        print(f"  [FAIL] Erro: {e}")
    
    # Multi-Deck Tools
    print("\n[2] Testando Multi-Deck Tools...")
    try:
        from app.agents.multi_deck.tools import get_available_tools
        tools = get_available_tools("/fake/path")
        
        if not tools:
            errors.append("Multi deck: get_available_tools retornou lista vazia")
            print("  [FAIL] Lista vazia")
        else:
            print(f"  [OK] {len(tools)} tools carregadas")
            
            # Verificar que cada tool pode ser instanciada
            tool_names = []
            for tool in tools:
                try:
                    name = tool.get_name()
                    tool_names.append(name)
                except Exception as e:
                    errors.append(f"Erro ao obter nome da tool {tool.__class__.__name__}: {e}")
            
            # Verificar que tem tools de comparação
            comparison_tools = ['MultiDeckComparisonTool', 'MudancasGeracoesTermicasTool']
            found_comparison = [t for t in comparison_tools if t in tool_names]
            if not found_comparison:
                errors.append("Multi deck não tem tools de comparação")
                print("  [FAIL] Tools de comparação não encontradas")
            else:
                print(f"  [OK] Tools de comparação encontradas: {found_comparison}")
    except Exception as e:
        errors.append(f"Multi deck tools: {e}")
        print(f"  [FAIL] Erro: {e}")
    
    print()
    if errors:
        print("[FAIL] Testes de tools falharam:")
        for error in errors:
            print(f"  - {error}")
        return False
    else:
        print("[PASS] Todos os testes de tools passaram")
        return True


def test_formatters():
    """Testa formatters em ambos os módulos."""
    print("=" * 70)
    print("TESTANDO FORMATTERS")
    print("=" * 70)
    print()
    
    errors = []
    
    # Single Deck Formatters
    print("[1] Testando Single Deck Formatters...")
    try:
        from app.agents.single_deck.formatters.registry import get_formatter_for_tool
        from app.agents.single_deck.formatters.base import SingleDeckFormatter
        from app.agents.single_deck.formatters.generic_formatter import GenericSingleDeckFormatter
        from app.agents.single_deck.formatters.data_formatters.clast_formatter import ClastSingleDeckFormatter
        from app.agents.single_deck.formatters.data_formatters.carga_mensal_formatter import CargaMensalSingleDeckFormatter
        
        # Testar com ClastValoresTool
        from app.tools.clast_valores_tool import ClastValoresTool
        tool = ClastValoresTool("/fake/path")
        formatter = get_formatter_for_tool(tool, {})
        
        if not isinstance(formatter, SingleDeckFormatter):
            errors.append("Formatter retornado não é SingleDeckFormatter")
            print("  [FAIL] Formatter não é SingleDeckFormatter")
        else:
            print("  [OK] Registry retorna SingleDeckFormatter")
        
        # Verificar formatters específicos
        if isinstance(formatter, ClastSingleDeckFormatter):
            print("  [OK] ClastSingleDeckFormatter retornado para ClastValoresTool")
        elif isinstance(formatter, GenericSingleDeckFormatter):
            print("  [WARN] GenericSingleDeckFormatter retornado (esperado ClastSingleDeckFormatter)")
        else:
            print(f"  [WARN] Formatter inesperado: {formatter.__class__.__name__}")
        
        # Testar com CargaMensalTool
        from app.tools.carga_mensal_tool import CargaMensalTool
        tool2 = CargaMensalTool("/fake/path")
        formatter2 = get_formatter_for_tool(tool2, {})
        if isinstance(formatter2, CargaMensalSingleDeckFormatter):
            print("  [OK] CargaMensalSingleDeckFormatter retornado para CargaMensalTool")
        else:
            print(f"  [WARN] Formatter inesperado para CargaMensalTool: {formatter2.__class__.__name__}")
        
    except Exception as e:
        errors.append(f"Single deck formatters: {e}")
        print(f"  [FAIL] Erro: {e}")
        import traceback
        traceback.print_exc()
    
    # Multi-Deck Formatters
    print("\n[2] Testando Multi-Deck Formatters...")
    try:
        from app.agents.multi_deck.formatters.registry import get_formatter_for_tool
        from app.agents.multi_deck.formatters.base import ComparisonFormatter
        from app.agents.multi_deck.formatters.formatters.llm_free_formatters import LLMFreeFormatter
        from app.agents.multi_deck.formatters.formatters.temporal_formatters import ClastComparisonFormatter
        
        # Testar com ClastValoresTool
        fake_result = {"dados_estruturais": {}}
        formatter = get_formatter_for_tool("ClastValoresTool", fake_result)
        
        if not isinstance(formatter, ComparisonFormatter):
            errors.append("Formatter retornado não é ComparisonFormatter")
            print("  [FAIL] Formatter não é ComparisonFormatter")
        else:
            print("  [OK] Registry retorna ComparisonFormatter")
        
        # Verificar formatters específicos
        if isinstance(formatter, ClastComparisonFormatter):
            print("  [OK] ClastComparisonFormatter retornado para ClastValoresTool")
        elif isinstance(formatter, LLMFreeFormatter):
            print("  [WARN] LLMFreeFormatter retornado (fallback)")
        else:
            print(f"  [INFO] Formatter retornado: {formatter.__class__.__name__}")
        
        # Testar fallback
        formatter_fallback = get_formatter_for_tool("UnknownTool", {})
        if isinstance(formatter_fallback, LLMFreeFormatter):
            print("  [OK] Fallback LLMFreeFormatter funciona")
        else:
            print(f"  [WARN] Fallback inesperado: {formatter_fallback.__class__.__name__}")
        
    except Exception as e:
        errors.append(f"Multi deck formatters: {e}")
        print(f"  [FAIL] Erro: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    if errors:
        print("[FAIL] Testes de formatters falharam:")
        for error in errors:
            print(f"  - {error}")
        return False
    else:
        print("[PASS] Todos os testes de formatters passaram")
        return True


def test_nodes():
    """Testa nodes em ambos os módulos."""
    print("=" * 70)
    print("TESTANDO NODES")
    print("=" * 70)
    print()
    
    errors = []
    
    # Single Deck Nodes
    print("[1] Testando Single Deck Nodes...")
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
        from app.agents.single_deck.state import SingleDeckState
        
        nodes = [
            ("tool_router_node", tool_router_node),
            ("coder_node", coder_node),
            ("executor_node", executor_node),
            ("interpreter_node", interpreter_node),
            ("rag_retriever_node", rag_retriever_node),
            ("rag_simple_node", rag_simple_node),
            ("rag_enhanced_node", rag_enhanced_node),
            ("llm_planner_node", llm_planner_node),
        ]
        
        for name, node in nodes:
            if not callable(node):
                errors.append(f"{name} não é callable")
                print(f"  [FAIL] {name} não é callable")
            else:
                print(f"  [OK] {name} é callable")
        
        # Verificar que tool_router não tem lógica de comparação
        print("\n[2] Verificando que tool_router não tem lógica de comparação...")
        import inspect
        tool_router_source = inspect.getsource(tool_router_node)
        if "comparison" in tool_router_source.lower() or "deck_december" in tool_router_source.lower():
            errors.append("tool_router_node contém lógica de comparação")
            print("  [FAIL] tool_router_node contém lógica de comparação")
        else:
            print("  [OK] tool_router_node não tem lógica de comparação")
        
    except Exception as e:
        errors.append(f"Single deck nodes: {e}")
        print(f"  [FAIL] Erro: {e}")
        import traceback
        traceback.print_exc()
    
    # Multi-Deck Nodes
    print("\n[3] Testando Multi-Deck Nodes...")
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
        from app.agents.multi_deck.state import MultiDeckState
        
        nodes = [
            ("comparison_tool_router_node", comparison_tool_router_node),
            ("comparison_coder_node", comparison_coder_node),
            ("comparison_executor_node", comparison_executor_node),
            ("comparison_interpreter_node", comparison_interpreter_node),
            ("rag_retriever_node", rag_retriever_node),
            ("rag_simple_node", rag_simple_node),
            ("rag_enhanced_node", rag_enhanced_node),
            ("llm_planner_node", llm_planner_node),
        ]
        
        for name, node in nodes:
            if not callable(node):
                errors.append(f"{name} não é callable")
                print(f"  [FAIL] {name} não é callable")
            else:
                print(f"  [OK] {name} é callable")
        
        # Verificar que comparison_tool_router executa em ambos os decks
        print("\n[4] Verificando que comparison_tool_router executa em ambos os decks...")
        import inspect
        comparison_router_source = inspect.getsource(comparison_tool_router_node)
        if "deck_december_path" in comparison_router_source and "deck_january_path" in comparison_router_source:
            print("  [OK] comparison_tool_router_node usa ambos os decks")
        else:
            errors.append("comparison_tool_router_node não usa ambos os decks")
            print("  [FAIL] comparison_tool_router_node não usa ambos os decks")
        
    except Exception as e:
        errors.append(f"Multi deck nodes: {e}")
        print(f"  [FAIL] Erro: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    if errors:
        print("[FAIL] Testes de nodes falharam:")
        for error in errors:
            print(f"  - {error}")
        return False
    else:
        print("[PASS] Todos os testes de nodes passaram")
        return True


def main():
    """Executa testes de componentes."""
    print("=" * 70)
    print("TESTE DE COMPONENTES INDIVIDUAIS")
    print("=" * 70)
    print()
    
    tools_ok = test_tools()
    print()
    formatters_ok = test_formatters()
    print()
    nodes_ok = test_nodes()
    
    print()
    print("=" * 70)
    print("RESUMO FINAL")
    print("=" * 70)
    if tools_ok and formatters_ok and nodes_ok:
        print("[PASS] Todos os componentes funcionam corretamente")
        return 0
    else:
        print("[FAIL] Alguns componentes falharam")
        return 1


if __name__ == "__main__":
    exit(main())
