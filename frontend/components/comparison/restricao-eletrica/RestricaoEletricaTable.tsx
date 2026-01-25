"use client";

import React, { useState, useMemo } from "react";
import { Download, ChevronDown, ChevronUp } from "lucide-react";
import { formatInteger } from "../shared/formatters";
import { exportToCSV } from "../shared/csvExport";
import type { TableRow } from "../shared/types";

const INITIAL_ROWS = 10;

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

interface RestricaoEletricaTableProps {
  data: TableRow[];
  deck1Name: string;
  deck2Name: string;
  deckNames?: string[]; // Novos: nomes de todos os decks para N-deck support
}

export function RestricaoEletricaTable({ data, deck1Name, deck2Name, deckNames }: RestricaoEletricaTableProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  
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
      if (`deck_${i}` in firstRow) {
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
  
  if (!data || data.length === 0) {
    return null;
  }

  const hasMoreRows = data.length > INITIAL_ROWS;
  const displayedData = isExpanded ? data : data.slice(0, INITIAL_ROWS);

  const handleDownloadCSV = () => {
    const csvData = data.map((row) => {
      const rowData = row as any;
      const result: Record<string, string | number | null> = {
        Restrição: rowData.restricao ? String(rowData.restricao) : "",
        Patamar: rowData.patamar ? String(rowData.patamar) : "",
        Período: rowData.periodo ? String(rowData.periodo) : "",
      };
      
      for (let i = 0; i < allDeckNames.length; i++) {
        const deckKey = `deck_${i + 1}`;
        result[allDeckNames[i]] = (rowData[deckKey] as number | null) ?? null;
      }
      
      return result;
    });
    exportToCSV(csvData, "restricoes-eletricas");
  };

  return (
    <div className="bg-card border border-border rounded-lg p-4 sm:p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <span className="text-sm text-muted-foreground">
            {data.length} registros
          </span>
        </div>
        <button
          onClick={handleDownloadCSV}
          className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-card-foreground bg-background/50 hover:bg-background/70 border border-border rounded-lg transition-colors"
          title="Baixar como CSV"
        >
          <Download className="w-4 h-4" />
          CSV
        </button>
      </div>

      <div className="overflow-x-auto -mx-4 sm:mx-0">
        <div className="inline-block min-w-full align-middle px-4 sm:px-0">
          <table className="min-w-full border-collapse">
            <thead>
              <tr className="border-b border-border bg-background/50">
                <th className="px-3 sm:px-4 py-3 text-left text-xs font-semibold text-card-foreground uppercase tracking-wider whitespace-nowrap">
                  Restrição
                </th>
                <th className="px-3 sm:px-4 py-3 text-left text-xs font-semibold text-card-foreground uppercase tracking-wider whitespace-nowrap">
                  Patamar
                </th>
                <th className="px-3 sm:px-4 py-3 text-left text-xs font-semibold text-card-foreground uppercase tracking-wider whitespace-nowrap">
                  Período
                </th>
                {allDeckNames.map((deckName, index) => (
                  <th
                    key={deckName}
                    className={`px-3 sm:px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider whitespace-nowrap ${DECK_COLORS[index % DECK_COLORS.length]}`}
                  >
                    {deckName} (MW)
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {displayedData.map((row, index) => {
                const rowData = row as any;
                const restricao = rowData.restricao ? String(rowData.restricao) : "";
                const patamar = rowData.patamar ? String(rowData.patamar) : "";
                const periodo = rowData.periodo ? String(rowData.periodo) : "";

                return (
                  <tr
                    key={`${restricao}-${patamar}-${periodo}-${index}`}
                    className="border-b border-border/50 hover:bg-background/30 transition-colors"
                  >
                    <td className="px-3 sm:px-4 py-2.5 text-sm text-card-foreground font-medium whitespace-nowrap">
                      {restricao}
                    </td>
                    <td className="px-3 sm:px-4 py-2.5 text-sm text-card-foreground whitespace-nowrap">
                      {patamar}
                    </td>
                    <td className="px-3 sm:px-4 py-2.5 text-sm text-card-foreground whitespace-nowrap">
                      {periodo}
                    </td>
                    {allDeckNames.map((deckName, deckIdx) => {
                      const deckKey = `deck_${deckIdx + 1}`;
                      const value = (rowData[deckKey] as number | null) ?? null;
                      return (
                        <td
                          key={deckName}
                          className={`px-3 sm:px-4 py-2.5 text-sm text-right whitespace-nowrap font-mono ${DECK_COLORS[deckIdx % DECK_COLORS.length]}`}
                        >
                          {value !== null ? formatInteger(value) : "-"}
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

      {hasMoreRows && (
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="mt-4 flex items-center gap-2 text-sm text-muted-foreground hover:text-card-foreground transition-colors"
        >
          {isExpanded ? (
            <>
              <ChevronUp className="w-4 h-4" />
              Mostrar menos
            </>
          ) : (
            <>
              <ChevronDown className="w-4 h-4" />
              Mostrar mais ({data.length - INITIAL_ROWS} registros)
            </>
          )}
        </button>
      )}
    </div>
  );
}
