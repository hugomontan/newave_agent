"use client";

import React from "react";
import { motion } from "framer-motion";
import { UsinasNaoSimuladasTable } from "./UsinasNaoSimuladasTable";
import { UsinasNaoSimuladasChart } from "./UsinasNaoSimuladasChart";
import type { ComparisonData } from "../shared/types";
import { getDeckNames, isHistoricalAnalysis } from "../shared/types";

interface UsinasNaoSimuladasViewProps {
  comparison: ComparisonData;
}

export function UsinasNaoSimuladasView({ comparison }: UsinasNaoSimuladasViewProps) {
  const { deck_1, deck_2, comparison_table, chart_data, chart_config, deck_displays, deck_count, decks_raw } = comparison as any;
  
  // Obter nomes de todos os decks (suporte N decks)
  const allDeckNames = getDeckNames(comparison);
  const isHistorical = isHistoricalAnalysis(comparison);
  
  // Validação: verificar se há dados para renderizar
  const hasTableData = comparison_table && comparison_table.length > 0;
  const hasChartData = chart_data && chart_data.labels && chart_data.labels.length > 0 && 
                       chart_data.datasets && chart_data.datasets.length > 0;
  
  // Validar se número de datasets corresponde ao número de decks
  const chartDataValid = hasChartData && chart_data.datasets.length === (deck_count || allDeckNames.length || 2);
  
  // Validar se tabela tem colunas para todos os decks
  const tableDataValid = hasTableData && comparison_table.length > 0;
  if (tableDataValid && comparison_table[0]) {
    const firstRow = comparison_table[0];
    const deckColumnsCount = Object.keys(firstRow).filter(key => key.startsWith('deck_')).length;
    const expectedDeckCount = deck_count || allDeckNames.length || 2;
    if (deckColumnsCount !== expectedDeckCount) {
      console.warn(`[UsinasNaoSimuladasView] Inconsistência: tabela tem ${deckColumnsCount} colunas de deck, mas esperado ${expectedDeckCount}`);
    }
  }

  // Obter nomes dos decks para a tabela (com fallback)
  const deckNamesForTable = deck_displays || allDeckNames || 
    (deck_1 && deck_2 ? [deck_1.name, deck_2.name] : []);

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="w-full space-y-6 mt-4"
    >
      {/* Tabela */}
      {hasTableData && (
        <UsinasNaoSimuladasTable
          data={comparison_table}
          deck1Name={deck_1?.name || deckNamesForTable[0] || "Deck 1"}
          deck2Name={deck_2?.name || deckNamesForTable[deckNamesForTable.length - 1] || "Deck 2"}
          deckNames={deckNamesForTable}
        />
      )}

      {/* Gráfico */}
      {hasChartData && chartDataValid && (
        <UsinasNaoSimuladasChart data={chart_data} chartConfig={chart_config} />
      )}
      
      {/* Aviso se dados incompletos */}
      {hasChartData && !chartDataValid && (
        <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-yellow-500 mb-2">
            Aviso: Dados incompletos
          </h3>
          <p className="text-xs text-yellow-500/80">
            O gráfico tem {chart_data.datasets.length} séries, mas esperado {deck_count || allDeckNames.length || 2} decks.
          </p>
        </div>
      )}

      {/* Mensagem de erro se algum deck falhou */}
      {deck_1 && deck_2 && (!deck_1.success || !deck_2.success) && (
        <div className="bg-destructive/10 border border-destructive/30 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-destructive mb-2">
            Erros na comparação:
          </h3>
          {deck_1 && !deck_1.success && (
            <p className="text-xs text-destructive/80">
              {deck_1.name}: {deck_1.error || "Erro desconhecido"}
            </p>
          )}
          {deck_2 && !deck_2.success && (
            <p className="text-xs text-destructive/80">
              {deck_2.name}: {deck_2.error || "Erro desconhecido"}
            </p>
          )}
        </div>
      )}
      
      {/* Mensagem se não há dados */}
      {!hasTableData && !hasChartData && (
        <div className="bg-muted/50 border border-border rounded-lg p-4">
          <p className="text-sm text-muted-foreground">
            Nenhum dado disponível para visualização.
          </p>
        </div>
      )}
    </motion.div>
  );
}
