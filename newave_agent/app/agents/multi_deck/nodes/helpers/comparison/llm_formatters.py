"""
Formatadores de comparação que usam LLM.
"""

from typing import Dict, Any
import json
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from app.config import OPENAI_API_KEY, OPENAI_MODEL, safe_print
from app.utils.text_utils import clean_response_text
from .summarizers import summarize_deck_data
from .simple_formatters import generate_fallback_comparison_response
from ..prompts import (
    COMPARISON_INTERPRETER_SYSTEM_PROMPT,
    COMPARISON_INTERPRETER_USER_PROMPT,
    COMPARISON_LLM_FREE_SYSTEM_PROMPT,
    COMPARISON_LLM_FREE_USER_PROMPT
)


def format_with_llm_structured(
    result_dec: Dict[str, Any],
    result_jan: Dict[str, Any],
    tool_used: str,
    query: str,
    deck_1_name: str,
    deck_2_name: str,
    formatted: Dict[str, Any]
) -> str:
    """
    Formata resposta usando LLM com prompt estruturado (para visualizações temporais, tabelas, etc).
    """
    # Preparar resumos dos dados para o LLM
    deck_1_summary = summarize_deck_data({"full_result": result_dec})
    deck_2_summary = summarize_deck_data({"full_result": result_jan})
    
    # Resumir diferenças da tabela comparativa
    comparison_table = formatted.get("comparison_table", [])
    differences_summary = ""
    if comparison_table:
        # Verificar se é formato de CVU (campos: data/ano, deck_1, deck_2)
        first_item = comparison_table[0] if comparison_table else {}
        is_cvu_format = ("data" in first_item or "ano" in first_item) and "deck_1" in first_item and "deck_2" in first_item
        
        if is_cvu_format:
            # Formato específico para CVU - instruir explicitamente como formatar
            differences_summary = f"TABELA COMPARATIVA DE CVU com {len(comparison_table)} anos:\n\n"
            differences_summary += "FORMATO OBRIGATORIO DA TABELA:\n"
            differences_summary += f"| Ano | {deck_1_name} | {deck_2_name} |\n"
            differences_summary += "|-----|---------------|---------------|\n"
            
            for item in comparison_table:
                # Usar campo "ano" se disponível, senão usar "data"
                ano = item.get("ano") or item.get("data", "")
                val1 = item.get("deck_1")
                val2 = item.get("deck_2")
                
                # Formatar valores
                val1_str = f"{val1:.2f}" if val1 is not None else "-"
                val2_str = f"{val2:.2f}" if val2 is not None else "-"
                
                differences_summary += f"| {ano} | {val1_str} | {val2_str} |\n"
        else:
            # Formato genérico
            differences_summary = f"Tabela comparativa com {len(comparison_table)} registros:\n"
            # Mostrar primeiros 10 itens como exemplo
            for item in comparison_table[:10]:
                differences_summary += f"- {json.dumps(item, ensure_ascii=False, default=str)}\n"
            if len(comparison_table) > 10:
                differences_summary += f"\n... e mais {len(comparison_table) - 10} registros\n"
    else:
        differences_summary = "Nenhuma diferença pré-calculada disponível."
    
    llm = ChatOpenAI(
        api_key=OPENAI_API_KEY,
        model=OPENAI_MODEL,
        temperature=0.3
    )
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", COMPARISON_INTERPRETER_SYSTEM_PROMPT.format(
            deck_1_name=deck_1_name,
            deck_2_name=deck_2_name,
            query=query
        )),
        ("human", COMPARISON_INTERPRETER_USER_PROMPT)
    ])
    
    chain = prompt | llm
    
    response = chain.invoke({
        "deck_1_name": deck_1_name,
        "deck_2_name": deck_2_name,
        "deck_1_summary": deck_1_summary,
        "deck_2_summary": deck_2_summary,
        "differences_summary": differences_summary
    })
    
    final_response = getattr(response, 'content', None)
    
    if final_response:
        safe_print(f"[INTERPRETER] [OK] Interpretacao estruturada gerada ({len(final_response)} caracteres)")
        final_response = clean_response_text(final_response, max_emojis=2)
    else:
        safe_print(f"[INTERPRETER] [AVISO] LLM nao retornou conteudo, usando fallback")
        final_response = generate_fallback_comparison_response(
            query, deck_1_name, deck_2_name, tool_used, comparison_table
        )
    
    return final_response


def format_with_llm_free(
    result_dec: Dict[str, Any],
    result_jan: Dict[str, Any],
    tool_used: str,
    query: str,
    deck_1_name: str,
    deck_2_name: str,
    formatted: Dict[str, Any]
) -> str:
    """
    Formata resposta usando LLM com prompt livre (para diff_list e llm_free).
    Dá mais liberdade para o LLM interpretar os dados.
    """
    # Preparar resumos dos dados para o LLM
    deck_1_summary = summarize_deck_data({"full_result": result_dec})
    deck_2_summary = summarize_deck_data({"full_result": result_jan})
    
    # Preparar contexto adicional
    context_info = ""
    llm_context = formatted.get("llm_context", {})
    
    if formatted.get("diff_categories"):
        diff_categories = formatted.get("diff_categories")
        
        if isinstance(diff_categories, dict) and "added" in diff_categories:
            # Formato Expt/Modif (diff simples)
            added = diff_categories.get("added", [])
            removed = diff_categories.get("removed", [])
            modified = diff_categories.get("modified", [])
            
            context_info = f"Diferenças identificadas:\n"
            context_info += f"- Adicionado em {deck_2_name}: {len(added)} item(s)\n"
            context_info += f"- Removido de {deck_1_name}: {len(removed)} item(s)\n"
            context_info += f"- Modificado: {len(modified)} item(s)\n\n"
            
            if added:
                context_info += f"Exemplos de itens adicionados:\n"
                for item in added[:3]:
                    context_info += f"  {json.dumps(item, ensure_ascii=False, default=str)}\n"
            
            if removed:
                context_info += f"\nExemplos de itens removidos:\n"
                for item in removed[:3]:
                    context_info += f"  {json.dumps(item, ensure_ascii=False, default=str)}\n"
        else:
            # Formato Modif (por tipo)
            context_info = "Diferenças por tipo de modificação:\n"
            for tipo, diffs in diff_categories.items():
                added = diffs.get("added", [])
                removed = diffs.get("removed", [])
                modified = diffs.get("modified", [])
                context_info += f"\n{tipo}:\n"
                context_info += f"  - Adicionado: {len(added)}, Removido: {len(removed)}, Modificado: {len(modified)}\n"
    
    if llm_context:
        context_info += f"\nContexto adicional: {json.dumps(llm_context, ensure_ascii=False, default=str)}\n"
    
    llm = ChatOpenAI(
        api_key=OPENAI_API_KEY,
        model=OPENAI_MODEL,
        temperature=0.5  # Temperatura maior para mais criatividade
    )
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", COMPARISON_LLM_FREE_SYSTEM_PROMPT.format(
            deck_1_name=deck_1_name,
            deck_2_name=deck_2_name,
            query=query
        )),
        ("human", COMPARISON_LLM_FREE_USER_PROMPT)
    ])
    
    chain = prompt | llm
    
    response = chain.invoke({
        "deck_1_name": deck_1_name,
        "deck_2_name": deck_2_name,
        "deck_1_summary": deck_1_summary,
        "deck_2_summary": deck_2_summary,
        "context_info": context_info
    })
    
    final_response = getattr(response, 'content', None)
    
    if final_response:
        safe_print(f"[INTERPRETER] [OK] Interpretacao livre gerada ({len(final_response)} caracteres)")
        final_response = clean_response_text(final_response, max_emojis=2)
    else:
        safe_print(f"[INTERPRETER] [AVISO] LLM nao retornou conteudo, usando fallback livre")
        # Fallback simples
        final_response = f"## Análise Comparativa\n\nDados comparados entre {deck_1_name} e {deck_2_name}.\n\nConsulte os dados detalhados para análise completa."
    
    return final_response

