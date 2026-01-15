"""
Formatadores de comparação que usam LLM com prompt estruturado.
Suporta N decks para comparação dinâmica.
"""

from typing import Dict, Any, List, Optional
import json
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from app.config import OPENAI_API_KEY, OPENAI_MODEL, safe_print
from app.utils.text_utils import clean_response_text
from .summarizers import summarize_deck_data, summarize_multiple_decks
from .simple import generate_fallback_comparison_response
from app.agents.multi_deck.nodes.helpers.prompts import (
    COMPARISON_INTERPRETER_SYSTEM_PROMPT,
    COMPARISON_INTERPRETER_USER_PROMPT,
)


def format_with_llm_structured(
    result_dec: Dict[str, Any],
    result_jan: Dict[str, Any],
    tool_used: str,
    query: str,
    deck_1_name: str,
    deck_2_name: str,
    formatted: Dict[str, Any],
    deck_names: Optional[List[str]] = None,
    deck_results: Optional[List[Dict[str, Any]]] = None
) -> str:
    """
    Formata resposta usando LLM com prompt estruturado (para visualizações temporais, tabelas, etc).
    Suporta N decks para comparação dinâmica.
    
    Args:
        result_dec: Resultado do primeiro deck (fallback)
        result_jan: Resultado do último deck (fallback)
        tool_used: Nome da tool utilizada
        query: Query original do usuário
        deck_1_name: Nome do primeiro deck (fallback)
        deck_2_name: Nome do último deck (fallback)
        formatted: Resultado formatado pelo formatter
        deck_names: Lista de nomes de decks (para N decks)
        deck_results: Lista de resultados de cada deck (para N decks)
    """
    n_decks = len(deck_names) if deck_names else 2
    is_historical_analysis = n_decks > 2
    
    # Preparar resumos dos dados para o LLM
    if deck_results and len(deck_results) > 0:
        # Usar summarize_multiple_decks para N decks
        decks_summary = summarize_multiple_decks(deck_results, deck_names)
        deck_1_summary = decks_summary  # Usar resumo combinado
        deck_2_summary = ""  # Não necessário para N decks
    else:
        deck_1_summary = summarize_deck_data({"full_result": result_dec})
        deck_2_summary = summarize_deck_data({"full_result": result_jan})
    
    # Resumir diferenças da tabela comparativa
    comparison_table = formatted.get("comparison_table", [])
    differences_summary = ""
    if comparison_table:
        # Verificar se é formato de CVU (campos: data/ano, deck_1, deck_2 ou deck_N)
        first_item = comparison_table[0] if comparison_table else {}
        has_deck_columns = any(key.startswith("deck_") for key in first_item.keys() if key not in ["data", "ano"])
        is_cvu_format = ("data" in first_item or "ano" in first_item) and has_deck_columns
        
        if is_cvu_format:
            # Formato específico para CVU - instruir explicitamente como formatar
            if is_historical_analysis:
                differences_summary = f"TABELA DE EVOLUÇÃO HISTÓRICA DE CVU com {len(comparison_table)} períodos e {n_decks} decks:\n\n"
                differences_summary += "FORMATO OBRIGATORIO DA TABELA:\n"
                header = "| Período |"
                divider = "|---------|"
                for name in (deck_names or [deck_1_name, deck_2_name]):
                    header += f" {name} |"
                    divider += "--------|"
                differences_summary += header + "\n" + divider + "\n"
            else:
                differences_summary = f"TABELA COMPARATIVA DE CVU com {len(comparison_table)} anos:\n\n"
                differences_summary += "FORMATO OBRIGATORIO DA TABELA:\n"
                differences_summary += f"| Ano | {deck_1_name} | {deck_2_name} |\n"
                differences_summary += "|-----|---------------|---------------|\n"
            
            for item in comparison_table[:20]:  # Limitar a 20 linhas para o resumo
                ano = item.get("ano") or item.get("data", "")
                row = f"| {ano} |"
                
                if deck_names:
                    for i in range(len(deck_names)):
                        val = item.get(f"deck_{i+1}")
                        val_str = f"{val:.2f}" if val is not None else "-"
                        row += f" {val_str} |"
                else:
                    val1 = item.get("deck_1")
                    val2 = item.get("deck_2")
                    val1_str = f"{val1:.2f}" if val1 is not None else "-"
                    val2_str = f"{val2:.2f}" if val2 is not None else "-"
                    row += f" {val1_str} | {val2_str} |"
                
                differences_summary += row + "\n"
            
            if len(comparison_table) > 20:
                differences_summary += f"\n... e mais {len(comparison_table) - 20} períodos\n"
        else:
            # Formato genérico
            differences_summary = f"Tabela comparativa com {len(comparison_table)} registros:\n"
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
    
    # Adaptar prompt para análise histórica se necessário
    if is_historical_analysis:
        system_prompt = COMPARISON_INTERPRETER_SYSTEM_PROMPT.format(
            deck_1_name=deck_names[0] if deck_names else deck_1_name,
            deck_2_name=deck_names[-1] if deck_names else deck_2_name,
            query=query
        )
        system_prompt = system_prompt.replace(
            "comparação entre dois decks",
            f"análise histórica de {n_decks} decks"
        )
    else:
        system_prompt = COMPARISON_INTERPRETER_SYSTEM_PROMPT.format(
            deck_1_name=deck_1_name,
            deck_2_name=deck_2_name,
            query=query
        )
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", COMPARISON_INTERPRETER_USER_PROMPT)
    ])
    
    chain = prompt | llm
    
    response = chain.invoke({
        "deck_1_name": deck_names[0] if deck_names else deck_1_name,
        "deck_2_name": deck_names[-1] if deck_names else deck_2_name,
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
            query, deck_1_name, deck_2_name, tool_used, comparison_table, deck_names
        )
    
    return final_response
