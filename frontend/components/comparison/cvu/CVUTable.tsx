"use client";

import React from "react";
import { Download } from "lucide-react";
import { formatNumber } from "../shared/formatters";
import { exportToCSV } from "../shared/csvExport";
import type { TableRow } from "../shared/types";

interface CVUTableProps {
  data: TableRow[];
  deck1Name: string;
  deck2Name: string;
}

export function CVUTable({ data, deck1Name, deck2Name }: CVUTableProps) {
  if (!data || data.length === 0) {
    return (
      <div className="bg-card border border-border rounded-lg p-4 sm:p-6">
        <h3 className="text-base sm:text-lg font-semibold text-card-foreground mb-2">
          Comparação de CVU
        </h3>
        <p className="text-sm text-muted-foreground">
          Nenhum dado disponível.
        </p>
      </div>
    );
  }

  const handleDownloadCSV = () => {
    const csvData = data.map((row) => {
      const ano = row.ano !== undefined && row.ano !== null 
        ? String(row.ano) 
        : (row.data ? String(row.data) : "");
      return {
        Ano: ano,
        [deck1Name]: row.deck_1 ?? row.deck_1_value ?? null,
        [deck2Name]: row.deck_2 ?? row.deck_2_value ?? null,
      };
    });
    exportToCSV(csvData, "cvu");
  };

  return (
    <div className="bg-card border border-border rounded-lg p-4 sm:p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-base sm:text-lg font-semibold text-card-foreground">
          Comparação de CVU
        </h3>
        <div className="flex items-center gap-3">
          <span className="text-sm text-muted-foreground">
            {data.length} anos
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
                  Ano
                </th>
                <th className="px-3 sm:px-4 py-3 text-right text-xs font-semibold text-blue-400 uppercase tracking-wider whitespace-nowrap">
                  {deck1Name}
                </th>
                <th className="px-3 sm:px-4 py-3 text-right text-xs font-semibold text-purple-400 uppercase tracking-wider whitespace-nowrap">
                  {deck2Name}
                </th>
              </tr>
            </thead>
            <tbody>
              {data.map((row, index) => {
                // Usar campo "ano" se disponível, senão usar "data"
                const ano = row.ano !== undefined && row.ano !== null 
                  ? String(row.ano) 
                  : (row.data ? String(row.data) : "");
                const deck1Value = row.deck_1 ?? row.deck_1_value ?? null;
                const deck2Value = row.deck_2 ?? row.deck_2_value ?? null;

                return (
                  <tr
                    key={`${ano}-${index}`}
                    className="border-b border-border/50 hover:bg-background/30 transition-colors"
                  >
                    <td className="px-3 sm:px-4 py-2.5 text-sm text-card-foreground font-medium whitespace-nowrap">
                      {ano}
                    </td>
                    <td className="px-3 sm:px-4 py-2.5 text-sm text-blue-400 text-right whitespace-nowrap font-mono">
                      {deck1Value !== null ? formatNumber(Number(deck1Value)) : "-"}
                    </td>
                    <td className="px-3 sm:px-4 py-2.5 text-sm text-purple-400 text-right whitespace-nowrap font-mono">
                      {deck2Value !== null ? formatNumber(Number(deck2Value)) : "-"}
                    </td>
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
