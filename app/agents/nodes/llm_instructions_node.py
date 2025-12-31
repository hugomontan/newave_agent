"""
Node para gerar instruções detalhadas no modo LLM Only.
Recebe query + contexto RAG e gera instruções específicas de como responder.
"""
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from app.agents.state import AgentState
from app.config import OPENAI_API_KEY, OPENAI_MODEL, safe_print


LLM_INSTRUCTIONS_SYSTEM_PROMPT = """Você é um especialista em análise de dados NEWAVE e na biblioteca inewave.

Sua tarefa é analisar a pergunta do usuário e o contexto do manual disponível, e gerar instruções detalhadas e específicas de como responder a pergunta usando código Python.

CONTEXTO DO MANUAL (snippets de código e exemplos):
{context}

PERGUNTA DO USUÁRIO:
{query}

Gere instruções detalhadas e específicas que incluam:

1. **Arquivo NEWAVE**: Qual arquivo deve ser lido (ex: SISTEMA.DAT, CLAST.DAT, MODIF.DAT)
2. **Classe inewave**: Qual classe usar (ex: Sistema, Clast, Modif)
3. **Como carregar o arquivo**: SEMPRE inclua instruções explícitas sobre como carregar o arquivo usando o método .read()
   - Se houver deck_path disponível: use "Classe.read(os.path.join(deck_path, 'NOME_ARQUIVO.DAT'))"
   - Exemplo: "Sistema.read(os.path.join(deck_path, 'SISTEMA.DAT'))"
   - NUNCA use apenas "Classe()" sem .read() e sem o caminho do arquivo
4. **Propriedades/Métodos**: Quais propriedades ou métodos acessar (ex: sistema.mercado_energia, clast.usinas)
5. **Filtros**: Como filtrar os dados se necessário (ex: por submercado, por ano, por usina)
6. **Processamento**: Como processar os dados (ex: converter para dict, calcular estatísticas)
7. **Formato de saída**: Qual formato esperado (ex: lista de dicionários, tabela, valores numéricos)

REGRAS CRÍTICAS DE IMPORTS:
- SEMPRE use "from inewave.newave import Classe" (NÃO "from inewave import Classe")
- Exemplo CORRETO: "from inewave.newave import Vazoes, Sistema"
- Exemplo ERRADO: "from inewave import Vazoes"  # ❌ NUNCA faça isso
- Todas as classes NEWAVE estão em inewave.newave, não diretamente em inewave
- SEMPRE inclua nas instruções o import correto: "from inewave.newave import [Classe]"

IMPORTANTE:
- Use EXATAMENTE os nomes de classes, propriedades e colunas mostrados no contexto
- Seja específico sobre os nomes exatos (case-sensitive)
- Baseie-se nos snippets de código do contexto
- Se o contexto mostrar um exemplo completo, use-o como referência
- Seja claro sobre qual snippet do manual usar
- SEMPRE inclua o passo de carregamento do arquivo usando .read() e os.path.join(deck_path, "ARQUIVO.DAT")
- SEMPRE inclua o import correto: "from inewave.newave import [Classe]"

Formate as instruções de forma clara e estruturada."""


LLM_INSTRUCTIONS_USER_PROMPT = """Com base no contexto do manual e na pergunta do usuário, gere instruções detalhadas de como responder.

Pergunta: {query}
{deck_path_info}

Gere as instruções seguindo o formato:
1. Arquivo: [nome do arquivo]
2. Classe: [nome da classe inewave]
3. Import: [SEMPRE use "from inewave.newave import [Classe]" - NÃO "from inewave import [Classe]"]
4. Como carregar: [instruções explícitas de como carregar usando Classe.read(os.path.join(deck_path, "NOME_ARQUIVO.DAT"))]
5. Propriedade/Método: [propriedade ou método a acessar]
6. Filtros: [como filtrar, se necessário]
7. Processamento: [como processar os dados]
8. Saída: [formato esperado]

Seja específico e use os nomes exatos do contexto. SEMPRE inclua o import correto e o passo de carregamento do arquivo."""


def llm_instructions_node(state: AgentState) -> dict:
    """
    Node que gera instruções detalhadas baseadas em query + contexto RAG.
    
    Usado no modo "llm_only" para criar um passo intermediário que gera
    instruções específicas antes de gerar o código.
    """
    query = state.get("query", "")
    relevant_docs = state.get("relevant_docs", [])
    deck_path = state.get("deck_path", "")
    
    safe_print("[LLM INSTRUCTIONS] ===== INÍCIO: llm_instructions_node =====")
    safe_print(f"[LLM INSTRUCTIONS] Query: {query[:100]}")
    safe_print(f"[LLM INSTRUCTIONS] Contexto disponível: {len(relevant_docs)} documento(s)")
    safe_print(f"[LLM INSTRUCTIONS] Deck path: {deck_path if deck_path else '(vazio - modo LLM sem deck)'}")
    
    try:
        # Combinar contexto de todos os documentos
        context = "\n\n".join(relevant_docs) if relevant_docs else "Nenhum contexto disponível."
        
        # Limitar tamanho do contexto para não exceder limites do modelo
        max_context_length = 15000  # Aproximadamente 3750 tokens
        if len(context) > max_context_length:
            context = context[:max_context_length] + "\n\n[... contexto truncado ...]"
            safe_print(f"[LLM INSTRUCTIONS] Contexto truncado para {max_context_length} caracteres")
        
        # Criar LLM
        llm = ChatOpenAI(
            api_key=OPENAI_API_KEY,
            model=OPENAI_MODEL,
            temperature=0.2  # Baixa temperatura para instruções mais consistentes
        )
        
        # Criar prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", LLM_INSTRUCTIONS_SYSTEM_PROMPT),
            ("human", LLM_INSTRUCTIONS_USER_PROMPT)
        ])
        
        # Preparar informação sobre deck_path
        if deck_path:
            deck_path_info = f"\n\nIMPORTANTE: O deck NEWAVE está disponível no caminho: {deck_path}\nSEMPRE inclua nas instruções como carregar o arquivo usando: Classe.read(os.path.join(deck_path, 'NOME_ARQUIVO.DAT'))"
        else:
            deck_path_info = "\n\nIMPORTANTE: Não há deck NEWAVE disponível. Gere instruções para código conceitual ou use exemplos genéricos."
        
        # Gerar instruções
        chain = prompt | llm
        response = chain.invoke({
            "context": context,
            "query": query,
            "deck_path_info": deck_path_info
        })
        
        instructions = getattr(response, 'content', 'Não foi possível gerar instruções.')
        
        safe_print(f"[LLM INSTRUCTIONS] Instruções geradas: {len(instructions)} caracteres")
        safe_print(f"[LLM INSTRUCTIONS] Preview: {instructions[:200]}...")
        safe_print("[LLM INSTRUCTIONS] ===== FIM: llm_instructions_node =====")
        
        return {
            "llm_instructions": instructions
        }
        
    except Exception as e:
        safe_print(f"[LLM INSTRUCTIONS] Erro ao gerar instruções: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            "llm_instructions": f"Erro ao gerar instruções: {str(e)}"
        }

