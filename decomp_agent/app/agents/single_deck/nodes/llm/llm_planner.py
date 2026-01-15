"""
LLM Planner Node para modo LLM DECOMP.
Especialista em idecomp que analisa query + contexto RAG e cria instruções detalhadas para o Coder.
Para Single Deck Agent DECOMP.
"""
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from decomp_agent.app.config import OPENAI_API_KEY, OPENAI_MODEL, safe_print
from decomp_agent.app.agents.single_deck.state import SingleDeckState


LLM_PLANNER_SYSTEM_PROMPT = """Você é um especialista em análise de dados DECOMP e na biblioteca idecomp.

Sua tarefa é analisar a query do usuário e o contexto fornecido (documentação DECOMP + documentação das tools) 
e criar instruções detalhadas e específicas para o Coder Node gerar código Python que acessa os arquivos DECOMP.

CONTEXTO DA DOCUMENTAÇÃO:
{relevant_docs}

QUERY DO USUÁRIO:
{query}

=====================================================================
INSTRUÇÕES PARA GERAR O DOCUMENTO DE INSTRUÇÕES:
=====================================================================

1. **IDENTIFIQUE ARQUIVOS NECESSÁRIOS**
   - Liste quais arquivos DECOMP são necessários para responder a query
   - Exemplo: "Para esta query, você precisa acessar dadger.rvx"

2. **IDENTIFIQUE CLASSES IDECOMP**
   - Liste quais classes idecomp usar (ex: Dadger)
   - Exemplo: "Use a classe Dadger para ler dadger.rvx: `from idecomp.decomp import Dadger`"

3. **IDENTIFIQUE MÉTODOS E PROPRIEDADES**
   - Liste quais métodos acessar (ex: dadger.uh(), dadger.ct())
   - Liste quais colunas são relevantes
   - Exemplo: "Use dadger.uh(df=True) para obter DataFrame de usinas hidrelétricas"

4. **FORNEÇA EXEMPLOS DE CÓDIGO**
   - Baseie-se nos exemplos fornecidos na documentação
   - Forneça código Python completo e funcional

5. **EXPLIQUE PADRÕES E BOAS PRÁTICAS**
   - Mencione filtros necessários
   - Mencione agregações necessárias
   - Mencione tratamento de dados

6. **SEJA ESPECÍFICO**
   - Não seja genérico - seja específico sobre arquivos, classes, métodos e colunas
   - Mencione valores exatos quando relevante

=====================================================================
FORMATO DO DOCUMENTO DE INSTRUÇÕES:
=====================================================================

Gere um documento de instruções estruturado que o Coder Node possa usar diretamente.
O documento deve ser claro, específico e acionável.

Estrutura sugerida:
- Arquivos DECOMP necessários
- Classes idecomp a usar
- Métodos e colunas relevantes
- Exemplos de código
- Padrões e boas práticas
- Filtros e processamento específico

Seja detalhado e específico. O Coder Node usará estas instruções para gerar código Python.
"""

LLM_PLANNER_USER_PROMPT = """Analise a query do usuário e o contexto fornecido.

Crie um documento de instruções detalhado que o Coder Node possa usar para gerar código Python 
que acessa os arquivos DECOMP e responde à query do usuário.

Siga a estrutura e diretrizes fornecidas no prompt do sistema.

Responda APENAS com o documento de instruções, sem explicações adicionais ou markdown de formatação.
O documento deve ser texto puro que será incluído diretamente no prompt do Coder.
"""


def llm_planner_node(state: SingleDeckState) -> dict:
    """
    Node que atua como especialista idecomp.
    Analisa query + contexto RAG e gera instruções detalhadas para o Coder.
    
    Args:
        state: Estado do Single Deck Agent DECOMP
        
    Returns:
        Dict com:
        - llm_instructions: String com instruções detalhadas para o Coder
    """
    query = state["query"]
    relevant_docs = state.get("relevant_docs", [])
    
    safe_print("[LLM PLANNER DECOMP] ===== INÍCIO: llm_planner_node =====")
    safe_print(f"[LLM PLANNER DECOMP] Query: {query[:100]}")
    safe_print(f"[LLM PLANNER DECOMP] Contexto RAG: {len(relevant_docs)} documentos")
    
    try:
        # Combinar documentos relevantes
        relevant_docs_str = "\n\n".join(relevant_docs) if relevant_docs else ""
        
        if not relevant_docs_str:
            safe_print("[LLM PLANNER DECOMP] ⚠️ Nenhum contexto RAG disponível")
            relevant_docs_str = "Nenhuma documentação disponível. Use a biblioteca idecomp para acessar arquivos DECOMP."
        
        # Criar LLM
        llm = ChatOpenAI(
            api_key=OPENAI_API_KEY,
            model=OPENAI_MODEL,
            temperature=0.3
        )
        
        # Criar prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", LLM_PLANNER_SYSTEM_PROMPT),
            ("human", LLM_PLANNER_USER_PROMPT)
        ])
        
        # Invocar LLM
        safe_print("[LLM PLANNER DECOMP] Gerando instruções detalhadas...")
        chain = prompt | llm
        result = chain.invoke({
            "query": query,
            "relevant_docs": relevant_docs_str
        })
        
        llm_instructions = result.content.strip()
        
        safe_print(f"[LLM PLANNER DECOMP] ✅ Instruções geradas ({len(llm_instructions)} caracteres)")
        safe_print("[LLM PLANNER DECOMP] ===== FIM: llm_planner_node =====")
        
        return {
            "llm_instructions": llm_instructions
        }
        
    except Exception as e:
        safe_print(f"[LLM PLANNER DECOMP] ❌ Erro ao gerar instruções: {e}")
        import traceback
        traceback.print_exc()
        return {
            "llm_instructions": f"Erro ao gerar instruções detalhadas. Use a biblioteca idecomp para acessar arquivos DECOMP e responder à query: {query}"
        }
