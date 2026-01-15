"use client";

import React, { useMemo } from "react";
import { Download } from "lucide-react";
import { formatNumber } from "../shared/formatters";
import { exportToCSV } from "../shared/csvExport";
import type { TableRow } from "../shared/types";

// Cores para as colunas de decks (expandido para suportar até 12 decks)
const DECK_COLORS = [
  "text-blue-400",
  "text-purple-400",
  "text-green-400",
  "text-orange-400",
  "text-cyan-400",
  "text-pink-400",
  "text-emerald-400",
  "text-sky-400",
  "text-violet-400",
  "text-red-400",
  "text-slate-400",
  "text-amber-400",
];

interface UsinasNaoSimuladasTableProps {
  data: TableRow[];
  deck1Name: string;
  deck2Name: string;
  deckNames?: string[]; // Novos: nomes de todos os decks para N-deck support
}

export function UsinasNaoSimuladasTable({ data, deck1Name, deck2Name, deckNames }: UsinasNaoSimuladasTableProps) {
  // Detectar quantos decks estão presentes nos dados
  const deckCount = useMemo(() => {
    if (deckNames && deckNames.length > 0) {
      return deckNames.length;
    }
    if (!data || data.length === 0) return 2;
    
    // Contar colunas deck_N nos dados
    const firstRow = data[0];
    let count = 0;
    for (let i = 1; i <= 12; i++) {
      if (`deck_${i}` in firstRow || (i === 1 && 'deck_1' in firstRow) || (i === 2 && 'deck_2' in firstRow)) {
        count = i;
      } else if (i > 2) {
        break;
      }
    }
    return Math.max(count, 2);
  }, [data, deckNames]);

  // Obter lista de nomes dos decks
  const allDeckNames = useMemo(() => {
    if (deckNames && deckNames.length > 0) {
      return deckNames;
    }
    return [deck1Name, deck2Name];
  }, [deckNames, deck1Name, deck2Name]);

  const isHistorical = deckCount > 2;
  const title = isHistorical ? "Evolução Histórica de Geração de Usinas Não Simuladas" : "Comparação de Geração de Usinas Não Simuladas";

  if (!data || data.length === 0) {
    return (
      <div className="bg-card border border-border rounded-lg p-4 sm:p-6">
        <h3 className="text-base sm:text-lg font-semibold text-card-foreground mb-2">
          {title}
        </h3>
        <p className="text-sm text-muted-foreground">
          Nenhum dado disponível.
        </p>
      </div>
    );
  }

  const handleDownloadCSV = () => {
    const csvData = data.map((row) => {
      const periodo = row.periodo !== undefined && row.periodo !== null 
        ? String(row.periodo) 
        : (row.ano ? String(row.ano) : "");
      
      const result: Record<string, string | number | null> = { Período: periodo };
      
      for (let i = 0; i < allDeckNames.length; i++) {
        const deckKey = `deck_${i + 1}` as keyof TableRow;
        result[allDeckNames[i]] = (row[deckKey] as number | null) ?? null;
      }
      
      return result;
    });
    exportToCSV(csvData, "usinas-nao-simuladas");
  };

  return (
    <div className="bg-card border border-border rounded-lg p-4 sm:p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-base sm:text-lg font-semibold text-card-foreground">
          {title}
          {isHistorical && (
            <span className="ml-2 text-xs font-normal text-muted-foreground">
              ({deckCount} decks)
            </span>
          )}
        </h3>
        <div className="flex items-center gap-3">
          <span className="text-sm text-muted-foreground">
            {data.length} períodos
          </span>
          <button
            onClick={handleDownloadCSV}
            className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-card-foreground bg-background/50 hover:bg-background/70 border border-border rounded-lg transition-colors"
            title="Baixar como CSV"
          >
            <Download className="w-4 h-4" />
            CSV
          </button>
        </div>
      </div>

      <div className="overflow-x-auto -mx-4 sm:mx-0">
        <div className="inline-block min-w-full align-middle px-4 sm:px-0">
          <table className="min-w-full border-collapse">
            <thead>
              <tr className="border-b border-border bg-background/50">
                <th className="px-3 sm:px-4 py-3 text-left text-xs font-semibold text-card-foreground uppercase tracking-wider whitespace-nowrap">
                  Período
                </th>
                {allDeckNames.map((name, index) => (
                  <th 
                    key={name}
                    className={`px-3 sm:px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider whitespace-nowrap ${DECK_COLORS[index % DECK_COLORS.length]}`}
                  >
                    {name}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.map((row, rowIndex) => {
                // Usar campo "periodo" se disponível, senão usar "ano"
                const periodo = row.periodo !== undefined && row.periodo !== null 
                  ? String(row.periodo) 
                  : (row.ano ? String(row.ano) : "");

                return (
                  <tr
                    key={`${periodo}-${rowIndex}`}
                    className="border-b border-border/50 hover:bg-background/30 transition-colors"
                  >
                    <td className="px-3 sm:px-4 py-2.5 text-sm text-card-foreground font-medium whitespace-nowrap">
                      {periodo}
                    </td>
                    {allDeckNames.map((name, deckIndex) => {
                      const deckKey = `deck_${deckIndex + 1}` as keyof TableRow;
                      const value = (row[deckKey] as number | null) ?? null;

                      return (
                        <td 
                          key={name}
                          className={`px-3 sm:px-4 py-2.5 text-sm text-right whitespace-nowrap font-mono ${DECK_COLORS[deckIndex % DECK_COLORS.length]}`}
                        >
                          {value !== null ? formatNumber(Number(value)) : "-"}
                        </td>
                      );
                    })}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
