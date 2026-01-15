## AGRINT.DAT

### 1. Informações do Arquivo

#### 1.1. Nome e Descrição

- **Nome do arquivo**: `agrint.dat` ou `AGRINT.DAT`
- **Tipo**: Arquivo de entrada do modelo NEWAVE
- **Função**: Permite ao usuário definir **restrições lineares** envolvendo as interligações entre subsistemas (submercados)

#### 1.2. Função e Ativação

**Funcionalidade:**
A funcionalidade de agrupamento livre de interligações é utilizada para representar limites de transmissão complexos.

**Habilitação:**
- Os registros contidos no `AGRINT.DAT` são considerados somente se o **registro 47 do arquivo de dados gerais (`dger.dat`)** estiver preenchido com o valor igual a **1 (um)**

**Formulação Matemática:**
Um agrupamento (`Agr`) pode ser definido como uma **combinação linear** de interligações que o compõem, seguindo a forma:

$$Agr = k_1 \cdot \text{Interc}(A \to B) + k_2 \cdot \text{Interc}(A \to C) + \dots + k_n \cdot \text{Interc}(J \to K) \le \text{LIMITE}$$

onde:
- $k_i$ são os coeficientes associados a cada interligação
- $\text{Interc}(X \to Y)$ representa a interligação do subsistema X para o subsistema Y
- $\text{LIMITE}$ é o limite máximo permitido para o agrupamento (em MWmédio)

**Capacidade máxima:**
A capacidade máxima de agrupamentos de intercâmbio que o programa suporta é de **20**.

#### 1.3. Estrutura do Arquivo

O `AGRINT.DAT` é composto por **dois blocos de dados**, precedidos por **três registros de comentários**, que são de existência obrigatória para orientação do usuário, mas são ignorados pelo programa.

#### 1.4. Bloco 1: Definição dos Agrupamentos

Este bloco é composto por registros que definem quais interligações formam cada agrupamento e os coeficientes associados.

| Campo | Colunas | Formato | Descrição |
| :--- | :--- | :--- | :--- |
| 1 | 2 a 4 | I3 | **Número do agrupamento** |
| 2 | 6 a 8 | I3 | **Subsistema/submercado de origem** da interligação |
| 3 | 10 a 12 | I3 | **Subsistema/submercado de destino** da interligação |
| 4 | 14 a 20 | F7.4 | **Coeficiente** associado à interligação que compõe o agrupamento ($k_i$) |

**Regras para o Bloco 1:**

1. Os subsistemas/submercados de origem e destino devem estar previamente declarados no arquivo `sistema.dat`

2. Deve existir **capacidade inflexível de intercâmbio** para a interligação declarada no arquivo `sistema.dat`

3. O coeficiente declarado no campo 4 ($k_i$) deve ser **maior do que zero**

4. Se for declarado mais de um registro para a mesma interligação e para o mesmo agrupamento, **somente o último registro será considerado**

5. O código **`999` no campo 1 indica o final do bloco**

#### 1.5. Bloco 2: Definição dos Limites do Agrupamento

Este bloco informa o limite do agrupamento de intercâmbio (em MWmédio) para **todos os patamares de carga** durante um período de tempo definido pelo usuário.

| Campo | Colunas | Formato | Descrição |
| :--- | :--- | :--- | :--- |
| 1 | 2 a 4 | I3 | **Número do agrupamento** |
| 2 | 7 a 8 | I2 | Mês de **início** para o limite do agrupamento |
| 3 | 10 a 13 | I4 | Ano de **início** para o limite do agrupamento |
| 4 | 15 a 16 | I2 | Mês de **fim** para o limite do agrupamento |
| 5 | 18 a 21 | I4 | Ano de **fim** para o limite do agrupamento |
| 6 | 23 a 29 | F7.0 | **Limite do agrupamento (MWmédio)** para o **primeiro patamar** de carga |
| 7 | 31 a 37 | F7.0 | Limite do agrupamento (MWmédio) para o **segundo patamar** de carga |
| 8 | 39 a 45 | F7.0 | Limite do agrupamento (MWmédio) para o **terceiro patamar** de carga |
| 9 | 47 a 53 | F7.0 | Limite do agrupamento (MWmédio) para o **quarto patamar** de carga |
| 10 | 55 a 61 | F7.0 | Limite do agrupamento (MWmédio) para o **quinto patamar** de carga |

**Regras para o Bloco 2:**

1. Os agrupamentos informados no campo 1 devem ter sido declarados no Bloco 1

2. A data inicial (campos 2 e 3) deve ser anterior ou igual à data final (campos 4 e 5)

3. Se a data inicial estiver em branco e a data final estiver preenchida, o limite será considerado a partir do **início do período de planejamento**. Se a data inicial for anterior ao período de planejamento, ela será deslocada para o início do período

4. Se a data final estiver em branco e a data inicial estiver preenchida, o limite será considerado até o **final do horizonte de planejamento**. Se a data final for posterior ao fim do período, ela será deslocada para o final do horizonte

5. Se as datas inicial e final estiverem em branco, o programa será interrompido com mensagem de erro

6. Os valores de limite (campos 6 a 10) devem ser **maiores ou iguais a zero** para serem considerados

7. Para não informar uma restrição em um determinado patamar, deve-se declarar um **limite igual a –1** para esse patamar. Valores negativos diferentes de -1 serão criticados pelo programa

8. O código **`999` no campo 1 indica o final do bloco**

---

### 2. Propriedades da Biblioteca inewave

#### 2.1. Classe Correspondente

**Classe**: `Agrint`

```python
class Agrint(data=<cfinterface.data.sectiondata.SectionData object>)
```

**Descrição**: Armazena os dados de entrada do NEWAVE referentes aos agrupamentos de intercâmbio.

#### 2.2. Propriedades Disponíveis

##### `property` **agrupamentos**: `pd.DataFrame | None`

- **Descrição**: Tabela com os intercâmbios em cada agrupamento
- **Tipo de retorno**: `pd.DataFrame | None`
- **Corresponde a**: Bloco 1 do arquivo (Definição dos Agrupamentos)
- **Colunas do DataFrame**:
  - `agrupamento` (`int`): Número do agrupamento (corresponde ao campo 1 do Bloco 1)
  - `submercado_de` (`int`): Subsistema/submercado de origem da interligação (corresponde ao campo 2 do Bloco 1)
  - `submercado_para` (`int`): Subsistema/submercado de destino da interligação (corresponde ao campo 3 do Bloco 1)
  - `coeficiente` (`float`): Coeficiente associado à interligação ($k_i$) (corresponde ao campo 4 do Bloco 1)

**Observações:**
- Esta propriedade contém a definição de quais interligações formam cada agrupamento
- Cada linha representa uma interligação que compõe um agrupamento específico
- O coeficiente indica o peso dessa interligação na combinação linear do agrupamento
- Se o arquivo não existir ou não contiver agrupamentos, a propriedade retorna `None`

##### `property` **limites_agrupamentos**: `pd.DataFrame | None`

- **Descrição**: Tabela com os limites dos agrupamentos de intercâmbio durante o período de estudo
- **Tipo de retorno**: `pd.DataFrame | None`
- **Corresponde a**: Bloco 2 do arquivo (Definição dos Limites)
- **Colunas do DataFrame**:
  - `agrupamento` (`int`): Número do agrupamento (corresponde ao campo 1 do Bloco 2)
  - `data_inicio` (`datetime`): Data de início para o limite do agrupamento (combinação dos campos 2 e 3 do Bloco 2: mês e ano de início)
  - `data_fim` (`datetime`): Data de fim para o limite do agrupamento (combinação dos campos 4 e 5 do Bloco 2: mês e ano de fim)
  - `comentario` (`str`): Comentário associado ao limite (adicionado pela biblioteca, se disponível no arquivo)
  - `patamar` (`int`): Número do patamar de carga (1, 2, 3, 4 ou 5)
  - `valor` (`float`): Limite do agrupamento em MWmédio para o patamar correspondente (corresponde aos campos 6-10 do Bloco 2)

**Observações:**
- Esta propriedade contém os limites aplicados a cada agrupamento para cada patamar de carga
- Cada linha representa um limite de um agrupamento para um patamar específico em um período determinado
- Os campos de data são automaticamente convertidos de string para objeto `datetime` do Python
- O limite de -1 indica que não há restrição para aquele patamar
- Se o arquivo não contiver limites ou estiver vazio, a propriedade retorna `None`

**Estrutura dos dados:**
- Os limites de cada patamar (campos 6-10 do arquivo) são transformados em linhas separadas no DataFrame
- Cada registro do arquivo gera até 5 linhas no DataFrame (uma para cada patamar com limite diferente de -1)

---

### 3. Mapeamento de Campos

#### 3.1. Bloco 1 → Propriedade `agrupamentos`

| Campo do Arquivo | Colunas | Formato | Coluna DataFrame | Tipo Python | Descrição |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Número do agrupamento | 2-4 | I3 | `agrupamento` | `int` | Identificador do agrupamento |
| Subsistema de origem | 6-8 | I3 | `submercado_de` | `int` | Subsistema/submercado de origem |
| Subsistema de destino | 10-12 | I3 | `submercado_para` | `int` | Subsistema/submercado de destino |
| Coeficiente | 14-20 | F7.4 | `coeficiente` | `float` | Coeficiente $k_i$ da combinação linear |

#### 3.2. Bloco 2 → Propriedade `limites_agrupamentos`

| Campo do Arquivo | Colunas | Formato | Coluna DataFrame | Tipo Python | Descrição |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Número do agrupamento | 2-4 | I3 | `agrupamento` | `int` | Identificador do agrupamento |
| Mês de início | 7-8 | I2 | (parte de `data_inicio`) | `datetime.month` | Mês de início |
| Ano de início | 10-13 | I4 | (parte de `data_inicio`) | `datetime.year` | Ano de início |
| Mês de fim | 15-16 | I2 | (parte de `data_fim`) | `datetime.month` | Mês de fim |
| Ano de fim | 18-21 | I4 | (parte de `data_fim`) | `datetime.year` | Ano de fim |
| Limite Patamar 1 | 23-29 | F7.0 | `valor` (quando `patamar=1`) | `float` | Limite para patamar 1 (MWmédio) |
| Limite Patamar 2 | 31-37 | F7.0 | `valor` (quando `patamar=2`) | `float` | Limite para patamar 2 (MWmédio) |
| Limite Patamar 3 | 39-45 | F7.0 | `valor` (quando `patamar=3`) | `float` | Limite para patamar 3 (MWmédio) |
| Limite Patamar 4 | 47-53 | F7.0 | `valor` (quando `patamar=4`) | `float` | Limite para patamar 4 (MWmédio) |
| Limite Patamar 5 | 55-61 | F7.0 | `valor` (quando `patamar=5`) | `float` | Limite para patamar 5 (MWmédio) |

**Observação**: Os limites de cada patamar são transformados em linhas separadas no DataFrame. O campo `comentario` é adicionado pela biblioteca se houver comentários no arquivo.

---

### 4. Exemplos de Uso

#### 4.1. Leitura do Arquivo

```python
from inewave.newave import Agrint

# Ler o arquivo agrint.dat
agrint = Agrint.read("agrint.dat")

# Acessar os agrupamentos
df_agrupamentos = agrint.agrupamentos

if df_agrupamentos is not None:
    print(f"Total de interligações em agrupamentos: {len(df_agrupamentos)}")
    print(f"Total de agrupamentos únicos: {df_agrupamentos['agrupamento'].nunique()}")
    print(df_agrupamentos.head())
else:
    print("Nenhum agrupamento encontrado ou arquivo vazio")
```

#### 4.2. Consulta de Agrupamentos

```python
from inewave.newave import Agrint

agrint = Agrint.read("agrint.dat")

if agrint.agrupamentos is not None:
    # Filtrar interligações de um agrupamento específico
    numero_agrupamento = 1
    interligacoes = agrint.agrupamentos[
        agrint.agrupamentos['agrupamento'] == numero_agrupamento
    ]
    
    print(f"Interligações do agrupamento {numero_agrupamento}:")
    print(interligacoes[['submercado_de', 'submercado_para', 'coeficiente']])
```

#### 4.3. Consulta de Limites por Agrupamento

```python
from inewave.newave import Agrint

agrint = Agrint.read("agrint.dat")

if agrint.limites_agrupamentos is not None:
    # Filtrar limites de um agrupamento específico
    numero_agrupamento = 1
    limites = agrint.limites_agrupamentos[
        agrint.limites_agrupamentos['agrupamento'] == numero_agrupamento
    ]
    
    print(f"Limites do agrupamento {numero_agrupamento}:")
    print(limites[['data_inicio', 'data_fim', 'patamar', 'valor']])
```

#### 4.4. Consulta de Limites por Período

```python
from inewave.newave import Agrint
from datetime import datetime

agrint = Agrint.read("agrint.dat")

if agrint.limites_agrupamentos is not None:
    # Filtrar limites em um período específico
    data_inicio_periodo = datetime(2023, 1, 1)
    data_fim_periodo = datetime(2023, 12, 31)
    
    # Limites que se sobrepõem ao período
    limites_periodo = agrint.limites_agrupamentos[
        (agrint.limites_agrupamentos['data_inicio'] <= data_fim_periodo) &
        (agrint.limites_agrupamentos['data_fim'] >= data_inicio_periodo)
    ]
    
    print(f"Limites no período {data_inicio_periodo.date()} a {data_fim_periodo.date()}:")
    print(limites_periodo)
```

#### 4.5. Consulta de Limites por Patamar

```python
from inewave.newave import Agrint

agrint = Agrint.read("agrint.dat")

if agrint.limites_agrupamentos is not None:
    # Filtrar limites de um patamar específico
    patamar = 1
    limites_patamar = agrint.limites_agrupamentos[
        agrint.limites_agrupamentos['patamar'] == patamar
    ]
    
    print(f"Limites do patamar {patamar}:")
    print(limites_patamar[['agrupamento', 'data_inicio', 'data_fim', 'valor']])
```

#### 4.6. Análise de Coeficientes por Agrupamento

```python
from inewave.newave import Agrint

agrint = Agrint.read("agrint.dat")

if agrint.agrupamentos is not None:
    # Calcular estatísticas dos coeficientes por agrupamento
    estatisticas = agrint.agrupamentos.groupby('agrupamento')['coeficiente'].agg([
        'count', 'mean', 'min', 'max', 'sum'
    ])
    
    print("Estatísticas dos coeficientes por agrupamento:")
    print(estatisticas)
    
    # Identificar agrupamentos com maior número de interligações
    interligacoes_por_agrupamento = agrint.agrupamentos.groupby('agrupamento').size().sort_values(ascending=False)
    
    print("\nAgrupamentos ordenados por número de interligações:")
    print(interligacoes_por_agrupamento)
```

#### 4.7. Consulta Combinada: Agrupamentos e Limites

```python
from inewave.newave import Agrint

agrint = Agrint.read("agrint.dat")

# Obter informações completas de um agrupamento
numero_agrupamento = 1

if agrint.agrupamentos is not None:
    # Interligações do agrupamento
    interligacoes = agrint.agrupamentos[
        agrint.agrupamentos['agrupamento'] == numero_agrupamento
    ]
    
    print(f"Interligações do agrupamento {numero_agrupamento}:")
    print(interligacoes[['submercado_de', 'submercado_para', 'coeficiente']])
    
    # Limites do agrupamento
    if agrint.limites_agrupamentos is not None:
        limites = agrint.limites_agrupamentos[
            agrint.limites_agrupamentos['agrupamento'] == numero_agrupamento
        ]
        
        if not limites.empty:
            print(f"\nLimites do agrupamento {numero_agrupamento}:")
            print(limites[['data_inicio', 'data_fim', 'patamar', 'valor']])
```

#### 4.8. Consulta por Subsistema (Origem ou Destino)

```python
from inewave.newave import Agrint

agrint = Agrint.read("agrint.dat")

if agrint.agrupamentos is not None:
    # Filtrar interligações que partem de um subsistema específico
    subsistema_origem = 1
    interligacoes_de = agrint.agrupamentos[
        agrint.agrupamentos['submercado_de'] == subsistema_origem
    ]
    
    print(f"Interligações que partem do subsistema {subsistema_origem}:")
    print(interligacoes_de)
    
    # Filtrar interligações que chegam a um subsistema específico
    subsistema_destino = 3
    interligacoes_para = agrint.agrupamentos[
        agrint.agrupamentos['submercado_para'] == subsistema_destino
    ]
    
    print(f"\nInterligações que chegam ao subsistema {subsistema_destino}:")
    print(interligacoes_para)
```

#### 4.9. Validação de Dados

```python
from inewave.newave import Agrint

agrint = Agrint.read("agrint.dat")

# Validar agrupamentos
if agrint.agrupamentos is not None:
    df_agrupamentos = agrint.agrupamentos
    
    # Verificar se há dados
    if len(df_agrupamentos) == 0:
        print("⚠️ Nenhum agrupamento encontrado no arquivo")
    
    # Verificar campos obrigatórios
    campos_obrigatorios = ['agrupamento', 'submercado_de', 'submercado_para', 'coeficiente']
    campos_faltando = [campo for campo in campos_obrigatorios if campo not in df_agrupamentos.columns]
    
    if campos_faltando:
        print(f"⚠️ Campos faltando: {campos_faltando}")
    
    # Verificar coeficientes positivos
    coeficientes_negativos = df_agrupamentos[df_agrupamentos['coeficiente'] <= 0]
    if len(coeficientes_negativos) > 0:
        print(f"⚠️ {len(coeficientes_negativos)} interligações com coeficiente não positivo encontradas")
    
    # Verificar duplicatas (mesma interligação no mesmo agrupamento)
    duplicatas = df_agrupamentos.groupby(['agrupamento', 'submercado_de', 'submercado_para']).size()
    duplicatas = duplicatas[duplicatas > 1]
    if len(duplicatas) > 0:
        print(f"⚠️ {len(duplicatas)} interligações duplicadas encontradas (última será considerada)")

# Validar limites
if agrint.limites_agrupamentos is not None:
    df_limites = agrint.limites_agrupamentos
    
    # Verificar datas válidas
    if 'data_inicio' in df_limites.columns and 'data_fim' in df_limites.columns:
        datas_invalidas = df_limites[df_limites['data_fim'] < df_limites['data_inicio']]
        if len(datas_invalidas) > 0:
            print(f"⚠️ {len(datas_invalidas)} limites com data de fim anterior à data de início")
    
    # Verificar limites negativos (exceto -1)
    limites_invalidos = df_limites[
        (df_limites['valor'] < 0) & (df_limites['valor'] != -1)
    ]
    if len(limites_invalidos) > 0:
        print(f"⚠️ {len(limites_invalidos)} limites com valores negativos inválidos (diferentes de -1)")
    
    # Verificar se os agrupamentos dos limites existem nos agrupamentos
    if agrint.agrupamentos is not None:
        agrupamentos_definidos = set(agrint.agrupamentos['agrupamento'].unique())
        agrupamentos_com_limite = set(df_limites['agrupamento'].unique())
        agrupamentos_inexistentes = agrupamentos_com_limite - agrupamentos_definidos
        
        if agrupamentos_inexistentes:
            print(f"⚠️ Limites definidos para agrupamentos não declarados: {agrupamentos_inexistentes}")
```

#### 4.10. Modificação e Gravação

```python
from inewave.newave import Agrint

# Ler o arquivo
agrint = Agrint.read("agrint.dat")

if agrint.agrupamentos is not None:
    # Modificar coeficiente de uma interligação específica
    numero_agrupamento = 1
    subsistema_de = 1
    subsistema_para = 3
    
    mask = (
        (agrint.agrupamentos['agrupamento'] == numero_agrupamento) &
        (agrint.agrupamentos['submercado_de'] == subsistema_de) &
        (agrint.agrupamentos['submercado_para'] == subsistema_para)
    )
    
    if mask.any():
        # Modificar o coeficiente
        agrint.agrupamentos.loc[mask, 'coeficiente'] = 1.5
        print(f"Coeficiente da interligação {subsistema_de}->{subsistema_para} no agrupamento {numero_agrupamento} atualizado para 1.5")
    
    # Salvar alterações
    agrint.write("agrint.dat")
```

---

### 5. Observações Importantes

1. **Habilitação**: O arquivo só é considerado se o registro 47 do `dger.dat` estiver preenchido com valor igual a 1

2. **Capacidade máxima**: O programa suporta no máximo **20 agrupamentos** de intercâmbio

3. **Dependências**: 
   - Os subsistemas/submercados devem estar previamente declarados no arquivo `sistema.dat`
   - Deve existir capacidade inflexível de intercâmbio para cada interligação no arquivo `sistema.dat`

4. **Coeficientes**: Todos os coeficientes ($k_i$) devem ser **maiores que zero**

5. **Duplicatas**: Se a mesma interligação for declarada múltiplas vezes para o mesmo agrupamento, apenas o último registro será considerado

6. **Limites por patamar**: 
   - Cada limite é definido separadamente para cada patamar de carga (1 a 5)
   - O valor -1 indica que não há restrição para aquele patamar
   - Valores negativos diferentes de -1 geram erro

7. **Validade dos limites**: Os limites devem ser **maiores ou iguais a zero** (exceto -1 para sem restrição)

8. **Datas**: 
   - A data inicial deve ser anterior ou igual à data final
   - Datas em branco seguem regras específicas (início ou fim do período de planejamento)
   - Se ambas as datas estiverem em branco, o programa será interrompido com erro

9. **Estrutura de dados**: 
   - A propriedade `limites_agrupamentos` transforma os limites de cada patamar em linhas separadas
   - Cada registro do arquivo gera até 5 linhas no DataFrame (uma por patamar)

10. **DataFrame pandas**: Ambas as propriedades retornam DataFrames do pandas, permitindo uso completo das funcionalidades do pandas para análise e manipulação

11. **Formulação matemática**: O agrupamento representa uma combinação linear de interligações, permitindo modelar restrições complexas de transmissão

12. **Comentários**: Os registros de comentário no início dos blocos são obrigatórios mas ignorados pelo programa

---
