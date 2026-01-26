# Matching de Usinas por Tool - Análise Detalhada

## 📋 Sumário

1. [Matcher Centralizado](#matcher-centralizado)
2. [Usinas Térmicas](#usinas-térmicas)
3. [Usinas Hidrelétricas](#usinas-hidrelétricas)
4. [Multi-Deck Tools](#multi-deck-tools)
5. [Resumo Comparativo](#resumo-comparativo)

---

## Matcher Centralizado

### Localização
`backend/core/utils/usina_name_matcher.py`

### Funções Principais

#### `normalize_usina_name(name: str) -> str`
**O que faz**: Normaliza nomes de usinas para comparação.

**Processo**:
1. Converte para minúsculas
2. Remove acentos (á → a, é → e, etc.)
3. Remove caracteres especiais
4. Normaliza espaços múltiplos

**Limitações**:
- Não trata abreviações ("SC" vs "Santa Cruz")
- Não trata números romanos ("I", "II", "III")
- Não remove prefixos ("Usina", "UTE", "UH")
- Não normaliza pontuação variada ("P.Sergipe" vs "PSergipe")

#### `find_usina_match(query: str, available_names: list, threshold: float = 0.5) -> Optional[Tuple[str, float]]`
**O que faz**: Encontra melhor match de usina usando fuzzy matching.

**Algoritmo**: `SequenceMatcher` (difflib)

**Processo**:
1. Normaliza query e cada nome disponível
2. Calcula similaridade usando `SequenceMatcher.ratio()`
3. Bônus de 0.7 se nome está contido na query (ou vice-versa)
4. Score 1.0 se match exato após normalização
5. Retorna melhor match se `score >= threshold`

**Limitações**:
- Algoritmo simples (SequenceMatcher)
- Não considera ordem de palavras
- Threshold fixo (0.5)
- Não trata contexto (pode pegar contexto ao redor do nome)

---

## Usinas Térmicas

### 1. CT Tool (CTUsinasTermelétricasTool)

**Localização**: `backend/decomp/tools/ct_usinas_termelétricas_tool.py`

**Fonte de Dados**: Bloco CT do DECOMP (usinas térmicas)

**Estratégia de Matching**:

#### ETAPA 1: Extração por Padrão Numérico
```python
Padrões testados:
- "usina 123"
- "usina térmica 123"
- "ute 123"
- "código 123"
```
- Valida se código existe nos dados antes de retornar
- Early return se encontrado

#### ETAPA 2: Matcher Centralizado
- Usa `find_usina_match()` com threshold 0.5
- Cria lista de usinas do bloco CT
- Se encontrar match, busca código correspondente

#### ETAPA 3: Fallback - Match Exato
- Ordena usinas por tamanho do nome (maior primeiro)
- Match exato: nome completo igual à query
- Match parcial: nome completo contido na query (com word boundaries)
- Requer nome com pelo menos 4 caracteres

#### ETAPA 4: Fallback - Palavras-Chave
- Ignora stopwords: 'de', 'da', 'do', 'usina', 'ute', 'térmica', etc.
- Filtra palavras com mais de 3 caracteres
- Requer: 2+ palavras encontradas OU 1 palavra com 6+ caracteres
- Prioriza usina com mais palavras em comum

**Características**:
- ✅ Usa matcher centralizado
- ✅ Validação de código antes de retornar
- ✅ Múltiplas estratégias em cascata
- ⚠️ Pode pegar contexto ao redor do nome

---

### 2. Patamar Calculation Base

**Localização**: `backend/decomp/tools/patamar_calculation_base.py`

**Herdeiras**: 
- `DisponibilidadeUsinaTool`
- `InflexibilidadeUsinaTool`
- `CVUUsinaTool`

**Fonte de Dados**: Bloco CT do DECOMP (usinas térmicas)

**Estratégia de Matching** (versão otimizada):

#### ETAPA 1: Extração por Padrão Numérico
- Usa patterns pré-compilados (constantes de classe)
- Validação com códigos válidos extraídos uma vez (vetorizado)
- Early return se encontrado

#### ETAPA 2: Busca por Nome (Otimizada)
- **PRIORIDADE 0**: Matcher centralizado
  - Usa `find_usina_match()` com threshold 0.5
  - Operações vetorizadas do pandas

- **PRIORIDADE 1**: Match exato (O(1))
  - Dicionário `nome_lower → codigo` para busca rápida
  - Se query normalizada está no dicionário → retorna código

- **PRIORIDADE 2**: Nome completo na query
  - Verifica se nome está contido na query
  - Usa word boundaries para precisão
  - Prioriza matches mais longos (mais específicos)

- **PRIORIDADE 3**: Todas palavras significativas
  - Verifica se todas as palavras do nome estão na query
  - Ignora stopwords

- **PRIORIDADE 4**: Similaridade (fallback)
  - Apenas se não encontrou antes

**Características**:
- ✅ Versão otimizada com operações vetorizadas
- ✅ Usa matcher centralizado
- ✅ Múltiplas prioridades bem definidas
- ✅ Performance melhorada (pandas vetorizado)
- ⚠️ Ainda pode pegar contexto

---

### 3. GL Tool (GLGeracoesGNLTool)

**Localização**: `backend/decomp/tools/gl_geracoes_gnl_tool.py`

**Fonte de Dados**: Registro GL (gerações GNL já comandadas)

**Estratégia de Matching**:

#### ETAPA 1: Extração por Padrão Numérico
```python
Padrões testados:
- "usina 86"
- "ute 86"
- "gl 86"
- "código 86"
```

#### ETAPA 2: Mapeamento Hardcoded
```python
usinas_conhecidas = {
    "santa cruz": 86,
    "luiz ormelo": 15,
    "luizormelo": 15,
    "psergipe": 224,
    "psergipe i": 224,
}
```
- Busca simples: `if nome in query_lower`
- Não usa matcher centralizado
- Não usa fuzzy matching

**Mapeamento Código → Nome** (também hardcoded):
```python
mapeamento_gl = {
    86: "SANTA CRUZ",
    224: "PSERGIPE I",
}
```

**Características**:
- ❌ Não usa matcher centralizado
- ❌ Mapeamento hardcoded (apenas 4 usinas)
- ❌ Não escala
- ❌ Não cobre variações
- ⚠️ Busca simples por substring (pode dar falso positivo)

---

## Usinas Hidrelétricas

### 1. UH Tool (UHUsinasHidrelétricasTool)

**Localização**: `backend/decomp/tools/uh_usinas_hidreletricas_tool.py`

**Fonte de Dados**: Bloco UH do DECOMP + HIDR.DAT

**Estratégia de Matching**:

#### ETAPA 1: Extração por Padrão Numérico
```python
Padrões testados:
- "usina 123"
- "uh 123"
- "código 123"
```
- Valida se código existe nos dados

#### ETAPA 2: Criação de Mapeamento (HIDR.DAT)
**Cache Global**: `_HIDR_MAPPING_CACHE`
- Cache compartilhado entre chamadas
- Prioridade de busca:
  1. `hidr.dat` do próprio deck DECOMP
  2. `HIDR.DAT` de decks NEWAVE (3 mais recentes)

**Processo de Carregamento**:
- Tenta múltiplos nomes de coluna para código e nome
- Carrega TODAS as usinas do HIDR.DAT no cache global
- Filtra apenas códigos necessários do cache

#### ETAPA 3: Busca por Nome
- Se mapeamento vazio → fallback com mapeamento conhecido hardcoded
- Filtra usinas com nomes reais (não "Usina X")
- Ordena por tamanho do nome (maior primeiro)

**Estratégias de Matching**:
1. **Match Exato**: Nome completo igual à query
2. **Match Parcial**: Nome completo na query (word boundaries, min 4 chars)
3. **Palavras-Chave**: Busca por palavras significativas
   - Ignora stopwords
   - Requer palavras com mais de 3 caracteres
   - Prioriza usina com mais palavras em comum

**Características**:
- ✅ Cache global otimizado
- ✅ Busca em múltiplas fontes (DECOMP → NEWAVE)
- ✅ Fallback com mapeamento conhecido
- ❌ Não usa matcher centralizado
- ⚠️ Pode pegar contexto ao redor do nome

---

### 2. Restrições Vazão HQ Tool

**Localização**: `backend/decomp/tools/restricoes_vazao_hq_tool.py`

**Fonte de Dados**: Bloco HQ (restrições de vazão) + HIDR.DAT

**Estratégia de Matching**:

**Código IDÊNTICO ao UH Tool** (espelhado)

#### ETAPA 1: Extração por Padrão Numérico
- Mesmos padrões do UH Tool

#### ETAPA 2: Busca por Nome
- Usa mapeamento do HIDR.DAT (mesmo processo do UH Tool)
- Fallback com mapeamento conhecido hardcoded
- Mesmas estratégias: match exato → match parcial → palavras-chave

**Características**:
- ✅ Reutiliza lógica do UH Tool
- ✅ Consistência entre tools
- ❌ Duplicação de código
- ❌ Não usa matcher centralizado

---

## Multi-Deck Tools

### 1. GL Multi-Deck Tool

**Localização**: `backend/decomp/agents/multi_deck/tools/gl_multi_deck_tool.py`

**Estratégia de Matching**:

#### ETAPA 1: Extração por Padrão Numérico
- Mesmos padrões do GL Tool single-deck

#### ETAPA 2: Mapeamento Hardcoded
- **IDÊNTICO ao GL Tool single-deck**
- Mesmas 4 usinas hardcoded
- Mesmo mapeamento código → nome

**Características**:
- ❌ Mesmas limitações do GL Tool
- ❌ Não usa matcher centralizado
- ❌ Mapeamento hardcoded

---

### 2. CVU Multi-Deck Tool

**Localização**: `backend/decomp/agents/multi_deck/tools/cvu_multi_deck_tool.py`

**Estratégia de Matching** (diferente):

#### ETAPA 1: Coleta de Nomes de Múltiplos Decks
- Carrega dadgers de até 5 decks em paralelo
- Coleta nomes de usinas do bloco CT de cada deck
- Usa `normalize_usina_name()` para criar mapeamento normalizado
- Mantém nome original mais longo quando há duplicatas

#### ETAPA 2: Matcher Centralizado
- Usa `find_usina_match()` com todos os nomes coletados
- Threshold 0.5
- Se encontrar match, busca código correspondente

#### ETAPA 3: Validação em Todos os Decks
- Verifica se código existe em cada deck
- Retorna código que existe em mais decks

**Características**:
- ✅ Usa matcher centralizado
- ✅ Coleta dados de múltiplos decks
- ✅ Normaliza nomes antes de matching
- ⚠️ Pode pegar contexto ao redor do nome

---

### 3. Inflexibilidade Multi-Deck Tool

**Localização**: `backend/decomp/agents/multi_deck/tools/inflexibilidade_multi_deck_tool.py`

**Estratégia de Matching**:

**CÓDIGO IDÊNTICO ao CVU Multi-Deck Tool**

- Mesma coleta de nomes de múltiplos decks
- Mesmo uso do matcher centralizado
- Mesma validação em todos os decks

**Características**:
- ✅ Reutiliza lógica do CVU Multi-Deck
- ✅ Consistência entre multi-deck tools
- ⚠️ Duplicação de código

---

### 4. Disponibilidade Multi-Deck Tool

**Localização**: `backend/decomp/agents/multi_deck/tools/disponibilidade_multi_deck_tool.py`

**Estratégia de Matching**:

**CÓDIGO IDÊNTICO ao CVU Multi-Deck Tool**

- Mesma estratégia de coleta e matching

---

## Resumo Comparativo

### Uso do Matcher Centralizado

| Tool | Usa Matcher Centralizado? | Observações |
|------|---------------------------|-------------|
| CT Tool | ✅ Sim | Com fallback por palavras-chave |
| Patamar Calculation Base | ✅ Sim | Versão otimizada |
| GL Tool | ❌ Não | Mapeamento hardcoded |
| UH Tool | ❌ Não | Busca direta por nome |
| Restrições Vazão HQ | ❌ Não | Código espelhado do UH Tool |
| GL Multi-Deck | ❌ Não | Mapeamento hardcoded |
| CVU Multi-Deck | ✅ Sim | Coleta de múltiplos decks |
| Inflexibilidade Multi-Deck | ✅ Sim | Código idêntico ao CVU |
| Disponibilidade Multi-Deck | ✅ Sim | Código idêntico ao CVU |

### Fonte de Dados

| Tool | Fonte Principal | Fonte Secundária | Cache |
|------|----------------|------------------|-------|
| CT Tool | Bloco CT | - | Não |
| Patamar Calculation | Bloco CT | - | Não |
| GL Tool | Registro GL | - | Não (hardcoded) |
| UH Tool | Bloco UH | HIDR.DAT | ✅ Global (`_HIDR_MAPPING_CACHE`) |
| Restrições Vazão HQ | Bloco HQ | HIDR.DAT | Não (usa mapeamento do UH) |
| GL Multi-Deck | Registro GL | - | Não (hardcoded) |
| CVU Multi-Deck | Bloco CT (múltiplos decks) | - | Não |
| Inflexibilidade Multi-Deck | Bloco CT (múltiplos decks) | - | Não |
| Disponibilidade Multi-Deck | Bloco CT (múltiplos decks) | - | Não |

### Estratégias de Matching

| Tool | Padrão Numérico | Match Exato | Match Parcial | Fuzzy Matching | Palavras-Chave |
|------|----------------|-------------|---------------|----------------|----------------|
| CT Tool | ✅ | ✅ | ✅ | ✅ (centralizado) | ✅ |
| Patamar Calculation | ✅ | ✅ | ✅ | ✅ (centralizado) | ✅ |
| GL Tool | ✅ | ❌ | ❌ | ❌ | ❌ (hardcoded) |
| UH Tool | ✅ | ✅ | ✅ | ❌ | ✅ |
| Restrições Vazão HQ | ✅ | ✅ | ✅ | ❌ | ✅ |
| GL Multi-Deck | ✅ | ❌ | ❌ | ❌ | ❌ (hardcoded) |
| CVU Multi-Deck | ❌ | ❌ | ❌ | ✅ (centralizado) | ❌ |
| Inflexibilidade Multi-Deck | ❌ | ❌ | ❌ | ✅ (centralizado) | ❌ |
| Disponibilidade Multi-Deck | ❌ | ❌ | ❌ | ✅ (centralizado) | ❌ |

### Problemas Identificados por Categoria

#### **Inconsistência de Implementação**
- Algumas tools usam matcher centralizado, outras não
- Algumas têm fallback complexo, outras são simples
- Duplicação de código (UH Tool e Restrições Vazão HQ são idênticos)
- Multi-deck tools têm estratégias diferentes

#### **Mapeamentos Hardcoded**
- GL Tool: 4 usinas hardcoded
- GL Multi-Deck: Mesmas 4 usinas hardcoded
- UH Tool: Mapeamento conhecido hardcoded como fallback
- Não escala, difícil de manter

#### **Extração com Contexto**
- Todas as tools podem pegar contexto ao redor do nome
- Ex: "gerações GNL de Santa Cruz" → pode extrair "gerações GNL de Santa Cruz"
- Deveria extrair apenas "Santa Cruz"

#### **Performance**
- CT Tool e Patamar Calculation: Otimizadas (pandas vetorizado)
- UH Tool: Cache global ajuda
- Multi-deck tools: Coletam dados de múltiplos decks (pode ser lento)

#### **Validação**
- CT Tool: Valida código antes de retornar ✅
- Patamar Calculation: Valida código antes de retornar ✅
- Outras: Algumas validam, outras não

---

## Conclusão

O matching de usinas está **fragmentado** e **inconsistente**:

1. **3 estratégias diferentes**:
   - Matcher centralizado + fallback (CT, Patamar Calculation, Multi-Deck)
   - Busca direta por nome (UH, Restrições Vazão HQ)
   - Mapeamento hardcoded (GL Tool)

2. **Duplicação de código**:
   - UH Tool e Restrições Vazão HQ são idênticos
   - CVU, Inflexibilidade e Disponibilidade Multi-Deck são idênticos

3. **Falta de padronização**:
   - Algumas usam cache, outras não
   - Algumas validam código, outras não
   - Algumas têm fallback complexo, outras são simples

4. **Problemas comuns**:
   - Extração com contexto (todas)
   - Normalização limitada (matcher centralizado)
   - Algoritmo simples (SequenceMatcher)

**Recomendação**: Criar serviço centralizado que unifique todas essas estratégias.
