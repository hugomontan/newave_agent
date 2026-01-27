"""
Tool para consultar informações do Bloco CT (Usinas Termelétricas) do DECOMP.
Acessa dados de cadastro de UTE, patamares de carga, CVU, disponibilidade, inflexibilidade.
"""
from backend.decomp.tools.base import DECOMPTool
from backend.decomp.config import safe_print
from idecomp.decomp import Dadger
import os
import pandas as pd
import re
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List

# Adicionar shared ao path para importar o matcher
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "shared"))
from backend.core.utils.usina_name_matcher import find_usina_match, normalize_usina_name
from backend.decomp.utils.thermal_plant_matcher import get_decomp_thermal_plant_matcher

class CTUsinasTermelétricasTool(DECOMPTool):
    """
    Tool para consultar informações do Bloco CT (Usinas Termelétricas) do DECOMP.
    
    Dados disponíveis:
    - Código da usina
    - Código do submercado
    - Nome da usina
    - Estágio de operação
    - Patamares de carga (1=PESADA, 2=MEDIA, 3=LEVE):
      - Custo Variável Unitário (CVU)
      - Disponibilidade (DISP)
      - Inflexibilidade (INFL)
    """
    
    def get_name(self) -> str:
        return "CTUsinasTermelétricasTool"
    
    def can_handle(self, query: str) -> bool:
        """
        Verifica se a query é sobre usinas termelétricas do Bloco CT.
        
        Args:
            query: Query do usuário
            
        Returns:
            True se a tool pode processar a query
        """
        query_lower = query.lower()
        
        # Excluir queries que são especificamente sobre disponibilidade ou inflexibilidade
        # sem mencionar CVU, bloco CT, ou outros termos relacionados
        if "disponibilidade" in query_lower and not any(kw in query_lower for kw in ["cvu", "custo", "bloco ct", "registro ct", "ct", "usina term"]):
            return False
        if "inflexibilidade" in query_lower and not any(kw in query_lower for kw in ["cvu", "custo", "bloco ct", "registro ct", "ct", "usina term"]):
            return False
        
        keywords = [
            "usina termelétrica",
            "usina termeletrica",
            "usinas termelétricas",
            "usinas termicas",
            "ute",
            "utes",
            "bloco ct",
            "registro ct",
            "ct decomp",
            "cvu",
            "custo variável",
            "custo variavel",
            "custo variável unitário",
            "custo variavel unitario",
            "patamar de carga",
            "patamar carga",
            "disponibilidade térmica",
            "disponibilidade termica",
            "inflexibilidade térmica",
            "inflexibilidade termica",
        ]
        return any(kw in query_lower for kw in keywords)
    
    def get_description(self) -> str:
        return """
        Tool para consultar informações do Bloco CT (Usinas Termelétricas) do DECOMP.
        
        Acessa dados do registro CT que define:
        - Cadastro de Usinas Termelétricas (UTE)
        - Código da usina e submercado
        - Nome da usina
        - Estágio de operação
        - Dados por patamar de carga (1=PESADA, 2=MEDIA, 3=LEVE):
          * Custo Variável Unitário (CVU)
          * Disponibilidade (DISP)
          * Inflexibilidade (INFL)
        
        Filtros disponíveis:
        - Por CVU apenas: mostra apenas custos variáveis unitários (remove disponibilidade e inflexibilidade)
        - Por estágio: filtra por estágio específico
        - Por patamar: filtra por patamar específico (pesada, média, leve ou 1, 2, 3)
        - Combinações: CVU + patamar, CVU + estágio, etc.
        
        Exemplos de queries:
        - "Quais são as usinas termelétricas do deck?"
        - "Qual o CVU da usina Angra 1?" (mostra apenas CVU, todos os patamares)
        - "CVU de cubatão" (mostra apenas CVU)
        - "CVU de cubatão patamar pesada" (mostra apenas CVU do patamar pesada)
        - "CVU de cubatão estágio 1" (mostra apenas CVU do estágio 1)
        - "CVU de cubatão estágio 1 patamar pesada" (mostra apenas CVU do estágio 1, patamar pesada)
        - "Mostre todas as UTE do submercado 1"
        - "Usinas com maior disponibilidade"
        - "CVU do patamar pesada"
        """
    
    def execute(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Executa a consulta sobre usinas termelétricas do Bloco CT.
        
        Args:
            query: Query do usuário
            **kwargs: Argumentos adicionais opcionais
            
        Returns:
            Dict com dados das usinas termelétricas formatados
        """
        try:
            # ⚡ OTIMIZAÇÃO: Usar cache global do Dadger
            from backend.decomp.utils.dadger_cache import get_cached_dadger
            dadger = get_cached_dadger(self.deck_path)
            
            if dadger is None:
                return {
                    "success": False,
                    "error": "Arquivo dadger não encontrado (nenhum arquivo dadger.rv* encontrado)"
                }
            
            # Extrair filtros da query
            forced_plant_code = kwargs.get("forced_plant_code")
            if forced_plant_code is not None:
                codigo_usina = int(forced_plant_code)
                safe_print(f"[CT TOOL] ⚙️ Código forçado recebido via follow-up: {codigo_usina}")
            else:
                codigo_usina = self._extract_codigo_usina(query)
            codigo_submercado = self._extract_codigo_submercado(query)
            estagio = self._extract_estagio(query)
            patamar = self._extract_patamar(query)  # NOVO: extrair patamar
            is_cvu_only = self._is_cvu_query(query)  # NOVO: verificar se é query de CVU
            is_cvu_inflexibilidade_disponibilidade_query = self._is_cvu_inflexibilidade_disponibilidade_query(query)
            
            # MUDANÇA: Se é query de CVU, SEMPRE usar estágio 1, ignorando qualquer especificação
            if is_cvu_only:
                estagio = 1
                safe_print(f"[CT TOOL] Query de CVU detectada - FORÇANDO estágio 1 (ignorando qualquer especificação de estágio)")
            elif is_cvu_inflexibilidade_disponibilidade_query and estagio is None:
                estagio = 1
                safe_print(f"[CT TOOL] Query específica sobre CVU/inflexibilidade/disponibilidade sem estágio especificado - usando estágio 1 por padrão")
            elif estagio is None:
                # Query geral do bloco CT - não aplicar filtro de estágio (mostrar todos)
                safe_print(f"[CT TOOL] Query geral do bloco CT - mostrando todos os estágios")
            
            safe_print(f"[CT TOOL] Query recebida: {query}")
            safe_print(f"[CT TOOL] Codigo usina extraido: {codigo_usina}")
            safe_print(f"[CT TOOL] Codigo submercado extraido: {codigo_submercado}")
            safe_print(f"[CT TOOL] Estagio extraido: {estagio}")
            safe_print(f"[CT TOOL] Patamar extraido: {patamar}")  # NOVO
            safe_print(f"[CT TOOL] CVU apenas: {is_cvu_only}")  # NOVO
            
            # Obter dados das usinas térmicas
            ct_data = dadger.ct(
                codigo_usina=codigo_usina,
                codigo_submercado=codigo_submercado,
                estagio=estagio,
                df=True  # Retornar como DataFrame
            )
            
            if ct_data is None or (isinstance(ct_data, pd.DataFrame) and ct_data.empty):
                return {
                    "success": False,
                    "error": "Nenhuma usina termelétrica encontrada com os filtros especificados"
                }
            
            # Converter para formato padronizado
            if isinstance(ct_data, pd.DataFrame):
                data = ct_data.to_dict('records')
            elif isinstance(ct_data, list):
                data = [self._ct_to_dict(ct) for ct in ct_data]
            else:
                data = [self._ct_to_dict(ct_data)]
            
            # SEMPRE filtrar por codigo_usina se foi especificado (extraído da query ou passado)
            # IMPORTANTE: Garantir que apenas registros da usina especificada sejam retornados
            if codigo_usina is not None:
                total_antes = len(data)
                data = [d for d in data if d.get('codigo_usina') == codigo_usina]
                if total_antes != len(data):
                    safe_print(f"[CT TOOL] Filtro por código aplicado: {total_antes} -> {len(data)} registros (Usina {codigo_usina})")
            
            # Tentar extrair usina da query (código ou nome) - PRIORIDADE MÁXIMA
            # Somente quando NÃO houver código forçado pelo follow-up
            if codigo_usina is None and forced_plant_code is None:
                safe_print(f"[CT TOOL] Tentando extrair usina da query (código ou nome)...")
                codigo_usina_extraido = self._extract_usina_from_query(query, dadger, data)
                if codigo_usina_extraido is not None:
                    safe_print(f"[CT TOOL] [OK] Usina encontrada: codigo {codigo_usina_extraido}")
                    codigo_usina = codigo_usina_extraido
                    # Filtrar APENAS essa usina
                    total_antes = len(data)
                    data = [d for d in data if d.get('codigo_usina') == codigo_usina]
                    safe_print(f"[CT TOOL] Filtro aplicado: {total_antes} -> {len(data)} registros (Usina {codigo_usina})")
            
            # NOVO: Aplicar filtros por CVU e/ou patamar
            filtros_aplicados_list = []
            
            if is_cvu_only and patamar is not None:
                # Filtro: CVU apenas + patamar específico
                safe_print(f"[CT TOOL] Aplicando filtro: CVU apenas do patamar {patamar}")
                data = self._filter_by_cvu_and_patamar(data, patamar)
                filtros_aplicados_list.append(f"CVU apenas (patamar {patamar})")
            elif is_cvu_only:
                # Filtro: CVU apenas (todos os patamares)
                safe_print(f"[CT TOOL] Aplicando filtro: CVU apenas (todos os patamares)")
                data = self._filter_by_cvu_only(data)
                filtros_aplicados_list.append("CVU apenas")
            elif patamar is not None:
                # Filtro: Patamar específico (CVU + disponibilidade + inflexibilidade)
                safe_print(f"[CT TOOL] Aplicando filtro: Patamar {patamar} (todos os campos)")
                data = self._filter_by_patamar(data, patamar)
                filtros_aplicados_list.append(f"Patamar {patamar}")

            # GARANTIA ADICIONAL: Qualquer query que contenha termos de CVU ou
            # "Custo Variável Unitário" deve SEMPRE retornar apenas estágio 1.
            # Mesmo que, por algum motivo, o estagio tenha vindo None ou outro valor,
            # filtramos defensivamente aqui.
            if is_cvu_only or is_cvu_inflexibilidade_disponibilidade_query:
                safe_print("[CT TOOL] Garantindo que resultados de CVU tenham apenas estágio 1")
                before_len = len(data)
                data = [
                    d for d in data
                    if d.get("estagio") == 1
                    or d.get("estágio") == 1
                    or d.get("estagio") is None
                ]
                safe_print(f"[CT TOOL] Registros após filtro de estágio 1 para CVU: {before_len} -> {len(data)}")
                # Ajustar variáveis de controle para refletir a garantia de estágio 1
                estagio = 1
                if "Estágio 1 (forçado para CVU)" not in filtros_aplicados_list:
                    filtros_aplicados_list.append("Estágio 1 (forçado para CVU)")
            
            safe_print(f"[CT TOOL] Retornando {len(data)} registros de usinas termelétricas")
            safe_print(f"[CT TOOL] Filtros aplicados: usina={codigo_usina}, submercado={codigo_submercado}, estagio={estagio}, patamar={patamar}, cvu_apenas={is_cvu_only}")
            
            # Preparar filtros
            filtros_dict = {
                "codigo_usina": codigo_usina,
                "codigo_submercado": codigo_submercado,
                "estagio": estagio,
                "patamar": patamar,  # NOVO
                "cvu_apenas": is_cvu_only,  # NOVO
                "filtros_aplicados": filtros_aplicados_list,  # NOVO
            }
            
            # Adicionar selected_plant para follow-up mechanism
            selected_plant = None
            if codigo_usina is not None:
                # Tentar obter nome da usina
                nome_usina = None
                for record in data:
                    nome_temp = record.get('nome_usina', '').strip()
                    if nome_temp and nome_temp != 'nan' and nome_temp != '':
                        nome_usina = nome_temp
                        break
                if nome_usina:
                    filtros_dict["nome_usina"] = nome_usina
                    selected_plant = {
                        "type": "thermal",
                        "codigo": codigo_usina,
                        "nome": nome_usina,
                        "nome_completo": nome_usina,
                        "context": "decomp",
                        "tool_name": self.get_name(),
                    }
            
            result = {
                "success": True,
                "data": data,
                "total_usinas": len(data),
                "filtros": filtros_dict,
                "tool": self.get_name()
            }
            
            if selected_plant:
                result["selected_plant"] = selected_plant
            
            return result
            
        except Exception as e:
            safe_print(f"[CT TOOL] ❌ Erro ao consultar Bloco CT: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": f"Erro ao consultar Bloco CT: {str(e)}",
                "tool": self.get_name()
            }
    
    def _extract_codigo_usina(self, query: str) -> Optional[int]:
        """Extrai código da usina da query."""
        patterns = [
            r'usina\s*(\d+)',
            r'ute\s*(\d+)',
            r'ct\s*(\d+)',
            r'código\s*(\d+)',
            r'codigo\s*(\d+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, query.lower())
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    continue
        return None
    
    def _extract_codigo_submercado(self, query: str) -> Optional[int]:
        """Extrai código do submercado da query."""
        patterns = [
            r'submercado\s*(\d+)',
            r'su\s*(\d+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, query.lower())
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    continue
        return None
    
    def _extract_estagio(self, query: str) -> Optional[int]:
        """Extrai estágio da query."""
        patterns = [
            r'estágio\s*(\d+)',
            r'estagio\s*(\d+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, query.lower())
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    continue
        return None
    
    def _extract_patamar(self, query: str) -> Optional[int]:
        """
        Extrai patamar da query.
        Aceita números (1, 2, 3) ou nomes (pesada, média, leve).
        
        Args:
            query: Query do usuário
            
        Returns:
            Número do patamar (1, 2, 3) ou None
        """
        query_lower = query.lower()
        
        # Mapeamento de nomes para números
        patamar_map = {
            'pesada': 1, 'pesado': 1, 'pesad': 1,
            'média': 2, 'media': 2, 'medio': 2, 'médio': 2,
            'leve': 3, 'leve': 3
        }
        
        # Buscar por nome do patamar
        for nome, numero in patamar_map.items():
            if nome in query_lower:
                safe_print(f"[CT TOOL] ✅ Patamar encontrado por nome: {nome} -> {numero}")
                return numero
        
        # Buscar por número explícito
        patterns = [
            r'patamar\s*(\d+)',
            r'patamar\s*#?\s*(\d+)',
            r'patamar\s*(?:de\s*carga\s*)?(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query_lower)
            if match:
                try:
                    patamar = int(match.group(1))
                    if 1 <= patamar <= 3:
                        safe_print(f"[CT TOOL] ✅ Patamar encontrado por número: {patamar}")
                        return patamar
                except ValueError:
                    continue
        
        return None
    
    def _is_cvu_query(self, query: str) -> bool:
        """
        Verifica se a query é especificamente sobre CVU.
        
        Args:
            query: Query do usuário
            
        Returns:
            True se a query é sobre CVU
        """
        query_lower = query.lower()
        cvu_keywords = [
            "cvu",
            "custo variável unitário",
            "custo variavel unitario",
            "custo variável unitario",
            "custo variavel unitário",
            "custo variável",
            "custo variavel",
        ]
        
        # Verificar se há palavras que indicam que NÃO é sobre CVU
        exclude_keywords = [
            "disponibilidade",
            "inflexibilidade",
            "patamar",
        ]
        
        # Se contém CVU e não contém palavras de exclusão, é query de CVU
        has_cvu = any(kw in query_lower for kw in cvu_keywords)
        has_exclude = any(kw in query_lower for kw in exclude_keywords if kw not in ["patamar"])
        
        # Se menciona CVU explicitamente, é query de CVU (mesmo que mencione patamar)
        if has_cvu:
            return True
        
        return False
    
    def _is_cvu_inflexibilidade_disponibilidade_query(self, query: str) -> bool:
        """
        Verifica se a query é ESPECIFICAMENTE sobre CVU, inflexibilidade ou disponibilidade.
        Essas queries sempre devem usar estágio 1 por padrão.
        
        Queries gerais do bloco CT (ex: "mostre todas as usinas termelétricas") não devem
        ser consideradas como queries específicas, permitindo mostrar todos os estágios.
        
        Args:
            query: Query do usuário
            
        Returns:
            True se a query é especificamente sobre CVU, inflexibilidade ou disponibilidade
        """
        query_lower = query.lower()
        
        # Palavras-chave que indicam query geral (não específica)
        general_keywords = [
            "todas as usinas",
            "todas usinas",
            "listar usinas",
            "mostrar usinas",
            "usinas termelétricas",
            "usinas termicas",
            "bloco ct",
            "registro ct",
            "ct decomp",
        ]
        
        # Se a query contém palavras-chave gerais, não é query específica
        if any(kw in query_lower for kw in general_keywords):
            # Verificar se também menciona CVU/inflexibilidade/disponibilidade especificamente
            # Se sim, ainda é query específica
            specific_mentions = [
                "cvu de",
                "cvu da",
                "cvu do",
                "inflexibilidade de",
                "inflexibilidade da",
                "inflexibilidade do",
                "disponibilidade de",
                "disponibilidade da",
                "disponibilidade do",
            ]
            if not any(kw in query_lower for kw in specific_mentions):
                return False
        
        # Palavras-chave para CVU
        cvu_keywords = [
            "cvu",
            "custo variável unitário",
            "custo variavel unitario",
            "custo variável unitario",
            "custo variavel unitário",
            "custo variável",
            "custo variavel",
        ]
        
        # Palavras-chave para inflexibilidade
        inflexibilidade_keywords = [
            "inflexibilidade",
            "inflexibilidade térmica",
            "inflexibilidade termica",
        ]
        
        # Palavras-chave para disponibilidade
        disponibilidade_keywords = [
            "disponibilidade",
            "disponibilidade térmica",
            "disponibilidade termica",
        ]
        
        # Verificar se a query menciona qualquer um desses campos
        has_cvu = any(kw in query_lower for kw in cvu_keywords)
        has_inflexibilidade = any(kw in query_lower for kw in inflexibilidade_keywords)
        has_disponibilidade = any(kw in query_lower for kw in disponibilidade_keywords)
        
        return has_cvu or has_inflexibilidade or has_disponibilidade
    
    def _filter_by_cvu_only(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filtra dados para mostrar apenas CVU, removendo disponibilidade e inflexibilidade.
        
        Args:
            data: Lista de registros de usinas
            
        Returns:
            Lista filtrada contendo apenas campos de CVU
        """
        filtered = []
        for record in data:
            filtered_record = {
                "codigo_usina": record.get("codigo_usina"),
                "codigo_submercado": record.get("codigo_submercado"),
                "nome_usina": record.get("nome_usina"),
                "estagio": record.get("estagio"),
            }
            
            # Adicionar apenas CVU por patamar
            for patamar in [1, 2, 3]:
                cvu_key = f"cvu_{patamar}"
                if cvu_key in record:
                    filtered_record[cvu_key] = record[cvu_key]
            
            filtered.append(filtered_record)
        
        return filtered
    
    def _filter_by_patamar(self, data: List[Dict[str, Any]], patamar: int) -> List[Dict[str, Any]]:
        """
        Filtra dados para mostrar apenas um patamar específico.
        
        Args:
            data: Lista de registros de usinas
            patamar: Número do patamar (1, 2, 3)
            
        Returns:
            Lista filtrada contendo apenas dados do patamar especificado
        """
        filtered = []
        for record in data:
            filtered_record = {
                "codigo_usina": record.get("codigo_usina"),
                "codigo_submercado": record.get("codigo_submercado"),
                "nome_usina": record.get("nome_usina"),
                "estagio": record.get("estagio"),
                "patamar": patamar,
            }
            
            # Adicionar apenas campos do patamar especificado
            cvu_key = f"cvu_{patamar}"
            disp_key = f"disponibilidade_{patamar}"
            infl_key = f"inflexibilidade_{patamar}"
            
            if cvu_key in record:
                filtered_record["cvu"] = record[cvu_key]
            if disp_key in record:
                filtered_record["disponibilidade"] = record[disp_key]
            if infl_key in record:
                filtered_record["inflexibilidade"] = record[infl_key]
            
            filtered.append(filtered_record)
        
        return filtered
    
    def _filter_by_cvu_and_patamar(self, data: List[Dict[str, Any]], patamar: int) -> List[Dict[str, Any]]:
        """
        Filtra dados para mostrar apenas CVU de um patamar específico.
        
        Args:
            data: Lista de registros de usinas
            patamar: Número do patamar (1, 2, 3)
            
        Returns:
            Lista filtrada contendo apenas CVU do patamar especificado
        """
        filtered = []
        for record in data:
            filtered_record = {
                "codigo_usina": record.get("codigo_usina"),
                "codigo_submercado": record.get("codigo_submercado"),
                "nome_usina": record.get("nome_usina"),
                "estagio": record.get("estagio"),
                "patamar": patamar,
            }
            
            # Adicionar apenas CVU do patamar especificado
            cvu_key = f"cvu_{patamar}"
            if cvu_key in record:
                filtered_record["cvu"] = record[cvu_key]
            
            filtered.append(filtered_record)
        
        return filtered
    
    def _extract_usina_from_query(
        self, 
        query: str, 
        dadger: Any, 
        data_usinas: list
    ) -> Optional[int]:
        """
        Extrai código da usina da query usando DecompThermalPlantMatcher.
        
        Args:
            query: Query do usuário
            dadger: Instância do Dadger
            data_usinas: Lista de dados das usinas já carregados
            
        Returns:
            Código da usina ou None
        """
        # Usar matcher DECOMP com CSV como fonte de verdade
        matcher = get_decomp_thermal_plant_matcher()
        
        # Converter data_usinas para formato que o matcher aceita
        # O matcher usa CSV como fonte de verdade, mas valida contra DataFrame
        codigo = matcher.extract_plant_from_query(
            query=query,
            available_plants=data_usinas,
            entity_type="usina",
            threshold=0.5
        )
        
        if codigo is not None:
            safe_print(f"[CT TOOL] ✅ Código {codigo} encontrado via DecompThermalPlantMatcher")
        else:
            safe_print(f"[CT TOOL] ⚠️ Nenhuma usina específica detectada na query")
        
        return codigo
    
    def _ct_to_dict(self, ct_obj) -> Dict[str, Any]:
        """Converte objeto CT para dict."""
        if isinstance(ct_obj, dict):
            return ct_obj
        if hasattr(ct_obj, '__dict__'):
            return ct_obj.__dict__
        # Extrair atributos conhecidos do registro CT
        return {
            "codigo_usina": getattr(ct_obj, 'codigo_usina', None),
            "codigo_submercado": getattr(ct_obj, 'codigo_submercado', None),
            "nome_usina": getattr(ct_obj, 'nome_usina', None),
            "estagio": getattr(ct_obj, 'estagio', None),
            "cvu_1": getattr(ct_obj, 'cvu_1', None),
            "cvu_2": getattr(ct_obj, 'cvu_2', None),
            "cvu_3": getattr(ct_obj, 'cvu_3', None),
            "disponibilidade_1": getattr(ct_obj, 'disponibilidade_1', None),
            "disponibilidade_2": getattr(ct_obj, 'disponibilidade_2', None),
            "disponibilidade_3": getattr(ct_obj, 'disponibilidade_3', None),
            "inflexibilidade_1": getattr(ct_obj, 'inflexibilidade_1', None),
            "inflexibilidade_2": getattr(ct_obj, 'inflexibilidade_2', None),
            "inflexibilidade_3": getattr(ct_obj, 'inflexibilidade_3', None),
        }
