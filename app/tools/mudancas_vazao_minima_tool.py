"""
Tool para análise de mudanças de vazão mínima (VAZMIN/VAZMINT) entre decks no modo multideck.
Foca especificamente em identificar e comparar variações de vazão mínima entre dezembro e janeiro.
"""
from app.tools.base import NEWAVETool
from inewave.newave import Modif
import os
import pandas as pd
from typing import Dict, Any, List, Optional
from app.utils.deck_loader import get_december_deck_path, get_january_deck_path


class MudancasVazaoMinimaTool(NEWAVETool):
    """
    Tool especializada para análise de mudanças de vazão mínima entre decks.
    
    Funcionalidades:
    - Lista todas as mudanças de VAZMIN/VAZMINT entre os dois decks
    - Identifica mudanças (variações de valor, novos registros, remoções)
    - Ordena mudanças por magnitude
    - Retorna apenas as mudanças (não todos os registros)
    """
    
    def get_name(self) -> str:
        return "MudancasVazaoMinimaTool"
    
    def can_handle(self, query: str) -> bool:
        """
        Verifica se a query é sobre análise de mudanças de vazão mínima.
        
        Args:
            query: Query do usuário
            
        Returns:
            True se a tool pode processar a query
        """
        query_lower = query.lower()
        keywords = [
            "mudanças vazão mínima",
            "mudancas vazao minima",
            "mudanças vazmin",
            "mudancas vazmin",
            "variação vazão mínima",
            "variacao vazao minima",
            "análise vazão mínima",
            "analise vazao minima",
            "mudanças vazmint",
            "mudancas vazmint",
            "mudanças vazao minima",
            "mudancas vazao minima",
        ]
        return any(kw in query_lower for kw in keywords)
    
    def execute(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Executa a análise de mudanças de vazão mínima entre os dois decks.
        
        Fluxo:
        1. Carrega caminhos dos decks de dezembro e janeiro
        2. Lê MODIF.DAT de ambos os decks
        3. Filtra apenas registros de VAZMIN e VAZMINT
        4. Compara e identifica mudanças
        5. Ordena mudanças por magnitude
        6. Retorna dados formatados
        """
        print(f"[TOOL] {self.get_name()}: Iniciando análise de mudanças de vazão mínima...")
        print(f"[TOOL] Query: {query[:100]}")
        
        try:
            # ETAPA 1: Carregar caminhos dos decks
            print("[TOOL] ETAPA 1: Carregando caminhos dos decks...")
            try:
                deck_december_path = get_december_deck_path()
                deck_january_path = get_january_deck_path()
                deck_december_name = "Dezembro 2025"
                deck_january_name = "Janeiro 2026"
            except FileNotFoundError as e:
                print(f"[TOOL] ❌ Erro ao carregar decks: {e}")
                return {
                    "success": False,
                    "error": f"Decks não encontrados: {str(e)}",
                    "tool": self.get_name()
                }
            
            print(f"[TOOL] ✅ Deck Dezembro: {deck_december_path}")
            print(f"[TOOL] ✅ Deck Janeiro: {deck_january_path}")
            
            # ETAPA 2: Ler MODIF.DAT de ambos os decks
            print("[TOOL] ETAPA 2: Lendo arquivos MODIF.DAT...")
            modif_dec = self._read_modif_file(deck_december_path)
            modif_jan = self._read_modif_file(deck_january_path)
            
            if modif_dec is None:
                return {
                    "success": False,
                    "error": f"Arquivo MODIF.DAT não encontrado em {deck_december_path}",
                    "tool": self.get_name()
                }
            
            if modif_jan is None:
                return {
                    "success": False,
                    "error": f"Arquivo MODIF.DAT não encontrado em {deck_january_path}",
                    "tool": self.get_name()
                }
            
            # ETAPA 3: Criar mapeamento código -> nome das usinas
            print("[TOOL] ETAPA 3: Criando mapeamento código -> nome das usinas...")
            mapeamento_codigo_nome = self._create_codigo_nome_mapping(modif_dec, modif_jan)
            print(f"[TOOL] ✅ Mapeamento criado: {len(mapeamento_codigo_nome)} usinas mapeadas")
            
            # ETAPA 4: Filtrar apenas registros de VAZMIN e VAZMINT
            print("[TOOL] ETAPA 4: Filtrando registros de VAZMIN e VAZMINT...")
            vazmin_dec = self._extract_vazmin_records(modif_dec)
            vazmin_jan = self._extract_vazmin_records(modif_jan)
            
            print(f"[TOOL] ✅ Registros VAZMIN/VAZMINT Dezembro: {len(vazmin_dec)}")
            print(f"[TOOL] ✅ Registros VAZMIN/VAZMINT Janeiro: {len(vazmin_jan)}")
            
            # ETAPA 5: Comparar e identificar mudanças
            print("[TOOL] ETAPA 5: Identificando mudanças...")
            mudancas = self._identify_changes(
                vazmin_dec, vazmin_jan, 
                deck_december_name, deck_january_name, 
                mapeamento_codigo_nome
            )
            
            print(f"[TOOL] ✅ Total de mudanças identificadas: {len(mudancas)}")
            
            # ETAPA 6: Ordenar por tipo e magnitude
            print("[TOOL] ETAPA 6: Ordenando mudanças por tipo e magnitude...")
            ordem_tipo = {"aumento": 0, "queda": 1, "remocao": 2, "novo": 3}
            mudancas_ordenadas = sorted(mudancas, key=lambda x: (
                ordem_tipo.get(x.get('tipo_mudanca', 'N/A'), 99),
                -abs(x.get('magnitude_mudanca', 0))  # Maior magnitude primeiro dentro do mesmo tipo
            ))
            
            # ETAPA 7: Calcular estatísticas
            stats = self._calculate_stats(vazmin_dec, vazmin_jan, mudancas)
            
            # ETAPA 8: Formatar tabela de comparação
            comparison_table = []
            for mudanca in mudancas_ordenadas:
                tipo_mudanca = mudanca.get("tipo_mudanca", "desconhecido")
                nome_usina = mudanca.get("nome_usina", "N/A")
                codigo = mudanca.get("codigo_usina")
                
                # Melhorar nome usando mapeamento
                if codigo and codigo in mapeamento_codigo_nome:
                    nome_mapeado = mapeamento_codigo_nome[codigo]
                    if nome_mapeado and nome_mapeado != "N/A" and not nome_mapeado.startswith("Usina "):
                        nome_usina = nome_mapeado
                    elif nome_usina == "N/A" or nome_usina.startswith("Usina "):
                        nome_usina = nome_mapeado
                
                comparison_table.append({
                    "nome_usina": nome_usina,
                    "codigo_usina": codigo,
                    "tipo_mudanca": tipo_mudanca,
                    "tipo_vazao": mudanca.get("tipo_vazao"),  # "VAZMIN" ou "VAZMINT"
                    "vazao_dezembro": mudanca.get("vazao_dezembro"),
                    "vazao_janeiro": mudanca.get("vazao_janeiro"),
                    "diferenca": mudanca.get("diferenca"),
                    "magnitude": round(mudanca.get("magnitude_mudanca", 0), 2),
                    "periodo_inicio": mudanca.get("periodo_inicio", "N/A"),
                    "periodo_fim": mudanca.get("periodo_fim", "N/A")
                })
            
            return {
                "success": True,
                "is_comparison": True,
                "tool": self.get_name(),
                "comparison_table": comparison_table,
                "stats": stats,
                "description": f"Análise de {len(mudancas_ordenadas)} mudanças de vazão mínima entre {deck_december_name} e {deck_january_name}, ordenadas por magnitude."
            }
            
        except Exception as e:
            print(f"[TOOL] ❌ Erro ao processar: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": f"Erro ao processar análise de vazão mínima: {str(e)}",
                "error_type": type(e).__name__,
                "tool": self.get_name()
            }
    
    def _read_modif_file(self, deck_path) -> Optional[Modif]:
        """
        Lê o arquivo MODIF.DAT de um deck.
        
        Args:
            deck_path: Caminho do diretório do deck
            
        Returns:
            Objeto Modif ou None se não encontrado
        """
        modif_path = os.path.join(deck_path, "MODIF.DAT")
        if not os.path.exists(modif_path):
            modif_path_lower = os.path.join(deck_path, "modif.dat")
            if os.path.exists(modif_path_lower):
                modif_path = modif_path_lower
            else:
                print(f"[TOOL] ⚠️ Arquivo MODIF.DAT não encontrado em {deck_path}")
                return None
        
        try:
            modif = Modif.read(modif_path)
            return modif
        except Exception as e:
            print(f"[TOOL] ❌ Erro ao ler MODIF.DAT: {e}")
            return None
    
    def _create_codigo_nome_mapping(self, modif_dec: Modif, modif_jan: Modif) -> Dict[int, str]:
        """
        Cria mapeamento de código de usina para nome a partir dos registros USINA.
        Usa modif.usina() para obter nomes das usinas modificadas.
        
        Args:
            modif_dec: Objeto Modif do deck de dezembro
            modif_jan: Objeto Modif do deck de janeiro
            
        Returns:
            Dicionário mapeando codigo_usina -> nome_usina
        """
        mapeamento = {}
        
        # Processar deck de dezembro
        if modif_dec is not None:
            usinas_dec = modif_dec.usina(df=True)
            if usinas_dec is not None and not usinas_dec.empty:
                if 'codigo' in usinas_dec.columns and 'nome' in usinas_dec.columns:
                    for _, row in usinas_dec.iterrows():
                        codigo = int(row['codigo'])
                        nome = str(row.get('nome', '')).strip()
                        if nome and nome != 'nan' and nome.lower() != 'none' and nome != '':
                            mapeamento[codigo] = nome
                            print(f"[TOOL] Mapeamento: {codigo} -> {nome}")
        
        # Processar deck de janeiro (sobrescreve se houver nome melhor)
        if modif_jan is not None:
            usinas_jan = modif_jan.usina(df=True)
            if usinas_jan is not None and not usinas_jan.empty:
                if 'codigo' in usinas_jan.columns and 'nome' in usinas_jan.columns:
                    for _, row in usinas_jan.iterrows():
                        codigo = int(row['codigo'])
                        nome = str(row.get('nome', '')).strip()
                        if nome and nome != 'nan' and nome.lower() != 'none' and nome != '':
                            # Sobrescrever se não existia ou se o nome é mais completo
                            if codigo not in mapeamento or len(nome) > len(mapeamento.get(codigo, '')):
                                mapeamento[codigo] = nome
                                print(f"[TOOL] Mapeamento: {codigo} -> {nome}")
        
        # Se ainda faltam nomes, tentar cruzar com HIDR.DAT
        codigos_sem_nome = [c for c in mapeamento.keys() if not mapeamento.get(c) or mapeamento.get(c).startswith("Usina ")]
        if codigos_sem_nome:
            print(f"[TOOL] ⚠️ {len(codigos_sem_nome)} usinas sem nome no MODIF, tentando HIDR.DAT...")
            try:
                from inewave.newave import Hidr
                deck_path_ref = get_december_deck_path()
                hidr_path = os.path.join(deck_path_ref, "HIDR.DAT")
                if not os.path.exists(hidr_path):
                    hidr_path = os.path.join(deck_path_ref, "hidr.dat")
                
                if os.path.exists(hidr_path):
                    hidr = Hidr.read(hidr_path)
                    if hidr.cadastro is not None and not hidr.cadastro.empty:
                        for _, hidr_row in hidr.cadastro.iterrows():
                            codigo_hidr = int(hidr_row.get('codigo_usina', 0))
                            if codigo_hidr in codigos_sem_nome:
                                nome_hidr = str(hidr_row.get('nome_usina', '')).strip()
                                if nome_hidr and nome_hidr != 'nan' and nome_hidr != '':
                                    mapeamento[codigo_hidr] = nome_hidr
                                    print(f"[TOOL] ✅ Nome do HIDR.DAT: {codigo_hidr} -> {nome_hidr}")
            except Exception as e:
                print(f"[TOOL] ⚠️ Erro ao ler HIDR.DAT para nomes: {e}")
        
        return mapeamento
    
    def _extract_vazmin_records(self, modif: Modif) -> List[Dict[str, Any]]:
        """
        Extrai registros de VAZMIN e VAZMINT do MODIF.
        Usa modificacoes_usina() para obter todos os registros com contexto completo.
        
        Args:
            modif: Objeto Modif
            
        Returns:
            Lista de dicionários com informações dos registros
        """
        registros = []
        
        # Obter lista de usinas modificadas
        usinas_df = modif.usina(df=True)
        if usinas_df is None or usinas_df.empty:
            return registros
        
        # Para cada usina, obter todas as modificações
        for _, usina_row in usinas_df.iterrows():
            codigo_usina = int(usina_row.get('codigo', 0))
            nome_usina = str(usina_row.get('nome', '')).strip()
            
            # Obter todas as modificações desta usina
            modificacoes = modif.modificacoes_usina(codigo_usina)
            if not modificacoes:
                continue
            
            # Processar cada modificação
            for registro in modificacoes:
                # Verificar se é VAZMIN ou VAZMINT
                tipo_registro = type(registro).__name__
                
                if 'Vazmin' in tipo_registro or 'VAZMIN' in tipo_registro:
                    # VAZMIN (sem data)
                    vazao_val = registro.vazao if hasattr(registro, 'vazao') else None
                    if vazao_val is not None:
                        registros.append({
                            "codigo_usina": codigo_usina,
                            "nome_usina": nome_usina if nome_usina else f"Usina {codigo_usina}",
                            "tipo_vazao": "VAZMIN",
                            "vazao": vazao_val,
                            "data_inicio": None,
                            "periodo_inicio": None,
                            "periodo_fim": None
                        })
                
                elif 'Vazmint' in tipo_registro or 'VAZMINT' in tipo_registro:
                    # VAZMINT (com data)
                    vazao_val = registro.vazao if hasattr(registro, 'vazao') else None
                    data_inicio = registro.data_inicio if hasattr(registro, 'data_inicio') else None
                    
                    periodo_inicio = self._format_date(data_inicio) if data_inicio else "N/A"
                    
                    registros.append({
                        "codigo_usina": codigo_usina,
                        "nome_usina": nome_usina if nome_usina else f"Usina {codigo_usina}",
                        "tipo_vazao": "VAZMINT",
                        "vazao": vazao_val,
                        "data_inicio": data_inicio,
                        "periodo_inicio": periodo_inicio,
                        "periodo_fim": None  # VAZMINT não tem data_fim explícita
                    })
        
        return registros
    
    def _identify_changes(
        self,
        vazmin_dec: List[Dict],
        vazmin_jan: List[Dict],
        deck_dec_name: str,
        deck_jan_name: str,
        mapeamento_codigo_nome: Dict[int, str]
    ) -> List[Dict[str, Any]]:
        """
        Identifica mudanças de vazão mínima entre os dois decks.
        
        Uma mudança é identificada quando:
        - Uma usina tem vazão diferente no mesmo período (mesmo tipo: VAZMIN ou VAZMINT)
        - Uma usina tem vazão em um deck mas não no outro
        - Uma usina tem VAZMIN em um deck e VAZMINT no outro
        
        Args:
            vazmin_dec: Lista de registros de dezembro
            vazmin_jan: Lista de registros de janeiro
            deck_dec_name: Nome do deck de dezembro
            deck_jan_name: Nome do deck de janeiro
            mapeamento_codigo_nome: Mapeamento código -> nome
            
        Returns:
            Lista de dicionários com informações sobre mudanças
        """
        mudancas = []
        
        # Criar índices para comparação eficiente
        # Para VAZMIN: chave = (codigo_usina, "VAZMIN", None)
        # Para VAZMINT: chave = (codigo_usina, "VAZMINT", periodo_inicio)
        def create_key(record):
            codigo = record.get("codigo_usina", 0)
            tipo = record.get("tipo_vazao", "VAZMIN")
            periodo = record.get("periodo_inicio")
            return (codigo, tipo, periodo)
        
        dec_indexed = {}
        for record in vazmin_dec:
            key = create_key(record)
            dec_indexed[key] = record
        
        jan_indexed = {}
        for record in vazmin_jan:
            key = create_key(record)
            jan_indexed[key] = record
        
        # Comparar registros
        all_keys = set(dec_indexed.keys()) | set(jan_indexed.keys())
        
        for key in all_keys:
            codigo_usina, tipo_vazao, periodo = key
            dec_record = dec_indexed.get(key)
            jan_record = jan_indexed.get(key)
            
            # Obter nome da usina (prioridade: mapeamento > registro)
            nome_usina = mapeamento_codigo_nome.get(codigo_usina)
            if not nome_usina or nome_usina.strip() == '':
                if dec_record is not None:
                    nome_temp = str(dec_record.get("nome_usina", '')).strip()
                    if nome_temp and nome_temp != 'nan' and nome_temp != '':
                        nome_usina = nome_temp
                if (not nome_usina or nome_usina.strip() == '') and jan_record is not None:
                    nome_temp = str(jan_record.get("nome_usina", '')).strip()
                    if nome_temp and nome_temp != 'nan' and nome_temp != '':
                        nome_usina = nome_temp
            
            # Se ainda não encontrou, usar código
            if not nome_usina or nome_usina.strip() == '':
                nome_usina = f'Usina {codigo_usina}'
            
            # Extrair valores de vazão
            vazao_dec_val = None
            vazao_jan_val = None
            
            if dec_record is not None:
                vazao_dec_val = self._sanitize_number(dec_record.get("vazao"))
            if jan_record is not None:
                vazao_jan_val = self._sanitize_number(jan_record.get("vazao"))
            
            # Normalizar valores None para 0 para comparação
            vazao_dec_normalized = vazao_dec_val if vazao_dec_val is not None else 0.0
            vazao_jan_normalized = vazao_jan_val if vazao_jan_val is not None else 0.0
            
            # Se ambos são zero, não é mudança significativa
            if abs(vazao_dec_normalized) < 0.01 and abs(vazao_jan_normalized) < 0.01:
                continue
            
            # Identificar tipo de mudança
            tipo_mudanca = None
            magnitude_mudanca = 0
            
            if dec_record is None and jan_record is not None:
                # Novo registro em janeiro
                if vazao_jan_val is not None and abs(vazao_jan_val) > 0.01:
                    tipo_mudanca = "novo"
                    magnitude_mudanca = abs(vazao_jan_val)
            elif dec_record is not None and jan_record is None:
                # Registro removido em janeiro
                if vazao_dec_val is not None and abs(vazao_dec_val) > 0.01:
                    tipo_mudanca = "remocao"
                    magnitude_mudanca = abs(vazao_dec_val)
            elif dec_record is not None and jan_record is not None:
                # Registro existe em ambos - verificar se valor mudou
                if vazao_dec_val is not None and vazao_jan_val is not None:
                    diferenca_val = vazao_jan_val - vazao_dec_val
                    if abs(diferenca_val) > 0.01:  # Tolerância para diferenças numéricas
                        if diferenca_val > 0:
                            tipo_mudanca = "aumento"
                        else:
                            tipo_mudanca = "queda"
                        magnitude_mudanca = abs(diferenca_val)
                elif vazao_dec_val is None and vazao_jan_val is not None:
                    # Dezembro não tem valor, janeiro tem
                    if abs(vazao_jan_val) > 0.01:
                        tipo_mudanca = "novo"
                        magnitude_mudanca = abs(vazao_jan_val)
                elif vazao_dec_val is not None and vazao_jan_val is None:
                    # Janeiro não tem valor, dezembro tem
                    if abs(vazao_dec_val) > 0.01:
                        tipo_mudanca = "remocao"
                        magnitude_mudanca = abs(vazao_dec_val)
            
            # Se há mudança, adicionar à lista
            if tipo_mudanca is not None:
                mudanca = {
                    "codigo_usina": int(codigo_usina),
                    "nome_usina": str(nome_usina).strip(),
                    "tipo_mudanca": tipo_mudanca,
                    "tipo_vazao": tipo_vazao,
                    "periodo_inicio": periodo if periodo else "N/A",
                    "periodo_fim": None,  # VAZMINT não tem data_fim
                    "vazao_dezembro": round(vazao_dec_val, 2) if vazao_dec_val is not None else None,
                    "vazao_janeiro": round(vazao_jan_val, 2) if vazao_jan_val is not None else None,
                    "magnitude_mudanca": round(magnitude_mudanca, 2),
                    "diferenca": round(vazao_jan_val - vazao_dec_val, 2) if (
                        vazao_dec_val is not None and vazao_jan_val is not None
                    ) else None
                }
                mudancas.append(mudanca)
        
        return mudancas
    
    def _format_date(self, date_value) -> str:
        """
        Formata uma data para string no formato YYYY-MM.
        
        Args:
            date_value: Valor de data (datetime, Timestamp, ou None)
            
        Returns:
            String no formato "YYYY-MM"
        """
        if date_value is None or pd.isna(date_value):
            return "N/A"
        
        try:
            if hasattr(date_value, 'year') and hasattr(date_value, 'month'):
                return f"{date_value.year:04d}-{date_value.month:02d}"
            elif isinstance(date_value, str):
                return date_value
            else:
                return str(date_value)
        except:
            return str(date_value)
    
    def _sanitize_number(self, value) -> Optional[float]:
        """
        Sanitiza um valor numérico, retornando None se for NaN ou inválido.
        
        Args:
            value: Valor a sanitizar
            
        Returns:
            Float ou None
        """
        if value is None:
            return None
        
        try:
            float_val = float(value)
            if pd.isna(float_val):
                return None
            return float_val
        except (ValueError, TypeError):
            return None
    
    def _calculate_stats(
        self,
        vazmin_dec: List[Dict],
        vazmin_jan: List[Dict],
        mudancas: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calcula estatísticas sobre os registros de vazão mínima e mudanças.
        
        Args:
            vazmin_dec: Lista de registros de dezembro
            vazmin_jan: Lista de registros de janeiro
            mudancas: Lista de mudanças identificadas
            
        Returns:
            Dicionário com estatísticas
        """
        stats = {
            "total_registros_dezembro": len(vazmin_dec),
            "total_registros_janeiro": len(vazmin_jan),
            "total_mudancas": len(mudancas),
            "usinas_com_mudanca": len(set(m['codigo_usina'] for m in mudancas)),
            "tipos_mudanca": {}
        }
        
        # Contar por tipo de mudança
        for mudanca in mudancas:
            tipo = mudanca.get('tipo_mudanca', 'desconhecido')
            stats["tipos_mudanca"][tipo] = stats["tipos_mudanca"].get(tipo, 0) + 1
        
        # Estatísticas de magnitude
        if mudancas:
            magnitudes = [abs(m.get('magnitude_mudanca', 0)) for m in mudancas]
            stats["magnitude_maxima"] = round(max(magnitudes), 2)
            stats["magnitude_minima"] = round(min(magnitudes), 2)
            stats["magnitude_media"] = round(sum(magnitudes) / len(magnitudes), 2)
        else:
            stats["magnitude_maxima"] = 0
            stats["magnitude_minima"] = 0
            stats["magnitude_media"] = 0
        
        # Usinas únicas em cada deck
        stats["usinas_unicas_dezembro"] = len(set(r.get('codigo_usina', 0) for r in vazmin_dec))
        stats["usinas_unicas_janeiro"] = len(set(r.get('codigo_usina', 0) for r in vazmin_jan))
        
        return stats
    
    def get_description(self) -> str:
        """
        Retorna descrição da tool para uso pelo LLM.
        
        Returns:
            String com descrição detalhada
        """
        return """
        Mudanças em vazão mínima. Análise de variações de VAZMIN/VAZMINT (Vazão Mínima) entre decks no modo multideck.
        
        Esta tool é especializada em:
        - Identificar todas as mudanças de vazão mínima entre dezembro e janeiro
        - Ordenar mudanças por magnitude (maior variação primeiro)
        - Classificar tipos de mudança (aumento, queda, novo, remocao)
        - Retornar apenas as mudanças (não todos os registros)
        
        Queries que ativam esta tool:
        - "mudanças vazão mínima" ou "mudancas vazao minima"
        - "variação vazão mínima" ou "variacao vazao minima"
        - "análise vazão mínima" ou "analise vazao minima"
        - "mudanças vazmin" ou "mudancas vazmin"
        - "mudanças vazmint" ou "mudancas vazmint"
        
        Termos-chave: mudanças vazão mínima, variação vazão mínima, análise vazão mínima, mudancas vazao minima, variacao vazao minima, analise vazao minima, vazmin, vazmint, mudanças em vazões mínimas.
        """