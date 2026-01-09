"""
Tool para análise de variação de volumes iniciais entre decks no modo multideck.
Foca especificamente em identificar e comparar variações de volume_inicial_percentual do CONFHD.DAT entre dezembro e janeiro.
"""
from app.tools.base import NEWAVETool
from inewave.newave import Confhd
import os
import pandas as pd
from typing import Dict, Any, List, Optional
from app.utils.deck_loader import get_december_deck_path, get_january_deck_path


class VariacaoVolumesIniciaisTool(NEWAVETool):
    """
    Tool especializada para análise de variação de volumes iniciais entre decks.
    
    Funcionalidades:
    - Lista todas as mudanças de volume_inicial_percentual entre os dois decks
    - Identifica mudanças (variações de valor, novas usinas, remoções)
    - Ordena mudanças por magnitude
    - Agrupa por REE
    - Retorna apenas as mudanças (não todos os registros)
    """
    
    def get_name(self) -> str:
        return "VariacaoVolumesIniciaisTool"
    
    def can_handle(self, query: str) -> bool:
        """
        Verifica se a query é sobre análise de variação de volumes iniciais.
        
        Args:
            query: Query do usuário
            
        Returns:
            True se a tool pode processar a query
        """
        query_lower = query.lower()
        keywords = [
            "variação volume inicial",
            "variacao volume inicial",
            "mudanças volume inicial",
            "mudancas volume inicial",
            "análise volume inicial",
            "analise volume inicial",
            "reservatórios iniciais",
            "reservatorios iniciais",
            "volume inicial percentual",
            "comparar volumes iniciais",
        ]
        return any(kw in query_lower for kw in keywords)
    
    def execute(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Executa a análise de variação de volumes iniciais entre os dois decks.
        
        Fluxo:
        1. Carrega caminhos dos decks de dezembro e janeiro
        2. Lê CONFHD.DAT de ambos os decks
        3. Compara volume_inicial_percentual por usina
        4. Identifica mudanças
        5. Ordena mudanças por magnitude
        6. Retorna dados formatados
        """
        print(f"[TOOL] {self.get_name()}: Iniciando análise de variação de volumes iniciais...")
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
            
            # ETAPA 2: Ler CONFHD.DAT de ambos os decks
            print("[TOOL] ETAPA 2: Lendo arquivos CONFHD.DAT...")
            confhd_dec = self._read_confhd_file(deck_december_path)
            confhd_jan = self._read_confhd_file(deck_january_path)
            
            if confhd_dec is None:
                return {
                    "success": False,
                    "error": f"Arquivo CONFHD.DAT não encontrado em {deck_december_path}",
                    "tool": self.get_name()
                }
            
            if confhd_jan is None:
                return {
                    "success": False,
                    "error": f"Arquivo CONFHD.DAT não encontrado em {deck_january_path}",
                    "tool": self.get_name()
                }
            
            # ETAPA 3: Extrair DataFrames de usinas
            print("[TOOL] ETAPA 3: Extraindo dados de usinas...")
            usinas_dec = confhd_dec.usinas
            usinas_jan = confhd_jan.usinas
            
            if usinas_dec is None or usinas_dec.empty:
                return {
                    "success": False,
                    "error": f"Nenhuma usina encontrada no CONFHD.DAT de dezembro",
                    "tool": self.get_name()
                }
            
            if usinas_jan is None or usinas_jan.empty:
                return {
                    "success": False,
                    "error": f"Nenhuma usina encontrada no CONFHD.DAT de janeiro",
                    "tool": self.get_name()
                }
            
            print(f"[TOOL] ✅ Usinas Dezembro: {len(usinas_dec)}")
            print(f"[TOOL] ✅ Usinas Janeiro: {len(usinas_jan)}")
            
            # ETAPA 4: Comparar e identificar mudanças
            print("[TOOL] ETAPA 4: Identificando mudanças...")
            mudancas = self._identify_changes(usinas_dec, usinas_jan, deck_december_name, deck_january_name)
            
            print(f"[TOOL] ✅ Total de mudanças identificadas: {len(mudancas)}")
            
            # ETAPA 5: Ordenar por tipo e magnitude
            print("[TOOL] ETAPA 5: Ordenando mudanças por tipo e magnitude...")
            ordem_tipo = {"aumento": 0, "reducao": 1, "remocao": 2, "novo": 3}
            mudancas_ordenadas = sorted(mudancas, key=lambda x: (
                ordem_tipo.get(x.get('tipo_mudanca', 'N/A'), 99),
                -abs(x.get('magnitude_mudanca', 0))  # Maior magnitude primeiro dentro do mesmo tipo
            ))
            
            # ETAPA 6: Calcular estatísticas
            stats = self._calculate_stats(usinas_dec, usinas_jan, mudancas)
            
            # ETAPA 7: Formatar tabela de comparação
            comparison_table = []
            for mudanca in mudancas_ordenadas:
                comparison_table.append({
                    "codigo_usina": mudanca.get("codigo_usina"),
                    "nome_usina": mudanca.get("nome_usina", "N/A"),
                    "ree": mudanca.get("ree"),
                    "tipo_mudanca": mudanca.get("tipo_mudanca"),
                    "volume_dezembro": mudanca.get("volume_dezembro"),
                    "volume_janeiro": mudanca.get("volume_janeiro"),
                    "diferenca": mudanca.get("diferenca"),
                    "magnitude_mudanca": round(mudanca.get("magnitude_mudanca", 0), 2),
                    "diferenca_percentual": mudanca.get("diferenca_percentual")
                })
            
            return {
                "success": True,
                "is_comparison": True,
                "tool": self.get_name(),
                "comparison_table": comparison_table,
                "stats": stats,
                "description": f"Análise de {len(mudancas_ordenadas)} mudanças de volume inicial entre {deck_december_name} e {deck_january_name}, ordenadas por magnitude."
            }
            
        except Exception as e:
            print(f"[TOOL] ❌ Erro ao processar: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": f"Erro ao processar análise de volumes iniciais: {str(e)}",
                "error_type": type(e).__name__,
                "tool": self.get_name()
            }
    
    def _read_confhd_file(self, deck_path) -> Optional[Confhd]:
        """
        Lê o arquivo CONFHD.DAT de um deck.
        
        Args:
            deck_path: Caminho do diretório do deck
            
        Returns:
            Objeto Confhd ou None se não encontrado
        """
        confhd_path = os.path.join(deck_path, "CONFHD.DAT")
        if not os.path.exists(confhd_path):
            confhd_path_lower = os.path.join(deck_path, "confhd.dat")
            if os.path.exists(confhd_path_lower):
                confhd_path = confhd_path_lower
            else:
                print(f"[TOOL] ⚠️ Arquivo CONFHD.DAT não encontrado em {deck_path}")
                return None
        
        try:
            confhd = Confhd.read(confhd_path)
            return confhd
        except Exception as e:
            print(f"[TOOL] ❌ Erro ao ler CONFHD.DAT: {e}")
            return None
    
    def _identify_changes(
        self,
        usinas_dec: pd.DataFrame,
        usinas_jan: pd.DataFrame,
        deck_dec_name: str,
        deck_jan_name: str
    ) -> List[Dict[str, Any]]:
        """
        Identifica mudanças de volume_inicial_percentual entre os dois decks.
        
        Uma mudança é identificada quando:
        - Uma usina tem volume diferente entre os decks
        - Uma usina existe em um deck mas não no outro
        
        Args:
            usinas_dec: DataFrame com usinas de dezembro
            usinas_jan: DataFrame com usinas de janeiro
            deck_dec_name: Nome do deck de dezembro
            deck_jan_name: Nome do deck de janeiro
            
        Returns:
            Lista de dicionários com informações sobre mudanças
        """
        mudancas = []
        TOLERANCIA = 0.1  # 0.1% de tolerância
        
        # Criar índices por código de usina
        dec_indexed = {}
        for _, row in usinas_dec.iterrows():
            codigo = int(row.get('codigo_usina', 0))
            if codigo > 0:
                dec_indexed[codigo] = row
        
        jan_indexed = {}
        for _, row in usinas_jan.iterrows():
            codigo = int(row.get('codigo_usina', 0))
            if codigo > 0:
                jan_indexed[codigo] = row
        
        # Comparar todas as usinas (presentes em qualquer um dos decks)
        all_codigos = set(dec_indexed.keys()) | set(jan_indexed.keys())
        
        for codigo_usina in all_codigos:
            dec_record = dec_indexed.get(codigo_usina)
            jan_record = jan_indexed.get(codigo_usina)
            
            # Obter nome da usina
            nome_usina = None
            if dec_record is not None:
                nome_temp = str(dec_record.get('nome_usina', '')).strip()
                if nome_temp and nome_temp != 'nan' and nome_temp.lower() != 'none' and nome_temp != '' and not pd.isna(dec_record.get('nome_usina')):
                    nome_usina = nome_temp
            
            if (not nome_usina or nome_usina.strip() == '') and jan_record is not None:
                nome_temp = str(jan_record.get('nome_usina', '')).strip()
                if nome_temp and nome_temp != 'nan' and nome_temp.lower() != 'none' and nome_temp != '' and not pd.isna(jan_record.get('nome_usina')):
                    nome_usina = nome_temp
            
            if not nome_usina or nome_usina.strip() == '':
                nome_usina = f'Usina {codigo_usina}'
            
            # Obter REE
            ree = None
            if dec_record is not None:
                ree = int(dec_record.get('ree', 0)) if pd.notna(dec_record.get('ree')) else None
            if ree is None and jan_record is not None:
                ree = int(jan_record.get('ree', 0)) if pd.notna(jan_record.get('ree')) else None
            
            # Extrair volumes iniciais
            volume_dec = self._sanitize_number(dec_record.get('volume_inicial_percentual') if dec_record is not None else None)
            volume_jan = self._sanitize_number(jan_record.get('volume_inicial_percentual') if jan_record is not None else None)
            
            # Tratar valores nulos como 0%
            if volume_dec is None:
                volume_dec = 0.0
            if volume_jan is None:
                volume_jan = 0.0
            
            # Identificar tipo de mudança
            tipo_mudanca = None
            magnitude_mudanca = 0.0
            diferenca = 0.0
            diferenca_percentual = None
            
            if dec_record is None and jan_record is not None:
                # Nova usina em janeiro
                if abs(volume_jan) > TOLERANCIA:
                    tipo_mudanca = "novo"
                    magnitude_mudanca = abs(volume_jan)
                    diferenca = volume_jan
            elif dec_record is not None and jan_record is None:
                # Usina removida em janeiro
                if abs(volume_dec) > TOLERANCIA:
                    tipo_mudanca = "remocao"
                    magnitude_mudanca = abs(volume_dec)
                    diferenca = -volume_dec
            elif dec_record is not None and jan_record is not None:
                # Usina existe em ambos - verificar se volume mudou
                diferenca = volume_jan - volume_dec
                if abs(diferenca) > TOLERANCIA:
                    if diferenca > 0:
                        tipo_mudanca = "aumento"
                    else:
                        tipo_mudanca = "reducao"
                    magnitude_mudanca = abs(diferenca)
                    
                    # Calcular diferença percentual
                    if abs(volume_dec) > 0.01:
                        diferenca_percentual = (diferenca / abs(volume_dec)) * 100
                    elif abs(volume_jan) > 0.01:
                        diferenca_percentual = (diferenca / abs(volume_jan)) * 100
            
            # Se há mudança, adicionar à lista
            if tipo_mudanca is not None:
                mudanca = {
                    "codigo_usina": int(codigo_usina),
                    "nome_usina": str(nome_usina).strip(),
                    "ree": ree,
                    "tipo_mudanca": tipo_mudanca,
                    "volume_dezembro": round(volume_dec, 2) if volume_dec is not None else None,
                    "volume_janeiro": round(volume_jan, 2) if volume_jan is not None else None,
                    "diferenca": round(diferenca, 2),
                    "magnitude_mudanca": round(magnitude_mudanca, 2),
                    "diferenca_percentual": round(diferenca_percentual, 2) if diferenca_percentual is not None else None
                }
                mudancas.append(mudanca)
        
        return mudancas
    
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
        usinas_dec: pd.DataFrame,
        usinas_jan: pd.DataFrame,
        mudancas: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calcula estatísticas sobre as usinas e mudanças.
        
        Args:
            usinas_dec: DataFrame com usinas de dezembro
            usinas_jan: DataFrame com usinas de janeiro
            mudancas: Lista de mudanças identificadas
            
        Returns:
            Dicionário com estatísticas
        """
        stats = {
            "total_usinas_dezembro": len(usinas_dec),
            "total_usinas_janeiro": len(usinas_jan),
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
        
        # Mudanças por REE
        mudancas_por_ree = {}
        for mudanca in mudancas:
            ree = mudanca.get('ree')
            if ree is not None:
                mudancas_por_ree[ree] = mudancas_por_ree.get(ree, 0) + 1
        stats["mudancas_por_ree"] = mudancas_por_ree
        
        return stats
    
    def get_description(self) -> str:
        """
        Retorna descrição da tool para uso pelo LLM.
        
        Returns:
            String com descrição detalhada
        """
        return """
        Variação de volumes iniciais. Análise de variações de volume_inicial_percentual entre decks no modo multideck.
        
        Esta tool é especializada em:
        - Identificar todas as mudanças de volume inicial entre dezembro e janeiro
        - Ordenar mudanças por magnitude (maior variação primeiro)
        - Classificar tipos de mudança (aumento, reducao, novo, remocao)
        - Agrupar por REE
        - Retornar apenas as mudanças (não todos os registros)
        
        Queries que ativam esta tool:
        - "variação volume inicial" ou "variacao volume inicial"
        - "mudanças volume inicial" ou "mudancas volume inicial"
        - "análise volume inicial" ou "analise volume inicial"
        - "reservatórios iniciais" ou "reservatorios iniciais"
        - "volume inicial percentual"
        - "comparar volumes iniciais"
        
        Termos-chave: variação volume inicial, variacao volume inicial, mudanças volume inicial, mudancas volume inicial, análise volume inicial, analise volume inicial, reservatórios iniciais, reservatorios iniciais, volume inicial percentual, comparar volumes iniciais.
        """
