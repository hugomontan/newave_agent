# NEWAVE Agent

Sistema inteligente de consultas em decks NEWAVE usando **LangGraph**, **RAG (Retrieval-Augmented Generation)** e **LLMs**. Permite fazer perguntas em linguagem natural sobre dados de planejamento energético e receber respostas precisas com código Python gerado automaticamente.

## Visão Geral

O NEWAVE Agent é uma plataforma que combina:
- **Agentes Autônomos** (LangGraph) para orquestração de tarefas complexas
- **RAG** para busca semântica na documentação NEWAVE
- **Tools Pré-programadas** para consultas frequentes (13 tools especializadas)
- **Geração de Código** para consultas customizadas
- **Interface Web** moderna e interativa

##  Funcionalidades Principais

###  Consultas Inteligentes
- **Linguagem Natural**: Faça perguntas em português sobre dados NEWAVE
- **Geração Automática de Código**: O sistema gera código Python usando a biblioteca `inewave`
- **Execução Segura**: Código executado em ambiente isolado com validações
- **Retry Automático**: Sistema tenta corrigir erros automaticamente

###  Tools Pré-programadas (13 tools)
1. **CargaMensalTool** - Demanda mensal por submercado
2. **ClastValoresTool** - Custos de classes térmicas (CVU)
3. **ExptOperacaoTool** - Operação térmica (expansões/modificações)
4. **ModifOperacaoTool** - Modificações hídricas (volumes/vazões)
5. **LimitesIntercambioTool** - Limites de intercâmbio entre subsistemas
6. **AgrintTool** - Agrupamentos de intercâmbio
7. **VazoesTool** - Vazões históricas de postos fluviométricos
8. **CadicTool** - Cargas e ofertas adicionais
9. **HidrCadastroTool** - Cadastro de usinas hidrelétricas
10. **ConfhdTool** - Configuração de usinas (REE/status)
11. **DsvaguaTool** - Desvios de água consuntivos
12. **UsinasNaoSimuladasTool** - Geração de pequenas usinas (PCH/EOL/UFV)
13. **RestricaoEletricaTool** - Restrições elétricas do sistema

###  RAG (Retrieval-Augmented Generation)
- **Busca Semântica**: Encontra documentação relevante usando embeddings
- **Self-Reflection**: Validação iterativa de arquivos candidatos
- **Query Expansion**: Expansão de sinônimos para melhor matching
- **Vector Store**: ChromaDB para armazenamento de embeddings

###  Interface Web
- **Upload de Decks**: Arraste e solte arquivos .zip
- **Chat Interativo**: Interface conversacional em tempo real
- **Streaming de Eventos**: Acompanhe o progresso da execução
- **Visualização de Código**: Veja o código Python gerado
- **Download de Dados**: Exporte resultados em JSON/CSV

##  Arquitetura

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
│  ┌──────────────────────────────┐  │
│  │  Tool Router (Semantic Match) │  │
│  └──────────────┬─────────────────┘  │
│                 │                    │
│  ┌──────────────▼─────────────────┐  │
│  │  RAG Node (Document Search)   │  │
│  └──────────────┬─────────────────┘  │
│                 │                    │
│  ┌──────────────▼─────────────────┐  │
│  │  Coder Node (Code Generation)  │  │
│  └──────────────┬─────────────────┘  │
│                 │                    │
│  ┌──────────────▼─────────────────┐  │
│  │  Executor Node (Code Execution)│  │
│  └──────────────┬─────────────────┘  │
│                 │                    │
│  ┌──────────────▼─────────────────┐  │
│  │ Interpreter Node (Response)    │  │
│  └────────────────────────────────┘  │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────┐
│   Tools (13)    │  Pré-programadas
│   + inewave     │  Biblioteca NEWAVE
└─────────────────┘
```

##  Tecnologias

### Backend
- **Python 3.10+**
- **FastAPI** - Framework web assíncrono
- **LangGraph** - Orquestração de agentes
- **LangChain** - Integração com LLMs
- **OpenAI** - GPT-4o-mini (LLM) + text-embedding-3-large (embeddings)
- **ChromaDB** - Vector store para RAG
- **inewave** - Biblioteca para leitura de arquivos NEWAVE
- **pandas** - Manipulação de dados
- **Langfuse** - Observabilidade e monitoramento

### Frontend
- **Next.js 14+** - Framework React
- **TypeScript** - Tipagem estática
- **Tailwind CSS** - Estilização
- **shadcn/ui** - Componentes UI
- **Server-Sent Events (SSE)** - Streaming de eventos

##  Instalação

### Pré-requisitos
- Python 3.10 ou superior
- Node.js 18+ (para o frontend)
- OpenAI API Key

### Backend

1. **Clone o repositório**
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

3. **Instale as dependências**
```bash
pip install -r requirements.txt
```

4. **Configure as variáveis de ambiente**
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

O servidor estará disponível em `http://localhost:8000`
Documentação da API em `http://localhost:8000/docs`

### Frontend

1. **Entre na pasta do frontend**
```bash
cd frontend
```

2. **Instale as dependências**
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

A interface estará disponível em `http://localhost:3000`

##  Uso

### 1. Upload de Deck

Faça upload de um arquivo `.zip` contendo o deck NEWAVE através da interface web ou API:

```bash
curl -X POST "http://localhost:8000/upload" \
  -F "file=@seu_deck.zip"
```

Você receberá um `session_id` para usar nas consultas.

### 2. Fazer Consultas

#### Via Interface Web
1. Acesse `http://localhost:3000`
2. Faça upload do deck
3. Digite sua pergunta no chat
4. Aguarde a resposta

#### Via API

**Consulta Simples:**
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "seu-session-id",
    "query": "Quais são as cargas mensais do Sudeste em 2025?"
  }'
```

**Consulta com Streaming:**
```bash
curl -X POST "http://localhost:8000/query/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "seu-session-id",
    "query": "Mostre os CVUs de todas as classes térmicas"
  }'
```

### 3. Exemplos de Consultas

#### Consultas que usam Tools Pré-programadas:
- "Quais são as cargas mensais por submercado?"
- "CVU da classe ANGRA 1"
- "Vazões históricas de Itaipu"
- "Modificações hídricas da usina Furnas"
- "Limites de intercâmbio entre Sudeste e Sul"

#### Consultas que geram código:
- "Qual a potência instalada total de todas as hidrelétricas?"
- "Mostre a evolução mensal da demanda do Nordeste"
- "Compare os custos térmicos entre 2024 e 2025"

##  API Endpoints

### `POST /upload`
Upload de deck NEWAVE (.zip)
- **Retorna**: `session_id`, `files_count`

### `POST /query`
Consulta síncrona
- **Body**: `{ "session_id": string, "query": string }`
- **Retorna**: Resposta completa com código gerado e resultados

### `POST /query/stream`
Consulta com streaming (SSE)
- **Body**: `{ "session_id": string, "query": string }`
- **Retorna**: Eventos em tempo real (Server-Sent Events)

### `GET /sessions/{session_id}`
Informações da sessão
- **Retorna**: Lista de arquivos carregados

### `DELETE /sessions/{session_id}`
Remove sessão e arquivos

### `POST /index`
Reindexa a documentação NEWAVE

##  Estrutura do Projeto

```
nw-new-new/
├── app/
│   ├── agents/           # Agente LangGraph
│   │   ├── graph.py      # Definição do grafo
│   │   ├── state.py      # Estado do agente
│   │   └── nodes/        # Nós do grafo
│   │       ├── tool_router.py    # Roteamento de tools
│   │       ├── rag.py            # Busca semântica
│   │       ├── coder.py          # Geração de código
│   │       ├── executor.py       # Execução de código
│   │       └── interpreter.py    # Interpretação de resultados
│   ├── tools/            # Tools pré-programadas (13 tools)
│   ├── rag/              # Sistema RAG
│   │   ├── vectorstore.py    # ChromaDB
│   │   └── indexer.py        # Indexação de docs
│   ├── utils/            # Utilitários
│   ├── config.py         # Configurações
│   └── main.py           # API FastAPI
├── frontend/             # Interface Next.js
├── docs/                 # Documentação NEWAVE
├── data/                 # Dados e vector store
├── uploads/              # Decks carregados
└── requirements.txt      # Dependências Python
```

##  Configuração Avançada

### Variáveis de Ambiente

```env
# OpenAI
OPENAI_API_KEY=obrigatório
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

## Segurança

- **Execução Isolada**: Código Python executado em ambiente controlado
- **Validação de Código**: Verificação de imports e operações permitidas
- **Timeout**: Limite de tempo para execução de código
- **Sanitização**: Validação de inputs e outputs

##  Observabilidade

O projeto integra com **Langfuse** para monitoramento:
- Rastreamento de queries
- Métricas de performance
- Análise de erros
- Logs de execução

Configure as chaves no `.env` para habilitar.


