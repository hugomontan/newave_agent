# Avaliação: Semantic Matching e Identificação de Usinas

## 📋 Sumário

1. [Estrutura Atual do Semantic Matching](#estrutura-atual-do-semantic-matching)
2. [Estrutura Atual do Matching de Usinas](#estrutura-atual-do-matching-de-usinas)
3. [Problemas Identificados](#problemas-identificados)
4. [Soluções Propostas](#soluções-propostas)

---

## 1. Estrutura Atual do Semantic Matching

### 1.1. Arquitetura Geral

O sistema de semantic matching funciona em **camadas**:

```
Query do Usuário
    ↓
Query Expansion (sinônimos e variações)
    ↓
Geração de Embedding (text-embedding-3-small)
    ↓
Cálculo de Similaridade (Cosine Similarity)
    ↓
Ranking e Decisão (threshold-based)
    ↓
Tool Selecionada ou Fluxo Normal
```

### 1.2. Componentes Principais

#### **Módulo Compartilhado** (`backend/core/semantic_matcher.py`)
- Função central: `find_best_tool_semantic()`
- Cache global de embeddings (tools e queries)
- Processamento paralelo de embeddings
- Cálculo vetorizado de similaridades

#### **Wrappers Específicos**
- **DECOMP**: `backend/decomp/tools/semantic_matcher.py`
  - Expansões específicas do domínio DECOMP
  - Thresholds configuráveis
- **NEWAVE**: `backend/newave/tools/semantic_matcher.py`
  - Expansões específicas do domínio NEWAVE

#### **Query Expansion**
- Dicionário de expansões (`DECOMP_QUERY_EXPANSIONS`)
- Substituição de padrões por sinônimos
- Normalização de acentos e pontuação
- Combinação de todas as expansões em uma string única

#### **Cache de Embeddings**
- Cache por hash da descrição da tool
- Cache por hash da query expandida
- Invalidação automática quando descrições mudam

### 1.3. Fluxo de Decisão

1. **Expansão da Query**: Aplica sinônimos e variações
2. **Geração de Embedding**: Converte query expandida em vetor
3. **Comparação com Tools**: Calcula similaridade com todas as tools
4. **Ranking**: Ordena tools por score decrescente
5. **Decisão Final**: 
   - Se `score >= SEMANTIC_MATCH_MIN_SCORE` (0.35) → Executa tool
   - Caso contrário → Retorna para fluxo normal (RAG)

### 1.4. Configurações Atuais

- **SEMANTIC_MATCH_THRESHOLD**: 0.55 (apenas para ranking, não usado na decisão)
- **SEMANTIC_MATCH_MIN_SCORE**: 0.35 (score mínimo para executar tool)
- **QUERY_EXPANSION_ENABLED**: true
- **Modelo de Embedding**: `text-embedding-3-small` (OpenAI)

---

## 2. Estrutura Atual do Matching de Usinas

### 2.1. Arquitetura Geral

O matching de usinas funciona em **múltiplas estratégias em cascata**:

```
Query do Usuário
    ↓
ETAPA 1: Extração por Padrão Numérico (regex)
    ↓ (se não encontrou)
ETAPA 2: Matcher Centralizado (fuzzy matching)
    ↓ (se não encontrou)
ETAPA 3: Busca por Palavras-Chave (fallback)
    ↓
Código da Usina ou None
```

### 2.2. Componentes Principais

#### **Matcher Centralizado** (`backend/core/utils/usina_name_matcher.py`)
- Função: `find_usina_match()`
- Normalização: `normalize_usina_name()`
- Algoritmo: `SequenceMatcher` (difflib)
- Threshold padrão: 0.5

#### **Implementações por Tool**

Cada tool tem sua própria implementação de `_extract_usina_from_query()`:

1. **CT Tool** (Termelétricas):
   - Usa matcher centralizado
   - Fallback por palavras-chave
   - Requer 2+ palavras ou 1 palavra com 6+ caracteres

2. **UH Tool** (Hidrelétricas):
   - Cache global de mapeamento HIDR.DAT
   - Busca em múltiplos arquivos (DECOMP → NEWAVE)

3. **GL Tool** (GNL):
   - Mapeamento hardcoded (apenas 4 usinas)
   - Não usa matcher centralizado

4. **Patamar Calculation Base**:
   - Usa matcher centralizado
   - Busca otimizada com índices

### 2.3. Fontes de Dados

#### **NEWAVE**
- `CONFHD.DAT`: Usinas hidrelétricas
- `TERM.DAT`: Usinas térmicas
- `HIDR.DAT`: Cadastro de usinas

#### **DECOMP**
- `CT`: Usinas térmicas
- `UH`: Usinas hidrelétricas
- `HIDR.DAT`: Cadastro (busca em decks NEWAVE)

#### **Cache Global**
- `_HIDR_MAPPING_CACHE`: Cache de mapeamento código → nome
- Algumas tools usam, outras não

### 2.4. Estratégias de Matching

1. **Match Exato**: Nome completo igual à query
2. **Match Parcial**: Nome completo contido na query (com word boundaries)
3. **Fuzzy Matching**: SequenceMatcher com threshold
4. **Palavras-Chave**: Busca por palavras significativas do nome

---

## 3. Problemas Identificados

### 3.1. Semantic Matching

#### **Problema 1: Thresholds Confusos**
- `SEMANTIC_MATCH_THRESHOLD` (0.55) não é usado na decisão final
- `SEMANTIC_MATCH_MIN_SCORE` (0.35) é muito baixo
- Falta clareza sobre qual threshold usar quando

#### **Problema 2: Query Expansion Limitada**
- Expansões hardcoded não cobrem variações de nomes de usinas
- Não expande termos técnicos específicos do domínio
- Não considera contexto (ex: "GL" pode ser "gerações GNL" ou "bloco GL")

#### **Problema 3: Embeddings Genéricos**
- Modelo `text-embedding-3-small` é genérico, não especializado
- Não captura relações específicas do domínio de energia
- Pode não entender que "GL" = "gerações GNL já comandadas"

#### **Problema 4: Descrições Inconsistentes**
- Algumas tools têm descrições muito genéricas
- Outras muito específicas
- Não padronizadas → afeta qualidade dos embeddings

#### **Problema 5: Falta de Contexto**
- Não considera histórico de queries
- Não aprende com correções do usuário
- Não usa informações do deck atual

#### **Problema 6: Entidades Poluindo Embeddings** ⚠️ **CRÍTICO**
- Nomes de usinas na query afetam o embedding
- Ex: "gerações GNL de Santa Cruz" → embedding focado em "Santa Cruz"
- Pode fazer match com tool errada ou não fazer match com tool certa
- Submercados, patamares, estágios também poluem

### 3.2. Matching de Usinas

#### **Problema 1: Múltiplas Implementações Inconsistentes**
- Cada tool tem sua própria lógica
- Algumas usam matcher centralizado, outras não
- Padrões diferentes de normalização
- Difícil manter e evoluir

#### **Problema 2: Matcher Centralizado Limitado**
- `SequenceMatcher` é algoritmo simples
- Não captura variações complexas (abreviações, números romanos)
- Threshold fixo (0.5) pode ser alto ou baixo dependendo do caso
- Não considera contexto (ex: "Santa Cruz" pode ser cidade ou usina)

#### **Problema 3: Normalização Incompleta**
- Remove acentos, mas não trata:
  - Abreviações ("SC" vs "Santa Cruz")
  - Números romanos ("I", "II", "III" vs "1", "2", "3")
  - Pontuação variada ("P.Sergipe" vs "PSergipe" vs "P Sergipe")
  - Variações comuns ("Usina X" vs "X" vs "UTE X")

#### **Problema 4: Falta de Fonte Única de Verdade**
- NEWAVE busca em múltiplos arquivos
- DECOMP busca em múltiplos arquivos
- Cada tool carrega seu próprio mapeamento
- Cache global existe mas não é universal
- Inconsistências entre fontes

#### **Problema 5: Mapeamentos Hardcoded**
- GL Tool tem apenas 4 usinas hardcoded
- Não escala
- Não cobre variações
- Difícil de manter

#### **Problema 6: Extração com Contexto** ⚠️ **CRÍTICO**
- Ao extrair nome da usina, pode pegar contexto ao redor
- Ex: "gerações GNL de Santa Cruz" → pode extrair "gerações GNL de Santa Cruz"
- Deveria extrair apenas "Santa Cruz"
- Afeta qualidade do matching

#### **Problema 7: Performance**
- Matcher centralizado itera sobre todas as usinas (O(n))
- Sem índice ou estrutura otimizada
- Pode ser lento com muitos decks

#### **Problema 8: Falta de Validação**
- Não verifica se código existe antes de retornar
- Não sugere alternativas quando não encontra
- Não trata ambiguidade (múltiplas usinas com nomes similares)

---

## 4. Soluções Propostas

### 4.1. Semantic Matching

#### **Solução 1: Pipeline em Duas Etapas** ⭐ **PRIORITÁRIO**

**Conceito**: Separar extração de entidades do semantic matching.

**Fluxo Proposto**:
```
Query Original
    ↓
Extração de Entidades (usinas, submercados, patamares, etc.)
    ↓
Query Limpa (sem entidades) → Semantic Matching
    ↓
Entidades Extraídas → Filtros na Tool
```

**Benefícios**:
- Embeddings focados na intenção, não em entidades específicas
- "gerações GNL de Santa Cruz" → "gerações GNL" para matching
- Melhor precisão na seleção de tools

**Implementação**:
- Criar `DomainEntityExtractor` genérico
- Modificar `find_best_tool_semantic()` para usar query limpa
- Entidades extraídas passadas como contexto para tools

#### **Solução 2: Melhorar Query Expansion**

**Conceito**: Expansões mais inteligentes e contextuais.

**Melhorias**:
- Adicionar expansões para nomes de usinas conhecidas
- Expandir termos técnicos específicos do domínio
- Considerar contexto (ex: "GL" em contexto de "geração" → "gerações GNL")

**Implementação**:
- Expandir `DECOMP_QUERY_EXPANSIONS` com termos de usinas
- Adicionar expansões contextuais (baseadas em palavras ao redor)
- Usar dados reais de usinas para gerar expansões

#### **Solução 3: Padronizar Descrições das Tools**

**Conceito**: Templates padronizados para descrições.

**Estrutura Proposta**:
```
[Nome da Tool]

[Descrição curta do que faz]

Dados disponíveis:
- [Lista de dados]

Palavras-chave relacionadas:
- [Lista de keywords]

Exemplos de queries:
- [Exemplos reais]
```

**Benefícios**:
- Embeddings mais consistentes
- Melhor matching semântico
- Mais fácil de manter

#### **Solução 4: Ajustar Thresholds Baseado em Análise Empírica**

**Conceito**: Coletar dados e ajustar thresholds.

**Processo**:
1. Coletar queries reais e tools selecionadas
2. Analisar scores de matching
3. Identificar threshold ótimo
4. Implementar thresholds adaptativos (diferentes por tipo de tool)

#### **Solução 5: Embeddings Híbridos (Futuro)**

**Conceito**: Combinar embedding genérico com features de domínio.

**Abordagem**:
- Embedding base (genérico)
- Features específicas (tem código usina? tem GNL? tem patamar?)
- Combinação ponderada

**Benefícios**:
- Melhor captura de relações do domínio
- Não requer treinamento de modelo

### 4.2. Matching de Usinas

#### **Solução 1: Serviço Centralizado de Matching** ⭐ **PRIORITÁRIO**

**Conceito**: Um único serviço que todas as tools usam.

**Arquitetura**:
```
UsinaMatcherService
    ├── Carregamento unificado de todas as fontes
    ├── Índice invertido para busca rápida
    ├── Normalização melhorada
    ├── Cache global persistente
    └── API unificada para todas as tools
```

**Benefícios**:
- Consistência entre tools
- Fácil de evoluir
- Performance melhorada
- Fonte única de verdade

**Implementação**:
- Criar `backend/core/services/usina_matcher_service.py`
- Migrar todas as tools para usar o serviço
- Manter compatibilidade com código existente

#### **Solução 2: Normalização Melhorada**

**Conceito**: Normalização que trata mais casos.

**Melhorias**:
- Normalizar números romanos ("I" → "1")
- Normalizar pontuação variada
- Remover prefixos comuns ("Usina", "UTE", "UH")
- Tratar abreviações conhecidas ("SC" → "Santa Cruz")

**Implementação**:
- Melhorar `normalize_usina_name()` em `usina_name_matcher.py`
- Adicionar dicionário de abreviações
- Adicionar normalização de números romanos

#### **Solução 3: Algoritmo de Matching Melhorado**

**Conceito**: Substituir `SequenceMatcher` por algoritmo melhor.

**Opções**:
1. **RapidFuzz** (recomendado):
   - Mais rápido (C++ otimizado)
   - Múltiplos algoritmos (WRatio melhor para nomes)
   - Não diferencia maiúsculas/minúsculas
   - Trata ordem de palavras

2. **FuzzyWuzzy** (alternativa):
   - Similar ao RapidFuzz
   - Mais lento

**Benefícios**:
- Melhor matching de nomes
- Performance melhorada
- Trata mais casos (ordem de palavras, matches parciais)

#### **Solução 4: Índice Invertido para Busca Rápida**

**Conceito**: Estrutura de dados otimizada para busca.

**Estrutura**:
```
Índice Invertido:
    palavra → [(codigo, nome_completo), ...]

Busca:
    1. Buscar palavras da query no índice
    2. Contar matches por usina
    3. Priorizar usinas com mais palavras em comum
    4. Aplicar fuzzy matching apenas nos top candidatos
```

**Benefícios**:
- Busca O(1) para palavras conhecidas
- Reduz número de comparações fuzzy
- Performance muito melhorada

#### **Solução 5: Extração Isolada de Nomes**

**Conceito**: Extrair apenas o nome, não o contexto ao redor.

**Estratégia**:
1. Usar word boundaries para encontrar nome completo
2. Remover apenas palavras do nome, não contexto
3. Retornar texto exato extraído

**Exemplo**:
- Query: "gerações GNL de Santa Cruz"
- Extrair: "Santa Cruz" (não "gerações GNL de Santa Cruz")
- Query limpa: "gerações GNL"

**Implementação**:
- Melhorar `find_usina_match()` para retornar texto exato
- Usar regex com word boundaries
- Remover palavras do nome uma por uma

#### **Solução 6: Cache Global Unificado**

**Conceito**: Cache único que todas as tools compartilham.

**Estrutura**:
```
Cache Global:
    - Mapeamento código → nome (todas as fontes)
    - Índice invertido
    - Cache persistente (opcional)
```

**Benefícios**:
- Evita recarregar dados
- Consistência entre tools
- Performance melhorada

#### **Solução 7: Validação e Sugestões**

**Conceito**: Validar resultados e sugerir alternativas.

**Funcionalidades**:
- Verificar se código existe antes de retornar
- Se não encontrar, sugerir usinas similares
- Tratar ambiguidade (múltiplas usinas com nomes similares)
- Retornar confiança do match

**Implementação**:
- Adicionar validação no serviço centralizado
- Retornar múltiplos candidatos com scores
- Tool decide qual usar baseado no contexto

### 4.3. Integração das Soluções

#### **Fluxo Completo Proposto**

```
Query Original
    ↓
DomainEntityExtractor
    ├── Extrai entidades (usinas, submercados, patamares, etc.)
    └── Cria query limpa
    ↓
Semantic Matching (com query limpa)
    ├── Query Expansion (melhorada)
    ├── Embedding (genérico + features de domínio)
    └── Ranking
    ↓
Tool Selecionada
    ↓
UsinaMatcherService (se precisar de usina)
    ├── Busca rápida (índice invertido)
    ├── Fuzzy matching (RapidFuzz)
    └── Validação e sugestões
    ↓
Execução da Tool (com entidades extraídas)
```

---

## 5. Priorização de Implementação

### Fase 1: Melhorias Rápidas (1-2 dias)
1. ✅ Substituir `SequenceMatcher` por `RapidFuzz`
2. ✅ Melhorar normalização (números romanos, pontuação, prefixos)
3. ✅ Adicionar tratamento de abreviações conhecidas

### Fase 2: Extração de Entidades (3-5 dias)
1. ✅ Criar `DomainEntityExtractor`
2. ✅ Modificar semantic matching para usar query limpa
3. ✅ Testar com queries reais

### Fase 3: Serviço Centralizado (5-7 dias)
1. ✅ Criar `UsinaMatcherService`
2. ✅ Implementar índice invertido
3. ✅ Migrar tools para usar serviço
4. ✅ Cache global unificado

### Fase 4: Melhorias Avançadas (7-10 dias)
1. ✅ Padronizar descrições das tools
2. ✅ Melhorar query expansion
3. ✅ Validação e sugestões
4. ✅ Análise empírica de thresholds

---

## 6. Métricas de Sucesso

### Semantic Matching
- ✅ Taxa de acerto na seleção de tools (meta: >90%)
- ✅ Redução de falsos positivos (tools erradas selecionadas)
- ✅ Redução de falsos negativos (tools certas não selecionadas)

### Matching de Usinas
- ✅ Taxa de acerto na identificação (meta: >95%)
- ✅ Redução de extrações com contexto
- ✅ Melhoria de performance (meta: <100ms por busca)

### Geral
- ✅ Consistência entre tools
- ✅ Facilidade de manutenção
- ✅ Escalabilidade (funciona com muitos decks)

---

## 7. Riscos e Mitigações

### Risco 1: Quebrar Funcionalidade Existente
**Mitigação**: Implementar gradualmente, manter compatibilidade

### Risco 2: Performance Piorar
**Mitigação**: Usar índices e cache, benchmark antes/depois

### Risco 3: Over-engineering
**Mitigação**: Começar simples, evoluir conforme necessidade

---

## 8. Conclusão

Os problemas identificados são **sistêmicos** e requerem **refatoração arquitetural**, não apenas ajustes pontuais. As soluções propostas focam em:

1. **Separação de responsabilidades**: Entidades vs Intenção
2. **Centralização**: Serviço único para matching de usinas
3. **Melhoria incremental**: Começar com melhorias rápidas, evoluir para arquitetura completa

A implementação deve ser **gradual** e **testada** em cada fase para garantir que não quebra funcionalidade existente.
