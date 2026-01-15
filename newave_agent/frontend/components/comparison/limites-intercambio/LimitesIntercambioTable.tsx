"use client";

import React, { useState } from "react";
import { Download } from "lucide-react";
import { formatNumber } from "../shared/formatters";
import { exportToCSV } from "../shared/csvExport";
import type { TableRow } from "../shared/types";

const INITIAL_ROWS = 10;

interface LimitesIntercambioTableProps {
  data: TableRow[];
  deck1Name: string;
  deck2Name: string;
  deckNames?: string[]; // Suporte para N decks
}

export function LimitesIntercambioTable({ data, deck1Name, deck2Name, deckNames }: LimitesIntercambioTableProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  
  // Determinar quais decks usar (suporte N decks)
  const allDeckNames = deckNames && deckNames.length > 0 ? deckNames : [deck1Name, deck2Name];
  
  // Verificar quantos decks estão presentes nos dados
  const detectDeckCount = () => {
    if (!data || data.length === 0) return allDeckNames.length;
    const firstRow = data[0];
    if (!firstRow) return allDeckNames.length;
    
    // Contar colunas deck_N nos dados
    let maxDeckIndex = 0;
    for (const key in firstRow) {
      if (key.startsWith('deck_')) {
        const match = key.match(/^deck_(\d+)$/);
        if (match) {
          const deckIndex = parseInt(match[1]);
          if (deckIndex > maxDeckIndex) {
            maxDeckIndex = deckIndex;
          }
        }
      }
    }
    
    // Se encontrou colunas deck_N, usar o máximo encontrado
    if (maxDeckIndex > 0) {
      return Math.max(maxDeckIndex, allDeckNames.length);
    }
    
    return allDeckNames.length;
  };
  
  const deckCount = detectDeckCount();
  const deckNamesToUse = allDeckNames.slice(0, deckCount);
  
  if (!data || data.length === 0) {
    return null;
  }

  const hasMoreRows = data.length > INITIAL_ROWS;
  const displayedData = isExpanded ? data : data.slice(0, INITIAL_ROWS);

  const handleDownloadCSV = () => {
    const csvData = data.map((row) => {
      const csvRow: Record<string, any> = {
        Período: row.data ? String(row.data) : "",
      };
      
      // Adicionar colunas para todos os decks
      deckNamesToUse.forEach((name, index) => {
        const deckKey = `deck_${index + 1}` as keyof TableRow;
        csvRow[name] = (row[deckKey] as number | null) ?? null;
      });
      
      return csvRow;
    });
    exportToCSV(csvData, "limites_intercambio");
  };

  return (
    <div className="bg-card border border-border rounded-lg p-4 sm:p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-base sm:text-lg font-semibold text-card-foreground">
          Limites de Intercâmbio
        </h3>
        <div className="flex items-center gap-3">
          <span className="text-sm text-muted-foreground">
            {data.length} registros
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
                {deckNamesToUse.map((name, index) => {
                  const colors = ["text-blue-400", "text-purple-400", "text-green-400", "text-yellow-400", "text-pink-400", "text-cyan-400", "text-orange-400", "text-indigo-400", "text-red-400", "text-teal-400", "text-lime-400", "text-amber-400"];
                  return (
                    <th 
                      key={name}
                      className={`px-3 sm:px-4 py-3 text-right text-xs font-semibold ${colors[index % colors.length]} uppercase tracking-wider whitespace-nowrap`}
                    >
                      {name}
                    </th>
                  );
                })}
              </tr>
            </thead>
            <tbody>
              {displayedData.map((row, index) => {
                const periodo = row.data ? String(row.data) : "";

                return (
                  <tr
                    key={`${periodo}-${index}`}
                    className="border-b border-border/50 hover:bg-background/30 transition-colors"
                  >
                    <td className="px-3 sm:px-4 py-2.5 text-sm text-card-foreground font-medium whitespace-nowrap">
                      {periodo}
                    </td>
                    {deckNamesToUse.map((name, deckIndex) => {
                      const deckKey = `deck_${deckIndex + 1}` as keyof TableRow;
                      const value = (row[deckKey] as number | null) ?? null;
                      const colors = ["text-blue-400", "text-purple-400", "text-green-400", "text-yellow-400", "text-pink-400", "text-cyan-400", "text-orange-400", "text-indigo-400", "text-red-400", "text-teal-400", "text-lime-400", "text-amber-400"];
                      return (
                        <td 
                          key={name}
                          className={`px-3 sm:px-4 py-2.5 text-sm ${colors[deckIndex % colors.length]} text-right whitespace-nowrap font-mono`}
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

      {hasMoreRows && (
        <div className="mt-4 flex justify-center">
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="px-4 py-2 text-sm font-medium text-card-foreground bg-background/50 hover:bg-background/70 border border-border rounded-lg transition-colors"
          >
            {isExpanded 
              ? `Mostrar menos (${INITIAL_ROWS} primeiros)` 
              : `Mostrar todos (${data.length - INITIAL_ROWS} restantes)`}
          </button>
        </div>
      )}
    </div>
  );
}
