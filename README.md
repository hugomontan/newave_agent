# NW Multi Agent

Sistema unificado para consultas inteligentes em decks NEWAVE e DECOMP usando LangGraph e RAG.

## Estrutura do Projeto

```
nw_multi/
├── backend/              # Backend Python (FastAPI)
│   ├── main.py          # Entry point unificado
│   ├── run.py           # Script de execução
│   ├── requirements.txt # Dependências Python
│   ├── core/            # Componentes compartilhados
│   │   ├── base_tool.py # Classe base para tools
│   │   ├── config.py    # Configurações compartilhadas
│   │   ├── nodes/       # Nodes LangGraph genéricos
│   │   └── utils/       # Utilitários compartilhados
│   ├── newave/          # Módulo NEWAVE
│   │   ├── agent.py     # Agentes LangGraph
│   │   ├── api.py       # Endpoints FastAPI
│   │   ├── tools/       # Tools específicas NEWAVE
│   │   ├── agents/      # Agentes (single_deck, multi_deck)
│   │   └── rag/         # Sistema RAG
│   └── decomp/          # Módulo DECOMP
│       ├── agent.py     # Agentes LangGraph
│       ├── api.py       # Endpoints FastAPI
│       ├── tools/       # Tools específicas DECOMP
│       ├── agents/      # Agentes (single_deck, multi_deck)
│       └── rag/         # Sistema RAG
├── frontend/            # Frontend Next.js
│   ├── app/             # Páginas Next.js
│   │   ├── newave/      # Páginas NEWAVE
│   │   ├── decomp/      # Páginas DECOMP
│   │   └── llm/         # Interface de chat
│   └── components/      # Componentes React
│       ├── comparison/  # Componentes de comparação
│       └── single-deck/ # Componentes single deck
└── .env                 # Variáveis de ambiente
```

## Pré-requisitos

- Python 3.10+
- Node.js 18+
- npm ou yarn

## Instalação

### Backend

1. Instale as dependências Python:
```bash
pip install -r requirements.txt
```

2. Configure as variáveis de ambiente:
```bash
# Copie o arquivo .env e configure as variáveis necessárias
# OPENAI_API_KEY=your_key_here
# LANGFUSE_SECRET_KEY=your_key_here (opcional)
# etc.
```

### Frontend

1. Instale as dependências Node.js:
```bash
npm install
```

## Execução

### Backend

Na raiz do projeto:
```bash
python run.py
```

O servidor será iniciado em `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`
- NEWAVE endpoints: `http://localhost:8000/api/newave/*`
- DECOMP endpoints: `http://localhost:8000/api/decomp/*`

### Frontend

Na raiz do projeto:
```bash
npm run dev
```

O frontend será iniciado em `http://localhost:3000`

## Arquitetura

### Visão Geral

O sistema utiliza uma arquitetura baseada em **LangGraph** para orquestrar agentes inteligentes que processam consultas sobre decks NEWAVE e DECOMP. A arquitetura é composta por:

1. **Backend FastAPI**: API REST unificada que expõe endpoints para ambos os modelos
2. **Agentes LangGraph**: Grafos de estado que orquestram o processamento de queries
3. **Tools Pré-programadas**: Funções especializadas para consultas frequentes
4. **Sistema RAG**: Recuperação de documentação contextual usando ChromaDB
5. **Frontend Next.js**: Interface web unificada para ambos os modelos

### Fluxo de Processamento

```
Query do Usuário
    ↓
API Endpoint (FastAPI)
    ↓
Agent LangGraph
    ↓
Tool Router (verifica se há tool pré-programada)
    ├─→ Tool encontrada → Executa tool → Interpreter formata resposta
    └─→ Tool não encontrada → Interpreter usa RAG + LLM para responder
    ↓
Resposta formatada retornada ao frontend
```

### Componentes Principais

#### 1. Agentes LangGraph

Cada modelo (NEWAVE e DECOMP) possui dois tipos de agentes:

- **Single Deck Agent**: Para consultas em um único deck
  - Fluxo: `tool_router` → `interpreter`
  - Foco em consultas específicas de um deck

- **Multi Deck Agent**: Para comparações entre múltiplos decks
  - Fluxo: `comparison_tool_router` → `comparison_interpreter`
  - Foco em análises comparativas

#### 2. Tool Router

O **Tool Router** é o primeiro node do grafo e tem a responsabilidade de:

1. Receber a query do usuário
2. Iterar sobre todas as tools disponíveis
3. Verificar se alguma tool pode processar a query (método `can_handle()`)
4. Se encontrada, executar a tool (método `execute()`)
5. Passar o resultado para o Interpreter

#### 3. Interpreter

O **Interpreter** recebe o resultado da tool (ou indicação de que não houve tool) e:

1. Se houve tool: formata o resultado usando formatters específicos
2. Se não houve tool: usa RAG + LLM para gerar resposta contextual

#### 4. Sistema RAG

- **Indexação**: Documentação dos modelos é indexada em ChromaDB
- **Recuperação**: Busca semântica por similaridade
- **Contexto**: Chunks relevantes são passados ao LLM para gerar respostas

## Funcionalidades

### NEWAVE (Modelo de Médio a Longo Prazo)

**Modo Single Deck** (14 tools):
- Carga Mensal
- Valores CLAS-T
- Expectativas de Operação (EXPT)
- Modificações de Operação (MODIF)
- Limites de Intercâmbio
- Agrupamentos de Intercâmbio (AGRINT)
- Vazões
- Cadastro Adicional (CADIC)
- Cadastro Hidrelétrico
- Configuração Hidrelétrica (CONFHD)
- Desvios de Água (DSVAGUA)
- Usinas Não Simuladas
- Restrições Elétricas
- Cadastro Termelétrico

**Modo Comparison** (4 tools adicionais):
- Variação de Reservatório Inicial
- Mudanças de Gerações Térmicas (GTMIN)
- Mudanças de Vazão Mínima
- Comparação Multi-Deck Genérica

### DECOMP (Modelo de Curto Prazo)

**Modo Single Deck** (12 tools):
- Usinas Hidrelétricas (UH)
- Usinas Termelétricas (CT)
- Carga de Subsistemas (DP)
- Inflexibilidade de Usina
- Disponibilidade de Usina
- Pequenas Usinas (PQ)
- Carga ANDE
- Limites de Intercâmbio
- Restrições Elétricas
- Restrições de Vazão HQ
- Restrições de Vazão HQ Conjunta
- Gerações GNL (GL)

**Modo Multi-Deck** (11 tools adicionais):
- Disponibilidade Multi-Deck
- Carga de Subsistemas Multi-Deck
- Volume Inicial Multi-Deck
- Restrições Vazão HQ Multi-Deck
- Restrições Elétricas Multi-Deck
- Pequenas Usinas Multi-Deck
- Limites Intercâmbio Multi-Deck
- Inflexibilidade Multi-Deck
- Gerações GNL Multi-Deck
- CVU Multi-Deck
- Carga ANDE Multi-Deck

**Total**: 41 tools cobrindo os principais casos de uso dos modelos NEWAVE e DECOMP

## Modelos Suportados

### NEWAVE
- Modelo de médio a longo prazo (até 5 anos, mensal)
- Endpoints: `/api/newave/*`
- 18 tools disponíveis (14 single + 4 comparison)

### DECOMP
- Modelo de curto prazo (até 12 meses, semanal/mensal)
- Endpoints: `/api/decomp/*`
- 23 tools disponíveis (12 single + 11 multi-deck)

## Funcionamento de uma Tool

### Arquitetura de uma Tool

Todas as tools herdam de `BaseTool` e implementam três métodos principais:

```python
class BaseTool(ABC):
    @abstractmethod
    def can_handle(self, query: str) -> bool:
        """Verifica se a tool pode processar a query"""
        
    @abstractmethod
    def execute(self, query: str, **kwargs) -> Dict[str, Any]:
        """Executa a tool e retorna dados processados"""
        
    @abstractmethod
    def get_description(self) -> str:
        """Retorna descrição da tool para o LLM"""
```

### Exemplo: LimitesIntercambioDECOMPTool

Vamos analisar como uma tool funciona usando como exemplo a `LimitesIntercambioDECOMPTool`:

#### 1. Detecção (`can_handle()`)

A tool verifica se a query do usuário contém palavras-chave relacionadas:

```python
def can_handle(self, query: str) -> bool:
    query_lower = query.lower()
    keywords = [
        "limite de intercambio",
        "limite de intercâmbio",
        "limites de intercambio",
        "intercambio entre",
        "registro ia",
    ]
    return any(kw in query_lower for kw in keywords)
```

**Exemplos de queries que ativam esta tool:**
- "Limite N para FC"
- "Limites de intercâmbio de S para SE"
- "Qual o limite entre NE e SE?"

#### 2. Execução (`execute()`)

Quando a tool é selecionada, o método `execute()` é chamado:

**Passo 1: Localização do arquivo**
```python
dadger_path = self._find_dadger_file()  # Busca dadger.rv* no deck
dadger = Dadger.read(dadger_path)      # Lê arquivo usando idecomp
```

**Passo 2: Extração de parâmetros da query**
```python
sub_de, sub_para, sentido_query = self._extrair_par_simples(query)
# Ex: "Limite N para FC" → sub_de="N", sub_para="FC"
```

**Passo 3: Leitura dos registros**
```python
ia_df = dadger.ia(df=True)  # Lê todos os registros IA como DataFrame
ia_objetos = dadger.ia(
    estagio=1,
    nome_submercado_de=sub_de,
    nome_submercado_para=sub_para,
    df=False
)  # Lê registros específicos como objetos para acessar limites
```

**Passo 4: Processamento dos dados**
```python
# Extrai limites por patamar (P1, P2, P3) para ambos os sentidos
limites_extraidos = self._extrair_limites_do_registro(registro)

# Calcula MW médio ponderado usando durações dos patamares
duracoes = self._extrair_duracoes_patamares(dadger)
mw_medio = self._calcular_mw_medio_ponderado(valores, duracoes)
```

**Passo 5: Retorno estruturado**
```python
return {
    "success": True,
    "data": [
        {
            "estagio": 1,
            "sub_de": "N",
            "sub_para": "FC",
            "limite_de_para_p1": 1000.0,
            "limite_de_para_p2": 800.0,
            "limite_de_para_p3": 600.0,
            "limite_para_de_p1": 500.0,
            "mw_medio_de_para": 850.0,
            # ...
        }
    ],
    "tool": "LimitesIntercambioDECOMPTool"
}
```

#### 3. Tratamento de Erros

A tool implementa tratamento robusto de erros:

- **Par não encontrado**: Sugere pares similares disponíveis
- **Arquivo não encontrado**: Retorna mensagem clara
- **Dados inválidos**: Valida e retorna erros específicos

```python
if registros_filtrados.empty:
    pares = self._listar_todos_pares(ia_df)
    sugestoes = self._sugerir_pares_similares(sub_de, sub_para, pares)
    return {
        "success": False,
        "error": f"Par '{sub_de} -> {sub_para}' não existe.",
        "pares_disponiveis": pares,
        "sugestoes": sugestoes
    }
```

#### 4. Formatação

Após a execução, o **Interpreter** recebe o resultado e usa formatters específicos para:

- Converter dados para formato tabular (DataFrames)
- Gerar visualizações (gráficos)
- Formatar texto para apresentação ao usuário

### Casos de Uso Cobertos

As 41 tools do sistema cobrem os principais casos de uso:

**Consultas de Cadastro:**
- Usinas hidrelétricas e termelétricas
- Configurações de usinas
- Parâmetros operacionais

**Consultas Operacionais:**
- Cargas e demandas
- Vazões e volumes
- Gerações e disponibilidades
- Limites de intercâmbio

**Consultas de Restrições:**
- Restrições elétricas
- Restrições de vazão
- Limites operacionais

**Análises Comparativas:**
- Comparação entre múltiplos decks
- Variações de parâmetros
- Análises de impacto

**Cálculos Especializados:**
- MW médio ponderado por patamar
- Inflexibilidades por usina
- Disponibilidades por período

### Vantagens da Arquitetura de Tools

1. **Performance**: Tools pré-programadas são muito mais rápidas que LLM
2. **Precisão**: Código específico garante resultados exatos
3. **Manutenibilidade**: Cada tool é independente e testável
4. **Extensibilidade**: Fácil adicionar novas tools para novos casos
5. **Fallback Inteligente**: Se não há tool, usa RAG + LLM como backup

## Desenvolvimento

### Estrutura de Módulos

Cada módulo (NEWAVE e DECOMP) possui sua própria estrutura:
- `tools/` - Tools específicas do modelo (herdam de BaseTool)
- `agents/` - Agentes LangGraph (single_deck, multi_deck)
- `rag/` - Sistema RAG para documentação
- `api.py` - Endpoints FastAPI do módulo

### Frontend

O frontend está unificado e serve ambos os modelos:
- `app/newave/` - Páginas NEWAVE
- `app/decomp/` - Páginas DECOMP
- `components/comparison/` - Componentes de comparação multi-deck
- `components/single-deck/` - Componentes para visualização single deck

## Variáveis de Ambiente

Principais variáveis no `.env`:
- `OPENAI_API_KEY` - Chave da API OpenAI
- `OPENAI_MODEL` - Modelo OpenAI a usar (padrão: gpt-4o-mini)
- `LANGFUSE_SECRET_KEY` - Chave secreta Langfuse (opcional)
- `LANGFUSE_PUBLIC_KEY` - Chave pública Langfuse (opcional)
- `LANGFUSE_HOST` - Host do Langfuse (opcional)

## Scripts Disponíveis

### Backend
- `python run.py` - Inicia servidor de desenvolvimento com reload

### Frontend
- `npm run dev` - Inicia servidor de desenvolvimento
- `npm run build` - Build para produção
- `npm start` - Inicia servidor de produção

## Documentação

- API Docs: `http://localhost:8000/docs` (quando backend estiver rodando)
- Documentação dos modelos: Ver `newave_agent/docs/` e `decomp_agent/docs/`
