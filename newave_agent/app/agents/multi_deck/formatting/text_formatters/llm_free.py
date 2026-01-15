"""
Formatadores de comparação que usam LLM com prompt livre.
Suporta N decks para comparação dinâmica.
"""

from typing import Dict, Any, List, Optional
import json
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from newave_agent.app.config import OPENAI_API_KEY, OPENAI_MODEL, safe_print
from newave_agent.app.utils.text_utils import clean_response_text
from .summarizers import summarize_deck_data, summarize_multiple_decks
from newave_agent.app.agents.multi_deck.nodes.helpers.prompts import (
    COMPARISON_LLM_FREE_SYSTEM_PROMPT,
    COMPARISON_LLM_FREE_USER_PROMPT
)


def format_with_llm_free(
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
    Formata resposta usando LLM com prompt livre (para diff_list e llm_free).
    Dá mais liberdade para o LLM interpretar os dados.
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
        deck_1_summary = decks_summary
        deck_2_summary = ""
    else:
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
            
            last_deck = deck_names[-1] if deck_names else deck_2_name
            first_deck = deck_names[0] if deck_names else deck_1_name
            
            if is_historical_analysis:
                context_info = f"Diferenças identificadas ao longo de {n_decks} decks ({first_deck} a {last_deck}):\n"
            else:
                context_info = f"Diferenças identificadas:\n"
            
            context_info += f"- Adicionado em {last_deck}: {len(added)} item(s)\n"
            context_info += f"- Removido de {first_deck}: {len(removed)} item(s)\n"
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
            if is_historical_analysis:
                context_info = f"Diferenças por tipo de modificação (análise de {n_decks} decks):\n"
            else:
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
    
    # Adaptar prompt para análise histórica se necessário
    first_deck = deck_names[0] if deck_names else deck_1_name
    last_deck = deck_names[-1] if deck_names else deck_2_name
    
    if is_historical_analysis:
        system_prompt = COMPARISON_LLM_FREE_SYSTEM_PROMPT.format(
            deck_1_name=first_deck,
            deck_2_name=last_deck,
            query=query
        )
        system_prompt = system_prompt.replace(
            "comparação entre dois decks",
            f"análise histórica de {n_decks} decks"
        )
    else:
        system_prompt = COMPARISON_LLM_FREE_SYSTEM_PROMPT.format(
            deck_1_name=first_deck,
            deck_2_name=last_deck,
            query=query
        )
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", COMPARISON_LLM_FREE_USER_PROMPT)
    ])
    
    chain = prompt | llm
    
    response = chain.invoke({
        "deck_1_name": first_deck,
        "deck_2_name": last_deck,
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
        if is_historical_analysis:
            final_response = f"## Análise Histórica\n\nDados analisados de {n_decks} decks ({first_deck} a {last_deck}).\n\nConsulte os dados detalhados para análise completa."
        else:
            final_response = f"## Análise Comparativa\n\nDados comparados entre {first_deck} e {last_deck}.\n\nConsulte os dados detalhados para análise completa."
    
    return final_response
