"use client";

import React from "react";
import { motion } from "framer-motion";
import { LimitesIntercambioTable } from "./LimitesIntercambioTable";
import { LimitesIntercambioChart } from "./LimitesIntercambioChart";
import type { ComparisonData, TableRow } from "../shared/types";
import { getDeckNames } from "../shared/types";

interface LimitesIntercambioViewProps {
  comparison: ComparisonData;
}

export function LimitesIntercambioView({ comparison }: LimitesIntercambioViewProps) {
  const { deck_1, deck_2, comparison_table, charts_by_par, deck_displays, deck_count } = comparison as any;
  
  // Obter nomes de todos os decks (suporte N decks)
  const allDeckNames = getDeckNames(comparison);

  // Agrupar por par_key se existir
  const groupedByPar = React.useMemo(() => {
    if (!comparison_table || comparison_table.length === 0) return null;
    if (!comparison_table[0]?.par_key) return null;
    
    const grouped: Record<string, { par: string; sentido: string; rows: TableRow[] }> = {};
    comparison_table.forEach((row: TableRow) => {
      const key = row.par_key!;
      if (!grouped[key]) {
        grouped[key] = {
          par: row.par || "",
          sentido: row.sentido || "",
          rows: []
        };
      }
      grouped[key].rows.push(row);
    });
    return grouped;
  }, [comparison_table]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="w-full space-y-6 mt-4"
    >
      {groupedByPar && charts_by_par ? (
        // Renderizar tabela e gráfico juntos para cada par
        Object.entries(groupedByPar).map(([key, group]) => {
          const parChart = charts_by_par[key];
          const hasChartData = parChart && parChart.chart_data && parChart.chart_data.labels && parChart.chart_data.labels.length > 0;
          
          return (
            <div key={key} className="space-y-4">
              <div className="space-y-2">
                <h4 className="text-lg font-semibold text-card-foreground">
                  {group.par} - {group.sentido}
                </h4>
                <LimitesIntercambioTable 
                  data={group.rows}
                  deck1Name={deck_1?.name || allDeckNames[0] || "Deck 1"}
                  deck2Name={deck_2?.name || allDeckNames[allDeckNames.length - 1] || "Deck 2"}
                  deckNames={allDeckNames}
                />
              </div>
              {hasChartData && parChart.chart_data && (
                <LimitesIntercambioChart 
                  data={parChart.chart_data} 
                  par={group.par}
                  sentido={group.sentido}
                />
              )}
            </div>
          );
        })
      ) : groupedByPar ? (
        // Renderizar apenas tabelas agrupadas por par (sem gráficos por par)
        Object.entries(groupedByPar).map(([key, group]) => (
          <div key={key} className="space-y-2">
            <h4 className="text-lg font-semibold text-card-foreground">
              {group.par} - {group.sentido}
            </h4>
            <LimitesIntercambioTable 
              data={group.rows}
              deck1Name={deck_1?.name || allDeckNames[0] || "Deck 1"}
              deck2Name={deck_2?.name || allDeckNames[allDeckNames.length - 1] || "Deck 2"}
              deckNames={allDeckNames}
            />
          </div>
        ))
      ) : comparison_table && comparison_table.length > 0 ? (
        // Fallback: renderizar tabela única se não houver agrupamento
        <LimitesIntercambioTable 
          data={comparison_table}
          deck1Name={deck_1?.name || allDeckNames[0] || "Deck 1"}
          deck2Name={deck_2?.name || allDeckNames[allDeckNames.length - 1] || "Deck 2"}
          deckNames={allDeckNames}
        />
      ) : null}

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
