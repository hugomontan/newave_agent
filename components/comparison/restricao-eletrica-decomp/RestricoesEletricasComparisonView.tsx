"use client";

import React from "react";
import { motion } from "framer-motion";
import { RestricoesEletricasComparisonTable } from "./RestricoesEletricasComparisonTable";
import { RestricoesEletricasComparisonChart } from "./RestricoesEletricasComparisonChart";
import type { ComparisonData } from "../shared/types";

interface RestricoesEletricasComparisonViewProps {
  comparison: ComparisonData;
}

export function RestricoesEletricasComparisonView({ comparison }: RestricoesEletricasComparisonViewProps) {
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
          Comparação de Restrições Elétricas
        </h3>
        <p className="text-sm text-muted-foreground">
          {deck_names && deck_names.length > 0 ? `${deck_names.length} decks comparados` : ""}
        </p>
      </div>

      {/* Tabela */}
      {hasTableData && (
        <RestricoesEletricasComparisonTable
          data={comparison_table}
        />
      )}

      {/* Gráfico GMIN */}
      {hasGminChart && (
        <RestricoesEletricasComparisonChart 
          data={chart_data_gmin} 
          config={chart_config_gmin}
        />
      )}

      {/* Gráfico GMAX */}
      {hasGmaxChart && (
        <RestricoesEletricasComparisonChart 
          data={chart_data_gmax} 
          config={chart_config_gmax}
        />
      )}
      
      {/* Mensagem se não há dados */}
      {!hasTableData && !hasGminChart && !hasGmaxChart && (
        <div className="bg-card border border-border rounded-lg p-4 sm:p-6">
          <p className="text-sm text-muted-foreground">
            Nenhum dado de restrições elétricas disponível para comparação.
          </p>
        </div>
      )}
    </motion.div>
  );
}
