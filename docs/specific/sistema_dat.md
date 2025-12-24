## SISTEMA.DAT

### 1. Informações do Arquivo

#### 1.1. Nome e Descrição

- **Nome do arquivo**: `sistema.dat` ou `SISTEMA.DAT`
- **Tipo**: Arquivo de entrada crucial do modelo NEWAVE
- **Função**: Define a configuração do sistema elétrico, a demanda e as condições de intercâmbio entre os subsistemas/submercados

#### 1.2. Estrutura Geral

O arquivo é composto por **cinco blocos de dados** distintos, e a **ordem em que esses blocos são fornecidos deve ser respeitada**. Cada bloco é precedido por um conjunto de **três registros destinados a comentários**, que são obrigatórios, mas ignorados pelo programa, servindo apenas para orientação do usuário.

**Ordem dos Blocos:**
1. Bloco 1: Definição do Número de Patamares de Déficit
2. Bloco 2: Cadastro de Subsistemas e Custos de Déficit
3. Bloco 3: Limites de Intercâmbio
4. Bloco 4: Mercado de Energia (Demanda)
5. Bloco 5: Geração de Pequenas Usinas Não Simuladas

#### 1.3. Bloco 1: Definição do Número de Patamares de Déficit

Este bloco é o primeiro e contém apenas um registro que especifica a complexidade do custo de déficit.

| Campo | Colunas | Formato | Descrição |
| :--- | :--- | :--- | :--- |
| **1** | 2 a 4 | I3 | **Número de patamares de déficit** |

**Observações:**
- Este valor define quantos patamares de déficit serão considerados no estudo
- O número de patamares afeta a complexidade do modelo de déficit
- Valores típicos: 1 (custo único de déficit) a 4 (até 4 patamares)

#### 1.4. Bloco 2: Cadastro de Subsistemas e Custos de Déficit

Este bloco lista cada subsistema/submercado considerado no estudo e define os custos e a profundidade de déficit associados a ele.

| Campo | Colunas | Formato | Descrição |
| :--- | :--- | :--- | :--- |
| **1** | 2 a 4 | I3 | **Número do subsistema/submercado** |
| **2** | 6 a 15 | A10 | **Nome do subsistema/submercado** |
| **3** | 18 a 18 | I1 | **Tipo do subsistema/submercado** (`0` = não fictício; `1` = fictício) |
| **4 a 7** | 20 a 50 | 4x F7.2 | **Custo do déficit** ($/MWh) para o primeiro ao quarto patamar |
| **8 a 11** | 52 a 74 | 4x F5.3 | **Profundidade** (p.u.) do primeiro ao quarto patamar de déficit |

**Regras e Observações:**

1. Se o subsistema for **fictício** (tipo = 1), os campos 4 a 11 (custos e profundidades) são **ignorados**

2. A **soma das profundidades** (campos 8 a 11) deve ser igual a **1** (1.000 em p.u.)

3. Os valores de custo de déficit fornecidos são multiplicados internamente por um fator de **1,001** durante a simulação final, um procedimento para evitar a indiferença de custos quando o valor da água é exatamente igual ao custo de déficit

4. O código **`999`** no campo 1 indica o final do bloco

**Estrutura de dados:**
- Cada linha representa um subsistema/submercado
- Os custos e profundidades são definidos para até 4 patamares (conforme definido no Bloco 1)

#### 1.5. Bloco 3: Limites de Intercâmbio

Este bloco define as capacidades máximas de interligação e os intercâmbios mínimos obrigatórios entre os subsistemas/submercados.

É composto por **três tipos de registros**, repetidos para cada interligação:

**Registro Tipo 1 (Identificação):**
- Campos definem o **Subsistema A** (I3, colunas 2-4)
- **Subsistema B** (I3, colunas 6-8)
- Um **Flag** para indicar se é **limite de intercâmbio** (0) ou **intercâmbio mínimo obrigatório** (1) (I1, colunas ~10)
- Um Flag para considerar ou não penalidade interna de intercâmbio (0 = considera; 1 = não considera) (I1)

**Registro Tipo 2 (Limite A para B):**
- Informa o **Limite/Mínimo Obrigatório** de A para B, em MWmédio (F7.0), para **cada mês do ano** (12 colunas)
- Os valores são fornecidos para cada ano do período de planejamento

**Registro Tipo 3 (Limite B para A):**
- Informa o **Limite/Mínimo Obrigatório** de B para A, em MWmédio (F7.0), para **cada mês do ano** (12 colunas)
- Os valores são fornecidos para cada ano do período de planejamento

**Regras:**
- A capacidade mínima de interligação deve ser sempre **inferior ou igual** à capacidade máxima
- O código **`999`** no campo 1 indica o final do bloco

#### 1.6. Bloco 4: Mercado de Energia (Demanda)

Este bloco define a demanda de energia (MWmédio) para cada subsistema/submercado em todos os meses do horizonte. O mercado (demanda) é dado em MWmês para blocos de energia em cada estágio.

É composto por conjuntos de registros que podem incluir até **quatro tipos**, dependendo da existência de períodos estáticos (pré e pós) de estabilização:

1. **Registro Tipo 1:** Identifica o **Número do subsistema/submercado** (I3)

2. **Registro Tipo 2:** Informa o **Mercado de Energia** (MWmédio, F7.0) para os **12 meses** de cada ano do período de planejamento

3. **Registro Tipo 3 (Opcional):** Informa o **Mercado Estático de Energia** para os **12 meses** do período estático **inicial** (se houver)

4. **Registro Tipo 4 (Opcional):** Informa o **Mercado Estático de Energia** para os **12 meses** do período estático **final** (se houver)

**Observações:**
- O código **`999`** no campo 1 indica o final do bloco
- Cada subsistema pode ter múltiplos registros Tipo 2 (um por ano do período de planejamento)
- Os registros Tipo 3 e 4 são opcionais e dependem da configuração do estudo

#### 1.7. Bloco 5: Geração de Pequenas Usinas Não Simuladas

Este bloco contém informações sobre a geração de pequenas usinas que **não são simuladas explicitamente** pelo modelo. A energia dessas usinas é subtraída do mercado (demanda).

É composto por conjuntos de registros que agrupam:

1. **Registro Tipo 1 (Identificação):**
   - Define o **Número do subsistema/submercado** (I3)
   - O **Número do bloco de usinas não simuladas** (I3)
   - A **Descrição do bloco** (A20)
   - O **Número da tecnologia** (I3)

2. **Registro Tipo 2:**
   - Informa a **Geração de usinas não simuladas** (MWmédio, F7.0) para os **12 meses** de cada ano do período de planejamento

**Observações:**
- Pode existir mais de um conjunto de registros (Blocos 1 e 2) para o mesmo subsistema/submercado
- O código **`999`** no campo 1 indica o final do bloco
- A geração das usinas não simuladas é subtraída do mercado antes do cálculo da operação

---

### 2. Propriedades da Biblioteca inewave

#### 2.1. Classe Correspondente

**Classe**: `Sistema`

```python
class Sistema(data=<cfinterface.data.sectiondata.SectionData object>)
```

**Descrição**: Armazena os dados de entrada do NEWAVE referentes às configurações dos subsistemas (submercados).

#### 2.2. Propriedades Disponíveis

##### `property` **numero_patamares_deficit**: `int | None`

- **Descrição**: O número de patamares de déficit utilizados no estudo
- **Tipo de retorno**: `int | None`
- **Corresponde a**: Bloco 1 do arquivo (Definição do Número de Patamares de Déficit)

**Observações:**
- Retorna um inteiro indicando quantos patamares de déficit são considerados (geralmente 1 a 4)
- Se o arquivo não for lido corretamente, retorna `None`

##### `property` **custo_deficit**: `pd.DataFrame | None`

- **Descrição**: Tabela com o custo de cada patamar de déficit, por subsistema
- **Tipo de retorno**: `pd.DataFrame | None`
- **Corresponde a**: Bloco 2 do arquivo (Cadastro de Subsistemas e Custos de Déficit)
- **Colunas do DataFrame**:
  - `codigo_submercado` (`int`): Número do subsistema/submercado
  - `nome_submercado` (`str`): Nome do subsistema/submercado
  - `ficticio` (`int`): Tipo do subsistema (0 = não fictício, 1 = fictício)
  - `patamar_deficit` (`int`): Número do patamar de déficit (1, 2, 3 ou 4)
  - `custo` (`float`): Custo do déficit ($/MWh) para o patamar
  - `corte` (`float`): Profundidade (p.u.) do patamar de déficit

**Observações:**
- Cada linha representa um patamar de déficit de um subsistema específico
- Para subsistemas fictícios, os custos e profundidades podem estar vazios ou zerados
- A soma das profundidades (`corte`) para cada subsistema deve ser igual a 1.0

##### `property` **limites_intercambio**: `pd.DataFrame | None`

- **Descrição**: Tabela com o limite de intercâmbio por par de subsistemas
- **Tipo de retorno**: `pd.DataFrame | None`
- **Corresponde a**: Bloco 3 do arquivo (Limites de Intercâmbio)
- **Colunas do DataFrame**:
  - `submercado_de` (`int`): Subsistema/submercado de origem (Subsistema A)
  - `submercado_para` (`int`): Subsistema/submercado de destino (Subsistema B)
  - `sentido` (`int`): Flag indicando o sentido (0 = limite de intercâmbio, 1 = intercâmbio mínimo obrigatório)
  - `data` (`datetime`): Data/período para o qual o limite se aplica
  - `valor` (`float`): Limite ou mínimo obrigatório em MWmédio

**Observações:**
- Cada linha representa um limite de intercâmbio para um período específico
- Os limites são definidos mensalmente para cada ano do período de planejamento
- O campo `sentido` indica se é limite máximo ou mínimo obrigatório
- Para cada par de subsistemas, há limites em ambas as direções (A→B e B→A)

##### `property` **mercado_energia**: `pd.DataFrame | None`

- **Descrição**: Tabela com o mercado total de energia por período de estudo
- **Tipo de retorno**: `pd.DataFrame | None`
- **Corresponde a**: Bloco 4 do arquivo (Mercado de Energia/Demanda)
- **Colunas do DataFrame**:
  - `codigo_submercado` (`int`): Número do subsistema/submercado
  - `data` (`datetime`): Data/período para o qual a demanda se aplica
  - `valor` (`float`): Mercado de energia em MWmédio (demanda)

**Observações:**
- Cada linha representa a demanda de um subsistema para um período específico
- A demanda é fornecida mensalmente para cada ano do período de planejamento
- Pode incluir períodos estáticos inicial (PRE) e final (POS), se existirem

##### `property` **geracao_usinas_nao_simuladas**: `pd.DataFrame | None`

- **Descrição**: Tabela com a geração das usinas não simuladas por fonte de geração
- **Tipo de retorno**: `pd.DataFrame | None`
- **Corresponde a**: Bloco 5 do arquivo (Geração de Pequenas Usinas Não Simuladas)
- **Colunas do DataFrame**:
  - `codigo_submercado` (`int`): Número do subsistema/submercado
  - `indice_bloco` (`int`): Número do bloco de usinas não simuladas
  - `fonte` (`str`): Descrição do bloco ou tecnologia
  - `data` (`int`): Data/período (pode ser ano ou período)
  - `valor` (`float`): Geração de usinas não simuladas em MWmédio

**Observações:**
- Cada linha representa a geração de um bloco de usinas não simuladas para um período específico
- A geração é fornecida mensalmente para cada ano do período de planejamento
- Pode haver múltiplos blocos de usinas não simuladas por subsistema

---

### 3. Mapeamento de Campos

#### 3.1. Bloco 1 → Propriedade `numero_patamares_deficit`

| Campo do Arquivo | Colunas | Formato | Propriedade | Tipo Python | Descrição |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Número de patamares | 2-4 | I3 | `numero_patamares_deficit` | `int` | Número de patamares de déficit |

#### 3.2. Bloco 2 → Propriedade `custo_deficit`

| Campo do Arquivo | Colunas | Formato | Coluna DataFrame | Tipo Python | Descrição |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Número do subsistema | 2-4 | I3 | `codigo_submercado` | `int` | Identificador do subsistema |
| Nome | 6-15 | A10 | `nome_submercado` | `str` | Nome do subsistema |
| Tipo (fictício) | 18 | I1 | `ficticio` | `int` | 0 = não fictício, 1 = fictício |
| Custo patamar 1 | 20-26 | F7.2 | `custo` (quando `patamar_deficit=1`) | `float` | Custo do déficit patamar 1 ($/MWh) |
| Custo patamar 2 | 28-34 | F7.2 | `custo` (quando `patamar_deficit=2`) | `float` | Custo do déficit patamar 2 ($/MWh) |
| Custo patamar 3 | 36-42 | F7.2 | `custo` (quando `patamar_deficit=3`) | `float` | Custo do déficit patamar 3 ($/MWh) |
| Custo patamar 4 | 44-50 | F7.2 | `custo` (quando `patamar_deficit=4`) | `float` | Custo do déficit patamar 4 ($/MWh) |
| Profundidade patamar 1 | 52-56 | F5.3 | `corte` (quando `patamar_deficit=1`) | `float` | Profundidade patamar 1 (p.u.) |
| Profundidade patamar 2 | 58-62 | F5.3 | `corte` (quando `patamar_deficit=2`) | `float` | Profundidade patamar 2 (p.u.) |
| Profundidade patamar 3 | 64-68 | F5.3 | `corte` (quando `patamar_deficit=3`) | `float` | Profundidade patamar 3 (p.u.) |
| Profundidade patamar 4 | 70-74 | F5.3 | `corte` (quando `patamar_deficit=4`) | `float` | Profundidade patamar 4 (p.u.) |

**Observação**: Cada registro do arquivo gera N linhas no DataFrame (onde N = número de patamares de déficit), uma para cada patamar.

#### 3.3. Bloco 3 → Propriedade `limites_intercambio`

| Campo do Arquivo | Formato | Coluna DataFrame | Tipo Python | Descrição |
| :--- | :--- | :--- | :--- | :--- |
| Subsistema A | I3 | `submercado_de` | `int` | Subsistema de origem |
| Subsistema B | I3 | `submercado_para` | `int` | Subsistema de destino |
| Flag limite/mínimo | I1 | `sentido` | `int` | 0 = limite, 1 = mínimo obrigatório |
| Valor mês 1 (ano N) | F7.0 | `valor` (quando `data` = mês correspondente) | `float` | Limite para janeiro do ano N (MWmédio) |
| ... | ... | ... | ... | ... |
| Valor mês 12 (ano N) | F7.0 | `valor` (quando `data` = mês correspondente) | `float` | Limite para dezembro do ano N (MWmédio) |

**Observação**: Cada registro Tipo 2 e Tipo 3 do arquivo gera 12 linhas no DataFrame (uma por mês), para cada ano do período de planejamento.

#### 3.4. Bloco 4 → Propriedade `mercado_energia`

| Campo do Arquivo | Formato | Coluna DataFrame | Tipo Python | Descrição |
| :--- | :--- | :--- | :--- | :--- |
| Número do subsistema | I3 | `codigo_submercado` | `int` | Identificador do subsistema |
| Valor mês 1 (ano N) | F7.0 | `valor` (quando `data` = mês correspondente) | `float` | Demanda para janeiro do ano N (MWmédio) |
| ... | ... | ... | ... | ... |
| Valor mês 12 (ano N) | F7.0 | `valor` (quando `data` = mês correspondente) | `float` | Demanda para dezembro do ano N (MWmédio) |

**Observação**: Cada registro Tipo 2, 3 ou 4 do arquivo gera 12 linhas no DataFrame (uma por mês).

#### 3.5. Bloco 5 → Propriedade `geracao_usinas_nao_simuladas`

| Campo do Arquivo | Formato | Coluna DataFrame | Tipo Python | Descrição |
| :--- | :--- | :--- | :--- | :--- |
| Número do subsistema | I3 | `codigo_submercado` | `int` | Identificador do subsistema |
| Número do bloco | I3 | `indice_bloco` | `int` | Identificador do bloco de usinas |
| Descrição | A20 | `fonte` | `str` | Descrição/tecnologia do bloco |
| Número da tecnologia | I3 | (parte de `fonte`) | `str` | Tecnologia associada |
| Valor mês 1 (ano N) | F7.0 | `valor` (quando `data` = período correspondente) | `float` | Geração para janeiro do ano N (MWmédio) |
| ... | ... | ... | ... | ... |
| Valor mês 12 (ano N) | F7.0 | `valor` (quando `data` = período correspondente) | `float` | Geração para dezembro do ano N (MWmédio) |

**Observação**: Cada registro Tipo 2 do arquivo gera 12 linhas no DataFrame (uma por mês), para cada ano do período de planejamento.

---

### 4. Exemplos de Uso

#### 4.1. Leitura do Arquivo

```python
from inewave.newave import Sistema

# Ler o arquivo sistema.dat
sistema = Sistema.read("sistema.dat")

# Verificar número de patamares de déficit
if sistema.numero_patamares_deficit is not None:
    print(f"Número de patamares de déficit: {sistema.numero_patamares_deficit}")

# Acessar custos de déficit
if sistema.custo_deficit is not None:
    print(f"Total de registros de custos: {len(sistema.custo_deficit)}")
```

#### 4.2. Consulta de Custos de Déficit

```python
from inewave.newave import Sistema

sistema = Sistema.read("sistema.dat")

if sistema.custo_deficit is not None:
    # Filtrar custos de um subsistema específico
    codigo_submercado = 1
    custos = sistema.custo_deficit[
        sistema.custo_deficit['codigo_submercado'] == codigo_submercado
    ]
    
    print(f"Custos de déficit do subsistema {codigo_submercado}:")
    print(custos[['patamar_deficit', 'custo', 'corte']])
    
    # Verificar se soma das profundidades é igual a 1
    soma_profundidades = custos['corte'].sum()
    print(f"\nSoma das profundidades: {soma_profundidades} (deve ser 1.0)")
```

#### 4.3. Consulta de Limites de Intercâmbio

```python
from inewave.newave import Sistema

sistema = Sistema.read("sistema.dat")

if sistema.limites_intercambio is not None:
    # Filtrar limites entre dois subsistemas específicos
    sub_de = 1
    sub_para = 2
    
    limites = sistema.limites_intercambio[
        (sistema.limites_intercambio['submercado_de'] == sub_de) &
        (sistema.limites_intercambio['submercado_para'] == sub_para)
    ]
    
    print(f"Limites de intercâmbio de {sub_de} para {sub_para}:")
    print(limites[['data', 'sentido', 'valor']])
```

#### 4.4. Consulta de Mercado de Energia (Demanda)

```python
from inewave.newave import Sistema
from datetime import datetime

sistema = Sistema.read("sistema.dat")

if sistema.mercado_energia is not None:
    # Filtrar demanda de um subsistema específico
    codigo_submercado = 1
    demanda = sistema.mercado_energia[
        sistema.mercado_energia['codigo_submercado'] == codigo_submercado
    ]
    
    print(f"Demanda do subsistema {codigo_submercado}:")
    print(demanda.head(20))
    
    # Filtrar por período
    data_inicio = datetime(2024, 1, 1)
    data_fim = datetime(2024, 12, 31)
    
    demanda_periodo = demanda[
        (demanda['data'] >= data_inicio) &
        (demanda['data'] <= data_fim)
    ]
    
    print(f"\nDemanda no período {data_inicio.date()} a {data_fim.date()}:")
    print(demanda_periodo)
```

#### 4.5. Consulta de Geração de Usinas Não Simuladas

```python
from inewave.newave import Sistema

sistema = Sistema.read("sistema.dat")

if sistema.geracao_usinas_nao_simuladas is not None:
    # Filtrar geração de um subsistema específico
    codigo_submercado = 1
    geracao = sistema.geracao_usinas_nao_simuladas[
        sistema.geracao_usinas_nao_simuladas['codigo_submercado'] == codigo_submercado
    ]
    
    print(f"Geração de usinas não simuladas do subsistema {codigo_submercado}:")
    print(geracao.head(20))
    
    # Agrupar por bloco
    geracao_por_bloco = geracao.groupby(['indice_bloco', 'fonte'])['valor'].sum()
    print("\nGeração total por bloco:")
    print(geracao_por_bloco)
```

#### 4.6. Análise de Subsistemas

```python
from inewave.newave import Sistema

sistema = Sistema.read("sistema.dat")

if sistema.custo_deficit is not None:
    # Listar todos os subsistemas
    subsistemas = sistema.custo_deficit[['codigo_submercado', 'nome_submercado', 'ficticio']].drop_duplicates()
    
    print("Subsistemas cadastrados:")
    print(subsistemas)
    
    # Separar fictícios e não fictícios
    ficticios = subsistemas[subsistemas['ficticio'] == 1]
    nao_ficticios = subsistemas[subsistemas['ficticio'] == 0]
    
    print(f"\nSubsistemas não fictícios: {len(nao_ficticios)}")
    print(f"Subsistemas fictícios: {len(ficticios)}")
```

#### 4.7. Validação de Dados

```python
from inewave.newave import Sistema

sistema = Sistema.read("sistema.dat")

# Validar custos de déficit
if sistema.custo_deficit is not None:
    df_custos = sistema.custo_deficit
    
    # Verificar soma das profundidades por subsistema
    for submercado in df_custos['codigo_submercado'].unique():
        custos_sub = df_custos[df_custos['codigo_submercado'] == submercado]
        soma = custos_sub['corte'].sum()
        
        if abs(soma - 1.0) > 0.001:  # Tolerância para erros de ponto flutuante
            print(f"⚠️ Subsistema {submercado}: soma das profundidades = {soma} (deve ser 1.0)")
    
    # Verificar subsistemas fictícios
    ficticios = df_custos[df_custos['ficticio'] == 1]
    if len(ficticios) > 0:
        custos_ficticios = ficticios[ficticios['custo'] > 0]
        if len(custos_ficticios) > 0:
            print("⚠️ Subsistemas fictícios com custos de déficit definidos (serão ignorados)")

# Validar limites de intercâmbio
if sistema.limites_intercambio is not None:
    df_limites = sistema.limites_intercambio
    
    # Verificar valores negativos
    limites_negativos = df_limites[df_limites['valor'] < 0]
    if len(limites_negativos) > 0:
        print(f"⚠️ {len(limites_negativos)} limites de intercâmbio com valores negativos")
```

#### 4.8. Modificação e Gravação

```python
from inewave.newave import Sistema

# Ler o arquivo
sistema = Sistema.read("sistema.dat")

# Modificar número de patamares
if sistema.numero_patamares_deficit is not None:
    sistema.numero_patamares_deficit = 2
    print("Número de patamares de déficit atualizado para 2")

# Modificar custo de déficit
if sistema.custo_deficit is not None:
    codigo_submercado = 1
    patamar = 1
    
    mask = (
        (sistema.custo_deficit['codigo_submercado'] == codigo_submercado) &
        (sistema.custo_deficit['patamar_deficit'] == patamar)
    )
    
    if mask.any():
        sistema.custo_deficit.loc[mask, 'custo'] = 7000.0
        print(f"Custo de déficit do subsistema {codigo_submercado}, patamar {patamar} atualizado para 7000.0 $/MWh")
    
    # Salvar alterações
    sistema.write("sistema.dat")
```

---

### 5. Observações Importantes

1. **Ordem dos blocos**: A ordem em que os blocos são fornecidos no arquivo **deve ser respeitada**

2. **Comentários**: Cada bloco é precedido por três registros de comentários que são obrigatórios mas ignorados pelo programa

3. **Subsistemas fictícios**: Subsistemas fictícios (tipo = 1) não têm custos e profundidades de déficit considerados

4. **Soma das profundidades**: A soma das profundidades de déficit de cada subsistema deve ser igual a 1.0 (em p.u.)

5. **Fator de ajuste**: Os custos de déficit são multiplicados por 1,001 internamente para evitar indiferença de custos

6. **Limites de intercâmbio**: 
   - A capacidade mínima deve ser sempre ≤ capacidade máxima
   - Podem ser limites máximos (sentido = 0) ou mínimos obrigatórios (sentido = 1)

7. **Mercado de energia**: 
   - Representa a demanda de cada subsistema
   - É fornecido mensalmente para cada ano do período de planejamento
   - Pode incluir períodos estáticos (PRE e POS)

8. **Usinas não simuladas**: 
   - A geração dessas usinas é **subtraída** do mercado (demanda)
   - Podem existir múltiplos blocos de usinas não simuladas por subsistema

9. **Estrutura de dados**: 
   - Cada propriedade retorna um DataFrame (exceto `numero_patamares_deficit` que retorna int)
   - Os dados temporais são organizados em linhas separadas (uma por mês/período)

10. **DataFrames**: Todas as propriedades que retornam DataFrames facilitam análises e manipulações usando pandas

11. **Validação**: É importante validar:
    - Soma das profundidades de déficit = 1.0
    - Valores de limites de intercâmbio não negativos
    - Consistência entre subsistemas referenciados

12. **Dependências**: 
    - Os subsistemas devem estar consistentes entre os blocos
    - Os limites de intercâmbio referenciam subsistemas cadastrados no Bloco 2

---
