"""
Node que interpreta os resultados e gera a resposta final formatada em Markdown (single deck DECOMP).
"""

import os
import json as json_module
from decomp_agent.app.agents.single_deck.state import SingleDeckState
from decomp_agent.app.config import safe_print
from shared.utils.text_utils import clean_response_text
from decomp_agent.app.agents.single_deck.formatters.registry import get_formatter_for_tool
from decomp_agent.app.tools import get_available_tools


# Função auxiliar para escrever no log de debug de forma segura
def _write_debug_log(data: dict):
    """Escreve no arquivo de debug, criando o diretório se necessário."""
    try:
        log_path = r'c:\Users\Inteli\OneDrive\Desktop\nw_multi\.cursor\debug.log'
        log_dir = os.path.dirname(log_path)
        os.makedirs(log_dir, exist_ok=True)
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(json_module.dumps(data) + '\n')
    except Exception:
        pass


def interpreter_node(state: SingleDeckState) -> dict:
    """
    Node que formata os resultados e gera a resposta final em Markdown.
    
    Prioridades:
    1. Se tool_result existe: formata resultado da tool usando formatters
    2. Se disambiguation existe: retorna resposta vazia (frontend cria mensagem)
    3. Caso contrário: retorna mensagem informando que não há tool disponível
    """
    try:
        tool_result = state.get("tool_result")
        tool_used = state.get("tool_used")
        
        if tool_result:
            safe_print(f"[INTERPRETER DECOMP] Processando resultado de tool: {tool_used}")
            safe_print(f"[INTERPRETER DECOMP]   Success: {tool_result.get('success', False)}")
            
            # Obter tool instance para usar no registry
            tool_instance = None
            deck_path = state.get("deck_path", "")
            try:
                available_tools = get_available_tools(deck_path)
                for tool in available_tools:
                    if tool.get_name() == tool_used:
                        tool_instance = tool
                        break
            except Exception as e:
                safe_print(f"[INTERPRETER DECOMP] [AVISO] Erro ao obter tools: {e}")
            
            if tool_instance is None:
                safe_print(f"[INTERPRETER DECOMP] [AVISO] Tool instance não encontrada, usando formatter genérico")
                from decomp_agent.app.agents.single_deck.formatters.generic_formatter import GenericSingleDeckFormatter
                formatter = GenericSingleDeckFormatter()
            else:
                # Obter formatter via registry
                safe_print(f"[INTERPRETER DECOMP] Obtendo formatter para tool: {tool_used}")
                formatter = get_formatter_for_tool(tool_instance, tool_result)
                safe_print(f"[INTERPRETER DECOMP] Formatter selecionado: {formatter.__class__.__name__}")
            
            query = state.get("query", "")
            # Se a query veio de disambiguation, extrair apenas a parte original
            if query.startswith("__DISAMBIG__:"):
                try:
                    parts = query.split(":", 2)
                    if len(parts) == 3:
                        query = parts[2].strip()
                except Exception:
                    pass
            elif " - " in query:
                query = query.split(" - ", 1)[0].strip()
            
            # Formatar resposta usando o formatter
            try:
                # Verificar se o formatter aceita deck_path como parâmetro
                import inspect
                sig = inspect.signature(formatter.format_response)
                if 'deck_path' in sig.parameters:
                    formatted = formatter.format_response(tool_result, tool_used, query, deck_path=deck_path)
                else:
                    formatted = formatter.format_response(tool_result, tool_used, query)
                safe_print(f"[INTERPRETER DECOMP] [OK] Resposta formatada com sucesso")
                safe_print(f"[INTERPRETER DECOMP]   Tem visualization_data: {bool(formatted.get('visualization_data'))}")
                
                return {
                    "final_response": clean_response_text(formatted.get("final_response", ""), max_emojis=2),
                    "visualization_data": formatted.get("visualization_data")
                }
            except Exception as e:
                safe_print(f"[INTERPRETER DECOMP] [ERRO] Erro ao formatar resposta: {e}")
                import traceback
                traceback.print_exc()
                # Fallback: resposta simples
                response = f"## Resultado da Tool: {tool_used}\n\n"
                if tool_result.get("success"):
                    data_count = len(tool_result.get("data", []))
                    response += f"Total de registros: {data_count}\n\nDados processados com sucesso."
                else:
                    response += f"Erro: {tool_result.get('error', 'Erro desconhecido')}"
                return {
                    "final_response": clean_response_text(response, max_emojis=2),
                    "visualization_data": None
                }
        
        # Verificar se há disambiguation
        disambiguation = state.get("disambiguation")
        if disambiguation:
            safe_print(f"[INTERPRETER DECOMP] Processando disambiguation com {len(disambiguation.get('options', []))} opções")
            return {"final_response": ""}  # Vazio - frontend já cria a mensagem
        
        # Se não há tool_result e não há disambiguation, retornar mensagem
        safe_print(f"[INTERPRETER DECOMP] Nenhuma tool disponível para processar a consulta")
        no_tool_msg = """## Nenhuma tool disponível para sua consulta

Não encontrei uma tool pré-programada que possa processar sua solicitação.

### Sugestões de perguntas válidas:

- "Quais são as usinas hidrelétricas do DECOMP?"
- "Quais são os limites de intercâmbio?"
- "Quais são as restrições elétricas?"
- "Quais são as manutenções programadas?"
- "Quais são as gerações GNL?"

### Tools disponíveis:

Consulte a documentação para ver todas as tools disponíveis para análise de decks DECOMP."""
        no_tool_msg = clean_response_text(no_tool_msg, max_emojis=2)
        return {"final_response": no_tool_msg, "visualization_data": None}
        
    except Exception as e:
        safe_print(f"[INTERPRETER DECOMP ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        error_msg = f"## Erro ao processar resultado\n\nOcorreu um erro ao formatar a resposta: {str(e)}"
        error_msg = clean_response_text(error_msg, max_emojis=2)
        return {"final_response": error_msg, "visualization_data": None}
