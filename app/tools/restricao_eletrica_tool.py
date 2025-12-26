"""
Tool para consultar restrições elétricas do arquivo restricao-eletrica.csv.
Acessa informações sobre restrições elétricas do modelo NEWAVE, incluindo:
- Fórmulas das restrições
- Períodos de validade
- Limites por período e patamar
"""
from app.tools.base import NEWAVETool
from app.utils.restricao_eletrica import RestricaoEletrica
import os
import pandas as pd
import re
from typing import Dict, Any, Optional


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
    
    def _extract_cod_rest_from_query(self, query: str, re_obj: RestricaoEletrica) -> Optional[int]:
        """
        Extrai código da restrição da query.
        Busca por código numérico ou por nome da restrição.
        
        Args:
            query: Query do usuário
            re_obj: Objeto RestricaoEletrica já lido
            
        Returns:
            Código da restrição ou None
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
                    return codigo
                except ValueError:
                    continue
        
        # ETAPA 2: Buscar por nome da restrição
        df_nomes = re_obj.nomes_restricoes
        if df_nomes is not None and not df_nomes.empty:
            for _, row in df_nomes.iterrows():
                cod_rest = int(row['cod_rest'])
                nome = str(row['nome']).lower().strip()
                
                if not nome:
                    continue
                
                # Match exato
                if nome == query_lower.strip():
                    print(f"[TOOL] ✅ Código {cod_rest} encontrado por nome (match exato): '{row['nome']}'")
                    return cod_rest
                
                # Match parcial - nome contido na query
                if nome in query_lower:
                    print(f"[TOOL] ✅ Código {cod_rest} encontrado por nome (match parcial): '{row['nome']}'")
                    return cod_rest
                
                # Match por palavras-chave
                palavras_nome = [p for p in nome.split() if len(p) > 2]
                palavras_query = [p for p in query_lower.split() if len(p) > 2]
                
                # Se todas as palavras principais do nome estão na query
                if palavras_nome and all(any(palavra in q for q in palavras_query) for palavra in palavras_nome):
                    print(f"[TOOL] ✅ Código {cod_rest} encontrado por nome (match por palavras): '{row['nome']}'")
                    return cod_rest
                
                # Match por similaridade (buscar palavras-chave específicas)
                palavras_chave_importantes = ['cachoeira', 'ferreira', 'gomes', 'escoamento', 'madeira', 
                                               'sul-se', 'imperatriz', 'sudeste', 'fns', 'fnese', 'xingu']
                
                for palavra_chave in palavras_chave_importantes:
                    if palavra_chave in nome and palavra_chave in query_lower:
                        print(f"[TOOL] ✅ Código {cod_rest} encontrado por palavra-chave '{palavra_chave}': '{row['nome']}'")
                        return cod_rest
        
        return None
    
    def _extract_patamar_from_query(self, query: str) -> Optional[int]:
        """
        Extrai patamar da query.
        
        Args:
            query: Query do usuário
            
        Returns:
            Patamar ou None
        """
        patterns = [
            r'patamar\s*(\d+)',
            r'pat\s*(\d+)',
            r'patamar\s*#?\s*(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query.lower())
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
            cod_rest = self._extract_cod_rest_from_query(query, re_obj)
            patamar = self._extract_patamar_from_query(query)
            periodo = self._extract_periodo_from_query(query)
            
            if cod_rest is not None:
                print(f"[TOOL] ✅ Filtro por código de restrição: {cod_rest}")
            
            if patamar is not None:
                print(f"[TOOL] ✅ Filtro por patamar: {patamar}")
            
            if periodo is not None:
                print(f"[TOOL] ✅ Filtro por período: {periodo}")
            
            # ETAPA 5: Aplicar filtros e formatar resultados
            print("[TOOL] ETAPA 5: Aplicando filtros e formatando resultados...")
            
            dados_lista = []
            
            # Processar restrições
            if df_restricoes is not None:
                resultado_restricoes = df_restricoes.copy()
                if cod_rest is not None:
                    resultado_restricoes = resultado_restricoes[resultado_restricoes['cod_rest'] == cod_rest]
                
                for _, row in resultado_restricoes.iterrows():
                    dados_lista.append({
                        'tipo': 'restricao',
                        **self._format_restricao_data(row)
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
                    dados_lista.append({
                        'tipo': 'horizonte',
                        **self._format_restricao_data(row)
                    })
            
            # Processar limites
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
                    dados_lista.append({
                        'tipo': 'limite',
                        **self._format_restricao_data(row)
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
        - "restrição Cachoeira Caldeirão"
        - "limites da restrição Sul-SE"
        - "restrição Imperatriz Sudeste"
        - "restrição FNS + FNESE"
        - "cachoeira caldeirão + ferreira gomes"
        
        Esta tool consulta o arquivo restricao-eletrica.csv e retorna informações sobre restrições elétricas, incluindo:
        - Fórmulas das restrições (ger_usih, ener_interc, etc.)
        - Períodos de validade das restrições (horizonte)
        - Limites por período e patamar
        
        A tool permite filtrar por:
        - Código da restrição (cod_rest) - ex: "restrição 1", "código restrição 20"
        - Nome da restrição - ex: "Escoamento Madeira", "Cachoeira Caldeirão", "Sul-SE", "Imperatriz Sudeste"
        - Patamar (1, 2, 3, ...)
        - Período (formato YYYY/MM)
        
        As restrições elétricas são usadas para modelar limites operacionais no sistema elétrico,
        como limites de geração de usinas específicas ou limites de intercâmbio entre submercados.
        
        Termos-chave: restrição elétrica, restrições elétricas, fórmula restrição, limite restrição, horizonte restrição, patamar restrição, ger_usih, ener_interc, cod_rest.
        """

