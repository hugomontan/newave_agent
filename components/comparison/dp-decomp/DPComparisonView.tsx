"use client";

import React from "react";
import { motion } from "framer-motion";
import { DPComparisonTable } from "./DPComparisonTable";
import { DPComparisonChart } from "./DPComparisonChart";
import type { ComparisonData } from "../shared/types";

interface DPComparisonViewProps {
  comparison: ComparisonData;
}

export function DPComparisonView({ comparison }: DPComparisonViewProps) {
  const { comparison_table, chart_data, chart_config, deck_names, submercados } = comparison;
  
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
          Carga Média Ponderada (MW Médio) por Submercado
        </h3>
        <p className="text-sm text-muted-foreground">
          {deck_names && deck_names.length > 0 ? `${deck_names.length} decks comparados` : ""}
          {submercados && submercados.length > 0 && (
            <> | Submercados: {submercados.map(s => s.nome).join(", ")}</>
          )}
        </p>
      </div>

      {/* Tabela */}
      {hasTableData && (
        <DPComparisonTable
          data={comparison_table}
          submercados={submercados as Array<{ codigo: number; nome: string }>}
        />
      )}

      {/* Gráfico */}
      {hasChartData && (
        <DPComparisonChart 
          data={chart_data} 
          config={chart_config}
        />
      )}
      
      {/* Mensagem se não há dados */}
      {!hasTableData && !hasChartData && (
        <div className="bg-card border border-border rounded-lg p-4 sm:p-6">
          <p className="text-sm text-muted-foreground">
            Nenhum dado de carga média ponderada disponível para comparação.
          </p>
        </div>
      )}
    </motion.div>
  );
}
