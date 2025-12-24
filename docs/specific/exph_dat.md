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
