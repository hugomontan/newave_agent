# Plano de Migração: Mudanças de Código Detalhadas

## Objetivo
Documentar todas as mudanças de imports e paths necessárias para a nova estrutura de pastas.

---

## ESTRUTURA FINAL

```
nw_multi/
├── backend/
│   ├── main.py
│   ├── run.py
│   ├── requirements.txt
│   ├── core/                    ← shared/ atual
│   ├── newave/                  ← newave_agent/app/
│   └── decomp/                  ← decomp_agent/app/
├── frontend/
│   ├── app/                     ← app/ atual
│   ├── components/              ← components/ atual
│   ├── lib/                     ← lib/ atual
│   └── package.json
├── data/
│   ├── newave/
│   └── decomp/
└── .env
```

---

## MUDANÇAS DE CÓDIGO - BACKEND

### Tabela de Substituição de Imports

| ANTES | DEPOIS |
|-------|--------|
| `from newave_agent.app.` | `from backend.newave.` |
| `from decomp_agent.app.` | `from backend.decomp.` |
| `from decomp_agent.registrocl` | `from backend.decomp.registrocl` |
| `from decomp_agent.decompclass` | `from backend.decomp.decompclass` |
| `from shared.` | `from backend.core.` |

---

### Arquivos a Alterar - CORE (shared/ → backend/core/)

| Arquivo | Import Antigo | Import Novo |
|---------|---------------|-------------|
| `shared/config.py` | - | - (sem imports internos) |
| `shared/utils/__init__.py` | `from shared.utils.` | `from backend.core.` |
| `shared/utils/debug.py` | `from shared.config` | `from backend.core.config` |
| `shared/agents/nodes/__init__.py` | `from shared.agents.nodes.` | `from backend.core.nodes.` |
| `shared/agents/nodes/coder.py` | `from shared.config` | `from backend.core.config` |
| `shared/agents/nodes/executor.py` | `from shared.utils.code_executor` | `from backend.core.code_executor` |
| `shared/agents/nodes/executor.py` | `from shared.config` | `from backend.core.config` |
| `shared/agents/nodes/interpreter.py` | `from shared.config` | `from backend.core.config` |
| `shared/agents/nodes/interpreter.py` | `from shared.utils.text_utils` | `from backend.core.text_utils` |
| `shared/agents/nodes/tool_router_base.py` | `from shared.config` | `from backend.core.config` |
| `shared/tools/__init__.py` | `from shared.tools.` | `from backend.core.` |
| `shared/tools/semantic_matcher.py` | `from shared.config` | `from backend.core.config` |

---

### Arquivos a Alterar - NEWAVE (newave_agent/app/ → backend/newave/)

| Arquivo | Imports a Alterar |
|---------|-------------------|
| `config.py` | `from shared.config import *` → `from backend.core.config import *` |
| `main.py` | `from newave_agent.app.config` → `from backend.newave.config` |
| `main.py` | `from newave_agent.app.agents.` → `from backend.newave.agents.` |
| `main.py` | `from newave_agent.app.rag` → `from backend.newave.rag` |
| `main.py` | `from newave_agent.app.utils.` → `from backend.newave.utils.` |
| `tools/base.py` | `from shared.base_tool` → `from backend.core.base_tool` |
| `tools/*.py` | `from newave_agent.app.tools.base` → `from backend.newave.tools.base` |
| `tools/*.py` | `from newave_agent.app.config` → `from backend.newave.config` |
| `tools/*.py` | `from newave_agent.app.utils.` → `from backend.newave.utils.` |
| `tools/semantic_matcher.py` | `from shared.tools.semantic_matcher` → `from backend.core.semantic_matcher` |
| `utils/deck_loader.py` | `from newave_agent.app.config` → `from backend.newave.config` |
| `rag/indexer.py` | `from newave_agent.app.config` → `from backend.newave.config` |
| `rag/indexer.py` | `from newave_agent.app.rag.vectorstore` → `from backend.newave.rag.vectorstore` |
| `rag/vectorstore.py` | `from newave_agent.app.config` → `from backend.newave.config` |
| `agents/__init__.py` | `from newave_agent.app.agents.` → `from backend.newave.agents.` |
| `agents/single_deck/nodes/*.py` | `from shared.agents.nodes.` → `from backend.core.nodes.` |
| `agents/single_deck/nodes/*.py` | `from shared.utils.` → `from backend.core.` |

---

### Arquivos a Alterar - DECOMP (decomp_agent/app/ → backend/decomp/)

| Arquivo | Imports a Alterar |
|---------|-------------------|
| `config.py` | `from shared.config import *` → `from backend.core.config import *` |
| `main.py` | `from decomp_agent.app.` → `from backend.decomp.` |
| `tools/base.py` | `from shared.base_tool` → `from backend.core.base_tool` |
| `tools/*.py` | `from decomp_agent.app.tools.base` → `from backend.decomp.tools.base` |
| `tools/*.py` | `from decomp_agent.app.config` → `from backend.decomp.config` |
| `tools/*.py` | `from decomp_agent.app.utils.` → `from backend.decomp.utils.` |
| `tools/*.py` | `from decomp_agent.registrocl` → `from backend.decomp.registrocl` |
| `tools/*.py` | `from shared.utils.usina_name_matcher` → `from backend.core.usina_name_matcher` |
| `tools/semantic_matcher.py` | `from shared.tools.semantic_matcher` → `from backend.core.semantic_matcher` |
| `tools/semantic_matcher.py` | `from decomp_agent.app.rag.vectorstore` → `from backend.decomp.rag.vectorstore` |
| `utils/dadgnl.py` | `from decomp_agent.registrocl` → `from backend.decomp.registrocl` |
| `utils/dadgnl_cache.py` | `from decomp_agent.app.` → `from backend.decomp.` |
| `utils/dadger_cache.py` | `from decomp_agent.app.` → `from backend.decomp.` |
| `utils/deck_loader.py` | `from decomp_agent.app.config` → `from backend.decomp.config` |
| `rag/indexer.py` | `from decomp_agent.app.` → `from backend.decomp.` |
| `rag/vectorstore.py` | `from decomp_agent.app.config` → `from backend.decomp.config` |
| `agents/single_deck/nodes/*.py` | `from shared.agents.nodes.` → `from backend.core.nodes.` |

---

### Arquivo Raiz - main.py

```python
# ANTES
from newave_agent.app.main import app as newave_app
from decomp_agent.app.main import app as decomp_app

# DEPOIS
from backend.newave.main import app as newave_app
from backend.decomp.main import app as decomp_app
```

---

## MUDANÇAS DE CÓDIGO - FRONTEND

### tsconfig.json - ÚNICA MUDANÇA NECESSÁRIA

**Opção A:** Se tsconfig.json ficar na RAIZ:
```json
// ANTES
"paths": {
  "@/*": ["./*"]
}

// DEPOIS
"paths": {
  "@/*": ["./frontend/*"]
}
```

**Opção B:** Se tsconfig.json for movido para `frontend/`:
```json
// Manter como está
"paths": {
  "@/*": ["./*"]
}
```

### Imports Frontend - NÃO MUDAM

Todos os imports `@/components/...`, `@/lib/...` continuam funcionando automaticamente se tsconfig.json for atualizado corretamente.

---

## MUDANÇAS DE PATHS DE DADOS

### backend/core/config.py

```python
# ANTES
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

# DEPOIS
ROOT_DIR = Path(__file__).resolve().parent.parent.parent  # nw_multi/
BACKEND_DIR = ROOT_DIR / "backend"
DATA_DIR = ROOT_DIR / "data"
UPLOADS_DIR = ROOT_DIR / "uploads"
```

### backend/newave/config.py

```python
# ANTES
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CHROMA_DIR = DATA_DIR / "chroma"

# DEPOIS
from backend.core.config import DATA_DIR
NEWAVE_DATA_DIR = DATA_DIR / "newave"
CHROMA_DIR = NEWAVE_DATA_DIR / "chroma"
DOCS_DIR = NEWAVE_DATA_DIR / "docs"
DECKS_DIR = NEWAVE_DATA_DIR / "decks"
```

### backend/decomp/config.py

```python
# ANTES
CHROMA_DIR = DATA_DIR / "chroma" / "decomp"

# DEPOIS
from backend.core.config import DATA_DIR
DECOMP_DATA_DIR = DATA_DIR / "decomp"
CHROMA_DIR = DECOMP_DATA_DIR / "chroma"
DOCS_DIR = DECOMP_DATA_DIR / "docs"
DECKS_DIR = DECOMP_DATA_DIR / "decks"
```

---

## COMANDOS DE MIGRAÇÃO

### Fase 1: Criar estrutura de diretórios

```bash
# Backend
mkdir -p backend/core/nodes
mkdir -p backend/newave
mkdir -p backend/decomp

# Frontend
mkdir -p frontend

# Data
mkdir -p data/newave/decks
mkdir -p data/newave/docs
mkdir -p data/newave/chroma
mkdir -p data/decomp/decks
mkdir -p data/decomp/docs
mkdir -p data/decomp/chroma
```

### Fase 2: Mover arquivos

```bash
# ==========================================
# BACKEND CORE (shared/ → backend/core/)
# ==========================================
cp -r shared/* backend/core/
# Flatten agents/nodes para nodes/
mv backend/core/agents/nodes/* backend/core/nodes/
rm -rf backend/core/agents
# Flatten tools para core/
mv backend/core/tools/* backend/core/
rm -rf backend/core/tools
# Flatten utils para core/
mv backend/core/utils/* backend/core/
rm -rf backend/core/utils

# ==========================================
# BACKEND NEWAVE
# ==========================================
cp -r newave_agent/app/* backend/newave/

# Mover dados
cp -r newave_agent/data/docs/* data/newave/docs/ 2>/dev/null || true
cp -r newave_agent/data/chroma/* data/newave/chroma/ 2>/dev/null || true
cp -r newave_agent/decks/* data/newave/decks/ 2>/dev/null || true

# ==========================================
# BACKEND DECOMP
# ==========================================
cp -r decomp_agent/app/* backend/decomp/
cp decomp_agent/decompclass.py backend/decomp/
cp decomp_agent/registrocl.py backend/decomp/

# Mover dados
cp -r decomp_agent/data/docs/* data/decomp/docs/ 2>/dev/null || true
cp -r decomp_agent/data/chroma/* data/decomp/chroma/ 2>/dev/null || true
cp -r decomp_agent/decks/* data/decomp/decks/ 2>/dev/null || true

# ==========================================
# BACKEND RAIZ
# ==========================================
cp main.py backend/
cp run.py backend/
cp requirements.txt backend/

# ==========================================
# FRONTEND
# ==========================================
cp -r app/* frontend/app/ 2>/dev/null || mkdir -p frontend/app && cp -r app/* frontend/app/
cp -r components/* frontend/components/ 2>/dev/null || mkdir -p frontend/components && cp -r components/* frontend/components/
cp -r lib/* frontend/lib/ 2>/dev/null || mkdir -p frontend/lib && cp -r lib/* frontend/lib/
cp package.json frontend/
cp package-lock.json frontend/ 2>/dev/null || true
cp tsconfig.json frontend/
cp tailwind.config.ts frontend/ 2>/dev/null || true
cp tailwind.config.js frontend/ 2>/dev/null || true
cp next.config.mjs frontend/ 2>/dev/null || true
cp next.config.js frontend/ 2>/dev/null || true
cp postcss.config.mjs frontend/ 2>/dev/null || true
cp postcss.config.js frontend/ 2>/dev/null || true
```

### Fase 3: Substituir imports em massa

```bash
# ==========================================
# BACKEND CORE
# ==========================================
# Linux/Mac
find backend/core -name "*.py" -exec sed -i 's/from shared\./from backend.core./g' {} \;
find backend/core -name "*.py" -exec sed -i 's/import shared\./import backend.core./g' {} \;

# Windows (PowerShell)
Get-ChildItem -Path backend/core -Filter *.py -Recurse | ForEach-Object {
    (Get-Content $_.FullName) -replace 'from shared\.', 'from backend.core.' | Set-Content $_.FullName
}

# ==========================================
# BACKEND NEWAVE
# ==========================================
# Linux/Mac
find backend/newave -name "*.py" -exec sed -i 's/from newave_agent\.app\./from backend.newave./g' {} \;
find backend/newave -name "*.py" -exec sed -i 's/from shared\./from backend.core./g' {} \;

# Windows (PowerShell)
Get-ChildItem -Path backend/newave -Filter *.py -Recurse | ForEach-Object {
    $content = Get-Content $_.FullName
    $content = $content -replace 'from newave_agent\.app\.', 'from backend.newave.'
    $content = $content -replace 'from shared\.', 'from backend.core.'
    Set-Content $_.FullName $content
}

# ==========================================
# BACKEND DECOMP
# ==========================================
# Linux/Mac
find backend/decomp -name "*.py" -exec sed -i 's/from decomp_agent\.app\./from backend.decomp./g' {} \;
find backend/decomp -name "*.py" -exec sed -i 's/from decomp_agent\./from backend.decomp./g' {} \;
find backend/decomp -name "*.py" -exec sed -i 's/from shared\./from backend.core./g' {} \;

# Windows (PowerShell)
Get-ChildItem -Path backend/decomp -Filter *.py -Recurse | ForEach-Object {
    $content = Get-Content $_.FullName
    $content = $content -replace 'from decomp_agent\.app\.', 'from backend.decomp.'
    $content = $content -replace 'from decomp_agent\.', 'from backend.decomp.'
    $content = $content -replace 'from shared\.', 'from backend.core.'
    Set-Content $_.FullName $content
}
```

### Fase 4: Atualizar imports específicos que não seguem padrão

```python
# backend/core/nodes/executor.py
# Mudar de:
from shared.utils.code_executor import execute_python_code
# Para:
from backend.core.code_executor import execute_python_code

# backend/core/nodes/interpreter.py
# Mudar de:
from shared.utils.text_utils import clean_response_text
# Para:
from backend.core.text_utils import clean_response_text

# backend/newave/tools/semantic_matcher.py
# Mudar de:
from shared.tools.semantic_matcher import ...
# Para:
from backend.core.semantic_matcher import ...

# backend/decomp/tools/*.py (que usam usina_name_matcher)
# Mudar de:
from shared.utils.usina_name_matcher import ...
# Para:
from backend.core.usina_name_matcher import ...
```

### Fase 5: Limpar diretórios antigos

```bash
# ATENÇÃO: Só executar após verificar que tudo funciona!
rm -rf shared/
rm -rf newave_agent/
rm -rf decomp_agent/
rm -rf app/
rm -rf components/
rm -rf lib/
rm main.py
rm run.py
rm requirements.txt
rm package.json
rm package-lock.json
rm tsconfig.json
rm tailwind.config.ts tailwind.config.js 2>/dev/null
rm next.config.mjs next.config.js 2>/dev/null
rm postcss.config.mjs postcss.config.js 2>/dev/null
```

---

## VERIFICAÇÃO

### Verificar Backend

```bash
cd backend

# Testar imports
python -c "from backend.core.config import *; print('✓ Core config OK')"
python -c "from backend.core.base_tool import BaseTool; print('✓ BaseTool OK')"
python -c "from backend.core.nodes.coder import coder_node; print('✓ Coder node OK')"
python -c "from backend.newave.main import app; print('✓ NEWAVE app OK')"
python -c "from backend.decomp.main import app; print('✓ DECOMP app OK')"

# Iniciar servidor
python run.py
# Deve iniciar em http://localhost:8000
```

### Verificar Frontend

```bash
cd frontend

# Instalar dependências (se necessário)
npm install

# Build de teste
npm run build
# Deve compilar sem erros

# Dev server
npm run dev
# Deve rodar em http://localhost:3001
```

### Verificar Funcional

1. Abrir http://localhost:3001
2. Navegar para /newave
3. Ir para /newave/analysis
4. Fazer upload de um deck
5. Executar uma query (ex: "qual a carga mensal?")
6. Repetir para /decomp

---

## RESUMO DE ARQUIVOS AFETADOS

| Categoria | Quantidade | Tipo de Mudança |
|-----------|------------|-----------------|
| Core (shared) | ~15 arquivos | Renomear imports `shared.` → `backend.core.` |
| NEWAVE | ~30 arquivos | Renomear imports `newave_agent.app.` → `backend.newave.` |
| DECOMP | ~25 arquivos | Renomear imports `decomp_agent.` → `backend.decomp.` |
| Frontend | 1 arquivo | Atualizar tsconfig.json paths |
| **Total** | **~71 arquivos** | - |

---

## POSSÍVEIS PROBLEMAS E SOLUÇÕES

### Problema 1: Import circular
**Sintoma:** `ImportError: cannot import name 'X' from partially initialized module`
**Solução:** Mover import para dentro da função que o usa

### Problema 2: Módulo não encontrado
**Sintoma:** `ModuleNotFoundError: No module named 'backend'`
**Solução:** Adicionar `backend/` ao PYTHONPATH:
```python
# No início de run.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
```

### Problema 3: Path de dados incorreto
**Sintoma:** `FileNotFoundError` ao carregar decks
**Solução:** Verificar se DATA_DIR aponta para `nw_multi/data/`

### Problema 4: Frontend não encontra componentes
**Sintoma:** `Module not found: Can't resolve '@/components/...'`
**Solução:** Verificar tsconfig.json paths:
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

---

## SCRIPTS DE EXECUÇÃO (criar na raiz)

### start-backend.bat (Windows)

```batch
@echo off
cd backend
python run.py
```

### start-frontend.bat (Windows)

```batch
@echo off
cd frontend
npm run dev
```

### start-backend.sh (Linux/Mac)

```bash
#!/bin/bash
cd backend
python run.py
```

### start-frontend.sh (Linux/Mac)

```bash
#!/bin/bash
cd frontend
npm run dev
```
