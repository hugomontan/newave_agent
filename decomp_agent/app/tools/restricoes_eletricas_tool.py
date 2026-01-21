"""
Tool para consultar restrições elétricas (bloco RE) do DECOMP,
com filtragem inicial por NOME textual (ex.: 'SEFAC', 'SERRA DO FACAO').

Estratégia INICIAL:
- Abre o arquivo dadger.rv*
- Monta um pool de nomes de restrição a partir dos comentários do arquivo,
  associando nomes a códigos de restrição (ex.: &-21- SERRA DO FACAO).
- Compara o nome pedido na query com esse pool (match simples por substring).
- Para os códigos encontrados, lê o bloco RE via idecomp (Dadger.re)
  e retorna os registros planificados como dicionários.
"""

from typing import Any, Dict, List, Optional
import os
import re

import pandas as pd
from idecomp.decomp import Dadger

from decomp_agent.app.tools.base import DECOMPTool
from decomp_agent.app.config import safe_print


class RestricoesEletricasDECOMPTool(DECOMPTool):
    """
    Tool INICIAL para consultar restrições elétricas (bloco RE) por nome.

    Exemplos de uso:
    - "Qual é a restrição elétrica SEFAC?"
    - "Mostrar a restrição elétrica da SERRA DO FACAO"
    """

    def get_name(self) -> str:
        return "RestricoesEletricasDECOMPTool"

    def can_handle(self, query: str) -> bool:
        """
        Decide se a query parece ser sobre restrições elétricas (bloco RE).
        Inclui palavras-chave para restrições de usinas e de intercâmbio estrutural.
        """
        q = query.lower()
        keywords = [
            "restricao eletrica",
            "restrição elétrica",
            "restricoes eletricas",
            "restrições elétricas",
            "bloco re",
            "registro re",
            "restrição re",
            "intercambio",
            "intercâmbio",
            "limite de intercambio",
            "limites de intercâmbio",
            "restricao de intercambio",
            "restrição de intercâmbio",
            "fns",
            "fnese",
            "germad",
            "ger mad",
            "fns + fnese",
            "gmin",
            "gmax",
            "limites minimos",
            "limites maximos",
        ]
        return any(k in q for k in keywords)

    def get_description(self) -> str:
        return """
        Consulta restrições elétricas (bloco RE/LU) do DECOMP filtrando por nome,
        incluindo restrições de usinas e de intercâmbio estrutural.
        
        A tool suporta busca por:
        - Nomes de restrições de usinas (ex: SEFAC, SERRA DO FACAO, PEDRA DO CAVALO)
        - Nomes de restrições de intercâmbio (ex: FNS + FNESE, GerMAD)
        - Pares de submercados via bloco FI (ex: FC + SE, NE + SE)

        Exemplos de queries:
        - "Qual é a restrição elétrica SEFAC?"
        - "Mostrar a restrição elétrica da SERRA DO FACAO"
        - "Qual a restrição de intercâmbio FNS + FNESE?"
        - "Mostrar GMIN e GMAX da restrição FC + SE"
        - "Restrição elétrica GerMAD"
        """

    def execute(self, query: str, **kwargs: Any) -> Dict[str, Any]:
        """
        Fluxo principal (refeito do zero, focado em LU):
        1. Localiza e lê o arquivo dadger.
        2. Constrói um pool de nomes de restrição a partir dos comentários (&-COD- NOME).
        3. Extrai o nome da restrição a partir da query.
        4. Casa o nome com um ou mais códigos de restrição.
        5. Para cada código, lê diretamente todos os registros LU via df=True
           e devolve os valores brutos da restrição (incluindo limites).
        """
        safe_print(f"[RE] Query: {query}")
        safe_print(f"[RE] Deck: {self.deck_path}")

        try:
            # 1) Encontrar arquivo dadger
            dadger_path = self._find_dadger_file()
            if not dadger_path:
                return self._error("Arquivo dadger.rv* não encontrado")

            safe_print(f"[RE] Arquivo: {dadger_path}")

            # 2) Ler Dadger (usar cache se disponível)
            try:
                from decomp_agent.app.utils.dadger_cache import get_cached_dadger

                dadger = get_cached_dadger(self.deck_path)
            except ImportError:
                dadger = Dadger.read(dadger_path)

            if dadger is None:
                return self._error("Erro ao ler arquivo dadger")

            # 3) Construir pool de nomes de restrições (usando dadger para acessar FI)
            pool_nomes = self._listar_nomes_restricoes(dadger_path, dadger)
            safe_print(f"[RE] Total de nomes de restrições encontrados no pool: {len(pool_nomes)}")

            if not pool_nomes:
                return self._error(
                    "Não foi possível identificar nomes de restrições elétricas no arquivo dadger."
                )

            # 4) Extrair nome da query (melhorado para aceitar mais variações)
            nome_query = self._extract_nome_query(query)
            if not nome_query:
                return {
                    "success": False,
                    "error": "Não consegui identificar o nome da restrição elétrica na pergunta.",
                    "pool_nomes_disponiveis": [
                        {
                            "nome": p.get("nome"),
                            "codigo_label": p.get("codigo_label"),
                            "codigo_restricao": p.get("codigo_restricao"),
                            "tipo": p.get("tipo", "usina")
                        }
                        for p in pool_nomes
                    ],
                    "tool": self.get_name(),
                }

            safe_print(f"[RE] Nome extraído da query: '{nome_query}'")
            safe_print(f"[RE] Pool de restrições disponíveis: {len(pool_nomes)} (usinas + intercâmbio)")
            
            # Mostrar alguns exemplos de nomes disponíveis (para debug)
            nomes_exemplo = [p.get("nome", "") for p in pool_nomes[:5]]
            if nomes_exemplo:
                safe_print(f"[RE] Exemplos de restrições disponíveis: {', '.join(nomes_exemplo)}...")

            # 5) Fazer match do nome da query com o pool de nomes
            matches = self._match_nome_pool(nome_query, pool_nomes)
            safe_print(f"[RE] Matches encontrados para '{nome_query}': {len(matches)}")
            if matches:
                match_info = []
                for m in matches[:3]:
                    nome_match = m.get('nome', '?')
                    nome_usado = m.get('nome_match_usado', nome_match)
                    score = m.get('score', 0.0)
                    codigo = m.get('codigo_restricao', m.get('codigo_label', '?'))
                    tipo = m.get('tipo', 'usina')
                    match_str = f"{nome_match}"
                    if nome_usado != nome_match:
                        match_str += f" (via '{nome_usado}')"
                    match_str += f" [código {codigo}, tipo: {tipo}, score: {score:.3f}]"
                    match_info.append(match_str)
                safe_print(f"[RE] Melhores matches: {', '.join(match_info)}")

            if not matches:
                nomes_disponiveis = [p.get("nome") for p in pool_nomes if p.get("nome")]
                return {
                    "success": False,
                    "error": (
                        f"Não encontrei nenhuma restrição elétrica cujo nome se pareça com '{nome_query}'. "
                        f"Consultas incluem restrições de usinas e de intercâmbio estrutural."
                    ),
                    "nome_query": nome_query,
                    "pool_nomes_disponiveis": [
                        {
                            "nome": p.get("nome"),
                            "codigo_label": p.get("codigo_label"),
                            "codigo_restricao": p.get("codigo_restricao"),
                            "tipo": p.get("tipo", "usina")
                        }
                        for p in pool_nomes
                    ],
                    "nomes_disponiveis": nomes_disponiveis[:20],  # Limitar a 20 para não sobrecarregar
                    "total_disponiveis": len(nomes_disponiveis),
                    "tool": self.get_name(),
                }

            # Códigos únicos encontrados (código efetivo de RE/LU), ignorando None
            codigos_set = set()
            for m in matches:
                cod = m.get("codigo_restricao", m.get("codigo_label", m.get("codigo")))
                if cod is not None:
                    codigos_set.add(cod)

            codigos = sorted(codigos_set)
            safe_print(f"[RE] Códigos de restrição (RE/LU) a consultar: {codigos}")

            # 6) Ler LU de TODO o arquivo uma vez e depois segmentar por código
            registros: List[Dict[str, Any]] = []
            lu_df_all = dadger.lu(df=True)
            if lu_df_all is None or not isinstance(lu_df_all, pd.DataFrame) or lu_df_all.empty:
                return {
                    "success": False,
                    "error": "Nenhum registro LU encontrado no arquivo dadger.",
                    "nome_query": nome_query,
                    "matches": matches,
                    "tool": self.get_name(),
                }

            # Tentar detectar o nome da coluna de código no DataFrame de LU
            col_codigo_options = ["codigo_restricao", "codigo", "cod_restricao"]
            col_codigo = None
            for c in col_codigo_options:
                if c in lu_df_all.columns:
                    col_codigo = c
                    break

            if col_codigo is None:
                safe_print("[RE] Aviso: coluna de código de restrição não encontrada em LU df=True")
                # Nesse caso extremo, não conseguimos segmentar; retornamos tudo explicitamente
                for _, row in lu_df_all.iterrows():
                    d = row.to_dict()
                    d["codigo_restricao_detectado"] = row.to_dict().get(col_codigo, None)
                    d["nomes_possiveis"] = []
                    d["nome_query"] = nome_query
                    registros.append(d)
            else:
                # Para cada código encontrado pelo nome, filtrar os LUs correspondentes
                for cod in codigos:
                    lu_df = lu_df_all[lu_df_all[col_codigo] == cod]
                    if lu_df.empty:
                        safe_print(f"[RE] Nenhum registro LU encontrado para código {cod}")
                        continue

                    # Nomes e código "de rótulo" (do comentário &-XX- NOME)
                    nomes_cod = [
                        m["nome"]
                        for m in matches
                        if m.get("codigo_restricao", m.get("codigo_label", m.get("codigo"))) == cod
                    ]
                    codigos_label = [
                        m.get("codigo_label", m.get("codigo"))
                        for m in matches
                        if m.get("codigo_restricao", m.get("codigo_label", m.get("codigo"))) == cod
                    ]
                    codigo_label = codigos_label[0] if codigos_label else None
                    
                    # Obter tipo da restrição ("usina" ou "intercambio")
                    tipo_restricao = "usina"  # default
                    for m in matches:
                        if m.get("codigo_restricao", m.get("codigo_label", m.get("codigo"))) == cod:
                            tipo_restricao = m.get("tipo", "usina")
                            break

                    for _, row in lu_df.iterrows():
                        d = row.to_dict()
                        # Preservar o código vindo do próprio DF (col_codigo),
                        # mas também marcar o código da query (RE/LU) e o código de rótulo (&-XX-)
                        d["codigo_restricao"] = row.get(col_codigo)
                        d["codigo_restricao_query"] = cod
                        d["codigo_label_comentario"] = codigo_label
                        d["nomes_possiveis"] = nomes_cod
                        d["nome_query"] = nome_query
                        d["tipo"] = tipo_restricao  # NOVO: tipo da restrição (sempre "usina" agora)
                        registros.append(d)

            if not registros:
                # Diferenciar dois casos:
                # - há códigos mapeados, mas nenhum LU ativo encontrado (provavelmente comentado)
                # - nenhum código mapeado (já tratado antes, em matches vazios)
                if codigos:
                    msg = (
                        "A restrição foi identificada no dadger, mas não há registros LU ativos "
                        f"associados aos código(s) {codigos}. "
                        "É provável que a restrição esteja comentada/inativa (linhas iniciadas com '&')."
                    )
                    return {
                        "success": False,
                        "error": msg,
                        "nome_query": nome_query,
                        "matches": matches,
                        "codigos_encontrados": codigos,
                        "restricao_possivelmente_inativa": True,
                        "tool": self.get_name(),
                    }
                else:
                    msg = (
                        "Não foi possível associar a consulta a nenhum código de restrição "
                        "no arquivo (nenhum RE/LU encontrado após o comentário)."
                    )
                    return {
                        "success": False,
                        "error": msg,
                        "nome_query": nome_query,
                        "matches": matches,
                        "tool": self.get_name(),
                    }

            # 7) Resposta planificada: os valores de LU aparecem exatamente como saem do idecomp
            return {
                "success": True,
                "nome_query": nome_query,
                "matches": matches,
                "codigos_encontrados": codigos,
                "total_registros": len(registros),
                "data": registros,
                "tool": self.get_name(),
            }

        except Exception as e:  # pragma: no cover - proteção em runtime
            safe_print(f"[RE] Erro: {e}")
            import traceback

            traceback.print_exc()
            return self._error(str(e))

    # ------------------------------------------------------------------
    # HELPERS
    # ------------------------------------------------------------------

    def _find_dadger_file(self) -> Optional[str]:
        """Encontra o arquivo dadger.rvX ou dadger.rvx no deck."""
        for ext in range(10):
            candidate = os.path.join(self.deck_path, f"dadger.rv{ext}")
            if os.path.exists(candidate):
                return candidate
        candidate = os.path.join(self.deck_path, "dadger.rvx")
        if os.path.exists(candidate):
            return candidate
        return None

    def _extract_nome_query(self, query: str) -> Optional[str]:
        """
        Extrai um nome de restrição a partir da query.

        Estratégia melhorada para aceitar mais variações:
        - "qual a restricao eletrica de CORUMBA I"
        - "restricao eletrica CORUMBA I"
        - "restricao de CORUMBA I"
        - "restrição CORUMBA I"
        - "CORUMBA I" (sem palavra-chave)
        """
        q = query.strip()

        # Padrão 1: "qual a restricao eletrica de [NOME]"
        m = re.search(
            r"qual\s+a\s+restri[cç][aã]o\s+el[eé]trica\s+de\s+(.+)$",
            q,
            flags=re.IGNORECASE,
        )
        if m:
            nome = m.group(1).strip()
            if nome:
                return nome

        # Padrão 2: "restricao eletrica de [NOME]" ou "restricao de [NOME]"
        m = re.search(
            r"restri[cç][aã]o(?:\s+el[eé]trica)?\s+de\s+(.+)$",
            q,
            flags=re.IGNORECASE,
        )
        if m:
            nome = m.group(1).strip()
            if nome:
                return nome

        # Padrão 3: "restricao eletrica [NOME]" (sem "de")
        # Captura nomes com "+" como "FNS + FNESE"
        m = re.search(
            r"restri[cç][aã]o(?:\s+el[eé]trica)?\s+([A-Z][A-Z\s\+\-]*(?:\s*\+\s*[A-Z][A-Z\s]*)*)",
            q,
            flags=re.IGNORECASE,
        )
        if m:
            nome = m.group(1).strip()
            if nome:
                return nome

        # Padrão 4: Remover palavras-chave comuns e pegar o restante
        palavras_chave = [
            r"qual\s+a\s+restri[cç][aã]o",
            r"restri[cç][aã]o\s+el[eé]trica",
            r"restri[cç][aã]o",
            r"mostrar",
            r"mostre",
            r"consulte",
            r"consultar",
        ]
        nome_limpo = q
        for pkw in palavras_chave:
            nome_limpo = re.sub(pkw, "", nome_limpo, flags=re.IGNORECASE)
        nome_limpo = nome_limpo.strip()
        
        if nome_limpo:
            # Remover "de" no início
            nome_limpo = re.sub(r"^de\s+", "", nome_limpo, flags=re.IGNORECASE).strip()
            if nome_limpo:
                return nome_limpo

        # Fallback: pegar últimas 1–4 palavras (para nomes compostos como "CORUMBA I")
        partes = q.split()
        if not partes:
            return None

        # Tentar últimas 4, 3, 2, depois 1
        for n in (4, 3, 2, 1):
            if len(partes) >= n:
                nome = " ".join(partes[-n:])
                nome = nome.strip()
                # Filtrar palavras-chave comuns
                if nome and nome.lower() not in ["eletrica", "restricao", "restrição"]:
                    return nome

        return None

    def _listar_nomes_restricoes(self, dadger_path: str, dadger: Dadger) -> List[Dict[str, Any]]:
        """
        Lista nomes de restrições elétricas a partir dos comentários do dadger
        E TAMBÉM usa o bloco FI para criar nomes alternativos baseados em pares de submercados.
        
        Diferencia entre:
        - Restrições de usinas (ex: PEDRA DO CAVALO, SERRA DO FACAO)
        - Restrições de intercâmbio estrutural (ex: GerMAD, SANTO ANTONIO E JIRAU, FNS + FNESE)
        
        Para restrições de intercâmbio, usa o bloco FI para criar nomes alternativos:
        - Ex: Se uma restrição tem FI com "FC + SE" e "NE + SE", cria nome "FC + SE" e "NE + SE"
        - Permite encontrar "FNS + FNESE" através dos pares de submercados

        Retorno:
        [
            {
                "codigo_label": 189,
                "codigo_restricao": 283,
                "nome": "PEDRA DO CAVALO",
                "tipo": "usina",
                "nomes_alternativos": []
            },
            {
                "codigo_label": None,
                "codigo_restricao": 429,
                "nome": "FNS + FNESE",
                "tipo": "intercambio",
                "nomes_alternativos": ["FC + SE", "NE + SE"]
            },
            ...
        ]
        """
        with open(dadger_path, "r", encoding="latin-1") as f:
            linhas = f.readlines()

        pool: List[Dict[str, Any]] = []
        tipo_atual = "usina"  # Default: restrições de usinas
        
        # Padrão para detectar seção de intercâmbio estrutural
        padrao_intercambio = re.compile(
            r"&\s*\*+\s*RESTRICOES?\s+DE\s+INTERCAMBIO\s+ESTRUTURAIS?\s*\*+",
            re.IGNORECASE
        )
        
        # Padrão para detectar fim da seção de intercâmbio (nova seção de usinas)
        # Ex: &************************** VOTORANTIM CIMENTOS **************************
        padrao_secao_usina = re.compile(
            r"&\s*\*+\s+[^*]+\s+\*+",
            re.IGNORECASE
        )

        for i, line in enumerate(linhas):
            texto = line.strip()
            
            # Verificar se é início da seção de intercâmbio estrutural
            if padrao_intercambio.search(texto):
                tipo_atual = "intercambio"
                safe_print(f"[RE] ✅ Seção de restrições de INTERCÂMBIO detectada na linha {i+1} - incluindo")
                continue
            
            # Verificar se é início de nova seção de usinas (marca fim da seção de intercâmbio)
            # Ex: &************************** VOTORANTIM CIMENTOS **************************
            if tipo_atual == "intercambio" and padrao_secao_usina.match(texto):
                # Se encontrou uma seção nova e não é intercâmbio explícito, volta para usinas
                if "intercambio" not in texto.lower() and "estrutural" not in texto.lower():
                    tipo_atual = "usina"
                    safe_print(f"[RE] ✅ Nova seção de USINAS detectada na linha {i+1}")

            # Padrão do comentário: &-189- PEDRA DO CAVALO
            m_comment = re.match(r"&\s*-(\d+)-\s*(.+)", texto)
            codigo_label: Optional[int] = None
            nome: Optional[str] = None
            
            if m_comment:
                codigo_label = int(m_comment.group(1))
                nome = m_comment.group(2).strip()
            
            # Se não encontrou padrão &-NNN-, verificar se é comentário simples de intercâmbio
            # Padrão alternativo para intercâmbio: & FNESE ou & FNS + FNESE - Restricao...
            if not nome and tipo_atual == "intercambio" and texto.startswith("&"):
                texto_sem_ampersand = texto[1:].strip()
                
                # SEMPRE tentar extrair nome antes de separadores, mesmo se a linha tem palavras genéricas
                # Padrão: nome em maiúsculas com possíveis "+" e espaços, seguido de " -", " --->", " =", ou " ("
                # Exemplos: 
                #   "FNS = GH LAJEADO..." → "FNS"
                #   "FNS + FNESE - Restricao..." → "FNS + FNESE"
                #   "FNEN (-FNE) = Fluxo..." → "FNEN" (para no parêntese)
                match_nome = re.match(r"^([A-Z][A-Z\s\+\-]+?)(?:\s*[-–]{1,3}>?\s*|\s*=\s*|\s*\()", texto_sem_ampersand)
                if match_nome:
                    nome_candidato = match_nome.group(1).strip()
                    # Filtrar nomes muito curtos (< 2 chars) ou que são apenas números
                    if len(nome_candidato) >= 2 and not nome_candidato.replace(" ", "").replace("+", "").isdigit():
                        nome = nome_candidato
                
                # Se não encontrou nome antes de separadores, verificar se é comentário simples
                if not nome and texto_sem_ampersand and len(texto_sem_ampersand) >= 2:
                    # Comentário simples: & FNESE ou & FNS + FNESE (apenas nome, sem " -")
                    # Verificar se parece com um nome de intercâmbio (principalmente maiúsculas, pode ter +)
                    # Aceitar se é principalmente maiúsculas (pelo menos 70% do texto)
                    texto_limpo = texto_sem_ampersand.replace(" ", "").replace("+", "")
                    if texto_limpo and texto_limpo.upper() == texto_limpo:
                        # Verificar se não é apenas números ou caracteres especiais
                        if any(c.isalpha() for c in texto_limpo):
                            nome = texto_sem_ampersand.strip()
            
            # Se ainda não encontrou nome, continuar (não é um comentário de nome válido)
            if not nome:
                continue

            # Procurar nas próximas linhas um RE (ou LU) com o código efetivo da restrição
            codigo_restricao: Optional[int] = None
            for j in range(i + 1, min(i + 20, len(linhas))):
                texto_prox = linhas[j].strip()
                # Linhas podem vir comentadas: "&RE  143   1   5" ou "RE  143   1   5"
                m_re = re.match(r"&?\s*RE\s+(\d+)\s+", texto_prox, flags=re.IGNORECASE)
                m_lu = re.match(r"&?\s*LU\s+(\d+)\s+", texto_prox, flags=re.IGNORECASE)
                m = m_re or m_lu
                if m:
                    codigo_restricao = int(m.group(1))
                    break

            # Adicionar TODAS as restrições ao pool (tanto usinas quanto intercâmbio)
            pool.append(
                {
                    "codigo_label": codigo_label,  # código do comentário &-XX- (pode ser None para intercâmbio)
                    "codigo_restricao": codigo_restricao,  # código efetivo RE/LU (pode ser None)
                    "nome": nome,
                    "tipo": tipo_atual,  # "usina" ou "intercambio"
                    "nomes_alternativos": [],  # será preenchido pelo FI
                }
            )

        # AGORA: Usar bloco FI para criar nomes alternativos baseados em pares de submercados
        # Isso permite encontrar restrições como "FNS + FNESE" através dos pares FI
        try:
            fi_df = dadger.fi(df=True)
            if fi_df is not None and not fi_df.empty:
                safe_print(f"[RE] 📋 Bloco FI encontrado com {len(fi_df)} registros")
                
                # Detectar colunas do DataFrame FI
                col_codigo = None
                col_sub_de = None
                col_sub_para = None
                
                for col in fi_df.columns:
                    col_lower = col.lower()
                    if col_codigo is None and "codigo_restricao" in col_lower or "cod_restricao" in col_lower:
                        col_codigo = col
                    if col_sub_de is None and ("codigo_submercado_de" in col_lower or "sub_de" in col_lower or "de" == col_lower):
                        col_sub_de = col
                    if col_sub_para is None and ("codigo_submercado_para" in col_lower or "sub_para" in col_lower or "para" == col_lower):
                        col_sub_para = col
                
                if col_codigo and col_sub_de and col_sub_para:
                    # Agrupar por código de restrição
                    for codigo_restricao, group in fi_df.groupby(col_codigo):
                        codigo_restricao_val = int(codigo_restricao) if pd.notna(codigo_restricao) else None
                        if codigo_restricao_val is None:
                            continue
                        
                        # Obter todos os pares únicos de submercados para esta restrição
                        pares_unicos = set()
                        for _, row in group.iterrows():
                            sub_de = str(row.get(col_sub_de, "")).strip() if pd.notna(row.get(col_sub_de)) else ""
                            sub_para = str(row.get(col_sub_para, "")).strip() if pd.notna(row.get(col_sub_para)) else ""
                            
                            if sub_de and sub_para:
                                # Criar nome alternativo: "FC + SE", "NE + SE", etc.
                                nome_alternativo = f"{sub_de} + {sub_para}"
                                pares_unicos.add(nome_alternativo)
                        
                        if pares_unicos:
                            # Verificar se já existe entrada no pool para este código
                            encontrado = False
                            for item in pool:
                                if item.get("codigo_restricao") == codigo_restricao_val:
                                    # Adicionar nomes alternativos à entrada existente
                                    nomes_alt_existentes = item.get("nomes_alternativos", [])
                                    for nome_alt in pares_unicos:
                                        if nome_alt not in nomes_alt_existentes:
                                            nomes_alt_existentes.append(nome_alt)
                                    item["nomes_alternativos"] = nomes_alt_existentes
                                    encontrado = True
                                    break
                            
                            if not encontrado:
                                # Criar nova entrada no pool com base nos pares FI
                                # Ordenar pares para criar nome consistente
                                pares_ordenados = sorted(list(pares_unicos))
                                nome_principal = " + ".join(pares_ordenados) if len(pares_ordenados) == 1 else " + ".join(pares_ordenados)
                                
                                pool.append({
                                    "codigo_label": None,
                                    "codigo_restricao": codigo_restricao_val,
                                    "nome": nome_principal,
                                    "tipo": "intercambio",
                                    "nomes_alternativos": list(pares_unicos),
                                })
                                safe_print(f"[RE] ✅ Adicionado ao pool via FI: código {codigo_restricao_val}, nomes: {', '.join(pares_unicos)}")
                else:
                    safe_print(f"[RE] ⚠️ Colunas do FI não identificadas corretamente. Colunas disponíveis: {list(fi_df.columns)}")
        except Exception as e:
            safe_print(f"[RE] ⚠️ Erro ao processar bloco FI: {e}")

        total_usinas = sum(1 for p in pool if p.get("tipo") == "usina")
        total_intercambio = sum(1 for p in pool if p.get("tipo") == "intercambio")
        safe_print(f"[RE] 📊 Total de restrições disponíveis: {len(pool)}")
        safe_print(f"[RE]   - Restrições de USINAS: {total_usinas}")
        safe_print(f"[RE]   - Restrições de INTERCÂMBIO: {total_intercambio}")

        return pool

    def _normalize(self, texto: str) -> str:
        """
        Normaliza string para comparação mais robusta:
        - strip
        - lower
        - remove acentos
        - remove pontuações simples (MAS preserva "+" para nomes de intercâmbio)
        - colapsa múltiplos espaços
        - normaliza espaços ao redor de "+"
        """
        import unicodedata

        if not isinstance(texto, str):
            texto = str(texto or "")

        texto = texto.strip().lower()
        # remover acentos
        texto = unicodedata.normalize("NFD", texto)
        texto = "".join(ch for ch in texto if unicodedata.category(ch) != "Mn")
        
        # Normalizar espaços ao redor de "+" (ex: "FNS+FNESE" -> "FNS + FNESE")
        texto = re.sub(r"\s*\+\s*", " + ", texto)
        
        # remover pontuação básica (MAS preservar "+")
        texto = re.sub(r"[^\w\s\+]", " ", texto)
        # colapsar múltiplos espaços
        texto = re.sub(r"\s+", " ", texto)
        return texto.strip()

    def _match_nome_pool(
        self, nome_query: str, pool: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Matching otimizado para restrições elétricas, incluindo intercâmbio.
        
        Regras para intercâmbio:
        - Se query é "FNESE" → matcha nomes que contêm "FNESE" (ex: "FNS + FNESE")
        - Se query é "FNS + FNESE" → matcha nomes que contêm ambos componentes
        - Prioriza nomes mais específicos (mais longos primeiro)
        """
        from difflib import SequenceMatcher

        alvo_norm = self._normalize(nome_query)
        if not alvo_norm:
            return []

        matches: List[Dict[str, Any]] = []
        
        # ============================================================
        # REGRA ESPECIAL: Correspondência direta para restrições de intercâmbio conhecidas
        # Lista exata: FNS, FNESE, FNNE, FNEN, EXPNE, FNS + FNESE, RSUL
        # Esta verificação deve ocorrer ANTES do matching geral (antes de usinas)
        # ============================================================
        restricoes_intercambio_diretas = {
            "fns": "fns",
            "fnese": "fnese",
            "fnne": "fnne",
            "fnen": "fnen",
            "expne": "expne",
            "fns + fnese": "fns + fnese",
            "rsul": "rsul"
        }
        
        # Verificar se a query normalizada corresponde a uma restrição de intercâmbio conhecida
        if alvo_norm in restricoes_intercambio_diretas:
            for item in pool:
                # Verificar apenas restrições de intercâmbio
                if item.get("tipo") != "intercambio":
                    continue
                
                nome_pool = item.get("nome", "")
                norm_pool = self._normalize(str(nome_pool)) if nome_pool else ""
                
                if not norm_pool:
                    continue
                
                # Regra especial para FNS: deve matchar apenas se o nome_pool NÃO começar com "FNS +"
                # Isso previne que "FNS" match com "FNS + FNESE"
                if alvo_norm == "fns":
                    # Se o nome_pool começa com "fns +", não é match (deve ser "FNS + FNESE")
                    if norm_pool.startswith("fns +"):
                        continue  # Ignora este item completamente
                    # Só continua se o nome_pool é exatamente "fns" ou contém "fns" como nome alternativo correto
                
                # Coletar todos os nomes possíveis (principal + alternativos)
                all_names = [nome_pool]
                all_names.extend(item.get("nomes_alternativos", []))
                
                for nome_candidate in all_names:
                    if not nome_candidate:
                        continue
                    
                    nome_candidate_norm = self._normalize(str(nome_candidate))
                    
                    # Match exato (sem espaços extras)
                    if alvo_norm == nome_candidate_norm:
                        # Regra adicional para FNS: garantir que o candidato não seja "FNS + FNESE"
                        if alvo_norm == "fns" and nome_candidate_norm.startswith("fns +"):
                            continue  # Ignora este candidato
                        
                        matches.append({
                            "codigo_label": item.get("codigo_label", item.get("codigo")),
                            "codigo_restricao": item.get(
                                "codigo_restricao", item.get("codigo_label", item.get("codigo"))
                            ),
                            "nome": nome_pool,
                            "nome_match_usado": nome_candidate,
                            "tipo": item.get("tipo", "intercambio"),
                            "nomes_alternativos": item.get("nomes_alternativos", []),
                            "score": 1.0,  # Match exato
                        })
                        break  # Encontrou match exato, não precisa verificar mais
            
            # Se encontrou matches diretos, retornar apenas o melhor (mais específico)
            # IMPORTANTE: Se não encontrou matches para restrições diretas, retornar vazio
            # (não continuar para o matching geral, pois essas são correspondências exatas)
            if matches:
                # Ordenar por score e retornar o melhor
                matches.sort(key=lambda m: m.get("score", 0.0), reverse=True)
                return [matches[0]]
            else:
                # Não encontrou match exato para restrição direta → retornar vazio
                # (evita fallback para matching geral que poderia dar match incorreto)
                return []
        
        # ============================================================
        # MATCHING GERAL (se não encontrou match direto)
        # ============================================================
        
        # Verificar se query tem estrutura de intercâmbio (contém "+")
        has_plus = " + " in alvo_norm
        if has_plus:
            query_components = [c.strip() for c in alvo_norm.split(" + ")]
        else:
            query_components = [alvo_norm]
        
        # Ordenar pool por especificidade (mais específico primeiro = mais longo)
        pool_sorted = sorted(
            pool,
            key=lambda x: len(str(x.get('nome', ''))),
            reverse=True
        )

        def _score_simple(a: str, b: str) -> float:
            """
            Score simples para fallback (usado quando matching de componentes não funciona).
            """
            if not a or not b:
                return 0.0
            
            if a == b:
                return 1.0
            
            if a in b or b in a:
                return 0.9
            
            fuzz = SequenceMatcher(None, a, b).ratio()
            return fuzz

        for item in pool_sorted:
            nome_pool = item.get("nome", "")
            norm_pool = self._normalize(str(nome_pool)) if nome_pool else ""
            
            if not norm_pool:
                continue

            # Coletar todos os nomes possíveis (principal + alternativos)
            all_names = [nome_pool]
            all_names.extend(item.get("nomes_alternativos", []))
            
            best_score = 0.0
            melhor_nome_usado = nome_pool
            
            for nome_candidate in all_names:
                if not nome_candidate:
                    continue
                
                nome_candidate_norm = self._normalize(str(nome_candidate))
                
                # REGRA 1: Match exato (maior prioridade)
                if alvo_norm == nome_candidate_norm:
                    best_score = 1.0
                    melhor_nome_usado = nome_candidate
                    break  # Match perfeito, não precisa verificar mais
                
                # REGRA 2: Se query tem múltiplos componentes (tem "+"), verificar se TODOS estão presentes
                if has_plus:
                    candidate_has_plus = " + " in nome_candidate_norm
                    
                    if candidate_has_plus:
                        candidate_components = [c.strip() for c in nome_candidate_norm.split(" + ")]
                        
                        # Verificar se TODOS os componentes da query estão no candidate
                        all_present = all(
                            any(
                                query_comp == cand_comp or 
                                (len(query_comp) >= 3 and query_comp in cand_comp) or
                                (len(cand_comp) >= 3 and cand_comp in query_comp)
                                for cand_comp in candidate_components
                            )
                            for query_comp in query_components
                        )
                        
                        if all_present:
                            # Score baseado na proporção de componentes
                            coverage = len(query_components) / max(len(candidate_components), 1)
                            score = 0.8 + (coverage * 0.15)  # 0.8-0.95
                            
                            # Bônus se número de componentes é igual (match mais preciso)
                            if len(query_components) == len(candidate_components):
                                score = min(1.0, score + 0.05)
                            
                            if score > best_score:
                                best_score = score
                                melhor_nome_usado = nome_candidate
                    else:
                        # Candidate não tem "+", mas query tem → verificar se candidate contém todos os componentes
                        all_present = all(query_comp in nome_candidate_norm for query_comp in query_components)
                        if all_present:
                            score = 0.75  # Score menor pois estrutura diferente
                            if score > best_score:
                                best_score = score
                                melhor_nome_usado = nome_candidate
                
                # REGRA 3: Se query tem 1 componente, verificar se está presente como substring válida
                else:
                    query_comp = query_components[0]
                    
                    # Verificar se o componente está presente no nome (como substring)
                    if query_comp in nome_candidate_norm:
                        # Verificar se é match de componente completo (separado por "+" ou espaço)
                        candidate_components = []
                        if " + " in nome_candidate_norm:
                            # Nome tem estrutura de intercâmbio: "FNS + FNESE"
                            candidate_components = [c.strip() for c in nome_candidate_norm.split(" + ")]
                        else:
                            # Nome não tem "+", tratar como um único componente ou tokens separados por espaço
                            candidate_components = [nome_candidate_norm]
                            # Também adicionar tokens significativos (> 3 chars)
                            candidate_components.extend([c.strip() for c in nome_candidate_norm.split() if len(c.strip()) >= 3])
                        
                        # Score baseado no tipo de match
                        if query_comp in candidate_components:
                            # Match exato de componente → score alto
                            # Ex: query "fnese" está em ["fns", "fnese"] como componente exato
                            score = 0.9
                            safe_print(f"[RE] [MATCH] Componente exato encontrado: '{query_comp}' em '{nome_candidate}' (componentes: {candidate_components})")
                        elif any(query_comp in comp or comp in query_comp for comp in candidate_components if len(comp) >= 3):
                            # Componente está contido em algum componente do candidate (ou vice-versa)
                            # Ex: "fnese" pode estar parcialmente em algum componente
                            score = 0.85
                            safe_print(f"[RE] [MATCH] Componente parcial encontrado: '{query_comp}' em '{nome_candidate}'")
                        else:
                            # Match como substring pura → score baseado no tamanho relativo
                            relative_size = len(query_comp) / max(len(nome_candidate_norm), 1)
                            
                            if relative_size >= 0.8:
                                score = 0.95
                            elif relative_size >= 0.5:
                                score = 0.85
                            else:
                                score = 0.75
                            
                            safe_print(f"[RE] [MATCH] Substring encontrada: '{query_comp}' em '{nome_candidate}' (score: {score:.2f})")
                        
                        if score > best_score:
                            best_score = score
                            melhor_nome_usado = nome_candidate
            
            # Fallback: usar score simples APENAS se:
            # 1. Query NÃO tem múltiplos componentes (query simples), OU
            # 2. Query tem múltiplos componentes MAS candidato também tem (ambos compostos)
            # Isso evita que "FNS + FNESE" match "FNESE" através do fallback
            if best_score < 0.7:
                # Se query tem "+" (composta), só usar fallback se candidato também tem "+"
                # Queries compostas devem priorizar matches compostos
                candidate_has_plus = " + " in norm_pool
                
                if not has_plus or candidate_has_plus:
                    # Tentar score simples para casos que não se encaixam nas regras acima
                    s_simple = _score_simple(alvo_norm, norm_pool)
                    
                    # Verificar alternativos também
                    for nome_alt in item.get("nomes_alternativos", []):
                        norm_alt = self._normalize(str(nome_alt))
                        if norm_alt:
                            # Se query é composta, só considerar alternativos também compostos
                            alt_has_plus = " + " in norm_alt
                            if not has_plus or alt_has_plus:
                                s_alt_simple = _score_simple(alvo_norm, norm_alt)
                                if s_alt_simple > s_simple:
                                    s_simple = s_alt_simple
                                    melhor_nome_usado = nome_alt
                    
                    if s_simple > best_score:
                        best_score = s_simple
            
            # Só adicionar se score é significativo
            if best_score >= 0.7:
                matches.append(
                    {
                        "codigo_label": item.get("codigo_label", item.get("codigo")),
                        "codigo_restricao": item.get(
                            "codigo_restricao", item.get("codigo_label", item.get("codigo"))
                        ),
                        "nome": nome_pool,
                        "nome_match_usado": melhor_nome_usado,
                        "tipo": item.get("tipo", "usina"),
                        "nomes_alternativos": item.get("nomes_alternativos", []),
                        "score": best_score,
                    }
                )

        if not matches:
            return []

        # Ordenar por score decrescente
        matches.sort(key=lambda m: m.get("score", 0.0), reverse=True)

        # Retornar apenas o melhor match (mais específico e com maior score)
        return [matches[0]]

    def _error(self, message: str) -> Dict[str, Any]:
        """Retorna resposta de erro padronizada."""
        return {
            "success": False,
            "error": message,
            "tool": self.get_name(),
        }

