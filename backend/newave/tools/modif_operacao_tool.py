"""
Tool para consultar dados de operação hídrica do MODIF.DAT.
Acessa modificações temporárias das características das usinas hidrelétricas.
"""
from backend.newave.tools.base import NEWAVETool
from inewave.newave import Modif
import os
import pandas as pd
import re
from typing import Dict, Any, Optional
from backend.newave.config import debug_print, safe_print

class ModifOperacaoTool(NEWAVETool):
    """
    Tool para consultar dados de operação hídrica do MODIF.DAT.
    
    Dados disponíveis:
    - Volumes (mínimo, máximo, com data)
    - Vazões (mínima, máxima, com data)
    - Níveis (canal de fuga, montante)
    - Turbinamento (máximo, mínimo, por patamar)
    - Potência efetiva
    - Indisponibilidades (programada, forçada)
    - Número de conjuntos e máquinas
    """
    
    def get_name(self) -> str:
        return "ModifOperacaoTool"
    
    def can_handle(self, query: str) -> bool:
        """
        Verifica se a query é sobre operação hídrica do MODIF.
        
        Args:
            query: Query do usuário
            
        Returns:
            True se a tool pode processar a query
        """
        query_lower = query.lower()
        query_upper = query.upper()
        
        # PALAVRAS-CHAVE PRIORITÁRIAS: "VAZAO MÍNIMA" em todas as variações
        # Verificar primeiro para garantir prioridade máxima e ativação automática
        # Verificar em lowercase (cobre todas as variações de maiúscula/minúscula)
        vazao_minima_patterns = [
            "vazão mínima", "vazao minima", "vazão minima", "vazao mínima",
            "vazao-minima", "vazão-mínima", "vazao_minima", "vazão_mínima"
        ]
        
        # Verificar se alguma variação de "vazão mínima" está presente (case-insensitive)
        if any(pattern in query_lower for pattern in vazao_minima_patterns):
            return True
        
        # Outras palavras-chave
        keywords = [
            "modif",
            "modificação hídrica",
            "modificacao hidrica",
            "modificação hidrelétrica",
            "modificacao hidreletrica",
            "operação hídrica",
            "operacao hidrica",
            "dados operação hídrica",
            "dados operacao hidrica",
            "volume mínimo",
            "volume minimo",
            "volume máximo",
            "volume maximo",
            "vazão máxima",
            "vazao maxima",
            "canal de fuga",
            "canal fuga",
            "nível montante",
            "nivel montante",
            "turbinamento",
            "potência efetiva hidrelétrica",
            "potencia efetiva hidreletrica",
            "modificações hidrelétricas",
            "modificacoes hidreletricas"
        ]
        return any(kw in query_lower for kw in keywords)
    
    def _extract_tipo_modificacao(self, query: str) -> Optional[str]:
        """
        Extrai tipo de modificação da query.
        
        Args:
            query: Query do usuário
            
        Returns:
            Tipo de modificação ou None (todos)
        """
        query_lower = query.lower()
        
        # Verificar primeiro "vazão mínima por período" (mais específico) antes de "vazão mínima" (genérico)
        vazao_minima_por_periodo_patterns = [
            "vazão mínima por período", "vazao minima por periodo",
            "vazão minima por período", "vazao mínima por periodo",
            "vazão mínima por periodo", "vazao minima por período",
            "vazão mínima temporal", "vazao minima temporal"
        ]
        
        if any(pattern in query_lower for pattern in vazao_minima_por_periodo_patterns):
            return "VAZMINT"
        
        tipos = {
            # Volumes
            "volume mínimo": "VOLMIN",
            "volume minimo": "VOLMIN",
            "volmin": "VOLMIN",
            "volume máximo": "VOLMAX",
            "volume maximo": "VOLMAX",
            "volmax": "VOLMAX",
            "vmaxt": "VMAXT",
            "vmint": "VMINT",
            "vminp": "VMINP",
            # Vazões
            "vazão mínima": "VAZMIN",
            "vazao minima": "VAZMIN",
            "vazmin": "VAZMIN",
            "vazmint": "VAZMINT",
            "vazão máxima": "VAZMAXT",
            "vazao maxima": "VAZMAXT",
            "vazmaxt": "VAZMAXT",
            # Níveis
            "canal de fuga": "CFUGA",
            "canal fuga": "CFUGA",
            "cfuga": "CFUGA",
            "nível montante": "CMONT",
            "nivel montante": "CMONT",
            "cmont": "CMONT",
            # Turbinamento
            "turbinamento máximo": "TURBMAXT",
            "turbinamento maximo": "TURBMAXT",
            "turbmaxt": "TURBMAXT",
            "turbinamento mínimo": "TURBMINT",
            "turbinamento minimo": "TURBMINT",
            "turbmint": "TURBMINT",
        }
        
        for key, value in tipos.items():
            if key in query_lower:
                return value
        
        return None
    
    def _extract_usina_from_query(self, query: str, modif: Modif) -> Optional[int]:
        """
        Extrai código da usina da query.
        Busca por número ou nome da usina.
        
        Args:
            query: Query do usuário
            modif: Objeto Modif já lido
            
        Returns:
            Código da usina ou None se não encontrado
        """
        query_lower = query.lower()
        
        # ETAPA 1: Tentar extrair número explícito
        patterns = [
            r'usina\s*(\d+)',
            r'usina\s*hidrelétrica\s*(\d+)',
            r'usina\s*hidreletrica\s*(\d+)',
            r'usina\s*#?\s*(\d+)',
            r'código\s*(\d+)',
            r'codigo\s*(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query_lower)
            if match:
                try:
                    codigo = int(match.group(1))
                    # Verificar se existe no arquivo
                    usinas_df = modif.usina(df=True)
                    if usinas_df is not None and not usinas_df.empty:
                        codigos_validos = usinas_df['codigo'].unique()
                        if codigo in codigos_validos:
                            debug_print(f"[TOOL] ✅ Código {codigo} encontrado por padrão numérico")
                            return codigo
                except ValueError:
                    continue
        
        # ETAPA 2: Buscar por nome da usina
        usinas_df = modif.usina(df=True)
        if usinas_df is not None and not usinas_df.empty:
            debug_print(f"[TOOL] Usinas disponíveis no arquivo:")
            for _, row in usinas_df.iterrows():
                codigo = int(row.get('codigo'))
                nome = str(row.get('nome', '')).strip()
                print(f"[TOOL]   - Código {codigo}: \"{nome}\"")
            
            # Ordenar por tamanho do nome (maior primeiro) para priorizar matches mais específicos
            usinas_sorted = sorted(
                usinas_df.iterrows(),
                key=lambda x: len(str(x[1].get('nome', '')).strip()),
                reverse=True
            )
            
            # ETAPA 2.1: Buscar match exato do nome completo (prioridade máxima)
            for _, row in usinas_sorted:
                codigo_usina = int(row.get('codigo'))
                nome_usina = str(row.get('nome', '')).strip()
                nome_usina_lower = nome_usina.lower().strip()
                
                if not nome_usina_lower:
                    continue
                
                # Match exato do nome completo
                if nome_usina_lower == query_lower.strip():
                    debug_print(f"[TOOL] ✅ Código {codigo_usina} encontrado por match exato '{nome_usina}'")
                    return codigo_usina
                
                # Match exato do nome completo dentro da query (com espaços/pontuação)
                if nome_usina_lower in query_lower:
                    # Verificar se não é apenas uma palavra parcial muito curta
                    if len(nome_usina_lower) >= 4:  # Nomes com pelo menos 4 caracteres
                        # Verificar se está como palavra completa (não parte de outra palavra)
                        pattern = r'\b' + re.escape(nome_usina_lower) + r'\b'
                        if re.search(pattern, query_lower):
                            debug_print(f"[TOOL] ✅ Código {codigo_usina} encontrado por nome completo '{nome_usina}' na query")
                            return codigo_usina
            
            # ETAPA 2.2: Buscar por palavras-chave do nome (apenas se match exato não encontrou)
            # Priorizar palavras mais longas e específicas
            palavras_candidatas = []
            for _, row in usinas_sorted:
                codigo_usina = int(row.get('codigo'))
                nome_usina = str(row.get('nome', '')).strip()
                nome_usina_lower = nome_usina.lower().strip()
                
                if not nome_usina_lower:
                    continue
                
                palavras_nome = nome_usina_lower.split()
                # Ordenar palavras por tamanho (maior primeiro)
                palavras_nome_sorted = sorted(palavras_nome, key=len, reverse=True)
                
                for palavra in palavras_nome_sorted:
                    # Apenas palavras com mais de 3 caracteres para evitar matches incorretos
                    if len(palavra) > 3:
                        # Verificar se a palavra está na query como palavra completa
                        pattern = r'\b' + re.escape(palavra) + r'\b'
                        if re.search(pattern, query_lower):
                            palavras_candidatas.append({
                                'codigo': codigo_usina,
                                'nome': nome_usina,
                                'palavra': palavra,
                                'tamanho': len(palavra),
                                'tamanho_nome': len(nome_usina_lower)
                            })
            
            # Se encontrou candidatos, escolher o melhor (palavra mais longa + nome mais específico)
            if palavras_candidatas:
                # Ordenar por tamanho da palavra (maior primeiro) e depois por tamanho do nome
                melhor_match = max(
                    palavras_candidatas,
                    key=lambda x: (x['tamanho'], x['tamanho_nome'])
                )
                debug_print(f"[TOOL] ✅ Código {melhor_match['codigo']} encontrado por palavra-chave '{melhor_match['palavra']}' do nome '{melhor_match['nome']}'")
                return melhor_match['codigo']
        
        debug_print("[TOOL] ⚠️ Nenhuma usina específica detectada na query")
        return None
    
    def _get_all_modifications(self, modif: Modif, codigo_usina: Optional[int] = None) -> Dict[str, pd.DataFrame]:
        """
        Obtém todas as modificações do arquivo, agrupadas por tipo.
        
        Se codigo_usina for especificado, usa modificacoes_usina() para obter todos os registros
        detalhados daquela usina. Caso contrário, usa os métodos genéricos.
        
        Args:
            modif: Objeto Modif
            codigo_usina: Código da usina para filtrar (opcional)
            
        Returns:
            Dict com modificações por tipo (DataFrames)
        """
        modificacoes_por_tipo = {}
        
        if codigo_usina is not None:
            # Abordagem detalhada: usar modificacoes_usina() para obter todos os registros completos
            debug_print(f"[TOOL] Obtendo modificações detalhadas da usina {codigo_usina}...")
            modificacoes_usina_list = modif.modificacoes_usina(codigo_usina)
            
            if not modificacoes_usina_list:
                debug_print(f"[TOOL] ⚠️ Nenhuma modificação encontrada para usina {codigo_usina}")
                return modificacoes_por_tipo
            
            # Obter informações da usina
            usina_info = None
            usinas_df = modif.usina(df=True)
            if usinas_df is not None:
                usina_row = usinas_df[usinas_df['codigo'] == codigo_usina]
                if not usina_row.empty:
                    usina_info = {
                        'codigo': codigo_usina,
                        'nome': str(usina_row.iloc[0].get('nome', f'Usina {codigo_usina}'))
                    }
            
            # Agrupar registros por tipo e converter para dicionários
            registros_por_tipo = {}
            
            # Mapeamento de nomes de classes para tipos conhecidos (caso haja diferença)
            tipo_mapping = {
                'RegistroVolminModif': 'VOLMIN',
                'RegistroVolmaxModif': 'VOLMAX',
                'RegistroVmaxtModif': 'VMAXT',
                'RegistroVmintModif': 'VMINT',
                'RegistroVminpModif': 'VMINP',
                'RegistroVazminModif': 'VAZMIN',
                'RegistroVazmintModif': 'VAZMINT',
                'RegistroVazmaxtModif': 'VAZMAXT',
                'RegistroCfugaModif': 'CFUGA',
                'RegistroCmontModif': 'CMONT',
                'RegistroTurbmaxtModif': 'TURBMAXT',
                'RegistroTurbmintModif': 'TURBMINT',
                'RegistroNumcnjModif': 'NUMCNJ',
                'RegistroNummaqModif': 'NUMMAQ',
                'RegistroPotefeModif': 'POTEFE',
                'RegistroTeifModif': 'TEIF',
                'RegistroIpModif': 'IP',
            }
            
            for registro in modificacoes_usina_list:
                tipo_registro_class = type(registro).__name__
                # Mapear para nome do tipo conhecido, ou usar o nome da classe diretamente
                tipo_registro = tipo_mapping.get(tipo_registro_class, tipo_registro_class)
                
                # Criar dicionário com todas as propriedades do registro
                registro_dict = {}
                
                # Adicionar informações da usina
                if usina_info:
                    registro_dict['codigo'] = usina_info['codigo']
                    registro_dict['codigo_usina'] = usina_info['codigo']
                    registro_dict['nome'] = usina_info['nome']
                    registro_dict['nome_usina'] = usina_info['nome']
                
                # Extrair propriedades específicas do tipo de registro
                # Usar getattr com None como padrão para evitar erros
                if hasattr(registro, 'volume'):
                    valor = getattr(registro, 'volume', None)
                    if valor is not None:
                        registro_dict['volume'] = valor
                if hasattr(registro, 'unidade'):
                    valor = getattr(registro, 'unidade', None)
                    if valor is not None:
                        registro_dict['unidade'] = valor
                if hasattr(registro, 'vazao'):
                    valor = getattr(registro, 'vazao', None)
                    if valor is not None:
                        registro_dict['vazao'] = valor
                if hasattr(registro, 'nivel'):
                    valor = getattr(registro, 'nivel', None)
                    if valor is not None:
                        registro_dict['nivel'] = valor
                if hasattr(registro, 'turbinamento'):
                    valor = getattr(registro, 'turbinamento', None)
                    if valor is not None:
                        registro_dict['turbinamento'] = valor
                if hasattr(registro, 'patamar'):
                    valor = getattr(registro, 'patamar', None)
                    if valor is not None:
                        registro_dict['patamar'] = valor
                if hasattr(registro, 'numero'):
                    valor = getattr(registro, 'numero', None)
                    if valor is not None:
                        registro_dict['numero'] = valor
                if hasattr(registro, 'conjunto'):
                    valor = getattr(registro, 'conjunto', None)
                    if valor is not None:
                        registro_dict['conjunto'] = valor
                if hasattr(registro, 'numero_maquinas'):
                    valor = getattr(registro, 'numero_maquinas', None)
                    if valor is not None:
                        registro_dict['numero_maquinas'] = valor
                if hasattr(registro, 'potencia'):
                    valor = getattr(registro, 'potencia', None)
                    if valor is not None:
                        registro_dict['potencia'] = valor
                if hasattr(registro, 'taxa'):
                    valor = getattr(registro, 'taxa', None)
                    if valor is not None:
                        registro_dict['taxa'] = valor
                if hasattr(registro, 'data_inicio'):
                    valor = getattr(registro, 'data_inicio', None)
                    if valor is not None:
                        registro_dict['data_inicio'] = valor
                if hasattr(registro, 'data_fim'):
                    valor = getattr(registro, 'data_fim', None)
                    if valor is not None:
                        registro_dict['data_fim'] = valor
                
                # Adicionar ao dicionário de registros por tipo
                if tipo_registro not in registros_por_tipo:
                    registros_por_tipo[tipo_registro] = []
                registros_por_tipo[tipo_registro].append(registro_dict)
            
            # Converter listas de dicionários em DataFrames
            for tipo, registros in registros_por_tipo.items():
                if registros:
                    df = pd.DataFrame(registros)
                    modificacoes_por_tipo[tipo] = df
                    debug_print(f"[TOOL] ✅ {len(registros)} registro(s) do tipo {tipo} extraído(s) com sucesso")
        
        else:
            # Abordagem genérica: usar métodos específicos para todas as usinas
            debug_print("[TOOL] Obtendo modificações de todas as usinas...")
            
            # Lista de métodos disponíveis
            metodos = {
                'VOLMIN': lambda: modif.volmin(df=True),
                'VOLMAX': lambda: modif.volmax(df=True),
                'VMAXT': lambda: modif.vmaxt(df=True),
                'VMINT': lambda: modif.vmint(df=True),
                'VMINP': lambda: modif.vminp(df=True),
                'VAZMIN': lambda: modif.vazmin(df=True),
                'VAZMINT': lambda: modif.vazmint(df=True),
                'VAZMAXT': lambda: modif.vazmaxt(df=True),
                'CFUGA': lambda: modif.cfuga(df=True),
                'CMONT': lambda: modif.cmont(df=True),
                'TURBMAXT': lambda: modif.turbmaxt(df=True),
                'TURBMINT': lambda: modif.turbmint(df=True),
                'NUMCNJ': lambda: modif.numcnj(df=True),
                'NUMMAQ': lambda: modif.nummaq(df=True),
            }
            
            # Tentar métodos que podem não existir
            try:
                if hasattr(modif, 'potefe'):
                    metodos['POTEFE'] = lambda: modif.potefe(df=True)
            except:
                pass
            
            try:
                if hasattr(modif, 'teif'):
                    metodos['TEIF'] = lambda: modif.teif(df=True)
            except:
                pass
            
            try:
                if hasattr(modif, 'ip'):
                    metodos['IP'] = lambda: modif.ip(df=True)
            except:
                pass
            
            for tipo, metodo in metodos.items():
                try:
                    resultado = metodo()
                    if resultado is not None and not resultado.empty:
                        modificacoes_por_tipo[tipo] = resultado
                        debug_print(f"[TOOL] ✅ {len(resultado)} registro(s) do tipo {tipo} encontrado(s)")
                except Exception as e:
                    debug_print(f"[TOOL] ⚠️ Erro ao obter {tipo}: {e}")
        
        return modificacoes_por_tipo
    
    def execute(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Executa a consulta de dados de operação hídrica.
        
        Fluxo:
        1. Verifica se MODIF.DAT existe
        2. Lê o arquivo usando inewave
        3. Identifica filtros (usina, tipo de modificação)
        4. Processa e retorna dados agrupados por tipo
        """
        debug_print(f"[TOOL] {self.get_name()}: Iniciando execução...")
        debug_print(f"[TOOL] Query: {query[:100]}")
        debug_print(f"[TOOL] Deck path: {self.deck_path}")
        
        try:
            # ETAPA 1: Verificar existência do arquivo
            debug_print("[TOOL] ETAPA 1: Verificando existência do arquivo MODIF.DAT...")
            modif_path = os.path.join(self.deck_path, "MODIF.DAT")
            
            if not os.path.exists(modif_path):
                modif_path_lower = os.path.join(self.deck_path, "modif.dat")
                if os.path.exists(modif_path_lower):
                    modif_path = modif_path_lower
                else:
                    safe_print(f"[TOOL] ❌ Arquivo MODIF.DAT não encontrado")
                    return {
                        "success": False,
                        "error": f"Arquivo MODIF.DAT não encontrado em {self.deck_path}",
                        "tool": self.get_name()
                    }
            
            debug_print(f"[TOOL] ✅ Arquivo encontrado: {modif_path}")
            
            # ETAPA 2: Ler arquivo usando inewave
            debug_print("[TOOL] ETAPA 2: Lendo arquivo com inewave...")
            modif = Modif.read(modif_path)
            debug_print("[TOOL] ✅ Arquivo lido com sucesso")
            
            # ETAPA 3: Verificar se há dados
            usinas_df = modif.usina(df=True)
            if usinas_df is None or usinas_df.empty:
                debug_print("[TOOL] ⚠️ Nenhuma usina modificada encontrada")
                return {
                    "success": False,
                    "error": "Nenhuma modificação encontrada no arquivo MODIF.DAT",
                    "tool": self.get_name()
                }
            
            debug_print(f"[TOOL] ✅ {len(usinas_df)} usina(s) modificada(s) encontrada(s)")
            
            # ETAPA 4: Identificar filtros
            debug_print("[TOOL] ETAPA 4: Identificando filtros...")
            codigo_usina = self._extract_usina_from_query(query, modif)
            tipo_modificacao = self._extract_tipo_modificacao(query)
            
            if codigo_usina is not None:
                debug_print(f"[TOOL] ✅ Filtro por usina: {codigo_usina}")
            if tipo_modificacao is not None:
                debug_print(f"[TOOL] ✅ Filtro por tipo de modificação: {tipo_modificacao}")
            
            # ETAPA 5: Obter todas as modificações
            debug_print("[TOOL] ETAPA 5: Obtendo modificações...")
            modificacoes_por_tipo = self._get_all_modifications(modif, codigo_usina)
            
            if not modificacoes_por_tipo:
                debug_print("[TOOL] ⚠️ Nenhuma modificação encontrada")
                return {
                    "success": False,
                    "error": "Nenhuma modificação encontrada com os filtros aplicados",
                    "tool": self.get_name()
                }
            
            debug_print(f"[TOOL] ✅ {len(modificacoes_por_tipo)} tipo(s) de modificação encontrado(s)")
            
            # ETAPA 6: Filtrar por tipo se especificado
            if tipo_modificacao is not None:
                if tipo_modificacao in modificacoes_por_tipo:
                    modificacoes_por_tipo = {tipo_modificacao: modificacoes_por_tipo[tipo_modificacao]}
                else:
                    # Caso especial: se não encontrou VAZMIN mas existe VAZMINT, oferecer alternativa
                    if tipo_modificacao == "VAZMIN" and "VAZMINT" in modificacoes_por_tipo:
                        debug_print(f"[TOOL] ⚠️ Tipo {tipo_modificacao} não encontrado, mas VAZMINT está disponível")
                        # Obter informações da usina para a mensagem
                        nome_usina_str = "a usina"
                        if codigo_usina is not None:
                            nome_usina = usinas_df[usinas_df['codigo'] == codigo_usina]
                            if not nome_usina.empty:
                                nome_usina_str = f"a usina {codigo_usina} ({str(nome_usina.iloc[0].get('nome', ''))})"
                            else:
                                nome_usina_str = f"a usina {codigo_usina}"
                        
                        return {
                            "success": False,
                            "error": f"Não existem registros de vazão mínima (VAZMIN) para {nome_usina_str}",
                            "requires_user_choice": True,
                            "choice_message": f"Não existem registros de vazão mínima (VAZMIN) para {nome_usina_str}, você deseja os valores de vazão mínima por período (VAZMINT)?",
                            "alternative_type": "VAZMINT",
                            "alternative_data_available": True,
                            "tool": self.get_name()
                        }
                    
                    debug_print(f"[TOOL] ⚠️ Tipo {tipo_modificacao} não encontrado")
                    return {
                        "success": False,
                        "error": f"Tipo de modificação {tipo_modificacao} não encontrado",
                        "tool": self.get_name()
                    }
            
            # ETAPA 7: Processar dados para JSON
            debug_print("[TOOL] ETAPA 7: Processando dados...")
            dados_por_tipo = {}
            stats_por_tipo = []
            
            for tipo, df in modificacoes_por_tipo.items():
                # Converter DataFrame para lista de dicts
                dados = df.to_dict(orient="records")
                
                # Converter tipos para JSON-serializable
                for record in dados:
                    for key, value in record.items():
                        if pd.isna(value):
                            record[key] = None
                        elif isinstance(value, (pd.Timestamp, pd.DatetimeTZDtype)):
                            record[key] = value.isoformat() if hasattr(value, 'isoformat') else str(value)
                
                dados_por_tipo[tipo] = dados
                
                # Calcular estatísticas
                stats = {
                    'tipo': tipo,
                    'total_registros': len(df),
                }
                
                # Estatísticas específicas por tipo
                if 'volume' in df.columns:
                    stats['valor_medio'] = float(df['volume'].mean()) if len(df) > 0 else 0
                    stats['valor_min'] = float(df['volume'].min()) if len(df) > 0 else 0
                    stats['valor_max'] = float(df['volume'].max()) if len(df) > 0 else 0
                    stats['unidade'] = df['unidade'].iloc[0] if 'unidade' in df.columns and len(df) > 0 else 'N/A'
                elif 'vazao' in df.columns:
                    stats['valor_medio'] = float(df['vazao'].mean()) if len(df) > 0 else 0
                    stats['valor_min'] = float(df['vazao'].min()) if len(df) > 0 else 0
                    stats['valor_max'] = float(df['vazao'].max()) if len(df) > 0 else 0
                    stats['unidade'] = 'm³/s'
                elif 'nivel' in df.columns:
                    stats['valor_medio'] = float(df['nivel'].mean()) if len(df) > 0 else 0
                    stats['valor_min'] = float(df['nivel'].min()) if len(df) > 0 else 0
                    stats['valor_max'] = float(df['nivel'].max()) if len(df) > 0 else 0
                    stats['unidade'] = 'm'
                elif 'turbinamento' in df.columns:
                    stats['valor_medio'] = float(df['turbinamento'].mean()) if len(df) > 0 else 0
                    stats['valor_min'] = float(df['turbinamento'].min()) if len(df) > 0 else 0
                    stats['valor_max'] = float(df['turbinamento'].max()) if len(df) > 0 else 0
                    stats['unidade'] = 'm³/s'
                elif 'numero' in df.columns:
                    stats['valor_medio'] = float(df['numero'].mean()) if len(df) > 0 else 0
                    stats['valor_min'] = float(df['numero'].min()) if len(df) > 0 else 0
                    stats['valor_max'] = float(df['numero'].max()) if len(df) > 0 else 0
                    stats['unidade'] = 'unidade'
                
                stats_por_tipo.append(stats)
            
            # ETAPA 8: Estatísticas gerais
            stats_geral = {
                'total_tipos': len(modificacoes_por_tipo),
                'total_registros': sum(len(df) for df in modificacoes_por_tipo.values()),
                'tipos_encontrados': list(modificacoes_por_tipo.keys()),
            }
            
            # Estatísticas por usina
            stats_por_usina = []
            if codigo_usina is None:
                # Se não filtrou por usina, listar todas
                for _, row in usinas_df.iterrows():
                    codigo = int(row.get('codigo'))
                    nome = str(row.get('nome', f'Usina {codigo}'))
                    
                    modificacoes_usina = modif.modificacoes_usina(codigo)
                    if modificacoes_usina:
                        tipos = list(set([type(r).__name__ for r in modificacoes_usina]))
                        stats_por_usina.append({
                            'codigo_usina': codigo,
                            'nome_usina': nome,
                            'total_modificacoes': len(modificacoes_usina),
                            'tipos_modificacao': tipos,
                        })
            else:
                # Se filtrou por usina, adicionar apenas ela
                nome_usina = usinas_df[usinas_df['codigo'] == codigo_usina]
                if not nome_usina.empty:
                    nome = str(nome_usina.iloc[0].get('nome', f'Usina {codigo_usina}'))
                    modificacoes_usina = modif.modificacoes_usina(codigo_usina)
                    if modificacoes_usina:
                        tipos = list(set([type(r).__name__ for r in modificacoes_usina]))
                        stats_por_usina.append({
                            'codigo_usina': codigo_usina,
                            'nome_usina': nome,
                            'total_modificacoes': len(modificacoes_usina),
                            'tipos_modificacao': tipos,
                        })
            
            # ETAPA 9: Formatar resultado
            debug_print("[TOOL] ETAPA 9: Formatando resultado...")
            
            # Informações sobre filtros aplicados
            filtro_info = {}
            if codigo_usina is not None:
                nome_usina = usinas_df[usinas_df['codigo'] == codigo_usina]
                if not nome_usina.empty:
                    filtro_info['usina'] = {
                        'codigo': codigo_usina,
                        'nome': str(nome_usina.iloc[0].get('nome', f'Usina {codigo_usina}')),
                    }
            if tipo_modificacao is not None:
                filtro_info['tipo_modificacao'] = tipo_modificacao
            
            return {
                "success": True,
                "dados_por_tipo": dados_por_tipo,
                "filtros": filtro_info if filtro_info else None,
                "stats_geral": stats_geral,
                "stats_por_tipo": stats_por_tipo,
                "stats_por_usina": stats_por_usina,
                "description": "Dados de operação hídrica do MODIF.DAT (modificações de volumes, vazões, níveis, turbinamento, etc.)",
                "tool": self.get_name()
            }
            
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
                "error": f"Erro ao processar MODIF.DAT: {str(e)}",
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
        Modificações hídricas. Operação hídrica. Modificações temporárias das características operacionais das usinas hidrelétricas.
        
        Queries que ativam esta tool:
        - "quais são as modificações hídricas do MODIF"
        - "modificações hídricas"
        - "modificação hídrica"
        - "operação hídrica"
        - "modificações hidrelétricas"
        - "alterações hidrelétricas"
        - "modificações da usina 1"
        - "modificações da usina ITAIPU"
        - "volume mínimo das usinas"
        - "volumes mínimos das usinas"
        - "volume máximo das usinas"
        - "volumes máximos das usinas"
        - "vazão mínima da usina"
        - "vazões mínimas das usinas"
        - "vazão máxima da usina"
        - "vazões máximas das usinas"
        - "canal de fuga das usinas"
        - "nível de montante"
        - "nível montante"
        - "turbinamento máximo"
        - "turbinamento mínimo"
        - "potência efetiva hidrelétrica"
        - "indisponibilidades programadas das hidrelétricas"
        - "indisponibilidade programada"
        - "indisponibilidade forçada"
        - "ajustes operacionais da usina"
        - "condições de operação hídrica"
        - "parâmetros operacionais das hidrelétricas"
        - "dados de operação hídrica do MODIF"
        
        Termos-chave: modif, modificação hídrica, modificações hídricas, operação hídrica, modificação hidrelétrica, volume mínimo, volume máximo, vazão mínima, vazão máxima, canal de fuga, nível montante, turbinamento, potência efetiva hidrelétrica, indisponibilidade programada, indisponibilidade forçada.
        """
