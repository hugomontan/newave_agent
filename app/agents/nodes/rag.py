import json
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from app.agents.state import AgentState
from app.rag.vectorstore import similarity_search
from app.rag.indexer import load_specific_documentation, NEWAVE_FILES
from app.config import RAG_TOP_K, OPENAI_API_KEY, OPENAI_MODEL


# Prompt para seleção inicial de arquivos candidatos
FILE_SELECTOR_PROMPT = """Você é um especialista em arquivos NEWAVE.

Baseado na pergunta do usuário e no contexto fornecido, selecione os arquivos NEWAVE candidatos para responder a pergunta.

ARQUIVOS DISPONÍVEIS:
{available_files}

CONTEXTO DA DOCUMENTAÇÃO:
{context}

PERGUNTA DO USUÁRIO:
{query}

REGRAS:
1. Selecione no MÍNIMO 1 e no MÁXIMO 3 arquivos candidatos
2. ORDENE por relevância (mais provável primeiro)
3. HIDR.DAT contém CADASTRO (potência, volumes), NÃO contém geração
4. Dados de geração vêm de resultados do modelo, não de arquivos de entrada

Responda APENAS com JSON:
{{"arquivos": ["arquivo1.dat", "arquivo2.dat"], "justificativa": "breve explicação"}}
"""


# Prompt para validação do arquivo e seleção de colunas
VALIDATION_PROMPT = """Você é um especialista em análise de dados NEWAVE.

Analise se o arquivo abaixo pode responder à pergunta do usuário.

PERGUNTA DO USUÁRIO:
{query}

DOCUMENTAÇÃO DO ARQUIVO {file_name}:
{documentation}

ANÁLISE REQUERIDA:
1. Este arquivo contém os dados necessários para responder a pergunta?
2. Se sim, quais colunas/propriedades específicas devem ser usadas?
3. Se não, explique brevemente por quê.

Responda APENAS com JSON no formato:
{{
    "arquivo_util": true/false,
    "colunas_relevantes": ["coluna1", "coluna2"],
    "classe_inewave": "NomeClasse",
    "propriedade_principal": "nome_propriedade",
    "motivo": "explicação breve"
}}
"""


# Prompt para fallback quando nenhum arquivo é útil
FALLBACK_PROMPT = """Você é um assistente especializado em análise de decks NEWAVE.

O usuário fez uma pergunta que não pode ser respondida com os arquivos disponíveis:
"{query}"

Arquivos tentados: {tried_files}
Motivos de rejeição: {rejection_reasons}

Gere uma resposta amigável explicando:
1. Por que a pergunta não pode ser respondida com os dados disponíveis
2. O que o sistema PODE fazer (listar capacidades)
3. Sugestões de perguntas válidas

CAPACIDADES DO SISTEMA:
- Consultar cadastro de usinas hidrelétricas (HIDR.DAT): potências, volumes, características físicas
- Consultar manutenções de térmicas (MANUTT.DAT): datas, potências, durações
- Consultar custos de térmicas (CLAST.DAT): custos por classe, tipos de combustível
- Consultar demandas e mercado (SISTEMA.DAT): demandas por submercado e patamar
- Consultar vazões históricas (VAZOES.DAT): séries de vazões por posto
- Consultar configuração de hidrelétricas (CONFHD.DAT): REEs, volumes iniciais
- Consultar REEs (REE.DAT): submercados associados
- Consultar expansões hidrelétricas (EXPH.DAT) e térmicas (EXPT.DAT)
- Consultar restrições de intercâmbio (AGRINT.DAT)

SUGESTÕES DE PERGUNTAS:
- "Quais são as usinas hidrelétricas com maior potência instalada?"
- "Quais térmicas têm manutenção programada?"
- "Qual o custo das classes térmicas?"
- "Qual a demanda do submercado Sudeste?"
- "Quais são as vazões históricas do posto 1?"

Responda de forma amigável e construtiva.
"""


def select_candidate_files(query: str, context: str) -> list[str]:
    """Seleciona arquivos candidatos baseado na query e contexto do abstract."""
    llm = ChatOpenAI(api_key=OPENAI_API_KEY, model=OPENAI_MODEL, temperature=0)
    
    available_files = ", ".join(NEWAVE_FILES.keys())
    
    prompt = ChatPromptTemplate.from_messages([("human", FILE_SELECTOR_PROMPT)])
    chain = prompt | llm
    
    result = chain.invoke({
        "available_files": available_files,
        "context": context,
        "query": query
    })
    
    try:
        content = result.content.strip()
        if "{" in content and "}" in content:
            json_str = content[content.find("{"):content.rfind("}") + 1]
            parsed = json.loads(json_str)
            files = parsed.get("arquivos", [])
            valid_files = [f.lower() for f in files if f.lower() in NEWAVE_FILES]
            if valid_files:
                return valid_files[:3]
    except (json.JSONDecodeError, KeyError, TypeError):
        pass
    
    # Fallback baseado em palavras-chave
    query_lower = query.lower()
    if any(w in query_lower for w in ["hidrelétrica", "hidr", "volume", "potência instalada", "usina hidro"]):
        return ["hidr.dat", "confhd.dat"]
    elif any(w in query_lower for w in ["térmica", "term", "manutenção", "custo"]):
        return ["clast.dat", "adterm.dat", "manutt.dat"]
    elif any(w in query_lower for w in ["vazão", "vazoes", "hidrologia"]):
        return ["vazoes.dat"]
    elif any(w in query_lower for w in ["demanda", "mercado", "subsistema"]):
        return ["sistema.dat", "ree.dat"]
    return ["hidr.dat"]


def validate_file_for_query(query: str, file_name: str, documentation: str) -> dict:
    """Valida se um arquivo pode responder à query e retorna colunas relevantes."""
    llm = ChatOpenAI(api_key=OPENAI_API_KEY, model=OPENAI_MODEL, temperature=0)
    
    prompt = ChatPromptTemplate.from_messages([("human", VALIDATION_PROMPT)])
    chain = prompt | llm
    
    result = chain.invoke({
        "query": query,
        "file_name": file_name.upper(),
        "documentation": documentation[:8000]  # Limitar para não exceder contexto
    })
    
    try:
        content = result.content.strip()
        if "{" in content and "}" in content:
            json_str = content[content.find("{"):content.rfind("}") + 1]
            return json.loads(json_str)
    except (json.JSONDecodeError, KeyError, TypeError):
        pass
    
    return {"arquivo_util": False, "motivo": "Erro ao analisar arquivo"}


def generate_fallback_response(query: str, tried_files: list[str], rejection_reasons: list[str]) -> str:
    """Gera resposta de fallback quando nenhum arquivo é útil."""
    llm = ChatOpenAI(api_key=OPENAI_API_KEY, model=OPENAI_MODEL, temperature=0.3)
    
    prompt = ChatPromptTemplate.from_messages([("human", FALLBACK_PROMPT)])
    chain = prompt | llm
    
    result = chain.invoke({
        "query": query,
        "tried_files": ", ".join(tried_files),
        "rejection_reasons": "; ".join(rejection_reasons)
    })
    
    return result.content


def rag_retriever_node(state: AgentState) -> dict:
    """
    Node que implementa RAG com Self-Reflection:
    
    1. Busca no abstract para selecionar arquivos candidatos
    2. Para cada arquivo candidato:
       - Carrega documentação específica
       - Valida se o arquivo responde à pergunta
       - Se sim, retorna colunas relevantes
       - Se não, tenta próximo arquivo
    3. Se nenhum arquivo servir, retorna sugestões
    """
    query = state["query"]
    
    # ============================================
    # ESTÁGIO 1: Buscar no abstract e selecionar candidatos
    # ============================================
    abstract_docs = similarity_search(query, k=RAG_TOP_K)
    abstract_context = "\n\n".join([doc.page_content for doc in abstract_docs])
    
    candidate_files = select_candidate_files(query, abstract_context)
    
    # ============================================
    # ESTÁGIO 2: Validação iterativa dos arquivos
    # ============================================
    tried_files = []
    rejection_reasons = []
    validated_file = None
    validation_result = None
    specific_documentation = None
    
    for file_name in candidate_files:
        tried_files.append(file_name)
        
        # Carregar documentação específica
        doc_content = load_specific_documentation([file_name])
        
        # Validar se o arquivo serve para a query
        result = validate_file_for_query(query, file_name, doc_content)
        
        if result.get("arquivo_util", False):
            validated_file = file_name
            validation_result = result
            specific_documentation = doc_content
            break
        else:
            rejection_reasons.append(f"{file_name}: {result.get('motivo', 'Não aplicável')}")
    
    # ============================================
    # ESTÁGIO 3: Preparar resposta
    # ============================================
    
    if validated_file and validation_result:
        # Arquivo válido encontrado - retornar documentação focada
        relevant_docs = []
        
        # Adicionar contexto geral
        relevant_docs.append(f"""
=== ARQUIVO SELECIONADO: {validated_file.upper()} ===
Classe inewave: {validation_result.get('classe_inewave', 'N/A')}
Propriedade principal: {validation_result.get('propriedade_principal', 'N/A')}
Colunas relevantes: {', '.join(validation_result.get('colunas_relevantes', []))}
Motivo da seleção: {validation_result.get('motivo', 'N/A')}
=== FIM DO RESUMO ===
""")
        
        # Adicionar documentação específica completa
        relevant_docs.append(f"""
=== DOCUMENTAÇÃO COMPLETA DO ARQUIVO ===
{specific_documentation}
=== FIM DA DOCUMENTAÇÃO ===
""")
        
        return {
            "relevant_docs": relevant_docs,
            "selected_files": [validated_file],
            "validation_result": validation_result,
            "rag_status": "success"
        }
    
    else:
        # Nenhum arquivo válido - gerar fallback
        fallback_response = generate_fallback_response(query, tried_files, rejection_reasons)
        
        return {
            "relevant_docs": [],
            "selected_files": [],
            "validation_result": None,
            "rag_status": "fallback",
            "fallback_response": fallback_response,
            "tried_files": tried_files,
            "rejection_reasons": rejection_reasons
        }


def rag_simple_node(state: AgentState) -> dict:
    """
    RAG simplificado: apenas busca semântica no abstract.md
    Usado quando tools não conseguem responder à query.
    
    Retorna apenas o contexto do abstract para o Coder, sem validação iterativa.
    Isso economiza tempo e custo quando não há tool disponível.
    
    Args:
        state: Estado do agente
        
    Returns:
        Dict com:
        - relevant_docs: Lista com contexto do abstract
        - rag_status: "success" (sempre, pois abstract sempre existe)
    """
    query = state["query"]
    
    print("[RAG SIMPLE] ===== INÍCIO: rag_simple_node =====")
    print(f"[RAG SIMPLE] Query: {query[:100]}")
    
    try:
        # Apenas busca semântica no abstract (sem validação iterativa)
        abstract_docs = similarity_search(query, k=RAG_TOP_K)
        abstract_context = "\n\n".join([doc.page_content for doc in abstract_docs])
        
        print(f"[RAG SIMPLE] ✅ {len(abstract_docs)} documentos do abstract encontrados")
        print(f"[RAG SIMPLE] Contexto preparado para Coder ({len(abstract_context)} caracteres)")
        print("[RAG SIMPLE] ===== FIM: rag_simple_node =====")
        
        return {
            "relevant_docs": [abstract_context],
            "rag_status": "success"
        }
    except Exception as e:
        print(f"[RAG SIMPLE] ❌ Erro ao buscar no abstract: {e}")
        import traceback
        traceback.print_exc()
        # Retornar vazio em caso de erro - coder pode tentar sem contexto
        return {
            "relevant_docs": [],
            "rag_status": "success"  # Ainda é success, apenas sem docs
        }