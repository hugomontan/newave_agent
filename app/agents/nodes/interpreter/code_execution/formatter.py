"""
Formatação de resultados de execução de código Python.
"""

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from app.config import OPENAI_API_KEY, OPENAI_MODEL
from app.utils.text_utils import clean_response_text
from ..prompts import INTERPRETER_SYSTEM_PROMPT, INTERPRETER_USER_PROMPT


def format_code_execution_response(
    execution_result: dict,
    generated_code: str,
    query: str,
    relevant_docs: list,
    retry_count: int = 0,
    max_retries: int = 3
) -> dict:
    """
    Formata o resultado da execução de código Python usando LLM.
    
    Args:
        execution_result: Resultado da execução do código
        generated_code: Código Python gerado
        query: Query original do usuário
        relevant_docs: Lista de documentos relevantes
        retry_count: Número de tentativas de execução
        max_retries: Número máximo de tentativas
        
    Returns:
        Dict com final_response formatado
    """
    # Preparar output da execução
    if execution_result.get("success"):
        exec_output = execution_result.get("stdout", "Sem output")
        # Remover dados JSON se presentes
        if "---JSON_DATA_START---" in exec_output:
            parts = exec_output.split("---JSON_DATA_START---")
            exec_output = parts[0].strip()
    else:
        exec_output = f"ERRO: {execution_result.get('stderr', 'Erro desconhecido')}"
    
    # Inicializar LLM
    llm = ChatOpenAI(
        api_key=OPENAI_API_KEY,
        model=OPENAI_MODEL,
        temperature=0.3
    )
    
    # Criar prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", INTERPRETER_SYSTEM_PROMPT),
        ("human", INTERPRETER_USER_PROMPT)
    ])
    
    # Preparar documentos relevantes
    relevant_docs_str = "\n\n---\n\n".join(relevant_docs or [])
    
    # Invocar LLM
    chain = prompt | llm
    
    response = chain.invoke({
        "query": query,
        "relevant_docs": relevant_docs_str,
        "generated_code": generated_code,
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

