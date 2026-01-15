"""
Script para validar estrutura completa dos módulos single_deck e multi_deck.
"""

import sys
import os
from pathlib import Path

# Configurar encoding UTF-8
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    # Redirecionar stdout para UTF-8
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Adicionar raiz do projeto ao path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def validate_single_deck_structure():
    """Valida estrutura completa do módulo single_deck."""
    print("=" * 70)
    print("VALIDANDO ESTRUTURA SINGLE DECK")
    print("=" * 70)
    print()
    
    errors = []
    
    # 1. State
    print("[1] Validando state.py...")
    try:
        from app.agents.single_deck.state import SingleDeckState
        # Verificar campos essenciais
        required_fields = ['query', 'deck_path', 'relevant_docs', 'generated_code', 
                          'execution_result', 'final_response', 'tool_route', 'tool_result']
        state_fields = SingleDeckState.__annotations__.keys()
        missing_fields = [f for f in required_fields if f not in state_fields]
        if missing_fields:
            errors.append(f"State faltando campos: {missing_fields}")
            print(f"  [FAIL] Campos faltando: {missing_fields}")
        else:
            print("  [OK] SingleDeckState definido corretamente")
    except Exception as e:
        errors.append(f"State: {e}")
        print(f"  [FAIL] State: {e}")
    
    # 2. Graph
    print("\n[2] Validando graph.py...")
    try:
        from app.agents.single_deck.graph import create_single_deck_agent, get_single_deck_agent
        # Tentar criar graph
        agent = create_single_deck_agent()
        if agent is None:
            errors.append("Graph criado é None")
            print("  [FAIL] Graph criado é None")
        else:
            print("  [OK] Graph criado com sucesso")
    except Exception as e:
        errors.append(f"Graph: {e}")
        print(f"  [FAIL] Graph: {e}")
    
    # 3. Tools
    print("\n[3] Validando tools/__init__.py...")
    try:
        from app.agents.single_deck.tools import get_available_tools
        tools = get_available_tools("/fake/path")
        if not tools:
            errors.append("get_available_tools retornou lista vazia")
            print("  [FAIL] get_available_tools retornou lista vazia")
        else:
            print(f"  [OK] {len(tools)} tools carregadas")
            # Verificar que não tem tools de comparação (usar try/except para encoding)
            tool_names = []
            for t in tools:
                try:
                    name = t.get_name()
                    # Tentar codificar para verificar se há problemas
                    name.encode('utf-8')
                    tool_names.append(name)
                except (UnicodeEncodeError, UnicodeDecodeError, AttributeError):
                    # Se houver erro de encoding ou método não existir, usar nome da classe
                    tool_names.append(t.__class__.__name__)
            comparison_tools = ['MultiDeckComparisonTool', 'MudancasGeracoesTermicasTool']
            found_comparison = [t for t in comparison_tools if t in tool_names]
            if found_comparison:
                errors.append(f"Tools de comparação encontradas em single_deck: {found_comparison}")
                print(f"  [FAIL] Tools de comparação encontradas: {found_comparison}")
            else:
                print("  [OK] Nenhuma tool de comparação encontrada (correto)")
    except Exception as e:
        errors.append(f"Tools: {e}")
        print(f"  [FAIL] Tools: {e}")
    
    # 4. Formatters Registry
    print("\n[4] Validando formatters/registry.py...")
    try:
        from app.agents.single_deck.formatters.registry import get_formatter_for_tool
        from app.agents.single_deck.formatters.base import SingleDeckFormatter
        from app.agents.single_deck.formatters.generic_formatter import GenericSingleDeckFormatter
        # Testar com uma tool fake
        from app.tools.clast_valores_tool import ClastValoresTool
        fake_tool = ClastValoresTool("/fake/path")
        # O registry deve funcionar mesmo se a tool não tem get_single_deck_formatter()
        # porque ele tem fallback para mapeamento por nome e genérico
        formatter = get_formatter_for_tool(fake_tool, {})
        if not isinstance(formatter, SingleDeckFormatter):
            errors.append("Formatter retornado não é SingleDeckFormatter")
            print("  [FAIL] Formatter retornado não é SingleDeckFormatter")
        else:
            print("  [OK] Registry funciona corretamente (com fallback)")
    except AttributeError as e:
        # Se a tool não tem get_single_deck_formatter, o registry deve usar fallback
        # Verificar se o registry trata isso corretamente
        try:
            from app.agents.single_deck.formatters.registry import get_formatter_for_tool
            from app.tools.clast_valores_tool import ClastValoresTool
            fake_tool = ClastValoresTool("/fake/path")
            # Tentar novamente - o registry deve usar mapeamento por nome ou genérico
            formatter = get_formatter_for_tool(fake_tool, {})
            print("  [OK] Registry funciona corretamente (tratou método ausente)")
        except Exception as e2:
            errors.append(f"Formatters (fallback): {e2}")
            print(f"  [FAIL] Formatters (fallback): {e2}")
    except Exception as e:
        errors.append(f"Formatters: {e}")
        print(f"  [FAIL] Formatters: {e}")
    
    # 5. Nodes
    print("\n[5] Validando nodes/__init__.py...")
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
        # Verificar que são callables
        nodes = [
            tool_router_node, coder_node, executor_node, interpreter_node,
            rag_retriever_node, rag_simple_node, rag_enhanced_node, llm_planner_node
        ]
        for node in nodes:
            if not callable(node):
                errors.append(f"Node {node.__name__} não é callable")
                print(f"  [FAIL] Node {node.__name__} não é callable")
        if not errors:
            print(f"  [OK] Todos os {len(nodes)} nodes exportados e callable")
    except Exception as e:
        errors.append(f"Nodes: {e}")
        print(f"  [FAIL] Nodes: {e}")
    
    print()
    print("=" * 70)
    if errors:
        print(f"[FAIL] {len(errors)} erro(s) encontrado(s)")
        for error in errors:
            print(f"  - {error}")
        return False
    else:
        print("[PASS] Estrutura Single Deck validada com sucesso")
        return True


def validate_multi_deck_structure():
    """Valida estrutura completa do módulo multi_deck."""
    print("=" * 70)
    print("VALIDANDO ESTRUTURA MULTI-DECK")
    print("=" * 70)
    print()
    
    errors = []
    
    # 1. State
    print("[1] Validando state.py...")
    try:
        from app.agents.multi_deck.state import MultiDeckState
        # Verificar campos essenciais
        required_fields = ['query', 'deck_path', 'deck_december_path', 'deck_january_path',
                          'relevant_docs', 'generated_code', 'execution_result', 'final_response',
                          'tool_route', 'tool_result', 'comparison_data']
        state_fields = MultiDeckState.__annotations__.keys()
        missing_fields = [f for f in required_fields if f not in state_fields]
        if missing_fields:
            errors.append(f"State faltando campos: {missing_fields}")
            print(f"  [FAIL] Campos faltando: {missing_fields}")
        else:
            # Verificar campos específicos de multi-deck
            if 'deck_december_path' not in state_fields:
                errors.append("deck_december_path não encontrado")
                print("  [FAIL] deck_december_path não encontrado")
            elif 'deck_january_path' not in state_fields:
                errors.append("deck_january_path não encontrado")
                print("  [FAIL] deck_january_path não encontrado")
            else:
                print("  [OK] MultiDeckState definido corretamente (com deck_december_path e deck_january_path)")
    except Exception as e:
        errors.append(f"State: {e}")
        print(f"  [FAIL] State: {e}")
    
    # 2. Graph
    print("\n[2] Validando graph.py...")
    try:
        from app.agents.multi_deck.graph import create_multi_deck_agent, get_multi_deck_agent
        # Tentar criar graph
        agent = create_multi_deck_agent()
        if agent is None:
            errors.append("Graph criado é None")
            print("  [FAIL] Graph criado é None")
        else:
            print("  [OK] Graph criado com sucesso")
    except Exception as e:
        errors.append(f"Graph: {e}")
        print(f"  [FAIL] Graph: {e}")
    
    # 3. Tools
    print("\n[3] Validando tools/__init__.py...")
    try:
        from app.agents.multi_deck.tools import get_available_tools
        tools = get_available_tools("/fake/path")
        if not tools:
            errors.append("get_available_tools retornou lista vazia")
            print("  [FAIL] get_available_tools retornou lista vazia")
        else:
            print(f"  [OK] {len(tools)} tools carregadas")
            # Verificar que tem tools de comparação (usar try/except para encoding)
            tool_names = []
            for t in tools:
                try:
                    name = t.get_name()
                    # Tentar codificar para verificar se há problemas
                    name.encode('utf-8')
                    tool_names.append(name)
                except (UnicodeEncodeError, UnicodeDecodeError, AttributeError):
                    # Se houver erro de encoding ou método não existir, usar nome da classe
                    tool_names.append(t.__class__.__name__)
            comparison_tools = ['MultiDeckComparisonTool', 'MudancasGeracoesTermicasTool']
            found_comparison = [t for t in comparison_tools if t in tool_names]
            if not found_comparison:
                errors.append("Tools de comparação não encontradas em multi_deck")
                print("  [FAIL] Tools de comparação não encontradas")
            else:
                print(f"  [OK] Tools de comparação encontradas: {found_comparison}")
    except Exception as e:
        errors.append(f"Tools: {e}")
        print(f"  [FAIL] Tools: {e}")
    
    # 4. Formatters Registry
    print("\n[4] Validando formatters/registry.py...")
    try:
        from app.agents.multi_deck.formatters.registry import get_formatter_for_tool
        from app.agents.multi_deck.formatters.base import ComparisonFormatter
        from app.agents.multi_deck.formatters.formatters.llm_free_formatters import LLMFreeFormatter
        # Testar com uma tool fake
        from app.tools.clast_valores_tool import ClastValoresTool
        fake_tool_result = {"dados_estruturais": {}}
        formatter = get_formatter_for_tool("ClastValoresTool", fake_tool_result)
        if not isinstance(formatter, ComparisonFormatter):
            errors.append("Formatter retornado não é ComparisonFormatter")
            print("  [FAIL] Formatter retornado não é ComparisonFormatter")
        else:
            print("  [OK] Registry funciona corretamente")
    except Exception as e:
        errors.append(f"Formatters: {e}")
        print(f"  [FAIL] Formatters: {e}")
    
    # 5. Nodes
    print("\n[5] Validando nodes/__init__.py...")
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
        # Verificar que são callables
        nodes = [
            comparison_tool_router_node, comparison_coder_node, comparison_executor_node,
            comparison_interpreter_node, rag_retriever_node, rag_simple_node,
            rag_enhanced_node, llm_planner_node
        ]
        for node in nodes:
            if not callable(node):
                errors.append(f"Node {node.__name__} não é callable")
                print(f"  [FAIL] Node {node.__name__} não é callable")
        if not errors:
            print(f"  [OK] Todos os {len(nodes)} nodes exportados e callable")
    except Exception as e:
        errors.append(f"Nodes: {e}")
        print(f"  [FAIL] Nodes: {e}")
    
    print()
    print("=" * 70)
    if errors:
        print(f"[FAIL] {len(errors)} erro(s) encontrado(s)")
        for error in errors:
            print(f"  - {error}")
        return False
    else:
        print("[PASS] Estrutura Multi-Deck validada com sucesso")
        return True


def main():
    """Executa validação de estrutura."""
    print("=" * 70)
    print("VALIDAÇÃO DE ESTRUTURA DE MÓDULOS")
    print("=" * 70)
    print()
    
    single_ok = validate_single_deck_structure()
    print()
    multi_ok = validate_multi_deck_structure()
    
    print()
    print("=" * 70)
    print("RESUMO FINAL")
    print("=" * 70)
    if single_ok and multi_ok:
        print("[PASS] Todas as estruturas validadas com sucesso")
        return 0
    else:
        print("[FAIL] Algumas estruturas falharam na validação")
        return 1


if __name__ == "__main__":
    exit(main())
