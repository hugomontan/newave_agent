"""
Tool para consultar informações cadastrais das usinas hidrelétricas do HIDR.DAT.
Acessa dados físicos e operacionais básicos das usinas hidrelétricas.
"""
from backend.newave.tools.base import NEWAVETool
from inewave.newave import Hidr
import os
import pandas as pd
import re
from typing import Dict, Any, Optional
from difflib import SequenceMatcher
from backend.newave.config import debug_print, safe_print


class HidrCadastroTool(NEWAVETool):
    """
    Tool para consultar informações cadastrais das usinas hidrelétricas do HIDR.DAT.
    
    Dados disponíveis:
    - Informações básicas (nome, posto, submercado, empresa)
    - Volumes e cotas (mínimo, máximo, vertedouro)
    - Polinômios (volume-cota, cota-área)
    - Evaporação mensal
    - Conjuntos de máquinas (potência, vazão, queda nominal)
    - Produtibilidade, perdas, vazão mínima
    - Polinômios de jusante
    - Tipo de regulação
    - E mais de 60 campos no total
    """
    
    def get_name(self) -> str:
        return "HidrCadastroTool"
    
    def can_handle(self, query: str) -> bool:
        """
        Verifica se a query é sobre informações cadastrais de usinas hidrelétricas.
        
        Args:
            query: Query do usuário
            
        Returns:
            True se a tool pode processar a query
        """
        query_lower = query.lower()
        keywords = [
            "informações da usina",
            "informacoes da usina",
            "dados da usina",
            "cadastro da usina",
            "cadastro usina",
            "informações cadastrais",
            "informacoes cadastrais",
            "dados cadastrais",
            "características da usina",
            "caracteristicas da usina",
            "dados físicos da usina",
            "dados fisicos da usina",
            "hidr.dat",
            "hidr dat",
            "cadastro hidrelétrica",
            "cadastro hidreletrica",
            "usina de",
            "usina hidrelétrica",
            "usina hidreletrica",
            "volume mínimo",
            "volume minimo",
            "volume máximo",
            "volume maximo",
            "cota mínima",
            "cota minima",
            "cota máxima",
            "cota maxima",
            "produtibilidade",
            "potência nominal",
            "potencia nominal",
            "conjuntos de máquinas",
            "conjuntos de maquinas",
            "tipo de regulação",
            "tipo de regulacao",
        ]
        return any(kw in query_lower for kw in keywords)
    
    def _extract_usina_from_query(self, query: str, hidr: Hidr) -> Optional[tuple]:
        """
        Extrai código da usina da query usando HydraulicPlantMatcher unificado.
        
        Mesma lógica usada nas outras tools (vazoes_tool, etc).
        
        Args:
            query: Query do usuário
            hidr: Objeto Hidr já lido
            
        Returns:
            Tupla (código_usina, idx_real) onde:
            - código_usina: Código da usina (1-based)
            - idx_real: Índice real do DataFrame (pode não ser sequencial)
            Retorna None se não encontrado
        """
        cadastro = hidr.cadastro
        if cadastro is None or cadastro.empty:
            debug_print("[TOOL] ⚠️ Cadastro vazio ou inexistente")
            return None
        
        # Usar a mesma lógica das outras tools: passar o DataFrame diretamente
        # O matcher já sabe como lidar com DataFrames que têm codigo_usina e nome_usina
        # Se não tiver essas colunas, o matcher vai tentar usar o índice
        
        # Garantir que temos a coluna nome_usina (necessária para o matcher)
        if 'nome_usina' not in cadastro.columns:
            debug_print("[TOOL] ⚠️ Coluna 'nome_usina' não encontrada no cadastro")
            return None
        
        # Se não tiver codigo_usina, usar o índice como código (comum no HIDR.DAT)
        # IMPORTANTE: Adicionar 1 ao índice para corresponder ao código do CSV
        if 'codigo_usina' not in cadastro.columns:
            cadastro = cadastro.copy()
            # Tentar usar o índice como código (adicionando 1)
            try:
                cadastro['codigo_usina'] = cadastro.index + 1
                if cadastro['codigo_usina'].dtype != 'int64':
                    cadastro['codigo_usina'] = cadastro['codigo_usina'].astype(int)
            except (ValueError, TypeError):
                # Fallback: índice sequencial começando de 1
                cadastro['codigo_usina'] = range(1, len(cadastro) + 1)
        
        from backend.newave.utils.hydraulic_plant_matcher import get_hydraulic_plant_matcher
        
        matcher = get_hydraulic_plant_matcher()
        result = matcher.extract_plant_from_query(
            query=query,
            available_plants=cadastro,
            return_format="tupla",
            threshold=0.5
        )
        
        return result
    
    def _format_usina_data(self, row: pd.Series, codigo: int) -> Dict[str, Any]:
        """
        Formata os dados de uma usina para um dicionário JSON-serializable.
        
        Args:
            row: Linha do DataFrame do cadastro
            codigo: Código da usina
            
        Returns:
            Dicionário com todos os dados formatados
        """
        dados = {
            'codigo_usina': codigo,
            'nome_usina': str(row.get('nome_usina', '')).strip() if pd.notna(row.get('nome_usina')) else None,
        }
        
        # Informações básicas
        campos_basicos = [
            'posto', 'submercado', 'empresa', 'codigo_usina_jusante', 'desvio',
            'data', 'observacao', 'tipo_regulacao'
        ]
        
        for campo in campos_basicos:
            valor = row.get(campo)
            if pd.notna(valor):
                if isinstance(valor, (int, float)):
                    dados[campo] = int(valor) if isinstance(valor, float) and valor.is_integer() else float(valor)
                else:
                    dados[campo] = str(valor).strip()
        
        # Volumes (hm³)
        volumes = {
            'volume_minimo': 'hm³',
            'volume_maximo': 'hm³',
            'volume_vertedouro': 'hm³',
            'volume_desvio': 'hm³',
            'volume_referencia': 'hm³',
        }
        
        for campo, unidade in volumes.items():
            valor = row.get(campo)
            if pd.notna(valor):
                dados[campo] = float(valor)
                dados[f'{campo}_unidade'] = unidade
        
        # Cotas (m)
        cotas = {
            'cota_minima': 'm',
            'cota_maxima': 'm',
            'canal_fuga_medio': 'm',
        }
        
        for campo, unidade in cotas.items():
            valor = row.get(campo)
            if pd.notna(valor):
                dados[campo] = float(valor)
                dados[f'{campo}_unidade'] = unidade
        
        # Polinômios Volume-Cota (coeficientes a0 a a4)
        polinomio_vc = {}
        for i in range(5):
            campo = f'a{i}_volume_cota'
            valor = row.get(campo)
            if pd.notna(valor):
                polinomio_vc[f'a{i}'] = float(valor)
        
        if polinomio_vc:
            dados['polinomio_volume_cota'] = polinomio_vc
        
        # Polinômios Cota-Área (coeficientes a0 a a4)
        polinomio_ca = {}
        for i in range(5):
            campo = f'a{i}_cota_area'
            valor = row.get(campo)
            if pd.notna(valor):
                polinomio_ca[f'a{i}'] = float(valor)
        
        if polinomio_ca:
            dados['polinomio_cota_area'] = polinomio_ca
        
        # Evaporação mensal (mm)
        evaporacao = {}
        meses = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
        for mes in meses:
            campo = f'evaporacao_{mes}'
            valor = row.get(campo)
            if pd.notna(valor):
                evaporacao[mes.lower()] = float(valor)
        
        if evaporacao:
            dados['evaporacao_mensal'] = evaporacao
            dados['evaporacao_unidade'] = 'mm'
        
        # Conjuntos de máquinas
        numero_conjuntos = row.get('numero_conjuntos_maquinas')
        if pd.notna(numero_conjuntos):
            numero_conjuntos = int(numero_conjuntos)
            dados['numero_conjuntos_maquinas'] = numero_conjuntos
            
            conjuntos = []
            for i in range(1, 6):  # Até 5 conjuntos
                maq_col = f'maquinas_conjunto_{i}'
                pot_col = f'potencia_nominal_conjunto_{i}'
                queda_col = f'queda_nominal_conjunto_{i}'
                vazao_col = f'vazao_nominal_conjunto_{i}'
                
                maquinas = row.get(maq_col)
                potencia = row.get(pot_col)
                queda = row.get(queda_col)
                vazao = row.get(vazao_col)
                
                if pd.notna(maquinas) or pd.notna(potencia) or pd.notna(queda) or pd.notna(vazao):
                    conjunto = {
                        'numero': i,
                        'maquinas': int(maquinas) if pd.notna(maquinas) else None,
                        'potencia_nominal': float(potencia) if pd.notna(potencia) else None,
                        'potencia_nominal_unidade': 'MWmed' if pd.notna(potencia) else None,
                        'queda_nominal': float(queda) if pd.notna(queda) else None,
                        'queda_nominal_unidade': 'm' if pd.notna(queda) else None,
                        'vazao_nominal': float(vazao) if pd.notna(vazao) else None,
                        'vazao_nominal_unidade': 'm³/s' if pd.notna(vazao) else None,
                    }
                    
                    conjuntos.append(conjunto)
            
            if conjuntos:
                dados['conjuntos_maquinas'] = conjuntos
        
        # Características operacionais
        campos_operacionais = {
            'produtibilidade_especifica': None,
            'perdas': None,
            'vazao_minima_historica': 'm³/s',
            'numero_polinomios_jusante': None,
            'influencia_vertimento_canal_fuga': None,
            'fator_carga_maximo': '%',
            'fator_carga_minimo': '%',
            'numero_unidades_base': None,
            'tipo_turbina': None,
            'representacao_conjunto': None,
            'teif': '%',
            'ip': '%',
            'tipo_perda': None,
        }
        
        for campo, unidade in campos_operacionais.items():
            valor = row.get(campo)
            if pd.notna(valor):
                if isinstance(valor, (int, float)):
                    dados[campo] = int(valor) if isinstance(valor, float) and valor.is_integer() else float(valor)
                else:
                    dados[campo] = str(valor).strip()
                
                if unidade:
                    dados[f'{campo}_unidade'] = unidade
        
        # Polinômios de jusante (até 6 polinômios)
        numero_polinjus = row.get('numero_polinomios_jusante')
        if pd.notna(numero_polinjus):
            numero_polinjus = int(numero_polinjus)
            if numero_polinjus > 0:
                polinomios_jusante = []
                
                for i in range(1, 7):  # Até 6 polinômios
                    polinomio = {}
                    tem_coeficientes = False
                    
                    # Coeficientes a0 a a4
                    for j in range(5):
                        campo = f'a{j}_jusante_{i}'
                        valor = row.get(campo)
                        if pd.notna(valor):
                            polinomio[f'a{j}'] = float(valor)
                            tem_coeficientes = True
                    
                    # Referência
                    campo_ref = f'referencia_jusante_{i}'
                    valor_ref = row.get(campo_ref)
                    if pd.notna(valor_ref):
                        polinomio['referencia'] = float(valor_ref)
                    
                    if tem_coeficientes:
                        polinomio['numero'] = i
                        polinomios_jusante.append(polinomio)
                
                if polinomios_jusante:
                    dados['polinomios_jusante'] = polinomios_jusante
        
        return dados
    
    def execute(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Executa a consulta de informações cadastrais de usinas hidrelétricas.
        
        Fluxo:
        1. Verifica se HIDR.DAT existe
        2. Lê o arquivo usando inewave
        3. Identifica a usina da query usando cross-validation
        4. Retorna todas as informações disponíveis sobre a usina
        """
        debug_print(f"[TOOL] {self.get_name()}: Iniciando execução...")
        debug_print(f"[TOOL] Query: {query[:100]}")
        debug_print(f"[TOOL] Deck path: {self.deck_path}")
        
        try:
            # ETAPA 1: Verificar existência do arquivo
            debug_print("[TOOL] ETAPA 1: Verificando existência do arquivo HIDR.DAT...")
            hidr_path = os.path.join(self.deck_path, "HIDR.DAT")
            
            if not os.path.exists(hidr_path):
                hidr_path_lower = os.path.join(self.deck_path, "hidr.dat")
                if os.path.exists(hidr_path_lower):
                    hidr_path = hidr_path_lower
                else:
                    safe_print(f"[TOOL] ❌ Arquivo HIDR.DAT não encontrado")
                    return {
                        "success": False,
                        "error": f"Arquivo HIDR.DAT não encontrado em {self.deck_path}",
                        "tool": self.get_name()
                    }
            
            debug_print(f"[TOOL] ✅ Arquivo encontrado: {hidr_path}")
            
            # ETAPA 2: Ler arquivo usando inewave
            debug_print("[TOOL] ETAPA 2: Lendo arquivo com inewave...")
            hidr = Hidr.read(hidr_path)
            debug_print("[TOOL] ✅ Arquivo lido com sucesso")
            
            # ETAPA 3: Verificar se há dados
            cadastro = hidr.cadastro
            if cadastro is None or cadastro.empty:
                debug_print("[TOOL] ⚠️ Nenhuma usina encontrada no cadastro")
                return {
                    "success": False,
                    "error": "Nenhuma usina encontrada no arquivo HIDR.DAT",
                    "tool": self.get_name()
                }
            
            debug_print(f"[TOOL] ✅ {len(cadastro)} usina(s) encontrada(s) no cadastro")
            
            # ETAPA 4: Identificar usina da query
            debug_print("[TOOL] ETAPA 4: Identificando usina da query...")
            resultado = self._extract_usina_from_query(query, hidr)
            
            if resultado is None:
                debug_print("[TOOL] ⚠️ Nenhuma usina específica identificada")
                return {
                    "success": False,
                    "error": "Não foi possível identificar qual usina consultar. Por favor, especifique o nome ou código da usina.",
                    "total_usinas": len(cadastro),
                    "tool": self.get_name()
                }
            
            codigo_usina, idx_real = resultado
            debug_print(f"[TOOL] ✅ Usina identificada: código CSV={codigo_usina}, índice DataFrame={idx_real}")
            
            # IMPORTANTE: codigo_usina vem do CSV (fonte de verdade)
            # idx_real vem do DataFrame e pode ser diferente do código
            
            # ETAPA 5: Obter dados da usina
            debug_print(f"[TOOL] ETAPA 5: Obtendo dados da usina código CSV={codigo_usina} (idx DataFrame={idx_real})...")
            
            # SEMPRE buscar pelo nome no DataFrame original usando o nome do CSV
            # Isso garante que encontramos a usina correta mesmo com códigos desalinhados
            from backend.newave.utils.hydraulic_plant_matcher import get_hydraulic_plant_matcher
            matcher = get_hydraulic_plant_matcher()
            
            if codigo_usina not in matcher.code_to_names:
                safe_print(f"[TOOL] ❌ Código CSV {codigo_usina} não encontrado no code_to_names")
                return {
                    "success": False,
                    "error": f"Código {codigo_usina} não encontrado no mapeamento CSV",
                    "tool": self.get_name()
                }
            
            nome_arquivo_csv, _, _ = matcher.code_to_names[codigo_usina]
            debug_print(f"[TOOL]   Buscando usina '{nome_arquivo_csv}' no DataFrame original pelo nome")
            
            # Buscar pelo nome no DataFrame original
            nome_upper = nome_arquivo_csv.upper().strip()
            row = None
            idx_real_encontrado = None
            
            for idx, df_row in cadastro.iterrows():
                nome_df = str(df_row.get('nome_usina', '')).upper().strip()
                if nome_df == nome_upper:
                    row = df_row
                    idx_real_encontrado = idx
                    debug_print(f"[TOOL] ✅ Usina encontrada no DataFrame original: idx={idx_real_encontrado}, nome='{nome_df}'")
                    break
            
            if row is None:
                safe_print(f"[TOOL] ❌ Usina '{nome_arquivo_csv}' não encontrada no DataFrame original")
                return {
                    "success": False,
                    "error": f"Usina '{nome_arquivo_csv}' (código CSV {codigo_usina}) encontrada no CSV mas não no arquivo HIDR.DAT",
                    "tool": self.get_name()
                }
            
            # Usar o idx_real encontrado (não o que veio do matcher)
            idx_real = idx_real_encontrado
            
            dados_usina = self._format_usina_data(row, codigo_usina)
            
            debug_print(f"[TOOL] ✅ Dados da usina '{dados_usina.get('nome_usina', 'N/A')}' extraídos com sucesso")
            
            # ETAPA 6: Estatísticas gerais
            stats = {
                'total_usinas_cadastro': len(cadastro),
                'campos_disponiveis': len(row.index),
            }
            
            # ETAPA 7: Obter metadados da usina selecionada para correção
            selected_plant = None
            if codigo_usina in matcher.code_to_names:
                nome_arquivo_csv, nome_completo_csv, _ = matcher.code_to_names[codigo_usina]
                selected_plant = {
                    "type": "hydraulic",
                    "codigo": codigo_usina,
                    "nome": nome_arquivo_csv,
                    "nome_completo": nome_completo_csv if nome_completo_csv else nome_arquivo_csv,
                    "tool_name": self.get_name()
                }
            
            # ETAPA 8: Formatar resultado
            debug_print("[TOOL] ETAPA 8: Formatando resultado...")
            
            result = {
                "success": True,
                "dados_usina": dados_usina,
                "stats": stats,
                "description": f"Informações cadastrais completas da usina {codigo_usina} ({dados_usina.get('nome_usina', 'N/A')}) do arquivo HIDR.DAT",
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
                "error": f"Erro ao processar HIDR.DAT: {str(e)}",
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
        Informações cadastrais de usinas hidrelétricas. Dados físicos e operacionais básicos das usinas hidrelétricas do HIDR.DAT.
        
        Queries que ativam esta tool:
        - "me de informacoes da usina de balbina"
        - "dados da usina de itaipu"
        - "informações cadastrais da usina X"
        - "cadastro da usina Y"
        - "características da usina Z"
        - "dados físicos da usina"
        - "volume mínimo da usina"
        - "volume máximo da usina"
        - "cota mínima da usina"
        - "cota máxima da usina"
        - "produtibilidade da usina"
        - "potência nominal da usina"
        - "conjuntos de máquinas da usina"
        - "tipo de regulação da usina"
        - "informações do hidr.dat da usina"
        
        Esta tool consulta o arquivo HIDR.DAT e retorna todas as informações cadastrais disponíveis sobre uma usina específica, incluindo:
        - Informações básicas (nome, posto, submercado, empresa)
        - Volumes e cotas (mínimo, máximo, vertedouro)
        - Polinômios (volume-cota, cota-área)
        - Evaporação mensal
        - Conjuntos de máquinas (potência, vazão, queda nominal)
        - Produtibilidade, perdas, vazão mínima
        - Polinômios de jusante
        - Tipo de regulação
        - E mais de 60 campos no total
        
        A tool identifica automaticamente a usina mencionada na query através de matching inteligente:
        - Busca por código numérico explícito
        - Busca por nome completo da usina
        - Busca por similaridade de strings
        - Busca por palavras-chave do nome
        
        Termos-chave: hidr.dat, cadastro hidrelétrica, informações cadastrais, dados cadastrais, características da usina, dados físicos da usina, volume mínimo, volume máximo, cota mínima, cota máxima, produtibilidade, potência nominal, conjuntos de máquinas, tipo de regulação.
        """

