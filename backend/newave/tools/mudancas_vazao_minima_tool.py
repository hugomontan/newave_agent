"""
Tool para análise de mudanças de vazão mínima (VAZMIN/VAZMINT) entre decks no modo multideck.
Suporta comparação de N decks para análise histórica de vazão mínima.
"""
from backend.newave.tools.base import NEWAVETool
from inewave.newave import Modif
import os
import pandas as pd
import re
from typing import Dict, Any, List, Optional
from backend.newave.config import debug_print, safe_print
from backend.newave.utils.deck_loader import (
    list_available_decks,
    load_multiple_decks,
    get_deck_display_name,
)


class MudancasVazaoMinimaTool(NEWAVETool):
    """
    Tool especializada para análise de mudanças de vazão mínima entre decks.
    Suporta comparação de N decks.
    
    Funcionalidades:
    - Lista todas as mudanças de VAZMIN/VAZMINT entre os decks selecionados
    - Identifica mudanças (variações de valor, novos registros, remoções)
    - Ordena mudanças por magnitude
    - Retorna apenas as mudanças (não todos os registros)
    
    Comportamento adaptativo:
    - 2 decks: comparação direta (antes/depois)
    - N decks: mostra todas as mudanças em cada transição
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
                debug_print(f"[TOOL] ⚠️ Erro ao carregar decks: {e}")
    
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
            # Palavras-chave genéricas primeiro (para capturar queries simples como "vazão mínima")
            "vazão mínima", "vazao minima", "vazão minima", "vazao mínima",
            "vazao-minima", "vazão-mínima", "vazao_minima", "vazão_mínima",
            # Palavras-chave específicas (para capturar queries mais detalhadas)
            "mudanças vazão mínima",
            "mudancas vazao minima",
            "variação vazão mínima",
            "variacao vazao minima",
            "variação de vazão mínima",
            "variacao de vazao minima",
            "variações vazão mínima",  # Plural
            "variacoes vazao minima",  # Plural
            "variações de vazão mínima",  # Plural
            "variacoes de vazao minima",  # Plural
            "quais foram as variações",  # Query específica
            "quais foram as variacoes",  # Query específica
            "análise vazão mínima",
            "analise vazao minima",
            "mudanças vazmin",
            "mudancas vazmin",
            "mudanças vazmint",
            "mudancas vazmint",
        ]
        return any(kw in query_lower for kw in keywords)
    
    def execute(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Executa a análise de mudanças de vazão mínima entre os decks selecionados.
        
        Fluxo:
        1. Usa decks selecionados (ou carrega automaticamente)
        2. Lê MODIF.DAT de todos os decks
        3. Filtra apenas registros de VAZMIN e VAZMINT
        4. Compara e identifica mudanças entre decks consecutivos
        5. Ordena mudanças por magnitude
        6. Retorna dados formatados
        """
        debug_print(f"[TOOL] {self.get_name()}: Iniciando análise de mudanças de vazão mínima...")
        debug_print(f"[TOOL] Query: {query[:100]}")
        debug_print(f"[TOOL] Decks selecionados: {self.selected_decks}")
        
        try:
            # ETAPA 1: Verificar decks disponíveis
            debug_print("[TOOL] ETAPA 1: Verificando decks...")
            
            if not self.deck_paths or len(self.deck_paths) < 2:
                return {
                    "success": False,
                    "error": "São necessários pelo menos 2 decks para comparação",
                    "tool": self.get_name()
                }
            
            # Verificar se há mais de 2 decks - usar matriz de comparação
            if len(self.selected_decks) > 2:
                debug_print(f"[TOOL] ✅ {len(self.selected_decks)} decks detectados - usando matriz de comparação")
                return self._execute_multi_deck_matrix(query, **kwargs)
            
            # Para compatibilidade, usar primeiro e último deck (2 decks)
            deck_december_path = self.deck_paths.get(self.selected_decks[0])
            deck_january_path = self.deck_paths.get(self.selected_decks[-1])
            deck_december_name = self.deck_display_names.get(self.selected_decks[0], "Deck Anterior")
            deck_january_name = self.deck_display_names.get(self.selected_decks[-1], "Deck Atual")
            
            debug_print(f"[TOOL] ✅ Deck Anterior: {deck_december_path} ({deck_december_name})")
            debug_print(f"[TOOL] ✅ Deck Atual: {deck_january_path} ({deck_january_name})")
            
            # ETAPA 2: Ler MODIF.DAT de ambos os decks
            debug_print("[TOOL] ETAPA 2: Lendo arquivos MODIF.DAT...")
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
            debug_print("[TOOL] ETAPA 3: Criando mapeamento código -> nome das usinas...")
            mapeamento_codigo_nome = self._create_codigo_nome_mapping(modif_dec, modif_jan)
            debug_print(f"[TOOL] ✅ Mapeamento criado: {len(mapeamento_codigo_nome)} usinas mapeadas")
            
            # ETAPA 3.5: Extrair usina da query (se especificada) ou forced_plant_code (correção, CSV)
            # codigo_modif: filtra MODIF; codigo_csv: selected_plant/follow-up (sempre base CSV)
            debug_print("[TOOL] ETAPA 3.5: Verificando se há filtro por usina na query...")
            codigo_modif = None
            codigo_csv = None
            forced = kwargs.get("forced_plant_code")
            if forced is not None:
                codigo_csv = int(forced)
                codigo_modif = self._csv_to_modif_code(codigo_csv, mapeamento_codigo_nome)
            else:
                codigo_modif = self._extract_usina_from_query(query, modif_dec, modif_jan, mapeamento_codigo_nome)
                if codigo_modif is not None:
                    codigo_csv = self._modif_to_csv_code(codigo_modif, mapeamento_codigo_nome)
                    if codigo_csv is None:
                        codigo_csv = codigo_modif
            codigo_usina_filtro = codigo_modif
            if codigo_usina_filtro is not None:
                nome_usina_filtro = mapeamento_codigo_nome.get(codigo_usina_filtro, f"Usina {codigo_usina_filtro}")
                debug_print(f"[TOOL] ✅ Filtro por usina detectado: MODIF={codigo_usina_filtro} CSV={codigo_csv} - {nome_usina_filtro}")
            else:
                debug_print("[TOOL] ℹ️ Nenhum filtro por usina detectado - retornando todas as mudanças")
            
            # ETAPA 4: Filtrar apenas registros de VAZMIN e VAZMINT
            debug_print("[TOOL] ETAPA 4: Filtrando registros de VAZMIN e VAZMINT...")
            vazmin_dec = self._extract_vazmin_records(modif_dec)
            vazmin_jan = self._extract_vazmin_records(modif_jan)
            
            # Aplicar filtro por usina se especificado
            if codigo_usina_filtro is not None:
                vazmin_dec = [r for r in vazmin_dec if r.get('codigo_usina') == codigo_usina_filtro]
                vazmin_jan = [r for r in vazmin_jan if r.get('codigo_usina') == codigo_usina_filtro]
                debug_print(f"[TOOL] ✅ Dados filtrados por usina {codigo_usina_filtro}")
            
            debug_print(f"[TOOL] ✅ Registros VAZMIN/VAZMINT Dezembro: {len(vazmin_dec)}")
            debug_print(f"[TOOL] ✅ Registros VAZMIN/VAZMINT Janeiro: {len(vazmin_jan)}")
            
            # Debug: mostrar todos os registros antes da comparação
            debug_print(f"[TOOL] [DEBUG] Registros dezembro detalhados:")
            for i, r in enumerate(vazmin_dec):
                debug_print(f"[TOOL] [DEBUG]   [{i}] codigo={r.get('codigo_usina')}, tipo={r.get('tipo_vazao')}, vazao={r.get('vazao')}, periodo={r.get('periodo_inicio')}")
            debug_print(f"[TOOL] [DEBUG] Registros janeiro detalhados:")
            for i, r in enumerate(vazmin_jan):
                debug_print(f"[TOOL] [DEBUG]   [{i}] codigo={r.get('codigo_usina')}, tipo={r.get('tipo_vazao')}, vazao={r.get('vazao')}, periodo={r.get('periodo_inicio')}")
            
            # ETAPA 5: Comparar e identificar mudanças
            debug_print("[TOOL] ETAPA 5: Identificando mudanças...")
            mudancas = self._identify_changes(
                vazmin_dec, vazmin_jan, 
                deck_december_name, deck_january_name, 
                mapeamento_codigo_nome
            )
            
            debug_print(f"[TOOL] ✅ Total de mudanças identificadas: {len(mudancas)}")
            
            # ETAPA 6: Ordenar por tipo e magnitude
            debug_print("[TOOL] ETAPA 6: Ordenando mudanças por tipo e magnitude...")
            ordem_tipo = {"aumento": 0, "queda": 1, "remocao": 2, "novo": 3, "sem_mudanca": 4}
            mudancas_ordenadas = sorted(mudancas, key=lambda x: (
                ordem_tipo.get(x.get('tipo_mudanca', 'N/A'), 99),
                -abs(x.get('magnitude_mudanca', 0))  # Maior magnitude primeiro dentro do mesmo tipo
            ))
            
            # ETAPA 7: Calcular estatísticas
            stats = self._calculate_stats(vazmin_dec, vazmin_jan, mudancas)
            
            # ETAPA 8: Formatar tabela de comparação
            comparison_table = []
            
            # Calcular estatísticas por tipo_vazao para incluir na descrição
            vazmin_count = sum(1 for m in mudancas_ordenadas if m.get("tipo_vazao") == "VAZMIN")
            vazmint_count = sum(1 for m in mudancas_ordenadas if m.get("tipo_vazao") == "VAZMINT")
            
            # Ajustar descrição se filtro por usina foi aplicado
            if codigo_usina_filtro is not None:
                nome_usina_filtro = mapeamento_codigo_nome.get(codigo_usina_filtro, f"Usina {codigo_usina_filtro}")
                descricao_parts = [f"Análise de {len(mudancas_ordenadas)} mudanças de vazão mínima para {nome_usina_filtro} (código {codigo_usina_filtro}) entre {deck_december_name} e {deck_january_name}"]
            else:
                descricao_parts = [f"Análise de {len(mudancas_ordenadas)} mudanças de vazão mínima entre {deck_december_name} e {deck_january_name}"]
            
            # Adicionar informação sobre tipos de vazão
            tipo_info_parts = []
            if vazmin_count > 0:
                tipo_info_parts.append(f"{vazmin_count} mudança(s) em VAZMIN (vazão mínima sem período)")
            if vazmint_count > 0:
                tipo_info_parts.append(f"{vazmint_count} mudança(s) em VAZMINT (vazão mínima com período)")
            
            if tipo_info_parts:
                descricao_parts.append(f" - {', '.join(tipo_info_parts)}")
            
            descricao_parts.append("ordenadas por magnitude.")
            description = " ".join(descricao_parts)
            
            # Obter metadados da usina selecionada (sempre codigo_csv para follow-up)
            selected_plant = None
            if codigo_csv is not None:
                from backend.newave.utils.hydraulic_plant_matcher import get_hydraulic_plant_matcher
                matcher = get_hydraulic_plant_matcher()
                if codigo_csv in matcher.code_to_names:
                    nome_arquivo_csv, nome_completo_csv, _ = matcher.code_to_names[codigo_csv]
                    selected_plant = {
                        "type": "hydraulic",
                        "codigo": codigo_csv,
                        "nome": nome_arquivo_csv,
                        "nome_completo": nome_completo_csv if nome_completo_csv else nome_arquivo_csv,
                        "tool_name": self.get_name()
                    }
            
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
            
            result = {
                "success": True,
                "is_comparison": True,
                "tool": self.get_name(),
                "comparison_table": comparison_table,
                "stats": stats,
                "description": description
            }
            
            # Adicionar metadados da usina selecionada se disponível
            if selected_plant:
                result["selected_plant"] = selected_plant
            
            return result
            
        except Exception as e:
            safe_print(f"[TOOL] ❌ Erro ao processar: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": f"Erro ao processar análise de vazão mínima: {str(e)}",
                "error_type": type(e).__name__,
                "tool": self.get_name()
            }
    
    def _execute_multi_deck_matrix(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Executa análise de vazão mínima para múltiplos decks (mais de 2) usando matriz de comparação.
        
        IMPORTANTE: Para VAZMINT, aplica forward fill por mês dentro de cada linha (Usina + Deck).
        Cada linha representa uma combinação Usina + Deck, e as colunas são os meses.
        O forward fill preenche meses sem valor com o último valor conhecido anteriormente.
        
        Args:
            query: Query do usuário
            
        Returns:
            Dicionário com dados formatados para matriz de comparação expandida por mês
        """
        debug_print("[TOOL] Executando análise de matriz para múltiplos decks...")
        
        try:
            # ETAPA 1: Ler MODIF.DAT de todos os decks
            debug_print("[TOOL] ETAPA 1: Lendo arquivos MODIF.DAT de todos os decks...")
            decks_modif = {}
            decks_vazmin = {}
            deck_names = []
            
            for deck_name in self.selected_decks:
                deck_path = self.deck_paths.get(deck_name)
                deck_display_name = self.deck_display_names.get(deck_name, deck_name)
                deck_names.append(deck_display_name)
                
                modif = self._read_modif_file(deck_path)
                if modif is None:
                    debug_print(f"[TOOL] ⚠️ Arquivo MODIF.DAT não encontrado em {deck_path}")
                    continue
                
                decks_modif[deck_display_name] = modif
                vazmin_records = self._extract_vazmin_records(modif)
                decks_vazmin[deck_display_name] = vazmin_records
                debug_print(f"[TOOL] ✅ Deck {deck_display_name}: {len(vazmin_records)} registros VAZMIN/VAZMINT")
            
            if len(decks_modif) < 2:
                return {
                    "success": False,
                    "error": "São necessários pelo menos 2 decks válidos para comparação",
                    "tool": self.get_name()
                }
            
            # ETAPA 2: Criar mapeamento código -> nome das usinas (usar primeiro e último deck como base)
            debug_print("[TOOL] ETAPA 2: Criando mapeamento código -> nome das usinas...")
            first_modif = list(decks_modif.values())[0]
            last_modif = list(decks_modif.values())[-1]
            mapeamento_codigo_nome = self._create_codigo_nome_mapping(first_modif, last_modif)
            debug_print(f"[TOOL] ✅ Mapeamento criado: {len(mapeamento_codigo_nome)} usinas mapeadas")
            
            # ETAPA 3: Extrair usina (codigo_modif para filtro; codigo_csv para selected_plant)
            debug_print("[TOOL] ETAPA 3: Verificando se há filtro por usina na query...")
            codigo_modif = None
            codigo_csv = None
            forced = kwargs.get("forced_plant_code")
            if forced is not None:
                codigo_csv = int(forced)
                codigo_modif = self._csv_to_modif_code(codigo_csv, mapeamento_codigo_nome)
            else:
                codigo_modif = self._extract_usina_from_query(query, first_modif, last_modif, mapeamento_codigo_nome)
                if codigo_modif is not None:
                    codigo_csv = self._modif_to_csv_code(codigo_modif, mapeamento_codigo_nome)
                    if codigo_csv is None:
                        codigo_csv = codigo_modif
            codigo_usina_filtro = codigo_modif
            if codigo_usina_filtro is not None:
                nome_usina_filtro = mapeamento_codigo_nome.get(codigo_usina_filtro, f"Usina {codigo_usina_filtro}")
                debug_print(f"[TOOL] ✅ Filtro por usina detectado: MODIF={codigo_usina_filtro} CSV={codigo_csv} - {nome_usina_filtro}")
                # Aplicar filtro
                for deck_name in decks_vazmin:
                    decks_vazmin[deck_name] = [
                        r for r in decks_vazmin[deck_name] 
                        if r.get('codigo_usina') == codigo_usina_filtro
                    ]
            
            # ETAPA 4: Coletar todos os meses únicos (períodos) de todos os registros VAZMINT
            debug_print("[TOOL] ETAPA 4: Coletando todos os meses do horizonte...")
            all_months = set()
            for vazmin_list in decks_vazmin.values():
                for record in vazmin_list:
                    if record.get('tipo_vazao') == 'VAZMINT':
                        periodo = record.get('periodo_inicio')
                        if periodo and periodo != 'N/A':
                            all_months.add(periodo)
            
            # Ordenar meses cronologicamente
            all_months_sorted = sorted(list(all_months))
            debug_print(f"[TOOL] ✅ Meses encontrados: {all_months_sorted}")
            
            # ETAPA 5: Coletar todas as usinas únicas com VAZMINT
            debug_print("[TOOL] ETAPA 5: Coletando usinas com VAZMINT...")
            usinas_com_vazmint = set()
            for vazmin_list in decks_vazmin.values():
                for record in vazmin_list:
                    if record.get('tipo_vazao') == 'VAZMINT':
                        usinas_com_vazmint.add(record.get('codigo_usina'))
            
            debug_print(f"[TOOL] ✅ Usinas com VAZMINT: {len(usinas_com_vazmint)}")
            
            # ETAPA 6: Construir dados expandidos (Usina x Deck x Mês) - PRIMEIRO SEM FORWARD FILL
            debug_print("[TOOL] ETAPA 6: Construindo matriz expandida (dados brutos)...")
            expanded_data = []
            
            for codigo_usina in usinas_com_vazmint:
                nome_usina = mapeamento_codigo_nome.get(codigo_usina, f"Usina {codigo_usina}")
                
                for deck_display_name in deck_names:
                    if deck_display_name not in decks_vazmin:
                        continue
                    
                    vazmin_list = decks_vazmin[deck_display_name]
                    
                    # Coletar registros VAZMINT desta usina neste deck
                    registros_usina = [
                        r for r in vazmin_list 
                        if r.get('codigo_usina') == codigo_usina and r.get('tipo_vazao') == 'VAZMINT'
                    ]
                    
                    if not registros_usina:
                        continue
                    
                    # Criar dicionário período -> valor (dados brutos)
                    periodo_valor = {}
                    for record in registros_usina:
                        periodo = record.get('periodo_inicio')
                        vazao = self._sanitize_number(record.get('vazao'))
                        if periodo and periodo != 'N/A' and vazao is not None:
                            periodo_valor[periodo] = round(vazao, 2)
                    
                    if not periodo_valor:
                        continue
                    
                    # Criar monthly_values com todos os meses (SEM forward fill ainda)
                    monthly_values = {}
                    for mes in all_months_sorted:
                        if mes in periodo_valor:
                            monthly_values[mes] = periodo_valor[mes]
                        else:
                            monthly_values[mes] = None  # Será preenchido depois
                    
                    # Adicionar linha expandida
                    expanded_row = {
                        "nome_usina": nome_usina,
                        "codigo_usina": codigo_usina,
                        "deck_name": deck_display_name,
                        "tipo_vazao": "VAZMINT",
                        "monthly_values": monthly_values,
                        "original_periods": list(periodo_valor.keys())  # Períodos com valores originais
                    }
                    expanded_data.append(expanded_row)
                    
                    debug_print(f"[TOOL] [DEBUG] {nome_usina} - {deck_display_name}: {len(periodo_valor)} valores originais em {list(periodo_valor.keys())}")
            
            debug_print(f"[TOOL] ✅ Dados brutos coletados: {len(expanded_data)} linhas (Usina x Deck)")
            
            # ETAPA 6.5: APLICAR FORWARD FILL NA MATRIZ JÁ FORMADA
            debug_print("[TOOL] ETAPA 6.5: Aplicando forward fill na matriz...")
            expanded_data = self._apply_forward_fill_to_matrix(expanded_data, all_months_sorted)
            debug_print(f"[TOOL] ✅ Forward fill aplicado em {len(expanded_data)} linhas")
            
            # ETAPA 7: Também processar VAZMIN (sem período) - mantém estrutura antiga
            debug_print("[TOOL] ETAPA 7: Processando VAZMIN (sem período)...")
            matrix_data_vazmin = []
            
            # Coletar chaves VAZMIN únicas
            vazmin_keys = set()
            for vazmin_list in decks_vazmin.values():
                for record in vazmin_list:
                    if record.get('tipo_vazao') == 'VAZMIN':
                        vazao_val = self._sanitize_number(record.get('vazao'))
                        if vazao_val is not None:
                            codigo = int(record.get('codigo_usina', 0))
                            vazao_rounded = round(vazao_val, 2)
                            vazmin_keys.add((codigo, vazao_rounded))
            
            for codigo_usina, vazao_rounded in vazmin_keys:
                nome_usina = mapeamento_codigo_nome.get(codigo_usina, f"Usina {codigo_usina}")
                
                # Coletar presença em cada deck
                vazao_values = {}
                for deck_display_name in deck_names:
                    if deck_display_name not in decks_vazmin:
                        vazao_values[deck_display_name] = None
                        continue
                    
                    vazmin_list = decks_vazmin[deck_display_name]
                    found = False
                    for record in vazmin_list:
                        if record.get('tipo_vazao') == 'VAZMIN' and record.get('codigo_usina') == codigo_usina:
                            record_vazao = self._sanitize_number(record.get('vazao'))
                            if record_vazao is not None and round(record_vazao, 2) == vazao_rounded:
                                vazao_values[deck_display_name] = vazao_rounded
                                found = True
                                break
                    if not found:
                        vazao_values[deck_display_name] = None
                
                # Verificar se há variação entre decks
                valores_nao_nulos = [v for v in vazao_values.values() if v is not None]
                if len(valores_nao_nulos) == 0:
                    continue
                
                # Para VAZMIN, verificar se o valor aparece/desaparece entre decks
                if len(valores_nao_nulos) < len(deck_names):
                    matrix_row = {
                        "nome_usina": nome_usina,
                        "codigo_usina": codigo_usina,
                        "tipo_vazao": "VAZMIN",
                        "periodo_inicio": "N/A",
                        "periodo_fim": None,
                        "vazao_values": vazao_values,
                        "matrix": {}
                    }
                    
                    # Preencher matriz de diferenças
                    for i, deck_from in enumerate(deck_names):
                        for j, deck_to in enumerate(deck_names):
                            if i == j:
                                matrix_row["matrix"][f"{deck_from},{deck_to}"] = 0.0
                            else:
                                val_from = vazao_values.get(deck_from)
                                val_to = vazao_values.get(deck_to)
                                
                                if val_from is not None and val_to is not None:
                                    diff = round(val_to - val_from, 2)
                                    matrix_row["matrix"][f"{deck_from},{deck_to}"] = diff
                                elif val_from is None and val_to is not None:
                                    matrix_row["matrix"][f"{deck_from},{deck_to}"] = val_to
                                elif val_from is not None and val_to is None:
                                    matrix_row["matrix"][f"{deck_from},{deck_to}"] = -val_from
                                else:
                                    matrix_row["matrix"][f"{deck_from},{deck_to}"] = None
                    
                    matrix_data_vazmin.append(matrix_row)
            
            debug_print(f"[TOOL] ✅ VAZMIN: {len(matrix_data_vazmin)} registros com variações")
            
            # ETAPA 8: Calcular estatísticas
            stats = {
                "total_linhas_expandidas": len(expanded_data),
                "total_registros_vazmin": len(matrix_data_vazmin),
                "total_decks": len(deck_names),
                "total_meses": len(all_months_sorted),
                "usinas_com_vazmint": len(usinas_com_vazmint),
                "tipos_vazao": {
                    "VAZMIN": len(matrix_data_vazmin),
                    "VAZMINT": len(expanded_data)
                }
            }
            
            out = {
                "success": True,
                "is_comparison": True,
                "tool": self.get_name(),
                "expanded_data": expanded_data,  # NOVO: dados expandidos com forward fill (Usina x Deck x Mês)
                "matrix_data": matrix_data_vazmin,  # VAZMIN sem período (formato antigo)
                "deck_names": deck_names,
                "all_months": all_months_sorted,  # NOVO: lista de todos os meses
                "stats": stats,
                "visualization_type": "vazao_minima_matrix",
                "description": f"Matriz de vazão mínima com forward fill. {len(expanded_data)} linhas VAZMINT (Usina x Deck) expandidas para {len(all_months_sorted)} meses. {len(matrix_data_vazmin)} registros VAZMIN."
            }
            if codigo_csv is not None:
                from backend.newave.utils.hydraulic_plant_matcher import get_hydraulic_plant_matcher
                matcher = get_hydraulic_plant_matcher()
                if codigo_csv in matcher.code_to_names:
                    nome_arquivo_csv, nome_completo_csv, _ = matcher.code_to_names[codigo_csv]
                    out["selected_plant"] = {
                        "type": "hydraulic",
                        "codigo": codigo_csv,
                        "nome": nome_arquivo_csv,
                        "nome_completo": nome_completo_csv if nome_completo_csv else nome_arquivo_csv,
                        "tool_name": self.get_name()
                    }
            return out
            
        except Exception as e:
            safe_print(f"[TOOL] ❌ Erro ao processar: {type(e).__name__}: {e}")
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
                debug_print(f"[TOOL] ⚠️ Arquivo MODIF.DAT não encontrado em {deck_path}")
                return None
        
        try:
            modif = Modif.read(modif_path)
            return modif
        except Exception as e:
            safe_print(f"[TOOL] ❌ Erro ao ler MODIF.DAT: {e}")
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
                        if nome and nome != 'nan' and nome.lower() != 'none' and nome != '' and not pd.isna(row.get('nome')):
                            mapeamento[codigo] = nome
                            debug_print(f"[TOOL] Mapeamento: {codigo} -> {nome}")
        
        # Processar deck de janeiro (sobrescreve se houver nome melhor)
        if modif_jan is not None:
            usinas_jan = modif_jan.usina(df=True)
            if usinas_jan is not None and not usinas_jan.empty:
                if 'codigo' in usinas_jan.columns and 'nome' in usinas_jan.columns:
                    for _, row in usinas_jan.iterrows():
                        codigo = int(row['codigo'])
                        nome = str(row.get('nome', '')).strip()
                        if nome and nome != 'nan' and nome.lower() != 'none' and nome != '' and not pd.isna(row.get('nome')):
                            # Sobrescrever se não existia ou se o nome é mais completo
                            if codigo not in mapeamento or len(nome) > len(mapeamento.get(codigo, '')):
                                mapeamento[codigo] = nome
                                debug_print(f"[TOOL] Mapeamento: {codigo} -> {nome}")
        
        # Se ainda faltam nomes, tentar cruzar com HIDR.DAT
        # Identificar códigos sem nome corretamente (códigos que não estão no mapeamento)
        codigos_sem_nome = []
        if modif_dec is not None:
            usinas_dec = modif_dec.usina(df=True)
            if usinas_dec is not None and not usinas_dec.empty and 'codigo' in usinas_dec.columns:
                codigos_sem_nome.extend([c for c in usinas_dec['codigo'].unique() if c not in mapeamento])
        if modif_jan is not None:
            usinas_jan = modif_jan.usina(df=True)
            if usinas_jan is not None and not usinas_jan.empty and 'codigo' in usinas_jan.columns:
                codigos_sem_nome.extend([c for c in usinas_jan['codigo'].unique() if c not in mapeamento])
        codigos_sem_nome = list(set(codigos_sem_nome))
        
        if codigos_sem_nome:
            debug_print(f"[TOOL] ⚠️ {len(codigos_sem_nome)} usinas sem nome no MODIF, tentando HIDR.DAT...")
            try:
                from inewave.newave import Hidr
                # Usar primeiro deck disponível como referência
                deck_path_ref = self.deck_paths.get(self.selected_decks[0]) if self.deck_paths else self.deck_path
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
                                    debug_print(f"[TOOL] ✅ Nome do HIDR.DAT: {codigo_hidr} -> {nome_hidr}")
            except Exception as e:
                debug_print(f"[TOOL] ⚠️ Erro ao ler HIDR.DAT para nomes: {e}")
        
        return mapeamento
    
    def _modif_to_csv_code(self, codigo_modif: int, mapeamento_codigo_nome: Dict[int, str]) -> Optional[int]:
        """Mapeia código MODIF -> código CSV (deparahidro) via nome. selected_plant usa sempre CSV."""
        from backend.newave.utils.hydraulic_plant_matcher import get_hydraulic_plant_matcher
        matcher = get_hydraulic_plant_matcher()
        nome_modif = mapeamento_codigo_nome.get(codigo_modif)
        if not nome_modif:
            return None
        nome_upper = nome_modif.upper().strip()
        for csv_cod, (nome_arq, nome_compl, _) in matcher.code_to_names.items():
            if (nome_arq and nome_arq.upper().strip() == nome_upper) or (nome_compl and nome_compl.upper().strip() == nome_upper):
                return csv_cod
        return None
    
    def _csv_to_modif_code(self, codigo_csv: int, mapeamento_codigo_nome: Dict[int, str]) -> Optional[int]:
        """Mapeia código CSV (follow-up) -> código MODIF para filtrar dados."""
        from backend.newave.utils.hydraulic_plant_matcher import get_hydraulic_plant_matcher
        matcher = get_hydraulic_plant_matcher()
        if codigo_csv not in matcher.code_to_names:
            return None
        nome_arq, nome_compl, _ = matcher.code_to_names[codigo_csv]
        nome_busca = (nome_arq or nome_compl or "").upper().strip()
        if not nome_busca:
            return None
        for modif_cod, nome in mapeamento_codigo_nome.items():
            if nome and nome.upper().strip() == nome_busca:
                return modif_cod
        return None
    
    def _extract_usina_from_query(
        self, 
        query: str, 
        modif_dec: Modif, 
        modif_jan: Modif,
        mapeamento_codigo_nome: Dict[int, str]
    ) -> Optional[int]:
        """
        Extrai código da usina da query usando HydraulicPlantMatcher unificado.
        
        Args:
            query: Query do usuário
            modif_dec: Objeto Modif do deck de dezembro
            modif_jan: Objeto Modif do deck de janeiro
            mapeamento_codigo_nome: Mapeamento código -> nome já criado
            
        Returns:
            Código da usina ou None se não encontrado
        """
        if not mapeamento_codigo_nome:
            debug_print("[TOOL] ⚠️ Mapeamento de nomes não disponível")
            return None
        
        from backend.newave.utils.hydraulic_plant_matcher import get_hydraulic_plant_matcher
        
        matcher = get_hydraulic_plant_matcher()
        result = matcher.extract_plant_from_query(
            query=query,
            available_plants=mapeamento_codigo_nome,
            return_format="codigo",
            threshold=0.5
        )
        
        return result
    
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
                # Verificar se é VAZMIN ou VAZMINT (NÃO VAZMAXT)
                tipo_registro = type(registro).__name__
                
                # IMPORTANTE: Verificar VAZMINT primeiro porque "Vazmint" contém "Vazmin"
                # Se verificarmos VAZMIN primeiro, VAZMINT será capturado incorretamente como VAZMIN
                
                # Verificar se é VAZMINT (com data) - mais específico, verificar primeiro
                is_vazmint = (
                    ('Vazmint' in tipo_registro or 'VAZMINT' in tipo_registro) and 
                    'Vazmax' not in tipo_registro and 
                    'VAZMAX' not in tipo_registro
                )
                
                # Verificar se é VAZMIN (sem data) - deve NÃO ser VAZMINT
                is_vazmin = (
                    ('Vazmin' in tipo_registro or 'VAZMIN' in tipo_registro) and 
                    'Vazmint' not in tipo_registro and  # NÃO é VAZMINT
                    'VAZMINT' not in tipo_registro and  # NÃO é VAZMINT
                    'Vazmax' not in tipo_registro and 
                    'VAZMAX' not in tipo_registro
                )
                
                # Verificar VAZMINT primeiro (mais específico)
                if is_vazmint:
                    # VAZMINT (com data) - OBRIGATÓRIO ter período
                    vazao_val = registro.vazao if hasattr(registro, 'vazao') else None
                    data_inicio = registro.data_inicio if hasattr(registro, 'data_inicio') else None
                    
                    if data_inicio is None:
                        debug_print(f"[TOOL] [WARNING] VAZMINT sem data_inicio para usina {codigo_usina}, ignorando...")
                        continue
                    
                    periodo_inicio = self._format_date(data_inicio)
                    
                    if periodo_inicio == "N/A":
                        debug_print(f"[TOOL] [WARNING] VAZMINT com data_inicio inválida para usina {codigo_usina}, ignorando...")
                        continue
                    
                    registros.append({
                        "codigo_usina": codigo_usina,
                        "nome_usina": nome_usina if nome_usina else f"Usina {codigo_usina}",
                        "tipo_vazao": "VAZMINT",
                        "vazao": vazao_val,
                        "data_inicio": data_inicio,
                        "periodo_inicio": periodo_inicio,
                        "periodo_fim": None  # VAZMINT não tem data_fim explícita
                    })
                    debug_print(f"[TOOL] [DEBUG] VAZMINT extraído: usina={codigo_usina}, periodo={periodo_inicio}, vazao={vazao_val}")
                
                elif is_vazmin:
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
                        debug_print(f"[TOOL] [DEBUG] VAZMIN extraído: usina={codigo_usina}, vazao={vazao_val}")
        
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
        
        # Separar registros por tipo: VAZMINT (com período) e VAZMIN (sem período)
        vazmint_dec = [r for r in vazmin_dec if r.get("tipo_vazao") == "VAZMINT"]
        vazmint_jan = [r for r in vazmin_jan if r.get("tipo_vazao") == "VAZMINT"]
        vazmin_only_dec = [r for r in vazmin_dec if r.get("tipo_vazao") == "VAZMIN"]
        vazmin_only_jan = [r for r in vazmin_jan if r.get("tipo_vazao") == "VAZMIN"]
        
        debug_print(f"[TOOL] [DEBUG] VAZMINT: Dezembro={len(vazmint_dec)}, Janeiro={len(vazmint_jan)}")
        debug_print(f"[TOOL] [DEBUG] VAZMIN: Dezembro={len(vazmin_only_dec)}, Janeiro={len(vazmin_only_jan)}")
        
        # ============================================================
        # PARTE 1: VAZMINT (com período) - Lógica similar ao GTMIN
        # Chave: (codigo_usina, periodo_inicio)
        # ============================================================
        
        def create_vazmint_key(record):
            """Cria chave para VAZMINT baseada em código e período."""
            codigo = record.get("codigo_usina", 0)
            periodo = record.get("periodo_inicio", "N/A")
            return (codigo, periodo)
        
        # Indexar VAZMINT por chave
        vazmint_dec_indexed = {}
        for record in vazmint_dec:
            key = create_vazmint_key(record)
            vazmint_dec_indexed[key] = record
        
        vazmint_jan_indexed = {}
        for record in vazmint_jan:
            key = create_vazmint_key(record)
            vazmint_jan_indexed[key] = record
        
        # Comparar registros VAZMINT
        all_vazmint_keys = set(vazmint_dec_indexed.keys()) | set(vazmint_jan_indexed.keys())
        debug_print(f"[TOOL] [DEBUG] Total de chaves VAZMINT únicas: {len(all_vazmint_keys)}")
        
        for key in all_vazmint_keys:
            codigo_usina, periodo_inicio = key
            dec_record = vazmint_dec_indexed.get(key)
            jan_record = vazmint_jan_indexed.get(key)
            
            # Obter nome da usina
            nome_usina = self._get_nome_usina(codigo_usina, dec_record, jan_record, mapeamento_codigo_nome)
            
            # Extrair valores de vazão
            vazao_dec_val = self._sanitize_number(dec_record.get("vazao")) if dec_record else None
            vazao_jan_val = self._sanitize_number(jan_record.get("vazao")) if jan_record else None
            
            # Normalizar para comparação
            vazao_dec_normalized = vazao_dec_val if vazao_dec_val is not None else 0.0
            vazao_jan_normalized = vazao_jan_val if vazao_jan_val is not None else 0.0
            
            # Se ambos são zero, pular (não é um registro válido)
            if abs(vazao_dec_normalized) < 0.01 and abs(vazao_jan_normalized) < 0.01:
                continue
            
            # Identificar tipo de mudança
            tipo_mudanca = None
            magnitude_mudanca = 0
            
            if dec_record is None and jan_record is not None:
                # Novo registro em janeiro (inclusão)
                if vazao_jan_val is not None and abs(vazao_jan_val) > 0.01:
                    tipo_mudanca = "novo"
                    magnitude_mudanca = abs(vazao_jan_val)
            elif dec_record is not None and jan_record is None:
                # Registro removido em janeiro (exclusão)
                if vazao_dec_val is not None and abs(vazao_dec_val) > 0.01:
                    tipo_mudanca = "remocao"
                    magnitude_mudanca = abs(vazao_dec_val)
            elif dec_record is not None and jan_record is not None:
                # Registro existe em ambos - verificar se valor mudou
                if vazao_dec_val is not None and vazao_jan_val is not None:
                    diferenca_val = vazao_jan_val - vazao_dec_val
                    if abs(diferenca_val) > 0.01:
                        if diferenca_val > 0:
                            tipo_mudanca = "aumento"
                        else:
                            tipo_mudanca = "queda"
                        magnitude_mudanca = abs(diferenca_val)
                    else:
                        # Valores iguais - incluir mesmo assim para exibição
                        tipo_mudanca = "sem_mudanca"
                        magnitude_mudanca = 0
                elif vazao_dec_val is None and vazao_jan_val is not None:
                    if abs(vazao_jan_val) > 0.01:
                        tipo_mudanca = "novo"
                        magnitude_mudanca = abs(vazao_jan_val)
                elif vazao_dec_val is not None and vazao_jan_val is None:
                    if abs(vazao_dec_val) > 0.01:
                        tipo_mudanca = "remocao"
                        magnitude_mudanca = abs(vazao_dec_val)
            
            # Sempre adicionar à lista se registro existe em pelo menos um deck e tem valor válido
            # Se tipo_mudanca ainda não foi definido mas há valores válidos, marcar como sem mudança
            if tipo_mudanca is None and dec_record is not None and jan_record is not None:
                tipo_mudanca = "sem_mudanca"
                magnitude_mudanca = 0
            
            # Se há mudança identificada ou valores válidos, adicionar à lista
            if tipo_mudanca is not None:
                # Garantir que período está presente (obrigatório para VAZMINT)
                periodo_display = periodo_inicio
                if periodo_display == "N/A" or not periodo_display:
                    # Tentar obter do registro original
                    if dec_record:
                        periodo_display = dec_record.get("periodo_inicio", "N/A")
                    elif jan_record:
                        periodo_display = jan_record.get("periodo_inicio", "N/A")
                    else:
                        periodo_display = "N/A"
                
                debug_print(f"[TOOL] [DEBUG] VAZMINT mudança: {nome_usina}, período={periodo_display}, {tipo_mudanca}, vazao_dec={vazao_dec_val}, vazao_jan={vazao_jan_val}")
                
                mudanca = {
                    "codigo_usina": int(codigo_usina),
                    "nome_usina": str(nome_usina).strip(),
                    "tipo_mudanca": tipo_mudanca,
                    "tipo_vazao": "VAZMINT",
                    "periodo_inicio": periodo_display,  # Sempre incluir período para VAZMINT
                    "periodo_fim": None,
                    "vazao_dezembro": round(vazao_dec_val, 2) if vazao_dec_val is not None else None,
                    "vazao_janeiro": round(vazao_jan_val, 2) if vazao_jan_val is not None else None,
                    "magnitude_mudanca": round(magnitude_mudanca, 2),
                    "diferenca": round(vazao_jan_val - vazao_dec_val, 2) if (
                        vazao_dec_val is not None and vazao_jan_val is not None
                    ) else None,
                    "data_inicio": dec_record.get("data_inicio") if dec_record else (jan_record.get("data_inicio") if jan_record else None)
                }
                mudancas.append(mudanca)
        
        # ============================================================
        # PARTE 2: VAZMIN (sem período) - Seção separada
        # Comparar por usina, cada registro individualmente
        # ============================================================
        
        # Agrupar VAZMIN por código de usina
        vazmin_dec_by_usina = {}
        for record in vazmin_only_dec:
            codigo = record.get("codigo_usina", 0)
            if codigo not in vazmin_dec_by_usina:
                vazmin_dec_by_usina[codigo] = []
            vazmin_dec_by_usina[codigo].append(record)
        
        vazmin_jan_by_usina = {}
        for record in vazmin_only_jan:
            codigo = record.get("codigo_usina", 0)
            if codigo not in vazmin_jan_by_usina:
                vazmin_jan_by_usina[codigo] = []
            vazmin_jan_by_usina[codigo].append(record)
        
        # Todas as usinas com VAZMIN
        all_vazmin_usinas = set(vazmin_dec_by_usina.keys()) | set(vazmin_jan_by_usina.keys())
        debug_print(f"[TOOL] [DEBUG] Total de usinas com VAZMIN: {len(all_vazmin_usinas)}")
        
        for codigo_usina in all_vazmin_usinas:
            dec_records = vazmin_dec_by_usina.get(codigo_usina, [])
            jan_records = vazmin_jan_by_usina.get(codigo_usina, [])
            
            # Obter nome da usina
            nome_usina = mapeamento_codigo_nome.get(codigo_usina)
            if not nome_usina or nome_usina.strip() == '':
                for record in dec_records + jan_records:
                    nome_temp = str(record.get("nome_usina", '')).strip()
                    if nome_temp and nome_temp != 'nan' and nome_temp != '':
                        nome_usina = nome_temp
                        break
            if not nome_usina or nome_usina.strip() == '':
                nome_usina = f'Usina {codigo_usina}'
            
            # Extrair valores de vazão (lista de valores)
            vazoes_dec = sorted([self._sanitize_number(r.get("vazao")) for r in dec_records if self._sanitize_number(r.get("vazao")) is not None])
            vazoes_jan = sorted([self._sanitize_number(r.get("vazao")) for r in jan_records if self._sanitize_number(r.get("vazao")) is not None])
            
            debug_print(f"[TOOL] [DEBUG] VAZMIN usina {codigo_usina} ({nome_usina}): Dez={vazoes_dec}, Jan={vazoes_jan}")
            
            # Comparar conjuntos de vazões
            # Identificar inclusões, exclusões e alterações
            
            # Valores removidos (estavam em dezembro, não estão em janeiro)
            # Valores que existem em ambos (sem mudança)
            vazoes_removidas = []
            vazoes_sem_mudanca = []
            vazoes_jan_copy = vazoes_jan.copy()
            for v_dec in vazoes_dec:
                if v_dec in vazoes_jan_copy:
                    vazoes_jan_copy.remove(v_dec)  # Match encontrado
                    vazoes_sem_mudanca.append(v_dec)  # Valores iguais em ambos
                else:
                    vazoes_removidas.append(v_dec)
            
            # Valores adicionados (estão em janeiro, não estavam em dezembro)
            vazoes_adicionadas = vazoes_jan_copy  # O que sobrou são adições
            
            # Registrar valores sem mudança
            for vazao in vazoes_sem_mudanca:
                if abs(vazao) > 0.01:
                    debug_print(f"[TOOL] [DEBUG] VAZMIN sem mudança: {nome_usina}, vazão={vazao}")
                    mudanca = {
                        "codigo_usina": int(codigo_usina),
                        "nome_usina": str(nome_usina).strip(),
                        "tipo_mudanca": "sem_mudanca",
                        "tipo_vazao": "VAZMIN",
                        "periodo_inicio": "N/A",
                        "periodo_fim": None,
                        "vazao_dezembro": round(vazao, 2),
                        "vazao_janeiro": round(vazao, 2),
                        "magnitude_mudanca": 0,
                        "diferenca": 0
                    }
                    mudancas.append(mudanca)
            
            # Registrar remoções
            for vazao in vazoes_removidas:
                if abs(vazao) > 0.01:
                    debug_print(f"[TOOL] [DEBUG] VAZMIN remoção: {nome_usina}, vazão={vazao}")
                    mudanca = {
                        "codigo_usina": int(codigo_usina),
                        "nome_usina": str(nome_usina).strip(),
                        "tipo_mudanca": "remocao",
                        "tipo_vazao": "VAZMIN",
                        "periodo_inicio": "N/A",
                        "periodo_fim": None,
                        "vazao_dezembro": round(vazao, 2),
                        "vazao_janeiro": None,
                        "magnitude_mudanca": round(abs(vazao), 2),
                        "diferenca": None
                    }
                    mudancas.append(mudanca)
            
            # Registrar adições
            for vazao in vazoes_adicionadas:
                if abs(vazao) > 0.01:
                    debug_print(f"[TOOL] [DEBUG] VAZMIN adição: {nome_usina}, vazão={vazao}")
                    mudanca = {
                        "codigo_usina": int(codigo_usina),
                        "nome_usina": str(nome_usina).strip(),
                        "tipo_mudanca": "novo",
                        "tipo_vazao": "VAZMIN",
                        "periodo_inicio": "N/A",
                        "periodo_fim": None,
                        "vazao_dezembro": None,
                        "vazao_janeiro": round(vazao, 2),
                        "magnitude_mudanca": round(abs(vazao), 2),
                        "diferenca": None
                    }
                    mudancas.append(mudanca)
        
        return mudancas
    
    def _get_nome_usina(self, codigo_usina: int, dec_record, jan_record, mapeamento: Dict[int, str]) -> str:
        """Obtém o nome da usina do mapeamento ou dos registros."""
        nome_usina = mapeamento.get(codigo_usina)
        if not nome_usina or nome_usina.strip() == '':
            if dec_record is not None:
                nome_temp = str(dec_record.get("nome_usina", '')).strip()
                if nome_temp and nome_temp != 'nan' and nome_temp != '':
                    nome_usina = nome_temp
            if (not nome_usina or nome_usina.strip() == '') and jan_record is not None:
                nome_temp = str(jan_record.get("nome_usina", '')).strip()
                if nome_temp and nome_temp != 'nan' and nome_temp != '':
                    nome_usina = nome_temp
        if not nome_usina or nome_usina.strip() == '':
            nome_usina = f'Usina {codigo_usina}'
        return nome_usina
    
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
    
    def _apply_forward_fill_to_matrix(self, expanded_data: List[Dict[str, Any]], all_months: List[str]) -> List[Dict[str, Any]]:
        """
        Aplica forward fill na matriz já formada.
        
        IMPORTANTE: Cada linha (Usina + Deck) é processada independentemente.
        O forward fill ocorre apenas dentro da mesma linha.
        
        Conceito:
        - Percorrer os meses em ordem cronológica para cada linha.
        - Quando encontrar um valor, guardá-lo como "último valor conhecido".
        - Para meses sem valor, usar o "último valor conhecido".
        - Se não houver valor inicial, os meses anteriores permanecem vazios.
        
        Exemplo:
        - Registros originais: 2025-12=4600, 2026-01=3900, 2026-11=4600
        - Resultado: 2025-12=4600, 2026-01=3900, 2026-02=3900, ..., 2026-10=3900, 2026-11=4600
        
        Args:
            expanded_data: Lista de linhas (cada linha é Usina + Deck com monthly_values)
            all_months: Lista de meses em ordem cronológica
            
        Returns:
            Lista de linhas com forward fill aplicado
        """
        debug_print(f"[TOOL] [FORWARD FILL] Processando {len(expanded_data)} linhas...")
        
        for row in expanded_data:
            monthly_values = row.get("monthly_values", {})
            original_periods = row.get("original_periods", [])
            
            # Debug: mostrar estado antes
            valores_antes = {k: v for k, v in monthly_values.items() if v is not None}
            
            # Aplicar forward fill
            ultimo_valor_conhecido = None
            for mes in all_months:
                valor_atual = monthly_values.get(mes)
                
                if valor_atual is not None:
                    # Mês tem valor original - guardar como último conhecido
                    ultimo_valor_conhecido = valor_atual
                elif ultimo_valor_conhecido is not None:
                    # Mês sem valor - preencher com último valor conhecido
                    monthly_values[mes] = ultimo_valor_conhecido
                # else: Nenhum valor conhecido ainda - mantém None
            
            # Debug: mostrar estado depois
            valores_depois = {k: v for k, v in monthly_values.items() if v is not None}
            
            # Atualizar monthly_values na linha
            row["monthly_values"] = monthly_values
            
            # Log de debug
            nome_usina = row.get("nome_usina", "?")
            deck_name = row.get("deck_name", "?")
            debug_print(f"[TOOL] [FORWARD FILL] {nome_usina} - {deck_name}:")
            debug_print(f"[TOOL]   Originais: {original_periods}")
            debug_print(f"[TOOL]   Antes: {len(valores_antes)} valores -> Depois: {len(valores_depois)} valores")
            if len(valores_depois) > len(valores_antes):
                preenchidos = len(valores_depois) - len(valores_antes)
                debug_print(f"[TOOL]   ✅ {preenchidos} meses preenchidos via forward fill")
        
        return expanded_data
    
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
        
        IMPORTANTE: Esta tool retorna ambos os tipos de vazão mínima:
        - VAZMIN: Vazão mínima sem período (valor fixo que se aplica a todo o horizonte)
        - VAZMINT: Vazão mínima com período (valor que se aplica a um período específico)
        
        Quando o usuário consulta "vazão mínima", "mudanças vazão mínima" ou termos similares,
        a tool retorna TODAS as mudanças de ambos os tipos (VAZMIN e VAZMINT), diferenciadas
        no campo "tipo_vazao" de cada registro e claramente indicadas na descrição do resultado.
        
        Esta tool é especializada em:
        - Identificar todas as mudanças de vazão mínima (VAZMIN e VAZMINT) entre dezembro e janeiro
        - Diferenciar entre VAZMIN (sem período) e VAZMINT (com período)
        - Ordenar mudanças por magnitude (maior variação primeiro)
        - Classificar tipos de mudança (aumento, queda, novo, remocao)
        - Retornar apenas as mudanças (não todos os registros)
        
        Queries que ativam esta tool (retornam ambos VAZMIN e VAZMINT):
        - "mudanças vazão mínima" ou "mudancas vazao minima"
        - "variação vazão mínima" ou "variacao vazao minima"
        - "análise vazão mínima" ou "analise vazao minima"
        - "mudanças vazmin" ou "mudancas vazmin"
        - "mudanças vazmint" ou "mudancas vazmint"
        - "vazão mínima" ou "vazao minima"
        
        Termos-chave: mudanças vazão mínima, variação vazão mínima, análise vazão mínima, mudancas vazao minima, variacao vazao minima, analise vazao minima, vazmin, vazmint, mudanças em vazões mínimas, variações de vazão mínima
        """