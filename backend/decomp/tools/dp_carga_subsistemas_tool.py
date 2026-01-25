"""
Tool para consultar informações do Bloco DP (Carga dos Subsistemas) do DECOMP.
Acessa dados de demanda por patamar, duração dos patamares, etc.
"""
from backend.decomp.tools.base import DECOMPTool
from backend.decomp.config import safe_print
from idecomp.decomp import Dadger
import os
import pandas as pd
import re
from typing import Dict, Any, Optional, List

# Mapeamento de nomes de submercado para códigos
SUBMERCADO_NAMES = {
    1: "SUDESTE",
    2: "SUL",
    3: "NORDESTE",
    4: "NORTE"
}

# Mapeamento reverso: nome (lowercase) -> código
SUBMERCADO_NAMES_REVERSE = {
    "sudeste": 1,
    "sul": 2,
    "nordeste": 3,
    "norte": 4
}

class DPCargaSubsistemasTool(DECOMPTool):
    """
    Tool para consultar informações do Bloco DP (Carga dos Subsistemas) do DECOMP.
    
    Dados disponíveis:
    - Estágio
    - Código do submercado
    - Número de patamares
    - Para cada patamar (1=PESADA, 2=MEDIA, 3=LEVE):
      - Demanda (MWmed)
      - Duração do patamar (horas)
    """
    
    def get_name(self) -> str:
        return "DPCargaSubsistemasTool"
    
    def can_handle(self, query: str) -> bool:
        """
        Verifica se a query é sobre carga dos subsistemas do Bloco DP.
        
        Args:
            query: Query do usuário
            
        Returns:
            True se a tool pode processar a query
        """
        query_lower = query.lower()
        
        # Excluir explicitamente carga mensal (deve ser CargaMensalTool do NEWAVE)
        if "carga mensal" in query_lower or "demanda mensal" in query_lower:
            return False
        
        keywords = [
            "carga dos subsistemas",
            "carga subsistemas",
            "demanda subsistemas",
            "demanda dos subsistemas",
            "bloco dp",
            "registro dp",
            "dp decomp",
            "patamares de carga",
            "patamares carga",
            "duração patamares",
            "duracao patamares",
            "demanda por patamar",
            "carga por patamar",
            "mwmed",
            "mw médio",
            "mw medio",
            "carga média ponderada",
            "carga media ponderada",
            "calcular carga média",
            "calcular carga media",
            "média ponderada carga",
            "media ponderada carga",
            "calcular mw médio",
            "calcular mw medio",
            "carga ponderada",
            "demanda média ponderada",
            "demanda media ponderada",
        ]
        
        # Verificar se há keywords relacionados a carga/patamares
        tem_keyword = any(kw in query_lower for kw in keywords)
        
        # Verificar se menciona algum nome de submercado junto com termos relacionados a carga/patamares
        nomes_submercados = ["sudeste", "sul", "nordeste", "norte"]
        tem_nome_submercado = any(nome in query_lower for nome in nomes_submercados)
        tem_termo_carga = any(termo in query_lower for termo in [
            "carga", "demanda", "patamar", "mw", "média", "media", "ponderada"
        ])
        
        # Se menciona nome de submercado E termos relacionados a carga, também pode processar
        return tem_keyword or (tem_nome_submercado and tem_termo_carga)
    
    def get_description(self) -> str:
        return """
        Tool para consultar informações do Bloco DP (Carga dos Subsistemas) do DECOMP.
        
        Acessa dados do registro DP que define:
        - Carga/Demanda dos subsistemas por patamar
        - Estágio de operação
        - Código do submercado
        - Número de patamares
        - Dados por patamar (1=PESADA, 2=MEDIA, 3=LEVE):
          * Demanda (MWmed - MW médio)
          * Duração do patamar (horas)
        
        Exemplos de queries:
        - "Quais são as cargas dos subsistemas?"
        - "Qual a demanda do submercado 1 no estágio 1?"
        - "Mostre os patamares de carga"
        - "Demanda por patamar do Sudeste"
        - "Carga média ponderada do Sudeste"
        - "MW médio do submercado Sul"
        - "Carga do Nordeste"
        - "Patamares de carga do Norte"
        - "Carga média ponderada do submercado Sudeste"
        """
    
    def execute(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Executa a consulta sobre carga dos subsistemas do Bloco DP.
        
        Args:
            query: Query do usuário
            **kwargs: Argumentos adicionais opcionais
            
        Returns:
            Dict com dados da carga dos subsistemas formatados
        """
        try:
            # ⚡ OTIMIZAÇÃO: Usar cache global do Dadger
            from backend.decomp.utils.dadger_cache import get_cached_dadger
            dadger = get_cached_dadger(self.deck_path)
            
            if dadger is None:
                return {
                    "success": False,
                    "error": "Arquivo dadger não encontrado (nenhum arquivo dadger.rv* encontrado)"
                }
            
            # Extrair filtros da query
            codigo_submercado = self._extract_codigo_submercado(query)
            estagio = self._extract_estagio(query)
            numero_patamares = self._extract_numero_patamares(query)
            
            safe_print(f"[DP TOOL] Query recebida: {query}")
            safe_print(f"[DP TOOL] Codigo submercado extraido: {codigo_submercado}")
            safe_print(f"[DP TOOL] Estagio extraido: {estagio}")
            safe_print(f"[DP TOOL] Numero patamares extraido: {numero_patamares}")

            # 🎯 Regra de UX: se o usuário filtra apenas por submercado (sem estágio),
            # sempre assumimos ESTÁGIO 1. Não há caso de uso para listar todos os estágios.
            if codigo_submercado is not None and estagio is None:
                estagio = 1
                safe_print(
                    "[DP TOOL] Nenhum estágio especificado na query; "
                    "assumindo estagio=1 por padrão para submercado filtrado"
                )
            
            # Obter dados da carga dos subsistemas
            dp_data = dadger.dp(
                codigo_submercado=codigo_submercado,
                estagio=estagio,
                numero_patamares=numero_patamares,
                df=True  # Retornar como DataFrame
            )
            
            if dp_data is None or (isinstance(dp_data, pd.DataFrame) and dp_data.empty):
                return {
                    "success": False,
                    "error": "Nenhum registro de carga encontrado com os filtros especificados"
                }
            
            # DEBUG: Verificar colunas reais do DataFrame
            if isinstance(dp_data, pd.DataFrame):
                safe_print(f"[DP TOOL] Colunas disponíveis: {list(dp_data.columns)}")
                if len(dp_data) > 0:
                    safe_print(f"[DP TOOL] Primeiro registro: {dp_data.iloc[0].to_dict()}")
                    safe_print(f"[DP TOOL] Total de registros ANTES do filtro manual: {len(dp_data)}")
                
                # 🔒 FILTRO MANUAL: Garantir que apenas o submercado solicitado seja retornado
                # (o dadger.dp() pode não estar filtrando corretamente)
                if codigo_submercado is not None:
                    col_submercado = None
                    # Tentar encontrar a coluna de submercado (pode ter nomes diferentes)
                    for col in ["codigo_submercado", "submercado", "s", "codigo_submercado"]:
                        if col in dp_data.columns:
                            col_submercado = col
                            break
                    
                    if col_submercado:
                        # Filtrar DataFrame para apenas o submercado solicitado
                        dp_data = dp_data[dp_data[col_submercado] == codigo_submercado].copy()
                        safe_print(f"[DP TOOL] Filtro manual aplicado: submercado={codigo_submercado}")
                        safe_print(f"[DP TOOL] Total de registros APÓS filtro manual: {len(dp_data)}")
                    else:
                        safe_print(f"[DP TOOL] ⚠️ Aviso: não foi possível encontrar coluna de submercado para filtrar")
                
                # 🔒 FILTRO MANUAL: Garantir que apenas o estágio solicitado seja retornado
                if estagio is not None:
                    col_estagio = None
                    # Tentar encontrar a coluna de estágio
                    for col in ["estagio", "ip", "estagio"]:
                        if col in dp_data.columns:
                            col_estagio = col
                            break
                    
                    if col_estagio:
                        # Filtrar DataFrame para apenas o estágio solicitado
                        dp_data = dp_data[dp_data[col_estagio] == estagio].copy()
                        safe_print(f"[DP TOOL] Filtro manual aplicado: estagio={estagio}")
                        safe_print(f"[DP TOOL] Total de registros APÓS filtro de estágio: {len(dp_data)}")
                    else:
                        safe_print(f"[DP TOOL] ⚠️ Aviso: não foi possível encontrar coluna de estágio para filtrar")

            # Detectar se precisa calcular carga média ponderada (antes de converter para dict)
            query_lower = query.lower()
            calcular_media = any(kw in query_lower for kw in [
                "carga média ponderada",
                "carga media ponderada",
                "mw médio",
                "mw medio",
                "calcular carga média",
                "calcular carga media",
                "carga média dos patamares",
                "carga media dos patamares",
                "média ponderada carga",
                "media ponderada carga",
                "calcular mw médio",
                "calcular mw medio",
                "carga ponderada",
                "demanda média ponderada",
                "demanda media ponderada",
            ])

            #  Regra adicional: sempre que tivermos um submercado + estágio bem definidos
            # (inclusive quando o estágio foi assumido como 1), faz sentido mostrar a
            # carga média ponderada daquele caso, mesmo que o usuário não tenha usado
            # explicitamente as palavras-chave de "média ponderada".
            if codigo_submercado is not None and estagio is not None:
                calcular_media = True

            # 🔁 Regra de UX: se for cálculo de média ponderada e o usuário
            # não especificar estágio, usamos apenas o primeiro estágio disponível
            # daquele submercado para fazer a conta (em vez de todos).
            if calcular_media and estagio is None and isinstance(dp_data, pd.DataFrame):
                try:
                    if "estagio" in dp_data.columns:
                        estagios_unicos = sorted(dp_data["estagio"].dropna().unique().tolist())
                        if estagios_unicos:
                            estagio_selecionado = estagios_unicos[0]
                            safe_print(
                                f"[DP TOOL] Nenhum estágio especificado; "
                                f"usando estagio={estagio_selecionado} para cálculo de média ponderada"
                            )
                            dp_data = dp_data[dp_data["estagio"] == estagio_selecionado]
                            # Atualiza estagio nos filtros para refletir a escolha
                            try:
                                estagio = int(estagio_selecionado)
                            except Exception:
                                estagio = estagio_selecionado
                except Exception as e:
                    safe_print(f"[DP TOOL] Aviso: não foi possível restringir para primeiro estágio: {e}")
            
            # Converter para formato padronizado
            if isinstance(dp_data, pd.DataFrame):
                data = dp_data.to_dict('records')
            elif isinstance(dp_data, list):
                data = [self._dp_to_dict(dp) for dp in dp_data]
            else:
                data = [self._dp_to_dict(dp_data)]
            
            # Se detectar query de cálculo, adicionar MW médio aos dados
            if calcular_media:
                safe_print(f"[DP TOOL] Calculando carga média ponderada para {len(data)} registros")
                for idx, record in enumerate(data):
                    safe_print(f"[DP TOOL] Registro {idx+1}: {list(record.keys())}")
                    resultado = self._calcular_carga_media_ponderada(record)
                    if resultado:
                        safe_print(f"[DP TOOL] ✅ MW médio calculado: {resultado.get('mw_medio')}")
                        record.update(resultado)
                    else:
                        safe_print(f"[DP TOOL] ⚠️ Não foi possível calcular MW médio para registro {idx+1}")
            
            safe_print(f"[DP TOOL] Retornando {len(data)} registros de carga dos subsistemas")
            safe_print(f"[DP TOOL] Filtros aplicados: submercado={codigo_submercado}, estagio={estagio}, patamares={numero_patamares}")
            safe_print(f"[DP TOOL] Calcular média ponderada: {calcular_media}")
            
            # Preparar filtros
            filtros_dict = {
                "codigo_submercado": codigo_submercado,
                "estagio": estagio,
                "numero_patamares": numero_patamares,
            }
            
            return {
                "success": True,
                "data": data,
                "total_registros": len(data),
                "filtros": filtros_dict,
                "calcular_media_ponderada": calcular_media,
                "tool": self.get_name()
            }
            
        except Exception as e:
            safe_print(f"[DP TOOL] ❌ Erro ao consultar Bloco DP: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": f"Erro ao consultar Bloco DP: {str(e)}",
                "tool": self.get_name()
            }
    
    def _extract_codigo_submercado(self, query: str) -> Optional[int]:
        """
        Extrai código do submercado da query.
        Aceita tanto códigos numéricos quanto nomes dos submercados.
        """
        query_lower = query.lower()
        
        # Primeiro, tentar extrair por código numérico
        patterns = [
            r'submercado\s*(\d+)',
            r'su\s*(\d+)',
            r'subsistema\s*(\d+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, query_lower)
            if match:
                try:
                    codigo = int(match.group(1))
                    safe_print(f"[DP TOOL] Código de submercado extraído por padrão numérico: {codigo}")
                    return codigo
                except ValueError:
                    continue
        
        # Se não encontrou código numérico, tentar por nome do submercado
        # Verificar padrões como "do sudeste", "submercado sudeste", "sudeste", etc.
        for nome_submercado, codigo in SUBMERCADO_NAMES_REVERSE.items():
            # Padrões para buscar o nome do submercado
            padroes = [
                f"do {nome_submercado}",
                f"da {nome_submercado}",
                f"de {nome_submercado}",
                f"submercado {nome_submercado}",
                f"subsistema {nome_submercado}",
                f"\\b{nome_submercado}\\b",  # Palavra completa (word boundary)
            ]
            
            for padrao in padroes:
                if re.search(padrao, query_lower):
                    safe_print(f"[DP TOOL] Código de submercado extraído por nome '{nome_submercado.upper()}': {codigo}")
                    return codigo
        
        return None
    
    def _extract_estagio(self, query: str) -> Optional[int]:
        """Extrai estágio da query."""
        patterns = [
            r'estágio\s*(\d+)',
            r'estagio\s*(\d+)',
            r'estágio\s*(\d+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, query.lower())
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    continue
        return None
    
    def _extract_numero_patamares(self, query: str) -> Optional[int]:
        """Extrai número de patamares da query."""
        patterns = [
            r'patamares?\s*(\d+)',
            r'pat\s*(\d+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, query.lower())
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    continue
        return None
    
    def _dp_to_dict(self, dp_obj) -> Dict[str, Any]:
        """Converte objeto DP para dict."""
        if isinstance(dp_obj, dict):
            return dp_obj
        if hasattr(dp_obj, '__dict__'):
            return dp_obj.__dict__
        
        # Extrair atributos conhecidos do registro DP
        # Tentar múltiplas variações de nomes de atributos
        result = {}
        
        # Campos básicos
        result["estagio"] = (
            getattr(dp_obj, 'estagio', None) or
            getattr(dp_obj, 'ip', None)
        )
        result["codigo_submercado"] = (
            getattr(dp_obj, 'codigo_submercado', None) or
            getattr(dp_obj, 'submercado', None) or
            getattr(dp_obj, 's', None)
        )
        result["numero_patamares"] = (
            getattr(dp_obj, 'numero_patamares', None) or
            getattr(dp_obj, 'patamares', None) or
            getattr(dp_obj, 'pat', None) or
            3
        )
        
        # Campos de demanda e duração por patamar - tentar todas as variações
        for patamar_idx in [1, 2, 3]:
            # Demanda
            demanda = (
                getattr(dp_obj, f'demanda_patamar_{patamar_idx}', None) or
                getattr(dp_obj, f'demanda_{patamar_idx}', None) or
                getattr(dp_obj, f'mwmed_{patamar_idx}', None) or
                getattr(dp_obj, f'mwmed_patamar_{patamar_idx}', None) or
                getattr(dp_obj, f'mwmed_pat{patamar_idx}', None) or
                getattr(dp_obj, f'demanda_pat{patamar_idx}', None)
            )
            result[f"demanda_patamar_{patamar_idx}"] = demanda
            
            # Duração
            duracao = (
                getattr(dp_obj, f'duracao_patamar_{patamar_idx}', None) or
                getattr(dp_obj, f'duracao_{patamar_idx}', None) or
                getattr(dp_obj, f'horas_{patamar_idx}', None) or
                getattr(dp_obj, f'horas_patamar_{patamar_idx}', None) or
                getattr(dp_obj, f'duracao_pat{patamar_idx}', None) or
                getattr(dp_obj, f'horas_pat{patamar_idx}', None)
            )
            result[f"duracao_patamar_{patamar_idx}"] = duracao
        
        return result
    
    def _calcular_carga_media_ponderada(self, record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Calcula carga média ponderada usando a fórmula de patamares."""
        # Extrair valores de demanda por patamar
        val_pesada = self._extrair_valor(record, "demanda", 1)
        val_media = self._extrair_valor(record, "demanda", 2)
        val_leve = self._extrair_valor(record, "demanda", 3)
        
        # Extrair durações por patamar
        dur_pesada = self._extrair_valor(record, "duracao", 1)
        dur_media = self._extrair_valor(record, "duracao", 2)
        dur_leve = self._extrair_valor(record, "duracao", 3)
        
        # Validar dados
        valores = [val_pesada, val_media, val_leve, dur_pesada, dur_media, dur_leve]
        if any(v is None for v in valores):
            return None
        
        # Converter para float
        try:
            val_pesada = float(val_pesada) if val_pesada is not None else 0.0
            val_media = float(val_media) if val_media is not None else 0.0
            val_leve = float(val_leve) if val_leve is not None else 0.0
            dur_pesada = float(dur_pesada) if dur_pesada is not None else 0.0
            dur_media = float(dur_media) if dur_media is not None else 0.0
            dur_leve = float(dur_leve) if dur_leve is not None else 0.0
        except (ValueError, TypeError):
            return None
        
        # Calcular numerador e denominador
        numerador = (val_leve * dur_leve) + (val_media * dur_media) + (val_pesada * dur_pesada)
        denominador = dur_leve + dur_media + dur_pesada
        
        if denominador == 0:
            return None
        
        # Calcular MW médio
        mw_medio = numerador / denominador
        
        return {
            "carga_media_ponderada": round(mw_medio, 2),
            "mw_medio": round(mw_medio, 2),
            "patamares": {
                "pesada": {
                    "demanda_mwmed": round(val_pesada, 2),
                    "duracao_horas": round(dur_pesada, 2)
                },
                "media": {
                    "demanda_mwmed": round(val_media, 2),
                    "duracao_horas": round(dur_media, 2)
                },
                "leve": {
                    "demanda_mwmed": round(val_leve, 2),
                    "duracao_horas": round(dur_leve, 2)
                }
            }
        }
    
    def _extrair_valor(self, record: Dict[str, Any], tipo: str, patamar: int) -> Optional[float]:
        """Extrai valor de demanda ou duração do registro."""
        if tipo == "demanda":
            keys = [
                f"carga_{patamar}",  # Formato do DataFrame: carga_1, carga_2, carga_3
                f"demanda_patamar_{patamar}",
                f"demanda_{patamar}",
                f"mwmed_{patamar}",
                f"mwmed_patamar_{patamar}",
                f"mwmed_pat{patamar}",
                f"demanda_pat{patamar}",
            ]
        else:  # duracao
            keys = [
                f"duracao_{patamar}",  # Formato do DataFrame: duracao_1, duracao_2, duracao_3
                f"duracao_patamar_{patamar}",
                f"horas_{patamar}",
                f"horas_patamar_{patamar}",
                f"duracao_pat{patamar}",
                f"horas_pat{patamar}",
            ]
        
        for key in keys:
            value = record.get(key)
            if value is not None:
                try:
                    return float(value)
                except (ValueError, TypeError):
                    continue
        
        return None
