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
