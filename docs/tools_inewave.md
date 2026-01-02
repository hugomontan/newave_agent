# Snippets de Código: Tools e inewave

Esta documentação contém snippets de código práticos e funcionais para usar a biblioteca `inewave` e acessar dados NEWAVE. Use estes exemplos como base para gerar código Python que responde perguntas sobre decks NEWAVE.

Cada snippet mostra o padrão completo de uso, desde a leitura do arquivo até o processamento e retorno dos dados.

## Índice por Categoria

- **Dados de Mercado e Demanda**
  - [CargaMensalTool](#cargamensal)
  - [CadicTool](#cadic)

- **Dados Térmicos**
  - [ClastValoresTool](#clastvalores)
  - [ExptOperacaoTool](#exptoperacao)
  - [TermCadastroTool](#termcadastro)

- **Dados Hidrelétricos**
  - [ModifOperacaoTool](#modifoperacao)
  - [HidrCadastroTool](#hidrcadastro)
  - [ConfhdTool](#confhd)
  - [VazoesTool](#vazoes)
  - [DsvaguaTool](#dsvagua)

- **Dados de Sistema**
  - [LimitesIntercambioTool](#limitesintercambio)
  - [AgrintTool](#agrint)
  - [UsinasNaoSimuladasTool](#usinasnaosimuladas)
  - [RestricaoEletricaTool](#restricaoeletrica)


---

## Dados de Mercado e Demanda

### CargaMensal

**Arquivo**: `SISTEMA.DAT` | **Classe**: `Sistema`

#### Snippet Completo

```python
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

# Converter tipos para JSON-serializable (se houver dados)
if resultado:
    for record in resultado:
        for key, value in record.items():
            if pd.isna(value):
                record[key] = None
            elif isinstance(value, (pd.Timestamp, pd.DatetimeTZDtype)):
                record[key] = value.isoformat() if hasattr(value, 'isoformat') else str(value)
    
    # Retornar resultado
    print(f"Total de registros: {len(resultado)}")
    for item in resultado[:10]:  # Preview dos primeiros 10
        print(item)
else:
    print("Nenhum dado encontrado")

```

#### Colunas Disponíveis

codigo_submercado, nome_submercado, ano, mes, valor

#### Queries Relacionadas

- `cargas mensais do Sudeste`
- `demanda do Nordeste em 2025`
- `cargas por submercado`
- `mercado de energia`

---

### Cadic

**Arquivo**: `C_ADIC.DAT` | **Classe**: `Cadic`

#### Snippet Completo

```python
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

# Converter tipos para JSON-serializable (se houver dados)
if resultado:
    for record in resultado:
        for key, value in record.items():
            if pd.isna(value):
                record[key] = None
            elif isinstance(value, (pd.Timestamp, pd.DatetimeTZDtype)):
                record[key] = value.isoformat() if hasattr(value, 'isoformat') else str(value)
    
    # Retornar resultado
    print(f"Total de registros: {len(resultado)}")
    for item in resultado[:10]:  # Preview dos primeiros 10
        print(item)
else:
    print("Nenhum dado encontrado")

```

#### Colunas Disponíveis

codigo_submercado, nome_submercado, ano, mes, valor

#### Queries Relacionadas

- `cargas adicionais`
- `carga adicional do Sudeste`
- `C_ADIC`

---


---

## Dados Térmicos

### ClastValores

**Arquivo**: `CLAST.DAT` | **Classe**: `Clast`

#### Snippet Completo

```python
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

# Converter tipos para JSON-serializable (se houver dados)
if resultado:
    for record in resultado:
        for key, value in record.items():
            if pd.isna(value):
                record[key] = None
            elif isinstance(value, (pd.Timestamp, pd.DatetimeTZDtype)):
                record[key] = value.isoformat() if hasattr(value, 'isoformat') else str(value)
    
    # Retornar resultado
    print(f"Total de registros: {len(resultado)}")
    for item in resultado[:10]:  # Preview dos primeiros 10
        print(item)
else:
    print("Nenhum dado encontrado")

```

#### Colunas Disponíveis

codigo_usina, nome_usina, tipo_combustivel, indice_ano_estudo, valor

#### Queries Relacionadas

- `custo das classes térmicas`
- `CVU`
- `custo variável unitário`
- `custos estruturais`
- `custos conjunturais`

---

### ExptOperacao

**Arquivo**: `EXPT.DAT` | **Classe**: `Expt`

#### Snippet Completo

```python
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

# Converter para formato de resposta (lista de dicionários)
if not df_expansoes.empty:
    resultado = df_expansoes.to_dict(orient='records')
    # Converter tipos para JSON-serializable
    for record in resultado:
        for key, value in record.items():
            if pd.isna(value):
                record[key] = None
            elif isinstance(value, (pd.Timestamp, pd.DatetimeTZDtype)):
                record[key] = value.isoformat() if hasattr(value, 'isoformat') else str(value)
    
    # Retornar resultado
    print(f"Total de registros: {len(resultado)}")
    for item in resultado[:10]:  # Preview dos primeiros 10
        print(item)
else:
    print("Nenhum dado encontrado")
    resultado = []

```

#### Colunas Disponíveis

codigo_usina, nome_usina, tipo, modificacao, data_inicio, data_fim

#### Queries Relacionadas

- `expansões térmicas`
- `repotenciações`
- `desativações de térmicas`
- `EXPT`

---

### TermCadastro

**Arquivo**: `TERM.DAT` | **Classe**: `Term`

#### Snippet Completo

```python
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

# Converter para formato de resposta (lista de dicionários)
if not df_usinas.empty:
    resultado = df_usinas.to_dict(orient='records')
    # Converter tipos para JSON-serializable
    for record in resultado:
        for key, value in record.items():
            if pd.isna(value):
                record[key] = None
            elif isinstance(value, (pd.Timestamp, pd.DatetimeTZDtype)):
                record[key] = value.isoformat() if hasattr(value, 'isoformat') else str(value)
    
    # Retornar resultado
    print(f"Total de registros: {len(resultado)}")
    for item in resultado[:10]:  # Preview dos primeiros 10
        print(item)
else:
    print("Nenhum dado encontrado")
    resultado = []

```

#### Colunas Disponíveis

codigo_usina, nome_usina, pot_efetiva, fcmax, teif, ip

#### Queries Relacionadas

- `cadastro térmica`
- `informações da usina térmica`
- `potência efetiva`
- `fator capacidade máximo`
- `TERM.DAT`

---


---

## Dados Hidrelétricos

### ModifOperacao

**Arquivo**: `MODIF.DAT` | **Classe**: `Modif`

#### Snippet Completo

```python
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

# Converter para formato de resposta (lista de dicionários)
if not df_resultado.empty:
    resultado = df_resultado.to_dict(orient='records')
    # Converter tipos para JSON-serializable
    for record in resultado:
        for key, value in record.items():
            if pd.isna(value):
                record[key] = None
            elif isinstance(value, (pd.Timestamp, pd.DatetimeTZDtype)):
                record[key] = value.isoformat() if hasattr(value, 'isoformat') else str(value)
    
    # Retornar resultado
    print(f"Total de registros: {len(resultado)}")
    for item in resultado[:10]:  # Preview dos primeiros 10
        print(item)
else:
    print("Nenhum dado encontrado")
    resultado = []

```

#### Colunas Disponíveis

codigo_usina, nome_usina, vazao, volume, data_inicio, data_fim

#### Queries Relacionadas

- `vazão mínima`
- `volume mínimo`
- `modificações hídricas`
- `vazão mínima pré-estabelecida`
- `volumes mínimos das usinas`

---

### HidrCadastro

**Arquivo**: `HIDR.DAT` | **Classe**: `Hidr`

#### Snippet Completo

```python
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

# Converter para formato de resposta (lista de dicionários)
if not df_resultado.empty:
    resultado = df_resultado.to_dict(orient='records')
    # Converter tipos para JSON-serializable
    for record in resultado:
        for key, value in record.items():
            if pd.isna(value):
                record[key] = None
            elif isinstance(value, (pd.Timestamp, pd.DatetimeTZDtype)):
                record[key] = value.isoformat() if hasattr(value, 'isoformat') else str(value)
    
    # Retornar resultado
    print(f"Total de registros: {len(resultado)}")
    for item in resultado[:10]:  # Preview dos primeiros 10
        print(item)
else:
    print("Nenhum dado encontrado")
    resultado = []

```

#### Colunas Disponíveis

nome_usina, posto, submercado, volume_minimo, volume_maximo, potencia_nominal_conjunto_1, produtibilidade_especifica

#### Queries Relacionadas

- `cadastro hidrelétrica`
- `informações da usina hidrelétrica`
- `potência instalada`
- `volumes da usina`
- `HIDR.DAT`

---

### Confhd

**Arquivo**: `CONFHD.DAT` | **Classe**: `Confhd`

#### Snippet Completo

```python
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

# Converter para formato de resposta (lista de dicionários)
if not df_usina.empty:
    resultado = df_usina.to_dict(orient='records')
    # Converter tipos para JSON-serializable
    for record in resultado:
        for key, value in record.items():
            if pd.isna(value):
                record[key] = None
            elif isinstance(value, (pd.Timestamp, pd.DatetimeTZDtype)):
                record[key] = value.isoformat() if hasattr(value, 'isoformat') else str(value)
    
    # Retornar resultado
    print(f"Total de registros: {len(resultado)}")
    for item in resultado[:10]:  # Preview dos primeiros 10
        print(item)
else:
    print("Nenhum dado encontrado")
    resultado = []

```

#### Colunas Disponíveis

codigo_usina, nome_usina, codigo_ree, volume_inicial

#### Queries Relacionadas

- `configuração hidrelétrica`
- `REEs das usinas`
- `volumes iniciais`
- `CONFHD`

---

### Vazoes

**Arquivo**: `VAZOES.DAT` | **Classe**: `Vazoes`

#### Snippet Completo

```python
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

# Converter para formato de resposta (lista de dicionários)
if not df_vazoes.empty:
    resultado = df_vazoes.to_dict(orient='records')
    # Converter tipos para JSON-serializable
    for record in resultado:
        for key, value in record.items():
            if pd.isna(value):
                record[key] = None
            elif isinstance(value, (pd.Timestamp, pd.DatetimeTZDtype)):
                record[key] = value.isoformat() if hasattr(value, 'isoformat') else str(value)
    
    # Retornar resultado
    print(f"Total de registros: {len(resultado)}")
    for item in resultado[:10]:  # Preview dos primeiros 10
        print(item)
else:
    print("Nenhum dado encontrado")
    resultado = []

```

#### Colunas Disponíveis

posto (colunas), mês (linhas)

#### Queries Relacionadas

- `vazões históricas`
- `vazões do posto`
- `série de vazões`
- `vazões da usina`

---

### Dsvagua

**Arquivo**: `DSVAGUA.DAT` | **Classe**: `Dsvagua`

#### Snippet Completo

```python
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

# Converter para formato de resposta (lista de dicionários)
if not df_desvios.empty:
    resultado = df_desvios.to_dict(orient='records')
    # Converter tipos para JSON-serializable
    for record in resultado:
        for key, value in record.items():
            if pd.isna(value):
                record[key] = None
            elif isinstance(value, (pd.Timestamp, pd.DatetimeTZDtype)):
                record[key] = value.isoformat() if hasattr(value, 'isoformat') else str(value)
    
    # Retornar resultado
    print(f"Total de registros: {len(resultado)}")
    for item in resultado[:10]:  # Preview dos primeiros 10
        print(item)
else:
    print("Nenhum dado encontrado")
    resultado = []

```

#### Colunas Disponíveis

codigo_usina_origem, codigo_usina_destino, percentual

#### Queries Relacionadas

- `desvios de água`
- `desvio entre usinas`
- `DSVAGUA`

---


---

## Dados de Sistema

### LimitesIntercambio

**Arquivo**: `SISTEMA.DAT` | **Classe**: `Sistema`

#### Snippet Completo

```python
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

# Converter para formato de resposta (lista de dicionários)
if not df_limites.empty:
    resultado = df_limites.to_dict(orient='records')
    # Converter tipos para JSON-serializable
    for record in resultado:
        for key, value in record.items():
            if pd.isna(value):
                record[key] = None
            elif isinstance(value, (pd.Timestamp, pd.DatetimeTZDtype)):
                record[key] = value.isoformat() if hasattr(value, 'isoformat') else str(value)
    
    # Retornar resultado
    print(f"Total de registros: {len(resultado)}")
    for item in resultado[:10]:  # Preview dos primeiros 10
        print(item)
else:
    print("Nenhum dado encontrado")
    resultado = []

```

#### Colunas Disponíveis

submercado_de, submercado_para, sentido, valor, ano, mes

#### Queries Relacionadas

- `limites de intercâmbio`
- `intercâmbio entre submercados`
- `limite máximo de intercâmbio`
- `intercâmbio mínimo obrigatório`

---

### Agrint

**Arquivo**: `AGRINT.DAT` | **Classe**: `Agrint`

#### Snippet Completo

```python
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

# Converter para formato de resposta (lista de dicionários)
if not df_agrupamentos.empty:
    resultado = df_agrupamentos.to_dict(orient='records')
    # Converter tipos para JSON-serializable
    for record in resultado:
        for key, value in record.items():
            if pd.isna(value):
                record[key] = None
            elif isinstance(value, (pd.Timestamp, pd.DatetimeTZDtype)):
                record[key] = value.isoformat() if hasattr(value, 'isoformat') else str(value)
    
    # Retornar resultado
    print(f"Total de registros: {len(resultado)}")
    for item in resultado[:10]:  # Preview dos primeiros 10
        print(item)
else:
    print("Nenhum dado encontrado")
    resultado = []

```

#### Colunas Disponíveis

codigo_agrupamento, codigo_intercambio, coeficiente, patamar, limite

#### Queries Relacionadas

- `agrupamentos de intercâmbio`
- `restrições lineares`
- `corredor de transmissão`
- `limite combinado`
- `AGRINT`

---

### UsinasNaoSimuladas

**Arquivo**: `SISTEMA.DAT` | **Classe**: `Sistema`

#### Snippet Completo

```python
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

# Converter para formato de resposta (lista de dicionários)
if not df_geracao.empty:
    resultado = df_geracao.to_dict(orient='records')
    # Converter tipos para JSON-serializable
    for record in resultado:
        for key, value in record.items():
            if pd.isna(value):
                record[key] = None
            elif isinstance(value, (pd.Timestamp, pd.DatetimeTZDtype)):
                record[key] = value.isoformat() if hasattr(value, 'isoformat') else str(value)
    
    # Retornar resultado
    print(f"Total de registros: {len(resultado)}")
    for item in resultado[:10]:  # Preview dos primeiros 10
        print(item)
else:
    print("Nenhum dado encontrado")
    resultado = []

```

#### Colunas Disponíveis

codigo_submercado, nome_submercado, bloco, fonte, ano, mes, valor

#### Queries Relacionadas

- `geração de usinas não simuladas`
- `usinas não simuladas`
- `geração não simulada`

---

### RestricaoEletrica

**Arquivo**: `restricao-eletrica.csv` | **Classe**: `RestricaoEletrica`

#### Snippet Completo

```python
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

# Converter para formato de resposta (lista de dicionários)
if not df_restricoes.empty:
    resultado = df_restricoes.to_dict(orient='records')
    # Converter tipos para JSON-serializable
    for record in resultado:
        for key, value in record.items():
            if pd.isna(value):
                record[key] = None
            elif isinstance(value, (pd.Timestamp, pd.DatetimeTZDtype)):
                record[key] = value.isoformat() if hasattr(value, 'isoformat') else str(value)
    
    # Retornar resultado
    print(f"Total de registros: {len(resultado)}")
    for item in resultado[:10]:  # Preview dos primeiros 10
        print(item)
else:
    print("Nenhum dado encontrado")
    resultado = []

```

#### Colunas Disponíveis

depende do formato do CSV

#### Queries Relacionadas

- `restrições elétricas`
- `restrição elétrica`
- `restricao-eletrica.csv`

---

