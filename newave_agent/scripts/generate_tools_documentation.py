"""
Script para gerar documentação otimizada baseada em tools e inewave.

Este script analisa as tools disponíveis e gera documentação estruturada
com exemplos de código para uso da biblioteca inewave.
"""
import os
import sys
from pathlib import Path

# Adicionar raiz do projeto ao path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# Mapeamento manual de tools para documentação
# Baseado na análise do código fonte das tools
TOOLS_DOCUMENTATION = {
    "CargaMensalTool": {
        "category": "Dados de Mercado e Demanda",
        "file": "SISTEMA.DAT",
        "class": "Sistema",
        "properties": ["mercado_energia", "custo_deficit"],
        "description": "Consulta cargas mensais por submercado e período",
        "example_code": """
from inewave.newave import Sistema
import os
import pandas as pd

# Ler arquivo SISTEMA.DAT
sistema_path = os.path.join(deck_path, "SISTEMA.DAT")
sistema = Sistema.read(sistema_path)

# Acessar dados de mercado de energia (cargas mensais)
df_mercado = sistema.mercado_energia

# Verificar se há dados
if df_mercado is None or df_mercado.empty:
    resultado = []
else:
    # Filtrar por submercado (ex: Sudeste = 1)
    # df_resultado = df_mercado[df_mercado['codigo_submercado'] == 1]
    
    # Filtrar por ano
    # df_resultado = df_mercado[df_mercado['ano'] == 2025]
    
    # Filtrar por submercado E ano
    # df_resultado = df_mercado[
    #     (df_mercado['codigo_submercado'] == 1) & 
    #     (df_mercado['ano'] == 2025)
    # ]
    
    # Usar todos os dados se não houver filtro específico
    df_resultado = df_mercado.copy()
    
    # Obter lista de submercados disponíveis (para referência)
    if sistema.custo_deficit is not None:
        subsistemas = sistema.custo_deficit[['codigo_submercado', 'nome_submercado']].drop_duplicates()
    
    # Converter para lista de dicionários
    resultado = df_resultado.to_dict(orient='records')
""",
        "columns": ["codigo_submercado", "nome_submercado", "ano", "mes", "valor"],
        "queries": [
            "cargas mensais do Sudeste",
            "demanda do Nordeste em 2025",
            "cargas por submercado",
            "mercado de energia"
        ]
    },
    "CadicTool": {
        "category": "Dados de Mercado e Demanda",
        "file": "C_ADIC.DAT",
        "class": "Cadic",
        "properties": ["cargas"],
        "description": "Consulta cargas adicionais por submercado e período",
        "example_code": """
from inewave.newave import Cadic, Sistema
import os
import pandas as pd

# Ler arquivo C_ADIC.DAT
cadic_path = os.path.join(deck_path, "C_ADIC.DAT")
cadic = Cadic.read(cadic_path)

# Acessar cargas adicionais
df_cargas = cadic.cargas

# Verificar se há dados
if df_cargas is None or df_cargas.empty:
    resultado = []
else:
    # Ler SISTEMA.DAT para obter nomes de submercados (opcional, para enriquecer dados)
    sistema_path = os.path.join(deck_path, "SISTEMA.DAT")
    sistema = None
    try:
        sistema = Sistema.read(sistema_path)
    except:
        pass
    
    # Filtrar por submercado se necessário
    # df_resultado = df_cargas[df_cargas['codigo_submercado'] == 1]
    
    # Filtrar por ano/mês se necessário
    # df_resultado = df_cargas[
    #     (df_cargas['ano'] == 2025) & 
    #     (df_cargas['mes'] == 1)
    # ]
    
    # Usar todos os dados se não houver filtro
    df_resultado = df_cargas.copy()
    
    # Converter para lista de dicionários
    resultado = df_resultado.to_dict(orient='records')
""",
        "columns": ["codigo_submercado", "nome_submercado", "ano", "mes", "valor"],
        "queries": [
            "cargas adicionais",
            "carga adicional do Sudeste",
            "C_ADIC"
        ]
    },
    "ClastValoresTool": {
        "category": "Dados Térmicos",
        "file": "CLAST.DAT",
        "class": "Clast",
        "properties": ["usinas", "modificacoes"],
        "description": "Consulta custos de classes térmicas (estruturais e conjunturais)",
        "example_code": """
from inewave.newave import Clast
import os
import pandas as pd

# Ler arquivo CLAST.DAT
clast_path = os.path.join(deck_path, "CLAST.DAT")
clast = Clast.read(clast_path)

# Acessar dados estruturais (custos base por classe e ano)
df_estrutural = clast.usinas

# Acessar dados conjunturais (modificações sazonais de custo)
df_conjuntural = clast.modificacoes

# Verificar qual tipo de dado usar (estrutural ou conjuntural)
# Para CVU (Custo Variável Unitário), SEMPRE usar dados estruturais e retornar TODOS os anos
usar_estrutural = True  # ou False para conjuntural

if usar_estrutural and df_estrutural is not None and not df_estrutural.empty:
    df_base = df_estrutural.copy()
    
    # IMPORTANTE: Para CVU, NÃO filtrar por ano - retornar todos os anos
    # Filtrar apenas por classe se especificado
    # df_resultado = df_base[df_base['codigo_usina'] == 1]  # Classe específica
    
    # Filtrar por tipo de combustível se especificado
    # df_resultado = df_base[df_base['tipo_combustivel'] == 'GAS']
    
    # Usar todos os dados estruturais
    df_resultado = df_base.copy()
    
elif not usar_estrutural and df_conjuntural is not None and not df_conjuntural.empty:
    df_base = df_conjuntural.copy()
    
    # Preencher nome_usina se não estiver presente
    if 'nome_usina' not in df_base.columns and df_estrutural is not None:
        mapeamento = df_estrutural[['codigo_usina', 'nome_usina']].drop_duplicates()
        df_base = df_base.merge(mapeamento, on='codigo_usina', how='left')
    
    df_resultado = df_base.copy()
else:
    df_resultado = pd.DataFrame()

# Converter para lista de dicionários
if not df_resultado.empty:
    resultado = df_resultado.to_dict(orient='records')
else:
    resultado = []
""",
        "columns": ["codigo_usina", "nome_usina", "tipo_combustivel", "indice_ano_estudo", "valor"],
        "queries": [
            "custo das classes térmicas",
            "CVU",
            "custo variável unitário",
            "custos estruturais",
            "custos conjunturais"
        ]
    },
    "ExptOperacaoTool": {
        "category": "Dados Térmicos",
        "file": "EXPT.DAT",
        "class": "Expt",
        "properties": ["expansoes"],
        "description": "Consulta expansões, repotenciações e desativações de térmicas",
        "example_code": """
from inewave.newave import Expt
import os

# Ler arquivo
expt_path = os.path.join(deck_path, "EXPT.DAT")
expt = Expt.read(expt_path)

# Acessar expansões
df_expansoes = expt.expansoes

# Filtrar por usina
df_usina = df_expansoes[df_expansoes['codigo_usina'] == 1]

# Filtrar por tipo de modificação
df_potef = df_expansoes[df_expansoes['tipo'] == 'POTEF']

# Desativações: POTEF=0 ou FCMAX=0
desativacoes = df_expansoes[
    ((df_expansoes['tipo'] == 'POTEF') & (df_expansoes['modificacao'] == 0)) |
    ((df_expansoes['tipo'] == 'FCMAX') & (df_expansoes['modificacao'] == 0))
]

# Repotenciações: POTEF > 0
repotenciacoes = df_expansoes[
    (df_expansoes['tipo'] == 'POTEF') &
    (df_expansoes['modificacao'] > 0)
]
""",
        "columns": ["codigo_usina", "nome_usina", "tipo", "modificacao", "data_inicio", "data_fim"],
        "queries": [
            "expansões térmicas",
            "repotenciações",
            "desativações de térmicas",
            "EXPT"
        ]
    },
    "TermCadastroTool": {
        "category": "Dados Térmicos",
        "file": "TERM.DAT",
        "class": "Term",
        "properties": ["usinas"],
        "description": "Consulta cadastro de usinas termoelétricas",
        "example_code": """
from inewave.newave import Term
import os

# Ler arquivo
term_path = os.path.join(deck_path, "TERM.DAT")
term = Term.read(term_path)

# Acessar cadastro
df_usinas = term.usinas

# Filtrar por usina específica
df_usina = df_usinas[df_usinas['codigo_usina'] == 1]

# Colunas principais: codigo_usina, nome_usina, pot_efetiva, fcmax, teif, ip, gtmin
""",
        "columns": ["codigo_usina", "nome_usina", "pot_efetiva", "fcmax", "teif", "ip"],
        "queries": [
            "cadastro térmica",
            "informações da usina térmica",
            "potência efetiva",
            "fator capacidade máximo",
            "TERM.DAT"
        ]
    },
    "ModifOperacaoTool": {
        "category": "Dados Hidrelétricos",
        "file": "MODIF.DAT",
        "class": "Modif",
        "properties": ["usina", "vazmin", "vazmint", "volmin", "volmax", "vmaxt", "vmint", 
                      "cfuga", "cmont", "turbmaxt", "turbmint", "numcnj", "nummaq", 
                      "modificacoes_usina"],
        "description": "Consulta modificações operacionais de usinas hidrelétricas",
        "example_code": """
from inewave.newave import Modif
import os

# Ler arquivo
modif_path = os.path.join(deck_path, "MODIF.DAT")
modif = Modif.read(modif_path)

# Obter lista de usinas modificadas
usinas_df = modif.usina(df=True)

# Acessar modificações por tipo (retorna DataFrame quando df=True)
vazmin = modif.vazmin(df=True)  # Vazão mínima
vazmint = modif.vazmint(df=True)  # Vazão mínima com data
volmin = modif.volmin(df=True)  # Volume mínimo
volmax = modif.volmax(df=True)  # Volume máximo
vmaxt = modif.vmaxt(df=True)  # Volume máximo com data
vmint = modif.vmint(df=True)  # Volume mínimo com data
cfuga = modif.cfuga(df=True)  # Canal de fuga
cmont = modif.cmont(df=True)  # Nível montante
turbmaxt = modif.turbmaxt(df=True)  # Turbinamento máximo
turbmint = modif.turbmint(df=True)  # Turbinamento mínimo
numcnj = modif.numcnj(df=True)  # Número de conjuntos
nummaq = modif.nummaq(df=True)  # Número de máquinas

# Obter todas as modificações de uma usina específica
codigo_usina = 6
modificacoes = modif.modificacoes_usina(codigo_usina)

# Filtrar por usina
vazmin_furnas = vazmin[vazmin['codigo_usina'] == 6]
""",
        "columns": ["codigo_usina", "nome_usina", "vazao", "volume", "data_inicio", "data_fim"],
        "queries": [
            "vazão mínima",
            "volume mínimo",
            "modificações hídricas",
            "vazão mínima pré-estabelecida",
            "volumes mínimos das usinas"
        ]
    },
    "HidrCadastroTool": {
        "category": "Dados Hidrelétricos",
        "file": "HIDR.DAT",
        "class": "Hidr",
        "properties": ["cadastro"],
        "description": "Consulta cadastro completo de usinas hidrelétricas",
        "example_code": """
from inewave.newave import Hidr
import os

# Ler arquivo
hidr_path = os.path.join(deck_path, "HIDR.DAT")
hidr = Hidr.read(hidr_path)

# Acessar cadastro (DataFrame com 60+ colunas)
cadastro = hidr.cadastro

# Filtrar por usina específica (usar índice real do DataFrame)
# O cadastro usa índice real, não código da usina diretamente
usina_row = cadastro.loc[idx_real]

# Colunas principais: nome_usina, posto, submercado, volume_minimo, volume_maximo,
# potencia_nominal_conjunto_[1-5], produtibilidade_especifica, vazao_minima_historica
""",
        "columns": ["nome_usina", "posto", "submercado", "volume_minimo", "volume_maximo", 
                   "potencia_nominal_conjunto_1", "produtibilidade_especifica"],
        "queries": [
            "cadastro hidrelétrica",
            "informações da usina hidrelétrica",
            "potência instalada",
            "volumes da usina",
            "HIDR.DAT"
        ]
    },
    "ConfhdTool": {
        "category": "Dados Hidrelétricos",
        "file": "CONFHD.DAT",
        "class": "Confhd",
        "properties": ["usinas"],
        "description": "Consulta configuração de usinas hidrelétricas (REEs, volumes iniciais)",
        "example_code": """
from inewave.newave import Confhd
import os

# Ler arquivo
confhd_path = os.path.join(deck_path, "CONFHD.DAT")
confhd = Confhd.read(confhd_path)

# Acessar configuração de usinas
usinas_df = confhd.usinas

# Filtrar por usina
df_usina = usinas_df[usinas_df['codigo_usina'] == 1]

# Filtrar por REE
df_ree = usinas_df[usinas_df['codigo_ree'] == 1]

# Colunas principais: codigo_usina, nome_usina, codigo_ree, volume_inicial
""",
        "columns": ["codigo_usina", "nome_usina", "codigo_ree", "volume_inicial"],
        "queries": [
            "configuração hidrelétrica",
            "REEs das usinas",
            "volumes iniciais",
            "CONFHD"
        ]
    },
    "VazoesTool": {
        "category": "Dados Hidrelétricos",
        "file": "VAZOES.DAT",
        "class": "Vazoes",
        "properties": ["vazoes"],
        "description": "Consulta vazões históricas por posto",
        "example_code": """
from inewave.newave import Vazoes, Confhd
import os

# Ler arquivo
vazoes_path = os.path.join(deck_path, "VAZOES.DAT")
vazoes = Vazoes.read(vazoes_path)

# Acessar vazões (DataFrame: linhas = meses, colunas = postos)
df_vazoes = vazoes.vazoes

# Acessar vazões de um posto específico
posto_1 = df_vazoes[1]  # Série de vazões do posto 1

# Para buscar posto por nome de usina, usar CONFHD
confhd_path = os.path.join(deck_path, "CONFHD.DAT")
confhd = Confhd.read(confhd_path)

if confhd.usinas is not None:
    # Mapear nome de usina para posto
    usinas_df = confhd.usinas[['posto', 'nome_usina']].drop_duplicates()
    # Buscar posto por nome
    posto_usina = usinas_df[usinas_df['nome_usina'].str.contains('Furnas', case=False)]
""",
        "columns": ["posto (colunas)", "mês (linhas)"],
        "queries": [
            "vazões históricas",
            "vazões do posto",
            "série de vazões",
            "vazões da usina"
        ]
    },
    "DsvaguaTool": {
        "category": "Dados Hidrelétricos",
        "file": "DSVAGUA.DAT",
        "class": "Dsvagua",
        "properties": ["desvios"],
        "description": "Consulta desvios de água entre usinas",
        "example_code": """
from inewave.newave import Dsvagua, Confhd
import os

# Ler arquivo
dsvagua_path = os.path.join(deck_path, "DSVAGUA.DAT")
dsvagua = Dsvagua.read(dsvagua_path)

# Acessar desvios
df_desvios = dsvagua.desvios

# Para mapear códigos para nomes, usar CONFHD
confhd_path = os.path.join(deck_path, "CONFHD.DAT")
confhd = Confhd.read(confhd_path)

if confhd.usinas is not None:
    mapeamento = confhd.usinas[['codigo_usina', 'nome_usina']].drop_duplicates()
""",
        "columns": ["codigo_usina_origem", "codigo_usina_destino", "percentual"],
        "queries": [
            "desvios de água",
            "desvio entre usinas",
            "DSVAGUA"
        ]
    },
    "LimitesIntercambioTool": {
        "category": "Dados de Sistema",
        "file": "SISTEMA.DAT",
        "class": "Sistema",
        "properties": ["limites_intercambio"],
        "description": "Consulta limites de intercâmbio entre submercados",
        "example_code": """
from inewave.newave import Sistema
import os

# Ler arquivo
sistema_path = os.path.join(deck_path, "SISTEMA.DAT")
sistema = Sistema.read(sistema_path)

# Acessar limites de intercâmbio
df_limites = sistema.limites_intercambio

# Filtrar por submercado de origem
df_de = df_limites[df_limites['submercado_de'] == 1]

# Filtrar por submercado de destino
df_para = df_limites[df_limites['submercado_para'] == 2]

# Filtrar por tipo: 0 = limite máximo, 1 = intercâmbio mínimo obrigatório
df_maximo = df_limites[df_limites['sentido'] == 0]
df_minimo = df_limites[df_limites['sentido'] == 1]
""",
        "columns": ["submercado_de", "submercado_para", "sentido", "valor", "ano", "mes"],
        "queries": [
            "limites de intercâmbio",
            "intercâmbio entre submercados",
            "limite máximo de intercâmbio",
            "intercâmbio mínimo obrigatório"
        ]
    },
    "AgrintTool": {
        "category": "Dados de Sistema",
        "file": "AGRINT.DAT",
        "class": "Agrint",
        "properties": ["agrupamentos", "limites_agrupamentos"],
        "description": "Consulta agrupamentos de intercâmbio e restrições lineares",
        "example_code": """
from inewave.newave import Agrint
import os

# Ler arquivo
agrint_path = os.path.join(deck_path, "AGRINT.DAT")
agrint = Agrint.read(agrint_path)

# Acessar agrupamentos
df_agrupamentos = agrint.agrupamentos

# Acessar limites de agrupamentos
df_limites = agrint.limites_agrupamentos

# Filtrar por agrupamento específico
df_agr_1 = df_agrupamentos[df_agrupamentos['codigo_agrupamento'] == 1]

# Filtrar por patamar
df_pat_1 = df_limites[df_limites['patamar'] == 1]
""",
        "columns": ["codigo_agrupamento", "codigo_intercambio", "coeficiente", "patamar", "limite"],
        "queries": [
            "agrupamentos de intercâmbio",
            "restrições lineares",
            "corredor de transmissão",
            "limite combinado",
            "AGRINT"
        ]
    },
    "UsinasNaoSimuladasTool": {
        "category": "Dados de Sistema",
        "file": "SISTEMA.DAT",
        "class": "Sistema",
        "properties": ["geracao_usinas_nao_simuladas", "custo_deficit"],
        "description": "Consulta geração de usinas não simuladas",
        "example_code": """
from inewave.newave import Sistema
import os

# Ler arquivo
sistema_path = os.path.join(deck_path, "SISTEMA.DAT")
sistema = Sistema.read(sistema_path)

# Acessar geração de usinas não simuladas
df_geracao = sistema.geracao_usinas_nao_simuladas

# Filtrar por submercado
df_sudeste = df_geracao[df_geracao['codigo_submercado'] == 1]

# Filtrar por bloco
df_bloco_1 = df_geracao[df_geracao['bloco'] == 1]

# Obter lista de submercados
if sistema.custo_deficit is not None:
    subsistemas = sistema.custo_deficit[['codigo_submercado', 'nome_submercado']].drop_duplicates()
""",
        "columns": ["codigo_submercado", "nome_submercado", "bloco", "fonte", "ano", "mes", "valor"],
        "queries": [
            "geração de usinas não simuladas",
            "usinas não simuladas",
            "geração não simulada"
        ]
    },
    "RestricaoEletricaTool": {
        "category": "Dados de Sistema",
        "file": "restricao-eletrica.csv",
        "class": "RestricaoEletrica",
        "properties": ["restricoes", "horizontes", "limites"],
        "description": "Consulta restrições elétricas (arquivo CSV customizado)",
        "example_code": """
from app.utils.restricao_eletrica import RestricaoEletrica
import os

# Ler arquivo CSV
csv_path = os.path.join(deck_path, "restricao-eletrica.csv")
re_obj = RestricaoEletrica.read(csv_path)

# Acessar propriedades
df_restricoes = re_obj.restricoes
df_horizontes = re_obj.horizontes
df_limites = re_obj.limites

# Filtrar por tipo de restrição
# (estrutura depende do formato do CSV)
""",
        "columns": ["depende do formato do CSV"],
        "queries": [
            "restrições elétricas",
            "restrição elétrica",
            "restricao-eletrica.csv"
        ]
    }
}


def generate_markdown_documentation():
    """Gera documentação Markdown focada em snippets de código práticos."""
    
    # Organizar por categoria
    categories = {}
    for tool_name, doc in TOOLS_DOCUMENTATION.items():
        category = doc["category"]
        if category not in categories:
            categories[category] = []
        categories[category].append((tool_name, doc))
    
    # Gerar Markdown
    markdown = """# Snippets de Código: Tools e inewave

Esta documentação contém snippets de código práticos e funcionais para usar a biblioteca `inewave` e acessar dados NEWAVE. Use estes exemplos como base para gerar código Python que responde perguntas sobre decks NEWAVE.

Cada snippet mostra o padrão completo de uso, desde a leitura do arquivo até o processamento e retorno dos dados.

## Índice por Categoria

"""
    
    # Adicionar índice
    for category, tools in categories.items():
        markdown += f"- **{category}**\n"
        for tool_name, _ in tools:
            markdown += f"  - [{tool_name}](#{tool_name.lower().replace('tool', '')})\n"
        markdown += "\n"
    
    # Adicionar documentação de cada tool
    for category, tools in categories.items():
        markdown += f"\n---\n\n## {category}\n\n"
        
        for tool_name, doc in tools:
            # Gerar snippet completo e funcional
            snippet = generate_complete_snippet(tool_name, doc)
            
            markdown += f"""### {tool_name.replace('Tool', '')}

**Arquivo**: `{doc['file']}` | **Classe**: `{doc['class']}`

#### Snippet Completo

```python
{snippet}
```

#### Colunas Disponíveis

{', '.join(doc['columns'])}

#### Queries Relacionadas

"""
            for query in doc['queries']:
                markdown += f"- `{query}`\n"
            
            markdown += "\n---\n\n"
    
    return markdown


def generate_complete_snippet(tool_name: str, doc: dict) -> str:
    """Gera um snippet completo e funcional para uma tool."""
    
    # Usar o example_code diretamente (já está bem formatado)
    base_snippet = doc['example_code'].strip()
    
    # Identificar a variável DataFrame principal e se já tem conversão
    df_var = None
    has_conversion = "to_dict(orient='records')" in base_snippet or "resultado = " in base_snippet
    
    # Tentar encontrar variável DataFrame principal
    for line in base_snippet.split('\n'):
        if 'df_resultado' in line and '=' in line:
            df_var = "df_resultado"
            break
        elif 'df_' in line and '=' in line and not line.strip().startswith('#'):
            # Pegar primeira variável df_ encontrada
            parts = line.split('=')
            if len(parts) > 0:
                var_name = parts[0].strip()
                if var_name.startswith('df_'):
                    df_var = var_name
                    break
    
    # Se não encontrou, usar padrão
    if not df_var:
        df_var = "df_resultado"
    
    # Se já tem conversão completa (com tratamento de tipos), retornar como está
    if has_conversion and "pd.isna" in base_snippet:
        return base_snippet
    
    # Adicionar conversão final com tratamento de tipos
    if has_conversion:
        # Já tem to_dict, só adicionar tratamento de tipos
        snippet = base_snippet + f"""

# Converter tipos para JSON-serializable (se houver dados)
if resultado:
    for record in resultado:
        for key, value in record.items():
            if pd.isna(value):
                record[key] = None
            elif isinstance(value, (pd.Timestamp, pd.DatetimeTZDtype)):
                record[key] = value.isoformat() if hasattr(value, 'isoformat') else str(value)
    
    # Retornar resultado
    print(f"Total de registros: {{len(resultado)}}")
    for item in resultado[:10]:  # Preview dos primeiros 10
        print(item)
else:
    print("Nenhum dado encontrado")
"""
    else:
        # Não tem conversão, adicionar tudo
        snippet = base_snippet + f"""

# Converter para formato de resposta (lista de dicionários)
if not {df_var}.empty:
    resultado = {df_var}.to_dict(orient='records')
    # Converter tipos para JSON-serializable
    for record in resultado:
        for key, value in record.items():
            if pd.isna(value):
                record[key] = None
            elif isinstance(value, (pd.Timestamp, pd.DatetimeTZDtype)):
                record[key] = value.isoformat() if hasattr(value, 'isoformat') else str(value)
    
    # Retornar resultado
    print(f"Total de registros: {{len(resultado)}}")
    for item in resultado[:10]:  # Preview dos primeiros 10
        print(item)
else:
    print("Nenhum dado encontrado")
    resultado = []
"""
    
    return snippet


def main():
    """Função principal."""
    print("Gerando documentação de tools e inewave...")
    
    # Gerar documentação
    markdown = generate_markdown_documentation()
    
    # Salvar arquivo
    output_path = BASE_DIR / "docs" / "tools_inewave.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(markdown)
    
    print(f"[OK] Documentacao gerada em: {output_path}")
    print(f"   Total de tools documentadas: {len(TOOLS_DOCUMENTATION)}")
    
    # Validar que todas as tools foram documentadas
    from app.tools import TOOLS_REGISTRY_SINGLE
    
    documented_tools = set(TOOLS_DOCUMENTATION.keys())
    registry_tools = set([tool.__name__ for tool in TOOLS_REGISTRY_SINGLE])
    
    missing = registry_tools - documented_tools
    if missing:
        print(f"[WARN] Tools nao documentadas: {missing}")
    else:
        print("[OK] Todas as tools foram documentadas")


if __name__ == "__main__":
    main()

