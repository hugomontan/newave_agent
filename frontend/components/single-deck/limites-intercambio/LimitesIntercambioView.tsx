"use client";

import React from "react";
import { motion } from "framer-motion";
import { LimitesIntercambioTable } from "./LimitesIntercambioTable";
import { LimitesIntercambioChart } from "./LimitesIntercambioChart";
import type { SingleDeckVisualizationData } from "../shared/types";

interface LimitesIntercambioViewProps {
  visualizationData: SingleDeckVisualizationData;
}

export function LimitesIntercambioView({ visualizationData }: LimitesIntercambioViewProps) {
  const { table, charts_by_par } = visualizationData;

  // Agrupar por par_key se existir (igual ao multi-deck)
  const groupedByPar = React.useMemo(() => {
    if (!table || table.length === 0) return null;
    if (!table[0]?.par_key) return null;
    
    const grouped: Record<string, { par: string; sentido: string; rows: typeof table }> = {};
    table.forEach((row) => {
      const key = row.par_key!;
      if (!grouped[key]) {
        grouped[key] = {
          par: row.par || "",
          sentido: row.sentido || "",
          rows: []
        };
      }
      grouped[key].rows.push(row);
    });
    return grouped;
  }, [table]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="w-full space-y-6 mt-4"
    >
      {groupedByPar && charts_by_par ? (
        // Renderizar tabela e gráfico juntos para cada par (igual ao multi-deck)
        Object.entries(groupedByPar).map(([key, group]) => {
          const parChart = charts_by_par[key];
          const hasChartData = parChart && parChart.chart_data && parChart.chart_data.labels && parChart.chart_data.labels.length > 0;
          
          return (
            <div key={key} className="space-y-4">
              <div className="space-y-2">
                <h4 className="text-lg font-semibold text-card-foreground">
                  {group.par} - {group.sentido}
                </h4>
                <LimitesIntercambioTable 
                  data={group.rows}
                />
              </div>
              {hasChartData && parChart.chart_data && (
                <LimitesIntercambioChart 
                  data={parChart.chart_data} 
                  par={group.par}
                  sentido={group.sentido}
                />
              )}
            </div>
          );
        })
      ) : groupedByPar ? (
        // Renderizar apenas tabelas agrupadas por par (sem gráficos por par)
        Object.entries(groupedByPar).map(([key, group]) => (
          <div key={key} className="space-y-2">
            <h4 className="text-lg font-semibold text-card-foreground">
              {group.par} - {group.sentido}
            </h4>
            <LimitesIntercambioTable 
              data={group.rows}
            />
          </div>
        ))
      ) : table && table.length > 0 ? (
        // Fallback: renderizar tabela única se não houver agrupamento
        <LimitesIntercambioTable 
          data={table}
        />
      ) : null}
    </motion.div>
  );
}
