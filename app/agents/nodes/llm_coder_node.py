"""
Node para gerar código Python no modo LLM Only.
Recebe instruções do LLM + contexto do manual e gera código baseado nas instruções.
"""
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from app.agents.state import AgentState
from app.config import OPENAI_API_KEY, OPENAI_MODEL, safe_print


LLM_CODER_SYSTEM_PROMPT = """Você é um especialista em programação Python e na biblioteca inewave para análise de decks NEWAVE.

Sua tarefa é gerar código Python que siga EXATAMENTE as instruções fornecidas, usando a biblioteca inewave e o contexto do manual como referência.

INSTRUÇÕES DETALHADAS (SIGA ESTAS INSTRUÇÕES):
{llm_instructions}

CONTEXTO DO MANUAL (use como referência para sintaxe e exemplos):
{relevant_docs}

REGRAS CRÍTICAS DE IMPORTS:
- SEMPRE use "from inewave.newave import Classe" (NÃO "from inewave import Classe")
- Exemplo CORRETO: "from inewave.newave import Vazoes, Sistema"
- Exemplo ERRADO: "from inewave import Vazoes"  # ❌ NUNCA faça isso
- Todas as classes NEWAVE estão em inewave.newave, não diretamente em inewave
- Use APENAS imports de: inewave.newave, pandas, numpy, datetime, os, json

REGRAS CRÍTICAS:
{deck_path_instruction}
- O código deve ser EXECUTÁVEL diretamente
- NÃO use input() ou qualquer interação com usuário
{deck_path_restriction}
- SIGA AS INSTRUÇÕES ACIMA EXATAMENTE

REGRAS DE FORMATAÇÃO DO OUTPUT:
- Para DataFrames, use print(df.to_string()) para mostrar a tabela completa
- Para dados grandes, limite a 50 linhas: print(df.head(50).to_string())
- Adicione separadores visuais: print("=" * 60)
- Use títulos descritivos: print("\\n### NOME DA ANÁLISE ###\\n")
- Para dados numéricos, formate adequadamente: f"{{valor:,.2f}}"

REGRAS DE OUTPUT ESTRUTURADO:
- Ao final, sempre adicione uma seção com os dados em formato JSON para download:
  print("\\n---JSON_DATA_START---")
  print(json.dumps(dados_dict, indent=2, default=str))
  print("---JSON_DATA_END---")

REGRAS CRÍTICAS DE LEITURA DE ARQUIVOS:
- SEMPRE use o método .read() para carregar arquivos NEWAVE
- SEMPRE use os.path.join(deck_path, "NOME_ARQUIVO.DAT") para construir o caminho
- NUNCA use apenas Classe() sem .read() e sem o caminho do arquivo
- Exemplo CORRETO: arquivo = Vazoes.read(os.path.join(deck_path, "VAZOES.DAT"))
- Exemplo ERRADO: arquivo = Vazoes()  # ❌ NUNCA faça isso
- As instruções devem mencionar como carregar o arquivo - siga essas instruções EXATAMENTE

ESTRUTURAS ESPECIAIS DE DADOS:
- Para VAZOES.DAT: O DataFrame tem estrutura especial:
  * Linhas = meses do histórico (índice numérico 0, 1, 2, ...)
  * Colunas = postos (números 1, 2, 3, ..., 320 ou 600)
  * NÃO há colunas 'posto' ou 'ano' - essas não existem!
  * Para buscar por nome de usina: use CONFHD para mapear nome → posto, depois acesse df_vazoes[numero_posto]
  * Para filtrar por ano: calcule o índice da linha baseado no ano inicial do histórico
  * Exemplo: df_vazoes[1] retorna a série de vazões do posto 1 (todas as linhas/meses)

IMPORTANTE:
- Use os nomes EXATOS de classes, propriedades e colunas das instruções
- Se as instruções mencionarem um arquivo específico, use esse arquivo
- Se as instruções mencionarem filtros, implemente esses filtros
- Se as instruções mencionarem como carregar o arquivo, siga EXATAMENTE essas instruções
- Baseie-se nos snippets do manual para sintaxe, mas siga as instruções para lógica
"""


LLM_CODER_USER_PROMPT = """Gere o código Python seguindo EXATAMENTE as instruções fornecidas.

Instruções:
{llm_instructions}

Retorne APENAS o código Python, sem explicações adicionais ou markdown."""


LLM_CODER_RETRY_PROMPT = """O código anterior falhou com o seguinte erro:

CÓDIGO ANTERIOR:
```python
{previous_code}
```

ERRO:
{error_message}

INSTRUÇÕES ORIGINAIS:
{llm_instructions}

TENTATIVAS ANTERIORES E ERROS:
{error_history}

Por favor, corrija o código considerando:
1. O erro específico acima
2. As instruções originais (mantenha a lógica das instruções)
3. IMPORTS: SEMPRE use "from inewave.newave import Classe" (NÃO "from inewave import Classe")
4. Nomes de propriedades e colunas - use EXATAMENTE como nas instruções
5. Tipos de dados retornados (DataFrame, dict, etc)
6. Caminhos de arquivos - use os.path.join(deck_path, "ARQUIVO.DAT")
7. Carregamento de arquivos - use Classe.read(caminho), nunca apenas Classe()

Gere um novo código Python corrigido. Retorne APENAS o código Python, sem explicações."""


def llm_coder_node(state: AgentState) -> dict:
    """
    Node que gera código Python baseado em instruções do LLM + contexto do manual.
    
    Similar ao coder_node, mas recebe instruções pré-geradas pelo llm_instructions_node.
    Usado no modo "llm_only" para gerar código seguindo instruções específicas.
    """
    llm = ChatOpenAI(
        api_key=OPENAI_API_KEY,
        model=OPENAI_MODEL,
        temperature=0  # Temperatura zero para código mais determinístico
    )
    
    relevant_docs_str = "\n\n".join(state.get("relevant_docs", []))
    llm_instructions = state.get("llm_instructions", "")
    deck_path = state.get("deck_path", "")
    
    safe_print("[LLM CODER] ===== INÍCIO: llm_coder_node =====")
    safe_print(f"[LLM CODER] Instruções disponíveis: {len(llm_instructions)} caracteres")
    safe_print(f"[LLM CODER] Contexto disponível: {len(relevant_docs_str)} caracteres")
    safe_print(f"[LLM CODER] Deck path: {deck_path if deck_path else '(vazio - modo LLM)'}")
    
    if not llm_instructions:
        safe_print("[LLM CODER] ⚠️ Nenhuma instrução disponível, usando apenas contexto")
    
    # Preparar instruções sobre deck_path
    if deck_path:
        deck_path_instruction = f"- O deck NEWAVE está no diretório: {deck_path}"
        deck_path_restriction = "- NÃO acesse a internet ou arquivos fora do deck_path"
    else:
        deck_path_instruction = "- NÃO há deck NEWAVE disponível - gere código que demonstre conceitos ou use exemplos genéricos"
        deck_path_restriction = "- NÃO acesse arquivos locais - use apenas dados de exemplo ou conceitos"
    
    # Verificar se é um retry
    retry_count = state.get("retry_count", 0)
    error_history = state.get("error_history", [])
    code_history = state.get("code_history", [])
    
    if retry_count > 0 and error_history:
        # Modo retry - usar prompt de correção
        safe_print(f"[LLM CODER] Modo retry (tentativa {retry_count + 1})")
        
        error_history_str = "\n".join([
            f"Tentativa {i+1}: {err}" 
            for i, err in enumerate(error_history)
        ])
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", LLM_CODER_SYSTEM_PROMPT),
            ("human", LLM_CODER_RETRY_PROMPT)
        ])
        
        previous_code = code_history[-1] if code_history else ""
        last_error = error_history[-1] if error_history else ""
        
        response = prompt | llm
        result = response.invoke({
            "llm_instructions": llm_instructions,
            "relevant_docs": relevant_docs_str,
            "deck_path_instruction": deck_path_instruction,
            "deck_path_restriction": deck_path_restriction,
            "previous_code": previous_code,
            "error_message": last_error,
            "error_history": error_history_str
        })
    else:
        # Primeira tentativa
        safe_print("[LLM CODER] Primeira tentativa de geração de código")
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", LLM_CODER_SYSTEM_PROMPT),
            ("human", LLM_CODER_USER_PROMPT)
        ])
        
        chain = prompt | llm
        
        result = chain.invoke({
            "llm_instructions": llm_instructions,
            "relevant_docs": relevant_docs_str,
            "deck_path_instruction": deck_path_instruction,
            "deck_path_restriction": deck_path_restriction
        })
    
    code = result.content.strip()
    
    # Limpar markdown se presente
    if code.startswith("```python"):
        code = code[9:]
    if code.startswith("```"):
        code = code[3:]
    if code.endswith("```"):
        code = code[:-3]
    
    code = code.strip()
    
    safe_print(f"[LLM CODER] Código gerado: {len(code)} caracteres")
    safe_print(f"[LLM CODER] Preview: {code[:200]}...")
    safe_print("[LLM CODER] ===== FIM: llm_coder_node =====")
    
    # Atualizar histórico de código
    new_code_history = list(code_history) + [code]
    
    return {
        "generated_code": code,
        "code_history": new_code_history
    }

