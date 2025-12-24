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
