"""
Módulo centralizado para normalização e matching de nomes de usinas térmicas.
Unifica nomes variantes entre NEWAVE e DECOMP.

ESTRATÉGIA:
1. Dicionário explícito de mapeamentos (baseado no CSV analisado)
2. Extração de candidatos de nomes da query (remove palavras comuns)
3. Normalização heurística (remoção de prefixos UTE, sufixos _F)
4. Matching fuzzy com similaridade de strings
"""

import re
from typing import Dict, List, Optional, Tuple, Set
from difflib import SequenceMatcher


class UsinaNameMatcher:
    """
    Classe para normalização e matching de nomes de usinas térmicas.
    Resolve variações de nomenclatura entre NEWAVE e DECOMP.
    """
    
    # Palavras a ignorar ao extrair nomes de usinas da query
    PALAVRAS_IGNORAR: Set[str] = {
        'qual', 'quais', 'a', 'o', 'as', 'os', 'da', 'de', 'do', 'das', 'dos',
        'para', 'por', 'em', 'na', 'no', 'nas', 'nos', 'é', 'e', 'que', 'como',
        'quanto', 'quantos', 'quantas', 'disponibilidade', 'usina', 'usinas',
        'térmica', 'termica', 'térmicas', 'termicas', 'ute', 'gerar', 'geracao',
        'geração', 'potencia', 'potência', 'cvu', 'custo', 'capacidade',
        'inflex', 'inflexibilidade', 'total', 'media', 'média', 'valor',
        'valores', 'dados', 'informacao', 'informação', 'sobre', 'mostrar',
        'exibir', 'listar', 'buscar', 'encontrar', 'calcular', 'obter'
    }
    
    # Dicionário de mapeamento: variante -> nome_canonico
    # Baseado na análise do CSV todas_termicas_20260116_172756.csv
    # IMPORTANTE: Usar nomes canônicos consistentes (sem conversão de romanos)
    NAME_VARIANTS: Dict[str, str] = {
        # TERMOMACAE / T.MACAE
        'termomacae': 'TERMOMACAE',
        't.macae': 'TERMOMACAE',
        't macae': 'TERMOMACAE',
        't.macae_f': 'TERMOMACAE',
        'tmacae': 'TERMOMACAE',
        
        # TERMOBAHIA / T.BAHIA
        'termobahia': 'TERMOBAHIA',
        't.bahia': 'TERMOBAHIA',
        't bahia': 'TERMOBAHIA',
        't.bahia_f': 'TERMOBAHIA',
        'tbahia': 'TERMOBAHIA',
        
        # JUIZ DE FORA / J.FORA
        'juiz de fora': 'JUIZ DE FORA',
        'j.fora': 'JUIZ DE FORA',
        'j fora': 'JUIZ DE FORA',
        'j.fora_f': 'JUIZ DE FORA',
        'jfora': 'JUIZ DE FORA',
        
        # TRES LAGOAS / T.LAGOAS
        'tres lagoas': 'TRES LAGOAS',
        't.lagoas': 'TRES LAGOAS',
        't lagoas': 'TRES LAGOAS',
        't.lagoas_f': 'TRES LAGOAS',
        'tlagoas': 'TRES LAGOAS',
        
        # J.LACERDA variações
        'j.lacerda c': 'J.LACERDA C',
        'j.lacer. c': 'J.LACERDA C',
        'j.lac. c': 'J.LACERDA C',
        'jlacerda c': 'J.LACERDA C',
        'j.lacerda b': 'J.LACERDA B',
        'j.lacer. b': 'J.LACERDA B',
        'jlacerda b': 'J.LACERDA B',
        'j.lacerda a1': 'J.LACERDA A1',
        'j.lac. a1': 'J.LACERDA A1',
        'jlacerda a1': 'J.LACERDA A1',
        'j.lacerda a2': 'J.LACERDA A2',
        'j.lac. a2': 'J.LACERDA A2',
        'jlacerda a2': 'J.LACERDA A2',
        
        # MARANHAO variações (manter romanos como canônico)
        'maranhao iv': 'MARANHAO IV',
        'maranhao 4': 'MARANHAO IV',
        'maranhaoiv': 'MARANHAO IV',
        'maranhao4': 'MARANHAO IV',
        'maranhao v': 'MARANHAO V',
        'maranhao 5': 'MARANHAO V',
        'maranhao iii': 'MARANHAO III',
        'maranhao 3': 'MARANHAO III',
        'maranhao3': 'MARANHAO III',
        
        # CUIABA
        'cuiaba g cc': 'CUIABA G CC',
        'cuiaba cc': 'CUIABA G CC',
        'cuiaba': 'CUIABA G CC',
        
        # N.VENECIA
        'n.venecia 2': 'N.VENECIA 2',
        'n.venecia2': 'N.VENECIA 2',
        'n.venec2_f': 'N.VENECIA 2',
        'nvenecia 2': 'N.VENECIA 2',
        'n.venecia ii': 'N.VENECIA 2',
        
        # PIRAT.12
        'pirat.12 g': 'PIRAT.12 G',
        'pirat.12 o': 'PIRAT.12 G',
        'pirat12': 'PIRAT.12 G',
        
        # CAMPINA
        'campina gde': 'CAMPINA GDE',
        'campina_gr': 'CAMPINA GDE',
        'campina grande': 'CAMPINA GDE',
        'campinagde': 'CAMPINA GDE',
        
        # GERAMAR (manter romanos como canônico)
        'geramar i': 'GERAMAR I',
        'geramar 1': 'GERAMAR I',
        'geramar1': 'GERAMAR I',
        'geramar1_f': 'GERAMAR I',
        'geramar ii': 'GERAMAR II',
        'geramar 2': 'GERAMAR II',
        'geramar2': 'GERAMAR II',
        'geramar2_f': 'GERAMAR II',
        
        # VALE DO ACU
        'vale do acu': 'VALE DO ACU',
        'vale acu': 'VALE DO ACU',
        'valedoacu': 'VALE DO ACU',
        
        # DO ATLAN_CSA
        'do atlan_csa': 'DO ATLAN_CSA',
        'atlan_csa': 'DO ATLAN_CSA',
        'atlantico': 'DO_ATLANTICO',
        'do_atlantico': 'DO_ATLANTICO',
        'atlantic_f': 'DO_ATLANTICO',
        
        # PROSPERIDADE
        'prosperidade': 'PROSPERIDADE',
        'prosp_i': 'PROSPERIDADE',
        'prosperi iii': 'PROSPERI III',
        'prosperi 3': 'PROSPERI III',
        'prosp_iii': 'PROSPERI III',
        'prosperid ii': 'PROSPERID II',
        'prosperid 2': 'PROSPERID II',
        'prosp_ii': 'PROSPERID II',
        
        # PERNAMBU
        'pernambu_iii': 'PERNAMBU_III',
        'pernambu_3': 'PERNAMBU_III',
        'pernambu iii': 'PERNAMBU_III',
        'pernambu 3': 'PERNAMBU_III',
        
        # ERB CANDEIAS
        'erb candeias': 'ERB CANDEIAS',
        'erb candei': 'ERB CANDEIAS',
        'erbcandeias': 'ERB CANDEIAS',
        
        # N.PIRATINING
        'n.pirating': 'N.PIRATINING',
        'npiratinga': 'N.PIRATINING',
        'npiratin_f': 'N.PIRATINING',
        'n.piratining': 'N.PIRATINING',
        
        # PARNAIBA
        'parnaiba iv': 'PARNAIBA IV',
        'parnaiba 4': 'PARNAIBA IV',
        'parnaib_iv': 'PARNAIBA IV',
        'parna_iv_f': 'PARNAIBA IV',
        'parnaiba v': 'PARNAIBA V',
        'parnaiba 5': 'PARNAIBA V',
        'parnaiba_v': 'PARNAIBA V',
        
        # GNA - IMPORTANTE: aceitar tanto romanos quanto números
        'gna i': 'GNA I',
        'gna 1': 'GNA I',
        'gna1': 'GNA I',
        'ute gna i': 'GNA I',
        'ute gna 1': 'GNA I',
        'gna ii': 'GNA II',
        'gna 2': 'GNA II',
        'gna2': 'GNA II',
        'ute gna ii': 'GNA II',
        'ute gna 2': 'GNA II',
        'gna iii': 'GNA III',
        'gna 3': 'GNA III',
        'gna3': 'GNA III',
        'ute gna iii': 'GNA III',
        'ute gna 3': 'GNA III',
        
        # MAUA
        'maua 3': 'MAUA 3',
        'maua iii': 'MAUA 3',
        'maua3': 'MAUA 3',
        'ute maua 3': 'MAUA 3',
        
        # ANGRA - IMPORTANTE: aceitar tanto romanos quanto números
        'angra 1': 'ANGRA 1',
        'angra i': 'ANGRA 1',
        'angra1': 'ANGRA 1',
        'angra 2': 'ANGRA 2',
        'angra ii': 'ANGRA 2',
        'angra2': 'ANGRA 2',
        
        # STA VITORIA
        'sta vitoria': 'STA VITORIA',
        'ute sta vi': 'STA VITORIA',
        'stavitoria': 'STA VITORIA',
        'santa vitoria': 'STA VITORIA',
        
        # CANDIOTA
        'candiota 3': 'CANDIOTA 3',
        'candiota_3': 'CANDIOTA 3',
        'candiota iii': 'CANDIOTA 3',
        'candiota3': 'CANDIOTA 3',
        
        # POTIGUAR
        'potiguar iii': 'POTIGUAR III',
        'potiguar 3': 'POTIGUAR III',
        'potiguar_3': 'POTIGUAR III',
        
        # PECEM
        'pecem ii': 'PECEM II',
        'pecem 2': 'PECEM II',
        'pecem2': 'PECEM II',
        'p. pecem ii': 'P. PECEM II',
        'p.pecem2': 'P. PECEM II',
        'p. pecem i': 'P. PECEM I',
        'p.pecem1': 'P. PECEM I',
        'p. pecem 1': 'P. PECEM I',
        'p. pecem 2': 'P. PECEM II',
        
        # PORTO ITAQUI
        'porto itaqui': 'PORTO ITAQUI',
        'p. itaqui': 'PORTO ITAQUI',
        'portoitaqui': 'PORTO ITAQUI',
        
        # PALMEIRAS
        'palmeiras go': 'PALMEIRAS GO',
        'palmeir_go': 'PALMEIRAS GO',
        'palmeirasgo': 'PALMEIRAS GO',
        
        # T. NORTE
        't. norte 2': 'T. NORTE 2',
        't norte 2': 'T. NORTE 2',
        'tnorte 2': 'T. NORTE 2',
        'tnorte2': 'T. NORTE 2',
        't. norte ii': 'T. NORTE 2',
        
        # ONCA PINTADA
        'onca pintada': 'ONCA PINTADA',
        'o.pintada': 'ONCA PINTADA',
        'oncapintada': 'ONCA PINTADA',
        
        # BAIXADA
        'baixada flu': 'BAIXADA FLU',
        'baixada fl': 'BAIXADA FLU',
        'baixadaflu': 'BAIXADA FLU',
        
        # MARLIM AZUL
        'marlim azul': 'MARLIM AZUL',
        'm.azul': 'MARLIM AZUL',
        'marlimazul': 'MARLIM AZUL',
        
        # BARCARENA
        'nt barcarena': 'NT BARCARENA',
        'barcarena': 'NT BARCARENA',
        'ntbarcarena': 'NT BARCARENA',
        
        # LINHARES PCS
        'linhares pcs': 'LINHARES PCS',
        'lorm_pcs': 'LINHARES PCS',
        'linharespcs': 'LINHARES PCS',
        
        # PAULINIA
        'paulinia ver': 'PAULINIA VER',
        'paulinia': 'PAULINIA VER',
        'pauliniaver': 'PAULINIA VER',
        
        # POVOACAO
        'povoacao 1': 'POVOACAO 1',
        'povoacao i': 'POVOACAO 1',
        'povoacao_mch': 'POVOACAO 1',
        'povoac i_f': 'POVOACAO 1',
        'povoacao1': 'POVOACAO 1',
        
        # VIANA
        'viana 1': 'VIANA 1',
        'viana i': 'VIANA 1',
        'viana i_f': 'VIANA 1',
        'viana_f': 'VIANA',
        'viana1': 'VIANA 1',
        
        # B. BONITA
        'b. bonita i': 'B. BONITA I',
        'b.bonita i': 'B. BONITA I',
        'b. bonita 1': 'B. BONITA I',
        'bbonita': 'B. BONITA I',
        
        # JAGUATIRI
        'jaguatiri ii': 'JAGUATIRI II',
        'jaguati ii': 'JAGUATIRI II',
        'jaguatiri 2': 'JAGUATIRI II',
        'jaguatiri2': 'JAGUATIRI II',
        
        # M.CRISTO SUC
        'm.cristo suc': 'M.CRISTO SUC',
        'm.c.sucuba': 'M.CRISTO SUC',
        'mcristo suc': 'M.CRISTO SUC',
        
        # PALMAPLAN
        'palmaplan 2': 'PALMAPLAN 2',
        'palmaplan': 'PALMAPLAN 2',
        'palmaplan ii': 'PALMAPLAN 2',
        
        # W. ARJONA
        'w. arjona': 'W. ARJONA',
        'w.arjona': 'W. ARJONA',
        'w.arjona o': 'W. ARJONA',
        'w.arjona_f': 'W. ARJONA',
        'warjona': 'W. ARJONA',
        
        # LORM / LINHARES
        'lorm_mch': 'LINHARES',
        'lorm': 'LINHARES',
        'linhares': 'LINHARES',
        
        # C. ROCHA / PORAQUE
        'c. rocha': 'C. ROCHA',
        'c.rocha': 'C. ROCHA',
        'poraque': 'C. ROCHA',
        'c. rocha_f': 'C. ROCHA',
        'crocha': 'C. ROCHA',
        
        # PONTA NEGRA
        'ponta negra': 'PONTA NEGRA',
        'ponta negr': 'PONTA NEGRA',
        'ponta ne_f': 'PONTA NEGRA',
        'pontanegra': 'PONTA NEGRA',
        
        # TERMOCEARA
        'termoceara': 'TERMOCEARA',
        'termocea_f': 'TERMOCEARA',
        
        # CUBATAO
        'cubatao': 'CUBATAO',
        'cubatao_f': 'CUBATAO',
        
        # TERMORIO
        'termorio': 'TERMORIO',
        'termorio_f': 'TERMORIO',
        
        # Sufixos _F (flexíveis) - outros
        'araucari_f': 'ARAUCARIA',
        'araucaria': 'ARAUCARIA',
        'norteflu_f': 'NORTEFLU',
        'norteflu': 'NORTEFLU',
        'seropedi_f': 'SEROPEDICA',
        'seropeda_f': 'SEROPEDICA',
        'seropedica': 'SEROPEDICA',
        'ibirite_f': 'IBIRITE',
        'ibirite': 'IBIRITE',
        'canoas_f': 'CANOAS',
        'canoas': 'CANOAS',
        'jaraqui_f': 'JARAQUI',
        'jaraqui': 'JARAQUI',
        'manauara_f': 'MANAUARA',
        'manauara': 'MANAUARA',
        'tambaqui_f': 'TAMBAQUI',
        'tambaqui': 'TAMBAQUI',
        'uruguaia_f': 'URUGUAIANA',
        'uruguaiana': 'URUGUAIANA',
    }
    
    @staticmethod
    def normalize_name(name: str) -> str:
        """
        Normaliza um nome de usina para uma forma canônica.
        
        Aplica transformações:
        1. Remove sufixos _F
        2. Remove prefixos "UTE "
        3. Normaliza espaços e underscores
        4. Consulta dicionário de mapeamentos
        
        NOTA: Não converte romanos para números aqui para manter consistência.
        A conversão é feita apenas no dicionário de mapeamentos.
        
        Args:
            name: Nome da usina (qualquer variante)
            
        Returns:
            Nome canônico normalizado
        """
        if not name or not name.strip():
            return name
        
        name_upper = name.strip().upper()
        
        # 1. Remover sufixos _F
        if name_upper.endswith('_F'):
            name_upper = name_upper[:-2].strip()
        
        # 2. Remover prefixo "UTE "
        if name_upper.startswith('UTE '):
            name_upper = name_upper[4:].strip()
        
        # 3. Normalizar espaços e underscores
        name_upper = re.sub(r'\s+', ' ', name_upper)  # Múltiplos espaços
        name_upper = name_upper.strip()
        
        # 4. Converter para chave de dicionário (lowercase para busca)
        name_key = name_upper.lower()
        name_key = re.sub(r'\s+', ' ', name_key).strip()
        
        # 5. Consultar dicionário
        if name_key in UsinaNameMatcher.NAME_VARIANTS:
            return UsinaNameMatcher.NAME_VARIANTS[name_key]
        
        # 6. Se não encontrou no dicionário, retornar normalizado (uppercase, espaços simples)
        return name_upper
    
    @staticmethod
    def _extract_usina_candidates(query: str) -> List[str]:
        """
        Extrai candidatos de nomes de usinas de uma query.
        Remove palavras comuns e retorna combinações de palavras.
        
        Args:
            query: Query do usuário (ex: "qual a disponibilidade de gna 2")
            
        Returns:
            Lista de candidatos de nomes (ex: ["gna 2", "gna", "2"])
        """
        query_lower = query.lower().strip()
        
        # Dividir em palavras e remover palavras comuns
        palavras = [p for p in query_lower.split() if p not in UsinaNameMatcher.PALAVRAS_IGNORAR and len(p) > 0]
        
        if not palavras:
            return [query_lower]
        
        candidatos = []
        
        # Gerar combinações de palavras (1 a 4 palavras consecutivas)
        for tamanho in range(min(4, len(palavras)), 0, -1):  # maior para menor
            for i in range(len(palavras) - tamanho + 1):
                candidato = ' '.join(palavras[i:i + tamanho])
                if candidato and len(candidato) > 1:
                    candidatos.append(candidato)
        
        # Adicionar a query original como último recurso
        if query_lower not in candidatos:
            candidatos.append(query_lower)
        
        return candidatos
    
    @staticmethod
    def find_match(
        query: str,
        available_names: List[str],
        threshold: float = 0.6
    ) -> Optional[Tuple[str, float]]:
        """
        Encontra o melhor match para uma query entre nomes disponíveis.
        
        Estratégia:
        1. Extrai candidatos de nomes da query (remove palavras comuns)
        2. Normaliza candidatos e nomes disponíveis
        3. Busca match exato após normalização
        4. Busca por substring
        5. Busca por similaridade fuzzy
        
        Args:
            query: Query do usuário (pode ser frase completa ou apenas nome)
            available_names: Lista de nomes disponíveis
            threshold: Threshold mínimo de similaridade (0.0 a 1.0)
            
        Returns:
            Tupla (nome_encontrado, score) ou None se não encontrou
        """
        if not query or not available_names:
            return None
        
        # Normalizar todos os nomes disponíveis
        normalized_map = {}
        for name in available_names:
            normalized = UsinaNameMatcher.normalize_name(name)
            normalized_lower = normalized.lower()
            normalized_map[normalized_lower] = name
        
        # Extrair candidatos de nomes da query
        candidatos = UsinaNameMatcher._extract_usina_candidates(query)
        
        # PRIORIDADE 1: Match exato de candidatos normalizados
        for candidato in candidatos:
            candidato_normalized = UsinaNameMatcher.normalize_name(candidato).lower()
            
            if candidato_normalized in normalized_map:
                return (normalized_map[candidato_normalized], 1.0)
        
        # PRIORIDADE 2: Buscar nome normalizado como substring na query
        # IMPORTANTE: Ordenar por tamanho (mais longo primeiro) para priorizar matches específicos
        query_lower = query.lower()
        matches_prioridade2 = []
        for normalized_key, original_name in normalized_map.items():
            # Se o nome normalizado está contido na query
            if len(normalized_key) >= 3 and normalized_key in query_lower:
                matches_prioridade2.append((len(normalized_key), original_name))
        
        # Retornar o match mais longo (mais específico)
        if matches_prioridade2:
            matches_prioridade2.sort(reverse=True)  # Ordenar por tamanho (maior primeiro)
            return (matches_prioridade2[0][1], 0.95)
        
        # PRIORIDADE 3: Buscar candidato como substring de nomes disponíveis
        for candidato in candidatos:
            candidato_normalized = UsinaNameMatcher.normalize_name(candidato).lower()
            
            for normalized_key, original_name in normalized_map.items():
                if candidato_normalized in normalized_key or normalized_key in candidato_normalized:
                    return (original_name, 0.9)
        
        # PRIORIDADE 4: Busca fuzzy com similaridade
        best_match = None
        best_score = 0.0
        
        for candidato in candidatos:
            candidato_normalized = UsinaNameMatcher.normalize_name(candidato).lower()
            
            for normalized_key, original_name in normalized_map.items():
                similarity = SequenceMatcher(None, candidato_normalized, normalized_key).ratio()
                
                # Bonus para palavras em comum
                candidato_words = set(candidato_normalized.split())
                name_words = set(normalized_key.split())
                common_words = candidato_words & name_words
                if common_words:
                    similarity += len(common_words) * 0.15
                
                if similarity > best_score and similarity >= threshold:
                    best_score = similarity
                    best_match = (original_name, similarity)
        
        return best_match
    
    @staticmethod
    def get_canonical_name(name: str) -> str:
        """
        Retorna o nome canônico de uma usina.
        
        Args:
            name: Nome da usina (qualquer variante)
            
        Returns:
            Nome canônico
        """
        return UsinaNameMatcher.normalize_name(name)


# Funções de conveniência para uso direto
def normalize_usina_name(name: str) -> str:
    """Normaliza um nome de usina."""
    return UsinaNameMatcher.normalize_name(name)


def find_usina_match(query: str, available_names: List[str], threshold: float = 0.6) -> Optional[Tuple[str, float]]:
    """Encontra match de usina."""
    return UsinaNameMatcher.find_match(query, available_names, threshold)
