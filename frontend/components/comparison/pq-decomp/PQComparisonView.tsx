"use client";

import React from "react";
import { motion } from "framer-motion";
import { PQComparisonTable } from "./PQComparisonTable";
import { PQComparisonChart } from "./PQComparisonChart";
import type { ComparisonData } from "../shared/types";

interface PQComparisonViewProps {
  comparison: ComparisonData;
}

export function PQComparisonView({ comparison }: PQComparisonViewProps) {
  // IMPORTANTE: Usar tipo_encontrado (tipo REAL nos dados) em vez de tipo_filtrado (tipo da query)
  const { comparison_table, chart_data, chart_config, deck_names, tipos, tipo_filtrado, tipo_encontrado } = comparison as any;
  const tipo_para_exibir = tipo_encontrado || tipo_filtrado;  // Priorizar tipo REAL encontrado
  
  // Validação: verificar se há dados para renderizar
  const hasTableData = comparison_table && comparison_table.length > 0;
  const hasChartData = chart_data && chart_data.labels && chart_data.labels.length > 0 && 
                       chart_data.datasets && chart_data.datasets.length > 0;
  
  // Título dinâmico baseado no tipo encontrado REAL
  const titulo = tipo_para_exibir 
    ? `Geração Média Ponderada (MW Médio) - ${tipo_para_exibir}`
    : "Geração Média Ponderada (MW Médio) por Tipo de Geração";
  
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="w-full space-y-6 mt-4"
    >
      {/* Header com informações */}
      <div className="bg-card border border-border rounded-lg p-4 sm:p-6">
        <h3 className="text-base sm:text-lg font-semibold text-card-foreground mb-2">
          {titulo}
        </h3>
        <p className="text-sm text-muted-foreground">
          {deck_names && deck_names.length > 0 ? `${deck_names.length} decks comparados` : ""}
          {tipo_para_exibir && (
            <span className="ml-2 px-2 py-0.5 bg-primary/10 text-primary rounded-md text-xs font-medium">
              {tipo_para_exibir}
            </span>
          )}
          {!tipo_para_exibir && tipos && tipos.length > 0 && (
            <> | Tipos: {tipos.map((t: { tipo: string }) => t.tipo).join(", ")}</>
          )}
        </p>
      </div>

      {/* Tabela */}
      {hasTableData && (
        <PQComparisonTable
          data={comparison_table}
          tipos={tipos as Array<{ tipo: string }>}
        />
      )}

      {/* Gráfico */}
      {hasChartData && (
        <PQComparisonChart 
          data={chart_data} 
          config={chart_config}
        />
      )}
      
      {/* Mensagem se não há dados */}
      {!hasTableData && !hasChartData && (
        <div className="bg-card border border-border rounded-lg p-4 sm:p-6">
          <p className="text-sm text-muted-foreground">
            Nenhum dado de geração média ponderada disponível para comparação.
          </p>
        </div>
      )}
    </motion.div>
  );
}
