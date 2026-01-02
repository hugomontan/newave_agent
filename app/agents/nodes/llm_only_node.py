"""
Node para modo LLM Only: gera resposta direta usando apenas LLM e RAG,
sem executar código ou tools.
"""
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from app.agents.state import AgentState
from app.config import OPENAI_API_KEY, OPENAI_MODEL, safe_print


LLM_ONLY_SYSTEM_PROMPT = """Você é um assistente especializado em análise de sistemas de energia elétrica e modelos NEWAVE.

Você recebe contexto de documentação sobre arquivos NEWAVE e ferramentas disponíveis. Sua função é responder perguntas do usuário de forma clara e precisa, usando apenas o conhecimento fornecido no contexto.

INSTRUÇÕES:
- Use APENAS o contexto fornecido para responder
- Se a pergunta não pode ser respondida com o contexto, explique isso de forma educada
- Seja claro e objetivo
- Se mencionar arquivos ou ferramentas, use os nomes exatos do contexto
- Não invente informações que não estão no contexto
- Se a pergunta for sobre como fazer algo, forneça instruções baseadas no contexto

CONTEXTO DISPONÍVEL:
{context}

PERGUNTA DO USUÁRIO:
{query}

Responda de forma clara e útil, usando o contexto fornecido."""


def llm_only_node(state: AgentState) -> dict:
    """
    Node que gera resposta usando apenas LLM e contexto RAG, sem executar código.
    
    Usado no modo "llm_only" para responder perguntas gerais sobre NEWAVE
    sem necessidade de acessar dados de decks específicos.
    """
    query = state.get("query", "")
    relevant_docs = state.get("relevant_docs", [])
    
    safe_print("[LLM ONLY] ===== INÍCIO: llm_only_node =====")
    safe_print(f"[LLM ONLY] Query: {query[:100]}")
    safe_print(f"[LLM ONLY] Contexto disponível: {len(relevant_docs)} documento(s)")
    
    try:
        # Combinar contexto de todos os documentos
        context = "\n\n".join(relevant_docs) if relevant_docs else "Nenhum contexto disponível."
        
        # Limitar tamanho do contexto para não exceder limites do modelo
        max_context_length = 15000  # Aproximadamente 3750 tokens
        if len(context) > max_context_length:
            context = context[:max_context_length] + "\n\n[... contexto truncado ...]"
            safe_print(f"[LLM ONLY] Contexto truncado para {max_context_length} caracteres")
        
        # Criar LLM
        llm = ChatOpenAI(
            api_key=OPENAI_API_KEY,
            model=OPENAI_MODEL,
            temperature=0.3
        )
        
        # Criar prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", LLM_ONLY_SYSTEM_PROMPT),
            ("human", "{query}")
        ])
        
        # Gerar resposta
        chain = prompt | llm
        response = chain.invoke({
            "context": context,
            "query": query
        })
        
        final_response = getattr(response, 'content', 'Não foi possível gerar uma resposta.')
        
        safe_print(f"[LLM ONLY] Resposta gerada: {len(final_response)} caracteres")
        safe_print("[LLM ONLY] ===== FIM: llm_only_node =====")
        
        return {
            "final_response": final_response
        }
        
    except Exception as e:
        safe_print(f"[LLM ONLY] Erro ao gerar resposta: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            "final_response": f"Desculpe, ocorreu um erro ao processar sua pergunta: {str(e)}"
        }

