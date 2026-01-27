"use client";

import React from "react";
import { motion } from "framer-motion";
import { RestricoesVazaoHQComparisonTable } from "./RestricoesVazaoHQComparisonTable";
import { RestricoesVazaoHQComparisonChart } from "./RestricoesVazaoHQComparisonChart";
import type { ComparisonData } from "../shared/types";

interface RestricoesVazaoHQComparisonViewProps {
  comparison: ComparisonData;
}

export function RestricoesVazaoHQComparisonView({ comparison }: RestricoesVazaoHQComparisonViewProps) {
  const { 
    comparison_table, 
    chart_data_gmin, 
    chart_data_gmax,
    chart_config_gmin,
    chart_config_gmax,
    deck_names 
  } = comparison as any;
  
  // Validação: verificar se há dados para renderizar
  const hasTableData = comparison_table && comparison_table.length > 0;
  const hasGminChart = chart_data_gmin && chart_data_gmin.labels && chart_data_gmin.labels.length > 0 && 
                       chart_data_gmin.datasets && chart_data_gmin.datasets.length > 0;
  const hasGmaxChart = chart_data_gmax && chart_data_gmax.labels && chart_data_gmax.labels.length > 0 && 
                       chart_data_gmax.datasets && chart_data_gmax.datasets.length > 0;
  
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="w-full space-y-6 mt-4"
    >
      {/* Header com informações */}
      <div className="bg-card border border-border rounded-lg p-4 sm:p-6">
        <h3 className="text-base sm:text-lg font-semibold text-card-foreground mb-2">
          Comparação de Restrições de Vazão (VAZMIN e VAZMAX)
        </h3>
        <p className="text-sm text-muted-foreground">
          {deck_names && deck_names.length > 0 
            ? `${deck_names.length} decks comparados — VAZMIN (vazão mínima) e VAZMAX (vazão máxima) por patamar.`
            : "VAZMIN (vazão mínima) e VAZMAX (vazão máxima) por patamar."}
        </p>
      </div>

      {/* Tabela */}
      {hasTableData && (
        <RestricoesVazaoHQComparisonTable
          data={comparison_table}
        />
      )}

      {/* Gráfico VAZMIN */}
      {hasGminChart && (
        <RestricoesVazaoHQComparisonChart 
          data={chart_data_gmin} 
          config={chart_config_gmin}
        />
      )}

      {/* Gráfico VAZMAX */}
      {hasGmaxChart && (
        <RestricoesVazaoHQComparisonChart 
          data={chart_data_gmax} 
          config={chart_config_gmax}
        />
      )}
      
      {/* Mensagem se não há dados */}
      {!hasTableData && !hasGminChart && !hasGmaxChart && (
        <div className="bg-card border border-border rounded-lg p-4 sm:p-6">
          <p className="text-sm text-muted-foreground">
            Nenhum dado de restrições de vazão disponível para comparação.
          </p>
        </div>
      )}
    </motion.div>
  );
}
