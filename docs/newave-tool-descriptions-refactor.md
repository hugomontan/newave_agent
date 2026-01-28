# Refatoração das Descrições de Tools NEWAVE para Embedding

Este documento apresenta a comparação **antes/depois** das descrições das tools NEWAVE, otimizadas para **matching por embedding** (não LLM textual).

---

## Configuração de Azure OpenAI para Embeddings

Os embeddings usados pelo RAG e pelo matcher semântico agora são servidos via **Azure OpenAI**, utilizando o modelo configurado em `OPENAI_EMBEDDING_MODEL` (default `text-embedding-3-small`).

### Variáveis de ambiente

Para ambientes como a EC2 (produção/intranet), configure:

- `OPENAI_API_KEY`: chave usada pela aplicação (pode ser a mesma chave do Azure).
- `OPENAI_EMBEDDING_MODEL`: nome do deployment/modelo de embedding (ex.: `text-embedding-3-small`).
- `AZURE_OPENAI_API_KEY`: chave do recurso Azure OpenAI (se não definida, a aplicação usa `OPENAI_API_KEY`).
- `AZURE_OPENAI_ENDPOINT`: endpoint Azure, ex.: `https://it-commodities.openai.azure.com/`.
- `AZURE_OPENAI_API_VERSION`: versão da API, ex.: `2024-02-01` (default se não configurada).

O backend faz a validação dessa configuração na subida da API; se faltar endpoint ou chave, a aplicação falha cedo com mensagem clara, em vez de quebrar apenas na primeira query.

### Exemplo de `.env` (desenvolvimento)

```bash
OPENAI_API_KEY="sua-chave-azure-ou-openai"
OPENAI_EMBEDDING_MODEL="text-embedding-3-small"

AZURE_OPENAI_API_KEY="sua-chave-azure"
AZURE_OPENAI_ENDPOINT="https://it-commodities.openai.azure.com/"
AZURE_OPENAI_API_VERSION="2024-02-01"
```

Em produção (EC2), recomenda-se definir as mesmas variáveis diretamente no ambiente (systemd, docker-compose, etc.), sem depender de `.env` no disco.

## Princípios da Otimização

O match é **semântico (embedding)**: similaridade cosseno entre vetores. Não há interpretação de frases, negações ou referências — só vetores e similaridade.

1. **Apenas keywords positivos**: O que a tool **é** e **faz**. Sem "não é X", "não inclui Y" ou "(ver TOOL_Z)" — o embedding **não interpreta negação**; incluir "C_ADIC" numa descrição **aumenta** a similaridade com queries sobre C_ADIC.
2. **Unicidade**: Palavras-chave exclusivas (arquivo, bloco, códigos como GTMIN, VAZMIN) que diferenciam o vetor da tool vizinha.
3. **Concisão**: Poucas frases ou lista de termos; evitar repetição de sinônimos (dilui o vetor).
4. **Sem exemplos de query**: O `NEWAVE_QUERY_EXPANSIONS` já cuida de sinônimos.
5. **Sem instruções para LLM**: Embedding não interpreta "IMPORTANTE:", "SEMPRE deve..." ou contexto frasal ("Alterações por período; não é custo...").

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
Carga mensal principal submercado mercado_energia SISTEMA.DAT demanda base.
```

### Justificativa
| Problema | Solução |
|----------|---------|
| Repetição de sinônimos ("carga", "demanda", "consumo") | Mantém apenas "carga mensal principal" + "demanda base" |
| Lista de queries redundante | Removida (query expansion já cobre) |
| "não inclui C_ADIC..." | **Removido**: embedding não interpreta negação; incluir "C_ADIC" aumenta similaridade com queries sobre C_ADIC |
| Diferenciação | Keywords únicos: `mercado_energia`, `SISTEMA.DAT` (Cadic usa C_ADIC, UsinasNaoSimuladas usa `geracao_usinas_nao_simuladas`) |

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
Cargas adicionais ofertas adicionais C_ADIC.DAT ajustes incrementais demanda.
```

### Justificativa
| Problema | Solução |
|----------|---------|
| "IMPORTANTE:" é instrução de LLM, não semântica | Removido |
| "não é carga mensal principal" | **Removido**: negação não funciona em embedding |
| Lista de queries | Removida |
| Diferenciação | Keyword único: `C_ADIC.DAT` (CargaMensal usa `mercado_energia` SISTEMA.DAT) |

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
Geração usinas não simuladas geracao_usinas_nao_simuladas SISTEMA.DAT PCH eólica solar biomassa subsistema fonte.
```

### Justificativa
| Problema | Solução |
|----------|---------|
| Não especifica bloco do SISTEMA.DAT | Especifica `geracao_usinas_nao_simuladas` |
| "não é carga nem demanda" | **Removido**: negação não funciona em embedding |
| Lista de queries | Removida |
| Diferenciação | Keywords únicos: `geracao_usinas_nao_simuladas`, PCH, eólica, solar, biomassa (CargaMensal usa `mercado_energia`) |

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
Custos classes térmicas CVU CLAST.DAT usinas modificacoes custo variável unitário.
```

### Justificativa
| Problema | Solução |
|----------|---------|
| "IMPORTANTE: SEMPRE deve..." é instrução de comportamento | Removido (lógica fica no código) |
| Não menciona blocos fonte | Especifica `usinas` e `modificacoes` |
| "não é potência nem geração mínima" | **Removido**: negação não funciona em embedding |
| Diferenciação | Keywords únicos: CVU, CLAST.DAT (EXPT usa POTEF/GTMIN, TERM usa cadastro) |

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
Modificações temporárias térmicas EXPT.DAT POTEF GTMIN FCMAX IPTER TEIFT período.
```

### Justificativa
| Problema | Solução |
|----------|---------|
| "Operação térmica" genérico demais | Especifica códigos: POTEF, GTMIN, FCMAX, IPTER, TEIFT |
| "não é CVU (ver CLAST) nem cadastro (ver TERM)" | **Removido**: embedding não interpreta negação nem "ver X"; incluir CVU/CLAST/TERM **aumentaria** similaridade com queries erradas |
| Diferenciação | Keywords únicos: EXPT.DAT, POTEF, GTMIN, FCMAX, IPTER, TEIFT (CLAST = CVU, TERM = cadastro) |

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
Modificações temporárias hídricas MODIF.DAT VOLMIN VOLMAX VAZMIN VAZMAX TURBM NUMMAQ período.
```

### Justificativa
| Problema | Solução |
|----------|---------|
| "Modificações hídricas" genérico | Especifica códigos: VOLMIN, VOLMAX, VAZMIN, VAZMAX, TURBM, NUMMAQ |
| "não é cadastro (ver HIDR) nem configuração (ver CONFHD)" | **Removido**: embedding não interpreta; incluir HIDR/CONFHD aumentaria similaridade com queries erradas |
| Diferenciação | Keywords únicos: MODIF.DAT, VOLMIN, VOLMAX, VAZMIN, etc. (HIDR = cadastro, CONFHD = configuração) |

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
Limites intercâmbio subsistemas limites_intercambio SISTEMA.DAT par-a-par interligação capacidade.
```

### Justificativa
| Problema | Solução |
|----------|---------|
| Repetição de sinônimos | Consolida em "intercâmbio", "par-a-par", "interligação" |
| "não é agrupamento (ver AGRINT)" | **Removido**: negação e "ver X" não funcionam em embedding |
| Diferenciação | Keywords únicos: `limites_intercambio`, SISTEMA.DAT, par-a-par (AGRINT usa AGRINT.DAT, agrupamentos) |

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
Agrupamentos intercâmbio AGRINT.DAT restrições lineares combinadas soma diferença múltiplas interligações.
```

### Justificativa
| Problema | Solução |
|----------|---------|
| "Corredores de transmissão" pode confundir | Removido, foca em "agrupamentos" |
| "não é limite par-a-par (ver SISTEMA...)" | **Removido**: negação e "ver X" não funcionam em embedding |
| Diferenciação | Keywords únicos: AGRINT.DAT, agrupamentos, soma/diferença (LimitesIntercambio usa limites_intercambio, par-a-par) |

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
Vazões históricas postos fluviométricos VAZOES.DAT séries naturais afluentes mensais.
```

### Justificativa
| Problema | Solução |
|----------|---------|
| Repetição: "vazões históricas", "séries históricas", "afluências históricas" | Consolida em termos únicos |
| "não é vazão mínima (ver MODIF)" | **Removido**: negação não funciona em embedding |
| Diferenciação | Keywords únicos: VAZOES.DAT, históricas, postos fluviométricos, afluentes (MODIF = VAZMIN temporal) |

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
Cadastro usinas hidrelétricas HIDR.DAT produtibilidade volumes cotas perdas.
```

### Justificativa
| Problema | Solução |
|----------|---------|
| "Informações cadastrais" genérico | Especifica: produtibilidade, volumes, cotas, perdas |
| "não é configuração (ver CONFHD) nem modificação (ver MODIF)" | **Removido**: negação e "ver X" não funcionam em embedding |
| Diferenciação | Keywords únicos: HIDR.DAT, cadastro, produtibilidade (CONFHD = configuração/REE, MODIF = modificações temporárias) |

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
Configuração usinas hidrelétricas CONFHD.DAT REE volume inicial status posto.
```

### Justificativa
| Problema | Solução |
|----------|---------|
| "Configuração" genérico | Especifica: REE, volume inicial, status, posto |
| "não é cadastro (ver HIDR) nem modificação (ver MODIF)" | **Removido**: negação e "ver X" não funcionam em embedding |
| Diferenciação | Keywords únicos: CONFHD.DAT, configuração, REE, volume inicial (HIDR = cadastro, MODIF = modificações) |

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
Desvios água usos consuntivos DSVAGUA.DAT usina estágio.
```

### Justificativa
| Problema | Solução |
|----------|---------|
| "não é vazão mínima (MODIF) nem vazão histórica (VAZOES)" | **Removido**: negação não funciona em embedding; citar MODIF/VAZOES aumentaria similaridade errada |
| Lista de queries | Removida |
| Diferenciação | Keywords únicos: DSVAGUA.DAT, desvios, usos consuntivos, estágio (VAZOES = históricas, MODIF = VAZMIN) |

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
Restrições elétricas restricao-eletrica.csv fórmulas horizontes limites modelo NEWAVE.
```

### Justificativa
| Problema | Solução |
|----------|---------|
| "não é limite de intercâmbio (ver SISTEMA/AGRINT)" | **Removido**: negação e "ver X" não funcionam em embedding |
| Lista de queries | Removida |
| Diferenciação | Keywords únicos: restricao-eletrica.csv, fórmulas, horizontes, restrições (intercâmbio = SISTEMA/AGRINT) |

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
Cadastro usinas termoelétricas TERM.DAT potência nominal fator capacidade TEIF GTMIN.
```

### Justificativa
| Problema | Solução |
|----------|---------|
| "Dados estruturais e operacionais básicos" genérico | Especifica: potência nominal, fator capacidade, TEIF, GTMIN |
| "não é modificação (ver EXPT) nem custo (ver CLAST)" | **Removido**: negação e "ver X" não funcionam em embedding |
| Diferenciação | Keywords únicos: TERM.DAT, cadastro, potência nominal, TEIF (EXPT = modificações, CLAST = CVU) |

---

## 15. MultiDeckComparisonTool

### Antes
```
Tool que executa outras tools em dois decks (dezembro e janeiro) 
e compara os resultados lado a lado com gráfico comparativo.
```

### Depois
```
Comparação multi-deck dois decks dezembro janeiro compara resultados lado a lado.
```

### Justificativa
| Problema | Solução |
|----------|---------|
| "não é análise de mudanças específicas (ver MudancasGTMIN...)" | **Removido**: negação e "ver X" não funcionam em embedding; citar MudancasGTMIN/VAZMIN aumentaria similaridade errada |
| "Gráfico comparativo" é detalhe de implementação | Removido |
| Diferenciação | Keywords únicos: comparação multi-deck, dois decks, lado a lado (MudancasGTMIN/VAZMIN = mudanças GTMIN/VAZMIN entre decks) |

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
Mudanças GTMIN geração térmica mínima decks dezembro janeiro EXPT.DAT.
```

### Justificativa
| Problema | Solução |
|----------|---------|
| Lista de funcionalidades é detalhe de implementação | Removida |
| "não é comparação genérica (ver MultiDeckComparisonTool)" | **Removido**: negação e "ver X" não funcionam em embedding |
| Diferenciação | Keywords únicos: GTMIN, EXPT.DAT, geração térmica mínima (MultiDeck = comparação genérica, MudancasVAZMIN = VAZMIN) |

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
Mudanças VAZMIN VAZMINT vazão mínima decks dezembro janeiro MODIF.DAT.
```

### Justificativa
| Problema | Solução |
|----------|---------|
| "IMPORTANTE:" é instrução de LLM | Removido |
| Explicação longa de VAZMIN vs VAZMINT | Condensado (ambos mencionados como keywords) |
| "não é comparação genérica (ver MultiDeck...)" | **Removido**: negação e "ver X" não funcionam em embedding |
| Diferenciação | Keywords únicos: VAZMIN, VAZMINT, MODIF.DAT, vazão mínima (MultiDeck = comparação genérica, MudancasGTMIN = GTMIN) |

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
Volume inicial percentual V.INIC reservatórios CONFHD.DAT usina hidrelétrica.
```

### Justificativa
| Problema | Solução |
|----------|---------|
| "não é volume max/min (ver HIDR) nem modificação (ver MODIF)" | **Removido**: negação e "ver X" não funcionam em embedding |
| Lista de queries | Removida |
| Diferenciação | Keywords únicos: V.INIC, volume inicial percentual, CONFHD.DAT (HIDR = cadastro, MODIF = VOLMIN/VOLMAX temporal) |

---

## Resumo das Mudanças

| Padrão Removido | Motivo |
|-----------------|--------|
| Listas de "Queries que ativam esta tool" | `NEWAVE_QUERY_EXPANSIONS` já faz expansão de sinônimos |
| "IMPORTANTE:", "SEMPRE deve...", "NÃO confundir" | São instruções para LLM, não semântica para embedding |
| **"não é X", "não inclui Y", "(ver TOOL_Z)"** | **Embedding não interpreta negação nem referências**; incluir "C_ADIC" numa descrição **aumenta** a similaridade com queries sobre C_ADIC — efeito oposto ao desejado |
| Repetição de sinônimos na mesma frase | Dilui o vetor de embedding |
| Detalhes de implementação (ordenação, classificação) | Embedding não precisa saber como a tool funciona internamente |
| Frases contextuais ("Alterações por período; não é custo...") | Match é só similaridade cosseno entre vetores; não há interpretação de frases |

| Padrão Adicionado | Motivo |
|-------------------|--------|
| **Apenas keywords positivos** | O que a tool **é** e **faz**; maximiza distância entre vetores de tools diferentes |
| Arquivo + bloco/objeto fonte | Diferencia tools que usam mesmo arquivo (ex: SISTEMA.DAT → `mercado_energia` vs `geracao_usinas_nao_simuladas`) |
| Códigos específicos (GTMIN, POTEF, VAZMIN, VOLMIN, etc.) | Keywords únicas para matching preciso; diferenciam EXPT vs CLAST vs TERM, MODIF vs HIDR vs CONFHD |
| Granularidade (mensal, período) quando relevante | Diferencia dados temporais de dados fixos |

---

## Próximos Passos

1. **Implementar** as novas descrições nos arquivos `*_tool.py`
2. **Testar** com queries ambíguas para validar diferenciação
3. **Ajustar** `NEWAVE_QUERY_EXPANSIONS` se necessário (remover expansões redundantes)
4. **Medir** taxa de acerto do semantic matching antes/depois
