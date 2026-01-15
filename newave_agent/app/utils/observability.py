"""
Modulo de observabilidade com Langfuse para rastrear chamadas LLM.
"""
from typing import Optional
from langfuse.langchain import CallbackHandler
from langfuse import Langfuse
from app.config import LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_HOST, safe_print


def get_langfuse_handler(
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
    trace_name: str = "newave-agent",
    metadata: Optional[dict] = None
) -> Optional[CallbackHandler]:
    """
    Retorna um callback handler do Langfuse para rastrear chamadas LLM.
    
    Args:
        session_id: ID da sessão (geralmente o deck_path ou session_id)
        user_id: ID do usuário (opcional)
        trace_name: Nome do trace no Langfuse
        metadata: Metadados adicionais para o trace
        
    Returns:
        CallbackHandler do Langfuse ou None se não configurado
    """
    safe_print("[LANGFUSE DEBUG] ===== INICIO: get_langfuse_handler =====")
    safe_print(f"[LANGFUSE DEBUG] Parametros recebidos:")
    safe_print(f"  - session_id: {session_id}")
    safe_print(f"  - user_id: {user_id}")
    safe_print(f"  - trace_name: {trace_name}")
    safe_print(f"  - metadata: {metadata}")
    
    # ETAPA 1: Verificar credenciais
    safe_print("[LANGFUSE DEBUG] ETAPA 1: Verificando credenciais...")
    safe_print(f"  - LANGFUSE_PUBLIC_KEY presente: {bool(LANGFUSE_PUBLIC_KEY)}")
    safe_print(f"  - LANGFUSE_PUBLIC_KEY valor: {LANGFUSE_PUBLIC_KEY[:20] + '...' if LANGFUSE_PUBLIC_KEY and len(LANGFUSE_PUBLIC_KEY) > 20 else LANGFUSE_PUBLIC_KEY}")
    safe_print(f"  - LANGFUSE_SECRET_KEY presente: {bool(LANGFUSE_SECRET_KEY)}")
    safe_print(f"  - LANGFUSE_SECRET_KEY valor: {LANGFUSE_SECRET_KEY[:20] + '...' if LANGFUSE_SECRET_KEY and len(LANGFUSE_SECRET_KEY) > 20 else LANGFUSE_SECRET_KEY}")
    safe_print(f"  - LANGFUSE_HOST: {LANGFUSE_HOST}")
    
    if not LANGFUSE_PUBLIC_KEY or not LANGFUSE_SECRET_KEY:
        safe_print("[LANGFUSE DEBUG] [ERRO] ETAPA 1 FALHOU: Credenciais nao configuradas")
        safe_print("[LANGFUSE DEBUG] ===== FIM: get_langfuse_handler (retornando None) =====")
        return None
    
    safe_print("[LANGFUSE DEBUG] [OK] ETAPA 1 OK: Credenciais presentes")
    
    # ETAPA 2: Configurar variaveis de ambiente (necessario para CallbackHandler)
    safe_print("[LANGFUSE DEBUG] ETAPA 2: Configurando variaveis de ambiente...")
    import os
    os.environ["LANGFUSE_PUBLIC_KEY"] = LANGFUSE_PUBLIC_KEY
    os.environ["LANGFUSE_SECRET_KEY"] = LANGFUSE_SECRET_KEY
    os.environ["LANGFUSE_HOST"] = LANGFUSE_HOST
    safe_print("[LANGFUSE DEBUG] [OK] ETAPA 2 OK: Variaveis de ambiente configuradas")
    
    # ETAPA 3: Criar cliente Langfuse para verificacao
    safe_print("[LANGFUSE DEBUG] ETAPA 3: Criando cliente Langfuse...")
    try:
        langfuse_client = Langfuse(
            public_key=LANGFUSE_PUBLIC_KEY,
            secret_key=LANGFUSE_SECRET_KEY,
            host=LANGFUSE_HOST,
        )
        safe_print("[LANGFUSE DEBUG] [OK] ETAPA 3 OK: Cliente Langfuse criado")
    except Exception as e:
        safe_print(f"[LANGFUSE DEBUG] [ERRO] ETAPA 3 FALHOU: Erro ao criar cliente: {e}")
        import traceback
        traceback.print_exc()
        safe_print("[LANGFUSE DEBUG] ===== FIM: get_langfuse_handler (retornando None) =====")
        return None
    
    # ETAPA 4: Criar CallbackHandler
    safe_print("[LANGFUSE DEBUG] ETAPA 4: Criando CallbackHandler...")
    try:
        # Na versao 3.x, o CallbackHandler usa apenas public_key e le secret_key do ambiente
        handler = CallbackHandler(
            public_key=LANGFUSE_PUBLIC_KEY,
            update_trace=True,  # Atualizar trace com input/output
        )
        safe_print("[LANGFUSE DEBUG] [OK] ETAPA 4 OK: CallbackHandler criado")
        safe_print(f"[LANGFUSE DEBUG] Handler type: {type(handler)}")
        safe_print(f"[LANGFUSE DEBUG] Handler attributes: {dir(handler)[:10]}")
    except Exception as e:
        safe_print(f"[LANGFUSE DEBUG] [ERRO] ETAPA 4 FALHOU: Erro ao criar handler: {e}")
        import traceback
        traceback.print_exc()
        safe_print("[LANGFUSE DEBUG] ===== FIM: get_langfuse_handler (retornando None) =====")
        return None
    
    # ETAPA 5: Configurar trace context se necessario
    safe_print("[LANGFUSE DEBUG] ETAPA 5: Configurando trace context...")
    try:
        if session_id or trace_name or metadata:
            # Tentar configurar via trace_context se disponivel
            trace_context = {}
            if session_id:
                trace_context["session_id"] = session_id
            if trace_name:
                trace_context["name"] = trace_name
            if metadata:
                trace_context["metadata"] = metadata
            
            safe_print(f"[LANGFUSE DEBUG] Trace context preparado: {trace_context}")
            # Nota: O CallbackHandler pode nao suportar todos esses parametros diretamente
            # Eles serao usados via variaveis de ambiente ou durante a execucao
    except Exception as e:
        safe_print(f"[LANGFUSE DEBUG] [AVISO] ETAPA 5 AVISO: Erro ao configurar trace context: {e}")
    
    safe_print(f"[LANGFUSE DEBUG] [OK] Handler final criado com sucesso")
    safe_print(f"[LANGFUSE DEBUG] Resumo:")
    safe_print(f"  - trace_name: {trace_name}")
    safe_print(f"  - session_id: {session_id}")
    safe_print(f"  - host: {LANGFUSE_HOST}")
    safe_print("[LANGFUSE DEBUG] ===== FIM: get_langfuse_handler (retornando handler) =====")
    return handler


def flush_langfuse():
    """
    Forca o envio de todos os eventos pendentes para o Langfuse.
    Util para chamar antes de encerrar a aplicacao.
    """
    try:
        from langfuse import Langfuse
        client = Langfuse(
            public_key=LANGFUSE_PUBLIC_KEY,
            secret_key=LANGFUSE_SECRET_KEY,
            host=LANGFUSE_HOST,
        )
        client.flush()
    except Exception as e:
        safe_print(f"[LANGFUSE] Erro ao fazer flush: {e}")

