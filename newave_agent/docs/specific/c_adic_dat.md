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
