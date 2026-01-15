## CVAR.DAT

### 1. Informações do Arquivo

#### 1.1. Nome e Descrição

- **Nome do arquivo**: `cvar.dat` ou `CVAR.DAT`
- **Tipo**: Arquivo de entrada do modelo NEWAVE
- **Função**: Implementa um dos **Mecanismos de Aversão a Risco (MAR)** disponíveis: o **Valor Condicionado a um Dado Risco (CVaR)**

#### 1.2. Função e Propósito

**Função do CVaR:**
Adicionar uma **parcela à Função Objetivo (FO)** do problema de otimização, referente ao custo dos **cenários hidrológicos de custo mais elevado**, a fim de proporcionar uma maior segurança no suprimento de energia.

**Parâmetros Principais:**
O mecanismo CVaR é definido por dois parâmetros principais:
- **$\alpha$ (alfa)**: Percentual do total de cenários de um período, de **custo mais elevado**, que será considerado com custo adicional na função objetivo
- **$\lambda$ (lambda)**: **Peso (em percentual)** da parcela adicional que será considerada na função objetivo, referente ao custo esperado dos $\alpha$ cenários mais críticos

**Contexto:**
O CVaR é um dos três mecanismos de aversão a risco implementados no NEWAVE, sendo os outros o CAR (Curva de Aversão a Risco) e o SAR (Superfície de Aversão a Risco). O uso do CVaR pode ser concomitante com a Nova SAR.

#### 1.3. Ativação e Estrutura Geral

**Habilitação:**
O CVaR só é considerado no modelo NEWAVE se o **registro 61** do arquivo de dados gerais (`dger.dat`) for preenchido com:
- **1**: Para parâmetros constantes no tempo
- **2**: Para parâmetros variáveis no tempo

O flag `FLCVAR` no arquivo auxiliar `cortesh.dat` também indica o uso do CVaR.

**Composição:**
O `CVAR.DAT` é composto por **três blocos de dados**, e cada bloco é precedido por **dois registros de comentários**, que são obrigatórios para orientação, mas ignorados pelo programa.

#### 1.4. Bloco 1: Parâmetros Constantes no Tempo

Este bloco é utilizado se os parâmetros $\alpha$ e $\lambda$ forem considerados **constantes** ao longo de todo o horizonte de estudo.

| Campo | Colunas | Formato | Descrição |
| :--- | :--- | :--- | :--- |
| **1 ($\alpha$)** | 8 a 12 | F5.1 | **Percentual** do total de cenários de um período, de **custo mais elevado**, que será considerado com custo adicional na função objetivo |
| **2 ($\lambda$)** | 15 a 19 | F5.1 | **Peso (em percentual)** da parcela adicional que será considerada na função objetivo, referente ao custo esperado dos $\alpha$ cenários mais críticos |

**Observações:**
- Este bloco só é usado quando o registro 61 do `dger.dat` é igual a 1
- Os valores são aplicados constantemente ao longo de todo o período de planejamento
- O formato F5.1 indica um número decimal com 5 posições totais e 1 casa decimal

#### 1.5. Bloco 2: Parâmetro $\alpha$ Variável no Tempo

Os Blocos 2 e 3 são utilizados se os parâmetros $\alpha$ e $\lambda$ forem **variáveis no tempo**. O Bloco 2 define a sazonalidade e variação anual do parâmetro $\alpha$.

**Estrutura:**
- O bloco contém registros **Tipo 1** (para anos de planejamento), **Tipo 2** (para o período estático inicial/PRE) e **Tipo 3** (para o período estático final/POS)
- Cada registro informa o **percentual do total de cenários** de um período que será considerado com custo adicional na FO ($\alpha$) para cada um dos **12 meses**

**Formato dos registros:**
- Cada registro contém um identificador (ano, "PRE" ou "POS") seguido de 12 valores (um para cada mês)
- Os valores são fornecidos no formato F5.1

#### 1.6. Bloco 3: Parâmetro $\lambda$ Variável no Tempo

Este bloco define a sazonalidade e variação anual do parâmetro $\lambda$.

**Estrutura:**
- O bloco também contém registros **Tipo 1** (para anos de planejamento), **Tipo 2** (para o período estático inicial/PRE) e **Tipo 3** (para o período estático final/POS)
- Cada registro informa o **peso (em percentual)** da parcela adicional na função objetivo ($\lambda$) para cada um dos **12 meses**

**Formato dos registros:**
- Cada registro contém um identificador (ano, "PRE" ou "POS") seguido de 12 valores (um para cada mês)
- Os valores são fornecidos no formato F5.1

#### 1.7. Variáveis no Arquivo Auxiliar (`cortesh.dat`)

No arquivo de cabeçalho auxiliar dos cortes (`cortesh.dat`), as variáveis associadas ao CVaR, lidas pelo programa NEWDESP, são:

- **`FLCVAR`** (I4): Flag para utilização do mecanismo de aversão a risco CVaR
- **`ACVAR`** (R8): Vetor do **Parâmetro alfa ($\alpha$)** (variável no tempo, indexado pelo número de períodos do planejamento mais duas vezes o número de períodos por ano)
- **`LCVAR`** (R8): Vetor do **Parâmetro lambda ($\lambda$)** (variável no tempo, indexado pelo número de períodos do planejamento mais duas vezes o número de períodos por ano)

#### 1.8. Arquivo Auxiliar de Validação (`memcorcvar.csv`)

Quando o CVaR é utilizado, o módulo NWLISTCF pode gerar um arquivo auxiliar (`memcorcvar.csv`) que lista, para cada cenário (série *forward*), a **ordem**, a **probabilidade** da abertura considerando o CVaR, e o **valor da Função Objetivo**, facilitando a validação e o acompanhamento do cálculo dos coeficientes dos cortes de Benders.

---

### 2. Propriedades da Biblioteca inewave

#### 2.1. Classe Correspondente

**Classe**: `Cvar`

```python
class Cvar(data=<cfinterface.data.blockdata.BlockData object>)
```

**Descrição**: Armazena os dados de entrada do NEWAVE referentes à curva para penalização por volume mínimo dos reservatórios (CVaR - Valor Condicionado a um Dado Risco).

**Nota**: A descrição na classe menciona "penalização por volume mínimo", mas na prática a classe armazena os parâmetros do mecanismo CVaR.

#### 2.2. Propriedades Disponíveis

##### `property` **valores_constantes**: `list | None`

- **Descrição**: Valores constantes dos parâmetros ALFA e LAMBDA do CVAR
- **Tipo de retorno**: `list | None`
- **Corresponde a**: Bloco 1 do arquivo (Parâmetros Constantes no Tempo)
- **Estrutura da lista**: `[alfa, lambda]` onde:
  - `alfa` (`float`): Valor do parâmetro $\alpha$ (percentual)
  - `lambda` (`float`): Valor do parâmetro $\lambda$ (percentual)

**Observações:**
- Esta propriedade contém os valores quando os parâmetros são constantes no tempo
- A lista contém exatamente dois elementos: `[alfa, lambda]`
- Se o arquivo usar parâmetros variáveis no tempo, esta propriedade retorna `None`
- Os valores são fornecidos diretamente como lista, não como DataFrame

##### `property` **alfa_variavel**: `pd.DataFrame | None`

- **Descrição**: Tabela com os valores variáveis do CVAR para o parâmetro ALFA
- **Tipo de retorno**: `pd.DataFrame | None`
- **Corresponde a**: Bloco 2 do arquivo (Parâmetro $\alpha$ Variável no Tempo)
- **Colunas do DataFrame**:
  - `data` (`datetime`): Data/período para o qual o valor se aplica
  - `valor` (`float`): Valor do parâmetro $\alpha$ (percentual) para o período correspondente

**Observações:**
- Esta propriedade contém os valores quando $\alpha$ é variável no tempo
- Cada linha representa um período (mês) com seu respectivo valor de $\alpha$
- Na existência de períodos PRE ou POS, são adotados os anos padrão "0001" para PRE e "9999" para POS
- Os valores são organizados em formato tabular com data e valor correspondente
- Se o arquivo usar parâmetros constantes, esta propriedade retorna `None`

##### `property` **lambda_variavel**: `pd.DataFrame | None`

- **Descrição**: Tabela com os valores variáveis do CVAR para o parâmetro LAMBDA
- **Tipo de retorno**: `pd.DataFrame | None`
- **Corresponde a**: Bloco 3 do arquivo (Parâmetro $\lambda$ Variável no Tempo)
- **Colunas do DataFrame**:
  - `data` (`datetime`): Data/período para o qual o valor se aplica
  - `valor` (`float`): Valor do parâmetro $\lambda$ (percentual) para o período correspondente

**Observações:**
- Esta propriedade contém os valores quando $\lambda$ é variável no tempo
- Cada linha representa um período (mês) com seu respectivo valor de $\lambda$
- Na existência de períodos PRE ou POS, são adotados os anos padrão "0001" para PRE e "9999" para POS
- Os valores são organizados em formato tabular com data e valor correspondente
- Se o arquivo usar parâmetros constantes, esta propriedade retorna `None`

---

### 3. Mapeamento de Campos

#### 3.1. Bloco 1 → Propriedade `valores_constantes`

| Campo do Arquivo | Colunas | Formato | Posição na Lista | Tipo Python | Descrição |
| :--- | :--- | :--- | :--- | :--- | :--- |
| $\alpha$ | 8-12 | F5.1 | `[0]` | `float` | Percentual de cenários de custo mais elevado |
| $\lambda$ | 15-19 | F5.1 | `[1]` | `float` | Peso percentual na função objetivo |

**Retorno**: Lista com 2 elementos `[alfa, lambda]` ou `None` se não aplicável

#### 3.2. Bloco 2 → Propriedade `alfa_variavel`

| Campo do Arquivo | Formato | Coluna DataFrame | Tipo Python | Descrição |
| :--- | :--- | :--- | :--- | :--- |
| Identificador (Ano/PRE/POS) | I4 ou A3 | (parte de `data`) | `datetime` | Identificador do período |
| Valor mês 1 | F5.1 | `valor` (quando `data` = mês 1) | `float` | $\alpha$ para janeiro |
| Valor mês 2 | F5.1 | `valor` (quando `data` = mês 2) | `float` | $\alpha$ para fevereiro |
| ... | ... | ... | ... | ... |
| Valor mês 12 | F5.1 | `valor` (quando `data` = mês 12) | `float` | $\alpha$ para dezembro |

**Observação**: Cada registro do arquivo (ano/PRE/POS) gera 12 linhas no DataFrame (uma por mês), com a data correspondente e o valor do parâmetro.

#### 3.3. Bloco 3 → Propriedade `lambda_variavel`

| Campo do Arquivo | Formato | Coluna DataFrame | Tipo Python | Descrição |
| :--- | :--- | :--- | :--- | :--- |
| Identificador (Ano/PRE/POS) | I4 ou A3 | (parte de `data`) | `datetime` | Identificador do período |
| Valor mês 1 | F5.1 | `valor` (quando `data` = mês 1) | `float` | $\lambda$ para janeiro |
| Valor mês 2 | F5.1 | `valor` (quando `data` = mês 2) | `float` | $\lambda$ para fevereiro |
| ... | ... | ... | ... | ... |
| Valor mês 12 | F5.1 | `valor` (quando `data` = mês 12) | `float` | $\lambda$ para dezembro |

**Observação**: Cada registro do arquivo (ano/PRE/POS) gera 12 linhas no DataFrame (uma por mês), com a data correspondente e o valor do parâmetro.

---

### 4. Exemplos de Uso

#### 4.1. Leitura do Arquivo

```python
from inewave.newave import Cvar

# Ler o arquivo cvar.dat
cvar = Cvar.read("cvar.dat")

# Verificar se usa valores constantes ou variáveis
if cvar.valores_constantes is not None:
    print("Parâmetros constantes no tempo")
    print(f"Alfa: {cvar.valores_constantes[0]}, Lambda: {cvar.valores_constantes[1]}")
else:
    print("Parâmetros variáveis no tempo")
    if cvar.alfa_variavel is not None:
        print(f"Valores de alfa: {len(cvar.alfa_variavel)} registros")
    if cvar.lambda_variavel is not None:
        print(f"Valores de lambda: {len(cvar.lambda_variavel)} registros")
```

#### 4.2. Consulta de Valores Constantes

```python
from inewave.newave import Cvar

cvar = Cvar.read("cvar.dat")

if cvar.valores_constantes is not None:
    alfa, lambda_val = cvar.valores_constantes
    print(f"Parâmetros constantes do CVaR:")
    print(f"  α (alfa): {alfa}%")
    print(f"  λ (lambda): {lambda_val}%")
else:
    print("Este arquivo usa parâmetros variáveis no tempo")
```

#### 4.3. Consulta de Valores Variáveis de Alfa

```python
from inewave.newave import Cvar

cvar = Cvar.read("cvar.dat")

if cvar.alfa_variavel is not None:
    print(f"Total de registros de alfa: {len(cvar.alfa_variavel)}")
    print("\nPrimeiros registros:")
    print(cvar.alfa_variavel.head(10))
    
    # Valores de alfa para um período específico
    from datetime import datetime
    data_consulta = datetime(2024, 6, 1)
    valores_periodo = cvar.alfa_variavel[
        cvar.alfa_variavel['data'] == data_consulta
    ]
    
    if not valores_periodo.empty:
        print(f"\nValor de alfa para {data_consulta.date()}: {valores_periodo['valor'].iloc[0]}%")
else:
    print("Valores de alfa não disponíveis (usando valores constantes)")
```

#### 4.4. Consulta de Valores Variáveis de Lambda

```python
from inewave.newave import Cvar

cvar = Cvar.read("cvar.dat")

if cvar.lambda_variavel is not None:
    print(f"Total de registros de lambda: {len(cvar.lambda_variavel)}")
    print("\nPrimeiros registros:")
    print(cvar.lambda_variavel.head(10))
    
    # Estatísticas dos valores de lambda
    estatisticas = cvar.lambda_variavel['valor'].describe()
    print("\nEstatísticas dos valores de lambda:")
    print(estatisticas)
else:
    print("Valores de lambda não disponíveis (usando valores constantes)")
```

#### 4.5. Consulta por Período

```python
from inewave.newave import Cvar
from datetime import datetime

cvar = Cvar.read("cvar.dat")

# Consultar valores para um período específico
data_inicio = datetime(2024, 1, 1)
data_fim = datetime(2024, 12, 31)

if cvar.alfa_variavel is not None:
    valores_alfa_periodo = cvar.alfa_variavel[
        (cvar.alfa_variavel['data'] >= data_inicio) &
        (cvar.alfa_variavel['data'] <= data_fim)
    ]
    
    print(f"Valores de alfa no período {data_inicio.date()} a {data_fim.date()}:")
    print(valores_alfa_periodo)

if cvar.lambda_variavel is not None:
    valores_lambda_periodo = cvar.lambda_variavel[
        (cvar.lambda_variavel['data'] >= data_inicio) &
        (cvar.lambda_variavel['data'] <= data_fim)
    ]
    
    print(f"\nValores de lambda no período {data_inicio.date()} a {data_fim.date()}:")
    print(valores_lambda_periodo)
```

#### 4.6. Análise de Variação Temporal

```python
from inewave.newave import Cvar

cvar = Cvar.read("cvar.dat")

if cvar.alfa_variavel is not None:
    # Agrupar valores por ano
    cvar.alfa_variavel['ano'] = cvar.alfa_variavel['data'].dt.year
    
    valores_por_ano = cvar.alfa_variavel.groupby('ano')['valor'].agg(['mean', 'min', 'max'])
    
    print("Valores de alfa por ano:")
    print(valores_por_ano)

if cvar.lambda_variavel is not None:
    # Agrupar valores por mês
    cvar.lambda_variavel['mes'] = cvar.lambda_variavel['data'].dt.month
    
    valores_por_mes = cvar.lambda_variavel.groupby('mes')['valor'].mean()
    
    print("\nValores médios de lambda por mês:")
    print(valores_por_mes)
```

#### 4.7. Consulta Combinada: Alfa e Lambda

```python
from inewave.newave import Cvar
from datetime import datetime

cvar = Cvar.read("cvar.dat")

# Consultar ambos os parâmetros para um período específico
data_consulta = datetime(2024, 6, 1)

if cvar.alfa_variavel is not None and cvar.lambda_variavel is not None:
    alfa_periodo = cvar.alfa_variavel[cvar.alfa_variavel['data'] == data_consulta]
    lambda_periodo = cvar.lambda_variavel[cvar.lambda_variavel['data'] == data_consulta]
    
    if not alfa_periodo.empty and not lambda_periodo.empty:
        print(f"Parâmetros CVaR para {data_consulta.date()}:")
        print(f"  α (alfa): {alfa_periodo['valor'].iloc[0]}%")
        print(f"  λ (lambda): {lambda_periodo['valor'].iloc[0]}%")
elif cvar.valores_constantes is not None:
    alfa, lambda_val = cvar.valores_constantes
    print(f"Parâmetros CVaR constantes:")
    print(f"  α (alfa): {alfa}%")
    print(f"  λ (lambda): {lambda_val}%")
```

#### 4.8. Validação de Dados

```python
from inewave.newave import Cvar

cvar = Cvar.read("cvar.dat")

# Validar valores constantes
if cvar.valores_constantes is not None:
    alfa, lambda_val = cvar.valores_constantes
    
    # Verificar se são valores válidos (percentuais)
    if alfa < 0 or alfa > 100:
        print(f"⚠️ Valor de alfa fora do intervalo esperado (0-100%): {alfa}")
    if lambda_val < 0 or lambda_val > 100:
        print(f"⚠️ Valor de lambda fora do intervalo esperado (0-100%): {lambda_val}")

# Validar valores variáveis de alfa
if cvar.alfa_variavel is not None:
    df_alfa = cvar.alfa_variavel
    
    # Verificar valores fora do intervalo
    valores_invalidos = df_alfa[(df_alfa['valor'] < 0) | (df_alfa['valor'] > 100)]
    if len(valores_invalidos) > 0:
        print(f"⚠️ {len(valores_invalidos)} valores de alfa fora do intervalo 0-100%")
    
    # Verificar se há valores nulos
    nulos = df_alfa['valor'].isnull().sum()
    if nulos > 0:
        print(f"⚠️ {nulos} valores nulos encontrados em alfa")

# Validar valores variáveis de lambda
if cvar.lambda_variavel is not None:
    df_lambda = cvar.lambda_variavel
    
    # Verificar valores fora do intervalo
    valores_invalidos = df_lambda[(df_lambda['valor'] < 0) | (df_lambda['valor'] > 100)]
    if len(valores_invalidos) > 0:
        print(f"⚠️ {len(valores_invalidos)} valores de lambda fora do intervalo 0-100%")
    
    # Verificar se há valores nulos
    nulos = df_lambda['valor'].isnull().sum()
    if nulos > 0:
        print(f"⚠️ {nulos} valores nulos encontrados em lambda")
```

#### 4.9. Modificação e Gravação

```python
from inewave.newave import Cvar

# Ler o arquivo
cvar = Cvar.read("cvar.dat")

# Modificar valores constantes
if cvar.valores_constantes is not None:
    # Modificar valores
    novo_alfa = 50.0
    novo_lambda = 40.0
    cvar.valores_constantes = [novo_alfa, novo_lambda]
    print(f"Valores constantes atualizados: α={novo_alfa}%, λ={novo_lambda}%")
    
    # Salvar alterações
    cvar.write("cvar.dat")

# Modificar valores variáveis (exemplo)
if cvar.alfa_variavel is not None:
    from datetime import datetime
    
    # Modificar valor para um período específico
    data_modificar = datetime(2024, 6, 1)
    mask = cvar.alfa_variavel['data'] == data_modificar
    
    if mask.any():
        cvar.alfa_variavel.loc[mask, 'valor'] = 55.0
        print(f"Valor de alfa para {data_modificar.date()} atualizado para 55.0%")
        
        # Salvar alterações
        cvar.write("cvar.dat")
```

---

### 5. Observações Importantes

1. **Habilitação**: O arquivo só é considerado se o registro 61 do `dger.dat` estiver preenchido com:
   - **1**: Para parâmetros constantes no tempo
   - **2**: Para parâmetros variáveis no tempo

2. **Mutualidade**: O arquivo usa **ou** valores constantes (Bloco 1) **ou** valores variáveis (Blocos 2 e 3), nunca ambos simultaneamente

3. **Períodos PRE e POS**: 
   - Na existência de períodos PRE ou POS, são adotados os anos padrão "0001" para PRE e "9999" para POS
   - Isso permite diferenciar esses períodos especiais nos DataFrames

4. **Unidades**: 
   - Ambos os parâmetros ($\alpha$ e $\lambda$) são expressos em **percentual** (0-100)
   - O formato F5.1 permite valores com uma casa decimal

5. **Interpretação dos parâmetros**:
   - **$\alpha$**: Percentual de cenários de custo mais elevado que serão penalizados na função objetivo
   - **$\lambda$**: Peso percentual da parcela adicional na função objetivo

6. **Arquivo auxiliar**: O flag `FLCVAR` no arquivo `cortesh.dat` também indica o uso do CVaR

7. **Módulo NWLISTCF**: Pode gerar o arquivo `memcorcvar.csv` com informações detalhadas sobre a ordem e probabilidade dos cenários considerando o CVaR

8. **Compatibilidade**: O uso do CVaR pode ser concomitante com a Nova SAR (Superfície de Aversão a Risco)

9. **Comentários**: Os registros de comentário no início de cada bloco são obrigatórios mas ignorados pelo programa

10. **Estrutura de dados**:
    - Valores constantes: retornados como lista `[alfa, lambda]`
    - Valores variáveis: retornados como DataFrames com colunas `data` e `valor`

11. **DataFrames variáveis**: 
    - Cada registro do arquivo (ano/PRE/POS) gera 12 linhas no DataFrame (uma por mês)
    - A data é automaticamente convertida para objeto `datetime`

12. **Validação**: É recomendado validar que os valores estão no intervalo 0-100% (percentuais válidos)

---
