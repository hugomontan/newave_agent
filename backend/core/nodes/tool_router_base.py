"""
Funções base compartilhadas para tool routers.
Contém a lógica comum de execução de tools usada por NEWAVE e DECOMP.
"""
from typing import Dict, Any, Optional, Callable
from backend.core.config import safe_print


def execute_tool(
    tool,
    tool_name: str,
    query: str,
    logger_prefix: str = "[TOOL ROUTER]",
    **kwargs
) -> Dict[str, Any]:
    """
    Executa uma tool e retorna o resultado formatado.
    Função compartilhada entre NEWAVE e DECOMP tool routers.
    
    Args:
        tool: Instância da tool a ser executada
        tool_name: Nome da tool (para logging)
        query: Query a ser passada para a tool
        logger_prefix: Prefixo para mensagens de log (ex: "[TOOL ROUTER]" ou "[TOOL ROUTER DECOMP]")
        **kwargs: Argumentos adicionais a serem passados para a tool (ex: forced_plant_code)
        
    Returns:
        Dict com:
        - tool_result: Dict - Resultado da execução da tool
        - tool_used: str - Nome da tool usada
        - tool_route: bool - True (indica que tool foi executada)
        - execution_result: Dict - Informações sobre a execução (success, stdout, stderr, return_code)
    """
    safe_print(f"{logger_prefix} Executando tool {tool_name}...")
    safe_print(f"{logger_prefix}   Query usada: {query[:100]}")
    if kwargs:
        safe_print(f"{logger_prefix}   Kwargs: {kwargs}")
    
    try:
        result = tool.execute(query, **kwargs)
        
        if result.get("success"):
            safe_print(f"{logger_prefix} [OK] Tool {tool_name} executada com sucesso")
            data_count = len(result.get('data', [])) if result.get('data') else 0
            safe_print(f"{logger_prefix} Registros retornados: {data_count}")
            
            return {
                "tool_result": result,
                "tool_used": tool_name,
                "tool_route": True,
                "execution_result": {
                    "success": True,
                    "stdout": f"Tool {tool_name} executada com sucesso. {result.get('summary', {}).get('total_registros', data_count)} registros processados.",
                    "stderr": "",
                    "return_code": 0
                }
            }
        else:
            safe_print(f"{logger_prefix} [AVISO] Tool {tool_name} executada mas retornou erro: {result.get('error')}")
            # Mesmo com erro, a tool foi tentada
            return {
                "tool_result": result,
                "tool_used": tool_name,
                "tool_route": True,
                "execution_result": {
                    "success": False,
                    "stdout": "",
                    "stderr": result.get("error", "Erro desconhecido na tool"),
                    "return_code": -1
                }
            }
    except Exception as e:
        safe_print(f"{logger_prefix} [ERRO] Erro ao executar tool {tool_name}: {e}")
        import traceback
        traceback.print_exc()
        return {
            "tool_result": {"success": False, "error": str(e)},
            "tool_used": tool_name,
            "tool_route": True,
            "execution_result": {
                "success": False,
                "stdout": "",
                "stderr": f"Erro ao executar tool: {str(e)}",
                "return_code": -1
            }
        }


def generate_disambiguation_response(
    query: str,
    top_tools: list,
    tool_short_descriptions: Dict[str, str],
    max_options: int = 3,
    logger_prefix: str = "[TOOL ROUTER]"
) -> Dict[str, Any]:
    """
    Gera resposta de disambiguation com descrições curtas fixas.
    Cada opção direciona diretamente para uma tool específica.
    
    Args:
        query: Query original do usuário
        top_tools: Lista de tuplas (tool, score) ordenadas por score
        tool_short_descriptions: Mapeamento de tool_name -> descrição curta
        max_options: Número máximo de opções a mostrar
        logger_prefix: Prefixo para mensagens de log
        
    Returns:
        Dict com tool_route, final_response e disambiguation
    """
    safe_print(f"{logger_prefix} Criando disambiguation com opcoes fixas...")
    
    # Limitar a máximo de opções
    tools_to_show = top_tools[:max_options]
    
    # Pergunta padrão
    question = "Preciso de mais informações, escolha a opção que se refere melhor a sua consulta:"
    
    safe_print(f"{logger_prefix} Query original: {query}")
    safe_print(f"{logger_prefix} Tools candidatas: {[t.get_name() for t, _ in tools_to_show]}")
    
    options = []
    for idx, (tool, score) in enumerate(tools_to_show, 1):
        tool_name = tool.get_name()
        # Usar descrição curta fixa do mapeamento
        friendly_desc = tool_short_descriptions.get(tool_name, tool_name)
        
        # Criar query no formato especial: __DISAMBIG__:ToolName:original_query
        # Isso permite que o backend identifique diretamente a tool sem novo semantic matching
        special_query = f"__DISAMBIG__:{tool_name}:{query}"
        
        safe_print(f"{logger_prefix}   Opcao {idx}: {tool_name} -> '{friendly_desc}'")
        safe_print(f"{logger_prefix}     Query especial: {special_query[:80]}")
        
        options.append({
            "label": friendly_desc,
            "query": special_query,  # Formato especial para identificação direta
            "tool_name": tool_name,
            "original_query": query  # Preservar query original
        })
    
    safe_print(f"{logger_prefix} [OK] Disambiguation criada com {len(options)} opcoes")
    
    return {
        "tool_route": False,
        "final_response": "",  # Vazio - frontend cria a mensagem
        "disambiguation": {
            "type": "tool_selection",
            "question": question,
            "options": options,
            "original_query": query
        }
    }


def parse_disambiguation_query(query: str) -> tuple[bool, Optional[str], Optional[str]]:
    """
    Verifica se a query é uma escolha de disambiguation e extrai as informações.
    
    Args:
        query: Query recebida
        
    Returns:
        Tupla (is_from_disambiguation, tool_name, original_query)
        - is_from_disambiguation: True se veio de disambiguation
        - tool_name: Nome da tool selecionada (ou None)
        - original_query: Query original (ou None)
    """
    # Verificar formato novo: __DISAMBIG__:ToolName:original_query
    if query.startswith("__DISAMBIG__:"):
        try:
            parts = query.split(":", 2)  # ["__DISAMBIG__", "ToolName", "original_query"]
            if len(parts) == 3:
                tool_name = parts[1].strip()
                original_query = parts[2].strip()
                return True, tool_name, original_query
        except Exception:
            pass
    
    # Verificar formato antigo: " - " na query
    if " - " in query:
        parts = query.split(" - ", 1)
        original_query = parts[0].strip()
        context = parts[1].strip() if len(parts) > 1 else ""
        return True, None, original_query  # tool_name será identificado pelo context
    
    return False, None, None


def find_tool_by_name(tool_name: str, tools: list):
    """
    Encontra uma tool pelo nome na lista de tools.
    
    Args:
        tool_name: Nome da tool a encontrar
        tools: Lista de tools disponíveis
        
    Returns:
        Tool encontrada ou None
    """
    for tool in tools:
        if tool.get_name() == tool_name:
            return tool
    return None


def generate_plant_correction_followup(
    tool_result: Dict[str, Any],
    original_query: str,
    all_plants: list = None
) -> Optional[Dict[str, Any]]:
    """
    Gera mensagem de follow-up se o resultado envolve uma usina específica.
    
    Args:
        tool_result: Resultado da execução da tool
        original_query: Query original do usuário
        all_plants: Lista completa de usinas disponíveis (opcional, será obtida do matcher se necessário)
        
    Returns:
        Dict com dados de plant_correction ou None se não aplicável
    """
    selected_plant = tool_result.get("selected_plant")
    if not selected_plant:
        return None
    
    safe_print(f"[TOOL ROUTER] Gerando follow-up de correção de usina para {selected_plant.get('type')} código {selected_plant.get('codigo')}")
    
    # Obter lista completa de usinas do matcher apropriado
    if all_plants is None:
        plant_type = selected_plant.get("type")
        all_plants = []
        try:
            if plant_type == "hydraulic":
                from backend.newave.utils.hydraulic_plant_matcher import get_hydraulic_plant_matcher
                matcher = get_hydraulic_plant_matcher()
                for codigo, (nome_arquivo, nome_completo, _) in matcher.code_to_names.items():
                    all_plants.append({
                        "codigo": codigo,
                        "nome": nome_arquivo,
                        "nome_completo": nome_completo if nome_completo else nome_arquivo
                    })
            elif plant_type == "thermal":
                from backend.newave.utils.thermal_plant_matcher import get_thermal_plant_matcher
                matcher = get_thermal_plant_matcher()
                for codigo, (nome_arquivo, nome_completo) in matcher.code_to_names.items():
                    all_plants.append({
                        "codigo": codigo,
                        "nome": nome_arquivo,
                        "nome_completo": nome_completo if nome_completo else nome_arquivo
                    })
        except Exception as e:
            safe_print(f"[TOOL ROUTER] [AVISO] Erro ao obter lista de usinas: {e}")
            all_plants = []  # Garantir que sempre seja uma lista vazia em caso de erro
    
    # Garantir que all_plants seja sempre uma lista
    if not isinstance(all_plants, list):
        all_plants = []
    
    return {
        "type": "plant_correction",
        "message": "Essa usina não condiz com sua busca?",
        "selected_plant": selected_plant,
        "all_plants": all_plants,
        "original_query": original_query
    }


def parse_plant_correction_query(query: str) -> tuple[bool, Optional[str], Optional[int], Optional[str]]:
    """
    Parseia query de correção de usina.
    
    Args:
        query: Query recebida
        
    Returns:
        Tupla (is_correction, tool_name, plant_code, original_query)
        - is_correction: True se é query de correção
        - tool_name: Nome da tool (ou None)
        - plant_code: Código da usina (ou None)
        - original_query: Query original (ou None)
    """
    if query.startswith("__PLANT_CORR__:"):
        try:
            parts = query.split(":", 3)  # ["__PLANT_CORR__", "ToolName", "codigo", "original_query"]
            if len(parts) == 4:
                tool_name = parts[1].strip()
                plant_code = int(parts[2].strip())
                original_query = parts[3].strip()
                return True, tool_name, plant_code, original_query
        except (ValueError, IndexError):
            pass
    
    return False, None, None, None
