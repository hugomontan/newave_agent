"""
Tool para consultar vazões históricas de postos fluviométricos.
Acessa o arquivo VAZOES.DAT, propriedade vazoes.
Inclui mapeamento interno de nome de usina para posto (via CONFHD.DAT).
"""
from app.tools.base import NEWAVETool
from inewave.newave import Vazoes, Confhd
import os
import pandas as pd
import re
from typing import Dict, Any, Optional
from difflib import SequenceMatcher

class VazoesTool(NEWAVETool):
    """
    Tool para consultar vazões históricas de postos fluviométricos.
    Acessa o arquivo VAZOES.DAT, propriedade vazoes.
    """
    
    def __init__(self, deck_path: str):
        super().__init__(deck_path)
        
        # Cache do mapeamento (carregado uma vez no init, não lazy)
        self._mapeamento_usina_posto: Optional[Dict[str, int]] = None
        self._mapeamento_posto_usina: Optional[Dict[int, str]] = None  # Inverso
        self._confhd_path: Optional[str] = None
        self._ano_inicial_cache: Optional[int] = None
        
        # Carregar mapeamento uma vez no init
        self._carregar_mapeamento_usina_posto()
    
    def get_name(self) -> str:
        return "VazoesTool"
    
    def can_handle(self, query: str) -> bool:
        """
        Verifica se a query é sobre vazões históricas.
        
        Args:
            query: Query do usuário
            
        Returns:
            True se a tool pode processar a query
        """
        query_lower = query.lower()
        keywords = [
            "vazao",
            "vazão",
            "vazoes",
            "vazões",
            "vazao historica",
            "vazão histórica",
            "vazoes historicas",
            "vazões históricas",
            "historico de vazoes",
            "histórico de vazões",
            "serie de vazoes",
            "série de vazões",
            "vazao do posto",
            "vazão do posto",
            "vazao do posto fluviometrico",
            "vazão do posto fluviométrico",
            "afluencia",
            "afluência",
            "afluencias",
            "afluências",
            "vazao natural",
            "vazão natural",
            "vazoes naturais",
            "vazões naturais",
            "evaporacoes"
        ]
        return any(kw in query_lower for kw in keywords)
    
    def _carregar_mapeamento_usina_posto(self) -> Dict[str, int]:
        """
        Carrega o mapeamento nome_usina → posto do CONFHD.DAT.
        Carrega uma vez e armazena na instância da tool.
        
        Returns:
            Dicionário {nome_usina_upper: posto}
        """
        # Se já foi carregado, retornar cache
        if self._mapeamento_usina_posto is not None:
            return self._mapeamento_usina_posto
        
        print("[TOOL] Carregando mapeamento completo usina → posto do CONFHD.DAT (descompilando)...")
        
        # Tentar encontrar CONFHD.DAT
        confhd_path = os.path.join(self.deck_path, "CONFHD.DAT")
        if not os.path.exists(confhd_path):
            confhd_path = os.path.join(self.deck_path, "confhd.dat")
        
        if not os.path.exists(confhd_path):
            print("[TOOL] ⚠️ CONFHD.DAT não encontrado - consultas por nome de usina não funcionarão")
            self._mapeamento_usina_posto = {}
            self._mapeamento_posto_usina = {}
            return self._mapeamento_usina_posto
        
        try:
            confhd = Confhd.read(confhd_path)
            
            if confhd.usinas is None or confhd.usinas.empty:
                print("[TOOL] ⚠️ Nenhuma usina encontrada no CONFHD.DAT")
                self._mapeamento_usina_posto = {}
                self._mapeamento_posto_usina = {}
                return self._mapeamento_usina_posto
            
            # Criar mapeamento
            mapeamento = {}
            mapeamento_inverso = {}
            
            for _, row in confhd.usinas.iterrows():
                nome_usina = str(row.get('nome_usina', '')).strip()
                posto = int(row.get('posto', 0))
                codigo = int(row.get('codigo_usina', 0))
                
                if nome_usina and posto > 0:
                    nome_upper = nome_usina.upper()
                    mapeamento[nome_upper] = posto
                    mapeamento_inverso[posto] = nome_usina  # Guardar nome original
            
            self._mapeamento_usina_posto = mapeamento
            self._mapeamento_posto_usina = mapeamento_inverso
            self._confhd_path = confhd_path
            
            print(f"[TOOL] ✅ Mapeamento carregado: {len(mapeamento)} usinas mapeadas")
            
            return mapeamento
            
        except Exception as e:
            print(f"[TOOL] ⚠️ Erro ao carregar mapeamento: {e}")
            self._mapeamento_usina_posto = {}
            self._mapeamento_posto_usina = {}
            return self._mapeamento_usina_posto
    
    def _buscar_posto_por_query(self, query: str, confhd: Confhd) -> Optional[tuple]:
        """
        Busca o posto de vazões associado a uma usina comparando diretamente com a query.
        Segue o padrão da ClastValoresTool: compara a query diretamente com os nomes das usinas.
        
        Args:
            query: Query do usuário
            confhd: Objeto Confhd já lido
            
        Returns:
            Tupla (posto, nome_usina) ou None se não encontrado
        """
        if confhd.usinas is None or confhd.usinas.empty:
            return None
        
        query_lower = query.lower()
        
        # Palavras comuns a ignorar (artigos, preposições, etc.)
        palavras_ignorar = {'de', 'da', 'do', 'das', 'dos', 'e', 'a', 'o', 'as', 'os', 'em', 'na', 'no', 'nas', 'nos',
                           'vazao', 'vazão', 'vazoes', 'vazões', 'historica', 'histórica', 'posto', 'postos',
                           'afluencia', 'afluência', 'afluencias', 'afluências'}
        
        # Extrair palavras significativas da query (remover palavras comuns)
        palavras_query = [p for p in query_lower.split() if len(p) > 2 and p not in palavras_ignorar]
        
        print(f"[TOOL] Palavras significativas extraídas da query: {palavras_query}")
        
        # Obter usinas únicas (pode haver múltiplas usinas com mesmo posto, mas queremos o posto)
        usinas_unicas = confhd.usinas[['posto', 'nome_usina']].drop_duplicates()
        usinas_unicas = usinas_unicas.sort_values('posto')
        
        print(f"[TOOL] Usinas disponíveis no CONFHD:")
        for _, row in usinas_unicas.iterrows():
            posto = int(row.get('posto', 0))
            nome = str(row.get('nome_usina', '')).strip()
            if posto > 0 and nome:
                print(f"[TOOL]   - Posto {posto}: \"{nome}\"")
        
        # Lista de candidatos com pontuação
        candidatos = []
        
        for _, row in usinas_unicas.iterrows():
            posto = int(row.get('posto', 0))
            nome_usina = str(row.get('nome_usina', '')).strip()
            nome_usina_lower = nome_usina.lower().strip()
            
            if not nome_usina_lower or posto == 0:
                continue
            
            # Extrair palavras significativas do nome da usina
            palavras_nome = [p for p in nome_usina_lower.split() if len(p) > 2 and p not in palavras_ignorar]
            
            # PRIORIDADE 1: Match exato do nome completo na query
            if nome_usina_lower in query_lower:
                print(f"[TOOL] ✅ Posto {posto} encontrado por nome completo '{nome_usina}' na query")
                return (posto, nome_usina)
            
            # PRIORIDADE 2: Match exato de todas as palavras significativas
            if palavras_nome and all(palavra in query_lower for palavra in palavras_nome):
                print(f"[TOOL] ✅ Posto {posto} encontrado: todas as palavras significativas de '{nome_usina}' estão na query")
                return (posto, nome_usina)
            
            # PRIORIDADE 3: Similaridade de string (para matches parciais)
            similarity = SequenceMatcher(None, query_lower, nome_usina_lower).ratio()
            if similarity > 0.6:  # 60% de similaridade
                candidatos.append((posto, nome_usina, similarity, 'similarity'))
            
            # PRIORIDADE 4: Contagem de palavras significativas em comum
            palavras_comuns = set(palavras_query) & set(palavras_nome)
            if palavras_comuns:
                # Requer pelo menos 2 palavras em comum OU uma palavra longa (>= 5 chars)
                palavras_longas = [p for p in palavras_comuns if len(p) >= 5]
                if len(palavras_comuns) >= 2 or (len(palavras_longas) >= 1 and len(palavras_comuns) >= 1):
                    score = len(palavras_comuns) / max(len(palavras_nome), 1)  # Proporção de palavras encontradas
                    candidatos.append((posto, nome_usina, score, 'palavras_comuns'))
        
        # Se encontrou candidatos, retornar o melhor
        if candidatos:
            # Ordenar por tipo de match (similarity primeiro) e depois por score
            candidatos.sort(key=lambda x: (x[3] == 'similarity', x[2]), reverse=True)
            melhor = candidatos[0]
            print(f"[TOOL] ✅ Posto {melhor[0]} encontrado por {melhor[3]} (score: {melhor[2]:.2f}) - '{melhor[1]}'")
            return (melhor[0], melhor[1])
        
        return None
    
    def _extract_posto_from_query(self, query: str) -> Optional[int]:
        """
        Extrai número do posto da query.
        
        Args:
            query: Query do usuário
            
        Returns:
            Número do posto ou None se não encontrado
        """
        query_lower = query.lower()
        
        patterns = [
            r'posto\s*(\d+)',
            r'posto\s*n[úu]mero\s*(\d+)',
            r'posto\s*#?\s*(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query_lower)
            if match:
                try:
                    posto = int(match.group(1))
                    print(f"[TOOL] ✅ Posto {posto} encontrado na query")
                    return posto
                except ValueError:
                    continue
        
        return None
    
    def _extract_usina_name_from_query(self, query: str) -> Optional[str]:
        """
        Tenta extrair nome de usina da query.
        Procura padrões como "vazão de X", "vazões da X", etc.
        Melhorado para ser case-insensitive e capturar mais variações.
        
        Args:
            query: Query do usuário
            
        Returns:
            Nome da usina ou None se não encontrado
        """
        query_lower = query.lower()
        query_original = query  # Manter original para preservar maiúsculas/minúsculas
        
        # Palavras-chave que indicam início de nome de usina
        palavras_ignorar = {'de', 'da', 'do', 'das', 'dos', 'e', 'a', 'o', 'as', 'os', 
                           'em', 'na', 'no', 'nas', 'nos', 'a', 'à', 'ao', 'aos',
                           'vazao', 'vazão', 'vazoes', 'vazões', 'historica', 'histórica',
                           'posto', 'postos', 'fluviometrico', 'fluviométrico', 'em', 'no', 'na'}
        
        # ETAPA 1: Padrões comuns com case-insensitive
        # Padrão 1: "vazão de X", "vazões da X", "vazão histórica de X"
        patterns = [
            # Padrão case-insensitive: "vazao de BALBINA", "vazão de balbina", "vazões da FURNAS"
            r'vaz[aoões]*\s+(?:historica|histórica|do|da|de|das|dos)\s+([A-ZÁÂÊÔÇa-záâêôç][A-ZÁÂÊÔÇa-záâêôç\s]+?)(?:\s|$|historica|histórica|do|da|de|posto|postos|em|no|na|\d)',
            # Padrão mais flexível: "vazao de X em 2015"
            r'vaz[aoões]*\s+(?:de|da|do|das|dos)\s+([A-ZÁÂÊÔÇa-záâêôç][A-ZÁÂÊÔÇa-záâêôç\s]+?)(?:\s+(?:em|no|na|historica|histórica|posto|postos)|\s+\d|$)',
            # Padrão sem preposição: "vazao BALBINA", "vazões ITAIPU"
            r'vaz[aoões]+\s+([A-ZÁÂÊÔÇa-záâêôç][A-ZÁÂÊÔÇa-záâêôç\s]+?)(?:\s+(?:em|no|na|historica|histórica|posto|postos|de|da|do)|\s+\d|$)',
            # Padrão com afluência: "afluência de X", "afluências da X"
            r'aflu[êe]ncia[s]?\s+(?:de|da|do|das|dos)\s+([A-ZÁÂÊÔÇa-záâêôç][A-ZÁÂÊÔÇa-záâêôç\s]+?)(?:\s|$|historica|histórica|em|no|na|\d)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query_original, re.IGNORECASE)
            if match:
                nome = match.group(1).strip()
                
                # Limpar palavras comuns do início e final
                palavras_nome = nome.split()
                
                # Remover do início
                while palavras_nome and palavras_nome[0].lower() in palavras_ignorar:
                    palavras_nome.pop(0)
                
                # Remover do final
                while palavras_nome and palavras_nome[-1].lower() in palavras_ignorar:
                    palavras_nome.pop()
                
                # Remover números do final (anos que podem ter sido capturados)
                while palavras_nome and palavras_nome[-1].isdigit():
                    palavras_nome.pop()
                
                if palavras_nome:
                    nome_limpo = ' '.join(palavras_nome)
                    # Capitalizar primeira letra de cada palavra para padronizar
                    nome_limpo = ' '.join(palavra.capitalize() for palavra in nome_limpo.split())
                    print(f"[TOOL] ✅ Nome de usina extraído (padrão): '{nome_limpo}'")
                    return nome_limpo
        
        # ETAPA 2: Buscar por palavras-chave conhecidas de usinas
        # Lista expandida de usinas comuns
        usinas_comuns = [
            'ITAIPU', 'FURNAS', 'TUCURUI', 'SOBRADINHO', 'ITAPARICA',
            'PAULO AFONSO', 'XINGO', 'SERRA DA MESA', 'EMBORCACAO', 'NOVA PONTE',
            'BALBINA', 'SAMUEL', 'CURUA-UNA', 'COARACY NUNES', 'PONTE DE PEDRA',
            'SALTO OSORIO', 'SALTO SANTIAGO', 'FOZ DO AREIA', 'SEGREDO', 'JORDÃO',
            'ERNESTINA', 'PASSO FUNDO', 'MONJOLINHO', 'ITAUBA', 'MACHADINHO',
            'BARRA GRANDE', 'CAMPOS NOVOS', 'ITAPEBI', 'ESTREITO', 'FUNIL',
            'PEDRA DO CAVALO', 'MOXOTO'
        ]
        
        query_upper = query.upper()
        # Buscar por substring (não apenas match exato)
        for usina in usinas_comuns:
            if usina in query_upper:
                print(f"[TOOL] ✅ Usina conhecida detectada: '{usina}'")
                return usina
        
        # ETAPA 3: Tentar extrair sequência de palavras que pareça nome de usina
        # Procurar por sequências de 1-4 palavras que começam com maiúscula
        # e não são palavras comuns
        palavras_query = query_original.split()
        candidatos = []
        
        for i in range(len(palavras_query)):
            # Tentar sequências de 1 a 4 palavras
            for tamanho in range(1, min(5, len(palavras_query) - i + 1)):
                sequencia = palavras_query[i:i+tamanho]
                sequencia_str = ' '.join(sequencia)
                sequencia_lower = sequencia_str.lower()
                
                # Verificar se não é apenas palavras comuns
                if sequencia_lower in palavras_ignorar:
                    continue
                
                # Verificar se contém pelo menos uma palavra com mais de 3 caracteres
                palavras_significativas = [p for p in sequencia if len(p) > 3]
                if not palavras_significativas:
                    continue
                
                # Verificar se a primeira palavra começa com maiúscula ou é toda maiúscula
                primeira_palavra = sequencia[0]
                if primeira_palavra[0].isupper() or primeira_palavra.isupper():
                    # Verificar se não é um número ou ano
                    if not primeira_palavra.isdigit():
                        # Verificar se não está muito próximo de palavras-chave de vazão
                        idx_inicio = i
                        idx_fim = i + tamanho
                        contexto_antes = ' '.join(palavras_query[max(0, idx_inicio-2):idx_inicio]).lower()
                        contexto_depois = ' '.join(palavras_query[idx_fim:min(len(palavras_query), idx_fim+2)]).lower()
                        
                        # Se está próximo de palavras de vazão, é um candidato forte
                        if any(kw in contexto_antes for kw in ['vazao', 'vazão', 'vazoes', 'vazões', 'afluencia', 'afluência', 'de', 'da', 'do']):
                            candidatos.append((sequencia_str, tamanho))
        
        # Ordenar candidatos por tamanho (maior primeiro) e posição (mais próximo de "vazão" primeiro)
        if candidatos:
            # Pegar o candidato mais longo
            melhor_candidato = max(candidatos, key=lambda x: (x[1], -query_original.find(x[0])))
            nome_limpo = melhor_candidato[0]
            # Capitalizar
            nome_limpo = ' '.join(palavra.capitalize() for palavra in nome_limpo.split())
            print(f"[TOOL] ✅ Nome de usina extraído (sequência): '{nome_limpo}'")
            return nome_limpo
        
        return None
    
    def _extract_ano_from_query(self, query: str) -> Optional[int]:
        """
        Extrai ano da query (ex: "em 2023", "de 2023", "ano 2023").
        
        Args:
            query: Query do usuário
            
        Returns:
            Ano extraído ou None se não encontrado
        """
        query_lower = query.lower()
        
        patterns = [
            r'\b(?:em|do|de|no|na|ano)\s+(\d{4})\b',
            r'\b(\d{4})\b',  # Qualquer 4 dígitos (menos específico)
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query_lower)
            if match:
                try:
                    ano = int(match.group(1))
                    # Validar que é um ano razoável (1900-2100)
                    if 1900 <= ano <= 2100:
                        print(f"[TOOL] ✅ Ano {ano} extraído da query")
                        return ano
                except ValueError:
                    continue
        
        return None
    
    def _ano_para_indice(self, ano: int, ano_inicial: int) -> Optional[int]:
        """
        Converte um ano para o índice correspondente no DataFrame.
        
        Args:
            ano: Ano a ser convertido
            ano_inicial: Ano inicial do histórico
            
        Returns:
            Índice (0-based) ou None se o ano estiver fora do range
        """
        if ano < ano_inicial:
            return None
        
        # Calcular diferença em meses
        meses_diferenca = (ano - ano_inicial) * 12
        
        # O índice pode variar de 0 (janeiro do ano inicial) a N-1
        # Retornar o índice do primeiro mês do ano solicitado (janeiro)
        return meses_diferenca
    
    def _obter_ano_inicial(self) -> Optional[int]:
        """
        Obtém o ano inicial do histórico de vazões.
        Tenta ler do dger.dat (registro 21), se não conseguir usa valor padrão.
        Usa cache se já foi determinado.
        
        Returns:
            Ano inicial ou None
        """
        # Retornar do cache se já foi determinado
        if self._ano_inicial_cache is not None:
            return self._ano_inicial_cache
        
        # Tentar ler do dger.dat
        dger_path = os.path.join(self.deck_path, "DGER.DAT")
        if not os.path.exists(dger_path):
            dger_path = os.path.join(self.deck_path, "dger.dat")
        
        if os.path.exists(dger_path):
            try:
                # Tentar ler diretamente do arquivo (registro 21)
                # O registro 21 é a linha 20 (0-based)
                with open(dger_path, 'r', encoding='latin-1') as f:
                    lines = f.readlines()
                    if len(lines) > 20:
                        reg21 = lines[20].strip()
                        # O ano inicial geralmente está nas colunas 9-12 do registro 21
                        # Tentar extrair valor numérico de 4 dígitos
                        # Procurar por padrão de 4 dígitos que possa ser um ano (1930-2100)
                        anos_match = re.findall(r'\b(19[3-9]\d|20[0-5]\d)\b', reg21)
                        if anos_match:
                            ano = int(anos_match[0])
                            print(f"[TOOL] ✅ Ano inicial encontrado no DGER.DAT: {ano}")
                            self._ano_inicial_cache = ano
                            return ano
            except Exception as e:
                print(f"[TOOL] ⚠️ Erro ao ler DGER.DAT: {e}")
        
        # Valor padrão comum em estudos brasileiros (1931 é muito comum)
        ano_padrao = 1931
        print(f"[TOOL] ⚠️ Usando ano inicial padrão: {ano_padrao}")
        self._ano_inicial_cache = ano_padrao
        return ano_padrao
    
    def _indice_para_data(self, indice: int, ano_inicial: Optional[int] = None) -> Dict[str, Any]:
        """
        Converte índice numérico (0, 1, 2...) em ano e mês.
        
        Args:
            indice: Índice do mês (0 = primeiro mês do histórico)
            ano_inicial: Ano inicial do histórico (se None, tenta obter automaticamente)
            
        Returns:
            Dict com 'ano', 'mes', 'ano_mes', 'mes_nome', 'data_display'
        """
        if ano_inicial is None:
            ano_inicial = self._obter_ano_inicial()
            if ano_inicial is None:
                ano_inicial = 1931  # Fallback
        
        # Calcular ano e mês a partir do índice
        meses_total = indice
        ano = ano_inicial + (meses_total // 12)
        mes = (meses_total % 12) + 1  # Mês de 1 a 12
        
        meses_nomes = {
            1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
            5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
            9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
        }
        
        return {
            'ano': ano,
            'mes': mes,
            'mes_nome': meses_nomes.get(mes, ''),
            'ano_mes': f"{ano}-{mes:02d}",
            'data_display': f"{meses_nomes.get(mes, '')} {ano}"
        }
    
    def execute(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Executa a consulta de vazões históricas.
        
        Fluxo:
        1. Verifica se VAZOES.DAT existe
        2. Lê o arquivo usando inewave
        3. Identifica posto(s) da query (por número ou nome de usina)
        4. Processa e retorna dados
        """
        print(f"[TOOL] {self.get_name()}: Iniciando execução...")
        print(f"[TOOL] Query: {query[:100]}")
        print(f"[TOOL] Deck path: {self.deck_path}")
        
        try:
            # ETAPA 1: Verificar existência do arquivo
            print("[TOOL] ETAPA 1: Verificando existência do arquivo VAZOES.DAT...")
            vazoes_path = os.path.join(self.deck_path, "VAZOES.DAT")
            
            if not os.path.exists(vazoes_path):
                vazoes_path_lower = os.path.join(self.deck_path, "vazoes.dat")
                if os.path.exists(vazoes_path_lower):
                    vazoes_path = vazoes_path_lower
                else:
                    print(f"[TOOL] ❌ Arquivo VAZOES.DAT não encontrado")
                    return {
                        "success": False,
                        "error": f"Arquivo VAZOES.DAT não encontrado em {self.deck_path}",
                        "tool": self.get_name()
                    }
            
            print(f"[TOOL] ✅ Arquivo encontrado: {vazoes_path}")
            
            # ETAPA 2: Ler arquivo usando inewave
            print("[TOOL] ETAPA 2: Lendo arquivo com inewave...")
            vazoes = Vazoes.read(vazoes_path)
            print("[TOOL] ✅ Arquivo lido com sucesso")
            
            # ETAPA 3: Acessar propriedade vazoes
            print("[TOOL] ETAPA 3: Acessando propriedade vazoes...")
            df_vazoes = vazoes.vazoes
            
            if df_vazoes is None or df_vazoes.empty:
                print("[TOOL] ❌ DataFrame vazio ou None")
                return {
                    "success": False,
                    "error": "Dados de vazões não encontrados no arquivo",
                    "tool": self.get_name()
                }
            
            print(f"[TOOL] ✅ DataFrame obtido: {len(df_vazoes)} meses, {len(df_vazoes.columns)} postos")
            
            # ETAPA 4: Identificar posto(s) da query
            print("[TOOL] ETAPA 4: Identificando posto(s) da query...")
            postos_consultados = []
            nome_usina_encontrado = None
            
            # Tentar extrair posto direto
            posto_numero = self._extract_posto_from_query(query)
            if posto_numero is not None:
                if posto_numero in df_vazoes.columns:
                    postos_consultados.append(posto_numero)
                    print(f"[TOOL] ✅ Posto {posto_numero} identificado")
                else:
                    print(f"[TOOL] ⚠️ Posto {posto_numero} não existe no arquivo (postos disponíveis: 1-{len(df_vazoes.columns)})")
            
            # Se não encontrou posto, tentar buscar por nome de usina diretamente na query
            # Seguindo o padrão da ClastValoresTool: comparar query diretamente com CONFHD
            if not postos_consultados:
                # Carregar CONFHD para busca direta
                confhd_path = os.path.join(self.deck_path, "CONFHD.DAT")
                if not os.path.exists(confhd_path):
                    confhd_path = os.path.join(self.deck_path, "confhd.dat")
                
                if os.path.exists(confhd_path):
                    try:
                        confhd = Confhd.read(confhd_path)
                        resultado = self._buscar_posto_por_query(query, confhd)
                        if resultado is not None:
                            posto_encontrado, nome_usina_encontrado = resultado
                            if posto_encontrado in df_vazoes.columns:
                                postos_consultados.append(posto_encontrado)
                                print(f"[TOOL] ✅ Posto {posto_encontrado} encontrado para usina '{nome_usina_encontrado}'")
                            else:
                                print(f"[TOOL] ⚠️ Posto {posto_encontrado} da usina '{nome_usina_encontrado}' não existe no arquivo")
                    except Exception as e:
                        print(f"[TOOL] ⚠️ Erro ao ler CONFHD.DAT para busca: {e}")
                else:
                    print("[TOOL] ⚠️ CONFHD.DAT não encontrado - não é possível buscar por nome de usina")
            
            # ETAPA 5: Extrair ano da query (se houver)
            print("[TOOL] ETAPA 5: Verificando filtro por ano na query...")
            ano_filtro = self._extract_ano_from_query(query)
            ano_inicial = self._obter_ano_inicial()
            indice_inicio = None
            
            # ETAPA 6: Processar dados
            print("[TOOL] ETAPA 6: Processando dados...")
            
            # Se nenhum posto específico foi identificado, retornar todos os postos
            if not postos_consultados:
                print("[TOOL] ⚠️ Nenhum posto específico identificado - retornando todos os postos disponíveis")
                postos_consultados = list(df_vazoes.columns)
                print(f"[TOOL] Total de postos disponíveis: {len(postos_consultados)}")
            
            # Filtrar DataFrame pelos postos consultados
            df_filtrado = df_vazoes[postos_consultados].copy()
            
            # Se há filtro por ano, aplicar filtro nos índices
            if ano_filtro and ano_inicial:
                print(f"[TOOL] Filtro por ano detectado: {ano_filtro}")
                # Calcular índices do ano (12 meses)
                indice_inicio = self._ano_para_indice(ano_filtro, ano_inicial)
                if indice_inicio is not None and indice_inicio < len(df_filtrado):
                    indice_fim = min(indice_inicio + 12, len(df_filtrado))
                    df_filtrado = df_filtrado.iloc[indice_inicio:indice_fim].copy()
                    print(f"[TOOL] ✅ Dados filtrados para o ano {ano_filtro} (índices {indice_inicio}-{indice_fim-1})")
                else:
                    print(f"[TOOL] ⚠️ Ano {ano_filtro} está fora do range do histórico (início: {ano_inicial})")
                    # Retornar erro indicando que o ano não está disponível
                    return {
                        "success": False,
                        "error": f"Ano {ano_filtro} não está disponível no histórico. Histórico disponível desde {ano_inicial}.",
                        "tool": self.get_name(),
                        "ano_solicitado": ano_filtro,
                        "ano_inicial_disponivel": ano_inicial
                    }
            
            # ETAPA 7: Calcular estatísticas
            print("[TOOL] ETAPA 7: Calculando estatísticas...")
            
            stats_por_posto = []
            for posto in postos_consultados:
                serie_posto = df_filtrado[posto]
                
                # Obter nome da usina se disponível
                nome_posto = f"Posto {posto}"
                nome_usina_posto = None
                if self._mapeamento_posto_usina:
                    nome_usina_posto = self._mapeamento_posto_usina.get(posto)
                    if nome_usina_posto:
                        nome_posto = f"{nome_usina_posto} (Posto {posto})"
                
                stats_por_posto.append({
                    'posto': posto,
                    'nome_usina': nome_usina_posto,
                    'nome_display': nome_posto,
                    'total_meses': len(serie_posto[serie_posto.notna()]),
                    'vazao_media': float(serie_posto.mean()) if serie_posto.notna().any() else 0,
                    'vazao_min': float(serie_posto.min()) if serie_posto.notna().any() else 0,
                    'vazao_max': float(serie_posto.max()) if serie_posto.notna().any() else 0,
                    'desvio_padrao': float(serie_posto.std()) if serie_posto.notna().any() else 0,
                    'coeficiente_variacao': float((serie_posto.std() / serie_posto.mean() * 100)) if serie_posto.notna().any() and serie_posto.mean() != 0 else 0,
                })
            
            # ETAPA 8: Formatar resultado
            print("[TOOL] ETAPA 8: Formatando resultado...")
            
            # Ano inicial já foi obtido anteriormente
            if ano_inicial:
                print(f"[TOOL] ✅ Ano inicial do histórico: {ano_inicial}")
            
            # Converter DataFrame para lista de dicts (limitado para não sobrecarregar)
            result_data = []
            
            # Se há apenas 1 posto, retornar série completa
            # Se há múltiplos postos, retornar amostra ou agregações
            if len(postos_consultados) == 1:
                posto = postos_consultados[0]
                serie_posto = df_filtrado[posto]
                
                # Limitar a 500 registros para não exceder tokens
                limite_registros = min(500, len(serie_posto))
                
                for idx in range(limite_registros):
                    if pd.notna(serie_posto.iloc[idx]):
                        # Converter índice para data
                        # Se houve filtro por ano, o idx já é relativo ao df_filtrado, mas precisamos calcular o índice global
                        if ano_filtro and indice_inicio is not None:
                            idx_global = indice_inicio + idx
                        else:
                            idx_global = idx
                        data_info = self._indice_para_data(idx_global, ano_inicial)
                        
                        result_data.append({
                            'mes_indice': int(idx),  # Manter para compatibilidade
                            'ano': data_info['ano'],
                            'mes': data_info['mes'],
                            'mes_nome': data_info['mes_nome'],
                            'ano_mes': data_info['ano_mes'],  # "YYYY-MM"
                            'data_display': data_info['data_display'],  # "Janeiro 1931"
                            'posto': posto,
                            'vazao_m3s': int(serie_posto.iloc[idx])
                        })
                
                if len(serie_posto) > limite_registros:
                    print(f"[TOOL] ⚠️ Série limitada a {limite_registros} primeiros registros (total: {len(serie_posto)})")
            else:
                # Múltiplos postos: retornar apenas estatísticas por posto
                # Não retornar dados mensais para múltiplos postos (apenas stats)
                # Isso evita sobrecarregar a resposta com dados de 320 postos
                print(f"[TOOL] Múltiplos postos detectados ({len(postos_consultados)}) - retornando apenas estatísticas")
            
            # Informações sobre filtros aplicados
            filtro_info = {}
            if len(postos_consultados) == 1:
                filtro_info['posto'] = postos_consultados[0]
                if nome_usina_encontrado:
                    filtro_info['nome_usina'] = nome_usina_encontrado
            elif len(postos_consultados) > 1:
                filtro_info['postos'] = postos_consultados
                if nome_usina_encontrado:
                    filtro_info['nome_usina'] = nome_usina_encontrado
            
            return {
                "success": True,
                "data": result_data,
                "summary": {
                    "total_meses": len(df_vazoes),
                    "total_postos": len(df_vazoes.columns),
                    "postos_consultados": len(postos_consultados),
                    "ano_inicial": ano_inicial,
                    "filtro_aplicado": filtro_info if filtro_info else None
                },
                "stats_por_posto": stats_por_posto,
                "description": "Vazões históricas de postos fluviométricos (m³/s)",
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
                "error": f"Erro ao processar VAZOES.DAT: {str(e)}",
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
        Vazões históricas de postos fluviométricos. Vazões naturais afluentes. Séries históricas de vazões. Afluências históricas.
        
        Queries que ativam esta tool:
        - "vazões históricas do posto 1"
        - "vazão histórica de Itaipu"
        - "vazões da usina Furnas"
        - "vazão do posto 15"
        - "série histórica de vazões"
        - "vazões naturais afluentes"
        - "afluências históricas"
        - "vazão histórica da usina Tucurui"
        - "vazões do posto fluviométrico 42"
        - "histórico de vazões do posto 10"
        - "vazões de Itaipu"
        - "afluência de Furnas"
        - "vazão natural do posto 5"
        - "vazões históricas das usinas"
        
        Termos-chave: vazão, vazões, vazão histórica, vazões históricas, posto fluviométrico, postos fluviométricos, vazão natural, vazões naturais, afluência, afluências, série histórica de vazões, histórico de vazões.
        """

