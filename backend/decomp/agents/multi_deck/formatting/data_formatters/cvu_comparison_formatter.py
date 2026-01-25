"""
Formatter de comparação para CVU no multi deck DECOMP.
Seguindo padrão NEWAVE com indexação por período (semanas operativas).
"""

from typing import Dict, Any, List, Optional
from backend.decomp.agents.multi_deck.formatting.base import ComparisonFormatter, DeckData
import math


class CVUComparisonFormatter(ComparisonFormatter):
    """
    Formatter específico para comparação de CVU entre múltiplos decks DECOMP.
    Segue padrão NEWAVE com indexação por período (semanas operativas contínuas).
    
    IMPORTANTE: Sempre usa apenas estágio 1 para CVU.
    """
    
    def __init__(self):
        """Inicializa o formatter."""
        super().__init__()
        # Referência para calcular semanas operativas contínuas
        self._reference_deck = None
    
    def can_format(self, tool_name: str, result_structure: Dict[str, Any]) -> bool:
        """Verifica se pode formatar resultados de CVU."""
        # Verificar por nome da tool
        tool_name_lower = tool_name.lower() if tool_name else ""
        if (
            tool_name == "CTUsinasTermelétricasTool" or 
            tool_name == "CVUMultiDeckTool" or
            "cvu" in tool_name_lower
        ):
            return True
        
        # Verificar pela estrutura do resultado (se tem cvu_1, cvu_2, cvu_3)
        if result_structure and isinstance(result_structure, dict):
            if "cvu_1" in result_structure or "cvu_2" in result_structure or "cvu_3" in result_structure:
                return True
            # Verificar se é um resultado de deck que contém dados de CVU
            if "data" in result_structure:
                data = result_structure.get("data", [])
                if isinstance(data, list) and len(data) > 0:
                    first_record = data[0]
                    if isinstance(first_record, dict):
                        if "cvu_1" in first_record or "cvu_2" in first_record or "cvu_3" in first_record:
                            return True
        
        return False
    
    def get_priority(self) -> int:
        """Prioridade alta para esta tool específica."""
        return 10
    
    def format_multi_deck_comparison(
        self,
        decks_data: List[DeckData],
        tool_name: str,
        query: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Formata comparação de CVU entre múltiplos decks.
        Segue padrão NEWAVE com indexação por período (semanas operativas).
        
        Args:
            decks_data: Lista de DeckData ordenados cronologicamente
            tool_name: Nome da tool usada
            query: Query original do usuário
            
        Returns:
            Dict com dados formatados para visualização (tabela + gráfico temporal)
        """
        # Resetar referência para cada formatação
        self._reference_deck = None
        
        # Verificar se há dados válidos
        valid_decks = [d for d in decks_data if d.has_data]
        if not valid_decks:
            return {
                "comparison_table": [],
                "chart_data": None,
                "visualization_type": "table_with_line_chart",
                "deck_names": [d.display_name for d in decks_data],
                "is_multi_deck": len(decks_data) > 2,
                "final_response": "Nenhum dado válido encontrado para comparação."
            }
        
        # Extrair informações da usina (do primeiro deck)
        usina_info = None
        for deck in valid_decks:
            result = deck.result
            data = result.get("data", [])
            if data and isinstance(data, list) and len(data) > 0:
                first_record = data[0]
                if isinstance(first_record, dict):
                    codigo_usina = first_record.get("codigo_usina")
                    nome_usina = first_record.get("nome_usina")
                    if codigo_usina or nome_usina:
                        usina_info = {
                            "codigo": codigo_usina,
                            "nome": nome_usina
                        }
                        break
        
        # Se não encontrou no resultado, tentar buscar em usina do resultado
        if not usina_info:
            for deck in valid_decks:
                usina = deck.result.get("usina", {})
                if usina:
                    usina_info = usina
                    break
        
        nome_usina = usina_info.get("nome", "Usina Desconhecida") if usina_info else "Usina Desconhecida"
        codigo_usina = usina_info.get("codigo", "N/A") if usina_info else "N/A"
        
        # Converter codigo_usina para int se possível (para comparação correta)
        codigo_usina_int = None
        if codigo_usina and codigo_usina != "N/A":
            try:
                codigo_usina_int = int(codigo_usina)
            except (ValueError, TypeError):
                pass
        
        # Padrão NEWAVE: Extrair dados de todos os decks e indexar por período
        decks_info = []
        all_weeks = set()
        
        # Calcular referência de semana operativa (primeiro deck)
        reference_deck_parsed = None
        if valid_decks:
            from backend.decomp.utils.deck_loader import parse_deck_name
            first_deck_parsed = parse_deck_name(valid_decks[0].name)
            if first_deck_parsed and first_deck_parsed.get("week"):
                reference_deck_parsed = first_deck_parsed
        
        for deck in valid_decks:
            result = deck.result
            data = result.get("data", [])
            
            # Filtrar apenas estágio 1 (garantir que apenas estágio 1 está presente)
            if isinstance(data, list):
                data_estagio_1 = [
                    d for d in data 
                    if isinstance(d, dict) and (d.get("estagio") == 1 or d.get("estágio") == 1 or d.get("estagio") is None)
                ]
            else:
                data_estagio_1 = []
            
            if not data_estagio_1:
                continue
            
            # Indexar por semana operativa (seguindo padrão _index_by_period do NEWAVE)
            deck_by_week = {}  # {semana_operativa: {cvu_pesada, cvu_media, cvu_leve}}
            
            for record in data_estagio_1:
                if not isinstance(record, dict):
                    continue
                
                # VALIDAÇÃO: Garantir que o registro corresponde à usina esperada
                # Evitar processar dados de outras usinas (ex: usina 1 quando esperamos usina 97)
                if codigo_usina_int is not None:
                    record_codigo = record.get("codigo_usina")
                    if record_codigo is not None:
                        try:
                            record_codigo_int = int(record_codigo)
                            if record_codigo_int != codigo_usina_int:
                                continue  # Pular registros de outras usinas
                        except (ValueError, TypeError):
                            pass  # Se não conseguir converter, processar de qualquer forma
                
                week_key = self._get_operational_week_key(deck, reference_deck_parsed)
                if week_key is None:
                    continue
                
                # Extrair CVU dos 3 patamares (1=PESADA, 2=MEDIA, 3=LEVE)
                cvu_pesada = self._sanitize_number(record.get("cvu_1"))
                cvu_media = self._sanitize_number(record.get("cvu_2"))
                cvu_leve = self._sanitize_number(record.get("cvu_3"))
                
                # Se pelo menos um patamar tem valor, adicionar
                if cvu_pesada is not None or cvu_media is not None or cvu_leve is not None:
                    if week_key not in deck_by_week:
                        deck_by_week[week_key] = {
                            "cvu_pesada": cvu_pesada,
                            "cvu_media": cvu_media,
                            "cvu_leve": cvu_leve
                        }
                        all_weeks.add(week_key)
            
            if deck_by_week:
                decks_info.append({
                    "deck": deck,
                    "display_name": deck.display_name,
                    "by_week": deck_by_week
                })
        
        if not decks_info:
            return {
                "comparison_table": [],
                "chart_data": None,
                "visualization_type": "table_with_line_chart",
                "deck_names": [d.display_name for d in decks_data],
                "is_multi_deck": len(decks_data) > 2,
                "final_response": "Nenhum dado de CVU (estágio 1) encontrado para comparação."
            }
        
        # Ordenar semanas operativas (seguindo padrão NEWAVE: sorted(all_periods))
        sorted_weeks = sorted(all_weeks)
        
        # Construir tabela e gráfico (seguindo padrão NEWAVE)
        comparison_table = []
        chart_labels = []
        chart_datasets = [
            {"label": "CVU Patamar Pesada", "data": [], "borderColor": "rgb(239, 68, 68)"},  # red-500
            {"label": "CVU Patamar Média", "data": [], "borderColor": "rgb(234, 179, 8)"},  # yellow-500
            {"label": "CVU Patamar Leve", "data": [], "borderColor": "rgb(34, 197, 94)"}  # green-500
        ]
        
        # Processar cada semana operativa (seguindo padrão: for period_key in sorted_periods)
        for week_key in sorted_weeks:
            week_label = self._format_week_label(week_key)
            
            # Extrair data da semana (quinta-feira)
            date = None
            # Encontrar primeiro deck com dados para esta semana para obter a data
            for deck_info in decks_info:
                if week_key in deck_info["by_week"]:
                    deck = deck_info["deck"]
                    result = deck.result
                    date = result.get("date")
                    if not date:
                        from backend.decomp.utils.deck_loader import parse_deck_name, calculate_week_thursday
                        parsed = parse_deck_name(deck.name)
                        if parsed and parsed.get("week"):
                            date = calculate_week_thursday(
                                parsed["year"],
                                parsed["month"],
                                parsed["week"]
                            )
                    break
            
            # Coletar valores do primeiro deck com dados para esta semana
            # (Decisão: usar primeiro deck disponível, similar a Disponibilidade)
            cvu_pesada = None
            cvu_media = None
            cvu_leve = None
            deck_with_data = None
            
            for deck_info in decks_info:
                week_data = deck_info["by_week"].get(week_key)
                if week_data:
                    cvu_pesada = week_data["cvu_pesada"]
                    cvu_media = week_data["cvu_media"]
                    cvu_leve = week_data["cvu_leve"]
                    deck_with_data = deck_info
                    break
            
            # Construir linha da tabela
            table_row = {
                "semana_operativa": week_key,
                "data": date or week_label,
                "deck": deck_with_data["deck"].name if deck_with_data else None,
                "display_name": deck_with_data["display_name"] if deck_with_data else None,
                "cvu_pesada": cvu_pesada,
                "cvu_media": cvu_media,
                "cvu_leve": cvu_leve,
                "usina_codigo": codigo_usina,
                "usina_nome": nome_usina
            }
            
            comparison_table.append(table_row)
            chart_labels.append(week_label)
            
            # Adicionar aos datasets do gráfico (3 séries, uma por patamar)
            chart_datasets[0]["data"].append(cvu_pesada)
            chart_datasets[1]["data"].append(cvu_media)
            chart_datasets[2]["data"].append(cvu_leve)
        
        # Construir chart_data (seguindo padrão NEWAVE)
        chart_data = {
            "labels": chart_labels,
            "datasets": chart_datasets
        } if chart_labels else None
        
        # Configuração do gráfico
        chart_config = {
            "type": "line",
            "title": f"Evolução do CVU - {nome_usina}",
            "x_axis": "Semana Operativa",
            "y_axis": "CVU (R$/MWh)",
            "tool_name": tool_name
        }
        
        # Resposta mínima
        final_response = f"Comparação de CVU para {nome_usina}."
        
        return {
            "comparison_table": comparison_table,
            "chart_data": chart_data,
            "visualization_type": "table_with_line_chart",
            "chart_config": chart_config,
            "deck_names": [d["display_name"] for d in decks_info],
            "is_multi_deck": len(decks_data) > 2,
            "final_response": final_response
        }
    
    def _get_operational_week_key(self, deck: DeckData, reference_deck_parsed: Optional[Dict[str, Any]] = None) -> Optional[int]:
        """
        Obtém chave de semana operativa (número sequencial).
        Similar a _get_period_key do NEWAVE, mas retorna número sequencial.
        
        Args:
            deck: DeckData com informações do deck
            reference_deck_parsed: Dados do primeiro deck (referência) já parseados
            
        Returns:
            Número sequencial da semana operativa (1, 2, 3, ...) ou None
        """
        # Extrair ano, mês, semana do deck
        from backend.decomp.utils.deck_loader import parse_deck_name
        parsed = parse_deck_name(deck.name)
        
        if not parsed or not parsed.get("week"):
            return None
        
        year = parsed["year"]
        month = parsed["month"]
        week = parsed["week"]
        
        # Se não há referência, este é o primeiro deck
        if reference_deck_parsed is None:
            return 1
        
        ref_year = reference_deck_parsed["year"]
        ref_month = reference_deck_parsed["month"]
        ref_week = reference_deck_parsed.get("week", 1)
        
        # Calcular diferença (assumindo máximo de 5 semanas por mês)
        months_diff = (year - ref_year) * 12 + (month - ref_month)
        weeks_from_ref = months_diff * 5 + (week - ref_week)
        
        return weeks_from_ref + 1
    
    def _format_week_label(self, week_key: int) -> str:
        """
        Formata chave de semana operativa para label legível.
        Similar a _format_period_label do NEWAVE.
        
        Args:
            week_key: Número sequencial da semana operativa
            
        Returns:
            Label formatado (ex: "Semana 1")
        """
        return f"Semana {week_key}"
    
    def _sanitize_number(self, value) -> Optional[float]:
        """
        Sanitiza valor numérico (igual ao NEWAVE).
        
        Args:
            value: Valor a sanitizar
            
        Returns:
            Float sanitizado ou None
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
