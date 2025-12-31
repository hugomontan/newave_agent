# Documentação de Contexto das Tools NEWAVE

Este documento fornece contexto completo sobre as tools disponíveis, arquivos que acessam, estruturas de dados e exemplos de código para uso pelo LLM no modo LLM Mode.

## Visão Geral

As tools são implementações pré-programadas que acessam arquivos NEWAVE usando a biblioteca inewave. Este documento serve como referência para que o LLM possa gerar código similar sem executar as tools diretamente.

**Importante**: Este documento descreve o que cada tool faz e como acessar os mesmos dados programaticamente. Use estas informações como guia para gerar código Python que acessa os arquivos NEWAVE diretamente.

---

## Tool 1: ClastValoresTool

### O que faz
Consulta valores estruturais e conjunturais do CLAST.DAT:
- **Valores estruturais**: Custos base das classes térmicas por ano (CVU - Custo Variável Unitário)
- **Valores conjunturais**: Modificações sazonais dos custos

### Arquivo acessado
- `CLAST.DAT`

### Classe inewave
```python
from inewave.newave import Clast
```

### Propriedades disponíveis
- `clast.usinas` (DataFrame): Valores estruturais
  - Colunas principais: `codigo_usina`, `nome_usina`, `tipo_combustivel`, `indice_ano_estudo`, `valor` (custo em $/MWh)
- `clast.modificacoes` (DataFrame): Valores conjunturais (modificações sazonais)
  - Colunas principais: `codigo_usina`, `data_inicio`, `data_fim`, `custo`

### Exemplo de código
```python
from inewave.newave import Clast
import os
import pandas as pd

deck_path = "/path/to/deck"
clast_path = os.path.join(deck_path, "CLAST.DAT")

# Ler arquivo
clast = Clast.read(clast_path)

# Acessar valores estruturais (custos base)
df_estrutural = clast.usinas
# Filtrar por classe específica (ex: código 211)
df_filtrado = df_estrutural[df_estrutural['codigo_usina'] == 211]

# Acessar valores conjunturais (modificações sazonais)
df_conjuntural = clast.modificacoes
# Filtrar por classe
df_conj_filtrado = df_conjuntural[df_conjuntural['codigo_usina'] == 211]

# Para CVU, sempre retornar TODOS OS ANOS (não filtrar por ano)
# O campo 'indice_ano_estudo' contém os anos
```

### Queries típicas
- "CVU da classe ANGRA 1"
- "custos das classes térmicas"
- "valores estruturais do CLAST"
- "modificações sazonais da classe 211"

---

## Tool 2: CargaMensalTool

### O que faz
Consulta dados de carga mensal (demanda) por submercado.

### Arquivo acessado
- `SISTEMA.DAT`

### Classe inewave
```python
from inewave.newave import Sistema
```

### Propriedades disponíveis
- `sistema.mercado_energia` (DataFrame): Carga mensal por submercado
  - Colunas: `codigo_submercado`, `nome_submercado`, `ano`, `mes`, `patamar`, `valor` (MWmédio)
- `sistema.custo_deficit` (DataFrame): Informações sobre submercados
  - Colunas: `codigo_submercado`, `nome_submercado`

### Exemplo de código
```python
from inewave.newave import Sistema
import os
import pandas as pd

deck_path = "/path/to/deck"
sistema_path = os.path.join(deck_path, "SISTEMA.DAT")

# Ler arquivo
sistema = Sistema.read(sistema_path)

# Acessar carga mensal
df_mercado = sistema.mercado_energia

# Filtrar por submercado (ex: Sudeste = código 1)
df_sudeste = df_mercado[df_mercado['codigo_submercado'] == 1]

# Agrupar por ano
df_anual = df_mercado.groupby(['codigo_submercado', 'ano'])['valor'].sum()

# Listar todos os submercados disponíveis
if sistema.custo_deficit is not None:
    subsistemas = sistema.custo_deficit[['codigo_submercado', 'nome_submercado']].drop_duplicates()
```

### Queries típicas
- "cargas mensais do Sudeste"
- "demanda mensal por submercado"
- "carga do subsistema 1"

---

## Tool 3: ExptOperacaoTool

### O que faz
Consulta dados de operação térmica do EXPT.DAT:
- Expansões de potência (POTEF)
- Geração mínima (GTMIN)
- Fator de capacidade (FCMAX)
- Indisponibilidades (IPTER, TEIFT)
- Desativações e repotenciações

### Arquivo acessado
- `EXPT.DAT`

### Classe inewave
```python
from inewave.newave import Expt
```

### Propriedades disponíveis
- `expt.expansoes` (DataFrame): Todas as modificações/expansões
  - Colunas principais: `codigo_usina`, `nome_usina`, `tipo` (POTEF, GTMIN, FCMAX, IPTER, TEIFT), `data`, `modificacao`

### Exemplo de código
```python
from inewave.newave import Expt
import os
import pandas as pd

deck_path = "/path/to/deck"
expt_path = os.path.join(deck_path, "EXPT.DAT")

# Ler arquivo
expt = Expt.read(expt_path)

# Acessar expansões
df_expansoes = expt.expansoes

# Filtrar por tipo de modificação
df_potef = df_expansoes[df_expansoes['tipo'] == 'POTEF']  # Potência efetiva
df_gtmin = df_expansoes[df_expansoes['tipo'] == 'GTMIN']  # Geração mínima
df_fcmax = df_expansoes[df_expansoes['tipo'] == 'FCMAX']  # Fator de capacidade

# Filtrar por usina específica
df_usina = df_expansoes[df_expansoes['codigo_usina'] == 1]

# Desativações: POTEF=0 ou FCMAX=0
desativacoes = df_expansoes[
    ((df_expansoes['tipo'] == 'POTEF') & (df_expansoes['modificacao'] == 0)) |
    ((df_expansoes['tipo'] == 'FCMAX') & (df_expansoes['modificacao'] == 0))
]

# Repotenciações: POTEF > 0
repotenciacoes = df_expansoes[
    (df_expansoes['tipo'] == 'POTEF') & (df_expansoes['modificacao'] > 0)
]
```

### Queries típicas
- "expansões térmicas"
- "potência efetiva das térmicas"
- "desativações de usinas térmicas"
- "repotenciações no EXPT"

---

## Tool 4: ModifOperacaoTool

### O que faz
Consulta dados de operação hídrica do MODIF.DAT:
- Volumes (mínimo, máximo)
- Vazões (mínima, máxima)
- Níveis (canal de fuga, montante)
- Turbinamento (máximo, mínimo, por patamar)
- Potência efetiva
- Indisponibilidades

### Arquivo acessado
- `MODIF.DAT`

### Classe inewave
```python
from inewave.newave import Modif
```

### Propriedades disponíveis
- `modif.modificacoes` (DataFrame): Todas as modificações
  - Colunas principais: `codigo_usina`, `nome_usina`, `tipo` (VOLMIN, VOLMAX, VAZMIN, VAZMAX, etc.), `data_inicio`, `data_fim`, `modificacao`

### Exemplo de código
```python
from inewave.newave import Modif
import os
import pandas as pd

deck_path = "/path/to/deck"
modif_path = os.path.join(deck_path, "MODIF.DAT")

# Ler arquivo
modif = Modif.read(modif_path)

# Acessar modificações
df_modificacoes = modif.modificacoes

# Filtrar por tipo
df_vazmin = df_modificacoes[df_modificacoes['tipo'] == 'VAZMIN']  # Vazão mínima
df_volmin = df_modificacoes[df_modificacoes['tipo'] == 'VOLMIN']  # Volume mínimo
df_volmax = df_modificacoes[df_modificacoes['tipo'] == 'VOLMAX']  # Volume máximo

# Filtrar por usina específica
df_usina = df_modificacoes[df_modificacoes['codigo_usina'] == 1]
```

### Queries típicas
- "vazão mínima de Furnas"
- "volumes mínimos das usinas"
- "modificações hídricas"

---

## Tool 5: LimitesIntercambioTool

### O que faz
Consulta limites de intercâmbio entre subsistemas.

### Arquivo acessado
- `SISTEMA.DAT`

### Classe inewave
```python
from inewave.newave import Sistema
```

### Propriedades disponíveis
- `sistema.limites_intercambio` (DataFrame): Limites de intercâmbio
  - Colunas principais: `submercado_de`, `submercado_para`, `patamar`, `valor` (limite em MW)

### Exemplo de código
```python
from inewave.newave import Sistema
import os
import pandas as pd

deck_path = "/path/to/deck"
sistema_path = os.path.join(deck_path, "SISTEMA.DAT")

# Ler arquivo
sistema = Sistema.read(sistema_path)

# Acessar limites de intercâmbio
df_limites = sistema.limites_intercambio

# Filtrar intercâmbio entre dois submercados específicos
df_intercambio = df_limites[
    (df_limites['submercado_de'] == 1) & 
    (df_limites['submercado_para'] == 2)
]

# Filtrar por patamar
df_patamar = df_limites[df_limites['patamar'] == 1]
```

### Queries típicas
- "limites entre Sudeste e Sul"
- "capacidade de intercâmbio"
- "limite máximo de intercâmbio"

---

## Tool 6: AgrintTool

### O que faz
Consulta agrupamentos de intercâmbio (restrições lineares compostas).

### Arquivo acessado
- `AGRINT.DAT`

### Classe inewave
```python
from inewave.newave import Agrint
```

### Propriedades disponíveis
- `agrint.agrupamentos` (DataFrame): Definição dos agrupamentos
  - Colunas principais: `agrupamento`, `submercado_de`, `submercado_para`, `coeficiente`
- `agrint.limites_agrupamentos` (DataFrame): Limites por agrupamento
  - Colunas principais: `agrupamento`, `patamar`, `valor` (limite em MW)

### Exemplo de código
```python
from inewave.newave import Agrint
import os
import pandas as pd

deck_path = "/path/to/deck"
agrint_path = os.path.join(deck_path, "AGRINT.DAT")

# Ler arquivo
agrint = Agrint.read(agrint_path)

# Acessar agrupamentos
df_agrupamentos = agrint.agrupamentos

# Acessar limites
df_limites = agrint.limites_agrupamentos

# Filtrar por agrupamento específico
df_agr1 = df_agrupamentos[df_agrupamentos['agrupamento'] == 1]
df_lim_agr1 = df_limites[df_limites['agrupamento'] == 1]
```

### Queries típicas
- "agrupamentos de intercâmbio"
- "restrições lineares de transmissão"
- "limites de agrupamento"

---

## Tool 7: VazoesTool

### O que faz
Consulta vazões históricas de postos fluviométricos.

### Arquivo acessado
- `VAZOES.DAT` (principal)
- `CONFHD.DAT` (para mapeamento usina → posto)

### Classe inewave
```python
from inewave.newave import Vazoes, Confhd
```

### Propriedades disponíveis
- `vazoes.vazoes` (DataFrame): Séries históricas de vazões
  - Colunas principais: `posto`, `ano`, `jan`, `fev`, `mar`, `abr`, `mai`, `jun`, `jul`, `ago`, `set`, `out`, `nov`, `dez` (valores em m³/s)

### Exemplo de código
```python
from inewave.newave import Vazoes, Confhd
import os
import pandas as pd

deck_path = "/path/to/deck"
vazoes_path = os.path.join(deck_path, "VAZOES.DAT")
confhd_path = os.path.join(deck_path, "CONFHD.DAT")

# Ler arquivos
vazoes = Vazoes.read(vazoes_path)
confhd = Confhd.read(confhd_path)

# Acessar vazões
df_vazoes = vazoes.vazoes

# Filtrar por posto específico
df_posto1 = df_vazoes[df_vazoes['posto'] == 1]

# Para buscar por nome de usina, primeiro mapear usina → posto via CONFHD
if confhd.usinas is not None:
    # Criar mapeamento nome_usina → posto
    mapeamento = confhd.usinas[['nome_usina', 'posto']].drop_duplicates()
    # Buscar posto da usina
    posto_usina = mapeamento[mapeamento['nome_usina'] == 'FURNAS']['posto'].values[0]
    df_vazoes_usina = df_vazoes[df_vazoes['posto'] == posto_usina]
```

### Queries típicas
- "vazões de Itaipu"
- "série histórica do posto 1"
- "vazões históricas"

---

## Tool 8: CadicTool

### O que faz
Consulta cargas e ofertas adicionais por subsistema.
- Valores positivos = cargas adicionais (aumentam demanda)
- Valores negativos = ofertas adicionais (reduzem demanda)

### Arquivo acessado
- `C_ADIC.DAT`

### Classe inewave
```python
from inewave.newave import Cadic
```

### Propriedades disponíveis
- `cadic.cargas` (DataFrame): Cargas e ofertas adicionais
  - Colunas principais: `codigo_submercado`, `nome_submercado`, `mes`, `ano`, `valor` (MWmédio)

### Exemplo de código
```python
from inewave.newave import Cadic
import os
import pandas as pd

deck_path = "/path/to/deck"
cadic_path = os.path.join(deck_path, "C_ADIC.DAT")

# Ler arquivo
cadic = Cadic.read(cadic_path)

# Acessar cargas adicionais
df_cargas = cadic.cargas

# Filtrar por submercado
df_sudeste = df_cargas[df_cargas['codigo_submercado'] == 1]

# Separar cargas (positivas) e ofertas (negativas)
cargas_adicionais = df_cargas[df_cargas['valor'] > 0]
ofertas_adicionais = df_cargas[df_cargas['valor'] < 0]
```

### Queries típicas
- "cargas adicionais do Sudeste"
- "ofertas adicionais"
- "cargas extras por submercado"

---

## Tool 9: HidrCadastroTool

### O que faz
Consulta informações cadastrais das usinas hidrelétricas (dados físicos e operacionais básicos).

### Arquivo acessado
- `HIDR.DAT` (arquivo binário)

### Classe inewave
```python
from inewave.newave import Hidr
```

### Propriedades disponíveis
- `hidr.cadastro` (DataFrame): Cadastro completo com 60+ colunas
  - Colunas principais: `nome_usina`, `posto`, `submercado`, `volume_minimo`, `volume_maximo`, `volume_vertedouro`, `potencia_nominal_conjunto_1` a `potencia_nominal_conjunto_5`, `produtibilidade_especifica`, `vazao_minima_historica`, etc.

### Exemplo de código
```python
from inewave.newave import Hidr
import os
import pandas as pd

deck_path = "/path/to/deck"
hidr_path = os.path.join(deck_path, "HIDR.DAT")

# Ler arquivo
hidr = Hidr.read(hidr_path)

# Acessar cadastro
df_cadastro = hidr.cadastro

# Filtrar por usina específica (usando índice, pois código = índice + 1)
# Exemplo: usina código 1 = índice 0
df_usina1 = df_cadastro.iloc[0:1]  # Primeira usina

# Filtrar por nome
df_furnas = df_cadastro[df_cadastro['nome_usina'] == 'FURNAS']

# Acessar colunas específicas
volumes = df_cadastro[['nome_usina', 'volume_minimo', 'volume_maximo']]
potencias = df_cadastro[['nome_usina', 'potencia_nominal_conjunto_1', 'potencia_nominal_conjunto_2']]
```

### Queries típicas
- "usinas hidrelétricas"
- "potência instalada"
- "volumes das usinas"
- "características da usina FURNAS"

---

## Tool 10: ConfhdTool

### O que faz
Consulta configuração de usinas hidrelétricas no estudo:
- Associação de usinas a REEs
- Status das usinas (EX, EE, NE, NC)
- Volume inicial armazenado
- Configurações de modificação

### Arquivo acessado
- `CONFHD.DAT`

### Classe inewave
```python
from inewave.newave import Confhd
```

### Propriedades disponíveis
- `confhd.usinas` (DataFrame): Configuração das usinas
  - Colunas principais: `codigo_usina`, `nome_usina`, `posto`, `ree`, `volume_inicial`, `status`, `modificacao`, `usina_jusante`, `ano_inicio_historico`, `ano_fim_historico`

### Exemplo de código
```python
from inewave.newave import Confhd
import os
import pandas as pd

deck_path = "/path/to/deck"
confhd_path = os.path.join(deck_path, "CONFHD.DAT")

# Ler arquivo
confhd = Confhd.read(confhd_path)

# Acessar configuração
df_usinas = confhd.usinas

# Filtrar por REE
df_ree1 = df_usinas[df_usinas['ree'] == 1]

# Filtrar por status
df_existentes = df_usinas[df_usinas['status'] == 'EX']  # Existentes
df_expansao = df_usinas[df_usinas['status'] == 'EE']  # Em expansão

# Filtrar por usina específica
df_usina = df_usinas[df_usinas['codigo_usina'] == 1]
```

### Queries típicas
- "configuração de usinas"
- "usinas por REE"
- "volume inicial das usinas"
- "status das usinas"

---

## Tool 11: DsvaguaTool

### O que faz
Consulta desvios de água para usos consuntivos.

### Arquivo acessado
- `DSVAGUA.DAT`
- `CONFHD.DAT` (para mapeamento código → nome)

### Classe inewave
```python
from inewave.newave import Dsvagua, Confhd
```

### Propriedades disponíveis
- `dsvagua.desvios` (DataFrame): Desvios de água
  - Colunas principais: `codigo_usina`, `data` (estágio), `valor` (desvio em m³/s)

### Exemplo de código
```python
from inewave.newave import Dsvagua, Confhd
import os
import pandas as pd

deck_path = "/path/to/deck"
dsvagua_path = os.path.join(deck_path, "DSVAGUA.DAT")
confhd_path = os.path.join(deck_path, "CONFHD.DAT")

# Ler arquivos
dsvagua = Dsvagua.read(dsvagua_path)
confhd = Confhd.read(confhd_path)

# Acessar desvios
df_desvios = dsvagua.desvios

# Filtrar por usina
df_usina = df_desvios[df_desvios['codigo_usina'] == 1]

# Para obter nome da usina, usar CONFHD
if confhd.usinas is not None:
    mapeamento = confhd.usinas[['codigo_usina', 'nome_usina']].drop_duplicates()
    df_desvios = df_desvios.merge(mapeamento, on='codigo_usina', how='left')
```

### Queries típicas
- "desvios de água"
- "desvios consuntivos"
- "desvios da usina FURNAS"

---

## Tool 12: UsinasNaoSimuladasTool

### O que faz
Consulta geração de usinas não simuladas (PCH, EOL, UFV, etc.).

### Arquivo acessado
- `SISTEMA.DAT`

### Classe inewave
```python
from inewave.newave import Sistema
```

### Propriedades disponíveis
- `sistema.geracao_usinas_nao_simuladas` (DataFrame): Geração de usinas não simuladas
  - Colunas principais: `codigo_submercado`, `indice_bloco`, `fonte`, `data`, `valor` (geração em MWmédio)

### Exemplo de código
```python
from inewave.newave import Sistema
import os
import pandas as pd

deck_path = "/path/to/deck"
sistema_path = os.path.join(deck_path, "SISTEMA.DAT")

# Ler arquivo
sistema = Sistema.read(sistema_path)

# Acessar geração de usinas não simuladas
df_nao_simuladas = sistema.geracao_usinas_nao_simuladas

# Filtrar por fonte/tecnologia
df_eol = df_nao_simuladas[df_nao_simuladas['fonte'] == 'EOL']  # Eólica
df_ufv = df_nao_simuladas[df_nao_simuladas['fonte'] == 'UFV']  # Solar
df_pch = df_nao_simuladas[df_nao_simuladas['fonte'] == 'PCH']  # Pequenas centrais

# Filtrar por submercado
df_sudeste = df_nao_simuladas[df_nao_simuladas['codigo_submercado'] == 1]
```

### Queries típicas
- "usinas não simuladas"
- "geração de pequenas centrais"
- "geração eólica"
- "geração solar"

---

## Tool 13: RestricaoEletricaTool

### O que faz
Consulta restrições elétricas do sistema.

### Arquivo acessado
- `restricao-eletrica.csv` (não é arquivo NEWAVE padrão, é CSV customizado)

### Classe utilitária
```python
from app.utils.restricao_eletrica import RestricaoEletrica
```

### Propriedades disponíveis
- `re.nomes_restricoes` (DataFrame): Nomes das restrições
- `re.formulas` (DataFrame): Fórmulas das restrições
- `re.limites` (DataFrame): Limites por período e patamar

### Exemplo de código
```python
from app.utils.restricao_eletrica import RestricaoEletrica
import os
import pandas as pd

deck_path = "/path/to/deck"
re_path = os.path.join(deck_path, "restricao-eletrica.csv")

# Ler arquivo
re = RestricaoEletrica.read(re_path)

# Acessar nomes
df_nomes = re.nomes_restricoes

# Acessar fórmulas
df_formulas = re.formulas

# Acessar limites
df_limites = re.limites

# Filtrar por código de restrição
df_rest1 = df_limites[df_limites['cod_rest'] == 1]
```

### Queries típicas
- "restrições elétricas"
- "fórmulas de restrição"
- "limites de restrição"

---

## Padrões e Boas Práticas

### 1. Leitura de Arquivos
Sempre use o método `.read()` da classe inewave correspondente:
```python
arquivo = ClasseInewave.read(caminho_arquivo)
```

### 2. Verificação de Existência
Sempre verifique se o arquivo existe antes de ler:
```python
import os
arquivo_path = os.path.join(deck_path, "ARQUIVO.DAT")
if not os.path.exists(arquivo_path):
    # Tentar variação lowercase
    arquivo_path = os.path.join(deck_path, "arquivo.dat")
```

### 3. Verificação de Dados
Sempre verifique se o DataFrame não é None ou vazio:
```python
if df is not None and not df.empty:
    # Processar dados
```

### 4. Filtragem de Dados
Use filtros pandas para dados específicos:
```python
# Por código
df_filtrado = df[df['codigo_usina'] == 1]

# Por múltiplas condições
df_filtrado = df[(df['codigo_usina'] == 1) & (df['ano'] == 2025)]

# Por nome (case-insensitive)
df_filtrado = df[df['nome_usina'].str.upper() == 'FURNAS']
```

### 5. Agregações
Use groupby para agregações:
```python
# Soma por grupo
df_agregado = df.groupby(['codigo_submercado', 'ano'])['valor'].sum()

# Múltiplas agregações
df_agregado = df.groupby('codigo_usina')['valor'].agg(['sum', 'mean', 'min', 'max'])
```

### 6. Conversão para JSON
Sempre converta tipos não-serializáveis:
```python
# Converter DataFrame para lista de dicts
resultado = df.to_dict(orient="records")

# Limpar NaN e tipos especiais
for record in resultado:
    for key, value in record.items():
        if pd.isna(value):
            record[key] = None
        elif isinstance(value, (pd.Timestamp, pd.DatetimeTZDtype)):
            record[key] = value.isoformat() if hasattr(value, 'isoformat') else str(value)
```

### 7. Mapeamento Usina → Posto
Para queries que mencionam nome de usina mas precisam de posto:
```python
# Carregar CONFHD para mapeamento
confhd = Confhd.read(confhd_path)
mapeamento = confhd.usinas[['nome_usina', 'posto']].drop_duplicates()
posto = mapeamento[mapeamento['nome_usina'] == 'FURNAS']['posto'].values[0]
```

### 8. Tratamento de Erros
Sempre trate exceções:
```python
try:
    arquivo = ClasseInewave.read(caminho)
    # Processar
except FileNotFoundError:
    # Arquivo não encontrado
except Exception as e:
    # Outro erro
```

---

## Observações Importantes

1. **HIDR.DAT é binário**: A biblioteca inewave abstrai isso, mas o arquivo é binário. Use sempre `Hidr.read()`.

2. **Códigos vs Índices**: Em alguns arquivos (como HIDR.DAT), o código da usina = índice + 1. Verifique a documentação específica.

3. **CVU sempre retorna todos os anos**: Quando a query mencionar CVU, sempre retornar dados de TODOS OS ANOS, não filtrar por ano específico.

4. **Status de usinas**: 
   - EX = Existente
   - EE = Em Expansão
   - NE = Nova Entrada
   - NC = Não Considerada

5. **Submercados comuns**:
   - 1 = Sudeste
   - 2 = Sul
   - 3 = Nordeste
   - 4 = Norte

6. **Tipos de modificação EXPT**:
   - POTEF = Potência Efetiva
   - GTMIN = Geração Mínima
   - FCMAX = Fator de Capacidade Máximo
   - IPTER = Indisponibilidade Programada
   - TEIFT = Taxa Equivalente de Indisponibilidade Forçada

7. **Tipos de modificação MODIF**:
   - VOLMIN = Volume Mínimo
   - VOLMAX = Volume Máximo
   - VAZMIN = Vazão Mínima
   - VAZMAX = Vazão Máxima

---

## Estrutura de Retorno Recomendada

Ao gerar código, sempre retorne dados em formato estruturado:

```python
# 1. Processar dados
df_resultado = # ... processamento ...

# 2. Converter para lista de dicts
resultado = df_resultado.to_dict(orient="records")

# 3. Limpar tipos
for record in resultado:
    for key, value in record.items():
        if pd.isna(value):
            record[key] = None
        elif isinstance(value, (pd.Timestamp, pd.DatetimeTZDtype)):
            record[key] = value.isoformat() if hasattr(value, 'isoformat') else str(value)

# 4. Imprimir resultado
print("=== RESULTADO ===")
print(df_resultado.to_string())

# 5. Incluir JSON para download (opcional)
print("\n---JSON_DATA_START---")
import json
print(json.dumps(resultado, indent=2, default=str))
print("---JSON_DATA_END---")
```

---

Este documento serve como referência completa para gerar código Python que acessa arquivos NEWAVE usando a biblioteca inewave, seguindo os mesmos padrões das tools pré-programadas.

