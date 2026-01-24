# Plano Fase 2: Unificação do Backend

## Objetivo
Unificar código duplicado entre `newave_agent` e `decomp_agent`, criando módulos compartilhados em `shared/`.

---

## 1. Unificação do `config.py`

### Arquivos Atuais
| Arquivo | Linhas |
|---------|--------|
| `newave_agent/app/config.py` | 131 |
| `decomp_agent/app/config.py` | 134 |
| **Total duplicado** | ~265 |

### Duplicação: 95%

### O que é IDÊNTICO (mover para shared)

```python
# shared/config.py

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ===== EMOJI MAPPING (linhas 12-45) =====
EMOJI_MAP = {
    "[INFO]": "[i]",
    "[DEBUG]": "[D]",
    "[WARNING]": "[!]",
    "[ERROR]": "[X]",
    "[SUCCESS]": "[OK]",
    # ... resto do mapeamento (idêntico em ambos)
}

# ===== SAFE PRINT (linhas 47-68) =====
def safe_print(message: str, *args, **kwargs):
    """Print seguro para Windows que substitui emojis problemáticos."""
    safe_message = message
    for emoji, replacement in EMOJI_MAP.items():
        safe_message = safe_message.replace(emoji, replacement)
    try:
        print(safe_message, *args, **kwargs)
    except OSError:
        ascii_message = safe_message.encode('ascii', errors='replace').decode('ascii')
        print(ascii_message, *args, **kwargs)

# ===== DEBUG PRINT (linhas 73-82) =====
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

def debug_print(message: str, *args, **kwargs):
    """Print condicional para debug."""
    if DEBUG:
        safe_print(f"[DEBUG] {message}", *args, **kwargs)

# ===== OPENAI CONFIG =====
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

# ===== RAG CONFIG =====
RAG_CHUNK_SIZE = int(os.getenv("RAG_CHUNK_SIZE", "2000"))
RAG_CHUNK_OVERLAP = int(os.getenv("RAG_CHUNK_OVERLAP", "200"))
RAG_TOP_K = int(os.getenv("RAG_TOP_K", "5"))

# ===== EXECUTOR CONFIG =====
CODE_EXECUTION_TIMEOUT = int(os.getenv("CODE_EXECUTION_TIMEOUT", "30"))

# ===== SEMANTIC MATCHING =====
SEMANTIC_MATCHING_ENABLED = os.getenv("SEMANTIC_MATCHING_ENABLED", "true").lower() == "true"
SEMANTIC_MATCH_THRESHOLD = float(os.getenv("SEMANTIC_MATCH_THRESHOLD", "0.3"))
SEMANTIC_FALLBACK_THRESHOLD = float(os.getenv("SEMANTIC_FALLBACK_THRESHOLD", "0.2"))

# ===== DISAMBIGUATION =====
DISAMBIGUATION_ENABLED = os.getenv("DISAMBIGUATION_ENABLED", "true").lower() == "true"
DISAMBIGUATION_SCORE_DIFF_THRESHOLD = float(os.getenv("DISAMBIGUATION_SCORE_DIFF_THRESHOLD", "0.15"))

# ===== LANGFUSE =====
LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY")
LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY")
LANGFUSE_HOST = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
```

### O que permanece ESPECÍFICO por agente

```python
# newave_agent/app/config.py
from shared.config import *

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DOCS_DIR = DATA_DIR / "docs"
UPLOADS_DIR = BASE_DIR / "uploads"
CHROMA_DIR = DATA_DIR / "chroma"  # <-- ESPECÍFICO NEWAVE
```

```python
# decomp_agent/app/config.py
from shared.config import *

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DOCS_DIR = DATA_DIR / "docs"
UPLOADS_DIR = BASE_DIR / "uploads"
CHROMA_DIR = DATA_DIR / "chroma" / "decomp"  # <-- ESPECÍFICO DECOMP
```

### Resultado Esperado
- **Antes:** 265 linhas (131 + 134)
- **Depois:** ~100 linhas em shared + ~20 linhas em cada agente = ~140 linhas
- **Redução:** ~125 linhas (~47%)

---

## 2. Unificação do `coder.py`

### Arquivos Atuais
| Arquivo | Linhas |
|---------|--------|
| `newave_agent/app/agents/single_deck/nodes/coder.py` | 187 |
| `decomp_agent/app/agents/single_deck/nodes/coder.py` | 187 |
| **Total** | 374 |

### Duplicação: 95%

### Diferenças (apenas 9 linhas)

| Aspecto | NEWAVE | DECOMP |
|---------|--------|--------|
| Library name | `inewave` | `idecomp` |
| Import exemplo | `from inewave.newave import NomeClasse` | `from idecomp.decomp import Dadger` |
| Método de leitura | `NomeClasse.read(deck_path)` | `Dadger.read(deck_path / "dadger.rv0")` |

### Estrutura Proposta

```python
# shared/agents/nodes/coder.py

from typing import Dict, Any
from langchain_openai import ChatOpenAI
from shared.config import OPENAI_API_KEY, OPENAI_MODEL, safe_print

def create_coder_prompts(library_name: str, library_import: str, read_example: str) -> Dict[str, str]:
    """Cria prompts parametrizados para o coder."""

    system_prompt = f"""You are an expert Python programmer specialized in the {library_name} library...

Example import:
```python
{library_import}
```

Example reading:
```python
{read_example}
```
"""

    user_prompt = f"Generate Python code using {library_name} library to answer: {{query}}"

    retry_prompt = """The previous code had an error..."""  # Idêntico em ambos

    return {
        "system": system_prompt,
        "user": user_prompt,
        "retry": retry_prompt
    }

def coder_node(state: Dict[str, Any], prompts: Dict[str, str]) -> Dict[str, Any]:
    """Node genérico do coder."""
    # Lógica idêntica (linhas 104-187)
    # ...
    return state
```

```python
# newave_agent/app/agents/single_deck/nodes/coder.py

from shared.agents.nodes.coder import create_coder_prompts, coder_node as _coder_node

PROMPTS = create_coder_prompts(
    library_name="inewave",
    library_import="from inewave.newave import Pmo, Sistema, Dger",
    read_example="pmo = Pmo.read(deck_path)"
)

def coder_node(state):
    return _coder_node(state, PROMPTS)
```

```python
# decomp_agent/app/agents/single_deck/nodes/coder.py

from shared.agents.nodes.coder import create_coder_prompts, coder_node as _coder_node

PROMPTS = create_coder_prompts(
    library_name="idecomp",
    library_import="from idecomp.decomp import Dadger, Relato",
    read_example='dadger = Dadger.read(deck_path / "dadger.rv0")'
)

def coder_node(state):
    return _coder_node(state, PROMPTS)
```

### Resultado Esperado
- **Antes:** 374 linhas
- **Depois:** ~150 linhas shared + ~20 linhas cada agente = ~190 linhas
- **Redução:** ~184 linhas (~49%)

---

## 3. Unificação do `executor.py`

### Arquivos Atuais
| Arquivo | Linhas |
|---------|--------|
| `newave_agent/app/agents/single_deck/nodes/executor.py` | 53 |
| `decomp_agent/app/agents/single_deck/nodes/executor.py` | 54 |
| **Total** | 107 |

### Duplicação: 90%

### Única Diferença
- DECOMP passa `timeout=CODE_EXECUTION_TIMEOUT` explícito
- NEWAVE usa timeout padrão

### Estrutura Proposta

```python
# shared/agents/nodes/executor.py

from typing import Dict, Any, Optional
from shared.utils.code_executor import execute_python_code
from shared.config import safe_print

def executor_node(state: Dict[str, Any], timeout: Optional[int] = None) -> Dict[str, Any]:
    """Node genérico do executor."""
    code = state.get("generated_code", "")
    deck_path = state.get("deck_path", "")

    if not code:
        safe_print("[EXECUTOR] Nenhum código para executar")
        return {**state, "execution_result": None, "execution_error": "No code to execute"}

    safe_print(f"[EXECUTOR] Executando código...")

    kwargs = {"code": code, "deck_path": deck_path}
    if timeout:
        kwargs["timeout"] = timeout

    result = execute_python_code(**kwargs)

    if result.get("success"):
        safe_print("[EXECUTOR] Código executado com sucesso")
        return {**state, "execution_result": result.get("output"), "execution_error": None}
    else:
        safe_print(f"[EXECUTOR] Erro: {result.get('error')}")
        return {**state, "execution_result": None, "execution_error": result.get("error")}
```

```python
# newave_agent/app/agents/single_deck/nodes/executor.py
from shared.agents.nodes.executor import executor_node
# Re-exporta diretamente, sem timeout customizado
```

```python
# decomp_agent/app/agents/single_deck/nodes/executor.py
from shared.agents.nodes.executor import executor_node as _executor_node
from decomp_agent.app.config import CODE_EXECUTION_TIMEOUT

def executor_node(state):
    return _executor_node(state, timeout=CODE_EXECUTION_TIMEOUT)
```

### Resultado Esperado
- **Antes:** 107 linhas
- **Depois:** ~45 linhas shared + ~5 linhas cada agente = ~55 linhas
- **Redução:** ~52 linhas (~49%)

---

## 4. Unificação do `interpreter.py`

### Arquivos Atuais
| Arquivo | Linhas |
|---------|--------|
| `newave_agent/app/agents/single_deck/nodes/interpreter.py` | 182 |
| `decomp_agent/app/agents/single_deck/nodes/interpreter.py` | 142 |
| **Total** | 324 |

### Duplicação: 70%

### Diferenças Principais

| Aspecto | NEWAVE | DECOMP |
|---------|--------|--------|
| Debug logging | Extensivo (`_write_debug_log()`) | Nenhum |
| Error handling | Básico | Robusto (try-catch + inspect) |
| No-tool message | Específico NEWAVE | Específico DECOMP |

### Estrutura Proposta

```python
# shared/agents/nodes/interpreter.py

from typing import Dict, Any, Optional, Callable
import inspect
from shared.config import safe_print, DEBUG

def interpreter_node(
    state: Dict[str, Any],
    formatter_registry: Any,
    no_tool_message: str,
    debug_logger: Optional[Callable] = None
) -> Dict[str, Any]:
    """Node genérico do interpreter."""

    tool_name = state.get("selected_tool")
    tool_result = state.get("tool_result")
    query = state.get("query", "")
    deck_path = state.get("deck_path", "")

    if debug_logger and DEBUG:
        debug_logger(f"Interpreting result for {tool_name}")

    if not tool_result:
        safe_print("[INTERPRETER] Nenhum resultado para interpretar")
        return {**state, "final_response": no_tool_message}

    # Buscar formatter
    try:
        formatter = formatter_registry.get_formatter_for_tool(tool_name, tool_result)

        # Detectar se formatter aceita deck_path (DECOMP approach - mais robusto)
        sig = inspect.signature(formatter.format_response)
        if "deck_path" in sig.parameters:
            formatted = formatter.format_response(tool_result, deck_path=deck_path)
        else:
            formatted = formatter.format_response(tool_result)

        return {**state, "final_response": formatted}

    except Exception as e:
        safe_print(f"[INTERPRETER] Erro ao formatar: {e}")
        return {**state, "final_response": f"Erro ao processar resultado: {str(e)}"}
```

```python
# newave_agent/app/agents/single_deck/nodes/interpreter.py
from shared.agents.nodes.interpreter import interpreter_node as _interpreter_node
from newave_agent.app.agents.single_deck.formatters import registry

NO_TOOL_MESSAGE = """Não encontrei uma ferramenta adequada para sua consulta.
Tente perguntas sobre: carga mensal, vazões, submercados, cadastro de usinas..."""

def interpreter_node(state):
    return _interpreter_node(state, registry, NO_TOOL_MESSAGE)
```

```python
# decomp_agent/app/agents/single_deck/nodes/interpreter.py
from shared.agents.nodes.interpreter import interpreter_node as _interpreter_node
from decomp_agent.app.agents.single_deck.formatters import registry

NO_TOOL_MESSAGE = """Não encontrei uma ferramenta adequada para sua consulta.
Tente perguntas sobre: usinas hidrelétricas, limites de intercâmbio, CVU..."""

def interpreter_node(state):
    return _interpreter_node(state, registry, NO_TOOL_MESSAGE)
```

### Resultado Esperado
- **Antes:** 324 linhas
- **Depois:** ~80 linhas shared + ~20 linhas cada agente = ~120 linhas
- **Redução:** ~204 linhas (~63%)

---

## 5. Unificação do `semantic_matcher.py`

### Arquivos Atuais
| Arquivo | Linhas |
|---------|--------|
| `newave_agent/app/tools/semantic_matcher.py` | 667 |
| `decomp_agent/app/tools/semantic_matcher.py` | 671 |
| **Total** | 1338 |

### Duplicação: 85%

### O que é IDÊNTICO (mover para shared)

```python
# shared/tools/semantic_matcher.py

# Cache management (100% idêntico)
_query_embedding_cache = {}
_tool_embedding_cache = {}
_similarity_cache = {}

def clear_query_cache(): ...
def clear_tool_cache(): ...
def clear_similarity_cache(): ...
def get_cache_stats(): ...

# Embedding functions (100% idêntico)
def _normalize_embedding(embedding): ...
def _get_query_embedding(query, client): ...
def _get_tool_embedding(tool, client): ...
def _get_tool_embeddings_parallel(tools, client): ...

# Similarity calculation (100% idêntico)
def _calculate_cosine_similarity_batch(query_embedding, tool_embeddings): ...

# Top tools finder (100% idêntico)
def find_top_tools_semantic(query, tools, client, top_k=5): ...
```

### O que é ESPECÍFICO (parametrizar)

```python
# shared/tools/semantic_matcher.py

def expand_query(query: str, agent_expansions: Dict[str, List[str]] = None) -> str:
    """Expande query com termos relacionados."""

    # Expansões genéricas (compartilhadas)
    GENERIC_EXPANSIONS = {
        "carga": ["demanda", "consumo", "mwmed"],
        "submercado": ["região", "subsistema"],
        # ...
    }

    # Combina com expansões específicas do agente
    all_expansions = {**GENERIC_EXPANSIONS}
    if agent_expansions:
        all_expansions.update(agent_expansions)

    expanded = query
    for term, synonyms in all_expansions.items():
        if term in query.lower():
            expanded += " " + " ".join(synonyms)

    return expanded

def find_best_tool_semantic(
    query: str,
    tools: List[Any],
    client: Any,
    use_can_handle_filter: bool = False  # DECOMP usa True
) -> Optional[Any]:
    """Encontra a melhor tool semanticamente."""

    # Se DECOMP, filtra por can_handle primeiro
    if use_can_handle_filter:
        tools = [t for t in tools if t.can_handle(query)]

    # Resto da lógica (idêntica)
    # ...
```

```python
# newave_agent/app/tools/semantic_matcher.py
from shared.tools.semantic_matcher import (
    find_best_tool_semantic as _find_best,
    find_top_tools_semantic,
    expand_query,
    # ... outros
)

def find_best_tool_semantic(query, tools, client):
    return _find_best(query, tools, client, use_can_handle_filter=False)
```

```python
# decomp_agent/app/tools/semantic_matcher.py
from shared.tools.semantic_matcher import (
    find_best_tool_semantic as _find_best,
    find_top_tools_semantic,
    expand_query,
    # ... outros
)

DECOMP_EXPANSIONS = {
    "disponibilidade": ["disponível", "indisponível", "manutenção"],
    "inflexibilidade": ["inflexível", "geração mínima"],
    "cvu": ["custo variável", "custo unitário"],
    # ... outros específicos DECOMP
}

def find_best_tool_semantic(query, tools, client):
    expanded = expand_query(query, DECOMP_EXPANSIONS)
    return _find_best(expanded, tools, client, use_can_handle_filter=True)
```

### Resultado Esperado
- **Antes:** 1338 linhas
- **Depois:** ~450 linhas shared + ~100 linhas cada agente = ~650 linhas
- **Redução:** ~688 linhas (~51%)

---

## 6. Unificação Parcial do `tool_router.py`

### Arquivos Atuais
| Arquivo | Linhas |
|---------|--------|
| `newave_agent/app/agents/single_deck/nodes/tool_router.py` | 658 |
| `decomp_agent/app/agents/single_deck/nodes/tool_router.py` | 203 |
| **Total** | 861 |

### Duplicação: 30% (apenas core)

### Abordagem: Extrair APENAS `_execute_tool()`

A lógica de execução de tool é idêntica (~85 linhas). O resto é muito diferente:
- NEWAVE tem disambiguation (180+ linhas extras)
- DECOMP é simplificado

```python
# shared/agents/nodes/tool_router_base.py

from typing import Dict, Any, Optional
from shared.config import safe_print

def execute_tool(
    tool: Any,
    query: str,
    deck_path: str,
    tool_name: str
) -> Dict[str, Any]:
    """Executa uma tool e retorna o resultado."""

    safe_print(f"[TOOL_ROUTER] Executando {tool_name}...")

    try:
        result = tool.execute(query)

        if result.get("success"):
            safe_print(f"[TOOL_ROUTER] {tool_name} executado com sucesso")
            return {
                "selected_tool": tool_name,
                "tool_result": result,
                "tool_error": None
            }
        else:
            error = result.get("error", "Unknown error")
            safe_print(f"[TOOL_ROUTER] Erro em {tool_name}: {error}")
            return {
                "selected_tool": tool_name,
                "tool_result": None,
                "tool_error": error
            }

    except Exception as e:
        safe_print(f"[TOOL_ROUTER] Exceção em {tool_name}: {e}")
        return {
            "selected_tool": tool_name,
            "tool_result": None,
            "tool_error": str(e)
        }
```

### Resultado Esperado
- **Antes:** 861 linhas
- **Depois:** ~85 linhas shared + 573 NEWAVE + 118 DECOMP = ~776 linhas
- **Redução:** ~85 linhas (~10%)

**Nota:** A unificação maior do tool_router é complexa devido às diferenças arquiteturais. Recomenda-se focar nos outros componentes primeiro.

---

## Resumo de Impacto

| Componente | Antes | Depois | Redução | % |
|------------|-------|--------|---------|---|
| config.py | 265 | 140 | 125 | 47% |
| coder.py | 374 | 190 | 184 | 49% |
| executor.py | 107 | 55 | 52 | 49% |
| interpreter.py | 324 | 120 | 204 | 63% |
| semantic_matcher.py | 1338 | 650 | 688 | 51% |
| tool_router.py | 861 | 776 | 85 | 10% |
| **TOTAL** | **3269** | **1931** | **1338** | **41%** |

---

## Estrutura de Diretórios Proposta

```
shared/
├── __init__.py
├── config.py                    # Config unificado
├── base_tool.py                 # Já existe
├── agents/
│   ├── __init__.py
│   └── nodes/
│       ├── __init__.py
│       ├── coder.py             # Coder genérico
│       ├── executor.py          # Executor genérico
│       ├── interpreter.py       # Interpreter genérico
│       └── tool_router_base.py  # Apenas _execute_tool
├── tools/
│   ├── __init__.py
│   └── semantic_matcher.py      # Matcher unificado
└── utils/
    ├── __init__.py
    ├── code_executor.py         # Já existe
    ├── observability.py         # Já existe
    └── text_utils.py            # Já existe
```

---

## Checklist de Execução

### Fase 2.1: Config
- [ ] Criar `shared/config.py`
- [ ] Refatorar `newave_agent/app/config.py`
- [ ] Refatorar `decomp_agent/app/config.py`
- [ ] Testar imports em ambos agentes

### Fase 2.2: Coder
- [ ] Criar `shared/agents/nodes/coder.py`
- [ ] Refatorar `newave_agent/.../coder.py`
- [ ] Refatorar `decomp_agent/.../coder.py`
- [ ] Testar geração de código

### Fase 2.3: Executor
- [ ] Criar `shared/agents/nodes/executor.py`
- [ ] Refatorar ambos executors
- [ ] Testar execução de código

### Fase 2.4: Interpreter
- [ ] Criar `shared/agents/nodes/interpreter.py`
- [ ] Refatorar ambos interpreters
- [ ] Testar formatação de respostas

### Fase 2.5: Semantic Matcher
- [ ] Criar `shared/tools/semantic_matcher.py`
- [ ] Refatorar ambos matchers
- [ ] Testar matching semântico

### Fase 2.6: Tool Router (Opcional)
- [ ] Criar `shared/agents/nodes/tool_router_base.py`
- [ ] Extrair `_execute_tool()` para shared
- [ ] Testar roteamento de tools

---

## Verificação Final

```bash
# Backend completo
python run.py
# Servidor deve iniciar sem erros

# Teste NEWAVE
curl -X POST http://localhost:8000/api/newave/query \
  -H "Content-Type: application/json" \
  -d '{"query": "qual a carga mensal?", "session_id": "test"}'

# Teste DECOMP
curl -X POST http://localhost:8000/api/decomp/query \
  -H "Content-Type: application/json" \
  -d '{"query": "quais usinas hidrelétricas?", "session_id": "test"}'
```
