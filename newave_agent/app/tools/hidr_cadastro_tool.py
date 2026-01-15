"""
Tool para consultar informações cadastrais das usinas hidrelétricas do HIDR.DAT.
Acessa dados físicos e operacionais básicos das usinas hidrelétricas.
"""
from app.tools.base import NEWAVETool
from inewave.newave import Hidr
import os
import pandas as pd
import re
from typing import Dict, Any, Optional
from difflib import SequenceMatcher


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
        Extrai código da usina da query usando cross-validation com o arquivo.
        Busca por número ou nome da usina com matching inteligente.
        
        Args:
            query: Query do usuário
            hidr: Objeto Hidr já lido
            
        Returns:
            Tupla (código_usina, idx_real) onde:
            - código_usina: Código da usina (1-based)
            - idx_real: Índice real do DataFrame (pode não ser sequencial)
            Retorna None se não encontrado
        """
        query_lower = query.lower()
        
        # Verificar se há cadastro
        cadastro = hidr.cadastro
        if cadastro is None or cadastro.empty:
            print("[TOOL] ⚠️ Cadastro vazio ou inexistente")
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
                    # Buscar a usina pelo código no cadastro
                    # Precisamos encontrar o índice real do DataFrame
                    for idx, row in cadastro.iterrows():
                        codigo_calculado = idx + 1
                        if codigo_calculado == codigo:
                            nome = str(row.get('nome_usina', '')).strip()
                            if nome:  # Só considerar se tiver nome
                                print(f"[TOOL] ✅ Código {codigo} encontrado por padrão numérico: '{nome}' (idx_real={idx})")
                                return (codigo, idx)
                except (ValueError, IndexError):
                    continue
        
        # ETAPA 2: Buscar por nome da usina
        print(f"[TOOL] Buscando usina por nome na query: '{query}'")
        print(f"[TOOL] Total de usinas no cadastro: {len(cadastro)}")
        
        # Palavras comuns a ignorar
        palavras_ignorar = {'de', 'da', 'do', 'das', 'dos', 'e', 'a', 'o', 'as', 'os', 'em', 'na', 'no', 'nas', 'nos', 'a', 'à', 'ao', 'aos', 'informacoes', 'informações', 'dados', 'usina', 'hidrelétrica', 'hidreletrica'}
        
        # Extrair palavras significativas da query
        palavras_query = [p for p in query_lower.split() if len(p) > 2 and p not in palavras_ignorar]
        print(f"[TOOL] Palavras significativas extraídas da query: {palavras_query}")
        
        # Lista todas as usinas disponíveis
        print(f"[TOOL] Usinas disponíveis no arquivo:")
        usinas_list = []
        for idx, row in cadastro.iterrows():
            codigo = idx + 1  # Código = índice + 1
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
                # Verificar se está como palavra completa (não parte de outra palavra)
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
        print(f"[TOOL] {self.get_name()}: Iniciando execução...")
        print(f"[TOOL] Query: {query[:100]}")
        print(f"[TOOL] Deck path: {self.deck_path}")
        
        try:
            # ETAPA 1: Verificar existência do arquivo
            print("[TOOL] ETAPA 1: Verificando existência do arquivo HIDR.DAT...")
            hidr_path = os.path.join(self.deck_path, "HIDR.DAT")
            
            if not os.path.exists(hidr_path):
                hidr_path_lower = os.path.join(self.deck_path, "hidr.dat")
                if os.path.exists(hidr_path_lower):
                    hidr_path = hidr_path_lower
                else:
                    print(f"[TOOL] ❌ Arquivo HIDR.DAT não encontrado")
                    return {
                        "success": False,
                        "error": f"Arquivo HIDR.DAT não encontrado em {self.deck_path}",
                        "tool": self.get_name()
                    }
            
            print(f"[TOOL] ✅ Arquivo encontrado: {hidr_path}")
            
            # ETAPA 2: Ler arquivo usando inewave
            print("[TOOL] ETAPA 2: Lendo arquivo com inewave...")
            hidr = Hidr.read(hidr_path)
            print("[TOOL] ✅ Arquivo lido com sucesso")
            
            # ETAPA 3: Verificar se há dados
            cadastro = hidr.cadastro
            if cadastro is None or cadastro.empty:
                print("[TOOL] ⚠️ Nenhuma usina encontrada no cadastro")
                return {
                    "success": False,
                    "error": "Nenhuma usina encontrada no arquivo HIDR.DAT",
                    "tool": self.get_name()
                }
            
            print(f"[TOOL] ✅ {len(cadastro)} usina(s) encontrada(s) no cadastro")
            
            # ETAPA 4: Identificar usina da query
            print("[TOOL] ETAPA 4: Identificando usina da query...")
            resultado = self._extract_usina_from_query(query, hidr)
            
            if resultado is None:
                print("[TOOL] ⚠️ Nenhuma usina específica identificada")
                return {
                    "success": False,
                    "error": "Não foi possível identificar qual usina consultar. Por favor, especifique o nome ou código da usina.",
                    "total_usinas": len(cadastro),
                    "tool": self.get_name()
                }
            
            codigo_usina, idx_real = resultado
            print(f"[TOOL] ✅ Usina identificada: código {codigo_usina}, índice real {idx_real}")
            
            # ETAPA 5: Obter dados da usina
            print(f"[TOOL] ETAPA 5: Obtendo dados da usina {codigo_usina} (idx_real={idx_real})...")
            
            # Usar o índice real do DataFrame para acessar a linha correta
            # Como idx_real vem de iterrows(), ele sempre existe no index do DataFrame
            try:
                row = cadastro.loc[idx_real]
                # Validar que pegamos a usina correta pelo nome
                nome_encontrado = str(row.get('nome_usina', '')).strip()
                print(f"[TOOL] ✅ Linha acessada: '{nome_encontrado}' (idx_real={idx_real})")
            except (KeyError, IndexError) as e:
                print(f"[TOOL] ❌ Erro ao acessar linha com índice {idx_real}: {e}")
                return {
                    "success": False,
                    "error": f"Erro ao acessar dados da usina {codigo_usina} (índice {idx_real}): {str(e)}",
                    "tool": self.get_name()
                }
            
            dados_usina = self._format_usina_data(row, codigo_usina)
            
            print(f"[TOOL] ✅ Dados da usina '{dados_usina.get('nome_usina', 'N/A')}' extraídos com sucesso")
            
            # ETAPA 6: Estatísticas gerais
            stats = {
                'total_usinas_cadastro': len(cadastro),
                'campos_disponiveis': len(row.index),
            }
            
            # ETAPA 7: Formatar resultado
            print("[TOOL] ETAPA 7: Formatando resultado...")
            
            return {
                "success": True,
                "dados_usina": dados_usina,
                "stats": stats,
                "description": f"Informações cadastrais completas da usina {codigo_usina} ({dados_usina.get('nome_usina', 'N/A')}) do arquivo HIDR.DAT",
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

