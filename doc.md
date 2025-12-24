# Documentação Completa - Arquivos NEWAVE e Propriedades da Biblioteca inewave

Este documento detalha todas as informações presentes nos arquivos NEWAVE e as propriedades correspondentes na biblioteca `inewave`.

---

## 📋 Índice

- [Estrutura do Documento](#estrutura-do-documento)
- [Arquivos Documentados](#arquivos-documentados)
- [CASO.DAT](#casodat)
- [MANUTT.DAT](#manuttdat)
- [CLAST.DAT](#clastdat)
- [AGRINT.DAT](#agrintdat)
- [CVAR.DAT](#cvardat)
- [SISTEMA.DAT](#sistemadat)
- [REE.DAT](#reedat)
- [CONFHD.DAT](#confhddat)
- [HIDR.DAT](#hidrdat)
- [VAZOES.DAT](#vazoesdat)
- [EXPH.DAT](#exphdat)
- [EXPT.DAT](#exptdat)
- [MODIF.DAT](#modifdat)
- [C_ADIC.DAT](#c_adicdat)
- [ADTERM.DAT](#adtermdat)

---

## Estrutura do Documento

Para cada arquivo NEWAVE, este documento contém:

1. **Informações do Arquivo**
   - Nome e descrição
   - Estrutura e formato
   - Campos principais
   - Utilidade no modelo NEWAVE

2. **Propriedades da Biblioteca inewave**
   - Classe correspondente
   - Propriedades disponíveis
   - Métodos de acesso
   - Exemplos de uso

3. **Mapeamento de Campos**
   - Relação entre campos do arquivo e propriedades da biblioteca
   - Tipos de dados
   - Validações

---

## Arquivos Documentados

Os arquivos serão documentados conforme recebidos. Lista inicial:

- [x] CASO (caso.dat)
- [x] MANUTT (manutt.dat)
- [x] CLAST (clast.dat)
- [x] AGRINT (agrint.dat)
- [x] CVAR (cvar.dat)
- [x] SISTEMA (sistema.dat)
- [x] REE (ree.dat)
- [x] CONFHD (confhd.dat)
- [x] HIDR (hidr.dat)
- [x] VAZOES (vazoes.dat)
- [x] EXPH (exph.dat)
- [x] EXPT (expt.dat)
- [x] MODIF (modif.dat)
- [x] CADIC (C_adic.dat)
- [x] ADTERM (adterm.dat)

---

## CASO.DAT

### 1. Informações do Arquivo

#### 1.1. Nome e Descrição

- **Nome do arquivo**: `caso.dat` ou `CASO.DAT`
- **Tipo**: Arquivo de entrada obrigatório e permanente
- **Função**: Identificador e mapeador dos outros arquivos de dados utilizados na execução do modelo NEWAVE

#### 1.2. Função e Conteúdo Principal

O `CASO.DAT` **não contém dados do modelo** (como demanda ou características de usinas), mas sim a **relação dos nomes dos arquivos** que o programa NEWAVE deve ler para configurar o estudo. Ele é o **primeiro ponto de referência** para a entrada de dados do sistema NEWAVE.

O arquivo é composto por **dois registros** que fornecem informações essenciais para a inicialização e, se aplicável, para a execução paralela do programa.

#### 1.3. Estrutura e Formato

| Registro | Colunas | Formato | Descrição |
| :--- | :--- | :--- | :--- |
| **1** | 1 a 12 | A12 | **Nome do arquivo com a relação de arquivos a serem utilizados** (o arquivo índice real, geralmente chamado `arquivos.dat` ou `arquivos.nwd`) |
| **2** | 1 a 110 | A110 | **Caminho (diretório) onde se encontra o gerenciador de processos** |

**Formato de entrada**: Formato fixo
- Registro 1: até 12 caracteres alfanuméricos (`A12`)
- Registro 2: até 110 caracteres alfanuméricos (`A110`)

#### 1.4. Detalhes Estruturais e de Execução

**Conteúdo do Registro 1:**
- O Registro 1 aponta para outro arquivo, como o `arquivos.dat` ou `arquivos.nwd`
- Este arquivo, por sua vez, lista os nomes e caminhos de todos os *decks* de dados (e.g., `dger.dat`, `sistema.dat`, `confhd.dat`)

**Conteúdo do Registro 2 (Gerenciador de Processos):**
- Este registro é **obrigatório** quando o programa NEWAVE é executado em ambiente **multiprocessado** (processamento paralelo)
- Deve conter o caminho completo para o gerenciador de processos, cujo nome é `gerenciamento_PLsXXXX` (onde XXXX é o número da versão)
- É crucial que o último caractere do caminho seja uma barra invertida ("/")

**Módulos Auxiliares:**
- Módulos auxiliares como o **NEWDESP** e **NWLISTCF** também utilizam o `CASO.DAT` para obter o nome do arquivo que lista os dados de entrada que serão usados por eles (Registro 1)

#### 1.5. Contexto no Fluxo de Trabalho

O `CASO.DAT` é essencial para iniciar qualquer estudo, pois ele é o **ponto de partida** para a leitura de todas as classes de dados necessárias para o cálculo da política de operação de longo e médio prazos do NEWAVE. A partir do nome do arquivo fornecido no Registro 1 (por exemplo, `arquivos.dat`), o programa consegue localizar todos os demais dados (dados gerais, parâmetros do modelo estocástico, dados dos REEs, etc.).

---

### 2. Propriedades da Biblioteca inewave

#### 2.1. Classe Correspondente

**Classe**: `Caso`

```python
class Caso(data=<cfinterface.data.sectiondata.SectionData object>)
```

**Descrição**: Armazena os dados de entrada do NEWAVE referentes ao caso de estudo.

Esta classe lida com informações de entrada fornecidas ao NEWAVE e que podem ser modificadas através do arquivo `caso.dat`.

#### 2.2. Propriedades Disponíveis

##### `property` **arquivos**: `str | None`

- **Descrição**: Caminho para o arquivo `arquivos.dat` de entrada do NEWAVE
- **Tipo de retorno**: `str | None`
- **Mapeamento**: Corresponde ao **Registro 1** do arquivo `caso.dat`
- **Uso**: Contém o nome do arquivo que lista todos os arquivos de dados do estudo (geralmente `arquivos.dat` ou `arquivos.nwd`)

##### `property` **gerenciador_processos**: `str | None`

- **Descrição**: Caminho para o gerenciador de processos do NEWAVE
- **Tipo de retorno**: `str | None`
- **Mapeamento**: Corresponde ao **Registro 2** do arquivo `caso.dat`
- **Uso**: Contém o caminho completo para o gerenciador de processos (obrigatório em execuções multiprocessadas)
- **Observação**: O caminho deve terminar com barra invertida ("/")

---

### 3. Mapeamento de Campos

| Campo do Arquivo | Registro | Colunas | Formato | Propriedade inewave | Tipo Python |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Nome do arquivo índice | 1 | 1-12 | A12 | `arquivos` | `str \| None` |
| Caminho do gerenciador | 2 | 1-110 | A110 | `gerenciador_processos` | `str \| None` |

---

### 4. Exemplos de Uso

#### 4.1. Leitura do Arquivo

```python
from inewave.newave import Caso

# Ler o arquivo caso.dat
caso = Caso.read("caso.dat")

# Acessar o nome do arquivo índice
arquivo_indice = caso.arquivos
print(f"Arquivo índice: {arquivo_indice}")

# Acessar o caminho do gerenciador de processos
caminho_gerenciador = caso.gerenciador_processos
print(f"Gerenciador: {caminho_gerenciador}")
```

#### 4.2. Modificação do Arquivo

```python
from inewave.newave import Caso

# Ler o arquivo
caso = Caso.read("caso.dat")

# Modificar o arquivo índice
caso.arquivos = "arquivos.nwd"

# Modificar o caminho do gerenciador
caso.gerenciador_processos = "/caminho/para/gerenciamento_PLs3000/"

# Salvar as alterações
caso.write("caso.dat")
```

#### 4.3. Validação

```python
from inewave.newave import Caso

caso = Caso.read("caso.dat")

# Verificar se o arquivo índice foi definido
if caso.arquivos:
    print(f"✅ Arquivo índice definido: {caso.arquivos}")
else:
    print("⚠️ Arquivo índice não definido")

# Verificar se o gerenciador foi definido (necessário para multiprocessamento)
if caso.gerenciador_processos:
    print(f"✅ Gerenciador definido: {caso.gerenciador_processos}")
    # Verificar se termina com barra
    if not caso.gerenciador_processos.endswith("/"):
        print("⚠️ AVISO: Caminho do gerenciador deve terminar com '/'")
else:
    print("ℹ️ Gerenciador não definido (não necessário para execução sequencial)")
```

---

### 5. Observações Importantes

1. **Obrigatoriedade**: O arquivo `caso.dat` é **obrigatório** para qualquer execução do NEWAVE
2. **Primeiro arquivo**: É o primeiro arquivo lido pelo programa, servindo como ponto de entrada
3. **Registro 2**: O Registro 2 (gerenciador de processos) é obrigatório apenas em ambientes multiprocessados
4. **Formato do caminho**: O caminho do gerenciador deve terminar com barra invertida ("/")
5. **Módulos auxiliares**: Módulos como NEWDESP e NWLISTCF também dependem deste arquivo

---

## MANUTT.DAT

### 1. Informações do Arquivo

#### 1.1. Nome e Descrição

- **Nome do arquivo**: `manutt.dat` ou `MANUTT.DAT`
- **Tipo**: Arquivo de entrada do modelo NEWAVE
- **Função**: Contém os dados de **manutenções programadas** para as unidades de **geração térmica**

#### 1.2. Conteúdo e Propósito

**Função Principal:**
- Informar as manutenções programadas nas unidades de geração térmica
- Considerado apenas para o **primeiro e segundo anos do período de planejamento**

**Influência no Modelo:**
- A informação contida no **33º registro do arquivo de dados gerais (`dger.dat`)** determina quantos anos de informações de manutenção programada serão levados em conta a partir do `MANUTT.DAT`

**Formato do Arquivo:**
- O arquivo inicia-se com um **conjunto de dois registros** (linhas) de existência obrigatória, cujo objetivo é orientar o usuário no preenchimento dos dados
- Segue o padrão adotado para arquivos de manutenções programadas

#### 1.3. Estrutura Detalhada dos Registros

Cada linha no `MANUTT.DAT` é um registro que detalha uma manutenção específica. Ele é composto por **13 campos**, dos quais apenas **6 são lidos pelo programa**. O formato de leitura desses 6 campos é de **formato fixo**.

| Campo | Colunas | Formato | Descrição |
| :--- | :--- | :--- | :--- |
| **1** | 18 a 20 | I3 | **Número da usina térmica** |
| **2, 3 e 4** | 41 a 48 | 2I2, I4 | **Data de início da manutenção (ddmmaaaa)**. A data deve pertencer ao primeiro ou ao segundo ano do planejamento |
| **5** | 50 a 52 | I3 | **Duração da manutenção, em dias** |
| **6** | 56 a 62 | F7.2 | **Potência da unidade em manutenção (MW)** |

**Campos lidos pelo programa:**
1. **Número da usina térmica** (I3, colunas 18-20)
2. **Dia de início** (I2, colunas 41-42)
3. **Mês de início** (I2, colunas 43-44)
4. **Ano de início** (I4, colunas 45-48)
5. **Duração em dias** (I3, colunas 50-52)
6. **Potência em manutenção** (F7.2, colunas 56-62)

**Observações:**
- Os campos 7-13 não são lidos pelo programa NEWAVE
- A data de início deve estar no formato ddmmaaaa
- A data deve pertencer ao primeiro ou segundo ano do período de planejamento

---

### 2. Propriedades da Biblioteca inewave

#### 2.1. Classe Correspondente

**Classe**: `Manutt`

```python
class Manutt(data=<cfinterface.data.sectiondata.SectionData object>)
```

**Descrição**: Armazena os dados de entrada do NEWAVE referentes à programação da manutenção das usinas térmicas.

#### 2.2. Propriedades Disponíveis

##### `property` **manutencoes**: `pd.DataFrame | None`

- **Descrição**: Tabela com as manutenções por usinas
- **Tipo de retorno**: `pd.DataFrame | None`
- **Colunas do DataFrame**:
  - `codigo_empresa` (`int`): Código da empresa
  - `nome_empresa` (`str`): Nome da empresa
  - `codigo_usina` (`int`): Código da usina térmica
  - `nome_usina` (`str`): Nome da usina térmica
  - `codigo_unidade` (`int`): Código da unidade
  - `data_inicio` (`datetime`): Data de início da manutenção (convertido de ddmmaaaa para objeto datetime)
  - `duracao` (`int`): Duração da manutenção em dias
  - `potencia` (`float`): Potência da unidade em manutenção (MW)

**Observações:**
- A propriedade retorna um DataFrame do pandas, facilitando consultas e filtragens
- O campo `data_inicio` é automaticamente convertido de string (ddmmaaaa) para objeto `datetime` do Python
- Se o arquivo não existir ou estiver vazio, a propriedade retorna `None`

---

### 3. Mapeamento de Campos

| Campo do Arquivo | Colunas | Formato | Propriedade DataFrame | Tipo Python | Descrição |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Número da usina | 18-20 | I3 | `codigo_usina` | `int` | Código numérico da usina térmica |
| Dia de início | 41-42 | I2 | (parte de `data_inicio`) | `datetime.day` | Dia da data de início |
| Mês de início | 43-44 | I2 | (parte de `data_inicio`) | `datetime.month` | Mês da data de início |
| Ano de início | 45-48 | I4 | (parte de `data_inicio`) | `datetime.year` | Ano da data de início |
| Duração | 50-52 | I3 | `duracao` | `int` | Duração em dias |
| Potência | 56-62 | F7.2 | `potencia` | `float` | Potência em MW |

**Observações sobre o mapeamento:**
- Os campos de data (dia, mês, ano) são combinados em um único campo `data_inicio` do tipo `datetime`
- A biblioteca inewave adiciona campos auxiliares (`codigo_empresa`, `nome_empresa`, `nome_usina`, `codigo_unidade`) que podem ser obtidos de outros arquivos do NEWAVE ou definidos durante a leitura
- O campo `codigo_usina` corresponde ao "Número da usina térmica" do arquivo original

---

### 4. Exemplos de Uso

#### 4.1. Leitura do Arquivo

```python
from inewave.newave import Manutt

# Ler o arquivo manutt.dat
manutt = Manutt.read("manutt.dat")

# Acessar a tabela de manutenções
df_manutencoes = manutt.manutencoes

if df_manutencoes is not None:
    print(f"Total de manutenções: {len(df_manutencoes)}")
    print(df_manutencoes.head())
else:
    print("Nenhuma manutenção encontrada ou arquivo vazio")
```

#### 4.2. Consulta por Usina

```python
from inewave.newave import Manutt

manutt = Manutt.read("manutt.dat")

if manutt.manutencoes is not None:
    # Filtrar manutenções de uma usina específica
    codigo_usina = 123
    manutencoes_usina = manutt.manutencoes[
        manutt.manutencoes['codigo_usina'] == codigo_usina
    ]
    
    print(f"Manutenções da usina {codigo_usina}:")
    print(manutencoes_usina)
```

#### 4.3. Consulta por Nome de Usina

```python
from inewave.newave import Manutt

manutt = Manutt.read("manutt.dat")

if manutt.manutencoes is not None:
    # Filtrar por nome da usina (busca parcial, case-insensitive)
    nome_procurado = "Angra"
    manutencoes_filtradas = manutt.manutencoes[
        manutt.manutencoes['nome_usina'].str.contains(nome_procurado, case=False, na=False)
    ]
    
    print(f"Manutenções encontradas para '{nome_procurado}':")
    print(manutencoes_filtradas[['nome_usina', 'data_inicio', 'duracao', 'potencia']])
```

#### 4.4. Consulta por Período

```python
from inewave.newave import Manutt
from datetime import datetime

manutt = Manutt.read("manutt.dat")

if manutt.manutencoes is not None:
    # Filtrar manutenções em um período específico
    data_inicio_periodo = datetime(2024, 1, 1)
    data_fim_periodo = datetime(2024, 12, 31)
    
    manutencoes_periodo = manutt.manutencoes[
        (manutt.manutencoes['data_inicio'] >= data_inicio_periodo) &
        (manutt.manutencoes['data_inicio'] <= data_fim_periodo)
    ]
    
    print(f"Manutenções no período {data_inicio_periodo.date()} a {data_fim_periodo.date()}:")
    print(manutencoes_periodo)
```

#### 4.5. Análise de Potência Total em Manutenção

```python
from inewave.newave import Manutt

manutt = Manutt.read("manutt.dat")

if manutt.manutencoes is not None:
    # Calcular potência total em manutenção
    potencia_total = manutt.manutencoes['potencia'].sum()
    
    # Agrupar por usina
    potencia_por_usina = manutt.manutencoes.groupby('nome_usina')['potencia'].sum()
    
    print(f"Potência total em manutenção: {potencia_total:.2f} MW")
    print("\nPotência por usina:")
    print(potencia_por_usina)
```

#### 4.6. Modificação e Gravação

```python
from inewave.newave import Manutt
from datetime import datetime

# Ler o arquivo
manutt = Manutt.read("manutt.dat")

if manutt.manutencoes is not None:
    # Adicionar nova manutenção (exemplo)
    nova_manutencao = {
        'codigo_empresa': 1,
        'nome_empresa': 'Empresa Exemplo',
        'codigo_usina': 123,
        'nome_usina': 'Usina Exemplo',
        'codigo_unidade': 1,
        'data_inicio': datetime(2025, 3, 15),
        'duracao': 30,
        'potencia': 150.0
    }
    
    # Adicionar ao DataFrame
    import pandas as pd
    novo_df = pd.concat([
        manutt.manutencoes,
        pd.DataFrame([nova_manutencao])
    ], ignore_index=True)
    
    # Atualizar a propriedade (se a biblioteca permitir)
    # Nota: Dependendo da implementação da biblioteca, pode ser necessário
    # usar métodos específicos para modificar os dados
    
    # Salvar alterações
    manutt.write("manutt.dat")
```

#### 4.7. Validação de Dados

```python
from inewave.newave import Manutt

manutt = Manutt.read("manutt.dat")

if manutt.manutencoes is not None:
    df = manutt.manutencoes
    
    # Verificar se há dados
    if len(df) == 0:
        print("⚠️ Nenhuma manutenção encontrada no arquivo")
    
    # Verificar campos obrigatórios
    campos_obrigatorios = ['codigo_usina', 'data_inicio', 'duracao', 'potencia']
    campos_faltando = [campo for campo in campos_obrigatorios if campo not in df.columns]
    
    if campos_faltando:
        print(f"⚠️ Campos faltando: {campos_faltando}")
    
    # Verificar valores nulos
    nulos = df[campos_obrigatorios].isnull().sum()
    if nulos.any():
        print("⚠️ Valores nulos encontrados:")
        print(nulos[nulos > 0])
    
    # Verificar duração positiva
    duracao_negativa = df[df['duracao'] <= 0]
    if len(duracao_negativa) > 0:
        print(f"⚠️ {len(duracao_negativa)} manutenções com duração inválida")
    
    # Verificar potência positiva
    potencia_negativa = df[df['potencia'] < 0]
    if len(potencia_negativa) > 0:
        print(f"⚠️ {len(potencia_negativa)} manutenções com potência negativa")
```

---

### 5. Observações Importantes

1. **Período de aplicação**: O arquivo contém manutenções apenas para o **primeiro e segundo anos** do período de planejamento

2. **Dependência do DGER**: O número de anos de manutenção considerados é definido no **33º registro do arquivo `dger.dat`**

3. **Formato de data**: A data de início deve estar no formato **ddmmaaaa** no arquivo original, mas é convertida para objeto `datetime` na biblioteca inewave

4. **Campos não lidos**: Apenas 6 dos 13 campos são lidos pelo programa NEWAVE; os campos 7-13 são ignorados

5. **Validação**: É recomendado validar que:
   - A data de início pertence ao primeiro ou segundo ano do planejamento
   - A duração é um número positivo
   - A potência é um número não negativo
   - O código da usina existe no cadastro de usinas térmicas

6. **DataFrame pandas**: A propriedade `manutencoes` retorna um DataFrame do pandas, permitindo uso de todas as funcionalidades do pandas para análise, filtragem e manipulação dos dados

7. **Campos auxiliares**: A biblioteca inewave pode adicionar campos auxiliares (como `nome_usina`) que não estão diretamente no arquivo, mas são obtidos de outros arquivos do NEWAVE ou metadados

---

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

## REE.DAT

### 1. Informações do Arquivo

#### 1.1. Nome e Descrição

- **Nome do arquivo**: `ree.dat` ou `REE.DAT`
- **Tipo**: Arquivo de entrada fundamental do modelo NEWAVE
- **Função**: Define a agregação das usinas hidrelétricas em Reservatórios Equivalentes de Energia (REEs) e estabelece o ponto no tempo onde o sistema passa da representação individualizada para a agregada (híbrida)

#### 1.2. Função e Contexto no Modelo

O NEWAVE representa o parque hidrelétrico de forma agregada em REEs para o cálculo da política de operação, utilizando a **Programação Dinâmica Dual Estocástica (PDDE)**.

**Principais funções do arquivo:**

1. **Associação de Usinas:** No arquivo de Configuração Hidrelétrica (`CONFHD.DAT`), cada usina é associada a um REE

2. **Agregação:** Definir os REEs e o momento (mês e ano) em que as usinas que o compõem deixam de ser representadas individualmente e passam a ser representadas pelo REE (modelagem híbrida)

3. **Representação Híbrida/Agregada:** O modelo NEWAVE permite que o parque hidrelétrico seja representado de forma:
   - **Agregada**: Todas as usinas representadas pelo REE
   - **Individualizada**: Cada usina representada individualmente
   - **Híbrida**: Individualizada nos primeiros anos e agregada nos demais

O `REE.DAT` é crucial para configurar a **data de transição** na modelagem híbrida.

**Acoplamento Hidráulico:**
O NEWAVE suporta a representação de usinas de uma mesma bacia hidrográfica que pertencem a REEs diferentes, que, por sua vez, podem estar associados a subsistemas/submercados distintos. Quando isso ocorre, forma-se um **acoplamento hidráulico** entre REEs.

#### 1.3. Estrutura do Arquivo

O arquivo é dividido em **dois blocos de dados**, ambos precedidos por **três registros de comentários obrigatórios**, que servem para orientação do usuário, mas são ignorados pelo programa.

#### 1.4. Bloco 1: Definição e Data de Agregação

Este bloco contém um registro para cada REE considerado.

| Campo | Colunas | Formato | Descrição |
| :--- | :--- | :--- | :--- |
| **1** | 2 a 4 | I3 | **Número do REE** |
| **2** | 6 a 15 | A10 | **Nome do REE** |
| **3** | 19 a 21 | I3 | **Número do subsistema/submercado** ao qual o REE está associado |
| **4** | 24 a 25 | I2 | **Mês** a partir do qual as usinas do REE **deixam de ser representadas individualmente** (data de agregação) |
| **5** | 27 a 30 | I4 | **Ano** a partir do qual as usinas do REE **deixam de ser representadas individualmente** (data de agregação) |

**Regras da Data de Agregação:**

1. O código **`999`** no campo 1 indica o final do bloco

2. Em casos com configuração hidrelétrica individualizada, a data de agregação (Campos 4 e 5) pode ser qualquer mês no período de planejamento

3. Para os períodos **pré e pós-estudo**, é permitido informar **somente o primeiro mês**; se um mês diferente do primeiro for escolhido, o NEWAVE assume que o respectivo período será agregado a partir do primeiro mês

**Observações:**
- A data de agregação define quando a representação muda de individualizada para agregada
- Antes da data de agregação, as usinas são representadas individualmente
- A partir da data de agregação, as usinas são representadas pelo REE agregado

#### 1.5. Bloco 2: Remoção de Usinas Fictícias

Este bloco contém um único registro com um *flag* que determina o tratamento de usinas fictícias em períodos individualizados.

| Campo | Colunas | Formato | Descrição |
| :--- | :--- | :--- | :--- |
| **1** | 22 a 25 | I4 | **Flag para remoção de usinas fictícias** nos períodos individualizados |
| | | **0** | Remove as usinas fictícias |
| | | **1** | Mantém as usinas fictícias |

**Observações:**
- Este flag afeta apenas os períodos onde as usinas são representadas individualmente
- Usinas fictícias são usadas para modelar restrições e acoplamentos hidráulicos
- A remoção ou manutenção de fictícias pode afetar a representação do sistema

#### 1.6. Relatório de Acompanhamento

O relatório de acompanhamento do programa (`PMO.DAT`) inclui um **relatório dos dados dos REEs**, facilitando a validação e o acompanhamento da configuração.

---

### 2. Propriedades da Biblioteca inewave

#### 2.1. Classe Correspondente

**Classe**: `Ree`

```python
class Ree(data=<cfinterface.data.sectiondata.SectionData object>)
```

**Descrição**: Armazena os dados de entrada do NEWAVE referentes às configurações dos REEs (Reservatórios Equivalentes de Energia).

#### 2.2. Propriedades Disponíveis

##### `property` **rees**: `pd.DataFrame | None`

- **Descrição**: Tabela com os REEs e os submercados
- **Tipo de retorno**: `pd.DataFrame | None`
- **Corresponde a**: Bloco 1 do arquivo (Definição e Data de Agregação)
- **Colunas do DataFrame**:
  - `codigo` (`int`): Número do REE (corresponde ao campo 1 do Bloco 1)
  - `nome` (`str`): Nome do REE (corresponde ao campo 2 do Bloco 1)
  - `submercado` (`int`): Número do subsistema/submercado ao qual o REE está associado (corresponde ao campo 3 do Bloco 1)
  - `mes_fim_individualizado` (`int`): Mês a partir do qual as usinas deixam de ser representadas individualmente (corresponde ao campo 4 do Bloco 1)
  - `ano_fim_individualizado` (`int`): Ano a partir do qual as usinas deixam de ser representadas individualmente (corresponde ao campo 5 do Bloco 1)

**Observações:**
- Cada linha representa um REE cadastrado no sistema
- Os campos `mes_fim_individualizado` e `ano_fim_individualizado` definem a data de agregação
- Se a data de agregação não for definida (valores nulos ou zero), o REE pode ser usado apenas de forma agregada
- Se o arquivo não existir ou estiver vazio, a propriedade retorna `None`

##### `property` **remocao_ficticias**: `int | None`

- **Descrição**: Opção de remover usinas fictícias nos períodos individualizados
- **Tipo de retorno**: `int | None`
- **Corresponde a**: Bloco 2 do arquivo (Remoção de Usinas Fictícias)
- **Valores possíveis**:
  - `0`: Remove as usinas fictícias nos períodos individualizados
  - `1`: Mantém as usinas fictícias nos períodos individualizados

**Observações:**
- Este flag afeta apenas os períodos onde as usinas são representadas individualmente
- Se o arquivo não contiver o Bloco 2 ou estiver vazio, a propriedade retorna `None`
- O valor padrão pode variar dependendo da configuração do estudo

---

### 3. Mapeamento de Campos

#### 3.1. Bloco 1 → Propriedade `rees`

| Campo do Arquivo | Colunas | Formato | Coluna DataFrame | Tipo Python | Descrição |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Número do REE | 2-4 | I3 | `codigo` | `int` | Identificador do REE |
| Nome do REE | 6-15 | A10 | `nome` | `str` | Nome do REE |
| Número do subsistema | 19-21 | I3 | `submercado` | `int` | Subsistema/submercado associado |
| Mês de agregação | 24-25 | I2 | `mes_fim_individualizado` | `int` | Mês de fim da individualização |
| Ano de agregação | 27-30 | I4 | `ano_fim_individualizado` | `int` | Ano de fim da individualização |

#### 3.2. Bloco 2 → Propriedade `remocao_ficticias`

| Campo do Arquivo | Colunas | Formato | Propriedade | Tipo Python | Descrição |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Flag de remoção | 22-25 | I4 | `remocao_ficticias` | `int` | 0 = Remove, 1 = Mantém |

---

### 4. Exemplos de Uso

#### 4.1. Leitura do Arquivo

```python
from inewave.newave import Ree

# Ler o arquivo ree.dat
ree = Ree.read("ree.dat")

# Acessar a tabela de REEs
df_rees = ree.rees

if df_rees is not None:
    print(f"Total de REEs cadastrados: {len(df_rees)}")
    print(df_rees.head())
else:
    print("Nenhum REE encontrado ou arquivo vazio")
```

#### 4.2. Consulta de REEs por Subsistema

```python
from inewave.newave import Ree

ree = Ree.read("ree.dat")

if ree.rees is not None:
    # Filtrar REEs de um subsistema específico
    codigo_submercado = 1
    rees_submercado = ree.rees[ree.rees['submercado'] == codigo_submercado]
    
    print(f"REEs do subsistema {codigo_submercado}:")
    print(rees_submercado[['codigo', 'nome', 'mes_fim_individualizado', 'ano_fim_individualizado']])
```

#### 4.3. Consulta de REEs Individualizados

```python
from inewave.newave import Ree

ree = Ree.read("ree.dat")

if ree.rees is not None:
    # Filtrar REEs com período de individualização definido
    rees_individualizados = ree.rees[
        (ree.rees['mes_fim_individualizado'].notna()) &
        (ree.rees['ano_fim_individualizado'].notna()) &
        (ree.rees['mes_fim_individualizado'] > 0) &
        (ree.rees['ano_fim_individualizado'] > 0)
    ]
    
    print(f"REEs com individualização: {len(rees_individualizados)}")
    print("\nREEs individualizados:")
    print(rees_individualizados[['codigo', 'nome', 'mes_fim_individualizado', 'ano_fim_individualizado']])
```

#### 4.4. Análise de Datas de Agregação

```python
from inewave.newave import Ree

ree = Ree.read("ree.dat")

if ree.rees is not None:
    # Criar coluna de data de agregação
    df_rees = ree.rees.copy()
    df_rees['data_agregacao'] = (
        df_rees['ano_fim_individualizado'].astype(str) + '-' +
        df_rees['mes_fim_individualizado'].astype(str).str.zfill(2)
    )
    
    # Agrupar por data de agregação
    rees_por_data = df_rees.groupby('data_agregacao')['codigo'].count()
    
    print("Quantidade de REEs por data de agregação:")
    print(rees_por_data)
```

#### 4.5. Consulta de Flag de Remoção de Fictícias

```python
from inewave.newave import Ree

ree = Ree.read("ree.dat")

# Verificar configuração de remoção de fictícias
remocao_ficticias = ree.remocao_ficticias

if remocao_ficticias is not None:
    print(f"Flag de remoção de usinas fictícias: {remocao_ficticias}")
    
    opcoes_remocao = {
        0: "Remove as usinas fictícias nos períodos individualizados",
        1: "Mantém as usinas fictícias nos períodos individualizados"
    }
    
    descricao = opcoes_remocao.get(remocao_ficticias, "Opção desconhecida")
    print(f"Significado: {descricao}")
else:
    print("Flag de remoção de fictícias não definido")
```

#### 4.6. Consulta de REE Específico

```python
from inewave.newave import Ree

ree = Ree.read("ree.dat")

if ree.rees is not None:
    # Consultar um REE específico
    codigo_ree = 1
    ree_especifico = ree.rees[ree.rees['codigo'] == codigo_ree]
    
    if not ree_especifico.empty:
        r = ree_especifico.iloc[0]
        print(f"REE {codigo_ree}: {r['nome']}")
        print(f"  Subsistema: {r['submercado']}")
        
        if not pd.isna(r['mes_fim_individualizado']) and not pd.isna(r['ano_fim_individualizado']):
            print(f"  Data de agregação: {int(r['mes_fim_individualizado']):02d}/{int(r['ano_fim_individualizado'])}")
            print(f"  Representação: Individualizada até {int(r['mes_fim_individualizado']):02d}/{int(r['ano_fim_individualizado'])}, depois agregada")
        else:
            print("  Representação: Agregada desde o início")
    else:
        print(f"REE {codigo_ree} não encontrado")
```

#### 4.7. Análise de REEs por Subsistema

```python
from inewave.newave import Ree

ree = Ree.read("ree.dat")

if ree.rees is not None:
    # Contar REEs por subsistema
    rees_por_submercado = ree.rees.groupby('submercado')['codigo'].count()
    
    print("Quantidade de REEs por subsistema:")
    print(rees_por_submercado)
    
    # Listar REEs por subsistema
    print("\nREEs por subsistema:")
    for submercado in ree.rees['submercado'].unique():
        rees_sub = ree.rees[ree.rees['submercado'] == submercado]
        print(f"\nSubsistema {submercado}:")
        print(rees_sub[['codigo', 'nome']].to_string(index=False))
```

#### 4.8. Validação de Dados

```python
from inewave.newave import Ree
import pandas as pd

ree = Ree.read("ree.dat")

# Validar REEs
if ree.rees is not None:
    df_rees = ree.rees
    
    # Verificar se há dados
    if len(df_rees) == 0:
        print("⚠️ Nenhum REE encontrado no arquivo")
    
    # Verificar campos obrigatórios
    campos_obrigatorios = ['codigo', 'nome', 'submercado']
    campos_faltando = [campo for campo in campos_obrigatorios if campo not in df_rees.columns]
    
    if campos_faltando:
        print(f"⚠️ Campos faltando: {campos_faltando}")
    
    # Verificar códigos duplicados
    duplicatas = df_rees[df_rees.duplicated(subset=['codigo'], keep=False)]
    if len(duplicatas) > 0:
        print(f"⚠️ {len(duplicatas)} REEs com códigos duplicados encontrados")
    
    # Verificar datas de agregação válidas
    rees_com_data = df_rees[
        (df_rees['mes_fim_individualizado'].notna()) &
        (df_rees['ano_fim_individualizado'].notna())
    ]
    
    # Verificar meses válidos (1-12)
    meses_invalidos = rees_com_data[
        (rees_com_data['mes_fim_individualizado'] < 1) |
        (rees_com_data['mes_fim_individualizado'] > 12)
    ]
    
    if len(meses_invalidos) > 0:
        print(f"⚠️ {len(meses_invalidos)} REEs com mês de agregação inválido (deve ser 1-12)")
    
    # Verificar anos válidos
    anos_invalidos = rees_com_data[rees_com_data['ano_fim_individualizado'] < 1900]
    if len(anos_invalidos) > 0:
        print(f"⚠️ {len(anos_invalidos)} REEs com ano de agregação inválido")

# Validar flag de remoção de fictícias
if ree.remocao_ficticias is not None:
    if ree.remocao_ficticias not in [0, 1]:
        print(f"⚠️ Flag de remoção de fictícias com valor inválido: {ree.remocao_ficticias} (deve ser 0 ou 1)")
```

#### 4.9. Modificação e Gravação

```python
from inewave.newave import Ree

# Ler o arquivo
ree = Ree.read("ree.dat")

if ree.rees is not None:
    # Modificar data de agregação de um REE específico
    codigo_ree = 1
    novo_mes = 6
    novo_ano = 2025
    
    mask = ree.rees['codigo'] == codigo_ree
    
    if mask.any():
        ree.rees.loc[mask, 'mes_fim_individualizado'] = novo_mes
        ree.rees.loc[mask, 'ano_fim_individualizado'] = novo_ano
        print(f"Data de agregação do REE {codigo_ree} atualizada para {novo_mes:02d}/{novo_ano}")
    
    # Modificar flag de remoção de fictícias
    ree.remocao_ficticias = 1  # Mantém fictícias
    print("Flag de remoção de fictícias atualizado para 1 (mantém)")
    
    # Salvar alterações
    ree.write("ree.dat")
```

#### 4.10. Análise de Modelagem Híbrida

```python
from inewave.newave import Ree
from datetime import datetime

ree = Ree.read("ree.dat")

if ree.rees is not None:
    # Identificar REEs com modelagem híbrida
    rees_hibridos = ree.rees[
        (ree.rees['mes_fim_individualizado'].notna()) &
        (ree.rees['ano_fim_individualizado'].notna()) &
        (ree.rees['mes_fim_individualizado'] > 0) &
        (ree.rees['ano_fim_individualizado'] > 0)
    ]
    
    print(f"REEs com modelagem híbrida: {len(rees_hibridos)}")
    
    # Identificar REEs totalmente agregados
    rees_agregados = ree.rees[
        (ree.rees['mes_fim_individualizado'].isna()) |
        (ree.rees['ano_fim_individualizado'].isna()) |
        (ree.rees['mes_fim_individualizado'] == 0) |
        (ree.rees['ano_fim_individualizado'] == 0)
    ]
    
    print(f"REEs totalmente agregados: {len(rees_agregados)}")
    
    # Análise temporal: quando ocorrem as agregações
    if len(rees_hibridos) > 0:
        rees_hibridos_copy = rees_hibridos.copy()
        rees_hibridos_copy['data_agregacao'] = pd.to_datetime(
            rees_hibridos_copy['ano_fim_individualizado'].astype(str) + '-' +
            rees_hibridos_copy['mes_fim_individualizado'].astype(str).str.zfill(2) + '-01'
        )
        
        agrupamento_por_data = rees_hibridos_copy.groupby('data_agregacao')['codigo'].count()
        
        print("\nQuantidade de REEs agregados por data:")
        print(agrupamento_por_data.sort_index())
```

---

### 5. Observações Importantes

1. **Associação com CONFHD**: Os REEs definidos neste arquivo devem estar consistentes com as associações de usinas a REEs definidas no arquivo `CONFHD.DAT`

2. **Data de agregação**: 
   - Define quando a representação muda de individualizada para agregada
   - Para períodos pré e pós-estudo, apenas o primeiro mês é permitido
   - Se um mês diferente for escolhido, o NEWAVE assume o primeiro mês

3. **Modelagem híbrida**: 
   - Permite representação individualizada nos primeiros anos e agregada nos demais
   - Útil para estudos que precisam de detalhamento inicial e agregação posterior

4. **Acoplamento hidráulico**: 
   - REEs diferentes podem ter usinas da mesma bacia hidrográfica
   - Isso forma acoplamento hidráulico entre REEs
   - Pode estar associado a subsistemas diferentes

5. **Remoção de fictícias**: 
   - O flag afeta apenas períodos individualizados
   - Usinas fictícias são usadas para modelar restrições e acoplamentos
   - A escolha de remover ou manter pode afetar a representação do sistema

6. **Subsistemas**: 
   - Cada REE está associado a um subsistema/submercado
   - Os subsistemas devem estar cadastrados no arquivo `SISTEMA.DAT`

7. **Relatório PMO**: 
   - O relatório de acompanhamento (`PMO.DAT`) inclui informações sobre os REEs
   - Facilita validação e acompanhamento da configuração

8. **Estrutura de dados**: 
   - A propriedade `rees` retorna um DataFrame do pandas
   - A propriedade `remocao_ficticias` retorna um inteiro (0 ou 1)

9. **Validação**: É importante validar:
   - Códigos de REE únicos
   - Datas de agregação válidas (mês 1-12, ano razoável)
   - Consistência com subsistemas cadastrados
   - Consistência com associações em CONFHD

10. **Dependências**: 
    - Os REEs referenciam subsistemas do arquivo `SISTEMA.DAT`
    - As usinas são associadas a REEs no arquivo `CONFHD.DAT`

11. **Comentários**: Os registros de comentário no início dos blocos são obrigatórios mas ignorados pelo programa

12. **DataFrame pandas**: A propriedade `rees` retorna um DataFrame do pandas, permitindo uso completo das funcionalidades do pandas para análise e manipulação

---

## CONFHD.DAT

### 1. Informações do Arquivo

#### 1.1. Nome e Descrição

- **Nome do arquivo**: `confhd.dat` ou `CONFHD.DAT`
- **Tipo**: Arquivo de entrada essencial do modelo NEWAVE
- **Função**: Listar e configurar todas as usinas hidrelétricas consideradas no estudo, associando cada usina a informações cadastrais e operacionais específicas

#### 1.2. Função e Conteúdo Principal

O `CONFHD.DAT` define a configuração do sistema hidrelétrico ao associar cada usina a:
- Informações cadastrais (código, nome, posto de vazões)
- Associação a REE (Reservatório Equivalente de Energia)
- Volume inicial armazenado
- Status da usina (existente, em expansão, não existente, não considerada)
- Configurações de modificação e histórico de vazões

**Estrutura:**
- O arquivo é composto por tantos registros quantas forem as usinas hidrelétricas na configuração do sistema em estudo
- O arquivo deve ser iniciado por **dois registros destinados a comentários**. Embora obrigatórios, esses registros são ignorados pelo programa e servem apenas para orientação do usuário

#### 1.3. Estrutura do Registro

Cada registro no `CONFHD.DAT` é composto por **11 campos**, dispostos em formato fixo:

| Campo | Colunas | Formato | Descrição |
| :--- | :--- | :--- | :--- |
| **1** | 2 a 5 | I4 | **Número da usina** (código no cadastro de usinas hidrelétricas) |
| **2** | 7 a 18 | A12 | **Nome da usina** |
| **3** | 20 a 23 | I4 | **Número do posto de vazões** da usina |
| **4** | 26 a 29 | I4 | **Número da usina a jusante** (código da usina no cadastro). O código é nulo se a usina não tiver aproveitamento a jusante, ou se o aproveitamento a jusante não estiver sendo considerado |
| **5** | 31 a 34 | I4 | **Número do REE** (Reservatório Equivalente de Energia) a que a usina pertence |
| **6** | 36 a 41 | F6.2 | **Volume armazenado inicial** em percentagem do volume útil. Este valor pode ser utilizado para o cálculo da energia armazenada inicial, dependendo da configuração no registro 22 do `dger.dat` |
| **7** | 45 a 46 | I4 | **Indicador de *status* da usina** (existente e/ou em expansão) |
| **8** | 50 a 53 | I4 | **Índice de modificação de dados da usina** |
| **9** | 59 a 62 | I4 | Primeiro ano do histórico de vazões, do posto correspondente à usina, considerado para **ajuste do modelo de energias afluentes** |
| **10** | 68 a 71 | I4 | Último ano do histórico de vazões, do posto correspondente à usina, considerado para **ajuste do modelo de energias afluentes** |
| **11** | 74 a 76 | I3 | **Tecnologia da usina** para efeito de cálculo de emissões de GEE |

#### 1.4. Detalhamento dos Campos

**Campo 7 - Indicador de Status:**
- **EX** = usina existente
- **EE** = usina existente, com expansão
- **NE** = não existente
- **NC** = não considerada (a usina não será incluída nos cálculos do estudo)

**Campo 8 - Índice de Modificação:**
- **0** = não modifica os dados do cadastro
- **1** = um conjunto restrito de dados do cadastro será modificado (usando, por exemplo, o arquivo `modif.dat`)

#### 1.5. Regras e Observações

**Status da Usina:**
- Se o campo 7 for preenchido como `EE` ou `NE`, o número de conjunto de máquinas e de máquinas da usina será, por *default*, preenchido com zero
- Se o status for `NC`, a usina é excluída dos cálculos do estudo
- Uma usina com volume morto preenchido é considerada existente

**Modificação de Dados:**
- O campo 8 (Índice de modificação) é usado para indicar se dados cadastrais serão alterados via arquivo como o `MODIF.DAT`

**Histórico de Vazões (Campos 9 e 10):**
- O preenchimento desses campos só é necessário se os dados diferirem do cadastro de postos fluviométricos (`postos.dat`)
- Se os campos 9 e/ou 10 forem zero ou não forem fornecidos, os valores serão lidos do cadastro de postos fluviométricos

**Tecnologia (Campo 11):**
- O preenchimento deste campo não é obrigatório
- Se for preenchido, a respectiva tecnologia deve estar declarada no arquivo de tecnologias (`tecno.dat`)

**Volume Inicial (Campo 6):**
- O valor informado neste campo é utilizado como o volume inicial, em percentual do volume útil, se o registro 22 do `dger.dat` estiver preenchido com `1`
- No caso de simulação final individualizada com política operativa híbrida, pode-se usar o volume inicial informado por REE no registro 23 do `dger.dat`; nesse caso, todas as usinas do REE terão o mesmo percentual de volume inicial, que deve ser compatível com o percentual do volume máximo

**Associação com REE:**
- O campo 5 associa cada usina a um REE, que deve estar cadastrado no arquivo `REE.DAT`
- Esta associação é fundamental para a modelagem agregada do sistema hidrelétrico

---

### 2. Propriedades da Biblioteca inewave

#### 2.1. Classe Correspondente

**Classe**: `Confhd`

```python
class Confhd(data=<cfinterface.data.sectiondata.SectionData object>)
```

**Descrição**: Armazena os dados de entrada do NEWAVE referentes às configurações das usinas hidrelétricas.

Esta classe lida com informações de entrada fornecidas ao NEWAVE e que podem ser modificadas através do arquivo `modif.dat`.

#### 2.2. Propriedades Disponíveis

##### `property` **usinas**: `pd.DataFrame | None`

- **Descrição**: Tabela com as usinas hidrelétricas
- **Tipo de retorno**: `pd.DataFrame | None`
- **Colunas do DataFrame**:
  - `codigo_usina` (`int`): Número da usina (código no cadastro) (corresponde ao campo 1)
  - `nome_usina` (`str`): Nome da usina (corresponde ao campo 2)
  - `posto` (`int`): Número do posto de vazões da usina (corresponde ao campo 3)
  - `codigo_usina_jusante` (`int`): Número da usina a jusante (corresponde ao campo 4). Pode ser nulo se não houver aproveitamento a jusante
  - `ree` (`int`): Número do REE (Reservatório Equivalente de Energia) a que a usina pertence (corresponde ao campo 5)
  - `volume_inicial_percentual` (`float`): Volume armazenado inicial em percentagem do volume útil (corresponde ao campo 6)
  - `usina_existente` (`str`): Indicador de status da usina (EX, EE, NE, NC) (corresponde ao campo 7)
  - `usina_modificada` (`int`): Índice de modificação de dados (0 ou 1) (corresponde ao campo 8)
  - `ano_inicio_historico` (`int`): Primeiro ano do histórico de vazões para ajuste do modelo (corresponde ao campo 9)
  - `ano_fim_historico` (`int`): Último ano do histórico de vazões para ajuste do modelo (corresponde ao campo 10)

**Observações:**
- Cada linha representa uma usina hidrelétrica cadastrada no sistema
- O campo `codigo_usina_jusante` pode ser nulo ou zero se não houver usina a jusante
- O campo `usina_existente` contém strings de 2 caracteres: "EX", "EE", "NE" ou "NC"
- Os campos `ano_inicio_historico` e `ano_fim_historico` podem ser zero se os valores devem ser lidos do cadastro de postos
- **Nota**: O campo 11 (Tecnologia) não está presente no DataFrame retornado pela biblioteca inewave na versão atual
- Se o arquivo não existir ou estiver vazio, a propriedade retorna `None`

---

### 3. Mapeamento de Campos

| Campo do Arquivo | Colunas | Formato | Coluna DataFrame | Tipo Python | Descrição |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Número da usina | 2-5 | I4 | `codigo_usina` | `int` | Código no cadastro |
| Nome da usina | 7-18 | A12 | `nome_usina` | `str` | Nome da usina |
| Posto de vazões | 20-23 | I4 | `posto` | `int` | Número do posto |
| Usina a jusante | 26-29 | I4 | `codigo_usina_jusante` | `int` | Código da usina a jusante (pode ser nulo) |
| Número do REE | 31-34 | I4 | `ree` | `int` | REE ao qual a usina pertence |
| Volume inicial | 36-41 | F6.2 | `volume_inicial_percentual` | `float` | Volume inicial (% do volume útil) |
| Status da usina | 45-46 | A2 | `usina_existente` | `str` | EX, EE, NE ou NC |
| Índice de modificação | 50-53 | I4 | `usina_modificada` | `int` | 0 ou 1 |
| Ano início histórico | 59-62 | I4 | `ano_inicio_historico` | `int` | Primeiro ano do histórico |
| Ano fim histórico | 68-71 | I4 | `ano_fim_historico` | `int` | Último ano do histórico |
| Tecnologia | 74-76 | I3 | *(não disponível)* | - | Tecnologia para cálculo de GEE |

**Observação**: O campo 11 (Tecnologia) não está mapeado na propriedade `usinas` da biblioteca inewave na versão atual.

---

### 4. Exemplos de Uso

#### 4.1. Leitura do Arquivo

```python
from inewave.newave import Confhd

# Ler o arquivo confhd.dat
confhd = Confhd.read("confhd.dat")

# Acessar a tabela de usinas
df_usinas = confhd.usinas

if df_usinas is not None:
    print(f"Total de usinas hidrelétricas: {len(df_usinas)}")
    print(df_usinas.head())
else:
    print("Nenhuma usina encontrada ou arquivo vazio")
```

#### 4.2. Consulta de Usinas por REE

```python
from inewave.newave import Confhd

confhd = Confhd.read("confhd.dat")

if confhd.usinas is not None:
    # Filtrar usinas de um REE específico
    codigo_ree = 1
    usinas_ree = confhd.usinas[confhd.usinas['ree'] == codigo_ree]
    
    print(f"Usinas do REE {codigo_ree}:")
    print(usinas_ree[['codigo_usina', 'nome_usina', 'posto', 'volume_inicial_percentual']])
```

#### 4.3. Consulta por Status da Usina

```python
from inewave.newave import Confhd

confhd = Confhd.read("confhd.dat")

if confhd.usinas is not None:
    # Filtrar usinas existentes
    usinas_existentes = confhd.usinas[confhd.usinas['usina_existente'] == 'EX']
    
    print(f"Usinas existentes: {len(usinas_existentes)}")
    
    # Filtrar usinas em expansão
    usinas_expansao = confhd.usinas[confhd.usinas['usina_existente'] == 'EE']
    
    print(f"Usinas em expansão: {len(usinas_expansao)}")
    
    # Filtrar usinas não consideradas
    usinas_nao_consideradas = confhd.usinas[confhd.usinas['usina_existente'] == 'NC']
    
    print(f"Usinas não consideradas: {len(usinas_nao_consideradas)}")
    
    # Distribuição por status
    distribuicao_status = confhd.usinas['usina_existente'].value_counts()
    print("\nDistribuição por status:")
    print(distribuicao_status)
```

#### 4.4. Consulta por Nome de Usina

```python
from inewave.newave import Confhd

confhd = Confhd.read("confhd.dat")

if confhd.usinas is not None:
    # Filtrar por nome da usina (busca parcial, case-insensitive)
    nome_procurado = "Itaipu"
    usinas_encontradas = confhd.usinas[
        confhd.usinas['nome_usina'].str.contains(nome_procurado, case=False, na=False)
    ]
    
    print(f"Usinas encontradas para '{nome_procurado}':")
    print(usinas_encontradas[['codigo_usina', 'nome_usina', 'ree', 'usina_existente']])
```

#### 4.5. Análise de Usinas por REE

```python
from inewave.newave import Confhd

confhd = Confhd.read("confhd.dat")

if confhd.usinas is not None:
    # Contar usinas por REE
    usinas_por_ree = confhd.usinas.groupby('ree').agg({
        'codigo_usina': 'count',
        'volume_inicial_percentual': 'mean'
    }).round(2)
    
    usinas_por_ree.columns = ['quantidade', 'volume_inicial_medio']
    
    print("Distribuição de usinas por REE:")
    print(usinas_por_ree)
    
    # Volume inicial médio por REE
    print("\nVolume inicial médio por REE:")
    print(usinas_por_ree['volume_inicial_medio'])
```

#### 4.6. Consulta de Usinas Modificadas

```python
from inewave.newave import Confhd

confhd = Confhd.read("confhd.dat")

if confhd.usinas is not None:
    # Filtrar usinas que serão modificadas
    usinas_modificadas = confhd.usinas[confhd.usinas['usina_modificada'] == 1]
    
    print(f"Usinas com modificações: {len(usinas_modificadas)}")
    print("\nUsinas modificadas:")
    print(usinas_modificadas[['codigo_usina', 'nome_usina', 'ree']])
    
    # Nota: As modificações específicas estarão no arquivo MODIF.DAT
```

#### 4.7. Análise de Cadeias Hidráulicas

```python
from inewave.newave import Confhd

confhd = Confhd.read("confhd.dat")

if confhd.usinas is not None:
    # Identificar usinas que têm usinas a jusante
    usinas_com_jusante = confhd.usinas[
        (confhd.usinas['codigo_usina_jusante'].notna()) &
        (confhd.usinas['codigo_usina_jusante'] > 0)
    ]
    
    print(f"Usinas com aproveitamento a jusante: {len(usinas_com_jusante)}")
    
    # Construir cadeias hidráulicas (exemplo simplificado)
    print("\nAlgumas cadeias hidráulicas:")
    for idx, usina in usinas_com_jusante.head(10).iterrows():
        jusante = usina['codigo_usina_jusante']
        usina_jusante = confhd.usinas[confhd.usinas['codigo_usina'] == jusante]
        
        if not usina_jusante.empty:
            print(f"{usina['nome_usina']} -> {usina_jusante.iloc[0]['nome_usina']}")
```

#### 4.8. Consulta de Histórico de Vazões

```python
from inewave.newave import Confhd

confhd = Confhd.read("confhd.dat")

if confhd.usinas is not None:
    # Filtrar usinas com histórico personalizado
    usinas_historico_personalizado = confhd.usinas[
        (confhd.usinas['ano_inicio_historico'] > 0) &
        (confhd.usinas['ano_fim_historico'] > 0)
    ]
    
    print(f"Usinas com histórico personalizado: {len(usinas_historico_personalizado)}")
    
    if len(usinas_historico_personalizado) > 0:
        print("\nUsinas com histórico personalizado:")
        print(usinas_historico_personalizado[['codigo_usina', 'nome_usina', 'ano_inicio_historico', 'ano_fim_historico']])
    
    # Usinas que usam histórico do cadastro de postos
    usinas_historico_cadastro = confhd.usinas[
        (confhd.usinas['ano_inicio_historico'] == 0) |
        (confhd.usinas['ano_fim_historico'] == 0)
    ]
    
    print(f"\nUsinas usando histórico do cadastro: {len(usinas_historico_cadastro)}")
```

#### 4.9. Validação de Dados

```python
from inewave.newave import Confhd

confhd = Confhd.read("confhd.dat")

if confhd.usinas is not None:
    df_usinas = confhd.usinas
    
    # Verificar se há dados
    if len(df_usinas) == 0:
        print("⚠️ Nenhuma usina encontrada no arquivo")
    
    # Verificar campos obrigatórios
    campos_obrigatorios = ['codigo_usina', 'nome_usina', 'posto', 'ree']
    campos_faltando = [campo for campo in campos_obrigatorios if campo not in df_usinas.columns]
    
    if campos_faltando:
        print(f"⚠️ Campos faltando: {campos_faltando}")
    
    # Verificar códigos duplicados
    duplicatas = df_usinas[df_usinas.duplicated(subset=['codigo_usina'], keep=False)]
    if len(duplicatas) > 0:
        print(f"⚠️ {len(duplicatas)} usinas com códigos duplicados encontradas")
    
    # Verificar status válidos
    status_validos = ['EX', 'EE', 'NE', 'NC']
    status_invalidos = df_usinas[~df_usinas['usina_existente'].isin(status_validos)]
    if len(status_invalidos) > 0:
        print(f"⚠️ {len(status_invalidos)} usinas com status inválido")
    
    # Verificar volume inicial válido (0-100%)
    volumes_invalidos = df_usinas[
        (df_usinas['volume_inicial_percentual'] < 0) |
        (df_usinas['volume_inicial_percentual'] > 100)
    ]
    if len(volumes_invalidos) > 0:
        print(f"⚠️ {len(volumes_invalidos)} usinas com volume inicial fora do intervalo 0-100%")
    
    # Verificar REEs válidos (deve estar no arquivo REE.DAT)
    # Nota: Validação completa requer leitura do arquivo REE.DAT
    
    # Verificar índice de modificação válido (0 ou 1)
    modif_invalidos = df_usinas[~df_usinas['usina_modificada'].isin([0, 1])]
    if len(modif_invalidos) > 0:
        print(f"⚠️ {len(modif_invalidos)} usinas com índice de modificação inválido")
```

#### 4.10. Modificação e Gravação

```python
from inewave.newave import Confhd

# Ler o arquivo
confhd = Confhd.read("confhd.dat")

if confhd.usinas is not None:
    # Modificar volume inicial de uma usina específica
    codigo_usina = 1
    novo_volume = 50.0
    
    mask = confhd.usinas['codigo_usina'] == codigo_usina
    
    if mask.any():
        confhd.usinas.loc[mask, 'volume_inicial_percentual'] = novo_volume
        print(f"Volume inicial da usina {codigo_usina} atualizado para {novo_volume}%")
    
    # Modificar status de uma usina
    codigo_usina = 2
    novo_status = 'EE'  # Usina existente com expansão
    
    mask = confhd.usinas['codigo_usina'] == codigo_usina
    
    if mask.any():
        confhd.usinas.loc[mask, 'usina_existente'] = novo_status
        print(f"Status da usina {codigo_usina} atualizado para {novo_status}")
    
    # Salvar alterações
    confhd.write("confhd.dat")
```

#### 4.11. Análise de Volume Inicial por REE

```python
from inewave.newave import Confhd

confhd = Confhd.read("confhd.dat")

if confhd.usinas is not None:
    # Análise de volume inicial por REE
    volume_por_ree = confhd.usinas.groupby('ree')['volume_inicial_percentual'].agg([
        'mean', 'min', 'max', 'std'
    ]).round(2)
    
    print("Estatísticas de volume inicial por REE:")
    print(volume_por_ree)
    
    # Verificar se todas as usinas de um REE têm o mesmo volume inicial
    # (necessário para simulação final individualizada com política híbrida)
    for ree in confhd.usinas['ree'].unique():
        usinas_ree = confhd.usinas[confhd.usinas['ree'] == ree]
        volumes_unicos = usinas_ree['volume_inicial_percentual'].nunique()
        
        if volumes_unicos > 1:
            print(f"\n⚠️ REE {ree}: {volumes_unicos} volumes iniciais diferentes")
            print(f"   Volumes: {sorted(usinas_ree['volume_inicial_percentual'].unique())}")
```

---

### 5. Observações Importantes

1. **Associação com REE**: Cada usina deve estar associada a um REE válido cadastrado no arquivo `REE.DAT`

2. **Status da usina**: 
   - **EX**: Usina existente (incluída nos cálculos)
   - **EE**: Usina existente com expansão (número de máquinas preenchido com zero por default)
   - **NE**: Não existente (número de máquinas preenchido com zero por default)
   - **NC**: Não considerada (excluída dos cálculos do estudo)

3. **Volume inicial**: 
   - Expresso em percentual do volume útil (0-100%)
   - Utilizado se o registro 22 do `dger.dat` estiver preenchido com 1
   - Para simulação final individualizada com política híbrida, pode usar volume por REE (registro 23 do `dger.dat`)

4. **Modificação de dados**: 
   - O índice de modificação (campo 8) indica se dados serão alterados via `MODIF.DAT`
   - Se igual a 1, as modificações específicas estarão no arquivo `MODIF.DAT`

5. **Histórico de vazões**: 
   - Campos 9 e 10 só são necessários se diferirem do cadastro de postos (`postos.dat`)
   - Se zero ou não fornecidos, valores são lidos do cadastro de postos fluviométricos

6. **Tecnologia**: 
   - Campo 11 não é obrigatório
   - Se preenchido, a tecnologia deve estar declarada no arquivo `tecno.dat`
   - **Nota**: Este campo não está disponível na propriedade `usinas` da biblioteca inewave na versão atual

7. **Usina a jusante**: 
   - Campo 4 pode ser nulo ou zero se não houver aproveitamento a jusante
   - Define a cadeia hidráulica das usinas

8. **Posto de vazões**: 
   - Cada usina está associada a um posto de vazões
   - Os postos são definidos no arquivo de vazões (`vazoes.dat`)

9. **Comentários**: Os dois registros de comentário no início do arquivo são obrigatórios mas ignorados pelo programa

10. **DataFrame pandas**: A propriedade `usinas` retorna um DataFrame do pandas, permitindo uso completo das funcionalidades do pandas para análise e manipulação

11. **Validação**: É importante validar:
    - Códigos de usina únicos
    - Status válidos (EX, EE, NE, NC)
    - Volume inicial no intervalo 0-100%
    - REEs válidos (consistência com `REE.DAT`)
    - Índice de modificação válido (0 ou 1)

12. **Dependências**: 
    - Os REEs devem estar cadastrados no arquivo `REE.DAT`
    - Os postos de vazões devem estar definidos no arquivo `vazoes.dat`
    - As modificações (se índice = 1) devem estar no arquivo `MODIF.DAT`

13. **Campo Tecnologia**: O campo 11 (Tecnologia) não está mapeado na propriedade `usinas` da biblioteca inewave na versão atual. Se necessário, pode ser acessado diretamente do arquivo ou adicionado em versões futuras da biblioteca

---

## HIDR.DAT

### 1. Informações do Arquivo

#### 1.1. Nome e Descrição

- **Nome do arquivo**: `hidr.dat` ou `HIDR.DAT`
- **Tipo**: Arquivo de entrada essencial do modelo NEWAVE
- **Função**: Contém os dados de **cadastro** das usinas hidrelétricas, incluindo seus dados físicos e operacionais básicos

#### 1.2. Função e Responsabilidade

**Conteúdo Principal:**
O `HIDR.DAT` contém os dados de **cadastro** das usinas hidrelétricas, incluindo seus dados físicos e operacionais básicos.

**Acesso e Formato:**
- É um arquivo de **acesso direto e não formatado** (arquivo binário)
- Diferente dos outros arquivos NEWAVE que são arquivos de texto formatado

**Responsabilidade:**
Este arquivo é de **responsabilidade do ONS (Operador Nacional do Sistema Elétrico)**, não devendo ser alterado pelo usuário.

#### 1.3. Estrutura e Dimensão

**Registros:**
- O arquivo possui **320 ou 600 registros**, onde cada registro corresponde a uma usina
- A numeração das usinas hidrelétricas deve seguir o número do registro no qual essa usina está cadastrada no `HIDR.DAT`

**Formato:**
- Arquivo binário de acesso direto
- Cada registro contém informações completas de uma usina hidrelétrica
- A estrutura interna do arquivo é gerenciada pela biblioteca inewave

#### 1.4. Relação com Outros Arquivos

Embora o `HIDR.DAT` seja o cadastro base, seus dados podem ser complementados ou modificados por outros arquivos de entrada:

**`CONFHD.DAT` (Configuração Hidrelétrica):**
- Este arquivo de configuração usa o código da usina (Campo 1) que está no cadastro do `HIDR.DAT`
- O `CONFHD.DAT` associa cada usina a um REE e define configurações específicas do estudo

**`MODIF.DAT` (Alteração de Características):**
- Se o campo `Índice de modificação` no `CONFHD.DAT` for 1, um conjunto restrito de dados lidos do `HIDR.DAT` pode ser modificado através do `MODIF.DAT`
- Permite alterar características como volume mínimo/máximo, produtibilidade, vazão mínima, etc.

**Outros arquivos relacionados:**
- `VAZOES.DAT`: Define os postos de vazões referenciados no cadastro
- `EXPH.DAT`: Define expansões hidrelétricas para usinas com status EE ou NE

---

### 2. Propriedades da Biblioteca inewave

#### 2.1. Classe Correspondente

**Classe**: `Hidr`

```python
class Hidr(data=Ellipsis)
```

**Descrição**: Armazena os dados de entrada do NEWAVE referentes ao cadastro das usinas hidroelétricas.

**Características:**
- Herda de `RegisterFile`
- Usa armazenamento binário (`STORAGE = "BINARY"`)
- Cada registro é do tipo `RegistroUHEHidr`

#### 2.2. Propriedades Disponíveis

##### `property` **cadastro**: `pd.DataFrame`

- **Descrição**: Obtém a tabela com os dados cadastrais existentes no arquivo binário
- **Tipo de retorno**: `pd.DataFrame` (não retorna `None`, mas pode estar vazio)
- **Colunas do DataFrame** (mais de 60 campos):

**Informações Básicas:**
- `nome_usina` (`str`): Nome da usina (12 caracteres)
- `posto` (`int`): Posto de vazão natural da usina
- `submercado` (`int`): Submercado da usina
- `empresa` (`int`): Agente responsável pela usina
- `codigo_usina_jusante` (`int`): Posto à jusante da usina
- `desvio` (`float`): Desvio (TODO - documentação pendente)
- `data` (`str`): Data no formato DD-MM-AA
- `observacao` (`str`): Observação qualquer sobre a usina

**Volumes e Cotas:**
- `volume_minimo` (`float`): Volume mínimo da usina (hm³)
- `volume_maximo` (`float`): Volume máximo da usina (hm³)
- `volume_vertedouro` (`float`): Volume do vertedouro da usina (hm³)
- `volume_desvio` (`float`): Volume de desvio (TODO - documentação pendente)
- `volume_referencia` (`float`): Volume de referência (TODO - documentação pendente)
- `cota_minima` (`float`): Cota mínima da usina (m)
- `cota_maxima` (`float`): Cota máxima da usina (m)

**Polinômios Volume-Cota e Cota-Área:**
- `a0_volume_cota` (`float`): Coeficiente 0 do polinômio volume-cota
- `a1_volume_cota` (`float`): Coeficiente 1 do polinômio volume-cota
- `a2_volume_cota` (`float`): Coeficiente 2 do polinômio volume-cota
- `a3_volume_cota` (`float`): Coeficiente 3 do polinômio volume-cota
- `a4_volume_cota` (`float`): Coeficiente 4 do polinômio volume-cota
- `a0_cota_area` (`float`): Coeficiente 0 do polinômio cota-área
- `a1_cota_area` (`float`): Coeficiente 1 do polinômio cota-área
- `a2_cota_area` (`float`): Coeficiente 2 do polinômio cota-área
- `a3_cota_area` (`float`): Coeficiente 3 do polinômio cota-área
- `a4_cota_area` (`float`): Coeficiente 4 do polinômio cota-área

**Evaporação:**
- `evaporacao_JAN` (`float`): Coeficiente de evaporação para janeiro (mm)
- `evaporacao_FEV` (`float`): Coeficiente de evaporação para fevereiro (mm)
- `evaporacao_MAR` (`float`): Coeficiente de evaporação para março (mm)
- `evaporacao_ABR` (`float`): Coeficiente de evaporação para abril (mm)
- `evaporacao_MAI` (`float`): Coeficiente de evaporação para maio (mm)
- `evaporacao_JUN` (`float`): Coeficiente de evaporação para junho (mm)
- `evaporacao_JUL` (`float`): Coeficiente de evaporação para julho (mm)
- `evaporacao_AGO` (`float`): Coeficiente de evaporação para agosto (mm)
- `evaporacao_SET` (`float`): Coeficiente de evaporação para setembro (mm)
- `evaporacao_OUT` (`float`): Coeficiente de evaporação para outubro (mm)
- `evaporacao_NOV` (`float`): Coeficiente de evaporação para novembro (mm)
- `evaporacao_DEZ` (`float`): Coeficiente de evaporação para dezembro (mm)

**Conjuntos de Máquinas (até 5 conjuntos):**
- `numero_conjuntos_maquinas` (`int`): Número de conjuntos de máquinas
- `maquinas_conjunto_1` (`int`): Número de máquinas no conjunto 1
- `maquinas_conjunto_2` (`int`): Número de máquinas no conjunto 2
- `maquinas_conjunto_3` (`int`): Número de máquinas no conjunto 3
- `maquinas_conjunto_4` (`int`): Número de máquinas no conjunto 4
- `maquinas_conjunto_5` (`int`): Número de máquinas no conjunto 5
- `potencia_nominal_conjunto_1` (`float`): Potência das máquinas do conjunto 1 (MWmed)
- `potencia_nominal_conjunto_2` (`float`): Potência das máquinas do conjunto 2 (MWmed)
- `potencia_nominal_conjunto_3` (`float`): Potência das máquinas do conjunto 3 (MWmed)
- `potencia_nominal_conjunto_4` (`float`): Potência das máquinas do conjunto 4 (MWmed)
- `potencia_nominal_conjunto_5` (`float`): Potência das máquinas do conjunto 5 (MWmed)
- `queda_nominal_conjunto_1` (`float`): Altura nominal de queda do conjunto 1 (m)
- `queda_nominal_conjunto_2` (`float`): Altura nominal de queda do conjunto 2 (m)
- `queda_nominal_conjunto_3` (`float`): Altura nominal de queda do conjunto 3 (m)
- `queda_nominal_conjunto_4` (`float`): Altura nominal de queda do conjunto 4 (m)
- `queda_nominal_conjunto_5` (`float`): Altura nominal de queda do conjunto 5 (m)
- `vazao_nominal_conjunto_1` (`float`): Vazão nominal do conjunto 1 (m³/s)
- `vazao_nominal_conjunto_2` (`float`): Vazão nominal do conjunto 2 (m³/s)
- `vazao_nominal_conjunto_3` (`float`): Vazão nominal do conjunto 3 (m³/s)
- `vazao_nominal_conjunto_4` (`float`): Vazão nominal do conjunto 4 (m³/s)
- `vazao_nominal_conjunto_5` (`float`): Vazão nominal do conjunto 5 (m³/s)

**Características Operacionais:**
- `produtibilidade_especifica` (`float`): Produtibilidade específica
- `perdas` (`float`): Perdas da usina
- `vazao_minima_historica` (`float`): Vazão mínima da usina (m³/s)
- `canal_fuga_medio` (`float`): Cota média do canal de fuga (m)
- `tipo_regulacao` (`str`): Tipo de regulação (D, S ou M)

**Polinômios de Jusante (até 6 polinômios):**
- `numero_polinomios_jusante` (`int`): Número de polinômios de jusante
- `a0_jusante_1` até `a4_jusante_1` (`float`): Coeficientes do polinômio de jusante 1
- `a0_jusante_2` até `a4_jusante_2` (`float`): Coeficientes do polinômio de jusante 2
- `a0_jusante_3` até `a4_jusante_3` (`float`): Coeficientes do polinômio de jusante 3
- `a0_jusante_4` até `a4_jusante_4` (`float`): Coeficientes do polinômio de jusante 4
- `a0_jusante_5` até `a4_jusante_5` (`float`): Coeficientes do polinômio de jusante 5
- `a0_jusante_6` até `a4_jusante_6` (`float`): Coeficientes do polinômio de jusante 6
- `referencia_jusante_1` até `referencia_jusante_6` (`float`): Coeficientes do polinjus de referência

**Campos Adicionais (documentação pendente):**
- `influencia_vertimento_canal_fuga` (`int`): TODO (0 ou 1)
- `fator_carga_maximo` (`float`): TODO (%)
- `fator_carga_minimo` (`float`): TODO (%)
- `numero_unidades_base` (`int`): TODO
- `tipo_turbina` (`int`): TODO
- `representacao_conjunto` (`int`): TODO
- `teif` (`float`): TODO (%)
- `ip` (`float`): TODO (%)
- `tipo_perda` (`int`): TODO

**Observações:**
- O DataFrame contém todas as informações cadastrais de cada usina
- Cada linha representa uma usina hidrelétrica
- O índice do DataFrame corresponde ao número do registro (código da usina)
- Alguns campos têm documentação pendente (marcados como TODO)
- O DataFrame é construído a partir dos registros binários do arquivo

---

### 3. Mapeamento de Campos

O arquivo `HIDR.DAT` é um arquivo binário de acesso direto, onde cada registro contém informações de uma usina. A biblioteca inewave converte esses registros binários em um DataFrame pandas com mais de 60 colunas.

**Principais grupos de campos mapeados:**

| Grupo de Campos | Colunas no DataFrame | Descrição |
| :--- | :--- | :--- |
| **Informações Básicas** | `nome_usina`, `posto`, `submercado`, `empresa`, `codigo_usina_jusante` | Dados de identificação e localização |
| **Volumes** | `volume_minimo`, `volume_maximo`, `volume_vertedouro`, `volume_desvio`, `volume_referencia` | Volumes do reservatório (hm³) |
| **Cotas** | `cota_minima`, `cota_maxima` | Cotas do reservatório (m) |
| **Polinômios Volume-Cota** | `a0_volume_cota` até `a4_volume_cota` | Coeficientes do polinômio volume-cota |
| **Polinômios Cota-Área** | `a0_cota_area` até `a4_cota_area` | Coeficientes do polinômio cota-área |
| **Evaporação** | `evaporacao_JAN` até `evaporacao_DEZ` | Coeficientes mensais de evaporação (mm) |
| **Conjuntos de Máquinas** | `numero_conjuntos_maquinas`, `maquinas_conjunto_[1-5]`, `potencia_nominal_conjunto_[1-5]`, `queda_nominal_conjunto_[1-5]`, `vazao_nominal_conjunto_[1-5]` | Características dos conjuntos de máquinas |
| **Características Operacionais** | `produtibilidade_especifica`, `perdas`, `vazao_minima_historica`, `canal_fuga_medio`, `tipo_regulacao` | Parâmetros operacionais |
| **Polinômios de Jusante** | `numero_polinomios_jusante`, `a[0-4]_jusante_[1-6]`, `referencia_jusante_[1-6]` | Polinômios de jusante |

**Nota**: Devido à natureza binária do arquivo e à complexidade da estrutura, o mapeamento completo campo-a-campo não é apresentado aqui. A biblioteca inewave abstrai essa complexidade fornecendo acesso direto através do DataFrame.

---

### 4. Exemplos de Uso

#### 4.1. Leitura do Arquivo

```python
from inewave.newave import Hidr

# Ler o arquivo hidr.dat (binário)
hidr = Hidr.read("hidr.dat")

# Acessar o cadastro completo
cadastro = hidr.cadastro

if cadastro is not None:
    print(f"Total de usinas hidrelétricas: {len(cadastro)}")
    print(f"Total de colunas: {len(cadastro.columns)}")
    print("\nPrimeiras 5 usinas:")
    print(cadastro.head())
else:
    print("Nenhuma usina encontrada ou arquivo vazio")
```

#### 4.2. Consulta de Usina Específica

```python
from inewave.newave import Hidr

hidr = Hidr.read("hidr.dat")

if hidr.cadastro is not None:
    # Consultar uma usina específica pelo índice (código da usina)
    codigo_usina = 1
    usina = hidr.cadastro.iloc[codigo_usina - 1]  # Índice é 0-based
    
    print(f"Usina {codigo_usina}: {usina['nome_usina']}")
    print(f"  Posto: {usina['posto']}")
    print(f"  Submercado: {usina['submercado']}")
    print(f"  Volume máximo: {usina['volume_maximo']} hm³")
    print(f"  Volume mínimo: {usina['volume_minimo']} hm³")
```

#### 4.3. Consulta por Nome de Usina

```python
from inewave.newave import Hidr

hidr = Hidr.read("hidr.dat")

if hidr.cadastro is not None:
    # Filtrar por nome da usina (busca parcial, case-insensitive)
    nome_procurado = "Itaipu"
    usinas_encontradas = hidr.cadastro[
        hidr.cadastro['nome_usina'].str.contains(nome_procurado, case=False, na=False)
    ]
    
    print(f"Usinas encontradas para '{nome_procurado}':")
    print(usinas_encontradas[['nome_usina', 'posto', 'submercado', 'volume_maximo']])
```

#### 4.4. Análise de Volumes dos Reservatórios

```python
from inewave.newave import Hidr

hidr = Hidr.read("hidr.dat")

if hidr.cadastro is not None:
    # Estatísticas dos volumes
    print("Estatísticas dos volumes dos reservatórios (hm³):")
    print(hidr.cadastro[['volume_minimo', 'volume_maximo', 'volume_vertedouro']].describe())
    
    # Usinas com maiores volumes máximos
    print("\nTop 10 usinas com maiores volumes máximos:")
    top_volumes = hidr.cadastro.nlargest(10, 'volume_maximo')
    print(top_volumes[['nome_usina', 'volume_maximo', 'volume_minimo']])
```

#### 4.5. Cálculo de Potência Total Instalada

```python
from inewave.newave import Hidr

hidr = Hidr.read("hidr.dat")

if hidr.cadastro is not None:
    # Calcular potência total instalada por usina
    cadastro_com_potencia = hidr.cadastro.copy()
    cadastro_com_potencia['potencia_total'] = 0
    
    for i in range(1, 6):
        pot_col = f'potencia_nominal_conjunto_{i}'
        maq_col = f'maquinas_conjunto_{i}'
        
        if pot_col in cadastro_com_potencia.columns and maq_col in cadastro_com_potencia.columns:
            cadastro_com_potencia['potencia_total'] += (
                cadastro_com_potencia[pot_col] * cadastro_com_potencia[maq_col]
            )
    
    print("Usinas com maior capacidade instalada:")
    top_potencia = cadastro_com_potencia.nlargest(10, 'potencia_total')
    print(top_potencia[['nome_usina', 'potencia_total']])
```

#### 4.6. Análise por Submercado

```python
from inewave.newave import Hidr

hidr = Hidr.read("hidr.dat")

if hidr.cadastro is not None:
    # Contar usinas por submercado
    usinas_por_submercado = hidr.cadastro.groupby('submercado').agg({
        'nome_usina': 'count',
        'volume_maximo': 'sum',
        'potencia_total': 'sum'  # Se calculado anteriormente
    })
    
    usinas_por_submercado.columns = ['quantidade', 'volume_total_hm3', 'potencia_total_mw']
    
    print("Distribuição de usinas por submercado:")
    print(usinas_por_submercado)
```

#### 4.7. Análise de Evaporação

```python
from inewave.newave import Hidr

hidr = Hidr.read("hidr.dat")

if hidr.cadastro is not None:
    # Calcular evaporação média anual por usina
    meses = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 
             'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
    
    colunas_evap = [f'evaporacao_{mes}' for mes in meses]
    colunas_existentes = [col for col in colunas_evap if col in hidr.cadastro.columns]
    
    if colunas_existentes:
        hidr.cadastro['evaporacao_media_anual'] = hidr.cadastro[colunas_existentes].mean(axis=1)
        
        print("Usinas com maior evaporação média anual:")
        top_evap = hidr.cadastro.nlargest(10, 'evaporacao_media_anual')
        print(top_evap[['nome_usina', 'evaporacao_media_anual']])
```

#### 4.8. Consulta de Características de Máquinas

```python
from inewave.newave import Hidr

hidr = Hidr.read("hidr.dat")

if hidr.cadastro is not None:
    # Filtrar usinas com múltiplos conjuntos de máquinas
    usinas_multiplos_conjuntos = hidr.cadastro[
        hidr.cadastro['numero_conjuntos_maquinas'] > 1
    ]
    
    print(f"Usinas com múltiplos conjuntos: {len(usinas_multiplos_conjuntos)}")
    
    # Analisar características do primeiro conjunto
    if 'potencia_nominal_conjunto_1' in hidr.cadastro.columns:
        print("\nEstatísticas da potência nominal do conjunto 1:")
        print(hidr.cadastro['potencia_nominal_conjunto_1'].describe())
```

#### 4.9. Validação de Dados

```python
from inewave.newave import Hidr

hidr = Hidr.read("hidr.dat")

if hidr.cadastro is not None:
    cadastro = hidr.cadastro
    
    # Verificar se há dados
    if len(cadastro) == 0:
        print("⚠️ Nenhuma usina encontrada no arquivo")
    
    # Verificar volumes válidos
    volumes_invalidos = cadastro[
        (cadastro['volume_maximo'] < cadastro['volume_minimo']) |
        (cadastro['volume_maximo'] <= 0)
    ]
    
    if len(volumes_invalidos) > 0:
        print(f"⚠️ {len(volumes_invalidos)} usinas com volumes inválidos")
    
    # Verificar cotas válidas
    cotas_invalidas = cadastro[
        (cadastro['cota_maxima'] < cadastro['cota_minima']) |
        (cadastro['cota_maxima'] <= 0)
    ]
    
    if len(cotas_invalidas) > 0:
        print(f"⚠️ {len(cotas_invalidas)} usinas com cotas inválidas")
    
    # Verificar número de conjuntos válido (1-5)
    conjuntos_invalidos = cadastro[
        (cadastro['numero_conjuntos_maquinas'] < 1) |
        (cadastro['numero_conjuntos_maquinas'] > 5)
    ]
    
    if len(conjuntos_invalidos) > 0:
        print(f"⚠️ {len(conjuntos_invalidos)} usinas com número de conjuntos inválido")
    
    # Verificar tipo de regulação válido
    if 'tipo_regulacao' in cadastro.columns:
        tipos_validos = ['D', 'S', 'M']
        tipos_invalidos = cadastro[~cadastro['tipo_regulacao'].isin(tipos_validos)]
        
        if len(tipos_invalidos) > 0:
            print(f"⚠️ {len(tipos_invalidos)} usinas com tipo de regulação inválido")
```

#### 4.10. Modificação e Gravação

```python
from inewave.newave import Hidr

# Ler o arquivo
hidr = Hidr.read("hidr.dat")

if hidr.cadastro is not None:
    # Modificar volume máximo de uma usina específica
    codigo_usina = 1
    novo_volume_maximo = 50000.0  # hm³
    
    # O índice do DataFrame corresponde ao código da usina - 1
    idx = codigo_usina - 1
    
    if idx < len(hidr.cadastro):
        hidr.cadastro.iloc[idx, hidr.cadastro.columns.get_loc('volume_maximo')] = novo_volume_maximo
        print(f"Volume máximo da usina {codigo_usina} atualizado para {novo_volume_maximo} hm³")
    
    # Salvar alterações
    # Nota: A biblioteca atualiza os registros internos antes de gravar
    hidr.write("hidr.dat")
```

#### 4.11. Análise de Polinômios

```python
from inewave.newave import Hidr

hidr = Hidr.read("hidr.dat")

if hidr.cadastro is not None:
    # Analisar polinômios volume-cota
    colunas_polin_vc = [f'a{i}_volume_cota' for i in range(5)]
    colunas_existentes_vc = [col for col in colunas_polin_vc if col in hidr.cadastro.columns]
    
    if colunas_existentes_vc:
        print("Estatísticas dos coeficientes do polinômio volume-cota:")
        print(hidr.cadastro[colunas_existentes_vc].describe())
    
    # Analisar polinômios de jusante
    if 'numero_polinomios_jusante' in hidr.cadastro.columns:
        distribuicao_polinjus = hidr.cadastro['numero_polinomios_jusante'].value_counts().sort_index()
        print("\nDistribuição do número de polinômios de jusante:")
        print(distribuicao_polinjus)
```

---

### 5. Observações Importantes

1. **Arquivo binário**: O `HIDR.DAT` é um arquivo binário de acesso direto, diferente dos outros arquivos NEWAVE que são texto formatado

2. **Responsabilidade do ONS**: Este arquivo é de responsabilidade do ONS e não deve ser alterado pelo usuário, exceto em casos específicos de estudos

3. **Número de registros**: O arquivo possui 320 ou 600 registros, onde cada registro corresponde a uma usina

4. **Numeração**: A numeração das usinas hidrelétricas deve seguir o número do registro no qual essa usina está cadastrada no `HIDR.DAT`

5. **Modificações**: 
   - Dados do `HIDR.DAT` podem ser modificados através do arquivo `MODIF.DAT`
   - Para isso, o campo `Índice de modificação` no `CONFHD.DAT` deve ser igual a 1

6. **Relação com CONFHD**: 
   - O `CONFHD.DAT` usa o código da usina que está no cadastro do `HIDR.DAT`
   - Os dois arquivos devem estar consistentes

7. **Estrutura complexa**: 
   - O DataFrame retornado pela propriedade `cadastro` contém mais de 60 colunas
   - Inclui polinômios, evaporação mensal, múltiplos conjuntos de máquinas, etc.

8. **Campos com documentação pendente**: 
   - Alguns campos estão marcados como "TODO" na biblioteca
   - Esses campos podem ter significado específico no contexto do NEWAVE

9. **Polinômios**: 
   - Os polinômios volume-cota e cota-área são fundamentais para cálculos de energia armazenada
   - Os polinômios de jusante modelam a relação com usinas a jusante

10. **Conjuntos de máquinas**: 
    - Uma usina pode ter até 5 conjuntos de máquinas
    - Cada conjunto tem suas próprias características (potência, queda, vazão)

11. **Evaporação**: 
    - Coeficientes de evaporação são fornecidos mensalmente
    - Importante para cálculo de perdas por evaporação

12. **Tipo de regulação**: 
    - Pode ser D (diária), S (semanal) ou M (mensal)
    - Afeta a modelagem operacional da usina

13. **DataFrame pandas**: 
    - A propriedade `cadastro` retorna um DataFrame do pandas
    - Permite uso completo das funcionalidades do pandas para análise e manipulação

14. **Gravação**: 
    - Ao modificar o DataFrame e gravar, a biblioteca atualiza automaticamente os registros binários
    - Use com cuidado, pois o arquivo é de responsabilidade do ONS

15. **Dependências**: 
    - Os postos de vazões referenciados devem estar no arquivo `vazoes.dat`
    - As modificações devem estar no arquivo `MODIF.DAT` (se aplicável)
    - A configuração deve estar no arquivo `CONFHD.DAT`

---

## VAZOES.DAT

### 1. Informações do Arquivo

#### 1.1. Nome e Descrição

- **Nome do arquivo**: `vazoes.dat` ou `VAZOES.DAT`
- **Tipo**: Arquivo de entrada essencial do modelo NEWAVE
- **Função**: Contém o **cadastro das vazões naturais históricas** que afluem às usinas hidrelétricas

#### 1.2. Função e Responsabilidade

**Conteúdo Principal:**
O `VAZOES.DAT` armazena o **cadastro das vazões naturais históricas** que afluem às usinas hidrelétricas.

**Finalidade no Modelo:**
A partir dos registros históricos contidos neste arquivo, é possível **construir a série histórica de energias naturais afluentes (ENAs)** a cada Reservatório Equivalente de Energia (REE). Essa série histórica de ENAs é então utilizada para o ajuste do modelo estocástico autorregressivo periódico (PAR(p)), que gera as séries sintéticas de energia para as simulações do NEWAVE.

**Responsabilidade:**
Este arquivo é de **responsabilidade do ONS (Operador Nacional do Sistema Elétrico)** e, portanto, seu nome e conteúdo básico não devem ser alterados pelo usuário.

#### 1.3. Estrutura e Formato

**Acesso e Formato:**
- É um arquivo de **acesso direto e não formatado** (arquivo binário)
- Diferente dos outros arquivos NEWAVE que são arquivos de texto formatado

**Registros:**
- O arquivo é estruturado com um número fixo de postos
- Ele contém **320 ou 600 postos**, onde cada registro corresponde a um mês do histórico de vazões
- Cada registro contém as vazões de todos os postos para aquele mês específico

**Estrutura de Dados:**
- Cada linha (registro) representa um mês do histórico de vazões
- Cada coluna representa um posto de vazões (numerado de 1 a N, onde N = 320 ou 600)
- Cada célula contém a vazão natural afluente (em m³/s ou unidade definida pelo modelo) para aquele posto naquele mês

#### 1.4. Relação com Outros Arquivos e Configurações

**Tamanho do Registro:**
- O tamanho do registro do `VAZOES.DAT` (320 ou 600 palavras) é um dado de configuração lido no **registro 21 do arquivo de dados gerais (`dger.dat`)** (coluna 29, formato I1), que indica se o arquivo possui 320 ou 600 palavras

**Ano Inicial:**
- O **ano inicial** do arquivo de vazões históricas também é lido no **registro 21 do `dger.dat`**

**Tendência Hidrológica:**
- A incerteza hidrológica do sistema, obtida a partir das afluências aos reservatórios nos meses anteriores, é uma informação que compõe o estado do sistema
- A tendência hidrológica pode ser lida por posto de medição (que utiliza as vazões) ou por REE, sendo a escolha feita através do registro 34 do `dger.dat`

**Dados de Postos Fluviométricos:**
- O `VAZOES.DAT` está intimamente ligado ao arquivo `POSTOS.DAT` (Dados de postos fluviométricos), que contém o nome do posto e os anos inicial e final do registro de vazões históricas
- Caso os campos 9 e/ou 10 do arquivo de configuração hidroelétrica (`CONFHD.DAT`), que definem o período do histórico de vazões a ser considerado para ajuste do modelo, não sejam fornecidos (ou sejam zero), o NEWAVE lerá esses valores do cadastro de postos fluviométricos (`postos.dat`)

**Relação com HIDR.DAT:**
- Cada usina no `HIDR.DAT` está associada a um posto de vazões
- As vazões históricas desse posto são utilizadas para calcular as ENAs da usina

**Relação com CONFHD.DAT:**
- O campo 3 do `CONFHD.DAT` (Número do posto de vazões) referencia os postos definidos no `VAZOES.DAT`
- Os campos 9 e 10 do `CONFHD.DAT` podem definir o período histórico específico para cada usina

---

### 2. Propriedades da Biblioteca inewave

#### 2.1. Classe Correspondente

**Classe**: `Vazoes`

```python
class Vazoes(data=Ellipsis)
```

**Descrição**: Armazena os dados de entrada do NEWAVE referentes ao cadastro das vazões históricas por posto.

**Características:**
- Herda de `RegisterFile`
- Usa armazenamento binário (`STORAGE = "BINARY"`)
- Cada registro é do tipo `RegistroVazoesPostos`
- Por padrão, suporta 320 postos (pode ser configurado para 600)

#### 2.2. Propriedades Disponíveis

##### `property` **vazoes**: `pd.DataFrame`

- **Descrição**: Obtém a tabela com os dados de vazão existentes no arquivo binário
- **Tipo de retorno**: `pd.DataFrame` (não retorna `None`, mas pode estar vazio)
- **Estrutura do DataFrame**:
  - **Linhas**: Cada linha representa um mês do histórico de vazões (ordenado cronologicamente)
  - **Colunas**: Numeradas de `1` a `N`, onde `N` é o número de postos (320 ou 600)
  - **Valores**: Cada célula contém a vazão natural afluente (`int`) para aquele posto naquele mês

**Exemplo de estrutura:**
```
        1      2      3    ...    320
0    1234   5678   9012   ...   3456
1    2345   6789   0123   ...   4567
2    3456   7890   1234   ...   5678
...
```

Onde:
- Linha 0 = primeiro mês do histórico
- Coluna 1 = posto 1
- Coluna 2 = posto 2
- etc.

**Observações:**
- O DataFrame é construído a partir dos registros binários do arquivo
- Cada coluna representa um posto de vazões (numerado de 1 a N)
- Cada linha representa um mês do histórico (ordenado cronologicamente)
- Os valores são do tipo `int` (vazões em m³/s ou unidade definida pelo modelo)
- O número de postos (320 ou 600) é determinado pela configuração do arquivo

---

### 3. Mapeamento de Campos

O arquivo `VAZOES.DAT` é um arquivo binário de acesso direto, onde cada registro contém as vazões de todos os postos para um mês específico.

**Estrutura do DataFrame:**

| Dimensão | Descrição | Tipo | Valores |
| :--- | :--- | :--- | :--- |
| **Linhas** | Meses do histórico | Índice (0-based) | 0, 1, 2, ... (ordenado cronologicamente) |
| **Colunas** | Postos de vazões | `int` (1 a N) | 1, 2, 3, ..., 320 (ou 600) |
| **Valores** | Vazões naturais afluentes | `int` | Vazão em m³/s (ou unidade definida) |

**Mapeamento:**
- **Registro binário** → **Linha do DataFrame** (um registro = um mês)
- **Posição no registro** → **Coluna do DataFrame** (posição = número do posto)
- **Valor no registro** → **Valor na célula** (vazão do posto naquele mês)

**Nota**: Devido à natureza binária do arquivo e à estrutura de acesso direto, o mapeamento é feito automaticamente pela biblioteca inewave, convertendo os registros binários em um DataFrame pandas bidimensional.

---

### 4. Exemplos de Uso

#### 4.1. Leitura do Arquivo

```python
from inewave.newave import Vazoes

# Ler o arquivo vazoes.dat (binário)
vazoes = Vazoes.read("vazoes.dat")

# Acessar o DataFrame de vazões
df_vazoes = vazoes.vazoes

if df_vazoes is not None and not df_vazoes.empty:
    print(f"Total de meses no histórico: {len(df_vazoes)}")
    print(f"Total de postos: {len(df_vazoes.columns)}")
    print(f"Postos disponíveis: {list(df_vazoes.columns)[:10]}...")  # Primeiros 10
    print("\nPrimeiros 5 meses (primeiros 5 postos):")
    print(df_vazoes.iloc[:5, :5])
else:
    print("Nenhuma vazão encontrada ou arquivo vazio")
```

#### 4.2. Consulta de Vazões de um Posto Específico

```python
from inewave.newave import Vazoes

vazoes = Vazoes.read("vazoes.dat")

if vazoes.vazoes is not None:
    # Consultar vazões do posto 1
    posto = 1
    vazoes_posto = vazoes.vazoes[posto]
    
    print(f"Vazões do posto {posto}:")
    print(f"Total de meses: {len(vazoes_posto)}")
    print(f"Vazão média: {vazoes_posto.mean():.2f} m³/s")
    print(f"Vazão mínima: {vazoes_posto.min()} m³/s")
    print(f"Vazão máxima: {vazoes_posto.max()} m³/s")
    print("\nPrimeiros 12 meses:")
    print(vazoes_posto.head(12))
```

#### 4.3. Consulta de Vazões de um Mês Específico

```python
from inewave.newave import Vazoes

vazoes = Vazoes.read("vazoes.dat")

if vazoes.vazoes is not None:
    # Consultar vazões do primeiro mês (índice 0)
    mes = 0
    vazoes_mes = vazoes.vazoes.iloc[mes]
    
    print(f"Vazões do mês {mes + 1} do histórico:")
    print(f"Total de postos: {len(vazoes_mes)}")
    print(f"Vazão média: {vazoes_mes.mean():.2f} m³/s")
    print("\nPrimeiros 10 postos:")
    print(vazoes_mes.head(10))
```

#### 4.4. Análise Estatística por Posto

```python
from inewave.newave import Vazoes

vazoes = Vazoes.read("vazoes.dat")

if vazoes.vazoes is not None:
    # Estatísticas descritivas por posto
    estatisticas = vazoes.vazoes.describe()
    
    print("Estatísticas descritivas das vazões por posto:")
    print(estatisticas)
    
    # Postos com maior vazão média
    vazoes_medias = vazoes.vazoes.mean().sort_values(ascending=False)
    
    print("\nTop 10 postos com maior vazão média:")
    print(vazoes_medias.head(10))
```

#### 4.5. Análise Temporal de um Posto

```python
from inewave.newave import Vazoes
import matplotlib.pyplot as plt

vazoes = Vazoes.read("vazoes.dat")

if vazoes.vazoes is not None:
    # Análise temporal do posto 1
    posto = 1
    serie_temporal = vazoes.vazoes[posto]
    
    print(f"Análise temporal do posto {posto}:")
    print(f"Total de meses: {len(serie_temporal)}")
    print(f"Vazão média: {serie_temporal.mean():.2f} m³/s")
    print(f"Desvio padrão: {serie_temporal.std():.2f} m³/s")
    print(f"Coeficiente de variação: {(serie_temporal.std() / serie_temporal.mean() * 100):.2f}%")
    
    # Identificar meses com vazões extremas
    vazao_media = serie_temporal.mean()
    desvio = serie_temporal.std()
    
    meses_secos = serie_temporal[serie_temporal < (vazao_media - 2 * desvio)]
    meses_umidos = serie_temporal[serie_temporal > (vazao_media + 2 * desvio)]
    
    print(f"\nMeses com vazões muito baixas (< média - 2σ): {len(meses_secos)}")
    print(f"Meses com vazões muito altas (> média + 2σ): {len(meses_umidos)}")
```

#### 4.6. Análise de Sazonalidade

```python
from inewave.newave import Vazoes

vazoes = Vazoes.read("vazoes.dat")

if vazoes.vazoes is not None:
    # Analisar sazonalidade do posto 1
    posto = 1
    serie = vazoes.vazoes[posto]
    
    # Agrupar por mês do ano (assumindo que a série começa em janeiro)
    # Nota: Ajustar conforme o ano inicial do histórico
    meses_do_ano = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun',
                     'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
    
    # Criar índice de mês (0-11)
    indices_mes = [i % 12 for i in range(len(serie))]
    
    # Agrupar por mês
    serie_com_mes = serie.copy()
    serie_com_mes.index = indices_mes
    
    vazoes_por_mes = serie_com_mes.groupby(level=0).mean()
    
    print(f"Vazões médias mensais do posto {posto}:")
    for i, (mes_idx, vazao) in enumerate(vazoes_por_mes.items()):
        print(f"  {meses_do_ano[mes_idx]}: {vazao:.2f} m³/s")
```

#### 4.7. Comparação entre Postos

```python
from inewave.newave import Vazoes

vazoes = Vazoes.read("vazoes.dat")

if vazoes.vazoes is not None:
    # Comparar dois postos específicos
    posto1 = 1
    posto2 = 2
    
    vazoes_posto1 = vazoes.vazoes[posto1]
    vazoes_posto2 = vazoes.vazoes[posto2]
    
    print(f"Comparação entre postos {posto1} e {posto2}:")
    print(f"\nPosto {posto1}:")
    print(f"  Média: {vazoes_posto1.mean():.2f} m³/s")
    print(f"  Mínima: {vazoes_posto1.min()} m³/s")
    print(f"  Máxima: {vazoes_posto1.max()} m³/s")
    
    print(f"\nPosto {posto2}:")
    print(f"  Média: {vazoes_posto2.mean():.2f} m³/s")
    print(f"  Mínima: {vazoes_posto2.min()} m³/s")
    print(f"  Máxima: {vazoes_posto2.max()} m³/s")
    
    # Correlação entre os postos
    correlacao = vazoes_posto1.corr(vazoes_posto2)
    print(f"\nCorrelação entre postos: {correlacao:.4f}")
```

#### 4.8. Análise de Períodos Específicos

```python
from inewave.newave import Vazoes

vazoes = Vazoes.read("vazoes.dat")

if vazoes.vazoes is not None:
    # Analisar um período específico (ex: primeiros 12 meses = primeiro ano)
    periodo_inicio = 0
    periodo_fim = 11  # 12 meses (0 a 11)
    
    vazoes_periodo = vazoes.vazoes.iloc[periodo_inicio:periodo_fim + 1]
    
    print(f"Análise do período (meses {periodo_inicio + 1} a {periodo_fim + 1}):")
    print(f"Vazão média por posto:")
    print(vazoes_periodo.mean().head(10))
    
    # Vazão total do período (soma de todos os postos)
    vazao_total_periodo = vazoes_periodo.sum().sum()
    print(f"\nVazão total do período (soma de todos os postos): {vazao_total_periodo:.2f}")
```

#### 4.9. Validação de Dados

```python
from inewave.newave import Vazoes

vazoes = Vazoes.read("vazoes.dat")

if vazoes.vazoes is not None:
    df_vazoes = vazoes.vazoes
    
    # Verificar se há dados
    if len(df_vazoes) == 0:
        print("⚠️ Nenhuma vazão encontrada no arquivo")
    
    # Verificar valores negativos (não deveriam existir)
    valores_negativos = (df_vazoes < 0).sum().sum()
    if valores_negativos > 0:
        print(f"⚠️ {valores_negativos} valores negativos encontrados")
    
    # Verificar valores zero (podem indicar problemas ou postos não utilizados)
    valores_zero = (df_vazoes == 0).sum().sum()
    print(f"ℹ️ {valores_zero} valores zero encontrados (podem ser postos não utilizados)")
    
    # Verificar postos com todas as vazões zero
    postos_zerados = df_vazoes.columns[(df_vazoes == 0).all()]
    if len(postos_zerados) > 0:
        print(f"⚠️ {len(postos_zerados)} postos com todas as vazões zero: {list(postos_zerados)}")
    
    # Verificar postos com valores muito altos (possíveis erros)
    # Definir um limite razoável (ex: 100.000 m³/s)
    limite_maximo = 100000
    valores_muito_altos = (df_vazoes > limite_maximo).sum().sum()
    if valores_muito_altos > 0:
        print(f"⚠️ {valores_muito_altos} valores acima de {limite_maximo} m³/s encontrados")
    
    # Verificar consistência do número de postos
    numero_postos = len(df_vazoes.columns)
    if numero_postos not in [320, 600]:
        print(f"⚠️ Número de postos ({numero_postos}) diferente do esperado (320 ou 600)")
    else:
        print(f"✅ Número de postos: {numero_postos}")
```

#### 4.10. Modificação e Gravação

```python
from inewave.newave import Vazoes

# Ler o arquivo
vazoes = Vazoes.read("vazoes.dat")

if vazoes.vazoes is not None:
    # Modificar vazão de um posto específico em um mês específico
    mes = 0  # Primeiro mês
    posto = 1
    nova_vazao = 5000  # m³/s
    
    vazoes.vazoes.iloc[mes, posto - 1] = nova_vazao
    print(f"Vazão do posto {posto} no mês {mes + 1} atualizada para {nova_vazao} m³/s")
    
    # Modificar todas as vazões de um posto (exemplo: corrigir um fator)
    posto = 2
    fator_correcao = 1.05  # Aumentar 5%
    
    vazoes.vazoes[posto] = (vazoes.vazoes[posto] * fator_correcao).astype(int)
    print(f"Vazões do posto {posto} corrigidas com fator {fator_correcao}")
    
    # Salvar alterações
    # Nota: A biblioteca atualiza os registros internos antes de gravar
    vazoes.write("vazoes.dat")
```

#### 4.11. Exportação para Análise

```python
from inewave.newave import Vazoes

vazoes = Vazoes.read("vazoes.dat")

if vazoes.vazoes is not None:
    # Exportar vazões de postos específicos para CSV
    postos_selecionados = [1, 2, 3, 4, 5]
    
    vazoes_selecionadas = vazoes.vazoes[postos_selecionados]
    vazoes_selecionadas.to_csv("vazoes_postos_selecionados.csv")
    
    print(f"Vazões dos postos {postos_selecionados} exportadas para CSV")
    
    # Exportar vazões de um período específico
    periodo = vazoes.vazoes.iloc[0:12]  # Primeiros 12 meses
    periodo.to_csv("vazoes_primeiro_ano.csv")
    
    print("Vazões do primeiro ano exportadas para CSV")
```

---

### 5. Observações Importantes

1. **Arquivo binário**: O `VAZOES.DAT` é um arquivo binário de acesso direto, diferente dos outros arquivos NEWAVE que são texto formatado

2. **Responsabilidade do ONS**: Este arquivo é de responsabilidade do ONS e não deve ser alterado pelo usuário, exceto em casos específicos de estudos

3. **Número de postos**: O arquivo contém **320 ou 600 postos**, conforme definido no registro 21 do `dger.dat`

4. **Estrutura do DataFrame**: 
   - Cada **linha** representa um **mês** do histórico (ordenado cronologicamente)
   - Cada **coluna** representa um **posto** de vazões (numerado de 1 a N)
   - Cada **célula** contém a **vazão** (int) daquele posto naquele mês

5. **Ano inicial**: O ano inicial do histórico é definido no registro 21 do `dger.dat`

6. **Relação com POSTOS.DAT**: 
   - O arquivo `POSTOS.DAT` contém informações sobre cada posto (nome, anos inicial e final)
   - Se os campos 9 e 10 do `CONFHD.DAT` não forem fornecidos, os valores são lidos do `POSTOS.DAT`

7. **Uso no modelo**: 
   - As vazões históricas são usadas para construir séries históricas de ENAs (Energias Naturais Afluentes)
   - As ENAs são utilizadas para ajuste do modelo estocástico PAR(p)
   - O modelo PAR(p) gera séries sintéticas de energia para as simulações

8. **Tendência hidrológica**: 
   - A tendência hidrológica pode ser lida por posto ou por REE
   - A escolha é feita através do registro 34 do `dger.dat`

9. **Relação com HIDR.DAT e CONFHD.DAT**: 
   - Cada usina no `HIDR.DAT` e `CONFHD.DAT` está associada a um posto de vazões
   - O campo 3 do `CONFHD.DAT` referencia o posto no `VAZOES.DAT`

10. **Unidade de medida**: 
    - As vazões são armazenadas como inteiros
    - A unidade típica é m³/s, mas pode variar conforme a configuração do modelo

11. **DataFrame pandas**: 
    - A propriedade `vazoes` retorna um DataFrame do pandas
    - Permite uso completo das funcionalidades do pandas para análise e manipulação
    - As colunas são numeradas de 1 a N (número de postos)

12. **Gravação**: 
    - Ao modificar o DataFrame e gravar, a biblioteca atualiza automaticamente os registros binários
    - Use com cuidado, pois o arquivo é de responsabilidade do ONS

13. **Dependências**: 
    - O número de postos (320 ou 600) deve estar consistente com o registro 21 do `dger.dat`
    - Os postos referenciados no `CONFHD.DAT` devem existir no `VAZOES.DAT`
    - O ano inicial deve estar definido no `dger.dat`

14. **Análise de dados**: 
    - É importante validar que não há valores negativos
    - Valores zero podem indicar postos não utilizados ou problemas nos dados
    - Valores muito altos podem indicar erros de dados

15. **Limitação de exibição**: 
    - Devido ao grande volume de dados (muitos meses × muitos postos), é recomendado limitar a exibição
    - Use filtragem e agregação para análises específicas

---

## EXPH.DAT

### 1. Informações do Arquivo

#### 1.1. Nome e Descrição

- **Nome do arquivo**: `exph.dat` ou `EXPH.DAT`
- **Tipo**: Arquivo de entrada do modelo NEWAVE
- **Função**: Contém o cronograma de expansão das usinas hidroelétricas, detalhando a adição de novas máquinas e o enchimento do volume morto de reservatórios

#### 1.2. Função e Conteúdo Principal

O `EXPH.DAT` detalha:
- A adição de novas máquinas às usinas hidrelétricas
- O enchimento do volume morto de reservatórios novos ou existentes em expansão

**Estrutura:**
- O arquivo é iniciado por **três registros obrigatórios destinados a comentários**, que são ignorados pelo programa e servem apenas para orientação do usuário
- O arquivo pode ser composto por **até dois tipos de registros** para cada usina
- O campo 1 deve ser preenchido com o valor **`9999`** ao final do cronograma de expansão de cada usina hidroelétrica

#### 1.3. Registro Tipo 1: Enchimento de Volume Morto

O Registro Tipo 1 é informado apenas uma vez por usina e detalha o enchimento do volume morto:

| Campo | Colunas | Formato | Descrição |
| :--- | :--- | :--- | :--- |
| 1 | 1 a 4 | I4 | **Código da usina** no cadastro de usinas |
| 2 | 6 a 17 | A | **Nome da usina** |
| 3 | 19 a 20 | I2 | **Mês de início** do enchimento de volume morto |
| 4 | 22 a 25 | I4 | **Ano de início** do enchimento de volume morto |
| 5 | 32 a 33 | I2 | **Duração** do enchimento de volume morto, em meses |
| 6 | 38 a 42 | F5.1 | **Percentual do volume morto já preenchido** até a data de início informada |

**Observações:**
- Se o valor percentual inicial (Campo 6) não for fornecido, ele será considerado nulo
- Este registro é opcional e só é necessário se houver enchimento de volume morto

#### 1.4. Registro Tipo 2: Entrada em Operação de Unidades

O Registro Tipo 2 detalha a entrada em operação de cada unidade hidroelétrica adicionada. Se forem necessários os dois tipos de registro para uma usina, não há necessidade de repetir o código e o nome da usina no Registro Tipo 2.

| Campo | Colunas | Formato | Descrição |
| :--- | :--- | :--- | :--- |
| 1 | 1 a 4 | I4 | **Código da usina** no cadastro de usinas |
| 2 | 6 a 17 | A | **Nome da usina** |
| 3 | 45 a 46 | I2 | **Mês de entrada em operação** da unidade |
| 4 | 48 a 51 | I4 | **Ano de entrada em operação** da unidade hidroelétrica |
| 5 | 61 a 62 | I2 | **Número da unidade** a ser adicionada |
| 6 | 65 | I1 | **Número do conjunto** da unidade a ser adicionada |

**Observações:**
- O número do conjunto da unidade (Campo 6) deve ser, no máximo, igual ao número de conjuntos de máquinas informados no arquivo de dados das usinas hidroelétricas (`hidr.dat`)
- Pode haver múltiplos registros Tipo 2 para a mesma usina (uma para cada unidade a ser adicionada)

#### 1.5. Regras e Compatibilidade

**Validação da Expansão:**
- Deve-se incluir uma crítica no arquivo de expansão hidráulica se uma máquina for inserida com número maior do que o número máximo de máquinas suportado pelo conjunto de máquinas

**Conversor de Arquivo:**
- A partir da versão 16.6 do NEWAVE, houve uma modificação no formato de entrada do `EXPH.DAT` (o campo "potência", informado anteriormente, não é mais utilizado)
- Foi desenvolvido um programa de conversão (`convertexphxxxx`) para facilitar a compatibilização de arquivos antigos
- O conversor aloca as máquinas no primeiro conjunto disponível até atingir o limite, e depois passa para o próximo conjunto
- É recomendado que o usuário **verifique o cronograma** no novo arquivo de expansão após a conversão, pois a premissa pode não corresponder ao cronograma de entrada original

**Usinas em Expansão:**
- As usinas hidroelétricas em expansão devem ter o campo `Indicador de status da usina` preenchido como `EE` (existente com expansão) ou `NE` (não existente) no arquivo de configuração hidroelétrica (`CONFHD.DAT`)

**Dados e Tempo:**
- Os dados no `EXPH.DAT` especificam o cronograma de expansão, que é utilizado para acrescentar novas máquinas à configuração inicial das usinas

**Período de Estudo:**
- As datas de entrada das máquinas não devem ser anteriores ao início do estudo
- Em casos de simulação final com data, se o estudo tiver período estático inicial, a funcionalidade deve ser ajustada

---

### 2. Propriedades da Biblioteca inewave

#### 2.1. Classe Correspondente

**Classe**: `Exph`

```python
class Exph(data=<cfinterface.data.sectiondata.SectionData object>)
```

**Descrição**: Armazena os dados de entrada do NEWAVE referentes à expansão hidráulica do sistema.

#### 2.2. Propriedades Disponíveis

##### `property` **expansoes**: `pd.DataFrame | None`

- **Descrição**: A tabela de expansões de máquinas das UHEs
- **Tipo de retorno**: `pd.DataFrame | None`
- **Colunas do DataFrame**:
  - `codigo_usina` (`int`): Código da usina no cadastro de usinas (corresponde ao campo 1 de ambos os tipos de registro)
  - `nome_usina` (`str`): Nome da usina (corresponde ao campo 2 de ambos os tipos de registro)
  - `data_inicio_enchimento` (`datetime`): Data de início do enchimento de volume morto (combinação dos campos 3 e 4 do Registro Tipo 1: mês e ano de início). Pode ser `None` se não houver enchimento
  - `duracao_enchimento` (`int`): Duração do enchimento de volume morto em meses (corresponde ao campo 5 do Registro Tipo 1). Pode ser `None` se não houver enchimento
  - `volume_morto` (`float`): Percentual do volume morto já preenchido até a data de início (corresponde ao campo 6 do Registro Tipo 1). Pode ser `None` se não fornecido
  - `data_entrada_operacao` (`datetime`): Data de entrada em operação da unidade (combinação dos campos 3 e 4 do Registro Tipo 2: mês e ano de entrada). Pode ser `None` se não houver entrada de unidade
  - `potencia_instalada` (`float`): Potência instalada da unidade (campo não mais utilizado a partir da versão 16.6, mas mantido para compatibilidade). Pode ser `None`
  - `maquina_entrada` (`int`): Número da unidade a ser adicionada (corresponde ao campo 5 do Registro Tipo 2). Pode ser `None` se não houver entrada de unidade
  - `conjunto_maquina_entrada` (`int`): Número do conjunto da unidade a ser adicionada (corresponde ao campo 6 do Registro Tipo 2). Pode ser `None` se não houver entrada de unidade

**Observações:**
- Cada linha pode representar:
  - Um registro de enchimento de volume morto (Registro Tipo 1): campos de enchimento preenchidos, campos de entrada de operação vazios
  - Um registro de entrada em operação (Registro Tipo 2): campos de entrada de operação preenchidos, campos de enchimento podem estar vazios
  - Ambos os tipos de informação para a mesma usina: alguns campos preenchidos, outros vazios
- A biblioteca combina os dois tipos de registros em um único DataFrame
- Campos opcionais podem ser `None` ou `NaN` dependendo do tipo de registro
- Se o arquivo não existir ou estiver vazio, a propriedade retorna `None`

---

### 3. Mapeamento de Campos

#### 3.1. Registro Tipo 1 → Propriedade `expansoes`

| Campo do Arquivo | Colunas | Formato | Coluna DataFrame | Tipo Python | Descrição |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Código da usina | 1-4 | I4 | `codigo_usina` | `int` | Identificador da usina |
| Nome da usina | 6-17 | A | `nome_usina` | `str` | Nome da usina |
| Mês de início | 19-20 | I2 | (parte de `data_inicio_enchimento`) | `datetime.month` | Mês de início do enchimento |
| Ano de início | 22-25 | I4 | (parte de `data_inicio_enchimento`) | `datetime.year` | Ano de início do enchimento |
| Duração | 32-33 | I2 | `duracao_enchimento` | `int` | Duração em meses |
| Percentual volume morto | 38-42 | F5.1 | `volume_morto` | `float` | Percentual já preenchido |

#### 3.2. Registro Tipo 2 → Propriedade `expansoes`

| Campo do Arquivo | Colunas | Formato | Coluna DataFrame | Tipo Python | Descrição |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Código da usina | 1-4 | I4 | `codigo_usina` | `int` | Identificador da usina |
| Nome da usina | 6-17 | A | `nome_usina` | `str` | Nome da usina |
| Mês de entrada | 45-46 | I2 | (parte de `data_entrada_operacao`) | `datetime.month` | Mês de entrada em operação |
| Ano de entrada | 48-51 | I4 | (parte de `data_entrada_operacao`) | `datetime.year` | Ano de entrada em operação |
| Número da unidade | 61-62 | I2 | `maquina_entrada` | `int` | Número da unidade |
| Número do conjunto | 65 | I1 | `conjunto_maquina_entrada` | `int` | Número do conjunto |

**Observação**: A biblioteca inewave combina os dois tipos de registros em um único DataFrame. Uma linha pode conter informações de enchimento, entrada em operação, ou ambos, dependendo dos registros presentes no arquivo.

---

### 4. Exemplos de Uso

#### 4.1. Leitura do Arquivo

```python
from inewave.newave import Exph

# Ler o arquivo exph.dat
exph = Exph.read("exph.dat")

# Acessar a tabela de expansões
df_expansoes = exph.expansoes

if df_expansoes is not None:
    print(f"Total de registros de expansão: {len(df_expansoes)}")
    print(df_expansoes.head())
else:
    print("Nenhuma expansão encontrada ou arquivo vazio")
```

#### 4.2. Consulta de Expansões por Usina

```python
from inewave.newave import Exph

exph = Exph.read("exph.dat")

if exph.expansoes is not None:
    # Filtrar expansões de uma usina específica
    codigo_usina = 1
    expansoes_usina = exph.expansoes[
        exph.expansoes['codigo_usina'] == codigo_usina
    ]
    
    print(f"Expansões da usina {codigo_usina}:")
    print(expansoes_usina)
```

#### 4.3. Consulta de Enchimento de Volume Morto

```python
from inewave.newave import Exph

exph = Exph.read("exph.dat")

if exph.expansoes is not None:
    # Filtrar registros com enchimento de volume morto
    enchimentos = exph.expansoes[
        exph.expansoes['data_inicio_enchimento'].notna()
    ]
    
    print(f"Usinas com enchimento de volume morto: {len(enchimentos)}")
    print("\nEnchimentos:")
    print(enchimentos[['codigo_usina', 'nome_usina', 'data_inicio_enchimento', 
                       'duracao_enchimento', 'volume_morto']])
```

#### 4.4. Consulta de Entrada em Operação de Unidades

```python
from inewave.newave import Exph

exph = Exph.read("exph.dat")

if exph.expansoes is not None:
    # Filtrar registros com entrada em operação
    entradas_operacao = exph.expansoes[
        exph.expansoes['data_entrada_operacao'].notna()
    ]
    
    print(f"Unidades com entrada em operação: {len(entradas_operacao)}")
    print("\nEntradas em operação:")
    print(entradas_operacao[['codigo_usina', 'nome_usina', 'data_entrada_operacao',
                             'maquina_entrada', 'conjunto_maquina_entrada']])
```

#### 4.5. Análise de Cronograma de Expansão

```python
from inewave.newave import Exph
from datetime import datetime

exph = Exph.read("exph.dat")

if exph.expansoes is not None:
    # Análise de entradas em operação por período
    entradas = exph.expansoes[exph.expansoes['data_entrada_operacao'].notna()]
    
    if not entradas.empty:
        # Agrupar por ano
        entradas['ano'] = entradas['data_entrada_operacao'].dt.year
        entradas_por_ano = entradas.groupby('ano').size()
        
        print("Unidades entrando em operação por ano:")
        print(entradas_por_ano)
        
        # Análise por usina
        unidades_por_usina = entradas.groupby('nome_usina').agg({
            'maquina_entrada': 'count',
            'data_entrada_operacao': ['min', 'max']
        })
        
        print("\nUnidades por usina:")
        print(unidades_por_usina)
```

#### 4.6. Consulta por Período

```python
from inewave.newave import Exph
from datetime import datetime

exph = Exph.read("exph.dat")

if exph.expansoes is not None:
    # Filtrar expansões em um período específico
    data_inicio = datetime(2024, 1, 1)
    data_fim = datetime(2025, 12, 31)
    
    # Expansões com entrada em operação no período
    entradas_periodo = exph.expansoes[
        (exph.expansoes['data_entrada_operacao'].notna()) &
        (exph.expansoes['data_entrada_operacao'] >= data_inicio) &
        (exph.expansoes['data_entrada_operacao'] <= data_fim)
    ]
    
    print(f"Expansões com entrada em operação no período {data_inicio.date()} a {data_fim.date()}:")
    print(entradas_periodo[['nome_usina', 'data_entrada_operacao', 'maquina_entrada']])
```

#### 4.7. Análise de Enchimento de Volume Morto

```python
from inewave.newave import Exph

exph = Exph.read("exph.dat")

if exph.expansoes is not None:
    # Filtrar enchimentos
    enchimentos = exph.expansoes[
        exph.expansoes['data_inicio_enchimento'].notna()
    ]
    
    if not enchimentos.empty:
        print("Análise de enchimento de volume morto:")
        print(f"Total de usinas com enchimento: {enchimentos['codigo_usina'].nunique()}")
        
        # Estatísticas de duração
        print("\nEstatísticas de duração do enchimento:")
        print(enchimentos['duracao_enchimento'].describe())
        
        # Estatísticas de percentual inicial
        if enchimentos['volume_morto'].notna().any():
            print("\nEstatísticas de percentual inicial de volume morto:")
            print(enchimentos['volume_morto'].describe())
```

#### 4.8. Consulta de Unidades por Conjunto

```python
from inewave.newave import Exph

exph = Exph.read("exph.dat")

if exph.expansoes is not None:
    # Filtrar entradas em operação
    entradas = exph.expansoes[
        exph.expansoes['conjunto_maquina_entrada'].notna()
    ]
    
    if not entradas.empty:
        # Agrupar por conjunto
        unidades_por_conjunto = entradas.groupby('conjunto_maquina_entrada').agg({
            'maquina_entrada': 'count',
            'codigo_usina': 'nunique'
        })
        
        unidades_por_conjunto.columns = ['total_unidades', 'total_usinas']
        
        print("Unidades entrando em operação por conjunto:")
        print(unidades_por_conjunto)
```

#### 4.9. Validação de Dados

```python
from inewave.newave import Exph

exph = Exph.read("exph.dat")

if exph.expansoes is not None:
    df_expansoes = exph.expansoes
    
    # Verificar se há dados
    if len(df_expansoes) == 0:
        print("⚠️ Nenhuma expansão encontrada no arquivo")
    
    # Verificar campos obrigatórios
    campos_obrigatorios = ['codigo_usina', 'nome_usina']
    campos_faltando = [campo for campo in campos_obrigatorios if campo not in df_expansoes.columns]
    
    if campos_faltando:
        print(f"⚠️ Campos faltando: {campos_faltando}")
    
    # Verificar se há registros com ambos os tipos de informação
    registros_completos = df_expansoes[
        df_expansoes['data_inicio_enchimento'].notna() &
        df_expansoes['data_entrada_operacao'].notna()
    ]
    
    if len(registros_completos) > 0:
        print(f"ℹ️ {len(registros_completos)} registros com ambos enchimento e entrada em operação")
    
    # Verificar número de conjunto válido (1-5, baseado em HIDR.DAT)
    if 'conjunto_maquina_entrada' in df_expansoes.columns:
        conjuntos_invalidos = df_expansoes[
            (df_expansoes['conjunto_maquina_entrada'].notna()) &
            ((df_expansoes['conjunto_maquina_entrada'] < 1) |
             (df_expansoes['conjunto_maquina_entrada'] > 5))
        ]
        
        if len(conjuntos_invalidos) > 0:
            print(f"⚠️ {len(conjuntos_invalidos)} registros com número de conjunto inválido (deve ser 1-5)")
    
    # Verificar duração de enchimento positiva
    if 'duracao_enchimento' in df_expansoes.columns:
        duracao_invalida = df_expansoes[
            (df_expansoes['duracao_enchimento'].notna()) &
            (df_expansoes['duracao_enchimento'] <= 0)
        ]
        
        if len(duracao_invalida) > 0:
            print(f"⚠️ {len(duracao_invalida)} registros com duração de enchimento inválida")
    
    # Verificar percentual de volume morto válido (0-100%)
    if 'volume_morto' in df_expansoes.columns:
        volume_invalido = df_expansoes[
            (df_expansoes['volume_morto'].notna()) &
            ((df_expansoes['volume_morto'] < 0) |
             (df_expansoes['volume_morto'] > 100))
        ]
        
        if len(volume_invalido) > 0:
            print(f"⚠️ {len(volume_invalido)} registros com percentual de volume morto inválido (deve ser 0-100%)")
```

#### 4.10. Modificação e Gravação

```python
from inewave.newave import Exph
from datetime import datetime

# Ler o arquivo
exph = Exph.read("exph.dat")

if exph.expansoes is not None:
    # Modificar data de entrada em operação de uma unidade
    codigo_usina = 1
    maquina = 1
    
    mask = (
        (exph.expansoes['codigo_usina'] == codigo_usina) &
        (exph.expansoes['maquina_entrada'] == maquina)
    )
    
    if mask.any():
        nova_data = datetime(2025, 6, 1)
        exph.expansoes.loc[mask, 'data_entrada_operacao'] = nova_data
        print(f"Data de entrada da máquina {maquina} da usina {codigo_usina} atualizada para {nova_data.date()}")
    
    # Modificar duração de enchimento
    mask_enchimento = (
        (exph.expansoes['codigo_usina'] == codigo_usina) &
        (exph.expansoes['data_inicio_enchimento'].notna())
    )
    
    if mask_enchimento.any():
        nova_duracao = 24  # meses
        exph.expansoes.loc[mask_enchimento, 'duracao_enchimento'] = nova_duracao
        print(f"Duração de enchimento da usina {codigo_usina} atualizada para {nova_duracao} meses")
    
    # Salvar alterações
    exph.write("exph.dat")
```

#### 4.11. Análise de Expansões por Status

```python
from inewave.newave import Exph
from inewave.newave import Confhd

exph = Exph.read("exph.dat")
confhd = Confhd.read("confhd.dat")

if exph.expansoes is not None and confhd.usinas is not None:
    # Verificar se as usinas em expansão têm status correto (EE ou NE)
    codigos_expansao = set(exph.expansoes['codigo_usina'].unique())
    
    usinas_expansao_confhd = confhd.usinas[
        confhd.usinas['codigo_usina'].isin(codigos_expansao)
    ]
    
    status_validos = ['EE', 'NE']
    status_invalidos = usinas_expansao_confhd[
        ~usinas_expansao_confhd['usina_existente'].isin(status_validos)
    ]
    
    if len(status_invalidos) > 0:
        print(f"⚠️ {len(status_invalidos)} usinas em expansão com status inválido:")
        print(status_invalidos[['codigo_usina', 'nome_usina', 'usina_existente']])
        print("\nStatus deve ser 'EE' (existente com expansão) ou 'NE' (não existente)")
    else:
        print("✅ Todas as usinas em expansão têm status válido (EE ou NE)")
```

---

### 5. Observações Importantes

1. **Dois tipos de registros**: O arquivo pode conter dois tipos de registros:
   - **Registro Tipo 1**: Enchimento de volume morto (opcional, uma vez por usina)
   - **Registro Tipo 2**: Entrada em operação de unidades (pode haver múltiplos por usina)

2. **Fim de bloco**: O campo 1 deve ser preenchido com **`9999`** ao final do cronograma de expansão de cada usina

3. **Status da usina**: 
   - Usinas em expansão devem ter status `EE` (existente com expansão) ou `NE` (não existente) no `CONFHD.DAT`
   - Usinas com status `EX` (existente) ou `NC` (não considerada) não devem ter expansões

4. **Número do conjunto**: 
   - O número do conjunto da unidade deve ser, no máximo, igual ao número de conjuntos de máquinas informados no `HIDR.DAT`
   - Valores típicos: 1 a 5

5. **Validação**: 
   - Deve-se validar se o número da máquina não excede o número máximo de máquinas suportado pelo conjunto
   - A validação completa requer consulta ao arquivo `HIDR.DAT`

6. **Conversor de arquivo**: 
   - A partir da versão 16.6 do NEWAVE, o campo "potência" não é mais utilizado
   - Existe um conversor (`convertexphxxxx`) para arquivos antigos
   - O conversor aloca máquinas automaticamente, mas é recomendado verificar o resultado

7. **Datas**: 
   - As datas de entrada das máquinas não devem ser anteriores ao início do estudo
   - Em simulações finais com período estático inicial, a funcionalidade deve ser ajustada

8. **Estrutura de dados**: 
   - A biblioteca combina os dois tipos de registros em um único DataFrame
   - Campos opcionais podem ser `None` ou `NaN` dependendo do tipo de registro
   - Uma linha pode conter informações de enchimento, entrada em operação, ou ambos

9. **Percentual de volume morto**: 
   - O campo `volume_morto` representa o percentual já preenchido até a data de início
   - Se não fornecido, será considerado nulo
   - Valores válidos: 0-100%

10. **Duração de enchimento**: 
    - Expressa em meses
    - Deve ser um valor positivo

11. **Comentários**: Os três registros de comentário no início do arquivo são obrigatórios mas ignorados pelo programa

12. **DataFrame pandas**: A propriedade `expansoes` retorna um DataFrame do pandas, permitindo uso completo das funcionalidades do pandas para análise e manipulação

13. **Dependências**: 
    - Os códigos de usina devem estar no cadastro (`HIDR.DAT` e `CONFHD.DAT`)
    - O número de conjuntos deve ser compatível com o `HIDR.DAT`
    - O status da usina deve ser `EE` ou `NE` no `CONFHD.DAT`

14. **Campo potência**: 
    - O campo `potencia_instalada` não é mais utilizado a partir da versão 16.6
    - Mantido no DataFrame para compatibilidade, mas pode estar vazio ou com valores antigos

15. **Múltiplas unidades**: 
    - Uma usina pode ter múltiplas unidades entrando em operação
    - Cada unidade deve ter seu próprio registro Tipo 2

---

## EXPT.DAT

### 1. Informações do Arquivo

#### 1.1. Nome e Descrição

- **Nome do arquivo**: `expt.dat` ou `EXPT.DAT`
- **Tipo**: Arquivo de entrada do modelo NEWAVE
- **Função**: Permite fornecer informações sobre a **expansão e/ou modificação** das usinas termoelétricas ao longo do horizonte de estudo

#### 1.2. Função e Estrutura Geral

**Propósito:**
- O `EXPT.DAT` é composto por registros que detalham modificações nas usinas termoelétricas que possuem o campo 4 do arquivo de configuração termoelétrica (`conft.dat`) preenchido com valor nulo, indicando expansão ou alteração
- As alterações definidas neste arquivo são válidas somente para **alguns meses do período de estudo**, diferentemente das alterações feitas no arquivo de dados das usinas termoelétricas (`term.dat`)

**Comentários Iniciais:**
- O arquivo começa com um **conjunto de dois registros destinados a comentários**, que são obrigatórios, mas ignorados pelo programa, servindo para orientar o usuário

**Hierarquia de Dados:**
- Se a usina térmica tem status `EE` (existente com expansão) ou `NE` (não existente com expansão) no `conft.dat`:
  - A potência efetiva e a geração mínima serão **zero** para os períodos não declarados no `EXPT.DAT`
  - O fator de capacidade máximo e a taxa de indisponibilidade programada serão iguais aos valores do `term.dat` para os períodos não declarados no `EXPT.DAT`

#### 1.3. Formato dos Registros

Cada registro no `EXPT.DAT` é composto por 7 campos, detalhando uma modificação específica:

| Campo | Colunas | Formato | Descrição |
| :--- | :--- | :--- | :--- |
| 1 | 1 a 4 | I4 | **Número da usina térmica** |
| 2 | 6 a 10 | A5 | **Tipo de modificação** (palavras-chave) |
| 3 | 12 a 19 | F8.2 | **Novo valor** da característica modificada |
| 4 | 21 a 22 | I2 | **Mês de início** da modificação |
| 5 | 24 a 27 | I4 | **Ano de início** da modificação |
| 6 | 29 a 30 | I2 | **Mês de fim** da modificação |
| 7 | 32 a 35 | I4 | **Ano de fim** da modificação |

#### 1.4. Tipos de Modificações Suportadas

O campo 2 (Tipo de modificação) aceita as seguintes palavras-chave:

| Palavra-chave | Descrição | Unidade |
| :--- | :--- | :--- |
| **GTMIN** | Geração térmica mínima | MW |
| **POTEF** | Potência efetiva | MW |
| **FCMAX** | Fator de capacidade máximo | % |
| **IPTER** | Indisponibilidade programada | % |
| **TEIFT** | Taxa Equivalente de Indisponibilidade Forçada | % |

**Observações:**
- As palavras-chave são case-sensitive e devem ser escritas exatamente como mostrado
- Cada registro modifica apenas uma característica por vez
- Uma mesma usina pode ter múltiplos registros para diferentes tipos de modificação ou períodos diferentes

#### 1.5. Regras de Preenchimento e Modificações

**Duração da Modificação:**
- Não é obrigatório o preenchimento dos campos 6 e 7 (mês e ano de fim) se a alteração for válida **até o final do período de estudo**
- Se os campos de fim não forem preenchidos, a modificação será válida até o final do horizonte de planejamento

**Regras de Consistência:**

1. **Desativação de Térmica:**
   - Pode ser feita alterando o valor de potência efetiva (`POTEF`) para zero
   - Ou alterando o valor do fator de capacidade máximo (`FCMAX`) para zero

2. **Repotenciação:**
   - Pode ser feita alterando o valor da potência efetiva (`POTEF`)

3. **Geração Mínima vs. Máxima:**
   - A geração térmica mínima (`GTMIN`) deve ser sempre **menor ou igual** à geração térmica máxima

4. **Validação de Datas:**
   - Desde a Versão 27.4.6, o programa passou a verificar as datas de início e fim das modificações
   - Alerta sobre datas finais anteriores às iniciais

5. **CVU Variável:**
   - O custo unitário variável (CVU) das classes térmicas também pode ser representado com valores variáveis por estágio

**Aplicação Temporal:**
- As modificações são aplicadas apenas no período especificado (entre data_inicio e data_fim)
- Fora desse período, os valores padrão do `term.dat` são utilizados
- Para usinas com status `EE` ou `NE`, valores não declarados no `EXPT.DAT` assumem zero para potência efetiva e geração mínima

---

### 2. Propriedades da Biblioteca inewave

#### 2.1. Classe Correspondente

**Classe**: `Expt`

```python
class Expt(data=<cfinterface.data.sectiondata.SectionData object>)
```

**Descrição**: Armazena os dados de entrada do NEWAVE referentes à expansão térmica do sistema.

#### 2.2. Propriedades Disponíveis

##### `property` **expansoes**: `pd.DataFrame | None`

- **Descrição**: A tabela de expansões das UTEs (Usinas Termoelétricas)
- **Tipo de retorno**: `pd.DataFrame | None`
- **Colunas do DataFrame**:
  - `codigo_usina` (`int`): Código da usina térmica no cadastro (corresponde ao campo 1 do registro)
  - `tipo` (`str`): Tipo de modificação (corresponde ao campo 2 do registro). Valores possíveis: `GTMIN`, `POTEF`, `FCMAX`, `IPTER`, `TEIFT`
  - `modificacao` (`float`): Novo valor da característica modificada (corresponde ao campo 3 do registro). Unidade depende do tipo de modificação
  - `data_inicio` (`datetime`): Data de início da modificação (combinação dos campos 4 e 5: mês e ano de início)
  - `data_fim` (`datetime`): Data de fim da modificação (combinação dos campos 6 e 7: mês e ano de fim). Pode ser `None` se não especificado (válido até o final do período)
  - `nome_usina` (`str`): Nome da usina térmica

**Observações:**
- Cada linha representa uma modificação específica de uma característica de uma usina em um período determinado
- Uma mesma usina pode ter múltiplas linhas para diferentes tipos de modificação ou períodos diferentes
- O campo `data_fim` pode ser `None` ou `NaT` (Not a Time) se a modificação for válida até o final do período de estudo
- Se o arquivo não existir ou estiver vazio, a propriedade retorna `None`
- Os tipos de modificação são armazenados como strings e devem corresponder exatamente às palavras-chave aceitas pelo NEWAVE

---

### 3. Mapeamento de Campos

#### 3.1. Registro → Propriedade `expansoes`

| Campo do Arquivo | Colunas | Formato | Coluna DataFrame | Tipo Python | Descrição |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Número da usina | 1-4 | I4 | `codigo_usina` | `int` | Identificador da usina térmica |
| Tipo de modificação | 6-10 | A5 | `tipo` | `str` | Palavra-chave da modificação |
| Novo valor | 12-19 | F8.2 | `modificacao` | `float` | Valor da modificação |
| Mês de início | 21-22 | I2 | (parte de `data_inicio`) | `datetime.month` | Mês de início |
| Ano de início | 24-27 | I4 | (parte de `data_inicio`) | `datetime.year` | Ano de início |
| Mês de fim | 29-30 | I2 | (parte de `data_fim`) | `datetime.month` ou `None` | Mês de fim (opcional) |
| Ano de fim | 32-35 | I4 | (parte de `data_fim`) | `datetime.year` ou `None` | Ano de fim (opcional) |
| Nome da usina | 37-76 | A40 | `nome_usina` | `str` | Nome da usina |

**Observação**: A biblioteca inewave lê o nome da usina de uma posição adicional no arquivo (colunas 37-76), que não está explicitamente documentada na estrutura de 7 campos, mas é incluída no DataFrame.

---

### 4. Exemplos de Uso

#### 4.1. Leitura do Arquivo

```python
from inewave.newave import Expt

# Ler o arquivo expt.dat
expt = Expt.read("expt.dat")

# Acessar a tabela de expansões
df_expansoes = expt.expansoes

if df_expansoes is not None:
    print(f"Total de modificações: {len(df_expansoes)}")
    print(df_expansoes.head())
else:
    print("Nenhuma expansão encontrada ou arquivo vazio")
```

#### 4.2. Consulta de Modificações por Usina

```python
from inewave.newave import Expt

expt = Expt.read("expt.dat")

if expt.expansoes is not None:
    # Filtrar modificações de uma usina específica
    codigo_usina = 1
    modificacoes_usina = expt.expansoes[
        expt.expansoes['codigo_usina'] == codigo_usina
    ]
    
    print(f"Modificações da usina {codigo_usina}:")
    print(modificacoes_usina)
```

#### 4.3. Consulta por Tipo de Modificação

```python
from inewave.newave import Expt

expt = Expt.read("expt.dat")

if expt.expansoes is not None:
    # Filtrar por tipo de modificação
    tipo = "POTEF"  # Potência efetiva
    
    modificacoes_tipo = expt.expansoes[
        expt.expansoes['tipo'] == tipo
    ]
    
    print(f"Modificações de {tipo}: {len(modificacoes_tipo)}")
    print("\nDetalhes:")
    print(modificacoes_tipo[['codigo_usina', 'nome_usina', 'modificacao', 
                             'data_inicio', 'data_fim']])
```

#### 4.4. Consulta de Todas as Modificações por Tipo

```python
from inewave.newave import Expt

expt = Expt.read("expt.dat")

if expt.expansoes is not None:
    # Agrupar por tipo de modificação
    tipos_modificacao = expt.expansoes.groupby('tipo').agg({
        'codigo_usina': 'count',
        'modificacao': ['mean', 'min', 'max']
    })
    
    print("Estatísticas por tipo de modificação:")
    print(tipos_modificacao)
    
    # Listar tipos disponíveis
    tipos_disponiveis = expt.expansoes['tipo'].unique()
    print(f"\nTipos de modificação encontrados: {sorted(tipos_disponiveis)}")
```

#### 4.5. Consulta por Período

```python
from inewave.newave import Expt
from datetime import datetime

expt = Expt.read("expt.dat")

if expt.expansoes is not None:
    # Filtrar modificações em um período específico
    data_inicio = datetime(2024, 1, 1)
    data_fim = datetime(2025, 12, 31)
    
    # Modificações que se sobrepõem ao período
    modificacoes_periodo = expt.expansoes[
        (expt.expansoes['data_inicio'] <= data_fim) &
        (
            (expt.expansoes['data_fim'].isna()) |  # Válido até o final
            (expt.expansoes['data_fim'] >= data_inicio)
        )
    ]
    
    print(f"Modificações ativas no período {data_inicio.date()} a {data_fim.date()}:")
    print(modificacoes_periodo[['nome_usina', 'tipo', 'modificacao', 
                                'data_inicio', 'data_fim']])
```

#### 4.6. Análise de Expansões (Potência Efetiva)

```python
from inewave.newave import Expt

expt = Expt.read("expt.dat")

if expt.expansoes is not None:
    # Filtrar apenas modificações de potência efetiva
    potencias = expt.expansoes[expt.expansoes['tipo'] == 'POTEF']
    
    if not potencias.empty:
        print("Análise de modificações de potência efetiva:")
        print(f"Total de modificações: {len(potencias)}")
        print(f"Usinas afetadas: {potencias['codigo_usina'].nunique()}")
        
        # Estatísticas
        print("\nEstatísticas de potência efetiva:")
        print(potencias['modificacao'].describe())
        
        # Agrupar por usina
        potencias_por_usina = potencias.groupby('nome_usina').agg({
            'modificacao': ['sum', 'mean', 'max'],
            'data_inicio': 'min',
            'data_fim': 'max'
        })
        
        print("\nPotência efetiva por usina:")
        print(potencias_por_usina)
```

#### 4.7. Análise de Desativações

```python
from inewave.newave import Expt

expt = Expt.read("expt.dat")

if expt.expansoes is not None:
    # Identificar desativações (potência ou fator de capacidade = 0)
    desativacoes = expt.expansoes[
        (
            (expt.expansoes['tipo'] == 'POTEF') & 
            (expt.expansoes['modificacao'] == 0)
        ) |
        (
            (expt.expansoes['tipo'] == 'FCMAX') & 
            (expt.expansoes['modificacao'] == 0)
        )
    ]
    
    if not desativacoes.empty:
        print(f"Usinas desativadas: {len(desativacoes)}")
        print("\nDetalhes das desativações:")
        print(desativacoes[['nome_usina', 'tipo', 'data_inicio', 'data_fim']])
    else:
        print("Nenhuma desativação encontrada")
```

#### 4.8. Análise de Repotenciações

```python
from inewave.newave import Expt

expt = Expt.read("expt.dat")

if expt.expansoes is not None:
    # Filtrar modificações de potência efetiva (repotenciações)
    repotenciacoes = expt.expansoes[
        (expt.expansoes['tipo'] == 'POTEF') &
        (expt.expansoes['modificacao'] > 0)
    ]
    
    if not repotenciacoes.empty:
        print("Análise de repotenciações:")
        
        # Agrupar por usina e período
        repotenciacoes_por_usina = repotenciacoes.groupby('nome_usina').agg({
            'modificacao': ['count', 'sum', 'mean'],
            'data_inicio': 'min',
            'data_fim': 'max'
        })
        
        print("\nRepotenciações por usina:")
        print(repotenciacoes_por_usina)
        
        # Identificar aumentos significativos (> 10%)
        # Nota: seria necessário comparar com valores do term.dat para calcular percentual
        print("\nRepotenciações (aumento de potência):")
        print(repotenciacoes[['nome_usina', 'modificacao', 'data_inicio', 'data_fim']])
```

#### 4.9. Análise de Indisponibilidades

```python
from inewave.newave import Expt

expt = Expt.read("expt.dat")

if expt.expansoes is not None:
    # Filtrar modificações de indisponibilidade
    indisponibilidades = expt.expansoes[
        expt.expansoes['tipo'].isin(['IPTER', 'TEIFT'])
    ]
    
    if not indisponibilidades.empty:
        print("Análise de indisponibilidades:")
        
        # Separar por tipo
        ipter = indisponibilidades[indisponibilidades['tipo'] == 'IPTER']
        teift = indisponibilidades[indisponibilidades['tipo'] == 'TEIFT']
        
        if not ipter.empty:
            print(f"\nIndisponibilidade Programada (IPTER): {len(ipter)} registros")
            print(ipter['modificacao'].describe())
        
        if not teift.empty:
            print(f"\nTaxa Equivalente de Indisponibilidade Forçada (TEIFT): {len(teift)} registros")
            print(teift['modificacao'].describe())
        
        # Análise por usina
        indisponibilidades_por_usina = indisponibilidades.groupby(['nome_usina', 'tipo']).agg({
            'modificacao': 'mean',
            'data_inicio': 'min',
            'data_fim': 'max'
        })
        
        print("\nIndisponibilidades por usina:")
        print(indisponibilidades_por_usina)
```

#### 4.10. Validação de Dados

```python
from inewave.newave import Expt

expt = Expt.read("expt.dat")

if expt.expansoes is not None:
    df_expansoes = expt.expansoes
    
    # Verificar se há dados
    if len(df_expansoes) == 0:
        print("⚠️ Nenhuma expansão encontrada no arquivo")
    
    # Verificar campos obrigatórios
    campos_obrigatorios = ['codigo_usina', 'tipo', 'modificacao', 'data_inicio']
    campos_faltando = [campo for campo in campos_obrigatorios if campo not in df_expansoes.columns]
    
    if campos_faltando:
        print(f"⚠️ Campos faltando: {campos_faltando}")
    
    # Verificar tipos de modificação válidos
    tipos_validos = ['GTMIN', 'POTEF', 'FCMAX', 'IPTER', 'TEIFT']
    tipos_invalidos = df_expansoes[
        ~df_expansoes['tipo'].isin(tipos_validos)
    ]
    
    if len(tipos_invalidos) > 0:
        print(f"⚠️ {len(tipos_invalidos)} registros com tipo de modificação inválido:")
        print(tipos_invalidos[['codigo_usina', 'tipo']].unique())
        print(f"Tipos válidos: {tipos_validos}")
    
    # Verificar datas (data_fim >= data_inicio)
    datas_invalidas = df_expansoes[
        (df_expansoes['data_fim'].notna()) &
        (df_expansoes['data_fim'] < df_expansoes['data_inicio'])
    ]
    
    if len(datas_invalidas) > 0:
        print(f"⚠️ {len(datas_invalidas)} registros com data de fim anterior à data de início:")
        print(datas_invalidas[['codigo_usina', 'nome_usina', 'data_inicio', 'data_fim']])
    
    # Verificar valores negativos onde não fazem sentido
    # GTMIN, POTEF devem ser >= 0
    valores_negativos = df_expansoes[
        (df_expansoes['tipo'].isin(['GTMIN', 'POTEF'])) &
        (df_expansoes['modificacao'] < 0)
    ]
    
    if len(valores_negativos) > 0:
        print(f"⚠️ {len(valores_negativos)} registros com valores negativos para GTMIN ou POTEF:")
        print(valores_negativos[['codigo_usina', 'tipo', 'modificacao']])
    
    # Verificar percentuais (FCMAX, IPTER, TEIFT devem estar entre 0-100)
    percentuais_invalidos = df_expansoes[
        (df_expansoes['tipo'].isin(['FCMAX', 'IPTER', 'TEIFT'])) &
        ((df_expansoes['modificacao'] < 0) | (df_expansoes['modificacao'] > 100))
    ]
    
    if len(percentuais_invalidos) > 0:
        print(f"⚠️ {len(percentuais_invalidos)} registros com percentuais inválidos (deve ser 0-100%):")
        print(percentuais_invalidos[['codigo_usina', 'tipo', 'modificacao']])
    
    # Verificar se há modificações sem data de fim (válido, mas importante notar)
    sem_data_fim = df_expansoes[df_expansoes['data_fim'].isna()]
    if len(sem_data_fim) > 0:
        print(f"ℹ️ {len(sem_data_fim)} modificações válidas até o final do período de estudo")
```

#### 4.11. Modificação e Gravação

```python
from inewave.newave import Expt
from datetime import datetime

# Ler o arquivo
expt = Expt.read("expt.dat")

if expt.expansoes is not None:
    # Adicionar nova modificação
    nova_modificacao = {
        'codigo_usina': 1,
        'tipo': 'POTEF',
        'modificacao': 500.0,  # MW
        'data_inicio': datetime(2025, 1, 1),
        'data_fim': datetime(2025, 12, 31),
        'nome_usina': 'TermoMacaé'
    }
    
    # Adicionar ao DataFrame
    import pandas as pd
    nova_linha = pd.DataFrame([nova_modificacao])
    expt.expansoes = pd.concat([expt.expansoes, nova_linha], ignore_index=True)
    
    # Modificar valor existente
    codigo_usina = 1
    tipo = 'POTEF'
    
    mask = (
        (expt.expansoes['codigo_usina'] == codigo_usina) &
        (expt.expansoes['tipo'] == tipo)
    )
    
    if mask.any():
        novo_valor = 600.0  # MW
        expt.expansoes.loc[mask, 'modificacao'] = novo_valor
        print(f"Potência efetiva da usina {codigo_usina} atualizada para {novo_valor} MW")
    
    # Remover modificação
    mask_remover = (
        (expt.expansoes['codigo_usina'] == codigo_usina) &
        (expt.expansoes['tipo'] == 'FCMAX')
    )
    
    if mask_remover.any():
        expt.expansoes = expt.expansoes[~mask_remover]
        print(f"Modificações de FCMAX da usina {codigo_usina} removidas")
    
    # Salvar alterações
    expt.write("expt.dat")
```

#### 4.12. Análise Temporal de Modificações

```python
from inewave.newave import Expt

expt = Expt.read("expt.dat")

if expt.expansoes is not None:
    # Análise de modificações por período
    df_expansoes = expt.expansoes.copy()
    
    # Extrair ano de início
    df_expansoes['ano_inicio'] = df_expansoes['data_inicio'].dt.year
    
    # Contar modificações por ano
    modificacoes_por_ano = df_expansoes.groupby('ano_inicio').size()
    
    print("Modificações por ano de início:")
    print(modificacoes_por_ano)
    
    # Análise por tipo e ano
    modificacoes_tipo_ano = df_expansoes.groupby(['tipo', 'ano_inicio']).size().unstack(fill_value=0)
    
    print("\nModificações por tipo e ano:")
    print(modificacoes_tipo_ano)
    
    # Identificar períodos com mais modificações
    periodo_mais_modificacoes = modificacoes_por_ano.idxmax()
    print(f"\nAno com mais modificações: {periodo_mais_modificacoes} ({modificacoes_por_ano[periodo_mais_modificacoes]} modificações)")
```

#### 4.13. Integração com CONFT.DAT

```python
from inewave.newave import Expt
from inewave.newave import Conft

expt = Expt.read("expt.dat")
conft = Conft.read("conft.dat")

if expt.expansoes is not None and conft.usinas is not None:
    # Verificar se as usinas em expansão têm status correto (EE ou NE)
    codigos_expansao = set(expt.expansoes['codigo_usina'].unique())
    
    usinas_expansao_conft = conft.usinas[
        conft.usinas['codigo_usina'].isin(codigos_expansao)
    ]
    
    # Verificar status (deve ser EE ou NE para expansões)
    if 'status' in usinas_expansao_conft.columns:
        status_validos = ['EE', 'NE']
        status_invalidos = usinas_expansao_conft[
            ~usinas_expansao_conft['status'].isin(status_validos)
        ]
        
        if len(status_invalidos) > 0:
            print(f"⚠️ {len(status_invalidos)} usinas em expansão com status inválido:")
            print(status_invalidos[['codigo_usina', 'nome_usina', 'status']])
            print("\nStatus deve ser 'EE' (existente com expansão) ou 'NE' (não existente)")
        else:
            print("✅ Todas as usinas em expansão têm status válido (EE ou NE)")
    
    # Comparar potências efetivas
    if 'potencia_efetiva' in usinas_expansao_conft.columns:
        potencias_expt = expt.expansoes[
            expt.expansoes['tipo'] == 'POTEF'
        ]
        
        if not potencias_expt.empty:
            print("\nComparação de potências efetivas:")
            for _, row in potencias_expt.iterrows():
                codigo = row['codigo_usina']
                valor_expt = row['modificacao']
                
                valor_conft = usinas_expansao_conft[
                    usinas_expansao_conft['codigo_usina'] == codigo
                ]['potencia_efetiva'].values
                
                if len(valor_conft) > 0:
                    print(f"Usina {codigo}: CONFT={valor_conft[0]:.2f} MW, EXPT={valor_expt:.2f} MW")
```

---

### 5. Observações Importantes

1. **Tipos de modificação**: 
   - Apenas 5 tipos são aceitos: `GTMIN`, `POTEF`, `FCMAX`, `IPTER`, `TEIFT`
   - As palavras-chave são case-sensitive e devem ser escritas exatamente como mostrado

2. **Aplicação temporal**: 
   - As modificações são válidas apenas no período especificado (entre `data_inicio` e `data_fim`)
   - Se `data_fim` não for especificada, a modificação é válida até o final do período de estudo

3. **Hierarquia de dados**: 
   - Para usinas com status `EE` ou `NE` no `conft.dat`:
     - Valores não declarados no `EXPT.DAT` assumem **zero** para potência efetiva e geração mínima
     - Fator de capacidade máximo e indisponibilidade programada assumem valores do `term.dat`

4. **Desativação de térmicas**: 
   - Pode ser feita definindo `POTEF = 0` ou `FCMAX = 0`
   - A desativação é válida apenas no período especificado

5. **Repotenciação**: 
   - Feita alterando o valor de `POTEF`
   - Pode ser aplicada em períodos específicos

6. **Validação de consistência**: 
   - Geração mínima (`GTMIN`) deve ser ≤ geração máxima
   - Desde a versão 27.4.6, o programa valida datas (data_fim >= data_inicio)
   - Valores negativos não são permitidos para `GTMIN` e `POTEF`
   - Percentuais (`FCMAX`, `IPTER`, `TEIFT`) devem estar entre 0-100%

7. **Múltiplas modificações**: 
   - Uma mesma usina pode ter múltiplas modificações
   - Diferentes tipos de modificação podem coexistir
   - Modificações do mesmo tipo podem ter períodos diferentes

8. **Comentários iniciais**: 
   - Os dois registros de comentário no início do arquivo são obrigatórios mas ignorados pelo programa

9. **DataFrame pandas**: 
   - A propriedade `expansoes` retorna um DataFrame do pandas, permitindo uso completo das funcionalidades do pandas para análise e manipulação

10. **Dependências**: 
    - Os códigos de usina devem estar no cadastro (`conft.dat` e `term.dat`)
    - O status da usina no `conft.dat` deve ser `EE` ou `NE` para expansões

11. **CVU variável**: 
    - O custo unitário variável (CVU) das classes térmicas também pode ser representado com valores variáveis por estágio
    - Isso é feito através de modificações no `EXPT.DAT`

12. **Unidades**: 
    - `GTMIN`, `POTEF`: MW
    - `FCMAX`, `IPTER`, `TEIFT`: percentual (%)

13. **Formato de data**: 
    - As datas são armazenadas como objetos `datetime` no DataFrame
    - O formato no arquivo é `MM YYYY` (mês e ano separados por espaço)

14. **Valores padrão**: 
    - Para períodos não declarados no `EXPT.DAT`, os valores do `term.dat` são utilizados
    - Exceção: para usinas `EE` ou `NE`, potência efetiva e geração mínima são zero se não declaradas

15. **Validação de datas**: 
    - Desde a versão 27.4.6, o NEWAVE verifica se data_fim >= data_inicio
    - É recomendado validar isso antes de executar o modelo

16. **Campo nome_usina**: 
    - O nome da usina é lido de uma posição adicional no arquivo (colunas 37-76)
    - Este campo não está explicitamente na estrutura de 7 campos, mas é incluído no DataFrame

---

## MODIF.DAT

### 1. Informações do Arquivo

#### 1.1. Nome e Descrição

- **Nome do arquivo**: `modif.dat` ou `MODIF.DAT`
- **Tipo**: Arquivo de entrada do modelo NEWAVE
- **Função**: Permite ao usuário **modificar dados cadastrais** das usinas hidrelétricas em relação ao arquivo de cadastro original (`hidr.dat`)

#### 1.2. Estrutura e Ativação

**Habilitação:**
- O uso deste arquivo é sinalizado pelo **Campo 8** no arquivo de Configuração Hidrelétrica (`confhd.dat`)
- Se esse campo for preenchido com **1**, indica que um conjunto restrito de dados do cadastro será modificado
- Cada usina que terá modificações deve ter o campo 8 (`usina_modificada`) igual a 1 no `CONFHD.DAT`

**Comentários Iniciais:**
- O arquivo deve iniciar-se por **dois registros destinados a comentários**, que são obrigatórios, mas ignorados pelo programa

**Organização:**
- O arquivo é composto por um conjunto de **blocos de dados**, onde cada bloco corresponde a uma usina hidrelétrica que terá seus dados alterados
- Cada bloco de dados de uma usina deve começar obrigatoriamente com a **palavra-chave `USINA`** (em maiúsculas) ou **`usina`** (em minúsculas), seguida do código de identificação da usina no cadastro
- Dentro de cada bloco de usina, o número de registros é variável, sendo que as alterações são identificadas por **palavras-chave** (mnemônicos) que podem ser fornecidas em qualquer ordem

#### 1.3. Formato do Registro USINA

Cada bloco de modificação de uma usina começa com o registro `USINA`:

| Campo | Colunas | Formato | Descrição |
| :--- | :--- | :--- | :--- |
| 1 | 2 a 9 | A8 | **`USINA`** ou `usina` (palavra-chave) |
| 2 | 11 a 30 | Livre | **Código da usina** no cadastro (Inteiro) |
| 3 | 31 a 70 | Livre | **Nome da usina** (opcional, para referência) |

#### 1.4. Formato dos Registros de Modificação

Após o registro `USINA`, seguem os registros de modificação, cada um identificado por uma palavra-chave:

| Campo | Colunas | Formato | Descrição |
| :--- | :--- | :--- | :--- |
| 1 | 2 a 9 | A8 | Palavra-chave que identifica o conteúdo do cadastro a ser modificado |
| 2 | 11 a 70 | Livre | Novos valores a serem considerados, escritos em formato livre |

#### 1.5. Principais Palavras-Chave de Modificação

O arquivo `MODIF.DAT` permite a alteração de diversas características físicas e operacionais das usinas:

| Palavra-chave | Descrição | Conteúdo e Tipo | Unidade |
| :--- | :--- | :--- | :--- |
| **`VOLMIN` / `volmin`** | Volume mínimo operativo | Novo valor e unidade | H/h ou % |
| **`VOLMAX` / `volmax`** | Volume máximo operativo | Novo valor e unidade | H/h ou % |
| **`VMAXT` / `vmaxt`** | Volume máximo, com data | Data (mm aaaa), Novo valor e unidade | H/h ou % |
| **`VMINT` / `vmint`** | Volume mínimo, com data | Data (mm aaaa) e Novo valor e unidade | H/h ou % |
| **`VMINP` / `vminp`** | Volume mínimo com adoção de penalidade, com data | Data (mm aaaa) e Novo valor e unidade | H/h ou % |
| **`VAZMIN` / `vazmin`** | Vazão mínima (m³/s) | Novo valor | m³/s |
| **`VAZMINT` / `vazmint`** | Vazão mínima, com data (m³/s) | Data (mm aaaa) e novo valor | m³/s |
| **`VAZMAXT` / `vazmaxt`** | Vazão máxima, com data | Data (mm aaaa) e novo valor | m³/s |
| **`CFUGA` / `cfuga`** | Canal de fuga (m) | Data (mm aaaa) e novo valor | m |
| **`CMONT` / `cmont`** | Nível de montante (m) | Data (mm aaaa) e novo valor | m |
| **`POTEFE` / `potefe`** | Potência efetiva (MW) | Novo valor e Número do conjunto | MW |
| **`TEIF` / `teif`** | Taxa esperada de indisponibilidade forçada (%) | Novo valor | % |
| **`IP` / `ip`** | Indisponibilidade programada (%) | Novo valor | % |
| **`NUMCNJ` / `numcnj`** | Número de conjuntos de máquinas | Novo valor | Inteiro |
| **`NUMMAQ` / `nummaq`** | Número de máquinas por conjunto | Número do conjunto e novo valor | Inteiro |
| **`TURBMAXT` / `turbmaxt`** | Turbinamento máximo, com data e por patamar | Data (mm aaaa), patamar e valor | m³/s |
| **`TURBMINT` / `turbmint`** | Turbinamento mínimo, com data e por patamar | Data (mm aaaa), patamar e valor | m³/s |
| **`CDESVIO` / `cdesvio`** | Usina a jusante no canal de desvio, com valor de vazão máxima do canal de desvio | Código da usina e novo valor | m³/s |

**Observações:**
- As palavras-chave são case-insensitive (podem ser maiúsculas ou minúsculas)
- Cada palavra-chave pode aparecer múltiplas vezes no mesmo bloco de usina (especialmente as com data)
- As palavras-chave com data permitem modificações temporárias (válidas a partir de uma data específica)

#### 1.6. Regras Específicas de Modificação

1. **Restrições de Volume e Canal de Fuga:**
   - As alterações de volume máximo (`VMAXT`), volume mínimo (`VMINT` e `VMINP`) com data são referenciadas ao **final do período**
   - As alterações de canal de fuga (`CFUGA`) são referenciadas ao **início do período**

2. **Datas nos Períodos Estáticos:**
   - Para a palavra-chave `VAZMINT`, os valores relativos ao período estático inicial (`PRE`) e/ou final (`POS`) podem ser informados, mas serão ignorados se não houver período estático no estudo

3. **Vazão Mínima:**
   - Para a modificação da vazão mínima obrigatória (`VAZMIN` ou `VAZMINT`), é possível informar até dois valores de vazão:
     - O primeiro para o requisito total
     - Um segundo (opcional e que deve ser inferior ao primeiro) para indicar a vazão a partir da qual o requisito pode ser relaxado

4. **Nível de Montante:**
   - As modificações no nível de montante (`CMONT`) são permitidas **somente para usinas consideradas fio d'água**

5. **Volume Mínimo Operativo Penalizado (VMINP):**
   - Esta restrição implementa um mecanismo de aversão a risco
   - O valor a ser considerado para o REE será o mais **restritivo** entre:
     - O valor informado no `MODIF.DAT` por usina
     - Aquele fornecido no arquivo `CURVA.DAT` por REE

6. **Turbinamento/Defluência com Data:**
   - As palavras-chave `TURBMAXT`, `TURBMINT` e `VAZMAXT` (Turbinamento Máximo, Turbinamento Mínimo e Defluência Máxima, respectivamente) com data e por patamar são consideradas apenas em **períodos individualizados**
   - Somente se os *flags* dos campos 87 e 88 do arquivo de dados gerais (`dger.dat`) estiverem habilitados

---

### 2. Propriedades da Biblioteca inewave

#### 2.1. Classe Correspondente

**Classe**: `Modif`

```python
class Modif(data=<cfinterface.data.registerdata.RegisterData object>)
```

**Descrição**: Armazena os dados de entrada do NEWAVE referentes às alterações nas configurações das usinas hidroelétricas.

**Estrutura:**
- A classe `Modif` herda de `RegisterFile`, que gerencia arquivos baseados em registros
- Cada tipo de modificação é representado por uma classe de registro específica
- A biblioteca fornece métodos específicos para acessar cada tipo de modificação

#### 2.2. Métodos Disponíveis

A classe `Modif` não possui uma propriedade única como os outros arquivos. Em vez disso, fornece **métodos específicos** para acessar cada tipo de modificação. Cada método pode retornar:
- Um objeto `Register` (se houver apenas um registro correspondente)
- Uma lista de objetos `Register` (se houver múltiplos registros)
- Um `DataFrame` do pandas (se `df=True` for passado como parâmetro)
- `None` (se não houver registros correspondentes)

##### 2.2.1. Método `usina()`

```python
usina(codigo: int | None = None, nome: str | None = None, df: bool = False) 
    -> USINA | List[USINA] | pd.DataFrame | None
```

- **Descrição**: Obtém um registro que define a usina modificada
- **Parâmetros**:
  - `codigo` (`int | None`): código da usina modificada (filtro opcional)
  - `nome` (`str | None`): nome da usina (filtro opcional)
  - `df` (`bool`): se `True`, retorna um DataFrame em vez de objetos Register
- **Retorna**: Registros `USINA` correspondentes

##### 2.2.2. Método `volmin()`

```python
volmin(volume: float | None = None, unidade: str | None = None, df: bool = False) 
    -> VOLMIN | List[VOLMIN] | pd.DataFrame | None
```

- **Descrição**: Obtém registros que definem volume mínimo operativo
- **Parâmetros**:
  - `volume` (`float | None`): valor do volume mínimo (filtro opcional)
  - `unidade` (`str | None`): unidade do volume ('H/h' ou '%') (filtro opcional)
  - `df` (`bool`): se `True`, retorna um DataFrame
- **Retorna**: Registros `VOLMIN` correspondentes

##### 2.2.3. Método `volmax()`

```python
volmax(volume: float | None = None, unidade: str | None = None, df: bool = False) 
    -> VOLMAX | List[VOLMAX] | pd.DataFrame | None
```

- **Descrição**: Obtém registros que definem volume máximo operativo
- **Parâmetros**: Similar a `volmin()`
- **Retorna**: Registros `VOLMAX` correspondentes

##### 2.2.4. Método `vmaxt()`

```python
vmaxt(data_inicio: datetime | None = None, volume: float | None = None, 
      unidade: str | None = None, df: bool = False) 
    -> VMAXT | List[VMAXT] | pd.DataFrame | None
```

- **Descrição**: Obtém registros que definem volume máximo por período (com data)
- **Parâmetros**:
  - `data_inicio` (`datetime | None`): data de início da validade (filtro opcional)
  - `volume` (`float | None`): valor do volume (filtro opcional)
  - `unidade` (`str | None`): unidade do volume (filtro opcional)
  - `df` (`bool`): se `True`, retorna um DataFrame
- **Retorna**: Registros `VMAXT` correspondentes

##### 2.2.5. Método `vmint()`

```python
vmint(data_inicio: datetime | None = None, volume: float | None = None, 
      unidade: str | None = None, df: bool = False) 
    -> VMINT | List[VMINT] | pd.DataFrame | None
```

- **Descrição**: Obtém registros que definem volume mínimo por período (com data)
- **Parâmetros**: Similar a `vmaxt()`
- **Retorna**: Registros `VMINT` correspondentes

##### 2.2.6. Método `vminp()`

```python
vminp(data_inicio: datetime | None = None, volume: float | None = None, 
      unidade: str | None = None, df: bool = False) 
    -> VMINP | List[VMINP] | pd.DataFrame | None
```

- **Descrição**: Obtém registros que definem volume mínimo para penalidade (com data)
- **Parâmetros**: Similar a `vmaxt()`
- **Retorna**: Registros `VMINP` correspondentes

##### 2.2.7. Método `vazmin()`

```python
vazmin(vazao: float | None = None, df: bool = False) 
    -> VAZMIN | List[VAZMIN] | pd.DataFrame | None
```

- **Descrição**: Obtém registros que definem vazão mínima
- **Parâmetros**:
  - `vazao` (`float | None`): valor da vazão mínima (filtro opcional)
  - `df` (`bool`): se `True`, retorna um DataFrame
- **Retorna**: Registros `VAZMIN` correspondentes

##### 2.2.8. Método `vazmint()`

```python
vazmint(data_inicio: datetime | None = None, vazao: float | None = None, 
        df: bool = False) 
    -> VAZMINT | List[VAZMINT] | pd.DataFrame | None
```

- **Descrição**: Obtém registros que definem vazão mínima por período (com data)
- **Parâmetros**:
  - `data_inicio` (`datetime | None`): data de início da validade (filtro opcional)
  - `vazao` (`float | None`): valor da vazão (filtro opcional)
  - `df` (`bool`): se `True`, retorna um DataFrame
- **Retorna**: Registros `VAZMINT` correspondentes

##### 2.2.9. Método `vazmaxt()`

```python
vazmaxt(data_inicio: datetime | None = None, vazao: float | None = None, 
        df: bool = False) 
    -> VAZMAXT | List[VAZMAXT] | pd.DataFrame | None
```

- **Descrição**: Obtém registros que definem vazão máxima por período (com data)
- **Parâmetros**: Similar a `vazmint()`
- **Retorna**: Registros `VAZMAXT` correspondentes

##### 2.2.10. Método `cfuga()`

```python
cfuga(data_inicio: datetime | None = None, nivel: float | None = None, 
      df: bool = False) 
    -> CFUGA | List[CFUGA] | pd.DataFrame | None
```

- **Descrição**: Obtém registros que definem o nível do canal de fuga
- **Parâmetros**:
  - `data_inicio` (`datetime | None`): data de início da validade (filtro opcional)
  - `nivel` (`float | None`): nível do canal de fuga (filtro opcional)
  - `df` (`bool`): se `True`, retorna um DataFrame
- **Retorna**: Registros `CFUGA` correspondentes

##### 2.2.11. Método `cmont()`

```python
cmont(data_inicio: datetime | None = None, nivel: float | None = None, 
      df: bool = False) 
    -> CMONT | List[CMONT] | pd.DataFrame | None
```

- **Descrição**: Obtém registros que definem o nível do canal de montante
- **Parâmetros**: Similar a `cfuga()`
- **Retorna**: Registros `CMONT` correspondentes

##### 2.2.12. Método `turbmaxt()`

```python
turbmaxt(data_inicio: datetime | None = None, turbinamento: float | None = None, 
         df: bool = False) 
    -> TURBMAXT | List[TURBMAXT] | pd.DataFrame | None
```

- **Descrição**: Obtém registros que definem o turbinamento máximo por período
- **Parâmetros**:
  - `data_inicio` (`datetime | None`): data de início da validade (filtro opcional)
  - `turbinamento` (`float | None`): valor do turbinamento máximo (filtro opcional)
  - `df` (`bool`): se `True`, retorna um DataFrame
- **Retorna**: Registros `TURBMAXT` correspondentes

##### 2.2.13. Método `turbmint()`

```python
turbmint(data_inicio: datetime | None = None, turbinamento: float | None = None, 
         df: bool = False) 
    -> TURBMINT | List[TURBMINT] | pd.DataFrame | None
```

- **Descrição**: Obtém registros que definem o turbinamento mínimo por período
- **Parâmetros**: Similar a `turbmaxt()`
- **Retorna**: Registros `TURBMINT` correspondentes

##### 2.2.14. Método `numcnj()`

```python
numcnj(numero: int | None = None, df: bool = False) 
    -> NUMCNJ | List[NUMCNJ] | pd.DataFrame | None
```

- **Descrição**: Obtém registros que definem o número de conjuntos de máquinas
- **Parâmetros**:
  - `numero` (`int | None`): número de conjuntos (filtro opcional)
  - `df` (`bool`): se `True`, retorna um DataFrame
- **Retorna**: Registros `NUMCNJ` correspondentes

##### 2.2.15. Método `nummaq()`

```python
nummaq(conjunto: int | None = None, numero_maquinas: int | None = None, 
       df: bool = False) 
    -> NUMMAQ | List[NUMMAQ] | pd.DataFrame | None
```

- **Descrição**: Obtém registros que definem o número de máquinas por conjunto
- **Parâmetros**:
  - `conjunto` (`int | None`): número do conjunto (filtro opcional)
  - `numero_maquinas` (`int | None`): número de máquinas (filtro opcional)
  - `df` (`bool`): se `True`, retorna um DataFrame
- **Retorna**: Registros `NUMMAQ` correspondentes

##### 2.2.16. Método `modificacoes_usina()`

```python
modificacoes_usina(codigo: int) -> List[Register] | None
```

- **Descrição**: Filtra os registros que são associados a uma usina específica
- **Parâmetros**:
  - `codigo` (`int`): O código da usina
- **Retorna**: Lista de todos os registros de modificação da usina (todos os tipos)

**Observação**: Este método retorna todos os tipos de modificação para uma usina, não apenas um tipo específico.

---

### 3. Estrutura dos Objetos Register

Cada tipo de modificação é representado por uma classe de registro específica. Estas classes têm propriedades que correspondem aos campos do arquivo:

#### 3.1. Classe USINA

- `codigo` (`int`): Código da usina
- `nome` (`str`): Nome da usina

#### 3.2. Classe VOLMIN / VOLMAX

- `volume` (`float`): Valor do volume
- `unidade` (`str`): Unidade do volume ('H/h' ou '%')

#### 3.3. Classe VMAXT / VMINT / VMINP

- `data_inicio` (`datetime`): Data de início da validade
- `volume` (`float`): Valor do volume
- `unidade` (`str`): Unidade do volume

#### 3.4. Classe VAZMIN

- `vazao` (`float`): Valor da vazão mínima

#### 3.5. Classe VAZMINT / VAZMAXT

- `data_inicio` (`datetime`): Data de início da validade
- `vazao` (`float`): Valor da vazão

#### 3.6. Classe CFUGA / CMONT

- `data_inicio` (`datetime`): Data de início da validade
- `nivel` (`float`): Nível do canal (em metros)

#### 3.7. Classe TURBMAXT / TURBMINT

- `data_inicio` (`datetime`): Data de início da validade
- `patamar` (`int`): Número do patamar
- `turbinamento` (`float`): Valor do turbinamento

#### 3.8. Classe NUMCNJ

- `numero` (`int`): Número de conjuntos de máquinas

#### 3.9. Classe NUMMAQ

- `conjunto` (`int`): Número do conjunto
- `numero_maquinas` (`int`): Número de máquinas

---

### 4. Exemplos de Uso

#### 4.1. Leitura do Arquivo

```python
from inewave.newave import Modif

# Ler o arquivo modif.dat
modif = Modif.read("modif.dat")

# Verificar se há modificações
if modif is not None:
    print("Arquivo MODIF.DAT carregado com sucesso")
else:
    print("Erro ao carregar arquivo ou arquivo vazio")
```

#### 4.2. Listar Todas as Usinas Modificadas

```python
from inewave.newave import Modif

modif = Modif.read("modif.dat")

# Obter todas as usinas modificadas como DataFrame
usinas_df = modif.usina(df=True)

if usinas_df is not None and len(usinas_df) > 0:
    print(f"Total de usinas modificadas: {len(usinas_df)}")
    print(usinas_df)
else:
    print("Nenhuma usina modificada encontrada")
```

#### 4.3. Consultar Modificações de uma Usina Específica

```python
from inewave.newave import Modif

modif = Modif.read("modif.dat")

codigo_usina = 1

# Obter todas as modificações da usina
modificacoes = modif.modificacoes_usina(codigo_usina)

if modificacoes:
    print(f"Modificações da usina {codigo_usina}:")
    for registro in modificacoes:
        print(f"  Tipo: {type(registro).__name__}")
        print(f"  Dados: {registro.data}")
else:
    print(f"Nenhuma modificação encontrada para a usina {codigo_usina}")
```

#### 4.4. Consultar Volume Mínimo

```python
from inewave.newave import Modif

modif = Modif.read("modif.dat")

# Obter todos os registros de volume mínimo
volmin_registros = modif.volmin()

if volmin_registros:
    if isinstance(volmin_registros, list):
        print(f"Total de registros VOLMIN: {len(volmin_registros)}")
        for registro in volmin_registros:
            print(f"  Volume: {registro.volume} {registro.unidade}")
    else:
        print(f"Volume mínimo: {volmin_registros.volume} {volmin_registros.unidade}")

# Como DataFrame
volmin_df = modif.volmin(df=True)
if volmin_df is not None:
    print("\nVolume mínimo como DataFrame:")
    print(volmin_df)
```

#### 4.5. Consultar Volume Máximo com Data

```python
from inewave.newave import Modif
from datetime import datetime

modif = Modif.read("modif.dat")

# Obter todos os registros de volume máximo com data
vmaxt_registros = modif.vmaxt()

if vmaxt_registros:
    if isinstance(vmaxt_registros, list):
        print(f"Total de registros VMAXT: {len(vmaxt_registros)}")
        for registro in vmaxt_registros:
            print(f"  Data: {registro.data_inicio.strftime('%m/%Y')}")
            print(f"  Volume: {registro.volume} {registro.unidade}")
    else:
        print(f"Data: {vmaxt_registros.data_inicio.strftime('%m/%Y')}")
        print(f"Volume: {vmaxt_registros.volume} {vmaxt_registros.unidade}")

# Filtrar por data específica
data_filtro = datetime(2024, 1, 1)
vmaxt_filtrado = modif.vmaxt(data_inicio=data_filtro)
if vmaxt_filtrado:
    print(f"\nVolume máximo a partir de {data_filtro.strftime('%m/%Y')}:")
    print(vmaxt_filtrado)
```

#### 4.6. Consultar Vazão Mínima

```python
from inewave.newave import Modif

modif = Modif.read("modif.dat")

# Obter todos os registros de vazão mínima
vazmin_registros = modif.vazmin()

if vazmin_registros:
    if isinstance(vazmin_registros, list):
        print(f"Total de registros VAZMIN: {len(vazmin_registros)}")
        for registro in vazmin_registros:
            print(f"  Vazão mínima: {registro.vazao} m³/s")
    else:
        print(f"Vazão mínima: {vazmin_registros.vazao} m³/s")

# Como DataFrame
vazmin_df = modif.vazmin(df=True)
if vazmin_df is not None:
    print("\nVazão mínima como DataFrame:")
    print(vazmin_df)
```

#### 4.7. Consultar Vazão Mínima com Data

```python
from inewave.newave import Modif
from datetime import datetime

modif = Modif.read("modif.dat")

# Obter todos os registros de vazão mínima com data
vazmint_registros = modif.vazmint()

if vazmint_registros:
    if isinstance(vazmint_registros, list):
        print(f"Total de registros VAZMINT: {len(vazmint_registros)}")
        for registro in vazmint_registros:
            print(f"  Data: {registro.data_inicio.strftime('%m/%Y')}")
            print(f"  Vazão mínima: {registro.vazao} m³/s")
    else:
        print(f"Data: {vazmint_registros.data_inicio.strftime('%m/%Y')}")
        print(f"Vazão mínima: {vazmint_registros.vazao} m³/s")
```

#### 4.8. Consultar Canal de Fuga

```python
from inewave.newave import Modif

modif = Modif.read("modif.dat")

# Obter todos os registros de canal de fuga
cfuga_registros = modif.cfuga()

if cfuga_registros:
    if isinstance(cfuga_registros, list):
        print(f"Total de registros CFUGA: {len(cfuga_registros)}")
        for registro in cfuga_registros:
            print(f"  Data: {registro.data_inicio.strftime('%m/%Y')}")
            print(f"  Nível: {registro.nivel} m")
    else:
        print(f"Data: {cfuga_registros.data_inicio.strftime('%m/%Y')}")
        print(f"Nível: {cfuga_registros.nivel} m")
```

#### 4.9. Consultar Nível de Montante

```python
from inewave.newave import Modif

modif = Modif.read("modif.dat")

# Obter todos os registros de nível de montante
cmont_registros = modif.cmont()

if cmont_registros:
    if isinstance(cmont_registros, list):
        print(f"Total de registros CMONT: {len(cmont_registros)}")
        for registro in cmont_registros:
            print(f"  Data: {registro.data_inicio.strftime('%m/%Y')}")
            print(f"  Nível: {registro.nivel} m")
    else:
        print(f"Data: {cmont_registros.data_inicio.strftime('%m/%Y')}")
        print(f"Nível: {cmont_registros.nivel} m")
```

#### 4.10. Consultar Turbinamento

```python
from inewave.newave import Modif

modif = Modif.read("modif.dat")

# Obter todos os registros de turbinamento máximo
turbmaxt_registros = modif.turbmaxt()

if turbmaxt_registros:
    if isinstance(turbmaxt_registros, list):
        print(f"Total de registros TURBMAXT: {len(turbmaxt_registros)}")
        for registro in turbmaxt_registros:
            print(f"  Data: {registro.data_inicio.strftime('%m/%Y')}")
            print(f"  Patamar: {registro.patamar}")
            print(f"  Turbinamento máximo: {registro.turbinamento} m³/s")
    else:
        print(f"Data: {turbmaxt_registros.data_inicio.strftime('%m/%Y')}")
        print(f"Patamar: {turbmaxt_registros.patamar}")
        print(f"Turbinamento máximo: {turbmaxt_registros.turbinamento} m³/s")

# Turbinamento mínimo
turbmint_registros = modif.turbmint()
if turbmint_registros:
    print("\nTurbinamento mínimo:")
    if isinstance(turbmint_registros, list):
        for registro in turbmint_registros:
            print(f"  Data: {registro.data_inicio.strftime('%m/%Y')}, "
                  f"Patamar: {registro.patamar}, "
                  f"Turbinamento: {registro.turbinamento} m³/s")
```

#### 4.11. Consultar Número de Conjuntos e Máquinas

```python
from inewave.newave import Modif

modif = Modif.read("modif.dat")

# Obter registros de número de conjuntos
numcnj_registros = modif.numcnj()

if numcnj_registros:
    if isinstance(numcnj_registros, list):
        print(f"Total de registros NUMCNJ: {len(numcnj_registros)}")
        for registro in numcnj_registros:
            print(f"  Número de conjuntos: {registro.numero}")
    else:
        print(f"Número de conjuntos: {numcnj_registros.numero}")

# Obter registros de número de máquinas por conjunto
nummaq_registros = modif.nummaq()

if nummaq_registros:
    if isinstance(nummaq_registros, list):
        print(f"\nTotal de registros NUMMAQ: {len(nummaq_registros)}")
        for registro in nummaq_registros:
            print(f"  Conjunto: {registro.conjunto}, "
                  f"Número de máquinas: {registro.numero_maquinas}")
    else:
        print(f"Conjunto: {nummaq_registros.conjunto}, "
              f"Número de máquinas: {nummaq_registros.numero_maquinas}")
```

#### 4.12. Análise Completa de Modificações por Usina

```python
from inewave.newave import Modif

modif = Modif.read("modif.dat")

# Obter todas as usinas modificadas
usinas = modif.usina(df=True)

if usinas is not None and len(usinas) > 0:
    print("Análise completa de modificações por usina:\n")
    
    for _, usina_row in usinas.iterrows():
        codigo = usina_row['codigo'] if 'codigo' in usina_row else None
        nome = usina_row['nome'] if 'nome' in usina_row else None
        
        if codigo is not None:
            print(f"Usina {codigo} - {nome}:")
            
            # Obter todas as modificações da usina
            modificacoes = modif.modificacoes_usina(codigo)
            
            if modificacoes:
                # Agrupar por tipo
                tipos = {}
                for registro in modificacoes:
                    tipo = type(registro).__name__
                    if tipo not in tipos:
                        tipos[tipo] = []
                    tipos[tipo].append(registro)
                
                for tipo, registros in tipos.items():
                    print(f"  {tipo}: {len(registros)} registro(s)")
                    for registro in registros:
                        # Exibir informações relevantes baseadas no tipo
                        if hasattr(registro, 'volume'):
                            print(f"    Volume: {registro.volume} {getattr(registro, 'unidade', '')}")
                        if hasattr(registro, 'vazao'):
                            print(f"    Vazão: {registro.vazao} m³/s")
                        if hasattr(registro, 'nivel'):
                            print(f"    Nível: {registro.nivel} m")
                        if hasattr(registro, 'data_inicio'):
                            print(f"    Data: {registro.data_inicio.strftime('%m/%Y')}")
            print()
```

#### 4.13. Validação de Dados

```python
from inewave.newave import Modif

modif = Modif.read("modif.dat")

# Verificar se há modificações
usinas = modif.usina(df=True)

if usinas is not None and len(usinas) > 0:
    print(f"✅ {len(usinas)} usina(s) com modificações encontrada(s)")
    
    # Verificar se todas as usinas têm código válido
    codigos_invalidos = usinas[usinas['codigo'].isna() | (usinas['codigo'] <= 0)]
    if len(codigos_invalidos) > 0:
        print(f"⚠️ {len(codigos_invalidos)} usina(s) com código inválido")
    
    # Verificar volumes mínimos e máximos
    volmin_registros = modif.volmin()
    volmax_registros = modif.volmax()
    
    if volmin_registros and volmax_registros:
        # Verificar consistência (volume mínimo < volume máximo)
        # Nota: Esta validação requer conhecimento do contexto da usina
        print("ℹ️ Verifique manualmente se volume mínimo < volume máximo para cada usina")
    
    # Verificar vazões mínimas
    vazmin_registros = modif.vazmin()
    if vazmin_registros:
        if isinstance(vazmin_registros, list):
            vazoes_negativas = [r for r in vazmin_registros if r.vazao < 0]
            if vazoes_negativas:
                print(f"⚠️ {len(vazoes_negativas)} registro(s) com vazão mínima negativa")
        else:
            if vazmin_registros.vazao < 0:
                print("⚠️ Vazão mínima negativa encontrada")
    
    # Verificar datas
    vmaxt_registros = modif.vmaxt()
    if vmaxt_registros:
        if isinstance(vmaxt_registros, list):
            datas_invalidas = [r for r in vmaxt_registros if r.data_inicio is None]
            if datas_invalidas:
                print(f"⚠️ {len(datas_invalidas)} registro(s) VMAXT com data inválida")
    
    print("\n✅ Validação concluída")
else:
    print("ℹ️ Nenhuma modificação encontrada no arquivo")
```

#### 4.14. Integração com CONFHD.DAT

```python
from inewave.newave import Modif
from inewave.newave import Confhd

modif = Modif.read("modif.dat")
confhd = Confhd.read("confhd.dat")

if modif is not None and confhd.usinas is not None:
    # Obter usinas modificadas
    usinas_modif = modif.usina(df=True)
    
    if usinas_modif is not None and len(usinas_modif) > 0:
        codigos_modif = set(usinas_modif['codigo'].unique())
        
        # Verificar se as usinas têm flag de modificação no CONFHD
        usinas_confhd_modif = confhd.usinas[
            (confhd.usinas['codigo_usina'].isin(codigos_modif)) &
            (confhd.usinas['usina_modificada'] == 1)
        ]
        
        usinas_sem_flag = codigos_modif - set(usinas_confhd_modif['codigo_usina'].unique())
        
        if usinas_sem_flag:
            print(f"⚠️ {len(usinas_sem_flag)} usina(s) no MODIF.DAT sem flag de modificação no CONFHD.DAT:")
            print(f"   Códigos: {sorted(usinas_sem_flag)}")
            print("   O campo 'usina_modificada' deve ser 1 no CONFHD.DAT")
        else:
            print("✅ Todas as usinas modificadas têm flag correto no CONFHD.DAT")
```

---

### 5. Observações Importantes

1. **Habilitação**: 
   - O arquivo só é considerado se o campo 8 (`usina_modificada`) do `CONFHD.DAT` for igual a 1 para a usina
   - Cada usina que terá modificações deve ter este flag ativado

2. **Estrutura baseada em palavras-chave**: 
   - Diferente dos outros arquivos, o `MODIF.DAT` usa uma estrutura baseada em palavras-chave (mnemônicos)
   - Cada bloco começa com `USINA` seguido do código da usina
   - As modificações seguem em qualquer ordem dentro do bloco

3. **Múltiplos métodos**: 
   - A biblioteca inewave não fornece uma propriedade única como `expansoes` ou `usinas`
   - Em vez disso, fornece métodos específicos para cada tipo de modificação
   - Cada método pode retornar um objeto, uma lista ou um DataFrame

4. **Formato livre**: 
   - Os valores após as palavras-chave são escritos em formato livre
   - A biblioteca faz o parsing automático dos valores

5. **Case-insensitive**: 
   - As palavras-chave podem ser maiúsculas ou minúsculas (`VOLMIN` ou `volmin`)

6. **Referência temporal**: 
   - Modificações de volume com data (`VMAXT`, `VMINT`, `VMINP`) são referenciadas ao **final do período**
   - Modificações de canal de fuga (`CFUGA`) são referenciadas ao **início do período**

7. **Volume mínimo penalizado (VMINP)**: 
   - Implementa mecanismo de aversão a risco
   - O valor considerado será o mais restritivo entre `MODIF.DAT` (por usina) e `CURVA.DAT` (por REE)

8. **Vazão mínima**: 
   - Pode ter até dois valores: requisito total e valor para relaxamento (opcional, menor que o primeiro)

9. **Nível de montante**: 
   - Modificações de `CMONT` são permitidas **somente para usinas fio d'água**

10. **Turbinamento/Defluência com data**: 
    - `TURBMAXT`, `TURBMINT` e `VAZMAXT` são considerados apenas em períodos individualizados
    - Requerem flags específicos habilitados no `dger.dat` (campos 87 e 88)

11. **Períodos estáticos**: 
    - Valores relativos a períodos `PRE` e `POS` podem ser informados, mas serão ignorados se não houver período estático no estudo

12. **Método `modificacoes_usina()`**: 
    - Retorna todos os tipos de modificação para uma usina específica
    - Útil para análise completa de uma usina

13. **Parâmetro `df=True`**: 
    - Todos os métodos aceitam o parâmetro `df=True` para retornar DataFrames
    - Facilita análise e manipulação com pandas

14. **Filtros opcionais**: 
    - Todos os métodos aceitam parâmetros opcionais para filtrar os resultados
    - Útil para consultas específicas

15. **Comentários iniciais**: 
    - Os dois registros de comentário no início do arquivo são obrigatórios mas ignorados pelo programa

16. **Ordem dos registros**: 
    - A ordem dos registros de modificação dentro de um bloco de usina não importa
    - A palavra-chave `USINA` deve aparecer antes das modificações da usina

17. **Múltiplas modificações do mesmo tipo**: 
    - Uma usina pode ter múltiplas modificações do mesmo tipo (especialmente as com data)
    - Cada modificação é um registro separado

18. **Dependências**: 
    - Os códigos de usina devem estar no cadastro (`HIDR.DAT` e `CONFHD.DAT`)
    - O flag de modificação deve estar ativado no `CONFHD.DAT`

19. **Unidades de volume**: 
    - Volumes podem ser especificados em `H/h` (hectômetros cúbicos) ou `%` (percentual do volume útil)
    - A unidade deve ser especificada explicitamente

20. **Validação de consistência**: 
    - É recomendado validar se volume mínimo < volume máximo
    - Vazões devem ser valores positivos
    - Datas devem ser válidas e dentro do período de estudo

---

## C_ADIC.DAT

### 1. Informações do Arquivo

#### 1.1. Nome e Descrição

- **Nome do arquivo**: `c_adic.dat` ou `C_ADIC.DAT`
- **Tipo**: Arquivo de entrada do modelo NEWAVE
- **Função**: Fornece dados de **cargas ou ofertas adicionais** que são consideradas no sistema, sendo abatidas ou acrescidas ao mercado (demanda)

#### 1.2. Uso e Estrutura

**Habilitação:**
- O arquivo só é considerado pelo programa se o **registro 51** do arquivo de dados gerais (`dger.dat`) for preenchido com o valor **1**
- Se o registro 51 não estiver habilitado, o arquivo é ignorado mesmo que exista

**Convenção de Valores:**
- **Valores positivos** representam **cargas adicionais** (adicionadas ao mercado, aumentam a demanda)
- **Valores negativos** representam **ofertas adicionais** (abatidas do mercado, reduzem a demanda)

**Organização do Arquivo:**
- O `C_ADIC.DAT` é composto por um **único bloco de dados**, precedido por dois registros de comentários obrigatórios, que são ignorados pelo programa, servindo apenas para orientação

**Final do Bloco:**
- O código **`999`** no primeiro campo indica o final do arquivo

#### 1.3. Estrutura dos Registros

O bloco de dados é estruturado por conjuntos de registros que podem incluir até quatro tipos, dependendo da inclusão de períodos estáticos (inicial e final) no estudo:

##### Registro Tipo 1: Identificação do Subsistema

| Campo | Colunas | Formato | Descrição |
| :--- | :--- | :--- | :--- |
| 1 | 2 a 4 | I3 | **Número do subsistema/submercado** ao qual a carga/oferta adicional se aplica |
| 2 | 6 a 15 | A10 | **Nome do subsistema/submercado** |
| 3 | 17 a 28 | A12 | **Razão/Descrição** da carga adicional (opcional, para referência) |

**Observação**: O campo 3 (razão) é opcional e serve apenas para documentação/referência.

##### Registro Tipo 2: Carga/Oferta Adicional - Período de Planejamento

| Campo | Colunas | Formato | Descrição |
| :--- | :--- | :--- | :--- |
| 1 | 1 a 4 | A4 | **Ano** do período de planejamento |
| 2 a 13 | 6 a 101 | 12x F8.0 | **Carga/Oferta Adicional** (MWmédio) para os **12 meses** do ano |

Este registro contém a Carga/Oferta Adicional para os **12 meses** de cada ano do **período de planejamento**.

##### Registro Tipo 3 (Opcional): Período Estático Inicial

| Campo | Colunas | Formato | Descrição |
| :--- | :--- | :--- | :--- |
| 1 | 1 a 4 | A4 | **Ano padrão "0001"** (identifica período estático inicial) |
| 2 a 13 | 6 a 101 | 12x F8.0 | **Carga/Oferta Adicional** (MWmédio) para os **12 meses** do período estático inicial |

Este registro é informado apenas se houver período estático inicial no estudo.

##### Registro Tipo 4 (Opcional): Período Estático Final

| Campo | Colunas | Formato | Descrição |
| :--- | :--- | :--- | :--- |
| 1 | 1 a 4 | A4 | **Ano padrão "9999"** (identifica período estático final) |
| 2 a 13 | 6 a 101 | 12x F8.0 | **Carga/Oferta Adicional** (MWmédio) para os **12 meses** do período estático final |

Este registro é informado apenas se houver período estático final no estudo.

**Estrutura de um Conjunto Completo:**
1. Registro Tipo 1 (identificação do subsistema)
2. Um ou mais Registros Tipo 2 (um para cada ano do período de planejamento)
3. Registro Tipo 3 (opcional, se houver período estático inicial)
4. Registro Tipo 4 (opcional, se houver período estático final)

Após completar um subsistema, pode-se iniciar outro subsistema com um novo Registro Tipo 1.

---

### 2. Propriedades da Biblioteca inewave

#### 2.1. Classe Correspondente

**Classe**: `Cadic`

```python
class Cadic(data=<cfinterface.data.sectiondata.SectionData object>)
```

**Descrição**: Armazena os dados de entrada do NEWAVE referentes às cargas adicionais.

#### 2.2. Propriedades Disponíveis

##### `property` **cargas**: `pd.DataFrame | None`

- **Descrição**: Tabela com as cargas adicionais por mês/ano e por subsistema para cada razão de carga adicional
- **Tipo de retorno**: `pd.DataFrame | None`
- **Colunas do DataFrame**:
  - `codigo_submercado` (`int`): Código do subsistema/submercado (corresponde ao campo 1 do Registro Tipo 1)
  - `nome_submercado` (`str`): Nome do subsistema/submercado (corresponde ao campo 2 do Registro Tipo 1)
  - `razao` (`str`): Razão/descrição da carga adicional (corresponde ao campo 3 do Registro Tipo 1, pode estar vazio)
  - `data` (`datetime`): Data (mês/ano) da carga adicional. Para períodos estáticos, são usados anos padrão: "0001" para PRE e "9999" para POS
  - `valor` (`float`): Valor da carga/oferta adicional em MWmédio. Valores positivos = cargas adicionais, valores negativos = ofertas adicionais

**Observações:**
- Cada linha representa uma carga/oferta adicional para um mês específico de um subsistema
- O DataFrame contém uma linha para cada combinação de subsistema, razão, ano e mês
- Para períodos estáticos, a biblioteca adota os anos padrão "0001" (PRE) e "9999" (POS) no campo `data`
- Se o arquivo não existir ou estiver vazio, a propriedade retorna `None`
- Valores positivos indicam cargas adicionais (aumentam demanda)
- Valores negativos indicam ofertas adicionais (reduzem demanda)

---

### 3. Mapeamento de Campos

#### 3.1. Registro Tipo 1 → Propriedade `cargas`

| Campo do Arquivo | Colunas | Formato | Coluna DataFrame | Tipo Python | Descrição |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Número do subsistema | 2-4 | I3 | `codigo_submercado` | `int` | Identificador do subsistema |
| Nome do subsistema | 6-15 | A10 | `nome_submercado` | `str` | Nome do subsistema |
| Razão | 17-28 | A12 | `razao` | `str` | Descrição da carga adicional |

#### 3.2. Registros Tipo 2, 3 e 4 → Propriedade `cargas`

| Campo do Arquivo | Colunas | Formato | Coluna DataFrame | Tipo Python | Descrição |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Ano | 1-4 | A4 | (parte de `data`) | `datetime.year` | Ano do período |
| Mês 1 | 6-13 | F8.0 | (parte de `data` e `valor`) | `datetime.month`, `float` | Carga do mês 1 |
| Mês 2 | 14-21 | F8.0 | (parte de `data` e `valor`) | `datetime.month`, `float` | Carga do mês 2 |
| ... | ... | ... | ... | ... | ... |
| Mês 12 | 94-101 | F8.0 | (parte de `data` e `valor`) | `datetime.month`, `float` | Carga do mês 12 |

**Observação**: A biblioteca expande cada registro de 12 meses em 12 linhas no DataFrame, uma para cada mês, mantendo as informações do Registro Tipo 1 (subsistema, nome, razão) e criando uma data completa (ano/mês) para cada linha.

---

### 4. Exemplos de Uso

#### 4.1. Leitura do Arquivo

```python
from inewave.newave import Cadic

# Ler o arquivo c_adic.dat
cadic = Cadic.read("c_adic.dat")

# Acessar a tabela de cargas adicionais
df_cargas = cadic.cargas

if df_cargas is not None:
    print(f"Total de registros de carga adicional: {len(df_cargas)}")
    print(df_cargas.head())
else:
    print("Nenhuma carga adicional encontrada ou arquivo vazio")
```

#### 4.2. Consulta de Cargas por Subsistema

```python
from inewave.newave import Cadic

cadic = Cadic.read("c_adic.dat")

if cadic.cargas is not None:
    # Filtrar cargas de um subsistema específico
    codigo_submercado = 1
    cargas_subsistema = cadic.cargas[
        cadic.cargas['codigo_submercado'] == codigo_submercado
    ]
    
    print(f"Cargas adicionais do subsistema {codigo_submercado}:")
    print(f"Total de registros: {len(cargas_subsistema)}")
    print(cargas_subsistema.head(10))
```

#### 4.3. Análise de Cargas vs. Ofertas

```python
from inewave.newave import Cadic

cadic = Cadic.read("c_adic.dat")

if cadic.cargas is not None:
    df_cargas = cadic.cargas
    
    # Separar cargas (positivas) e ofertas (negativas)
    cargas_adicionais = df_cargas[df_cargas['valor'] > 0]
    ofertas_adicionais = df_cargas[df_cargas['valor'] < 0]
    
    print(f"Total de registros: {len(df_cargas)}")
    print(f"Cargas adicionais (positivas): {len(cargas_adicionais)}")
    print(f"Ofertas adicionais (negativas): {len(ofertas_adicionais)}")
    
    if len(cargas_adicionais) > 0:
        print(f"\nSoma total de cargas adicionais: {cargas_adicionais['valor'].sum():.2f} MWmédio")
        print(f"Média de cargas adicionais: {cargas_adicionais['valor'].mean():.2f} MWmédio")
    
    if len(ofertas_adicionais) > 0:
        print(f"\nSoma total de ofertas adicionais: {ofertas_adicionais['valor'].sum():.2f} MWmédio")
        print(f"Média de ofertas adicionais: {ofertas_adicionais['valor'].mean():.2f} MWmédio")
```

#### 4.4. Consulta por Período

```python
from inewave.newave import Cadic
from datetime import datetime

cadic = Cadic.read("c_adic.dat")

if cadic.cargas is not None:
    # Filtrar cargas em um período específico
    data_inicio = datetime(2024, 1, 1)
    data_fim = datetime(2024, 12, 31)
    
    cargas_periodo = cadic.cargas[
        (cadic.cargas['data'] >= data_inicio) &
        (cadic.cargas['data'] <= data_fim)
    ]
    
    print(f"Cargas adicionais no período {data_inicio.date()} a {data_fim.date()}:")
    print(f"Total de registros: {len(cargas_periodo)}")
    
    if len(cargas_periodo) > 0:
        print(f"Soma total: {cargas_periodo['valor'].sum():.2f} MWmédio")
        print("\nDetalhes:")
        print(cargas_periodo[['nome_submercado', 'data', 'valor']].head(20))
```

#### 4.5. Análise por Razão

```python
from inewave.newave import Cadic

cadic = Cadic.read("c_adic.dat")

if cadic.cargas is not None:
    # Agrupar por razão
    cargas_por_razao = cadic.cargas.groupby('razao').agg({
        'valor': ['count', 'sum', 'mean', 'min', 'max']
    })
    
    print("Análise de cargas adicionais por razão:")
    print(cargas_por_razao)
    
    # Listar razões disponíveis
    razoes = cadic.cargas['razao'].unique()
    print(f"\nRazões encontradas: {len(razoes)}")
    for razao in razoes:
        if razao and razao.strip():  # Ignorar razões vazias
            print(f"  - {razao}")
```

#### 4.6. Análise Temporal (por Ano)

```python
from inewave.newave import Cadic

cadic = Cadic.read("c_adic.dat")

if cadic.cargas is not None:
    # Extrair ano da data
    cadic.cargas['ano'] = cadic.cargas['data'].dt.year
    
    # Agrupar por ano
    cargas_por_ano = cadic.cargas.groupby('ano').agg({
        'valor': ['count', 'sum', 'mean']
    })
    
    print("Análise de cargas adicionais por ano:")
    print(cargas_por_ano)
    
    # Identificar períodos estáticos (anos 0001 e 9999)
    periodo_pre = cadic.cargas[cadic.cargas['ano'] == 1]
    periodo_pos = cadic.cargas[cadic.cargas['ano'] == 9999]
    
    if len(periodo_pre) > 0:
        print(f"\nPeríodo estático inicial (PRE): {len(periodo_pre)} registros")
        print(f"Soma: {periodo_pre['valor'].sum():.2f} MWmédio")
    
    if len(periodo_pos) > 0:
        print(f"\nPeríodo estático final (POS): {len(periodo_pos)} registros")
        print(f"Soma: {periodo_pos['valor'].sum():.2f} MWmédio")
```

#### 4.7. Análise por Subsistema e Razão

```python
from inewave.newave import Cadic

cadic = Cadic.read("c_adic.dat")

if cadic.cargas is not None:
    # Agrupar por subsistema e razão
    cargas_subsistema_razao = cadic.cargas.groupby(['nome_submercado', 'razao']).agg({
        'valor': ['count', 'sum', 'mean']
    })
    
    print("Análise de cargas adicionais por subsistema e razão:")
    print(cargas_subsistema_razao)
    
    # Análise detalhada por subsistema
    for submercado in cadic.cargas['nome_submercado'].unique():
        cargas_sub = cadic.cargas[cadic.cargas['nome_submercado'] == submercado]
        print(f"\n{submercado}:")
        print(f"  Total de registros: {len(cargas_sub)}")
        print(f"  Soma: {cargas_sub['valor'].sum():.2f} MWmédio")
        print(f"  Média: {cargas_sub['valor'].mean():.2f} MWmédio")
```

#### 4.8. Consulta de Cargas por Mês

```python
from inewave.newave import Cadic

cadic = Cadic.read("c_adic.dat")

if cadic.cargas is not None:
    # Extrair mês da data
    cadic.cargas['mes'] = cadic.cargas['data'].dt.month
    
    # Agrupar por mês
    cargas_por_mes = cadic.cargas.groupby('mes').agg({
        'valor': ['count', 'sum', 'mean']
    })
    
    print("Análise de cargas adicionais por mês:")
    print(cargas_por_mes)
    
    # Identificar mês com maior carga adicional
    soma_por_mes = cadic.cargas.groupby('mes')['valor'].sum()
    mes_max = soma_por_mes.idxmax()
    print(f"\nMês com maior soma de cargas adicionais: {mes_max}")
    print(f"Valor: {soma_por_mes[mes_max]:.2f} MWmédio")
```

#### 4.9. Análise de Sazonalidade

```python
from inewave.newave import Cadic

cadic = Cadic.read("c_adic.dat")

if cadic.cargas is not None:
    # Extrair mês e ano
    cadic.cargas['mes'] = cadic.cargas['data'].dt.month
    cadic.cargas['ano'] = cadic.cargas['data'].dt.year
    
    # Filtrar apenas período de planejamento (excluir PRE e POS)
    periodo_planejamento = cadic.cargas[
        (cadic.cargas['ano'] != 1) & (cadic.cargas['ano'] != 9999)
    ]
    
    if len(periodo_planejamento) > 0:
        # Análise sazonal
        sazonalidade = periodo_planejamento.groupby('mes').agg({
            'valor': ['mean', 'std']
        })
        
        print("Análise sazonal de cargas adicionais (período de planejamento):")
        print(sazonalidade)
        
        # Identificar padrão sazonal
        meses_nomes = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun',
                       'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
        
        print("\nMédia de cargas adicionais por mês:")
        for mes in range(1, 13):
            media = sazonalidade.loc[mes, ('valor', 'mean')]
            print(f"  {meses_nomes[mes-1]}: {media:.2f} MWmédio")
```

#### 4.10. Validação de Dados

```python
from inewave.newave import Cadic

cadic = Cadic.read("c_adic.dat")

if cadic.cargas is not None:
    df_cargas = cadic.cargas
    
    # Verificar se há dados
    if len(df_cargas) == 0:
        print("⚠️ Nenhuma carga adicional encontrada no arquivo")
    
    # Verificar campos obrigatórios
    campos_obrigatorios = ['codigo_submercado', 'nome_submercado', 'data', 'valor']
    campos_faltando = [campo for campo in campos_obrigatorios if campo not in df_cargas.columns]
    
    if campos_faltando:
        print(f"⚠️ Campos faltando: {campos_faltando}")
    
    # Verificar valores nulos
    valores_nulos = df_cargas['valor'].isna().sum()
    if valores_nulos > 0:
        print(f"⚠️ {valores_nulos} registros com valor nulo")
    
    # Verificar códigos de subsistema válidos
    codigos_invalidos = df_cargas[
        df_cargas['codigo_submercado'].isna() | 
        (df_cargas['codigo_submercado'] <= 0)
    ]
    
    if len(codigos_invalidos) > 0:
        print(f"⚠️ {len(codigos_invalidos)} registros com código de subsistema inválido")
    
    # Verificar datas válidas
    datas_invalidas = df_cargas[df_cargas['data'].isna()]
    if len(datas_invalidas) > 0:
        print(f"⚠️ {len(datas_invalidas)} registros com data inválida")
    
    # Estatísticas gerais
    print("\nEstatísticas gerais:")
    print(f"  Total de registros: {len(df_cargas)}")
    print(f"  Subsistemas únicos: {df_cargas['codigo_submercado'].nunique()}")
    print(f"  Período: {df_cargas['data'].min().strftime('%Y-%m')} a {df_cargas['data'].max().strftime('%Y-%m')}")
    print(f"  Soma total: {df_cargas['valor'].sum():.2f} MWmédio")
    print(f"  Média: {df_cargas['valor'].mean():.2f} MWmédio")
    print(f"  Mínimo: {df_cargas['valor'].min():.2f} MWmédio")
    print(f"  Máximo: {df_cargas['valor'].max():.2f} MWmédio")
    
    print("\n✅ Validação concluída")
else:
    print("ℹ️ Arquivo vazio ou não encontrado")
```

#### 4.11. Modificação e Gravação

```python
from inewave.newave import Cadic
from datetime import datetime

# Ler o arquivo
cadic = Cadic.read("c_adic.dat")

if cadic.cargas is not None:
    # Modificar valor de uma carga específica
    codigo_submercado = 1
    data_modificacao = datetime(2024, 6, 1)
    
    mask = (
        (cadic.cargas['codigo_submercado'] == codigo_submercado) &
        (cadic.cargas['data'] == data_modificacao)
    )
    
    if mask.any():
        novo_valor = 100.0  # MWmédio
        cadic.cargas.loc[mask, 'valor'] = novo_valor
        print(f"Carga adicional atualizada para {novo_valor} MWmédio")
    
    # Adicionar nova carga adicional
    import pandas as pd
    
    nova_carga = pd.DataFrame({
        'codigo_submercado': [1],
        'nome_submercado': ['SUDESTE'],
        'razao': ['Nova carga'],
        'data': [datetime(2025, 1, 1)],
        'valor': [50.0]  # MWmédio
    })
    
    cadic.cargas = pd.concat([cadic.cargas, nova_carga], ignore_index=True)
    print("Nova carga adicional adicionada")
    
    # Remover cargas de um período específico
    data_inicio = datetime(2023, 1, 1)
    data_fim = datetime(2023, 12, 31)
    
    mask_remover = (
        (cadic.cargas['data'] >= data_inicio) &
        (cadic.cargas['data'] <= data_fim)
    )
    
    if mask_remover.any():
        cadic.cargas = cadic.cargas[~mask_remover]
        print(f"Cargas do período {data_inicio.date()} a {data_fim.date()} removidas")
    
    # Salvar alterações
    cadic.write("c_adic.dat")
```

#### 4.12. Integração com SISTEMA.DAT

```python
from inewave.newave import Cadic
from inewave.newave import Sistema

cadic = Cadic.read("c_adic.dat")
sistema = Sistema.read("sistema.dat")

if cadic.cargas is not None and sistema.mercado_energia is not None:
    # Verificar se os subsistemas no C_ADIC existem no SISTEMA
    codigos_cadic = set(cadic.cargas['codigo_submercado'].unique())
    codigos_sistema = set(sistema.mercado_energia['codigo_submercado'].unique())
    
    codigos_inexistentes = codigos_cadic - codigos_sistema
    
    if codigos_inexistentes:
        print(f"⚠️ {len(codigos_inexistentes)} subsistema(s) no C_ADIC.DAT não encontrado(s) no SISTEMA.DAT:")
        print(f"   Códigos: {sorted(codigos_inexistentes)}")
    else:
        print("✅ Todos os subsistemas no C_ADIC.DAT existem no SISTEMA.DAT")
    
    # Comparar cargas adicionais com mercado de energia
    for codigo in codigos_cadic:
        cargas_sub = cadic.cargas[cadic.cargas['codigo_submercado'] == codigo]
        mercado_sub = sistema.mercado_energia[
            sistema.mercado_energia['codigo_submercado'] == codigo
        ]
        
        if len(cargas_sub) > 0 and len(mercado_sub) > 0:
            soma_cargas = cargas_sub['valor'].sum()
            soma_mercado = mercado_sub['valor'].sum()
            
            print(f"\nSubsistema {codigo}:")
            print(f"  Cargas adicionais: {soma_cargas:.2f} MWmédio")
            print(f"  Mercado de energia: {soma_mercado:.2f} MWmédio")
            print(f"  Proporção: {(soma_cargas/soma_mercado*100):.2f}%")
```

---

### 5. Observações Importantes

1. **Habilitação**: 
   - O arquivo só é considerado se o registro 51 do `dger.dat` for igual a 1
   - Se não estiver habilitado, o arquivo é ignorado mesmo que exista

2. **Convenção de valores**: 
   - **Valores positivos** = cargas adicionais (aumentam a demanda)
   - **Valores negativos** = ofertas adicionais (reduzem a demanda)

3. **Estrutura de registros**: 
   - Cada subsistema começa com um Registro Tipo 1 (identificação)
   - Seguem-se Registros Tipo 2 (um para cada ano do período de planejamento)
   - Opcionalmente, Registros Tipo 3 (período estático inicial) e Tipo 4 (período estático final)

4. **Períodos estáticos**: 
   - A biblioteca usa anos padrão: "0001" para PRE e "9999" para POS
   - Estes anos aparecem no campo `data` do DataFrame

5. **Campo razão**: 
   - O campo `razao` é opcional e serve apenas para documentação/referência
   - Pode estar vazio em alguns registros

6. **Expansão de dados**: 
   - A biblioteca expande cada registro de 12 meses em 12 linhas no DataFrame
   - Cada linha representa um mês específico

7. **Final do arquivo**: 
   - O código `999` no primeiro campo indica o final do arquivo

8. **Comentários iniciais**: 
   - Os dois registros de comentário no início do arquivo são obrigatórios mas ignorados pelo programa

9. **DataFrame pandas**: 
   - A propriedade `cargas` retorna um DataFrame do pandas, permitindo uso completo das funcionalidades do pandas para análise e manipulação

10. **Dependências**: 
    - Os códigos de subsistema devem estar no cadastro (`SISTEMA.DAT`)
    - O registro 51 do `dger.dat` deve estar habilitado

11. **Unidade**: 
    - Todos os valores são em MWmédio (megawatts médios)

12. **Validação**: 
    - É recomendado validar se os subsistemas existem no `SISTEMA.DAT`
    - Verificar se há valores nulos ou inválidos
    - Validar se as datas estão dentro do período de estudo

13. **Análise de impacto**: 
    - Cargas adicionais aumentam a demanda total do sistema
    - Ofertas adicionais reduzem a demanda efetiva (podem representar geração adicional não simulada)

14. **Múltiplas razões**: 
    - Um mesmo subsistema pode ter múltiplas razões de carga adicional
    - Cada razão é tratada separadamente no DataFrame

15. **Formato de data**: 
    - As datas são armazenadas como objetos `datetime` no DataFrame
    - Para períodos estáticos, os anos padrão (1 e 9999) são usados

16. **Compatibilidade**: 
    - O arquivo é opcional e só é processado se habilitado no `dger.dat`
    - Se não habilitado, não há impacto no modelo mesmo que o arquivo exista

---

## ADTERM.DAT

### 1. Informações do Arquivo

#### 1.1. Nome e Descrição

- **Nome do arquivo**: `adterm.dat` ou `ADTERM.DAT`
- **Tipo**: Arquivo de entrada opcional do modelo NEWAVE
- **Função**: Fornece informações sobre a geração térmica das usinas a Gás Natural Liquefeito (GNL) que têm seu despacho antecipado

#### 1.2. Requisito para Utilização

**Habilitação:**
- Os registros contidos no arquivo `ADTERM.DAT` só são processados pelo programa NEWAVE se o **registro 55** do arquivo de dados gerais (`dger.dat`) estiver preenchido com o **valor igual a 1**
- Se o registro 55 não estiver habilitado, o arquivo é ignorado mesmo que exista

#### 1.3. Função e Conteúdo

**Estrutura:**
- O arquivo é composto por um **único bloco de dados**, que contém dois tipos de registros
- O bloco é precedido por **dois registros destinados a comentários**, que são obrigatórios, mas ignorados pelo programa

**Final do Arquivo:**
- O código **`9999`** no Campo 1 do Registro Tipo 1 indica o final do arquivo

#### 1.4. Registro Tipo 1: Identificação da Usina GNL

| Campo | Colunas | Formato | Descrição |
| :--- | :--- | :--- | :--- |
| 1 | 2 a 5 | I4 | **Número da usina térmica GNL** |
| 2 | 8 a 19 | A12 | **Nome da usina térmica GNL** |
| 3 | 22 | I1 | **Lag de antecipação de despacho** da usina térmica GNL (`nlag`) |

**Observações:**
- O lag de antecipação (`nlag`) indica quantos meses à frente o despacho será antecipado
- O lag 1 corresponde ao mês inicial (do período de simulação no NEWDESP)
- O lag `nlag` corresponde ao mês inicial + `nlag` - 1
- O código `9999` no Campo 1 indica o final do arquivo

#### 1.5. Registro Tipo 2: Geração Térmica Antecipada

Este registro informa a geração térmica antecipada para o lag correspondente em cada patamar de carga. O número de registros do Tipo 2 deve ser igual ao **lag de antecipação** (`nlag`) da usina GNL (i = 1 a `nlag`), seguindo a ordem cronológica.

| Campo | Colunas | Formato | Descrição |
| :--- | :--- | :--- | :--- |
| 1 | 25 a 34 | F10.2 | **Geração térmica antecipada** lag *i* para **1º patamar** de carga (MW) |
| 2 | 37 a 46 | F10.2 | **Geração térmica antecipada** lag *i* para **2º patamar** de carga (MW) |
| 3 | 49 a 58 | F10.2 | **Geração térmica antecipada** lag *i* para **3º patamar** de carga (MW) |
| 4 | 61 a 70 | F10.2 | **Geração térmica antecipada** lag *i* para **4º patamar** de carga (MW) |
| 5 | 73 a 82 | F10.2 | **Geração térmica antecipada** lag *i* para **5º patamar** de carga (MW) |

**Estrutura de um Conjunto Completo:**
1. Registro Tipo 1 (identificação da usina: código, nome, lag)
2. `nlag` Registros Tipo 2 (um para cada lag, do 1 ao `nlag`)

**Observações:**
- Cada Registro Tipo 2 contém valores para todos os patamares de carga (até 5 patamares)
- O número de patamares é definido no arquivo `SISTEMA.DAT`
- A ordem dos registros Tipo 2 deve seguir a ordem cronológica dos lags (1, 2, 3, ..., `nlag`)
- O lag 1 corresponde ao mês inicial e o lag `nlag` corresponde ao mês inicial + `nlag` - 1

#### 1.6. Regras e Validações

1. **Declaração prévia**: As usinas térmicas a GNL listadas no `ADTERM.DAT` devem ter sido previamente declaradas no arquivo de configuração termoelétrica (`conft.dat`)

2. **Lag de antecipação**: Duas usinas a GNL que pertençam à **mesma classe térmica** devem ter o **mesmo lag de antecipação de despacho**

3. **Limites de geração**: A geração térmica antecipada deve ser:
   - **Maior ou igual à geração térmica mínima** da usina
   - **Menor ou igual à geração térmica máxima** da usina

4. **Unicidade**: Não é permitida a declaração de mais de um bloco de dados para a mesma usina térmica GNL

5. **Ajuste automático**: Existe uma opção para que o montante de antecipação de despacho seja **modificado automaticamente** se a capacidade de geração máxima da usina for inferior ao valor antecipado fornecido pelo usuário. Nesse caso, o valor antecipado será ajustado para ser igual ao valor da geração térmica máxima

#### 1.7. Contexto de Uso

**Módulo NEWDESP:**
- O arquivo `ADTERM.DAT` é relevante no contexto do módulo **NEWDESP**, que calcula o despacho ótimo para o período corrente usando a Função de Custo Futuro (FCF) do NEWAVE
- O NEWDESP possui um bloco dedicado à leitura das informações de antecipação de despacho das classes térmicas GNL para os primeiros meses do horizonte de simulação

**Função de Custo Futuro (FCF):**
- A informação de despacho antecipado é uma variável de estado crucial para a Função de Custo Futuro (FCF)
- O custo futuro relaciona-se com o vetor de volumes armazenados e a geração térmica antecipada (variável $SGT_{t+l,k,c}$) através de coeficientes específicos ($\pi^{GNL}$) nos cortes de Benders
- O termo de **antecipação de despacho de usinas térmicas a GNL** é uma variável de estado na FCF
- O número máximo de meses de antecipação (`LAGMAX`) é um parâmetro lido no arquivo de cabeçalho dos cortes (`cortesh.dat`)

---

### 2. Propriedades da Biblioteca inewave

#### 2.1. Classe Correspondente

**Classe**: `Adterm`

```python
class Adterm(data=<cfinterface.data.sectiondata.SectionData object>)
```

**Descrição**: Armazena os dados de entrada do NEWAVE referentes às térmicas de despacho antecipado disponíveis.

#### 2.2. Propriedades Disponíveis

##### `property` **despachos**: `pd.DataFrame | None`

- **Descrição**: A tabela de despachos antecipados das térmicas GNL
- **Tipo de retorno**: `pd.DataFrame | None`
- **Colunas do DataFrame**:
  - `codigo_usina` (`int`): Código da usina térmica GNL (corresponde ao campo 1 do Registro Tipo 1)
  - `nome_usina` (`str`): Nome da usina térmica GNL (corresponde ao campo 2 do Registro Tipo 1)
  - `lag` (`int`): Lag de antecipação de despacho (corresponde ao campo 3 do Registro Tipo 1 e identifica qual registro Tipo 2)
  - `patamar` (`int`): Número do patamar de carga (1 a 5, corresponde aos campos 1-5 do Registro Tipo 2)
  - `valor` (`float`): Geração térmica antecipada em MW (corresponde ao valor do patamar no Registro Tipo 2)

**Observações:**
- Cada linha representa uma geração térmica antecipada para uma combinação específica de usina, lag e patamar
- A biblioteca expande os registros Tipo 2 em múltiplas linhas, uma para cada patamar
- O DataFrame contém uma linha para cada combinação de usina × lag × patamar
- Se o arquivo não existir ou estiver vazio, a propriedade retorna `None`
- O número de patamares é determinado automaticamente durante a leitura (parâmetro `numero_patamares`)

---

### 3. Mapeamento de Campos

#### 3.1. Registro Tipo 1 → Propriedade `despachos`

| Campo do Arquivo | Colunas | Formato | Coluna DataFrame | Tipo Python | Descrição |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Número da usina | 2-5 | I4 | `codigo_usina` | `int` | Identificador da usina GNL |
| Nome da usina | 8-19 | A12 | `nome_usina` | `str` | Nome da usina GNL |
| Lag de antecipação | 22 | I1 | `lag` | `int` | Número de meses de antecipação |

#### 3.2. Registro Tipo 2 → Propriedade `despachos`

| Campo do Arquivo | Colunas | Formato | Coluna DataFrame | Tipo Python | Descrição |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Geração lag i, patamar 1 | 25-34 | F10.2 | (`patamar`=1, `valor`) | `int`, `float` | Geração para patamar 1 |
| Geração lag i, patamar 2 | 37-46 | F10.2 | (`patamar`=2, `valor`) | `int`, `float` | Geração para patamar 2 |
| Geração lag i, patamar 3 | 49-58 | F10.2 | (`patamar`=3, `valor`) | `int`, `float` | Geração para patamar 3 |
| Geração lag i, patamar 4 | 61-70 | F10.2 | (`patamar`=4, `valor`) | `int`, `float` | Geração para patamar 4 |
| Geração lag i, patamar 5 | 73-82 | F10.2 | (`patamar`=5, `valor`) | `int`, `float` | Geração para patamar 5 |

**Observação**: A biblioteca expande cada Registro Tipo 2 em múltiplas linhas no DataFrame, uma para cada patamar, mantendo as informações do Registro Tipo 1 (código, nome, lag) e criando uma linha para cada patamar com seu respectivo valor.

---

### 4. Exemplos de Uso

#### 4.1. Leitura do Arquivo

```python
from inewave.newave import Adterm

# Ler o arquivo adterm.dat
adterm = Adterm.read("adterm.dat")

# Acessar a tabela de despachos antecipados
df_despachos = adterm.despachos

if df_despachos is not None:
    print(f"Total de registros de despacho antecipado: {len(df_despachos)}")
    print(df_despachos.head())
else:
    print("Nenhum despacho antecipado encontrado ou arquivo vazio")
```

#### 4.2. Consulta de Despachos por Usina

```python
from inewave.newave import Adterm

adterm = Adterm.read("adterm.dat")

if adterm.despachos is not None:
    # Filtrar despachos de uma usina específica
    codigo_usina = 1
    despachos_usina = adterm.despachos[
        adterm.despachos['codigo_usina'] == codigo_usina
    ]
    
    print(f"Despachos antecipados da usina {codigo_usina}:")
    print(f"Total de registros: {len(despachos_usina)}")
    print(despachos_usina)
```

#### 4.3. Consulta por Lag

```python
from inewave.newave import Adterm

adterm = Adterm.read("adterm.dat")

if adterm.despachos is not None:
    # Filtrar despachos por lag específico
    lag = 1
    despachos_lag = adterm.despachos[
        adterm.despachos['lag'] == lag
    ]
    
    print(f"Despachos antecipados para lag {lag}:")
    print(f"Total de registros: {len(despachos_lag)}")
    print(despachos_lag)
    
    # Análise por lag
    despachos_por_lag = adterm.despachos.groupby('lag').agg({
        'valor': ['count', 'sum', 'mean']
    })
    
    print("\nAnálise por lag:")
    print(despachos_por_lag)
```

#### 4.4. Consulta por Patamar

```python
from inewave.newave import Adterm

adterm = Adterm.read("adterm.dat")

if adterm.despachos is not None:
    # Filtrar despachos por patamar específico
    patamar = 1
    despachos_patamar = adterm.despachos[
        adterm.despachos['patamar'] == patamar
    ]
    
    print(f"Despachos antecipados para patamar {patamar}:")
    print(f"Total de registros: {len(despachos_patamar)}")
    print(despachos_patamar.head(10))
    
    # Análise por patamar
    despachos_por_patamar = adterm.despachos.groupby('patamar').agg({
        'valor': ['count', 'sum', 'mean', 'min', 'max']
    })
    
    print("\nAnálise por patamar:")
    print(despachos_por_patamar)
```

#### 4.5. Análise Completa por Usina

```python
from inewave.newave import Adterm

adterm = Adterm.read("adterm.dat")

if adterm.despachos is not None:
    # Agrupar por usina
    despachos_por_usina = adterm.despachos.groupby(['codigo_usina', 'nome_usina']).agg({
        'lag': ['min', 'max', 'nunique'],
        'valor': ['count', 'sum', 'mean', 'min', 'max']
    })
    
    print("Análise de despachos antecipados por usina:")
    print(despachos_por_usina)
    
    # Análise detalhada por usina
    for codigo in adterm.despachos['codigo_usina'].unique():
        despachos_usina = adterm.despachos[
            adterm.despachos['codigo_usina'] == codigo
        ]
        nome = despachos_usina['nome_usina'].iloc[0]
        lag_max = despachos_usina['lag'].max()
        
        print(f"\nUsina {codigo} - {nome}:")
        print(f"  Lag máximo: {lag_max}")
        print(f"  Total de registros: {len(despachos_usina)}")
        print(f"  Soma total: {despachos_usina['valor'].sum():.2f} MW")
        print(f"  Média: {despachos_usina['valor'].mean():.2f} MW")
        
        # Análise por lag
        for lag in range(1, lag_max + 1):
            despachos_lag = despachos_usina[despachos_usina['lag'] == lag]
            if len(despachos_lag) > 0:
                print(f"    Lag {lag}: {despachos_lag['valor'].sum():.2f} MW")
```

#### 4.6. Análise de Evolução por Lag

```python
from inewave.newave import Adterm

adterm = Adterm.read("adterm.dat")

if adterm.despachos is not None:
    # Análise de como a geração evolui ao longo dos lags
    for codigo in adterm.despachos['codigo_usina'].unique():
        despachos_usina = adterm.despachos[
            adterm.despachos['codigo_usina'] == codigo
        ]
        nome = despachos_usina['nome_usina'].iloc[0]
        lag_max = despachos_usina['lag'].max()
        
        print(f"\nUsina {codigo} - {nome}:")
        print("Evolução da geração por lag (soma de todos os patamares):")
        
        for lag in range(1, lag_max + 1):
            despachos_lag = despachos_usina[despachos_usina['lag'] == lag]
            soma_lag = despachos_lag['valor'].sum()
            print(f"  Lag {lag}: {soma_lag:.2f} MW")
```

#### 4.7. Análise por Patamar e Lag

```python
from inewave.newave import Adterm

adterm = Adterm.read("adterm.dat")

if adterm.despachos is not None:
    # Análise cruzada: patamar × lag
    analise_cruzada = adterm.despachos.groupby(['patamar', 'lag']).agg({
        'valor': ['count', 'sum', 'mean']
    })
    
    print("Análise cruzada: Patamar × Lag")
    print(analise_cruzada)
    
    # Pivot table para visualização
    pivot_table = adterm.despachos.pivot_table(
        values='valor',
        index='patamar',
        columns='lag',
        aggfunc='mean'
    )
    
    print("\nTabela pivot: Média de geração por patamar e lag:")
    print(pivot_table)
```

#### 4.8. Validação de Dados

```python
from inewave.newave import Adterm

adterm = Adterm.read("adterm.dat")

if adterm.despachos is not None:
    df_despachos = adterm.despachos
    
    # Verificar se há dados
    if len(df_despachos) == 0:
        print("⚠️ Nenhum despacho antecipado encontrado no arquivo")
    
    # Verificar campos obrigatórios
    campos_obrigatorios = ['codigo_usina', 'nome_usina', 'lag', 'patamar', 'valor']
    campos_faltando = [campo for campo in campos_obrigatorios if campo not in df_despachos.columns]
    
    if campos_faltando:
        print(f"⚠️ Campos faltando: {campos_faltando}")
    
    # Verificar valores nulos
    valores_nulos = df_despachos['valor'].isna().sum()
    if valores_nulos > 0:
        print(f"⚠️ {valores_nulos} registros com valor nulo")
    
    # Verificar códigos de usina válidos
    codigos_invalidos = df_despachos[
        df_despachos['codigo_usina'].isna() | 
        (df_despachos['codigo_usina'] <= 0)
    ]
    
    if len(codigos_invalidos) > 0:
        print(f"⚠️ {len(codigos_invalidos)} registros com código de usina inválido")
    
    # Verificar lags válidos (deve ser >= 1)
    lags_invalidos = df_despachos[
        df_despachos['lag'].isna() | 
        (df_despachos['lag'] < 1)
    ]
    
    if len(lags_invalidos) > 0:
        print(f"⚠️ {len(lags_invalidos)} registros com lag inválido (deve ser >= 1)")
    
    # Verificar patamares válidos (deve ser 1-5)
    patamares_invalidos = df_despachos[
        df_despachos['patamar'].isna() | 
        (df_despachos['patamar'] < 1) | 
        (df_despachos['patamar'] > 5)
    ]
    
    if len(patamares_invalidos) > 0:
        print(f"⚠️ {len(patamares_invalidos)} registros com patamar inválido (deve ser 1-5)")
    
    # Verificar valores negativos
    valores_negativos = df_despachos[df_despachos['valor'] < 0]
    if len(valores_negativos) > 0:
        print(f"⚠️ {len(valores_negativos)} registros com valor negativo")
    
    # Verificar consistência: número de registros por usina
    registros_por_usina = df_despachos.groupby('codigo_usina').agg({
        'lag': 'max',
        'patamar': 'nunique',
        'valor': 'count'
    })
    
    # Verificar se o número de registros está correto (lag_max × num_patamares)
    for codigo, row in registros_por_usina.iterrows():
        lag_max = row['lag']
        num_patamares = row['patamar']
        num_registros = row['valor']
        esperado = lag_max * num_patamares
        
        if num_registros != esperado:
            print(f"⚠️ Usina {codigo}: número de registros inconsistente "
                  f"(esperado: {esperado}, encontrado: {num_registros})")
    
    # Estatísticas gerais
    print("\nEstatísticas gerais:")
    print(f"  Total de registros: {len(df_despachos)}")
    print(f"  Usinas únicas: {df_despachos['codigo_usina'].nunique()}")
    print(f"  Lag máximo: {df_despachos['lag'].max()}")
    print(f"  Patamares únicos: {sorted(df_despachos['patamar'].unique())}")
    print(f"  Soma total: {df_despachos['valor'].sum():.2f} MW")
    print(f"  Média: {df_despachos['valor'].mean():.2f} MW")
    print(f"  Mínimo: {df_despachos['valor'].min():.2f} MW")
    print(f"  Máximo: {df_despachos['valor'].max():.2f} MW")
    
    print("\n✅ Validação concluída")
else:
    print("ℹ️ Arquivo vazio ou não encontrado")
```

#### 4.9. Modificação e Gravação

```python
from inewave.newave import Adterm

# Ler o arquivo
adterm = Adterm.read("adterm.dat")

if adterm.despachos is not None:
    # Modificar valor de um despacho específico
    codigo_usina = 1
    lag = 1
    patamar = 1
    
    mask = (
        (adterm.despachos['codigo_usina'] == codigo_usina) &
        (adterm.despachos['lag'] == lag) &
        (adterm.despachos['patamar'] == patamar)
    )
    
    if mask.any():
        novo_valor = 100.0  # MW
        adterm.despachos.loc[mask, 'valor'] = novo_valor
        print(f"Despacho antecipado atualizado para {novo_valor} MW")
    
    # Adicionar novo despacho antecipado
    import pandas as pd
    
    novo_despacho = pd.DataFrame({
        'codigo_usina': [2],
        'nome_usina': ['TermoGNL'],
        'lag': [1],
        'patamar': [1],
        'valor': [50.0]  # MW
    })
    
    adterm.despachos = pd.concat([adterm.despachos, novo_despacho], ignore_index=True)
    print("Novo despacho antecipado adicionado")
    
    # Remover despachos de uma usina específica
    codigo_remover = 3
    mask_remover = adterm.despachos['codigo_usina'] == codigo_remover
    
    if mask_remover.any():
        adterm.despachos = adterm.despachos[~mask_remover]
        print(f"Despachos da usina {codigo_remover} removidos")
    
    # Salvar alterações
    adterm.write("adterm.dat")
```

#### 4.10. Integração com CONFT.DAT

```python
from inewave.newave import Adterm
from inewave.newave import Conft

adterm = Adterm.read("adterm.dat")
conft = Conft.read("conft.dat")

if adterm.despachos is not None and conft.usinas is not None:
    # Verificar se as usinas no ADTERM existem no CONFT
    codigos_adterm = set(adterm.despachos['codigo_usina'].unique())
    codigos_conft = set(conft.usinas['codigo_usina'].unique())
    
    codigos_inexistentes = codigos_adterm - codigos_conft
    
    if codigos_inexistentes:
        print(f"⚠️ {len(codigos_inexistentes)} usina(s) no ADTERM.DAT não encontrada(s) no CONFT.DAT:")
        print(f"   Códigos: {sorted(codigos_inexistentes)}")
        print("   As usinas devem estar declaradas no CONFT.DAT antes de serem usadas no ADTERM.DAT")
    else:
        print("✅ Todas as usinas no ADTERM.DAT existem no CONFT.DAT")
    
    # Verificar se são usinas GNL
    # Nota: A verificação de tipo de combustível requer conhecimento do CONFT.DAT
    # Esta é uma validação conceitual - na prática, seria necessário verificar o tipo de combustível
    print("\nℹ️ Verifique manualmente se as usinas são do tipo GNL")
```

#### 4.11. Análise de Consistência de Lag por Classe Térmica

```python
from inewave.newave import Adterm
from inewave.newave import Conft

adterm = Adterm.read("adterm.dat")
conft = Conft.read("conft.dat")

if adterm.despachos is not None and conft.usinas is not None:
    # Verificar se usinas da mesma classe térmica têm o mesmo lag
    # Nota: Esta validação requer mapeamento de usinas para classes térmicas
    # que pode estar no CONFT.DAT ou CLAST.DAT
    
    # Agrupar por usina e obter lag máximo
    lag_por_usina = adterm.despachos.groupby('codigo_usina')['lag'].max()
    
    print("Lag de antecipação por usina:")
    for codigo, lag in lag_por_usina.items():
        nome = adterm.despachos[
            adterm.despachos['codigo_usina'] == codigo
        ]['nome_usina'].iloc[0]
        print(f"  Usina {codigo} ({nome}): lag = {lag}")
    
    print("\nℹ️ Verifique manualmente se usinas da mesma classe térmica têm o mesmo lag")
    print("   (Regra: duas usinas a GNL da mesma classe térmica devem ter o mesmo lag)")
```

---

### 5. Observações Importantes

1. **Habilitação**: 
   - O arquivo só é considerado se o registro 55 do `dger.dat` for igual a 1
   - Se não estiver habilitado, o arquivo é ignorado mesmo que exista

2. **Estrutura de registros**: 
   - Cada usina começa com um Registro Tipo 1 (identificação: código, nome, lag)
   - Seguem-se `nlag` Registros Tipo 2 (um para cada lag, do 1 ao `nlag`)
   - Cada Registro Tipo 2 contém valores para todos os patamares (até 5)

3. **Lag de antecipação**: 
   - O lag indica quantos meses à frente o despacho será antecipado
   - Lag 1 = mês inicial do período de simulação
   - Lag `nlag` = mês inicial + `nlag` - 1
   - Usinas da mesma classe térmica devem ter o mesmo lag

4. **Limites de geração**: 
   - A geração antecipada deve estar entre a geração mínima e máxima da usina
   - O programa pode ajustar automaticamente se o valor exceder a capacidade máxima

5. **Unicidade**: 
   - Não é permitida a declaração de mais de um bloco de dados para a mesma usina

6. **Dependências**: 
   - As usinas devem estar declaradas no `CONFT.DAT` antes de serem usadas no `ADTERM.DAT`
   - O número de patamares é definido no `SISTEMA.DAT`

7. **DataFrame pandas**: 
   - A propriedade `despachos` retorna um DataFrame do pandas
   - Cada linha representa uma combinação de usina × lag × patamar

8. **Expansão de dados**: 
   - A biblioteca expande cada Registro Tipo 2 em múltiplas linhas (uma por patamar)
   - O número total de linhas = número de usinas × lag máximo × número de patamares

9. **Final do arquivo**: 
   - O código `9999` no Campo 1 do Registro Tipo 1 indica o final do arquivo

10. **Comentários iniciais**: 
    - Os dois registros de comentário no início do arquivo são obrigatórios mas ignorados pelo programa

11. **Contexto NEWDESP**: 
    - O arquivo é usado pelo módulo NEWDESP para calcular o despacho ótimo
    - A informação é uma variável de estado na Função de Custo Futuro (FCF)

12. **Variável de estado**: 
    - O despacho antecipado é uma variável de estado crucial para a FCF
    - Relaciona-se com volumes armazenados e coeficientes de Benders ($\pi^{GNL}$)

13. **LAGMAX**: 
    - O número máximo de meses de antecipação (`LAGMAX`) é lido no `cortesh.dat`

14. **Validação**: 
    - É recomendado validar se as usinas existem no `CONFT.DAT`
    - Verificar se os valores estão dentro dos limites (mínimo e máximo)
    - Validar se usinas da mesma classe térmica têm o mesmo lag

15. **Unidade**: 
    - Todos os valores são em MW (megawatts)

16. **Ordem cronológica**: 
    - Os registros Tipo 2 devem seguir a ordem cronológica dos lags (1, 2, 3, ..., `nlag`)

17. **Ajuste automático**: 
    - Se a capacidade máxima for inferior ao valor antecipado, o programa ajusta automaticamente
    - O valor antecipado será igualado à geração térmica máxima

18. **Patamares**: 
    - O número de patamares é determinado pelo `SISTEMA.DAT`
    - O arquivo suporta até 5 patamares

---

**Próximo arquivo a ser documentado...**

