"""
Formatadores de comparação que usam LLM com prompt estruturado.
"""

from typing import Dict, Any
import json
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from app.config import OPENAI_API_KEY, OPENAI_MODEL, safe_print
from app.utils.text_utils import clean_response_text
from .summarizers import summarize_deck_data
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
        # Verificar se é formato de CVU (campos: data, deck_1, deck_2, diferenca, diferenca_percent)
        first_item = comparison_table[0] if comparison_table else {}
        is_cvu_format = "data" in first_item and "deck_1" in first_item and "deck_2" in first_item and "diferenca" in first_item
        
        if is_cvu_format:
            # Formato específico para CVU - instruir explicitamente como formatar
            differences_summary = f"TABELA COMPARATIVA DE CVU com {len(comparison_table)} anos:\n\n"
            differences_summary += "FORMATO OBRIGATORIO DA TABELA:\n"
            differences_summary += f"| Data | {deck_1_name} | {deck_2_name} | Diferenca |\n"
            differences_summary += "|------|---------------|---------------|----------|\n"
            
            for item in comparison_table:
                data = item.get("data", "")
                val1 = item.get("deck_1")
                val2 = item.get("deck_2")
                diff = item.get("diferenca")
                diff_pct = item.get("diferenca_percent")
                
                # Formatar valores
                val1_str = f"{val1:.2f}" if val1 is not None else "-"
                val2_str = f"{val2:.2f}" if val2 is not None else "-"
                
                # Formatar diferença (nominal + percentual)
                if diff is not None:
                    if diff_pct is not None:
                        diff_str = f"{diff:.2f} ({diff_pct:.2f}%)"
                    else:
                        diff_str = f"{diff:.2f}"
                else:
                    diff_str = "-"
                
                differences_summary += f"| {data} | {val1_str} | {val2_str} | {diff_str} |\n"
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
