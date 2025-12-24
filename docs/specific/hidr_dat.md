## HIDR.DAT

### 1. Informações do Arquivo

#### 1.1. Nome e Descrição

- **Nome do arquivo**: `hidr.dat` ou `HIDR.DAT`
- **Tipo**: Arquivo de entrada essencial do modelo NEWAVE
- **Função**: Contém os dados de **cadastro** das usinas hidrelétricas, incluindo seus dados físicos e operacionais básicos

#### 1.2. Função e Responsabilidade

**Conteúdo Principal:**
O `HIDR.DAT` contém os dados de **cadastro** das usinas hidrelétricas, incluindo seus dados físicos e operacionais básicos.

**Acesso e Formato:**
- É um arquivo de **acesso direto e não formatado** (arquivo binário)
- Diferente dos outros arquivos NEWAVE que são arquivos de texto formatado

**Responsabilidade:**
Este arquivo é de **responsabilidade do ONS (Operador Nacional do Sistema Elétrico)**, não devendo ser alterado pelo usuário.

#### 1.3. Estrutura e Dimensão

**Registros:**
- O arquivo possui **320 ou 600 registros**, onde cada registro corresponde a uma usina
- A numeração das usinas hidrelétricas deve seguir o número do registro no qual essa usina está cadastrada no `HIDR.DAT`

**Formato:**
- Arquivo binário de acesso direto
- Cada registro contém informações completas de uma usina hidrelétrica
- A estrutura interna do arquivo é gerenciada pela biblioteca inewave

#### 1.4. Relação com Outros Arquivos

Embora o `HIDR.DAT` seja o cadastro base, seus dados podem ser complementados ou modificados por outros arquivos de entrada:

**`CONFHD.DAT` (Configuração Hidrelétrica):**
- Este arquivo de configuração usa o código da usina (Campo 1) que está no cadastro do `HIDR.DAT`
- O `CONFHD.DAT` associa cada usina a um REE e define configurações específicas do estudo

**`MODIF.DAT` (Alteração de Características):**
- Se o campo `Índice de modificação` no `CONFHD.DAT` for 1, um conjunto restrito de dados lidos do `HIDR.DAT` pode ser modificado através do `MODIF.DAT`
- Permite alterar características como volume mínimo/máximo, produtibilidade, vazão mínima, etc.

**Outros arquivos relacionados:**
- `VAZOES.DAT`: Define os postos de vazões referenciados no cadastro
- `EXPH.DAT`: Define expansões hidrelétricas para usinas com status EE ou NE

---

### 2. Propriedades da Biblioteca inewave

#### 2.1. Classe Correspondente

**Classe**: `Hidr`

```python
class Hidr(data=Ellipsis)
```

**Descrição**: Armazena os dados de entrada do NEWAVE referentes ao cadastro das usinas hidroelétricas.

**Características:**
- Herda de `RegisterFile`
- Usa armazenamento binário (`STORAGE = "BINARY"`)
- Cada registro é do tipo `RegistroUHEHidr`

#### 2.2. Propriedades Disponíveis

##### `property` **cadastro**: `pd.DataFrame`

- **Descrição**: Obtém a tabela com os dados cadastrais existentes no arquivo binário
- **Tipo de retorno**: `pd.DataFrame` (não retorna `None`, mas pode estar vazio)
- **Colunas do DataFrame** (mais de 60 campos):

**Informações Básicas:**
- `nome_usina` (`str`): Nome da usina (12 caracteres)
- `posto` (`int`): Posto de vazão natural da usina
- `submercado` (`int`): Submercado da usina
- `empresa` (`int`): Agente responsável pela usina
- `codigo_usina_jusante` (`int`): Posto à jusante da usina
- `desvio` (`float`): Desvio (TODO - documentação pendente)
- `data` (`str`): Data no formato DD-MM-AA
- `observacao` (`str`): Observação qualquer sobre a usina

**Volumes e Cotas:**
- `volume_minimo` (`float`): Volume mínimo da usina (hm³)
- `volume_maximo` (`float`): Volume máximo da usina (hm³)
- `volume_vertedouro` (`float`): Volume do vertedouro da usina (hm³)
- `volume_desvio` (`float`): Volume de desvio (TODO - documentação pendente)
- `volume_referencia` (`float`): Volume de referência (TODO - documentação pendente)
- `cota_minima` (`float`): Cota mínima da usina (m)
- `cota_maxima` (`float`): Cota máxima da usina (m)

**Polinômios Volume-Cota e Cota-Área:**
- `a0_volume_cota` (`float`): Coeficiente 0 do polinômio volume-cota
- `a1_volume_cota` (`float`): Coeficiente 1 do polinômio volume-cota
- `a2_volume_cota` (`float`): Coeficiente 2 do polinômio volume-cota
- `a3_volume_cota` (`float`): Coeficiente 3 do polinômio volume-cota
- `a4_volume_cota` (`float`): Coeficiente 4 do polinômio volume-cota
- `a0_cota_area` (`float`): Coeficiente 0 do polinômio cota-área
- `a1_cota_area` (`float`): Coeficiente 1 do polinômio cota-área
- `a2_cota_area` (`float`): Coeficiente 2 do polinômio cota-área
- `a3_cota_area` (`float`): Coeficiente 3 do polinômio cota-área
- `a4_cota_area` (`float`): Coeficiente 4 do polinômio cota-área

**Evaporação:**
- `evaporacao_JAN` (`float`): Coeficiente de evaporação para janeiro (mm)
- `evaporacao_FEV` (`float`): Coeficiente de evaporação para fevereiro (mm)
- `evaporacao_MAR` (`float`): Coeficiente de evaporação para março (mm)
- `evaporacao_ABR` (`float`): Coeficiente de evaporação para abril (mm)
- `evaporacao_MAI` (`float`): Coeficiente de evaporação para maio (mm)
- `evaporacao_JUN` (`float`): Coeficiente de evaporação para junho (mm)
- `evaporacao_JUL` (`float`): Coeficiente de evaporação para julho (mm)
- `evaporacao_AGO` (`float`): Coeficiente de evaporação para agosto (mm)
- `evaporacao_SET` (`float`): Coeficiente de evaporação para setembro (mm)
- `evaporacao_OUT` (`float`): Coeficiente de evaporação para outubro (mm)
- `evaporacao_NOV` (`float`): Coeficiente de evaporação para novembro (mm)
- `evaporacao_DEZ` (`float`): Coeficiente de evaporação para dezembro (mm)

**Conjuntos de Máquinas (até 5 conjuntos):**
- `numero_conjuntos_maquinas` (`int`): Número de conjuntos de máquinas
- `maquinas_conjunto_1` (`int`): Número de máquinas no conjunto 1
- `maquinas_conjunto_2` (`int`): Número de máquinas no conjunto 2
- `maquinas_conjunto_3` (`int`): Número de máquinas no conjunto 3
- `maquinas_conjunto_4` (`int`): Número de máquinas no conjunto 4
- `maquinas_conjunto_5` (`int`): Número de máquinas no conjunto 5
- `potencia_nominal_conjunto_1` (`float`): Potência das máquinas do conjunto 1 (MWmed)
- `potencia_nominal_conjunto_2` (`float`): Potência das máquinas do conjunto 2 (MWmed)
- `potencia_nominal_conjunto_3` (`float`): Potência das máquinas do conjunto 3 (MWmed)
- `potencia_nominal_conjunto_4` (`float`): Potência das máquinas do conjunto 4 (MWmed)
- `potencia_nominal_conjunto_5` (`float`): Potência das máquinas do conjunto 5 (MWmed)
- `queda_nominal_conjunto_1` (`float`): Altura nominal de queda do conjunto 1 (m)
- `queda_nominal_conjunto_2` (`float`): Altura nominal de queda do conjunto 2 (m)
- `queda_nominal_conjunto_3` (`float`): Altura nominal de queda do conjunto 3 (m)
- `queda_nominal_conjunto_4` (`float`): Altura nominal de queda do conjunto 4 (m)
- `queda_nominal_conjunto_5` (`float`): Altura nominal de queda do conjunto 5 (m)
- `vazao_nominal_conjunto_1` (`float`): Vazão nominal do conjunto 1 (m³/s)
- `vazao_nominal_conjunto_2` (`float`): Vazão nominal do conjunto 2 (m³/s)
- `vazao_nominal_conjunto_3` (`float`): Vazão nominal do conjunto 3 (m³/s)
- `vazao_nominal_conjunto_4` (`float`): Vazão nominal do conjunto 4 (m³/s)
- `vazao_nominal_conjunto_5` (`float`): Vazão nominal do conjunto 5 (m³/s)

**Características Operacionais:**
- `produtibilidade_especifica` (`float`): Produtibilidade específica
- `perdas` (`float`): Perdas da usina
- `vazao_minima_historica` (`float`): Vazão mínima da usina (m³/s)
- `canal_fuga_medio` (`float`): Cota média do canal de fuga (m)
- `tipo_regulacao` (`str`): Tipo de regulação (D, S ou M)

**Polinômios de Jusante (até 6 polinômios):**
- `numero_polinomios_jusante` (`int`): Número de polinômios de jusante
- `a0_jusante_1` até `a4_jusante_1` (`float`): Coeficientes do polinômio de jusante 1
- `a0_jusante_2` até `a4_jusante_2` (`float`): Coeficientes do polinômio de jusante 2
- `a0_jusante_3` até `a4_jusante_3` (`float`): Coeficientes do polinômio de jusante 3
- `a0_jusante_4` até `a4_jusante_4` (`float`): Coeficientes do polinômio de jusante 4
- `a0_jusante_5` até `a4_jusante_5` (`float`): Coeficientes do polinômio de jusante 5
- `a0_jusante_6` até `a4_jusante_6` (`float`): Coeficientes do polinômio de jusante 6
- `referencia_jusante_1` até `referencia_jusante_6` (`float`): Coeficientes do polinjus de referência

**Campos Adicionais (documentação pendente):**
- `influencia_vertimento_canal_fuga` (`int`): TODO (0 ou 1)
- `fator_carga_maximo` (`float`): TODO (%)
- `fator_carga_minimo` (`float`): TODO (%)
- `numero_unidades_base` (`int`): TODO
- `tipo_turbina` (`int`): TODO
- `representacao_conjunto` (`int`): TODO
- `teif` (`float`): TODO (%)
- `ip` (`float`): TODO (%)
- `tipo_perda` (`int`): TODO

**Observações:**
- O DataFrame contém todas as informações cadastrais de cada usina
- Cada linha representa uma usina hidrelétrica
- O índice do DataFrame corresponde ao número do registro (código da usina)
- Alguns campos têm documentação pendente (marcados como TODO)
- O DataFrame é construído a partir dos registros binários do arquivo

---

### 3. Mapeamento de Campos

O arquivo `HIDR.DAT` é um arquivo binário de acesso direto, onde cada registro contém informações de uma usina. A biblioteca inewave converte esses registros binários em um DataFrame pandas com mais de 60 colunas.

**Principais grupos de campos mapeados:**

| Grupo de Campos | Colunas no DataFrame | Descrição |
| :--- | :--- | :--- |
| **Informações Básicas** | `nome_usina`, `posto`, `submercado`, `empresa`, `codigo_usina_jusante` | Dados de identificação e localização |
| **Volumes** | `volume_minimo`, `volume_maximo`, `volume_vertedouro`, `volume_desvio`, `volume_referencia` | Volumes do reservatório (hm³) |
| **Cotas** | `cota_minima`, `cota_maxima` | Cotas do reservatório (m) |
| **Polinômios Volume-Cota** | `a0_volume_cota` até `a4_volume_cota` | Coeficientes do polinômio volume-cota |
| **Polinômios Cota-Área** | `a0_cota_area` até `a4_cota_area` | Coeficientes do polinômio cota-área |
| **Evaporação** | `evaporacao_JAN` até `evaporacao_DEZ` | Coeficientes mensais de evaporação (mm) |
| **Conjuntos de Máquinas** | `numero_conjuntos_maquinas`, `maquinas_conjunto_[1-5]`, `potencia_nominal_conjunto_[1-5]`, `queda_nominal_conjunto_[1-5]`, `vazao_nominal_conjunto_[1-5]` | Características dos conjuntos de máquinas |
| **Características Operacionais** | `produtibilidade_especifica`, `perdas`, `vazao_minima_historica`, `canal_fuga_medio`, `tipo_regulacao` | Parâmetros operacionais |
| **Polinômios de Jusante** | `numero_polinomios_jusante`, `a[0-4]_jusante_[1-6]`, `referencia_jusante_[1-6]` | Polinômios de jusante |

**Nota**: Devido à natureza binária do arquivo e à complexidade da estrutura, o mapeamento completo campo-a-campo não é apresentado aqui. A biblioteca inewave abstrai essa complexidade fornecendo acesso direto através do DataFrame.

---

### 4. Exemplos de Uso

#### 4.1. Leitura do Arquivo

```python
from inewave.newave import Hidr

# Ler o arquivo hidr.dat (binário)
hidr = Hidr.read("hidr.dat")

# Acessar o cadastro completo
cadastro = hidr.cadastro

if cadastro is not None:
    print(f"Total de usinas hidrelétricas: {len(cadastro)}")
    print(f"Total de colunas: {len(cadastro.columns)}")
    print("\nPrimeiras 5 usinas:")
    print(cadastro.head())
else:
    print("Nenhuma usina encontrada ou arquivo vazio")
```

#### 4.2. Consulta de Usina Específica

```python
from inewave.newave import Hidr

hidr = Hidr.read("hidr.dat")

if hidr.cadastro is not None:
    # Consultar uma usina específica pelo índice (código da usina)
    codigo_usina = 1
    usina = hidr.cadastro.iloc[codigo_usina - 1]  # Índice é 0-based
    
    print(f"Usina {codigo_usina}: {usina['nome_usina']}")
    print(f"  Posto: {usina['posto']}")
    print(f"  Submercado: {usina['submercado']}")
    print(f"  Volume máximo: {usina['volume_maximo']} hm³")
    print(f"  Volume mínimo: {usina['volume_minimo']} hm³")
```

#### 4.3. Consulta por Nome de Usina

```python
from inewave.newave import Hidr

hidr = Hidr.read("hidr.dat")

if hidr.cadastro is not None:
    # Filtrar por nome da usina (busca parcial, case-insensitive)
    nome_procurado = "Itaipu"
    usinas_encontradas = hidr.cadastro[
        hidr.cadastro['nome_usina'].str.contains(nome_procurado, case=False, na=False)
    ]
    
    print(f"Usinas encontradas para '{nome_procurado}':")
    print(usinas_encontradas[['nome_usina', 'posto', 'submercado', 'volume_maximo']])
```

#### 4.4. Análise de Volumes dos Reservatórios

```python
from inewave.newave import Hidr

hidr = Hidr.read("hidr.dat")

if hidr.cadastro is not None:
    # Estatísticas dos volumes
    print("Estatísticas dos volumes dos reservatórios (hm³):")
    print(hidr.cadastro[['volume_minimo', 'volume_maximo', 'volume_vertedouro']].describe())
    
    # Usinas com maiores volumes máximos
    print("\nTop 10 usinas com maiores volumes máximos:")
    top_volumes = hidr.cadastro.nlargest(10, 'volume_maximo')
    print(top_volumes[['nome_usina', 'volume_maximo', 'volume_minimo']])
```

#### 4.5. Cálculo de Potência Total Instalada

```python
from inewave.newave import Hidr

hidr = Hidr.read("hidr.dat")

if hidr.cadastro is not None:
    # Calcular potência total instalada por usina
    cadastro_com_potencia = hidr.cadastro.copy()
    cadastro_com_potencia['potencia_total'] = 0
    
    for i in range(1, 6):
        pot_col = f'potencia_nominal_conjunto_{i}'
        maq_col = f'maquinas_conjunto_{i}'
        
        if pot_col in cadastro_com_potencia.columns and maq_col in cadastro_com_potencia.columns:
            cadastro_com_potencia['potencia_total'] += (
                cadastro_com_potencia[pot_col] * cadastro_com_potencia[maq_col]
            )
    
    print("Usinas com maior capacidade instalada:")
    top_potencia = cadastro_com_potencia.nlargest(10, 'potencia_total')
    print(top_potencia[['nome_usina', 'potencia_total']])
```

#### 4.6. Análise por Submercado

```python
from inewave.newave import Hidr

hidr = Hidr.read("hidr.dat")

if hidr.cadastro is not None:
    # Contar usinas por submercado
    usinas_por_submercado = hidr.cadastro.groupby('submercado').agg({
        'nome_usina': 'count',
        'volume_maximo': 'sum',
        'potencia_total': 'sum'  # Se calculado anteriormente
    })
    
    usinas_por_submercado.columns = ['quantidade', 'volume_total_hm3', 'potencia_total_mw']
    
    print("Distribuição de usinas por submercado:")
    print(usinas_por_submercado)
```

#### 4.7. Análise de Evaporação

```python
from inewave.newave import Hidr

hidr = Hidr.read("hidr.dat")

if hidr.cadastro is not None:
    # Calcular evaporação média anual por usina
    meses = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 
             'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
    
    colunas_evap = [f'evaporacao_{mes}' for mes in meses]
    colunas_existentes = [col for col in colunas_evap if col in hidr.cadastro.columns]
    
    if colunas_existentes:
        hidr.cadastro['evaporacao_media_anual'] = hidr.cadastro[colunas_existentes].mean(axis=1)
        
        print("Usinas com maior evaporação média anual:")
        top_evap = hidr.cadastro.nlargest(10, 'evaporacao_media_anual')
        print(top_evap[['nome_usina', 'evaporacao_media_anual']])
```

#### 4.8. Consulta de Características de Máquinas

```python
from inewave.newave import Hidr

hidr = Hidr.read("hidr.dat")

if hidr.cadastro is not None:
    # Filtrar usinas com múltiplos conjuntos de máquinas
    usinas_multiplos_conjuntos = hidr.cadastro[
        hidr.cadastro['numero_conjuntos_maquinas'] > 1
    ]
    
    print(f"Usinas com múltiplos conjuntos: {len(usinas_multiplos_conjuntos)}")
    
    # Analisar características do primeiro conjunto
    if 'potencia_nominal_conjunto_1' in hidr.cadastro.columns:
        print("\nEstatísticas da potência nominal do conjunto 1:")
        print(hidr.cadastro['potencia_nominal_conjunto_1'].describe())
```

#### 4.9. Validação de Dados

```python
from inewave.newave import Hidr

hidr = Hidr.read("hidr.dat")

if hidr.cadastro is not None:
    cadastro = hidr.cadastro
    
    # Verificar se há dados
    if len(cadastro) == 0:
        print("⚠️ Nenhuma usina encontrada no arquivo")
    
    # Verificar volumes válidos
    volumes_invalidos = cadastro[
        (cadastro['volume_maximo'] < cadastro['volume_minimo']) |
        (cadastro['volume_maximo'] <= 0)
    ]
    
    if len(volumes_invalidos) > 0:
        print(f"⚠️ {len(volumes_invalidos)} usinas com volumes inválidos")
    
    # Verificar cotas válidas
    cotas_invalidas = cadastro[
        (cadastro['cota_maxima'] < cadastro['cota_minima']) |
        (cadastro['cota_maxima'] <= 0)
    ]
    
    if len(cotas_invalidas) > 0:
        print(f"⚠️ {len(cotas_invalidas)} usinas com cotas inválidas")
    
    # Verificar número de conjuntos válido (1-5)
    conjuntos_invalidos = cadastro[
        (cadastro['numero_conjuntos_maquinas'] < 1) |
        (cadastro['numero_conjuntos_maquinas'] > 5)
    ]
    
    if len(conjuntos_invalidos) > 0:
        print(f"⚠️ {len(conjuntos_invalidos)} usinas com número de conjuntos inválido")
    
    # Verificar tipo de regulação válido
    if 'tipo_regulacao' in cadastro.columns:
        tipos_validos = ['D', 'S', 'M']
        tipos_invalidos = cadastro[~cadastro['tipo_regulacao'].isin(tipos_validos)]
        
        if len(tipos_invalidos) > 0:
            print(f"⚠️ {len(tipos_invalidos)} usinas com tipo de regulação inválido")
```

#### 4.10. Modificação e Gravação

```python
from inewave.newave import Hidr

# Ler o arquivo
hidr = Hidr.read("hidr.dat")

if hidr.cadastro is not None:
    # Modificar volume máximo de uma usina específica
    codigo_usina = 1
    novo_volume_maximo = 50000.0  # hm³
    
    # O índice do DataFrame corresponde ao código da usina - 1
    idx = codigo_usina - 1
    
    if idx < len(hidr.cadastro):
        hidr.cadastro.iloc[idx, hidr.cadastro.columns.get_loc('volume_maximo')] = novo_volume_maximo
        print(f"Volume máximo da usina {codigo_usina} atualizado para {novo_volume_maximo} hm³")
    
    # Salvar alterações
    # Nota: A biblioteca atualiza os registros internos antes de gravar
    hidr.write("hidr.dat")
```

#### 4.11. Análise de Polinômios

```python
from inewave.newave import Hidr

hidr = Hidr.read("hidr.dat")

if hidr.cadastro is not None:
    # Analisar polinômios volume-cota
    colunas_polin_vc = [f'a{i}_volume_cota' for i in range(5)]
    colunas_existentes_vc = [col for col in colunas_polin_vc if col in hidr.cadastro.columns]
    
    if colunas_existentes_vc:
        print("Estatísticas dos coeficientes do polinômio volume-cota:")
        print(hidr.cadastro[colunas_existentes_vc].describe())
    
    # Analisar polinômios de jusante
    if 'numero_polinomios_jusante' in hidr.cadastro.columns:
        distribuicao_polinjus = hidr.cadastro['numero_polinomios_jusante'].value_counts().sort_index()
        print("\nDistribuição do número de polinômios de jusante:")
        print(distribuicao_polinjus)
```

---

### 5. Observações Importantes

1. **Arquivo binário**: O `HIDR.DAT` é um arquivo binário de acesso direto, diferente dos outros arquivos NEWAVE que são texto formatado

2. **Responsabilidade do ONS**: Este arquivo é de responsabilidade do ONS e não deve ser alterado pelo usuário, exceto em casos específicos de estudos

3. **Número de registros**: O arquivo possui 320 ou 600 registros, onde cada registro corresponde a uma usina

4. **Numeração**: A numeração das usinas hidrelétricas deve seguir o número do registro no qual essa usina está cadastrada no `HIDR.DAT`

5. **Modificações**: 
   - Dados do `HIDR.DAT` podem ser modificados através do arquivo `MODIF.DAT`
   - Para isso, o campo `Índice de modificação` no `CONFHD.DAT` deve ser igual a 1

6. **Relação com CONFHD**: 
   - O `CONFHD.DAT` usa o código da usina que está no cadastro do `HIDR.DAT`
   - Os dois arquivos devem estar consistentes

7. **Estrutura complexa**: 
   - O DataFrame retornado pela propriedade `cadastro` contém mais de 60 colunas
   - Inclui polinômios, evaporação mensal, múltiplos conjuntos de máquinas, etc.

8. **Campos com documentação pendente**: 
   - Alguns campos estão marcados como "TODO" na biblioteca
   - Esses campos podem ter significado específico no contexto do NEWAVE

9. **Polinômios**: 
   - Os polinômios volume-cota e cota-área são fundamentais para cálculos de energia armazenada
   - Os polinômios de jusante modelam a relação com usinas a jusante

10. **Conjuntos de máquinas**: 
    - Uma usina pode ter até 5 conjuntos de máquinas
    - Cada conjunto tem suas próprias características (potência, queda, vazão)

11. **Evaporação**: 
    - Coeficientes de evaporação são fornecidos mensalmente
    - Importante para cálculo de perdas por evaporação

12. **Tipo de regulação**: 
    - Pode ser D (diária), S (semanal) ou M (mensal)
    - Afeta a modelagem operacional da usina

13. **DataFrame pandas**: 
    - A propriedade `cadastro` retorna um DataFrame do pandas
    - Permite uso completo das funcionalidades do pandas para análise e manipulação

14. **Gravação**: 
    - Ao modificar o DataFrame e gravar, a biblioteca atualiza automaticamente os registros binários
    - Use com cuidado, pois o arquivo é de responsabilidade do ONS

15. **Dependências**: 
    - Os postos de vazões referenciados devem estar no arquivo `vazoes.dat`
    - As modificações devem estar no arquivo `MODIF.DAT` (se aplicável)
    - A configuração deve estar no arquivo `CONFHD.DAT`

---
