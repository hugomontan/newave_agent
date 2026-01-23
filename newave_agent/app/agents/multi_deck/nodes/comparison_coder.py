"""
Node que gera código Python para buscar dados de DOIS decks NEWAVE e compará-los.
Para Multi-Deck Agent.
"""
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from newave_agent.app.agents.multi_deck.state import MultiDeckState
from newave_agent.app.config import OPENAI_API_KEY, OPENAI_MODEL


CODER_SYSTEM_PROMPT = """Você é um especialista em programação Python e na biblioteca inewave para análise de decks NEWAVE.

Sua tarefa é gerar código Python que:
1. Use a biblioteca inewave para ler os arquivos de DOIS decks NEWAVE
2. Extraia os dados solicitados pelo usuário de AMBOS os decks
3. Compare os dados entre os dois decks
4. Retorne os dados em formato estruturado para comparação

REGRAS CRÍTICAS:
- Use APENAS imports de: inewave, pandas, numpy, datetime, os, json
- Você tem DOIS decks NEWAVE:
  - Deck 1 (Dezembro 2025): {deck_december_path}
  - Deck 2 (Janeiro 2026): {deck_january_path}
- O código deve ser EXECUTÁVEL diretamente
- NÃO use input() ou qualquer interação com usuário
- NÃO acesse a internet ou arquivos fora dos deck_paths

REGRAS DE FORMATAÇÃO DO OUTPUT:
- Para DataFrames, use print(df.to_string()) para mostrar a tabela completa
- Para dados grandes, limite a 50 linhas: print(df.head(50).to_string())
- Adicione separadores visuais: print("=" * 60)
- Use títulos descritivos: print("\\n### NOME DA ANÁLISE ###\\n")
- Para dados numéricos, formate adequadamente: f"{{valor:,.2f}}"
- SEMPRE identifique de qual deck cada dado vem (Dezembro 2025 ou Janeiro 2026)

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

EXEMPLO DE ESTRUTURA PARA COMPARAÇÃO:
```python
import os
import json
import pandas as pd
from inewave.newave import NomeClasse

deck_december_path = "{deck_december_path}"
deck_january_path = "{deck_january_path}"

try:
    # Ler dados do Deck 1 (Dezembro 2025)
    arquivo_dec = NomeClasse.read(os.path.join(deck_december_path, "nome_arquivo.dat"))
    df_dec = arquivo_dec.propriedade
    
    # Ler dados do Deck 2 (Janeiro 2026)
    arquivo_jan = NomeClasse.read(os.path.join(deck_january_path, "nome_arquivo.dat"))
    df_jan = arquivo_jan.propriedade
    
    print("\\n" + "=" * 60)
    print("### COMPARAÇÃO ENTRE DECKS ###")
    print("=" * 60 + "\\n")
    
    print("### DECK 1 - DEZEMBRO 2025 ###")
    if isinstance(df_dec, pd.DataFrame):
        print(df_dec.head(50).to_string())
    else:
        print(df_dec)
    
    print("\\n### DECK 2 - JANEIRO 2026 ###")
    if isinstance(df_jan, pd.DataFrame):
        print(df_jan.head(50).to_string())
    else:
        print(df_jan)
    
    # Comparação (opcional - pode calcular diferenças se necessário)
    if isinstance(df_dec, pd.DataFrame) and isinstance(df_jan, pd.DataFrame):
        # Exemplo: calcular diferenças se aplicável
        # diff = df_jan - df_dec  # Ajustar conforme necessário
        # print("\\n### DIFERENÇAS ###")
        # print(diff.head(50).to_string())
        pass
    
    print("\\n---JSON_DATA_START---")
    comparison_data = {
        "deck_1": df_dec.head(100).to_dict(orient='records') if isinstance(df_dec, pd.DataFrame) else str(df_dec),
        "deck_2": df_jan.head(100).to_dict(orient='records') if isinstance(df_jan, pd.DataFrame) else str(df_jan)
    }
    print(json.dumps(comparison_data, indent=2, default=str))
    print("---JSON_DATA_END---")
        
except Exception as e:
    print(f"Erro: {{e}}")
```
"""

CODER_USER_PROMPT = """Pergunta do usuário: {query}

Gere o código Python para responder esta pergunta comparando os dados entre os dois decks NEWAVE.
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
3. Caminhos de arquivos - você tem DOIS decks: {deck_december_path} e {deck_january_path}
4. Imports necessários
5. Garantir que processa AMBOS os decks

Gere um novo código Python corrigido. Retorne APENAS o código Python, sem explicações."""


def comparison_coder_node(state: MultiDeckState) -> dict:
    """
    Node que gera código Python para buscar dados de DOIS decks NEWAVE e compará-los.
    Suporta retry em caso de erro.
    
    Args:
        state: Estado do Multi-Deck Agent
        
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
    
    # Obter caminhos dos decks
    deck_december_path = state.get("deck_december_path", "")
    deck_january_path = state.get("deck_january_path", "")
    
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
            "deck_december_path": deck_december_path,
            "deck_january_path": deck_january_path,
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
            "deck_december_path": deck_december_path,
            "deck_january_path": deck_january_path,
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
