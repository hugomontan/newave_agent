# NEWAVE Agent

Sistema inteligente de consultas em decks NEWAVE usando **LangGraph**, **RAG (Retrieval-Augmented Generation)** e **LLMs**. Permite fazer perguntas em linguagem natural sobre dados de planejamento energetico e receber respostas precisas com codigo Python gerado automaticamente.

## Visao Geral

O NEWAVE Agent e uma plataforma que combina:
- **Agentes Autonomos** (LangGraph) para orquestracao de tarefas complexas
- **RAG** para busca semantica na documentacao NEWAVE
- **Tools Pre-programadas** para consultas frequentes (13 tools especializadas)
- **Geracao de Codigo** para consultas customizadas
- **Interface Web** moderna e interativa
- **Modo Comparativo** para analise entre dois decks (Dezembro vs Janeiro)

## Funcionalidades Principais

### Modos de Analise

| Modo | Descricao |
|------|-----------|
| **Single Deck** | Analise de um unico deck NEWAVE |
| **Multi-Deck** | Comparacao automatica entre dois decks (Dez/Jan) |

### Consultas Inteligentes
- **Linguagem Natural**: Faca perguntas em portugues sobre dados NEWAVE
- **Geracao Automatica de Codigo**: O sistema gera codigo Python usando a biblioteca `inewave`
- **Execucao Segura**: Codigo executado em ambiente isolado com validacoes
- **Retry Automatico**: Sistema tenta corrigir erros automaticamente

### Tools Pre-programadas (13 tools)
1. **CargaMensalTool** - Demanda mensal por submercado
2. **ClastValoresTool** - Custos de classes termicas (CVU)
3. **ExptOperacaoTool** - Operacao termica (expansoes/modificacoes)
4. **ModifOperacaoTool** - Modificacoes hidricas (volumes/vazoes)
5. **LimitesIntercambioTool** - Limites de intercambio entre subsistemas
6. **AgrintTool** - Agrupamentos de intercambio
7. **VazoesTool** - Vazoes historicas de postos fluviometricos
8. **CadicTool** - Cargas e ofertas adicionais
9. **HidrCadastroTool** - Cadastro de usinas hidreletricas
10. **ConfhdTool** - Configuracao de usinas (REE/status)
11. **DsvaguaTool** - Desvios de agua consuntivos
12. **UsinasNaoSimuladasTool** - Geracao de pequenas usinas (PCH/EOL/UFV)
13. **RestricaoEletricaTool** - Restricoes eletricas do sistema

### Modo Multi-Deck (Comparativo)
- **Execucao Paralela**: Mesma tool executada em ambos os decks simultaneamente
- **Interpretacao por LLM**: Analise comparativa gerada por IA
- **Deteccao de Diferencas**: Identifica alteracoes entre decks automaticamente
- **Visualizacao Rica**: Tabelas e graficos comparativos no frontend

### RAG (Retrieval-Augmented Generation)
- **Busca Semantica**: Encontra documentacao relevante usando embeddings
- **Self-Reflection**: Validacao iterativa de arquivos candidatos
- **Query Expansion**: Expansao de sinonimos para melhor matching
- **Vector Store**: ChromaDB para armazenamento de embeddings

### Interface Web
- **Upload de Decks**: Arraste e solte arquivos .zip
- **Decks Pre-carregados**: Use decks do repositorio sem upload
- **Chat Interativo**: Interface conversacional em tempo real
- **Streaming de Eventos**: Acompanhe o progresso da execucao
- **Visualizacao de Codigo**: Veja o codigo Python gerado
- **Download de Dados**: Exporte resultados em JSON/CSV

## Arquitetura

```
┌─────────────────┐
│   Frontend      │  Next.js + React + TypeScript
│   (Next.js)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Backend API   │  FastAPI + Python
│   (FastAPI)     │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────┐
│      LangGraph Agent                │
│  ┌──────────────────────────────┐   │
│  │  Tool Router (Semantic Match)│   │
│  └──────────────┬───────────────┘   │
│                 │                   │
│  ┌──────────────▼───────────────┐   │
│  │  RAG Node (Document Search)  │   │
│  └──────────────┬───────────────┘   │
│                 │                   │
│  ┌──────────────▼───────────────┐   │
│  │  Coder Node (Code Generation)│   │
│  └──────────────┬───────────────┘   │
│                 │                   │
│  ┌──────────────▼───────────────┐   │
│  │  Executor Node (Execution)   │   │
│  └──────────────┬───────────────┘   │
│                 │                   │
│  ┌──────────────▼───────────────┐   │
│  │ Interpreter Node (Response)  │   │
│  └──────────────────────────────┘   │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────┐
│   Tools (13)    │  Pre-programadas
│   + inewave     │  Biblioteca NEWAVE
└─────────────────┘
```

## Tecnologias

### Backend
- **Python 3.10+**
- **FastAPI** - Framework web assincrono
- **LangGraph** - Orquestracao de agentes
- **LangChain** - Integracao com LLMs
- **OpenAI** - GPT-4o-mini (LLM) + text-embedding-3-large (embeddings)
- **ChromaDB** - Vector store para RAG
- **inewave** - Biblioteca para leitura de arquivos NEWAVE
- **pandas** - Manipulacao de dados
- **Langfuse** - Observabilidade e monitoramento

### Frontend
- **Next.js 14+** - Framework React
- **TypeScript** - Tipagem estatica
- **Tailwind CSS** - Estilizacao
- **shadcn/ui** - Componentes UI
- **Framer Motion** - Animacoes
- **Server-Sent Events (SSE)** - Streaming de eventos

## Instalacao

### Pre-requisitos
- Python 3.10 ou superior
- Node.js 18+ (para o frontend)
- OpenAI API Key

### Backend

1. **Clone o repositorio**
```bash
git clone <repository-url>
cd nw-new-new
```

2. **Crie um ambiente virtual**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

3. **Instale as dependencias**
```bash
pip install -r requirements.txt
```

4. **Configure as variaveis de ambiente**
```bash
cp .env.example .env  # Se existir
```

Edite o arquivo `.env`:
```env
OPENAI_API_KEY=sua_chave_aqui
OPENAI_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-large

# Opcional: Langfuse para observabilidade
LANGFUSE_SECRET_KEY=opcional
LANGFUSE_PUBLIC_KEY=opcional
LANGFUSE_HOST=https://us.cloud.langfuse.com
```

5. **Execute o servidor**
```bash
python run.py
```

O servidor estara disponivel em `http://localhost:8000`
Documentacao da API em `http://localhost:8000/docs`

### Frontend

1. **Entre na pasta do frontend**
```bash
cd frontend
```

2. **Instale as dependencias**
```bash
npm install
```

3. **Configure a URL da API** (opcional)
```bash
# Criar arquivo .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
```

4. **Execute o frontend**
```bash
npm run dev
```

A interface estara disponivel em `http://localhost:3000`

## Uso

### 1. Escolha o Modo de Analise

Na tela inicial, selecione:
- **Single Deck Analysis** - Para analisar um deck individual
- **Multi-Deck Analysis** - Para comparar dois decks

### 2. Modos de Carregamento

#### Decks do Repositorio (Recomendado)
Os decks ja estao disponiveis na pasta `decks/`:
- `dezembro/` - Deck de dezembro
- `janeiro/` - Deck de janeiro

O sistema carrega automaticamente sem necessidade de upload.

#### Upload Manual
Faca upload de um arquivo `.zip` contendo o deck NEWAVE:

```bash
curl -X POST "http://localhost:8000/upload" \
  -F "file=@seu_deck.zip"
```

### 3. Fazer Consultas

#### Via Interface Web
1. Acesse `http://localhost:3000`
2. Selecione o modo de analise
3. Digite sua pergunta no chat
4. Aguarde a resposta

#### Via API

**Consulta Single Deck:**
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "seu-session-id",
    "query": "Quais sao as cargas mensais do Sudeste em 2025?",
    "analysis_mode": "single"
  }'
```

**Consulta Multi-Deck (Comparacao):**
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "seu-session-id",
    "query": "Compare os CVUs de Angra entre os decks",
    "analysis_mode": "comparison"
  }'
```

**Consulta com Streaming:**
```bash
curl -X POST "http://localhost:8000/query/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "seu-session-id",
    "query": "Mostre os CVUs de todas as classes termicas",
    "analysis_mode": "single"
  }'
```

### 4. Exemplos de Consultas

#### Consultas que usam Tools Pre-programadas:
- "Quais sao as cargas mensais por submercado?"
- "CVU da classe ANGRA 1"
- "Vazoes historicas de Itaipu"
- "Modificacoes hidricas da usina Furnas"
- "Limites de intercambio entre Sudeste e Sul"

#### Consultas Comparativas (Multi-Deck):
- "Compare a carga do Sudeste entre os decks"
- "Quais modificacoes hidricas mudaram entre dezembro e janeiro?"
- "Diferenca nos CVUs entre os decks"

#### Consultas que geram codigo:
- "Qual a potencia instalada total de todas as hidreletricas?"
- "Mostre a evolucao mensal da demanda do Nordeste"
- "Compare os custos termicos entre 2024 e 2025"

## API Endpoints

### Upload e Sessoes

| Endpoint | Metodo | Descricao |
|----------|--------|-----------|
| `/upload` | POST | Upload de deck NEWAVE (.zip) |
| `/load-deck` | POST | Carrega deck do repositorio |
| `/init-comparison` | POST | Inicializa modo comparativo |
| `/sessions/{id}` | GET | Informacoes da sessao |
| `/sessions/{id}` | DELETE | Remove sessao |

### Consultas

| Endpoint | Metodo | Descricao |
|----------|--------|-----------|
| `/query` | POST | Consulta sincrona |
| `/query/stream` | POST | Consulta com streaming (SSE) |

### Sistema

| Endpoint | Metodo | Descricao |
|----------|--------|-----------|
| `/index` | POST | Reindexa documentacao NEWAVE |
| `/health` | GET | Status do servidor |

## Estrutura do Projeto

```
nw-new-new/
├── app/
│   ├── agents/           # Agente LangGraph
│   │   ├── graph.py      # Definicao do grafo
│   │   ├── state.py      # Estado do agente
│   │   └── nodes/        # Nos do grafo
│   │       ├── tool_router.py    # Roteamento de tools
│   │       ├── rag.py            # Busca semantica
│   │       ├── coder.py          # Geracao de codigo
│   │       ├── executor.py       # Execucao de codigo
│   │       └── interpreter.py    # Interpretacao de resultados
│   ├── tools/            # Tools pre-programadas (13 tools)
│   ├── rag/              # Sistema RAG
│   │   ├── vectorstore.py    # ChromaDB
│   │   └── indexer.py        # Indexacao de docs
│   ├── utils/            # Utilitarios
│   │   └── deck_loader.py    # Carregador de decks
│   ├── config.py         # Configuracoes
│   └── main.py           # API FastAPI
├── frontend/             # Interface Next.js
├── decks/                # Decks pre-carregados
│   ├── dezembro/         # Deck dezembro
│   └── janeiro/          # Deck janeiro
├── docs/                 # Documentacao NEWAVE
├── data/                 # Dados e vector store
└── requirements.txt      # Dependencias Python
```

## Configuracao Avancada

### Variaveis de Ambiente

```env
# OpenAI
OPENAI_API_KEY=obrigatorio
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
QUERY_EXPANSION_ENABLED=true

# Disambiguation
DISAMBIGUATION_SCORE_DIFF_THRESHOLD=0.1
DISAMBIGUATION_MAX_OPTIONS=3
DISAMBIGUATION_MIN_SCORE=0.4

# Executor
CODE_EXECUTION_TIMEOUT=30

# Observability (Opcional)
LANGFUSE_SECRET_KEY=
LANGFUSE_PUBLIC_KEY=
LANGFUSE_HOST=https://us.cloud.langfuse.com
```

## Seguranca

- **Execucao Isolada**: Codigo Python executado em ambiente controlado
- **Validacao de Codigo**: Verificacao de imports e operacoes permitidas
- **Timeout**: Limite de tempo para execucao de codigo
- **Sanitizacao**: Validacao de inputs e outputs

## Observabilidade

O projeto integra com **Langfuse** para monitoramento:
- Rastreamento de queries
- Metricas de performance
- Analise de erros
- Logs de execucao

Configure as chaves no `.env` para habilitar.

## Changelog Recente

### v2.0 - Modo Multi-Deck
- Novo modo de analise comparativa entre dois decks
- Execucao paralela de tools em ambos os decks
- Interpretacao por LLM para comparacoes
- Otimizacao: decks usados diretamente sem copia de arquivos
- Endpoints `/load-deck` e `/init-comparison`
- Interface atualizada com selecao de modo
