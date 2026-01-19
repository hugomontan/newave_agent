"use client";

import React from "react";
import { motion } from "framer-motion";
import { VolumeInicialComparisonTable } from "./VolumeInicialComparisonTable";
import { VolumeInicialComparisonChart } from "./VolumeInicialComparisonChart";
import type { ComparisonData } from "../shared/types";

interface VolumeInicialComparisonViewProps {
  comparison: ComparisonData;
}

export function VolumeInicialComparisonView({ comparison }: VolumeInicialComparisonViewProps) {
  const { comparison_table, chart_data, chart_config } = comparison;

  const hasTableData = comparison_table && comparison_table.length > 0;
  const hasChartData = chart_data && chart_data.labels && chart_data.labels.length > 0;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="w-full space-y-6 mt-4"
    >
      {/* Tabela */}
      {hasTableData && (
        <VolumeInicialComparisonTable data={comparison_table} />
      )}

      {/* Gráfico */}
      {hasChartData && (
        <VolumeInicialComparisonChart data={chart_data} config={chart_config} />
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
