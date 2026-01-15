# NEWAVE Agent Frontend

Interface web para o sistema de consultas inteligentes em decks NEWAVE.

## Requisitos

- Node.js 18+
- npm ou yarn

## Instalação

```bash
cd frontend
npm install
```

## Executando

1. Primeiro, certifique-se de que o backend está rodando:
```bash
# Na pasta raiz do projeto
python run.py
```

2. Em outro terminal, inicie o frontend:
```bash
cd frontend
npm run dev
```

3. Acesse http://localhost:3000

## Funcionalidades

- **Upload de Deck**: Arraste ou selecione um arquivo .zip com o deck NEWAVE
- **Chat Interativo**: Faça perguntas em linguagem natural sobre os dados
- **Visualização de Código**: Veja o código Python gerado pelo agente
- **Gerenciamento de Sessão**: Acompanhe os arquivos carregados e limpe sessões
- **Reindexação**: Reindexe a documentação quando necessário

## Configuração

A URL da API pode ser configurada através da variável de ambiente `NEXT_PUBLIC_API_URL`:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev
```
