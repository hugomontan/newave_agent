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

