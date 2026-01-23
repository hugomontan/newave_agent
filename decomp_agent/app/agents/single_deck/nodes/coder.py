"""
Node que gera código Python para buscar dados do deck DECOMP.
Para Single Deck Agent DECOMP.
"""
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from decomp_agent.app.agents.single_deck.state import SingleDeckState
from decomp_agent.app.config import OPENAI_API_KEY, OPENAI_MODEL


CODER_SYSTEM_PROMPT = """Você é um especialista em programação Python e na biblioteca idecomp para análise de decks DECOMP.

Sua tarefa é gerar código Python que:
1. Use a biblioteca idecomp para ler os arquivos do deck DECOMP
2. Extraia os dados solicitados pelo usuário
3. Retorne os dados em formato estruturado

REGRAS CRÍTICAS:
- Use APENAS imports de: idecomp, pandas, numpy, datetime, os, json
- O deck DECOMP está no diretório: {deck_path}
- O código deve ser EXECUTÁVEL diretamente
- NÃO use input() ou qualquer interação com usuário
- NÃO acesse a internet ou arquivos fora do deck_path

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

DOCUMENTAÇÃO DISPONÍVEL (USE ESTES CAMPOS E PROPRIEDADES EXATAMENTE COMO DESCRITO):
{relevant_docs}

IMPORTANTE - LEIA A DOCUMENTAÇÃO ACIMA COM ATENÇÃO:
- Use EXATAMENTE os nomes de propriedades e campos mostrados na documentação
- A documentação mostra quais colunas existem nos DataFrames retornados
- Se a documentação mostrar que uma propriedade retorna um DataFrame, verifique as colunas disponíveis antes de filtrar

EXEMPLO DE ESTRUTURA:
```python
import os
import json
import pandas as pd
from idecomp.decomp import Dadger

deck_path = "{deck_path}"

try:
    dadger = Dadger.read(os.path.join(deck_path, "dadger.rvx"))
    df = dadger.uh(df=True)  # Usinas hidrelétricas
    
    print("\\n" + "=" * 60)
    print("### ANÁLISE DE DADOS ###")
    print("=" * 60 + "\\n")
    
    if isinstance(df, pd.DataFrame):
        print(df.head(50).to_string())
        print("\\n---JSON_DATA_START---")
        print(json.dumps(df.head(100).to_dict(orient='records'), indent=2, default=str))
        print("---JSON_DATA_END---")
    else:
        print(df)
        
except Exception as e:
    print(f"Erro: {{e}}")
```
"""

CODER_USER_PROMPT = """Pergunta do usuário: {query}

Gere o código Python para responder esta pergunta usando a biblioteca idecomp.
Retorne APENAS o código Python, sem explicações adicionais ou markdown."""


CODER_RETRY_PROMPT = """O código anterior falhou com o seguinte erro:

CÓDIGO ANTERIOR:
```python
{previous_code}
```

ERRO:
{error_message}

TENTATIVAS ANTERIORES E ERROS:
{error_history}

Por favor, corrija o código considerando o erro. Preste atenção especial a:
1. Nomes de propriedades e colunas - use EXATAMENTE como na documentação
2. Tipos de dados retornados (DataFrame, dict, etc)
3. Caminhos de arquivos
4. Imports necessários

Gere um novo código Python corrigido. Retorne APENAS o código Python, sem explicações."""


def coder_node(state: SingleDeckState) -> dict:
    """
    Node que gera código Python para buscar dados do deck DECOMP.
    Suporta retry em caso de erro.
    
    Args:
        state: Estado do Single Deck Agent DECOMP
        
    Returns:
        Dict com generated_code e code_history
    """
    llm = ChatOpenAI(
        api_key=OPENAI_API_KEY,
        model=OPENAI_MODEL,
        temperature=0
    )
    
    # Usar apenas relevant_docs
    relevant_docs = state.get("relevant_docs", [])
    relevant_docs_str = "\n\n".join(relevant_docs)
    
    # Verificar se é um retry
    retry_count = state.get("retry_count", 0)
    error_history = state.get("error_history", [])
    code_history = state.get("code_history", [])
    
    if retry_count > 0 and error_history:
        # Modo retry - usar prompt de correção
        error_history_str = "\n".join([
            f"Tentativa {i+1}: {err}" 
            for i, err in enumerate(error_history)
        ])
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", CODER_SYSTEM_PROMPT),
            ("human", CODER_RETRY_PROMPT)
        ])
        
        previous_code = code_history[-1] if code_history else ""
        last_error = error_history[-1] if error_history else ""
        
        response = prompt | llm
        result = response.invoke({
            "query": state["query"],
            "deck_path": state["deck_path"],
            "relevant_docs": relevant_docs_str,
            "previous_code": previous_code,
            "error_message": last_error,
            "error_history": error_history_str
        })
    else:
        # Primeira tentativa
        prompt = ChatPromptTemplate.from_messages([
            ("system", CODER_SYSTEM_PROMPT),
            ("human", CODER_USER_PROMPT)
        ])
        
        chain = prompt | llm
        
        result = chain.invoke({
            "query": state["query"],
            "deck_path": state["deck_path"],
            "relevant_docs": relevant_docs_str
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
    
    # Atualizar histórico de código
    new_code_history = list(code_history) + [code]
    
    return {
        "generated_code": code,
        "code_history": new_code_history
    }
