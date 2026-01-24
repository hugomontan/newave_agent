# Plano Fase 3: Unificação do Frontend

## Objetivo
Unificar componentes e páginas duplicados no frontend, mantendo estrutura de pastas separadas para melhor legibilidade.

---

## 1. Unificação do FileUpload

### Arquivos Atuais
| Arquivo | Linhas |
|---------|--------|
| `components/FileUpload.tsx` | 156 |
| `components/FileUploadDecomp.tsx` | 156 |
| **Total** | 312 |

### Duplicação: 99.4%

### Diferenças (apenas 4 linhas)

| Linha | FileUpload | FileUploadDecomp |
|-------|-----------|------------------|
| 7 | `import { uploadDeck }` | `import { uploadDecompDeck }` |
| 15 | `export function FileUpload` | `export function FileUploadDecomp` |
| 73 | `uploadDeck(file)` | `uploadDecompDeck(file)` |
| 135 | `"deck NEWAVE"` | `"deck DECOMP"` |

### Solução: Componente Parametrizado

```tsx
// components/FileUpload.tsx

import { useState, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { uploadDeck, uploadDecompDeck, UploadResponse } from "@/lib/api";

type ModelType = 'newave' | 'decomp';

interface FileUploadProps {
  model: ModelType;
  onUploadSuccess: (response: UploadResponse) => void;
  disabled?: boolean;
}

const MODEL_CONFIG = {
  newave: {
    uploadFn: uploadDeck,
    label: "NEWAVE",
    acceptedExtensions: [".zip", ".dat", ".txt"],
  },
  decomp: {
    uploadFn: uploadDecompDeck,
    label: "DECOMP",
    acceptedExtensions: [".zip", ".dat", ".rv0"],
  },
};

export function FileUpload({ model, onUploadSuccess, disabled }: FileUploadProps) {
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const config = MODEL_CONFIG[model];

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return;

    const file = acceptedFiles[0];
    setUploading(true);
    setError(null);

    try {
      const response = await config.uploadFn(file);
      onUploadSuccess(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao fazer upload");
    } finally {
      setUploading(false);
    }
  }, [config, onUploadSuccess]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    disabled: disabled || uploading,
    accept: {
      "application/zip": [".zip"],
      "text/plain": [".dat", ".txt", ".rv0"],
    },
    maxFiles: 1,
  });

  return (
    <div
      {...getRootProps()}
      className={`
        border-2 border-dashed rounded-lg p-8 text-center cursor-pointer
        transition-colors duration-200
        ${isDragActive ? "border-blue-500 bg-blue-50" : "border-gray-300"}
        ${disabled ? "opacity-50 cursor-not-allowed" : "hover:border-blue-400"}
      `}
    >
      <input {...getInputProps()} />

      {uploading ? (
        <p className="text-gray-600">Enviando arquivo...</p>
      ) : isDragActive ? (
        <p className="text-blue-600">Solte o arquivo aqui</p>
      ) : (
        <div>
          <p className="text-gray-600 mb-2">
            Arraste seu deck {config.label} aqui
          </p>
          <p className="text-gray-400 text-sm">
            ou clique para selecionar
          </p>
        </div>
      )}

      {error && (
        <p className="text-red-500 mt-2 text-sm">{error}</p>
      )}
    </div>
  );
}

// Exports para compatibilidade com código existente
export function FileUploadDecomp(props: Omit<FileUploadProps, 'model'>) {
  return <FileUpload {...props} model="decomp" />;
}
```

### Migração

1. Atualizar `components/FileUpload.tsx` com código acima
2. Deletar `components/FileUploadDecomp.tsx`
3. Atualizar imports onde `FileUploadDecomp` é usado:
   - `app/decomp/analysis/page.tsx`
   - `app/decomp/comparison/page.tsx`

### Resultado Esperado
- **Antes:** 312 linhas (2 arquivos)
- **Depois:** ~100 linhas (1 arquivo)
- **Redução:** ~212 linhas (68%)

---

## 2. Criação de Componente de Página Compartilhado

### Arquivos Atuais
| Arquivo | Linhas |
|---------|--------|
| `app/newave/analysis/page.tsx` | 1192 |
| `app/decomp/analysis/page.tsx` | 1195 |
| **Total** | 2387 |

### Duplicação: 99%

### Abordagem: Manter Páginas Separadas + Componente Compartilhado

Em vez de usar dynamic routes, vamos extrair a lógica para um componente compartilhado e manter as páginas como wrappers simples.

### Estrutura Proposta

```
components/
├── pages/
│   ├── AnalysisPageContent.tsx    # Lógica compartilhada
│   └── ComparisonPageContent.tsx  # Lógica compartilhada
app/
├── newave/
│   ├── analysis/
│   │   └── page.tsx               # Wrapper simples
│   └── comparison/
│       └── page.tsx               # Wrapper simples
└── decomp/
    ├── analysis/
    │   └── page.tsx               # Wrapper simples
    └── comparison/
        └── page.tsx               # Wrapper simples
```

### Componente Compartilhado de Análise

```tsx
// components/pages/AnalysisPageContent.tsx

"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";
import { FileUpload } from "@/components/FileUpload";
import { ChatMessage } from "@/components/ChatMessage";
import { AgentProgress } from "@/components/AgentProgress";
import {
  sendQueryStream,
  queryDecompStream,
  reindexDocs,
  reindexDecompDocs,
  loadDeckFromRepo,
  loadDecompDeckFromRepo,
  getSession,
  QueryResponse,
} from "@/lib/api";

type ModelType = 'newave' | 'decomp';

interface AnalysisPageContentProps {
  model: ModelType;
}

const MODEL_CONFIG = {
  newave: {
    title: "Análise Single Deck - NEWAVE",
    backRoute: "/newave",
    streamFn: sendQueryStream,
    reindexFn: reindexDocs,
    loadDeckFn: loadDeckFromRepo,
    getSessionFn: (id: string) => getSession(id),
  },
  decomp: {
    title: "Análise Single Deck - DECOMP",
    backRoute: "/decomp",
    streamFn: queryDecompStream,
    reindexFn: reindexDecompDocs,
    loadDeckFn: loadDecompDeckFromRepo,
    getSessionFn: (id: string) => getSession(id, "decomp"),
  },
};

export function AnalysisPageContent({ model }: AnalysisPageContentProps) {
  const router = useRouter();
  const config = MODEL_CONFIG[model];

  // Estados (idênticos em ambas páginas)
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Array<{role: string; content: string}>>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [agentSteps, setAgentSteps] = useState<string[]>([]);
  // ... outros estados

  // Handlers usando config
  const handleQuery = useCallback(async () => {
    if (!sessionId || !input.trim()) return;

    setLoading(true);
    setAgentSteps([]);

    try {
      await config.streamFn(sessionId, input, "single", (step) => {
        setAgentSteps(prev => [...prev, step]);
      });
      // ... resto da lógica
    } catch (error) {
      console.error("Error:", error);
    } finally {
      setLoading(false);
    }
  }, [sessionId, input, config]);

  const handleLoadDeck = useCallback(async (deckName: string) => {
    try {
      const response = await config.loadDeckFn(deckName);
      setSessionId(response.session_id);
    } catch (error) {
      console.error("Error loading deck:", error);
    }
  }, [config]);

  // Render (estrutura idêntica)
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center">
          <button onClick={() => router.push(config.backRoute)}>
            Voltar
          </button>
          <h1 className="text-xl font-semibold ml-4">{config.title}</h1>
        </div>
      </header>

      {/* Content */}
      <main className="max-w-7xl mx-auto px-4 py-8">
        {!sessionId ? (
          <FileUpload
            model={model}
            onUploadSuccess={(response) => setSessionId(response.session_id)}
          />
        ) : (
          <div className="space-y-4">
            {/* Messages */}
            {messages.map((msg, i) => (
              <ChatMessage key={i} role={msg.role} content={msg.content} />
            ))}

            {/* Agent Progress */}
            {loading && <AgentProgress steps={agentSteps} />}

            {/* Input */}
            <div className="flex gap-2">
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Digite sua pergunta..."
                className="flex-1 border rounded-lg px-4 py-2"
                disabled={loading}
              />
              <button
                onClick={handleQuery}
                disabled={loading || !input.trim()}
                className="bg-blue-500 text-white px-4 py-2 rounded-lg"
              >
                Enviar
              </button>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
```

### Páginas Wrapper

```tsx
// app/newave/analysis/page.tsx

"use client";

import { AnalysisPageContent } from "@/components/pages/AnalysisPageContent";

export default function NewaveAnalysisPage() {
  return <AnalysisPageContent model="newave" />;
}
```

```tsx
// app/decomp/analysis/page.tsx

"use client";

import { AnalysisPageContent } from "@/components/pages/AnalysisPageContent";

export default function DecompAnalysisPage() {
  return <AnalysisPageContent model="decomp" />;
}
```

### Resultado Esperado para Páginas de Análise
- **Antes:** 2387 linhas (2 arquivos grandes)
- **Depois:** ~800 linhas shared + ~10 linhas cada página = ~820 linhas
- **Redução:** ~1567 linhas (66%)

---

## 3. Componente Compartilhado de Comparação

### Arquivos Atuais
| Arquivo | Linhas |
|---------|--------|
| `app/newave/comparison/page.tsx` | 1396 |
| `app/decomp/comparison/page.tsx` | 1247 |
| **Total** | 2643 |

### Duplicação: 85-90%

### Componente Compartilhado

```tsx
// components/pages/ComparisonPageContent.tsx

"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { DeckSelector } from "@/components/DeckSelector";
import { ChatMessage } from "@/components/ChatMessage";
import { ComparisonRouter } from "@/components/comparison/ComparisonRouter";
import {
  sendQueryStream,
  queryDecompStream,
  initComparison,
  initDecompComparison,
  listDecks,
  listDecompDecks,
} from "@/lib/api";

type ModelType = 'newave' | 'decomp';

interface ComparisonPageContentProps {
  model: ModelType;
}

const MODEL_CONFIG = {
  newave: {
    title: "Análise Comparativa - NEWAVE",
    backRoute: "/newave",
    streamFn: sendQueryStream,
    initComparisonFn: initComparison,
    listDecksFn: listDecks,
  },
  decomp: {
    title: "Análise Comparativa - DECOMP",
    backRoute: "/decomp",
    streamFn: queryDecompStream,
    initComparisonFn: initDecompComparison,
    listDecksFn: listDecompDecks,
  },
};

export function ComparisonPageContent({ model }: ComparisonPageContentProps) {
  const router = useRouter();
  const config = MODEL_CONFIG[model];

  // Estados
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [selectedDecks, setSelectedDecks] = useState<string[]>([]);
  const [availableDecks, setAvailableDecks] = useState<string[]>([]);
  const [comparison, setComparison] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  // ... outros estados

  // Carregar decks disponíveis
  useEffect(() => {
    config.listDecksFn()
      .then(setAvailableDecks)
      .catch(console.error);
  }, [config]);

  // Iniciar comparação
  const handleInitComparison = useCallback(async () => {
    if (selectedDecks.length < 2) return;

    setLoading(true);
    try {
      const response = await config.initComparisonFn(selectedDecks);
      setSessionId(response.session_id);
    } catch (error) {
      console.error("Error:", error);
    } finally {
      setLoading(false);
    }
  }, [selectedDecks, config]);

  // Query
  const handleQuery = useCallback(async (query: string) => {
    if (!sessionId) return;

    setLoading(true);
    try {
      const response = await config.streamFn(sessionId, query, "comparison");
      if (response.comparison_data) {
        setComparison(response.comparison_data);
      }
    } catch (error) {
      console.error("Error:", error);
    } finally {
      setLoading(false);
    }
  }, [sessionId, config]);

  // Render
  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center">
          <button onClick={() => router.push(config.backRoute)}>
            Voltar
          </button>
          <h1 className="text-xl font-semibold ml-4">{config.title}</h1>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8">
        {!sessionId ? (
          <DeckSelector
            model={model}
            availableDecks={availableDecks}
            selectedDecks={selectedDecks}
            onSelect={setSelectedDecks}
            onConfirm={handleInitComparison}
            loading={loading}
          />
        ) : (
          <div className="space-y-6">
            {/* Comparison Display */}
            {comparison && (
              <ComparisonRouter comparison={comparison} model={model} />
            )}

            {/* Query Input */}
            {/* ... input UI ... */}
          </div>
        )}
      </main>
    </div>
  );
}
```

### Páginas Wrapper

```tsx
// app/newave/comparison/page.tsx
"use client";
import { ComparisonPageContent } from "@/components/pages/ComparisonPageContent";
export default function NewaveComparisonPage() {
  return <ComparisonPageContent model="newave" />;
}
```

```tsx
// app/decomp/comparison/page.tsx
"use client";
import { ComparisonPageContent } from "@/components/pages/ComparisonPageContent";
export default function DecompComparisonPage() {
  return <ComparisonPageContent model="decomp" />;
}
```

### Resultado Esperado para Páginas de Comparação
- **Antes:** 2643 linhas (2 arquivos)
- **Depois:** ~900 linhas shared + ~10 linhas cada página = ~920 linhas
- **Redução:** ~1723 linhas (65%)

---

## 4. Organização dos Componentes de Comparação

### Estado Atual
```
components/comparison/
├── cvu/                    # NEWAVE
├── cvu-decomp/             # DECOMP (duplicado)
├── carga-mensal/           # NEWAVE
├── carga-ande-decomp/      # DECOMP
├── gl-decomp/              # DECOMP only
├── restricao-eletrica/     # NEWAVE
├── restricao-eletrica-decomp/  # DECOMP (duplicado)
└── shared/                 # Tipos compartilhados
```

### Proposta de Organização
```
components/comparison/
├── shared/
│   ├── types.ts
│   ├── ComparisonChart.tsx
│   ├── ComparisonTable.tsx
│   └── DifferencesView.tsx
├── cvu/
│   ├── CVUView.tsx          # Genérico (aceita model prop)
│   ├── CVUChart.tsx
│   └── CVUTable.tsx
├── carga/
│   ├── CargaView.tsx        # Genérico
│   ├── CargaChart.tsx
│   └── CargaTable.tsx
├── restricao-eletrica/
│   ├── RestricaoEletricaView.tsx  # Genérico
│   └── ...
├── gl/                      # DECOMP específico (sem equivalente NEWAVE)
│   ├── GLView.tsx
│   └── ...
└── ComparisonRouter.tsx     # Router que seleciona componente
```

### Exemplo: Unificando CVU

```tsx
// components/comparison/cvu/CVUView.tsx

interface CVUViewProps {
  comparison: ComparisonData;
  model: 'newave' | 'decomp';
}

export function CVUView({ comparison, model }: CVUViewProps) {
  // Lógica compartilhada
  const { comparison_table, chart_data, deck_names } = comparison;

  // Pequenas diferenças podem ser tratadas com condicionais
  const columns = model === 'decomp'
    ? ['estagio', 'patamar', 'usina', 'cvu']
    : ['mes', 'ano', 'usina', 'cvu'];

  return (
    <div className="space-y-4">
      <CVUChart data={chart_data} model={model} />
      <CVUTable data={comparison_table} columns={columns} />
    </div>
  );
}
```

### ComparisonRouter Atualizado

```tsx
// components/comparison/ComparisonRouter.tsx

import { CVUView } from "./cvu/CVUView";
import { CargaView } from "./carga/CargaView";
import { RestricaoEletricaView } from "./restricao-eletrica/RestricaoEletricaView";
import { GLView } from "./gl/GLView";
import { GenericComparisonView } from "./shared/GenericComparisonView";

interface ComparisonRouterProps {
  comparison: ComparisonData;
  model: 'newave' | 'decomp';
}

const TOOL_COMPONENT_MAP: Record<string, React.ComponentType<any>> = {
  'ClastValoresTool': CVUView,
  'CVUTool': CVUView,
  'CargaMensalTool': CargaView,
  'CargaAndeTool': CargaView,
  'RestricaoEletricaTool': RestricaoEletricaView,
  'GLGeracoesGNLTool': GLView,
};

export function ComparisonRouter({ comparison, model }: ComparisonRouterProps) {
  const { tool_name, visualization_type } = comparison;

  // Buscar componente específico
  const Component = TOOL_COMPONENT_MAP[tool_name];

  if (Component) {
    return <Component comparison={comparison} model={model} />;
  }

  // Fallback genérico
  return <GenericComparisonView comparison={comparison} />;
}
```

### Resultado Esperado para Componentes de Comparação
- **Antes:** ~61 arquivos com muita duplicação
- **Depois:** ~40 arquivos organizados
- **Redução:** ~21 arquivos (~34%)

---

## Resumo de Impacto

| Componente | Antes | Depois | Redução | % |
|------------|-------|--------|---------|---|
| FileUpload | 312 | 100 | 212 | 68% |
| Analysis Pages | 2387 | 820 | 1567 | 66% |
| Comparison Pages | 2643 | 920 | 1723 | 65% |
| Comparison Components | ~3000* | ~2000* | ~1000* | 33% |
| **TOTAL** | **~8342** | **~3840** | **~4502** | **54%** |

*Estimativas para componentes de comparação

---

## Estrutura Final de Diretórios

```
components/
├── FileUpload.tsx              # Unificado com prop model
├── ChatMessage.tsx
├── AgentProgress.tsx
├── DeckSelector.tsx
├── pages/
│   ├── AnalysisPageContent.tsx    # Novo - lógica compartilhada
│   └── ComparisonPageContent.tsx  # Novo - lógica compartilhada
├── comparison/
│   ├── shared/
│   │   ├── types.ts
│   │   ├── ComparisonChart.tsx
│   │   ├── ComparisonTable.tsx
│   │   └── GenericComparisonView.tsx
│   ├── cvu/
│   │   └── CVUView.tsx           # Genérico (aceita model)
│   ├── carga/
│   │   └── CargaView.tsx         # Genérico
│   ├── restricao-eletrica/
│   │   └── RestricaoEletricaView.tsx
│   ├── gl/                       # DECOMP específico
│   │   └── GLView.tsx
│   └── ComparisonRouter.tsx
└── ui/
    └── ... (componentes base)

app/
├── page.tsx                      # Home (escolha NEWAVE/DECOMP)
├── newave/
│   ├── page.tsx                  # Menu NEWAVE
│   ├── analysis/
│   │   └── page.tsx              # Wrapper simples
│   └── comparison/
│       └── page.tsx              # Wrapper simples
└── decomp/
    ├── page.tsx                  # Menu DECOMP
    ├── analysis/
    │   └── page.tsx              # Wrapper simples
    └── comparison/
        └── page.tsx              # Wrapper simples
```

---

## Checklist de Execução

### Fase 3.1: FileUpload
- [ ] Refatorar `components/FileUpload.tsx` para aceitar prop `model`
- [ ] Adicionar export de compatibilidade `FileUploadDecomp`
- [ ] Testar upload em ambos os modos
- [ ] Deletar `components/FileUploadDecomp.tsx` após validação

### Fase 3.2: Componentes de Página
- [ ] Criar `components/pages/AnalysisPageContent.tsx`
- [ ] Criar `components/pages/ComparisonPageContent.tsx`
- [ ] Refatorar `app/newave/analysis/page.tsx` para usar wrapper
- [ ] Refatorar `app/decomp/analysis/page.tsx` para usar wrapper
- [ ] Refatorar `app/newave/comparison/page.tsx` para usar wrapper
- [ ] Refatorar `app/decomp/comparison/page.tsx` para usar wrapper
- [ ] Testar todas as rotas

### Fase 3.3: Componentes de Comparação
- [ ] Identificar componentes duplicados (cvu, cvu-decomp, etc.)
- [ ] Criar versões genéricas com prop `model`
- [ ] Atualizar `ComparisonRouter.tsx`
- [ ] Remover componentes duplicados
- [ ] Testar visualizações de comparação

---

## Verificação Final

```bash
# Build
npm run build
# Deve compilar sem erros

# Dev server
npm run dev

# Testar navegação
# http://localhost:3000 - Home
# http://localhost:3000/newave - Menu NEWAVE
# http://localhost:3000/newave/analysis - Análise NEWAVE
# http://localhost:3000/newave/comparison - Comparação NEWAVE
# http://localhost:3000/decomp - Menu DECOMP
# http://localhost:3000/decomp/analysis - Análise DECOMP
# http://localhost:3000/decomp/comparison - Comparação DECOMP

# Testar funcionalidades
# 1. Upload de deck em /newave/analysis
# 2. Upload de deck em /decomp/analysis
# 3. Seleção de decks em /newave/comparison
# 4. Seleção de decks em /decomp/comparison
# 5. Query em cada modo
# 6. Visualização de comparação
```

---

## Ordem de Execução Recomendada

```
1. FileUpload (independente, baixo risco)
2. AnalysisPageContent (maior impacto)
3. Páginas de análise (wrappers)
4. ComparisonPageContent
5. Páginas de comparação (wrappers)
6. Componentes de comparação (mais complexo)
7. Limpeza de arquivos antigos
```
