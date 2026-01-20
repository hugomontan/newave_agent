"use client";

import React from "react";
import { motion } from "framer-motion";
import { LimitesIntercambioComparisonTable } from "./LimitesIntercambioComparisonTable";
import { LimitesIntercambioComparisonChart } from "./LimitesIntercambioComparisonChart";
import type { ComparisonData } from "../shared/types";

interface LimitesIntercambioComparisonViewProps {
  comparison: ComparisonData;
}

export function LimitesIntercambioComparisonView({ comparison }: LimitesIntercambioComparisonViewProps) {
  const { comparison_table, chart_data, chart_config, deck_names } = comparison;
  
  // Validação: verificar se há dados para renderizar
  const hasTableData = comparison_table && comparison_table.length > 0;
  const hasChartData = chart_data && chart_data.labels && chart_data.labels.length > 0 && 
                       chart_data.datasets && chart_data.datasets.length > 0;
  
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="w-full space-y-6 mt-4"
    >
      {/* Header com informações */}
      <div className="bg-card border border-border rounded-lg p-4 sm:p-6">
        <h3 className="text-base sm:text-lg font-semibold text-card-foreground mb-2">
          Limites de Intercâmbio - MW Médio Ponderado
        </h3>
        <p className="text-sm text-muted-foreground">
          {deck_names && deck_names.length > 0 ? `${deck_names.length} decks comparados` : ""}
        </p>
      </div>

      {/* Tabela */}
      {hasTableData && (
        <LimitesIntercambioComparisonTable
          data={comparison_table}
        />
      )}

      {/* Gráfico */}
      {hasChartData && (
        <LimitesIntercambioComparisonChart 
          data={chart_data} 
          config={chart_config}
        />
      )}
      
      {/* Mensagem se não há dados */}
      {!hasTableData && !hasChartData && (
        <div className="bg-card border border-border rounded-lg p-4 sm:p-6">
          <p className="text-sm text-muted-foreground">
            Nenhum dado de Limites de Intercâmbio disponível para comparação.
          </p>
        </div>
      )}
    </motion.div>
  );
}
