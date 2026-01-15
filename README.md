# NW Multi Agent

Sistema unificado para consultas inteligentes em decks NEWAVE e DECOMP usando LangGraph e RAG.

## Estrutura do Projeto

```
nw_multi/
├── main.py              # Backend unificado (FastAPI)
├── run.py               # Script de execução do backend
├── requirements.txt     # Dependências Python
├── package.json         # Dependências Node.js (frontend)
├── .env                 # Variáveis de ambiente
├── frontend/             # Frontend Next.js (NEWAVE + DECOMP)
├── newave_agent/        # Módulo NEWAVE
│   └── app/
├── decomp_agent/        # Módulo DECOMP
│   └── app/
└── shared/              # Utilitários compartilhados
```

## Pré-requisitos

- Python 3.10+
- Node.js 18+
- npm ou yarn

## Instalação

### Backend

1. Instale as dependências Python:
```bash
pip install -r requirements.txt
```

2. Configure as variáveis de ambiente:
```bash
# Copie o arquivo .env e configure as variáveis necessárias
# OPENAI_API_KEY=your_key_here
# LANGFUSE_SECRET_KEY=your_key_here (opcional)
# etc.
```

### Frontend

1. Instale as dependências Node.js:
```bash
npm install
```

## Execução

### Backend

Na raiz do projeto:
```bash
python run.py
```

O servidor será iniciado em `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`
- NEWAVE endpoints: `http://localhost:8000/api/newave/*`
- DECOMP endpoints: `http://localhost:8000/api/decomp/*`

### Frontend

Na raiz do projeto:
```bash
npm run dev
```

O frontend será iniciado em `http://localhost:3000`

## Modelos Suportados

### NEWAVE
- Modelo de médio a longo prazo (até 5 anos, mensal)
- Endpoints: `/api/newave/*`

### DECOMP
- Modelo de curto prazo (até 12 meses, semanal/mensal)
- Endpoints: `/api/decomp/*`

## Desenvolvimento

### Estrutura de Módulos

Cada módulo (NEWAVE e DECOMP) possui sua própria estrutura:
- `app/agents/` - Agentes LangGraph (single_deck, multi_deck)
- `app/tools/` - Tools específicas do modelo
- `app/rag/` - Sistema RAG para documentação
- `app/main.py` - API FastAPI do módulo

### Frontend

O frontend está unificado e serve ambos os modelos:
- `app/newave/` - Páginas NEWAVE
- `app/decomp/` - Páginas DECOMP
- `components/` - Componentes compartilhados

## Variáveis de Ambiente

Principais variáveis no `.env`:
- `OPENAI_API_KEY` - Chave da API OpenAI
- `OPENAI_MODEL` - Modelo OpenAI a usar (padrão: gpt-4o-mini)
- `LANGFUSE_SECRET_KEY` - Chave secreta Langfuse (opcional)
- `LANGFUSE_PUBLIC_KEY` - Chave pública Langfuse (opcional)
- `LANGFUSE_HOST` - Host do Langfuse (opcional)

## Scripts Disponíveis

### Backend
- `python run.py` - Inicia servidor de desenvolvimento com reload

### Frontend
- `npm run dev` - Inicia servidor de desenvolvimento
- `npm run build` - Build para produção
- `npm start` - Inicia servidor de produção

## Documentação

- API Docs: `http://localhost:8000/docs` (quando backend estiver rodando)
- Documentação dos modelos: Ver `newave_agent/docs/` e `decomp_agent/docs/`
