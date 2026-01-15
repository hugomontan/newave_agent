# Documentação de Arquitetura - NEWAVE Agent

## Índice

1. [Visão Geral](#visão-geral)
2. [Arquitetura do Sistema](#arquitetura-do-sistema)
3. [Componentes Principais](#componentes-principais)
4. [Fluxo de Execução](#fluxo-de-execução)
5. [Sistema de Tools](#sistema-de-tools)
6. [Sistema RAG](#sistema-rag)
7. [Modo Multi-Deck](#modo-multi-deck)
8. [Estado e Persistência](#estado-e-persistência)
9. [API e Endpoints](#api-e-endpoints)
10. [Frontend](#frontend)
11. [Segurança e Validação](#segurança-e-validação)
12. [Observabilidade](#observabilidade)

---

## Visão Geral

O **NEWAVE Agent** é uma plataforma inteligente de consultas em linguagem natural sobre dados de planejamento energético do modelo NEWAVE. O sistema combina:

- **Agentes Autônomos** (LangGraph) para orquestração de tarefas complexas
- **RAG (Retrieval-Augmented Generation)** para busca semântica na documentação
- **13 Tools Pré-programadas** para consultas frequentes
- **Geração Automática de Código Python** para consultas customizadas
- **Interface Web Moderna** com streaming de eventos em tempo real
- **Modo Comparativo** para análise entre múltiplos decks

### Objetivo

Permitir que usuários façam perguntas em português sobre dados NEWAVE e recebam respostas precisas, seja através de tools pré-programadas ou código Python gerado automaticamente.

---

## Arquitetura do Sistema

### Diagrama de Alto Nível

```
┌─────────────────────────────────────────────────────────────┐
│                        FRONTEND                              │
│  Next.js 14 + React + TypeScript + Tailwind CSS            │
│  - Interface conversacional                                 │
│  - Streaming de eventos (SSE)                              │
│  - Visualização de dados e gráficos                        │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP/SSE
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                      BACKEND API                             │
│  FastAPI + Python 3.10+                                     │
│  - Endpoints REST                                            │
│  - Server-Sent Events (SSE)                                 │
│  - Upload e gerenciamento de decks                          │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                   LANGGRAPH AGENT                            │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Tool Router Node                                    │   │
│  │  - Semantic Matching (embeddings)                    │   │
│  │  - Keyword Matching (fallback)                       │   │
│  │  - Disambiguation (queries ambíguas)                 │   │
│  └──────────────┬───────────────────────────────────────┘   │
│                 │                                            │
│        ┌────────┴────────┐                                  │
│        │                 │                                  │
│   [Tool Found]    [No Tool]                                 │
│        │                 │                                  │
│        ▼                 ▼                                  │
│  ┌──────────┐    ┌──────────────────┐                      │
│  │Interpreter│    │  RAG Simple Node │                      │
│  │   Node   │    │  (abstract.md)   │                      │
│  └────┬─────┘    └────────┬─────────┘                      │
│       │                  │                                  │
│       │                  ▼                                  │
│       │          ┌──────────────────┐                      │
│       │          │   Coder Node     │                      │
│       │          │ (Code Generation)│                      │
│       │          └────────┬─────────┘                      │
│       │                   │                                  │
│       │                   ▼                                  │
│       │          ┌──────────────────┐                      │
│       │          │  Executor Node   │                      │
│       │          │  (Code Execution)│                      │
│       │          └────────┬─────────┘                      │
│       │                   │                                  │
│       │                   ▼                                  │
│       │          ┌──────────────────┐                      │
│       │          │  Retry Check     │                      │
│       │          │     Node         │                      │
│       │          └────────┬─────────┘                      │
│       │                   │                                  │
│       └───────────┬───────┘                                  │
│                   │                                            │
│                   ▼                                            │
│          ┌──────────────────┐                                │
│          │ Interpreter Node  │                                │
│          │ (Response Format) │                                │
│          └──────────────────┘                                │
└────────────────────┬─────────────────────────────────────────┘
                     │
         ┌───────────┴───────────┐
         │                       │
         ▼                       ▼
┌─────────────────┐    ┌──────────────────┐
│  Tools (13)     │    │  RAG System      │
│  Pre-programadas│    │  - ChromaDB      │
│  + inewave      │    │  - Embeddings    │
└─────────────────┘    └──────────────────┘
```

### Camadas da Arquitetura

1. **Camada de Apresentação (Frontend)**
   - Interface web React/Next.js
   - Comunicação via SSE para streaming
   - Componentes de visualização de dados

2. **Camada de API (Backend)**
   - FastAPI para endpoints REST
   - Gerenciamento de sessões
   - Upload e processamento de decks

3. **Camada de Agentes (LangGraph)**
   - Orquestração de fluxo de trabalho
   - Roteamento inteligente de queries
   - Geração e execução de código

4. **Camada de Dados**
   - Tools pré-programadas (13 tools)
   - Sistema RAG com ChromaDB
   - Biblioteca inewave para leitura de arquivos NEWAVE

---

## Componentes Principais

### 1. Entry Point: `app/main.py`

**Responsabilidades:**
- Inicialização do servidor FastAPI
- Definição de endpoints REST
- Gerenciamento de sessões
- Upload e carregamento de decks
- Streaming de eventos (SSE)

**Endpoints Principais:**
- `POST /query` - Consulta síncrona
- `POST /query/stream` - Consulta com streaming
- `POST /upload` - Upload de deck
- `POST /load-deck` - Carregar deck do repositório
- `POST /init-comparison` - Inicializar modo comparativo

### 2. Agente LangGraph: `app/agents/graph.py`

**Estrutura:**
- **StateGraph**: Grafo de estados que orquestra o fluxo
- **Nodes**: Nós individuais que executam tarefas específicas
- **Edges**: Conexões condicionais entre nós

**Fluxo Otimizado:**
1. **Entry Point**: `tool_router` (otimização - tenta tool primeiro)
2. **Decisão**: Tool encontrada → `interpreter` | Não encontrada → `rag_simple`
3. **RAG Simplificado**: Busca apenas em `abstract.md` (rápido)
4. **Coder**: Gera código Python baseado no contexto
5. **Executor**: Executa código em ambiente isolado
6. **Retry Check**: Verifica se precisa tentar novamente
7. **Interpreter**: Formata resposta final

### 3. Estado do Agente: `app/agents/state.py`

**AgentState (TypedDict):**
```python
class AgentState(TypedDict):
    # Dados básicos
    query: str
    deck_path: str
    relevant_docs: List[str]
    generated_code: str
    execution_result: dict
    final_response: str
    
    # Retry loop
    retry_count: int
    max_retries: int
    code_history: List[str]
    error_history: List[str]
    
    # RAG
    selected_files: List[str]
    validation_result: Optional[dict]
    rag_status: str  # "success" ou "fallback"
    
    # Tools
    tool_route: bool
    tool_result: Optional[dict]
    tool_used: Optional[str]
    
    # Disambiguation
    disambiguation: Optional[dict]
    
    # Multi-Deck
    comparison_data: Optional[dict]
    analysis_mode: str  # "single" ou "comparison"
```

**Características:**
- Estado compartilhado entre todos os nós
- Tipado com TypedDict para type safety
- Imutável (cada nó retorna atualizações)

---

## Fluxo de Execução

### Fluxo Principal (Single Deck)

```
1. Usuário envia query
   ↓
2. Tool Router Node
   ├─ Semantic Matching (embeddings)
   ├─ Keyword Matching (fallback)
   └─ Disambiguation (se ambíguo)
   ↓
3a. Tool Encontrada → Interpreter Node → Resposta Final
   ↓
3b. Tool Não Encontrada
   ↓
4. RAG Simple Node (busca em abstract.md)
   ↓
5. Coder Node (gera código Python)
   ↓
6. Executor Node (executa código)
   ↓
7. Retry Check Node
   ├─ Sucesso → Interpreter Node
   └─ Erro → Coder Node (retry)
   ↓
8. Interpreter Node (formata resposta)
   ↓
9. Resposta Final
```

### Fluxo Multi-Deck (Comparison)

```
1. Usuário envia query em modo comparison
   ↓
2. Tool Router Node
   ├─ MultiDeckComparisonTool intercepta
   └─ Executa tool em ambos os decks (paralelo)
   ↓
3. MultiDeckComparisonTool
   ├─ Executa tool no Deck 1 (Dezembro)
   ├─ Executa tool no Deck 2 (Janeiro)
   └─ Retorna dados brutos de ambos
   ↓
4. Interpreter Node
   ├─ Detecta is_comparison=True
   ├─ Formata dados comparativos
   └─ Gera comparison_data com chart_data
   ↓
5. Frontend renderiza tabela e gráfico comparativo
```

### Decisões Condicionais

**Após Tool Router:**
- `disambiguation` → END (frontend mostra opções)
- `tool_route=True` → `interpreter`
- `tool_route=False` → `rag_simple`

**Após Retry Check:**
- `success=True` ou `retry_count >= max_retries` → `interpreter`
- `success=False` e `retry_count < max_retries` → `coder` (retry)

---

## Sistema de Tools

### Arquitetura de Tools

Todas as tools herdam de `NEWAVETool` (classe abstrata):

```python
class NEWAVETool(ABC):
    def __init__(self, deck_path: str)
    @abstractmethod
    def can_handle(self, query: str) -> bool
    @abstractmethod
    def execute(self, query: str, **kwargs) -> Dict[str, Any]
    @abstractmethod
    def get_description(self) -> str
    def get_name(self) -> str
```

### Tools Disponíveis (13 tools)

#### 1. **CargaMensalTool**
- **Arquivo**: `SISTEMA.DAT`
- **Dados**: Demanda mensal de energia (MWmédio) por submercado
- **Uso**: "cargas mensais do Sudeste", "demanda do Nordeste em 2025"

#### 2. **ClastValoresTool**
- **Arquivo**: `CLAST.DAT`
- **Dados**: Custos Variáveis Unitários (CVU) de classes térmicas
- **Uso**: "CVU de Angra", "custos das térmicas"

#### 3. **ExptOperacaoTool**
- **Arquivo**: `EXPT.DAT`
- **Dados**: Operação térmica (expansões, modificações, desativações)
- **Uso**: "expansões térmicas", "modificações de potência"

#### 4. **ModifOperacaoTool**
- **Arquivo**: `MODIF.DAT`
- **Dados**: Modificações hídricas (volumes, vazões, níveis, turbinamento)
- **Uso**: "vazão mínima de Furnas", "volumes mínimos das usinas"

#### 5. **LimitesIntercambioTool**
- **Arquivo**: `AGRINT.DAT`
- **Dados**: Limites de intercâmbio entre subsistemas
- **Uso**: "limites entre Sudeste e Sul"

#### 6. **AgrintTool**
- **Arquivo**: `AGRINT.DAT`
- **Dados**: Agrupamentos de intercâmbio
- **Uso**: "agrupamentos de intercâmbio"

#### 7. **VazoesTool**
- **Arquivo**: `VAZOES.DAT`
- **Dados**: Séries históricas de vazões de postos fluviométricos
- **Uso**: "vazões de Itaipu", "série histórica do posto 1"

#### 8. **CadicTool**
- **Arquivo**: `C_ADIC.DAT`
- **Dados**: Cargas e ofertas adicionais (valores extras)
- **Uso**: "cargas adicionais do Sudeste"

#### 9. **HidrCadastroTool**
- **Arquivo**: `HIDR.DAT`
- **Dados**: Cadastro de usinas hidrelétricas
- **Uso**: "usinas hidrelétricas", "potência instalada"

#### 10. **ConfhdTool**
- **Arquivo**: `CONFHD.DAT`
- **Dados**: Configuração de usinas (REE, status, volumes iniciais)
- **Uso**: "configuração de usinas", "usinas por REE"

#### 11. **DsvaguaTool**
- **Arquivo**: `DSVAGUA.DAT`
- **Dados**: Desvios de água consuntivos
- **Uso**: "desvios de água"

#### 12. **UsinasNaoSimuladasTool**
- **Arquivo**: `SISTEMA.DAT`
- **Dados**: Geração de pequenas usinas (PCH, EOL, UFV)
- **Uso**: "usinas não simuladas", "geração de pequenas centrais"

#### 13. **RestricaoEletricaTool**
- **Arquivo**: `RE.DAT`
- **Dados**: Restrições elétricas do sistema
- **Uso**: "restrições elétricas"

#### 14. **MultiDeckComparisonTool** (Modo Comparison)
- **Arquivo**: N/A (orquestra outras tools)
- **Dados**: Comparação entre dois decks
- **Uso**: Automático em modo comparison

### Sistema de Matching

#### Semantic Matching (Primário)

**Como funciona:**
1. Gera embedding da query usando `text-embedding-3-large`
2. Gera embeddings das descrições de todas as tools
3. Calcula similaridade de cosseno
4. Retorna tool com maior score (se >= 0.4)

**Vantagens:**
- Entende sinônimos e variações
- Não depende de palavras-chave exatas
- Mais robusto para queries em linguagem natural

**Configuração:**
- `SEMANTIC_MATCHING_ENABLED=true`
- `SEMANTIC_MATCH_THRESHOLD=0.55` (ranking)
- `SEMANTIC_MATCH_MIN_SCORE=0.4` (execução)

#### Keyword Matching (Fallback)

**Como funciona:**
1. Cada tool implementa `can_handle(query)`
2. Verifica palavras-chave específicas
3. Retorna True/False

**Uso:**
- Fallback quando semantic matching desabilitado
- Híbrido: semantic + keyword para maior precisão

#### Disambiguation

**Quando ativa:**
- Múltiplas tools com scores similares
- Diferença entre top 2 < `DISAMBIGUATION_SCORE_DIFF_THRESHOLD` (0.1)
- Score mínimo >= `DISAMBIGUATION_MIN_SCORE` (0.4)

**Comportamento:**
- Retorna opções para o usuário escolher
- Frontend exibe botões de seleção
- Fluxo pausa até escolha do usuário

---

## Sistema RAG

### Componentes

#### 1. Vector Store: `app/rag/vectorstore.py`

**Tecnologia**: ChromaDB
- Armazena embeddings de documentos
- Busca por similaridade semântica
- Persistência em disco (`data/chroma/`)

**Funções:**
- `get_vectorstore()` - Obtém instância do ChromaDB
- `get_embeddings()` - Modelo de embeddings (text-embedding-3-large)

#### 2. Indexer: `app/rag/indexer.py`

**Responsabilidades:**
- Indexa documentação NEWAVE
- Divide documentos em chunks
- Gera embeddings e armazena no ChromaDB

**Configuração:**
- `RAG_CHUNK_SIZE=2000` caracteres
- `RAG_CHUNK_OVERLAP=200` caracteres
- `RAG_TOP_K=5` documentos retornados

#### 3. RAG Nodes

**rag_retriever_node** (completo):
- Busca semântica em toda documentação
- Self-reflection para validar arquivos
- Validação iterativa de arquivos candidatos

**rag_simple_node** (otimizado):
- Busca apenas em `abstract.md`
- Mais rápido (sem validação iterativa)
- Suficiente para geração de código

### Fluxo RAG

```
1. Query do usuário
   ↓
2. Gera embedding da query
   ↓
3. Busca no ChromaDB (similaridade)
   ↓
4. Retorna top K documentos
   ↓
5. (Opcional) Self-reflection valida arquivos
   ↓
6. Contexto enviado para Coder Node
```

---

## Modo Multi-Deck

### Conceito

Permite comparar dados entre dois decks NEWAVE (ex: Dezembro vs Janeiro) automaticamente.

### Implementação

#### 1. Inicialização

**Endpoint**: `POST /init-comparison`

**Comportamento:**
- Carrega dois decks: `NW202512` (Dezembro) e `NW202601` (Janeiro)
- Cria sessão de comparação
- Retorna `session_id`

#### 2. MultiDeckComparisonTool

**Orquestração:**
1. Intercepta todas as queries em modo `comparison`
2. Identifica tool apropriada para a query
3. Executa tool em ambos os decks (paralelo)
4. Retorna dados brutos de ambos

**Estrutura de Retorno:**
```python
{
    "success": True,
    "is_comparison": True,
    "deck_1": {
        "name": "NW202512",
        "path": "...",
        "result": {...}  # Resultado da tool no deck 1
    },
    "deck_2": {
        "name": "NW202601",
        "path": "...",
        "result": {...}  # Resultado da tool no deck 2
    },
    "tool_name": "ClastValoresTool"
}
```

#### 3. Formatação Comparativa

**Interpreter Node** detecta `is_comparison=True` e:
- Usa formatters específicos (`app/comparison/formatters/`)
- Gera `comparison_data` com:
  - `comparison_table`: Tabela comparativa
  - `chart_data`: Dados para gráfico
  - `chart_config`: Configuração do gráfico

**Formatters Disponíveis:**
- `ClastComparisonFormatter`: CVU
- `CargaComparisonFormatter`: Carga Mensal e Carga Adicional

#### 4. Frontend

**Componentes:**
- `ComparisonView.tsx`: Renderiza comparação
- `DifferencesTable.tsx`: Tabela estilizada
- `ComparisonChart.tsx`: Gráfico interativo (Recharts)

**Formato Simplificado:**
- Apenas tabela + gráfico
- Sem conclusões ou análises textuais
- Foco em dados comparativos

---

## Estado e Persistência

### Sessões

**Gerenciamento:**
- Armazenadas em memória (`sessions: dict[str, Path]`)
- Chave: `session_id` (UUID)
- Valor: Caminho do deck

**Ciclo de Vida:**
1. Criação: Upload ou `load-deck`
2. Uso: Consultas usam `session_id`
3. Remoção: `DELETE /sessions/{id}` ou timeout

### Vector Store

**Persistência:**
- ChromaDB armazena em `data/chroma/`
- Embeddings persistidos em disco
- Recuperação automática ao reiniciar

### Decks

**Estrutura:**
```
decks/
├── NW202512/  # Deck Dezembro
│   ├── HIDR.DAT
│   ├── SISTEMA.DAT
│   └── ...
└── NW202601/  # Deck Janeiro
    ├── HIDR.DAT
    ├── SISTEMA.DAT
    └── ...
```

**Carregamento:**
- Decks pré-carregados no repositório
- Upload via `/upload` extrai para `uploads/`
- Modo comparison usa decks fixos

---

## API e Endpoints

### Consultas

#### `POST /query`
**Síncrono** - Aguarda resposta completa

**Request:**
```json
{
    "session_id": "uuid",
    "query": "Quais são as cargas mensais do Sudeste?",
    "analysis_mode": "single"
}
```

**Response:**
```json
{
    "session_id": "uuid",
    "query": "...",
    "response": "## Resposta...",
    "code": "import inewave...",
    "execution_result": {...}
}
```

#### `POST /query/stream`
**Assíncrono** - Streaming via SSE

**Eventos:**
- `node_start` - Nó iniciou execução
- `node_progress` - Progresso do nó
- `node_complete` - Nó completou
- `code_generated` - Código gerado
- `execution_result` - Resultado da execução
- `response_complete` - Resposta final
- `error` - Erro ocorreu

### Upload e Decks

#### `POST /upload`
Upload de arquivo `.zip` contendo deck NEWAVE

#### `POST /load-deck`
Carrega deck do repositório (sem upload)

#### `POST /init-comparison`
Inicializa modo comparativo (carrega ambos os decks)

### Sistema

#### `POST /index`
Reindexa documentação NEWAVE no ChromaDB

#### `GET /health`
Status do servidor

---

## Frontend

### Tecnologias

- **Next.js 14**: Framework React com App Router
- **TypeScript**: Tipagem estática
- **Tailwind CSS**: Estilização
- **shadcn/ui**: Componentes UI
- **Recharts**: Gráficos
- **ReactMarkdown**: Renderização de Markdown
- **Server-Sent Events**: Streaming de eventos

### Estrutura

```
frontend/
├── app/
│   ├── page.tsx           # Página inicial
│   ├── analysis/
│   │   └── page.tsx       # Modo single deck
│   └── comparison/
│       └── page.tsx       # Modo multi-deck
├── components/
│   ├── ChatMessage.tsx    # Mensagem do chat
│   ├── ComparisonView.tsx # Visualização comparativa
│   ├── DifferencesTable.tsx # Tabela comparativa
│   └── ComparisonChart.tsx # Gráfico comparativo
└── lib/
    └── api.ts             # Cliente API
```

### Fluxo de Comunicação

```
Frontend → POST /query/stream
   ↓
Backend → SSE Events
   ├─ node_start
   ├─ code_generated
   ├─ execution_result
   └─ response_complete
   ↓
Frontend atualiza UI em tempo real
```

### Componentes Principais

#### ChatMessage
- Renderiza mensagens do chat
- Suporta Markdown
- Renderiza gráficos base64
- Exibe código com syntax highlighting

#### ComparisonView
- Renderiza dados comparativos
- Integra tabela e gráfico
- Suporta `comparison_data` do backend

#### DifferencesTable
- Tabela estilizada comparativa
- Preview de 15 valores (expansível)
- Colunas: Ano, Deck 1, Deck 2, Diferença

---

## Segurança e Validação

### Execução de Código

**Ambiente Isolado:**
- Código executado em processo Python separado
- Timeout configurável (`CODE_EXECUTION_TIMEOUT=30s`)
- Captura de stdout/stderr

**Validações:**
- Verificação de imports permitidos
- Sanitização de inputs
- Limitação de recursos

### Validação de Dados

**Tool Results:**
- Estrutura validada
- Tipos verificados
- Campos obrigatórios checados

**Limites:**
- Limite dinâmico baseado em tipo de query
- Queries de lista: 200 registros
- Queries normais: 20 registros

---

## Observabilidade

### Langfuse Integration

**Rastreamento:**
- Queries do usuário
- Respostas geradas
- Código executado
- Erros e exceções

**Configuração:**
```env
LANGFUSE_SECRET_KEY=...
LANGFUSE_PUBLIC_KEY=...
LANGFUSE_HOST=https://us.cloud.langfuse.com
```

### Logging

**Níveis:**
- `[TOOL ROUTER]` - Roteamento de tools
- `[RAG]` - Sistema RAG
- `[CODER]` - Geração de código
- `[EXECUTOR]` - Execução de código
- `[INTERPRETER]` - Formatação de resposta

**Safe Print:**
- Substitui emojis por ASCII no Windows
- Evita erros de encoding
- Compatibilidade cross-platform

---

## Configuração

### Variáveis de Ambiente

**Obrigatórias:**
```env
OPENAI_API_KEY=sua_chave
```

**Opcionais:**
```env
# OpenAI
OPENAI_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-large

# RAG
RAG_CHUNK_SIZE=2000
RAG_CHUNK_OVERLAP=200
RAG_TOP_K=5

# Semantic Matching
SEMANTIC_MATCHING_ENABLED=true
SEMANTIC_MATCH_THRESHOLD=0.55
SEMANTIC_MATCH_MIN_SCORE=0.4
USE_HYBRID_MATCHING=true

# Executor
CODE_EXECUTION_TIMEOUT=30

# Langfuse (opcional)
LANGFUSE_SECRET_KEY=
LANGFUSE_PUBLIC_KEY=
LANGFUSE_HOST=https://us.cloud.langfuse.com
```

---

## Estado Atual do Projeto

### Versão: 2.0 (Multi-Deck)

**Funcionalidades Implementadas:**
- ✅ 13 tools pré-programadas
- ✅ Sistema RAG completo
- ✅ Modo multi-deck comparativo
- ✅ Semantic matching de tools
- ✅ Disambiguation para queries ambíguas
- ✅ Formatação simplificada para comparações
- ✅ Interface web moderna
- ✅ Streaming de eventos

**Limitações Conhecidas:**
- Modo comparison limitado a 2 decks fixos (Dez/Jan)
- Formatação comparativa apenas para CVU, Carga Mensal e Carga Adicional
- Sessões em memória (não persistem após restart)

**Próximas Melhorias Planejadas:**
- Suporte a 1-4 decks no modo comparison
- Seleção dinâmica de decks (últimos 12 meses)
- Persistência de sessões
- Mais formatters comparativos
- Validação de respostas com LLM

---

## Conclusão

O NEWAVE Agent é uma plataforma robusta e escalável para consultas inteligentes em dados NEWAVE. A arquitetura baseada em LangGraph permite orquestração complexa, enquanto o sistema de tools pré-programadas otimiza consultas frequentes. O modo multi-deck adiciona capacidade comparativa poderosa, e a interface web moderna proporciona experiência de usuário excelente.

A arquitetura é projetada para ser:
- **Modular**: Componentes independentes e reutilizáveis
- **Escalável**: Fácil adicionar novas tools e funcionalidades
- **Manutenível**: Código organizado e bem documentado
- **Extensível**: Interfaces claras para extensões

