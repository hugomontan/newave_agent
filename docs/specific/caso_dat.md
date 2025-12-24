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
