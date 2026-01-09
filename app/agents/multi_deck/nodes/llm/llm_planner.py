"""
LLM Planner Node para modo LLM.
Especialista em inewave que analisa query + contexto RAG e cria instruções detalhadas para o Coder.
Para Single Deck Agent.
"""
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from app.config import OPENAI_API_KEY, OPENAI_MODEL, safe_print
from app.agents.multi_deck.state import MultiDeckState


LLM_PLANNER_SYSTEM_PROMPT = """Você é um especialista em análise de dados NEWAVE e na biblioteca inewave.

Sua tarefa é analisar a query do usuário e o contexto fornecido (documentação NEWAVE + documentação das tools) 
e criar instruções detalhadas e específicas para o Coder Node gerar código Python que acessa os arquivos NEWAVE.

CONTEXTO DA DOCUMENTAÇÃO:
{relevant_docs}

QUERY DO USUÁRIO:
{query}

=====================================================================
INSTRUÇÕES PARA GERAR O DOCUMENTO DE INSTRUÇÕES:
=====================================================================

1. **IDENTIFIQUE ARQUIVOS NECESSÁRIOS**
   - Liste quais arquivos NEWAVE são necessários para responder a query
   - Exemplo: "Para esta query, você precisa acessar CLAST.DAT e SISTEMA.DAT"

2. **IDENTIFIQUE CLASSES INEWAVE**
   - Liste quais classes inewave usar (ex: Clast, Sistema, Expt, etc.)
   - Exemplo: "Use a classe Clast para ler CLAST.DAT: `from inewave.newave import Clast`"

3. **IDENTIFIQUE PROPRIEDADES E COLUNAS**
   - Liste quais propriedades acessar (ex: clast.usinas, sistema.mercado_energia)
   - Liste quais colunas são relevantes (ex: codigo_usina, nome_usina, valor)
   - Exemplo: "Acesse clast.usinas para obter valores estruturais. As colunas relevantes são: codigo_usina, nome_usina, indice_ano_estudo, valor"

4. **FORNEÇA EXEMPLOS DE CÓDIGO**
   - Baseie-se nos exemplos fornecidos na documentação das tools
   - Forneça código Python completo e funcional
   - Exemplo: 
     ```python
     from inewave.newave import Clast
     import os
     clast_path = os.path.join(deck_path, "CLAST.DAT")
     clast = Clast.read(clast_path)
     df_estrutural = clast.usinas
     ```

5. **EXPLIQUE PADRÕES E BOAS PRÁTICAS**
   - Mencione filtros necessários
   - Mencione agregações necessárias
   - Mencione tratamento de dados (NaN, tipos, etc.)
   - Exemplo: "Filtre por codigo_usina == 211. Para CVU, sempre retorne TODOS OS ANOS (não filtre por ano)"

6. **SEJA ESPECÍFICO**
   - Não seja genérico - seja específico sobre arquivos, classes, propriedades e colunas
   - Mencione valores exatos quando relevante
   - Exemplo: "O submercado Sudeste tem código 1. Use codigo_submercado == 1 para filtrar"

=====================================================================
FORMATO DO DOCUMENTO DE INSTRUÇÕES:
=====================================================================

Gere um documento de instruções estruturado que o Coder Node possa usar diretamente.
O documento deve ser claro, específico e acionável.

Estrutura sugerida:
- Arquivos NEWAVE necessários
- Classes inewave a usar
- Propriedades e colunas relevantes
- Exemplos de código baseados nas tools
- Padrões e boas práticas
- Filtros e processamento específico

Seja detalhado e específico. O Coder Node usará estas instruções para gerar código Python.
"""

LLM_PLANNER_USER_PROMPT = """Analise a query do usuário e o contexto fornecido.

Crie um documento de instruções detalhado que o Coder Node possa usar para gerar código Python 
que acessa os arquivos NEWAVE e responde à query do usuário.

Siga a estrutura e diretrizes fornecidas no prompt do sistema.

Responda APENAS com o documento de instruções, sem explicações adicionais ou markdown de formatação.
O documento deve ser texto puro que será incluído diretamente no prompt do Coder.
"""


def llm_planner_node(state: MultiDeckState) -> dict:
    """
    Node que atua como especialista inewave.
    Analisa query + contexto RAG e gera instruções detalhadas para o Coder.
    
    Args:
        state: Estado do Multi-Deck Agent
        
    Returns:
        Dict com:
        - llm_instructions: String com instruções detalhadas para o Coder
    """
    query = state["query"]
    relevant_docs = state.get("relevant_docs", [])
    
    safe_print("[LLM PLANNER] ===== INÍCIO: llm_planner_node =====")
    safe_print(f"[LLM PLANNER] Query: {query[:100]}")
    safe_print(f"[LLM PLANNER] Contexto RAG: {len(relevant_docs)} documentos")
    
    try:
        # Combinar documentos relevantes
        relevant_docs_str = "\n\n".join(relevant_docs) if relevant_docs else ""
        
        if not relevant_docs_str:
            safe_print("[LLM PLANNER] ⚠️ Nenhum contexto RAG disponível")
            # Retornar instruções básicas mesmo sem contexto
            relevant_docs_str = "Nenhuma documentação disponível. Use a biblioteca inewave para acessar arquivos NEWAVE."
        
        # Criar LLM
        llm = ChatOpenAI(
            api_key=OPENAI_API_KEY,
            model=OPENAI_MODEL,
            temperature=0.3  # Um pouco de criatividade, mas focado
        )
        
        # Criar prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", LLM_PLANNER_SYSTEM_PROMPT),
            ("human", LLM_PLANNER_USER_PROMPT)
        ])
        
        # Invocar LLM
        safe_print("[LLM PLANNER] Gerando instruções detalhadas...")
        chain = prompt | llm
        result = chain.invoke({
            "query": query,
            "relevant_docs": relevant_docs_str
        })
        
        llm_instructions = result.content.strip()
        
        safe_print(f"[LLM PLANNER] ✅ Instruções geradas ({len(llm_instructions)} caracteres)")
        safe_print(f"[LLM PLANNER] Preview: {llm_instructions[:200]}...")
        safe_print("[LLM PLANNER] ===== FIM: llm_planner_node =====")
        
        return {
            "llm_instructions": llm_instructions
        }
        
    except Exception as e:
        safe_print(f"[LLM PLANNER] ❌ Erro ao gerar instruções: {e}")
        import traceback
        traceback.print_exc()
        # Retornar instruções básicas em caso de erro
        return {
            "llm_instructions": f"Erro ao gerar instruções detalhadas. Use a biblioteca inewave para acessar arquivos NEWAVE e responder à query: {query}"
        }
