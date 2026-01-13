"use client";

import React, { useState } from "react";
import { Download } from "lucide-react";
import { formatNumber } from "../shared/formatters";
import { exportToCSV } from "../shared/csvExport";
import type { TableRow, Difference } from "../shared/types";

// Configuração de tamanhos das mensagens (pode ser ajustado para testar)
const MESSAGE_SIZES = {
  emptyMessage: "text-base"
} as const;

const INITIAL_ROWS = 10;

interface VazaoMinimaGroupedTableProps {
  differences: Difference[];
  deck1Name: string;
  deck2Name: string;
  firstColumnLabel?: string;
}

export function VazaoMinimaGroupedTable({ differences, deck1Name, deck2Name, firstColumnLabel = "Usina" }: VazaoMinimaGroupedTableProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  
  if (!differences || differences.length === 0) {
    return (
      <div className="bg-card border border-border rounded-lg p-4 sm:p-6">
        <h3 className="text-base sm:text-lg font-semibold text-card-foreground mb-2">
          Mudanças de Vazão Mínima
        </h3>
        <p className={`${MESSAGE_SIZES.emptyMessage} text-muted-foreground`}>
          Não houveram mudanças registradas do deck {deck1Name} para o deck {deck2Name}.
        </p>
      </div>
    );
  }

  const hasMoreRows = differences.length > INITIAL_ROWS;
  const displayedData = isExpanded ? differences : differences.slice(0, INITIAL_ROWS);
  
  // Verificar se alguma linha tem periodo_coluna para mostrar a coluna consistentemente
  const showPeriodoColumn = differences.some(d => d.periodo_coluna);

  const handleDownloadCSV = () => {
    const csvData = differences.map((diff) => {
      const row: Record<string, string | number | null> = {};
      // Período primeiro (se houver)
      if (showPeriodoColumn) {
        row.Período = diff.periodo_coluna || null;
      }
      // Depois Usina
      row[firstColumnLabel] = diff.period;
      // Depois valores
      row[deck1Name] = diff.deck_1_value ?? null;
      row[deck2Name] = diff.deck_2_value ?? null;
      return row;
    });
    exportToCSV(csvData, "vazao_minima");
  };

  return (
    <div className="bg-card border border-border rounded-lg p-4 sm:p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-base sm:text-lg font-semibold text-card-foreground">
          Mudanças de Vazão Mínima
        </h3>
        <div className="flex items-center gap-3">
          <span className="text-sm text-muted-foreground">
            {differences.length} registros
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
          <table className="min-w-full border-collapse table-fixed">
            <thead>
              <tr className="border-b border-border bg-background/50">
                {showPeriodoColumn && (
                  <th className="w-1/5 px-3 sm:px-4 py-3 text-left text-xs font-semibold text-card-foreground uppercase tracking-wider">
                    Período
                  </th>
                )}
                <th className={`${showPeriodoColumn ? "w-1/5" : "w-1/4"} px-3 sm:px-4 py-3 text-left text-xs font-semibold text-card-foreground uppercase tracking-wider`}>
                  {firstColumnLabel}
                </th>
                <th className={`${showPeriodoColumn ? "w-1/5" : "w-1/4"} px-3 sm:px-4 py-3 text-right text-xs font-semibold text-blue-400 uppercase tracking-wider`}>
                  {deck1Name}
                </th>
                <th className={`${showPeriodoColumn ? "w-1/5" : "w-1/4"} px-3 sm:px-4 py-3 text-right text-xs font-semibold text-purple-400 uppercase tracking-wider`}>
                  {deck2Name}
                </th>
              </tr>
            </thead>
            <tbody>
              {displayedData.map((diff, index) => (
                <tr
                  key={`${diff.period}-${index}`}
                  className="border-b border-border/50 hover:bg-background/30 transition-colors"
                >
                  {showPeriodoColumn && (
                    <td className="px-3 sm:px-4 py-2.5 text-sm text-muted-foreground font-medium truncate" title={diff.periodo_coluna || "-"}>
                      {diff.periodo_coluna || "-"}
                    </td>
                  )}
                  <td className="px-3 sm:px-4 py-2.5 text-sm text-card-foreground font-medium truncate" title={diff.period}>
                    {diff.period}
                  </td>
                  <td className="px-3 sm:px-4 py-2.5 text-sm text-blue-400 text-right font-mono">
                    {formatNumber(diff.deck_1_value)} <span className="text-xs text-muted-foreground ml-1">m³/s</span>
                  </td>
                  <td className="px-3 sm:px-4 py-2.5 text-sm text-purple-400 text-right font-mono">
                    {formatNumber(diff.deck_2_value)} <span className="text-xs text-muted-foreground ml-1">m³/s</span>
                  </td>
                </tr>
              ))}
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
              : `Mostrar todos (${differences.length - INITIAL_ROWS} restantes)`}
          </button>
        </div>
      )}
    </div>
  );
}
