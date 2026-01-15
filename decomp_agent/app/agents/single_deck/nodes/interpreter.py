"""
Node que interpreta os resultados e gera a resposta final formatada em Markdown (single deck DECOMP).
"""

import os
import json as json_module
from decomp_agent.app.agents.single_deck.state import SingleDeckState
from decomp_agent.app.config import safe_print
from shared.utils.text_utils import clean_response_text
from decomp_agent.app.agents.single_deck.formatters.registry import get_formatter_for_tool
from decomp_agent.app.agents.single_deck.tools import get_available_tools


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
    Node que interpreta os resultados e gera a resposta final formatada em Markdown.
    
    Prioridades:
    1. Se tool_result existe: processa resultado da tool
    2. Se rag_status == "fallback": retorna resposta de fallback
    3. Caso contrário: interpreta resultados de execução de código
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

- "Quais são as usinas hidrelétricas do DECOMP?"
- "Quais são os limites de intercâmbio?"
- "Quais são as restrições elétricas?"
- "Quais são as manutenções programadas?"

### Dados disponíveis para consulta:

- **dadger.rvx**: Arquivo principal DECOMP com todos os dados de entrada
"""
            fallback_msg = clean_response_text(fallback_msg, max_emojis=2)
            return {"final_response": fallback_msg}
        
        # Fluxo normal - interpretar resultados de execução
        execution_result = state.get("execution_result") or {}
        generated_code = state.get("generated_code", "")
        query = state.get("query", "")
        
        # Limpar query se vier de disambiguation
        if query.startswith("__DISAMBIG__:"):
            try:
                parts = query.split(":", 2)
                if len(parts) == 3:
                    query = parts[2].strip()
            except Exception:
                pass
        elif " - " in query:
            query = query.split(" - ", 1)[0].strip()
        
        # Formatação básica de resposta
        success = execution_result.get("success", False)
        stdout = execution_result.get("stdout", "")
        stderr = execution_result.get("stderr", "")
        
        if success:
            response = f"## Resultado da Análise\n\n{stdout}"
        else:
            response = f"## Erro na Execução\n\n{stderr}\n\nCódigo gerado:\n```python\n{generated_code}\n```"
        
        response = clean_response_text(response, max_emojis=2)
        
        return {
            "final_response": response,
            "visualization_data": None
        }
        
    except Exception as e:
        safe_print(f"[INTERPRETER DECOMP ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        error_msg = f"## Erro ao interpretar resultados\n\nOcorreu um erro ao gerar a resposta: {str(e)}\n\nConsulte a saída da execução do código para ver os dados."
        error_msg = clean_response_text(error_msg, max_emojis=2)
        return {"final_response": error_msg}
