"""
Script para testar get_initial_state() em ambos os módulos.
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


def test_single_deck_initial_state():
    """Testa get_initial_state() do single_deck."""
    print("=" * 70)
    print("TESTANDO get_initial_state() - SINGLE DECK")
    print("=" * 70)
    print()
    
    errors = []
    
    try:
        from app.agents.single_deck.graph import get_initial_state
        from app.agents.single_deck.state import SingleDeckState
        
        # Testar criação de estado inicial
        print("[1] Testando get_initial_state()...")
        state = get_initial_state("test query", "/fake/path", llm_mode=False)
        
        if not isinstance(state, dict):
            errors.append("get_initial_state() não retornou dict")
            print("  [FAIL] get_initial_state() não retornou dict")
        else:
            print("  [OK] get_initial_state() retornou dict")
        
        # Verificar campos essenciais
        print("\n[2] Verificando campos essenciais...")
        required_fields = ['query', 'deck_path', 'relevant_docs', 'generated_code',
                         'execution_result', 'final_response', 'tool_route', 'tool_result']
        missing_fields = [f for f in required_fields if f not in state]
        if missing_fields:
            errors.append(f"Campos faltando: {missing_fields}")
            print(f"  [FAIL] Campos faltando: {missing_fields}")
        else:
            print("  [OK] Todos os campos essenciais presentes")
        
        # Verificar valores
        print("\n[3] Verificando valores iniciais...")
        if state.get('query') != "test query":
            errors.append(f"query incorreto: {state.get('query')}")
            print(f"  [FAIL] query incorreto: {state.get('query')}")
        else:
            print("  [OK] query correto")
        
        if state.get('deck_path') != "/fake/path":
            errors.append(f"deck_path incorreto: {state.get('deck_path')}")
            print(f"  [FAIL] deck_path incorreto: {state.get('deck_path')}")
        else:
            print("  [OK] deck_path correto")
        
        if state.get('tool_route') is not False:
            errors.append(f"tool_route deve ser False inicialmente: {state.get('tool_route')}")
            print(f"  [FAIL] tool_route incorreto: {state.get('tool_route')}")
        else:
            print("  [OK] tool_route inicializado corretamente")
        
        # Verificar que NÃO tem campos de multi-deck
        print("\n[4] Verificando que não tem campos de multi-deck...")
        multi_deck_fields = ['deck_december_path', 'deck_january_path']
        found_multi = [f for f in multi_deck_fields if f in state]
        if found_multi:
            errors.append(f"Campos de multi-deck encontrados em single_deck: {found_multi}")
            print(f"  [FAIL] Campos de multi-deck encontrados: {found_multi}")
        else:
            print("  [OK] Nenhum campo de multi-deck encontrado (correto)")
        
        # Testar com llm_mode=True
        print("\n[5] Testando com llm_mode=True...")
        state_llm = get_initial_state("test query", "/fake/path", llm_mode=True)
        if state_llm.get('llm_instructions') is None:
            errors.append("llm_instructions deve ser string vazia quando llm_mode=True")
            print("  [FAIL] llm_instructions incorreto")
        else:
            print("  [OK] llm_mode funciona corretamente")
        
    except Exception as e:
        errors.append(f"Erro: {e}")
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


def test_multi_deck_initial_state():
    """Testa get_initial_state() do multi_deck."""
    print("=" * 70)
    print("TESTANDO get_initial_state() - MULTI-DECK")
    print("=" * 70)
    print()
    
    errors = []
    
    try:
        from app.agents.multi_deck.graph import get_initial_state
        from app.agents.multi_deck.state import MultiDeckState
        from app.utils.deck_loader import get_december_deck_path, get_january_deck_path
        
        # Testar criação de estado inicial
        print("[1] Testando get_initial_state()...")
        state = get_initial_state("test query", "/fake/path", llm_mode=False)
        
        if not isinstance(state, dict):
            errors.append("get_initial_state() não retornou dict")
            print("  [FAIL] get_initial_state() não retornou dict")
        else:
            print("  [OK] get_initial_state() retornou dict")
        
        # Verificar campos essenciais
        print("\n[2] Verificando campos essenciais...")
        required_fields = ['query', 'deck_path', 'deck_december_path', 'deck_january_path',
                         'relevant_docs', 'generated_code', 'execution_result', 
                         'final_response', 'tool_route', 'tool_result', 'comparison_data']
        missing_fields = [f for f in required_fields if f not in state]
        if missing_fields:
            errors.append(f"Campos faltando: {missing_fields}")
            print(f"  [FAIL] Campos faltando: {missing_fields}")
        else:
            print("  [OK] Todos os campos essenciais presentes")
        
        # Verificar campos específicos de multi-deck
        print("\n[3] Verificando campos específicos de multi-deck...")
        if 'deck_december_path' not in state:
            errors.append("deck_december_path não encontrado")
            print("  [FAIL] deck_december_path não encontrado")
        else:
            print("  [OK] deck_december_path presente")
        
        if 'deck_january_path' not in state:
            errors.append("deck_january_path não encontrado")
            print("  [FAIL] deck_january_path não encontrado")
        else:
            print("  [OK] deck_january_path presente")
        
        # Verificar valores
        print("\n[4] Verificando valores iniciais...")
        if state.get('query') != "test query":
            errors.append(f"query incorreto: {state.get('query')}")
            print(f"  [FAIL] query incorreto: {state.get('query')}")
        else:
            print("  [OK] query correto")
        
        if state.get('deck_path') != "/fake/path":
            errors.append(f"deck_path incorreto: {state.get('deck_path')}")
            print(f"  [FAIL] deck_path incorreto: {state.get('deck_path')}")
        else:
            print("  [OK] deck_path correto")
        
        # Verificar que deck_december_path e deck_january_path são definidos
        # (mesmo que sejam None ou strings vazias inicialmente)
        print("\n[5] Verificando inicialização de caminhos dos decks...")
        if state.get('deck_december_path') is None:
            print("  [WARN] deck_december_path é None (pode ser normal se não houver deck)")
        else:
            print(f"  [OK] deck_december_path: {state.get('deck_december_path')}")
        
        if state.get('deck_january_path') is None:
            print("  [WARN] deck_january_path é None (pode ser normal se não houver deck)")
        else:
            print(f"  [OK] deck_january_path: {state.get('deck_january_path')}")
        
        # Testar com llm_mode=True
        print("\n[6] Testando com llm_mode=True...")
        state_llm = get_initial_state("test query", "/fake/path", llm_mode=True)
        if state_llm.get('llm_instructions') is None:
            errors.append("llm_instructions deve ser string vazia quando llm_mode=True")
            print("  [FAIL] llm_instructions incorreto")
        else:
            print("  [OK] llm_mode funciona corretamente")
        
    except Exception as e:
        errors.append(f"Erro: {e}")
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
    """Executa testes de inicialização de estado."""
    print("=" * 70)
    print("TESTE DE INICIALIZAÇÃO DE ESTADO")
    print("=" * 70)
    print()
    
    single_ok = test_single_deck_initial_state()
    print()
    multi_ok = test_multi_deck_initial_state()
    
    print()
    print("=" * 70)
    print("RESUMO FINAL")
    print("=" * 70)
    if single_ok and multi_ok:
        print("[PASS] Todos os estados foram inicializados corretamente")
        return 0
    else:
        print("[FAIL] Alguns estados falharam na inicialização")
        return 1


if __name__ == "__main__":
    exit(main())
