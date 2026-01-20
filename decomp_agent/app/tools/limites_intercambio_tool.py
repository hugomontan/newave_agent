"""
Tool para consultar limites de intercâmbio entre subsistemas do DECOMP.
Acessa o arquivo dadger.rvx, registro IA.

Formato do registro IA:
IA   EST   S1   S2   DE->PARA(P1)  PARA->DE(P1)  DE->PARA(P2)  PARA->DE(P2)  DE->PARA(P3)  PARA->DE(P3)

VERSÃO SIMPLIFICADA: Apenas lê o registro IA do arquivo como DataFrame.
"""
from decomp_agent.app.tools.base import DECOMPTool
from decomp_agent.app.config import safe_print
from idecomp.decomp import Dadger
import os
import pandas as pd
import re
from typing import Dict, Any, Optional, List


class LimitesIntercambioDECOMPTool(DECOMPTool):
    """
    Tool SIMPLIFICADA para consultar limites de intercâmbio entre subsistemas do DECOMP.
    Versão básica que apenas lê o registro IA do arquivo como DataFrame.
    """
    
    def get_name(self) -> str:
        return "LimitesIntercambioDECOMPTool"
    
    def can_handle(self, query: str) -> bool:
        """Verifica se a query é sobre limites de intercâmbio."""
        query_lower = query.lower()
        
        keywords = [
            "limite de intercambio",
            "limite de intercâmbio",
            "limites de intercambio",
            "limites de intercâmbio",
            "intercambio entre",
            "intercâmbio entre",
            "limite de",
            "limite para",
            "limite entre",
            "registro ia",
        ]
        
        return any(kw in query_lower for kw in keywords)
    
    def get_description(self) -> str:
        return """
        Consulta limites de intercâmbio entre subsistemas do DECOMP.
        
        Exemplos de queries:
        - "Limite N para FC"
        - "Limite SE para NE"
        - "Limites de intercâmbio de S para SE"
        """
    
    def execute(self, query: str, **kwargs) -> Dict[str, Any]:
        """Executa a consulta de limites de intercâmbio - VERSÃO SIMPLIFICADA."""
        safe_print(f"[LIMITES IA] Query: {query}")
        safe_print(f"[LIMITES IA] Deck: {self.deck_path}")
        
        try:
            # 1. Encontrar arquivo dadger
            dadger_path = self._find_dadger_file()
            if not dadger_path:
                return self._error("Arquivo dadger.rv* não encontrado")
            
            safe_print(f"[LIMITES IA] Arquivo: {dadger_path}")
            
            # 2. Ler dadger
            try:
                from decomp_agent.app.utils.dadger_cache import get_cached_dadger
                dadger = get_cached_dadger(self.deck_path)
            except ImportError:
                dadger = Dadger.read(dadger_path)
            
            if dadger is None:
                return self._error("Erro ao ler arquivo dadger")
            
            # 3. LER TODOS OS REGISTROS IA COMO DATAFRAME (SIMPLIFICADO)
            safe_print("[LIMITES IA] Lendo TODOS os registros IA do arquivo...")
            ia_df = dadger.ia(df=True)
            
            if ia_df is None or ia_df.empty:
                return self._error("Nenhum registro IA encontrado no arquivo dadger")
            
            safe_print(f"[LIMITES IA] Total de registros IA encontrados: {len(ia_df)}")
            safe_print(f"[LIMITES IA] Colunas disponíveis: {list(ia_df.columns)}")
            
            # 4. Mostrar primeiras linhas para diagnóstico
            safe_print(f"[LIMITES IA] Primeiras 5 linhas:")
            safe_print(str(ia_df.head()))
            
            # 5. Tentar extrair par de submercados da query
            sub_de, sub_para, sentido_query = self._extrair_par_simples(query)
            
            if not sub_de or not sub_para:
                # Se não conseguir extrair, retornar TODOS os limites disponíveis
                safe_print("[LIMITES IA] Não foi possível extrair par da query. Retornando TODOS os limites disponíveis...")
                pares = self._listar_todos_pares(ia_df)
                
                # Ler todos os registros como objetos - APENAS ESTÁGIO 1
                todos_objetos = dadger.ia(estagio=1, df=False)
                if todos_objetos is None:
                    return {
                        "success": False,
                        "error": "Nenhum registro IA encontrado para estágio 1",
                        "pares_disponiveis": pares,
                        "tool": self.get_name()
                    }
                
                if not isinstance(todos_objetos, list):
                    todos_objetos = [todos_objetos]
                
                # Extrair durações dos patamares (necessário para cálculo de MW médio ponderado)
                duracoes = self._extrair_duracoes_patamares(dadger)
                
                # Processar todos os registros (todos já são estágio 1)
                resultados = []
                for registro in todos_objetos:
                    estagio = getattr(registro, 'estagio', None)
                    
                    # Garantir que é estágio 1 (filtro extra de segurança)
                    if estagio != 1:
                        safe_print(f"[LIMITES IA] Pulando registro estágio {estagio} (apenas estágio 1)")
                        continue
                    nome_de = getattr(registro, 'nome_submercado_de', None)
                    nome_para = getattr(registro, 'nome_submercado_para', None)
                    
                    safe_print(f"[LIMITES IA] ===== Processando: Estágio {estagio}, {nome_de} -> {nome_para} =====")
                    
                    # DEBUG CRÍTICO: Mostrar TODOS os atributos do objeto
                    todos_atributos = [a for a in dir(registro) if not a.startswith('_')]
                    safe_print(f"[LIMITES IA] Todos os atributos disponíveis: {todos_atributos}")
                    
                    # DEBUG: Tentar acessar atributo 'data'
                    data = getattr(registro, 'data', None)
                    if data is not None:
                        safe_print(f"[LIMITES IA] Atributo 'data' encontrado: tipo={type(data)}, valor={data}")
                        if isinstance(data, (list, tuple)):
                            safe_print(f"[LIMITES IA] Data é lista/tupla com {len(data)} elementos: {list(data)}")
                            for i, item in enumerate(data[:10]):
                                safe_print(f"[LIMITES IA]   data[{i}] = {item} (tipo: {type(item)})")
                        elif hasattr(data, '__dict__'):
                            safe_print(f"[LIMITES IA] Data é objeto com atributos: {data.__dict__}")
                    else:
                        safe_print(f"[LIMITES IA] Atributo 'data' não encontrado")
                        # Tentar outros atributos
                        for attr_name in ['limites', 'valores', 'dados']:
                            if hasattr(registro, attr_name):
                                data = getattr(registro, attr_name)
                                safe_print(f"[LIMITES IA] Atributo '{attr_name}' encontrado: {data}")
                                break
                    
                    # DEBUG: Tentar acessar atributos que podem conter os limites
                    safe_print(f"[LIMITES IA] Procurando atributos relacionados a limites...")
                    for attr in todos_atributos:
                        attr_lower = attr.lower()
                        if any(x in attr_lower for x in ['limite', 'patamar', 'de_para', 'para_de', 'valor']):
                            try:
                                val = getattr(registro, attr)
                                safe_print(f"[LIMITES IA]   {attr} = {val} (tipo: {type(val)})")
                            except Exception as e:
                                safe_print(f"[LIMITES IA]   {attr} = ERRO ao acessar: {e}")
                    
                    resultado = {
                        "estagio": estagio,
                        "sub_de": nome_de,
                        "sub_para": nome_para,
                    }
                    
                    # Extrair limites usando função auxiliar (sem filtro de sentido - retorna todos)
                    limites_extraidos = self._extrair_limites_do_registro(registro, sentido=None)
                    safe_print(f"[LIMITES IA] Limites extraídos: {limites_extraidos}")
                    resultado.update(limites_extraidos)
                    
                    # Calcular MW médio ponderado para cada sentido (se tiver durações e limites)
                    if duracoes and any(v is not None for v in duracoes.values()):
                        # Calcular MW médio para sentido DE->PARA
                        limite_de_para_p1 = limites_extraidos.get("limite_de_para_p1")
                        limite_de_para_p2 = limites_extraidos.get("limite_de_para_p2")
                        limite_de_para_p3 = limites_extraidos.get("limite_de_para_p3")
                        
                        if all(v is not None for v in [limite_de_para_p1, limite_de_para_p2, limite_de_para_p3]):
                            valores_de_para = {
                                "pesada": limite_de_para_p1,
                                "media": limite_de_para_p2,
                                "leve": limite_de_para_p3
                            }
                            mw_medio_de_para = self._calcular_mw_medio_ponderado(valores_de_para, duracoes)
                            if mw_medio_de_para is not None:
                                resultado["mw_medio_de_para"] = mw_medio_de_para
                        
                        # Calcular MW médio para sentido PARA->DE
                        limite_para_de_p1 = limites_extraidos.get("limite_para_de_p1")
                        limite_para_de_p2 = limites_extraidos.get("limite_para_de_p2")
                        limite_para_de_p3 = limites_extraidos.get("limite_para_de_p3")
                        
                        if all(v is not None for v in [limite_para_de_p1, limite_para_de_p2, limite_para_de_p3]):
                            valores_para_de = {
                                "pesada": limite_para_de_p1,
                                "media": limite_para_de_p2,
                                "leve": limite_para_de_p3
                            }
                            mw_medio_para_de = self._calcular_mw_medio_ponderado(valores_para_de, duracoes)
                            if mw_medio_para_de is not None:
                                resultado["mw_medio_para_de"] = mw_medio_para_de
                    
                    resultados.append(resultado)
                    safe_print(f"[LIMITES IA] ===== Fim processamento =====\n")
                
                return {
                    "success": True,
                    "data": resultados,
                    "par": None,  # Sem par específico
                    "duracoes": duracoes,  # Adicionar durações para formatter
                    "total_registros": len(resultados),
                    "pares_disponiveis": pares,
                    "tool": self.get_name()
                }
            
            safe_print(f"[LIMITES IA] Buscando: {sub_de} -> {sub_para} (sentido={sentido_query})")
            
            # Guardar os valores originais da query para a resposta
            sub_de_original = sub_de
            sub_para_original = sub_para
            
            # 6. Filtrar registros pelo par (tentar diferentes nomes de colunas)
            # Tentar primeiro o par normal, depois o inverso se não encontrar
            registros_filtrados = self._filtrar_por_par(ia_df, sub_de, sub_para)
            
            # Se não encontrou, SEMPRE tentar par invertido
            # Ex: "IV para SE" não existe, mas "SE -> IV" existe (retornar sentido PARA->DE)
            par_invertido = False
            if registros_filtrados is None or registros_filtrados.empty:
                safe_print(f"[LIMITES IA] Par {sub_de}->{sub_para} não encontrado, tentando par invertido...")
                registros_filtrados = self._filtrar_por_par(ia_df, sub_para, sub_de)
                if registros_filtrados is not None and not registros_filtrados.empty:
                    par_invertido = True
                    safe_print(f"[LIMITES IA] Par invertido encontrado: {sub_para}->{sub_de}")
                    # Trocar sub_de e sub_para para buscar o registro correto
                    sub_de, sub_para = sub_para, sub_de
            
            if registros_filtrados is None or registros_filtrados.empty:
                # Mostrar todos os valores únicos para diagnóstico
                valores_de = self._obter_valores_unicos(ia_df, "de")
                valores_para = self._obter_valores_unicos(ia_df, "para")
                pares = self._listar_todos_pares(ia_df)
                
                safe_print(f"[LIMITES IA] Par {sub_de} -> {sub_para} NÃO EXISTE no arquivo!")
                safe_print(f"[LIMITES IA] Pares disponíveis: {pares}")
                
                # Tentar sugerir pares semelhantes
                sugestoes = self._sugerir_pares_similares(sub_de, sub_para, pares)
                
                if sugestoes:
                    safe_print(f"[LIMITES IA] Sugestões encontradas: {sugestoes}")
                else:
                    safe_print(f"[LIMITES IA] Nenhuma sugestão encontrada")
                
                error_msg = f"Par de intercâmbio '{sub_de} -> {sub_para}' não existe no arquivo."
                if sugestoes:
                    error_msg += f" Talvez você quis dizer: {', '.join(sugestoes[:3])}?"
                error_msg += f" Pares disponíveis: {', '.join(pares)}"
                
                return {
                    "success": False,
                    "error": error_msg,
                    "valores_de_disponiveis": valores_de,
                    "valores_para_disponiveis": valores_para,
                    "pares_disponiveis": pares,
                    "sugestoes": sugestoes,
                    "tool": self.get_name()
                }
            
            safe_print(f"[LIMITES IA] Registros encontrados: {len(registros_filtrados)}")
            
            # 7. LER COMO OBJETOS para acessar os limites dos patamares - APENAS ESTÁGIO 1
            # O DataFrame não contém os valores dos limites, apenas metadados
            # Usar sub_de e sub_para que podem ter sido invertidos acima
            safe_print(f"[LIMITES IA] Lendo registros como objetos para acessar limites (estágio 1, {sub_de}->{sub_para})...")
            ia_objetos = dadger.ia(
                estagio=1,  # FILTRO: apenas estágio 1
                nome_submercado_de=sub_de,
                nome_submercado_para=sub_para,
                df=False
            )
            
            if ia_objetos is None:
                return self._error(f"Nenhum limite encontrado para {sub_de} -> {sub_para} no estágio 1")
            
            # Converter para lista se necessário
            if not isinstance(ia_objetos, list):
                ia_objetos = [ia_objetos]
            
            safe_print(f"[LIMITES IA] {len(ia_objetos)} objetos encontrados (todos estágio 1)")
            
            # 8. Extrair durações dos patamares (necessário para cálculo de MW médio ponderado)
            duracoes = self._extrair_duracoes_patamares(dadger)
            
            # 9. Processar objetos e extrair limites
            resultados = []
            for registro in ia_objetos:
                # Acessar estágio
                estagio = getattr(registro, 'estagio', None)
                
                # Garantir que é estágio 1 (filtro extra de segurança)
                if estagio != 1:
                    safe_print(f"[LIMITES IA] Pulando registro estágio {estagio} (apenas estágio 1)")
                    continue
                nome_de_obj = getattr(registro, 'nome_submercado_de', None)
                nome_para_obj = getattr(registro, 'nome_submercado_para', None)
                
                safe_print(f"[LIMITES IA] Processando estágio {estagio}, {nome_de_obj} -> {nome_para_obj}")
                
                # Debug: mostrar TODOS os atributos do objeto
                todos_atributos = [a for a in dir(registro) if not a.startswith('_')]
                safe_print(f"[LIMITES IA] Todos os atributos disponíveis: {todos_atributos}")
                
                # Tentar acessar atributo 'data' que contém os limites
                data = getattr(registro, 'data', None)
                
                # Debug: mostrar tipo e conteúdo de data
                if data is not None:
                    safe_print(f"[LIMITES IA] Atributo 'data' encontrado: tipo={type(data)}, valor={data}")
                    if isinstance(data, (list, tuple)):
                        safe_print(f"[LIMITES IA] Data é lista/tupla com {len(data)} elementos")
                        for i, item in enumerate(data[:10]):  # Mostrar primeiros 10
                            safe_print(f"[LIMITES IA]   data[{i}] = {item} (tipo: {type(item)})")
                    elif hasattr(data, '__dict__'):
                        safe_print(f"[LIMITES IA] Data é objeto com atributos: {data.__dict__}")
                
                # Tentar acessar atributos individuais diretamente
                # Formato esperado: 6 valores [DE->PARA_P1, PARA->DE_P1, DE->PARA_P2, PARA->DE_P2, DE->PARA_P3, PARA->DE_P3]
                # Tentar diferentes padrões de nomes de atributos
                atributos_limites = {}
                for attr in todos_atributos:
                    attr_lower = attr.lower()
                    if any(x in attr_lower for x in ['limite', 'patamar', 'de_para', 'para_de']):
                        try:
                            valor = getattr(registro, attr)
                            atributos_limites[attr] = valor
                            safe_print(f"[LIMITES IA] Atributo '{attr}' = {valor} (tipo: {type(valor)})")
                        except:
                            pass
            
                if data is None and not atributos_limites:
                    # Tentar outros atributos
                    for attr_name in ['limites', 'valores', 'dados']:
                        if hasattr(registro, attr_name):
                            data = getattr(registro, attr_name)
                            safe_print(f"[LIMITES IA] Usando atributo '{attr_name}': {data}")
                            break
                
                # Determinar sentido efetivo baseado no par invertido
                # Exemplo: Usuário pede "IV para SE", encontramos registro "SE -> IV"
                # - Usuário quer IV→SE = sentido PARA->DE do registro SE->IV
                if par_invertido:
                    if sentido_query == "de_para":
                        # Usuário pediu X→Y, encontramos registro Y→X
                        # Retornar sentido PARA→DE do registro (que é X→Y)
                        sentido_efetivo = "para_de"
                        safe_print(f"[LIMITES IA] Par invertido + de_para → retornando PARA->DE do registro")
                    elif sentido_query == "para_de":
                        # Usuário pediu X←Y, encontramos registro Y→X
                        # Retornar sentido DE→PARA do registro (que é Y→X = X←Y)
                        sentido_efetivo = "de_para"
                        safe_print(f"[LIMITES IA] Par invertido + para_de → retornando DE->PARA do registro")
                    else:
                        # Ambos os sentidos
                        sentido_efetivo = None
                        safe_print(f"[LIMITES IA] Par invertido + ambos → retornando todos os sentidos")
                else:
                    # Par normal - usar sentido da query diretamente
                    sentido_efetivo = sentido_query
                    safe_print(f"[LIMITES IA] Par normal → sentido_efetivo = {sentido_efetivo}")
                
                # Resultado usa os submercados ORIGINAIS da query do usuário
                resultado = {
                    "estagio": estagio,
                    "sub_de": sub_de_original,
                    "sub_para": sub_para_original,
                }
                
                # Extrair limites usando função auxiliar (aplicar filtro de sentido)
                limites_extraidos = self._extrair_limites_do_registro(registro, sentido=sentido_efetivo)
                
                # Se par foi invertido, renomear campos para refletir perspectiva do usuário
                # Ex: Usuário pediu "IV para SE", encontramos "SE->IV"
                # limite_para_de do registro = IV→SE = limite_de_para para o usuário
                if par_invertido and limites_extraidos:
                    limites_renomeados = {}
                    for key, value in limites_extraidos.items():
                        if "de_para" in key:
                            # de_para do registro = para_de para o usuário
                            novo_key = key.replace("de_para", "para_de")
                            limites_renomeados[novo_key] = value
                        elif "para_de" in key:
                            # para_de do registro = de_para para o usuário
                            novo_key = key.replace("para_de", "de_para")
                            limites_renomeados[novo_key] = value
                        else:
                            limites_renomeados[key] = value
                    safe_print(f"[LIMITES IA] Limites renomeados (par invertido): {limites_renomeados}")
                    limites_extraidos = limites_renomeados
                
                resultado.update(limites_extraidos)
                
                # Calcular MW médio ponderado para cada sentido (se tiver durações e limites)
                if duracoes and any(v is not None for v in duracoes.values()):
                    # Calcular MW médio para sentido DE->PARA
                    limite_de_para_p1 = limites_extraidos.get("limite_de_para_p1")
                    limite_de_para_p2 = limites_extraidos.get("limite_de_para_p2")
                    limite_de_para_p3 = limites_extraidos.get("limite_de_para_p3")
                    
                    if all(v is not None for v in [limite_de_para_p1, limite_de_para_p2, limite_de_para_p3]):
                        valores_de_para = {
                            "pesada": limite_de_para_p1,
                            "media": limite_de_para_p2,
                            "leve": limite_de_para_p3
                        }
                        mw_medio_de_para = self._calcular_mw_medio_ponderado(valores_de_para, duracoes)
                        if mw_medio_de_para is not None:
                            resultado["mw_medio_de_para"] = mw_medio_de_para
                            safe_print(f"[LIMITES IA] MW médio DE->PARA: {mw_medio_de_para} MW")
                    
                    # Calcular MW médio para sentido PARA->DE
                    limite_para_de_p1 = limites_extraidos.get("limite_para_de_p1")
                    limite_para_de_p2 = limites_extraidos.get("limite_para_de_p2")
                    limite_para_de_p3 = limites_extraidos.get("limite_para_de_p3")
                    
                    if all(v is not None for v in [limite_para_de_p1, limite_para_de_p2, limite_para_de_p3]):
                        valores_para_de = {
                            "pesada": limite_para_de_p1,
                            "media": limite_para_de_p2,
                            "leve": limite_para_de_p3
                        }
                        mw_medio_para_de = self._calcular_mw_medio_ponderado(valores_para_de, duracoes)
                        if mw_medio_para_de is not None:
                            resultado["mw_medio_para_de"] = mw_medio_para_de
                            safe_print(f"[LIMITES IA] MW médio PARA->DE: {mw_medio_para_de} MW")
                
                # Debug: mostrar limites extraídos
                if limites_extraidos:
                    safe_print(f"[LIMITES IA] Limites extraídos (sentido={sentido_efetivo}): {limites_extraidos}")
                else:
                    safe_print(f"[LIMITES IA] AVISO: Nenhum limite extraído do registro!")
                
                resultados.append(resultado)
            
            return {
                "success": True,
                "data": resultados,
                "par": {"de": sub_de_original, "para": sub_para_original},  # Usar valores originais da query
                "sentido_query": sentido_query,  # "de_para", "para_de", ou None (ambos)
                "duracoes": duracoes,  # Adicionar durações para formatter
                "total_registros": len(registros_filtrados),
                "tool": self.get_name()
            }
            
        except Exception as e:
            safe_print(f"[LIMITES IA] Erro: {e}")
            import traceback
            traceback.print_exc()
            return self._error(str(e))
    
    def _find_dadger_file(self) -> Optional[str]:
        """Encontra o arquivo dadger.rvX no deck."""
        for ext in range(10):
            candidate = os.path.join(self.deck_path, f"dadger.rv{ext}")
            if os.path.exists(candidate):
                return candidate
        # Tentar .rvx
        candidate = os.path.join(self.deck_path, "dadger.rvx")
        if os.path.exists(candidate):
            return candidate
        return None
    
    def _extrair_par_simples(self, query: str) -> tuple:
        """
        Extrai par de submercados da query de forma simples.
        Retorna: (sub_de, sub_para, sentido)
        - sentido: "de_para" = apenas DE→PARA (padrão quando especifica direção)
        - sentido: None = ambos os sentidos (quando não especifica direção clara)
        """
        query_upper = query.upper()
        
        # Normalização básica de nomes de submercado para siglas
        # Importante: manter os demais mapeamentos como estão por enquanto
        def _normalize_submercado(nome: str) -> str:
            if not nome:
                return nome
            nome = nome.upper().strip()
            # Variações pedidas explicitamente:
            # NE = NORDESTE, SE = SUDESTE, N = NORTE, S = SUL
            normalizacao = {
                "NORDESTE": "NE",
                "NE": "NE",
                "SUDESTE": "SE",
                "SE": "SE",
                "NORTE": "N",
                "N": "N",
                "SUL": "S",
                "S": "S",
            }
            return normalizacao.get(nome, nome)
        
        # Padrões que indicam DIREÇÃO CLARA (X para Y = apenas X→Y)
        # Quando o usuário diz "de N para FC", ele quer apenas N→FC
        patterns_direcional = [
            r'(?:DE\s+)?(\w+)\s+(?:PARA|->|→)\s+(\w+)',  # "de N para FC" ou "N para FC" ou "N -> FC"
            r'LIMITE\s+(?:DE\s+)?(\w+)\s+(?:PARA|->|→)\s+(\w+)',  # "limite de N para FC"
        ]
        
        # Padrões que indicam AMBOS OS SENTIDOS
        patterns_bidirecional = [
            r'ENTRE\s+(\w+)\s+E\s+(\w+)',  # "entre N e FC" = ambos os sentidos
        ]
        
        # Primeiro tentar padrões bidirecionais
        for pattern in patterns_bidirecional:
            match = re.search(pattern, query_upper)
            if match:
                sub_de = match.group(1).strip()
                sub_para = match.group(2).strip()
                # Limpar palavras de ruído
                sub_de = re.sub(r'\b(DE|LIMITE|LIMITES)\b', '', sub_de).strip()
                sub_para = re.sub(r'\b(PARA|LIMITE|LIMITES)\b', '', sub_para).strip()
                # Normalizar nomes para siglas (ex: SUDESTE -> SE)
                sub_de = _normalize_submercado(sub_de)
                sub_para = _normalize_submercado(sub_para)
                if sub_de and sub_para:
                    safe_print(f"[LIMITES IA] Padrão bidirecional detectado: {sub_de} ↔ {sub_para}")
                    return (sub_de, sub_para, None)  # None = ambos os sentidos
        
        # Depois tentar padrões direcionais (mais comum)
        for pattern in patterns_direcional:
            match = re.search(pattern, query_upper)
            if match:
                sub_de = match.group(1).strip()
                sub_para = match.group(2).strip()
                # Remover palavras comuns
                sub_de = re.sub(r'\b(DE|LIMITE|LIMITES|INTERCAMBIO|INTERCÂMBIO)\b', '', sub_de).strip()
                sub_para = re.sub(r'\b(PARA|LIMITE|LIMITES)\b', '', sub_para).strip()
                # Normalizar nomes para siglas (ex: SUDESTE -> SE)
                sub_de = _normalize_submercado(sub_de)
                sub_para = _normalize_submercado(sub_para)
                
                if sub_de and sub_para:
                    # Por padrão, "X para Y" significa apenas X→Y (sentido único)
                    sentido = "de_para"
                    safe_print(f"[LIMITES IA] Padrão direcional detectado: {sub_de} → {sub_para} (sentido: {sentido})")
                    return (sub_de, sub_para, sentido)
        
        return (None, None, None)
    
    def _filtrar_por_par(self, df: pd.DataFrame, sub_de: str, sub_para: str) -> Optional[pd.DataFrame]:
        """Filtra DataFrame pelo par de submercados, tentando diferentes nomes de colunas."""
        # Possíveis nomes de colunas
        col_de_options = [
            "nome_submercado_de", "submercado_de", "s1", "sub_de", 
            "de", "origem", "submercado_origem"
        ]
        col_para_options = [
            "nome_submercado_para", "submercado_para", "s2", "sub_para",
            "para", "destino", "submercado_destino"
        ]
        
        col_de = None
        col_para = None
        
        # Encontrar coluna DE
        for col_option in col_de_options:
            if col_option in df.columns:
                col_de = col_option
                break
        
        # Encontrar coluna PARA
        for col_option in col_para_options:
            if col_option in df.columns:
                col_para = col_option
                break
        
        if not col_de or not col_para:
            safe_print(f"[LIMITES IA] Colunas não encontradas. DE: {col_de}, PARA: {col_para}")
            return None
        
        safe_print(f"[LIMITES IA] Usando colunas: {col_de} e {col_para}")
        
        # Criar mapeamento de nomes comuns para códigos
        # Ex: "S" pode ser "SUL" ou "S", "SUDESTE" pode ser "SE" ou "SUDESTE"
        # Inclui mapeamentos bidirecionais
        mapeamento_submercados = {
            "S": ["S", "SUL"],
            "SUL": ["S", "SUL"],
            "SE": ["SE", "SUDESTE"],
            "SUDESTE": ["SE", "SUDESTE"],
            "N": ["N", "NORTE"],
            "NORTE": ["N", "NORTE"],
            "NE": ["NE", "NORDESTE"],
            "NORDESTE": ["NE", "NORDESTE"],
            "FC": ["FC", "FICTICIO"],
            "FICTICIO": ["FC", "FICTICIO"],
            "IV": ["IV", "ITAIPU"],
            "ITAIPU": ["IV", "ITAIPU"],
        }
        
        # Obter variações possíveis dos submercados
        sub_de_upper = sub_de.upper().strip()
        sub_para_upper = sub_para.upper().strip()
        
        variacoes_de = mapeamento_submercados.get(sub_de_upper, [sub_de_upper])
        variacoes_para = mapeamento_submercados.get(sub_para_upper, [sub_para_upper])
        
        safe_print(f"[LIMITES IA] Variações de '{sub_de}': {variacoes_de}")
        safe_print(f"[LIMITES IA] Variações de '{sub_para}': {variacoes_para}")
        
        # Filtrar usando match exato (case-insensitive)
        # Tentar cada combinação de variações
        df_filtered = None
        for var_de in variacoes_de:
            for var_para in variacoes_para:
                df_temp = df[
                    (df[col_de].astype(str).str.upper().str.strip() == var_de.upper()) &
                    (df[col_para].astype(str).str.upper().str.strip() == var_para.upper())
                ]
                if df_temp is not None and not df_temp.empty:
                    df_filtered = df_temp
                    safe_print(f"[LIMITES IA] Match encontrado com: {var_de} -> {var_para}")
                    break
            if df_filtered is not None and not df_filtered.empty:
                break
        
        if df_filtered is None or df_filtered.empty:
            safe_print(f"[LIMITES IA] Nenhum match encontrado para {sub_de} -> {sub_para}")
        
        return df_filtered
    
    def _obter_valores_unicos(self, df: pd.DataFrame, tipo: str) -> List[str]:
        """Obtém valores únicos das colunas de submercado."""
        if tipo == "de":
            col_options = ["nome_submercado_de", "submercado_de", "s1", "sub_de", "de"]
        else:
            col_options = ["nome_submercado_para", "submercado_para", "s2", "sub_para", "para"]
        
        for col_option in col_options:
            if col_option in df.columns:
                valores = df[col_option].dropna().unique().tolist()
                return [str(v) for v in valores]
        
        return []
    
    def _listar_todos_pares(self, df: pd.DataFrame) -> List[str]:
        """Lista todos os pares de submercados disponíveis."""
        col_de_options = ["nome_submercado_de", "submercado_de", "s1", "sub_de", "de"]
        col_para_options = ["nome_submercado_para", "submercado_para", "s2", "sub_para", "para"]
        
        col_de = None
        col_para = None
        
        for col_option in col_de_options:
            if col_option in df.columns:
                col_de = col_option
                break
        
        for col_option in col_para_options:
            if col_option in df.columns:
                col_para = col_option
                break
        
        if not col_de or not col_para:
            return []
        
        pares = df[[col_de, col_para]].drop_duplicates()
        return [f"{row[col_de]} -> {row[col_para]}" for _, row in pares.iterrows()]
    
    def _sugerir_pares_similares(self, sub_de: str, sub_para: str, pares: List[str]) -> List[str]:
        """
        Sugere pares similares quando o par solicitado não existe.
        Prioriza pares que são similares em ambos os sentidos, depois parcialmente similares.
        """
        sugestoes_ambos = []  # Pares similares em ambos (origem E destino)
        sugestoes_parcial = []  # Pares similares em apenas um (origem OU destino)
        
        sub_de_upper = sub_de.upper().strip()
        sub_para_upper = sub_para.upper().strip()
        
        for par in pares:
            # Extrair DE e PARA do par (formato: "DE -> PARA")
            parts = par.split(" -> ")
            if len(parts) != 2:
                continue
                
            par_de = parts[0].strip().upper()
            par_para = parts[1].strip().upper()
            
            # Verificar similaridade na origem
            similar_de = False
            if sub_de_upper:
                # Match exato ou substring
                if sub_de_upper == par_de or sub_de_upper in par_de or par_de in sub_de_upper:
                    similar_de = True
                # Começa com a mesma letra (para casos como "S" -> "SE" ou "SUL")
                elif len(sub_de_upper) >= 1 and par_de.startswith(sub_de_upper[0]):
                    similar_de = True
            
            # Verificar similaridade no destino
            similar_para = False
            if sub_para_upper:
                # Match exato ou substring
                if sub_para_upper == par_para or sub_para_upper in par_para or par_para in sub_para_upper:
                    similar_para = True
                # Começa com a mesma letra
                elif len(sub_para_upper) >= 1 and par_para.startswith(sub_para_upper[0]):
                    similar_para = True
            
            # Prioridade 1: Ambos similares
            if similar_de and similar_para:
                sugestoes_ambos.append(par)
            # Prioridade 2: Apenas origem ou apenas destino similar
            elif similar_de or similar_para:
                sugestoes_parcial.append(par)
        
        # Combinar: primeiro ambos, depois parciais (até 3 no total)
        todas_sugestoes = sugestoes_ambos + sugestoes_parcial
        return todas_sugestoes[:3]
    
    def _safe_float(self, value: Any) -> Optional[float]:
        """Converte valor para float de forma segura."""
        if value is None:
            return None
        try:
            # Tentar converter para float
            if isinstance(value, (int, float)):
                return float(value)
            if isinstance(value, str):
                # Remover espaços e tentar converter
                value = value.strip()
                if value == '' or value.lower() in ['none', 'null', 'nan']:
                    return None
                return float(value)
            return float(value)
        except (ValueError, TypeError):
            # Se não conseguir converter, retornar None
            return None
    
    def _extrair_duracoes_patamares(self, dadger: Any) -> Dict[str, Optional[float]]:
        """
        Extrai durações dos patamares do bloco DP (estágio 1).
        
        Args:
            dadger: Objeto Dadger do idecomp
            
        Returns:
            Dict com durações por patamar: {"pesada": X, "media": Y, "leve": Z}
        """
        duracoes = {"pesada": None, "media": None, "leve": None}
        
        try:
            # Ler DP do estágio 1 (qualquer submercado, as durações são as mesmas)
            dp_data = dadger.dp(estagio=1, df=True)
            
            if dp_data is None or (isinstance(dp_data, pd.DataFrame) and dp_data.empty):
                safe_print(f"[LIMITES IA] Aviso: Não foi possível ler DP para extrair durações")
                return duracoes
            
            # Pegar primeiro registro (durações são as mesmas para todos)
            primeiro_registro = dp_data.iloc[0].to_dict()
            
            # Mapeamento: 1=PESADA, 2=MEDIA, 3=LEVE
            patamar_map = {
                "pesada": 1,
                "media": 2,
                "leve": 3
            }
            
            for patamar_nome, patamar_num in patamar_map.items():
                colunas_possiveis = [
                    f"duracao_patamar_{patamar_num}",
                    f"duracao_{patamar_num}",
                    f"horas_{patamar_num}",
                    f"horas_patamar_{patamar_num}",
                    f"duracao_pat{patamar_num}",
                    f"horas_pat{patamar_num}",
                ]
                
                for col in colunas_possiveis:
                    if col in primeiro_registro:
                        valor = primeiro_registro[col]
                        if valor is not None:
                            try:
                                duracoes[patamar_nome] = float(valor)
                                break
                            except (ValueError, TypeError):
                                continue
            
            safe_print(f"[LIMITES IA] Durações extraídas: {duracoes}")
            return duracoes
            
        except Exception as e:
            safe_print(f"[LIMITES IA] Erro ao extrair durações: {e}")
            return duracoes
    
    def _calcular_mw_medio_ponderado(
        self,
        valores: Dict[str, Optional[float]],
        duracoes: Dict[str, Optional[float]]
    ) -> Optional[float]:
        """
        Calcula MW médio ponderado usando a fórmula de patamares.
        
        Fórmula: MW_medio = (Val_P1 × Dur_P1 + Val_P2 × Dur_P2 + Val_P3 × Dur_P3) / (Dur_P1 + Dur_P2 + Dur_P3)
        
        Args:
            valores: Dict com valores por patamar {"pesada": X, "media": Y, "leve": Z}
            duracoes: Dict com durações por patamar em horas {"pesada": X, "media": Y, "leve": Z}
            
        Returns:
            MW médio ponderado ou None se houver erro
        """
        # Validar dados
        if any(v is None for v in valores.values()) or any(v is None for v in duracoes.values()):
            return None
        
        # Extrair valores (0.0 é válido!)
        val_pesada = valores.get("pesada", 0) or 0
        val_media = valores.get("media", 0) or 0
        val_leve = valores.get("leve", 0) or 0
        
        dur_pesada = duracoes.get("pesada", 0) or 0
        dur_media = duracoes.get("media", 0) or 0
        dur_leve = duracoes.get("leve", 0) or 0
        
        # Calcular numerador: (Val_Leve × Dur_Leve + Val_Médio × Dur_Médio + Val_Pesada × Dur_Pesada)
        numerador = (val_leve * dur_leve) + (val_media * dur_media) + (val_pesada * dur_pesada)
        
        # Calcular denominador: (Dur_Leve + Dur_Médio + Dur_Pesada)
        denominador = dur_leve + dur_media + dur_pesada
        
        if denominador == 0:
            return None
        
        # Calcular MW médio
        mw_medio = numerador / denominador
        
        return round(mw_medio, 2)
    
    def _extrair_limites_do_registro(self, registro, sentido: Optional[str] = None) -> Dict[str, Optional[float]]:
        """
        Extrai limites de um registro IA.
        
        Args:
            registro: Objeto IA do idecomp
            sentido: "de_para" para retornar apenas DE->PARA, "para_de" para apenas PARA->DE, None para ambos
        
        Returns:
            Dict com chaves: limite_de_para_p1, limite_para_de_p1, etc.
        """
        limites = {}
        
        safe_print(f"[LIMITES IA] _extrair_limites_do_registro: Iniciando extração...")
        
        # Tentar acessar atributo 'data'
        data = getattr(registro, 'data', None)
        safe_print(f"[LIMITES IA] _extrair_limites: data={data}, tipo={type(data)}")
        
        # Método 1: Se data é uma lista/tupla
        # Estrutura esperada: [estagio, sub_de, sub_para, ?, DE->PARA_P1, PARA->DE_P1, DE->PARA_P2, PARA->DE_P2, DE->PARA_P3, PARA->DE_P3, ...]
        # Índices dos limites: 4, 5, 6, 7, 8, 9
        if isinstance(data, (list, tuple)) and len(data) >= 10:
            safe_print(f"[LIMITES IA] _extrair_limites: Extraindo de lista/tupla com {len(data)} elementos")
            safe_print(f"[LIMITES IA] _extrair_limites: Estrutura detectada - data[4:10] contém os limites")
            
            # Extrair limites dos índices corretos: 4, 5, 6, 7, 8, 9
            limite_de_para_p1 = self._safe_float(data[4]) if len(data) > 4 else None
            limite_para_de_p1 = self._safe_float(data[5]) if len(data) > 5 else None
            limite_de_para_p2 = self._safe_float(data[6]) if len(data) > 6 else None
            limite_para_de_p2 = self._safe_float(data[7]) if len(data) > 7 else None
            limite_de_para_p3 = self._safe_float(data[8]) if len(data) > 8 else None
            limite_para_de_p3 = self._safe_float(data[9]) if len(data) > 9 else None
            
            safe_print(f"[LIMITES IA] _extrair_limites:   data[4] (DE->PARA_P1) = {data[4]} -> {limite_de_para_p1}")
            safe_print(f"[LIMITES IA] _extrair_limites:   data[5] (PARA->DE_P1) = {data[5]} -> {limite_para_de_p1}")
            safe_print(f"[LIMITES IA] _extrair_limites:   data[6] (DE->PARA_P2) = {data[6]} -> {limite_de_para_p2}")
            safe_print(f"[LIMITES IA] _extrair_limites:   data[7] (PARA->DE_P2) = {data[7]} -> {limite_para_de_p2}")
            safe_print(f"[LIMITES IA] _extrair_limites:   data[8] (DE->PARA_P3) = {data[8]} -> {limite_de_para_p3}")
            safe_print(f"[LIMITES IA] _extrair_limites:   data[9] (PARA->DE_P3) = {data[9]} -> {limite_para_de_p3}")
            
            # Adicionar apenas os limites que foram extraídos com sucesso (aplicar filtro de sentido)
            if sentido is None or sentido == "de_para":
                if limite_de_para_p1 is not None:
                    limites["limite_de_para_p1"] = limite_de_para_p1
                if limite_de_para_p2 is not None:
                    limites["limite_de_para_p2"] = limite_de_para_p2
                if limite_de_para_p3 is not None:
                    limites["limite_de_para_p3"] = limite_de_para_p3
            
            if sentido is None or sentido == "para_de":
                if limite_para_de_p1 is not None:
                    limites["limite_para_de_p1"] = limite_para_de_p1
                if limite_para_de_p2 is not None:
                    limites["limite_para_de_p2"] = limite_para_de_p2
                if limite_para_de_p3 is not None:
                    limites["limite_para_de_p3"] = limite_para_de_p3
            
            if limites:
                sentido_info = f" (filtro: {sentido})" if sentido else " (ambos os sentidos)"
                safe_print(f"[LIMITES IA] _extrair_limites: ✅ Limites extraídos com sucesso{sentido_info}: {limites}")
                return limites
            else:
                safe_print(f"[LIMITES IA] _extrair_limites: ⚠️ Nenhum limite numérico encontrado nos índices 4-9")
        
        # Método 2: Tentar atributos individuais
        padroes_de_para = [
            ("limite_de_para_patamar_1", "limite_de_para_patamar_2", "limite_de_para_patamar_3"),
            ("de_para_patamar_1", "de_para_patamar_2", "de_para_patamar_3"),
            ("limite_de_para_p1", "limite_de_para_p2", "limite_de_para_p3"),
            ("de_para_p1", "de_para_p2", "de_para_p3"),
        ]
        
        padroes_para_de = [
            ("limite_para_de_patamar_1", "limite_para_de_patamar_2", "limite_para_de_patamar_3"),
            ("para_de_patamar_1", "para_de_patamar_2", "para_de_patamar_3"),
            ("limite_para_de_p1", "limite_para_de_p2", "limite_para_de_p3"),
            ("para_de_p1", "para_de_p2", "para_de_p3"),
        ]
        
        # Tentar DE->PARA
        for padrao_set in padroes_de_para:
            valores = []
            for attr_name in padrao_set:
                if hasattr(registro, attr_name):
                    val = getattr(registro, attr_name)
                    float_val = self._safe_float(val)
                    valores.append(float_val)
                    safe_print(f"[LIMITES IA] _extrair_limites:   {attr_name} = {val} -> {float_val}")
                else:
                    safe_print(f"[LIMITES IA] _extrair_limites:   {attr_name} não existe")
                    break
            
            if len(valores) == 3 and all(v is not None for v in valores):
                limites["limite_de_para_p1"] = valores[0]
                limites["limite_de_para_p2"] = valores[1]
                limites["limite_de_para_p3"] = valores[2]
                safe_print(f"[LIMITES IA] _extrair_limites: ✅ Limites DE->PARA extraídos: {valores}")
                break
        
        # Tentar PARA->DE
        for padrao_set in padroes_para_de:
            valores = []
            for attr_name in padrao_set:
                if hasattr(registro, attr_name):
                    val = getattr(registro, attr_name)
                    float_val = self._safe_float(val)
                    valores.append(float_val)
                    safe_print(f"[LIMITES IA] _extrair_limites:   {attr_name} = {val} -> {float_val}")
                else:
                    safe_print(f"[LIMITES IA] _extrair_limites:   {attr_name} não existe")
                    break
            
            if len(valores) == 3 and all(v is not None for v in valores):
                limites["limite_para_de_p1"] = valores[0]
                limites["limite_para_de_p2"] = valores[1]
                limites["limite_para_de_p3"] = valores[2]
                safe_print(f"[LIMITES IA] _extrair_limites: ✅ Limites PARA->DE extraídos: {valores}")
                break
        
        if not limites:
            safe_print(f"[LIMITES IA] _extrair_limites: ❌ NENHUM limite extraído!")
        
        return limites
    
    def _get_value(self, row: pd.Series, *keys) -> Any:
        """Obtém valor de uma linha tentando diferentes chaves."""
        for key in keys:
            if key in row.index:
                val = row[key]
                if pd.notna(val):
                    return val
        return None
    
    def _get_limite_patamar(self, row: pd.Series, patamar: int, sentido: str) -> Optional[float]:
        """Obtém limite de um patamar específico."""
        # Tentar diferentes nomes de colunas
        if sentido == "de_para":
            # Patamares 1,2,3 -> índices 0,2,4 (ou colunas 5,7,9)
            idx_map = {1: 0, 2: 2, 3: 4}
            patterns = [
                f"limite_de_para_patamar_{patamar}",
                f"de_para_p{patamar}",
                f"limite_p{patamar}_de_para",
                f"limite_{idx_map[patamar]}",
            ]
        else:  # para_de
            # Patamares 1,2,3 -> índices 1,3,5 (ou colunas 6,8,10)
            idx_map = {1: 1, 2: 3, 3: 5}
            patterns = [
                f"limite_para_de_patamar_{patamar}",
                f"para_de_p{patamar}",
                f"limite_p{patamar}_para_de",
                f"limite_{idx_map[patamar]}",
            ]
        
        for pattern in patterns:
            if pattern in row.index:
                val = row[pattern]
                if pd.notna(val):
                    float_val = self._safe_float(val)
                    if float_val is not None:
                        return float_val
        
            return None
    
    def _error(self, message: str) -> Dict[str, Any]:
        """Retorna resposta de erro padronizada."""
        return {
            "success": False,
            "error": message,
            "tool": self.get_name()
        }
