"use client";

import React, { useState } from "react";
import { Download, ChevronDown, ChevronUp } from "lucide-react";
import { formatNumber } from "../shared/formatters";
import { exportToCSV } from "../shared/csvExport";
import type { TableRow } from "../shared/types";

interface DsvaguaTableProps {
  data: TableRow[];
}

export function DsvaguaTable({ data }: DsvaguaTableProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const INITIAL_ROWS = 10;
  const hasMoreRows = data.length > INITIAL_ROWS;
  const displayedData = isExpanded ? data : data.slice(0, INITIAL_ROWS);

  if (!data || data.length === 0) {
    return (
      <div className="bg-card border border-border rounded-lg p-4 sm:p-6">
        <h3 className="text-base sm:text-lg font-semibold text-card-foreground mb-2">
          Desvios de Água
        </h3>
        <p className="text-sm text-muted-foreground">Nenhum dado disponível.</p>
      </div>
    );
  }

  const handleDownloadCSV = () => {
    const csvData = data.map((row) => ({
      Período: row.periodo_display || row.periodo || "",
      "Desvio (m³/s)": row.valor ?? null,
    }));
    exportToCSV(csvData, "desvios-agua");
  };

  return (
    <div className="bg-card border border-border rounded-lg p-4 sm:p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-base sm:text-lg font-semibold text-card-foreground">
          Desvios de Água
        </h3>
        <div className="flex items-center gap-3">
          <span className="text-sm text-muted-foreground">{data.length} registros</span>
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
                <th className="px-3 sm:px-4 py-3 text-right text-xs font-semibold text-card-foreground uppercase tracking-wider whitespace-nowrap">
                  Desvio (m³/s)
                </th>
              </tr>
            </thead>
            <tbody>
              {displayedData.map((row, index) => (
                <tr
                  key={`${row.periodo}-${index}`}
                  className="border-b border-border/50 hover:bg-background/30 transition-colors"
                >
                  <td className="px-3 sm:px-4 py-2.5 text-sm text-card-foreground font-medium whitespace-nowrap">
                    {row.periodo_display || row.periodo || "-"}
                  </td>
                  <td className="px-3 sm:px-4 py-2.5 text-sm text-card-foreground text-right whitespace-nowrap font-mono">
                    {formatNumber(row.valor as number)}
                  </td>
                </tr>
              ))}
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
