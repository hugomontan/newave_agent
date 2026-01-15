"""
Tool para consultar cadastro de usinas termoelétricas do TERM.DAT.
Acessa dados estruturais e operacionais básicos das usinas térmicas.
"""
from newave_agent.app.tools.base import NEWAVETool
import os
import pandas as pd
import re
from typing import Dict, Any, Optional
from difflib import SequenceMatcher


class TermCadastroTool(NEWAVETool):
    """
    Tool para consultar cadastro de usinas termoelétricas do TERM.DAT.
    
    Dados disponíveis (baseado no formato do arquivo):
    - Código da usina (NUM)
    - Nome da usina (NOME)
    - Potência efetiva (POT) - MW
    - Fator de capacidade máximo (FCMX) - %
    - Taxa equivalente de indisponibilidade forçada (TEIF) - %
    - Indisponibilidade programada (IP) - %
    - Geração mínima mensal do primeiro ano (GTMIN) - 12 valores (JAN a DEZ) - MW
    - Geração mínima para anos seguintes (D+ ANOS) - 2 valores - MW
    """
    
    def get_name(self) -> str:
        return "TermCadastroTool"
    
    def can_handle(self, query: str) -> bool:
        """
        Verifica se a query é sobre cadastro de usinas termoelétricas do TERM.DAT.
        
        Args:
            query: Query do usuário
            
        Returns:
            True se a tool pode processar a query
        """
        query_lower = query.lower()
        keywords = [
            "term.dat",
            "term dat",
            "cadastro térmica",
            "cadastro termica",
            "cadastro termelétrica",
            "cadastro termoeletrica",
            "informações da usina térmica",
            "informacoes da usina termica",
            "dados da usina térmica",
            "dados da usina termica",
            "cadastro da usina térmica",
            "cadastro da usina termica",
            "informações cadastrais térmica",
            "informacoes cadastrais termica",
            "dados cadastrais térmica",
            "características da usina térmica",
            "caracteristicas da usina termica",
            "dados estruturais térmica",
            "potência efetiva térmica",
            "potencia efetiva termica",
            "fator capacidade máximo",
            "fator capacidade maximo",
            "indisponibilidade forçada",
            "indisponibilidade forcada",
            "indisponibilidade programada",
            "geração mínima térmica",
            "geracao minima termica",
            "gtmin térmica",
            "gtmin termica",
            "potef térmica",
            "potef termica",
            "fcmax térmica",
            "fcmax termica",
            "teif",
            "ip térmica",
            "ip termica",
        ]
        return any(kw in query_lower for kw in keywords)
    
    def _extract_usina_from_query(self, query: str, term_data: pd.DataFrame) -> Optional[int]:
        """
        Extrai código da usina da query usando matching inteligente.
        Busca por número ou nome da usina.
        
        Args:
            query: Query do usuário
            term_data: DataFrame com dados do TERM.DAT
            
        Returns:
            Código da usina ou None se não encontrado
        """
        query_lower = query.lower()
        
        # ETAPA 1: Tentar extrair número explícito
        patterns = [
            r'usina\s*(\d+)',
            r'usina\s*térmica\s*(\d+)',
            r'usina\s*termica\s*(\d+)',
            r'usina\s*#?\s*(\d+)',
            r'código\s*(\d+)',
            r'codigo\s*(\d+)',
            r'térmica\s*(\d+)',
            r'termica\s*(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query_lower)
            if match:
                try:
                    codigo = int(match.group(1))
                    if 'codigo_usina' in term_data.columns:
                        if codigo in term_data['codigo_usina'].values:
                            print(f"[TOOL] ✅ Código {codigo} encontrado por padrão numérico")
                            return codigo
                except ValueError:
                    continue
        
        # ETAPA 2: Buscar por nome da usina
        if 'nome_usina' in term_data.columns:
            palavras_ignorar = {
                'de', 'da', 'do', 'das', 'dos', 'e', 'a', 'o', 'as', 'os',
                'em', 'na', 'no', 'nas', 'nos', 'a', 'à', 'ao', 'aos',
                'informacoes', 'informações', 'dados', 'usina', 'térmica', 'termica',
                'cadastro', 'características', 'caracteristicas'
            }
            
            palavras_query = [p for p in query_lower.split() 
                            if len(p) > 2 and p not in palavras_ignorar]
            
            if not palavras_query:
                return None
            
            candidatos = []
            for _, row in term_data.iterrows():
                codigo = row.get('codigo_usina')
                nome = str(row.get('nome_usina', '')).strip().lower()
                
                if not nome:
                    continue
                
                palavras_nome = [p for p in nome.split() 
                               if len(p) > 2 and p not in palavras_ignorar]
                
                palavras_comuns = set(palavras_query) & set(palavras_nome)
                score = len(palavras_comuns)
                
                # Bonus se todas as palavras significativas da query estão no nome
                if palavras_query and all(p in palavras_nome for p in palavras_query):
                    score += 10
                
                # Bonus por similaridade de strings
                similarity = SequenceMatcher(None, query_lower, nome).ratio()
                score += similarity * 5
                
                if score > 0:
                    candidatos.append((codigo, nome, score))
            
            if candidatos:
                candidatos.sort(key=lambda x: x[2], reverse=True)
                melhor_codigo, melhor_nome, melhor_score = candidatos[0]
                print(f"[TOOL] ✅ Código {melhor_codigo} encontrado: '{melhor_nome}' (score: {melhor_score:.2f})")
                return melhor_codigo
        
        return None
    
    def _read_term_file(self, term_path: str) -> Optional[pd.DataFrame]:
        """
        Lê o arquivo TERM.DAT e retorna DataFrame.
        
        Estrutura esperada (baseado no snippet):
        NUM NOME          POT  FCMX    TEIF   IP    JAN.XX FEV.XX ... DEZ.XX XXX.XX XXX.XX
        
        Formato fixo:
        - NUM: colunas 1-5 (código da usina)
        - NOME: colunas 6-18 (nome da usina, 12 caracteres)
        - POT: colunas 19-24 (potência efetiva)
        - FCMX: colunas 25-29 (fator de capacidade máximo)
        - TEIF: colunas 30-36 (taxa equivalente de indisponibilidade forçada)
        - IP: colunas 37-43 (indisponibilidade programada)
        - GTMIN mensal: 12 valores (JAN a DEZ) - colunas 44-115 (6 chars cada)
        - D+ ANOS: 2 valores - colunas 116-127 (6 chars cada)
        
        Args:
            term_path: Caminho do arquivo TERM.DAT
            
        Returns:
            DataFrame com dados ou None se erro
        """
        try:
            print(f"[TOOL] Lendo arquivo TERM.DAT: {term_path}")
            
            # Ler como texto fixo
            with open(term_path, 'r', encoding='latin-1') as f:
                lines = f.readlines()
            
            # Pular linhas de cabeçalho/comentários
            data_lines = []
            header_found = False
            for line in lines:
                line_stripped = line.strip()
                if not line_stripped:
                    continue
                
                # Detectar linha de cabeçalho
                if 'NUM' in line_stripped and 'NOME' in line_stripped:
                    header_found = True
                    continue
                
                # Pular linhas de separador
                if line_stripped.startswith('---') or line_stripped.startswith('==='):
                    continue
                
                # Se já passou o cabeçalho, processar linhas de dados
                if header_found:
                    # Verificar se é linha de dados (começa com número)
                    if re.match(r'^\s*\d+', line_stripped):
                        data_lines.append(line)
            
            if not data_lines:
                print("[TOOL] ⚠️ Nenhuma linha de dados encontrada após o cabeçalho")
                # Tentar ler todas as linhas que começam com número
                for line in lines:
                    line_stripped = line.strip()
                    if re.match(r'^\s*\d+', line_stripped):
                        data_lines.append(line)
            
            if not data_lines:
                print("[TOOL] ❌ Nenhuma linha de dados encontrada")
                return None
            
            print(f"[TOOL] ✅ {len(data_lines)} linhas de dados encontradas")
            
            # Parsear linhas
            records = []
            meses = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 
                    'jul', 'ago', 'set', 'out', 'nov', 'dez']
            
            for line_idx, line in enumerate(data_lines):
                # Garantir que a linha tenha tamanho mínimo
                if len(line) < 44:
                    print(f"[TOOL] ⚠️ Linha {line_idx + 1} muito curta, pulando")
                    continue
                
                try:
                    # Parsear campos usando abordagem flexível para lidar com espaçamento variável
                    # Exemplo: "   1 ANGRA 1        640. 100.    2.19  10.38   0.00   0.00..."
                    
                    # Função auxiliar para converter string para float de forma segura
                    def safe_float(s):
                        if not s or not s.strip():
                            return 0.0
                        s_clean = s.strip().rstrip('.')
                        try:
                            return float(s_clean)
                        except ValueError:
                            return 0.0
                    
                    # ETAPA 1: Extrair código (primeiro número na linha)
                    match = re.match(r'^\s*(\d+)', line)
                    if not match:
                        continue
                    codigo = int(match.group(1))
                    
                    # ETAPA 2: Remover código do início e processar resto da linha
                    line_after_code = line[match.end():].strip()
                    
                    # ETAPA 3: Encontrar onde termina o nome da usina
                    # O nome pode conter números (ex: "ANGRA 1"), então precisamos ser mais cuidadosos
                    # A potência (POT) geralmente é um número grande (>= 100), então vamos procurar por isso
                    # Estratégia: encontrar o primeiro número >= 100 que indica início da potência
                    
                    # Dividir a linha após o código em palavras
                    words = line_after_code.split()
                    
                    # Procurar pela primeira palavra que é um número >= 100 (potência)
                    # Ou que contém um número grande seguido de ponto
                    numeric_start_idx = -1
                    
                    for i, word in enumerate(words):
                        # Remover ponto final se existir
                        word_clean = word.rstrip('.')
                        # Tentar converter para float
                        try:
                            value = float(word_clean)
                            # Se for um número >= 100, provavelmente é a potência
                            if value >= 100:
                                numeric_start_idx = i
                                break
                        except ValueError:
                            # Não é um número, continua procurando
                            continue
                    
                    if numeric_start_idx == -1:
                        print(f"[TOOL] ⚠️ Não foi possível encontrar potência (número >= 100) na linha {line_idx + 1}")
                        print(f"[TOOL]    Linha: {line[:80]}")
                        continue
                    
                    # Nome da usina é todas as palavras antes da potência
                    nome_parts = words[:numeric_start_idx]
                    nome = ' '.join(nome_parts).strip()
                    
                    # ETAPA 4: Dividir a parte numérica em campos
                    # Pegar todas as palavras a partir da potência
                    numeric_words = words[numeric_start_idx:]
                    # Converter para string e dividir novamente para garantir espaçamento correto
                    numeric_part = ' '.join(numeric_words)
                    # Dividir por espaços múltiplos
                    parts = re.split(r'\s+', numeric_part.strip())
                    
                    # ETAPA 5: Extrair campos
                    # parts[0] = POT
                    # parts[1] = FCMX
                    # parts[2] = TEIF
                    # parts[3] = IP
                    # parts[4:16] = GTMIN mensal (12 valores)
                    # parts[16] = GTMIN ano 2
                    # parts[17] = GTMIN anos posteriores
                    
                    pot = safe_float(parts[0]) if len(parts) > 0 else 0.0
                    fcmx = safe_float(parts[1]) if len(parts) > 1 else 0.0
                    teif = safe_float(parts[2]) if len(parts) > 2 else 0.0
                    ip = safe_float(parts[3]) if len(parts) > 3 else 0.0
                    
                    # ETAPA 6: GTMIN mensal e anos posteriores
                    # parts[4:16] = GTMIN mensal (12 valores)
                    # parts[16] = GTMIN ano 2
                    # parts[17] = GTMIN anos posteriores
                    gmin_mensal = {}
                    for i, mes in enumerate(meses):
                        idx = 4 + i
                        if idx < len(parts):
                            gmin_mensal[f'gtmin_{mes}'] = safe_float(parts[idx])
                        else:
                            gmin_mensal[f'gtmin_{mes}'] = 0.0
                    
                    # D+ ANOS: 2 valores após os 12 meses
                    idx_ano2 = 4 + 12
                    gmin_ano2 = safe_float(parts[idx_ano2]) if idx_ano2 < len(parts) else 0.0
                    
                    idx_anos_posteriores = 4 + 13
                    gmin_anos_posteriores = safe_float(parts[idx_anos_posteriores]) if idx_anos_posteriores < len(parts) else 0.0
                    
                    record = {
                        'codigo_usina': codigo,
                        'nome_usina': nome,
                        'potencia_efetiva': pot,
                        'fator_capacidade_maximo': fcmx,
                        'taxa_indisponibilidade_forcada': teif,
                        'indisponibilidade_programada': ip,
                        'gtmin_ano2': gmin_ano2,
                        'gtmin_anos_posteriores': gmin_anos_posteriores,
                        **gmin_mensal
                    }
                    records.append(record)
                    
                except (ValueError, IndexError) as e:
                    print(f"[TOOL] ⚠️ Erro ao parsear linha {line_idx + 1}: {e}")
                    print(f"[TOOL]    Linha: {line[:80]}")
                    continue
            
            if records:
                df = pd.DataFrame(records)
                print(f"[TOOL] ✅ DataFrame criado com {len(df)} registros")
                print(f"[TOOL]    Colunas: {list(df.columns)}")
                return df
            else:
                print("[TOOL] ❌ Nenhum registro válido encontrado")
                return None
                
        except FileNotFoundError:
            print(f"[TOOL] ❌ Arquivo não encontrado: {term_path}")
            return None
        except Exception as e:
            print(f"[TOOL] ❌ Erro ao ler TERM.DAT: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def execute(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Executa a consulta de cadastro de usinas térmicas.
        
        Fluxo:
        1. Verifica se TERM.DAT existe
        2. Lê o arquivo
        3. Identifica usina se mencionada
        4. Retorna dados cadastrais
        """
        print(f"[TOOL] {self.get_name()}: Iniciando execução...")
        print(f"[TOOL] Query: {query[:100]}")
        print(f"[TOOL] Deck path: {self.deck_path}")
        
        try:
            # ETAPA 1: Verificar existência do arquivo
            print("[TOOL] ETAPA 1: Verificando existência do arquivo TERM.DAT...")
            term_path = os.path.join(self.deck_path, "TERM.DAT")
            
            if not os.path.exists(term_path):
                term_path_lower = os.path.join(self.deck_path, "term.dat")
                if os.path.exists(term_path_lower):
                    term_path = term_path_lower
                else:
                    print(f"[TOOL] ❌ Arquivo TERM.DAT não encontrado")
                    return {
                        "success": False,
                        "error": f"Arquivo TERM.DAT não encontrado em {self.deck_path}",
                        "tool": self.get_name()
                    }
            
            print(f"[TOOL] ✅ Arquivo encontrado: {term_path}")
            
            # ETAPA 2: Ler arquivo
            print("[TOOL] ETAPA 2: Lendo arquivo TERM.DAT...")
            term_data = self._read_term_file(term_path)
            
            if term_data is None or term_data.empty:
                print("[TOOL] ❌ Nenhum dado encontrado no arquivo")
                return {
                    "success": False,
                    "error": "Nenhum dado encontrado no arquivo TERM.DAT",
                    "tool": self.get_name()
                }
            
            print(f"[TOOL] ✅ DataFrame obtido: {len(term_data)} registros")
            
            # ETAPA 3: Extrair usina da query (se mencionada)
            print("[TOOL] ETAPA 3: Extraindo usina da query...")
            codigo_usina = self._extract_usina_from_query(query, term_data)
            
            # ETAPA 4: Filtrar dados
            if codigo_usina is not None:
                print(f"[TOOL] Filtrando por usina {codigo_usina}...")
                dados_filtrados = term_data[term_data['codigo_usina'] == codigo_usina].copy()
                if dados_filtrados.empty:
                    return {
                        "success": False,
                        "error": f"Usina {codigo_usina} não encontrada no TERM.DAT",
                        "tool": self.get_name()
                    }
                print(f"[TOOL] ✅ {len(dados_filtrados)} registro(s) encontrado(s) para usina {codigo_usina}")
            else:
                print("[TOOL] Nenhuma usina específica mencionada, retornando todas as usinas")
                dados_filtrados = term_data.copy()
            
            # ETAPA 5: Converter para lista de dicionários
            dados_lista = dados_filtrados.to_dict('records')
            
            # Preparar estatísticas resumidas
            stats = {}
            if len(dados_filtrados) > 0:
                if 'potencia_efetiva' in dados_filtrados.columns:
                    stats['potencia_total'] = float(dados_filtrados['potencia_efetiva'].sum())
                    stats['potencia_media'] = float(dados_filtrados['potencia_efetiva'].mean())
                    stats['potencia_min'] = float(dados_filtrados['potencia_efetiva'].min())
                    stats['potencia_max'] = float(dados_filtrados['potencia_efetiva'].max())
            
            return {
                "success": True,
                "data": dados_lista,
                "summary": stats if stats else None,
                "description": f"Cadastro de usinas térmicas: {len(dados_lista)} registro(s) do TERM.DAT",
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
                "error": f"Erro ao processar TERM.DAT: {str(e)}",
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
        Cadastro de usinas termoelétricas. Dados estruturais e operacionais básicos das usinas termoelétricas do TERM.DAT.
        
        Queries que ativam esta tool:
        - "dados da usina térmica 1"
        - "informações cadastrais da usina térmica ANGRA 1"
        - "cadastro da usina térmica X"
        - "características da usina térmica Y"
        - "potência efetiva da usina térmica"
        - "geração mínima da usina térmica"
        - "fator de capacidade máximo da térmica"
        - "indisponibilidade programada da térmica"
        - "taxa de indisponibilidade forçada"
        - "dados estruturais da usina térmica"
        - "informações do term.dat da usina"
        - "potef da usina"
        - "fcmax da térmica"
        - "teif da usina"
        - "ip da térmica"
        
        Esta tool consulta o arquivo TERM.DAT e retorna todas as informações cadastrais disponíveis sobre uma usina térmica específica, incluindo:
        - Informações básicas (código, nome)
        - Potência efetiva (POT) - MW
        - Fator de capacidade máximo (FCMX) - %
        - Taxa equivalente de indisponibilidade forçada (TEIF) - %
        - Indisponibilidade programada (IP) - %
        - Geração mínima mensal do primeiro ano (GTMIN) - 12 valores (JAN a DEZ) - MW
        - Geração mínima para anos seguintes (D+ ANOS) - 2 valores - MW
        
        IMPORTANTE: 
        - TERM.DAT contém os valores PADRÃO/PERSISTENTES das características das usinas térmicas
        - Modificações temporárias são definidas no EXPT.DAT
        - Para períodos não declarados no EXPT.DAT, os valores do TERM.DAT são utilizados
        
        A tool identifica automaticamente a usina mencionada na query através de matching inteligente:
        - Busca por código numérico explícito
        - Busca por nome completo da usina
        - Busca por similaridade de strings
        - Busca por palavras-chave do nome
        
        Termos-chave: term.dat, cadastro térmica, informações cadastrais térmicas, dados cadastrais térmicas, características da usina térmica, potência efetiva, geração mínima, fator de capacidade máximo, indisponibilidade programada, indisponibilidade forçada, potef, fcmax, teif, ip.
        """

