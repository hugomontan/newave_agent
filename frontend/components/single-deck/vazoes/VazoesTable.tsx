"use client";

import React from "react";
import { Download } from "lucide-react";
import { formatNumber } from "../shared/formatters";
import { exportToCSV } from "../shared/csvExport";
import type { TableRow } from "../shared/types";

interface VazoesTableProps {
  data: TableRow[];
}

export function VazoesTable({ data }: VazoesTableProps) {
  if (!data || data.length === 0) {
    return (
      <div className="bg-card border border-border rounded-lg p-4 sm:p-6">
        <h3 className="text-base sm:text-lg font-semibold text-card-foreground mb-2">
          Vazões Históricas
        </h3>
        <p className="text-sm text-muted-foreground">Nenhum dado disponível.</p>
      </div>
    );
  }

  const handleDownloadCSV = () => {
    const csvData = data.map((row) => ({
      Período: row.periodo_display || row.periodo || "",
      "Vazão (m³/s)": row.valor ?? null,
    }));
    exportToCSV(csvData, "vazoes");
  };

  return (
    <div className="bg-card border border-border rounded-lg p-4 sm:p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-base sm:text-lg font-semibold text-card-foreground">
          Vazões Históricas
        </h3>
        <div className="flex items-center gap-3">
          <span className="text-sm text-muted-foreground">{data.length} registros</span>
          <button
            onClick={handleDownloadCSV}
            className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-card-foreground bg-background/50 hover:bg-background/70 border border-border rounded-lg transition-colors"
          >
            <Download className="w-4 h-4" />
            CSV
          </button>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full border-collapse">
          <thead>
            <tr className="border-b border-border bg-background/50">
              <th className="px-4 py-3 text-left text-xs font-semibold text-card-foreground uppercase">
                Período
              </th>
              <th className="px-4 py-3 text-right text-xs font-semibold text-card-foreground uppercase">
                Vazão (m³/s)
              </th>
            </tr>
          </thead>
          <tbody>
            {data.map((row, index) => (
              <tr
                key={`${row.periodo}-${index}`}
                className="border-b border-border/50 hover:bg-background/30"
              >
                <td className="px-4 py-2.5 text-sm text-card-foreground">
                  {row.periodo_display || row.periodo || "-"}
                </td>
                <td className="px-4 py-2.5 text-sm text-card-foreground text-right font-mono">
                  {formatNumber(row.valor as number)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
