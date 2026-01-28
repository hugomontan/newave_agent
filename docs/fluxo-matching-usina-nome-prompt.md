# Fluxo: matching de código de usina a partir do nome no prompt

Este documento descreve como o matcher identifica o código da usina quando o usuário escreve o **nome** da usina no prompt, com exemplo real (Serra da Mesa, código 45). Os matchers thermal e hydro seguem a mesma lógica; a diferença está na fonte dos códigos/nomes (deck+CSV vs CSV).

---

## Dados de exemplo (CSV hidro)

| codigo | nome_decomp   | nome_completo  |
|--------|----------------|----------------|
| 45     | SERRA DA MESA  | Serra da Mesa  |

---

## Os três caminhos até o código (por nome)

| Tipo de match     | Exemplo de prompt                              | Como identifica o código 45 |
|-------------------|------------------------------------------------|-----------------------------|
| **Exato**         | `"Serra da Mesa"`                              | query == "serra da mesa" |
| **Todas palavras**| `"Qual a restrição de vazão da Serra da Mesa?"` | "serra", "da", "mesa" presentes na query |
| **Fuzzy**         | `"restrição da Serra Mesa"` ou `"Serra da Messa"` | similaridade com "Serra da Mesa" acima do threshold |

---

## Diagrama Mermaid (fluxo completo)

Para compatibilidade com viewers: evite aspas duplas dentro de labels; use arestas separadas em vez de `P1 & P2 --> X`; use apenas ASCII em labels de aresta (ex.: `->` em vez de `→`, `>=` em vez de `≥`).

```mermaid
flowchart TB
    subgraph prompts[Exemplos de prompt]
        P1[Serra da Mesa]
        P2[Qual a restricao de vazao da Serra da Mesa]
        P3[restricao da Serra Mesa]
        P4[Serra da Messa]
    end

    P1 --> NORMAL
    P2 --> NORMAL
    P3 --> NORMAL
    P4 --> NORMAL

    NORMAL[query.lower + expandir abreviacoes CSV]
    NORMAL --> NUM[Número no texto usina 45 uh 45]
    NUM -->|Nao| NOME[Match por nome CSV cod 45 SERRA DA MESA]
    NOME --> EXATO[EXATO query igual nome]
    NOME --> PALAVRAS[NOME NA QUERY todas palavras serra da mesa]
    NOME --> FUZZY[FUZZY find_usina_match threshold]
    NOME --> FALLBACK[FALLBACK palavras em comum score]

    EXATO -->|SIM| COD45[Codigo 45 Serra da Mesa]
    PALAVRAS -->|SIM| COD45
    FUZZY -->|score >= threshold| COD45
    FALLBACK -->|melhor candidato| COD45

    COD45 --> RET[Retorna 45]
    NUM -->|Sim| RET

    style EXATO fill:#e8f5e9
    style PALAVRAS fill:#e3f2fd
    style FUZZY fill:#fff3e0
    style FALLBACK fill:#fce4ec
    style COD45 fill:#c8e6c9
```

---

## Diagrama Mermaid (versão resumida)

```mermaid
flowchart LR
    subgraph entrada[Prompt]
        A1[Serra da Mesa]
        A2[restricao da Serra da Mesa]
        A3[Serra Mesa ou Serra da Messa]
    end

    A1 --> EXATO[Exato query igual nome]
    A2 --> PALAVRAS[Todas as palavras serra da mesa na query]
    A3 --> FUZZY[Fuzzy similaridade >= threshold]

    EXATO --> C45[Codigo 45]
    PALAVRAS --> C45
    FUZZY --> C45

    C45 --> R[Retorna 45]
```

---

## Referências no código

- **Hydro (hidrelétricas):** `backend/decomp/utils/hydraulic_plant_matcher.py` — `_extract_by_name()` (match exato, word boundary/todas palavras, fuzzy, fallback).
- **Thermal (térmicas):** `backend/decomp/utils/thermal_plant_matcher.py` — `_extract_by_name()` (mesma ideia; fonte deck+CSV).
- **Matcher centralizado (fuzzy):** `backend/core/utils/usina_name_matcher.py` — `find_usina_match()`.
