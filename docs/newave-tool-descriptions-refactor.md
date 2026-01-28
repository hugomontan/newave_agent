# Refatoração das Descrições de Tools NEWAVE para Embedding

Este documento apresenta a comparação **antes/depois** das descrições das tools NEWAVE, otimizadas para **matching por embedding** (não LLM textual).

## Princípios da Otimização

1. **Concisão**: 1-3 frases curtas em vez de parágrafos longos
2. **Unicidade**: Palavras-chave exclusivas que diferenciam da tool vizinha
3. **Fronteiras claras**: Explicitar o que a tool **NÃO** faz
4. **Sem exemplos de query**: O `NEWAVE_QUERY_EXPANSIONS` já cuida de sinônimos
5. **Sem instruções para LLM**: Embedding não interpreta "IMPORTANTE:" ou "SEMPRE deve..."

---

## 1. CargaMensalTool

### Antes
```
Carga mensal por submercado. Demanda mensal por submercado. Consumo mensal de energia por submercado.

Queries que ativam esta tool:
- "me dê as cargas mensais por submercado"
- "me de as cargas mensais por submercado"
- "mostre as cargas mensais por submercado"
- "quais são as cargas mensais por submercado"
- "cargas mensais por submercado"
...
```

### Depois
```
Carga mensal principal por submercado do bloco mercado_energia do SISTEMA.DAT.
Demanda base do sistema elétrico; não inclui C_ADIC nem usinas não simuladas.
```

### Justificativa
| Problema | Solução |
|----------|---------|
| Repetição de sinônimos ("carga", "demanda", "consumo") | Mantém apenas "carga mensal principal" + "demanda base" |
| Lista de queries redundante | Removida (query expansion já cobre) |
| Não diferencia de `CadicTool` e `UsinasNaoSimuladasTool` | Fronteira explícita: "não inclui C_ADIC nem usinas não simuladas" |
| Não menciona arquivo/bloco fonte | Especifica `SISTEMA.DAT` + `mercado_energia` |

---

## 2. CadicTool

### Antes
```
Cargas e ofertas adicionais do arquivo C_ADIC.DAT. Valores extras somados ou subtraídos da demanda principal do sistema.

IMPORTANTE: NÃO confundir com carga mensal principal (demanda base do sistema do SISTEMA.DAT).

Cargas adicionais são valores POSITIVOS que AUMENTAM a demanda (somadas ao mercado).
Ofertas adicionais são valores NEGATIVOS que REDUZEM a demanda (abatidas do mercado).

Queries específicas:
- "cargas adicionais por submercado"
- "ofertas adicionais do subsistema"
- "carga adicional do Sudeste"
```

### Depois
```
Cargas adicionais e ofertas adicionais do C_ADIC.DAT.
Ajustes incrementais à demanda (positivos = carga, negativos = oferta); não é a carga mensal principal.
```

### Justificativa
| Problema | Solução |
|----------|---------|
| "IMPORTANTE:" é instrução de LLM, não semântica | Removido |
| Explicação longa de positivo/negativo | Condensado em parênteses |
| Lista de queries | Removida |
| Boa fronteira com carga mensal | Mantida de forma curta |

---

## 3. UsinasNaoSimuladasTool

### Antes
```
Geração de usinas não simuladas. Dados de geração de pequenas usinas não simuladas por fonte e período do arquivo SISTEMA.DAT.

Queries que ativam esta tool:
- "usinas não simuladas"
- "geração de usinas não simuladas"
- "usinas não simuladas do subsistema 1"
- "geração não simulada do bloco 2"
- "usinas não simuladas da fonte eólica"
...
```

### Depois
```
Geração de usinas não simuladas do bloco geracao_usinas_nao_simuladas do SISTEMA.DAT.
Pequenas centrais (PCH, eólica, solar, biomassa) agregadas por subsistema e fonte; não é carga nem demanda.
```

### Justificativa
| Problema | Solução |
|----------|---------|
| Não especifica bloco do SISTEMA.DAT | Especifica `geracao_usinas_nao_simuladas` |
| Pode confundir com carga (ambas no SISTEMA.DAT) | Fronteira: "não é carga nem demanda" |
| Lista de queries | Removida |
| Fontes não listadas | Adiciona exemplos de fontes (PCH, eólica, solar, biomassa) |

---

## 4. ClastValoresTool

### Antes
```
Custos de classes térmicas. Valores estruturais e conjunturais do CLAST. Custos operacionais das classes térmicas.

IMPORTANTE: Quando a query mencionar CVU (Custo Variável Unitário) ou "custo variável unitário", 
a resposta SEMPRE deve retornar dados de TODOS OS ANOS disponíveis...

Queries que ativam esta tool:
- "CVU da classe térmica 1"
- "custo da classe ANGRA 1"
...
```

### Depois
```
Custos de classes térmicas (CVU) dos blocos usinas e modificacoes do CLAST.DAT.
Valores estruturais e conjunturais de custo variável unitário; não é potência nem geração mínima.
```

### Justificativa
| Problema | Solução |
|----------|---------|
| "IMPORTANTE: SEMPRE deve..." é instrução de comportamento | Removido (lógica fica no código) |
| Não menciona blocos fonte | Especifica `usinas` e `modificacoes` |
| Pode confundir com EXPT (também trata térmicas) | Fronteira: "não é potência nem geração mínima" |

---

## 5. ExptOperacaoTool

### Antes
```
Operação térmica. Expansões térmicas. Modificações temporárias das características operacionais das usinas termoelétricas.

Queries que ativam esta tool:
- "quais são as modificações térmicas do EXPT"
- "modificações térmicas"
- "expansão térmica"
- "expansões térmicas"
- "operação térmica"
...
```

### Depois
```
Modificações temporárias de térmicas do EXPT.DAT (POTEF, GTMIN, FCMAX, IPTER, TEIFT).
Alterações operacionais por período; não é CVU/custo (ver CLAST) nem cadastro fixo (ver TERM).
```

### Justificativa
| Problema | Solução |
|----------|---------|
| "Operação térmica" genérico demais | Especifica códigos: POTEF, GTMIN, FCMAX, IPTER, TEIFT |
| Pode confundir com CLAST (custos) e TERM (cadastro) | Fronteiras explícitas |
| Não menciona que é por período | Adiciona "por período" |

---

## 6. ModifOperacaoTool

### Antes
```
Modificações hídricas. Operação hídrica. Modificações temporárias das características operacionais das usinas hidrelétricas.

Queries que ativam esta tool:
- "quais são as modificações hídricas do MODIF"
- "modificações hídricas"
- "modificação hídrica"
- "operação hídrica"
...
```

### Depois
```
Modificações temporárias de hídricas do MODIF.DAT (VOLMIN, VOLMAX, VAZMIN, VAZMAX, TURBM, NUMMAQ, etc.).
Alterações operacionais por período; não é cadastro fixo (ver HIDR) nem configuração (ver CONFHD).
```

### Justificativa
| Problema | Solução |
|----------|---------|
| "Modificações hídricas" genérico | Especifica códigos: VOLMIN, VOLMAX, VAZMIN, VAZMAX, TURBM, NUMMAQ |
| Pode confundir com HIDR (cadastro) e CONFHD (configuração) | Fronteiras explícitas |
| Não menciona que é por período | Adiciona "por período" |

---

## 7. LimitesIntercambioTool

### Antes
```
Limites de intercâmbio entre subsistemas. Capacidade de interligação entre submercados. Intercâmbio mínimo obrigatório. Limites máximos de intercâmbio.

Queries que ativam esta tool:
- "quais são os limites de intercâmbio entre subsistemas"
- "limites de intercâmbio"
- "limite de intercâmbio entre Sudeste e Sul"
...
```

### Depois
```
Limites de intercâmbio direto entre pares de subsistemas do bloco limites_intercambio do SISTEMA.DAT.
Capacidade máxima e mínima de interligação par-a-par; não é agrupamento combinado (ver AGRINT).
```

### Justificativa
| Problema | Solução |
|----------|---------|
| Repetição de sinônimos | Consolida em "intercâmbio direto" + "par-a-par" |
| Pode confundir com AGRINT (agrupamentos) | Fronteira explícita: "não é agrupamento combinado" |
| Não menciona bloco fonte | Especifica `limites_intercambio` |

---

## 8. AgrintTool

### Antes
```
Agrupamentos de intercâmbio. Restrições lineares de transmissão. Limites combinados de interligações. Corredores de transmissão.

Queries que ativam esta tool:
- "quais são os agrupamentos de intercâmbio"
- "agrupamentos de intercâmbio"
- "agrupamento 1"
...
```

### Depois
```
Agrupamentos de intercâmbio (restrições lineares combinadas) do AGRINT.DAT.
Limites de soma/diferença de múltiplas interligações; não é limite par-a-par simples (ver SISTEMA.DAT limites_intercambio).
```

### Justificativa
| Problema | Solução |
|----------|---------|
| "Corredores de transmissão" pode confundir | Removido, foca em "agrupamentos" |
| Pode confundir com LimitesIntercambioTool | Fronteira: "não é limite par-a-par simples" |
| Não explica o que é agrupamento | Adiciona "soma/diferença de múltiplas interligações" |

---

## 9. VazoesTool

### Antes
```
Vazões históricas de postos fluviométricos. Vazões naturais afluentes. Séries históricas de vazões. Afluências históricas.

Queries que ativam esta tool:
- "vazões históricas do posto 1"
- "vazão histórica de Itaipu"
- "vazões da usina Furnas"
...
```

### Depois
```
Séries históricas de vazões naturais afluentes do VAZOES.DAT.
Vazões mensais de postos fluviométricos; não é vazão mínima operacional (ver MODIF VAZMIN).
```

### Justificativa
| Problema | Solução |
|----------|---------|
| Repetição: "vazões históricas", "séries históricas", "afluências históricas" | Consolida em uma frase |
| Pode confundir com VAZMIN do MODIF | Fronteira explícita |
| Não menciona granularidade | Adiciona "mensais" |

---

## 10. HidrCadastroTool

### Antes
```
Informações cadastrais de usinas hidrelétricas. Dados físicos e operacionais básicos das usinas hidrelétricas do HIDR.DAT.

Queries que ativam esta tool:
- "me de informacoes da usina de balbina"
- "dados da usina de itaipu"
- "informações cadastrais da usina X"
...
```

### Depois
```
Cadastro fixo de usinas hidrelétricas do HIDR.DAT (produtibilidade, volumes, cotas, perdas).
Dados estruturais permanentes; não é configuração variável (ver CONFHD) nem modificação temporária (ver MODIF).
```

### Justificativa
| Problema | Solução |
|----------|---------|
| "Informações cadastrais" genérico | Especifica: produtibilidade, volumes, cotas, perdas |
| Pode confundir com CONFHD e MODIF | Fronteiras explícitas |
| Não diferencia fixo vs variável | Adiciona "estruturais permanentes" |

---

## 11. ConfhdTool

### Antes
```
Configuração de usinas hidrelétricas. Dados de configuração do sistema hidrelétrico do arquivo CONFHD.DAT.

Queries que ativam esta tool:
- "configuração de usinas do confhd"
- "usinas do REE 1"
- "volume inicial da usina X"
- "status da usina Y"
...
```

### Depois
```
Configuração operacional de hídricas do CONFHD.DAT (REE, volume inicial, status, posto).
Atribuições de configuração por usina; não é cadastro físico (ver HIDR) nem modificação temporal (ver MODIF).
```

### Justificativa
| Problema | Solução |
|----------|---------|
| "Configuração" genérico | Especifica: REE, volume inicial, status, posto |
| Pode confundir com HIDR (cadastro) e MODIF | Fronteiras explícitas |
| "Dados de configuração do sistema hidrelétrico" redundante | Removido |

---

## 12. DsvaguaTool

### Antes
```
Desvios de água para usos consuntivos. Dados de desvios de água por usina e estágio do arquivo DSVAGUA.DAT.

Queries que ativam esta tool:
- "desvios de água do dsvagua"
- "desvios de água da usina X"
- "desvios de água da usina Itaipu"
- "desvio de água consuntivo"
- "usos consuntivos de água"
```

### Depois
```
Desvios de água para usos consuntivos do DSVAGUA.DAT.
Vazão desviada por usina hidrelétrica e estágio; não é vazão mínima (MODIF) nem vazão histórica (VAZOES).
```

### Justificativa
| Problema | Solução |
|----------|---------|
| Pode confundir com VAZMIN e VAZOES | Fronteiras explícitas |
| Lista de queries | Removida |
| Boa descrição original | Mantida essência, adicionada diferenciação |

---

## 13. RestricaoEletricaTool

### Antes
```
Restrições elétricas. Dados de restrições elétricas do modelo NEWAVE do arquivo restricao-eletrica.csv.

Queries que ativam esta tool:
- "restrição elétrica"
- "restrições elétricas"
- "fórmula restrição"
- "limite restrição"
- "horizonte restrição"
```

### Depois
```
Restrições elétricas do arquivo restricao-eletrica.csv.
Fórmulas, horizontes e limites de restrições do modelo; não é limite de intercâmbio (ver SISTEMA/AGRINT).
```

### Justificativa
| Problema | Solução |
|----------|---------|
| Pode confundir com limites de intercâmbio | Fronteira explícita |
| Lista de queries | Removida |
| Não especifica conteúdo | Adiciona "fórmulas, horizontes e limites" |

---

## 14. TermCadastroTool

### Antes
```
Cadastro de usinas termoelétricas. Dados estruturais e operacionais básicos das usinas termoelétricas do TERM.DAT.

Queries que ativam esta tool:
- "dados da usina térmica 1"
- "informações cadastrais da usina térmica ANGRA 1"
- "cadastro da usina térmica X"
- "características da usina térmica Y"
- "potência efetiva da usina térmica"
```

### Depois
```
Cadastro fixo de usinas termoelétricas do TERM.DAT (potência nominal, fator capacidade, TEIF, GTMIN base).
Dados estruturais permanentes; não é modificação temporal (ver EXPT) nem custo (ver CLAST).
```

### Justificativa
| Problema | Solução |
|----------|---------|
| "Dados estruturais e operacionais básicos" genérico | Especifica: potência nominal, fator capacidade, TEIF, GTMIN base |
| Pode confundir com EXPT e CLAST | Fronteiras explícitas |
| Lista de queries | Removida |

---

## 15. MultiDeckComparisonTool

### Antes
```
Tool que executa outras tools em dois decks (dezembro e janeiro) 
e compara os resultados lado a lado com gráfico comparativo.
```

### Depois
```
Comparação multi-deck: executa qualquer tool em dois decks (dezembro e janeiro) e compara resultados.
Análise lado-a-lado de diferenças entre versões de deck; não é análise de mudanças específicas (ver MudancasGTMIN, MudancasVAZMIN).
```

### Justificativa
| Problema | Solução |
|----------|---------|
| Descrição curta e boa, mas pode confundir com tools de mudanças | Fronteira: "não é análise de mudanças específicas" |
| "Gráfico comparativo" é detalhe de implementação | Removido |

---

## 16. MudancasGeracoesTermicasTool

### Antes
```
Mudanças em gerações térmicas. Análise de variações de GTMIN (Geração Térmica Mínima) entre decks no modo multideck.

Esta tool é especializada em:
- Identificar todas as mudanças de GTMIN entre dezembro e janeiro
- Ordenar mudanças por magnitude (maior variação primeiro)
- Classificar tipos de mudança (alterado, novo_registro, removido)
- Retornar apenas as mudanças (não todos os registros)
...
```

### Depois
```
Mudanças de GTMIN (geração térmica mínima) entre decks dezembro/janeiro.
Diferenças de GTMIN do EXPT.DAT entre versões; não é comparação genérica (ver MultiDeckComparisonTool).
```

### Justificativa
| Problema | Solução |
|----------|---------|
| Lista de funcionalidades é detalhe de implementação | Removida |
| Pode confundir com MultiDeckComparisonTool | Fronteira explícita |
| Não menciona arquivo fonte | Adiciona EXPT.DAT |

---

## 17. MudancasVazaoMinimaTool

### Antes
```
Mudanças em vazão mínima. Análise de variações de VAZMIN/VAZMINT (Vazão Mínima) entre decks no modo multideck.

IMPORTANTE: Esta tool retorna ambos os tipos de vazão mínima:
- VAZMIN: Vazão mínima sem período (valor fixo que se aplica a todo o horizonte)
- VAZMINT: Vazão mínima com período (valor que se aplica a um período específico)

Quando o usuário consulta "vazão mínima", "mudanças vazão mínima" ou termos similares,
a tool retorna TODAS as mudanças de ambos os tipos (VAZMIN e VAZMINT), diferenciadas
...
```

### Depois
```
Mudanças de VAZMIN e VAZMINT (vazão mínima) entre decks dezembro/janeiro.
Diferenças de vazão mínima do MODIF.DAT entre versões; não é comparação genérica (ver MultiDeckComparisonTool).
```

### Justificativa
| Problema | Solução |
|----------|---------|
| "IMPORTANTE:" é instrução de LLM | Removido |
| Explicação longa de VAZMIN vs VAZMINT | Condensado (ambos mencionados) |
| Pode confundir com MultiDeckComparisonTool | Fronteira explícita |
| Não menciona arquivo fonte | Adiciona MODIF.DAT |

---

## 18. VariacaoReservatorioInicialTool

### Antes
```
Volume inicial percentual (v.inic) por usina do CONFHD.DAT. Reservatório inicial das usinas hidrelétricas.

Queries que ativam esta tool:
- "reservatório inicial por usina"
- "volume inicial por usina"
- "v.inic por usina"
- "reservatório inicial"
- "volume inicial percentual"
```

### Depois
```
Volume inicial percentual (V.INIC) de reservatórios do CONFHD.DAT.
Nível inicial de armazenamento por usina hidrelétrica; não é volume max/min (ver HIDR) nem modificação temporal (ver MODIF).
```

### Justificativa
| Problema | Solução |
|----------|---------|
| Pode confundir com HIDR (volumes estruturais) e MODIF (VOLMIN/VOLMAX temporal) | Fronteiras explícitas |
| Lista de queries | Removida |
| "Reservatório inicial" redundante com "volume inicial" | Consolida |

---

## Resumo das Mudanças

| Padrão Removido | Motivo |
|-----------------|--------|
| Listas de "Queries que ativam esta tool" | `NEWAVE_QUERY_EXPANSIONS` já faz expansão de sinônimos |
| "IMPORTANTE:", "SEMPRE deve...", "NÃO confundir" | São instruções para LLM, não semântica para embedding |
| Repetição de sinônimos na mesma frase | Dilui o vetor de embedding |
| Detalhes de implementação (ordenação, classificação) | Embedding não precisa saber como a tool funciona internamente |

| Padrão Adicionado | Motivo |
|-------------------|--------|
| Arquivo + bloco/objeto fonte | Diferencia tools que usam mesmo arquivo (ex: SISTEMA.DAT) |
| Códigos específicos (GTMIN, POTEF, VAZMIN) | Keywords únicas para matching preciso |
| "não é X (ver TOOL_Y)" | Fronteira clara para embedding não confundir tools similares |
| Granularidade (mensal, por período, permanente) | Diferencia dados temporais de dados fixos |

---

## Próximos Passos

1. **Implementar** as novas descrições nos arquivos `*_tool.py`
2. **Testar** com queries ambíguas para validar diferenciação
3. **Ajustar** `NEWAVE_QUERY_EXPANSIONS` se necessário (remover expansões redundantes)
4. **Medir** taxa de acerto do semantic matching antes/depois
