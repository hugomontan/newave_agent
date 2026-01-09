"""
Script de teste rápido para validar modularização.
Combina testes básicos de imports, estrutura e componentes.
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


def test_imports():
    """Testa se todos os imports funcionam."""
    print("=" * 70)
    print("TESTE DE IMPORTS")
    print("=" * 70)
    print()
    
    errors = []
    
    # Single Deck
    print("[TEST] Testando imports do Single Deck...")
    try:
        from app.agents.single_deck.state import SingleDeckState
        from app.agents.single_deck.graph import create_single_deck_agent
        from app.agents.single_deck.tools import get_available_tools
        from app.agents.single_deck.formatters.registry import get_formatter_for_tool
        from app.agents.single_deck.nodes import tool_router_node, coder_node, executor_node, interpreter_node
        print("  [OK] Single Deck imports OK")
    except Exception as e:
        errors.append(f"Single Deck: {e}")
        print(f"  [FAIL] Single Deck imports falharam: {e}")
    
    # Multi-Deck
    print("\n[TEST] Testando imports do Multi-Deck...")
    try:
        from app.agents.multi_deck.state import MultiDeckState
        from app.agents.multi_deck.graph import create_multi_deck_agent
        from app.agents.multi_deck.tools import get_available_tools
        from app.agents.multi_deck.formatters.registry import get_formatter_for_tool
        from app.agents.multi_deck.nodes import comparison_tool_router_node, comparison_coder_node, comparison_executor_node, comparison_interpreter_node
        print("  [OK] Multi-Deck imports OK")
    except Exception as e:
        errors.append(f"Multi-Deck: {e}")
        print(f"  [FAIL] Multi-Deck imports falharam: {e}")
    
    return errors


def test_graph_creation():
    """Testa se os graphs podem ser criados."""
    print("\n" + "=" * 70)
    print("TESTE DE CRIAÇÃO DE GRAPHS")
    print("=" * 70)
    print()
    
    errors = []
    
    # Single Deck
    print("[TEST] Testando criação do Single Deck graph...")
    try:
        from app.agents.single_deck.graph import create_single_deck_agent
        agent = create_single_deck_agent()
        if agent is None:
            errors.append("Single Deck graph é None")
            print("  [FAIL] Graph criado é None")
        else:
            print("  [OK] Single Deck graph criado")
    except Exception as e:
        errors.append(f"Single Deck graph: {e}")
        print(f"  [FAIL] Single Deck graph falhou: {e}")
    
    # Multi-Deck
    print("\n[TEST] Testando criação do Multi-Deck graph...")
    try:
        from app.agents.multi_deck.graph import create_multi_deck_agent
        agent = create_multi_deck_agent()
        if agent is None:
            errors.append("Multi-Deck graph é None")
            print("  [FAIL] Graph criado é None")
        else:
            print("  [OK] Multi-Deck graph criado")
    except Exception as e:
        errors.append(f"Multi-Deck graph: {e}")
        print(f"  [FAIL] Multi-Deck graph falhou: {e}")
    
    return errors


def test_tools():
    """Testa se as tools podem ser carregadas."""
    print("\n" + "=" * 70)
    print("TESTE DE TOOLS")
    print("=" * 70)
    print()
    
    errors = []
    
    # Single Deck
    print("[TEST] Testando Single Deck tools...")
    try:
        from app.agents.single_deck.tools import get_available_tools
        tools = get_available_tools("/fake/path")
        print(f"  [OK] Single Deck: {len(tools)} tools carregadas")
        
        # Verificar que não tem tools de comparação
        tool_names = []
        for t in tools:
            try:
                tool_names.append(t.get_name())
            except (UnicodeEncodeError, AttributeError):
                tool_names.append(t.__class__.__name__)
        
        comparison_tools = ['MultiDeckComparisonTool', 'MudancasGeracoesTermicasTool', 'VariacaoVolumesIniciaisTool']
        found_comparison = [t for t in comparison_tools if t in tool_names]
        if found_comparison:
            errors.append(f"Single Deck tem tools de comparação: {found_comparison}")
            print(f"  [FAIL] Tools de comparação encontradas: {found_comparison}")
        else:
            print("  [OK] Nenhuma tool de comparação (correto)")
    except Exception as e:
        errors.append(f"Single Deck tools: {e}")
        print(f"  [FAIL] Single Deck tools falharam: {e}")
    
    # Multi-Deck
    print("\n[TEST] Testando Multi-Deck tools...")
    try:
        from app.agents.multi_deck.tools import get_available_tools
        tools = get_available_tools("/fake/path")
        print(f"  [OK] Multi-Deck: {len(tools)} tools carregadas")
        
        # Verificar que tem tools de comparação
        tool_names = []
        for t in tools:
            try:
                tool_names.append(t.get_name())
            except (UnicodeEncodeError, AttributeError):
                tool_names.append(t.__class__.__name__)
        
        comparison_tools = ['MultiDeckComparisonTool', 'MudancasGeracoesTermicasTool', 'VariacaoVolumesIniciaisTool']
        found_comparison = [t for t in comparison_tools if t in tool_names]
        if not found_comparison:
            errors.append("Multi-Deck não tem tools de comparação")
            print("  [FAIL] Tools de comparação não encontradas")
        else:
            print(f"  [OK] Tools de comparação encontradas: {found_comparison}")
    except Exception as e:
        errors.append(f"Multi-Deck tools: {e}")
        print(f"  [FAIL] Multi-Deck tools falharam: {e}")
    
    return errors


def test_formatters():
    """Testa registries de formatters."""
    print("\n" + "=" * 70)
    print("TESTE DE FORMATTERS")
    print("=" * 70)
    print()
    
    errors = []
    
    # Single Deck
    print("[TEST] Testando Single Deck formatters...")
    try:
        from app.agents.single_deck.formatters.registry import get_formatter_for_tool
        from app.agents.single_deck.formatters.base import SingleDeckFormatter
        from app.tools.clast_valores_tool import ClastValoresTool
        tool = ClastValoresTool("/fake/path")
        formatter = get_formatter_for_tool(tool, {})
        if not isinstance(formatter, SingleDeckFormatter):
            errors.append("Single Deck formatter não é SingleDeckFormatter")
            print("  [FAIL] Formatter incorreto")
        else:
            print("  [OK] Single Deck formatters funcionam")
    except Exception as e:
        errors.append(f"Single Deck formatters: {e}")
        print(f"  [FAIL] Single Deck formatters falharam: {e}")
    
    # Multi-Deck
    print("\n[TEST] Testando Multi-Deck formatters...")
    try:
        from app.agents.multi_deck.formatters.registry import get_formatter_for_tool
        from app.agents.multi_deck.formatters.base import ComparisonFormatter
        fake_result = {"dados_estruturais": {}}
        formatter = get_formatter_for_tool("ClastValoresTool", fake_result)
        if not isinstance(formatter, ComparisonFormatter):
            errors.append("Multi-Deck formatter não é ComparisonFormatter")
            print("  [FAIL] Formatter incorreto")
        else:
            print("  [OK] Multi-Deck formatters funcionam")
    except Exception as e:
        errors.append(f"Multi-Deck formatters: {e}")
        print(f"  [FAIL] Multi-Deck formatters falharam: {e}")
    
    return errors


def main():
    """Executa todos os testes básicos."""
    print("=" * 70)
    print("TESTE DE MODULARIZAÇÃO - TESTES BÁSICOS")
    print("=" * 70)
    print()
    
    all_errors = []
    
    # Testar imports
    errors = test_imports()
    all_errors.extend([("imports", e) for e in errors])
    
    # Testar criação de graphs
    errors = test_graph_creation()
    all_errors.extend([("graph_creation", e) for e in errors])
    
    # Testar tools
    errors = test_tools()
    all_errors.extend([("tools", e) for e in errors])
    
    # Testar formatters
    errors = test_formatters()
    all_errors.extend([("formatters", e) for e in errors])
    
    print()
    print("=" * 70)
    print("RESUMO")
    print("=" * 70)
    
    if all_errors:
        print(f"[FAIL] {len(all_errors)} erro(s) encontrado(s):")
        for category, error in all_errors:
            print(f"  [{category}] {error}")
        print()
        print("=" * 70)
        print("[FAIL] TESTE FALHOU - Revisar erros acima")
        print("=" * 70)
        return 1
    else:
        print("[PASS] TODOS OS TESTES BÁSICOS PASSARAM")
        print()
        print("=" * 70)
        print("[PASS] TESTE PASSOU")
        print("=" * 70)
        return 0


if __name__ == "__main__":
    exit(main())
