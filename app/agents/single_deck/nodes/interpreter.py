"""
Node que interpreta os resultados e gera a resposta final formatada em Markdown (single deck).
"""

import os
import json as json_module
from app.agents.single_deck.state import SingleDeckState
from app.config import safe_print
from app.utils.text_utils import clean_response_text
from app.agents.single_deck.nodes.helpers.code_execution.formatter import format_code_execution_response
from app.agents.single_deck.formatters.registry import get_formatter_for_tool
from app.agents.single_deck.tools import get_available_tools

# Função auxiliar para escrever no log de debug de forma segura
def _write_debug_log(data: dict):
    """Escreve no arquivo de debug, criando o diretório se necessário."""
    try:
        log_path = r'c:\Users\Inteli\OneDrive\Desktop\nw_multi\.cursor\debug.log'
        log_dir = os.path.dirname(log_path)
        # Criar diretório se não existir
        os.makedirs(log_dir, exist_ok=True)
        # Escrever no arquivo
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(json_module.dumps(data) + '\n')
    except Exception:
        # Silenciosamente ignorar erros de log para não interromper o fluxo
        pass


def interpreter_node(state: SingleDeckState) -> dict:
    """
    Node que interpreta os resultados e gera a resposta final formatada em Markdown.
    
    Prioridades:
    1. Se tool_result existe: processa resultado da tool
    2. Se rag_status == "fallback": retorna resposta de fallback
    3. Caso contrário: interpreta resultados de execução de código
    """
    # #region agent log
    _write_debug_log({
        "sessionId": "debug-session",
        "runId": "run1",
        "hypothesisId": "A",
        "location": "interpreter.py:13",
        "message": "Interpreter node called",
        "data": {"has_tool_result": bool(state.get("tool_result")), "tool_used": state.get("tool_used"), "tool_route": state.get("tool_route", False)},
        "timestamp": int(__import__('time').time() * 1000)
    })
    # #endregion
    
    try:
        tool_result = state.get("tool_result")
        tool_used = state.get("tool_used")
        
        if tool_result:
            safe_print(f"[INTERPRETER] Processando resultado de tool: {tool_used}")
            safe_print(f"[INTERPRETER]   Success: {tool_result.get('success', False)}")
            
            # #region agent log
            _write_debug_log({
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "B",
                "location": "interpreter.py:27",
                "message": "Tool result found, starting formatting",
                "data": {"tool_used": tool_used, "success": tool_result.get('success', False), "has_data": bool(tool_result.get('data'))},
                "timestamp": int(__import__('time').time() * 1000)
            })
            # #endregion
            
            # Obter tool instance para usar no registry
            tool_instance = None
            available_tools = get_available_tools(state.get("deck_path", ""))
            for tool in available_tools:
                if tool.get_name() == tool_used:
                    tool_instance = tool
                    break
            
            if tool_instance is None:
                safe_print(f"[INTERPRETER] ⚠️ Tool instance não encontrada, usando formatter genérico")
                from app.agents.single_deck.formatters.generic_formatter import GenericSingleDeckFormatter
                formatter = GenericSingleDeckFormatter()
            else:
                # Obter formatter via registry
                formatter = get_formatter_for_tool(tool_instance, tool_result)
            
            query = state.get("query", "")
            # Se a query veio de disambiguation, extrair apenas a parte original
            # Formato novo: "__DISAMBIG__:ToolName:original_query"
            if query.startswith("__DISAMBIG__:"):
                try:
                    parts = query.split(":", 2)
                    if len(parts) == 3:
                        query = parts[2].strip()  # Usar apenas a query original
                        safe_print(f"[INTERPRETER]   Query veio de disambiguation (formato novo), usando query original: {query[:100]}")
                except Exception as e:
                    safe_print(f"[INTERPRETER] ⚠️ Erro ao limpar query de disambiguation: {e}")
            # Formato antigo (compatibilidade): "query - tool_name"
            elif " - " in query:
                query = query.split(" - ", 1)[0].strip()
                safe_print(f"[INTERPRETER]   Query veio de disambiguation (formato antigo), usando query original: {query[:100]}")
            else:
                safe_print(f"[INTERPRETER]   Query original: {query[:100]}")
            safe_print(f"[INTERPRETER]   Usando formatter: {formatter.__class__.__name__}")
            
            # #region agent log
            _write_debug_log({
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "C",
                "location": "interpreter.py:48",
                "message": "Formatter obtained, about to format",
                "data": {"formatter_class": formatter.__class__.__name__, "query": query[:50]},
                "timestamp": int(__import__('time').time() * 1000)
            })
            # #endregion
            
            # Formatar resposta usando o formatter
            result = formatter.format_response(tool_result, tool_used, query)
            
            # Extrair visualization_data se presente
            visualization_data = result.get("visualization_data")
            
            # #region agent log
            _write_debug_log({
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "D",
                "location": "interpreter.py:51",
                "message": "Formatter result obtained",
                "data": {
                    "has_final_response": bool(result.get('final_response')),
                    "has_visualization_data": visualization_data is not None,
                    "response_length": len(result.get('final_response', '')),
                    "response_preview": result.get('final_response', '')[:100]
                },
                "timestamp": int(__import__('time').time() * 1000)
            })
            # #endregion
            
            safe_print(f"[INTERPRETER]   Resposta gerada: {len(result.get('final_response', ''))} caracteres")
            if visualization_data:
                safe_print(f"[INTERPRETER]   Visualization data presente: {visualization_data.get('visualization_type', 'N/A')}")
            
            return {
                "final_response": result.get("final_response", ""),
                "visualization_data": visualization_data
            }
        
        # Verificar se há disambiguation
        disambiguation = state.get("disambiguation")
        if disambiguation:
            safe_print(f"[INTERPRETER] Processando disambiguation com {len(disambiguation.get('options', []))} opções")
            return {"final_response": ""}  # Vazio - frontend já cria a mensagem
        
        # Verificar se é um caso de fallback
        rag_status = state.get("rag_status", "success")
        
        if rag_status == "fallback":
            fallback_response = state.get("fallback_response", "")
            if fallback_response:
                fallback_response = clean_response_text(fallback_response, max_emojis=2)
                return {"final_response": fallback_response}
            
            # Fallback genérico se não houver resposta
            fallback_msg = """## Não foi possível processar sua solicitação

Não encontrei arquivos de dados adequados para responder sua pergunta.

### Sugestões de perguntas válidas:

- "Quais são as usinas hidrelétricas com maior potência instalada?"
- "Quais térmicas têm manutenção programada?"
- "Qual o custo das classes térmicas?"
- "Qual a demanda do submercado Sudeste?"
- "Quais são as vazões históricas do posto 1?"

### Dados disponíveis para consulta:

- **HIDR.DAT**: Cadastro de usinas hidrelétricas (potência, volumes, características)
- **MANUTT.DAT**: Manutenções de térmicas
- **CLAST.DAT**: Custos de classes térmicas
- **SISTEMA.DAT**: Demandas e intercâmbios entre submercados
- **VAZOES.DAT**: Séries históricas de vazões
"""
            fallback_msg = clean_response_text(fallback_msg, max_emojis=2)
            return {"final_response": fallback_msg}
        
        # Fluxo normal - interpretar resultados de execução
        execution_result = state.get("execution_result") or {}
        generated_code = state.get("generated_code", "")
        query = state.get("query", "")
        
        # Limpar query se vier de disambiguation (remover tag __DISAMBIG__)
        if query.startswith("__DISAMBIG__:"):
            try:
                parts = query.split(":", 2)
                if len(parts) == 3:
                    query = parts[2].strip()  # Usar apenas a query original
                    safe_print(f"[INTERPRETER] Query limpa de disambiguation: {query}")
            except Exception as e:
                safe_print(f"[INTERPRETER] ⚠️ Erro ao limpar query de disambiguation: {e}")
        # Formato antigo (compatibilidade)
        elif " - " in query:
            query = query.split(" - ", 1)[0].strip()
            safe_print(f"[INTERPRETER] Query limpa de disambiguation (formato antigo): {query}")
        
        relevant_docs = state.get("relevant_docs", [])
        retry_count = state.get("retry_count", 0)
        max_retries = state.get("max_retries", 3)
        
        return format_code_execution_response(
            execution_result=execution_result,
            generated_code=generated_code,
            query=query,
            relevant_docs=relevant_docs,
            retry_count=retry_count,
            max_retries=max_retries
        )
        
    except Exception as e:
        safe_print(f"[INTERPRETER ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        error_msg = f"## Erro ao interpretar resultados\n\nOcorreu um erro ao gerar a resposta: {str(e)}\n\nConsulte a saída da execução do código para ver os dados."
        error_msg = clean_response_text(error_msg, max_emojis=2)
        return {"final_response": error_msg}

