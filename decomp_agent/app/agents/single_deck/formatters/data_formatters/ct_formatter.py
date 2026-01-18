"""
Formatter específico para CTUsinasTermelétricasTool (Bloco CT do DECOMP).
"""

from typing import Dict, Any, List, Optional
from decomp_agent.app.agents.single_deck.formatters.base import SingleDeckFormatter


class CTSingleDeckFormatter(SingleDeckFormatter):
    """
    Formatter específico para resultados da CTUsinasTermelétricasTool.
    Formata dados do Bloco CT (Usinas Termelétricas) do DECOMP.
    
    Suporta filtro por usina específica através do visualization_data.
    """
    
    def can_format(self, tool_name: str, result_structure: Dict[str, Any]) -> bool:
        """Verifica se pode formatar resultados da CTUsinasTermelétricasTool."""
        return tool_name == "CTUsinasTermelétricasTool" or "ct" in tool_name.lower()
    
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
        Formata resposta da CTUsinasTermelétricasTool.
        
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
                "final_response": f"## Erro ao Consultar Bloco CT\n\n{error}",
                "visualization_data": None
            }
        
        data = tool_result.get("data", [])
        total_usinas = tool_result.get("total_usinas", len(data))
        filtros = tool_result.get("filtros", {})
        cvu_apenas = filtros.get("cvu_apenas", False)
        
        if not data:
            return {
                "final_response": "## Bloco CT - Usinas Termelétricas\n\nNenhuma usina encontrada com os filtros especificados.",
                "visualization_data": None
            }
        
        # Normalizar dados para formato padronizado
        # Passar flag cvu_apenas para o normalizador respeitar o filtro
        normalized_data = self._normalize_data(data, cvu_apenas=cvu_apenas)
        
        # Construir resposta em Markdown
        response_parts = []
        
        # Se filtrado por usina específica, resposta mínima (dados aparecem na tabela)
        if filtros.get("codigo_usina"):
            nome_filtrado = filtros.get('nome_usina', f"Usina {filtros['codigo_usina']}")
            response_parts.append(f"## Bloco CT - {nome_filtrado}\n\n")
            response_parts.append(f"Dados da usina termelétrica {nome_filtrado} (Código {filtros['codigo_usina']}).\n\n")
        elif filtros.get("codigo_submercado"):
            response_parts.append(f"## Bloco CT - Submercado {filtros['codigo_submercado']}\n\n")
            response_parts.append(f"Total de registros: {total_usinas}\n\n")
        elif filtros.get("estagio"):
            response_parts.append(f"## Bloco CT - Estágio {filtros['estagio']}\n\n")
            response_parts.append(f"Total de registros: {total_usinas}\n\n")
        else:
            # Sem filtro - resposta completa
            response_parts.append("## Bloco CT - Usinas Termelétricas\n\n")
            response_parts.append(f"**Total de registros encontrados**: {total_usinas}\n\n")
        
        # Dados de visualização (SEM filtro no frontend - matching já feito na tool)
        visualization_data = {
            "table": normalized_data,
            "chart_data": None,
            "visualization_type": "table_only",
            "tool_name": tool_name,
            "filtros": {
                "usina_especifica": filtros.get("codigo_usina"),
                "submercado": filtros.get("codigo_submercado"),
                "estagio": filtros.get("estagio"),
                "nome_usina": filtros.get("nome_usina"),
                "cvu_apenas": cvu_apenas,  # NOVO: passar flag para frontend
            } if filtros else None,
        }
        
        return {
            "final_response": "".join(response_parts),
            "visualization_data": visualization_data
        }
    
    def _normalize_data(self, data: List[Dict[str, Any]], cvu_apenas: bool = False) -> List[Dict[str, Any]]:
        """
        Normaliza os dados das usinas termelétricas para um formato consistente.
        Expande patamares em linhas separadas para melhor visualização.
        
        Suporta dois formatos:
        1. Dados completos (cvu_1, cvu_2, cvu_3, etc.) - expande por patamar
        2. Dados filtrados (cvu, patamar) - já filtrados, apenas normaliza
        
        Args:
            data: Lista de dicionários com dados das usinas
            cvu_apenas: Se True, inclui apenas CVU (remove disponibilidade e inflexibilidade)
            
        Returns:
            Lista de dicionários normalizados (expandidos por patamar ou já filtrados)
        """
        normalized = []
        
        # Mapeamento de índices de patamar para nomes
        patamar_names = {
            1: "PESADA",
            2: "MEDIA",
            3: "LEVE"
        }
        
        for usina in data:
            codigo_usina = usina.get("codigo_usina") or usina.get("codigo")
            codigo_submercado = usina.get("codigo_submercado") or usina.get("submercado")
            nome_usina = str(usina.get("nome_usina", "")).strip()
            estagio = usina.get("estagio")
            
            # Verificar se os dados já foram filtrados (têm campo "patamar" e "cvu" direto)
            if "patamar" in usina and "cvu" in usina:
                # Dados já filtrados - apenas normalizar
                patamar_num = usina.get("patamar")
                patamar_nome = patamar_names.get(patamar_num, f"PATAMAR_{patamar_num}")
                
                normalized_record = {
                    "codigo_usina": codigo_usina,
                    "codigo_submercado": codigo_submercado,
                    "nome_usina": nome_usina,
                    "estagio": estagio,
                    "patamar": patamar_nome,
                    "patamar_numero": patamar_num,
                    "cvu": usina.get("cvu"),
                }
                
                # Adicionar disponibilidade e inflexibilidade apenas se não for CVU apenas
                if not cvu_apenas:
                    normalized_record["disponibilidade"] = usina.get("disponibilidade")
                    normalized_record["inflexibilidade"] = usina.get("inflexibilidade")
                
                # Adicionar se houver pelo menos um campo com valor
                if normalized_record.get("cvu") is not None or \
                   (not cvu_apenas and (normalized_record.get("disponibilidade") is not None or \
                                        normalized_record.get("inflexibilidade") is not None)):
                    normalized.append(normalized_record)
            else:
                # Dados completos - expandir por patamar (1, 2, 3)
                for patamar_idx in [1, 2, 3]:
                    patamar_nome = patamar_names.get(patamar_idx, f"PATAMAR_{patamar_idx}")
                    
                    # Normalizar campos (aceitar múltiplas nomenclaturas)
                    normalized_record = {
                        "codigo_usina": codigo_usina,
                        "codigo_submercado": codigo_submercado,
                        "nome_usina": nome_usina,
                        "estagio": estagio,
                        "patamar": patamar_nome,
                        "patamar_numero": patamar_idx,
                        "cvu": usina.get(f"cvu_{patamar_idx}") or usina.get(f"cvu{patamar_idx}"),
                    }
                    
                    # Adicionar disponibilidade e inflexibilidade apenas se não for CVU apenas
                    if not cvu_apenas:
                        normalized_record["disponibilidade"] = usina.get(f"disponibilidade_{patamar_idx}") or usina.get(f"disponibilidade{patamar_idx}")
                        normalized_record["inflexibilidade"] = usina.get(f"inflexibilidade_{patamar_idx}") or usina.get(f"inflexibilidade{patamar_idx}")
                    
                    # Apenas adicionar se houver dados relevantes (não adicionar linhas vazias)
                    if normalized_record.get("cvu") is not None or \
                       (not cvu_apenas and (normalized_record.get("disponibilidade") is not None or \
                                            normalized_record.get("inflexibilidade") is not None)):
                        normalized.append(normalized_record)
        
        return normalized
