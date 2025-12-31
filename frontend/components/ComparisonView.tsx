"use client";

import React from "react";
import { ComparisonChart } from "./ComparisonChart";
import { DifferencesTable } from "./DifferencesTable";
import { ExptHierarchicalView } from "./ExptHierarchicalView";
import { motion } from "framer-motion";

interface ComparisonViewProps {
  comparison: {
    deck_1: {
      name: string;
      success: boolean;
      data: Record<string, unknown>[];
      summary?: Record<string, unknown>;
      error?: string;
    };
    deck_2: {
      name: string;
      success: boolean;
      data: Record<string, unknown>[];
      summary?: Record<string, unknown>;
      error?: string;
    };
    chart_data?: {
      labels: string[];
      datasets: Array<{
        label: string;
        data: (number | null)[];
      }>;
    } | null;
    differences?: Array<{
      field: string;
      period: string;
      deck_1_value: number;
      deck_2_value: number;
      difference: number;
      difference_percent: number;
    }>;
    comparison_table?: Array<{
      data?: string | number;
      classe?: string;
      ano?: string | number;
      deck_1?: number | null;
      deck_2?: number | null;
      deck_1_value?: number | null;
      deck_2_value?: number | null;
      diferenca?: number | null;
      difference?: number | null;
      diferenca_percent?: number | null;
      difference_percent?: number | null;
    }>;
    visualization_type?: string;
    comparison_by_type?: Record<string, unknown>;
    comparison_by_usina?: Record<string, unknown>;
  };
}

export function ComparisonView({ comparison }: ComparisonViewProps) {
  const { deck_1, deck_2, chart_data, differences, comparison_table, visualization_type, comparison_by_type, comparison_by_usina } = comparison;
  
  // Verificar se é formato hierárquico do EXPT
  const isExptHierarchical = visualization_type === "expt_hierarchical" && 
                             (comparison_by_type || comparison_by_usina);
  
  // Se for formato hierárquico, usar componente específico
  if (isExptHierarchical) {
    return <ExptHierarchicalView comparison={comparison} />;
  }
  
  // Debug: verificar chart_data
  React.useEffect(() => {
    console.log("[ComparisonView] comparison completo:", comparison);
    if (chart_data) {
      console.log("[ComparisonView] chart_data recebido:", chart_data);
      console.log("[ComparisonView] labels:", chart_data.labels);
      console.log("[ComparisonView] datasets:", chart_data.datasets);
      console.log("[ComparisonView] labels.length:", chart_data.labels?.length);
      console.log("[ComparisonView] datasets.length:", chart_data.datasets?.length);
    } else {
      console.log("[ComparisonView] chart_data é null ou undefined");
    }
  }, [chart_data, comparison]);

  // Converter comparison_table para formato de differences se necessário
  const tableData = comparison_table || differences || [];
  
  // Debug: verificar comparison_table
  React.useEffect(() => {
    console.log("[ComparisonView] comparison_table:", comparison_table);
    console.log("[ComparisonView] comparison_table length:", comparison_table?.length);
    if (comparison_table && comparison_table.length > 0) {
      console.log("[ComparisonView] primeiro item comparison_table:", comparison_table[0]);
    }
  }, [comparison_table]);
  
  // Mapear comparison_table para formato de differences
  const mappedDifferences = comparison_table 
    ? comparison_table.map((row) => {
        // Priorizar "ano" se disponível (para Carga Mensal), senão usar "data" ou "classe"
        const periodValue = row.ano !== undefined ? String(row.ano) : 
                           (row.data !== undefined ? String(row.data) : 
                           (row.classe !== undefined ? String(row.classe) : ""));
        
        // Determinar o tipo baseado no formato do período
        const isCargaMensal = periodValue.includes("/") || periodValue.match(/\d{4}-\d{2}/); // Formato "Dez/2025" ou "2025-12"
        // Para Carga Adicional, usar label apropriado
        const isCargaAdicional = periodValue.includes("/") && comparison_table && comparison_table.length > 0;
        const fieldLabel = isCargaMensal || isCargaAdicional ? (isCargaAdicional ? "Carga Adicional" : "Carga Mensal") : (row.classe ? String(row.classe) : "CVU");
        
        const deck1Value = row.deck_1 ?? row.deck_1_value ?? null;
        const deck2Value = row.deck_2 ?? row.deck_2_value ?? null;
        
        return {
          field: fieldLabel,
          period: periodValue,
          deck_1_value: deck1Value !== null && deck1Value !== undefined ? Number(deck1Value) : 0,
          deck_2_value: deck2Value !== null && deck2Value !== undefined ? Number(deck2Value) : 0,
          difference: row.diferenca ?? row.difference ?? 0,
          difference_percent: row.diferenca_percent ?? row.difference_percent ?? 0,
        };
      })
    : differences || [];
  
  // Debug: verificar mappedDifferences
  React.useEffect(() => {
    console.log("[ComparisonView] mappedDifferences length:", mappedDifferences?.length);
    if (mappedDifferences && mappedDifferences.length > 0) {
      console.log("[ComparisonView] primeiro mappedDifference:", mappedDifferences[0]);
    }
  }, [mappedDifferences]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="w-full space-y-6 mt-4"
    >
      {/* Tabela de Comparação */}
      {mappedDifferences.length > 0 && (
        <DifferencesTable 
          differences={mappedDifferences}
          deck1Name={deck_1.name}
          deck2Name={deck_2.name}
        />
      )}

      {/* Gráfico Comparativo */}
      {(() => {
        const hasChartData = chart_data && chart_data.labels && chart_data.labels.length > 0 && chart_data.datasets && chart_data.datasets.length > 0;
        console.log("[ComparisonView] Renderizando gráfico - hasChartData:", hasChartData);
        console.log("[ComparisonView] chart_data:", chart_data);
        if (hasChartData) {
          return (
            <div className="w-full">
              <ComparisonChart data={chart_data} />
            </div>
          );
        }
        return null;
      })()}

      {/* Mensagem de erro se algum deck falhou */}
      {(!deck_1.success || !deck_2.success) && (
        <div className="bg-destructive/10 border border-destructive/30 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-destructive mb-2">
            Erros na comparação:
          </h3>
          {!deck_1.success && (
            <p className="text-xs text-destructive/80">
              {deck_1.name}: {deck_1.error || "Erro desconhecido"}
            </p>
          )}
          {!deck_2.success && (
            <p className="text-xs text-destructive/80">
              {deck_2.name}: {deck_2.error || "Erro desconhecido"}
            </p>
          )}
        </div>
      )}
    </motion.div>
  );
}
