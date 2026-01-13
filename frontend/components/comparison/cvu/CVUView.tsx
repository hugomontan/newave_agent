"use client";

import React from "react";
import { motion } from "framer-motion";
import { CVUTable } from "./CVUTable";
import { CVUChart } from "./CVUChart";
import type { ComparisonData } from "../shared/types";

interface CVUViewProps {
  comparison: ComparisonData;
}

export function CVUView({ comparison }: CVUViewProps) {
  const { deck_1, deck_2, comparison_table, chart_data } = comparison;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="w-full space-y-6 mt-4"
    >
      {/* Tabela */}
      {comparison_table && comparison_table.length > 0 && (
        <CVUTable
          data={comparison_table}
          deck1Name={deck_1.name}
          deck2Name={deck_2.name}
        />
      )}

      {/* Gráfico */}
      {chart_data && chart_data.labels && chart_data.labels.length > 0 && (
        <CVUChart data={chart_data} />
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
