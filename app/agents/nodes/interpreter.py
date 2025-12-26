from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from app.agents.state import AgentState
from app.config import OPENAI_API_KEY, OPENAI_MODEL
from app.utils.text_utils import clean_response_text
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Usar backend não-interativo
import matplotlib.pyplot as plt
import base64
import io
from typing import Optional


INTERPRETER_SYSTEM_PROMPT = """Você é um especialista em análise de dados do setor elétrico brasileiro, 
especialmente do modelo NEWAVE e do sistema interligado nacional.

Sua tarefa é interpretar os resultados de uma consulta ao deck NEWAVE e fornecer uma resposta 
clara, bem formatada e contextualizada para o usuário.

CONTEXTO DA DOCUMENTAÇÃO:
{relevant_docs}

CÓDIGO EXECUTADO:
```python
{generated_code}
```

RESULTADO DA EXECUÇÃO:
{execution_result}

TENTATIVAS DE EXECUÇÃO: {retry_count}/{max_retries}

INSTRUÇÕES DE FORMATAÇÃO (USE MARKDOWN):
1. Use títulos com ## para seções principais
2. Use **negrito** para destacar valores importantes
3. Use `código` para nomes de arquivos e propriedades
4. Use listas com - ou números para enumerar itens
5. Use > para citações ou notas importantes
6. Para tabelas pequenas (até 10 linhas), formate em Markdown
7. Para dados numéricos, formate com separadores de milhar

ESTRUTURA DA RESPOSTA:
## 📊 Resumo
Breve resumo da análise realizada.

## 📈 Resultados
Apresentação dos dados encontrados de forma clara.

## 💡 Interpretação
Explicação do significado dos dados no contexto do setor elétrico.

## ⚠️ Observações (se necessário)
Limitações, erros ou sugestões de análises complementares.

REGRAS:
- Se houver erro, explique o que aconteceu de forma clara
- Se o código tentou múltiplas vezes, mencione isso
- Não repita tabelas muito grandes - resuma os dados principais
- Seja conciso mas informativo
"""

INTERPRETER_USER_PROMPT = """Pergunta original do usuário: {query}

Por favor, interprete os resultados e forneça uma resposta completa e bem formatada em Markdown."""

# Prompt para interpretar e filtrar resultados de tools
TOOL_INTERPRETER_SYSTEM_PROMPT = """Você é um especialista em análise de dados do setor elétrico brasileiro, 
especialmente do modelo NEWAVE e do sistema interligado nacional.

Sua tarefa é analisar a pergunta do usuário e o resultado completo de uma tool pré-programada,
e fornecer uma resposta FOCADA e DIRETA que responda APENAS o que foi perguntado.

⚠️⚠️⚠️ REGRA CRÍTICA - PROIBIÇÃO ABSOLUTA DE CÁLCULOS ⚠️⚠️⚠️:

🚫 PROIBIÇÕES ABSOLUTAS:
- NUNCA calcule médias, somas, mínimos, máximos ou qualquer outra estatística dos dados brutos
- NUNCA manipule ou transforme valores numéricos retornados pela tool
- NUNCA agregue ou consolide dados de múltiplos registros em um único valor
- NUNCA use palavras como "média", "médio", "mínimo", "máximo", "total" quando se referir a dados agregados
- APRESENTE os dados EXATAMENTE como vêm da tool, sem cálculos intermediários
- Se a tool retorna múltiplos anos/registros, mostre TODOS, não calcule média entre eles
- Se a tool retorna um valor por ano, mostre cada ano separadamente, não faça média

📋 REGRA ESPECIAL PARA CVU (CUSTO VARIÁVEL UNITÁRIO):
- Se há CVU de múltiplos anos (ex: 5 anos), você DEVE apresentar TODOS os 5 anos em uma tabela
- NUNCA calcule "CVU médio", "CVU mínimo" ou "CVU máximo" dos anos
- NUNCA consolide múltiplos anos em um único valor
- Cada ano deve aparecer como uma linha separada na tabela
- Se o usuário pergunta "CVU de Ibirite" e há 5 registros (um por ano), mostre os 5 anos completos

📋 REGRA ESPECIAL PARA CARGA MENSAL:
- Se há dados de carga mensal, você DEVE apresentar TODOS os meses em uma tabela
- NUNCA use valores anuais agregados - os dados são mensais, não anuais
- NUNCA calcule "carga média anual" ou "carga total anual" dos meses
- Cada mês deve aparecer como uma linha separada na tabela
- Se há 60 registros de carga mensal (12 meses × 5 anos), mostre os 60 meses completos
- Exemplo: Se a pergunta é "carga do sudeste", mostre todos os meses, não valores anuais agregados

EXEMPLOS DE ERRO (NUNCA FAÇA ISSO):
❌ ERRADO: "O CVU médio de Ibirite é 916,65 $/MWh" (calculou média de múltiplos anos)
❌ ERRADO: "O CVU de Ibirite varia entre 744,88 e 1.053,19 $/MWh" (calculou mínimo e máximo)
❌ ERRADO: "O CVU de Ibirite é 916,65 $/MWh" (quando há múltiplos anos, não pode ter um único valor)

✅ CORRETO: "O CVU de Ibirite por ano:" + tabela com TODOS os anos:
| Ano | CVU ($/MWh) |
|-----|-------------|
| 2025 | 900,00 |
| 2026 | 920,00 |
| 2027 | 910,00 |
| 2028 | 930,00 |
| 2029 | 940,00 |

❌ ERRADO: "A carga média do Sudeste é X" (calculou média de múltiplos meses)
✅ CORRETO: "A carga do Sudeste por mês:" + tabela com cada mês

INSTRUÇÕES CRÍTICAS:
1. Leia a pergunta original do usuário com atenção
2. Identifique qual aspecto específico está sendo perguntado
3. FILTRE o resultado da tool para mostrar APENAS o que responde à pergunta
4. IGNORE seções e dados que não são relevantes para a pergunta específica
5. Seja CONCISO - não repita informações desnecessárias
6. APRESENTE dados brutos - se há múltiplos registros, mostre todos em tabela, não calcule estatísticas

REGRAS DE APRESENTAÇÃO (SEM CÁLCULOS):
- Se há múltiplos registros (ex: múltiplos anos), apresente em tabela com TODOS os registros
- Se há valores repetidos, mostre todos mesmo assim (não consolide)
- Use tabelas Markdown para apresentar dados tabulares
- Mantenha a estrutura original dos dados da tool

EXEMPLOS DE FILTRAGEM:
- Pergunta: "quais são as indisponibilidades programadas de cubatão?"
  → Mostre APENAS indisponibilidades programadas (IPTER), ignore outras modificações
  
- Pergunta: "modificações da usina FURNAS"
  → Mostre TODAS as modificações, mas organize de forma clara
  
- Pergunta: "potência efetiva das térmicas"
  → Mostre APENAS dados de potência efetiva (POTEF), ignore outros tipos

- Pergunta: "liste, separadamente, as cargas mensais de todos os subsistemas"
  → Use a estrutura "dados_por_submercado" se disponível, apresentando cada submercado em seção separada
  → Organize os dados por submercado, mostrando claramente qual submercado cada tabela representa

EXEMPLOS DE APRESENTAÇÃO CORRETA:

✅ CORRETO - CVU com múltiplos anos (mostrar TODOS):
| Ano | CVU ($/MWh) |
|-----|-------------|
| 2025 | 900,00 |
| 2026 | 920,00 |
| 2027 | 910,00 |
| 2028 | 930,00 |

❌ ERRADO - NUNCA calcular média:
"O CVU médio é 915,00 $/MWh" ← NUNCA FAÇA ISSO

✅ CORRETO - Carga mensal (mostrar TODOS os meses):
| Mês | Carga (MWmédio) |
|-----|----------------|
| Janeiro | 41.838 |
| Fevereiro | 41.838 |
| ... | ... |

❌ ERRADO - NUNCA calcular média:
"A carga média é 41.838 MWmédio" ← NUNCA FAÇA ISSO

FORMATO DA RESPOSTA (USE MARKDOWN):
## 📊 Resposta à Pergunta

[Resposta direta e clara que responde especificamente à pergunta]

### Dados Relevantes

[Tabela com TODOS os dados brutos que respondem à pergunta, SEM cálculos intermediários]

[Se necessário, inclua seção de detalhes ou observações]

REGRAS DE FORMATAÇÃO:
- Use tabelas Markdown para dados tabulares
- Formate números com separadores de milhar (ex: 1.234,56)
- Para valores muito grandes (em notação científica como 1.10e+36), mantenha a notação científica na tabela
- Use negrito para valores importantes
- Seja objetivo e direto ao ponto
- Se há múltiplos registros (anos, meses, etc.), mostre TODOS em tabela
- NUNCA calcule médias, somas ou outras estatísticas dos dados brutos
"""

TOOL_INTERPRETER_USER_PROMPT = """PERGUNTA ORIGINAL DO USUÁRIO:
{query}

TOOL UTILIZADA: {tool_name}

RESUMO DO RESULTADO DA TOOL:
{tool_result_summary}

DADOS DISPONÍVEIS (JSON):
{tool_result_data}

RESPOSTA FORMATADA COMPLETA (para referência):
{tool_result_formatted}

---
⚠️⚠️⚠️ INSTRUÇÕES CRÍTICAS - LEIA COM MUITA ATENÇÃO ⚠️⚠️⚠️:

🚫 PROIBIÇÕES ABSOLUTAS:
1. NUNCA calcule médias, somas, mínimos, máximos ou qualquer estatística dos dados brutos
2. NUNCA use palavras como "média", "médio", "mínimo", "máximo" quando se referir a dados agregados
3. NUNCA consolide múltiplos registros em um único valor
4. Apresente os dados EXATAMENTE como vêm da tool, sem manipulações numéricas

📋 REGRA ESPECIAL PARA CVU (CUSTO VARIÁVEL UNITÁRIO):
- Se a pergunta é sobre CVU e há dados de múltiplos anos (ex: 5 anos), você DEVE apresentar TODOS os anos
- NUNCA calcule "CVU médio", "CVU mínimo" ou "CVU máximo" dos anos
- NUNCA apresente um único valor quando há múltiplos anos
- Cada ano deve aparecer como uma linha separada na tabela
- Se há 5 registros de CVU (um para cada ano), mostre os 5 anos completos em uma tabela

EXEMPLOS ESPECÍFICOS PARA CVU:
- Se há CVU de 5 anos: [900, 920, 910, 930, 940]
- ❌ ERRADO: "O CVU médio é 920,00 $/MWh"
- ❌ ERRADO: "O CVU varia entre 900,00 e 940,00 $/MWh"
- ❌ ERRADO: "O CVU de Ibirite é 916,65 $/MWh" (quando há múltiplos anos)
- ✅ CORRETO: Tabela com 5 linhas, uma para cada ano:
  | Ano | CVU ($/MWh) |
  |-----|--------------|
  | 2025 | 900,00 |
  | 2026 | 920,00 |
  | 2027 | 910,00 |
  | 2028 | 930,00 |
  | 2029 | 940,00 |

📋 REGRA ESPECIAL PARA CARGA MENSAL:
- Se a pergunta é sobre carga mensal (ex: "carga do sudeste"), você DEVE apresentar TODOS os meses
- NUNCA use valores anuais agregados - os dados são mensais, não anuais
- NUNCA calcule "carga média anual" ou "carga total anual" dos meses
- Cada mês deve aparecer como uma linha separada na tabela
- Se há 60 registros de carga mensal (12 meses × 5 anos), mostre os 60 meses completos

EXEMPLOS ESPECÍFICOS PARA CARGA MENSAL:
- Se a pergunta é "carga do sudeste" e há dados mensais de 5 anos (60 meses):
- ❌ ERRADO: Tabela com valores anuais agregados (5 linhas, uma por ano)
- ❌ ERRADO: "A carga do Sudeste por ano:" + valores anuais
- ✅ CORRETO: Tabela com TODOS os meses (60 linhas, uma por mês):
  | Ano | Mês | Carga (MWmédio) |
  |-----|-----|-----------------|
  | 2025 | 1 | 41.838 |
  | 2025 | 2 | 41.838 |
  | ... | ... | ... |
  | 2029 | 12 | 49.635 |

📊 REGRAS GERAIS:
- Se os dados contêm múltiplos registros (ex: múltiplos anos), apresente TODOS em uma tabela
- Use tabelas Markdown para apresentar dados tabulares com todos os registros
- Analise a pergunta original e forneça uma resposta FOCADA que responda APENAS ao que foi perguntado
- FILTRE as informações do resultado da tool, mostrando apenas o que é relevante para a pergunta específica
- Se a pergunta é sobre um tipo específico de dado, mostre APENAS esse tipo, ignorando outros
- MAS SEMPRE apresente os dados brutos sem cálculos intermediários

⚠️ LEMBRE-SE: Se você calcular qualquer estatística (média, mínimo, máximo) dos dados brutos, estará ERRADO."""


def interpreter_node(state: AgentState) -> dict:
    """
    Node que interpreta os resultados e gera a resposta final formatada em Markdown.
    
    Prioridades:
    1. Se tool_result existe: processa resultado da tool
    2. Se rag_status == "fallback": retorna resposta de fallback
    3. Caso contrário: interpreta resultados de execução de código
    """
    try:
        # IMPORTANTE: Verificar resultado de tool PRIMEIRO
        # Se há tool_result, processar mesmo que haja disambiguation no state
        # (disambiguation pode estar no state de uma query anterior)
        tool_result = state.get("tool_result")
        tool_used = state.get("tool_used")
        
        if tool_result:
            print(f"[INTERPRETER] Processando resultado de tool: {tool_used}")
            print(f"[INTERPRETER]   Success: {tool_result.get('success', False)}")
            print(f"[INTERPRETER]   Data count: {len(tool_result.get('data', [])) if tool_result.get('data') else 0}")
            query = state.get("query", "")
            print(f"[INTERPRETER]   Query original: {query[:100]}")
            result = _format_tool_response_with_llm(tool_result, tool_used, query)
            print(f"[INTERPRETER]   Resposta gerada: {len(result.get('final_response', ''))} caracteres")
            return result
        
        # Verificar se há disambiguation (apenas se não há tool_result)
        disambiguation = state.get("disambiguation")
        if disambiguation:
            # Para disambiguation, não retornar mensagem - o frontend já cria
            # Apenas retornar vazio para evitar duplicação
            print(f"[INTERPRETER] Processando disambiguation com {len(disambiguation.get('options', []))} opções")
            return {"final_response": ""}  # Vazio - frontend já cria a mensagem
        
        # Verificar se é um caso de fallback
        rag_status = state.get("rag_status", "success")
        
        if rag_status == "fallback":
            fallback_response = state.get("fallback_response", "")
            if fallback_response:
                fallback_response = clean_response_text(fallback_response, max_emojis=2)
                return {"final_response": fallback_response}
            
            # Fallback genérico se não houver resposta
            fallback_msg = """## Não foi possível processar sua solicitação

Não encontrei arquivos de dados adequados para responder sua pergunta.

### Sugestões de perguntas válidas:

- "Quais são as usinas hidrelétricas com maior potência instalada?"
- "Quais térmicas têm manutenção programada?"
- "Qual o custo das classes térmicas?"
- "Qual a demanda do submercado Sudeste?"
- "Quais são as vazões históricas do posto 1?"

### Dados disponíveis para consulta:

- **HIDR.DAT**: Cadastro de usinas hidrelétricas (potência, volumes, características)
- **MANUTT.DAT**: Manutenções de térmicas
- **CLAST.DAT**: Custos de classes térmicas
- **SISTEMA.DAT**: Demandas e intercâmbios entre submercados
- **VAZOES.DAT**: Séries históricas de vazões
"""
            fallback_msg = clean_response_text(fallback_msg, max_emojis=2)
            return {"final_response": fallback_msg}
        
        # Fluxo normal - interpretar resultados de execução
        execution_result = state.get("execution_result") or {}
        retry_count = state.get("retry_count", 0)
        max_retries = state.get("max_retries", 3)
        
        if execution_result.get("success"):
            exec_output = execution_result.get("stdout", "Sem output")
            # Remover dados JSON se presentes
            if "---JSON_DATA_START---" in exec_output:
                parts = exec_output.split("---JSON_DATA_START---")
                exec_output = parts[0].strip()
        else:
            exec_output = f"ERRO: {execution_result.get('stderr', 'Erro desconhecido')}"
        
        llm = ChatOpenAI(
            api_key=OPENAI_API_KEY,
            model=OPENAI_MODEL,
            temperature=0.3
        )
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", INTERPRETER_SYSTEM_PROMPT),
            ("human", INTERPRETER_USER_PROMPT)
        ])
        
        relevant_docs_str = "\n\n---\n\n".join(state.get("relevant_docs") or [])
        
        chain = prompt | llm
        
        response = chain.invoke({
            "query": state.get("query", ""),
            "relevant_docs": relevant_docs_str,
            "generated_code": state.get("generated_code", ""),
            "execution_result": exec_output,
            "retry_count": retry_count,
            "max_retries": max_retries
        })
        
        # Garantir que response.content existe e não é None
        final_response = getattr(response, 'content', None)
        if not final_response:
            final_response = "## Processamento concluído\n\nOs dados foram processados com sucesso. Consulte a saída da execução acima para mais detalhes."
        # Limitar emojis na resposta
        final_response = clean_response_text(final_response, max_emojis=2)
        return {"final_response": final_response}
        
    except Exception as e:
        print(f"[INTERPRETER ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        error_msg = f"## Erro ao interpretar resultados\n\nOcorreu um erro ao gerar a resposta: {str(e)}\n\nConsulte a saída da execução do código para ver os dados."
        error_msg = clean_response_text(error_msg, max_emojis=2)
        return {"final_response": error_msg}


def _format_tool_response_summary(tool_result: dict, tool_used: str) -> str:
    """
    Cria um resumo do resultado da tool para passar ao LLM.
    Mantém informações estruturadas mas de forma resumida.
    
    Args:
        tool_result: Resultado da execução da tool
        tool_used: Nome da tool usada
        
    Returns:
        String com resumo formatado
    """
    summary_parts = []
    
    # Informações básicas
    if tool_result.get("success"):
        summary_parts.append(f"Status: ✅ Sucesso")
    else:
        summary_parts.append(f"Status: ❌ Erro - {tool_result.get('error', 'Erro desconhecido')}")
        return "\n".join(summary_parts)
    
    # Filtros aplicados
    filtros = tool_result.get("filtros")
    if filtros:
        summary_parts.append(f"\nFiltros aplicados:")
        if isinstance(filtros, dict):
            for key, value in filtros.items():
                summary_parts.append(f"  - {key}: {value}")
    
    # Estatísticas gerais
    stats_geral = tool_result.get("stats_geral")
    if stats_geral:
        summary_parts.append(f"\nEstatísticas gerais:")
        summary_parts.append(f"  - Total de registros: {stats_geral.get('total_registros', 0)}")
        summary_parts.append(f"  - Total de tipos: {stats_geral.get('total_tipos', 0)}")
        tipos_encontrados = stats_geral.get('tipos_encontrados', [])
        if tipos_encontrados:
            summary_parts.append(f"  - Tipos encontrados: {', '.join(tipos_encontrados)}")
    
    # Dados por tipo (resumido)
    dados_por_tipo = tool_result.get("dados_por_tipo", {})
    if dados_por_tipo:
        summary_parts.append(f"\nDados por tipo de modificação:")
        for tipo, dados in dados_por_tipo.items():
            total = len(dados) if isinstance(dados, list) else 0
            summary_parts.append(f"  - {tipo}: {total} registro(s)")
            # Mostrar primeiros 3 registros como exemplo
            if isinstance(dados, list) and dados:
                summary_parts.append(f"    Exemplos:")
                for i, registro in enumerate(dados[:3]):
                    summary_parts.append(f"      {i+1}. {str(registro)[:200]}...")
    
    # Dados por submercado (se organizados separadamente)
    dados_por_submercado = tool_result.get("dados_por_submercado")
    if dados_por_submercado:
        summary_parts.append(f"\nDados organizados por submercado:")
        for codigo, info in dados_por_submercado.items():
            nome = info.get('nome', f'Subsistema {codigo}')
            total = info.get('total_registros', 0)
            summary_parts.append(f"  - {nome} (Código {codigo}): {total} registro(s)")
    
    # Summary da tool (para CargaMensalTool)
    summary = tool_result.get("summary")
    if summary:
        if summary.get("organizado_por_submercado"):
            summary_parts.append(f"\n⚠️ Dados organizados separadamente por submercado conforme solicitado")
        submercados = summary.get("submercados", [])
        if submercados:
            summary_parts.append(f"\nSubmercados disponíveis: {', '.join(map(str, submercados))}")
    
    # Outras seções importantes
    for key in ["desativacoes", "repotenciacoes", "expansoes", "indisponibilidades", 
                "dados_expansoes", "dados_estruturais", "dados_conjunturais", "data"]:
        if key in tool_result and tool_result[key]:
            value = tool_result[key]
            if isinstance(value, list):
                summary_parts.append(f"\n{key}: {len(value)} registro(s)")
            elif isinstance(value, dict):
                summary_parts.append(f"\n{key}: {len(value)} item(s)")
            else:
                summary_parts.append(f"\n{key}: {value}")
    
    return "\n".join(summary_parts)


def _format_number_for_display(value: float, threshold: float = 1e10) -> str:
    """
    Formata um número para exibição, usando notação científica para valores muito grandes.
    
    Args:
        value: Valor numérico a formatar
        threshold: Limite acima do qual usar notação científica
        
    Returns:
        String formatada
    """
    if not isinstance(value, (int, float)):
        return str(value)
    
    # Valores muito grandes (absoluto >= 1e10) ou muito pequenos (absoluto < 1e-3 e != 0): usar notação científica
    # Valores como -1.0999999999999999e+36 devem ser formatados em notação científica
    if abs(value) >= threshold or (abs(value) < 1e-3 and value != 0):
        # Formatar em notação científica com 2 casas decimais
        return f"{value:.2e}"
    elif abs(value) >= 1e30:  # Valores extremamente grandes (como -1.0999999999999999e+36)
        # Formatar em notação científica com 2 casas decimais
        return f"{value:.2e}"
    else:
        # Formatar com separador de milhar e 2 casas decimais
        return f"{value:,.2f}"


def _format_restricao_eletrica_data(dados: list) -> list:
    """
    Formata os dados de restrições elétricas, convertendo valores muito grandes
    para notação científica.
    
    Args:
        dados: Lista de dicionários com dados de restrições elétricas
        
    Returns:
        Lista de dicionários formatados
    """
    dados_formatados = []
    for registro in dados:
        registro_formatado = registro.copy()
        
        # Formatar lim_inf e lim_sup se existirem
        if 'lim_inf' in registro_formatado:
            valor = registro_formatado['lim_inf']
            if isinstance(valor, (int, float)):
                registro_formatado['lim_inf'] = _format_number_for_display(valor)
        
        if 'lim_sup' in registro_formatado:
            valor = registro_formatado['lim_sup']
            if isinstance(valor, (int, float)):
                registro_formatado['lim_sup'] = _format_number_for_display(valor)
        
        dados_formatados.append(registro_formatado)
    
    return dados_formatados


def _format_tool_response_data_for_llm(tool_result: dict) -> str:
    """
    Formata os dados da tool em formato estruturado para o LLM.
    Usa JSON para manter estrutura, mas limita tamanho.
    
    Args:
        tool_result: Resultado da execução da tool
        
    Returns:
        String JSON resumida
    """
    import json
    
    # Criar estrutura resumida
    # IMPORTANTE: NÃO incluir stats_estrutural ou stats_conjuntural que contêm
    # custo_medio, custo_min, custo_max - essas estatísticas podem influenciar
    # o LLM a calcular médias, o que é proibido
    data_summary = {
        "success": tool_result.get("success", False),
        "filtros": tool_result.get("filtros"),
    }
    
    # Incluir stats_geral apenas se não contiver estatísticas calculadas
    stats_geral = tool_result.get("stats_geral")
    if stats_geral:
        # Criar cópia sem campos de estatísticas calculadas
        stats_geral_clean = {}
        for key, value in stats_geral.items():
            # Incluir apenas campos descritivos, não estatísticas calculadas
            if key not in ['custo_medio', 'custo_min', 'custo_max', 'valor_medio', 'valor_min', 'valor_max']:
                stats_geral_clean[key] = value
        if stats_geral_clean:
            data_summary["stats_geral"] = stats_geral_clean
    
    # Dados por submercado (prioridade quando disponível)
    dados_por_submercado = tool_result.get("dados_por_submercado")
    if dados_por_submercado:
        data_summary["dados_por_submercado"] = {}
        for codigo, info in dados_por_submercado.items():
            nome = info.get('nome', f'Subsistema {codigo}')
            dados = info.get('dados', [])
            # Limitar a 50 registros por submercado para não exceder tokens
            data_summary["dados_por_submercado"][codigo] = {
                "nome": nome,
                "dados": dados[:50],
                "total_registros": len(dados)
            }
            if len(dados) > 50:
                data_summary["dados_por_submercado"][codigo]["_limitado"] = True
    
    # Adicionar dados principais (limitado para não sobrecarregar)
    dados_por_tipo = tool_result.get("dados_por_tipo", {})
    if dados_por_tipo:
        data_summary["dados_por_tipo"] = {}
        for tipo, dados in dados_por_tipo.items():
            if isinstance(dados, list):
                # Limitar a 20 registros por tipo para não exceder tokens
                data_summary["dados_por_tipo"][tipo] = dados[:20]
                if len(dados) > 20:
                    data_summary["dados_por_tipo"][tipo + "_total"] = len(dados)
            else:
                data_summary["dados_por_tipo"][tipo] = dados
    
    # Dados de carga mensal (para CargaMensalTool)
    # IMPORTANTE: Incluir apenas dados mensais brutos, NÃO dados agregados anuais
    data = tool_result.get("data")
    if data:
        # Incluir TODOS os dados mensais (sem limite para carga mensal)
        # O LLM deve apresentar todos os meses, não valores anuais agregados
        data_summary["data"] = data
    
    # Dados por submercado (para CargaMensalTool quando organizado por submercado)
    # IMPORTANTE: Incluir dados mensais brutos, não agregados
    dados_por_submercado = tool_result.get("dados_por_submercado")
    if dados_por_submercado:
        data_summary["dados_por_submercado"] = {}
        for codigo, info in dados_por_submercado.items():
            nome = info.get('nome', f'Subsistema {codigo}')
            dados = info.get('dados', [])
            # Incluir TODOS os dados mensais (sem limite para carga mensal)
            data_summary["dados_por_submercado"][codigo] = {
                "nome": nome,
                "dados": dados,  # TODOS os dados mensais, sem limite
                "total_registros": len(dados)
            }
    
    # Dados estruturais e conjunturais (para ClastValoresTool)
    # IMPORTANTE: Incluir apenas os dados brutos, NÃO as estatísticas calculadas
    dados_estruturais = tool_result.get("dados_estruturais")
    if dados_estruturais:
        # Incluir TODOS os dados estruturais (sem limite para CVU)
        # O LLM deve apresentar todos os anos, não calcular médias
        data_summary["dados_estruturais"] = dados_estruturais
    
    dados_conjunturais = tool_result.get("dados_conjunturais")
    if dados_conjunturais:
        # Incluir dados conjunturais (limitado para não exceder tokens)
        data_summary["dados_conjunturais"] = dados_conjunturais[:50]
        if len(dados_conjunturais) > 50:
            data_summary["dados_conjunturais_total"] = len(dados_conjunturais)
    
    # Dados de restrições elétricas (para RestricaoEletricaTool)
    dados = tool_result.get("dados")
    if dados:
        # Formatar valores numéricos muito grandes em notação científica
        dados_formatados = _format_restricao_eletrica_data(dados)
        data_summary["dados"] = dados_formatados[:50]  # Limitar a 50 registros
        if len(dados_formatados) > 50:
            data_summary["dados_total"] = len(dados_formatados)
    
    # Outras seções importantes
    for key in ["desativacoes", "repotenciacoes", "expansoes", "indisponibilidades"]:
        if key in tool_result:
            value = tool_result[key]
            if isinstance(value, list):
                data_summary[key] = value[:20]  # Limitar também
            else:
                data_summary[key] = value
    
    # IMPORTANTE: NUNCA incluir:
    # - aggregated: dados agregados anuais (para CargaMensalTool)
    # - stats_estrutural ou stats_conjuntural: estatísticas calculadas (para ClastValoresTool)
    # Esses dados podem influenciar o LLM a calcular médias ou usar valores agregados, o que é proibido
    
    try:
        return json.dumps(data_summary, indent=2, ensure_ascii=False, default=str)
    except:
        return str(data_summary)[:2000]  # Fallback


def _format_tool_response_with_llm(tool_result: dict, tool_used: str, query: str) -> dict:
    """
    Formata o resultado de uma tool usando LLM para filtrar e focar na pergunta do usuário.
    
    Args:
        tool_result: Resultado da execução da tool
        tool_used: Nome da tool usada
        query: Query original do usuário
        
    Returns:
        Dict com final_response formatado e filtrado
    """
    if not tool_result.get("success"):
        error = tool_result.get("error", "Erro desconhecido")
        return {
            "final_response": f"## ❌ Erro na Tool {tool_used}\n\n{error}"
        }
    
    try:
        print(f"[TOOL INTERPRETER LLM] Gerando resposta focada para query: {query[:100]}")
        
        # Adicionar query ao tool_result para uso na formatação
        tool_result_with_query = tool_result.copy()
        tool_result_with_query["query"] = query
        
        # Primeiro, gerar resposta formatada básica usando métodos existentes
        formatted_response = _format_tool_response(tool_result_with_query, tool_used)
        base_response = formatted_response.get("final_response", "")
        
        # Criar resumos para o LLM
        tool_result_summary = _format_tool_response_summary(tool_result, tool_used)
        tool_result_data = _format_tool_response_data_for_llm(tool_result)
        
        # Usar LLM para filtrar e focar
        llm = ChatOpenAI(
            api_key=OPENAI_API_KEY,
            model=OPENAI_MODEL,
            temperature=0.2  # Temperatura baixa para respostas mais consistentes
        )
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", TOOL_INTERPRETER_SYSTEM_PROMPT),
            ("human", TOOL_INTERPRETER_USER_PROMPT)
        ])
        
        chain = prompt | llm
        
        response = chain.invoke({
            "query": query,
            "tool_name": tool_used,
            "tool_result_summary": tool_result_summary,
            "tool_result_data": tool_result_data,
            "tool_result_formatted": base_response[:4000]  # Limitar tamanho da resposta formatada
        })
        
        final_response = getattr(response, 'content', None)
        
        if final_response:
            print(f"[TOOL INTERPRETER LLM] ✅ Resposta focada gerada ({len(final_response)} caracteres)")
            # Limitar emojis na resposta
            final_response = clean_response_text(final_response, max_emojis=2)
            return {"final_response": final_response}
        else:
            # Fallback para resposta formatada original
            print(f"[TOOL INTERPRETER LLM] ⚠️ LLM não retornou conteúdo, usando resposta formatada original")
            return formatted_response
            
    except Exception as e:
        print(f"[TOOL INTERPRETER LLM] ❌ Erro ao processar com LLM: {e}")
        import traceback
        traceback.print_exc()
        # Fallback para formatação original em caso de erro
        return _format_tool_response(tool_result, tool_used)


def _format_tool_response(tool_result: dict, tool_used: str) -> dict:
    """
    Formata o resultado de uma tool em resposta Markdown (método original, usado como base).
    
    Args:
        tool_result: Resultado da execução da tool
        tool_used: Nome da tool usada
        
    Returns:
        Dict com final_response formatado
    """
    if not tool_result.get("success"):
        error = tool_result.get("error", "Erro desconhecido")
        return {
            "final_response": f"## ❌ Erro na Tool {tool_used}\n\n{error}"
        }
    
    # Roteamento para formatação específica de cada tool
    if tool_used == "CargaMensalTool":
        return _format_carga_mensal_response(tool_result, tool_used)
    elif tool_used == "ClastValoresTool":
        # Passar query para detectar se é CVU e gerar gráfico
        query = tool_result.get("query", "")
        return _format_clast_valores_response(tool_result, tool_used, query)
    elif tool_used == "ExptOperacaoTool":
        return _format_expt_operacao_response(tool_result, tool_used)
    elif tool_used == "ModifOperacaoTool":
        return _format_modif_operacao_response(tool_result, tool_used)
    
    # Formatação genérica para outras tools
    return {
        "final_response": f"## ✅ Dados Processados\n\n*Processado pela tool: **{tool_used}***\n\n{str(tool_result)}"
    }


def _format_carga_mensal_response(tool_result: dict, tool_used: str) -> dict:
    
    # Extrair dados
    data = tool_result.get("data", [])
    summary = tool_result.get("summary", {})
    stats = tool_result.get("stats_por_submercado", [])
    # IMPORTANTE: NÃO usar aggregated (dados agregados anuais)
    # Os dados devem ser apresentados mês a mês, não agregados por ano
    
    # Construir resposta em Markdown
    response_parts = []
    
    # Cabeçalho
    filtro_info = summary.get('filtro_aplicado') if summary else None
    
    if filtro_info and filtro_info.get('filtrado'):
        nome_sub = filtro_info.get('nome_submercado', f"Subsistema {filtro_info.get('codigo_submercado')}")
        response_parts.append(f"## ✅ Dados de Carga Mensal - {nome_sub}\n\n")
        response_parts.append(f"*Filtrado para: **{nome_sub}** (Código: {filtro_info.get('codigo_submercado')})*\n")
    else:
        response_parts.append(f"## ✅ Dados de Carga Mensal por Submercado\n\n")
    
    response_parts.append(f"*Processado pela tool: **{tool_used}***\n\n")
    
    # Resumo
    if summary:
        response_parts.append("### 📊 Resumo\n\n")
        response_parts.append(f"- **Total de registros**: {summary.get('total_registros', 0):,}\n")
        
        if filtro_info and filtro_info.get('filtrado'):
            nome_filtrado = filtro_info.get('nome_submercado') or f"Subsistema {filtro_info.get('codigo_submercado')}"
            codigo_filtrado = filtro_info.get('codigo_submercado')
            response_parts.append(f"- **Submercado filtrado**: {nome_filtrado} (Código: {codigo_filtrado})\n")
        else:
            response_parts.append(f"- **Submercados**: {', '.join(map(str, summary.get('submercados', [])))}\n")
        
        response_parts.append(f"- **Período**: {summary.get('periodo', 'N/A')}\n")
        response_parts.append(f"- **Anos**: {', '.join(map(str, summary.get('anos', [])))}\n\n")
    
    # Estatísticas por submercado
    if stats:
        response_parts.append("### 📈 Estatísticas por Submercado\n\n")
        response_parts.append("| Submercado | Registros | Média (MWmédio) | Mínimo | Máximo | Total |\n")
        response_parts.append("|------------|-----------|-----------------|--------|--------|-------|\n")
        
        for stat in stats:
            sub = stat.get('codigo_submercado', 'N/A')
            total = stat.get('total_registros', 0)
            media = stat.get('carga_media_mwmed', 0)
            minimo = stat.get('carga_min_mwmed', 0)
            maximo = stat.get('carga_max_mwmed', 0)
            total_sum = stat.get('carga_total_mwmed', 0)
            
            response_parts.append(
                f"| {sub} | {total} | {media:,.2f} | {minimo:,.2f} | {maximo:,.2f} | {total_sum:,.2f} |\n"
            )
        response_parts.append("\n")
    
    # Agregação anual
    # IMPORTANTE: NÃO mostrar dados agregados anuais
    # Os dados de carga mensal devem ser apresentados mês a mês, não agregados por ano
    # A seção de dados agregados foi removida para evitar que o LLM use valores anuais
    
    # Dados mensais detalhados
    if data:
        response_parts.append("### 📋 Dados Detalhados\n\n")
        response_parts.append(f"*Total de {len(data)} registros disponíveis*\n\n")
        
        # Mostrar todos os dados ou uma amostra se for muito grande para exibição
        # Mas todos os dados estarão disponíveis no JSON
        if len(data) > 100:
            response_parts.append("*Exibindo primeiros 100 registros. Todos os dados estão disponíveis no JSON para download.*\n\n")
            sample = data[:100]
        else:
            sample = data
        if sample:
            # Pegar colunas principais
            cols = ['codigo_submercado', 'ano', 'mes', 'valor']
            available_cols = [col for col in cols if col in sample[0]]
            
            if available_cols:
                response_parts.append("| " + " | ".join(available_cols) + " |\n")
                response_parts.append("|" + "|".join(["---"] * len(available_cols)) + "|\n")
                
                for record in sample:
                    row = [str(record.get(col, '')) for col in available_cols]
                    response_parts.append("| " + " | ".join(row) + " |\n")
                
                if len(data) > len(sample):
                    response_parts.append(f"\n*Exibindo {len(sample)} de {len(data)} registros. Todos os dados estão disponíveis no JSON.*\n")
                else:
                    response_parts.append(f"\n*Todos os {len(data)} registros exibidos acima.*\n")
                response_parts.append("\n")
    
    response_parts.append("---\n\n")
    response_parts.append("*Dados processados diretamente do arquivo SISTEMA.DAT usando tool pré-programada.*\n")
    
    response_text = "".join(response_parts)
    response_text = clean_response_text(response_text, max_emojis=2)
    return {"final_response": response_text}


def _generate_cvu_chart(dados_estruturais: list, classe_nome: str = None) -> Optional[str]:
    """
    Gera um gráfico de CVU (Custo Variável Unitário) por ano.
    
    Args:
        dados_estruturais: Lista de dicionários com dados estruturais
        classe_nome: Nome da classe (opcional, para título)
        
    Returns:
        String base64 da imagem do gráfico ou None se não for possível gerar
    """
    try:
        if not dados_estruturais:
            return None
        
        df = pd.DataFrame(dados_estruturais)
        
        # Verificar se tem as colunas necessárias
        if 'indice_ano_estudo' not in df.columns or 'valor' not in df.columns:
            return None
        
        # Se há múltiplas classes, usar apenas a primeira (ou agrupar)
        if 'codigo_usina' in df.columns:
            codigos_unicos = df['codigo_usina'].unique()
            if len(codigos_unicos) == 1:
                # Uma única classe - usar todos os dados
                df_plot = df.copy()
                if classe_nome is None and 'nome_usina' in df.columns:
                    classe_nome = df['nome_usina'].iloc[0]
            else:
                # Múltiplas classes - usar a primeira ou fazer gráfico separado por classe
                # Por enquanto, usar a primeira classe
                primeiro_codigo = codigos_unicos[0]
                df_plot = df[df['codigo_usina'] == primeiro_codigo].copy()
                if classe_nome is None and 'nome_usina' in df_plot.columns:
                    classe_nome = df_plot['nome_usina'].iloc[0]
        else:
            df_plot = df.copy()
        
        # Agrupar por ano e pegar o valor (se houver múltiplos valores por ano, usar o primeiro)
        df_plot = df_plot.sort_values('indice_ano_estudo')
        anos = df_plot['indice_ano_estudo'].tolist()
        custos = df_plot['valor'].tolist()
        
        if not anos or not custos:
            return None
        
        # Criar gráfico
        plt.figure(figsize=(10, 6))
        plt.plot(anos, custos, marker='o', linewidth=2, markersize=8)
        plt.xlabel('Ano', fontsize=12, fontweight='bold')
        plt.ylabel('CVU ($/MWh)', fontsize=12, fontweight='bold')
        
        if classe_nome:
            plt.title(f'Custo Variável Unitário (CVU) - {classe_nome}', fontsize=14, fontweight='bold')
        else:
            plt.title('Custo Variável Unitário (CVU)', fontsize=14, fontweight='bold')
        
        plt.grid(True, alpha=0.3, linestyle='--')
        plt.xticks(anos, rotation=45)
        
        # Adicionar valores nos pontos
        for i, (ano, custo) in enumerate(zip(anos, custos)):
            plt.annotate(f'{custo:,.2f}', (ano, custo), 
                        textcoords="offset points", xytext=(0,10), ha='center', fontsize=9)
        
        plt.tight_layout()
        
        # Converter para base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
        plt.close()
        
        return image_base64
        
    except Exception as e:
        print(f"[INTERPRETER] ⚠️ Erro ao gerar gráfico CVU: {e}")
        import traceback
        traceback.print_exc()
        return None


def _is_cvu_query(query: str) -> bool:
    """
    Verifica se a query é sobre CVU (Custo Variável Unitário).
    
    Args:
        query: Query do usuário
        
    Returns:
        True se for uma query de CVU
    """
    query_lower = query.lower()
    cvu_keywords = [
        "cvu",
        "custo variável unitário",
        "custo variavel unitario",
        "custo variável unitario",
        "custo variavel unitário",
    ]
    return any(kw in query_lower for kw in cvu_keywords)


def _format_clast_valores_response(tool_result: dict, tool_used: str, query: str = "") -> dict:
    """
    Formata o resultado da ClastValoresTool em resposta Markdown.
    
    Args:
        tool_result: Resultado da execução da tool
        tool_used: Nome da tool usada
        
    Returns:
        Dict com final_response formatado
    """
    response_parts = []
    
    # Cabeçalho
    tipo_solicitado = tool_result.get("tipo_solicitado", "ambos")
    filtros = tool_result.get("filtros")
    
    if tipo_solicitado == "estrutural":
        response_parts.append("## ✅ Valores Estruturais do CLAST.DAT\n\n")
    elif tipo_solicitado == "conjuntural":
        response_parts.append("## ✅ Valores Conjunturais do CLAST.DAT\n\n")
    else:
        response_parts.append("## ✅ Valores Estruturais e Conjunturais do CLAST.DAT\n\n")
    
    response_parts.append(f"*Processado pela tool: **{tool_used}***\n\n")
    
    # Informações sobre filtros
    if filtros:
        if 'classe' in filtros:
            classe_info = filtros['classe']
            response_parts.append(f"### 🔍 Filtros Aplicados\n\n")
            response_parts.append(f"- **Classe**: {classe_info.get('nome')} (Código: {classe_info.get('codigo')})\n")
            response_parts.append(f"- **Tipo de Combustível**: {classe_info.get('tipo_combustivel')}\n\n")
        if 'tipo_combustivel' in filtros:
            response_parts.append(f"- **Tipo de Combustível**: {filtros['tipo_combustivel']}\n\n")
    
    # Valores estruturais
    dados_estruturais = tool_result.get("dados_estruturais")
    stats_estrutural = tool_result.get("stats_estrutural")
    
    if dados_estruturais is not None:
        response_parts.append("### 📊 Valores Estruturais (Custos Base)\n\n")
        
        if stats_estrutural:
            response_parts.append(f"- **Total de classes**: {stats_estrutural.get('total_classes', 0)}\n")
            response_parts.append(f"- **Total de registros**: {stats_estrutural.get('total_registros', 0):,}\n")
            response_parts.append(f"- **Anos cobertos**: {', '.join(map(str, stats_estrutural.get('anos_cobertos', [])))}\n")
            response_parts.append(f"- **Custo médio**: {stats_estrutural.get('custo_medio', 0):,.2f} $/MWh\n")
            response_parts.append(f"- **Custo mínimo**: {stats_estrutural.get('custo_min', 0):,.2f} $/MWh\n")
            response_parts.append(f"- **Custo máximo**: {stats_estrutural.get('custo_max', 0):,.2f} $/MWh\n\n")
            
            # Estatísticas por tipo de combustível
            if 'stats_por_tipo' in stats_estrutural:
                response_parts.append("#### 📈 Estatísticas por Tipo de Combustível\n\n")
                response_parts.append("| Tipo | Classes | Custo Médio ($/MWh) | Mínimo | Máximo |\n")
                response_parts.append("|------|---------|---------------------|--------|--------|\n")
                
                for stat in stats_estrutural['stats_por_tipo']:
                    tipo = stat.get('tipo_combustivel', 'N/A')
                    classes = stat.get('total_classes', 0)
                    medio = stat.get('custo_medio', 0)
                    minimo = stat.get('custo_min', 0)
                    maximo = stat.get('custo_max', 0)
                    
                    response_parts.append(
                        f"| {tipo} | {classes} | {medio:,.2f} | {minimo:,.2f} | {maximo:,.2f} |\n"
                    )
                response_parts.append("\n")
        
        # Tabela de dados estruturais
        if dados_estruturais:
            # Verificar se é query de CVU para gerar gráfico
            is_cvu = _is_cvu_query(query)
            classe_nome_grafico = None
            if filtros and 'classe' in filtros:
                classe_nome_grafico = filtros['classe'].get('nome')
            
            # Gerar gráfico se for CVU
            chart_base64 = None
            if is_cvu:
                chart_base64 = _generate_cvu_chart(dados_estruturais, classe_nome_grafico)
                if chart_base64:
                    response_parts.append("#### 📈 Gráfico de CVU por Ano\n\n")
                    response_parts.append(f"![Gráfico CVU](data:image/png;base64,{chart_base64})\n\n")
            
            response_parts.append("#### 📋 Dados Estruturais Detalhados\n\n")
            
            # Criar tabela pivotada por classe e ano
            df_est = pd.DataFrame(dados_estruturais)
            
            if len(df_est) > 0 and 'codigo_usina' in df_est.columns and 'indice_ano_estudo' in df_est.columns:
                # Agrupar por classe
                classes_unicas = df_est[['codigo_usina', 'nome_usina', 'tipo_combustivel']].drop_duplicates()
                
                response_parts.append("| Código | Nome Classe | Tipo Combustível | ")
                anos = sorted(df_est['indice_ano_estudo'].unique())
                for ano in anos:
                    response_parts.append(f"Ano {ano} | ")
                response_parts.append("\n")
                response_parts.append("|--------|-------------|------------------|")
                for ano in anos:
                    response_parts.append("--------|")
                response_parts.append("\n")
                
                for _, classe_row in classes_unicas.iterrows():
                    codigo = classe_row['codigo_usina']
                    nome = classe_row['nome_usina']
                    tipo = classe_row['tipo_combustivel']
                    
                    response_parts.append(f"| {codigo} | {nome} | {tipo} | ")
                    
                    for ano in anos:
                        custo_row = df_est[(df_est['codigo_usina'] == codigo) & 
                                          (df_est['indice_ano_estudo'] == ano)]
                        if not custo_row.empty:
                            custo = custo_row.iloc[0].get('valor', 0)
                            response_parts.append(f"{custo:,.2f} | ")
                        else:
                            response_parts.append("- | ")
                    
                    response_parts.append("\n")
                
                response_parts.append("\n")
            else:
                response_parts.append(f"*Total de {len(dados_estruturais)} registros disponíveis no JSON*\n\n")
    
    # Valores conjunturais
    dados_conjunturais = tool_result.get("dados_conjunturais")
    stats_conjuntural = tool_result.get("stats_conjuntural")
    
    if dados_conjunturais is not None:
        response_parts.append("### 🔄 Valores Conjunturais (Modificações Sazonais)\n\n")
        
        if stats_conjuntural:
            response_parts.append(f"- **Total de modificações**: {stats_conjuntural.get('total_modificacoes', 0)}\n")
            response_parts.append(f"- **Classes afetadas**: {stats_conjuntural.get('classes_afetadas', 0)}\n")
            response_parts.append(f"- **Custo médio**: {stats_conjuntural.get('custo_medio', 0):,.2f} $/MWh\n")
            response_parts.append(f"- **Custo mínimo**: {stats_conjuntural.get('custo_min', 0):,.2f} $/MWh\n")
            response_parts.append(f"- **Custo máximo**: {stats_conjuntural.get('custo_max', 0):,.2f} $/MWh\n\n")
        
        # Tabela de modificações
        if dados_conjunturais:
            response_parts.append("#### 📋 Modificações Sazonais\n\n")
            response_parts.append("| Código | Nome Classe | Data Início | Data Fim | Custo ($/MWh) |\n")
            response_parts.append("|--------|-------------|-------------|----------|---------------|\n")
            
            for modif in dados_conjunturais[:50]:  # Limitar exibição a 50
                codigo = modif.get('codigo_usina', 'N/A')
                nome = modif.get('nome_usina', 'N/A')
                inicio = modif.get('data_inicio', 'N/A')
                fim = modif.get('data_fim', 'N/A')
                custo = modif.get('custo', 0)
                
                # Formatar datas
                if isinstance(inicio, str) and 'T' in inicio:
                    inicio = inicio.split('T')[0]
                if isinstance(fim, str) and 'T' in fim:
                    fim = fim.split('T')[0]
                
                response_parts.append(f"| {codigo} | {nome} | {inicio} | {fim} | {custo:,.2f} |\n")
            
            if len(dados_conjunturais) > 50:
                response_parts.append(f"\n*Exibindo 50 de {len(dados_conjunturais)} modificações. Todas estão disponíveis no JSON.*\n")
            response_parts.append("\n")
    
    response_parts.append("---\n\n")
    response_parts.append("*Dados processados diretamente do arquivo CLAST.DAT usando tool pré-programada.*\n")
    
    response_text = "".join(response_parts)
    response_text = clean_response_text(response_text, max_emojis=2)
    return {"final_response": response_text}


def _format_expt_operacao_response(tool_result: dict, tool_used: str) -> dict:
    """
    Formata o resultado da ExptOperacaoTool em resposta Markdown.
    
    Args:
        tool_result: Resultado da execução da tool
        tool_used: Nome da tool usada
        
    Returns:
        Dict com final_response formatado
    """
    response_parts = []
    
    # Cabeçalho
    filtros = tool_result.get("filtros")
    
    response_parts.append("## ✅ Dados de Operação Térmica do EXPT.DAT\n\n")
    response_parts.append(f"*Processado pela tool: **{tool_used}***\n\n")
    
    # Informações sobre filtros
    if filtros:
        response_parts.append("### 🔍 Filtros Aplicados\n\n")
        if 'usina' in filtros:
            usina_info = filtros['usina']
            response_parts.append(f"- **Usina**: {usina_info.get('nome')} (Código: {usina_info.get('codigo')})\n")
        if 'tipo_modificacao' in filtros:
            response_parts.append(f"- **Tipo de Modificação**: {filtros['tipo_modificacao']}\n")
        if 'operacao_especifica' in filtros:
            op = filtros['operacao_especifica']
            op_nome = {
                'desativacao': 'Desativações',
                'repotenciacao': 'Repotenciações',
                'expansao': 'Expansões'
            }.get(op, op)
            response_parts.append(f"- **Operação**: {op_nome}\n")
        response_parts.append("\n")
    
    # Estatísticas gerais
    stats_geral = tool_result.get("stats_geral")
    if stats_geral:
        response_parts.append("### 📊 Resumo\n\n")
        response_parts.append(f"- **Total de registros**: {stats_geral.get('total_registros', 0):,}\n")
        response_parts.append(f"- **Usinas afetadas**: {stats_geral.get('total_usinas', 0)}\n")
        tipos = stats_geral.get('tipos_modificacao', [])
        if tipos:
            response_parts.append(f"- **Tipos de modificação encontrados**: {', '.join(tipos)}\n")
        response_parts.append("\n")
    
    # Dicionário de explicações para cada tipo
    explicacoes_tipos = {
        'POTEF': {
            'nome': 'Potência Efetiva',
            'descricao': 'Potência efetiva da usina térmica em MW. Modificações neste valor representam expansões (aumentos), repotenciações ou desativações (quando = 0).',
            'unidade': 'MW'
        },
        'GTMIN': {
            'nome': 'Geração Térmica Mínima',
            'descricao': 'Geração térmica mínima obrigatória em MW. Define a geração mínima que a usina deve manter durante o período especificado.',
            'unidade': 'MW'
        },
        'FCMAX': {
            'nome': 'Fator de Capacidade Máximo',
            'descricao': 'Fator de capacidade máximo em percentual (0-100%). Limita a capacidade de geração da usina. Quando = 0, indica desativação.',
            'unidade': '%'
        },
        'IPTER': {
            'nome': 'Indisponibilidade Programada',
            'descricao': 'Indisponibilidade programada em percentual (0-100%). Representa períodos de manutenção programada onde a usina não estará disponível.',
            'unidade': '%'
        },
        'TEIFT': {
            'nome': 'Taxa Equivalente de Indisponibilidade Forçada',
            'descricao': 'Taxa equivalente de indisponibilidade forçada em percentual (0-100%). Representa indisponibilidades não programadas (forçadas) da usina.',
            'unidade': '%'
        }
    }
    
    # Obter dados de expansões
    dados_expansoes = tool_result.get("dados_expansoes", [])
    
    if dados_expansoes:
        # Agrupar por tipo de modificação
        import pandas as pd
        df_expansoes = pd.DataFrame(dados_expansoes)
        
        tipos_presentes = df_expansoes['tipo'].unique() if 'tipo' in df_expansoes.columns else []
        
        # Para cada tipo, criar uma seção separada
        for tipo in sorted(tipos_presentes):
            df_tipo = df_expansoes[df_expansoes['tipo'] == tipo]
            explicacao = explicacoes_tipos.get(tipo, {
                'nome': tipo,
                'descricao': f'Modificações do tipo {tipo}',
                'unidade': ''
            })
            
            response_parts.append(f"### 🔧 {explicacao['nome']} ({tipo})\n\n")
            response_parts.append(f"**Explicação**: {explicacao['descricao']}\n\n")
            response_parts.append(f"**Total de registros**: {len(df_tipo)}\n\n")
            
            # Tabela com os dados deste tipo
            response_parts.append("| Código | Nome Usina | Valor | Data Início | Data Fim |\n")
            response_parts.append("|--------|------------|-------|-------------|----------|\n")
            
            for _, record in df_tipo.iterrows():
                codigo = record.get('codigo_usina', 'N/A')
                nome = record.get('nome_usina', 'N/A')
                modificacao = record.get('modificacao', 0)
                inicio = record.get('data_inicio', 'N/A')
                fim = record.get('data_fim', 'N/A')
                
                # Formatar datas
                if isinstance(inicio, str) and 'T' in inicio:
                    inicio = inicio.split('T')[0]
                elif hasattr(inicio, 'date'):
                    inicio = inicio.date()
                if isinstance(fim, str) and 'T' in fim:
                    fim = fim.split('T')[0]
                elif hasattr(fim, 'date'):
                    fim = fim.date()
                elif pd.isna(fim):
                    fim = 'Até o final'
                
                # Formatar valor com unidade
                if explicacao['unidade']:
                    valor_str = f"{modificacao:,.2f} {explicacao['unidade']}"
                else:
                    valor_str = f"{modificacao:,.2f}"
                
                response_parts.append(f"| {codigo} | {nome} | {valor_str} | {inicio} | {fim} |\n")
            
            response_parts.append("\n")
            
            # Estatísticas específicas deste tipo
            if len(df_tipo) > 1:
                valor_medio = df_tipo['modificacao'].mean()
                valor_min = df_tipo['modificacao'].min()
                valor_max = df_tipo['modificacao'].max()
                unidade = explicacao['unidade']
                
                response_parts.append(f"**Estatísticas**:\n")
                response_parts.append(f"- Valor médio: {valor_medio:,.2f} {unidade}\n")
                response_parts.append(f"- Valor mínimo: {valor_min:,.2f} {unidade}\n")
                response_parts.append(f"- Valor máximo: {valor_max:,.2f} {unidade}\n")
                response_parts.append("\n")
            
            response_parts.append("---\n\n")
    
    # Estatísticas por tipo (resumo geral - já detalhado acima por tipo)
    stats_por_tipo = tool_result.get("stats_por_tipo", [])
    if stats_por_tipo and len(stats_por_tipo) > 1:
        response_parts.append("### 📈 Resumo Estatístico por Tipo\n\n")
        response_parts.append("| Tipo | Registros | Usinas | Valor Médio | Mínimo | Máximo |\n")
        response_parts.append("|------|-----------|--------|-------------|--------|--------|\n")
        
        for stat in stats_por_tipo:
            tipo = stat.get('tipo', 'N/A')
            registros = stat.get('total_registros', 0)
            usinas = stat.get('usinas_afetadas', 0)
            medio = stat.get('valor_medio', 0)
            minimo = stat.get('valor_min', 0)
            maximo = stat.get('valor_max', 0)
            
            # Formatar unidade baseado no tipo
            if tipo in ['POTEF', 'GTMIN']:
                unidade = "MW"
                response_parts.append(
                    f"| {tipo} | {registros} | {usinas} | {medio:,.2f} {unidade} | {minimo:,.2f} {unidade} | {maximo:,.2f} {unidade} |\n"
                )
            else:
                unidade = "%"
                response_parts.append(
                    f"| {tipo} | {registros} | {usinas} | {medio:,.2f} {unidade} | {minimo:,.2f} {unidade} | {maximo:,.2f} {unidade} |\n"
                )
        response_parts.append("\n")
    
    # Estatísticas por usina
    stats_por_usina = tool_result.get("stats_por_usina", [])
    if stats_por_usina:
        response_parts.append("### 🏭 Modificações por Usina\n\n")
        response_parts.append("| Código | Nome Usina | Total Modificações | Tipos |\n")
        response_parts.append("|--------|------------|-------------------|-------|\n")
        
        for stat in stats_por_usina[:20]:  # Limitar a 20 para não sobrecarregar
            codigo = stat.get('codigo_usina', 'N/A')
            nome = stat.get('nome_usina', 'N/A')
            total = stat.get('total_modificacoes', 0)
            tipos = ', '.join(stat.get('tipos_modificacao', []))
            
            response_parts.append(f"| {codigo} | {nome} | {total} | {tipos} |\n")
        
        if len(stats_por_usina) > 20:
            response_parts.append(f"\n*Exibindo 20 de {len(stats_por_usina)} usinas. Todas estão disponíveis no JSON.*\n")
        response_parts.append("\n")
    
    # Desativações
    desativacoes = tool_result.get("desativacoes")
    if desativacoes:
        response_parts.append("### ⚠️ Desativações de Usinas Térmicas\n\n")
        response_parts.append("| Código | Nome Usina | Tipo | Data Início | Data Fim |\n")
        response_parts.append("|--------|------------|------|-------------|----------|\n")
        
        for desat in desativacoes[:20]:
            codigo = desat.get('codigo_usina', 'N/A')
            nome = desat.get('nome_usina', 'N/A')
            tipo = desat.get('tipo', 'N/A')
            inicio = desat.get('data_inicio', 'N/A')
            fim = desat.get('data_fim', 'N/A')
            
            # Formatar datas
            if isinstance(inicio, str) and 'T' in inicio:
                inicio = inicio.split('T')[0]
            if isinstance(fim, str) and 'T' in fim:
                fim = fim.split('T')[0]
            
            response_parts.append(f"| {codigo} | {nome} | {tipo} | {inicio} | {fim} |\n")
        
        if len(desativacoes) > 20:
            response_parts.append(f"\n*Exibindo 20 de {len(desativacoes)} desativações. Todas estão disponíveis no JSON.*\n")
        response_parts.append("\n")
    
    # Repotenciações
    repotenciacoes = tool_result.get("repotenciacoes")
    if repotenciacoes:
        response_parts.append("### ⚡ Repotenciações\n\n")
        response_parts.append("| Código | Nome Usina | Nova Potência (MW) | Data Início | Data Fim |\n")
        response_parts.append("|--------|------------|-------------------|-------------|----------|\n")
        
        for repot in repotenciacoes[:20]:
            codigo = repot.get('codigo_usina', 'N/A')
            nome = repot.get('nome_usina', 'N/A')
            potencia = repot.get('modificacao', 0)
            inicio = repot.get('data_inicio', 'N/A')
            fim = repot.get('data_fim', 'N/A')
            
            # Formatar datas
            if isinstance(inicio, str) and 'T' in inicio:
                inicio = inicio.split('T')[0]
            if isinstance(fim, str) and 'T' in fim:
                fim = fim.split('T')[0]
            
            response_parts.append(f"| {codigo} | {nome} | {potencia:,.2f} | {inicio} | {fim} |\n")
        
        if len(repotenciacoes) > 20:
            response_parts.append(f"\n*Exibindo 20 de {len(repotenciacoes)} repotenciações. Todas estão disponíveis no JSON.*\n")
        response_parts.append("\n")
    
    # Indisponibilidades
    indisponibilidades = tool_result.get("indisponibilidades")
    if indisponibilidades:
        response_parts.append("### 🔧 Indisponibilidades\n\n")
        response_parts.append("| Código | Nome Usina | Tipo | Taxa (%) | Data Início | Data Fim |\n")
        response_parts.append("|--------|------------|------|----------|-------------|----------|\n")
        
        for indis in indisponibilidades[:20]:
            codigo = indis.get('codigo_usina', 'N/A')
            nome = indis.get('nome_usina', 'N/A')
            tipo = indis.get('tipo', 'N/A')
            taxa = indis.get('modificacao', 0)
            inicio = indis.get('data_inicio', 'N/A')
            fim = indis.get('data_fim', 'N/A')
            
            # Formatar datas
            if isinstance(inicio, str) and 'T' in inicio:
                inicio = inicio.split('T')[0]
            if isinstance(fim, str) and 'T' in fim:
                fim = fim.split('T')[0]
            
            response_parts.append(f"| {codigo} | {nome} | {tipo} | {taxa:,.2f} | {inicio} | {fim} |\n")
        
        if len(indisponibilidades) > 20:
            response_parts.append(f"\n*Exibindo 20 de {len(indisponibilidades)} indisponibilidades. Todas estão disponíveis no JSON.*\n")
        response_parts.append("\n")
    
    # Nota sobre dados completos (já apresentados acima por tipo)
    dados_expansoes = tool_result.get("dados_expansoes", [])
    if dados_expansoes:
        response_parts.append("### 📋 Nota sobre Dados Completos\n\n")
        response_parts.append(f"*Todos os {len(dados_expansoes)} registros foram apresentados acima, agrupados por tipo de modificação. Dados completos também estão disponíveis no JSON para download.*\n\n")
    
    response_parts.append("---\n\n")
    response_parts.append("*Dados processados diretamente do arquivo EXPT.DAT usando tool pré-programada.*\n")
    
    response_text = "".join(response_parts)
    response_text = clean_response_text(response_text, max_emojis=2)
    return {"final_response": response_text}


def _format_modif_operacao_response(tool_result: dict, tool_used: str) -> dict:
    """
    Formata o resultado da ModifOperacaoTool em resposta Markdown.
    
    Args:
        tool_result: Resultado da execução da tool
        tool_used: Nome da tool usada
        
    Returns:
        Dict com final_response formatado
    """
    response_parts = []
    
    # Cabeçalho
    filtros = tool_result.get("filtros")
    
    response_parts.append("## ✅ Dados de Operação Hídrica do MODIF.DAT\n\n")
    response_parts.append(f"*Processado pela tool: **{tool_used}***\n\n")
    
    # Informações sobre filtros
    if filtros:
        response_parts.append("### 🔍 Filtros Aplicados\n\n")
        if 'usina' in filtros:
            usina_info = filtros['usina']
            response_parts.append(f"- **Usina**: {usina_info.get('nome')} (Código: {usina_info.get('codigo')})\n")
        if 'tipo_modificacao' in filtros:
            response_parts.append(f"- **Tipo de Modificação**: {filtros['tipo_modificacao']}\n")
        response_parts.append("\n")
    
    # Estatísticas gerais
    stats_geral = tool_result.get("stats_geral")
    if stats_geral:
        response_parts.append("### 📊 Resumo\n\n")
        response_parts.append(f"- **Total de tipos de modificação**: {stats_geral.get('total_tipos', 0)}\n")
        response_parts.append(f"- **Total de registros**: {stats_geral.get('total_registros', 0):,}\n")
        tipos = stats_geral.get('tipos_encontrados', [])
        if tipos:
            response_parts.append(f"- **Tipos encontrados**: {', '.join(tipos)}\n")
        response_parts.append("\n")
    
    # Dicionário de explicações para cada tipo
    explicacoes_tipos = {
        'VOLMIN': {
            'nome': 'Volume Mínimo Operativo',
            'descricao': 'Volume mínimo operativo da usina hidrelétrica. Pode ser especificado em H/h (hectômetros cúbicos) ou % (percentual do volume útil).',
            'unidade': 'H/h ou %'
        },
        'VOLMAX': {
            'nome': 'Volume Máximo Operativo',
            'descricao': 'Volume máximo operativo da usina hidrelétrica. Pode ser especificado em H/h (hectômetros cúbicos) ou % (percentual do volume útil).',
            'unidade': 'H/h ou %'
        },
        'VMAXT': {
            'nome': 'Volume Máximo com Data',
            'descricao': 'Volume máximo operativo com data de início. Modificação temporal que altera o volume máximo a partir de uma data específica. Referenciado ao final do período.',
            'unidade': 'H/h ou %'
        },
        'VMINT': {
            'nome': 'Volume Mínimo com Data',
            'descricao': 'Volume mínimo operativo com data de início. Modificação temporal que altera o volume mínimo a partir de uma data específica. Referenciado ao final do período.',
            'unidade': 'H/h ou %'
        },
        'VMINP': {
            'nome': 'Volume Mínimo com Penalidade',
            'descricao': 'Volume mínimo com adoção de penalidade, com data. Implementa mecanismo de aversão a risco. O valor considerado será o mais restritivo entre MODIF.DAT (por usina) e CURVA.DAT (por REE).',
            'unidade': 'H/h ou %'
        },
        'VAZMIN': {
            'nome': 'Vazão Mínima',
            'descricao': 'Vazão mínima obrigatória da usina. Pode ter até dois valores: requisito total e valor para relaxamento (opcional, menor que o primeiro).',
            'unidade': 'm³/s'
        },
        'VAZMINT': {
            'nome': 'Vazão Mínima com Data',
            'descricao': 'Vazão mínima obrigatória com data de início. Modificação temporal que altera a vazão mínima a partir de uma data específica.',
            'unidade': 'm³/s'
        },
        'VAZMAXT': {
            'nome': 'Vazão Máxima com Data',
            'descricao': 'Vazão máxima (defluência máxima) com data. Considerada apenas em períodos individualizados, se os flags apropriados estiverem habilitados no dger.dat.',
            'unidade': 'm³/s'
        },
        'CFUGA': {
            'nome': 'Canal de Fuga',
            'descricao': 'Nível do canal de fuga da usina. Modificação temporal que altera o nível do canal de fuga a partir de uma data específica. Referenciado ao início do período.',
            'unidade': 'm'
        },
        'CMONT': {
            'nome': 'Nível de Montante',
            'descricao': 'Nível de montante da usina. Modificação temporal que altera o nível de montante a partir de uma data específica. Permitido somente para usinas fio d\'água.',
            'unidade': 'm'
        },
        'TURBMAXT': {
            'nome': 'Turbinamento Máximo com Data',
            'descricao': 'Turbinamento máximo com data e por patamar. Considerado apenas em períodos individualizados, se os flags apropriados estiverem habilitados no dger.dat.',
            'unidade': 'm³/s'
        },
        'TURBMINT': {
            'nome': 'Turbinamento Mínimo com Data',
            'descricao': 'Turbinamento mínimo com data e por patamar. Considerado apenas em períodos individualizados, se os flags apropriados estiverem habilitados no dger.dat.',
            'unidade': 'm³/s'
        },
        'POTEFE': {
            'nome': 'Potência Efetiva',
            'descricao': 'Potência efetiva da usina hidrelétrica. Modificação da potência efetiva por conjunto de máquinas.',
            'unidade': 'MW'
        },
        'TEIF': {
            'nome': 'Taxa Esperada de Indisponibilidade Forçada',
            'descricao': 'Taxa esperada de indisponibilidade forçada da usina. Representa indisponibilidades não programadas (forçadas).',
            'unidade': '%'
        },
        'IP': {
            'nome': 'Indisponibilidade Programada',
            'descricao': 'Indisponibilidade programada da usina. Representa períodos de manutenção programada onde a usina não estará disponível.',
            'unidade': '%'
        },
        'NUMCNJ': {
            'nome': 'Número de Conjuntos de Máquinas',
            'descricao': 'Número de conjuntos de máquinas da usina. Modifica a quantidade de conjuntos de máquinas.',
            'unidade': 'unidade'
        },
        'NUMMAQ': {
            'nome': 'Número de Máquinas por Conjunto',
            'descricao': 'Número de máquinas por conjunto. Modifica a quantidade de máquinas em um conjunto específico.',
            'unidade': 'unidade'
        }
    }
    
    # Obter dados por tipo
    dados_por_tipo = tool_result.get("dados_por_tipo", {})
    
    if dados_por_tipo:
        # Para cada tipo, criar uma seção separada
        for tipo in sorted(dados_por_tipo.keys()):
            dados_tipo = dados_por_tipo[tipo]
            explicacao = explicacoes_tipos.get(tipo, {
                'nome': tipo,
                'descricao': f'Modificações do tipo {tipo}',
                'unidade': ''
            })
            
            response_parts.append(f"### 🔧 {explicacao['nome']} ({tipo})\n\n")
            response_parts.append(f"**Explicação**: {explicacao['descricao']}\n\n")
            response_parts.append(f"**Total de registros**: {len(dados_tipo)}\n\n")
            
            # Tabela com os dados deste tipo
            # Determinar colunas baseado no tipo
            if tipo in ['VOLMIN', 'VOLMAX', 'VMAXT', 'VMINT', 'VMINP']:
                response_parts.append("| Código | Nome Usina | Volume | Unidade | Data Início |\n")
                response_parts.append("|--------|------------|--------|---------|-------------|\n")
                
                for record in dados_tipo:
                    codigo = record.get('codigo', record.get('codigo_usina', 'N/A'))
                    nome = record.get('nome', record.get('nome_usina', 'N/A'))
                    volume = record.get('volume', 0)
                    unidade = record.get('unidade', 'N/A')
                    inicio = record.get('data_inicio', 'N/A')
                    
                    # Formatar data
                    if isinstance(inicio, str) and 'T' in inicio:
                        inicio = inicio.split('T')[0]
                    elif hasattr(inicio, 'date'):
                        inicio = inicio.date()
                    
                    response_parts.append(f"| {codigo} | {nome} | {volume:,.2f} | {unidade} | {inicio} |\n")
            
            elif tipo in ['VAZMIN', 'VAZMINT', 'VAZMAXT']:
                response_parts.append("| Código | Nome Usina | Vazão | Data Início |\n")
                response_parts.append("|--------|------------|-------|-------------|\n")
                
                for record in dados_tipo:
                    codigo = record.get('codigo', record.get('codigo_usina', 'N/A'))
                    nome = record.get('nome', record.get('nome_usina', 'N/A'))
                    vazao = record.get('vazao', 0)
                    inicio = record.get('data_inicio', 'N/A')
                    
                    # Formatar data
                    if isinstance(inicio, str) and 'T' in inicio:
                        inicio = inicio.split('T')[0]
                    elif hasattr(inicio, 'date'):
                        inicio = inicio.date()
                    
                    response_parts.append(f"| {codigo} | {nome} | {vazao:,.2f} m³/s | {inicio} |\n")
            
            elif tipo in ['CFUGA', 'CMONT']:
                response_parts.append("| Código | Nome Usina | Nível (m) | Data Início |\n")
                response_parts.append("|--------|------------|-----------|-------------|\n")
                
                for record in dados_tipo:
                    codigo = record.get('codigo', record.get('codigo_usina', 'N/A'))
                    nome = record.get('nome', record.get('nome_usina', 'N/A'))
                    nivel = record.get('nivel', 0)
                    inicio = record.get('data_inicio', 'N/A')
                    
                    # Formatar data
                    if isinstance(inicio, str) and 'T' in inicio:
                        inicio = inicio.split('T')[0]
                    elif hasattr(inicio, 'date'):
                        inicio = inicio.date()
                    
                    response_parts.append(f"| {codigo} | {nome} | {nivel:,.2f} | {inicio} |\n")
            
            elif tipo in ['TURBMAXT', 'TURBMINT']:
                response_parts.append("| Código | Nome Usina | Patamar | Turbinamento (m³/s) | Data Início |\n")
                response_parts.append("|--------|------------|---------|---------------------|-------------|\n")
                
                for record in dados_tipo:
                    codigo = record.get('codigo', record.get('codigo_usina', 'N/A'))
                    nome = record.get('nome', record.get('nome_usina', 'N/A'))
                    patamar = record.get('patamar', 'N/A')
                    turbinamento = record.get('turbinamento', 0)
                    inicio = record.get('data_inicio', 'N/A')
                    
                    # Formatar data
                    if isinstance(inicio, str) and 'T' in inicio:
                        inicio = inicio.split('T')[0]
                    elif hasattr(inicio, 'date'):
                        inicio = inicio.date()
                    
                    response_parts.append(f"| {codigo} | {nome} | {patamar} | {turbinamento:,.2f} | {inicio} |\n")
            
            elif tipo in ['NUMCNJ', 'NUMMAQ']:
                if tipo == 'NUMCNJ':
                    response_parts.append("| Código | Nome Usina | Número de Conjuntos |\n")
                    response_parts.append("|--------|------------|---------------------|\n")
                    
                    for record in dados_tipo:
                        codigo = record.get('codigo', record.get('codigo_usina', 'N/A'))
                        nome = record.get('nome', record.get('nome_usina', 'N/A'))
                        numero = record.get('numero', 'N/A')
                        response_parts.append(f"| {codigo} | {nome} | {numero} |\n")
                else:
                    response_parts.append("| Código | Nome Usina | Conjunto | Número de Máquinas |\n")
                    response_parts.append("|--------|------------|----------|-------------------|\n")
                    
                    for record in dados_tipo:
                        codigo = record.get('codigo', record.get('codigo_usina', 'N/A'))
                        nome = record.get('nome', record.get('nome_usina', 'N/A'))
                        conjunto = record.get('conjunto', 'N/A')
                        numero_maquinas = record.get('numero_maquinas', 'N/A')
                        response_parts.append(f"| {codigo} | {nome} | {conjunto} | {numero_maquinas} |\n")
            
            else:
                # Formato genérico
                response_parts.append("| Código | Nome Usina | Valor |\n")
                response_parts.append("|--------|------------|-------|\n")
                
                for record in dados_tipo:
                    codigo = record.get('codigo', record.get('codigo_usina', 'N/A'))
                    nome = record.get('nome', record.get('nome_usina', 'N/A'))
                    # Tentar encontrar qualquer valor numérico
                    valor = 'N/A'
                    for key, val in record.items():
                        if key not in ['codigo', 'codigo_usina', 'nome', 'nome_usina'] and isinstance(val, (int, float)):
                            valor = f"{val:,.2f}"
                            break
                    response_parts.append(f"| {codigo} | {nome} | {valor} |\n")
            
            response_parts.append("\n")
            
            # Estatísticas específicas deste tipo
            stats_por_tipo = tool_result.get("stats_por_tipo", [])
            stats_tipo = next((s for s in stats_por_tipo if s.get('tipo') == tipo), None)
            
            if stats_tipo and len(dados_tipo) > 1:
                valor_medio = stats_tipo.get('valor_medio', 0)
                valor_min = stats_tipo.get('valor_min', 0)
                valor_max = stats_tipo.get('valor_max', 0)
                unidade = stats_tipo.get('unidade', explicacao['unidade'])
                
                response_parts.append(f"**Estatísticas**:\n")
                response_parts.append(f"- Valor médio: {valor_medio:,.2f} {unidade}\n")
                response_parts.append(f"- Valor mínimo: {valor_min:,.2f} {unidade}\n")
                response_parts.append(f"- Valor máximo: {valor_max:,.2f} {unidade}\n")
                response_parts.append("\n")
            
            response_parts.append("---\n\n")
    
    # Estatísticas por usina
    stats_por_usina = tool_result.get("stats_por_usina", [])
    if stats_por_usina:
        response_parts.append("### 🏭 Modificações por Usina\n\n")
        response_parts.append("| Código | Nome Usina | Total Modificações | Tipos |\n")
        response_parts.append("|--------|------------|-------------------|-------|\n")
        
        for stat in stats_por_usina[:20]:  # Limitar a 20
            codigo = stat.get('codigo_usina', 'N/A')
            nome = stat.get('nome_usina', 'N/A')
            total = stat.get('total_modificacoes', 0)
            tipos = ', '.join(stat.get('tipos_modificacao', []))
            
            response_parts.append(f"| {codigo} | {nome} | {total} | {tipos} |\n")
        
        if len(stats_por_usina) > 20:
            response_parts.append(f"\n*Exibindo 20 de {len(stats_por_usina)} usinas. Todas estão disponíveis no JSON.*\n")
        response_parts.append("\n")
    
    response_parts.append("---\n\n")
    response_parts.append("*Dados processados diretamente do arquivo MODIF.DAT usando tool pré-programada.*\n")
    
    response_text = "".join(response_parts)
    response_text = clean_response_text(response_text, max_emojis=2)
    return {"final_response": response_text}
