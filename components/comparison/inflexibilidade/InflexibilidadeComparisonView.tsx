"use client";

import React from "react";
import { motion } from "framer-motion";
import { InflexibilidadeComparisonTable } from "./InflexibilidadeComparisonTable";
import { InflexibilidadeComparisonChart } from "./InflexibilidadeComparisonChart";
import type { ComparisonData } from "../shared/types";

interface InflexibilidadeComparisonViewProps {
  comparison: ComparisonData;
}

export function InflexibilidadeComparisonView({ comparison }: InflexibilidadeComparisonViewProps) {
  const { comparison_table, chart_data, chart_config, deck_names } = comparison;
  
  // Validação: verificar se há dados para renderizar
  const hasTableData = comparison_table && comparison_table.length > 0;
  const hasChartData = chart_data && chart_data.labels && chart_data.labels.length > 0 && 
                       chart_data.datasets && chart_data.datasets.length > 0;
  
  // Extrair informações da usina (do primeiro registro da tabela)
  const usinaInfo = hasTableData && comparison_table[0] 
    ? {
        nome: (comparison_table[0] as any).usina_nome || "Usina Desconhecida",
        codigo: (comparison_table[0] as any).usina_codigo || "N/A"
      }
    : null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="w-full space-y-6 mt-4"
    >
      {/* Header com informações da usina */}
      {usinaInfo && (
        <div className="bg-card border border-border rounded-lg p-4 sm:p-6">
          <h3 className="text-base sm:text-lg font-semibold text-card-foreground mb-2">
            Inflexibilidade Total - {usinaInfo.nome}
          </h3>
          <p className="text-sm text-muted-foreground">
            Código: {usinaInfo.codigo} | {deck_names && deck_names.length > 0 ? `${deck_names.length} decks comparados` : ""}
          </p>
        </div>
      )}

      {/* Tabela */}
      {hasTableData && (
        <InflexibilidadeComparisonTable
          data={comparison_table}
          deckNames={deck_names || []}
        />
      )}

      {/* Gráfico */}
      {hasChartData && (
        <InflexibilidadeComparisonChart 
          data={chart_data} 
          config={chart_config}
        />
      )}
      
      {/* Mensagem se não há dados */}
      {!hasTableData && !hasChartData && (
        <div className="bg-card border border-border rounded-lg p-4 sm:p-6">
          <p className="text-sm text-muted-foreground">
            Nenhum dado de inflexibilidade disponível para comparação.
          </p>
        </div>
      )}
    </motion.div>
  );
}
