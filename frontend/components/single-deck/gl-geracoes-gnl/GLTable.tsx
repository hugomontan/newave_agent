"use client";

import React from "react";
import { Download } from "lucide-react";
import { exportToCSV } from "../shared/csvExport";
import { formatNumber } from "../shared/formatters";
import type { TableRow as TableRowType } from "../shared/types";

interface GLTableProps {
  data: TableRowType[];
}

export function GLTable({ data }: GLTableProps) {
  if (!data || data.length === 0) {
    return (
      <div className="bg-card border border-border rounded-lg p-4 sm:p-6">
        <h3 className="text-base sm:text-lg font-semibold text-card-foreground mb-2">
          Gerações GNL já Comandadas
        </h3>
        <p className="text-sm text-muted-foreground">Nenhum dado disponível.</p>
      </div>
    );
  }

  const handleDownloadCSV = () => {
    exportToCSV(data, "geracoes-gnl-comandadas");
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
          Gerações GNL já Comandadas
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
                Data Início
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-card-foreground uppercase">
                Semana
              </th>
              <th className="px-4 py-3 text-right text-xs font-semibold text-card-foreground uppercase">
                Geração Pat. 1 (MW)
              </th>
              <th className="px-4 py-3 text-right text-xs font-semibold text-card-foreground uppercase">
                Geração Pat. 2 (MW)
              </th>
              <th className="px-4 py-3 text-right text-xs font-semibold text-card-foreground uppercase">
                Geração Pat. 3 (MW)
              </th>
            </tr>
          </thead>
          <tbody>
            {data.map((row, index) => (
              <tr
                key={`${row.data_inicio}-${row.semana}-${index}`}
                className="border-b border-border/50 hover:bg-background/30"
              >
                <td className="px-4 py-2.5 text-sm text-card-foreground font-medium">
                  {row.data_inicio || "-"}
                </td>
                <td className="px-4 py-2.5 text-sm text-card-foreground">
                  {row.semana ?? row.estagio ?? "-"}
                </td>
                <td className="px-4 py-2.5 text-sm text-card-foreground text-right">
                  {formatValue(row.geracao_patamar_1)}
                </td>
                <td className="px-4 py-2.5 text-sm text-card-foreground text-right">
                  {formatValue(row.geracao_patamar_2)}
                </td>
                <td className="px-4 py-2.5 text-sm text-card-foreground text-right">
                  {formatValue(row.geracao_patamar_3)}
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
