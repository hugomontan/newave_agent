# Plano Fase 1: Limpeza de Código Morto

## Objetivo
Remover arquivos não utilizados, páginas órfãs e diretórios abandonados para reduzir ruído no repositório.

---

## 1. Arquivos Python Não Utilizados

### Arquivos a Deletar

| Arquivo | Evidência | Linhas |
|---------|-----------|--------|
| `shared/utils/debug.py` | Zero imports em todo o codebase | ~50 |
| `shared/utils/json_utils.py` | Zero imports em todo o codebase | ~30 |
| `shared/utils/logging.py` | Zero imports em todo o codebase | ~40 |

### Verificação Prévia
```bash
# Confirmar que não há imports
grep -r "from shared.utils.debug" --include="*.py" .
grep -r "from shared.utils.json_utils" --include="*.py" .
grep -r "from shared.utils.logging" --include="*.py" .
```

### Ação
```bash
# Deletar arquivos
rm shared/utils/debug.py
rm shared/utils/json_utils.py
rm shared/utils/logging.py
```

---

## 2. Páginas Frontend Órfãs

### Contexto
O roteamento principal (`app/page.tsx`) direciona para:
- `/newave` → `/newave/analysis`, `/newave/comparison`
- `/decomp` → `/decomp/analysis`, `/decomp/comparison`

As páginas na raiz (`/analysis`, `/comparison`) NÃO são acessíveis via navegação normal.

### Arquivos a Deletar

| Arquivo | Status | Linhas |
|---------|--------|--------|
| `app/analysis/page.tsx` | Órfão - canonical é `/newave/analysis` | ~949 |
| `app/comparison/page.tsx` | Órfão - canonical é `/newave/comparison` | ~1076 |

### Verificação Prévia
```bash
# Confirmar que não há links para essas rotas
grep -r '"/analysis"' --include="*.tsx" --include="*.ts" .
grep -r '"/comparison"' --include="*.tsx" --include="*.ts" .
# Se encontrar, verificar se são rotas relativas (ok) ou absolutas (problema)
```

### Ação
```bash
# Deletar diretórios
rm -rf app/analysis/
rm -rf app/comparison/
```

---

## 3. Diretório Frontend Abandonado

### Contexto
O diretório `frontend/` contém apenas:
- `.next/` - Build cache do Next.js
- `node_modules/` - Dependências (se existir)

Nenhum arquivo source (`.tsx`, `.ts`, `.jsx`, `.js`).

### Verificação Prévia
```bash
# Listar conteúdo
ls -la frontend/
# Verificar se há arquivos source
find frontend/ -name "*.tsx" -o -name "*.ts" -o -name "*.jsx" -o -name "*.js" | head -20
```

### Ação
```bash
# Deletar diretório inteiro
rm -rf frontend/
```

---

## 4. Arquivos a MANTER (Verificados como em Uso)

### `decomp_agent/decompclass.py`
- **Status:** EM USO ATIVO
- **Evidência:** 72 arquivos importam de `decomp_agent`
- **Usado por:** `main.py`, `dadger_cache.py`, nodes, tools, formatters
- **Ação:** MANTER

### `decomp_agent/registrocl.py`
- **Status:** EM USO
- **Evidência:** Importado por `gl_geracoes_gnl_tool.py` e `dadgnl.py`
- **Usado para:** Classe de registro GL customizada
- **Ação:** MANTER

### Arquivos `__init__.py` não rastreados
- `newave_agent/app/agents/shared/__init__.py`
- `newave_agent/app/agents/shared/formatting/__init__.py`
- `newave_agent/app/agents/shared/helpers/__init__.py`
- **Status:** Novos arquivos da branch `clean-code`
- **Propósito:** Reorganização de módulos
- **Ação:** ADICIONAR AO GIT (são intencionais)

---

## Resumo de Impacto

| Item | Linhas Removidas | Risco |
|------|------------------|-------|
| Utils Python não usados | ~120 | Nenhum |
| Páginas frontend órfãs | ~2025 | Baixo |
| Diretório frontend/ | N/A (apenas cache) | Nenhum |
| **TOTAL** | **~2145 linhas** | **Baixo** |

---

## Checklist de Execução

- [ ] Executar verificações prévias (greps)
- [ ] Deletar `shared/utils/debug.py`
- [ ] Deletar `shared/utils/json_utils.py`
- [ ] Deletar `shared/utils/logging.py`
- [ ] Deletar `app/analysis/`
- [ ] Deletar `app/comparison/`
- [ ] Deletar `frontend/`
- [ ] Adicionar novos `__init__.py` ao git
- [ ] Rodar `python run.py` - verificar que backend inicia
- [ ] Rodar `npm run dev` - verificar que frontend compila
- [ ] Testar navegação: `/newave/analysis`, `/decomp/analysis`
- [ ] Commit das mudanças

---

## Comandos de Verificação Pós-Limpeza

```bash
# Backend
python run.py
# Deve iniciar sem erros de import

# Frontend
npm run dev
# Deve compilar sem erros

# Navegação (manual)
# http://localhost:3000/newave/analysis - deve funcionar
# http://localhost:3000/decomp/analysis - deve funcionar
# http://localhost:3000/analysis - deve dar 404 (esperado)
```
