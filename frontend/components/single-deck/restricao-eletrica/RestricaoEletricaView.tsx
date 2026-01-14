"use client";

import React from "react";
import { motion } from "framer-motion";
import { RestricaoEletricaTable } from "./RestricaoEletricaTable";
import { RestricaoEletricaChart } from "./RestricaoEletricaChart";
import type { SingleDeckVisualizationData } from "../shared/types";

interface RestricaoEletricaViewProps {
  visualizationData: SingleDeckVisualizationData;
}

export function RestricaoEletricaView({ visualizationData }: RestricaoEletricaViewProps) {
  const { table, charts_by_restricao } = visualizationData;

  // Agrupar tabela por restrição
  const groupedByRestricao = React.useMemo(() => {
    if (!table || table.length === 0) return null;
    
    const grouped: Record<string, typeof table> = {};
    table.forEach((row) => {
      const restricao = row.restricao ? String(row.restricao) : "Sem nome";
      if (!grouped[restricao]) {
        grouped[restricao] = [];
      }
      grouped[restricao].push(row);
    });
    return grouped;
  }, [table]);

  if (!table || table.length === 0) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full space-y-6 mt-4"
      >
        <p className="text-sm text-muted-foreground">
          Nenhuma restrição elétrica encontrada.
        </p>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="w-full space-y-6 mt-4"
    >
      {groupedByRestricao && charts_by_restricao ? (
        // Renderizar tabela e gráfico juntos para cada restrição
        Object.entries(groupedByRestricao).map(([restricaoNome, rows]) => {
          const chartData = charts_by_restricao[restricaoNome];
          const hasChartData = chartData && chartData.labels && chartData.labels.length > 0;
          
          return (
            <div key={restricaoNome} className="space-y-4">
              <div className="space-y-2">
                <h4 className="text-lg font-semibold text-card-foreground">
                  {restricaoNome}
                </h4>
                <RestricaoEletricaTable 
                  data={rows}
                />
              </div>
              {hasChartData && (
                <RestricaoEletricaChart 
                  data={chartData}
                  restricao={restricaoNome}
                />
              )}
            </div>
          );
        })
      ) : groupedByRestricao ? (
        // Renderizar apenas tabelas agrupadas por restrição (sem gráficos)
        Object.entries(groupedByRestricao).map(([restricaoNome, rows]) => (
          <div key={restricaoNome} className="space-y-2">
            <h4 className="text-lg font-semibold text-card-foreground">
              {restricaoNome}
            </h4>
            <RestricaoEletricaTable 
              data={rows}
            />
          </div>
        ))
      ) : table && table.length > 0 ? (
        // Fallback: renderizar tabela única se não houver agrupamento
        <RestricaoEletricaTable 
          data={table}
        />
      ) : null}
    </motion.div>
  );
}
