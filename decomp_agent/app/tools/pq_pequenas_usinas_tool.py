"""
Tool para consultar informações do Bloco PQ (Gerações das Pequenas Usinas) do DECOMP.
Específica para Single Deck: apenas estágio 1, com cálculo ponderado por horas.
"""
from decomp_agent.app.tools.base import DECOMPTool
from decomp_agent.app.config import safe_print
from idecomp.decomp import Dadger
import os
import pandas as pd
import re
from typing import Dict, Any, Optional, List

# Mapeamento de códigos de submercado para regiões
SUBMERCADO_TO_REGIAO = {
    1: "SUDESTE/CENTRO-OESTE",
    2: "SUL",
    3: "NORDESTE",
    4: "NORTE"
}

# Mapeamento de região para prefixos possíveis no nome do registro
# Os nomes seguem padrão: {PREFIXO}_{TIPO} ou {PREFIXO}_{TIPO}gd
REGIAO_TO_PREFIXOS = {
    "SUDESTE/CENTRO-OESTE": ["SECO"],
    "SUL": ["SUL"],
    "NORDESTE": ["NE", "NORDESTE"],
    "NORTE": ["NORTE", "N"]
}

# Tipos de geração suportados
TIPOS_GERACAO = ["PCH", "PCT", "EOL", "UFV", "PCHgd", "PCTgd", "EOLgd", "UFVgd"]


class PQPequenasUsinasTool(DECOMPTool):
    """
    Tool para consultar informações do Bloco PQ (Gerações das Pequenas Usinas) do DECOMP.
    
    Específica para Single Deck:
    - Apenas estágio 1
    - Cálculo ponderado pelas horas por patamar
    - Segmentação por região (Sudeste/Centro-Oeste, Sul, Nordeste, Norte)
    - Segmentação por tipo (PCH, PCT, EOL, UFV, PCHgd, PCTgd, EOLgd, UFVgd)
    - Output: tabela por patamares e horas + MW médio
    """
    
    def get_name(self) -> str:
        return "PQPequenasUsinasTool"
    
    def can_handle(self, query: str) -> bool:
        """
        Verifica se a query é sobre gerações de pequenas usinas (Bloco PQ).
        
        Args:
            query: Query do usuário
            
        Returns:
            True se a tool pode processar a query
        """
        query_lower = query.lower()
        
        keywords = [
            "pequenas usinas",
            "geração pequenas usinas",
            "geracoes pequenas usinas",
            "bloco pq",
            "registro pq",
            "pq decomp",
            "pch", "pct", "eol", "ufv",
            "pchgd", "pctgd", "eolgd", "ufvgd",
            "pequenas centrais hidrelétricas",
            "pequenas centrais termelétricas",
            "eólica", "fotovoltaica",
            "geração eólica",
            "geração fotovoltaica",
            "pequenas centrais",
        ]
        
        return any(kw in query_lower for kw in keywords)
    
    def get_description(self) -> str:
        return """
        Tool para consultar informações do Bloco PQ (Gerações das Pequenas Usinas) do DECOMP.
        
        Específica para Single Deck:
        - Apenas estágio 1
        - Cálculo ponderado pelas horas por patamar
        - Segmentação por região (Sudeste/Centro-Oeste, Sul, Nordeste, Norte)
        - Segmentação por tipo (PCH, PCT, EOL, UFV, PCHgd, PCTgd, EOLgd, UFVgd)
        - Output: tabela por patamares e horas + MW médio
        
        Exemplos de queries:
        - "Gerações de pequenas usinas"
        - "Geração PCH do Sudeste"
        - "Pequenas usinas eólicas"
        - "Geração fotovoltaica do Nordeste"
        - "MW médio das pequenas usinas"
        """
    
    def execute(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Executa a consulta sobre gerações das pequenas usinas do Bloco PQ.
        
        Args:
            query: Query do usuário
            **kwargs: Argumentos adicionais opcionais
            
        Returns:
            Dict com dados das gerações formatados
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
            
            # SEMPRE usar estágio 1 para Single Deck
            estagio = 1
            
            # Extrair filtros da query
            tipo_filtro = self._extract_tipo_from_query(query)
            codigo_submercado = self._extract_codigo_submercado_from_query(query)
            
            # Logs essenciais apenas
            if tipo_filtro or codigo_submercado:
                safe_print(f"[PQ TOOL] Filtros: tipo={tipo_filtro}, submercado={codigo_submercado}")
            
            # Obter dados do bloco PQ (estágio 1)
            pq_data = dadger.pq(
                estagio=estagio,
                codigo_submercado=codigo_submercado,
                df=True  # Retornar como DataFrame
            )
            
            if pq_data is None or (isinstance(pq_data, pd.DataFrame) and pq_data.empty):
                return {
                    "success": False,
                    "error": "Nenhum registro de geração de pequenas usinas encontrado no estágio 1"
                }
            
            # Filtrar apenas estágio 1 (garantia)
            if isinstance(pq_data, pd.DataFrame):
                if "estagio" in pq_data.columns:
                    pq_data = pq_data[pq_data["estagio"] == estagio].copy()
                
                safe_print(f"[PQ TOOL] Total de registros PQ: {len(pq_data)}")
                
                # IMPORTANTE: Filtrar por submercado PRIMEIRO (se especificado)
                # Isso garante que o fallback de tipo seja feito dentro do submercado correto
                if codigo_submercado is not None:
                    col_submercado = None
                    for col in ["codigo_submercado", "submercado", "s"]:
                        if col in pq_data.columns:
                            col_submercado = col
                            break
                    
                    if col_submercado:
                        pq_data = pq_data[pq_data[col_submercado] == codigo_submercado].copy()
                        safe_print(f"[PQ TOOL] {len(pq_data)} registros após filtro submercado")
                        # DEBUG: Mostrar nomes reais dos registros para entender o padrão
                        if len(pq_data) > 0 and "nome" in pq_data.columns:
                            nomes_reais = pq_data["nome"].unique().tolist()
                            safe_print(f"[PQ TOOL] DEBUG: Nomes reais encontrados no submercado {codigo_submercado}: {nomes_reais}")
                
                # Filtrar por tipo se especificado (DEPOIS do filtro de submercado)
                tipo_encontrado_real = None  # Guardar tipo REAL encontrado nos dados
                
                if tipo_filtro:
                    tipo_filtro_upper = tipo_filtro.upper() if tipo_filtro else None
                    tem_gd_na_query = tipo_filtro_upper and tipo_filtro_upper.endswith("GD")
                    
                    if "nome" in pq_data.columns:
                        # LÓGICA CORRIGIDA:
                        # Se há submercado especificado: buscar padrão {PREFIXO}_{TIPO}
                        # Ex: "EOL no nordeste" → buscar "NE_EOL" ou "NORDESTE_EOL" (NÃO "NE_EOLgd")
                        # Ex: "EOLgd no nordeste" → buscar "NE_EOLgd" ou "NORDESTE_EOLgd"
                        
                        if codigo_submercado is not None:
                            # Obter prefixos possíveis da região
                            prefixos = self._obter_prefixos_regiao(codigo_submercado)
                            
                            if prefixos:
                                # IMPORTANTE: Salvar cópia dos dados antes do filtro para usar no fallback
                                pq_data_original = pq_data.copy()
                                
                                # Construir padrões de busca EXATOS: {PREFIXO}_{TIPO} ou {PREFIXO}_{TIPO}gd
                                # IMPORTANTE: Se query NÃO tem GD, buscar EXATAMENTE sem GD (não pode ter "gd" depois)
                                padroes_busca = []
                                for prefixo in prefixos:
                                    if tem_gd_na_query:
                                        # Se query tem GD, buscar com GD: "NE_EOLGD"
                                        padroes_busca.append(f"{prefixo}_{tipo_filtro_upper}")
                                    else:
                                        # Se query NÃO tem GD, buscar SEM GD: "NE_EOL" (exato, sem "gd" depois)
                                        padroes_busca.append(f"{prefixo}_{tipo_filtro_upper}")
                                
                                # Filtrar por nomes que correspondem EXATAMENTE aos padrões
                                # IMPORTANTE: Se não tem GD na query, garantir que não há "GD" após o tipo
                                mask = pd.Series([False] * len(pq_data), index=pq_data.index)
                                nomes_upper = pq_data["nome"].str.upper()
                                
                                for padrao in padroes_busca:
                                    if tem_gd_na_query:
                                        # Com GD: match que começa com padrão (ex: "NE_EOLGD")
                                        mask |= nomes_upper.str.startswith(padrao)
                                    else:
                                        # SEM GD: match exato OU padrão seguido de algo que NÃO seja "GD"
                                        # Ex: "NE_EOL" ✅, "NE_EOL_123" ✅, mas "NE_EOLGD" ❌
                                        def match_sem_gd(nome_upper_str):
                                            if not nome_upper_str:
                                                return False
                                            if nome_upper_str == padrao:
                                                return True  # Match exato
                                            if nome_upper_str.startswith(padrao):
                                                # Verificar se o próximo caractere (se existir) não é "G"
                                                if len(nome_upper_str) > len(padrao):
                                                    next_char = nome_upper_str[len(padrao)]
                                                    return next_char != "G"  # Não pode começar com "GD"
                                                return True  # Está no fim, ok
                                            return False
                                        
                                        mask |= pq_data["nome"].str.upper().apply(match_sem_gd)
                                
                                pq_data = pq_data[mask].copy()
                                
                                if len(pq_data) > 0:
                                    # Extrair tipo REAL do primeiro registro encontrado
                                    primeiro_nome = pq_data.iloc[0]["nome"]
                                    tipo_encontrado_real = self._extrair_tipo_geracao(primeiro_nome)
                                    safe_print(f"[PQ TOOL] {len(pq_data)} registros encontrados com padrão {padroes_busca} (tipo real: {tipo_encontrado_real})")
                                else:
                                    safe_print(f"[PQ TOOL] ⚠️ Nenhum registro encontrado com padrões: {padroes_busca}")
                                    # FALLBACK: Se não encontrou tipo puro e query não pediu GD, tentar versão GD
                                    if not tem_gd_na_query:
                                        safe_print(f"[PQ TOOL] Tentando fallback para versão GD...")
                                        padroes_busca_gd = [f"{prefixo}_{tipo_filtro_upper}GD" for prefixo in prefixos]
                                        mask_gd = pd.Series([False] * len(pq_data_original), index=pq_data_original.index)
                                        nomes_upper_original = pq_data_original["nome"].str.upper()
                                        for padrao_gd in padroes_busca_gd:
                                            mask_gd |= nomes_upper_original.str.startswith(padrao_gd)
                                        
                                        pq_data = pq_data_original[mask_gd].copy()
                                        
                                        if len(pq_data) > 0:
                                            primeiro_nome = pq_data.iloc[0]["nome"]
                                            tipo_encontrado_real = self._extrair_tipo_geracao(primeiro_nome)
                                            safe_print(f"[PQ TOOL] ✅ Fallback: {len(pq_data)} registros encontrados com padrão GD {padroes_busca_gd} (tipo real: {tipo_encontrado_real})")
                                        else:
                                            safe_print(f"[PQ TOOL] ⚠️ Fallback também não encontrou registros com padrões: {padroes_busca_gd}")
                            else:
                                safe_print(f"[PQ TOOL] ⚠️ Nenhum prefixo encontrado para submercado {codigo_submercado}")
                        else:
                            # Sem submercado: usar lógica antiga (filtrar por tipo extraído)
                            pq_data_temp = pq_data.copy()
                            pq_data_temp["_tipo_extraido"] = pq_data_temp["nome"].apply(
                                lambda x: self._extrair_tipo_geracao(str(x) if x else "")
                            )
                            
                            # Filtrar por tipo EXATO (sem fallback para GD se não pediu GD)
                            pq_data = pq_data_temp[
                                pq_data_temp["_tipo_extraido"].str.upper() == tipo_filtro_upper
                            ].copy()
                            
                            if len(pq_data) > 0:
                                tipo_encontrado_real = tipo_filtro_upper
                            
                            pq_data = pq_data.drop(columns=["_tipo_extraido"], errors="ignore")
                            if len(pq_data) == 0:
                                tipos_disponiveis = pq_data_temp["_tipo_extraido"].unique().tolist()
                                safe_print(f"[PQ TOOL] ⚠️ Tipo '{tipo_filtro}' não encontrado. Tipos disponíveis: {tipos_disponiveis}")
                            else:
                                safe_print(f"[PQ TOOL] {len(pq_data)} registros após filtro tipo '{tipo_filtro_upper}'")
                    else:
                        safe_print(f"[PQ TOOL] ⚠️ Aviso: coluna 'nome' não encontrada para filtrar por tipo")
            
            # Obter durações dos patamares do bloco DP (estágio 1)
            # FALLBACK: Se não encontrar para o submercado específico, tentar sem filtro de submercado
            dp_data = dadger.dp(
                estagio=estagio,
                codigo_submercado=codigo_submercado,
                df=True
            )
            
            # Se não encontrou com submercado específico, tentar sem filtro de submercado
            if (dp_data is None or (isinstance(dp_data, pd.DataFrame) and dp_data.empty)) and codigo_submercado is not None:
                safe_print(f"[PQ TOOL] ⚠️ Durações não encontradas para submercado {codigo_submercado}, tentando sem filtro de submercado...")
                dp_data = dadger.dp(
                    estagio=estagio,
                    codigo_submercado=None,  # Tentar sem filtro
                    df=True
                )
            
            if dp_data is None or (isinstance(dp_data, pd.DataFrame) and dp_data.empty):
                return {
                    "success": False,
                    "error": "Nenhum registro de duração de patamares encontrado no estágio 1"
                }
            
            # Filtrar apenas estágio 1
            if isinstance(dp_data, pd.DataFrame):
                if "estagio" in dp_data.columns:
                    dp_data = dp_data[dp_data["estagio"] == estagio].copy()
            
            # Extrair durações por patamar
            duracoes = self._extrair_duracoes_patamares(dp_data)
            
            if not duracoes or any(v is None for v in duracoes.values()):
                return {
                    "success": False,
                    "error": "Não foi possível extrair durações dos patamares do bloco DP"
                }
            
            # Log apenas se houver problema
            if any(v is None for v in duracoes.values()):
                safe_print(f"[PQ TOOL] ⚠️ Durações incompletas: {duracoes}")
            
            # Processar dados: extrair valores por patamar e calcular MW médio
            data = []
            registros = pq_data.to_dict('records') if isinstance(pq_data, pd.DataFrame) else []
            
            for registro in registros:
                nome = registro.get("nome") or registro.get("name") or ""
                tipo = self._extrair_tipo_geracao(nome)
                codigo_submercado_reg = (
                    registro.get("codigo_submercado") or
                    registro.get("submercado") or
                    registro.get("s")
                )
                regiao = self._mapear_submercado_para_regiao(codigo_submercado_reg)
                
                # Extrair valores de geração por patamar
                valores_geracao = self._extrair_valores_geracao(registro)
                
                # Calcular MW médio ponderado
                mw_medio = self._calcular_mw_medio_ponderado(valores_geracao, duracoes)
                
                # Estruturar dados do patamar
                patamares = {
                    "pesada": {
                        "geracao_mw": valores_geracao.get("pesada"),
                        "duracao_horas": duracoes.get("pesada")
                    },
                    "media": {
                        "geracao_mw": valores_geracao.get("media"),
                        "duracao_horas": duracoes.get("media")
                    },
                    "leve": {
                        "geracao_mw": valores_geracao.get("leve"),
                        "duracao_horas": duracoes.get("leve")
                    }
                }
                
                data.append({
                    "nome": nome,
                    "tipo": tipo,
                    "regiao": regiao,
                    "codigo_submercado": codigo_submercado_reg,
                    "estagio": estagio,
                    "patamares": patamares,
                    "mw_medio": mw_medio
                })
            
            if not data:
                # Obter nome da região para mensagem
                regiao_nome = self._mapear_submercado_para_regiao(codigo_submercado) if codigo_submercado else "TODAS"
                
                # IMPORTANTE: Para comparação multi-deck, retornar sucesso com dados vazios (será tratado como 0)
                # Isso permite que comparações temporais continuem funcionando mesmo quando um deck não tem o tipo
                tipo_info = f"tipo '{tipo_filtro}'" if tipo_filtro else "tipo não especificado"
                safe_print(f"[PQ TOOL] ⚠️ Nenhum registro encontrado para {tipo_info} na região '{regiao_nome}' - retornando dados vazios (será tratado como 0 em comparações)")
                
                # Retornar sucesso com dados vazios - o formatter/multi-deck tratará como 0
                return {
                    "success": True,
                    "data": [],
                    "total_registros": 0,
                    "filtros": {
                        "tipo": tipo_filtro,
                        "tipo_encontrado": tipo_encontrado_real,
                        "codigo_submercado": codigo_submercado,
                        "regiao": regiao_nome,
                        "estagio": estagio,
                    },
                    "tipo_encontrado": tipo_encontrado_real,
                    "calcular_media_ponderada": True,
                    "tool": self.get_name(),
                    "sem_dados": True,  # Flag para indicar que não há dados (será 0 em comparações)
                    "mensagem": f"Nenhum registro encontrado para {tipo_info} na região '{regiao_nome}' (será tratado como 0 em comparações)"
                }
            
            # Obter nome da região para mensagem
            regiao_nome = self._mapear_submercado_para_regiao(codigo_submercado) if codigo_submercado else "TODAS"
            tipo_info = f"tipo '{tipo_encontrado_real or tipo_filtro}'" if (tipo_encontrado_real or tipo_filtro) else "todos os tipos"
            
            safe_print(f"[PQ TOOL] ✅ {len(data)} registros processados para {tipo_info} na região '{regiao_nome}'")
            
            # Se tipo_encontrado_real não foi definido, usar tipo do primeiro registro
            if tipo_encontrado_real is None and data:
                primeiro_nome = data[0].get("nome", "")
                tipo_encontrado_real = self._extrair_tipo_geracao(primeiro_nome)
            
            # Preparar filtros
            filtros_dict = {
                "tipo": tipo_filtro,  # Tipo da query
                "tipo_encontrado": tipo_encontrado_real,  # Tipo REAL encontrado nos dados
                "codigo_submercado": codigo_submercado,
                "regiao": regiao_nome,
                "estagio": estagio,
            }
            
            return {
                "success": True,
                "data": data,
                "total_registros": len(data),
                "filtros": filtros_dict,
                "tipo_encontrado": tipo_encontrado_real,  # IMPORTANTE: Tipo REAL para o frontend
                "calcular_media_ponderada": True,  # Sempre calcular MW médio
                "tool": self.get_name()
            }
            
        except Exception as e:
            safe_print(f"[PQ TOOL] ❌ Erro ao consultar Bloco PQ: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": f"Erro ao consultar Bloco PQ: {str(e)}",
                "tool": self.get_name()
            }
    
    def _extrair_duracoes_patamares(self, dp_data: pd.DataFrame) -> Dict[str, Optional[float]]:
        """
        Extrai durações dos patamares do DataFrame DP.
        
        Args:
            dp_data: DataFrame com dados do bloco DP
            
        Returns:
            Dict com durações por patamar: {"pesada": X, "media": Y, "leve": Z}
        """
        duracoes = {"pesada": None, "media": None, "leve": None}
        
        if dp_data is None or dp_data.empty:
            return duracoes
        
        # Tentar extrair durações do primeiro registro (assumindo que são iguais para todos no estágio 1)
        primeiro_registro = dp_data.iloc[0].to_dict()
        
        # Mapeamento de patamares: 1=PESADA, 2=MEDIA, 3=LEVE
        patamar_map = {
            "pesada": 1,
            "media": 2,
            "leve": 3
        }
        
        for patamar_nome, patamar_num in patamar_map.items():
            # Tentar múltiplas variações de nomes de colunas
            colunas_possiveis = [
                f"duracao_patamar_{patamar_num}",
                f"duracao_{patamar_num}",
                f"horas_{patamar_num}",
                f"horas_patamar_{patamar_num}",
                f"duracao_pat{patamar_num}",
                f"horas_pat{patamar_num}",
                f"duracao_patamar_{patamar_nome}",
                f"horas_{patamar_nome}",
            ]
            
            for col in colunas_possiveis:
                if col in primeiro_registro:
                    valor = primeiro_registro[col]
                    if valor is not None:
                        try:
                            duracoes[patamar_nome] = float(valor)
                            break
                        except (ValueError, TypeError):
                            continue
        
        return duracoes
    
    def _extrair_tipo_geracao(self, nome: str) -> str:
        """
        Extrai tipo de geração do nome usando regex.
        IMPORTANTE: Retorna tipo exato do nome (EOL ou EOLgd, não ambos).
        
        Args:
            nome: Nome da geração (ex: "SECO_PCH", "SUL_EOLgd")
            
        Returns:
            Tipo extraído (PCH, PCT, EOL, UFV, PCHgd, etc.) ou "OUTROS" se não encontrar
        """
        if not nome:
            return "OUTROS"
        
        # Normalizar para uppercase para garantir consistência
        nome_upper = str(nome).upper().strip()
        
        # Primeiro tentar encontrar padrão com "GD" (mais específico)
        # Padrão: (tipo)GD - ex: EOLGD, PCHGD
        # Pode estar em qualquer posição do nome (NORD_EOLGD, SECO_PCHGD, etc.)
        pattern_com_gd = r'(PCH|PCT|EOL|UFV)GD'
        match_gd = re.search(pattern_com_gd, nome_upper)
        if match_gd:
            tipo_base = match_gd.group(1)
            return f"{tipo_base}GD"
        
        # Se não encontrou com "GD", buscar sem "GD"
        # Padrão simples: encontrar PCH, PCT, EOL, UFV em qualquer lugar do nome
        # Verificar que NÃO é seguido por "GD" (para não confundir EOLGD com EOL)
        pattern_sem_gd = r'(PCH|PCT|EOL|UFV)(?!GD)'
        match_sem_gd = re.search(pattern_sem_gd, nome_upper)
        if match_sem_gd:
            tipo_base = match_sem_gd.group(1)
            return tipo_base
        
        return "OUTROS"
    
    def _mapear_submercado_para_regiao(self, codigo_submercado: Optional[int]) -> str:
        """
        Mapeia código de submercado para região.
        
        Args:
            codigo_submercado: Código do submercado (1-4)
            
        Returns:
            Nome da região ou "DESCONHECIDO" se código inválido
        """
        if codigo_submercado is None:
            return "DESCONHECIDO"
        
        return SUBMERCADO_TO_REGIAO.get(codigo_submercado, "DESCONHECIDO")
    
    def _obter_prefixos_regiao(self, codigo_submercado: Optional[int]) -> List[str]:
        """
        Obtém lista de prefixos possíveis para uma região baseado no código do submercado.
        Os nomes dos registros seguem padrão: {PREFIXO}_{TIPO} ou {PREFIXO}_{TIPO}gd
        
        Args:
            codigo_submercado: Código do submercado (1-4)
            
        Returns:
            Lista de prefixos possíveis (ex: ["NE", "NORDESTE"] para Nordeste)
        """
        if codigo_submercado is None:
            return []
        
        regiao = self._mapear_submercado_para_regiao(codigo_submercado)
        return REGIAO_TO_PREFIXOS.get(regiao, [])
    
    def _calcular_mw_medio_ponderado(
        self,
        valores: Dict[str, Optional[float]],
        duracoes: Dict[str, Optional[float]]
    ) -> Optional[float]:
        """
        Calcula MW médio ponderado usando a fórmula de patamares.
        
        Args:
            valores: Dict com valores de geração por patamar {"pesada": X, "media": Y, "leve": Z}
            duracoes: Dict com durações por patamar em horas {"pesada": X, "media": Y, "leve": Z}
            
        Returns:
            MW médio ponderado ou None se houver erro
        """
        # Validar dados
        if any(v is None for v in valores.values()) or any(v is None for v in duracoes.values()):
            return None
        
        # Extrair valores (0.0 é válido!)
        val_pesada = valores.get("pesada", 0) or 0
        val_media = valores.get("media", 0) or 0
        val_leve = valores.get("leve", 0) or 0
        
        dur_pesada = duracoes.get("pesada", 0) or 0
        dur_media = duracoes.get("media", 0) or 0
        dur_leve = duracoes.get("leve", 0) or 0
        
        # Calcular numerador: (Val_Leve × Dur_Leve + Val_Médio × Dur_Médio + Val_Pesada × Dur_Pesada)
        numerador = (val_leve * dur_leve) + (val_media * dur_media) + (val_pesada * dur_pesada)
        
        # Calcular denominador: (Dur_Leve + Dur_Médio + Dur_Pesada)
        denominador = dur_leve + dur_media + dur_pesada
        
        if denominador == 0:
            return None
        
        # Calcular MW médio
        mw_medio = numerador / denominador
        
        return round(mw_medio, 2)
    
    def _extrair_valores_geracao(self, registro: Dict[str, Any]) -> Dict[str, Optional[float]]:
        """
        Extrai valores de geração por patamar do registro.
        
        Args:
            registro: Dict com dados do registro PQ
            
        Returns:
            Dict com valores por patamar: {"pesada": X, "media": Y, "leve": Z}
        """
        valores = {"pesada": None, "media": None, "leve": None}
        
        # Mapeamento de patamares: 1=PESADA, 2=MEDIA, 3=LEVE
        patamar_map = {
            "pesada": 1,
            "media": 2,
            "leve": 3
        }
        
        for patamar_nome, patamar_num in patamar_map.items():
            # Tentar múltiplas variações de nomes de colunas
            # O idecomp pode retornar colunas como: geracao_1, geracao_2, geracao_3
            # ou geracao_patamar_1, etc. Também pode ser apenas números como chaves
            colunas_possiveis = [
                f"geracao_patamar_{patamar_num}",
                f"geracao_{patamar_num}",
                f"valor_patamar_{patamar_num}",
                f"valor_{patamar_num}",
                f"patamar_{patamar_num}",
                f"geracao_pat{patamar_num}",
                f"valor_pat{patamar_num}",
                # Também tentar variações com nome do patamar
                f"geracao_{patamar_nome}",
                f"valor_{patamar_nome}",
                # Tentar chaves numéricas diretas (caso seja lista expandida)
                str(patamar_num),
                f"pat{patamar_num}",
            ]
            
            for col in colunas_possiveis:
                if col in registro:
                    valor = registro[col]
                    if valor is not None:
                        try:
                            valores[patamar_nome] = float(valor)
                            break
                        except (ValueError, TypeError):
                            continue
            
            # Se ainda não encontrou, tentar buscar em listas/arrays expandidos
            # O idecomp pode expandir listas em colunas separadas como geracao_1, geracao_2, geracao_3
            if valores[patamar_nome] is None:
                # Tentar acessar diretamente por índice se for uma lista
                for key, value in registro.items():
                    if isinstance(value, (int, float)) and value is not None:
                        # Verificar se a chave sugere que é geração do patamar
                        key_lower = str(key).lower()
                        if (f"pat{patamar_num}" in key_lower or 
                            f"patamar{patamar_num}" in key_lower or 
                            f"_{patamar_num}" in key_lower) and \
                           ("geracao" in key_lower or "valor" in key_lower or 
                            key_lower == str(patamar_num)):
                            if "hora" not in key_lower and "duracao" not in key_lower:
                                try:
                                    valores[patamar_nome] = float(value)
                                    break
                                except (ValueError, TypeError):
                                    continue
        
        return valores
    
    
    def _extract_tipo_from_query(self, query: str) -> Optional[str]:
        """
        Extrai tipo de geração da query (PCH, PCT, EOL, UFV, etc.).
        
        LÓGICA SIMPLES:
        - Se "gd" aparecer em QUALQUER lugar da query → retorna tipo+GD (ex: EOLGD)
        - Se "gd" NÃO aparecer → retorna apenas tipo base (ex: EOL)
        
        Args:
            query: Query do usuário
            
        Returns:
            Tipo extraído em UPPERCASE (EOL, EOLGD, PCH, PCHGD, etc.) ou None
        """
        query_lower = query.lower()
        
        # Verificar se "gd" aparece em qualquer lugar da query
        tem_gd = "gd" in query_lower
        
        # Mapeamento de termos para tipos base
        termos_tipo = {
            "pch": "PCH",
            "pct": "PCT",
            "eol": "EOL",
            "eólica": "EOL",
            "eolica": "EOL",
            "vento": "EOL",
            "ufv": "UFV",
            "fotovoltaica": "UFV",
            "fotovoltaico": "UFV",
            "solar": "UFV",
        }
        
        # Buscar tipo base na query
        tipo_base = None
        for termo, tipo in termos_tipo.items():
            if termo in query_lower:
                tipo_base = tipo
                break
        
        # Fallback: buscar por padrões regex
        if not tipo_base:
            pattern = r'\b(PCH|PCT|EOL|UFV)\b'
            match = re.search(pattern, query.upper())
            if match:
                tipo_base = match.group(1)
        
        if not tipo_base:
            return None
        
        # Se "gd" aparece na query, adicionar GD ao tipo
        if tem_gd:
            return f"{tipo_base}GD"
        else:
            return tipo_base
    
    def _extract_codigo_submercado_from_query(self, query: str) -> Optional[int]:
        """
        Extrai código do submercado da query.
        Aceita tanto códigos numéricos quanto nomes dos submercados.
        
        Args:
            query: Query do usuário
            
        Returns:
            Código do submercado ou None
        """
        query_lower = query.lower()
        
        # Mapeamento reverso: nome (lowercase) -> código
        SUBMERCADO_NAMES_REVERSE = {
            "sudeste": 1,
            "centro-oeste": 1,
            "sul": 2,
            "nordeste": 3,
            "norte": 4
        }
        
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
                    return codigo
                except ValueError:
                    continue
        
        # Se não encontrou código numérico, tentar por nome do submercado
        for nome_submercado, codigo in SUBMERCADO_NAMES_REVERSE.items():
            padroes = [
                f"do {nome_submercado}",
                f"da {nome_submercado}",
                f"de {nome_submercado}",
                f"submercado {nome_submercado}",
                f"subsistema {nome_submercado}",
                f"\\b{nome_submercado}\\b",
            ]
            
            for padrao in padroes:
                if re.search(padrao, query_lower):
                    return codigo
        
        return None
