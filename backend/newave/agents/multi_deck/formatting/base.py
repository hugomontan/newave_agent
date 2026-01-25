"""
Interface base para formatadores de comparação multi-deck.
Suporta N decks para comparação dinâmica.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import math


@dataclass
class DeckData:
    """
    Wrapper para dados de um deck individual.
    
    Attributes:
        name: Nome do deck (ex: "NW202501")
        display_name: Nome amigável (ex: "Janeiro 2025")
        result: Resultado da tool para este deck
        success: Se a execução foi bem-sucedida
        error: Mensagem de erro (se houver)
    """
    name: str
    display_name: str
    result: Dict[str, Any]
    success: bool = True
    error: Optional[str] = None
    
    @property
    def has_data(self) -> bool:
        """Verifica se o deck tem dados válidos."""
        return self.success and self.result is not None
    
    def get(self, key: str, default: Any = None) -> Any:
        """Acessa um campo do resultado."""
        if self.result is None:
            return default
        return self.result.get(key, default)


class ComparisonFormatter(ABC):
    """
    Classe base abstrata para formatadores de comparação.
    
    Cada formatador é especializado para um tipo específico de tool
    e gera visualizações otimizadas (tabelas, gráficos, diff lists).
    
    Suporta comparação de N decks com comportamento adaptativo:
    - 2 decks: comparação direta (antes/depois)
    - N decks: evolução histórica/temporal
    """
    
    @abstractmethod
    def can_format(self, tool_name: str, result_structure: Dict[str, Any]) -> bool:
        """
        Verifica se este formatador pode processar o resultado desta tool.
        
        Args:
            tool_name: Nome da tool (ex: "ClastValoresTool")
            result_structure: Estrutura do resultado da tool (para verificar campos)
            
        Returns:
            True se pode formatar, False caso contrário
        """
        pass
    
    @abstractmethod
    def format_multi_deck_comparison(
        self,
        decks_data: List[DeckData],
        tool_name: str,
        query: str
    ) -> Dict[str, Any]:
        """
        Formata a comparação entre N decks.
        
        Este é o método principal para formatação. Deve lidar com:
        - 2 decks: comparação direta (similar ao antigo format_comparison)
        - N decks: evolução histórica com múltiplas séries/colunas
        
        Args:
            decks_data: Lista de DeckData ordenados cronologicamente (mais antigo primeiro)
            tool_name: Nome da tool usada
            query: Query original do usuário
            
        Returns:
            Dict com:
            - comparison_table: List[Dict] - Tabela comparativa (opcional)
            - chart_data: Dict - Dados para gráfico Chart.js (opcional)
            - visualization_type: str - Tipo de visualização
            - chart_config: Dict - Configurações específicas do gráfico (opcional)
            - llm_context: Dict - Contexto adicional para LLM (opcional)
            - deck_names: List[str] - Nomes dos decks comparados
            - is_multi_deck: bool - True se >2 decks
        """
        pass
    
    def format_comparison(
        self,
        result_dec: Dict[str, Any],
        result_jan: Dict[str, Any],
        tool_name: str,
        query: str
    ) -> Dict[str, Any]:
        """
        DEPRECATED: Use format_multi_deck_comparison instead.
        
        Mantido para compatibilidade. Converte automaticamente para format_multi_deck_comparison.
        
        Args:
            result_dec: Resultado completo da tool para deck mais antigo
            result_jan: Resultado completo da tool para deck mais recente
            tool_name: Nome da tool usada
            query: Query original do usuário
            
        Returns:
            Dict com dados de comparação
        """
        # Converter para o novo formato
        decks_data = [
            DeckData(
                name="deck_1",
                display_name="Deck Anterior",
                result=result_dec,
                success=True
            ),
            DeckData(
                name="deck_2", 
                display_name="Deck Atual",
                result=result_jan,
                success=True
            )
        ]
        return self.format_multi_deck_comparison(decks_data, tool_name, query)
    
    def get_priority(self) -> int:
        """
        Retorna a prioridade do formatador.
        
        Formatadores com maior prioridade têm precedência quando múltiplos
        formatadores podem processar a mesma tool.
        
        Returns:
            Prioridade (maior = mais específico). Padrão: 0
        """
        return 0
    
    def is_direct_comparison(self, decks_data: List[DeckData]) -> bool:
        """
        Verifica se é uma comparação direta (2 decks) ou evolução histórica (N decks).
        
        Args:
            decks_data: Lista de DeckData
            
        Returns:
            True se é comparação direta (2 decks), False se é evolução histórica
        """
        return len(decks_data) == 2
    
    def get_deck_names(self, decks_data: List[DeckData]) -> List[str]:
        """
        Retorna lista de nomes amigáveis dos decks.
        
        Args:
            decks_data: Lista de DeckData
            
        Returns:
            Lista de nomes amigáveis
        """
        return [d.display_name for d in decks_data]
    
    def get_comparison_context(self, decks_data: List[DeckData]) -> Dict[str, Any]:
        """
        Gera contexto base para comparação.
        
        Args:
            decks_data: Lista de DeckData
            
        Returns:
            Dict com contexto básico da comparação
        """
        return {
            "deck_count": len(decks_data),
            "deck_names": self.get_deck_names(decks_data),
            "is_direct_comparison": self.is_direct_comparison(decks_data),
            "comparison_mode": "direct" if len(decks_data) == 2 else "historical",
            "oldest_deck": decks_data[0].display_name if decks_data else None,
            "newest_deck": decks_data[-1].display_name if decks_data else None,
        }
    
    def _sanitize_number(self, value: Any) -> Optional[float]:
        """
        Sanitiza valor numérico, tratando None, NaN e Inf.
        
        Args:
            value: Valor a ser sanitizado
            
        Returns:
            float válido ou None
        """
        if value is None:
            return None
        try:
            float_val = float(value)
            if math.isnan(float_val) or math.isinf(float_val):
                return None
            return float_val
        except (ValueError, TypeError):
            return None
    
    def _safe_round(self, value: Any, decimals: int = 2) -> Optional[float]:
        """
        Arredonda valor numérico de forma segura.
        
        Args:
            value: Valor a ser arredondado
            decimals: Número de casas decimais (padrão: 2)
            
        Returns:
            float arredondado ou None. Se o resultado for inteiro, retorna int.
        """
        sanitized = self._sanitize_number(value)
        if sanitized is None:
            return None
        try:
            rounded = round(sanitized, decimals)
            if math.isnan(rounded) or math.isinf(rounded):
                return None
            # Se for número inteiro, retornar sem decimais
            if rounded == int(rounded):
                return int(rounded)
            return rounded
        except (ValueError, TypeError):
            return None
    
    def _get_period_key(self, record: Dict[str, Any]) -> Optional[str]:
        """
        Obtém chave de período (ano-mês) de um registro.
        Suporta múltiplos formatos: ano/mes, data ISO, datetime object.
        
        Args:
            record: Dicionário com dados do registro
            
        Returns:
            String no formato "YYYY-MM" ou None
        """
        # Tentar ano e mes primeiro
        ano = record.get("ano")
        mes = record.get("mes")
        
        if ano is not None and mes is not None:
            try:
                ano_int = int(float(ano)) if isinstance(ano, (int, float, str)) else None
                mes_int = int(float(mes)) if isinstance(mes, (int, float, str)) else None
                if ano_int is not None and mes_int is not None:
                    return f"{ano_int:04d}-{mes_int:02d}"
            except (ValueError, TypeError):
                pass
        
        # Tentar campo data
        data = record.get("data")
        if data:
            if isinstance(data, str):
                if len(data) >= 7 and "-" in data:
                    return data[:7]  # YYYY-MM
            elif hasattr(data, 'year') and hasattr(data, 'month'):
                try:
                    return f"{data.year:04d}-{data.month:02d}"
                except (AttributeError, ValueError):
                    pass
        
        # Tentar ano_mes se existir
        ano_mes = record.get("ano_mes")
        if ano_mes:
            if isinstance(ano_mes, str) and len(ano_mes) >= 7:
                return ano_mes[:7]  # YYYY-MM
        
        return None
    
    def _format_period_label(self, periodo_key: str) -> str:
        """
        Formata chave de período (ex: "2025-12") para label legível (ex: "Dez/2025").
        
        Args:
            periodo_key: String no formato "YYYY-MM"
            
        Returns:
            String formatada (ex: "Dez/2025")
        """
        try:
            if "-" in periodo_key:
                parts = periodo_key.split("-")
                if len(parts) == 2:
                    ano = parts[0]
                    mes = int(parts[1])
                    meses_nomes = {
                        1: "Jan", 2: "Fev", 3: "Mar", 4: "Abr",
                        5: "Mai", 6: "Jun", 7: "Jul", 8: "Ago",
                        9: "Set", 10: "Out", 11: "Nov", 12: "Dez"
                    }
                    mes_nome = meses_nomes.get(mes, str(mes))
                    return f"{mes_nome}/{ano}"
        except (ValueError, TypeError, IndexError):
            pass
        return periodo_key


def convert_legacy_result_to_decks_data(
    tool_result: Dict[str, Any],
    deck_display_names: Optional[Dict[str, str]] = None
) -> List[DeckData]:
    """
    Converte resultado legado (deck_1, deck_2) ou novo formato (decks) para List[DeckData].
    PRIORIDADE: Novo formato (decks) tem precedência sobre formato legado (deck_1, deck_2).
    
    Args:
        tool_result: Resultado no formato legado com deck_1, deck_2 ou novo formato com decks
        deck_display_names: Mapeamento de nomes dos decks
        
    Returns:
        Lista de DeckData
    """
    decks_data = []
    
    # PRIORIDADE 1: Novo formato com lista "decks" (contém todos os decks)
    # Verificar PRIMEIRO para garantir que todos os N decks sejam processados
    if "decks" in tool_result and isinstance(tool_result["decks"], list):
        for deck in tool_result["decks"]:
            name = deck.get("name", deck.get("deck_name", "unknown"))
            display_name = deck.get("display_name")
            if not display_name and deck_display_names:
                display_name = deck_display_names.get(name, name)
            if not display_name:
                display_name = name
            
            # PRIORIDADE: Usar full_result se disponível (preserva estrutura original completa)
            # O full_result contém dados_estruturais, dados_conjunturais, etc.
            full_result = deck.get("full_result")
            if not full_result:
                full_result = deck.get("result")
            if not full_result:
                full_result = deck
            if not isinstance(full_result, dict):
                full_result = {
                    "success": deck.get("success", True),
                    "data": deck.get("data", []),
                    "error": deck.get("error")
                }
            
            decks_data.append(DeckData(
                name=name,
                display_name=display_name,
                result=full_result,  # Usar full_result preservado (contém dados_estruturais, dados_conjunturais, etc.)
                success=deck.get("success", True),
                error=deck.get("error")
            ))
        
        return decks_data
    
    # PRIORIDADE 2: Formato legado: deck_1, deck_2 (apenas 2 decks)
    if "deck_1" in tool_result and "deck_2" in tool_result:
        deck_1 = tool_result["deck_1"]
        deck_2 = tool_result["deck_2"]
        
        name_1 = deck_1.get("deck_name", "deck_1")
        name_2 = deck_2.get("deck_name", "deck_2")
        
        display_1 = deck_display_names.get(name_1, "Deck Anterior") if deck_display_names else "Deck Anterior"
        display_2 = deck_display_names.get(name_2, "Deck Atual") if deck_display_names else "Deck Atual"
        
        # PRIORIDADE: Usar full_result se disponível (preserva estrutura original completa)
        # O full_result contém dados_estruturais, dados_conjunturais, data, etc.
        result_1 = deck_1.get("full_result")
        if not result_1:
            result_1 = deck_1
        if not isinstance(result_1, dict):
            result_1 = {
                "success": deck_1.get("success", True),
                "data": deck_1.get("data", []),
                "error": deck_1.get("error")
            }
        
        result_2 = deck_2.get("full_result")
        if not result_2:
            result_2 = deck_2
        if not isinstance(result_2, dict):
            result_2 = {
                "success": deck_2.get("success", True),
                "data": deck_2.get("data", []),
                "error": deck_2.get("error")
            }
        
        decks_data = [
            DeckData(
                name=name_1,
                display_name=display_1,
                result=result_1,  # Usar full_result extraído (contém dados_estruturais, dados_conjunturais, data, etc.)
                success=deck_1.get("success", True),
                error=deck_1.get("error")
            ),
            DeckData(
                name=name_2,
                display_name=display_2,
                result=result_2,  # Usar full_result extraído (contém dados_estruturais, dados_conjunturais, data, etc.)
                success=deck_2.get("success", True),
                error=deck_2.get("error")
            )
        ]
    
    # Novo formato: decks (lista)
    elif "decks" in tool_result:
        for deck in tool_result["decks"]:
            name = deck.get("name", deck.get("deck_name", "unknown"))
            display_name = deck.get("display_name")
            if not display_name and deck_display_names:
                display_name = deck_display_names.get(name, name)
            if not display_name:
                display_name = name
            
            # PRIORIDADE: Usar full_result se disponível (preserva estrutura original completa)
            # O full_result contém dados_estruturais, dados_conjunturais, etc.
            full_result = deck.get("full_result")
            if not full_result:
                full_result = deck.get("result")
            if not full_result:
                full_result = deck
            if not isinstance(full_result, dict):
                full_result = {
                    "success": deck.get("success", True),
                    "data": deck.get("data", []),
                    "error": deck.get("error")
                }
            
            decks_data.append(DeckData(
                name=name,
                display_name=display_name,
                result=full_result,  # Usar full_result preservado (contém dados_estruturais, dados_conjunturais, etc.)
                success=deck.get("success", True),
                error=deck.get("error")
            ))
    
    return decks_data