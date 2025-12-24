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
