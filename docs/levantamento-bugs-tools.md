# Levantamento de Bugs Potenciais - Tools NEWAVE e DECOMP

Este documento lista os possíveis bugs identificados para cada tool, organizados por modelo e modo de operação.

## Estrutura

- **NEWAVE**
  - Single Deck (14 tools)
  - Comparison/Multi-Deck (4 tools)
- **DECOMP**
  - Single Deck (12 tools)
  - Multi-Deck (11 tools)

---

## NEWAVE - Single Deck

### 1. CargaMensalTool

**Tipos de Prompts:**
- Genérico: "carga mensal", "demanda mensal", "mercado energia"
- Por submercado: "carga do Sudeste", "demanda do Sul", "carga subsistema 1"
- Agrupado: "cargas mensais por submercado", "todos os submercados separadamente"

**Bugs Potenciais:**
1. **Extração de submercado ambígua**: Query "carga do norte" pode confundir "Norte" (subsistema) com "norte" (direção)
2. **Normalização de nomes**: "SE" vs "Sudeste" - pode não encontrar se normalização falhar
3. **Códigos numéricos inválidos**: Query "subsistema 99" quando só existem 4 subsistemas - não valida antes de filtrar
4. **DataFrame vazio após filtro**: Se filtro por submercado inexistente, retorna erro genérico
5. **Conversão de data**: Se coluna 'data' não for datetime, pode falhar silenciosamente
6. **Agrupamento por submercado**: Se query pede "separadamente" mas não há múltiplos submercados, pode retornar estrutura incorreta
7. **Redundância de dados**: Se todos os valores são iguais, pode retornar estrutura redundante
8. **Anos ausentes**: Se não há coluna 'ano', pode quebrar na agregação

---

### 2. LimitesIntercambioTool

**Tipos de Prompts:**
- Genérico: "limites de intercâmbio", "capacidade de intercâmbio"
- Por par: "limite entre Sudeste e Sul", "intercâmbio de 1 para 2"
- Por sentido: "intercâmbio mínimo", "limite máximo"

**Bugs Potenciais:**
1. **Extração de par falha**: Query "limite entre X e Y" pode extrair par invertido incorretamente
2. **Normalização de submercados**: "SE" vs "Sudeste" - matching pode falhar
3. **Padrão "entre X e Y"**: Regex pode capturar "entre" em contexto errado
4. **Códigos numéricos**: "subsistema 1 para 2" - validação pode falhar se códigos não existem
5. **Sentido não detectado**: Query não especifica "mínimo" ou "máximo" - pode retornar ambos sem filtro
6. **DataFrame vazio**: Se filtros não encontram nada, retorna erro genérico sem sugerir alternativas
7. **Mapeamento de nomes**: Se sistema.custo_deficit não tem nomes, mapeamento falha silenciosamente
8. **Conversão de data**: Similar ao CargaMensalTool

---

### 3. ClastValoresTool

**Tipos de Prompts:**
- Genérico: "valores CLAS-T", "custos estruturais", "custos conjunturais"
- Por ano: "CLAS-T do ano 1", "custos do ano de estudo 2"

**Bugs Potenciais:**
1. **Estrutura de dados**: Retorna `dados_estruturais` e `dados_conjunturais` separados - formatters podem não saber qual usar
2. **Índice de ano**: Se query pede "ano 1" mas dados usam `indice_ano_estudo`, matching pode falhar
3. **Campos ausentes**: Se arquivo não tem custos estruturais ou conjunturais, retorna estrutura parcial
4. **Agregação**: Se não há dados para algum ano, pode quebrar agregação

---

### 4. ExptOperacaoTool

**Tipos de Prompts:**
- Genérico: "expectativas de operação", "expansões", "expt"
- Por tipo: "expansões hidrelétricas", "expansões termelétricas"

**Bugs Potenciais:**
1. **Estrutura de dados**: Retorna `dados_expansoes` - formatters precisam saber este campo
2. **Filtro por tipo**: Se query pede "hidrelétricas" mas não há filtro implementado, retorna tudo
3. **Datas**: Se expansões não têm datas, agrupamento temporal pode falhar

---

### 5. ModifOperacaoTool

**Tipos de Prompts:**
- Genérico: "modificações de operação", "modif", "mudanças operacionais"
- Por tipo: "modificações estruturais", "modificações conjunturais"

**Bugs Potenciais:**
1. **Estrutura de dados**: Retorna `dados_por_tipo` (dict de listas) - formatters precisam lidar com estrutura aninhada
2. **Tipos desconhecidos**: Se arquivo tem tipo não mapeado, pode ser ignorado silenciosamente
3. **Agregação**: Se algum tipo está vazio, dict pode ter chaves com listas vazias

---

### 6. AgrintTool

**Tipos de Prompts:**
- Genérico: "agrupamentos de intercâmbio", "agrint", "grupos de intercâmbio"

**Bugs Potenciais:**
1. **Estrutura de dados**: Pode retornar estrutura específica que formatters não conhecem
2. **Agrupamentos vazios**: Se não há agrupamentos, pode retornar estrutura vazia sem aviso

---

### 7. VazoesTool

**Tipos de Prompts:**
- Genérico: "vazões", "vazões naturais", "afluências"
- Por usina: "vazões da usina X", "afluências de Y"

**Bugs Potenciais:**
1. **Extração de usina**: Similar a HidrCadastroTool - matching de nome pode falhar
2. **Período**: Se query pede período específico mas dados não têm data, pode retornar tudo
3. **Formato de dados**: Vazões podem ter estrutura temporal complexa

---

### 8. CadicTool

**Tipos de Prompts:**
- Genérico: "cadastro adicional", "cadic", "dados adicionais"

**Bugs Potenciais:**
1. **Estrutura variável**: Dados adicionais podem ter estrutura muito variável
2. **Campos opcionais**: Muitos campos podem ser opcionais, estrutura pode ser inconsistente

---

### 9. HidrCadastroTool

**Tipos de Prompts:**
- Genérico: "cadastro hidrelétrico", "informações da usina", "dados da usina X"
- Por campo: "volume mínimo da usina Y", "potência nominal de Z"

**Bugs Potenciais:**
1. **Matching de nome**: SequenceMatcher pode dar falso positivo - "Angra" pode matchar "Angra 1" e "Angra 2"
2. **Código vs Nome**: Query "usina 1" pode ser código ou nome - ambiguidade
3. **Campos ausentes**: Se usina não tem determinado campo, pode retornar None sem aviso
4. **Índice vs Código**: Código da usina (1-based) vs índice do DataFrame podem não coincidir
5. **Múltiplas correspondências**: Se nome matcha múltiplas usinas, pode retornar apenas a primeira
6. **Case sensitivity**: "ANGRA" vs "Angra" - normalização pode falhar
7. **Acentos**: "Itaipu" vs "Itaipú" - normalização pode não lidar

---

### 10. ConfhdTool

**Tipos de Prompts:**
- Genérico: "configuração hidrelétrica", "confhd", "configurações das usinas"

**Bugs Potenciais:**
1. **Estrutura de dados**: Retorna `dados` - formatters precisam conhecer estrutura
2. **Múltiplas configurações**: Se usina tem múltiplas configurações, pode retornar apenas uma

---

### 11. DsvaguaTool

**Tipos de Prompts:**
- Genérico: "desvios de água", "dsvagua", "desvios"

**Bugs Potenciais:**
1. **Estrutura de dados**: Similar a outras tools - estrutura específica
2. **Período**: Desvios podem ser por período específico

---

### 12. UsinasNaoSimuladasTool

**Tipos de Prompts:**
- Genérico: "usinas não simuladas", "usinas excluídas"

**Bugs Potenciais:**
1. **Lista vazia**: Se não há usinas não simuladas, pode retornar lista vazia sem contexto
2. **Razão da exclusão**: Se query pede "por que não simulada", pode não ter informação

---

### 13. RestricaoEletricaTool

**Tipos de Prompts:**
- Genérico: "restrições elétricas", "restrições do sistema"
- Por tipo: "restrições de transmissão", "restrições de geração"

**Bugs Potenciais:**
1. **Estrutura complexa**: Restrições podem ter estrutura muito complexa
2. **Múltiplos tipos**: Se não filtra por tipo, pode retornar tudo misturado

---

### 14. TermCadastroTool

**Tipos de Prompts:**
- Genérico: "cadastro termelétrico", "usinas térmicas", "dados das térmicas"
- Por usina: "cadastro da usina X", "dados da térmica Y"

**Bugs Potenciais:**
1. **Matching de nome**: Similar a HidrCadastroTool - problemas de matching
2. **Múltiplas correspondências**: Nome pode matchar múltiplas usinas

---

## NEWAVE - Comparison/Multi-Deck

### 15. VariacaoReservatorioInicialTool

**Tipos de Prompts:**
- Genérico: "variação de reservatório inicial", "volume inicial", "reservatório inicial"
- Por usina: "volume inicial da usina X"

**Bugs Potenciais:**
1. **Estrutura de dados**: Retorna `dados_volume_inicial` - formatters precisam conhecer
2. **Matching de usina**: Similar a HidrCadastroTool
3. **Comparação multi-deck**: Se tool é usada em modo comparison, pode não funcionar corretamente

---

### 16. MudancasGeracoesTermicasTool

**Tipos de Prompts:**
- Genérico: "mudanças de gerações térmicas", "GTMIN", "gerações mínimas"
- Por usina: "GTMIN da usina X"

**Bugs Potenciais:**
1. **Estrutura de dados**: Retorna `comparison_table` - estrutura específica para comparação
2. **Modo single vs comparison**: Se usada em modo single, pode retornar estrutura incorreta
3. **Matching de usina**: Similar a outras tools

---

### 17. MudancasVazaoMinimaTool

**Tipos de Prompts:**
- Genérico: "mudanças de vazão mínima", "VAZMIN", "vazão mínima"
- Por usina: "vazão mínima da usina X"

**Bugs Potenciais:**
1. **Similar a MudancasGeracoesTermicasTool**
2. **Estrutura de dados**: Pode retornar estrutura específica

---

### 18. MultiDeckComparisonTool

**Tipos de Prompts:**
- Genérico: "comparar decks", "diferenças entre decks", "comparação"
- Com tool específica: Qualquer query que ative outra tool em modo comparison

**Bugs Potenciais:**
1. **Semantic matching falha**: Se `find_best_tool_semantic` retorna None, tool falha sem fallback
2. **Score baixo**: Se score < 0.4, rejeita mas pode ser falso negativo
3. **Execução paralela**: Se um deck falha, outros podem continuar mas resultado fica inconsistente
4. **Extração de dados**: `_extract_data_from_result` pode não encontrar dados se tool retorna campo não mapeado
5. **Estrutura de dados variável**: Cada tool retorna estrutura diferente - pode não conseguir agregar
6. **Timeout**: Se execução paralela demora muito, pode timeout sem aviso
7. **Compatibilidade de formatos**: Diferentes tools podem retornar formatos incompatíveis para comparação
8. **Períodos diferentes**: Se decks têm períodos diferentes, comparação pode falhar
9. **Índice por período**: `_index_by_period` pode não funcionar se estrutura de dados é diferente
10. **Formatação de período**: `_format_period_label` pode falhar para formatos não esperados

---

## DECOMP - Single Deck

### 19. UHUsinasHidrelétricasTool

**Tipos de Prompts:**
- Genérico: "usinas hidrelétricas", "UH", "hidrelétricas do DECOMP"
- Por usina: "usina hidrelétrica X", "UH Y"

**Bugs Potenciais:**
1. **Matching de nome**: Similar a HidrCadastroTool
2. **Estágio**: Tool pode ser específica para estágio 1, mas query pode pedir outro estágio
3. **Estrutura de dados**: Dados do DECOMP podem ter estrutura diferente do NEWAVE

---

### 20. CTUsinasTermelétricasTool

**Tipos de Prompts:**
- Genérico: "usinas termelétricas", "CT", "térmicas do DECOMP"
- Por usina: "usina termelétrica X", "CT Y"

**Bugs Potenciais:**
1. **Similar a UHUsinasHidrelétricasTool**
2. **Matching de nome**: Problemas de matching similares

---

### 21. DPCargaSubsistemasTool

**Tipos de Prompts:**
- Genérico: "carga de subsistemas", "DP", "demanda dos subsistemas"
- Por subsistema: "carga do subsistema X"

**Bugs Potenciais:**
1. **Similar a CargaMensalTool do NEWAVE**
2. **Estrutura temporal**: DECOMP usa semanas, não meses - formatação pode ser diferente
3. **Patamares**: DECOMP tem patamares (P1, P2, P3) - agregação pode ser complexa

---

### 22. InflexibilidadeUsinaTool

**Tipos de Prompts:**
- Genérico: "inflexibilidade", "inflexibilidade de usina"
- Por usina: "inflexibilidade da usina X", "inflexibilidade de Y"

**Bugs Potenciais:**
1. **Herda de PatamarCalculationBase**: Bugs podem estar na classe base
2. **Cálculo ponderado**: Se durações dos patamares não estão disponíveis, cálculo falha
3. **Extração de inflexibilidades**: Se campos não seguem padrão esperado, extração falha
4. **Matching de usina**: Similar a outras tools
5. **Estágio**: Pode ser específico para estágio 1

---

### 23. DisponibilidadeUsinaTool

**Tipos de Prompts:**
- Genérico: "disponibilidade", "disponibilidade de usina"
- Por usina: "disponibilidade da usina X", "disponibilidade de Y"

**Bugs Potenciais:**
1. **Similar a InflexibilidadeUsinaTool**
2. **Herda de PatamarCalculationBase**: Mesmos problemas potenciais
3. **Extração de disponibilidades**: Se campos não seguem padrão, extração falha
4. **Cálculo ponderado**: Depende de durações dos patamares

---

### 24. PQPequenasUsinasTool

**Tipos de Prompts:**
- Genérico: "pequenas usinas", "PQ", "gerações de pequenas usinas"
- Por tipo: "PCH", "PCT", "EOL", "UFV"
- Por região: "pequenas usinas do Sudeste", "PQ do Nordeste"

**Bugs Potenciais:**
1. **Mapeamento de região**: `SUBMERCADO_TO_REGIAO` pode não cobrir todos os casos
2. **Prefixos de região**: `REGIAO_TO_PREFIXOS` pode não ter todos os prefixos possíveis
3. **Tipos de geração**: Se arquivo tem tipo não mapeado em `TIPOS_GERACAO`, é ignorado
4. **Matching de nome**: Nomes podem não seguir padrão esperado (ex: "SECO_PCH" vs "SECO_PCHgd")
5. **Cálculo ponderado**: Similar a outras tools - depende de durações
6. **Estágio**: Pode ser específico para estágio 1

---

### 25. CargaAndeTool

**Tipos de Prompts:**
- Genérico: "carga ANDE", "demanda ANDE", "ANDE"

**Bugs Potenciais:**
1. **Estrutura específica**: Dados da ANDE podem ter estrutura específica
2. **Período**: Pode ser específico para estágio 1

---

### 26. LimitesIntercambioDECOMPTool

**Tipos de Prompts:**
- Genérico: "limites de intercâmbio", "registro IA", "intercâmbio DECOMP"
- Por par: "limite de N para FC", "intercâmbio entre S e SE"

**Bugs Potenciais:**
1. **Similar a LimitesIntercambioTool do NEWAVE**
2. **Extração de par**: `_extrair_par_simples` pode falhar para formatos não esperados
3. **Par invertido**: Se par não existe, tenta invertido mas pode não ser o que usuário quer
4. **Sugestões**: `_sugerir_pares_similares` pode não sugerir corretamente
5. **Estágio**: Pode ser específico para estágio 1
6. **Extração de limites**: `_extrair_limites_do_registro` pode falhar se estrutura do objeto é diferente
7. **Cálculo MW médio**: Se durações não estão disponíveis, cálculo falha
8. **Listar todos os pares**: Se query não especifica par, retorna todos - pode ser muito dados

---

### 27. RestricoesEletricasDECOMPTool

**Tipos de Prompts:**
- Genérico: "restrições elétricas", "restrições DECOMP"

**Bugs Potenciais:**
1. **Estrutura complexa**: Restrições podem ter estrutura muito complexa
2. **Múltiplos tipos**: Pode haver diferentes tipos de restrições

---

### 28. RestricoesVazaoHQTool

**Tipos de Prompts:**
- Genérico: "restrições de vazão HQ", "vazão HQ", "restrições HQ"

**Bugs Potenciais:**
1. **Estrutura específica**: Restrições HQ podem ter estrutura específica
2. **Matching de usina**: Se restrição é por usina, matching pode falhar

---

### 29. RestricoesVazaoHQConjuntaTool

**Tipos de Prompts:**
- Genérico: "restrições de vazão HQ conjunta", "vazão HQ conjunta"

**Bugs Potenciais:**
1. **Similar a RestricoesVazaoHQTool**
2. **Restrições conjuntas**: Estrutura pode ser mais complexa

---

### 30. GLGeracoesGNLTool

**Tipos de Prompts:**
- Genérico: "gerações GNL", "GL", "GNL"

**Bugs Potenciais:**
1. **Estrutura específica**: Dados GNL podem ter estrutura específica
2. **Período**: Pode ser específico para estágio 1

---

## DECOMP - Multi-Deck

### 31-41. Tools Multi-Deck DECOMP

**Tools:**
- DisponibilidadeMultiDeckTool
- DPMultiDeckTool
- VolumeInicialMultiDeckTool
- RestricoesVazaoHQMultiDeckTool
- RestricoesEletricasMultiDeckTool
- PQMultiDeckTool
- LimitesIntercambioMultiDeckTool
- InflexibilidadeMultiDeckTool
- GLMultiDeckTool
- CVUMultiDeckTool
- CargaAndeMultiDeckTool

**Tipos de Prompts:**
- Similar às tools single deck correspondentes, mas em contexto de comparação

**Bugs Potenciais (comuns a todas):**
1. **Execução paralela**: Similar a MultiDeckComparisonTool do NEWAVE
2. **Carregamento de decks**: Se `deck_paths` está vazio, tool falha
3. **Parsing de nome do deck**: `parse_deck_name` pode falhar para formatos não esperados
4. **Cálculo de data**: `calculate_week_thursday` pode falhar se nome do deck não tem data
5. **Agregação de resultados**: Diferentes decks podem ter estruturas ligeiramente diferentes
6. **Timeout**: Execução paralela pode timeout
7. **Workers**: `max_workers` pode ser muito alto ou muito baixo dependendo do sistema
8. **Cache de dadger**: Se cache está desatualizado, pode usar dados incorretos
9. **Compatibilidade de formatos**: Diferentes versões de decks podem ter formatos diferentes
10. **Ordenação temporal**: Se decks não estão ordenados corretamente, comparação pode ser incorreta

**Bugs Específicos por Tool:**

**DisponibilidadeMultiDeckTool:**
- Herda problemas de DisponibilidadeUsinaTool
- Agregação de resultados pode falhar se estruturas são diferentes

**DPMultiDeckTool:**
- Herda problemas de DPCargaSubsistemasTool
- Agregação por patamar pode ser complexa

**VolumeInicialMultiDeckTool:**
- Similar a VariacaoReservatorioInicialTool
- Matching de usina pode falhar

**RestricoesVazaoHQMultiDeckTool:**
- Herda problemas de RestricoesVazaoHQTool
- Restrições podem não existir em todos os decks

**RestricoesEletricasMultiDeckTool:**
- Herda problemas de RestricoesEletricasDECOMPTool
- Estrutura pode variar entre decks

**PQMultiDeckTool:**
- Herda problemas de PQPequenasUsinasTool
- Agregação por tipo/região pode falhar

**LimitesIntercambioMultiDeckTool:**
- Herda problemas de LimitesIntercambioDECOMPTool
- Pares podem não existir em todos os decks

**InflexibilidadeMultiDeckTool:**
- Herda problemas de InflexibilidadeUsinaTool
- Cálculo paralelo pode ter race conditions

**GLMultiDeckTool:**
- Herda problemas de GLGeracoesGNLTool
- Dados podem não existir em todos os decks

**CVUMultiDeckTool:**
- Estrutura específica de CVU
- Cálculo pode ser complexo

**CargaAndeMultiDeckTool:**
- Herda problemas de CargaAndeTool
- Dados ANDE podem não existir em todos os decks

---

## Bugs Comuns a Todas as Tools

### 1. Arquivo não encontrado
- **Cenário**: Arquivo esperado não existe no deck
- **Impacto**: Tool retorna erro genérico
- **Melhoria**: Sugerir arquivos similares ou listar arquivos disponíveis

### 2. Arquivo vazio ou corrompido
- **Cenário**: Arquivo existe mas está vazio ou corrompido
- **Impacto**: Tool pode falhar silenciosamente ou retornar dados vazios
- **Melhoria**: Validar arquivo antes de processar

### 3. Estrutura de dados inesperada
- **Cenário**: Arquivo tem estrutura diferente do esperado
- **Impacto**: Tool pode falhar ao acessar campos
- **Melhoria**: Validar estrutura antes de processar

### 4. Matching de entidades (usinas, submercados, etc)
- **Cenário**: Nome ou código não encontrado
- **Impacto**: Retorna erro sem sugerir alternativas
- **Melhoria**: Sugerir entidades similares usando fuzzy matching

### 5. Normalização de texto
- **Cenário**: Query tem variações (maiúsculas, acentos, abreviações)
- **Impacto**: Matching pode falhar
- **Melhoria**: Normalização mais robusta

### 6. Campos opcionais ausentes
- **Cenário**: Campo esperado não existe no arquivo
- **Impacto**: Tool pode falhar ou retornar None sem contexto
- **Melhoria**: Validar campos opcionais e avisar quando ausentes

### 7. Conversão de tipos
- **Cenário**: Dados não estão no tipo esperado (ex: string vs int)
- **Impacto**: Operações podem falhar
- **Melhoria**: Conversão robusta com tratamento de erros

### 8. Agregação de dados
- **Cenário**: Dados não podem ser agregados (tipos incompatíveis, valores None)
- **Impacto**: Agregação falha ou retorna valores incorretos
- **Melhoria**: Validar dados antes de agregar

### 9. Formatação de período/tempo
- **Cenário**: Período não pode ser formatado (formato inesperado)
- **Impacto**: Exibição pode falhar
- **Melhoria**: Suportar múltiplos formatos de período

### 10. Retorno de estrutura de dados
- **Cenário**: Tool retorna estrutura que formatters não conhecem
- **Impacto**: Frontend não consegue exibir dados
- **Melhoria**: Padronizar estruturas de retorno ou documentar todas as possíveis

---

## Priorização de Bugs

### Alta Prioridade
1. Arquivo não encontrado sem sugestões
2. Matching de entidades falha sem alternativas
3. Estrutura de dados inesperada causa crash
4. Execução paralela falha silenciosamente
5. Campos obrigatórios ausentes causam crash

### Média Prioridade
1. Normalização de texto incompleta
2. Agregação de dados falha para casos edge
3. Formatação de período não suporta todos os formatos
4. Retorno de estrutura não padronizada
5. Conversão de tipos falha silenciosamente

### Baixa Prioridade
1. Sugestões de entidades similares
2. Validação de campos opcionais
3. Logs mais detalhados
4. Performance de matching
5. Mensagens de erro mais descritivas

---

## Recomendações

1. **Validação robusta**: Validar arquivos, estruturas e dados antes de processar
2. **Tratamento de erros**: Sempre retornar erros descritivos com sugestões
3. **Fuzzy matching**: Implementar matching mais robusto para entidades
4. **Normalização**: Normalizar texto de forma mais abrangente
5. **Estruturas padronizadas**: Padronizar estruturas de retorno ou documentar todas
6. **Testes**: Criar testes para casos edge identificados
7. **Logs**: Melhorar logs para facilitar debug
8. **Fallbacks**: Implementar fallbacks quando possível
9. **Documentação**: Documentar todas as estruturas de retorno possíveis
10. **Validação de entrada**: Validar queries antes de processar
