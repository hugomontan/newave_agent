# Plano de Implementação: Comparação Multi-Deck - Restrições Elétricas

## Objetivo
Criar funcionalidade de comparação multi-deck para `RestricoesEletricasDECOMPTool`, consolidando dados de múltiplos decks em uma tabela e dois gráficos de linha (GMIN e GMAX).

## Estrutura dos Dados

### Dados de Entrada (Single-Deck)
Cada deck retorna da `RestricoesEletricasDECOMPTool`:
```python
{
    "success": True,
    "data": [
        {
            "Nome": "SERRA DO FACAO",
            "GMIN P1": 55.0,
            "GMIN P2": 55.0,
            "GMIN P3": 55.0,
            "GMAX P1": 212.0,
            "GMAX P2": 212.0,
            "GMAX P3": 212.0,
            # ... outros campos (codigo_restricao, estagio, etc.)
        }
    ]
}
```

### Dados de Saída (Multi-Deck)
**Tabela consolidada** (comparison_table):
```python
[
    {
        "deck": "DC202501-sem1",
        "display_name": "Janeiro 2025 - Semana 1",
        "Nome": "SERRA DO FACAO",
        "GMIN P1": 55.0,
        "GMIN P2": 55.0,
        "GMIN P3": 55.0,
        "GMAX P1": 212.0,
        "GMAX P2": 212.0,
        "GMAX P3": 212.0
    },
    {
        "deck": "DC202502-sem1",
        "display_name": "Fevereiro 2025 - Semana 1",
        "Nome": "SERRA DO FACAO",
        "GMIN P1": 55.0,
        "GMIN P2": 55.0,
        "GMIN P3": 55.0,
        "GMAX P1": 215.0,  # Mudou
        "GMAX P2": 215.0,
        "GMAX P3": 215.0
    },
    # ... mais decks
]
```

**Gráfico GMIN** (chart_data_gmin):
```python
{
    "labels": ["JAN25 - S1", "FEV25 - S1", ...],  # Labels compactas dos decks
    "datasets": [
        {
            "label": "GMIN P1",
            "data": [55.0, 55.0, ...],
            "borderColor": "rgb(59, 130, 246)",
            ...
        },
        {
            "label": "GMIN P2",
            "data": [55.0, 55.0, ...],
            "borderColor": "rgb(16, 185, 129)",
            ...
        },
        {
            "label": "GMIN P3",
            "data": [55.0, 55.0, ...],
            "borderColor": "rgb(245, 158, 11)",
            ...
        }
    ]
}
```

**Gráfico GMAX** (chart_data_gmax):
```python
{
    "labels": ["JAN25 - S1", "FEV25 - S1", ...],
    "datasets": [
        {
            "label": "GMAX P1",
            "data": [212.0, 215.0, ...],
            "borderColor": "rgb(239, 68, 68)",
            ...
        },
        {
            "label": "GMAX P2",
            "data": [212.0, 215.0, ...],
            "borderColor": "rgb(234, 179, 8)",
            ...
        },
        {
            "label": "GMAX P3",
            "data": [212.0, 215.0, ...],
            "borderColor": "rgb(139, 92, 246)",
            ...
        }
    ]
}
```

## Implementação

### 1. Backend: Formatter de Comparação

**Arquivo**: `decomp_agent/app/agents/multi_deck/formatting/data_formatters/restricoes_eletricas_comparison_formatter.py`

**Estrutura**:
```python
class RestricoesEletricasComparisonFormatter(ComparisonFormatter):
    def can_format(self, tool_name: str, result_structure: Dict[str, Any]) -> bool:
        # Verificar se é RestricoesEletricasDECOMPTool
        # Verificar estrutura (presença de campos "GMIN P1", "GMAX P1", etc.)
    
    def get_priority(self) -> int:
        return 85  # Alta prioridade
    
    def format_multi_deck_comparison(
        self,
        decks_data: List[DeckData],
        tool_name: str,
        query: str,
        **kwargs
    ) -> Dict[str, Any]:
        # 1. Extrair dados válidos de todos os decks
        # 2. Construir tabela consolidada (uma linha por deck)
        # 3. Construir gráfico GMIN (3 séries: P1, P2, P3)
        # 4. Construir gráfico GMAX (3 séries: P1, P2, P3)
        # 5. Retornar dict formatado
```

**Lógica**:
1. **Extração de dados**:
   - Para cada deck em `decks_data`:
     - Verificar `deck.has_data` e `deck.result.get("success")`
     - Extrair `data` do resultado
     - Pegar primeiro registro (assumindo que query retorna apenas uma restrição)
     - Normalizar valores NaN/None para 0

2. **Construção da tabela**:
   - Para cada deck válido:
     - Criar linha com: `deck`, `display_name`, `Nome`, `GMIN P1/P2/P3`, `GMAX P1/P2/P3`
     - Usar função `format_compact_label` para labels do gráfico

3. **Construção dos gráficos**:
   - **Gráfico GMIN**:
     - Labels: labels compactas dos decks (ex: "JAN25 - S1")
     - 3 datasets (GMIN P1, GMIN P2, GMIN P3)
     - Cores: azul, verde, amarelo
   - **Gráfico GMAX**:
     - Labels: mesmas labels do GMIN
     - 3 datasets (GMAX P1, GMAX P2, GMAX P3)
     - Cores: vermelho, amarelo, roxo

4. **Retorno**:
```python
{
    "comparison_table": [...],
    "chart_data_gmin": {...},  # Novo campo
    "chart_data_gmax": {...},  # Novo campo
    "visualization_type": "restricoes_eletricas_comparison",
    "chart_config_gmin": {
        "type": "line",
        "title": "Evolução dos Limites Mínimos (GMIN) por Patamar",
        "x_axis": "Deck/Data",
        "y_axis": "GMIN (MW)"
    },
    "chart_config_gmax": {
        "type": "line",
        "title": "Evolução dos Limites Máximos (GMAX) por Patamar",
        "x_axis": "Deck/Data",
        "y_axis": "GMAX (MW)"
    },
    "deck_names": [...],
    "is_multi_deck": True,
    "final_response": "Evolução das restrições elétricas: {NOME} ao longo do tempo.",
    "tool_name": "RestricoesEletricasDECOMPTool"
}
```

### 2. Registro do Formatter

**Arquivo**: `decomp_agent/app/agents/multi_deck/formatting/data_formatters/__init__.py`
- Adicionar import de `RestricoesEletricasComparisonFormatter`

**Arquivo**: `decomp_agent/app/agents/multi_deck/formatting/registry.py`
- Adicionar `RestricoesEletricasComparisonFormatter()` à lista `FORMATTERS`
- Prioridade 85 (alta, similar a LimitesIntercambio)

### 3. Frontend: Componente de Visualização

**Estrutura de pastas**:
```
components/comparison/restricao-eletrica-decomp/
  - RestricoesEletricasComparisonView.tsx  # Componente principal
  - RestricoesEletricasComparisonTable.tsx # Tabela consolidada
  - RestricoesEletricasComparisonChart.tsx # Gráfico reutilizável (GMIN/GMAX)
  - index.ts
```

**Componentes**:

1. **RestricoesEletricasComparisonTable.tsx**:
   - Recebe `comparison_table`
   - Renderiza tabela com colunas: Deck, Nome, GMIN P1/P2/P3, GMAX P1/P2/P3
   - Botão de download CSV
   - Estilo similar a `DPComparisonTable.tsx`

2. **RestricoesEletricasComparisonChart.tsx**:
   - Componente genérico para renderizar gráfico de linha
   - Recebe `chart_data` e `chart_config`
   - Usa Chart.js (similar a outros componentes de comparação)

3. **RestricoesEletricasComparisonView.tsx**:
   - Componente principal
   - Renderiza tabela
   - Renderiza dois gráficos: GMIN e GMAX (um abaixo do outro)
   - Layout: Tabela → Gráfico GMIN → Gráfico GMAX

### 4. Integração no Router

**Arquivo**: `components/comparison/ComparisonRouter.tsx`
- Adicionar caso para `RestricoesEletricasDECOMPTool` ou `RestricoesEletricasMultiDeckTool`
- Verificar `tool_name` e `visualization_type === "restricoes_eletricas_comparison"`
- Renderizar `RestricoesEletricasComparisonView`

### 5. Tipos TypeScript

**Arquivo**: `components/comparison/shared/types.ts`
- Adicionar campos opcionais:
  - `chart_data_gmin?: ChartData | null`
  - `chart_data_gmax?: ChartData | null`
  - `chart_config_gmin?: ChartConfig`
  - `chart_config_gmax?: ChartConfig`

## Considerações

1. **Assunções**:
   - A query sempre retorna apenas UMA restrição elétrica (melhor match)
   - Todos os decks têm a mesma restrição (mesmo nome/código)
   - Se algum deck não tiver a restrição, usar `None/null` no gráfico

2. **Normalização**:
   - Converter NaN/None para 0 em todos os valores numéricos
   - Garantir que nomes de colunas sejam consistentes ("GMIN P1", não "gmin p1")

3. **Tratamento de Erros**:
   - Se nenhum deck tiver dados válidos → mensagem de erro
   - Se apenas alguns decks tiverem dados → mostrar apenas esses
   - Se a restrição não for encontrada em algum deck → None/null na tabela/gráfico

4. **Ordenação**:
   - Decks devem vir ordenados cronologicamente (mais antigo primeiro)
   - Isso já é garantido pelo `decks_data` que vem ordenado

## Checklist de Implementação

- [ ] Criar `RestricoesEletricasComparisonFormatter` (Python)
- [ ] Registrar formatter no `__init__.py` e `registry.py`
- [ ] Criar `RestricoesEletricasComparisonTable.tsx`
- [ ] Criar `RestricoesEletricasComparisonChart.tsx`
- [ ] Criar `RestricoesEletricasComparisonView.tsx`
- [ ] Adicionar tipos TypeScript em `types.ts`
- [ ] Integrar no `ComparisonRouter.tsx`
- [ ] Testar com 2+ decks
- [ ] Verificar download CSV da tabela
- [ ] Verificar renderização dos gráficos
