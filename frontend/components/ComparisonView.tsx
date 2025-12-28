"use client";

import React from "react";
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

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="w-full space-y-6 mt-4"
    >
      {/* Tabela de Comparação */}
      <DifferencesTable 
        differences={differences || []}
        deck1Name={deck_1.name}
        deck2Name={deck_2.name}
      />

      {/* Gráfico Comparativo */}
      {chart_data && chart_data.labels && chart_data.labels.length > 0 && (
        <div className="w-full">
          <ComparisonChart data={chart_data} />
        </div>
      )}

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
