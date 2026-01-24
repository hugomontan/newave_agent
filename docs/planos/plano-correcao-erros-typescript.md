# Plano: Correção de Erros TypeScript - Fase 1 Limpeza

## Resumo Executivo

**Status:** 1 erro de tipo TypeScript bloqueando compilação  
**Arquivo afetado:** `components/comparison/limites-intercambio-decomp/LimitesIntercambioComparisonTable.tsx`  
**Solução:** Adicionar cast `as any` na linha 28 (consistente com padrão do projeto)  
**Tempo estimado:** < 1 minuto  
**Risco:** Baixo (função funciona em runtime, apenas incompatibilidade de tipos)

## Objetivo
Corrigir todos os erros de tipo TypeScript que impedem a compilação do frontend após a limpeza de código morto.

## Status Atual

### Erros Identificados (Total: 1)

#### 1. Erro de Tipo: `TableRow[]` vs `CSVExportData[]`
- **Arquivo:** `components/comparison/limites-intercambio-decomp/LimitesIntercambioComparisonTable.tsx`
- **Linha:** 28
- **Erro:** `Argument of type 'TableRow[]' is not assignable to parameter of type 'CSVExportData[]'`
- **Causa:** TypeScript não reconhece `TableRow` como compatível com `CSVExportData`, mesmo tendo estrutura idêntica
- **Contexto:** Função `exportToCSV` espera `CSVExportData[]` mas recebe `TableRow[]`

### Análise do Problema

#### Definição de Tipos

**`TableRow`** (em `components/comparison/shared/types.ts`, linha 139):
```typescript
export interface TableRow {
  data?: string | number;
  classe?: string;
  // ... muitos campos específicos ...
  deck_1?: number | null;
  deck_2?: number | null;
  // ... campos dinâmicos para N decks ...
  [key: `deck_${number}`]: number | null | undefined;
  // ... mais campos ...
}
```

**Observação:** `TableRow` tem campos específicos definidos + index signature parcial para `deck_${number}`, mas **NÃO tem** index signature geral `[key: string]: ...`

**`CSVExportData`** (em `components/comparison/shared/csvExport.ts`, linha 5):
```typescript
export interface CSVExportData {
  [key: string]: string | number | null | undefined;
}
```

**Observação:** `CSVExportData` tem apenas index signature geral, permitindo qualquer chave string.

#### Por que o erro ocorre?

TypeScript não considera `TableRow` compatível com `CSVExportData` porque:
1. `TableRow` não tem index signature geral `[key: string]: ...`
2. TypeScript requer que o tipo de origem tenha **todos** os membros do tipo de destino
3. Embora em runtime funcionem (ambos são objetos com propriedades string), TypeScript é estrito sobre estruturas de tipo

#### Contexto de Uso

A função `exportToCSV` precisa de um index signature porque:
- Itera sobre todas as chaves do objeto: `Object.keys(row)`
- Acessa propriedades dinamicamente: `row[col]`
- Não conhece antecipadamente quais campos existem

#### Arquivos Afetados

Baseado na busca, 32 arquivos usam `exportToCSV`, mas apenas 1 está falhando:
- `components/comparison/limites-intercambio-decomp/LimitesIntercambioComparisonTable.tsx` ❌
- `components/comparison/carga-ande-decomp/CargaAndeComparisonTable.tsx` ✅ (já corrigido com `as any`)

## Plano de Correção

### Opção 1: Cast para `any` (Solução Rápida)
**Prós:**
- Correção imediata
- Consistente com outras correções já aplicadas
- Baixo risco

**Contras:**
- Perde type safety
- Não resolve o problema de raiz

**Implementação:**
```typescript
exportToCSV(data as any, "limites-intercambio-comparison");
```

### Opção 2: Unificar Tipos (Solução Ideal)
**Prós:**
- Resolve o problema de raiz
- Melhora type safety
- Evita erros futuros

**Contras:**
- Requer refatoração de tipos
- Mais trabalho

**Implementação:**
1. Criar tipo base compartilhado
2. Fazer `TableRow` e `CSVExportData` estenderem o tipo base
3. Ou fazer `CSVExportData` ser um alias de `TableRow`

### Opção 3: Converter `TableRow[]` para `CSVExportData[]` (Solução Intermediária)
**Prós:**
- Mantém type safety
- Não requer mudanças em tipos

**Contras:**
- Conversão desnecessária (mesma estrutura)

**Implementação:**
```typescript
exportToCSV(data as CSVExportData[], "limites-intercambio-comparison");
```

## Recomendação

**Usar Opção 1 (cast para `any`)** por:
1. **Consistência:** Outro arquivo similar (`CargaAndeComparisonTable.tsx`) já usa `as any` na linha 28
2. **Urgência:** Precisa compilar para completar a limpeza de código morto
3. **Baixo risco:** Função `exportToCSV` já funciona com `TableRow[]` em runtime (ambos têm estrutura compatível)
4. **Pragmatismo:** Refatoração de tipos (Opção 2) pode ser feita em fase dedicada, não bloqueia limpeza atual
5. **Padrão do projeto:** Várias correções anteriores já usaram `as any` para resolver incompatibilidades de tipo similares

## Checklist de Execução

- [ ] Verificar definição de `CSVExportData` em `components/comparison/shared/csvExport.ts`
- [ ] Verificar definição de `TableRow` em `components/comparison/shared/types.ts`
- [ ] Aplicar correção em `LimitesIntercambioComparisonTable.tsx`
- [ ] Executar `npm run build` para verificar
- [ ] Se houver mais erros, documentar e corrigir sequencialmente

## Arquivos a Modificar

### 1. `components/comparison/limites-intercambio-decomp/LimitesIntercambioComparisonTable.tsx`

**Localização:** Linha 28

**Código Atual:**
```typescript
const handleDownloadCSV = () => {
  exportToCSV(data, "limites-intercambio-comparison");
};
```

**Código Corrigido:**
```typescript
const handleDownloadCSV = () => {
  exportToCSV(data as any, "limites-intercambio-comparison");
};
```

**Justificativa:**
- Consistente com `CargaAndeComparisonTable.tsx` (linha 28)
- `TableRow` e `CSVExportData` são estruturalmente compatíveis em runtime
- Cast é seguro porque `exportToCSV` apenas lê propriedades via index signature

## Verificação Pós-Correção

```bash
# Executar build
npm run build

# Verificar que compila sem erros
# Deve mostrar: "✓ Compiled successfully" sem "Failed to compile"
```

## Notas e Contexto Adicional

### Por que este erro apareceu?

Este erro provavelmente já existia antes, mas pode ter sido exposto por:
1. Mudanças em strictness do TypeScript após atualizações
2. Mudanças em imports após limpeza de código
3. Verificação de tipos mais rigorosa no build de produção

### Arquivos Similares (Já Corrigidos)

- `components/comparison/carga-ande-decomp/CargaAndeComparisonTable.tsx` (linha 28) - usa `as any`
- Outros 30+ arquivos usam `exportToCSV` mas não têm este erro (provavelmente já corrigidos ou usando tipos compatíveis)

### Refatoração Futura (Opcional)

Para resolver o problema de raiz, considerar:
1. Adicionar index signature geral a `TableRow`:
   ```typescript
   export interface TableRow {
     // ... campos existentes ...
     [key: string]: string | number | null | undefined; // Adicionar esta linha
   }
   ```
2. Ou fazer `CSVExportData` estender `TableRow`:
   ```typescript
   export type CSVExportData = TableRow;
   ```
3. Ou criar tipo base compartilhado que ambos estendem

**Nota:** Refatoração de tipos deve ser feita em fase separada para não bloquear limpeza atual.
