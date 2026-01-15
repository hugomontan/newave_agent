"""
Tool para consultar restrições elétricas do arquivo restricao-eletrica.csv.
Acessa informações sobre restrições elétricas do modelo NEWAVE, incluindo:
- Fórmulas das restrições
- Períodos de validade
- Limites por período e patamar
"""
from newave_agent.app.tools.base import NEWAVETool
from newave_agent.app.utils.restricao_eletrica import RestricaoEletrica
import os
import pandas as pd
import re
from typing import Dict, Any, Optional, Tuple


class RestricaoEletricaTool(NEWAVETool):
    """
    Tool para consultar restrições elétricas do arquivo restricao-eletrica.csv.
    
    Dados disponíveis:
    - Fórmulas das restrições elétricas (ger_usih, ener_interc, etc.)
    - Períodos de validade das restrições
    - Limites por período e patamar
    """
    
    def get_name(self) -> str:
        return "RestricaoEletricaTool"
    
    def can_handle(self, query: str) -> bool:
        """
        Verifica se a query é sobre restrições elétricas.
        
        Args:
            query: Query do usuário
            
        Returns:
            True se a tool pode processar a query
        """
        query_lower = query.lower()
        keywords = [
            "restrição elétrica",
            "restricao eletrica",
            "restrições elétricas",
            "restricoes eletricas",
            "restricao-eletrica",
            "restricao eletrica",
            "fórmula restrição",
            "formula restricao",
            "limite restrição",
            "limite restricao",
            "horizonte restrição",
            "horizonte restricao",
            "patamar restrição",
            "patamar restricao",
            "ger_usih",
            "ener_interc",
            "cod_rest",
            "código restrição",
            "codigo restricao",
        ]
        return any(kw in query_lower for kw in keywords)
    
    def _extract_cod_rest_from_query(self, query: str, re_obj: RestricaoEletrica) -> Tuple[Optional[int], list[str]]:
        """
        Extrai código da restrição da query.
        Busca por código numérico ou por nome da restrição.
        
        Args:
            query: Query do usuário
            re_obj: Objeto RestricaoEletrica já lido
            
        Returns:
            Tupla (código da restrição ou None, lista de nomes extraídos)
        """
        query_lower = query.lower()
        
        # ETAPA 1: Buscar por código numérico
        patterns = [
            r'restrição\s*(\d+)',
            r'restricao\s*(\d+)',
            r'cod_rest\s*(\d+)',
            r'código\s*restrição\s*(\d+)',
            r'codigo\s*restricao\s*(\d+)',
            r'restrição\s*#?\s*(\d+)',
            r'restricao\s*#?\s*(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query_lower)
            if match:
                try:
                    codigo = int(match.group(1))
                    print(f"[TOOL] ✅ Código de restrição encontrado por padrão numérico: {codigo}")
                    return codigo, []
                except ValueError:
                    continue
        
        # ETAPA 2: Extrair possíveis nomes da query antes de buscar
        # Padrões para extrair nomes de restrições da query
        nome_patterns = [
            r'restri[çc][ãa]o\s+(?:el[ée]trica\s+)?(?:de\s+|da\s+|do\s+)?([A-Z][A-Z0-9\s\+\-\>\/]+?)(?:\s|$)',  # "restrição de RSUL" ou "restrição RSUL"
            r'(?:de\s+|da\s+|do\s+)([A-Z][A-Z0-9\s\+\-\>\/]+?)(?:\s|$)',  # "de RSUL" ou "da FNS"
            r'\b([A-Z][A-Z0-9]{2,})\b',  # Qualquer palavra em maiúsculas com 3+ caracteres (sem espaços)
        ]
        
        nomes_extraidos = []
        palavras_comuns = {'restrição', 'restricao', 'elétrica', 'eletrica', 'qual', 'quais', 'de', 'da', 'do', 'as', 'os', 'the', 'of', 'a', 'an'}
        
        for pattern in nome_patterns:
            matches = re.findall(pattern, query)
            for match in matches:
                nome = match.strip()
                # Filtrar palavras muito curtas ou que são apenas palavras comuns
                # Também filtrar se contém apenas uma palavra comum
                palavras_nome = nome.lower().split()
                if len(nome) >= 3 and nome.lower() not in palavras_comuns:
                    # Verificar se não é apenas palavras comuns
                    palavras_validas = [p for p in palavras_nome if p not in palavras_comuns and len(p) >= 2]
                    if palavras_validas:
                        nomes_extraidos.append(nome)
        
        # Remover duplicatas mantendo ordem
        nomes_extraidos = list(dict.fromkeys(nomes_extraidos))
        
        print(f"[TOOL] Nomes extraídos da query: {nomes_extraidos}")
        
        # ETAPA 3: Buscar por nome da restrição
        # Primeiro tentar com os nomes extraídos (mais específico)
        for nome_extraido in nomes_extraidos:
            # Aplicar mapeamento se necessário
            nome_normalizado = nome_extraido.strip()
            # Remover "+" no final se houver
            nome_normalizado = re.sub(r'\s*\+\s*$', '', nome_normalizado).strip()
            # Aplicar mapeamento
            nome_mapeado = RestricaoEletrica.MAPEAMENTO_NOMES.get(nome_normalizado, nome_normalizado)
            # Verificar variações case-insensitive
            if nome_mapeado == nome_normalizado:
                nome_lower = nome_normalizado.lower()
                for nome_antigo, nome_novo in RestricaoEletrica.MAPEAMENTO_NOMES.items():
                    if nome_lower == nome_antigo.lower():
                        nome_mapeado = nome_novo
                        break
            
            cod_rest = re_obj.buscar_por_nome(nome_mapeado.lower())
            if cod_rest is not None:
                nome_encontrado = re_obj.nomes_restricoes[
                    re_obj.nomes_restricoes['cod_rest'] == cod_rest
                ]['nome'].iloc[0] if not re_obj.nomes_restricoes.empty else str(cod_rest)
                print(f"[TOOL] ✅ Código {cod_rest} encontrado por nome extraído '{nome_extraido}' (mapeado: '{nome_mapeado}'): '{nome_encontrado}'")
                return cod_rest, nomes_extraidos
        
        # ETAPA 4: Buscar com a query completa (fallback)
        cod_rest = re_obj.buscar_por_nome(query_lower)
        if cod_rest is not None:
            nome_encontrado = re_obj.nomes_restricoes[
                re_obj.nomes_restricoes['cod_rest'] == cod_rest
            ]['nome'].iloc[0] if not re_obj.nomes_restricoes.empty else str(cod_rest)
            print(f"[TOOL] ✅ Código {cod_rest} encontrado por nome (query completa): '{nome_encontrado}'")
            return cod_rest, nomes_extraidos
        
        # ETAPA 5: Busca direta pelos nomes conhecidos (mapeados por código)
        # Tentar buscar diretamente pelos nomes do mapeamento por código
        for cod_rest_mapeado, nome_mapeado in RestricaoEletrica.MAPEAMENTO_POR_CODIGO.items():
            if nome_mapeado.lower() in query_lower:
                cod_rest = re_obj.buscar_por_nome(nome_mapeado.lower())
                if cod_rest is not None:
                    print(f"[TOOL] ✅ Código {cod_rest} encontrado por nome mapeado (código {cod_rest_mapeado}): '{nome_mapeado}'")
                    return cod_rest, nomes_extraidos
        
        # ETAPA 6: Busca pelos nomes antigos (compatibilidade)
        for nome_antigo, nome_novo in RestricaoEletrica.MAPEAMENTO_NOMES.items():
            if nome_antigo.lower() in query_lower or nome_novo.lower() in query_lower:
                cod_rest = re_obj.buscar_por_nome(nome_novo.lower())
                if cod_rest is not None:
                    print(f"[TOOL] ✅ Código {cod_rest} encontrado por nome mapeado: '{nome_novo}'")
                    return cod_rest, nomes_extraidos
        
        print(f"[TOOL] ⚠️ Nenhum código de restrição encontrado na query")
        return None, nomes_extraidos
    
    def _extract_patamar_from_query(self, query: str) -> Optional[int]:
        """
        Extrai patamar da query.
        MELHORADO para aceitar nomes de patamares também.
        
        Args:
            query: Query do usuário
            
        Returns:
            Patamar ou None
        """
        query_lower = query.lower()
        
        # Buscar por nome do patamar
        if 'pesado' in query_lower or 'p1' in query_lower:
            return 1
        if 'medio' in query_lower or 'médio' in query_lower or 'p2' in query_lower:
            return 2
        if 'leve' in query_lower or 'p3' in query_lower:
            return 3
        
        # Buscar por número (lógica existente)
        patterns = [
            r'patamar\s*(\d+)',
            r'pat\s*(\d+)',
            r'patamar\s*#?\s*(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query_lower)
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    continue
        
        return None
    
    def _extract_periodo_from_query(self, query: str) -> Optional[Dict[str, str]]:
        """
        Extrai período da query (formato YYYY/MM).
        
        Args:
            query: Query do usuário
            
        Returns:
            Dict com 'per_ini' e/ou 'per_fin' ou None
        """
        periodo = {}
        
        # Buscar período no formato YYYY/MM
        pattern_periodo = r'(\d{4}/\d{1,2})'
        periodos = re.findall(pattern_periodo, query)
        
        if len(periodos) >= 1:
            periodo['per_ini'] = periodos[0]
        if len(periodos) >= 2:
            periodo['per_fin'] = periodos[1]
        elif len(periodos) == 1:
            periodo['per_fin'] = periodos[0]
        
        return periodo if periodo else None
    
    def _format_restricao_data(self, row: pd.Series) -> Dict[str, Any]:
        """
        Formata os dados de uma restrição.
        
        Args:
            row: Linha do DataFrame
            
        Returns:
            Dicionário formatado
        """
        dados = {}
        for col in row.index:
            valor = row[col]
            if pd.notna(valor):
                if isinstance(valor, (int, float)):
                    dados[col] = int(valor) if isinstance(valor, float) and valor.is_integer() else float(valor)
                else:
                    dados[col] = str(valor)
            else:
                dados[col] = None
        
        return dados
    
    def execute(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Executa a consulta de restrições elétricas.
        
        Fluxo:
        1. Verifica se restricao-eletrica.csv existe
        2. Lê o arquivo usando RestricaoEletrica
        3. Identifica filtros (código restrição, patamar, período)
        4. Retorna dados filtrados
        """
        print(f"[TOOL] {self.get_name()}: Iniciando execução...")
        print(f"[TOOL] Query: {query[:100]}")
        print(f"[TOOL] Deck path: {self.deck_path}")
        
        try:
            # ETAPA 1: Verificar existência do arquivo
            print("[TOOL] ETAPA 1: Verificando existência do arquivo restricao-eletrica.csv...")
            csv_path = os.path.join(self.deck_path, "restricao-eletrica.csv")
            
            if not os.path.exists(csv_path):
                print(f"[TOOL] ❌ Arquivo restricao-eletrica.csv não encontrado")
                return {
                    "success": False,
                    "error": f"Arquivo restricao-eletrica.csv não encontrado em {self.deck_path}",
                    "tool": self.get_name()
                }
            
            print(f"[TOOL] ✅ Arquivo encontrado: {csv_path}")
            
            # ETAPA 2: Ler arquivo usando RestricaoEletrica
            print("[TOOL] ETAPA 2: Lendo arquivo com RestricaoEletrica...")
            re_obj = RestricaoEletrica.read(csv_path)
            print("[TOOL] ✅ Arquivo lido com sucesso")
            
            # ETAPA 3: Acessar propriedades
            print("[TOOL] ETAPA 3: Acessando propriedades...")
            df_restricoes = re_obj.restricoes
            df_horizontes = re_obj.horizontes
            df_limites = re_obj.limites
            
            if df_restricoes is None and df_horizontes is None and df_limites is None:
                print("[TOOL] ⚠️ Nenhuma restrição elétrica encontrada")
                return {
                    "success": False,
                    "error": "Nenhuma restrição elétrica encontrada no arquivo",
                    "tool": self.get_name()
                }
            
            print(f"[TOOL] ✅ Dados carregados:")
            if df_restricoes is not None:
                print(f"[TOOL]   - Restrições: {len(df_restricoes)} registro(s)")
            if df_horizontes is not None:
                print(f"[TOOL]   - Horizontes: {len(df_horizontes)} registro(s)")
            if df_limites is not None:
                print(f"[TOOL]   - Limites: {len(df_limites)} registro(s)")
            
            # ETAPA 4: Identificar filtros
            print("[TOOL] ETAPA 4: Identificando filtros...")
            cod_rest, nomes_extraidos = self._extract_cod_rest_from_query(query, re_obj)
            patamar = self._extract_patamar_from_query(query)
            periodo = self._extract_periodo_from_query(query)
            
            # Verificar se a query menciona uma restrição específica mas não foi encontrada
            if nomes_extraidos and cod_rest is None:
                print(f"[TOOL] ⚠️ Query menciona restrição específica ({nomes_extraidos}) mas não foi encontrada")
                return {
                    "success": False,
                    "error": f"Nenhuma restrição elétrica encontrada para: {', '.join(nomes_extraidos)}",
                    "tool": self.get_name()
                }
            
            if cod_rest is not None:
                print(f"[TOOL] ✅ Filtro por código de restrição: {cod_rest}")
            
            if patamar is not None:
                print(f"[TOOL] ✅ Filtro por patamar: {patamar}")
            
            if periodo is not None:
                print(f"[TOOL] ✅ Filtro por período: {periodo}")
            
            # ETAPA 5: Aplicar filtros e formatar resultados
            print("[TOOL] ETAPA 5: Aplicando filtros e formatando resultados...")
            
            dados_lista = []
            
            # Obter mapeamento de nomes
            df_nomes = re_obj.nomes_restricoes
            nomes_dict = {}
            if df_nomes is not None and not df_nomes.empty:
                nomes_dict = dict(zip(df_nomes['cod_rest'], df_nomes['nome']))
            
            # Processar restrições
            if df_restricoes is not None:
                resultado_restricoes = df_restricoes.copy()
                if cod_rest is not None:
                    resultado_restricoes = resultado_restricoes[resultado_restricoes['cod_rest'] == cod_rest]
                
                for _, row in resultado_restricoes.iterrows():
                    dados_formatados = self._format_restricao_data(row)
                    # Adicionar nome da restrição se disponível
                    if 'cod_rest' in dados_formatados and dados_formatados['cod_rest'] in nomes_dict:
                        dados_formatados['nome_restricao'] = nomes_dict[dados_formatados['cod_rest']]
                    dados_lista.append({
                        'tipo': 'restricao',
                        **dados_formatados
                    })
            
            # Processar horizontes
            if df_horizontes is not None:
                resultado_horizontes = df_horizontes.copy()
                if cod_rest is not None:
                    resultado_horizontes = resultado_horizontes[resultado_horizontes['cod_rest'] == cod_rest]
                if periodo is not None:
                    if 'per_ini' in periodo:
                        resultado_horizontes = resultado_horizontes[
                            resultado_horizontes['per_ini'] == periodo['per_ini']
                        ]
                    if 'per_fin' in periodo:
                        resultado_horizontes = resultado_horizontes[
                            resultado_horizontes['per_fin'] == periodo['per_fin']
                        ]
                
                for _, row in resultado_horizontes.iterrows():
                    dados_formatados = self._format_restricao_data(row)
                    # Adicionar nome da restrição se disponível
                    if 'cod_rest' in dados_formatados and dados_formatados['cod_rest'] in nomes_dict:
                        dados_formatados['nome_restricao'] = nomes_dict[dados_formatados['cod_rest']]
                    dados_lista.append({
                        'tipo': 'horizonte',
                        **dados_formatados
                    })
            
            # Processar limites - REMOVER lim_inf e adicionar nome_patamar
            if df_limites is not None:
                resultado_limites = df_limites.copy()
                if cod_rest is not None:
                    resultado_limites = resultado_limites[resultado_limites['cod_rest'] == cod_rest]
                if patamar is not None:
                    resultado_limites = resultado_limites[resultado_limites['patamar'] == patamar]
                if periodo is not None:
                    if 'per_ini' in periodo:
                        resultado_limites = resultado_limites[
                            resultado_limites['per_ini'] == periodo['per_ini']
                        ]
                    if 'per_fin' in periodo:
                        resultado_limites = resultado_limites[
                            resultado_limites['per_fin'] == periodo['per_fin']
                        ]
                
                for _, row in resultado_limites.iterrows():
                    dados_formatados = self._format_restricao_data(row)
                    # Remover lim_inf (não queremos mostrar limites inferiores)
                    if 'lim_inf' in dados_formatados:
                        del dados_formatados['lim_inf']
                    # Adicionar nome da restrição se disponível
                    if 'cod_rest' in dados_formatados and dados_formatados['cod_rest'] in nomes_dict:
                        dados_formatados['nome_restricao'] = nomes_dict[dados_formatados['cod_rest']]
                    # Nome do patamar já está incluído na propriedade limites
                    dados_lista.append({
                        'tipo': 'limite',
                        **dados_formatados
                    })
            
            print(f"[TOOL] ✅ {len(dados_lista)} registro(s) após filtros")
            
            # ETAPA 6: Estatísticas
            stats = {}
            if df_restricoes is not None:
                stats['total_restricoes'] = len(df_restricoes)
                stats['codigos_restricoes'] = sorted(df_restricoes['cod_rest'].unique().tolist()) if 'cod_rest' in df_restricoes.columns else []
            
            # Adicionar informações de nomes das restrições
            df_nomes = re_obj.nomes_restricoes
            if df_nomes is not None and not df_nomes.empty:
                stats['restricoes_com_nome'] = df_nomes.to_dict('records')
            
            if df_horizontes is not None:
                stats['total_horizontes'] = len(df_horizontes)
            
            if df_limites is not None:
                stats['total_limites'] = len(df_limites)
                if 'patamar' in df_limites.columns:
                    stats['patamares_disponiveis'] = sorted(df_limites['patamar'].unique().tolist())
            
            # ETAPA 7: Formatar resultado final
            print("[TOOL] ETAPA 7: Formatando resultado final...")
            
            filtros_aplicados = {}
            if cod_rest is not None:
                filtros_aplicados['cod_rest'] = cod_rest
            if patamar is not None:
                filtros_aplicados['patamar'] = patamar
            if periodo is not None:
                filtros_aplicados['periodo'] = periodo
            
            return {
                "success": True,
                "dados": dados_lista,
                "stats": stats,
                "filtros_aplicados": filtros_aplicados if filtros_aplicados else None,
                "description": f"Restrições elétricas: {len(dados_lista)} registro(s) do arquivo restricao-eletrica.csv",
                "tool": self.get_name()
            }
            
        except FileNotFoundError as e:
            print(f"[TOOL] ❌ Erro FileNotFoundError: {e}")
            return {
                "success": False,
                "error": f"Arquivo não encontrado: {str(e)}",
                "tool": self.get_name()
            }
        except Exception as e:
            print(f"[TOOL] ❌ Erro ao processar: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": f"Erro ao processar restricao-eletrica.csv: {str(e)}",
                "error_type": type(e).__name__,
                "tool": self.get_name()
            }
    
    def get_description(self) -> str:
        """
        Retorna descrição da tool para uso pelo LLM.
        
        Returns:
            String com descrição detalhada
        """
        return """
        Restrições elétricas. Dados de restrições elétricas do modelo NEWAVE do arquivo restricao-eletrica.csv.
        
        Queries que ativam esta tool:
        - "restrição elétrica"
        - "restrições elétricas"
        - "fórmula restrição"
        - "limite restrição"
        - "horizonte restrição"
        - "patamar restrição"
        - "restrição 1"
        - "código restrição 20"
        - "limites da restrição 1"
        - "fórmula da restrição 20"
        - "horizonte da restrição 1"
        - "limites da restrição 1 patamar 2"
        - "restrição elétrica período 2025/12"
        - "restrição Escoamento Madeira"
        - "restrição RSUL"
        - "restrição FNS"
        - "limites da restrição FNS"
        - "restrição FNS + FNESE"
        - "restrição FNS + FNESE + XINGU"
        - "restrição Cachoeira Caldeirão + Ferreira Gomes"
        
        Esta tool consulta o arquivo restricao-eletrica.csv e retorna informações sobre restrições elétricas, incluindo:
        - Fórmulas das restrições (ger_usih, ener_interc, etc.)
        - Períodos de validade das restrições (horizonte)
        - Limites por período e patamar
        
        A tool permite filtrar por:
        - Código da restrição (cod_rest) - ex: "restrição 1", "código restrição 20"
        - Nome da restrição - ex: "Escoamento Madeira", "RSUL", "FNS", "FNS + FNESE", "FNS + FNESE + XINGU", "Cachoeira Caldeirão + Ferreira Gomes"
        - Patamar (1, 2, 3, ...)
        - Período (formato YYYY/MM)
        
        As restrições elétricas são usadas para modelar limites operacionais no sistema elétrico,
        como limites de geração de usinas específicas ou limites de intercâmbio entre submercados.
        
        Termos-chave: restrição elétrica, restrições elétricas, fórmula restrição, limite restrição, horizonte restrição, patamar restrição, ger_usih, ener_interc, cod_rest.
        """

