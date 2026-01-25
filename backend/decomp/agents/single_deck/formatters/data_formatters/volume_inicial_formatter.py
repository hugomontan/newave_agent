"""
Formatter específico para consultas de volume inicial/nível de partida de usinas hidrelétricas.
Módulo separado e modularizado para volume inicial.
"""

from typing import Dict, Any, Optional
from backend.decomp.agents.single_deck.formatters.base import SingleDeckFormatter
from backend.decomp.agents.single_deck.formatters.visualizations.volume_inicial_visualization import (
    create_volume_inicial_visualization
)


class VolumeInicialFormatter(SingleDeckFormatter):
    """
    Formatter específico para resultados de volume inicial/nível de partida.
    Trabalha em conjunto com o módulo de visualização separado.
    """
    
    def can_format(self, tool_name: str, result_structure: Dict[str, Any]) -> bool:
        """
        Verifica se pode formatar resultados de volume inicial.
        
        Verifica se:
        1. É a tool UHUsinasHidrelétricasTool
        2. O resultado contém 'volume_inicial' (estrutura específica de volume inicial)
        """
        if tool_name != "UHUsinasHidrelétricasTool":
            return False
        
        # Verificar se tem a estrutura específica de volume inicial
        return "volume_inicial" in result_structure and "usina" in result_structure
    
    def get_priority(self) -> int:
        """Prioridade alta para esta tool específica."""
        return 95  # Maior que o formatter genérico UH
    
    def format_response(
        self,
        tool_result: Dict[str, Any],
        tool_name: str,
        query: str,
        deck_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Formata resposta de volume inicial usando módulo de visualização separado.
        
        Args:
            tool_result: Resultado da execução da tool
            tool_name: Nome da tool
            query: Query original do usuário
            
        Returns:
            Dict com final_response e visualization_data
        """
        if not tool_result.get("success", False):
            error = tool_result.get("error", "Erro desconhecido")
            return {
                "final_response": f"## Erro ao Consultar Volume Inicial\n\n{error}",
                "visualization_data": None
            }
        
        volume_inicial = tool_result.get("volume_inicial")
        usina = tool_result.get("usina", {})
        unidade = tool_result.get("unidade", "%")
        descricao = tool_result.get("descricao", "")
        
        # Verificar se volume_inicial está disponível
        if volume_inicial is None:
            return {
                "final_response": "## Erro ao Consultar Volume Inicial\n\nVolume inicial não disponível.",
                "visualization_data": None
            }
        
        # Extrair data do deck_path se disponível (formato: DCYYYYMM-semX_extracted)
        data_deck = None
        if deck_path:
            try:
                import os
                import re
                from datetime import datetime, timedelta
                deck_name = os.path.basename(deck_path)
                # Tentar extrair ano, mês e semana do nome do deck (ex: DC202601-sem3_extracted)
                match = re.search(r'DC(\d{4})(\d{2})-sem(\d+)', deck_name)
                if match:
                    ano = int(match.group(1))
                    mes = int(match.group(2))
                    semana = int(match.group(3))
                    
                    # Calcular a quinta-feira correspondente à semana do mês
                    # Semana 1 = primeira quinta-feira do mês
                    # Semana 2 = segunda quinta-feira do mês
                    # etc.
                    
                    # Encontrar a primeira quinta-feira do mês (dia da semana 3 = quinta-feira)
                    primeiro_dia = datetime(ano, mes, 1)
                    weekday_primeiro = primeiro_dia.weekday()  # 0=segunda, 1=terça, 2=quarta, 3=quinta, 4=sexta, 5=sábado, 6=domingo
                    
                    # Calcular quantos dias até a primeira quinta-feira do mês
                    # Fórmula: (3 - weekday) % 7, mas se resultado for 0 e não for quinta, usar 7
                    dias_ate_quinta = (3 - weekday_primeiro) % 7
                    if dias_ate_quinta == 0 and weekday_primeiro != 3:
                        dias_ate_quinta = 7
                    
                    primeira_quinta = primeiro_dia + timedelta(days=dias_ate_quinta)
                    
                    # Adicionar (semana - 1) semanas para obter a quinta-feira da semana desejada
                    quinta_desejada = primeira_quinta + timedelta(weeks=(semana - 1))
                    
                    data_deck = quinta_desejada.strftime("%Y-%m-%d")
                    
                    from backend.decomp.config import safe_print
                    safe_print(f"[VOLUME INICIAL FORMATTER] Deck: {deck_name} -> Data calculada: {data_deck} (semana {semana}, quinta-feira)")
            except Exception as e:
                from backend.decomp.config import safe_print
                safe_print(f"[VOLUME INICIAL FORMATTER] Erro ao calcular data do deck: {e}")
                pass
        
        # Usar módulo de visualização separado - retorna apenas a tabela com 4 colunas
        visualization_data = create_volume_inicial_visualization(
            volume_inicial=volume_inicial,
            usina=usina,
            unidade=unidade,
            tool_name=tool_name,
            data=data_deck
        )
        
        # DEBUG: Verificar estrutura retornada
        from backend.decomp.config import safe_print
        safe_print(f"[VOLUME INICIAL FORMATTER] ✅ Tabela criada com {len(visualization_data.get('table', []))} linha(s)")
        if visualization_data.get('table'):
            safe_print(f"[VOLUME INICIAL FORMATTER] Colunas na tabela: {list(visualization_data['table'][0].keys())}")
        
        # Resposta mínima - toda informação está na tabela
        nome_usina = usina.get("nome", f"Usina {usina.get('codigo', 'N/A')}")
        response_parts = []
        response_parts.append(f"## Volume Inicial - {nome_usina}\n\n")
        
        return {
            "final_response": "".join(response_parts),
            "visualization_data": visualization_data
        }
