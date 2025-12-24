# Documentação NEWAVE - Índice de Arquivos

Este documento fornece uma visão geral dos arquivos NEWAVE e suas funções principais. Use este índice para identificar quais arquivos são relevantes para sua análise.

---

## Arquivos de Configuração Geral

### CASO.DAT
- **Função**: Arquivo de entrada inicial que aponta para outros arquivos do estudo
- **Classe inewave**: `Caso`
- **Propriedades**: `arquivos`, `gerenciador_processos`
- **Use quando**: Precisa saber qual arquivo índice está sendo usado ou o caminho do gerenciador de processos

---

## Arquivos de Usinas Térmicas

### MANUTT.DAT
- **Função**: Manutenções programadas das usinas térmicas
- **Classe inewave**: `Manutt`
- **Propriedades**: `manutencoes` (DataFrame)
- **Colunas principais**: `codigo_usina`, `nome_usina`, `data_inicio`, `duracao`, `potencia`
- **Use quando**: Precisa analisar manutenções de térmicas, indisponibilidades programadas, potência em manutenção

### CLAST.DAT
- **Função**: Classes de usinas térmicas e custos de operação
- **Classe inewave**: `Clast`
- **Propriedades**: `usinas` (DataFrame), `modificacoes` (DataFrame)
- **Colunas principais**: `codigo_usina`, `nome_usina`, `tipo_combustivel`, `indice_ano_estudo`, `valor` (custo $/MWh)
- **Use quando**: Precisa analisar custos de térmicas, tipos de combustível, modificações sazonais de custo

### ADTERM.DAT
- **Função**: Dados adicionais das usinas térmicas (limites operativos)
- **Classe inewave**: `Adterm`
- **Propriedades**: `usinas` (DataFrame), `restricoes_geracao` (DataFrame)
- **Colunas principais**: `codigo_usina`, `nome_usina`, `lag`, `geracao_minima`, `geracao_maxima`, `custo`
- **Use quando**: Precisa analisar limites de geração térmica, restrições operativas, geracao mínima/máxima

---

## Arquivos de Usinas Hidrelétricas

### HIDR.DAT
- **Função**: Cadastro completo das usinas hidrelétricas (arquivo binário)
- **Classe inewave**: `Hidr`
- **Propriedades**: `cadastro` (DataFrame com 60+ colunas)
- **Colunas principais**: `nome_usina`, `posto`, `submercado`, `volume_minimo`, `volume_maximo`, `potencia_nominal_conjunto_[1-5]`, `produtibilidade_especifica`, `vazao_minima_historica`
- **Use quando**: Precisa de dados cadastrais de hidrelétricas, volumes, potências, características físicas
- **NÃO TEM**: geração hidráulica (isso vem de resultados, não do cadastro)

### CONFHD.DAT
- **Função**: Configuração das usinas hidrelétricas no estudo
- **Classe inewave**: `Confhd`
- **Propriedades**: `usinas` (DataFrame)
- **Colunas principais**: `codigo_usina`, `nome_usina`, `ree`, `volume_inicial`, `status`, `modificacao`, `existe_modelagem_individualizada`
- **Use quando**: Precisa saber quais usinas estão no estudo, qual REE pertencem, volume inicial

### VAZOES.DAT
- **Função**: Séries históricas de vazões naturais
- **Classe inewave**: `Vazoes`
- **Propriedades**: `vazoes` (DataFrame)
- **Colunas principais**: `posto`, `ano`, meses (jan a dez com valores de vazão em m³/s)
- **Use quando**: Precisa analisar histórico de vazões, séries hidrológicas

### EXPH.DAT
- **Função**: Expansões hidrelétricas programadas
- **Classe inewave**: `Exph`
- **Propriedades**: `expansoes` (DataFrame)
- **Colunas principais**: `codigo_usina`, `data`, `volume_maximo`, `potencia`, `produtibilidade`
- **Use quando**: Precisa analisar novas usinas hidrelétricas, expansões de capacidade

### MODIF.DAT
- **Função**: Modificações temporárias de características de usinas hidrelétricas
- **Classe inewave**: `Modif`
- **Propriedades**: `modificacoes` (DataFrame)
- **Colunas principais**: `codigo_usina`, `data_inicio`, `data_fim`, parâmetro modificado
- **Use quando**: Precisa analisar alterações temporárias em características de usinas

---

## Arquivos de Subsistemas e REEs

### SISTEMA.DAT
- **Função**: Definição dos subsistemas/submercados e suas demandas
- **Classe inewave**: `Sistema`
- **Propriedades**: `custo_deficit` (DataFrame), `mercado_energia` (DataFrame), `intercambios` (DataFrame)
- **Colunas principais**: `codigo_submercado`, `nome_submercado`, `mes`, `ano`, `mercado`, `patamar`, `valor`
- **Use quando**: Precisa analisar demandas, custos de déficit, limites de intercâmbio entre submercados

### REE.DAT
- **Função**: Definição dos Reservatórios Equivalentes de Energia
- **Classe inewave**: `Ree`
- **Propriedades**: `rees` (DataFrame)
- **Colunas principais**: `codigo`, `nome`, `submercado`, `mes_fim_periodo_seco`, `ano_fim_periodo_seco`
- **Use quando**: Precisa saber quais REEs existem, a qual submercado pertencem

---

## Arquivos de Restrições e Configurações Especiais

### AGRINT.DAT
- **Função**: Agrupamentos de interligações (restrições lineares de transmissão)
- **Classe inewave**: `Agrint`
- **Propriedades**: `agrupamentos` (DataFrame), `limites_agrupamentos` (DataFrame)
- **Colunas principais**: `agrupamento`, `submercado_de`, `submercado_para`, `coeficiente`, `patamar`, `valor`
- **Use quando**: Precisa analisar restrições de transmissão, limites de intercâmbio compostos

### CVAR.DAT
- **Função**: Configuração do CVaR (mecanismo de aversão a risco)
- **Classe inewave**: `Cvar`
- **Propriedades**: `valores` (DataFrame)
- **Colunas principais**: `alfa`, `lambda`, `periodo_inicio`, `periodo_fim`
- **Use quando**: Precisa analisar parâmetros de aversão a risco

### EXPT.DAT
- **Função**: Expansões de usinas térmicas
- **Classe inewave**: `Expt`
- **Propriedades**: `expansoes` (DataFrame)
- **Colunas principais**: `codigo_usina`, `nome_usina`, `data`, `potencia`, `custo`, `tipo_combustivel`
- **Use quando**: Precisa analisar novas usinas térmicas, expansões de capacidade

### C_ADIC.DAT
- **Função**: Custos adicionais por subsistema
- **Classe inewave**: `Cadic`
- **Propriedades**: `custos_adicionais` (DataFrame)
- **Colunas principais**: `codigo_submercado`, `nome_submercado`, `mes`, `ano`, `valor`
- **Use quando**: Precisa analisar custos adicionais de operação por submercado

---

## Resumo de Colunas Importantes por Tema

### Para análise de POTÊNCIA:
- `HIDR.DAT`: `potencia_nominal_conjunto_[1-5]` (potência instalada de hidrelétricas)
- `ADTERM.DAT`: `geracao_minima`, `geracao_maxima` (limites de térmicas)
- `MANUTT.DAT`: `potencia` (potência em manutenção)

### Para análise de VOLUMES:
- `HIDR.DAT`: `volume_minimo`, `volume_maximo`, `volume_vertedouro`
- `CONFHD.DAT`: `volume_inicial`
- `EXPH.DAT`: `volume_maximo` (expansões)

### Para análise de CUSTOS:
- `CLAST.DAT`: `valor` (custo de operação de térmicas $/MWh)
- `SISTEMA.DAT`: `custo_deficit` (custo de déficit)
- `C_ADIC.DAT`: custos adicionais

### Para análise de VAZÕES:
- `VAZOES.DAT`: séries históricas de vazões por posto
- `HIDR.DAT`: `vazao_minima_historica`, `vazao_nominal_conjunto_[1-5]`

### Para análise de DEMANDA/MERCADO:
- `SISTEMA.DAT`: `mercado_energia` (demanda por submercado e patamar)

### Para análise de TRANSMISSÃO:
- `SISTEMA.DAT`: `intercambios` (limites de intercâmbio)
- `AGRINT.DAT`: restrições compostas de transmissão

---

## Observações Importantes

1. **Geração hidráulica**: O arquivo `HIDR.DAT` contém dados CADASTRAIS das usinas (potência instalada, volumes, etc.), NÃO contém valores de geração hidráulica. Geração é um RESULTADO do modelo, não uma entrada.

2. **Dados binários**: O arquivo `HIDR.DAT` é binário, mas a biblioteca inewave abstrai isso através da propriedade `cadastro`.

3. **Expansões**: Usinas com status "EE" ou "NE" no `CONFHD.DAT` têm suas expansões definidas em `EXPH.DAT` (hidrelétricas) ou `EXPT.DAT` (térmicas).

4. **Modificações**: Alterações temporárias nas características de usinas hidrelétricas são feitas via `MODIF.DAT`.

