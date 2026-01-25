"use client";

import React from "react";
import { Download } from "lucide-react";
import { exportToCSV } from "../shared/csvExport";
import type { TableRow } from "../shared/types";

interface UHTableProps {
  data: TableRow[];
}

export function UHTable({ data }: UHTableProps) {
  if (!data || data.length === 0) {
    return (
      <div className="bg-card border border-border rounded-lg p-4 sm:p-6">
        <h3 className="text-base sm:text-lg font-semibold text-card-foreground mb-2">
          Bloco UH - Usinas Hidrelétricas
        </h3>
        <p className="text-sm text-muted-foreground">Nenhum dado disponível.</p>
      </div>
    );
  }

  const handleDownloadCSV = () => {
    exportToCSV(data, "bloco-uh-usinas");
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
          Bloco UH - Usinas Hidrelétricas
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
                Código
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-card-foreground uppercase">
                REE
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-card-foreground uppercase">
                Volume Inicial
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-card-foreground uppercase">
                Vazão Mínima
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-card-foreground uppercase">
                Evaporação
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-card-foreground uppercase">
                Operação
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-card-foreground uppercase">
                Volume Morto
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-card-foreground uppercase">
                Limite Superior
              </th>
            </tr>
          </thead>
          <tbody>
            {data.map((row, index) => (
              <tr
                key={`${row.codigo_usina}-${index}`}
                className="border-b border-border/50 hover:bg-background/30"
              >
                <td className="px-4 py-2.5 text-sm text-card-foreground font-medium">
                  {row.codigo_usina ?? "-"}
                </td>
                <td className="px-4 py-2.5 text-sm text-card-foreground">
                  {row.codigo_ree ?? "-"}
                </td>
                <td className="px-4 py-2.5 text-sm text-card-foreground">
                  {formatValue(row.volume_inicial)}
                </td>
                <td className="px-4 py-2.5 text-sm text-card-foreground">
                  {formatValue(row.vazao_minima)}
                </td>
                <td className="px-4 py-2.5 text-sm text-card-foreground">
                  {row.evaporacao ?? "-"}
                </td>
                <td className="px-4 py-2.5 text-sm text-card-foreground">
                  {row.operacao ?? "-"}
                </td>
                <td className="px-4 py-2.5 text-sm text-card-foreground">
                  {formatValue(row.volume_morto_inicial)}
                </td>
                <td className="px-4 py-2.5 text-sm text-card-foreground">
                  {formatValue(row.limite_superior)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      
      <div className="mt-4 text-sm text-muted-foreground">
        <p>
          <strong>Total de usinas:</strong> {data.length}
        </p>
      </div>
    </div>
  );
}
