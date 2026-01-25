"""
Utilitários para debug logging.
"""
import json
import os
from pathlib import Path
from backend.core.config import DEBUG_MODE


def write_debug_log(data: dict) -> None:
    """
    Escreve log de debug em arquivo.
    
    Args:
        data: Dicionário com dados do log
    """
    if not DEBUG_MODE:
        return
    
    try:
        # Caminho do arquivo de debug (na raiz do projeto)
        project_root = Path(__file__).parent.parent.parent.parent
        log_path = project_root / ".cursor" / "debug.log"
        log_dir = log_path.parent
        
        # Criar diretório se não existir
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Escrever no arquivo
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(data) + '\n')
    except Exception:
        # Silenciosamente ignorar erros de log para não interromper o fluxo
        pass
