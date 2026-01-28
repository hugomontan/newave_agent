# Guia para criação de nova tool

Este documento descreve a metodologia de criação de uma nova tool no sistema, aprofundando em cada modo de operação, seleção e formatação. O texto não usa emojis.

---

## Indice

1. [Visao Geral](#visao-geral)
2. [Modo de Analise da API](#modo-de-analise-da-api)
3. [Modo de Operacao da Tool: Single-Deck vs Multi-Deck](#modo-de-operacao-da-tool-single-deck-vs-multi-deck)
4. [Modo de Selecao da Tool (Matching)](#modo-de-selecao-da-tool-matching)
5. [Modos Internos da Tool](#modos-internos-da-tool)
6. [Modo de Formatacao](#modo-de-formatacao)
7. [Passo a Passo por Cenario](#passo-a-passo-por-cenario)
8. [Estruturas de Dados e Contratos](#estruturas-de-dados-e-contratos)
9. [Referencias no Codigo](#referencias-no-codigo)

---

## Visao Geral

Uma "tool" e um modulo que responde a consultas do usuario sobre dados do deck (NEWAVE ou DECOMP). A criacao envolve:

- **Onde** a tool vive (single-deck ou multi-deck, NEWAVE ou DECOMP)
- **Como** ela e escolhida (semantico, keywords, correcao de usina, disambiguation)
- **Como** ela se comporta por dentro (modos como "somente usina exata" vs "multi-usina")
- **Como** o resultado e formatado para o frontend (formatter especifico ou generico)

Cada uma dessas dimensoes e um "modo" que pode ser configurado ou implementado de forma distinta.

---

## Modo de Analise da API

O frontend envia `analysis_mode` na requisicao de query. O backend usa esse campo para decidir qual fluxo executar.

### Valores e efeito

| analysis_mode | Fluxo                        | Origem do deck                         |
|---------------|------------------------------|----------------------------------------|
| `"single"`    | Single-deck agent            | `sessions[session_id]` (um diretorio)   |
| `"comparison"` | Multi-deck (comparison) agent| `comparison_sessions[session_id]` + `deck_paths` |

- **Single**: um unico deck por sessao. A API chama `single_deck_run_query` ou `single_deck_run_query_stream`. O estado tem `deck_path` e `query`.
- **Comparison**: multiplos decks selecionados. A API chama `multi_deck_run_query` ou `multi_deck_run_query_stream`. O estado tem `deck_paths` (nome -> caminho), `selected_decks` e `query`.

### Onde isso e definido

- Contrato da API: `QueryRequest.analysis_mode` (ex.: em `backend/decomp/api.py`).
- Roteamento: em `/query` e `/query/stream`, `analysis_mode == "comparison"` escolhe o fluxo multi-deck; caso contrario, single-deck.

Para criar uma tool, e preciso saber em qual modo de analise ela sera usada: apenas single, apenas comparison, ou ambos (neste caso sera necessaria uma tool single e outra multi, ou uma multi que internamente use a single).

---

## Modo de Operacao da Tool: Single-Deck vs Multi-Deck

O "modo de operacao" da tool e definido pelo tipo de entrada (um deck ou varios) e pelo lugar onde ela e registrada e instanciada.

### Single-Deck

- **Entrada**: um unico caminho de deck.
- **Construtor**: `__init__(self, deck_path: str)`.
- **Registry**: lista de classes no modulo de tools do modelo (NEWAVE ou DECOMP), por exemplo `TOOLS_REGISTRY_SINGLE` em `backend/decomp/tools/__init__.py`.
- **Instanciacao**: `get_available_tools(deck_path)` retorna `[Classe(deck_path) for Classe in TOOLS_REGISTRY_SINGLE]`.
- **Uso**: no agente single-deck. No DECOMP, o tool router single-deck usa essas instancias.

Arquivos tipicos:

- Base: `backend/core/base_tool.py` (interface abstrata), `backend/decomp/tools/base.py` (DECOMPTool).
- Tools: `backend/decomp/tools/<nome>_tool.py`.
- Registry: `backend/decomp/tools/__init__.py` (`TOOLS_REGISTRY_SINGLE`, `get_available_tools(deck_path)`).

### Multi-Deck

- **Entrada**: varios decks, identificados por nome e caminho.
- **Construtor**: `__init__(self, deck_paths: Dict[str, str])`. Por compatibilidade com a base, costuma-se passar o primeiro caminho para `super().__init__(first_deck_path)` e guardar `self.deck_paths`.
- **Registry**: lista no modulo de tools multi-deck do modelo, por exemplo `TOOLS_REGISTRY_MULTI` em `backend/decomp/agents/multi_deck/tools/__init__.py`.
- **Instanciacao**: `get_available_tools(selected_decks, deck_paths)` retorna uma instancia por classe em `TOOLS_REGISTRY_MULTI`, cada uma recebendo `deck_paths`.
- **Uso**: no agente de comparacao. No DECOMP, o comparison tool router usa essas instancias.

Arquivos tipicos:

- Tools: `backend/decomp/agents/multi_deck/tools/<nome>_multi_deck_tool.py`.
- Registry: `backend/decomp/agents/multi_deck/tools/__init__.py` (`TOOLS_REGISTRY_MULTI`, `get_available_tools(selected_decks, deck_paths)`).

### Relacao Single x Multi

Uma tool multi-deck costuma:

1. Receber a mesma `query` que o usuario digitou.
2. Para cada deck em `deck_paths` (ou em `selected_decks`), instanciar a tool single-deck correspondente e chamar `tool_single.execute(query, ...)`.
3. Agregar os resultados (por exemplo por deck e por data) e retornar um unico dicionario com estrutura de comparacao.

Ou seja, o "modo multi-deck" e, em geral, uma orquestracao em paralelo da versao single-deck, com agregacao e, se for o caso, calculo de datas (ex.: quinta-feira da semana do deck).

Exemplo de orquestracao: `PQMultiDeckTool` usa `ThreadPoolExecutor`, para cada par (deck_name, deck_path) chama `_execute_single_deck(deck_name, deck_path, query)`, que instancia `PQPequenasUsinasTool(deck_path)` e chama `tool.execute(query, verbose=False)`.

---

## Modo de Selecao da Tool (Matching)

A escolha de qual tool executar e feita no "tool router" de cada agente. Ha diferentes mecanismos (modos de matching):

### 1. Matching semantico

Usa embeddings da query e das descricoes das tools para ranquear por similaridade.

- **Single-deck DECOMP**: em `backend/decomp/agents/single_deck/nodes/tool_router.py`, se `SEMANTIC_MATCHING_ENABLED` ou `USE_HYBRID_MATCHING`, chama `find_top_tools_semantic(query, tools, top_n=5, threshold=SEMANTIC_MATCH_THRESHOLD)`. A primeira do ranking e a candidata; regras adicionais podem trocar a escolha (ex.: vazao conjunta vs unitaria).
- **Multi-deck DECOMP**: em `backend/decomp/agents/multi_deck/nodes/comparison_tool_router.py`, se `SEMANTIC_MATCHING_ENABLED`, chama `find_best_tool_semantic(query, tools, threshold=SEMANTIC_MATCH_THRESHOLD)` e usa a primeira tool retornada.

Variaveis de ambiente (ou equivalentes em `backend/core/config.py`):

- `SEMANTIC_MATCHING_ENABLED`: liga/desliga o matching semantico.
- `SEMANTIC_MATCH_THRESHOLD`: limite minimo de score para considerar uma tool (ex.: 0.4).
- `SEMANTIC_MATCH_MIN_SCORE`: score minimo para executar direto (acima disso nao se gera disambiguation).
- `USE_HYBRID_MATCHING`: no single-deck, pode combinar semantico com outro criterio.

Para uma nova tool ser encontrada pelo fluxo semantico, e essencial que `get_description()` descreva bem o dominio (termos, exemplos de perguntas, fluxo tecnico). O `semantic_matcher` usa essas descricoes para gerar os embeddings.

### 2. Regras pos-ranking (single-deck)

Apos o ranking semantico, o router pode sobrescrever a escolha com base em palavras-chave da query.

Exemplo no tool router single-deck DECOMP:

- Se a query contem termos como "conjunta", "somatorio", etc., o router procura no top-N a `RestricoesVazaoHQConjuntaTool` e, se achar, prefere ela.
- Se a query nao tem esses termos e o melhor do ranking e `RestricoesVazaoHQConjuntaTool`, o router pode trocar para `RestricoesVazaoHQTool` (unitaria).

Ou seja: mesmo em "modo semantico", existe um submodo "regras por keyword" que ajusta a tool final.

### 3. Query de correcao de usina

Formato especial: `__PLANT_CORR__:NomeDaTool:CodigoUsina:query_original`.

- O router detecta esse padrao e extrai tool, codigo e query original.
- Em single-deck: resolve a tool pelo nome, chama `execute(original_query, forced_plant_code=codigo)` (ou equivalente) e retorna o resultado.
- Em multi-deck: o router mapeia o nome da tool single para a tool multi correspondente (ex.: `UHUsinasHidrelétricasTool` -> `VolumeInicialMultiDeckTool`), instancia essa multi, chama `execute(original_query, forced_plant_code=codigo)` e retorna.

Para sua nova tool participar desse modo, ela deve:

- Aceitar em `execute(query, **kwargs)` um argumento como `forced_plant_code` (ou o nome que o router usar).
- Tratar esse argumento internamente (ex.: ignorar resolucao por nome e usar o codigo fixo).

O parsing da query especial e feito em `parse_plant_correction_query` (em `backend/core/nodes/tool_router_base.py` ou equivalente).

### 4. Query de disambiguation (escolha explicita de tool)

Formato especial: `__DISAMBIG__:NomeDaTool:query_original`.

- O usuario escolheu uma das opcoes de disambiguation; a query enviada e essa string.
- O router identifica o padrao, localiza a tool pelo nome e executa com `query_original`.

Para a nova tool ser escolhivel via disambiguation, ela precisa poder aparecer na lista de opcoes do fluxo de disambiguation (que depende do modelo e do router; no NEWAVE single-deck ha suporte a disambiguation com `generate_disambiguation_response` e listas como `DISAMBIGUATION_MAX_OPTIONS`). No DECOMP single-deck, o fluxo atual prioriza semantic + regras e nao reexpoe disambiguation da mesma forma que o NEWAVE; mesmo assim, o contrato `__DISAMBIG__:ToolName:query` e o conceito a implementar se esse modo for estendido.

### 5. Matching por keyword (can_handle)

A interface base exige `can_handle(query: str) -> bool`. Em varios roteadores, porem, o fluxo principal e semantico; `can_handle` acaba mais relevante para:

- documentar quais queries "fariam sentido" para a tool;
- eventual fallback ou filtros em outros modelos (ex.: NEWAVE), onde o hybrid matching pode usar keywords.

Para uma nova tool, e boa pratica implementar `can_handle` de forma consistente com `get_description`: se a descricao diz que a tool trata "restricao de vazao da usina X", `can_handle` deve retornar True para queries que mencionem esse tipo de assunto, para nao contradizer o comportamento do ranking semantico.

Resumo dos modos de selecao:

| Modo              | Onde usado          | Entrada                    | Acao principal                                      |
|-------------------|---------------------|----------------------------|-----------------------------------------------------|
| Semantico         | Single e multi      | `query`                    | Ranking por embedding; escolhe melhor tool          |
| Regras pos-rank   | Single DECOMP       | `query` + top-N tools      | Ajusta escolha (ex.: conjunta vs unitaria HQ)      |
| Correcao usina    | Single e multi      | `__PLANT_CORR__:...`       | Executa tool com codigo de usina forcado           |
| Disambiguation    | Onde implementado   | `__DISAMBIG__:...`         | Executa tool escolhida com query original         |
| can_handle        | Hibrido/fallback   | `query`                    | Filtro booleano por keyword                        |

---

## Modos Internos da Tool

"Modos internos" sao comportamentos parametrizados dentro da propria tool, sem mudar a tool que foi selecionada. Eles controlam como os dados sao filtrados ou agregados.

### Exemplo: RestricoesVazaoHQTool

Em `backend/decomp/tools/restricoes_vazao_hq_tool.py`:

- **Somente usina exata** (`somente_usina_exata=True`): considera apenas restricoes HQ em que a usina consultada e a unica participante. Restricoes que envolvem outras usinas (HQ multi-usina) sao ignoradas.
- **Multi-usina** (`somente_usina_exata=False`): inclui restricoes que envolvem mais de uma usina. Quando a query menciona varias usinas, a tool usa a interseccao dos codigos HQ comuns a todas elas.

A escolha entre esses modos e feita pela propria tool com base na query e no numero de usinas resolvidas:

- Uma usina mencionada -> `somente_usina_exata=True`.
- Duas ou mais usinas -> `somente_usina_exata=False` e logica de interseccao.

Outros parametros tipicos de comportamento interno:

- **verbose**: reduz ou aumenta logs dentro de `execute`.
- **Filtros extraidos da query**: patamar, estagio, tipo de geracao, subsistema, etc. A tool pode expor metodos como `_extract_tipo_from_query(query)` ou `_extract_usina_from_query(query)` e usar o resultado para filtrar antes de montar o retorno.

Para documentar uma nova tool, convem listar explicitamente os "modos internos" (incluindo parametros como `somente_usina_exata`, `verbose`, ou filtros derivados da query) e em que condicoes cada um e ativado.

---

## Modo de Formatacao

Apos `tool.execute(query, **kwargs)` retornar um dicionario, o resultado e passado a um formatter, que gera o texto final e os dados de visualizacao para o frontend.

### Quem escolhe o formatter

No single-deck DECOMP, em `backend/decomp/agents/single_deck/formatters/registry.py`:

- `get_formatter_for_tool(tool, tool_result)` percorre uma lista de formatters (`SINGLE_DECK_FORMATTERS`).
- Cada formatter e interrogado com `can_format(tool_name, tool_result)`.
- A lista e ordenada por `get_priority()` (maior valor primeiro). O primeiro que retornar True em `can_format` e usado.
- Se nenhum atender, usa-se um `GenericSingleDeckFormatter`.

Ou seja, o "modo" de formatacao e "qual formatter atende esta tool e este resultado". Isso e decidido por nome da tool + estrutura do resultado + prioridade.

### Contrato do formatter

O formatter implementa a interface em `backend/decomp/agents/single_deck/formatters/base.py`:

- `can_format(tool_name: str, result_structure: Dict[str, Any]) -> bool`
- `get_priority() -> int` (default 0; quanto maior, mais prioritario)
- `format_response(tool_result, tool_name, query) -> Dict[str, Any]`

O retorno de `format_response` deve conter pelo menos:

- `final_response`: string (geralmente Markdown) para exibir ao usuario.
- `visualization_data`: opcional; estrutura usada pelo frontend para tabelas, graficos, etc.

Um mesmo formatter pode tratar mais de uma tool. Exemplo: `RestricoesEletricasSingleDeckFormatter` trata `RestricoesEletricasDECOMPTool`, `RestricoesVazaoHQTool` e `RestricoesVazaoHQConjuntaTool`, escolhendo titulos e sugestoes de arquivo conforme `tool_name`.

### Multi-deck

No fluxo de comparacao, a formatacao e feita no "comparison interpreter". Ele recebe o resultado agregado da tool multi-deck (ex.: `decks`, `is_comparison`, `tool_name`) e monta a resposta e, se houver, os dados de comparacao/graficos. Formatters especificos para comparacao podem viver em algo como `backend/decomp/agents/multi_deck/formatting/` ou na estrutura equivalente do modelo.

Para uma nova tool multi-deck, e necessario garantir que o interpreter saiba tratar a estrutura retornada por ela (ou que exista um formatter de comparacao que a reconheca por `tool_name` e por chaves do resultado).

---

## Passo a Passo por Cenario

### Cenario A: Nova tool single-deck (DECOMP)

1. **Classe e arquivo**
   - Criar `backend/decomp/tools/<nome>_tool.py`.
   - Herdar de `DECOMPTool` (que herda de `BaseTool`).
   - Implementar `get_name()`, `can_handle(query)`, `execute(query, **kwargs)`, `get_description()`.

2. **Construtor**
   - `__init__(self, deck_path: str)` e `super().__init__(deck_path)`.

3. **Retorno de execute**
   - Seguir o contrato esperado pelo formatter e pelo router: por exemplo `success`, `dados` ou `data`, `error` em falha, `tool` com o nome da tool. Incluir campos que o formatter ira usar (ex.: listas por estagio/patamar).

4. **Registro**
   - Em `backend/decomp/tools/__init__.py`: importar a classe e incluir em `TOOLS_REGISTRY_SINGLE`. Manter `get_available_tools(deck_path)` instanciando todas as classes do registry.

5. **Matching**
   - Escrever `get_description()` rico em termos e exemplos, para o matching semantico ranquear bem.
   - Implementar `can_handle(query)` alinhado à descricao.
   - Se a nova tool disputar com outra (como no caso HQ unitaria vs conjunta), ver se e preciso adicionar regras pos-ranking no `tool_router` single-deck.

6. **Formatacao**
   - Se os dados forem complexos ou especificos, criar um formatter em `backend/decomp/agents/single_deck/formatters/data_formatters/`, implementando `can_format`, `get_priority` e `format_response`, e registrando-o em `SINGLE_DECK_FORMATTERS` no registry de formatters.

7. **Testes**
   - Instanciar a tool com um `deck_path` valido, chamar `execute` com queries tipicas e verificar estrutura do retorno e se o formatter correto e escolhido.

### Cenario B: Nova tool multi-deck (DECOMP)

1. **Classe e arquivo**
   - Criar `backend/decomp/agents/multi_deck/tools/<nome>_multi_deck_tool.py`.
   - Herdar de `DECOMPTool`.
   - Construtor: `__init__(self, deck_paths: Dict[str, str])`, armazenar `self.deck_paths` e eventualmente `self.max_workers` para paralelismo.

2. **Implementacao**
   - `can_handle(query)`: refletir o mesmo dominio da tool single correspondente, eventualmente com termos como "comparar", "entre decks", etc., se quiser restringir a comparacao.
   - `execute(query, **kwargs)`: para cada (deck_name, deck_path) em `deck_paths` (ou em `kwargs.get("selected_decks", ...)`), instanciar a tool single-deck correspondente e chamar `tool_single.execute(query, ...)`. Reunir resultados em uma estrutura unica (ex.: lista por deck com `name`, `display_name`, `result`, `success`, `date`).

3. **Paralelismo**
   - Usar `ThreadPoolExecutor` (ou equivalente) para chamar a tool single em cada deck, com timeout e tratamento de excecao por deck.

4. **Retorno**
   - Incluir `success`, `is_comparison=True`, estrutura por deck (`decks`), `tool_name` (pode ser o nome da tool single para o frontend/interpreter), e metadados que o comparison interpreter ou formatter de multi-deck esperem.

5. **Registro**
   - Em `backend/decomp/agents/multi_deck/tools/__init__.py`: importar a classe e colocar em `TOOLS_REGISTRY_MULTI`. Ajustar `get_available_tools(selected_decks, deck_paths)` para incluir a nova classe.

6. **Correcao de usina (se aplicavel)**
   - Se a tool single aceita `forced_plant_code`, a multi-deck deve repassar em `execute(..., forced_plant_code=...)`. Garantir que o mapeamento single -> multi em `comparison_tool_router` inclua a nova tool, se ela participara de correcao de usina.

7. **Formatacao**
   - Garantir que o comparison interpreter (ou o formatter de multi-deck) saiba interpretar a estrutura retornada (ex.: `decks`, `tool_name`, campos de data).

### Cenario C: Nova tool single-deck com modos internos

1. **Identificar os modos**
   - Listar comportamentos alternativos (ex.: "somente usina exata" vs "multi-usina", "por estagio" vs "todos estagios").

2. **Parametros de execute**
   - Decidir se os modos vem de `kwargs` (ex.: `forced_plant_code`, `verbose`) ou sao inferidos da query (ex.: numero de usinas, palavras como "conjunta").

3. **Implementacao**
   - Dentro de `execute`, resolver usinas/entidades a partir da query (e de `kwargs`), depois aplicar a logica condicional (ex.: se uma usina -> `somente_usina_exata=True`; se duas ou mais -> interseccao e `somente_usina_exata=False`).

4. **Documentacao**
   - Em docstrings e em `get_description()`, descrever quando cada modo e usado, para quem for dar manutencao e para o ranking semantico continuar coerente.

### Cenario D: Formatter para uma tool existente

1. **Arquivo**
   - Criar ou editar um modulo em `backend/decomp/agents/single_deck/formatters/data_formatters/`, por exemplo `<nome>_formatter.py`.

2. **Classe**
   - Herdar de `SingleDeckFormatter`, implementar `can_format(tool_name, result_structure)` (retornar True para a nova tool e para chaves esperadas no resultado), `get_priority()` (valor maior que o do formatter generico e que outros que possam conflitar) e `format_response(tool_result, tool_name, query)`.

3. **Retorno de format_response**
   - `final_response`: texto em Markdown.
   - `visualization_data`: dicionario com o que o frontend espera (ex.: `table`, `chart_data`, `visualization_type`, `chart_config`, `tool_name`). Consultar formatters existentes e componentes do frontend para manter contrato.

4. **Registro**
   - Importar a classe no `__init__.py` dos data_formatters e adicionar uma instancia em `SINGLE_DECK_FORMATTERS` em `backend/decomp/agents/single_deck/formatters/registry.py`, na posicao desejada segundo prioridade.

---

## Estruturas de Dados e Contratos

### Retorno tipico de execute (single-deck)

```python
{
    "success": bool,
    "dados": List[Dict],   # ou "data", conforme convencao do formatter
    "error": str,          # se success=False
    "tool": str,           # nome da tool
    "stats": Dict,         # opcional
    "filtros_aplicados": Dict,  # opcional
    "description": str,    # opcional
    # Campos usados por formatters ou por correcao de usina:
    "selected_plant": {...},  # opcional, para follow-up de correcao
}
```

### Retorno tipico de execute (multi-deck)

```python
{
    "success": bool,
    "is_comparison": True,
    "decks": [
        {
            "name": str,
            "display_name": str,
            "result": Dict,   # resultado da tool single nesse deck
            "success": bool,
            "error": Optional[str],
            "date": Optional[str],
        },
        ...
    ],
    "tool_name": str,   # nome da tool single, para o interpreter
    # Metadados adicionais (ex.: tipo_filtrado, tipo_encontrado)
}
```

### Retorno de format_response (single-deck)

```python
{
    "final_response": str,
    "visualization_data": {
        "table": ...,
        "chart_data": ...,
        "visualization_type": str,
        "chart_config": {...},
        "tool_name": str,
        # Outros campos que o frontend consumir
    }
}
```

Mantenha consistencia com os formatters e com os componentes de UI que leem `visualization_data`.

---

## Referencias no Codigo

- Base e interface: `backend/core/base_tool.py`, `backend/decomp/tools/base.py`
- Registry single DECOMP: `backend/decomp/tools/__init__.py`
- Registry multi DECOMP: `backend/decomp/agents/multi_deck/tools/__init__.py`
- Tool router single DECOMP: `backend/decomp/agents/single_deck/nodes/tool_router.py`
- Tool router multi DECOMP: `backend/decomp/agents/multi_deck/nodes/comparison_tool_router.py`
- Funcoes compartilhadas do router: `backend/core/nodes/tool_router_base.py`
- Matching semantico DECOMP: `backend/decomp/tools/semantic_matcher.py`
- Formatters single DECOMP: `backend/decomp/agents/single_deck/formatters/registry.py`, `backend/decomp/agents/single_deck/formatters/base.py`, `backend/decomp/agents/single_deck/formatters/data_formatters/`
- Exemplo de modos internos: `backend/decomp/tools/restricoes_vazao_hq_tool.py` (somente_usina_exata, multi-usina)
- Exemplo multi-deck: `backend/decomp/agents/multi_deck/tools/pq_multi_deck_tool.py`
- API e analysis_mode: `backend/decomp/api.py` (rotas `/query`, `/query/stream`)

Documentos complementares: `docs/guia-adicionar-tools.md`, `docs/levantamento-bugs-tools.md`.

---

## Resumo: Arquivos e Alteracoes por Cenario

Quantidade aproximada de arquivos a criar e de arquivos existentes a editar em cada situacao.

### Cenario minimo: so tool single-deck

| Tipo | Quantidade | Onde |
|------|------------|------|
| Arquivo novo | 1 | `backend/decomp/tools/<nome>_tool.py` |
| Arquivo editado | 1 | `backend/decomp/tools/__init__.py` (import + entrada em `TOOLS_REGISTRY_SINGLE`) |

Total: **1 arquivo novo, 1 edicao**. A tool passa a ser instanciada por `get_available_tools(deck_path)` e pode ser encontrada pelo matching semantico. Se nao houver formatter especifico, o `GenericSingleDeckFormatter` e usado.

---

### Tool single-deck + formatter especifico

| Tipo | Quantidade | Onde |
|------|------------|------|
| Arquivos novos | 2 | `backend/decomp/tools/<nome>_tool.py` e `backend/decomp/agents/single_deck/formatters/data_formatters/<nome>_formatter.py` |
| Arquivos editados | 3 | `backend/decomp/tools/__init__.py`; `backend/decomp/agents/single_deck/formatters/registry.py` (entrada em `SINGLE_DECK_FORMATTERS`); `backend/decomp/agents/single_deck/formatters/data_formatters/__init__.py` (import e export do formatter) |

Total: **2 arquivos novos, 3 edicoes**.

---

### Tool single-deck + tool multi-deck (comparacao)

| Tipo | Quantidade | Onde |
|------|------------|------|
| Arquivos novos | 2 | `backend/decomp/tools/<nome>_tool.py` e `backend/decomp/agents/multi_deck/tools/<nome>_multi_deck_tool.py` |
| Arquivos editados | 2 | `backend/decomp/tools/__init__.py`; `backend/decomp/agents/multi_deck/tools/__init__.py` (import + entrada em `TOOLS_REGISTRY_MULTI`) |

Total: **2 arquivos novos, 2 edicoes**. A tool multi-deck orquestra a single; o comparison interpreter formata o resultado agregado. Se a comparacao precisar de formatter proprio (ex.: grafico de series por deck), pode ser preciso mais um formatter de multi-deck e edicoes no interpreter/formatting.

---

### Tool single + multi + formatter single

| Tipo | Quantidade | Onde |
|------|------------|------|
| Arquivos novos | 3 | `backend/decomp/tools/<nome>_tool.py`; `backend/decomp/agents/multi_deck/tools/<nome>_multi_deck_tool.py`; `backend/decomp/agents/single_deck/formatters/data_formatters/<nome>_formatter.py` |
| Arquivos editados | 4 | `backend/decomp/tools/__init__.py`; `backend/decomp/agents/multi_deck/tools/__init__.py`; `backend/decomp/agents/single_deck/formatters/registry.py`; `backend/decomp/agents/single_deck/formatters/data_formatters/__init__.py` |

Total: **3 arquivos novos, 4 edicoes**.

---

### Participacao em correcao de usina (multi-deck)

Nao gera arquivos novos; exige edicao em arquivo existente:

| Tipo | Quantidade | Onde |
|------|------------|------|
| Arquivo editado | 1 | `backend/decomp/agents/multi_deck/nodes/comparison_tool_router.py`: incluir o par `"NomeToolSingle": "NomeToolMulti"` no dicionario `single_to_multi_tool_map` |

A tool single deve aceitar em `execute(query, **kwargs)` um argumento como `forced_plant_code` (ou o nome usado pelo router) e repassar isso na chamada interna; a tool multi deve repassar o mesmo parametro ao chamar a single.

---

### Regras pos-ranking no tool router (single-deck)

Usado quando duas tools disputam o mesmo tipo de query (ex.: vazao unitaria vs conjunta). Nao gera arquivos novos; exige edicao em arquivo existente:

| Tipo | Quantidade | Onde |
|------|------------|------|
| Arquivo editado | 1 | `backend/decomp/agents/single_deck/nodes/tool_router.py`: depois de obter `top_tools`, adicionar ramificacao por keyword que escolha ou troque a tool (ex.: se "conjunta" na query, preferir ToolConjunta; senao, preferir ToolUnitaria) |

---

### Tabela consolidada (ordem crescente de escopo)

| Cenario | Arquivos novos | Arquivos editados |
|---------|----------------|-------------------|
| So tool single | 1 | 1 |
| Tool single + formatter | 2 | 3 |
| Tool single + multi | 2 | 2 |
| Tool single + multi + formatter single | 3 | 4 |
| + correcao usina (multi) | 0 | +1 |
| + regra pos-ranking (single) | 0 | +1 |

Em um caso completo (tool single, multi, formatter single, correcao de usina e regra pos-ranking): **3 arquivos novos** e **6 arquivos editados** (ou 5 se a regra de ranking for desnecessaria).

---

### Observacoes

- **Nao criar**: `backend/core/base_tool.py`, `backend/decomp/tools/base.py`, `tool_router.py` e `comparison_tool_router.py` sao compartilhados; novas tools nao exigem novos routers, apenas registro e, quando fizer sentido, regras ou mapeamentos nos routers existentes.
- **Reutilizar formatter**: se uma tool nova for coberta por um formatter ja existente (ex.: mesma estrutura de `dados` e mesmo tipo de grafico), nao e obrigatorio criar formatter novo; basta garantir que `can_format(tool_name, result_structure)` dessa classe retorne True para a nova tool. Nesse caso, zero arquivos de formatter e zero edicoes em registry/__init__ de formatters.
- **Linhas de codigo (ordem de grandeza)**: tool single tipica 80–300 linhas; tool multi tipica 150–350 linhas; formatter tipico 80–200 linhas. Variam conforme filtros, modos internos e tipo de visualizacao.
