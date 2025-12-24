"""
Tool para consultar configuração de usinas hidrelétricas do CONFHD.DAT.
Acessa informações de configuração do sistema hidrelétrico, incluindo:
- Associação de usinas a REEs
- Status das usinas (EX, EE, NE, NC)
- Volume inicial armazenado
- Configurações de modificação
- Histórico de vazões
"""
from app.tools.base import NEWAVETool
from inewave.newave import Confhd
import os
import pandas as pd
import re
from typing import Dict, Any, Optional
from difflib import SequenceMatcher


class ConfhdTool(NEWAVETool):
    """
    Tool para consultar configuração de usinas hidrelétricas do CONFHD.DAT.
    
    Dados disponíveis:
    - Código e nome da usina
    - Posto de vazões
    - Usina a jusante
    - REE (Reservatório Equivalente de Energia)
    - Volume inicial (% do volume útil)
    - Status da usina (EX, EE, NE, NC)
    - Índice de modificação
    - Histórico de vazões (ano início/fim)
    """
    
    def get_name(self) -> str:
        return "ConfhdTool"
    
    def can_handle(self, query: str) -> bool:
        """
        Verifica se a query é sobre configuração de usinas do CONFHD.
        
        Args:
            query: Query do usuário
            
        Returns:
            True se a tool pode processar a query
        """
        query_lower = query.lower()
        keywords = [
            "confhd",
            "confhd.dat",
            "configuração hidrelétrica",
            "configuracao hidreletrica",
            "configuração de usinas",
            "configuracao de usinas",
            "ree",
            "reservatório equivalente",
            "reservatorio equivalente",
            "volume inicial",
            "status da usina",
            "usina existente",
            "usina em expansão",
            "usina modificada",
            "histórico de vazões",
            "historico de vazoes",
            "ano início histórico",
            "ano inicio historico",
            "ano fim histórico",
            "ano fim historico",
            "usina a jusante",
            "cadeia hidráulica",
            "cadeia hidraulica",
            "usina jusante",
            "índice de modificação",
            "indice de modificacao",
        ]
        return any(kw in query_lower for kw in keywords)
    
    def _extract_usina_from_query(self, query: str, confhd: Confhd) -> Optional[tuple]:
        """
        Extrai código da usina da query usando cross-validation com o arquivo.
        Busca por número ou nome da usina com matching inteligente.
        
        Args:
            query: Query do usuário
            confhd: Objeto Confhd já lido
            
        Returns:
            Tupla (código_usina, idx_real) onde:
            - código_usina: Código da usina
            - idx_real: Índice real do DataFrame
            Retorna None se não encontrado
        """
        query_lower = query.lower()
        
        # Verificar se há usinas
        usinas_df = confhd.usinas
        if usinas_df is None or usinas_df.empty:
            print("[TOOL] ⚠️ DataFrame de usinas vazio ou inexistente")
            return None
        
        # ETAPA 1: Tentar extrair número explícito (código da usina)
        patterns = [
            r'usina\s*(\d+)',
            r'usina\s*hidrelétrica\s*(\d+)',
            r'usina\s*hidreletrica\s*(\d+)',
            r'usina\s*#?\s*(\d+)',
            r'código\s*(\d+)',
            r'codigo\s*(\d+)',
            r'hidrelétrica\s*(\d+)',
            r'hidreletrica\s*(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query_lower)
            if match:
                try:
                    codigo = int(match.group(1))
                    # Buscar a usina pelo código
                    mask = usinas_df['codigo_usina'] == codigo
                    if mask.any():
                        row = usinas_df[mask].iloc[0]
                        nome = str(row.get('nome_usina', '')).strip()
                        idx_real = row.name
                        print(f"[TOOL] ✅ Código {codigo} encontrado por padrão numérico: '{nome}' (idx_real={idx_real})")
                        return (codigo, idx_real)
                except (ValueError, IndexError):
                    continue
        
        # ETAPA 2: Buscar por nome da usina
        print(f"[TOOL] Buscando usina por nome na query: '{query}'")
        print(f"[TOOL] Total de usinas no CONFHD: {len(usinas_df)}")
        
        # Palavras comuns a ignorar
        palavras_ignorar = {'de', 'da', 'do', 'das', 'dos', 'e', 'a', 'o', 'as', 'os', 'em', 'na', 'no', 'nas', 'nos', 'a', 'à', 'ao', 'aos', 'informacoes', 'informações', 'dados', 'usina', 'hidrelétrica', 'hidreletrica', 'configuração', 'configuracao', 'confhd'}
        
        # Extrair palavras significativas da query
        palavras_query = [p for p in query_lower.split() if len(p) > 2 and p not in palavras_ignorar]
        print(f"[TOOL] Palavras significativas extraídas da query: {palavras_query}")
        
        # Lista todas as usinas disponíveis
        print(f"[TOOL] Usinas disponíveis no arquivo:")
        usinas_list = []
        for idx, row in usinas_df.iterrows():
            codigo = int(row.get('codigo_usina', 0))
            nome = str(row.get('nome_usina', '')).strip()
            if nome:
                usinas_list.append({'codigo': codigo, 'nome': nome, 'idx': idx})
                print(f"[TOOL]   - Código {codigo}: \"{nome}\"")
        
        if not usinas_list:
            print("[TOOL] ⚠️ Nenhuma usina com nome encontrada")
            return None
        
        # Ordenar por tamanho do nome (maior primeiro) para priorizar matches mais específicos
        usinas_sorted = sorted(usinas_list, key=lambda x: len(x['nome']), reverse=True)
        
        # ETAPA 2.1: Buscar match exato do nome completo (prioridade máxima)
        for usina in usinas_sorted:
            codigo_usina = usina['codigo']
            nome_usina = usina['nome']
            nome_usina_lower = nome_usina.lower().strip()
            
            if not nome_usina_lower:
                continue
            
            # Match exato do nome completo
            if nome_usina_lower == query_lower.strip():
                idx_real = usina['idx']
                print(f"[TOOL] ✅ Código {codigo_usina} encontrado por match exato '{nome_usina}' (idx_real={idx_real})")
                return (codigo_usina, idx_real)
            
            # Match exato do nome completo dentro da query (como palavra completa)
            if len(nome_usina_lower) >= 4:  # Nomes com pelo menos 4 caracteres
                pattern = r'\b' + re.escape(nome_usina_lower) + r'\b'
                if re.search(pattern, query_lower):
                    idx_real = usina['idx']
                    print(f"[TOOL] ✅ Código {codigo_usina} encontrado por nome completo '{nome_usina}' na query (idx_real={idx_real})")
                    return (codigo_usina, idx_real)
        
        # ETAPA 2.2: Buscar por similaridade e palavras-chave
        candidatos = []
        
        for usina in usinas_sorted:
            codigo_usina = usina['codigo']
            nome_usina = usina['nome']
            nome_usina_lower = nome_usina.lower().strip()
            
            if not nome_usina_lower:
                continue
            
            # Extrair palavras significativas do nome da usina
            palavras_nome = [p for p in nome_usina_lower.split() if len(p) > 2 and p not in palavras_ignorar]
            
            # PRIORIDADE 3: Match exato de todas as palavras significativas
            if palavras_nome and all(palavra in query_lower for palavra in palavras_nome):
                idx_real = usina['idx']
                print(f"[TOOL] ✅ Código {codigo_usina} encontrado: todas as palavras significativas de '{nome_usina}' estão na query (idx_real={idx_real})")
                return (codigo_usina, idx_real)
            
            # PRIORIDADE 4: Similaridade de string
            similarity = SequenceMatcher(None, query_lower, nome_usina_lower).ratio()
            if similarity > 0.6:  # 60% de similaridade
                candidatos.append({
                    'codigo': codigo_usina,
                    'nome': nome_usina,
                    'idx_real': usina['idx'],
                    'score': similarity,
                    'tipo': 'similarity'
                })
            
            # PRIORIDADE 5: Contagem de palavras significativas em comum
            palavras_comuns = set(palavras_query) & set(palavras_nome)
            if palavras_comuns:
                # Requer pelo menos 2 palavras em comum OU uma palavra longa (>= 5 chars)
                palavras_longas = [p for p in palavras_comuns if len(p) >= 5]
                if len(palavras_comuns) >= 2 or (len(palavras_longas) >= 1 and len(palavras_comuns) >= 1):
                    score = len(palavras_comuns) / max(len(palavras_nome), 1)
                    candidatos.append({
                        'codigo': codigo_usina,
                        'nome': nome_usina,
                        'idx_real': usina['idx'],
                        'score': score,
                        'tipo': 'palavras_comuns'
                    })
        
        # Se encontrou candidatos, retornar o melhor
        if candidatos:
            # Ordenar por tipo (similarity primeiro) e depois por score
            candidatos.sort(key=lambda x: (x['tipo'] == 'similarity', x['score']), reverse=True)
            melhor = candidatos[0]
            print(f"[TOOL] ✅ Código {melhor['codigo']} encontrado por {melhor['tipo']} (score: {melhor['score']:.2f}): '{melhor['nome']}' (idx_real={melhor['idx_real']})")
            return (melhor['codigo'], melhor['idx_real'])
        
        print("[TOOL] ⚠️ Nenhuma usina específica detectada na query")
        return None
    
    def _extract_ree_from_query(self, query: str) -> Optional[int]:
        """
        Extrai número do REE da query.
        
        Args:
            query: Query do usuário
            
        Returns:
            Número do REE ou None
        """
        patterns = [
            r'ree\s*(\d+)',
            r'reservatório\s+equivalente\s*(\d+)',
            r'reservatorio\s+equivalente\s*(\d+)',
            r'ree\s*#?\s*(\d+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, query.lower())
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    continue
        return None
    
    def _extract_status_from_query(self, query: str) -> Optional[str]:
        """
        Extrai status da usina da query.
        
        Args:
            query: Query do usuário
            
        Returns:
            Status (EX, EE, NE, NC) ou None
        """
        query_lower = query.lower()
        if 'existente' in query_lower and ('expansão' in query_lower or 'expansao' in query_lower):
            return 'EE'
        elif 'existente' in query_lower:
            return 'EX'
        elif 'não existente' in query_lower or 'nao existente' in query_lower:
            return 'NE'
        elif 'não considerada' in query_lower or 'nao considerada' in query_lower:
            return 'NC'
        return None
    
    def _format_usina_data(self, row: pd.Series) -> Dict[str, Any]:
        """
        Formata os dados de uma usina do CONFHD.
        
        Args:
            row: Linha do DataFrame do CONFHD
            
        Returns:
            Dicionário com todos os dados formatados
        """
        dados = {
            'codigo_usina': int(row.get('codigo_usina', 0)) if pd.notna(row.get('codigo_usina')) else None,
            'nome_usina': str(row.get('nome_usina', '')).strip() if pd.notna(row.get('nome_usina')) else None,
            'posto': int(row.get('posto', 0)) if pd.notna(row.get('posto')) and row.get('posto', 0) > 0 else None,
            'codigo_usina_jusante': int(row.get('codigo_usina_jusante', 0)) if pd.notna(row.get('codigo_usina_jusante')) and row.get('codigo_usina_jusante', 0) > 0 else None,
            'ree': int(row.get('ree', 0)) if pd.notna(row.get('ree')) else None,
            'volume_inicial_percentual': float(row.get('volume_inicial_percentual', 0)) if pd.notna(row.get('volume_inicial_percentual')) else None,
            'usina_existente': str(row.get('usina_existente', '')).strip() if pd.notna(row.get('usina_existente')) else None,
            'usina_modificada': int(row.get('usina_modificada', 0)) if pd.notna(row.get('usina_modificada')) else None,
            'ano_inicio_historico': int(row.get('ano_inicio_historico', 0)) if pd.notna(row.get('ano_inicio_historico')) and row.get('ano_inicio_historico', 0) > 0 else None,
            'ano_fim_historico': int(row.get('ano_fim_historico', 0)) if pd.notna(row.get('ano_fim_historico')) and row.get('ano_fim_historico', 0) > 0 else None,
        }
        
        # Adicionar descrições dos status
        status_desc = {
            'EX': 'Usina existente',
            'EE': 'Usina existente com expansão',
            'NE': 'Usina não existente',
            'NC': 'Usina não considerada'
        }
        if dados['usina_existente'] in status_desc:
            dados['usina_existente_descricao'] = status_desc[dados['usina_existente']]
        
        return dados
    
    def execute(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Executa a consulta de configuração de usinas do CONFHD.DAT.
        
        Fluxo:
        1. Verifica se CONFHD.DAT existe
        2. Lê o arquivo usando inewave
        3. Identifica filtros (usina, REE, status)
        4. Retorna dados filtrados
        """
        print(f"[TOOL] {self.get_name()}: Iniciando execução...")
        print(f"[TOOL] Query: {query[:100]}")
        print(f"[TOOL] Deck path: {self.deck_path}")
        
        try:
            # ETAPA 1: Verificar existência do arquivo
            print("[TOOL] ETAPA 1: Verificando existência do arquivo CONFHD.DAT...")
            confhd_path = os.path.join(self.deck_path, "CONFHD.DAT")
            
            if not os.path.exists(confhd_path):
                confhd_path = os.path.join(self.deck_path, "confhd.dat")
                if not os.path.exists(confhd_path):
                    print(f"[TOOL] ❌ Arquivo CONFHD.DAT não encontrado")
                    return {
                        "success": False,
                        "error": f"Arquivo CONFHD.DAT não encontrado em {self.deck_path}",
                        "tool": self.get_name()
                    }
            
            print(f"[TOOL] ✅ Arquivo encontrado: {confhd_path}")
            
            # ETAPA 2: Ler arquivo usando inewave
            print("[TOOL] ETAPA 2: Lendo arquivo com inewave...")
            confhd = Confhd.read(confhd_path)
            print("[TOOL] ✅ Arquivo lido com sucesso")
            
            # ETAPA 3: Verificar se há dados
            usinas_df = confhd.usinas
            if usinas_df is None or usinas_df.empty:
                print("[TOOL] ⚠️ Nenhuma usina encontrada no CONFHD")
                return {
                    "success": False,
                    "error": "Nenhuma usina encontrada no arquivo CONFHD.DAT",
                    "tool": self.get_name()
                }
            
            print(f"[TOOL] ✅ {len(usinas_df)} usina(s) encontrada(s) no CONFHD")
            
            # ETAPA 4: Identificar filtros da query
            print("[TOOL] ETAPA 4: Identificando filtros...")
            codigo_usina = None
            ree = self._extract_ree_from_query(query)
            status = self._extract_status_from_query(query)
            
            # Buscar usina por código ou nome
            resultado_usina = self._extract_usina_from_query(query, confhd)
            if resultado_usina is not None:
                codigo_usina, _ = resultado_usina
                print(f"[TOOL] ✅ Filtro por usina: {codigo_usina}")
            
            if ree is not None:
                print(f"[TOOL] ✅ Filtro por REE: {ree}")
            
            if status is not None:
                print(f"[TOOL] ✅ Filtro por status: {status}")
            
            # ETAPA 5: Aplicar filtros
            print("[TOOL] ETAPA 5: Aplicando filtros...")
            resultado_df = usinas_df.copy()
            
            if codigo_usina is not None:
                resultado_df = resultado_df[resultado_df['codigo_usina'] == codigo_usina]
            
            if ree is not None:
                resultado_df = resultado_df[resultado_df['ree'] == ree]
            
            if status is not None:
                resultado_df = resultado_df[resultado_df['usina_existente'] == status]
            
            print(f"[TOOL] ✅ {len(resultado_df)} usina(s) após filtros")
            
            # ETAPA 6: Formatar resultados
            print("[TOOL] ETAPA 6: Formatando resultados...")
            dados_lista = []
            for _, row in resultado_df.iterrows():
                dados_lista.append(self._format_usina_data(row))
            
            # ETAPA 7: Estatísticas
            stats = {
                'total_usinas': len(usinas_df),
                'usinas_filtradas': len(resultado_df),
            }
            
            # Usinas por REE
            if 'ree' in usinas_df.columns:
                stats['usinas_por_ree'] = usinas_df.groupby('ree').size().to_dict()
            
            # Usinas por status
            if 'usina_existente' in usinas_df.columns:
                stats['usinas_por_status'] = usinas_df['usina_existente'].value_counts().to_dict()
            
            # Volume inicial médio por REE
            if 'volume_inicial_percentual' in usinas_df.columns and 'ree' in usinas_df.columns:
                volume_medio_por_ree = usinas_df.groupby('ree')['volume_inicial_percentual'].mean().to_dict()
                stats['volume_inicial_medio_por_ree'] = {k: round(v, 2) for k, v in volume_medio_por_ree.items()}
            
            # ETAPA 8: Formatar resultado final
            print("[TOOL] ETAPA 8: Formatando resultado final...")
            
            filtros_aplicados = {}
            if codigo_usina is not None:
                filtros_aplicados['codigo_usina'] = codigo_usina
            if ree is not None:
                filtros_aplicados['ree'] = ree
            if status is not None:
                filtros_aplicados['status'] = status
            
            return {
                "success": True,
                "dados": dados_lista,
                "stats": stats,
                "filtros_aplicados": filtros_aplicados if filtros_aplicados else None,
                "description": f"Configuração de {len(resultado_df)} usina(s) do CONFHD.DAT",
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
                "error": f"Erro ao processar CONFHD.DAT: {str(e)}",
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
        Configuração de usinas hidrelétricas. Dados de configuração do sistema hidrelétrico do arquivo CONFHD.DAT.
        
        Queries que ativam esta tool:
        - "configuração de usinas do confhd"
        - "usinas do REE 1"
        - "volume inicial da usina X"
        - "status da usina Y"
        - "usinas existentes"
        - "usinas em expansão"
        - "usinas modificadas"
        - "histórico de vazões da usina Z"
        - "cadeia hidráulica"
        - "usina a jusante"
        - "configuração da usina Itaipu"
        - "ree da usina Furnas"
        
        Esta tool consulta o arquivo CONFHD.DAT e retorna informações de configuração das usinas, incluindo:
        - Associação a REE (Reservatório Equivalente de Energia)
        - Status da usina (EX=existente, EE=existente com expansão, NE=não existente, NC=não considerada)
        - Volume inicial armazenado (% do volume útil)
        - Índice de modificação (indica se dados serão modificados via MODIF.DAT)
        - Histórico de vazões (anos início/fim para ajuste do modelo)
        - Usina a jusante (cadeia hidráulica)
        - Posto de vazões
        
        A tool identifica automaticamente a usina mencionada na query através de matching inteligente:
        - Busca por código numérico explícito
        - Busca por nome completo da usina
        - Busca por similaridade de strings
        - Busca por palavras-chave do nome
        
        A tool também permite filtrar por:
        - REE específico
        - Status da usina (EX, EE, NE, NC)
        
        Termos-chave: CONFHD, configuração hidrelétrica, REE, reservatório equivalente, volume inicial, status da usina, usina existente, usina em expansão, usina modificada, histórico de vazões, cadeia hidráulica, usina a jusante.
        """

