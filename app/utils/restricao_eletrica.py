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
        proximo_cod_rest = None
        
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
                            # Associar nome se houver comentário anterior
                            if ultimo_comentario_nome and cod_rest not in self._nomes_restricoes:
                                self._nomes_restricoes[cod_rest] = ultimo_comentario_nome
                        # Não adicionar aos limites pois está comentada
                        continue
                    
                    # Comentários que não são cabeçalhos de seção
                    if not any(keyword in line for keyword in ['RE;', 'RE ', 'RE-HORIZ-PER']):
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
                        # Associar nome se houver comentário anterior
                        if ultimo_comentario_nome and cod_rest not in self._nomes_restricoes:
                            self._nomes_restricoes[cod_rest] = ultimo_comentario_nome
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
                        # Associar nome se houver comentário anterior (mesmo que haja outros comentários no meio)
                        if ultimo_comentario_nome and cod_rest not in self._nomes_restricoes:
                            self._nomes_restricoes[cod_rest] = ultimo_comentario_nome
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
    
    def _extrair_nome_restricao(self, comentario: str) -> Optional[str]:
        """
        Extrai o nome da restrição de um comentário.
        
        Args:
            comentario: Linha de comentário (começa com &)
            
        Returns:
            Nome da restrição ou None
        """
        # Remover o & inicial
        comentario_original = comentario.lstrip('&').strip()
        comentario = comentario_original
        comentario_lower = comentario.lower()
        
        # Ignorar comentários genéricos
        if 'tratamento realizado' in comentario_lower:
            return None
        
        # Caso 1: "Restricao de geracao Cachoeira Caldeirão + Ferreira Gomes"
        if 'restricao de geracao' in comentario_lower or 'restrição de geração' in comentario_lower or 'restricao de geracao' in comentario_lower:
            # Extrair parte após "de geracao" ou "de geração"
            match = re.search(r'(?:restricao|restrição)\s+de\s+(?:geracao|geração)\s+(.+)', comentario_lower, re.IGNORECASE)
            if match:
                nome = match.group(1).strip()
                return nome.title()
            # Alternativa: buscar diretamente após "de geracao"
            partes = re.split(r'de\s+geracao|de\s+geração', comentario_lower, flags=re.IGNORECASE)
            if len(partes) > 1:
                nome = partes[1].strip()
                if nome and len(nome) > 3:
                    return nome.title()
        
        # Caso 2: "Escoamento Madeira" (nome direto, sem prefixo)
        if not any(palavra in comentario_lower for palavra in ['limite', 'restricao', 'restrição', 'valores']):
            # Verificar se parece um nome (contém apenas letras, espaços, hífens, +)
            if re.match(r'^[A-Za-zÀ-ÿ\s\-\+]+$', comentario) and len(comentario) > 3:
                return comentario.strip()
        
        # Caso 3: "Limite Sul-SE = Min..." -> extrair "Sul-SE"
        # Caso 4: "Limite Imperatriz - Sudeste = ..." -> extrair "Imperatriz - Sudeste"
        # Caso 5: "Limite FNS + FNESE = ..." -> extrair "FNS + FNESE"
        if 'limite' in comentario_lower:
            # Tentar extrair nome após "Limite"
            match = re.search(r'limite\s+([^=]+)', comentario_lower, re.IGNORECASE)
            if match:
                nome = match.group(1).strip()
                # Remover "= ..." se houver
                nome = re.sub(r'\s*=.*$', '', nome).strip()
                # Remover sufixos como "- valores de RSE:" ou "- valores do FNS:"
                nome = re.sub(r'\s*-\s*valores\s+(?:de|do)\s+[^:]+:?\s*$', '', nome, flags=re.IGNORECASE).strip()
                if nome and len(nome) > 2:
                    return nome.title()
        
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
                'pat': pat,
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
    
    @property
    def limites(self) -> Optional[pd.DataFrame]:
        """
        Retorna DataFrame com os limites por período e patamar.
        
        Padrão inewave: propriedade que retorna DataFrame ou None.
        
        Returns:
            DataFrame com colunas:
            - cod_rest (int): Código da restrição
            - per_ini (str): Período inicial (formato: YYYY/MM)
            - per_fin (str): Período final (formato: YYYY/MM)
            - pat (int): Patamar (1, 2, 3, ...)
            - lim_inf (float): Limite inferior
            - lim_sup (float): Limite superior
            None se não houver dados
        """
        return self._limites

