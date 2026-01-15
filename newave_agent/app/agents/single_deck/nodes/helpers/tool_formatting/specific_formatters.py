"""
Formatadores específicos para cada tipo de tool.
"""

from typing import Dict, Any, Optional
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import base64
import io
from app.config import safe_print
from app.utils.text_utils import clean_response_text


def format_carga_mensal_response(tool_result: dict, tool_used: str) -> dict:
    
    # Extrair dados
    data = tool_result.get("data", [])
    summary = tool_result.get("summary", {})
    stats = tool_result.get("stats_por_submercado", [])
    # IMPORTANTE: NÃO usar aggregated (dados agregados anuais)
    # Os dados devem ser apresentados mês a mês, não agregados por ano
    
    # Construir resposta em Markdown
    response_parts = []
    
    # Cabeçalho
    filtro_info = summary.get('filtro_aplicado') if summary else None
    
    if filtro_info and filtro_info.get('filtrado'):
        nome_sub = filtro_info.get('nome_submercado', f"Subsistema {filtro_info.get('codigo_submercado')}")
        response_parts.append(f"## ✅ Dados de Carga Mensal - {nome_sub}\n\n")
        response_parts.append(f"*Filtrado para: **{nome_sub}** (Código: {filtro_info.get('codigo_submercado')})*\n")
    else:
        response_parts.append(f"## ✅ Dados de Carga Mensal por Submercado\n\n")
    
    response_parts.append(f"*Processado pela tool: **{tool_used}***\n\n")
    
    # Resumo
    if summary:
        response_parts.append("###  Resumo\n\n")
        response_parts.append(f"- **Total de registros**: {summary.get('total_registros', 0):,}\n")
        
        if filtro_info and filtro_info.get('filtrado'):
            nome_filtrado = filtro_info.get('nome_submercado') or f"Subsistema {filtro_info.get('codigo_submercado')}"
            codigo_filtrado = filtro_info.get('codigo_submercado')
            response_parts.append(f"- **Submercado filtrado**: {nome_filtrado} (Código: {codigo_filtrado})\n")
        else:
            response_parts.append(f"- **Submercados**: {', '.join(map(str, summary.get('submercados', [])))}\n")
        
        response_parts.append(f"- **Período**: {summary.get('periodo', 'N/A')}\n")
        response_parts.append(f"- **Anos**: {', '.join(map(str, summary.get('anos', [])))}\n\n")
    
    # Estatísticas por submercado
    if stats:
        response_parts.append("### 📈 Estatísticas por Submercado\n\n")
        response_parts.append("| Submercado | Registros | Média (MWmédio) | Mínimo | Máximo | Total |\n")
        response_parts.append("|------------|-----------|-----------------|--------|--------|-------|\n")
        
        for stat in stats:
            sub = stat.get('codigo_submercado', 'N/A')
            total = stat.get('total_registros', 0)
            media = stat.get('carga_media_mwmed', 0)
            minimo = stat.get('carga_min_mwmed', 0)
            maximo = stat.get('carga_max_mwmed', 0)
            total_sum = stat.get('carga_total_mwmed', 0)
            
            response_parts.append(
                f"| {sub} | {total} | {media:,.2f} | {minimo:,.2f} | {maximo:,.2f} | {total_sum:,.2f} |\n"
            )
        response_parts.append("\n")
    
    # Agregação anual
    # IMPORTANTE: NÃO mostrar dados agregados anuais
    # Os dados de carga mensal devem ser apresentados mês a mês, não agregados por ano
    # A seção de dados agregados foi removida para evitar que o LLM use valores anuais
    
    # Dados mensais detalhados
    if data:
        response_parts.append("### 📋 Dados Detalhados\n\n")
        response_parts.append(f"*Total de {len(data)} registros disponíveis*\n\n")
        
        # Mostrar todos os dados ou uma amostra se for muito grande para exibição
        # Mas todos os dados estarão disponíveis no JSON
        if len(data) > 100:
            response_parts.append("*Exibindo primeiros 100 registros. Todos os dados estão disponíveis no JSON para download.*\n\n")
            sample = data[:100]
        else:
            sample = data
        if sample:
            # Pegar colunas principais
            cols = ['codigo_submercado', 'ano', 'mes', 'valor']
            available_cols = [col for col in cols if col in sample[0]]
            
            if available_cols:
                response_parts.append("| " + " | ".join(available_cols) + " |\n")
                response_parts.append("|" + "|".join(["---"] * len(available_cols)) + "|\n")
                
                for record in sample:
                    row = [str(record.get(col, '')) for col in available_cols]
                    response_parts.append("| " + " | ".join(row) + " |\n")
                
                if len(data) > len(sample):
                    response_parts.append(f"\n*Exibindo {len(sample)} de {len(data)} registros. Todos os dados estão disponíveis no JSON.*\n")
                else:
                    response_parts.append(f"\n*Todos os {len(data)} registros exibidos acima.*\n")
                response_parts.append("\n")
    
    response_parts.append("---\n\n")
    response_parts.append("*Dados processados diretamente do arquivo SISTEMA.DAT usando tool pré-programada.*\n")
    
    response_text = "".join(response_parts)
    response_text = clean_response_text(response_text, max_emojis=2)
    return {"final_response": response_text}


def generate_cvu_chart(dados_estruturais: list, classe_nome: str = None) -> Optional[str]:
    """
    Gera um gráfico de CVU (Custo Variável Unitário) por ano.
    
    Args:
        dados_estruturais: Lista de dicionários com dados estruturais
        classe_nome: Nome da classe (opcional, para título)
        
    Returns:
        String base64 da imagem do gráfico ou None se não for possível gerar
    """
    try:
        if not dados_estruturais:
            return None
        
        df = pd.DataFrame(dados_estruturais)
        
        # Verificar se tem as colunas necessárias
        if 'indice_ano_estudo' not in df.columns or 'valor' not in df.columns:
            return None
        
        # Se há múltiplas classes, usar apenas a primeira (ou agrupar)
        if 'codigo_usina' in df.columns:
            codigos_unicos = df['codigo_usina'].unique()
            if len(codigos_unicos) == 1:
                # Uma única classe - usar todos os dados
                df_plot = df.copy()
                if classe_nome is None and 'nome_usina' in df.columns:
                    classe_nome = df['nome_usina'].iloc[0]
            else:
                # Múltiplas classes - usar a primeira ou fazer gráfico separado por classe
                # Por enquanto, usar a primeira classe
                primeiro_codigo = codigos_unicos[0]
                df_plot = df[df['codigo_usina'] == primeiro_codigo].copy()
                if classe_nome is None and 'nome_usina' in df_plot.columns:
                    classe_nome = df_plot['nome_usina'].iloc[0]
        else:
            df_plot = df.copy()
        
        # Agrupar por ano e pegar o valor (se houver múltiplos valores por ano, usar o primeiro)
        df_plot = df_plot.sort_values('indice_ano_estudo')
        anos = df_plot['indice_ano_estudo'].tolist()
        custos = df_plot['valor'].tolist()
        
        if not anos or not custos:
            return None
        
        # Criar gráfico (linha reta, sem suavização)
        plt.figure(figsize=(10, 6))
        plt.plot(anos, custos, marker='o', linewidth=2, markersize=8)  # Linha linear, sem interpolação
        plt.xlabel('Ano', fontsize=12, fontweight='bold')
        plt.ylabel('CVU ($/MWh)', fontsize=12, fontweight='bold')
        
        if classe_nome:
            plt.title(f'Custo Variável Unitário (CVU) - {classe_nome}', fontsize=14, fontweight='bold')
        else:
            plt.title('Custo Variável Unitário (CVU)', fontsize=14, fontweight='bold')
        
        plt.grid(True, alpha=0.3, linestyle='--')
        plt.xticks(anos, rotation=45)
        
        # Adicionar valores nos pontos
        for i, (ano, custo) in enumerate(zip(anos, custos)):
            plt.annotate(f'{custo:,.2f}', (ano, custo), 
                        textcoords="offset points", xytext=(0,10), ha='center', fontsize=9)
        
        plt.tight_layout()
        
        # Converter para base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
        plt.close()
        
        return image_base64
        
    except Exception as e:
        safe_print(f"[INTERPRETER] ⚠️ Erro ao gerar gráfico CVU: {e}")
        import traceback
        traceback.print_exc()
        return None


def is_cvu_query(query: str) -> bool:
    """
    Verifica se a query é sobre CVU (Custo Variável Unitário).
    
    Args:
        query: Query do usuário
        
    Returns:
        True se for uma query de CVU
    """
    query_lower = query.lower()
    cvu_keywords = [
        "cvu",
        "custo variável unitário",
        "custo variavel unitario",
        "custo variável unitario",
        "custo variavel unitário",
    ]
    return any(kw in query_lower for kw in cvu_keywords)


def format_clast_valores_response(tool_result: dict, tool_used: str, query: str = "") -> dict:
    """
    Formata o resultado da ClastValoresTool em resposta Markdown.
    
    Args:
        tool_result: Resultado da execução da tool
        tool_used: Nome da tool usada
        
    Returns:
        Dict com final_response formatado
    """
    response_parts = []
    
    # Cabeçalho
    tipo_solicitado = tool_result.get("tipo_solicitado", "ambos")
    filtros = tool_result.get("filtros")
    
    if tipo_solicitado == "estrutural":
        response_parts.append("## ✅ Valores Estruturais do CLAST.DAT\n\n")
    elif tipo_solicitado == "conjuntural":
        response_parts.append("## ✅ Valores Conjunturais do CLAST.DAT\n\n")
    else:
        response_parts.append("## ✅ Valores Estruturais e Conjunturais do CLAST.DAT\n\n")
    
    response_parts.append(f"*Processado pela tool: **{tool_used}***\n\n")
    
    # Informações sobre filtros
    if filtros:
        if 'classe' in filtros:
            classe_info = filtros['classe']
            response_parts.append(f"### 🔍 Filtros Aplicados\n\n")
            response_parts.append(f"- **Classe**: {classe_info.get('nome')} (Código: {classe_info.get('codigo')})\n")
            response_parts.append(f"- **Tipo de Combustível**: {classe_info.get('tipo_combustivel')}\n\n")
        if 'tipo_combustivel' in filtros:
            response_parts.append(f"- **Tipo de Combustível**: {filtros['tipo_combustivel']}\n\n")
    
    # Valores estruturais
    dados_estruturais = tool_result.get("dados_estruturais")
    stats_estrutural = tool_result.get("stats_estrutural")
    
    if dados_estruturais is not None:
        response_parts.append("###  Valores Estruturais (Custos Base)\n\n")
        
        if stats_estrutural:
            response_parts.append(f"- **Total de classes**: {stats_estrutural.get('total_classes', 0)}\n")
            response_parts.append(f"- **Total de registros**: {stats_estrutural.get('total_registros', 0):,}\n")
            response_parts.append(f"- **Anos cobertos**: {', '.join(map(str, stats_estrutural.get('anos_cobertos', [])))}\n")
            response_parts.append(f"- **Custo médio**: {stats_estrutural.get('custo_medio', 0):,.2f} $/MWh\n")
            response_parts.append(f"- **Custo mínimo**: {stats_estrutural.get('custo_min', 0):,.2f} $/MWh\n")
            response_parts.append(f"- **Custo máximo**: {stats_estrutural.get('custo_max', 0):,.2f} $/MWh\n\n")
            
            # Estatísticas por tipo de combustível
            if 'stats_por_tipo' in stats_estrutural:
                response_parts.append("#### 📈 Estatísticas por Tipo de Combustível\n\n")
                response_parts.append("| Tipo | Classes | Custo Médio ($/MWh) | Mínimo | Máximo |\n")
                response_parts.append("|------|---------|---------------------|--------|--------|\n")
                
                for stat in stats_estrutural['stats_por_tipo']:
                    tipo = stat.get('tipo_combustivel', 'N/A')
                    classes = stat.get('total_classes', 0)
                    medio = stat.get('custo_medio', 0)
                    minimo = stat.get('custo_min', 0)
                    maximo = stat.get('custo_max', 0)
                    
                    response_parts.append(
                        f"| {tipo} | {classes} | {medio:,.2f} | {minimo:,.2f} | {maximo:,.2f} |\n"
                    )
                response_parts.append("\n")
        
        # Tabela de dados estruturais
        if dados_estruturais:
            # Verificar se é query de CVU para gerar gráfico
            is_cvu = is_cvu_query(query)
            classe_nome_grafico = None
            if filtros and 'classe' in filtros:
                classe_nome_grafico = filtros['classe'].get('nome')
            
            # Gerar gráfico se for CVU
            chart_base64 = None
            if is_cvu:
                chart_base64 = generate_cvu_chart(dados_estruturais, classe_nome_grafico)
                if chart_base64:
                    response_parts.append("#### 📈 Gráfico de CVU por Ano\n\n")
                    response_parts.append(f"![Gráfico CVU](data:image/png;base64,{chart_base64})\n\n")
            
            response_parts.append("#### 📋 Dados Estruturais Detalhados\n\n")
            
            # Criar tabela pivotada por classe e ano
            df_est = pd.DataFrame(dados_estruturais)
            
            if len(df_est) > 0 and 'codigo_usina' in df_est.columns and 'indice_ano_estudo' in df_est.columns:
                # Agrupar por classe
                classes_unicas = df_est[['codigo_usina', 'nome_usina', 'tipo_combustivel']].drop_duplicates()
                
                response_parts.append("| Código | Nome Classe | Tipo Combustível | ")
                anos = sorted(df_est['indice_ano_estudo'].unique())
                for ano in anos:
                    response_parts.append(f"Ano {ano} | ")
                response_parts.append("\n")
                response_parts.append("|--------|-------------|------------------|")
                for ano in anos:
                    response_parts.append("--------|")
                response_parts.append("\n")
                
                for _, classe_row in classes_unicas.iterrows():
                    codigo = classe_row['codigo_usina']
                    nome = classe_row['nome_usina']
                    tipo = classe_row['tipo_combustivel']
                    
                    response_parts.append(f"| {codigo} | {nome} | {tipo} | ")
                    
                    for ano in anos:
                        custo_row = df_est[(df_est['codigo_usina'] == codigo) & 
                                          (df_est['indice_ano_estudo'] == ano)]
                        if not custo_row.empty:
                            custo = custo_row.iloc[0].get('valor', 0)
                            response_parts.append(f"{custo:,.2f} | ")
                        else:
                            response_parts.append("- | ")
                    
                    response_parts.append("\n")
                
                response_parts.append("\n")
            else:
                response_parts.append(f"*Total de {len(dados_estruturais)} registros disponíveis no JSON*\n\n")
    
    # Valores conjunturais
    dados_conjunturais = tool_result.get("dados_conjunturais")
    stats_conjuntural = tool_result.get("stats_conjuntural")
    
    if dados_conjunturais is not None:
        response_parts.append("### 🔄 Valores Conjunturais (Modificações Sazonais)\n\n")
        
        if stats_conjuntural:
            response_parts.append(f"- **Total de modificações**: {stats_conjuntural.get('total_modificacoes', 0)}\n")
            response_parts.append(f"- **Classes afetadas**: {stats_conjuntural.get('classes_afetadas', 0)}\n")
            response_parts.append(f"- **Custo médio**: {stats_conjuntural.get('custo_medio', 0):,.2f} $/MWh\n")
            response_parts.append(f"- **Custo mínimo**: {stats_conjuntural.get('custo_min', 0):,.2f} $/MWh\n")
            response_parts.append(f"- **Custo máximo**: {stats_conjuntural.get('custo_max', 0):,.2f} $/MWh\n\n")
        
        # Tabela de modificações
        if dados_conjunturais:
            response_parts.append("#### 📋 Modificações Sazonais\n\n")
            response_parts.append("| Código | Nome Classe | Data Início | Data Fim | Custo ($/MWh) |\n")
            response_parts.append("|--------|-------------|-------------|----------|---------------|\n")
            
            for modif in dados_conjunturais[:50]:  # Limitar exibição a 50
                codigo = modif.get('codigo_usina', 'N/A')
                nome = modif.get('nome_usina', 'N/A')
                inicio = modif.get('data_inicio', 'N/A')
                fim = modif.get('data_fim', 'N/A')
                custo = modif.get('custo', 0)
                
                # Formatar datas
                if isinstance(inicio, str) and 'T' in inicio:
                    inicio = inicio.split('T')[0]
                if isinstance(fim, str) and 'T' in fim:
                    fim = fim.split('T')[0]
                
                response_parts.append(f"| {codigo} | {nome} | {inicio} | {fim} | {custo:,.2f} |\n")
            
            if len(dados_conjunturais) > 50:
                response_parts.append(f"\n*Exibindo 50 de {len(dados_conjunturais)} modificações. Todas estão disponíveis no JSON.*\n")
            response_parts.append("\n")
    
    response_parts.append("---\n\n")
    response_parts.append("*Dados processados diretamente do arquivo CLAST.DAT usando tool pré-programada.*\n")
    
    response_text = "".join(response_parts)
    response_text = clean_response_text(response_text, max_emojis=2)
    return {"final_response": response_text}


def format_expt_operacao_response(tool_result: dict, tool_used: str) -> dict:
    """
    Formata o resultado da ExptOperacaoTool em resposta Markdown.
    
    Args:
        tool_result: Resultado da execução da tool
        tool_used: Nome da tool usada
        
    Returns:
        Dict com final_response formatado
    """
    response_parts = []
    
    # Cabeçalho
    filtros = tool_result.get("filtros")
    
    response_parts.append("## ✅ Dados de Operação Térmica do EXPT.DAT\n\n")
    response_parts.append(f"*Processado pela tool: **{tool_used}***\n\n")
    
    # Informações sobre filtros
    if filtros:
        response_parts.append("### 🔍 Filtros Aplicados\n\n")
        if 'usina' in filtros:
            usina_info = filtros['usina']
            response_parts.append(f"- **Usina**: {usina_info.get('nome')} (Código: {usina_info.get('codigo')})\n")
        if 'tipo_modificacao' in filtros:
            response_parts.append(f"- **Tipo de Modificação**: {filtros['tipo_modificacao']}\n")
        if 'operacao_especifica' in filtros:
            op = filtros['operacao_especifica']
            op_nome = {
                'desativacao': 'Desativações',
                'repotenciacao': 'Repotenciações',
                'expansao': 'Expansões'
            }.get(op, op)
            response_parts.append(f"- **Operação**: {op_nome}\n")
        response_parts.append("\n")
    
    # Estatísticas gerais
    stats_geral = tool_result.get("stats_geral")
    if stats_geral:
        response_parts.append("###  Resumo\n\n")
        response_parts.append(f"- **Total de registros**: {stats_geral.get('total_registros', 0):,}\n")
        response_parts.append(f"- **Usinas afetadas**: {stats_geral.get('total_usinas', 0)}\n")
        tipos = stats_geral.get('tipos_modificacao', [])
        if tipos:
            response_parts.append(f"- **Tipos de modificação encontrados**: {', '.join(tipos)}\n")
        response_parts.append("\n")
    
    # Dicionário de explicações para cada tipo
    explicacoes_tipos = {
        'POTEF': {
            'nome': 'Potência Efetiva',
            'descricao': 'Potência efetiva da usina térmica em MW. Modificações neste valor representam expansões (aumentos), repotenciações ou desativações (quando = 0).',
            'unidade': 'MW'
        },
        'GTMIN': {
            'nome': 'Geração Térmica Mínima',
            'descricao': 'Geração térmica mínima obrigatória em MW. Define a geração mínima que a usina deve manter durante o período especificado.',
            'unidade': 'MW'
        },
        'FCMAX': {
            'nome': 'Fator de Capacidade Máximo',
            'descricao': 'Fator de capacidade máximo em percentual (0-100%). Limita a capacidade de geração da usina. Quando = 0, indica desativação.',
            'unidade': '%'
        },
        'IPTER': {
            'nome': 'Indisponibilidade Programada',
            'descricao': 'Indisponibilidade programada em percentual (0-100%). Representa períodos de manutenção programada onde a usina não estará disponível.',
            'unidade': '%'
        },
        'TEIFT': {
            'nome': 'Taxa Equivalente de Indisponibilidade Forçada',
            'descricao': 'Taxa equivalente de indisponibilidade forçada em percentual (0-100%). Representa indisponibilidades não programadas (forçadas) da usina.',
            'unidade': '%'
        }
    }
    
    # Obter dados de expansões
    dados_expansoes = tool_result.get("dados_expansoes", [])
    
    if dados_expansoes:
        # Agrupar por tipo de modificação
        df_expansoes = pd.DataFrame(dados_expansoes)
        
        tipos_presentes = df_expansoes['tipo'].unique() if 'tipo' in df_expansoes.columns else []
        
        # Para cada tipo, criar uma seção separada
        for tipo in sorted(tipos_presentes):
            df_tipo = df_expansoes[df_expansoes['tipo'] == tipo]
            explicacao = explicacoes_tipos.get(tipo, {
                'nome': tipo,
                'descricao': f'Modificações do tipo {tipo}',
                'unidade': ''
            })
            
            response_parts.append(f"### 🔧 {explicacao['nome']} ({tipo})\n\n")
            response_parts.append(f"**Explicação**: {explicacao['descricao']}\n\n")
            response_parts.append(f"**Total de registros**: {len(df_tipo)}\n\n")
            
            # Tabela com os dados deste tipo
            response_parts.append("| Código | Nome Usina | Valor | Data Início | Data Fim |\n")
            response_parts.append("|--------|------------|-------|-------------|----------|\n")
            
            for _, record in df_tipo.iterrows():
                codigo = record.get('codigo_usina', 'N/A')
                nome = record.get('nome_usina', 'N/A')
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
                
                # Formatar valor com unidade
                if explicacao['unidade']:
                    valor_str = f"{modificacao:,.2f} {explicacao['unidade']}"
                else:
                    valor_str = f"{modificacao:,.2f}"
                
                response_parts.append(f"| {codigo} | {nome} | {valor_str} | {inicio} | {fim} |\n")
            
            response_parts.append("\n")
            
            # Estatísticas específicas deste tipo
            if len(df_tipo) > 1:
                valor_medio = df_tipo['modificacao'].mean()
                valor_min = df_tipo['modificacao'].min()
                valor_max = df_tipo['modificacao'].max()
                unidade = explicacao['unidade']
                
                response_parts.append(f"**Estatísticas**:\n")
                response_parts.append(f"- Valor médio: {valor_medio:,.2f} {unidade}\n")
                response_parts.append(f"- Valor mínimo: {valor_min:,.2f} {unidade}\n")
                response_parts.append(f"- Valor máximo: {valor_max:,.2f} {unidade}\n")
                response_parts.append("\n")
            
            response_parts.append("---\n\n")
    
    # Estatísticas por tipo (resumo geral - já detalhado acima por tipo)
    stats_por_tipo = tool_result.get("stats_por_tipo", [])
    if stats_por_tipo and len(stats_por_tipo) > 1:
        response_parts.append("### 📈 Resumo Estatístico por Tipo\n\n")
        response_parts.append("| Tipo | Registros | Usinas | Valor Médio | Mínimo | Máximo |\n")
        response_parts.append("|------|-----------|--------|-------------|--------|--------|\n")
        
        for stat in stats_por_tipo:
            tipo = stat.get('tipo', 'N/A')
            registros = stat.get('total_registros', 0)
            usinas = stat.get('usinas_afetadas', 0)
            medio = stat.get('valor_medio', 0)
            minimo = stat.get('valor_min', 0)
            maximo = stat.get('valor_max', 0)
            
            # Formatar unidade baseado no tipo
            if tipo in ['POTEF', 'GTMIN']:
                unidade = "MW"
                response_parts.append(
                    f"| {tipo} | {registros} | {usinas} | {medio:,.2f} {unidade} | {minimo:,.2f} {unidade} | {maximo:,.2f} {unidade} |\n"
                )
            else:
                unidade = "%"
                response_parts.append(
                    f"| {tipo} | {registros} | {usinas} | {medio:,.2f} {unidade} | {minimo:,.2f} {unidade} | {maximo:,.2f} {unidade} |\n"
                )
        response_parts.append("\n")
    
    # Estatísticas por usina
    stats_por_usina = tool_result.get("stats_por_usina", [])
    if stats_por_usina:
        response_parts.append("### 🏭 Modificações por Usina\n\n")
        response_parts.append("| Código | Nome Usina | Total Modificações | Tipos |\n")
        response_parts.append("|--------|------------|-------------------|-------|\n")
        
        for stat in stats_por_usina[:20]:  # Limitar a 20 para não sobrecarregar
            codigo = stat.get('codigo_usina', 'N/A')
            nome = stat.get('nome_usina', 'N/A')
            total = stat.get('total_modificacoes', 0)
            tipos = ', '.join(stat.get('tipos_modificacao', []))
            
            response_parts.append(f"| {codigo} | {nome} | {total} | {tipos} |\n")
        
        if len(stats_por_usina) > 20:
            response_parts.append(f"\n*Exibindo 20 de {len(stats_por_usina)} usinas. Todas estão disponíveis no JSON.*\n")
        response_parts.append("\n")
    
    # Desativações
    desativacoes = tool_result.get("desativacoes")
    if desativacoes:
        response_parts.append("### ⚠️ Desativações de Usinas Térmicas\n\n")
        response_parts.append("| Código | Nome Usina | Tipo | Data Início | Data Fim |\n")
        response_parts.append("|--------|------------|------|-------------|----------|\n")
        
        for desat in desativacoes[:20]:
            codigo = desat.get('codigo_usina', 'N/A')
            nome = desat.get('nome_usina', 'N/A')
            tipo = desat.get('tipo', 'N/A')
            inicio = desat.get('data_inicio', 'N/A')
            fim = desat.get('data_fim', 'N/A')
            
            # Formatar datas
            if isinstance(inicio, str) and 'T' in inicio:
                inicio = inicio.split('T')[0]
            if isinstance(fim, str) and 'T' in fim:
                fim = fim.split('T')[0]
            
            response_parts.append(f"| {codigo} | {nome} | {tipo} | {inicio} | {fim} |\n")
        
        if len(desativacoes) > 20:
            response_parts.append(f"\n*Exibindo 20 de {len(desativacoes)} desativações. Todas estão disponíveis no JSON.*\n")
        response_parts.append("\n")
    
    # Repotenciações
    repotenciacoes = tool_result.get("repotenciacoes")
    if repotenciacoes:
        response_parts.append("### ⚡ Repotenciações\n\n")
        response_parts.append("| Código | Nome Usina | Nova Potência (MW) | Data Início | Data Fim |\n")
        response_parts.append("|--------|------------|-------------------|-------------|----------|\n")
        
        for repot in repotenciacoes[:20]:
            codigo = repot.get('codigo_usina', 'N/A')
            nome = repot.get('nome_usina', 'N/A')
            potencia = repot.get('modificacao', 0)
            inicio = repot.get('data_inicio', 'N/A')
            fim = repot.get('data_fim', 'N/A')
            
            # Formatar datas
            if isinstance(inicio, str) and 'T' in inicio:
                inicio = inicio.split('T')[0]
            if isinstance(fim, str) and 'T' in fim:
                fim = fim.split('T')[0]
            
            response_parts.append(f"| {codigo} | {nome} | {potencia:,.2f} | {inicio} | {fim} |\n")
        
        if len(repotenciacoes) > 20:
            response_parts.append(f"\n*Exibindo 20 de {len(repotenciacoes)} repotenciações. Todas estão disponíveis no JSON.*\n")
        response_parts.append("\n")
    
    # Indisponibilidades
    indisponibilidades = tool_result.get("indisponibilidades")
    if indisponibilidades:
        response_parts.append("### 🔧 Indisponibilidades\n\n")
        response_parts.append("| Código | Nome Usina | Tipo | Taxa (%) | Data Início | Data Fim |\n")
        response_parts.append("|--------|------------|------|----------|-------------|----------|\n")
        
        for indis in indisponibilidades[:20]:
            codigo = indis.get('codigo_usina', 'N/A')
            nome = indis.get('nome_usina', 'N/A')
            tipo = indis.get('tipo', 'N/A')
            taxa = indis.get('modificacao', 0)
            inicio = indis.get('data_inicio', 'N/A')
            fim = indis.get('data_fim', 'N/A')
            
            # Formatar datas
            if isinstance(inicio, str) and 'T' in inicio:
                inicio = inicio.split('T')[0]
            if isinstance(fim, str) and 'T' in fim:
                fim = fim.split('T')[0]
            
            response_parts.append(f"| {codigo} | {nome} | {tipo} | {taxa:,.2f} | {inicio} | {fim} |\n")
        
        if len(indisponibilidades) > 20:
            response_parts.append(f"\n*Exibindo 20 de {len(indisponibilidades)} indisponibilidades. Todas estão disponíveis no JSON.*\n")
        response_parts.append("\n")
    
    # Nota sobre dados completos (já apresentados acima por tipo)
    dados_expansoes = tool_result.get("dados_expansoes", [])
    if dados_expansoes:
        response_parts.append("### 📋 Nota sobre Dados Completos\n\n")
        response_parts.append(f"*Todos os {len(dados_expansoes)} registros foram apresentados acima, agrupados por tipo de modificação. Dados completos também estão disponíveis no JSON para download.*\n\n")
    
    response_parts.append("---\n\n")
    response_parts.append("*Dados processados diretamente do arquivo EXPT.DAT usando tool pré-programada.*\n")
    
    response_text = "".join(response_parts)
    response_text = clean_response_text(response_text, max_emojis=2)
    return {"final_response": response_text}

def format_modif_operacao_response(tool_result: dict, tool_used: str) -> dict:
    """
    Formata o resultado da ModifOperacaoTool em resposta Markdown.
    
    Args:
        tool_result: Resultado da execução da tool
        tool_used: Nome da tool usada
        
    Returns:
        Dict com final_response formatado
    """
    response_parts = []
    
    # Cabeçalho
    filtros = tool_result.get("filtros")
    
    response_parts.append("## ✅ Dados de Operação Hídrica do MODIF.DAT\n\n")
    response_parts.append(f"*Processado pela tool: **{tool_used}***\n\n")
    
    # Informações sobre filtros
    if filtros:
        response_parts.append("### 🔍 Filtros Aplicados\n\n")
        if 'usina' in filtros:
            usina_info = filtros['usina']
            response_parts.append(f"- **Usina**: {usina_info.get('nome')} (Código: {usina_info.get('codigo')})\n")
        if 'tipo_modificacao' in filtros:
            response_parts.append(f"- **Tipo de Modificação**: {filtros['tipo_modificacao']}\n")
        response_parts.append("\n")
    
    # Estatísticas gerais
    stats_geral = tool_result.get("stats_geral")
    if stats_geral:
        response_parts.append("###  Resumo\n\n")
        response_parts.append(f"- **Total de tipos de modificação**: {stats_geral.get('total_tipos', 0)}\n")
        response_parts.append(f"- **Total de registros**: {stats_geral.get('total_registros', 0):,}\n")
        tipos = stats_geral.get('tipos_encontrados', [])
        if tipos:
            response_parts.append(f"- **Tipos encontrados**: {', '.join(tipos)}\n")
        response_parts.append("\n")
    
    # Dicionário de explicações para cada tipo
    explicacoes_tipos = {
        'VOLMIN': {
            'nome': 'Volume Mínimo Operativo',
            'descricao': 'Volume mínimo operativo da usina hidrelétrica. Pode ser especificado em H/h (hectômetros cúbicos) ou % (percentual do volume útil).',
            'unidade': 'H/h ou %'
        },
        'VOLMAX': {
            'nome': 'Volume Máximo Operativo',
            'descricao': 'Volume máximo operativo da usina hidrelétrica. Pode ser especificado em H/h (hectômetros cúbicos) ou % (percentual do volume útil).',
            'unidade': 'H/h ou %'
        },
        'VMAXT': {
            'nome': 'Volume Máximo com Data',
            'descricao': 'Volume máximo operativo com data de início. Modificação temporal que altera o volume máximo a partir de uma data específica. Referenciado ao final do período.',
            'unidade': 'H/h ou %'
        },
        'VMINT': {
            'nome': 'Volume Mínimo com Data',
            'descricao': 'Volume mínimo operativo com data de início. Modificação temporal que altera o volume mínimo a partir de uma data específica. Referenciado ao final do período.',
            'unidade': 'H/h ou %'
        },
        'VMINP': {
            'nome': 'Volume Mínimo com Penalidade',
            'descricao': 'Volume mínimo com adoção de penalidade, com data. Implementa mecanismo de aversão a risco. O valor considerado será o mais restritivo entre MODIF.DAT (por usina) e CURVA.DAT (por REE).',
            'unidade': 'H/h ou %'
        },
        'VAZMIN': {
            'nome': 'Vazão Mínima',
            'descricao': 'Vazão mínima obrigatória da usina. Pode ter até dois valores: requisito total e valor para relaxamento (opcional, menor que o primeiro).',
            'unidade': 'm³/s'
        },
        'VAZMINT': {
            'nome': 'Vazão Mínima com Data',
            'descricao': 'Vazão mínima obrigatória com data de início. Modificação temporal que altera a vazão mínima a partir de uma data específica.',
            'unidade': 'm³/s'
        },
        'VAZMAXT': {
            'nome': 'Vazão Máxima com Data',
            'descricao': 'Vazão máxima (defluência máxima) com data. Considerada apenas em períodos individualizados, se os flags apropriados estiverem habilitados no dger.dat.',
            'unidade': 'm³/s'
        },
        'CFUGA': {
            'nome': 'Canal de Fuga',
            'descricao': 'Nível do canal de fuga da usina. Modificação temporal que altera o nível do canal de fuga a partir de uma data específica. Referenciado ao início do período.',
            'unidade': 'm'
        },
        'CMONT': {
            'nome': 'Nível de Montante',
            'descricao': 'Nível de montante da usina. Modificação temporal que altera o nível de montante a partir de uma data específica. Permitido somente para usinas fio d\'água.',
            'unidade': 'm'
        },
        'TURBMAXT': {
            'nome': 'Turbinamento Máximo com Data',
            'descricao': 'Turbinamento máximo com data e por patamar. Considerado apenas em períodos individualizados, se os flags apropriados estiverem habilitados no dger.dat.',
            'unidade': 'm³/s'
        },
        'TURBMINT': {
            'nome': 'Turbinamento Mínimo com Data',
            'descricao': 'Turbinamento mínimo com data e por patamar. Considerado apenas em períodos individualizados, se os flags apropriados estiverem habilitados no dger.dat.',
            'unidade': 'm³/s'
        },
        'POTEFE': {
            'nome': 'Potência Efetiva',
            'descricao': 'Potência efetiva da usina hidrelétrica. Modificação da potência efetiva por conjunto de máquinas.',
            'unidade': 'MW'
        },
        'TEIF': {
            'nome': 'Taxa Esperada de Indisponibilidade Forçada',
            'descricao': 'Taxa esperada de indisponibilidade forçada da usina. Representa indisponibilidades não programadas (forçadas).',
            'unidade': '%'
        },
        'IP': {
            'nome': 'Indisponibilidade Programada',
            'descricao': 'Indisponibilidade programada da usina. Representa períodos de manutenção programada onde a usina não estará disponível.',
            'unidade': '%'
        },
        'NUMCNJ': {
            'nome': 'Número de Conjuntos de Máquinas',
            'descricao': 'Número de conjuntos de máquinas da usina. Modifica a quantidade de conjuntos de máquinas.',
            'unidade': 'unidade'
        },
        'NUMMAQ': {
            'nome': 'Número de Máquinas por Conjunto',
            'descricao': 'Número de máquinas por conjunto. Modifica a quantidade de máquinas em um conjunto específico.',
            'unidade': 'unidade'
        }
    }
    
    # Obter dados por tipo
    dados_por_tipo = tool_result.get("dados_por_tipo", {})
    
    if dados_por_tipo:
        # Para cada tipo, criar uma seção separada
        for tipo in sorted(dados_por_tipo.keys()):
            dados_tipo = dados_por_tipo[tipo]
            explicacao = explicacoes_tipos.get(tipo, {
                'nome': tipo,
                'descricao': f'Modificações do tipo {tipo}',
                'unidade': ''
            })
            
            response_parts.append(f"### 🔧 {explicacao['nome']} ({tipo})\n\n")
            response_parts.append(f"**Explicação**: {explicacao['descricao']}\n\n")
            response_parts.append(f"**Total de registros**: {len(dados_tipo)}\n\n")
            
            # Tabela com os dados deste tipo
            # Determinar colunas baseado no tipo
            if tipo in ['VOLMIN', 'VOLMAX', 'VMAXT', 'VMINT', 'VMINP']:
                response_parts.append("| Código | Nome Usina | Volume | Unidade | Data Início |\n")
                response_parts.append("|--------|------------|--------|---------|-------------|\n")
                
                for record in dados_tipo:
                    codigo = record.get('codigo', record.get('codigo_usina', 'N/A'))
                    nome = record.get('nome', record.get('nome_usina', 'N/A'))
                    volume = record.get('volume', 0)
                    unidade = record.get('unidade', 'N/A')
                    inicio = record.get('data_inicio', 'N/A')
                    
                    # Formatar data
                    if isinstance(inicio, str) and 'T' in inicio:
                        inicio = inicio.split('T')[0]
                    elif hasattr(inicio, 'date'):
                        inicio = inicio.date()
                    
                    response_parts.append(f"| {codigo} | {nome} | {volume:,.2f} | {unidade} | {inicio} |\n")
            
            elif tipo in ['VAZMIN', 'VAZMINT', 'VAZMAXT']:
                response_parts.append("| Código | Nome Usina | Vazão | Data Início |\n")
                response_parts.append("|--------|------------|-------|-------------|\n")
                
                for record in dados_tipo:
                    codigo = record.get('codigo', record.get('codigo_usina', 'N/A'))
                    nome = record.get('nome', record.get('nome_usina', 'N/A'))
                    vazao = record.get('vazao', 0)
                    inicio = record.get('data_inicio', 'N/A')
                    
                    # Formatar data
                    if isinstance(inicio, str) and 'T' in inicio:
                        inicio = inicio.split('T')[0]
                    elif hasattr(inicio, 'date'):
                        inicio = inicio.date()
                    
                    response_parts.append(f"| {codigo} | {nome} | {vazao:,.2f} m³/s | {inicio} |\n")
            
            elif tipo in ['CFUGA', 'CMONT']:
                response_parts.append("| Código | Nome Usina | Nível (m) | Data Início |\n")
                response_parts.append("|--------|------------|-----------|-------------|\n")
                
                for record in dados_tipo:
                    codigo = record.get('codigo', record.get('codigo_usina', 'N/A'))
                    nome = record.get('nome', record.get('nome_usina', 'N/A'))
                    nivel = record.get('nivel', 0)
                    inicio = record.get('data_inicio', 'N/A')
                    
                    # Formatar data
                    if isinstance(inicio, str) and 'T' in inicio:
                        inicio = inicio.split('T')[0]
                    elif hasattr(inicio, 'date'):
                        inicio = inicio.date()
                    
                    response_parts.append(f"| {codigo} | {nome} | {nivel:,.2f} | {inicio} |\n")
            
            elif tipo in ['TURBMAXT', 'TURBMINT']:
                response_parts.append("| Código | Nome Usina | Patamar | Turbinamento (m³/s) | Data Início |\n")
                response_parts.append("|--------|------------|---------|---------------------|-------------|\n")
                
                for record in dados_tipo:
                    codigo = record.get('codigo', record.get('codigo_usina', 'N/A'))
                    nome = record.get('nome', record.get('nome_usina', 'N/A'))
                    patamar = record.get('patamar', 'N/A')
                    turbinamento = record.get('turbinamento', 0)
                    inicio = record.get('data_inicio', 'N/A')
                    
                    # Formatar data
                    if isinstance(inicio, str) and 'T' in inicio:
                        inicio = inicio.split('T')[0]
                    elif hasattr(inicio, 'date'):
                        inicio = inicio.date()
                    
                    response_parts.append(f"| {codigo} | {nome} | {patamar} | {turbinamento:,.2f} | {inicio} |\n")
            
            elif tipo in ['NUMCNJ', 'NUMMAQ']:
                if tipo == 'NUMCNJ':
                    response_parts.append("| Código | Nome Usina | Número de Conjuntos |\n")
                    response_parts.append("|--------|------------|---------------------|\n")
                    
                    for record in dados_tipo:
                        codigo = record.get('codigo', record.get('codigo_usina', 'N/A'))
                        nome = record.get('nome', record.get('nome_usina', 'N/A'))
                        numero = record.get('numero', 'N/A')
                        response_parts.append(f"| {codigo} | {nome} | {numero} |\n")
                else:
                    response_parts.append("| Código | Nome Usina | Conjunto | Número de Máquinas |\n")
                    response_parts.append("|--------|------------|----------|-------------------|\n")
                    
                    for record in dados_tipo:
                        codigo = record.get('codigo', record.get('codigo_usina', 'N/A'))
                        nome = record.get('nome', record.get('nome_usina', 'N/A'))
                        conjunto = record.get('conjunto', 'N/A')
                        numero_maquinas = record.get('numero_maquinas', 'N/A')
                        response_parts.append(f"| {codigo} | {nome} | {conjunto} | {numero_maquinas} |\n")
            
            else:
                # Formato genérico
                response_parts.append("| Código | Nome Usina | Valor |\n")
                response_parts.append("|--------|------------|-------|\n")
                
                for record in dados_tipo:
                    codigo = record.get('codigo', record.get('codigo_usina', 'N/A'))
                    nome = record.get('nome', record.get('nome_usina', 'N/A'))
                    # Tentar encontrar qualquer valor numérico
                    valor = 'N/A'
                    for key, val in record.items():
                        if key not in ['codigo', 'codigo_usina', 'nome', 'nome_usina'] and isinstance(val, (int, float)):
                            valor = f"{val:,.2f}"
                            break
                    response_parts.append(f"| {codigo} | {nome} | {valor} |\n")
            
            response_parts.append("\n")
            
            # Estatísticas específicas deste tipo
            stats_por_tipo = tool_result.get("stats_por_tipo", [])
            stats_tipo = next((s for s in stats_por_tipo if s.get('tipo') == tipo), None)
            
            if stats_tipo and len(dados_tipo) > 1:
                valor_medio = stats_tipo.get('valor_medio', 0)
                valor_min = stats_tipo.get('valor_min', 0)
                valor_max = stats_tipo.get('valor_max', 0)
                unidade = stats_tipo.get('unidade', explicacao['unidade'])
                
                response_parts.append(f"**Estatísticas**:\n")
                response_parts.append(f"- Valor médio: {valor_medio:,.2f} {unidade}\n")
                response_parts.append(f"- Valor mínimo: {valor_min:,.2f} {unidade}\n")
                response_parts.append(f"- Valor máximo: {valor_max:,.2f} {unidade}\n")
                response_parts.append("\n")
            
            response_parts.append("---\n\n")
    
    # Estatísticas por usina
    stats_por_usina = tool_result.get("stats_por_usina", [])
    if stats_por_usina:
        response_parts.append("### 🏭 Modificações por Usina\n\n")
        response_parts.append("| Código | Nome Usina | Total Modificações | Tipos |\n")
        response_parts.append("|--------|------------|-------------------|-------|\n")
        
        for stat in stats_por_usina[:20]:  # Limitar a 20
            codigo = stat.get('codigo_usina', 'N/A')
            nome = stat.get('nome_usina', 'N/A')
            total = stat.get('total_modificacoes', 0)
            tipos = ', '.join(stat.get('tipos_modificacao', []))
            
            response_parts.append(f"| {codigo} | {nome} | {total} | {tipos} |\n")
        
        if len(stats_por_usina) > 20:
            response_parts.append(f"\n*Exibindo 20 de {len(stats_por_usina)} usinas. Todas estão disponíveis no JSON.*\n")
        response_parts.append("\n")
    
    response_parts.append("---\n\n")
    response_parts.append("*Dados processados diretamente do arquivo MODIF.DAT usando tool pré-programada.*\n")
    
    response_text = "".join(response_parts)
    response_text = clean_response_text(response_text, max_emojis=2)
    return {"final_response": response_text}

