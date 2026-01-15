"""
Classe para leitura do arquivo restricao-eletrica.csv.
Este arquivo contém restrições elétricas do modelo NEWAVE.
Seguindo o padrão da biblioteca inewave.
"""
import os
import pandas as pd
from typing import Optional, List, Dict
import re


class RestricaoEletrica:
    """
    Classe para ler e processar o arquivo restricao-eletrica.csv.
    
    Segue o padrão da biblioteca inewave:
    - Método de classe read() para leitura
    - Propriedades que retornam DataFrames ou None
    
    O arquivo contém três seções principais:
    1. RE: Fórmulas das restrições elétricas
    2. RE-HORIZ-PER: Períodos de validade das restrições
    3. RE-LIM-FORM-PER-PAT: Limites por período e patamar
    """
    
    # Mapeamento de patamares
    PATAMARES_NOMES = {
        1: "Pesado",
        2: "Médio", 
        3: "Leve"
    }
    
    # Mapeamento direto por código de restrição (cod_rest -> nome)
    MAPEAMENTO_POR_CODIGO = {
        1: "Escoamento Madeira",
        10: "Cachoeira Caldeirão + Ferreira Gomes",
        20: "RSUL",
        21: "FNS",
        22: "FNS + FNESE",
        23: "FNS + FNESE + XINGU",
    }
    
    # Mapeamento de nomes antigos para novos (para compatibilidade com nomes extraídos)
    MAPEAMENTO_NOMES = {
        "Escoamento Madeira": "Escoamento Madeira",  # Mantém
        "Sul-SE": "RSUL",
        "sul-se": "RSUL",  # Variação lowercase
        "Imperatriz - Sudeste": "FNS",
        "imperatriz - sudeste": "FNS",  # Variação lowercase
        "FNS + FNESE": "FNS + FNESE",  # Mantém o mesmo
        "FNS + FNESE + XINGU->SE/CO +": "FNS + FNESE + XINGU",
        "FNS + FNESE + XINGU->SE/CO": "FNS + FNESE + XINGU",  # Caso sem o "+" final
        "Cachoeira Caldeirão + Ferreira Gomes": "Cachoeira Caldeirão + Ferreira Gomes",  # Mantém
    }
    
    def __init__(self, file_path: str):
        """
        Inicializa a classe com o caminho do arquivo.
        
        Args:
            file_path: Caminho completo do arquivo restricao-eletrica.csv
        """
        self.file_path = file_path
        self._restricoes: Optional[pd.DataFrame] = None
        self._horizontes: Optional[pd.DataFrame] = None
        self._limites: Optional[pd.DataFrame] = None
        self._comentarios: List[str] = []
        self._nomes_restricoes: Dict[int, str] = {}  # Mapeamento cod_rest -> nome
        self._nomes_restricoes_inverso: Dict[str, int] = {}  # Mapeamento nome -> cod_rest (para busca)
        
    @classmethod
    def read(cls, file_path: str) -> 'RestricaoEletrica':
        """
        Lê o arquivo restricao-eletrica.csv e retorna uma instância da classe.
        
        Padrão inewave: método de classe que recebe caminho e retorna instância.
        
        Args:
            file_path: Caminho do arquivo CSV
            
        Returns:
            Instância de RestricaoEletrica com dados carregados
            
        Raises:
            FileNotFoundError: Se o arquivo não existir
        """
        instance = cls(file_path)
        instance._parse_file()
        return instance
    
    def _parse_file(self):
        """
        Faz o parse do arquivo CSV, separando as três seções.
        """
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"Arquivo não encontrado: {self.file_path}")
        
        # Listas para armazenar dados de cada seção
        restricoes_data = []
        horizontes_data = []
        limites_data = []
        
        # Variáveis para rastrear contexto (último comentário e próximo código de restrição)
        ultimo_comentario_nome = None
        
        # Tentar diferentes encodings
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        file_handle = None
        
        for encoding in encodings:
            try:
                file_handle = open(self.file_path, 'r', encoding=encoding)
                # Testar se consegue ler uma linha
                file_handle.readline()
                file_handle.seek(0)  # Voltar ao início
                break
            except UnicodeDecodeError:
                if file_handle:
                    file_handle.close()
                file_handle = None
                continue
        
        if file_handle is None:
            raise ValueError(f"Não foi possível ler o arquivo com nenhum encoding conhecido: {encodings}")
        
        try:
            for line in file_handle:
                line = line.strip()
                
                # Ignorar linhas vazias
                if not line:
                    continue
                
                # Capturar comentários (linhas que começam com &)
                if line.startswith('&'):
                    # Verificar se é uma linha de dados comentada (RE-LIM-FORM-PER-PAT comentada)
                    if 'RE-LIM-FORM-PER-PAT' in line:
                        # Processar como seção RE-LIM-FORM-PER-PAT (será tratado abaixo)
                        linha_processar = line.lstrip('&').strip()
                        limite = self._parse_limite_line(linha_processar)
                        if limite:
                            cod_rest = limite['cod_rest']
                            # Aplicar mapeamento por código primeiro, senão usar nome extraído
                            if cod_rest not in self._nomes_restricoes:
                                nome_final = self._obter_nome_restricao(cod_rest, ultimo_comentario_nome)
                                if nome_final:
                                    self._nomes_restricoes[cod_rest] = nome_final
                                    self._nomes_restricoes_inverso[nome_final.lower()] = cod_rest
                        # Não adicionar aos limites pois está comentada
                        continue
                    
                    # Comentários que não são cabeçalhos de seção
                    # Verificar se é um comentário de nome (antes de RE-LIM-FORM-PER-PAT)
                    if not any(keyword in line for keyword in ['RE;', 'RE ', 'RE-HORIZ-PER', 'RE-LIM-FORM-PER-PAT']):
                        self._comentarios.append(line)
                        # Extrair nome da restrição do comentário
                        nome_extraido = self._extrair_nome_restricao(line)
                        if nome_extraido:
                            ultimo_comentario_nome = nome_extraido
                    continue
                
                # Detectar e parsear seção RE
                if line.startswith('RE ;') or line.startswith('RE;'):
                    restricao = self._parse_restricao_line(line)
                    if restricao:
                        cod_rest = restricao['cod_rest']
                        # Aplicar mapeamento por código primeiro, senão usar nome extraído
                        if cod_rest not in self._nomes_restricoes:
                            nome_final = self._obter_nome_restricao(cod_rest, ultimo_comentario_nome)
                            if nome_final:
                                self._nomes_restricoes[cod_rest] = nome_final
                                self._nomes_restricoes_inverso[nome_final.lower()] = cod_rest
                            # Não limpar ultimo_comentario_nome aqui, pois pode haver múltiplos registros da mesma restrição
                        restricoes_data.append(restricao)
                
                # Detectar e parsear seção RE-HORIZ-PER
                elif 'RE-HORIZ-PER' in line:
                    horizonte = self._parse_horizonte_line(line)
                    if horizonte:
                        horizontes_data.append(horizonte)
                
                # Detectar e parsear seção RE-LIM-FORM-PER-PAT (incluindo linhas comentadas)
                elif 'RE-LIM-FORM-PER-PAT' in line:
                    # Processar mesmo se estiver comentada (começa com &)
                    linha_processar = line.lstrip('&').strip() if line.startswith('&') else line
                    limite = self._parse_limite_line(linha_processar)
                    if limite:
                        cod_rest = limite['cod_rest']
                        # Aplicar mapeamento por código primeiro, senão usar nome extraído
                        if cod_rest not in self._nomes_restricoes:
                            nome_final = self._obter_nome_restricao(cod_rest, ultimo_comentario_nome)
                            if nome_final:
                                self._nomes_restricoes[cod_rest] = nome_final
                                self._nomes_restricoes_inverso[nome_final.lower()] = cod_rest
                            # Não limpar ultimo_comentario_nome aqui, pois pode haver múltiplos registros da mesma restrição
                        # Só adicionar aos limites se não estiver comentada
                        if not line.startswith('&'):
                            limites_data.append(limite)
        finally:
            file_handle.close()
        
        # Criar DataFrames (seguindo padrão inewave: retornar None se vazio)
        if restricoes_data:
            self._restricoes = pd.DataFrame(restricoes_data)
        else:
            self._restricoes = None
        
        if horizontes_data:
            self._horizontes = pd.DataFrame(horizontes_data)
        else:
            self._horizontes = None
        
        if limites_data:
            self._limites = pd.DataFrame(limites_data)
        else:
            self._limites = None
    
    def _parse_restricao_line(self, line: str) -> Optional[dict]:
        """
        Parseia uma linha da seção RE.
        
        Formato: RE ; cod_rest; formula
        """
        # Remover prefixo "RE ;" ou "RE;"
        line = re.sub(r'^RE\s*;?\s*', '', line)
        
        # Dividir por ponto e vírgula
        parts = [p.strip() for p in line.split(';')]
        
        if len(parts) < 2:
            return None
        
        try:
            cod_rest = int(parts[0])
            formula = parts[1] if len(parts) > 1 else ''
            
            return {
                'cod_rest': cod_rest,
                'formula': formula
            }
        except (ValueError, IndexError):
            return None
    
    def _parse_horizonte_line(self, line: str) -> Optional[dict]:
        """
        Parseia uma linha da seção RE-HORIZ-PER.
        
        Formato: RE-HORIZ-PER ; cod_rest; PerIni; PerFin
        """
        # Remover prefixo
        line = re.sub(r'^.*?RE-HORIZ-PER\s*;?\s*', '', line)
        
        # Dividir por ponto e vírgula
        parts = [p.strip() for p in line.split(';')]
        
        if len(parts) < 3:
            return None
        
        try:
            cod_rest = int(parts[0])
            per_ini = parts[1]
            per_fin = parts[2]
            
            return {
                'cod_rest': cod_rest,
                'per_ini': per_ini,
                'per_fin': per_fin
            }
        except (ValueError, IndexError):
            return None
    
    def _obter_nome_restricao(self, cod_rest: int, nome_extraido: Optional[str] = None) -> Optional[str]:
        """
        Obtém o nome da restrição aplicando mapeamento por código primeiro.
        
        Args:
            cod_rest: Código da restrição
            nome_extraido: Nome extraído do comentário (opcional)
            
        Returns:
            Nome da restrição (mapeado por código ou extraído) ou None
        """
        # Prioridade 1: Mapeamento direto por código
        if cod_rest in self.MAPEAMENTO_POR_CODIGO:
            return self.MAPEAMENTO_POR_CODIGO[cod_rest]
        
        # Prioridade 2: Nome extraído (já mapeado)
        if nome_extraido:
            return nome_extraido
        
        return None
    
    def _aplicar_mapeamento_nome(self, nome: str) -> str:
        """
        Aplica o mapeamento de nomes antigos para novos.
        
        Args:
            nome: Nome extraído do comentário
            
        Returns:
            Nome mapeado ou o nome original se não houver mapeamento
        """
        # Normalizar nome (remover espaços extras e normalizar "+" no final)
        nome_normalizado = nome.strip()
        # Remover "+" no final se houver (com espaços)
        nome_normalizado = re.sub(r'\s*\+\s*$', '', nome_normalizado).strip()
        
        # Aplicar mapeamento se existir (exato)
        if nome_normalizado in self.MAPEAMENTO_NOMES:
            return self.MAPEAMENTO_NOMES[nome_normalizado]
        
        # Verificar variações case-insensitive
        nome_lower = nome_normalizado.lower()
        for nome_antigo, nome_novo in self.MAPEAMENTO_NOMES.items():
            if nome_lower == nome_antigo.lower():
                return nome_novo
        
        # Verificar se contém algum dos nomes antigos (busca parcial)
        for nome_antigo, nome_novo in self.MAPEAMENTO_NOMES.items():
            if nome_antigo.lower() in nome_lower or nome_lower in nome_antigo.lower():
                return nome_novo
        
        return nome_normalizado
    
    def _extrair_nome_restricao(self, comentario: str) -> Optional[str]:
        """
        Extrai o nome da restrição de um comentário.
        MELHORADO para capturar melhor os nomes dos comentários.
        Aplica mapeamento de nomes após extração.
        
        Args:
            comentario: Linha de comentário (começa com &)
            
        Returns:
            Nome da restrição (mapeado) ou None
        """
        # Remover o & inicial
        comentario_original = comentario.lstrip('&').strip()
        comentario = comentario_original
        comentario_lower = comentario.lower()
        
        # Ignorar comentários genéricos
        if 'tratamento realizado' in comentario_lower:
            return None
        
        nome_extraido = None
        
        # Caso 1: "Escoamento Madeira" (nome direto, sem prefixo)
        # Verificar se parece um nome simples (contém apenas letras, espaços, hífens, +, números)
        if not any(palavra in comentario_lower for palavra in ['limite', 'restricao', 'restrição', 'valores', '=']):
            # Verificar se parece um nome (contém principalmente letras, espaços, hífens, +)
            if re.match(r'^[A-Za-zÀ-ÿ\s\-\+0-9]+$', comentario) and len(comentario) > 3:
                nome_extraido = comentario.strip()
        
        # Caso 2: "Restricao de geracao Cachoeira Caldeirão + Ferreira Gomes"
        if nome_extraido is None and ('restricao de geracao' in comentario_lower or 'restrição de geração' in comentario_lower):
            # Extrair parte após "de geracao" ou "de geração"
            match = re.search(r'(?:restricao|restrição)\s+de\s+(?:geracao|geração)\s+(.+)', comentario_lower, re.IGNORECASE)
            if match:
                nome_extraido = match.group(1).strip()
            else:
                # Alternativa: buscar diretamente após "de geracao"
                partes = re.split(r'de\s+geracao|de\s+geração', comentario_lower, flags=re.IGNORECASE)
                if len(partes) > 1:
                    nome = partes[1].strip()
                    if nome and len(nome) > 3:
                        nome_extraido = nome.title()
        
        # Caso 3: "Limite Sul-SE = Min..." -> extrair "Sul-SE"
        # Caso 4: "Limite Imperatriz - Sudeste = ..." -> extrair "Imperatriz - Sudeste"
        # Caso 5: "Limite FNS + FNESE = ..." -> extrair "FNS + FNESE"
        if nome_extraido is None and 'limite' in comentario_lower:
            # Tentar extrair nome após "Limite"
            match = re.search(r'limite\s+([^=]+)', comentario_lower, re.IGNORECASE)
            if match:
                nome = match.group(1).strip()
                # Remover "= ..." se houver
                nome = re.sub(r'\s*=.*$', '', nome).strip()
                # Remover sufixos como "- valores de RSE:" ou "- valores do FNS:"
                nome = re.sub(r'\s*-\s*valores\s+(?:de|do)\s+[^:]+:?\s*$', '', nome, flags=re.IGNORECASE).strip()
                if nome and len(nome) > 2:
                    nome_extraido = nome.title()
        
        # Aplicar mapeamento se nome foi extraído
        if nome_extraido:
            return self._aplicar_mapeamento_nome(nome_extraido)
        
        return None
    
    def _parse_limite_line(self, line: str) -> Optional[dict]:
        """
        Parseia uma linha da seção RE-LIM-FORM-PER-PAT.
        
        Formato: RE-LIM-FORM-PER-PAT ; cod_rest; PerIni; PerFin; Pat; LimInf; LimSup
        """
        # Remover prefixo
        line = re.sub(r'^.*?RE-LIM-FORM-PER-PAT\s*;?\s*', '', line)
        
        # Dividir por ponto e vírgula
        parts = [p.strip() for p in line.split(';')]
        
        if len(parts) < 6:
            return None
        
        try:
            cod_rest = int(parts[0])
            per_ini = parts[1]
            per_fin = parts[2]
            pat = int(parts[3])
            lim_inf = float(parts[4])
            lim_sup = float(parts[5])
            
            return {
                'cod_rest': cod_rest,
                'per_ini': per_ini,
                'per_fin': per_fin,
                'patamar': pat,  # Renomeado de 'pat' para 'patamar' para evitar confusão com "Patrimônio"
                'lim_inf': lim_inf,
                'lim_sup': lim_sup
            }
        except (ValueError, IndexError):
            return None
    
    @property
    def restricoes(self) -> Optional[pd.DataFrame]:
        """
        Retorna DataFrame com as fórmulas das restrições elétricas.
        
        Padrão inewave: propriedade que retorna DataFrame ou None.
        
        Returns:
            DataFrame com colunas:
            - cod_rest (int): Código da restrição
            - formula (str): Fórmula da restrição
            None se não houver dados
        """
        return self._restricoes
    
    @property
    def horizontes(self) -> Optional[pd.DataFrame]:
        """
        Retorna DataFrame com os períodos de validade das restrições.
        
        Padrão inewave: propriedade que retorna DataFrame ou None.
        
        Returns:
            DataFrame com colunas:
            - cod_rest (int): Código da restrição
            - per_ini (str): Período inicial (formato: YYYY/MM)
            - per_fin (str): Período final (formato: YYYY/MM)
            None se não houver dados
        """
        return self._horizontes
    
    @property
    def nomes_restricoes(self) -> pd.DataFrame:
        """
        Retorna DataFrame com código e nome de cada restrição.
        
        Returns:
            DataFrame com colunas:
            - cod_rest (int): Código da restrição
            - nome (str): Nome da restrição
        """
        if not self._nomes_restricoes:
            return pd.DataFrame(columns=['cod_rest', 'nome'])
        
        dados = [{'cod_rest': cod, 'nome': nome} for cod, nome in self._nomes_restricoes.items()]
        return pd.DataFrame(dados).sort_values('cod_rest')
    
    @staticmethod
    def get_nome_patamar(patamar: int) -> str:
        """
        Retorna o nome do patamar baseado no número.
        
        Args:
            patamar: Número do patamar (1, 2, 3)
            
        Returns:
            Nome do patamar: "Pesado", "Médio" ou "Leve"
        """
        return RestricaoEletrica.PATAMARES_NOMES.get(patamar, f"Patamar {patamar}")
    
    def buscar_por_nome(self, nome_query: str) -> Optional[int]:
        """
        Busca código da restrição por nome (busca flexível).
        
        Args:
            nome_query: Nome ou parte do nome da restrição (ex: "madeira", "escoamento madeira")
            
        Returns:
            Código da restrição ou None se não encontrado
        """
        nome_query_lower = nome_query.lower().strip()
        
        # Busca exata
        if nome_query_lower in self._nomes_restricoes_inverso:
            return self._nomes_restricoes_inverso[nome_query_lower]
        
        # Busca parcial (nome contém a query)
        for nome, cod_rest in self._nomes_restricoes_inverso.items():
            if nome_query_lower in nome:
                return cod_rest
        
        # Busca por palavras-chave
        palavras_query = [p for p in nome_query_lower.split() if len(p) > 2]
        for nome, cod_rest in self._nomes_restricoes_inverso.items():
            palavras_nome = [p for p in nome.split() if len(p) > 2]
            # Se todas as palavras principais da query estão no nome
            if palavras_query and all(any(pq in pn for pn in palavras_nome) for pq in palavras_query):
                return cod_rest
        
        return None
    
    @property
    def limites(self) -> Optional[pd.DataFrame]:
        """
        Retorna DataFrame com os limites por período e patamar.
        INCLUI coluna adicional 'nome_patamar' com o nome do patamar.
        
        Padrão inewave: propriedade que retorna DataFrame ou None.
        
        Returns:
            DataFrame com colunas:
            - cod_rest (int): Código da restrição
            - per_ini (str): Período inicial (formato: YYYY/MM)
            - per_fin (str): Período final (formato: YYYY/MM)
            - patamar (int): Patamar (1, 2, 3, ...)
            - nome_patamar (str): Nome do patamar ("Pesado", "Médio", "Leve")
            - lim_inf (float): Limite inferior
            - lim_sup (float): Limite superior
            None se não houver dados
        """
        if self._limites is None:
            return None
        
        # Criar cópia para não modificar o original
        df = self._limites.copy()
        
        # Adicionar coluna com nome do patamar
        df['nome_patamar'] = df['patamar'].apply(self.get_nome_patamar)
        
        return df

