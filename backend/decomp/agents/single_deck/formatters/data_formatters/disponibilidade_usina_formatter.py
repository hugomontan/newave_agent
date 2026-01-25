"""
Formatter específico para DisponibilidadeUsinaTool (Cálculo de Disponibilidade).
"""

from typing import Dict, Any, List, Optional
from backend.decomp.agents.single_deck.formatters.base import SingleDeckFormatter
from backend.decomp.config import safe_print


class DisponibilidadeUsinaFormatter(SingleDeckFormatter):
    """
    Formatter específico para resultados da DisponibilidadeUsinaTool.
    Formata dados do cálculo de disponibilidade total de usina termelétrica.
    """
    
    def can_format(self, tool_name: str, result_structure: Dict[str, Any]) -> bool:
        """Verifica se pode formatar resultados da DisponibilidadeUsinaTool."""
        return tool_name == "DisponibilidadeUsinaTool" or "disponibilidade" in tool_name.lower()
    
    def get_priority(self) -> int:
        """Prioridade alta para esta tool específica."""
        return 90
    
    def format_response(
        self,
        tool_result: Dict[str, Any],
        tool_name: str,
        query: str,
    ) -> Dict[str, Any]:
        """
        Formata resposta da DisponibilidadeUsinaTool.
        """
        if not tool_result.get("success", False):
            error = tool_result.get("error", "Erro desconhecido")
            return {
                "final_response": f"❌ **Erro ao Calcular Disponibilidade**\n\n{error}",
                "visualization_data": None,
            }
        
        disponibilidade_total = tool_result.get("disponibilidade_total")
        usina = tool_result.get("usina", {})
        detalhes = tool_result.get("detalhes", {})
        calculo = tool_result.get("calculo", {})
        
        # Verificar explicitamente se é None (0 é um valor válido!)
        if disponibilidade_total is None:
            return {
                "final_response": "❌ **Erro ao Calcular Disponibilidade**\n\nResultado do cálculo não disponível.",
                "visualization_data": None,
            }
        
        nome_usina = usina.get("nome", f"Usina {usina.get('codigo', 'N/A')}")
        codigo_usina = usina.get("codigo")
        response_parts: List[str] = []
        response_parts.append(f"## Disponibilidade Total - {nome_usina}\n\n")
        response_parts.append(f"Código: {codigo_usina} | Submercado: {usina.get('submercado')}\n\n")
        
        # Preparar dados de visualização.
        # IMPORTANTE: o componente React hoje espera o campo 'inflexibilidade' em detalhes_patamares,
        # então mapeamos disponibilidade -> inflexibilidade para reaproveitar o mesmo tipo.
        detalhes_patamares: List[Dict[str, Any]] = []
        for patamar_nome, patamar_label in [("pesada", "PESADA"), ("media", "MEDIA"), ("leve", "LEVE")]:
            patamar_data = detalhes.get(patamar_nome, {})
            detalhes_patamares.append(
                {
                    "patamar": patamar_label,
                    "patamar_numero": {"pesada": 1, "media": 2, "leve": 3}[patamar_nome],
                    "inflexibilidade": patamar_data.get("disponibilidade"),
                    "duracao": patamar_data.get("duracao"),
                }
            )
        
        visualization_data = {
            "disponibilidade_total": disponibilidade_total,
            "detalhes_patamares": detalhes_patamares,
            "usina": usina,
            "calculo": calculo,
            "visualization_type": "disponibilidade_calculo",
            "tool_name": tool_name,
        }
        
        return {
            "final_response": "".join(response_parts),
            "visualization_data": visualization_data,
        }

"""
Formatter específico para InflexibilidadeUsinaTool (Cálculo de Inflexibilidade).
"""

from typing import Dict, Any, List, Optional
from backend.decomp.agents.single_deck.formatters.base import SingleDeckFormatter
from backend.decomp.config import safe_print


class InflexibilidadeUsinaFormatter(SingleDeckFormatter):
    """
    Formatter específico para resultados da InflexibilidadeUsinaTool.
    Formata dados do cálculo de inflexibilidade total de usina termelétrica.
    """
    
    def can_format(self, tool_name: str, result_structure: Dict[str, Any]) -> bool:
        """Verifica se pode formatar resultados da InflexibilidadeUsinaTool."""
        return tool_name == "InflexibilidadeUsinaTool" or "inflexibilidade" in tool_name.lower()
    
    def get_priority(self) -> int:
        """Prioridade alta para esta tool específica."""
        return 90
    
    def format_response(
        self,
        tool_result: Dict[str, Any],
        tool_name: str,
        query: str
    ) -> Dict[str, Any]:
        """
        Formata resposta da InflexibilidadeUsinaTool.
        
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
                "final_response": f"❌ **Erro ao Calcular Inflexibilidade**\n\n{error}",
                "visualization_data": None
            }
        
        inflexibilidade_total = tool_result.get("inflexibilidade_total")
        usina = tool_result.get("usina", {})
        detalhes = tool_result.get("detalhes", {})
        calculo = tool_result.get("calculo", {})
        
        # Verificar explicitamente se é None (0 é um valor válido!)
        if inflexibilidade_total is None:
            return {
                "final_response": "❌ **Erro ao Calcular Inflexibilidade**\n\nResultado do cálculo não disponível.",
                "visualization_data": None
            }
        
        # Resposta mínima - toda a informação está na visualização
        nome_usina = usina.get("nome", f"Usina {usina.get('codigo', 'N/A')}")
        codigo_usina = usina.get("codigo")
        response_parts = []
        response_parts.append(f"## Inflexibilidade Total - {nome_usina}\n\n")
        response_parts.append(f"Código: {codigo_usina} | Submercado: {usina.get('submercado')}\n\n")
        
        # Preparar dados de visualização para o componente React
        detalhes_patamares = []
        for patamar_nome, patamar_label in [("pesada", "PESADA"), ("media", "MEDIA"), ("leve", "LEVE")]:
            patamar_data = detalhes.get(patamar_nome, {})
            detalhes_patamares.append({
                "patamar": patamar_label,
                "patamar_numero": {"pesada": 1, "media": 2, "leve": 3}[patamar_nome],
                "inflexibilidade": patamar_data.get("inflexibilidade"),
                "duracao": patamar_data.get("duracao")
            })
        
        visualization_data = {
            "inflexibilidade_total": inflexibilidade_total,
            "detalhes_patamares": detalhes_patamares,
            "usina": usina,
            "calculo": calculo,
            "visualization_type": "inflexibilidade_calculo",
            "tool_name": tool_name
        }
        
        return {
            "final_response": "".join(response_parts),
            "visualization_data": visualization_data
        }
