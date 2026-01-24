"use client";

import React from "react";
import { motion } from "framer-motion";
import { GLComparisonTable } from "./GLComparisonTable";
import { GLComparisonChart } from "./GLComparisonChart";
import type { ComparisonData } from "../shared/types";

interface GLComparisonViewProps {
  comparison: ComparisonData;
}

export function GLComparisonView({ comparison }: GLComparisonViewProps) {
  const { comparison_table, charts_by_patamar, deck_names, usina } = comparison as any;
  
  // Validação: verificar se há dados para renderizar
  const hasTableData = comparison_table && comparison_table.length > 0;
  const hasChartsData = charts_by_patamar && Object.keys(charts_by_patamar).length > 0;
  
  // Extrair informações da usina
  const nome_usina = (usina as any)?.nome || "Usina Desconhecida";
  const codigo_usina = (usina as any)?.codigo || "N/A";
  
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="w-full space-y-6 mt-4"
    >
      {/* Header com informações */}
      <div className="bg-card border border-border rounded-lg p-4 sm:p-6">
        <h3 className="text-base sm:text-lg font-semibold text-card-foreground mb-2">
          Gerações GNL já Comandadas - {nome_usina}
        </h3>
        <p className="text-sm text-muted-foreground">
          {nome_usina && codigo_usina !== "N/A" ? (
            <>Usina: {nome_usina} (Código: {codigo_usina})</>
          ) : (
            <>Código: {codigo_usina}</>
          )}
          {deck_names && deck_names.length > 0 && (
            <> | {deck_names.length} decks comparados</>
          )}
        </p>
      </div>

      {/* Tabela */}
      {hasTableData && (
        <GLComparisonTable
          data={comparison_table}
        />
      )}

      {/* Gráficos por patamar */}
      {hasChartsData && (
        <div className="space-y-6">
          {Object.entries(charts_by_patamar).map(([patamarKey, patamarData]: [string, any]) => {
            const chartData = patamarData.chart_data;
            const chartConfig = patamarData.chart_config;
            const hasChartData = chartData && chartData.labels && chartData.labels.length > 0 && 
                               chartData.datasets && chartData.datasets.length > 0;
            
            if (!hasChartData) {
              return null;
            }
            
            return (
              <div key={patamarKey} className="space-y-2">
                <GLComparisonChart 
                  data={chartData} 
                  config={chartConfig}
                  patamar={patamarData.patamar}
                  patamarNumero={patamarData.patamar_numero}
                />
              </div>
            );
          })}
        </div>
      )}
      
      {/* Mensagem se não há dados */}
      {!hasTableData && !hasChartsData && (
        <div className="bg-card border border-border rounded-lg p-4 sm:p-6">
          <p className="text-sm text-muted-foreground">
            Nenhum dado de geração GNL disponível para comparação.
          </p>
        </div>
      )}
    </motion.div>
  );
}
