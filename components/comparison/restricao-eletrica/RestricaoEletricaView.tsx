"use client";

import React, { useMemo } from "react";
import { motion } from "framer-motion";
import { RestricaoEletricaTable } from "./RestricaoEletricaTable";
import { RestricaoEletricaChart } from "./RestricaoEletricaChart";
import type { ComparisonData } from "../shared/types";
import { getDeckNames } from "../shared/types";

interface RestricaoEletricaViewProps {
  comparison: ComparisonData;
}

export function RestricaoEletricaView({ comparison }: RestricaoEletricaViewProps) {
  const { deck_1, deck_2, comparison_table, charts_by_restricao, deck_displays, deck_count } = comparison;
  
  // Obter nomes de todos os decks (suporte N decks)
  const allDeckNames = getDeckNames(comparison);
  
  // Validação: verificar se há dados para renderizar
  const hasTableData = comparison_table && comparison_table.length > 0;
  const hasChartsData = charts_by_restricao && Object.keys(charts_by_restricao).length > 0;
  
  // Obter nomes dos decks para a tabela (com fallback)
  const deckNamesForTable = deck_displays || allDeckNames || 
    (deck_1 && deck_2 ? [deck_1.name, deck_2.name] : []);

  // Agrupar tabela por restrição
  const groupedByRestricao = useMemo(() => {
    if (!comparison_table || comparison_table.length === 0) return null;
    
    const grouped: Record<string, typeof comparison_table> = {};
    comparison_table.forEach((row) => {
      const restricao = row.restricao ? String(row.restricao) : "Sem nome";
      if (!grouped[restricao]) {
        grouped[restricao] = [];
      }
      grouped[restricao].push(row);
    });
    return grouped;
  }, [comparison_table]);

  if (!hasTableData && !hasChartsData) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full space-y-6 mt-4"
      >
        <p className="text-sm text-muted-foreground">
          Nenhuma restrição elétrica encontrada.
        </p>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="w-full space-y-6 mt-4"
    >
      {groupedByRestricao && charts_by_restricao ? (
        // Renderizar tabela e gráficos agrupados por restrição e patamar
        Object.entries(groupedByRestricao).map(([restricaoNome, rows]) => {
          const restricaoCharts = charts_by_restricao[restricaoNome];
          
          return (
            <div key={restricaoNome} className="space-y-4">
              <div className="space-y-2">
                <h4 className="text-lg font-semibold text-card-foreground">
                  {restricaoNome}
                </h4>
                <RestricaoEletricaTable
                  data={rows}
                  deck1Name={deck_1?.name || deckNamesForTable[0] || "Deck 1"}
                  deck2Name={deck_2?.name || deckNamesForTable[deckNamesForTable.length - 1] || "Deck 2"}
                  deckNames={deckNamesForTable}
                />
              </div>
              
              {/* Renderizar gráficos por patamar */}
              {restricaoCharts && Object.keys(restricaoCharts).length > 0 && (
                <div className="space-y-4">
                  {Object.entries(restricaoCharts).map(([patamarNome, chartData]) => (
                    <RestricaoEletricaChart
                      key={patamarNome}
                      data={chartData}
                      restricao={restricaoNome}
                      patamar={patamarNome}
                    />
                  ))}
                </div>
              )}
            </div>
          );
        })
      ) : groupedByRestricao ? (
        // Renderizar apenas tabelas agrupadas por restrição (sem gráficos)
        Object.entries(groupedByRestricao).map(([restricaoNome, rows]) => (
          <div key={restricaoNome} className="space-y-2">
            <h4 className="text-lg font-semibold text-card-foreground">
              {restricaoNome}
            </h4>
            <RestricaoEletricaTable
              data={rows}
              deck1Name={deck_1?.name || deckNamesForTable[0] || "Deck 1"}
              deck2Name={deck_2?.name || deckNamesForTable[deckNamesForTable.length - 1] || "Deck 2"}
              deckNames={deckNamesForTable}
            />
          </div>
        ))
      ) : comparison_table && comparison_table.length > 0 ? (
        // Fallback: renderizar tabela única se não houver agrupamento
        <RestricaoEletricaTable
          data={comparison_table}
          deck1Name={deck_1?.name || deckNamesForTable[0] || "Deck 1"}
          deck2Name={deck_2?.name || deckNamesForTable[deckNamesForTable.length - 1] || "Deck 2"}
          deckNames={deckNamesForTable}
        />
      ) : null}
    </motion.div>
  );
}
