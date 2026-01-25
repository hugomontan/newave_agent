"""
Formatador para VariacaoReservatorioInicialTool - volume inicial percentual por usina.
Visualização: Tabela comparativa + Gráfico de linha (deck vs deck)
Suporta N decks para comparação dinâmica.
"""
import math
from typing import Dict, Any, List, Optional
from backend.newave.agents.multi_deck.formatting.base import ComparisonFormatter, DeckData


class VariacaoReservatorioInicialFormatter(ComparisonFormatter):
    """
    Formatador para VariacaoReservatorioInicialTool - volume inicial percentual por usina.
    Visualização: Tabela comparativa + Gráfico de linha (deck vs deck)
    """
    
    def can_format(self, tool_name: str, result_structure: Dict[str, Any]) -> bool:
        # Verificar se é a tool correta
        if tool_name != "VariacaoReservatorioInicialTool":
            return False
        
        # Verificar se tem dados_volume_inicial (formato direto)
        if "dados_volume_inicial" in result_structure:
            return True
        
        # Verificar se tem dados_por_tipo com estrutura de reservatório inicial
        # (pode acontecer se a tool retornar em formato diferente)
        if "dados_por_tipo" in result_structure:
            dados_por_tipo = result_structure.get("dados_por_tipo", {})
            # Verificar se algum tipo contém dados de volume inicial
            for tipo, dados in dados_por_tipo.items():
                if isinstance(dados, list) and len(dados) > 0:
                    first_record = dados[0] if isinstance(dados[0], dict) else {}
                    # Verificar se tem campos típicos de reservatório inicial
                    if "volume_inicial_percentual" in first_record or "codigo_usina" in first_record:
                        return True
        
        return False
    
    def get_priority(self) -> int:
        return 100  # Alta prioridade - muito específico
    
    def format_multi_deck_comparison(
        self,
        decks_data: List[DeckData],
        tool_name: str,
        query: str
    ) -> Dict[str, Any]:
        """Formata comparação de variação de reservatório inicial para N decks."""
        if len(decks_data) < 2:
            return {
                "comparison_table": [],
                "chart_data": None,
                "visualization_type": "reservatorio_inicial_table",
                "error": "São necessários pelo menos 2 decks para comparação"
            }
        
        # Extrair dados de todos os decks
        all_codigos = set()
        decks_info = []
        
        for deck in decks_data:
            result = deck.result
            # Tentar extrair dados de diferentes formatos
            dados = result.get("dados_volume_inicial", [])
            
            # Se não encontrou em dados_volume_inicial, tentar dados_por_tipo
            if not dados and "dados_por_tipo" in result:
                dados_por_tipo = result.get("dados_por_tipo", {})
                # Concatenar todos os tipos que contêm dados de volume inicial
                for tipo, dados_tipo in dados_por_tipo.items():
                    if isinstance(dados_tipo, list):
                        # Verificar se são dados de volume inicial
                        if dados_tipo and isinstance(dados_tipo[0], dict):
                            if "volume_inicial_percentual" in dados_tipo[0] or "codigo_usina" in dados_tipo[0]:
                                dados.extend(dados_tipo)
            
            # Extrair período do deck (ano-mês)
            periodo_key, periodo_label = self._extract_period_from_deck(deck)
            
            # Indexar por código da usina
            deck_indexed = {}
            for record in dados:
                if not isinstance(record, dict):
                    continue
                codigo = record.get("codigo_usina")
                if codigo is not None:
                    deck_indexed[codigo] = record
                    all_codigos.add(codigo)
            
            decks_info.append({
                "deck": deck,
                "display_name": deck.display_name,
                "periodo_key": periodo_key,
                "periodo_label": periodo_label,
                "indexed": deck_indexed
            })
        
        # Construir tabela comparativa com N colunas
        comparison_table = []
        chart_datasets = []
        
        for codigo in sorted(all_codigos):
            # Obter nome da usina do primeiro deck que tiver
            nome_usina = None
            for deck_info in decks_info:
                record = deck_info["indexed"].get(codigo, {})
                if record.get("nome_usina"):
                    nome_usina = record.get("nome_usina")
                    break
            if not nome_usina:
                nome_usina = f"Usina {codigo}"
            
            usina_info = f"{nome_usina} ({codigo})"
            
            # Criar linha na tabela para cada deck
            for deck_info in decks_info:
                record = deck_info["indexed"].get(codigo, {})
                volume = self._sanitize_number(record.get("volume_inicial_percentual"))
                
                if volume is not None:
                    comparison_table.append({
                        "usina": usina_info,
                        "codigo_usina": codigo,
                        "data": deck_info["periodo_key"],
                        "periodo": deck_info["periodo_label"],
                        "volume_inicial": round(volume, 2)
                    })
            
            # Adicionar ao gráfico (uma série por usina, com N valores)
            volumes = []
            labels = []
            for deck_info in decks_info:
                record = deck_info["indexed"].get(codigo, {})
                volume = self._sanitize_number(record.get("volume_inicial_percentual"))
                volumes.append(round(volume, 2) if volume is not None else None)
                labels.append(deck_info["periodo_label"])
            
            chart_datasets.append({
                "label": usina_info,
                "data": volumes
            })
        
        # Construir chart_data com N labels (um por deck)
        chart_labels = [deck_info["periodo_label"] for deck_info in decks_info]
        
        chart_data = {
            "labels": chart_labels,
            "datasets": chart_datasets
        } if chart_datasets else None
        
        return {
            "comparison_table": comparison_table,
            "chart_data": chart_data,
            "visualization_type": "reservatorio_inicial_table",
            "chart_config": {
                "type": "line",
                "title": "Volume Inicial Percentual por Usina",
                "x_axis": "Deck",
                "y_axis": "Volume Inicial (%)"
            },
            "deck_names": self.get_deck_names(decks_data),
            "is_multi_deck": len(decks_data) > 2
        }
    
    def _extract_period_from_deck(self, deck: DeckData) -> tuple:
        """
        Extrai período (ano-mês) do deck.
        Retorna (periodo_key, periodo_label) onde:
        - periodo_key: "MM-YYYY" (ex: "12-2025")
        - periodo_label: "Mês YYYY" (ex: "Dezembro 2025")
        """
        # Tentar extrair do resultado
        result = deck.result
        ano = result.get("ano")
        mes = result.get("mes")
        
        if ano is not None and mes is not None:
            periodo_key = f"{int(mes):02d}-{int(ano):04d}"
            meses_nomes = {
                1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
                5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
                9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
            }
            periodo_label = f"{meses_nomes.get(int(mes), f'Mês {mes}')} {int(ano)}"
            return (periodo_key, periodo_label)
        
        # Fallback: tentar extrair do nome do deck
        import re
        deck_name = deck.name
        match = re.search(r'NW(\d{4})(\d{2})', deck_name)
        if match:
            ano = int(match.group(1))
            mes = int(match.group(2))
            periodo_key = f"{mes:02d}-{ano:04d}"
            meses_nomes = {
                1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
                5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
                9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
            }
            periodo_label = f"{meses_nomes.get(mes, f'Mês {mes}')} {ano}"
            return (periodo_key, periodo_label)
        
        # Último fallback: usar display_name
        if deck.display_name:
            return (deck.display_name, deck.display_name)
        
        return ("N/A", "N/A")
    
    def _format_comparison_internal(
        self,
        result_dec: Dict[str, Any],
        result_jan: Dict[str, Any],
        tool_name: str,
        query: str
    ) -> Dict[str, Any]:
        """
        Formata comparação de volume inicial percentual por usina.
        Compara valores entre dezembro e janeiro, criando tabela e gráfico.
        """
        dados_dec = result_dec.get("dados_volume_inicial", [])
        dados_jan = result_jan.get("dados_volume_inicial", [])
        
        if not dados_dec and not dados_jan:
            return {
                "comparison_table": [],
                "chart_data": None,
                "visualization_type": "reservatorio_inicial_table",
            }
        
        # Indexar por código da usina
        dec_indexed = {r.get("codigo_usina"): r for r in dados_dec if r.get("codigo_usina") is not None}
        jan_indexed = {r.get("codigo_usina"): r for r in dados_jan if r.get("codigo_usina") is not None}
        
        # Construir tabela comparativa
        comparison_table = []
        chart_datasets = []
        
        all_codigos = sorted(set(dec_indexed.keys()) | set(jan_indexed.keys()))
        
        for codigo in all_codigos:
            dec_record = dec_indexed.get(codigo, {})
            jan_record = jan_indexed.get(codigo, {})
            
            nome_usina = dec_record.get("nome_usina") or jan_record.get("nome_usina", f"Usina {codigo}")
            # Formato: "Nome da Usina (Código)" para confirmação visual
            usina_info = f"{nome_usina} ({codigo})"
            
            volume_dec = self._sanitize_number(dec_record.get("volume_inicial_percentual"))
            volume_jan = self._sanitize_number(jan_record.get("volume_inicial_percentual"))
            
            # Formato vertical: uma linha por deck
            # Linha para Dezembro 2025
            if volume_dec is not None:
                comparison_table.append({
                    "usina": usina_info,
                    "codigo_usina": codigo,
                    "data": "12-2025",  # MM-YYYY
                    "periodo": "Dezembro 2025",
                    "volume_inicial": round(volume_dec, 2)
                })
            
            # Linha para Janeiro 2026
            if volume_jan is not None:
                comparison_table.append({
                    "usina": usina_info,
                    "codigo_usina": codigo,
                    "data": "01-2026",  # MM-YYYY
                    "periodo": "Janeiro 2026",
                    "volume_inicial": round(volume_jan, 2)
                })
            
            # Adicionar ao gráfico (mantém formato original para o gráfico)
            if volume_dec is not None or volume_jan is not None:
                chart_datasets.append({
                    "label": usina_info,
                    "data": [
                        volume_dec if volume_dec is not None else None,
                        volume_jan if volume_jan is not None else None
                    ]
                })
        
        # Construir chart_data
        chart_data = {
            "labels": ["Dezembro 2025", "Janeiro 2026"],
            "datasets": chart_datasets
        } if chart_datasets else None
        
        return {
            "comparison_table": comparison_table,
            "chart_data": chart_data,
            "visualization_type": "reservatorio_inicial_table",
            "chart_config": {
                "type": "line",
                "title": "Volume Inicial Percentual por Usina",
                "x_axis": "Deck",
                "y_axis": "Volume Inicial (%)"
            }
        }
    
    def _sanitize_number(self, value: Any) -> Optional[float]:
        """
        Sanitiza número, convertendo para float ou retornando None.
        """
        if value is None:
            return None
        if isinstance(value, (int, float)):
            if math.isnan(value) or math.isinf(value):
                return None
            return float(value)
        try:
            num = float(value)
            if math.isnan(num) or math.isinf(num):
                return None
            return num
        except (ValueError, TypeError):
            return None
