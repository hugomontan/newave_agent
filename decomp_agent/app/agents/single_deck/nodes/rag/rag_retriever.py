"""
RAG Retriever Node - busca e valida arquivos DECOMP.
Para Single Deck Agent DECOMP.
"""
import json
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from decomp_agent.app.rag.vectorstore import similarity_search
from decomp_agent.app.rag.indexer import load_specific_documentation, DECOMP_FILES
from decomp_agent.app.config import RAG_TOP_K, OPENAI_API_KEY, OPENAI_MODEL, safe_print
from decomp_agent.app.agents.single_deck.state import SingleDeckState


# Prompt para seleção inicial de arquivos candidatos
FILE_SELECTOR_PROMPT = """Você é um especialista em arquivos DECOMP.

Baseado na pergunta do usuário e no contexto fornecido, selecione os arquivos DECOMP candidatos para responder a pergunta.

ARQUIVOS DISPONÍVEIS:
{available_files}

CONTEXTO DA DOCUMENTAÇÃO:
{context}

PERGUNTA DO USUÁRIO:
{query}

REGRAS:
1. Selecione no MÍNIMO 1 e no MÁXIMO 3 arquivos candidatos
2. ORDENE por relevância (mais provável primeiro)
3. O arquivo principal é dadger.rvx que contém todos os dados de entrada

Responda APENAS com JSON:
{{"arquivos": ["arquivo1.rvx", "arquivo2.rvx"], "justificativa": "breve explicação"}}
"""


# Prompt para validação do arquivo e seleção de colunas
VALIDATION_PROMPT = """Você é um especialista em análise de dados DECOMP.

Analise se o arquivo abaixo pode responder à pergunta do usuário.

PERGUNTA DO USUÁRIO:
{query}

DOCUMENTAÇÃO DO ARQUIVO {file_name}:
{documentation}

ANÁLISE REQUERIDA:
1. Este arquivo contém os dados necessários para responder a pergunta?
2. Se sim, quais métodos/propriedades específicas devem ser usadas?
3. Se não, explique brevemente por quê.

Responda APENAS com JSON no formato:
{{
    "arquivo_util": true/false,
    "metodos_relevantes": ["metodo1", "metodo2"],
    "classe_idecomp": "NomeClasse",
    "motivo": "explicação breve"
}}
"""


# Prompt para fallback quando nenhum arquivo é útil
FALLBACK_PROMPT = """Você é um assistente especializado em análise de decks DECOMP.

O usuário fez uma pergunta que não pode ser respondida com os arquivos disponíveis:
"{query}"

Arquivos tentados: {tried_files}
Motivos de rejeição: {rejection_reasons}

Gere uma resposta amigável explicando:
1. Por que a pergunta não pode ser respondida com os dados disponíveis
2. O que o sistema PODE fazer (listar capacidades)
3. Sugestões de perguntas válidas

CAPACIDADES DO SISTEMA:
- Consultar cadastro de usinas hidrelétricas (dadger.uh())
- Consultar usinas térmicas (dadger.ct())
- Consultar limites de intercâmbio (dadger.ia())
- Consultar demanda e patamares (dadger.dp())
- Consultar restrições elétricas (dadger.re(), dadger.lu())
- Consultar restrições de volume (dadger.hv(), dadger.lv())
- Consultar restrições de vazão (dadger.hq(), dadger.lq())
- Consultar manutenções (dadger.mp(), dadger.mt())
- Consultar ENA (dadger.ea(), dadger.es())

SUGESTÕES DE PERGUNTAS:
- "Quais são as usinas hidrelétricas do DECOMP?"
- "Quais são os limites de intercâmbio?"
- "Quais são as restrições elétricas?"
- "Quais são as manutenções programadas?"

Responda de forma amigável e construtiva.
"""


def select_candidate_files(query: str, context: str) -> list[str]:
    """Seleciona arquivos candidatos baseado na query e contexto do abstract."""
    llm = ChatOpenAI(api_key=OPENAI_API_KEY, model=OPENAI_MODEL, temperature=0)
    
    # Por enquanto, sempre retornar dadger.rvx (arquivo principal DECOMP)
    # Quando houver mais arquivos, expandir esta lógica
    available_files = "dadger.rvx"
    
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
            # Validar arquivos (por enquanto apenas dadger.rvx)
            valid_files = [f.lower() for f in files if "dadger" in f.lower() or f.lower() == "dadger.rvx"]
            if valid_files:
                return ["dadger.rvx"]  # Sempre retornar dadger.rvx
    except (json.JSONDecodeError, KeyError, TypeError):
        pass
    
    # Fallback: sempre retornar dadger.rvx
    return ["dadger.rvx"]


def validate_file_for_query(query: str, file_name: str, documentation: str) -> dict:
    """Valida se um arquivo pode responder à query e retorna métodos relevantes."""
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


def rag_retriever_node(state: SingleDeckState) -> dict:
    """
    Node que implementa RAG com Self-Reflection para DECOMP.
    
    Args:
        state: Estado do Single Deck Agent DECOMP
    """
    query = state["query"]
    
    # ESTÁGIO 1: Buscar no abstract e selecionar candidatos
    abstract_docs = similarity_search(query, k=RAG_TOP_K)
    abstract_context = "\n\n".join([doc.page_content for doc in abstract_docs])
    
    candidate_files = select_candidate_files(query, abstract_context)
    
    # ESTÁGIO 2: Validação iterativa dos arquivos
    tried_files = []
    rejection_reasons = []
    validated_file = None
    validation_result = None
    specific_documentation = None
    
    for file_name in candidate_files:
        tried_files.append(file_name)
        
        # Carregar documentação específica (se existir)
        try:
            doc_content = load_specific_documentation([file_name])
        except (FileNotFoundError, ValueError):
            # Se não há documentação específica, usar apenas abstract
            doc_content = abstract_context
        
        # Validar se o arquivo serve para a query
        result = validate_file_for_query(query, file_name, doc_content)
        
        if result.get("arquivo_util", False):
            validated_file = file_name
            validation_result = result
            specific_documentation = doc_content
            break
        else:
            rejection_reasons.append(f"{file_name}: {result.get('motivo', 'Não aplicável')}")
    
    # ESTÁGIO 3: Preparar resposta
    if validated_file and validation_result:
        # Arquivo válido encontrado
        relevant_docs = []
        
        relevant_docs.append(f"""
=== ARQUIVO SELECIONADO: {validated_file.upper()} ===
Classe idecomp: {validation_result.get('classe_idecomp', 'Dadger')}
Métodos relevantes: {', '.join(validation_result.get('metodos_relevantes', []))}
Motivo da seleção: {validation_result.get('motivo', 'N/A')}
=== FIM DO RESUMO ===
""")
        
        if specific_documentation:
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


def rag_simple_node(state: SingleDeckState) -> dict:
    """
    RAG simplificado: apenas busca semântica no abstract.md
    Usado quando tools não conseguem responder à query.
    
    Args:
        state: Estado do Single Deck Agent DECOMP
        
    Returns:
        Dict com:
        - relevant_docs: Lista com contexto do abstract
        - rag_status: "success"
    """
    query = state["query"]
    
    safe_print("[RAG SIMPLE DECOMP] ===== INÍCIO: rag_simple_node =====")
    safe_print(f"[RAG SIMPLE DECOMP] Query: {query[:100]}")
    
    try:
        # Apenas busca semântica no abstract (sem validação iterativa)
        abstract_docs = similarity_search(query, k=RAG_TOP_K)
        abstract_context = "\n\n".join([doc.page_content for doc in abstract_docs])
        
        safe_print(f"[RAG SIMPLE DECOMP] ✅ {len(abstract_docs)} documentos do abstract encontrados")
        safe_print(f"[RAG SIMPLE DECOMP] Contexto preparado para Coder ({len(abstract_context)} caracteres)")
        safe_print("[RAG SIMPLE DECOMP] ===== FIM: rag_simple_node =====")
        
        return {
            "relevant_docs": [abstract_context],
            "rag_status": "success"
        }
    except Exception as e:
        safe_print(f"[RAG SIMPLE DECOMP] ❌ Erro ao buscar no abstract: {e}")
        import traceback
        traceback.print_exc()
        return {
            "relevant_docs": [],
            "rag_status": "success"
        }
