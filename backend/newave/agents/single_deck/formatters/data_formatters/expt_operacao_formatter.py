"""
Formatter para ExptOperacaoTool no single deck.
Replica a formatação simplificada sem explicações, resumos, emojis ou estatísticas.
"""
from typing import Dict, Any, List
import pandas as pd
from backend.newave.agents.single_deck.formatters.base import SingleDeckFormatter
from backend.newave.agents.single_deck.formatters.text_formatters.simple import format_expt_operacao_simple


class ExptOperacaoSingleDeckFormatter(SingleDeckFormatter):
    """Formatter específico para ExptOperacaoTool."""
    
    def can_format(self, tool_name: str, result_structure: Dict[str, Any]) -> bool:
        """Verifica se pode formatar ExptOperacaoTool."""
        return tool_name == "ExptOperacaoTool" and "dados_expansoes" in result_structure
    
    def get_priority(self) -> int:
        """Prioridade média."""
        return 75
    
    def format_response(
        self,
        tool_result: Dict[str, Any],
        tool_name: str,
        query: str
    ) -> Dict[str, Any]:
        """Formata resposta de ExptOperacaoTool."""
        from backend.newave.config import safe_print
        
        dados_expansoes = tool_result.get("dados_expansoes", [])
        filtros = tool_result.get("filtros")
        
        safe_print(f"[EXPT FORMATTER] Dados recebidos: {len(dados_expansoes) if dados_expansoes else 0} registros")
        safe_print(f"[EXPT FORMATTER] Filtros: {filtros}")
        safe_print(f"[EXPT FORMATTER] Tool result keys: {list(tool_result.keys())}")
        safe_print(f"[EXPT FORMATTER] Success: {tool_result.get('success')}")
        
        if not dados_expansoes:
            safe_print(f"[EXPT FORMATTER] ⚠️ dados_expansoes está vazio ou None!")
            safe_print(f"[EXPT FORMATTER] Verificando se há dados em outros campos...")
            safe_print(f"[EXPT FORMATTER] desativacoes: {tool_result.get('desativacoes')}")
            safe_print(f"[EXPT FORMATTER] repotenciacoes: {tool_result.get('repotenciacoes')}")
            safe_print(f"[EXPT FORMATTER] indisponibilidades: {tool_result.get('indisponibilidades')}")
            nome_usina = "USINA"
            if filtros and 'usina' in filtros:
                nome_usina = filtros['usina'].get('nome', 'USINA')
            return {
                "final_response": f"## Dados de Operação Térmica - {nome_usina}\n\nNenhum dado encontrado.",
                "visualization_data": {
                    "table": [],
                    "tables_by_tipo": {},
                    "visualization_type": "expt_operacao",
                    "tool_name": "ExptOperacaoTool"
                }
            }
        
        # Dicionário de nomes e unidades para cada tipo
        tipos_info = {
            'GTMIN': {
                'nome': 'Geração Térmica Mínima (GTMIN)',
                'unidade': 'MW'
            },
            'IPTER': {
                'nome': 'Indisponibilidade Programada (IPTER)',
                'unidade': '%'
            },
            'POTEF': {
                'nome': 'Potência Efetiva (POTEF)',
                'unidade': 'MW'
            },
            'TEIFT': {
                'nome': 'Taxa Equivalente de Indisponibilidade Forçada (TEIFT)',
                'unidade': '%'
            },
            'FCMAX': {
                'nome': 'Fator de Capacidade Máximo (FCMAX)',
                'unidade': '%'
            }
        }
        
        # Ordem de exibição dos tipos
        ordem_tipos = ['GTMIN', 'IPTER', 'POTEF', 'TEIFT', 'FCMAX']
        
        # Agrupar por tipo de modificação
        if not dados_expansoes:
            safe_print(f"[EXPT FORMATTER] ⚠️ dados_expansoes está vazio!")
            df_expansoes = pd.DataFrame()
            tipos_presentes = []
        else:
            df_expansoes = pd.DataFrame(dados_expansoes)
            tipos_presentes = df_expansoes['tipo'].unique() if 'tipo' in df_expansoes.columns else []
            safe_print(f"[EXPT FORMATTER] ✅ DataFrame criado: {len(df_expansoes)} registros, tipos: {tipos_presentes}")
        
        # Obter nome da usina dos filtros (prioridade máxima - sempre usar se disponível)
        nome_usina_fallback = None
        if filtros and 'usina' in filtros:
            nome_usina_fallback = filtros['usina'].get('nome', None)
            safe_print(f"[EXPT FORMATTER] Nome usina dos filtros: {nome_usina_fallback}")
        
        # Criar tabelas separadas por tipo de modificação
        tables_by_tipo: Dict[str, List[Dict[str, Any]]] = {}
        
        for tipo in ordem_tipos:
            if tipo not in tipos_presentes:
                continue
            
            df_tipo = df_expansoes[df_expansoes['tipo'] == tipo]
            tipo_info = tipos_info.get(tipo, {
                'nome': tipo,
                'unidade': ''
            })
            
            # Processar e limpar dados para cada tipo
            table_data = []
            for _, record in df_tipo.iterrows():
                codigo = record.get('codigo_usina', 'N/A')
                
                # Prioridade: 1) Nome dos filtros, 2) Nome do registro, 3) Fallback
                nome = None
                
                # Prioridade 1: Usar nome dos filtros se disponível
                if nome_usina_fallback:
                    nome = nome_usina_fallback
                else:
                    # Prioridade 2: Tentar obter nome_usina do registro
                    nome_registro = record.get('nome_usina', '')
                    if nome_registro and not pd.isna(nome_registro):
                        nome_str = str(nome_registro).strip()
                        if nome_str and nome_str.lower() != 'nan' and nome_str != '':
                            nome = nome_str
                
                # Prioridade 3: Fallback
                if not nome:
                    nome = f'Usina {codigo}' if codigo != 'N/A' else 'N/A'
                
                safe_print(f"[EXPT FORMATTER] Registro {codigo}: nome_usina = '{nome}'")
                
                modificacao = record.get('modificacao', 0)
                inicio = record.get('data_inicio', 'N/A')
                fim = record.get('data_fim', 'N/A')
                
                # Formatar datas
                if isinstance(inicio, str) and 'T' in inicio:
                    inicio = inicio.split('T')[0]
                elif hasattr(inicio, 'date'):
                    inicio = inicio.date()
                if isinstance(fim, str) and 'T' in fim:
                    fim = fim.split('T')[0]
                elif hasattr(fim, 'date'):
                    fim = fim.date()
                elif pd.isna(fim):
                    fim = 'Até o final'
                
                # Criar registro limpo
                registro_limpo = {
                    'codigo_usina': codigo,
                    'nome_usina': nome,
                    'tipo': tipo,
                    'modificacao': modificacao,
                    'valor_formatado': f"{modificacao:,.2f} {tipo_info['unidade']}" if tipo_info['unidade'] else f"{modificacao:,.2f}",
                    'data_inicio': str(inicio),
                    'data_fim': str(fim)
                }
                table_data.append(registro_limpo)
            
            tables_by_tipo[tipo] = table_data
        
        # Criar tabela única para compatibilidade (todas as tabelas concatenadas)
        table_data = []
        for tipo in ordem_tipos:
            if tipo in tables_by_tipo:
                table_data.extend(tables_by_tipo[tipo])
        
        # Criar título descritivo
        nome_usina = "USINA"
        if filtros and 'usina' in filtros:
            nome_usina = filtros['usina'].get('nome', 'USINA')
        titulo = f"Dados de Operação Térmica - {nome_usina}"
        
        final_response = format_expt_operacao_simple(
            tables_by_tipo,
            filtros,
            titulo
        )
        
        return {
            "final_response": final_response,
            "visualization_data": {
                "table": table_data,
                "tables_by_tipo": tables_by_tipo,
                "tipos_info": tipos_info,
                "ordem_tipos": ordem_tipos,
                "filtros": filtros,
                "visualization_type": "expt_operacao",
                "tool_name": "ExptOperacaoTool"
            }
        }
