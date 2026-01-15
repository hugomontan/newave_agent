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
