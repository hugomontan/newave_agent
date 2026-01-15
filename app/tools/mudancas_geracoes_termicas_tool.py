"""
Tool para análise de mudanças de GTMIN entre decks no modo multideck.
Suporta comparação de N decks para análise histórica de GTMIN.
"""
from app.tools.base import NEWAVETool
from inewave.newave import Expt
import os
import pandas as pd
import re
from typing import Dict, Any, List, Optional
from app.utils.deck_loader import (
    list_available_decks,
    load_multiple_decks,
    get_deck_display_name,
)


class MudancasGeracoesTermicasTool(NEWAVETool):
    """
    Tool especializada para análise de mudanças de GTMIN entre decks.
    Suporta comparação de N decks.
    
    Funcionalidades:
    - Lista todas as mudanças de GTMIN entre os decks selecionados
    - Identifica mudanças (variações de valor, novos registros, remoções)
    - Ordena mudanças por magnitude
    - Retorna apenas as mudanças (não todos os registros)
    """
    
    def __init__(self, deck_path: str, selected_decks: Optional[List[str]] = None):
        """
        Inicializa a tool.
        
        Args:
            deck_path: Caminho do deck principal (para compatibilidade)
            selected_decks: Lista de nomes dos decks a comparar
        """
        super().__init__(deck_path)
        self.selected_decks = selected_decks or []
        self.deck_paths: Dict[str, str] = {}
        self.deck_display_names: Dict[str, str] = {}
        
        # Se não foram especificados decks, usar os dois mais recentes
        if not self.selected_decks:
            try:
                available = list_available_decks()
                if len(available) >= 2:
                    self.selected_decks = [d["name"] for d in available[-2:]]
                elif len(available) == 1:
                    self.selected_decks = [available[0]["name"]]
            except Exception:
                pass
        
        # Carregar caminhos dos decks
        if self.selected_decks:
            try:
                paths = load_multiple_decks(self.selected_decks)
                self.deck_paths = {name: str(path) for name, path in paths.items()}
                self.deck_display_names = {
                    name: get_deck_display_name(name) 
                    for name in self.selected_decks
                }
            except Exception as e:
                print(f"[TOOL] ⚠️ Erro ao carregar decks: {e}")
    
    def get_name(self) -> str:
        return "MudancasGeracoesTermicasTool"
    
    def can_handle(self, query: str) -> bool:
        """
        Verifica se a query é sobre análise de mudanças de GTMIN.
        
        Args:
            query: Query do usuário
            
        Returns:
            True se a tool pode processar a query
        """
        query_lower = query.lower()
        keywords = [
            "mudanças gtmin",
            "mudancas gtmin",
            "variação gtmin",
            "variacao gtmin",
            "variações gtmin",  # Plural
            "variacoes gtmin",  # Plural
            "variações de gtmin",  # Plural com "de"
            "variacoes de gtmin",  # Plural com "de"
            "variação de gtmin",  # Singular com "de"
            "variacao de gtmin",  # Singular com "de"
            "quais foram as variações de gtmin",  # Query específica
            "quais foram as variacoes de gtmin",  # Query específica
            "quais foram as variações gtmin",  # Query específica sem "de"
            "quais foram as variacoes gtmin",  # Query específica sem "de"
            "análise gtmin",
            "analise gtmin",
            "comparar gtmin",
            "comparação gtmin",
            "comparacao gtmin",
            "mudanças em gerações térmicas",
            "mudancas em geracoes termicas",
            "variações em gerações térmicas",
            "variacoes em geracoes termicas",
            "geração térmica mínima",
            "geracao termica minima",
        ]
        return any(kw in query_lower for kw in keywords)
    
    def execute(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Executa a análise de mudanças de GTMIN entre os decks selecionados.
        
        Fluxo:
        1. Usa decks selecionados (ou carrega automaticamente)
        2. Lê EXPT.DAT de todos os decks
        3. Filtra apenas registros de GTMIN
        4. Compara e identifica mudanças
        5. Ordena mudanças por magnitude
        6. Retorna dados formatados
        """
        print(f"[TOOL] {self.get_name()}: Iniciando análise de mudanças de GTMIN...")
        print(f"[TOOL] Query: {query[:100]}")
        print(f"[TOOL] Decks selecionados: {self.selected_decks}")
        
        try:
            # ETAPA 1: Verificar decks disponíveis
            print("[TOOL] ETAPA 1: Verificando decks...")
            
            if not self.deck_paths or len(self.deck_paths) < 2:
                return {
                    "success": False,
                    "error": "São necessários pelo menos 2 decks para comparação",
                    "tool": self.get_name()
                }
            
            # Verificar se há mais de 2 decks - usar matriz de comparação
            if len(self.selected_decks) > 2:
                print(f"[TOOL] ✅ {len(self.selected_decks)} decks detectados - usando matriz de comparação")
                return self._execute_multi_deck_matrix(query)
            
            # Para compatibilidade, usar primeiro e último deck (2 decks)
            deck_december_path = self.deck_paths.get(self.selected_decks[0])
            deck_january_path = self.deck_paths.get(self.selected_decks[-1])
            deck_december_name = self.deck_display_names.get(self.selected_decks[0], "Deck Anterior")
            deck_january_name = self.deck_display_names.get(self.selected_decks[-1], "Deck Atual")
            
            print(f"[TOOL] ✅ Deck Anterior: {deck_december_path} ({deck_december_name})")
            print(f"[TOOL] ✅ Deck Atual: {deck_january_path} ({deck_january_name})")
            
            # ETAPA 2: Ler EXPT.DAT de ambos os decks
            print("[TOOL] ETAPA 2: Lendo arquivos EXPT.DAT...")
            expt_dec = self._read_expt_file(deck_december_path)
            expt_jan = self._read_expt_file(deck_january_path)
            
            if expt_dec is None:
                return {
                    "success": False,
                    "error": f"Arquivo EXPT.DAT não encontrado em {deck_december_path}",
                    "tool": self.get_name()
                }
            
            if expt_jan is None:
                return {
                    "success": False,
                    "error": f"Arquivo EXPT.DAT não encontrado em {deck_january_path}",
                    "tool": self.get_name()
                }
            
            # ETAPA 3: Criar mapeamento código -> nome das usinas
            print("[TOOL] ETAPA 3: Criando mapeamento código -> nome das usinas...")
            mapeamento_codigo_nome = self._create_codigo_nome_mapping(expt_dec, expt_jan)
            print(f"[TOOL] ✅ Mapeamento criado: {len(mapeamento_codigo_nome)} usinas mapeadas")
            
            # ETAPA 3.5: Extrair usina da query (NOVO)
            print("[TOOL] ETAPA 3.5: Verificando se há filtro por usina na query...")
            codigo_usina_filtro = self._extract_usina_from_query(query, expt_dec, expt_jan, mapeamento_codigo_nome)
            if codigo_usina_filtro is not None:
                nome_usina_filtro = mapeamento_codigo_nome.get(codigo_usina_filtro, f"Usina {codigo_usina_filtro}")
                print(f"[TOOL] ✅ Filtro por usina detectado: {codigo_usina_filtro} - {nome_usina_filtro}")
            else:
                print("[TOOL] ℹ️ Nenhum filtro por usina detectado - retornando todas as mudanças")
            
            # ETAPA 4: Filtrar apenas registros de GTMIN
            print("[TOOL] ETAPA 4: Filtrando registros de GTMIN...")
            gtmin_dec = self._extract_gtmin_records(expt_dec)
            gtmin_jan = self._extract_gtmin_records(expt_jan)
            
            # Aplicar filtro por usina se especificado (NOVO)
            if codigo_usina_filtro is not None:
                gtmin_dec = gtmin_dec[gtmin_dec['codigo_usina'] == codigo_usina_filtro]
                gtmin_jan = gtmin_jan[gtmin_jan['codigo_usina'] == codigo_usina_filtro]
                print(f"[TOOL] ✅ Dados filtrados por usina {codigo_usina_filtro}")
            
            print(f"[TOOL] ✅ Registros GTMIN Dezembro: {len(gtmin_dec)}")
            print(f"[TOOL] ✅ Registros GTMIN Janeiro: {len(gtmin_jan)}")
            
            # ETAPA 5: Comparar e identificar mudanças
            print("[TOOL] ETAPA 5: Identificando mudanças...")
            mudancas = self._identify_changes(gtmin_dec, gtmin_jan, deck_december_name, deck_january_name, mapeamento_codigo_nome)
            
            print(f"[TOOL] ✅ Total de mudanças identificadas: {len(mudancas)}")
            
            # ETAPA 6: Ordenar por tipo e magnitude
            print("[TOOL] ETAPA 6: Ordenando mudanças por tipo e magnitude...")
            ordem_tipo = {"aumento": 0, "queda": 1, "remocao": 2, "novo": 3}
            mudancas_ordenadas = sorted(mudancas, key=lambda x: (
                ordem_tipo.get(x.get('tipo_mudanca', 'N/A'), 99),
                -abs(x.get('magnitude_mudanca', 0))  # Maior magnitude primeiro dentro do mesmo tipo
            ))
            
            # ETAPA 7: Calcular estatísticas
            stats = self._calculate_stats(gtmin_dec, gtmin_jan, mudancas)
            
            # ETAPA 7: Formatar tabela de comparação
            comparison_table = []
            for mudanca in mudancas_ordenadas:
                tipo_mudanca = mudanca.get("tipo_mudanca", "desconhecido")
                nome_usina = mudanca.get("nome_usina", "N/A")
                codigo = mudanca.get("codigo_usina")
                
                # Sempre tentar melhorar o nome usando o mapeamento
                # O mapeamento já foi criado com dados de ambos os decks e TERM.DAT
                if codigo and codigo in mapeamento_codigo_nome:
                    nome_mapeado = mapeamento_codigo_nome[codigo]
                    # Se temos um nome válido no mapeamento, usar (mesmo que já tenhamos um nome)
                    if nome_mapeado and nome_mapeado != "N/A" and not nome_mapeado.startswith("Usina "):
                        nome_usina = nome_mapeado
                    elif nome_usina == "N/A" or nome_usina.startswith("Usina "):
                        # Se o nome atual é inválido, usar o mapeado mesmo que seja "Usina X"
                        nome_usina = nome_mapeado
                
                comparison_table.append({
                    "nome_usina": nome_usina,
                    "codigo_usina": codigo,  # Incluir código para referência
                    "tipo_mudanca": tipo_mudanca,  # Manter tipo original (aumento, queda, remocao, novo)
                    "gtmin_dezembro": mudanca.get("gtmin_dezembro"),
                    "gtmin_janeiro": mudanca.get("gtmin_janeiro"),
                    "diferenca": mudanca.get("diferenca"),
                    "magnitude": round(mudanca.get("magnitude_mudanca", 0), 2),
                    "periodo_inicio": mudanca.get("periodo_inicio", "N/A"),
                    "periodo_fim": mudanca.get("periodo_fim", "N/A")
                })
            
            # Ajustar descrição se houver filtro por usina (NOVO)
            if codigo_usina_filtro is not None:
                nome_usina_filtro = mapeamento_codigo_nome.get(codigo_usina_filtro, f"Usina {codigo_usina_filtro}")
                description = f"Análise de {len(mudancas_ordenadas)} mudanças de GTMIN para {nome_usina_filtro} (código {codigo_usina_filtro}) entre {deck_december_name} e {deck_january_name}, ordenadas por magnitude."
            else:
                description = f"Análise de {len(mudancas_ordenadas)} mudanças de GTMIN entre {deck_december_name} e {deck_january_name}, ordenadas por magnitude."
            
            return {
                "success": True,
                "is_comparison": True,
                "tool": self.get_name(),
                "comparison_table": comparison_table,
                "stats": stats,
                "description": description
            }
            
        except Exception as e:
            print(f"[TOOL] ❌ Erro ao processar: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": f"Erro ao processar análise de GTMIN: {str(e)}",
                "error_type": type(e).__name__,
                "tool": self.get_name()
            }
    
    def _execute_multi_deck_matrix(self, query: str) -> Dict[str, Any]:
        """
        Executa análise de GTMIN para múltiplos decks (mais de 2) usando matriz de comparação.
        
        Args:
            query: Query do usuário
            
        Returns:
            Dicionário com dados formatados para matriz de comparação
        """
        print("[TOOL] Executando análise de matriz para múltiplos decks...")
        
        try:
            # ETAPA 1: Ler EXPT.DAT de todos os decks
            print("[TOOL] ETAPA 1: Lendo arquivos EXPT.DAT de todos os decks...")
            decks_expt = {}
            decks_gtmin = {}
            deck_names = []
            
            for deck_name in self.selected_decks:
                deck_path = self.deck_paths.get(deck_name)
                deck_display_name = self.deck_display_names.get(deck_name, deck_name)
                deck_names.append(deck_display_name)
                
                expt = self._read_expt_file(deck_path)
                if expt is None:
                    print(f"[TOOL] ⚠️ Arquivo EXPT.DAT não encontrado em {deck_path}")
                    continue
                
                decks_expt[deck_display_name] = expt
                gtmin = self._extract_gtmin_records(expt)
                decks_gtmin[deck_display_name] = gtmin
                print(f"[TOOL] ✅ Deck {deck_display_name}: {len(gtmin)} registros GTMIN")
            
            if len(decks_expt) < 2:
                return {
                    "success": False,
                    "error": "São necessários pelo menos 2 decks válidos para comparação",
                    "tool": self.get_name()
                }
            
            # ETAPA 2: Criar mapeamento código -> nome das usinas (usar primeiro deck como base)
            print("[TOOL] ETAPA 2: Criando mapeamento código -> nome das usinas...")
            first_expt = list(decks_expt.values())[0]
            last_expt = list(decks_expt.values())[-1]
            mapeamento_codigo_nome = self._create_codigo_nome_mapping(first_expt, last_expt)
            print(f"[TOOL] ✅ Mapeamento criado: {len(mapeamento_codigo_nome)} usinas mapeadas")
            
            # ETAPA 3: Extrair usina da query (opcional)
            print("[TOOL] ETAPA 3: Verificando se há filtro por usina na query...")
            codigo_usina_filtro = self._extract_usina_from_query(query, first_expt, last_expt, mapeamento_codigo_nome)
            if codigo_usina_filtro is not None:
                nome_usina_filtro = mapeamento_codigo_nome.get(codigo_usina_filtro, f"Usina {codigo_usina_filtro}")
                print(f"[TOOL] ✅ Filtro por usina detectado: {codigo_usina_filtro} - {nome_usina_filtro}")
                # Aplicar filtro
                for deck_name in decks_gtmin:
                    decks_gtmin[deck_name] = decks_gtmin[deck_name][
                        decks_gtmin[deck_name]['codigo_usina'] == codigo_usina_filtro
                    ]
            
            # ETAPA 4: Criar estrutura de dados para matriz
            print("[TOOL] ETAPA 4: Criando estrutura de matriz de comparação...")
            
            # Coletar todas as chaves únicas (codigo_usina, periodo_inicio, periodo_fim)
            def create_key(row):
                codigo = int(row['codigo_usina'])
                inicio = self._format_date(row.get('data_inicio'))
                fim = self._format_date(row.get('data_fim'))
                return (codigo, inicio, fim)
            
            all_keys = set()
            for gtmin_df in decks_gtmin.values():
                for _, row in gtmin_df.iterrows():
                    all_keys.add(create_key(row))
            
            print(f"[TOOL] ✅ Total de chaves únicas: {len(all_keys)}")
            
            # ETAPA 5: Construir matriz de comparação
            matrix_data = []
            
            for key in all_keys:
                codigo_usina, periodo_inicio, periodo_fim = key
                nome_usina = mapeamento_codigo_nome.get(codigo_usina, f"Usina {codigo_usina}")
                
                # Coletar valores de GTMIN de cada deck
                gtmin_values = {}
                for deck_display_name in deck_names:
                    if deck_display_name not in decks_gtmin:
                        gtmin_values[deck_display_name] = None
                        continue
                    
                    gtmin_df = decks_gtmin[deck_display_name]
                    matching_rows = gtmin_df[
                        (gtmin_df['codigo_usina'] == codigo_usina) &
                        (gtmin_df['data_inicio'].apply(self._format_date) == periodo_inicio) &
                        (gtmin_df['data_fim'].apply(self._format_date) == periodo_fim)
                    ]
                    
                    if not matching_rows.empty:
                        gtmin_val = self._sanitize_number(matching_rows.iloc[0].get('modificacao'))
                        gtmin_values[deck_display_name] = round(gtmin_val, 2) if gtmin_val is not None else None
                    else:
                        gtmin_values[deck_display_name] = None
                
                # Verificar se há alguma mudança (não todos None ou todos iguais)
                valores_nao_nulos = [v for v in gtmin_values.values() if v is not None]
                if len(valores_nao_nulos) == 0:
                    continue  # Pular se não há valores
                
                # Verificar se há variação
                valores_unicos = set(valores_nao_nulos)
                if len(valores_unicos) <= 1:
                    continue  # Pular se todos os valores são iguais
                
                # Calcular diferenças entre todos os pares de decks
                matrix_row = {
                    "nome_usina": nome_usina,
                    "codigo_usina": codigo_usina,
                    "periodo_inicio": periodo_inicio,
                    "periodo_fim": periodo_fim,
                    "gtmin_values": gtmin_values,  # Dict[deck_name, value]
                    "matrix": {}  # Dict[(deck_from, deck_to), difference]
                }
                
                # Preencher matriz de diferenças
                # Usar string como chave para compatibilidade com JSON
                for i, deck_from in enumerate(deck_names):
                    for j, deck_to in enumerate(deck_names):
                        if i == j:
                            matrix_row["matrix"][f"{deck_from},{deck_to}"] = 0.0
                        else:
                            val_from = gtmin_values.get(deck_from)
                            val_to = gtmin_values.get(deck_to)
                            
                            if val_from is not None and val_to is not None:
                                diff = round(val_to - val_from, 2)
                                matrix_row["matrix"][f"{deck_from},{deck_to}"] = diff
                            elif val_from is None and val_to is not None:
                                matrix_row["matrix"][f"{deck_from},{deck_to}"] = val_to  # Novo
                            elif val_from is not None and val_to is None:
                                matrix_row["matrix"][f"{deck_from},{deck_to}"] = -val_from  # Removido
                            else:
                                matrix_row["matrix"][f"{deck_from},{deck_to}"] = None
                
                matrix_data.append(matrix_row)
            
            print(f"[TOOL] ✅ Matriz criada: {len(matrix_data)} registros com variações")
            
            # ETAPA 6: Calcular estatísticas
            stats = {
                "total_registros": len(matrix_data),
                "total_decks": len(deck_names),
                "usinas_unicas": len(set(row["codigo_usina"] for row in matrix_data))
            }
            
            return {
                "success": True,
                "is_comparison": True,
                "tool": self.get_name(),
                "matrix_data": matrix_data,
                "deck_names": deck_names,
                "stats": stats,
                "visualization_type": "gtmin_matrix",
                "description": f"Matriz de comparação de GTMIN entre {len(deck_names)} decks, com {len(matrix_data)} registros com variações."
            }
            
        except Exception as e:
            print(f"[TOOL] ❌ Erro ao processar: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": f"Erro ao processar análise de GTMIN: {str(e)}",
                "error_type": type(e).__name__,
                "tool": self.get_name()
            }
    
    def _read_expt_file(self, deck_path) -> Optional[Expt]:
        """
        Lê o arquivo EXPT.DAT de um deck.
        
        Args:
            deck_path: Caminho do diretório do deck
            
        Returns:
            Objeto Expt ou None se não encontrado
        """
        expt_path = os.path.join(deck_path, "EXPT.DAT")
        if not os.path.exists(expt_path):
            expt_path_lower = os.path.join(deck_path, "expt.dat")
            if os.path.exists(expt_path_lower):
                expt_path = expt_path_lower
            else:
                print(f"[TOOL] ⚠️ Arquivo EXPT.DAT não encontrado em {deck_path}")
                return None
        
        try:
            expt = Expt.read(expt_path)
            return expt
        except Exception as e:
            print(f"[TOOL] ❌ Erro ao ler EXPT.DAT: {e}")
            return None
    
    def _create_codigo_nome_mapping(self, expt_dec: Expt, expt_jan: Expt) -> Dict[int, str]:
        """
        Cria mapeamento de código de usina para nome a partir dos DataFrames de expansões.
        Prioriza nomes não vazios e usa ambos os decks para garantir cobertura completa.
        Se não encontrar no EXPT, tenta cruzar com TERM.DAT.
        
        Args:
            expt_dec: Objeto Expt do deck de dezembro
            expt_jan: Objeto Expt do deck de janeiro
            
        Returns:
            Dicionário mapeando codigo_usina -> nome_usina
        """
        mapeamento = {}
        
        # Processar deck de dezembro
        if expt_dec.expansoes is not None and not expt_dec.expansoes.empty:
            if 'codigo_usina' in expt_dec.expansoes.columns and 'nome_usina' in expt_dec.expansoes.columns:
                usinas_dec = expt_dec.expansoes[['codigo_usina', 'nome_usina']].drop_duplicates()
                for _, row in usinas_dec.iterrows():
                    codigo = int(row['codigo_usina'])
                    nome = str(row.get('nome_usina', '')).strip()
                    # Verificar se nome é válido (não vazio, não NaN, não None)
                    if nome and nome != 'nan' and nome.lower() != 'none' and nome != '' and not pd.isna(row.get('nome_usina')):
                        mapeamento[codigo] = nome
                        print(f"[TOOL] Mapeamento: {codigo} -> {nome}")
        
        # Processar deck de janeiro (sobrescreve se houver nome melhor ou se não existia)
        if expt_jan.expansoes is not None and not expt_jan.expansoes.empty:
            if 'codigo_usina' in expt_jan.expansoes.columns and 'nome_usina' in expt_jan.expansoes.columns:
                usinas_jan = expt_jan.expansoes[['codigo_usina', 'nome_usina']].drop_duplicates()
                for _, row in usinas_jan.iterrows():
                    codigo = int(row['codigo_usina'])
                    nome = str(row.get('nome_usina', '')).strip()
                    if nome and nome != 'nan' and nome.lower() != 'none' and nome != '' and not pd.isna(row.get('nome_usina')):
                        # Sobrescrever se não existia ou se o nome é mais completo
                        if codigo not in mapeamento or (len(nome) > len(mapeamento.get(codigo, ''))):
                            mapeamento[codigo] = nome
                            print(f"[TOOL] Mapeamento: {codigo} -> {nome}")
        
        # Se ainda faltam nomes, tentar cruzar com TERM.DAT (usando deck de dezembro como referência)
        codigos_sem_nome = []
        if expt_dec.expansoes is not None and not expt_dec.expansoes.empty:
            codigos_sem_nome.extend([c for c in expt_dec.expansoes['codigo_usina'].unique() if c not in mapeamento])
        if expt_jan.expansoes is not None and not expt_jan.expansoes.empty:
            codigos_sem_nome.extend([c for c in expt_jan.expansoes['codigo_usina'].unique() if c not in mapeamento])
        codigos_sem_nome = list(set(codigos_sem_nome))
        
        if codigos_sem_nome:
            print(f"[TOOL] ⚠️ {len(codigos_sem_nome)} usinas sem nome no EXPT, tentando TERM.DAT...")
            try:
                from inewave.newave import Term
                deck_path_ref = get_december_deck_path()
                term_path = os.path.join(deck_path_ref, "TERM.DAT")
                if not os.path.exists(term_path):
                    term_path = os.path.join(deck_path_ref, "term.dat")
                
                if os.path.exists(term_path):
                    term = Term.read(term_path)
                    if term.usinas is not None and not term.usinas.empty:
                        for _, term_row in term.usinas.iterrows():
                            codigo_term = int(term_row.get('codigo', 0))
                            if codigo_term in codigos_sem_nome:
                                nome_term = str(term_row.get('nome', '')).strip()
                                if nome_term and nome_term != 'nan' and nome_term.lower() != 'none' and nome_term != '':
                                    mapeamento[codigo_term] = nome_term
                                    print(f"[TOOL] ✅ Nome do TERM.DAT: {codigo_term} -> {nome_term}")
            except Exception as e:
                print(f"[TOOL] ⚠️ Erro ao ler TERM.DAT para nomes: {e}")
        
        return mapeamento
    
    def _extract_usina_from_query(
        self, 
        query: str, 
        expt_dec: Expt, 
        expt_jan: Expt,
        mapeamento_codigo_nome: Dict[int, str]
    ) -> Optional[int]:
        """
        Extrai código da usina da query.
        Busca por número ou nome da usina.
        
        Args:
            query: Query do usuário
            expt_dec: Objeto Expt do deck de dezembro
            expt_jan: Objeto Expt do deck de janeiro
            mapeamento_codigo_nome: Mapeamento código -> nome já criado
            
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
        ]
        
        # Obter códigos válidos de ambos os decks
        codigos_validos = set()
        if expt_dec.expansoes is not None and not expt_dec.expansoes.empty:
            codigos_validos.update(expt_dec.expansoes['codigo_usina'].unique())
        if expt_jan.expansoes is not None and not expt_jan.expansoes.empty:
            codigos_validos.update(expt_jan.expansoes['codigo_usina'].unique())
        
        for pattern in patterns:
            match = re.search(pattern, query_lower)
            if match:
                try:
                    codigo = int(match.group(1))
                    if codigo in codigos_validos:
                        print(f"[TOOL] ✅ Código {codigo} encontrado por padrão numérico")
                        return codigo
                except ValueError:
                    continue
        
        # ETAPA 2: Buscar por nome da usina usando o mapeamento
        print(f"[TOOL] Buscando usina por nome na query: '{query}'")
        
        if not mapeamento_codigo_nome:
            print("[TOOL] ⚠️ Mapeamento de nomes não disponível")
            return None
        
        # Criar mapeamento reverso nome -> código (ordenado por tamanho do nome, maior primeiro)
        mapeamento_nome_codigo = {}
        for codigo, nome in mapeamento_codigo_nome.items():
            if nome and nome.strip() and nome != "N/A" and not nome.startswith("Usina "):
                nome_lower = nome.lower().strip()
                # Se já existe, manter o que tem nome mais longo (mais específico)
                if nome_lower not in mapeamento_nome_codigo or len(nome) > len(mapeamento_codigo_nome[mapeamento_nome_codigo[nome_lower]]):
                    mapeamento_nome_codigo[nome_lower] = codigo
        
        # Ordenar por tamanho do nome (maior primeiro) para priorizar matches mais específicos
        nomes_ordenados = sorted(
            mapeamento_nome_codigo.items(),
            key=lambda x: len(x[0]),
            reverse=True
        )
        
        # ETAPA 2.1: Buscar match exato do nome completo (prioridade máxima)
        for nome_lower, codigo in nomes_ordenados:
            nome_original = mapeamento_codigo_nome[codigo]
            
            # Match exato do nome completo
            if nome_lower == query_lower.strip():
                print(f"[TOOL] ✅ Código {codigo} encontrado por match exato '{nome_original}'")
                return codigo
            
            # Match exato do nome completo dentro da query (com word boundaries)
            if nome_lower in query_lower:
                # Verificar se não é apenas uma palavra parcial muito curta
                if len(nome_lower) >= 4:  # Nomes com pelo menos 4 caracteres
                    # Verificar se está como palavra completa (não parte de outra palavra)
                    pattern = r'\b' + re.escape(nome_lower) + r'\b'
                    if re.search(pattern, query_lower):
                        print(f"[TOOL] ✅ Código {codigo} encontrado por nome completo '{nome_original}' na query")
                        return codigo
        
        # ETAPA 2.2: Buscar por palavras-chave do nome (apenas se match exato não encontrou)
        palavras_ignorar = {'de', 'da', 'do', 'das', 'dos', 'e', 'a', 'o', 'as', 'os', 'em', 'na', 'no', 'nas', 'nos', 'gtmin', 'variação', 'variacao', 'mudanças', 'mudancas'}
        palavras_query = [p for p in query_lower.split() if len(p) > 2 and p not in palavras_ignorar]
        
        if not palavras_query:
            return None
        
        # Lista de candidatos com pontuação
        candidatos = []
        
        for nome_lower, codigo in nomes_ordenados:
            nome_original = mapeamento_codigo_nome[codigo]
            palavras_nome = [p for p in nome_lower.split() if len(p) > 2 and p not in palavras_ignorar]
            
            if not palavras_nome:
                continue
            
            # Calcular pontuação: quantas palavras do nome estão na query
            palavras_match = sum(1 for palavra in palavras_nome if palavra in palavras_query)
            if palavras_match > 0:
                # Priorizar matches com mais palavras e nomes mais longos
                score = palavras_match * 100 + len(nome_lower)
                candidatos.append((codigo, nome_original, score))
        
        if candidatos:
            # Ordenar por pontuação (maior primeiro)
            candidatos.sort(key=lambda x: x[2], reverse=True)
            melhor_candidato = candidatos[0]
            print(f"[TOOL] ✅ Código {melhor_candidato[0]} encontrado por palavras-chave '{melhor_candidato[1]}' (score: {melhor_candidato[2]})")
            return melhor_candidato[0]
        
        print("[TOOL] ⚠️ Nenhuma usina encontrada na query")
        return None
    
    def _extract_gtmin_records(self, expt: Expt) -> pd.DataFrame:
        """
        Extrai apenas os registros de GTMIN do DataFrame de expansões.
        
        Args:
            expt: Objeto Expt
            
        Returns:
            DataFrame com apenas registros de GTMIN
        """
        if expt.expansoes is None or expt.expansoes.empty:
            return pd.DataFrame()
        
        # Filtrar apenas GTMIN
        gtmin_df = expt.expansoes[expt.expansoes['tipo'] == 'GTMIN'].copy()
        
        return gtmin_df
    
    def _identify_changes(
        self,
        gtmin_dec: pd.DataFrame,
        gtmin_jan: pd.DataFrame,
        deck_dec_name: str,
        deck_jan_name: str,
        mapeamento_codigo_nome: Dict[int, str]
    ) -> List[Dict[str, Any]]:
        """
        Identifica mudanças de GTMIN entre os dois decks.
        
        Uma mudança é identificada quando:
        - Uma usina tem GTMIN diferente no mesmo período
        - Uma usina tem GTMIN em um deck mas não no outro
        
        Args:
            gtmin_dec: DataFrame com GTMIN de dezembro
            gtmin_jan: DataFrame com GTMIN de janeiro
            deck_dec_name: Nome do deck de dezembro
            deck_jan_name: Nome do deck de janeiro
            
        Returns:
            Lista de dicionários com informações sobre mudanças
        """
        mudancas = []
        
        # Criar índices para comparação eficiente
        # Chave: (codigo_usina, periodo_inicio, periodo_fim)
        def create_key(row):
            codigo = int(row['codigo_usina'])
            inicio = self._format_date(row.get('data_inicio'))
            fim = self._format_date(row.get('data_fim'))
            return (codigo, inicio, fim)
        
        dec_indexed = {}
        for _, row in gtmin_dec.iterrows():
            key = create_key(row)
            dec_indexed[key] = row
        
        jan_indexed = {}
        for _, row in gtmin_jan.iterrows():
            key = create_key(row)
            jan_indexed[key] = row
        
        # Comparar registros
        all_keys = set(dec_indexed.keys()) | set(jan_indexed.keys())
        
        for key in all_keys:
            codigo_usina, periodo_inicio, periodo_fim = key
            dec_record = dec_indexed.get(key)
            jan_record = jan_indexed.get(key)
            
            # Obter nome da usina do mapeamento (prioridade) ou dos registros
            nome_usina = mapeamento_codigo_nome.get(codigo_usina)
            
            if not nome_usina or nome_usina.strip() == '':
                # Fallback: tentar obter dos registros
                if dec_record is not None:
                    nome_temp = str(dec_record.get('nome_usina', '')).strip()
                    if nome_temp and nome_temp != 'nan' and nome_temp.lower() != 'none' and nome_temp != '':
                        nome_usina = nome_temp
                if (not nome_usina or nome_usina.strip() == '') and jan_record is not None:
                    nome_temp = str(jan_record.get('nome_usina', '')).strip()
                    if nome_temp and nome_temp != 'nan' and nome_temp.lower() != 'none' and nome_temp != '':
                        nome_usina = nome_temp
            
            # Se ainda não encontrou, usar código
            if not nome_usina or nome_usina.strip() == '':
                nome_usina = f'Usina {codigo_usina}'
            
            # Extrair valores de GTMIN
            gtmin_dec_val = None
            gtmin_jan_val = None
            
            if dec_record is not None:
                gtmin_dec_val = self._sanitize_number(dec_record.get('modificacao'))
            if jan_record is not None:
                gtmin_jan_val = self._sanitize_number(jan_record.get('modificacao'))
            
            # Normalizar valores None para 0 para comparação
            # Mas manter None para exibição quando apropriado
            gtmin_dec_val_normalized = gtmin_dec_val if gtmin_dec_val is not None else 0.0
            gtmin_jan_val_normalized = gtmin_jan_val if gtmin_jan_val is not None else 0.0
            
            # Se ambos os valores são zero ou muito próximos de zero, não é uma mudança
            if abs(gtmin_dec_val_normalized) < 0.01 and abs(gtmin_jan_val_normalized) < 0.01:
                # Ambos são zero - não é uma mudança significativa, pular este registro
                tipo_mudanca = None
            else:
                # Identificar tipo de mudança
                tipo_mudanca = None
                magnitude_mudanca = 0
                
                if dec_record is None and jan_record is not None:
                    # Novo registro em janeiro
                    # Só considerar como "novo" se o valor de janeiro for diferente de zero
                    if gtmin_jan_val is not None and abs(gtmin_jan_val) > 0.01:
                        tipo_mudanca = "novo"
                        magnitude_mudanca = abs(gtmin_jan_val)
                elif dec_record is not None and jan_record is None:
                    # Registro removido em janeiro
                    # Só considerar como "remocao" se o valor de dezembro for diferente de zero
                    if gtmin_dec_val is not None and abs(gtmin_dec_val) > 0.01:
                        tipo_mudanca = "remocao"
                        magnitude_mudanca = abs(gtmin_dec_val)
                elif dec_record is not None and jan_record is not None:
                    # Registro existe em ambos - verificar se valor mudou
                    if gtmin_dec_val is not None and gtmin_jan_val is not None:
                        diferenca_val = gtmin_jan_val - gtmin_dec_val
                        if abs(diferenca_val) > 0.01:  # Tolerância para diferenças numéricas
                            if diferenca_val > 0:
                                tipo_mudanca = "aumento"
                            else:
                                tipo_mudanca = "queda"
                            magnitude_mudanca = abs(diferenca_val)
                    elif gtmin_dec_val is None and gtmin_jan_val is not None:
                        # Dezembro não tem valor, janeiro tem - só considerar se janeiro não for zero
                        if abs(gtmin_jan_val) > 0.01:
                            tipo_mudanca = "novo"
                            magnitude_mudanca = abs(gtmin_jan_val)
                    elif gtmin_dec_val is not None and gtmin_jan_val is None:
                        # Janeiro não tem valor, dezembro tem - só considerar se dezembro não for zero
                        if abs(gtmin_dec_val) > 0.01:
                            tipo_mudanca = "remocao"
                            magnitude_mudanca = abs(gtmin_dec_val)
            
            # Se há mudança, adicionar à lista
            if tipo_mudanca is not None:
                mudanca = {
                    "codigo_usina": int(codigo_usina),
                    "nome_usina": str(nome_usina).strip(),
                    "tipo_mudanca": tipo_mudanca,
                    "periodo_inicio": periodo_inicio,
                    "periodo_fim": periodo_fim,
                    "gtmin_dezembro": round(gtmin_dec_val, 2) if gtmin_dec_val is not None else None,
                    "gtmin_janeiro": round(gtmin_jan_val, 2) if gtmin_jan_val is not None else None,
                    "magnitude_mudanca": round(magnitude_mudanca, 2),
                    "diferenca": round(gtmin_jan_val - gtmin_dec_val, 2) if (
                        gtmin_dec_val is not None and gtmin_jan_val is not None
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
        gtmin_dec: pd.DataFrame,
        gtmin_jan: pd.DataFrame,
        mudancas: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calcula estatísticas sobre os registros de GTMIN e mudanças.
        
        Args:
            gtmin_dec: DataFrame com GTMIN de dezembro
            gtmin_jan: DataFrame com GTMIN de janeiro
            mudancas: Lista de mudanças identificadas
            
        Returns:
            Dicionário com estatísticas
        """
        stats = {
            "total_registros_dezembro": len(gtmin_dec),
            "total_registros_janeiro": len(gtmin_jan),
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
        if not gtmin_dec.empty:
            stats["usinas_unicas_dezembro"] = gtmin_dec['codigo_usina'].nunique()
        else:
            stats["usinas_unicas_dezembro"] = 0
        
        if not gtmin_jan.empty:
            stats["usinas_unicas_janeiro"] = gtmin_jan['codigo_usina'].nunique()
        else:
            stats["usinas_unicas_janeiro"] = 0
        
        return stats
    
    def get_description(self) -> str:
        """
        Retorna descrição da tool para uso pelo LLM.
        
        Returns:
            String com descrição detalhada
        """
        return """
        Mudanças em gerações térmicas. Análise de variações de GTMIN (Geração Térmica Mínima) entre decks no modo multideck.
        
        Esta tool é especializada em:
        - Identificar todas as mudanças de GTMIN entre dezembro e janeiro
        - Ordenar mudanças por magnitude (maior variação primeiro)
        - Classificar tipos de mudança (alterado, novo_registro, removido)
        - Retornar apenas as mudanças (não todos os registros)
        
        Queries que ativam esta tool:
        - "mudanças gtmin" ou "mudancas gtmin"
        - "variação gtmin" ou "variacao gtmin"
        - "variações de gtmin" ou "variacoes de gtmin" (plural)
        - "quais foram as variações de gtmin" ou "quais foram as variacoes de gtmin"
        - "análise gtmin" ou "analise gtmin"
        - "mudanças em gerações térmicas" ou "mudancas em geracoes termicas"
        
        Termos-chave: mudanças gtmin, variação gtmin, variações de gtmin, análise gtmin, mudancas gtmin, variacao gtmin, variacoes de gtmin, analise gtmin, geração mínima térmica, mudanças em gerações térmicas, variações em gerações térmicas.
        """
