"""
Formatadores de comparação que usam LLM com prompt livre.
"""

from typing import Dict, Any
import json
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from app.config import OPENAI_API_KEY, OPENAI_MODEL, safe_print
from app.utils.text_utils import clean_response_text
from .summarizers import summarize_deck_data
from app.agents.multi_deck.nodes.helpers.prompts import (
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
