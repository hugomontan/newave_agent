# Guia: Como Adicionar Tools

Este guia explica como adicionar novas tools ao sistema após a limpeza e reorganização do código. A estrutura atual está mais modular e organizada, facilitando a adição de novas funcionalidades.

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Estrutura de uma Tool](#estrutura-de-uma-tool)
3. [Passo a Passo](#passo-a-passo)
4. [Exemplo Completo](#exemplo-completo)
5. [Formatters](#formatters)
6. [Boas Práticas](#boas-práticas)
7. [Troubleshooting](#troubleshooting)

---

## Visão Geral

### O que mudou após a limpeza?

✅ **Estrutura mais limpa e modular**
- Classes base unificadas em `backend/core/`
- Tools organizadas por modelo (NEWAVE/DECOMP)
- Formatters separados e registrados automaticamente
- Registry centralizado e fácil de usar

✅ **Processo simplificado**
- Herança clara de classes base
- Padrões consistentes entre tools
- Sistema de formatters automático
- Menos código duplicado

### Tipos de Tools

O sistema suporta dois tipos principais de tools:

1. **NEWAVE Tools** (`backend/newave/tools/`)
   - Para análise de decks NEWAVE
   - Herdam de `NEWAVETool`
   - Registradas em `backend/newave/tools/__init__.py`

2. **DECOMP Tools** (`backend/decomp/tools/`)
   - Para análise de decks DECOMP
   - Herdam de `DECOMPTool`
   - Registradas em `backend/decomp/tools/__init__.py`

### Modos de Operação

As tools podem operar em dois modos:

1. **Single Deck** (padrão)
   - Analisa um único deck
   - Recebe `deck_path: str` no construtor
   - Tools em `backend/newave/tools/` ou `backend/decomp/tools/`

2. **Multi-Deck** (comparação)
   - Compara múltiplos decks simultaneamente
   - Recebe `deck_paths: Dict[str, str]` no construtor
   - Tools específicas em `backend/newave/agents/multi_deck/tools/` ou `backend/decomp/agents/multi_deck/tools/`
   - Executam tools single-deck em paralelo e agregam resultados

---

## Estrutura de uma Tool

Toda tool deve implementar a interface `BaseTool` com três métodos obrigatórios:

```python
class MinhaTool(NEWAVETool):
    def can_handle(self, query: str) -> bool:
        """Verifica se a tool pode processar a query"""
        pass
    
    def execute(self, query: str, **kwargs) -> Dict[str, Any]:
        """Executa a tool e retorna os dados"""
        pass
    
    def get_description(self) -> str:
        """Retorna descrição da tool para o LLM"""
        pass
```

### Estrutura do Retorno de `execute()`

O método `execute()` deve retornar um dicionário com a seguinte estrutura:

```python
{
    "success": bool,           # True se execução foi bem-sucedida
    "dados": List[Dict],        # Dados processados (se success=True)
    "error": str,               # Mensagem de erro (se success=False)
    "stats": Dict,              # Estatísticas resumidas (opcional)
    "filtros_aplicados": Dict,  # Filtros aplicados (opcional)
    "description": str,         # Descrição do resultado (opcional)
    "tool": str                 # Nome da tool
}
```

---

## Passo a Passo

### 1. Criar o arquivo da Tool

Crie um novo arquivo em:
- `backend/newave/tools/minha_tool.py` (para NEWAVE)
- `backend/decomp/tools/minha_tool.py` (para DECOMP)

### 2. Implementar a classe da Tool

```python
from backend.newave.tools.base import NEWAVETool
from typing import Dict, Any
import os

class MinhaTool(NEWAVETool):
    """Tool para consultar [descrição do que a tool faz]."""
    
    def __init__(self, deck_path: str):
        super().__init__(deck_path)
        # Inicializações específicas aqui
    
    def get_name(self) -> str:
        return "MinhaTool"
    
    def can_handle(self, query: str) -> bool:
        """Verifica se a query é sobre [tema da tool]."""
        query_lower = query.lower()
        keywords = ["palavra-chave1", "palavra-chave2"]
        return any(kw in query_lower for kw in keywords)
    
    def execute(self, query: str, **kwargs) -> Dict[str, Any]:
        """Executa a consulta."""
        try:
            # 1. Verificar existência do arquivo
            arquivo_path = os.path.join(self.deck_path, "ARQUIVO.DAT")
            if not os.path.exists(arquivo_path):
                return {
                    "success": False,
                    "error": f"Arquivo ARQUIVO.DAT não encontrado",
                    "tool": self.get_name()
                }
            
            # 2. Ler arquivo usando inewave ou idecomp
            # dados = Arquivo.read(arquivo_path)
            
            # 3. Processar dados
            # dados_processados = self._processar_dados(dados)
            
            # 4. Retornar resultado
            return {
                "success": True,
                "dados": dados_processados,
                "description": "Descrição do resultado",
                "tool": self.get_name()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Erro ao processar: {str(e)}",
                "tool": self.get_name()
            }
    
    def get_description(self) -> str:
        """Retorna descrição da tool para o LLM."""
        return """
        [Descrição detalhada da tool]
        
        Queries que ativam esta tool:
        - "exemplo 1"
        - "exemplo 2"
        
        Termos-chave: palavra1, palavra2, palavra3.
        """
```

### 3. Registrar a Tool

Adicione a tool ao registry apropriado:

**Para NEWAVE Single Deck:**
Edite `backend/newave/tools/__init__.py`:

```python
from backend.newave.tools.minha_tool import MinhaTool

TOOLS_REGISTRY_SINGLE = [
    # ... outras tools
    MinhaTool,
]
```

**Para DECOMP Single Deck:**
Edite `backend/decomp/tools/__init__.py`:

```python
from backend.decomp.tools.minha_tool import MinhaTool

TOOLS_REGISTRY_SINGLE = [
    # ... outras tools
    MinhaTool,
]
```

### 4. Testar a Tool

Teste a tool manualmente ou através da API:

```python
from backend.newave.tools.minha_tool import MinhaTool

tool = MinhaTool("/caminho/para/deck")
result = tool.execute("consulta de teste")
print(result)
```

---

## Exemplo Completo

Vamos criar uma tool exemplo: `ExemploTool` que consulta um arquivo fictício `EXEMPLO.DAT`.

### 1. Arquivo da Tool

```python
"""
Tool para consultar dados do EXEMPLO.DAT.
"""
from backend.newave.tools.base import NEWAVETool
from typing import Dict, Any, Optional
import os
import pandas as pd
import re
from backend.newave.config import debug_print, safe_print


class ExemploTool(NEWAVETool):
    """
    Tool para consultar dados do arquivo EXEMPLO.DAT.
    
    Dados disponíveis:
    - Campo1
    - Campo2
    - Data
    """
    
    def __init__(self, deck_path: str):
        super().__init__(deck_path)
    
    def get_name(self) -> str:
        return "ExemploTool"
    
    def can_handle(self, query: str) -> bool:
        """Verifica se a query é sobre exemplo."""
        query_lower = query.lower()
        keywords = [
            "exemplo",
            "exemplo.dat",
            "dados exemplo",
        ]
        return any(kw in query_lower for kw in keywords)
    
    def _extract_filtro_from_query(self, query: str) -> Optional[str]:
        """Extrai filtro da query (exemplo)."""
        # Implementar lógica de extração de filtros
        return None
    
    def execute(self, query: str, **kwargs) -> Dict[str, Any]:
        """Executa a consulta de exemplo."""
        debug_print(f"[TOOL] {self.get_name()}: Iniciando execução...")
        
        try:
            # ETAPA 1: Verificar existência do arquivo
            exemplo_path = os.path.join(self.deck_path, "EXEMPLO.DAT")
            if not os.path.exists(exemplo_path):
                exemplo_path = os.path.join(self.deck_path, "exemplo.dat")
                if not os.path.exists(exemplo_path):
                    safe_print(f"[TOOL] ❌ Arquivo EXEMPLO.DAT não encontrado")
                    return {
                        "success": False,
                        "error": f"Arquivo EXEMPLO.DAT não encontrado em {self.deck_path}",
                        "tool": self.get_name()
                    }
            
            debug_print(f"[TOOL] ✅ Arquivo encontrado: {exemplo_path}")
            
            # ETAPA 2: Ler arquivo
            # dados = Exemplo.read(exemplo_path)
            
            # ETAPA 3: Processar dados
            # dados_processados = self._processar_dados(dados, query)
            
            # ETAPA 4: Retornar resultado
            return {
                "success": True,
                "dados": [],  # Substituir por dados reais
                "description": "Dados do EXEMPLO.DAT",
                "tool": self.get_name()
            }
            
        except Exception as e:
            safe_print(f"[TOOL] ❌ Erro ao processar: {type(e).__name__}: {e}")
            return {
                "success": False,
                "error": f"Erro ao processar EXEMPLO.DAT: {str(e)}",
                "error_type": type(e).__name__,
                "tool": self.get_name()
            }
    
    def get_description(self) -> str:
        """Retorna descrição da tool para o LLM."""
        return """
        Consulta dados do arquivo EXEMPLO.DAT.
        
        Queries que ativam esta tool:
        - "dados do exemplo"
        - "exemplo.dat"
        - "consulta exemplo"
        
        Termos-chave: exemplo, exemplo.dat, dados exemplo.
        """
```

### 2. Registrar no `__init__.py`

```python
# backend/newave/tools/__init__.py
from backend.newave.tools.exemplo_tool import ExemploTool

TOOLS_REGISTRY_SINGLE = [
    # ... outras tools
    ExemploTool,
]
```

---

## Tools Multi-Deck

Tools multi-deck são usadas para comparar dados entre múltiplos decks. Elas executam a tool single-deck correspondente em paralelo em todos os decks selecionados e agregam os resultados.

### Quando criar uma Tool Multi-Deck?

✅ **Crie uma tool multi-deck quando:**
- Você quer comparar dados entre múltiplos decks
- A comparação requer lógica específica (não apenas executar a tool single-deck)
- Você precisa agregar ou processar resultados de múltiplos decks

❌ **Não precisa criar tool multi-deck quando:**
- A comparação pode ser feita pela `MultiDeckComparisonTool` genérica
- A tool single-deck já retorna dados comparáveis

### Estrutura de uma Tool Multi-Deck

```python
from backend.decomp.tools.base import DECOMPTool
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, List

class MinhaToolMultiDeck(DECOMPTool):
    """Tool para comparar [dados] entre múltiplos decks."""
    
    def __init__(self, deck_paths: Dict[str, str]):
        """
        Inicializa a tool multi-deck.
        
        Args:
            deck_paths: Dict mapeando nome do deck para seu caminho
                       (ex: {"DC202501": "/path/to/deck"})
        """
        # Usar o primeiro deck como deck_path base (compatibilidade)
        first_deck_path = list(deck_paths.values())[0] if deck_paths else ""
        super().__init__(first_deck_path)
        self.deck_paths = deck_paths
        self.max_workers = min(len(deck_paths), 8)  # Ajustar conforme necessário
    
    def can_handle(self, query: str) -> bool:
        """Verifica se pode processar a query."""
        # Similar à tool single-deck, mas pode ter palavras-chave adicionais
        # como "comparar", "diferenças", etc.
        pass
    
    def execute(self, query: str, **kwargs) -> Dict[str, Any]:
        """Executa a tool em paralelo em todos os decks."""
        selected_decks = kwargs.get("selected_decks", list(self.deck_paths.keys()))
        
        # Executar tool single-deck em paralelo
        results = {}
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self._execute_single_deck, deck_name, query): deck_name
                for deck_name in selected_decks
            }
            
            for future in as_completed(futures):
                deck_name = futures[future]
                try:
                    results[deck_name] = future.result()
                except Exception as e:
                    results[deck_name] = {
                        "success": False,
                        "error": str(e)
                    }
        
        # Agregar resultados
        aggregated = self._aggregate_results(results, query)
        
        return {
            "success": True,
            "comparison_data": aggregated,
            "tool": self.get_name()
        }
    
    def _execute_single_deck(self, deck_name: str, query: str) -> Dict[str, Any]:
        """Executa a tool single-deck correspondente em um deck."""
        from backend.decomp.tools.minha_tool import MinhaTool
        
        deck_path = self.deck_paths[deck_name]
        tool = MinhaTool(deck_path)
        return tool.execute(query)
    
    def _aggregate_results(self, results: Dict[str, Dict], query: str) -> Dict[str, Any]:
        """Agrega resultados de múltiplos decks."""
        # Implementar lógica de agregação
        pass
```

### Registrar Tool Multi-Deck

**Para DECOMP Multi-Deck:**
Edite `backend/decomp/agents/multi_deck/tools/__init__.py`:

```python
from backend.decomp.agents.multi_deck.tools.minha_tool_multi_deck import MinhaToolMultiDeck

TOOLS_REGISTRY_MULTI = [
    # ... outras tools
    MinhaToolMultiDeck,
]
```

**Para NEWAVE Multi-Deck:**
Edite `backend/newave/agents/multi_deck/tools/__init__.py`:

```python
from backend.newave.agents.multi_deck.tools.minha_tool_multi_deck import MinhaToolMultiDeck

MULTI_DECK_TOOLS = [
    # ... outras tools
    MinhaToolMultiDeck,
]
```

### Exemplo: Tool Multi-Deck

Veja `backend/decomp/agents/multi_deck/tools/pq_multi_deck_tool.py` para um exemplo completo de tool multi-deck com execução paralela e agregação de resultados.

---

## Formatters

Formatters são responsáveis por formatar os dados retornados pela tool para exibição no frontend. Eles são opcionais, mas altamente recomendados.

### Quando criar um Formatter?

✅ **Crie um formatter quando:**
- A tool retorna dados complexos que precisam de formatação específica
- Você quer visualizações customizadas (gráficos, tabelas)
- A estrutura de dados é específica e não funciona bem com o formatter genérico

❌ **Não precisa criar formatter quando:**
- A tool retorna dados simples que o formatter genérico já formata bem
- Você está apenas testando a tool

### Estrutura de um Formatter

```python
from backend.newave.agents.single_deck.formatters.base import SingleDeckFormatter
from typing import Dict, Any

class ExemploSingleDeckFormatter(SingleDeckFormatter):
    """Formatter específico para ExemploTool."""
    
    def can_format(self, tool_name: str, result_structure: Dict[str, Any]) -> bool:
        """Verifica se pode formatar ExemploTool."""
        return tool_name == "ExemploTool" and "dados" in result_structure
    
    def get_priority(self) -> int:
        """Prioridade do formatter (maior = mais específico)."""
        return 80
    
    def format_response(
        self,
        tool_result: Dict[str, Any],
        tool_name: str,
        query: str
    ) -> Dict[str, Any]:
        """Formata resposta de ExemploTool."""
        dados = tool_result.get("dados", [])
        
        # Processar dados para tabela
        table_data = self._processar_para_tabela(dados)
        
        # Processar dados para gráfico (opcional)
        chart_data = self._processar_para_grafico(dados)
        
        # Formatar resposta em texto
        final_response = self._formatar_texto(dados)
        
        return {
            "final_response": final_response,
            "visualization_data": {
                "table": table_data,
                "chart_data": chart_data,
                "visualization_type": "line_chart",  # ou "bar_chart", "table", etc.
                "chart_config": {
                    "type": "line",
                    "title": "Título do Gráfico",
                    "x_axis": "Eixo X",
                    "y_axis": "Eixo Y"
                },
                "tool_name": "ExemploTool"
            }
        }
```

### Registrar o Formatter

**Para NEWAVE Single Deck:**
Edite `backend/newave/agents/single_deck/formatters/registry.py`:

```python
from backend.newave.agents.single_deck.formatters.data_formatters.exemplo_formatter import ExemploSingleDeckFormatter

SINGLE_DECK_FORMATTERS = [
    # ... outros formatters
    ExemploSingleDeckFormatter(),
]
```

**Para DECOMP Single Deck:**
Edite `backend/decomp/agents/single_deck/formatters/registry.py`:

```python
from backend.decomp.agents.single_deck.formatters.data_formatters.exemplo_formatter import ExemploSingleDeckFormatter

SINGLE_DECK_FORMATTERS = [
    # ... outros formatters
    ExemploSingleDeckFormatter(),
]
```

### Formatters para Multi-Deck

Para tools que suportam comparação multi-deck, você também pode criar formatters específicos:

- **NEWAVE**: `backend/newave/agents/multi_deck/formatting/`
- **DECOMP**: `backend/decomp/agents/multi_deck/formatting/`

---

## Boas Práticas

### 1. Nomenclatura

✅ **Bom:**
- `CargaMensalTool`
- `LimitesIntercambioTool`
- `DsvaguaTool`

❌ **Evitar:**
- `Tool1`
- `MinhaToolNova`
- `ToolCarga`

### 2. Tratamento de Erros

Sempre trate erros adequadamente:

```python
try:
    # Código que pode falhar
    dados = Arquivo.read(path)
except FileNotFoundError:
    return {
        "success": False,
        "error": f"Arquivo não encontrado: {path}",
        "tool": self.get_name()
    }
except Exception as e:
    return {
        "success": False,
        "error": f"Erro ao processar: {str(e)}",
        "error_type": type(e).__name__,
        "tool": self.get_name()
    }
```

### 3. Debug e Logging

Use as funções de debug fornecidas:

```python
from backend.newave.config import debug_print, safe_print

debug_print("[TOOL] Mensagem de debug")  # Apenas em modo debug
safe_print("[TOOL] Mensagem importante")  # Sempre exibida
```

### 4. Extração de Filtros

Implemente métodos auxiliares para extrair filtros da query:

```python
def _extract_usina_from_query(self, query: str) -> Optional[int]:
    """Extrai código da usina da query."""
    # Implementar lógica de extração
    pass

def _extract_periodo_from_query(self, query: str) -> Optional[Dict]:
    """Extrai período da query."""
    # Implementar lógica de extração
    pass
```

### 5. Cache de Dados

Para dados que são carregados frequentemente, use cache:

```python
def __init__(self, deck_path: str):
    super().__init__(deck_path)
    self._cache_dados = None

def _carregar_dados(self):
    """Carrega dados com cache."""
    if self._cache_dados is None:
        self._cache_dados = Arquivo.read(self.arquivo_path)
    return self._cache_dados
```

### 6. Documentação

Sempre documente:
- O que a tool faz
- Quais arquivos ela lê
- Quais queries a ativam
- Quais filtros suporta

### 7. Testes

Teste a tool com diferentes queries:

```python
# Teste básico
tool = MinhaTool("/caminho/deck")
assert tool.can_handle("consulta teste") == True

# Teste de execução
result = tool.execute("consulta teste")
assert result["success"] == True
```

---

## Troubleshooting

### Problema: Tool não é reconhecida

**Solução:**
1. Verifique se a tool está registrada no `__init__.py` correto
2. Verifique se o import está correto
3. Reinicie o servidor backend

### Problema: `can_handle()` sempre retorna False

**Solução:**
1. Verifique se as palavras-chave estão corretas
2. Teste com `query.lower()` para case-insensitive
3. Adicione mais palavras-chave se necessário

### Problema: Erro ao ler arquivo

**Solução:**
1. Verifique se o arquivo existe no deck
2. Verifique permissões de leitura
3. Verifique se está usando o caminho correto (case-sensitive em alguns sistemas)

### Problema: Formatter não é usado

**Solução:**
1. Verifique se o formatter está registrado no registry
2. Verifique se `can_format()` retorna `True`
3. Verifique a prioridade do formatter (maior = mais específico)
4. Verifique se o `tool_name` corresponde exatamente

### Problema: Dados não aparecem no frontend

**Solução:**
1. Verifique a estrutura do retorno de `execute()`
2. Verifique se `success` é `True`
3. Verifique se `dados` é uma lista de dicionários
4. Verifique o formatter e a estrutura de `visualization_data`

---

## Checklist Final

Antes de considerar a tool completa, verifique:

- [ ] Tool implementa `can_handle()`, `execute()`, e `get_description()`
- [ ] Tool está registrada no `__init__.py` apropriado
- [ ] Tool trata erros adequadamente
- [ ] Tool usa debug_print/safe_print para logging
- [ ] Tool tem documentação adequada
- [ ] Tool foi testada com diferentes queries
- [ ] Formatter foi criado (se necessário) e registrado
- [ ] Formatter foi testado no frontend

---

## Recursos Adicionais

- **Exemplos de Tools:**
  - `backend/newave/tools/dsvagua_tool.py` - Exemplo completo com extração de filtros
  - `backend/newave/tools/carga_mensal_tool.py` - Exemplo com agregação de dados
  
- **Exemplos de Formatters:**
  - `backend/newave/agents/single_deck/formatters/data_formatters/dsvagua_formatter.py`
  - `backend/newave/agents/single_deck/formatters/data_formatters/carga_mensal_formatter.py`

- **Documentação de Bugs:**
  - `docs/levantamento-bugs-tools.md` - Lista de bugs potenciais e como evitá-los

---

## Conclusão

### Resposta: Sim, ficou muito mais fácil! 🎉

Após a limpeza e reorganização do código, adicionar novas tools se tornou significativamente mais simples. As principais melhorias incluem:

#### ✅ **Antes vs Depois**

**Antes da limpeza:**
- ❌ Código duplicado entre tools
- ❌ Estruturas inconsistentes
- ❌ Formatters misturados com lógica de tools
- ❌ Registry difícil de entender
- ❌ Muitos arquivos espalhados

**Depois da limpeza:**
- ✅ Classes base unificadas (`BaseTool`, `NEWAVETool`, `DECOMPTool`)
- ✅ Padrões consistentes entre todas as tools
- ✅ Formatters separados e registrados automaticamente
- ✅ Registry centralizado e claro
- ✅ Estrutura modular e organizada

#### 📊 **Comparação de Esforço**

| Tarefa | Antes | Depois |
|--------|-------|--------|
| Criar tool básica | ~200 linhas | ~100 linhas |
| Registrar tool | Múltiplos lugares | 1 linha no `__init__.py` |
| Criar formatter | Misturado com tool | Arquivo separado, 1 linha no registry |
| Entender estrutura | Difícil (código espalhado) | Fácil (padrão claro) |
| Manutenção | Complexa | Simples |

#### 🚀 **Processo Simplificado**

O processo agora é direto e padronizado:

1. ✅ Criar a classe da tool seguindo o padrão (herdar de `NEWAVETool` ou `DECOMPTool`)
2. ✅ Implementar 3 métodos: `can_handle()`, `execute()`, `get_description()`
3. ✅ Registrar no `__init__.py` (1 linha)
4. ✅ Criar formatter (opcional, mas recomendado)
5. ✅ Registrar formatter (1 linha)
6. ✅ Testar

#### 💡 **Benefícios Adicionais**

- **Reutilização**: Classes base podem ser estendidas facilmente
- **Consistência**: Todas as tools seguem o mesmo padrão
- **Manutenibilidade**: Código organizado facilita correções e melhorias
- **Testabilidade**: Estrutura clara facilita criação de testes
- **Documentação**: Padrões claros facilitam onboarding de novos desenvolvedores

#### 📚 **Próximos Passos**

1. Consulte os exemplos existentes:
   - `backend/newave/tools/dsvagua_tool.py` - Tool completa com extração de filtros
   - `backend/decomp/agents/multi_deck/tools/pq_multi_deck_tool.py` - Tool multi-deck

2. Revise a documentação de bugs:
   - `docs/levantamento-bugs-tools.md` - Lista de problemas comuns e como evitá-los

3. Teste sua tool:
   - Use diferentes queries
   - Teste casos de erro
   - Verifique o formatter no frontend

A estrutura modular facilita a manutenção e evolução do sistema. Se tiver dúvidas, consulte os exemplos existentes ou a documentação de bugs para evitar problemas comuns.

**Boa sorte criando suas tools! 🛠️**
