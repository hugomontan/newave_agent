"use client";

import React from "react";
import { motion } from "framer-motion";
import { CargaAndeComparisonTable } from "./CargaAndeComparisonTable";
import { CargaAndeComparisonChart } from "./CargaAndeComparisonChart";
import type { ComparisonData } from "../shared/types";

interface CargaAndeComparisonViewProps {
  comparison: ComparisonData;
}

export function CargaAndeComparisonView({ comparison }: CargaAndeComparisonViewProps) {
  const { comparison_table, chart_data, chart_config, deck_names } = comparison as any;
  
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
          Carga ANDE Média Ponderada (MW Médio)
        </h3>
        <p className="text-sm text-muted-foreground">
          {deck_names && deck_names.length > 0 ? `${deck_names.length} decks comparados` : ""}
        </p>
      </div>

      {/* Tabela */}
      {hasTableData && (
        <CargaAndeComparisonTable
          data={comparison_table}
        />
      )}

      {/* Gráfico */}
      {hasChartData && (
        <CargaAndeComparisonChart 
          data={chart_data} 
          config={chart_config}
        />
      )}
      
      {/* Mensagem se não há dados */}
      {!hasTableData && !hasChartData && (
        <div className="bg-card border border-border rounded-lg p-4 sm:p-6">
          <p className="text-sm text-muted-foreground">
            Nenhum dado de Carga ANDE disponível para comparação.
          </p>
        </div>
      )}
    </motion.div>
  );
}
