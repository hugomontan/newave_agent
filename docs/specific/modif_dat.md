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
