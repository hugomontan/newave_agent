# Plano de Migração: Nova Estrutura de Pastas

## Objetivo
Reorganizar o repositório para uma estrutura mais clara e navegável, separando backend, frontend e dados.

---

## Estrutura Final

```
nw_multi/
├── backend/
│   ├── main.py
│   ├── run.py
│   ├── requirements.txt
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── base_tool.py
│   │   ├── code_executor.py
│   │   ├── observability.py
│   │   ├── text_utils.py
│   │   ├── debug.py
│   │   ├── json_utils.py
│   │   ├── semantic_matcher.py
│   │   └── nodes/
│   │       ├── __init__.py
│   │       ├── coder.py
│   │       ├── executor.py
│   │       ├── interpreter.py
│   │       └── tool_router_base.py
│   ├── newave/
│   │   ├── __init__.py
│   │   ├── api.py
│   │   ├── config.py
│   │   ├── agent.py
│   │   ├── tools/
│   │   ├── formatters/
│   │   └── rag/
│   └── decomp/
│       ├── __init__.py
│       ├── api.py
│       ├── config.py
│       ├── agent.py
│       ├── decompclass.py
│       ├── registrocl.py
│       ├── tools/
│       ├── formatters/
│       └── rag/
│
├── frontend/
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   ├── next.config.mjs
│   ├── postcss.config.mjs
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx
│   │   ├── globals.css
│   │   ├── providers.tsx
│   │   ├── newave/
│   │   └── decomp/
│   ├── components/
│   │   ├── ui/
│   │   ├── shared/
│   │   ├── pages/
│   │   └── comparison/
│   └── lib/
│
├── data/
│   ├── newave/
│   │   ├── decks/
│   │   ├── docs/
│   │   └── chroma/
│   └── decomp/
│       ├── decks/
│       ├── docs/
│       └── chroma/
│
├── uploads/
├── docs/
└── .env
```

---

## FASE 1: Criar Estrutura Base

### 1.1 Criar diretórios

```bash
# Backend
mkdir -p backend/core/nodes
mkdir -p backend/newave/tools
mkdir -p backend/newave/formatters
mkdir -p backend/newave/rag
mkdir -p backend/decomp/tools
mkdir -p backend/decomp/formatters
mkdir -p backend/decomp/rag

# Frontend
mkdir -p frontend/app/newave
mkdir -p frontend/app/decomp
mkdir -p frontend/components/ui
mkdir -p frontend/components/shared
mkdir -p frontend/components/pages
mkdir -p frontend/components/comparison
mkdir -p frontend/lib

# Data
mkdir -p data/newave/decks
mkdir -p data/newave/docs
mkdir -p data/newave/chroma
mkdir -p data/decomp/decks
mkdir -p data/decomp/docs
mkdir -p data/decomp/chroma
```

---

## FASE 2: Migrar Backend Core

### 2.1 Mapeamento de arquivos

| Origem | Destino |
|--------|---------|
| `main.py` | `backend/main.py` |
| `run.py` | `backend/run.py` |
| `requirements.txt` | `backend/requirements.txt` |
| `shared/config.py` | `backend/core/config.py` |
| `shared/base_tool.py` | `backend/core/base_tool.py` |
| `shared/utils/code_executor.py` | `backend/core/code_executor.py` |
| `shared/utils/observability.py` | `backend/core/observability.py` |
| `shared/utils/text_utils.py` | `backend/core/text_utils.py` |
| `shared/utils/debug.py` | `backend/core/debug.py` |
| `shared/utils/json_utils.py` | `backend/core/json_utils.py` |
| `shared/tools/semantic_matcher.py` | `backend/core/semantic_matcher.py` |
| `shared/agents/nodes/coder.py` | `backend/core/nodes/coder.py` |
| `shared/agents/nodes/executor.py` | `backend/core/nodes/executor.py` |
| `shared/agents/nodes/interpreter.py` | `backend/core/nodes/interpreter.py` |
| `shared/agents/nodes/tool_router_base.py` | `backend/core/nodes/tool_router_base.py` |

### 2.2 Criar `backend/core/__init__.py`

```python
"""
Core: Código compartilhado entre agentes NEWAVE e DECOMP.
"""
from .config import *
from .base_tool import BaseTool
```

### 2.3 Criar `backend/core/nodes/__init__.py`

```python
"""
Nodes genéricos do LangGraph para Single Deck Agent.
"""
from .coder import coder_node, create_coder_prompts
from .executor import executor_node
from .interpreter import interpreter_node
from .tool_router_base import execute_tool
```

---

## FASE 3: Migrar Backend NEWAVE

### 3.1 Mapeamento de arquivos

| Origem | Destino |
|--------|---------|
| `newave_agent/app/main.py` | `backend/newave/api.py` |
| `newave_agent/app/config.py` | `backend/newave/config.py` |
| `newave_agent/app/tools/*.py` | `backend/newave/tools/*.py` |
| `newave_agent/app/agents/single_deck/graph.py` | `backend/newave/agent.py` |
| `newave_agent/app/agents/single_deck/state.py` | `backend/newave/state.py` |
| `newave_agent/app/agents/single_deck/nodes/*.py` | `backend/newave/nodes/*.py` |
| `newave_agent/app/agents/single_deck/formatters/` | `backend/newave/formatters/` |
| `newave_agent/app/agents/multi_deck/` | `backend/newave/multi_deck/` |
| `newave_agent/app/rag/` | `backend/newave/rag/` |
| `newave_agent/data/docs/` | `data/newave/docs/` |
| `newave_agent/data/chroma/` | `data/newave/chroma/` |
| `newave_agent/decks/` | `data/newave/decks/` |

### 3.2 Atualizar imports em `backend/newave/`

**Padrão de substituição:**
```python
# ANTES
from newave_agent.app.config import ...
from shared.config import ...
from shared.agents.nodes.coder import ...

# DEPOIS
from backend.newave.config import ...
from backend.core.config import ...
from backend.core.nodes.coder import ...
```

### 3.3 Criar `backend/newave/__init__.py`

```python
"""
Agente NEWAVE: Análise de decks do modelo NEWAVE.
"""
from .api import newave_app
```

---

## FASE 4: Migrar Backend DECOMP

### 4.1 Mapeamento de arquivos

| Origem | Destino |
|--------|---------|
| `decomp_agent/app/main.py` | `backend/decomp/api.py` |
| `decomp_agent/app/config.py` | `backend/decomp/config.py` |
| `decomp_agent/decompclass.py` | `backend/decomp/decompclass.py` |
| `decomp_agent/registrocl.py` | `backend/decomp/registrocl.py` |
| `decomp_agent/app/tools/*.py` | `backend/decomp/tools/*.py` |
| `decomp_agent/app/agents/single_deck/graph.py` | `backend/decomp/agent.py` |
| `decomp_agent/app/agents/single_deck/state.py` | `backend/decomp/state.py` |
| `decomp_agent/app/agents/single_deck/nodes/*.py` | `backend/decomp/nodes/*.py` |
| `decomp_agent/app/agents/single_deck/formatters/` | `backend/decomp/formatters/` |
| `decomp_agent/app/agents/multi_deck/` | `backend/decomp/multi_deck/` |
| `decomp_agent/app/rag/` | `backend/decomp/rag/` |
| `decomp_agent/data/docs/` | `data/decomp/docs/` |
| `decomp_agent/data/chroma/` | `data/decomp/chroma/` |
| `decomp_agent/decks/` | `data/decomp/decks/` |

### 4.2 Atualizar imports em `backend/decomp/`

**Padrão de substituição:**
```python
# ANTES
from decomp_agent.app.config import ...
from shared.config import ...

# DEPOIS
from backend.decomp.config import ...
from backend.core.config import ...
```

### 4.3 Criar `backend/decomp/__init__.py`

```python
"""
Agente DECOMP: Análise de decks do modelo DECOMP.
"""
from .api import decomp_app
```

---

## FASE 5: Atualizar Entry Point Backend

### 5.1 Atualizar `backend/main.py`

```python
"""
Entry point unificado - FastAPI
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.newave.api import newave_app
from backend.decomp.api import decomp_app

app = FastAPI(title="NW Multi Agent API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount agents
app.mount("/api/newave", newave_app)
app.mount("/api/decomp", decomp_app)

@app.get("/")
def root():
    return {"status": "ok", "agents": ["newave", "decomp"]}
```

### 5.2 Atualizar `backend/run.py`

```python
"""
Script para iniciar o servidor.
"""
import sys
import os

# Adicionar backend ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
```

---

## FASE 6: Migrar Frontend

### 6.1 Mapeamento de arquivos

| Origem | Destino |
|--------|---------|
| `app/layout.tsx` | `frontend/app/layout.tsx` |
| `app/page.tsx` | `frontend/app/page.tsx` |
| `app/globals.css` | `frontend/app/globals.css` |
| `app/providers.tsx` | `frontend/app/providers.tsx` |
| `app/newave/` | `frontend/app/newave/` |
| `app/decomp/` | `frontend/app/decomp/` |
| `components/FileUpload.tsx` | `frontend/components/shared/FileUpload.tsx` |
| `components/ChatMessage.tsx` | `frontend/components/shared/ChatMessage.tsx` |
| `components/AgentProgress.tsx` | `frontend/components/shared/AgentProgress.tsx` |
| `components/DeckSelector.tsx` | `frontend/components/shared/DeckSelector.tsx` |
| `components/SessionPanel.tsx` | `frontend/components/shared/SessionPanel.tsx` |
| `components/pages/` | `frontend/components/pages/` |
| `components/comparison/` | `frontend/components/comparison/` |
| `components/single-deck/` | `frontend/components/single-deck/` |
| `components/ui/` | `frontend/components/ui/` |
| `lib/` | `frontend/lib/` |
| `package.json` | `frontend/package.json` |
| `tsconfig.json` | `frontend/tsconfig.json` |
| `tailwind.config.ts` | `frontend/tailwind.config.ts` |
| `next.config.mjs` | `frontend/next.config.mjs` |
| `postcss.config.mjs` | `frontend/postcss.config.mjs` |

### 6.2 Atualizar imports no frontend

**Padrão de substituição:**
```typescript
// ANTES
import { FileUpload } from "@/components/FileUpload"
import { api } from "@/lib/api"

// DEPOIS (mesmo padrão, @ aponta para frontend/)
import { FileUpload } from "@/components/shared/FileUpload"
import { api } from "@/lib/api"
```

### 6.3 Atualizar `frontend/tsconfig.json`

```json
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["./*"]
    }
  }
}
```

### 6.4 Atualizar `frontend/package.json`

Adicionar script para rodar do diretório correto:
```json
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start"
  }
}
```

---

## FASE 7: Atualizar Paths de Dados

### 7.1 Em `backend/core/config.py`

```python
from pathlib import Path

# Base paths
ROOT_DIR = Path(__file__).resolve().parent.parent.parent  # nw_multi/
BACKEND_DIR = ROOT_DIR / "backend"
DATA_DIR = ROOT_DIR / "data"
UPLOADS_DIR = ROOT_DIR / "uploads"
```

### 7.2 Em `backend/newave/config.py`

```python
from backend.core.config import DATA_DIR

NEWAVE_DATA_DIR = DATA_DIR / "newave"
NEWAVE_DECKS_DIR = NEWAVE_DATA_DIR / "decks"
NEWAVE_DOCS_DIR = NEWAVE_DATA_DIR / "docs"
NEWAVE_CHROMA_DIR = NEWAVE_DATA_DIR / "chroma"
```

### 7.3 Em `backend/decomp/config.py`

```python
from backend.core.config import DATA_DIR

DECOMP_DATA_DIR = DATA_DIR / "decomp"
DECOMP_DECKS_DIR = DECOMP_DATA_DIR / "decks"
DECOMP_DOCS_DIR = DECOMP_DATA_DIR / "docs"
DECOMP_CHROMA_DIR = DECOMP_DATA_DIR / "chroma"
```

---

## FASE 8: Limpeza

### 8.1 Diretórios a deletar após migração

```bash
# Após verificar que tudo funciona
rm -rf newave_agent/
rm -rf decomp_agent/
rm -rf shared/
rm -rf app/           # Frontend antigo (agora em frontend/app)
rm -rf components/    # Antigo (agora em frontend/components)
rm -rf lib/           # Antigo (agora em frontend/lib)
```

### 8.2 Arquivos na raiz a mover/deletar

| Arquivo | Ação |
|---------|------|
| `main.py` | Deletar (movido para backend/) |
| `run.py` | Deletar (movido para backend/) |
| `requirements.txt` | Deletar (movido para backend/) |
| `package.json` | Deletar (movido para frontend/) |
| `tsconfig.json` | Deletar (movido para frontend/) |
| `tailwind.config.ts` | Deletar (movido para frontend/) |
| `next.config.mjs` | Deletar (movido para frontend/) |
| `postcss.config.mjs` | Deletar (movido para frontend/) |
| `.env` | Manter na raiz |
| `.gitignore` | Manter na raiz |

---

## FASE 9: Atualizar Scripts de Execução

### 9.1 Criar `start-backend.sh` (ou .bat)

```bash
#!/bin/bash
cd backend
python run.py
```

### 9.2 Criar `start-frontend.sh` (ou .bat)

```bash
#!/bin/bash
cd frontend
npm run dev
```

### 9.3 Criar `start-all.sh` (ou .bat)

```bash
#!/bin/bash
# Start backend in background
cd backend && python run.py &
BACKEND_PID=$!

# Start frontend
cd ../frontend && npm run dev

# Cleanup on exit
trap "kill $BACKEND_PID" EXIT
```

---

## Checklist de Verificação

### Backend
- [ ] `cd backend && python run.py` inicia sem erros
- [ ] `GET http://localhost:8000/` retorna status ok
- [ ] `GET http://localhost:8000/api/newave/decks/list` funciona
- [ ] `GET http://localhost:8000/api/decomp/decks/list` funciona
- [ ] Query NEWAVE funciona
- [ ] Query DECOMP funciona

### Frontend
- [ ] `cd frontend && npm run dev` inicia sem erros
- [ ] `http://localhost:3000` carrega
- [ ] Navegação para /newave funciona
- [ ] Navegação para /decomp funciona
- [ ] Upload de deck funciona
- [ ] Query funciona

### Dados
- [ ] Decks NEWAVE acessíveis em `data/newave/decks/`
- [ ] Decks DECOMP acessíveis em `data/decomp/decks/`
- [ ] ChromaDB funciona nos novos paths

---

## Ordem de Execução Recomendada

```
1. FASE 1   → Criar estrutura de diretórios
2. FASE 2   → Migrar backend/core (shared)
3. FASE 3   → Migrar backend/newave
4. FASE 4   → Migrar backend/decomp
5. FASE 5   → Atualizar entry point backend
6. TESTAR   → Verificar backend funciona
7. FASE 6   → Migrar frontend
8. FASE 7   → Atualizar paths de dados
9. TESTAR   → Verificar frontend funciona
10. FASE 8  → Limpeza (deletar antigos)
11. FASE 9  → Scripts de execução
12. COMMIT  → Commitar mudanças
```

---

## Estimativa de Impacto

| Métrica | Antes | Depois |
|---------|-------|--------|
| Níveis de aninhamento máximo | 6 | 4 |
| Clareza backend vs frontend | Confuso | Claro |
| Tempo para encontrar arquivo | Alto | Baixo |
| Onboarding de novo dev | Difícil | Fácil |
