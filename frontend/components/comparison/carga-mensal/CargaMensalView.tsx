"use client";

import React from "react";
import { motion } from "framer-motion";
import { CargaMensalTable } from "./CargaMensalTable";
import { CargaMensalChart } from "./CargaMensalChart";
import type { ComparisonData } from "../shared/types";
import { getDeckNames, isHistoricalAnalysis } from "../shared/types";

interface CargaMensalViewProps {
  comparison: ComparisonData;
}

export function CargaMensalView({ comparison }: CargaMensalViewProps) {
  const { deck_1, deck_2, comparison_table, chart_data, deck_displays, deck_count } = comparison as any;
  
  // Obter nomes de todos os decks (suporte N decks)
  const allDeckNames = getDeckNames(comparison);
  const isHistorical = isHistoricalAnalysis(comparison);

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="w-full space-y-6 mt-4"
    >
      {/* Tabela */}
      {comparison_table && comparison_table.length > 0 && (
        <CargaMensalTable
          data={comparison_table}
          deck1Name={deck_1?.name || allDeckNames[0] || "Deck 1"}
          deck2Name={deck_2?.name || allDeckNames[allDeckNames.length - 1] || "Deck 2"}
          deckNames={allDeckNames}
        />
      )}

      {/* Gráfico */}
      {chart_data && chart_data.labels && chart_data.labels.length > 0 && (
        <CargaMensalChart data={chart_data} />
      )}

      {/* Mensagem de erro se algum deck falhou */}
      {(!deck_1.success || !deck_2.success) && (
        <div className="bg-destructive/10 border border-destructive/30 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-destructive mb-2">
            Erros na comparação:
          </h3>
          {!deck_1.success && (
            <p className="text-xs text-destructive/80">
              {deck_1.name}: {deck_1.error || "Erro desconhecido"}
            </p>
          )}
          {!deck_2.success && (
            <p className="text-xs text-destructive/80">
              {deck_2.name}: {deck_2.error || "Erro desconhecido"}
            </p>
          )}
        </div>
      )}
    </motion.div>
  );
}
