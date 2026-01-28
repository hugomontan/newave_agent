"""
Tool para consultar cadastro de usinas termoelétricas do TERM.DAT.
Acessa dados estruturais e operacionais básicos das usinas térmicas.
"""
from backend.newave.tools.base import NEWAVETool
import os
import pandas as pd
import re
from typing import Dict, Any, Optional
from backend.newave.config import debug_print, safe_print
from backend.newave.utils.thermal_plant_matcher import get_thermal_plant_matcher


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
        Extrai código da usina da query usando o ThermalPlantMatcher unificado.
        
        Args:
            query: Query do usuário
            term_data: DataFrame com dados do TERM.DAT
            
        Returns:
            Código da usina ou None se não encontrado
        """
        # Usar o matcher unificado
        matcher = get_thermal_plant_matcher()
        return matcher.extract_plant_from_query(
            query=query,
            available_plants=term_data,
            entity_type="usina",
            threshold=0.5
        )
    
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
            debug_print(f"[TOOL] Lendo arquivo TERM.DAT: {term_path}")
            
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
                debug_print("[TOOL] ⚠️ Nenhuma linha de dados encontrada após o cabeçalho")
                # Tentar ler todas as linhas que começam com número
                for line in lines:
                    line_stripped = line.strip()
                    if re.match(r'^\s*\d+', line_stripped):
                        data_lines.append(line)
            
            if not data_lines:
                safe_print(f"[TOOL] ❌ Nenhuma linha de dados encontrada")
                return None
            
            debug_print(f"[TOOL] ✅ {len(data_lines)} linhas de dados encontradas")
            
            # Parsear linhas
            records = []
            meses = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 
                    'jul', 'ago', 'set', 'out', 'nov', 'dez']
            
            for line_idx, line in enumerate(data_lines):
                # Garantir que a linha tenha tamanho mínimo
                if len(line) < 44:
                    debug_print(f"[TOOL] ⚠️ Linha {line_idx + 1} muito curta, pulando")
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
                        debug_print(f"[TOOL] ⚠️ Não foi possível encontrar potência (número >= 100) na linha {line_idx + 1}")
                        debug_print(f"[TOOL]    Linha: {line[:80]}")
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
                    debug_print(f"[TOOL] ⚠️ Erro ao parsear linha {line_idx + 1}: {e}")
                    debug_print(f"[TOOL]    Linha: {line[:80]}")
                    continue
            
            if records:
                df = pd.DataFrame(records)
                debug_print(f"[TOOL] ✅ DataFrame criado com {len(df)} registros")
                debug_print(f"[TOOL]    Colunas: {list(df.columns)}")
                return df
            else:
                safe_print(f"[TOOL] ❌ Nenhum registro válido encontrado")
                return None
                
        except FileNotFoundError:
            safe_print(f"[TOOL] ❌ Arquivo não encontrado: {term_path}")
            return None
        except Exception as e:
            safe_print(f"[TOOL] ❌ Erro ao ler TERM.DAT: {type(e).__name__}: {e}")
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
        debug_print(f"[TOOL] {self.get_name()}: Iniciando execução...")
        debug_print(f"[TOOL] Query: {query[:100]}")
        debug_print(f"[TOOL] Deck path: {self.deck_path}")
        
        try:
            # ETAPA 1: Verificar existência do arquivo
            debug_print("[TOOL] ETAPA 1: Verificando existência do arquivo TERM.DAT...")
            term_path = os.path.join(self.deck_path, "TERM.DAT")
            
            if not os.path.exists(term_path):
                term_path_lower = os.path.join(self.deck_path, "term.dat")
                if os.path.exists(term_path_lower):
                    term_path = term_path_lower
                else:
                    safe_print(f"[TOOL] ❌ Arquivo TERM.DAT não encontrado")
                    return {
                        "success": False,
                        "error": f"Arquivo TERM.DAT não encontrado em {self.deck_path}",
                        "tool": self.get_name()
                    }
            
            debug_print(f"[TOOL] ✅ Arquivo encontrado: {term_path}")
            
            # ETAPA 2: Ler arquivo
            debug_print("[TOOL] ETAPA 2: Lendo arquivo TERM.DAT...")
            term_data = self._read_term_file(term_path)
            
            if term_data is None or term_data.empty:
                safe_print(f"[TOOL] ❌ Nenhum dado encontrado no arquivo")
                return {
                    "success": False,
                    "error": "Nenhum dado encontrado no arquivo TERM.DAT",
                    "tool": self.get_name()
                }
            
            debug_print(f"[TOOL] ✅ DataFrame obtido: {len(term_data)} registros")
            
            # ETAPA 3: Extrair usina da query (se mencionada)
            # Verificar se há código forçado (correção de usina)
            forced_plant_code = kwargs.get("forced_plant_code")
            if forced_plant_code is not None:
                debug_print(f"[TOOL] ETAPA 3: Usando código forçado (correção): {forced_plant_code}")
                codigo_usina = forced_plant_code
            else:
                debug_print("[TOOL] ETAPA 3: Extraindo usina da query...")
                codigo_usina = self._extract_usina_from_query(query, term_data)
            
            # ETAPA 3.5: Criar selected_plant ANTES de buscar dados (para garantir que follow-up apareça)
            # Isso é crítico quando forced_plant_code está presente
            selected_plant = None
            if codigo_usina is not None:
                from backend.newave.utils.thermal_plant_matcher import get_thermal_plant_matcher
                matcher = get_thermal_plant_matcher()
                if codigo_usina in matcher.code_to_names:
                    nome_arquivo_csv, nome_completo_csv = matcher.code_to_names[codigo_usina]
                    selected_plant = {
                        "type": "thermal",
                        "codigo": codigo_usina,
                        "nome": nome_arquivo_csv,
                        "nome_completo": nome_completo_csv if nome_completo_csv else nome_arquivo_csv,
                        "tool_name": self.get_name()
                    }
                    debug_print(f"[TOOL] ✅ selected_plant criado: código={codigo_usina}, nome={nome_arquivo_csv}")
            
            # ETAPA 4: Filtrar dados
            if codigo_usina is not None:
                debug_print(f"[TOOL] Filtrando por usina {codigo_usina}...")
                dados_filtrados = term_data[term_data['codigo_usina'] == codigo_usina].copy()
                if dados_filtrados.empty:
                    # Se não encontrou dados mas tem selected_plant, retornar com selected_plant para follow-up
                    if selected_plant:
                        debug_print(f"[TOOL] ⚠️ Usina {codigo_usina} não encontrada no TERM.DAT, mas selected_plant foi criado para follow-up")
                        return {
                            "success": False,
                            "error": f"Usina {codigo_usina} não encontrada no TERM.DAT",
                            "tool": self.get_name(),
                            "selected_plant": selected_plant  # Incluir mesmo com erro para permitir follow-up
                        }
                    return {
                        "success": False,
                        "error": f"Usina {codigo_usina} não encontrada no TERM.DAT",
                        "tool": self.get_name()
                    }
                debug_print(f"[TOOL] ✅ {len(dados_filtrados)} registro(s) encontrado(s) para usina {codigo_usina}")
            else:
                debug_print("[TOOL] Nenhuma usina específica mencionada, retornando todas as usinas")
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
            
            result = {
                "success": True,
                "data": dados_lista,
                "summary": stats if stats else None,
                "description": f"Cadastro de usinas térmicas: {len(dados_lista)} registro(s) do TERM.DAT",
                "tool": self.get_name()
            }
            
            # Adicionar metadados da usina selecionada se disponível
            if selected_plant:
                result["selected_plant"] = selected_plant
            
            return result
            
        except FileNotFoundError as e:
            safe_print(f"[TOOL] ❌ Erro FileNotFoundError: {e}")
            return {
                "success": False,
                "error": f"Arquivo não encontrado: {str(e)}",
                "tool": self.get_name()
            }
        except Exception as e:
            safe_print(f"[TOOL] ❌ Erro ao processar: {type(e).__name__}: {e}")
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
        return """Cadastro usinas termoelétricas TERM.DAT potência nominal fator capacidade TEIF GTMIN."""

