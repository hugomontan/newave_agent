## CLAST.DAT

### 1. Informações do Arquivo

#### 1.1. Nome e Descrição

- **Nome do arquivo**: `clast.dat` ou `CLAST.DAT`
- **Tipo**: Arquivo de entrada essencial do modelo NEWAVE
- **Função**: Agrupar as usinas termoelétricas em classes com base em custos de operação semelhantes e definir o tipo de combustível

#### 1.2. Função e Estrutura Geral

O `CLAST.DAT` é usado para definir e parametrizar o **Sistema de Geração Termoelétrico**, onde as usinas são representadas por **grupos de térmicas com custos semelhantes** (classes térmicas), que estão associadas a subsistemas/submercados.

**Estrutura do arquivo:**
- O arquivo começa com um conjunto de **dois registros destinados a comentários**, que são obrigatórios, mas ignorados pelo programa, servindo apenas para orientação do usuário
- O conteúdo subsequente é composto por **dois tipos principais de registros**:
  - **Registro Tipo 1**: Definição da classe térmica
  - **Registro Tipo 2**: Modificação sazonal do custo

**Contexto Adicional:**
O custo incremental de operação é um dos parâmetros básicos das classes termoelétricas, juntamente com a geração máxima e a geração mínima. Este arquivo é fundamental para a representação do Sistema de Geração Termoelétrico no NEWAVE.

#### 1.3. Registros Tipo 1 (Definição da Classe)

O Registro Tipo 1 é utilizado para definir a classe térmica, seu tipo de combustível e os custos de operação para cada ano do período de planejamento.

| Campo | Colunas | Formato | Descrição |
| :--- | :--- | :--- | :--- |
| 1 | 2 a 5 | I4 | **Número da classe térmica** |
| 2 | 7 a 18 | A12 | **Nome da classe térmica** |
| 3 | 20 a 29 | A10 | **Tipo de combustível** da classe térmica |
| 4 | 31 a 37 | F7.2 | **Custo de operação** da classe térmica para o **primeiro ano** do período de planejamento ($/MWh) |
| 5 | 39 a 45 | F7.2 | **Custo de operação** da classe térmica para o **segundo ano** do período de planejamento ($/MWh) |
| **...** | | | **Haverá um custo de operação para cada ano do período de planejamento** |

**Fim do bloco:**
- O valor **`9999`** no campo 1 indica o fim da definição deste registro

#### 1.4. Registros Tipo 2 (Modificação Sazonal do Custo)

Antes do Registro Tipo 2, devem existir **dois registros destinados a comentários**, que são ignorados pelo programa. O Registro Tipo 2 permite a modificação do custo de operação da classe térmica com datas de início e fim.

| Campo | Colunas | Formato | Descrição |
| :--- | :--- | :--- | :--- |
| 1 | 2 a 5 | I4 | **Número da classe térmica** |
| 2 | 9 a 15 | F7.2 | **Novo valor do Custo de operação** da classe térmica ($/MWh) |
| 3 | 18 a 19 | I2 | **Mês de início** da modificação |
| 4 | 21 a 24 | I4 | **Ano de início** da modificação |
| 5 | 27 a 28 | I2 | **Mês de fim** da modificação |
| 6 | 30 a 33 | I4 | **Ano de fim** da modificação |

**Regras de Validade para Modificação:**

1. Se os campos 5 e 6 (mês e ano de fim) **não forem preenchidos**, a modificação será válida até o **fim do período de planejamento**

2. Se os campos 3, 4, 5 e 6 (datas de início e fim) **não forem preenchidos**, a modificação será válida apenas para o **primeiro mês do primeiro ano de planejamento**

---

### 2. Propriedades da Biblioteca inewave

#### 2.1. Classe Correspondente

**Classe**: `Clast`

```python
class Clast(data=<cfinterface.data.sectiondata.SectionData object>)
```

**Descrição**: Armazena os dados de entrada do NEWAVE referentes às classes de usinas térmicas.

#### 2.2. Propriedades Disponíveis

##### `property` **usinas**: `pd.DataFrame | None`

- **Descrição**: Tabela com as usinas e seus custos
- **Tipo de retorno**: `pd.DataFrame | None`
- **Colunas do DataFrame**:
  - `codigo_usina` (`int`): Número da classe térmica (corresponde ao "Número da classe térmica" do Registro Tipo 1)
  - `nome_usina` (`str`): Nome da classe térmica (corresponde ao "Nome da classe térmica" do Registro Tipo 1)
  - `tipo_combustivel` (`str`): Tipo de combustível da classe térmica (corresponde ao "Tipo de combustível" do Registro Tipo 1)
  - `indice_ano_estudo` (`int`): Índice do ano do período de planejamento (1 = primeiro ano, 2 = segundo ano, etc.)
  - `valor` (`float`): Custo de operação da classe térmica para o ano correspondente ($/MWh)

**Observações:**
- Esta propriedade corresponde aos **Registros Tipo 1** do arquivo
- Cada linha representa o custo de uma classe térmica para um ano específico do período de planejamento
- O campo `codigo_usina` na verdade contém o número da classe térmica (não da usina individual)
- Se o arquivo não existir ou estiver vazio, a propriedade retorna `None`

##### `property` **modificacoes**: `pd.DataFrame | None`

- **Descrição**: Tabela com as modificações de custos das usinas organizadas por usina
- **Tipo de retorno**: `pd.DataFrame | None`
- **Colunas do DataFrame**:
  - `codigo_usina` (`int`): Número da classe térmica (corresponde ao campo 1 do Registro Tipo 2)
  - `nome_usina` (`str`): Nome da classe térmica (adicionado pela biblioteca)
  - `data_inicio` (`datetime`): Data de início da modificação (combinação dos campos 3 e 4 do Registro Tipo 2: mês e ano de início)
  - `data_fim` (`datetime`): Data de fim da modificação (combinação dos campos 5 e 6 do Registro Tipo 2: mês e ano de fim)
  - `custo` (`float`): Novo valor do custo de operação ($/MWh) (corresponde ao campo 2 do Registro Tipo 2)

**Observações:**
- Esta propriedade corresponde aos **Registros Tipo 2** do arquivo
- Os campos de data são automaticamente convertidos de string para objeto `datetime` do Python
- Se os campos de data não forem preenchidos no arquivo, a biblioteca pode definir valores padrão conforme as regras de validação
- Se o arquivo não contiver modificações ou estiver vazio, a propriedade retorna `None`

---

### 3. Mapeamento de Campos

#### 3.1. Registro Tipo 1 → Propriedade `usinas`

| Campo do Arquivo | Colunas | Formato | Coluna DataFrame | Tipo Python | Descrição |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Número da classe | 2-5 | I4 | `codigo_usina` | `int` | Identificador da classe térmica |
| Nome da classe | 7-18 | A12 | `nome_usina` | `str` | Nome da classe térmica |
| Tipo de combustível | 20-29 | A10 | `tipo_combustivel` | `str` | Tipo de combustível usado |
| Custo ano 1 | 31-37 | F7.2 | `valor` (quando `indice_ano_estudo=1`) | `float` | Custo para o primeiro ano ($/MWh) |
| Custo ano 2 | 39-45 | F7.2 | `valor` (quando `indice_ano_estudo=2`) | `float` | Custo para o segundo ano ($/MWh) |
| Custo ano N | ... | F7.2 | `valor` (quando `indice_ano_estudo=N`) | `float` | Custo para o ano N ($/MWh) |

**Observação**: Cada custo de operação para cada ano é representado como uma linha separada no DataFrame, com o campo `indice_ano_estudo` indicando qual ano corresponde.

#### 3.2. Registro Tipo 2 → Propriedade `modificacoes`

| Campo do Arquivo | Colunas | Formato | Coluna DataFrame | Tipo Python | Descrição |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Número da classe | 2-5 | I4 | `codigo_usina` | `int` | Identificador da classe térmica |
| Novo custo | 9-15 | F7.2 | `custo` | `float` | Novo valor do custo ($/MWh) |
| Mês de início | 18-19 | I2 | (parte de `data_inicio`) | `datetime.month` | Mês de início da modificação |
| Ano de início | 21-24 | I4 | (parte de `data_inicio`) | `datetime.year` | Ano de início da modificação |
| Mês de fim | 27-28 | I2 | (parte de `data_fim`) | `datetime.month` | Mês de fim da modificação |
| Ano de fim | 30-33 | I4 | (parte de `data_fim`) | `datetime.year` | Ano de fim da modificação |

**Observação**: Os campos de data são combinados em objetos `datetime`. O campo `nome_usina` é adicionado pela biblioteca inewave.

---

### 4. Exemplos de Uso

#### 4.1. Leitura do Arquivo

```python
from inewave.newave import Clast

# Ler o arquivo clast.dat
clast = Clast.read("clast.dat")

# Acessar a tabela de usinas (classes térmicas)
df_usinas = clast.usinas

if df_usinas is not None:
    print(f"Total de classes térmicas: {df_usinas['codigo_usina'].nunique()}")
    print(f"Total de registros de custos: {len(df_usinas)}")
    print(df_usinas.head())
else:
    print("Nenhuma classe térmica encontrada ou arquivo vazio")
```

#### 4.2. Consulta de Custos por Classe Térmica

```python
from inewave.newave import Clast

clast = Clast.read("clast.dat")

if clast.usinas is not None:
    # Filtrar custos de uma classe térmica específica
    codigo_classe = 1
    custos_classe = clast.usinas[
        clast.usinas['codigo_usina'] == codigo_classe
    ]
    
    print(f"Custos da classe térmica {codigo_classe}:")
    print(custos_classe[['nome_usina', 'tipo_combustivel', 'indice_ano_estudo', 'valor']])
```

#### 4.3. Consulta por Nome de Classe

```python
from inewave.newave import Clast

clast = Clast.read("clast.dat")

if clast.usinas is not None:
    # Filtrar por nome da classe (busca parcial, case-insensitive)
    nome_procurado = "GNL"
    classes_filtradas = clast.usinas[
        clast.usinas['nome_usina'].str.contains(nome_procurado, case=False, na=False)
    ]
    
    print(f"Classes encontradas para '{nome_procurado}':")
    print(classes_filtradas[['codigo_usina', 'nome_usina', 'tipo_combustivel', 'indice_ano_estudo', 'valor']])
```

#### 4.4. Consulta de Modificações Sazonais

```python
from inewave.newave import Clast

clast = Clast.read("clast.dat")

if clast.modificacoes is not None:
    print(f"Total de modificações sazonais: {len(clast.modificacoes)}")
    print("\nModificações:")
    print(clast.modificacoes)
else:
    print("Nenhuma modificação sazonal encontrada")
```

#### 4.5. Análise de Custos por Ano

```python
from inewave.newave import Clast

clast = Clast.read("clast.dat")

if clast.usinas is not None:
    # Agrupar custos por ano
    custos_por_ano = clast.usinas.groupby('indice_ano_estudo')['valor'].agg(['mean', 'min', 'max'])
    
    print("Estatísticas de custos por ano:")
    print(custos_por_ano)
    
    # Custo médio por classe
    custo_medio_classe = clast.usinas.groupby('nome_usina')['valor'].mean().sort_values(ascending=False)
    
    print("\nCusto médio por classe térmica:")
    print(custo_medio_classe)
```

#### 4.6. Consulta de Modificações por Classe

```python
from inewave.newave import Clast

clast = Clast.read("clast.dat")

if clast.modificacoes is not None:
    # Filtrar modificações de uma classe específica
    codigo_classe = 1
    modif_classe = clast.modificacoes[
        clast.modificacoes['codigo_usina'] == codigo_classe
    ]
    
    if not modif_classe.empty:
        print(f"Modificações da classe {codigo_classe}:")
        print(modif_classe[['nome_usina', 'data_inicio', 'data_fim', 'custo']])
    else:
        print(f"Nenhuma modificação encontrada para a classe {codigo_classe}")
```

#### 4.7. Consulta de Modificações por Período

```python
from inewave.newave import Clast
from datetime import datetime

clast = Clast.read("clast.dat")

if clast.modificacoes is not None:
    # Filtrar modificações em um período específico
    data_inicio_periodo = datetime(2024, 1, 1)
    data_fim_periodo = datetime(2024, 12, 31)
    
    # Modificações que se sobrepõem ao período
    modif_periodo = clast.modificacoes[
        (clast.modificacoes['data_inicio'] <= data_fim_periodo) &
        (clast.modificacoes['data_fim'] >= data_inicio_periodo)
    ]
    
    print(f"Modificações no período {data_inicio_periodo.date()} a {data_fim_periodo.date()}:")
    print(modif_periodo)
```

#### 4.8. Consulta Combinada: Custos Base + Modificações

```python
from inewave.newave import Clast

clast = Clast.read("clast.dat")

# Obter classe específica
codigo_classe = 1

if clast.usinas is not None:
    # Custos base da classe
    custos_base = clast.usinas[clast.usinas['codigo_usina'] == codigo_classe]
    print(f"Custos base da classe {codigo_classe}:")
    print(custos_base[['nome_usina', 'indice_ano_estudo', 'valor']])
    
    # Modificações da classe
    if clast.modificacoes is not None:
        modif_classe = clast.modificacoes[clast.modificacoes['codigo_usina'] == codigo_classe]
        if not modif_classe.empty:
            print(f"\nModificações sazonais da classe {codigo_classe}:")
            print(modif_classe[['data_inicio', 'data_fim', 'custo']])
```

#### 4.9. Validação de Dados

```python
from inewave.newave import Clast

clast = Clast.read("clast.dat")

# Validar usinas
if clast.usinas is not None:
    df_usinas = clast.usinas
    
    # Verificar se há dados
    if len(df_usinas) == 0:
        print("⚠️ Nenhuma classe térmica encontrada no arquivo")
    
    # Verificar campos obrigatórios
    campos_obrigatorios = ['codigo_usina', 'nome_usina', 'tipo_combustivel', 'indice_ano_estudo', 'valor']
    campos_faltando = [campo for campo in campos_obrigatorios if campo not in df_usinas.columns]
    
    if campos_faltando:
        print(f"⚠️ Campos faltando: {campos_faltando}")
    
    # Verificar valores negativos de custo
    custos_negativos = df_usinas[df_usinas['valor'] < 0]
    if len(custos_negativos) > 0:
        print(f"⚠️ {len(custos_negativos)} registros com custo negativo encontrados")
    
    # Verificar classes duplicadas por ano
    duplicatas = df_usinas.groupby(['codigo_usina', 'indice_ano_estudo']).size()
    duplicatas = duplicatas[duplicatas > 1]
    if len(duplicatas) > 0:
        print(f"⚠️ {len(duplicatas)} classes com múltiplos custos para o mesmo ano")

# Validar modificações
if clast.modificacoes is not None:
    df_modif = clast.modificacoes
    
    # Verificar datas válidas
    if 'data_inicio' in df_modif.columns and 'data_fim' in df_modif.columns:
        datas_invalidas = df_modif[df_modif['data_fim'] < df_modif['data_inicio']]
        if len(datas_invalidas) > 0:
            print(f"⚠️ {len(datas_invalidas)} modificações com data de fim anterior à data de início")
```

#### 4.10. Modificação e Gravação

```python
from inewave.newave import Clast

# Ler o arquivo
clast = Clast.read("clast.dat")

if clast.usinas is not None:
    # Modificar custo de uma classe para um ano específico
    codigo_classe = 1
    ano = 1
    
    # Localizar o registro
    mask = (clast.usinas['codigo_usina'] == codigo_classe) & \
           (clast.usinas['indice_ano_estudo'] == ano)
    
    if mask.any():
        # Modificar o valor
        clast.usinas.loc[mask, 'valor'] = 150.0
        print(f"Custo da classe {codigo_classe} para o ano {ano} atualizado para 150.0 $/MWh")
    
    # Salvar alterações
    clast.write("clast.dat")
```

---

### 5. Observações Importantes

1. **Classes térmicas vs Usinas**: As "classes térmicas" agrupam usinas com custos semelhantes. O campo `codigo_usina` no DataFrame na verdade representa o número da classe, não de uma usina individual

2. **Estrutura de dados**: A propriedade `usinas` representa cada custo anual como uma linha separada, facilitando consultas por ano, mas requer agrupamento para ver todos os custos de uma classe

3. **Modificações sazonais**: As modificações (Registro Tipo 2) são aplicadas sobre os custos base (Registro Tipo 1) e têm precedência durante o período especificado

4. **Regras de validação**: As modificações seguem regras específicas:
   - Se data de fim não for preenchida: válida até o fim do período de planejamento
   - Se nenhuma data for preenchida: válida apenas para o primeiro mês do primeiro ano

5. **Tipo de combustível**: Este campo é importante para classificação e análise das classes térmicas (ex: GNL, Carvão, Óleo)

6. **Unidade de custo**: Todos os custos são expressos em **$/MWh** (dólares por megawatt-hora)

7. **Período de planejamento**: O número de anos de custos definidos depende do período de planejamento configurado no modelo NEWAVE

8. **Formato fixo**: O arquivo segue formato fixo de colunas, onde a posição exata dos campos é importante

9. **Comentários**: Os registros de comentário no início de cada bloco são obrigatórios mas ignorados pelo programa

10. **DataFrame pandas**: Ambas as propriedades retornam DataFrames do pandas, permitindo uso completo das funcionalidades do pandas para análise e manipulação

---
