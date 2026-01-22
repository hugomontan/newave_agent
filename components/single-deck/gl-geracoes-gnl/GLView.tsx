"use client";

import React from "react";
import { motion } from "framer-motion";
import { GLTable } from "./GLTable";
import { GLChart } from "./GLChart";
import type { SingleDeckVisualizationData } from "../shared/types";

interface GLViewProps {
  visualizationData: SingleDeckVisualizationData;
}

export function GLView({ visualizationData }: GLViewProps) {
  const { table, charts_by_patamar, usina } = visualizationData;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="w-full space-y-6 mt-4"
    >
      {/* Informação da usina */}
      {usina && (
        <div className="bg-card border border-border rounded-lg p-4 sm:p-6">
          <h3 className="text-base sm:text-lg font-semibold text-card-foreground mb-2">
            {usina.nome ? `${usina.nome} (Código: ${usina.codigo})` : `Usina ${usina.codigo}`}
          </h3>
        </div>
      )}

      {/* Tabela de gerações GNL */}
      {table && table.length > 0 && (
        <GLTable data={table} />
      )}

      {/* Gráficos por patamar */}
      {charts_by_patamar && Object.keys(charts_by_patamar).length > 0 && (
        <div className="space-y-6">
          {Object.entries(charts_by_patamar)
            .sort(([key1], [key2]) => {
              // Ordenar por patamar_numero: 1, 2, 3
              const num1 = charts_by_patamar[key1]?.patamar_numero || 0;
              const num2 = charts_by_patamar[key2]?.patamar_numero || 0;
              return num1 - num2;
            })
            .map(([key, patamarData]) => {
              if (!patamarData.chart_data) return null;
              
              return (
                <GLChart
                  key={key}
                  data={patamarData.chart_data}
                  title={patamarData.chart_config?.title || `Evolução da Geração - Patamar ${patamarData.patamar_numero} (${patamarData.patamar})`}
                  patamar={patamarData.patamar}
                />
              );
            })}
        </div>
      )}

      {(!table || table.length === 0) && (!charts_by_patamar || Object.keys(charts_by_patamar).length === 0) && (
        <div className="bg-card border border-border rounded-lg p-4 sm:p-6">
          <p className="text-sm text-muted-foreground">
            Nenhum dado disponível.
          </p>
        </div>
      )}
    </motion.div>
  );
}
