"""
Tool para calcular disponibilidade total de uma usina termelétrica.
Combina dados dos blocos CT (inflexibilidades) e DP (durações dos patamares).

OTIMIZADO: Carrega CT apenas uma vez, regex pré-compiladas, operações vetorizadas.
"""
from decomp_agent.app.tools.base import DECOMPTool
from decomp_agent.app.config import safe_print
from idecomp.decomp import Dadger
import os
import pandas as pd
import re
from typing import Dict, Any, Optional, List
from difflib import SequenceMatcher

class DisponibilidadeUsinaTool(DECOMPTool):
    """
    Tool para calcular disponibilidade total de uma usina termelétrica.
    
    Combina dados de:
    - Bloco CT: Inflexibilidades por patamar (PESADA, MEDIA, LEVE)
    - Bloco DP: Durações dos patamares em horas
    
    Fórmula:
    Disponibilidade Total = 
      (Inflexibilidade_Leve × Duração_Leve + 
       Inflexibilidade_Médio × Duração_Médio + 
       Inflexibilidade_Pesada × Duração_Pesada) 
      / 
      (Duração_Leve + Duração_Médio + Duração_Pesada)
    """
    
    # ⚡ OTIMIZAÇÃO: Patterns compilados UMA vez (não toda chamada)
    _CODIGO_PATTERNS = [
        re.compile(r'usina\s*(\d+)'),
        re.compile(r'usina\s*térmica\s*(\d+)'),
        re.compile(r'usina\s*termica\s*(\d+)'),
        re.compile(r'usina\s*#?\s*(\d+)'),
        re.compile(r'código\s*(\d+)'),
        re.compile(r'codigo\s*(\d+)'),
        re.compile(r'térmica\s*(\d+)'),
        re.compile(r'termica\s*(\d+)'),
        re.compile(r'ute\s*(\d+)'),
    ]
    
    # ⚡ OTIMIZAÇÃO: Palavras ignoradas como frozenset (busca O(1))
    _PALAVRAS_IGNORAR = frozenset({
        'de', 'da', 'do', 'das', 'dos', 'e', 'a', 'o', 'as', 'os', 
        'em', 'na', 'no', 'nas', 'nos', 'qual', 'disponibilidade'
    })
    
    def get_name(self) -> str:
        return "DisponibilidadeUsinaTool"
    
    def can_handle(self, query: str) -> bool:
        """
        Verifica se a query é sobre cálculo de disponibilidade de usina.
        
        Args:
            query: Query do usuário
            
        Returns:
            True se a tool pode processar a query
        """
        query_lower = query.lower()
        keywords = [
            "disponibilidade",
            "disponibilidade usina",
            "disponibilidade da usina",
            "calcular disponibilidade",
            "disponibilidade total",
            "disponibilidade de",
            "disponibilidade cubatao",
            "disponibilidade angra",
        ]
        return any(kw in query_lower for kw in keywords)
    
    def get_description(self) -> str:
        return """
        Tool para calcular disponibilidade total de uma usina termelétrica.
        
        Combina dados dos blocos CT e DP do DECOMP:
        - Bloco CT: Inflexibilidades por patamar (PESADA, MEDIA, LEVE) no estágio 1
        - Bloco DP: Durações dos patamares em horas no estágio 1
        
        Fórmula de cálculo:
        Disponibilidade Total = 
          (Inflexibilidade_Leve × Duração_Leve + 
           Inflexibilidade_Médio × Duração_Médio + 
           Inflexibilidade_Pesada × Duração_Pesada) 
          / 
          (Duração_Leve + Duração_Médio + Duração_Pesada)
        
        Exemplos de queries:
        - "Qual a disponibilidade de Cubatao?"
        - "Calcular disponibilidade da usina 97"
        - "Disponibilidade total de Angra 1"
        """
    
    def execute(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Executa o cálculo de disponibilidade para uma usina.
        
        OTIMIZADO: Carrega CT apenas UMA vez e passa para os métodos.
        
        Args:
            query: Query do usuário
            **kwargs: Argumentos adicionais opcionais
            
        Returns:
            Dict com resultado do cálculo e detalhes
        """
        try:
            # ⚡ OTIMIZAÇÃO: Usar cache global do Dadger
            from decomp_agent.app.utils.dadger_cache import get_cached_dadger
            dadger = get_cached_dadger(self.deck_path)
            
            if dadger is None:
                return {
                    "success": False,
                    "error": "Arquivo dadger não encontrado (nenhum arquivo dadger.rv* encontrado)"
                }
            
            verbose = kwargs.get("verbose", True)
            if verbose:
                safe_print(f"[DISPONIBILIDADE TOOL] Query recebida: {query}")
            
            # ⚡ OTIMIZAÇÃO: Carregar CT DataFrame UMA ÚNICA VEZ
            ct_df = dadger.ct(estagio=1, df=True)
            if ct_df is None or (isinstance(ct_df, pd.DataFrame) and ct_df.empty):
                return {
                    "success": False,
                    "error": "Dados do bloco CT (estágio 1) não encontrados"
                }
            
            # Passar ct_df já carregado para evitar leituras duplicadas
            codigo_usina = self._extract_usina_from_query_fast(query, ct_df)
            
            if codigo_usina is None:
                return {
                    "success": False,
                    "error": "Não foi possível identificar a usina na query. Por favor, especifique o nome ou código da usina (ex: 'disponibilidade de Cubatao' ou 'disponibilidade da usina 97')"
                }
            
            if verbose:
                safe_print(f"[DISPONIBILIDADE TOOL] Usina identificada: código {codigo_usina}")
            
            # ⚡ Chamar método otimizado passando ct_df já carregado
            return self._execute_with_ct_loaded(codigo_usina, dadger, ct_df, verbose=verbose)
            
        except Exception as e:
            safe_print(f"[DISPONIBILIDADE TOOL] ❌ Erro ao calcular disponibilidade: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": f"Erro ao calcular disponibilidade: {str(e)}",
                "tool": self.get_name()
            }
    
    def _extract_usina_from_query_fast(self, query: str, ct_df: pd.DataFrame) -> Optional[int]:
        """
        ⚡ VERSÃO OTIMIZADA: Extrai código da usina da query.
        Recebe ct_df já carregado para evitar leituras duplicadas.
        
        Otimizações:
        - Usa patterns pré-compilados (constantes de classe)
        - Recebe ct_df já carregado
        - Operações vetorizadas do pandas
        - Early return agressivo
        
        Args:
            query: Query do usuário
            ct_df: DataFrame do bloco CT já carregado
            
        Returns:
            Código da usina ou None
        """
        query_lower = query.lower()
        
        # ⚡ OTIMIZAÇÃO: Códigos válidos extraídos UMA vez (operação vetorizada)
        codigos_validos = set(ct_df['codigo_usina'].unique())
        
        # ETAPA 1: Tentar extrair código numérico (usa patterns pré-compilados)
        for pattern in self._CODIGO_PATTERNS:
            match = pattern.search(query_lower)
            if match:
                try:
                    codigo = int(match.group(1))
                    if codigo in codigos_validos:
                        safe_print(f"[DISPONIBILIDADE TOOL] ✅ Código {codigo} encontrado por padrão numérico")
                        return codigo  # Early return!
                except (ValueError, KeyError):
                    continue
        
        # ETAPA 2: Buscar por nome (operações vetorizadas)
        if 'nome_usina' not in ct_df.columns:
            return None
        
        # ⚡ OTIMIZAÇÃO: Preparar dados uma vez com operações vetorizadas
        usinas_unicas = ct_df[['codigo_usina', 'nome_usina']].drop_duplicates()
        usinas_unicas = usinas_unicas.dropna(subset=['nome_usina'])
        usinas_unicas = usinas_unicas.copy()
        usinas_unicas['nome_lower'] = usinas_unicas['nome_usina'].str.lower().str.strip()
        
        # Criar dicionário para busca O(1)
        nome_to_codigo = dict(zip(usinas_unicas['nome_lower'], usinas_unicas['codigo_usina']))
        
        # PRIORIDADE 1: Match exato (busca O(1))
        query_stripped = query_lower.strip()
        if query_stripped in nome_to_codigo:
            codigo = int(nome_to_codigo[query_stripped])
            safe_print(f"[DISPONIBILIDADE TOOL] ✅ Código {codigo} encontrado por match exato")
            return codigo
        
        # PRIORIDADE 2: Nome completo contido na query
        for nome_lower, codigo in nome_to_codigo.items():
            if len(nome_lower) >= 4 and nome_lower in query_lower:
                # Verificar word boundaries
                pattern = r'\b' + re.escape(nome_lower) + r'\b'
                if re.search(pattern, query_lower):
                    safe_print(f"[DISPONIBILIDADE TOOL] ✅ Código {int(codigo)} encontrado por nome completo na query")
                    return int(codigo)  # Early return!
        
        # PRIORIDADE 3: Match de todas as palavras significativas
        palavras_query = set(p for p in query_lower.split() if len(p) > 2 and p not in self._PALAVRAS_IGNORAR)
        
        for _, row in usinas_unicas.itertuples():
            nome_lower = row.nome_lower
            palavras_nome = set(p for p in nome_lower.split() if len(p) > 2 and p not in self._PALAVRAS_IGNORAR)
            if palavras_nome and all(p in query_lower for p in palavras_nome):
                safe_print(f"[DISPONIBILIDADE TOOL] ✅ Código {int(row.codigo_usina)} encontrado: todas palavras significativas")
                return int(row.codigo_usina)
        
        # PRIORIDADE 4: Similaridade (apenas se não encontrou antes)
        candidatos = []
        for _, row in usinas_unicas.itertuples():
            nome_lower = row.nome_lower
            similarity = SequenceMatcher(None, query_lower, nome_lower).ratio()
            if similarity > 0.6:
                candidatos.append((int(row.codigo_usina), nome_lower, similarity))
        
        if candidatos:
            candidatos.sort(key=lambda x: x[2], reverse=True)
            melhor = candidatos[0]
            safe_print(f"[DISPONIBILIDADE TOOL] ✅ Código {melhor[0]} encontrado por similaridade (score: {melhor[2]:.2f})")
            return melhor[0]
        
        return None
    
    def _execute_with_ct_loaded(
        self, 
        codigo_usina: int, 
        dadger: Any,
        ct_df: pd.DataFrame,
        verbose: bool = True
    ) -> Dict[str, Any]:
        """
        ⚡ VERSÃO OTIMIZADA: Executa cálculo com ct_df já carregado.
        Evita leitura duplicada do bloco CT.
        
        Args:
            codigo_usina: Código da usina já identificado
            dadger: Objeto Dadger já carregado
            ct_df: DataFrame do bloco CT já carregado
            verbose: Se True, exibe logs detalhados
            
        Returns:
            Dict com resultado do cálculo e detalhes
        """
        try:
            # ⚡ OTIMIZAÇÃO: Não precisa chamar dadger.ct() novamente!
            # Filtrar diretamente no DataFrame já carregado
            ct_filtrado = ct_df[ct_df['codigo_usina'] == codigo_usina]
            
            if ct_filtrado.empty:
                return {
                    "success": False,
                    "error": f"Usina {codigo_usina} não encontrada no bloco CT (estágio 1)"
                }
            
            ct_record = ct_filtrado.iloc[0].to_dict()
            
            # Extrair informações da usina
            nome_usina = str(ct_record.get('nome_usina', '')).strip() or f"Usina {codigo_usina}"
            codigo_submercado = ct_record.get('codigo_submercado') or ct_record.get('submercado')
            
            if codigo_submercado is None:
                return {
                    "success": False,
                    "error": f"Não foi possível identificar o submercado da usina {codigo_usina}"
                }
            
            if verbose:
                safe_print(f"[DISPONIBILIDADE TOOL] Submercado identificado: {codigo_submercado}")
            
            # Extrair inflexibilidades dos 3 patamares
            inflexibilidades = self._extract_inflexibilidades(ct_record)
            
            if not inflexibilidades or all(v is None for v in inflexibilidades.values()):
                return {
                    "success": False,
                    "error": f"Não foi possível extrair inflexibilidades da usina {codigo_usina} no bloco CT"
                }
            
            if verbose:
                safe_print(f"[DISPONIBILIDADE TOOL] Inflexibilidades: {inflexibilidades}")
            
            # Buscar dados do DP (estágio 1, submercado)
            dp_data = dadger.dp(
                codigo_submercado=codigo_submercado,
                estagio=1,
                df=True
            )
            
            if dp_data is None or (isinstance(dp_data, pd.DataFrame) and dp_data.empty):
                return {
                    "success": False,
                    "error": f"Dados do bloco DP não encontrados para submercado {codigo_submercado} (estágio 1)"
                }
            
            # Filtrar DP
            dp_record = None
            if isinstance(dp_data, pd.DataFrame):
                for col_sub in ['codigo_submercado', 'submercado', 's']:
                    if col_sub in dp_data.columns:
                        dp_filtrado = dp_data[dp_data[col_sub] == codigo_submercado]
                        if not dp_filtrado.empty:
                            dp_record = dp_filtrado.iloc[0].to_dict()
                            break
            
            if dp_record is None:
                return {
                    "success": False,
                    "error": f"Dados do bloco DP não encontrados para submercado {codigo_submercado} no estágio 1"
                }
            
            # Extrair durações dos patamares
            duracoes = self._extract_duracoes(dp_record)
            
            if not duracoes or all(v is None for v in duracoes.values()):
                return {
                    "success": False,
                    "error": f"Não foi possível extrair durações dos patamares do bloco DP"
                }
            
            if verbose:
                safe_print(f"[DISPONIBILIDADE TOOL] Durações: {duracoes}")
            
            # Calcular disponibilidade total
            resultado = self._calcular_disponibilidade(inflexibilidades, duracoes)
            
            if resultado is None:
                return {
                    "success": False,
                    "error": "Erro ao calcular disponibilidade. Verifique se todos os dados necessários estão disponíveis."
                }
            
            # Preparar resposta estruturada
            return {
                "success": True,
                "disponibilidade_total": resultado["disponibilidade_total"],
                "usina": {
                    "codigo": codigo_usina,
                    "nome": nome_usina,
                    "submercado": codigo_submercado
                },
                "detalhes": {
                    "pesada": {
                        "inflexibilidade": inflexibilidades.get("pesada"),
                        "duracao": duracoes.get("pesada")
                    },
                    "media": {
                        "inflexibilidade": inflexibilidades.get("media"),
                        "duracao": duracoes.get("media")
                    },
                    "leve": {
                        "inflexibilidade": inflexibilidades.get("leve"),
                        "duracao": duracoes.get("leve")
                    }
                },
                "calculo": resultado["calculo"],
                "tool": self.get_name()
            }
            
        except Exception as e:
            safe_print(f"[DISPONIBILIDADE TOOL] ❌ Erro ao calcular disponibilidade: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": f"Erro ao calcular disponibilidade: {str(e)}",
                "tool": self.get_name()
            }
    
    def execute_with_codigo_usina(
        self, 
        codigo_usina: int, 
        dadger: Any,
        verbose: bool = True
    ) -> Dict[str, Any]:
        """
        Executa o cálculo de disponibilidade para uma usina (versão otimizada).
        Pula leitura de arquivo e extração de usina da query.
        
        Args:
            codigo_usina: Código da usina já identificado
            dadger: Objeto Dadger já carregado
            verbose: Se True, exibe logs detalhados
            
        Returns:
            Dict com resultado do cálculo e detalhes
        """
        try:
            
            # ETAPA 1: Buscar dados do CT (estágio 1)
            # IMPORTANTE: Quando df=True, os filtros são ignorados pelo idecomp
            # Então precisamos obter todos os dados e filtrar manualmente
            if verbose:
                safe_print(f"[DISPONIBILIDADE TOOL] Buscando dados do bloco CT (estágio 1)...")
            ct_data = dadger.ct(
                estagio=1,  # Sempre estágio 1 (semana 1)
                df=True
            )
            
            if ct_data is None or (isinstance(ct_data, pd.DataFrame) and ct_data.empty):
                return {
                    "success": False,
                    "error": f"Dados do bloco CT (estágio 1) não encontrados"
                }
            
            # Filtrar manualmente pelo codigo_usina (otimizado: usar iloc direto quando possível)
            if isinstance(ct_data, pd.DataFrame):
                if verbose:
                    safe_print(f"[DISPONIBILIDADE TOOL] CT DataFrame com {len(ct_data)} registros totais")
                
                # Filtrar pelo codigo_usina identificado
                ct_filtrado = ct_data[ct_data['codigo_usina'] == codigo_usina]
                
                if ct_filtrado.empty:
                    return {
                        "success": False,
                        "error": f"Usina {codigo_usina} não encontrada no bloco CT (estágio 1)"
                    }
                
                # Otimização: usar iloc[0] direto em vez de to_dict('records')
                ct_record = ct_filtrado.iloc[0].to_dict()
                if verbose:
                    safe_print(f"[DISPONIBILIDADE TOOL] CT filtrado para usina {codigo_usina}: 1 registro")
            else:
                ct_records = [ct_data] if not isinstance(ct_data, list) else ct_data
                # Filtrar manualmente se for lista
                ct_records = [r for r in ct_records if r.get('codigo_usina') == codigo_usina]
                
                if not ct_records:
                    return {
                        "success": False,
                        "error": f"Usina {codigo_usina} não encontrada no bloco CT (estágio 1)"
                    }
                
                ct_record = ct_records[0]
                if isinstance(ct_record, pd.Series):
                    ct_record = ct_record.to_dict()
            
            if verbose:
                safe_print(f"[DISPONIBILIDADE TOOL] Dados CT da usina {codigo_usina} obtidos: {ct_record}")
            
            # Extrair informações da usina
            nome_usina = str(ct_record.get('nome_usina', '')).strip() or f"Usina {codigo_usina}"
            codigo_submercado = ct_record.get('codigo_submercado') or ct_record.get('submercado')
            
            if codigo_submercado is None:
                return {
                    "success": False,
                    "error": f"Não foi possível identificar o submercado da usina {codigo_usina}"
                }
            
            if verbose:
                safe_print(f"[DISPONIBILIDADE TOOL] Submercado identificado: {codigo_submercado}")
            
            # ETAPA 2: Extrair inflexibilidades dos 3 patamares
            inflexibilidades = self._extract_inflexibilidades(ct_record)
            
            if not inflexibilidades or all(v is None for v in inflexibilidades.values()):
                return {
                    "success": False,
                    "error": f"Não foi possível extrair inflexibilidades da usina {codigo_usina} no bloco CT"
                }
            
            if verbose:
                safe_print(f"[DISPONIBILIDADE TOOL] Inflexibilidades: {inflexibilidades}")
            
            # ETAPA 3: Buscar dados do DP (estágio 1, submercado)
            if verbose:
                safe_print(f"[DISPONIBILIDADE TOOL] Buscando dados do bloco DP (estágio 1, submercado {codigo_submercado})...")
            dp_data = dadger.dp(
                codigo_submercado=codigo_submercado,
                estagio=1,  # Sempre estágio 1
                df=True
            )
            
            if dp_data is None or (isinstance(dp_data, pd.DataFrame) and dp_data.empty):
                return {
                    "success": False,
                    "error": f"Dados do bloco DP não encontrados para submercado {codigo_submercado} (estágio 1)"
                }
            
            # Otimização: Filtrar DataFrame antes de converter para dict
            dp_record = None
            if isinstance(dp_data, pd.DataFrame):
                if verbose:
                    safe_print(f"[DISPONIBILIDADE TOOL] DP DataFrame com {len(dp_data)} registros")
                
                # Filtrar por submercado diretamente no DataFrame
                for col_sub in ['codigo_submercado', 'submercado', 's']:
                    if col_sub in dp_data.columns:
                        dp_filtrado = dp_data[dp_data[col_sub] == codigo_submercado]
                        if not dp_filtrado.empty:
                            # Verificar estágio se disponível
                            for col_est in ['estagio', 'ip']:
                                if col_est in dp_filtrado.columns:
                                    dp_filtrado_est = dp_filtrado[dp_filtrado[col_est].fillna(1) == 1]
                                    if not dp_filtrado_est.empty:
                                        dp_record = dp_filtrado_est.iloc[0].to_dict()
                                        break
                            
                            if dp_record is None:
                                dp_record = dp_filtrado.iloc[0].to_dict()
                            
                            if dp_record:
                                break
                
                if dp_record is None:
                    # Fallback: tentar qualquer registro do submercado
                    for col_sub in ['codigo_submercado', 'submercado', 's']:
                        if col_sub in dp_data.columns:
                            dp_filtrado = dp_data[dp_data[col_sub] == codigo_submercado]
                            if not dp_filtrado.empty:
                                dp_record = dp_filtrado.iloc[0].to_dict()
                                break
            else:
                # Fallback para formato não-DataFrame
                dp_records = [dp_data] if not isinstance(dp_data, list) else dp_data
                for record in dp_records:
                    if isinstance(record, pd.Series):
                        record = record.to_dict()
                    
                    record_submercado = (
                        record.get('codigo_submercado') or 
                        record.get('submercado') or 
                        record.get('s')
                    )
                    record_estagio = record.get('estagio') or record.get('ip')
                    
                    if record_submercado == codigo_submercado:
                        if record_estagio is None or record_estagio == 1:
                            dp_record = record
                            break
                
                if dp_record is None:
                    # Tentar qualquer registro do submercado
                    for record in dp_records:
                        if isinstance(record, pd.Series):
                            record = record.to_dict()
                        record_submercado = (
                            record.get('codigo_submercado') or 
                            record.get('submercado') or 
                            record.get('s')
                        )
                        if record_submercado == codigo_submercado:
                            dp_record = record
                            break
            
            if dp_record is None:
                return {
                    "success": False,
                    "error": f"Dados do bloco DP não encontrados para submercado {codigo_submercado} no estágio 1"
                }
            
            if verbose:
                safe_print(f"[DISPONIBILIDADE TOOL] Dados DP obtidos: {dp_record}")
            
            # ETAPA 4: Extrair durações dos patamares
            duracoes = self._extract_duracoes(dp_record)
            
            if not duracoes or all(v is None for v in duracoes.values()):
                return {
                    "success": False,
                    "error": f"Não foi possível extrair durações dos patamares do bloco DP"
                }
            
            if verbose:
                safe_print(f"[DISPONIBILIDADE TOOL] Durações: {duracoes}")
            
            # ETAPA 5: Calcular disponibilidade total
            resultado = self._calcular_disponibilidade(inflexibilidades, duracoes)
            
            if resultado is None:
                return {
                    "success": False,
                    "error": "Erro ao calcular disponibilidade. Verifique se todos os dados necessários estão disponíveis."
                }
            
            # ETAPA 6: Preparar resposta estruturada
            return {
                "success": True,
                "disponibilidade_total": resultado["disponibilidade_total"],
                "usina": {
                    "codigo": codigo_usina,
                    "nome": nome_usina,
                    "submercado": codigo_submercado
                },
                "detalhes": {
                    "pesada": {
                        "inflexibilidade": inflexibilidades.get("pesada"),
                        "duracao": duracoes.get("pesada")
                    },
                    "media": {
                        "inflexibilidade": inflexibilidades.get("media"),
                        "duracao": duracoes.get("media")
                    },
                    "leve": {
                        "inflexibilidade": inflexibilidades.get("leve"),
                        "duracao": duracoes.get("leve")
                    }
                },
                "calculo": resultado["calculo"],
                "tool": self.get_name()
            }
            
        except Exception as e:
            safe_print(f"[DISPONIBILIDADE TOOL] ❌ Erro ao calcular disponibilidade: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": f"Erro ao calcular disponibilidade: {str(e)}",
                "tool": self.get_name()
            }
    
    def _extract_usina_from_query(self, query: str, dadger: Any) -> Optional[int]:
        """
        Extrai código da usina da query - VERSÃO OTIMIZADA para performance.
        Baseado em clast_valores_tool.py do NEWAVE, adaptado para usar CT do idecomp.
        
        Otimizações:
        - Regex compiladas para busca mais rápida
        - Dicionários para busca O(1) em matches exatos
        - Early return quando encontra match
        - Pré-processamento de dados para evitar recálculos
        - Menos logs desnecessários
        
        Args:
            query: Query do usuário
            dadger: Instância do Dadger
            
        Returns:
            Código da usina ou None
        """
        query_lower = query.lower()
        
        # ETAPA 1: Tentar extrair número explícito (OTIMIZADO)
        # Compilar regex uma vez (mais rápido que re.search repetido)
        patterns = [
            re.compile(r'usina\s*(\d+)'),
            re.compile(r'usina\s*térmica\s*(\d+)'),
            re.compile(r'usina\s*termica\s*(\d+)'),
            re.compile(r'usina\s*#?\s*(\d+)'),
            re.compile(r'código\s*(\d+)'),
            re.compile(r'codigo\s*(\d+)'),
            re.compile(r'térmica\s*(\d+)'),
            re.compile(r'termica\s*(\d+)'),
            re.compile(r'ute\s*(\d+)'),
        ]
        
        for pattern in patterns:
            match = pattern.search(query_lower)
            if match:
                try:
                    codigo = int(match.group(1))
                    # Verificar se existe no CT (OTIMIZADO: buscar todos os códigos de uma vez)
                    ct_df = dadger.ct(estagio=1, df=True)
                    if ct_df is not None and isinstance(ct_df, pd.DataFrame) and not ct_df.empty:
                        if 'codigo_usina' in ct_df.columns:
                            codigos_validos = set(ct_df['codigo_usina'].unique())
                            if codigo in codigos_validos:
                                safe_print(f"[DISPONIBILIDADE TOOL] ✅ Código {codigo} encontrado por padrão numérico")
                                return codigo
                except (ValueError, KeyError):
                    continue
        
        # ETAPA 2: Buscar por nome da usina (OTIMIZADO)
        try:
            # Obter DataFrame do CT uma única vez
            ct_df = dadger.ct(estagio=1, df=True)
            if ct_df is None or (isinstance(ct_df, pd.DataFrame) and ct_df.empty):
                return None
            
            if not isinstance(ct_df, pd.DataFrame):
                return None
            
            if 'codigo_usina' not in ct_df.columns or 'nome_usina' not in ct_df.columns:
                return None
            
            # Obter usinas únicas
            usinas_unicas = ct_df[['codigo_usina', 'nome_usina']].drop_duplicates()
            
            # Criar dicionário indexado por nome (lowercase) para busca O(1)
            nome_lower_to_codigo = {}
            
            # Pré-processar palavras significativas uma vez
            palavras_ignorar = {'de', 'da', 'do', 'das', 'dos', 'e', 'a', 'o', 'as', 'os', 'em', 'na', 'no', 'nas', 'nos'}
            palavras_query = [p for p in query_lower.split() if len(p) > 2 and p not in palavras_ignorar]
            palavras_query_set = set(palavras_query)
            
            # Preparar dados para busca rápida
            usinas_data = []
            for _, row in usinas_unicas.iterrows():
                codigo = int(row.get('codigo_usina'))
                nome = str(row.get('nome_usina', '')).strip()
                nome_lower = nome.lower().strip()
                
                if not nome_lower:
                    continue
                
                nome_lower_to_codigo[nome_lower] = codigo
                
                # Pré-processar palavras do nome
                palavras_nome = [p for p in nome_lower.split() if len(p) > 2 and p not in palavras_ignorar]
                palavras_nome_set = set(palavras_nome)
                
                usinas_data.append({
                    'codigo': codigo,
                    'nome': nome,
                    'nome_lower': nome_lower,
                    'palavras_nome': palavras_nome,
                    'palavras_nome_set': palavras_nome_set
                })
            
            # PRIORIDADE 1: Match exato do nome completo (busca O(1))
            if query_lower.strip() in nome_lower_to_codigo:
                codigo = nome_lower_to_codigo[query_lower.strip()]
                safe_print(f"[DISPONIBILIDADE TOOL] ✅ Código {codigo} encontrado por match exato")
                return codigo
            
            # PRIORIDADE 2: Match exato do nome completo dentro da query (early return)
            for nome_lower, codigo in nome_lower_to_codigo.items():
                if len(nome_lower) >= 4 and nome_lower in query_lower:
                    # Verificar word boundaries apenas se necessário
                    pattern = r'\b' + re.escape(nome_lower) + r'\b'
                    if re.search(pattern, query_lower):
                        safe_print(f"[DISPONIBILIDADE TOOL] ✅ Código {codigo} encontrado por nome completo na query")
                        return codigo
            
            # PRIORIDADE 3: Match de todas as palavras significativas (early return)
            for usina in usinas_data:
                if usina['palavras_nome'] and all(palavra in query_lower for palavra in usina['palavras_nome']):
                    safe_print(f"[DISPONIBILIDADE TOOL] ✅ Código {usina['codigo']} encontrado: todas palavras significativas")
                    return usina['codigo']
            
            # PRIORIDADE 4: Similaridade de string (apenas se não encontrou match exato)
            candidatos = []
            for usina in usinas_data:
                similarity = SequenceMatcher(None, query_lower, usina['nome_lower']).ratio()
                if similarity > 0.6:
                    candidatos.append((usina['codigo'], usina['nome'], similarity, 'similarity'))
            
            # PRIORIDADE 5: Contagem de palavras significativas em comum
            for usina in usinas_data:
                palavras_comuns = palavras_query_set & usina['palavras_nome_set']
                if palavras_comuns:
                    palavras_longas = [p for p in palavras_comuns if len(p) >= 5]
                    if len(palavras_comuns) >= 2 or (len(palavras_longas) >= 1 and len(palavras_comuns) >= 1):
                        score = len(palavras_comuns) / max(len(usina['palavras_nome']), 1)
                        candidatos.append((usina['codigo'], usina['nome'], score, 'palavras_comuns'))
            
            # Se encontrou candidatos, retornar o melhor
            if candidatos:
                candidatos.sort(key=lambda x: (x[3] == 'similarity', x[2]), reverse=True)
                melhor = candidatos[0]
                safe_print(f"[DISPONIBILIDADE TOOL] ✅ Código {melhor[0]} encontrado por {melhor[3]} (score: {melhor[2]:.2f})")
                return melhor[0]
        
        except Exception as e:
            safe_print(f"[DISPONIBILIDADE TOOL] ⚠️ Erro ao buscar usina por nome: {e}")
        
        return None
    
    def _extract_inflexibilidades(self, ct_record: Dict[str, Any]) -> Dict[str, Optional[float]]:
        """
        ⚡ OTIMIZADO: Extrai inflexibilidades dos 3 patamares do registro CT.
        Removidos logs excessivos dentro de loops.
        
        Args:
            ct_record: Registro do bloco CT
            
        Returns:
            Dict com inflexibilidades por patamar (pesada, media, leve)
        """
        inflexibilidades = {
            "pesada": None,
            "media": None,
            "leve": None
        }
        
        # ⚡ OTIMIZAÇÃO: Criar set de chaves uma vez
        ct_keys = set(ct_record.keys())
        
        # Tentar múltiplas variações de nomes de campos
        for patamar_idx, patamar_nome in [(1, "pesada"), (2, "media"), (3, "leve")]:
            valor = None
            
            # ⚡ OTIMIZAÇÃO: Tentar variações mais comuns primeiro
            common_keys = [
                f"inflexibilidade_patamar_{patamar_idx}",
                f"inflexibilidade_{patamar_idx}",
                f"inflexibilidade_pat{patamar_idx}",
            ]
            
            for key in common_keys:
                if key in ct_keys and ct_record[key] is not None:
                    valor = ct_record[key]
                    break
            
            # Fallback: buscar por padrão (sem logs)
            if valor is None:
                for key, value in ct_record.items():
                    if value is not None and isinstance(value, (int, float)):
                        key_lower = str(key).lower()
                        if (f"pat{patamar_idx}" in key_lower or f"patamar{patamar_idx}" in key_lower or 
                            f"_{patamar_idx}" in key_lower) and ("inflexibilidade" in key_lower):
                            valor = value
                            break
            
            if valor is not None:
                try:
                    inflexibilidades[patamar_nome] = float(valor)
                except (ValueError, TypeError):
                    pass  # Silencioso - erro será capturado depois
        
        return inflexibilidades
    
    def _extract_duracoes(self, dp_record: Dict[str, Any]) -> Dict[str, Optional[float]]:
        """
        ⚡ OTIMIZADO: Extrai durações dos 3 patamares do registro DP.
        Removidos logs excessivos dentro de loops.
        
        Args:
            dp_record: Registro do bloco DP
            
        Returns:
            Dict com durações por patamar (pesada, media, leve) em horas
        """
        duracoes = {
            "pesada": None,
            "media": None,
            "leve": None
        }
        
        # ⚡ OTIMIZAÇÃO: Criar set de chaves uma vez
        dp_keys = set(dp_record.keys())
        
        # Tentar múltiplas variações de nomes de campos
        for patamar_idx, patamar_nome in [(1, "pesada"), (2, "media"), (3, "leve")]:
            valor = None
            
            # ⚡ OTIMIZAÇÃO: Tentar variações mais comuns primeiro
            common_keys = [
                f"duracao_patamar_{patamar_idx}",
                f"duracao_{patamar_idx}",
                f"horas_patamar_{patamar_idx}",
                f"horas_{patamar_idx}",
            ]
            
            for key in common_keys:
                if key in dp_keys and dp_record[key] is not None:
                    valor = dp_record[key]
                    break
            
            # Fallback: buscar por padrão (sem logs)
            if valor is None:
                for key, value in dp_record.items():
                    if value is not None and isinstance(value, (int, float)):
                        key_lower = str(key).lower()
                        if (f"pat{patamar_idx}" in key_lower or f"patamar{patamar_idx}" in key_lower or 
                            f"_{patamar_idx}" in key_lower) and ("hora" in key_lower or "duracao" in key_lower):
                            valor = value
                            break
            
            if valor is not None:
                try:
                    duracoes[patamar_nome] = float(valor)
                except (ValueError, TypeError):
                    pass  # Silencioso - erro será capturado depois
        
        return duracoes
    
    def _calcular_disponibilidade(
        self, 
        inflexibilidades: Dict[str, Optional[float]], 
        duracoes: Dict[str, Optional[float]]
    ) -> Optional[Dict[str, Any]]:
        """
        Calcula disponibilidade total usando a fórmula especificada.
        
        Args:
            inflexibilidades: Dict com inflexibilidades por patamar (pesada, media, leve)
            duracoes: Dict com durações por patamar em horas (pesada, media, leve)
            
        Returns:
            Dict com resultado do cálculo ou None se houver erro
        """
        # Validar que temos todos os dados necessários (verificar None, não valores falsy como 0.0)
        # 0.0 é um valor válido! Significa que a usina não tem inflexibilidade naquele patamar
        if any(v is None for v in inflexibilidades.values()) or any(v is None for v in duracoes.values()):
            safe_print(f"[DISPONIBILIDADE TOOL] [ERRO] Dados incompletos: inflexibilidades={inflexibilidades}, duracoes={duracoes}")
            return None
        
        # Extrair valores (0.0 é válido e deve ser considerado!)
        inf_pesada = inflexibilidades.get("pesada", 0) or 0
        inf_media = inflexibilidades.get("media", 0) or 0
        inf_leve = inflexibilidades.get("leve", 0) or 0
        
        dur_pesada = duracoes.get("pesada", 0) or 0
        dur_media = duracoes.get("media", 0) or 0
        dur_leve = duracoes.get("leve", 0) or 0
        
        # Calcular numerador: (Inf_Leve × Dur_Leve + Inf_Médio × Dur_Médio + Inf_Pesada × Dur_Pesada)
        numerador = (inf_leve * dur_leve) + (inf_media * dur_media) + (inf_pesada * dur_pesada)
        
        # Calcular denominador: (Dur_Leve + Dur_Médio + Dur_Pesada)
        denominador = dur_leve + dur_media + dur_pesada
        
        if denominador == 0:
            safe_print(f"[DISPONIBILIDADE TOOL] [ERRO] Denominador zero (soma das durações = 0)")
            return None
        
        # Calcular disponibilidade total
        disponibilidade_total = numerador / denominador
        
        return {
            "disponibilidade_total": round(disponibilidade_total, 2),
            "calculo": {
                "numerador": round(numerador, 2),
                "denominador": round(denominador, 2),
                "resultado": round(disponibilidade_total, 2)
            }
        }
