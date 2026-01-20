"use client";

import React from "react";
import { Download } from "lucide-react";
import { exportToCSV } from "../shared/csvExport";
import type { TableRow } from "../shared/types";

interface CargaAndeTableProps {
  data: TableRow[];
}

export function CargaAndeTable({ data }: CargaAndeTableProps) {
  if (!data || data.length === 0) {
    return (
      <div className="bg-card border border-border rounded-lg p-4 sm:p-6">
        <h3 className="text-base sm:text-lg font-semibold text-card-foreground mb-2">
          Carga ANDE
        </h3>
        <p className="text-sm text-muted-foreground">Nenhum dado disponível.</p>
      </div>
    );
  }

  const handleDownloadCSV = () => {
    exportToCSV(data, "carga-ande");
  };

  const formatValue = (value: any): string => {
    if (value === null || value === undefined) return "-";
    if (typeof value === "number") {
      return value.toLocaleString("pt-BR", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      });
    }
    return String(value);
  };

  return (
    <div className="bg-card border border-border rounded-lg p-4 sm:p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-base sm:text-lg font-semibold text-card-foreground">
          Carga ANDE
        </h3>
        <button
          onClick={handleDownloadCSV}
          className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-card-foreground bg-background/50 hover:bg-background/70 border border-border rounded-lg transition-colors"
        >
          <Download className="w-4 h-4" />
          CSV
        </button>
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full border-collapse">
          <thead>
            <tr className="border-b border-border bg-background/50">
              <th className="px-4 py-3 text-left text-xs font-semibold text-card-foreground uppercase">
                Patamar
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-card-foreground uppercase">
                Carga ANDE (MW)
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-card-foreground uppercase">
                Duração (horas)
              </th>
            </tr>
          </thead>
          <tbody>
            {data.map((row, index) => (
              <tr
                key={`${row.patamar}-${index}`}
                className="border-b border-border/50 hover:bg-background/30"
              >
                <td className="px-4 py-2.5 text-sm text-card-foreground font-medium">
                  {row.patamar ?? "-"}
                </td>
                <td className="px-4 py-2.5 text-sm text-card-foreground">
                  {formatValue(row.carga_ande_mw)}
                </td>
                <td className="px-4 py-2.5 text-sm text-card-foreground">
                  {formatValue(row.duracao_horas)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      
      <div className="mt-4 text-sm text-muted-foreground">
        <p>
          <strong>Total de registros:</strong> {data.length}
        </p>
      </div>
    </div>
  );
}
