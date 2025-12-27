"use client";

import React from "react";
import { DataTable } from "./DataTable";
import { ComparisonChart } from "./ComparisonChart";
import { DifferencesTable } from "./DifferencesTable";
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
  };
}

export function ComparisonView({ comparison }: ComparisonViewProps) {
  const { deck_1, deck_2, chart_data, differences } = comparison;

  // Debug: verificar se chart_data está presente
  React.useEffect(() => {
    if (chart_data) {
      console.log("[ComparisonView] ✅ Chart data recebido:", {
        labels: chart_data.labels?.length || 0,
        datasets: chart_data.datasets?.length || 0,
        labels_sample: chart_data.labels?.slice(0, 5),
        datasets_labels: chart_data.datasets?.map(d => d.label)
      });
    } else {
      console.log("[ComparisonView] ⚠️ Chart data não recebido");
      console.log("[ComparisonView]   Deck 1 success:", deck_1.success);
      console.log("[ComparisonView]   Deck 2 success:", deck_2.success);
      console.log("[ComparisonView]   Deck 1 data length:", deck_1.data?.length || 0);
      console.log("[ComparisonView]   Deck 2 data length:", deck_2.data?.length || 0);
    }
  }, [chart_data, deck_1.success, deck_2.success]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="w-full space-y-6 mt-4"
    >
      {/* Tabela de Diferenças (se houver) */}
      {differences && differences.length > 0 && (
        <DifferencesTable 
          differences={differences}
          deck1Name={deck_1.name}
          deck2Name={deck_2.name}
        />
      )}

      {/* Tabelas lado a lado */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4 sm:gap-6">
        <div className="min-w-0 w-full">
          {deck_1.success ? (
            <DataTable 
              data={deck_1.data} 
              title={deck_1.name}
            />
          ) : (
            <div className="bg-card border border-border rounded-lg p-4 sm:p-6">
              <h3 className="text-base sm:text-lg font-semibold mb-2 text-card-foreground">
                {deck_1.name}
              </h3>
              <p className="text-xs sm:text-sm text-destructive">
                ❌ Erro: {deck_1.error || "Erro desconhecido"}
              </p>
            </div>
          )}
        </div>
        
        <div className="min-w-0 w-full">
          {deck_2.success ? (
            <DataTable 
              data={deck_2.data} 
              title={deck_2.name}
            />
          ) : (
            <div className="bg-card border border-border rounded-lg p-4 sm:p-6">
              <h3 className="text-base sm:text-lg font-semibold mb-2 text-card-foreground">
                {deck_2.name}
              </h3>
              <p className="text-xs sm:text-sm text-destructive">
                ❌ Erro: {deck_2.error || "Erro desconhecido"}
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Gráfico comparativo - SEMPRE exibir se chart_data existir */}
      {chart_data ? (
        <div className="w-full">
          <ComparisonChart data={chart_data} />
        </div>
      ) : (
        deck_1.success && deck_2.success && (
          <div className="bg-card border border-border rounded-lg p-4 sm:p-6 w-full">
            <h3 className="text-base sm:text-lg font-semibold mb-2 text-card-foreground">
              Comparação Visual
            </h3>
            <p className="text-sm text-muted-foreground">
              ⚠️ Dados do gráfico não disponíveis. Verifique os logs do backend.
            </p>
          </div>
        )
      )}
    </motion.div>
  );
}

