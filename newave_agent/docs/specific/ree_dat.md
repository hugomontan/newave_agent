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
