"""
Formatter para LimitesIntercambioDECOMPTool no single deck.
Seguindo padrão similar ao CargaAndeSingleDeckFormatter.
"""
from typing import Dict, Any, List, Optional
from decomp_agent.app.agents.single_deck.formatters.base import SingleDeckFormatter
from decomp_agent.app.config import safe_print


class LimitesIntercambioSingleDeckFormatter(SingleDeckFormatter):
    """Formatter para LimitesIntercambioDECOMPTool."""
    
    def can_format(self, tool_name: str, result_structure: Dict[str, Any]) -> bool:
        """Verifica se pode formatar LimitesIntercambioDECOMPTool."""
        return tool_name == "LimitesIntercambioDECOMPTool"
    
    def get_priority(self) -> int:
        """Prioridade alta."""
        return 85
    
    def format_response(
        self,
        tool_result: Dict[str, Any],
        tool_name: str,
        query: str
    ) -> Dict[str, Any]:
        """Formata resposta de LimitesIntercambioDECOMPTool."""
        
        if not tool_result.get("success", False):
            error = tool_result.get("error", "Erro desconhecido")
            return {
                "final_response": f"## Erro ao Consultar Limites de Intercâmbio\n\n{error}",
                "visualization_data": None
            }
        
        data = tool_result.get("data", [])
        par = tool_result.get("par")  # Pode ser None ou dict
        sentido_query = tool_result.get("sentido_query")  # "de_para", "para_de", ou None (ambos)
        duracoes = tool_result.get("duracoes", {})
        pares_disponiveis = tool_result.get("pares_disponiveis", [])
        
        if not data:
            return {
                "final_response": "## Limites de Intercâmbio\n\nNenhum registro encontrado.",
                "visualization_data": None
            }
        
        # Normalizar dados para formato padronizado (expandir por patamar e sentido)
        normalized_data = self._normalize_data(data, duracoes, par)
        
        # Extrair MW médios (similar ao Carga ANDE)
        mw_medios = []
        for record in data:
            # MW médio DE->PARA
            mw_medio_de_para = record.get("mw_medio_de_para")
            if mw_medio_de_para is not None:
                sub_de = record.get("sub_de", "?")
                sub_para = record.get("sub_para", "?")
                mw_medios.append({
                    "sentido": f"{sub_de} → {sub_para}",
                    "mw_medio": mw_medio_de_para
                })
            
            # MW médio PARA->DE
            mw_medio_para_de = record.get("mw_medio_para_de")
            if mw_medio_para_de is not None:
                sub_de = record.get("sub_de", "?")
                sub_para = record.get("sub_para", "?")
                mw_medios.append({
                    "sentido": f"{sub_para} → {sub_de}",
                    "mw_medio": mw_medio_para_de
                })
        
        # Construir resposta em Markdown (mínima, dados aparecem na tabela)
        response_parts = []
        
        # Título
        if par:
            sub_de = par.get("de", "?") if isinstance(par, dict) else "?"
            sub_para = par.get("para", "?") if isinstance(par, dict) else "?"
            if sentido_query == "de_para":
                titulo = f"## Limites de Intercâmbio: {sub_de} → {sub_para}\n\n"
            elif sentido_query == "para_de":
                titulo = f"## Limites de Intercâmbio: {sub_para} → {sub_de}\n\n"
            else:
                titulo = f"## Limites de Intercâmbio: {sub_de} ↔ {sub_para}\n\n"
            response_parts.append(titulo)
        else:
            response_parts.append("## Limites de Intercâmbio\n\n")
        
        # Dados de visualização (similar ao Carga ANDE)
        visualization_data = {
            "table": normalized_data,
            "chart_data": None,
            "visualization_type": "table_with_summary" if mw_medios else "table_only",
            "tool_name": tool_name,
        }
        
        # Adicionar MW médios para o summary (similar ao Carga ANDE)
        if mw_medios:
            visualization_data["mw_medios"] = mw_medios
        
        # Adicionar informações adicionais
        if par:
            visualization_data["par"] = par
        if duracoes:
            visualization_data["duracoes"] = duracoes
        if pares_disponiveis:
            visualization_data["pares_disponiveis"] = pares_disponiveis
        
        return {
            "final_response": "".join(response_parts),
            "visualization_data": visualization_data
        }
    
    def _normalize_data(
        self, 
        data: List[Dict[str, Any]], 
        duracoes: Dict[str, Optional[float]],
        par: Optional[Dict[str, str]]
    ) -> List[Dict[str, Any]]:
        """
        Normaliza os dados de limites de intercâmbio para um formato consistente.
        Expande por patamar E sentido para melhor visualização (similar ao Carga ANDE).
        
        Formato:
        - SENTIDO (DE->PARA ou PARA->DE)
        - PATAMAR (PESADA, MEDIA, LEVE)
        - LIMITE (MW)
        - DURAÇÃO (HORAS) - se disponível
        
        Args:
            data: Lista de dicionários com dados dos limites
            duracoes: Dict com durações dos patamares
            par: Dict com par de submercados (se específico)
            
        Returns:
            Lista de dicionários normalizados (expandidos por patamar e sentido)
        """
        normalized = []
        
        # Mapeamento de nomes de patamar
        patamar_names = {
            "pesada": "PESADA",
            "media": "MEDIA",
            "leve": "LEVE"
        }
        
        patamar_numbers = {
            "pesada": 1,
            "media": 2,
            "leve": 3
        }
        
        # Mapeamento de índices para patamares
        patamar_map = {
            1: "pesada",  # P1 = Pesada
            2: "media",   # P2 = Media
            3: "leve"     # P3 = Leve
        }
        
        for record in data:
            sub_de = record.get("sub_de", "?")
            sub_para = record.get("sub_para", "?")
            estagio = record.get("estagio", "?")
            
            # Processar sentido DE->PARA
            limite_de_para_p1 = record.get("limite_de_para_p1")
            limite_de_para_p2 = record.get("limite_de_para_p2")
            limite_de_para_p3 = record.get("limite_de_para_p3")
            
            if any(v is not None for v in [limite_de_para_p1, limite_de_para_p2, limite_de_para_p3]):
                sentido_label = f"{sub_de} → {sub_para}"
                
                for pat_num, pat_key in patamar_map.items():
                    limite_key = f"limite_de_para_p{pat_num}"
                    limite_val = record.get(limite_key)
                    
                    if limite_val is not None:
                        duracao = None
                        if duracoes and pat_key in duracoes:
                            duracao = duracoes.get(pat_key)
                        
                        normalized_record = {
                            "sentido": sentido_label,
                            "patamar": patamar_names.get(pat_key, f"P{pat_num}"),
                            "patamar_numero": pat_num,
                            "limite_mw": limite_val,
                            "duracao_horas": duracao,
                            "estagio": estagio,
                            "sub_de": sub_de,
                            "sub_para": sub_para,
                        }
                        normalized.append(normalized_record)
            
            # Processar sentido PARA->DE
            limite_para_de_p1 = record.get("limite_para_de_p1")
            limite_para_de_p2 = record.get("limite_para_de_p2")
            limite_para_de_p3 = record.get("limite_para_de_p3")
            
            if any(v is not None for v in [limite_para_de_p1, limite_para_de_p2, limite_para_de_p3]):
                sentido_label = f"{sub_para} → {sub_de}"
                
                for pat_num, pat_key in patamar_map.items():
                    limite_key = f"limite_para_de_p{pat_num}"
                    limite_val = record.get(limite_key)
                    
                    if limite_val is not None:
                        duracao = None
                        if duracoes and pat_key in duracoes:
                            duracao = duracoes.get(pat_key)
                        
                        normalized_record = {
                            "sentido": sentido_label,
                            "patamar": patamar_names.get(pat_key, f"P{pat_num}"),
                            "patamar_numero": pat_num,
                            "limite_mw": limite_val,
                            "duracao_horas": duracao,
                            "estagio": estagio,
                            "sub_de": sub_de,
                            "sub_para": sub_para,
                        }
                        normalized.append(normalized_record)
        
        safe_print(f"[LIMITES INTERCAMBIO FORMATTER] Total de registros normalizados: {len(normalized)}")
        
        return normalized
