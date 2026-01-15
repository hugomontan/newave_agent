"""
Tool para análise de mudanças de vazão mínima (VAZMIN/VAZMINT) entre decks no modo multideck.
Suporta comparação de N decks para análise histórica de vazão mínima.
"""
from newave_agent.app.tools.base import NEWAVETool
from inewave.newave import Modif
import os
import pandas as pd
import re
from typing import Dict, Any, List, Optional
from newave_agent.app.utils.deck_loader import (
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
                print(f"[TOOL] ⚠️ Erro ao carregar decks: {e}")
    
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
        print(f"[TOOL] {self.get_name()}: Iniciando análise de mudanças de vazão mínima...")
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
            
            # ETAPA 3.5: Extrair usina da query (se especificada)
            print("[TOOL] ETAPA 3.5: Verificando se há filtro por usina na query...")
            codigo_usina_filtro = self._extract_usina_from_query(query, modif_dec, modif_jan, mapeamento_codigo_nome)
            if codigo_usina_filtro is not None:
                nome_usina_filtro = mapeamento_codigo_nome.get(codigo_usina_filtro, f"Usina {codigo_usina_filtro}")
                print(f"[TOOL] ✅ Filtro por usina detectado: {codigo_usina_filtro} - {nome_usina_filtro}")
            else:
                print("[TOOL] ℹ️ Nenhum filtro por usina detectado - retornando todas as mudanças")
            
            # ETAPA 4: Filtrar apenas registros de VAZMIN e VAZMINT
            print("[TOOL] ETAPA 4: Filtrando registros de VAZMIN e VAZMINT...")
            vazmin_dec = self._extract_vazmin_records(modif_dec)
            vazmin_jan = self._extract_vazmin_records(modif_jan)
            
            # Aplicar filtro por usina se especificado
            if codigo_usina_filtro is not None:
                vazmin_dec = [r for r in vazmin_dec if r.get('codigo_usina') == codigo_usina_filtro]
                vazmin_jan = [r for r in vazmin_jan if r.get('codigo_usina') == codigo_usina_filtro]
                print(f"[TOOL] ✅ Dados filtrados por usina {codigo_usina_filtro}")
            
            print(f"[TOOL] ✅ Registros VAZMIN/VAZMINT Dezembro: {len(vazmin_dec)}")
            print(f"[TOOL] ✅ Registros VAZMIN/VAZMINT Janeiro: {len(vazmin_jan)}")
            
            # Debug: mostrar todos os registros antes da comparação
            print(f"[TOOL] [DEBUG] Registros dezembro detalhados:")
            for i, r in enumerate(vazmin_dec):
                print(f"[TOOL] [DEBUG]   [{i}] codigo={r.get('codigo_usina')}, tipo={r.get('tipo_vazao')}, vazao={r.get('vazao')}, periodo={r.get('periodo_inicio')}")
            print(f"[TOOL] [DEBUG] Registros janeiro detalhados:")
            for i, r in enumerate(vazmin_jan):
                print(f"[TOOL] [DEBUG]   [{i}] codigo={r.get('codigo_usina')}, tipo={r.get('tipo_vazao')}, vazao={r.get('vazao')}, periodo={r.get('periodo_inicio')}")
            
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
                "description": description
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
    
    def _execute_multi_deck_matrix(self, query: str) -> Dict[str, Any]:
        """
        Executa análise de vazão mínima para múltiplos decks (mais de 2) usando matriz de comparação.
        Retorna formato idêntico ao GTMIN, mas com separação de VAZMIN/VAZMINT.
        
        Args:
            query: Query do usuário
            
        Returns:
            Dicionário com dados formatados para matriz de comparação
        """
        print("[TOOL] Executando análise de matriz para múltiplos decks...")
        
        try:
            # ETAPA 1: Ler MODIF.DAT de todos os decks
            print("[TOOL] ETAPA 1: Lendo arquivos MODIF.DAT de todos os decks...")
            decks_modif = {}
            decks_vazmin = {}
            deck_names = []
            
            for deck_name in self.selected_decks:
                deck_path = self.deck_paths.get(deck_name)
                deck_display_name = self.deck_display_names.get(deck_name, deck_name)
                deck_names.append(deck_display_name)
                
                modif = self._read_modif_file(deck_path)
                if modif is None:
                    print(f"[TOOL] ⚠️ Arquivo MODIF.DAT não encontrado em {deck_path}")
                    continue
                
                decks_modif[deck_display_name] = modif
                vazmin_records = self._extract_vazmin_records(modif)
                decks_vazmin[deck_display_name] = vazmin_records
                print(f"[TOOL] ✅ Deck {deck_display_name}: {len(vazmin_records)} registros VAZMIN/VAZMINT")
            
            if len(decks_modif) < 2:
                return {
                    "success": False,
                    "error": "São necessários pelo menos 2 decks válidos para comparação",
                    "tool": self.get_name()
                }
            
            # ETAPA 2: Criar mapeamento código -> nome das usinas (usar primeiro e último deck como base)
            print("[TOOL] ETAPA 2: Criando mapeamento código -> nome das usinas...")
            first_modif = list(decks_modif.values())[0]
            last_modif = list(decks_modif.values())[-1]
            mapeamento_codigo_nome = self._create_codigo_nome_mapping(first_modif, last_modif)
            print(f"[TOOL] ✅ Mapeamento criado: {len(mapeamento_codigo_nome)} usinas mapeadas")
            
            # ETAPA 3: Extrair usina da query (opcional)
            print("[TOOL] ETAPA 3: Verificando se há filtro por usina na query...")
            codigo_usina_filtro = self._extract_usina_from_query(query, first_modif, last_modif, mapeamento_codigo_nome)
            if codigo_usina_filtro is not None:
                nome_usina_filtro = mapeamento_codigo_nome.get(codigo_usina_filtro, f"Usina {codigo_usina_filtro}")
                print(f"[TOOL] ✅ Filtro por usina detectado: {codigo_usina_filtro} - {nome_usina_filtro}")
                # Aplicar filtro
                for deck_name in decks_vazmin:
                    decks_vazmin[deck_name] = [
                        r for r in decks_vazmin[deck_name] 
                        if r.get('codigo_usina') == codigo_usina_filtro
                    ]
            
            # ETAPA 4: Criar estrutura de dados para matriz
            print("[TOOL] ETAPA 4: Criando estrutura de matriz de comparação...")
            
            # Separar VAZMINT e VAZMIN para processamento diferente
            # VAZMINT: chave (codigo_usina, tipo_vazao, periodo_inicio)
            # VAZMIN: chave (codigo_usina, tipo_vazao, vazao_value) - incluir valor na chave
            
            def create_vazmint_key(record):
                """Cria chave para VAZMINT baseada em código, tipo e período."""
                codigo = int(record.get('codigo_usina', 0))
                tipo_vazao = record.get('tipo_vazao', 'VAZMINT')
                periodo = record.get('periodo_inicio', 'N/A')
                return (codigo, tipo_vazao, periodo)
            
            def create_vazmin_key(record):
                """Cria chave para VAZMIN baseada em código, tipo e valor."""
                codigo = int(record.get('codigo_usina', 0))
                tipo_vazao = record.get('tipo_vazao', 'VAZMIN')
                vazao_val = self._sanitize_number(record.get('vazao'))
                # Arredondar para evitar problemas de precisão float
                vazao_rounded = round(vazao_val, 2) if vazao_val is not None else None
                return (codigo, tipo_vazao, vazao_rounded)
            
            # Coletar todas as chaves únicas
            all_keys = set()
            
            # Coletar chaves VAZMINT
            for vazmin_list in decks_vazmin.values():
                for record in vazmin_list:
                    if record.get('tipo_vazao') == 'VAZMINT':
                        key = create_vazmint_key(record)
                        all_keys.add(key)
            
            # Coletar chaves VAZMIN (incluir valor na chave)
            for vazmin_list in decks_vazmin.values():
                for record in vazmin_list:
                    if record.get('tipo_vazao') == 'VAZMIN':
                        vazao_val = self._sanitize_number(record.get('vazao'))
                        if vazao_val is not None:
                            key = create_vazmin_key(record)
                            all_keys.add(key)
            
            print(f"[TOOL] ✅ Total de chaves únicas: {len(all_keys)}")
            
            # ETAPA 5: Construir matriz de comparação
            matrix_data = []
            
            for key in all_keys:
                if len(key) == 3:
                    codigo_usina, tipo_vazao, third_component = key
                else:
                    continue
                
                nome_usina = mapeamento_codigo_nome.get(codigo_usina, f"Usina {codigo_usina}")
                
                # Coletar valores de vazão de cada deck
                vazao_values = {}
                
                for deck_display_name in deck_names:
                    if deck_display_name not in decks_vazmin:
                        vazao_values[deck_display_name] = None
                        continue
                    
                    vazmin_list = decks_vazmin[deck_display_name]
                    matching_record = None
                    
                    # Buscar registro correspondente
                    for record in vazmin_list:
                        if tipo_vazao == 'VAZMINT':
                            # VAZMINT: comparar por código e período
                            if (record.get('codigo_usina') == codigo_usina and
                                record.get('tipo_vazao') == 'VAZMINT' and
                                record.get('periodo_inicio') == third_component):
                                matching_record = record
                                break
                        elif tipo_vazao == 'VAZMIN':
                            # VAZMIN: comparar por código e valor (arredondado)
                            record_vazao = self._sanitize_number(record.get('vazao'))
                            record_vazao_rounded = round(record_vazao, 2) if record_vazao is not None else None
                            if (record.get('codigo_usina') == codigo_usina and
                                record.get('tipo_vazao') == 'VAZMIN' and
                                record_vazao_rounded == third_component):
                                matching_record = record
                                break
                    
                    if matching_record:
                        vazao_val = self._sanitize_number(matching_record.get('vazao'))
                        vazao_values[deck_display_name] = round(vazao_val, 2) if vazao_val is not None else None
                    else:
                        vazao_values[deck_display_name] = None
                
                # Verificar se há alguma mudança (não todos None ou todos iguais)
                valores_nao_nulos = [v for v in vazao_values.values() if v is not None]
                if len(valores_nao_nulos) == 0:
                    continue  # Pular se não há valores
                
                # Verificar se há variação
                valores_unicos = set(valores_nao_nulos)
                if len(valores_unicos) <= 1:
                    continue  # Pular se todos os valores são iguais
                
                # Determinar período para o registro
                if tipo_vazao == 'VAZMINT':
                    periodo_inicio = third_component  # third_component é o período
                    periodo_fim = None
                else:  # VAZMIN
                    periodo_inicio = "N/A"
                    periodo_fim = None
                
                # Calcular diferenças entre todos os pares de decks
                matrix_row = {
                    "nome_usina": nome_usina,
                    "codigo_usina": codigo_usina,
                    "tipo_vazao": tipo_vazao,  # IMPORTANTE: incluir tipo_vazao
                    "periodo_inicio": periodo_inicio,
                    "periodo_fim": periodo_fim,
                    "vazao_values": vazao_values,  # Dict[deck_name, value] - similar a gtmin_values
                    "matrix": {}  # Dict[(deck_from, deck_to), difference]
                }
                
                # Preencher matriz de diferenças
                # Usar string como chave para compatibilidade com JSON
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
                "usinas_unicas": len(set(row["codigo_usina"] for row in matrix_data)),
                "tipos_vazao": {
                    "VAZMIN": len([r for r in matrix_data if r["tipo_vazao"] == "VAZMIN"]),
                    "VAZMINT": len([r for r in matrix_data if r["tipo_vazao"] == "VAZMINT"])
                }
            }
            
            return {
                "success": True,
                "is_comparison": True,
                "tool": self.get_name(),
                "matrix_data": matrix_data,
                "deck_names": deck_names,
                "stats": stats,
                "visualization_type": "vazao_minima_matrix",
                "description": f"Matriz de comparação de vazão mínima entre {len(deck_names)} decks, com {len(matrix_data)} registros com variações. Separado por VAZMIN (sem período) e VAZMINT (com período)."
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
                        if nome and nome != 'nan' and nome.lower() != 'none' and nome != '' and not pd.isna(row.get('nome')):
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
                        if nome and nome != 'nan' and nome.lower() != 'none' and nome != '' and not pd.isna(row.get('nome')):
                            # Sobrescrever se não existia ou se o nome é mais completo
                            if codigo not in mapeamento or len(nome) > len(mapeamento.get(codigo, '')):
                                mapeamento[codigo] = nome
                                print(f"[TOOL] Mapeamento: {codigo} -> {nome}")
        
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
            print(f"[TOOL] ⚠️ {len(codigos_sem_nome)} usinas sem nome no MODIF, tentando HIDR.DAT...")
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
                                    print(f"[TOOL] ✅ Nome do HIDR.DAT: {codigo_hidr} -> {nome_hidr}")
            except Exception as e:
                print(f"[TOOL] ⚠️ Erro ao ler HIDR.DAT para nomes: {e}")
        
        return mapeamento
    
    def _extract_usina_from_query(
        self, 
        query: str, 
        modif_dec: Modif, 
        modif_jan: Modif,
        mapeamento_codigo_nome: Dict[int, str]
    ) -> Optional[int]:
        """
        Extrai código da usina da query.
        Busca por número ou nome da usina.
        
        Args:
            query: Query do usuário
            modif_dec: Objeto Modif do deck de dezembro
            modif_jan: Objeto Modif do deck de janeiro
            mapeamento_codigo_nome: Mapeamento código -> nome já criado
            
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
        
        # Obter códigos válidos de ambos os decks
        codigos_validos = set()
        if modif_dec is not None:
            usinas_dec = modif_dec.usina(df=True)
            if usinas_dec is not None and not usinas_dec.empty and 'codigo' in usinas_dec.columns:
                codigos_validos.update(usinas_dec['codigo'].unique())
        if modif_jan is not None:
            usinas_jan = modif_jan.usina(df=True)
            if usinas_jan is not None and not usinas_jan.empty and 'codigo' in usinas_jan.columns:
                codigos_validos.update(usinas_jan['codigo'].unique())
        
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
        palavras_ignorar = {
            'de', 'da', 'do', 'das', 'dos', 'e', 'a', 'o', 'as', 'os', 'em', 'na', 'no', 'nas', 'nos',
            'vazão', 'vazao', 'mínima', 'minima', 'variação', 'variacao', 'mudanças', 'mudancas',
            'qual', 'foi', 'a', 'o', 'para', 'por', 'com', 'sem'
        }
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
                        print(f"[TOOL] [WARNING] VAZMINT sem data_inicio para usina {codigo_usina}, ignorando...")
                        continue
                    
                    periodo_inicio = self._format_date(data_inicio)
                    
                    if periodo_inicio == "N/A":
                        print(f"[TOOL] [WARNING] VAZMINT com data_inicio inválida para usina {codigo_usina}, ignorando...")
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
                    print(f"[TOOL] [DEBUG] VAZMINT extraído: usina={codigo_usina}, periodo={periodo_inicio}, vazao={vazao_val}")
                
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
                        print(f"[TOOL] [DEBUG] VAZMIN extraído: usina={codigo_usina}, vazao={vazao_val}")
        
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
        
        print(f"[TOOL] [DEBUG] VAZMINT: Dezembro={len(vazmint_dec)}, Janeiro={len(vazmint_jan)}")
        print(f"[TOOL] [DEBUG] VAZMIN: Dezembro={len(vazmin_only_dec)}, Janeiro={len(vazmin_only_jan)}")
        
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
        print(f"[TOOL] [DEBUG] Total de chaves VAZMINT únicas: {len(all_vazmint_keys)}")
        
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
                
                print(f"[TOOL] [DEBUG] VAZMINT mudança: {nome_usina}, período={periodo_display}, {tipo_mudanca}, vazao_dec={vazao_dec_val}, vazao_jan={vazao_jan_val}")
                
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
        print(f"[TOOL] [DEBUG] Total de usinas com VAZMIN: {len(all_vazmin_usinas)}")
        
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
            
            print(f"[TOOL] [DEBUG] VAZMIN usina {codigo_usina} ({nome_usina}): Dez={vazoes_dec}, Jan={vazoes_jan}")
            
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
                    print(f"[TOOL] [DEBUG] VAZMIN sem mudança: {nome_usina}, vazão={vazao}")
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
                    print(f"[TOOL] [DEBUG] VAZMIN remoção: {nome_usina}, vazão={vazao}")
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
                    print(f"[TOOL] [DEBUG] VAZMIN adição: {nome_usina}, vazão={vazao}")
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