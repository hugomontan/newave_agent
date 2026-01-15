"use client";

import React from "react";
import { Download } from "lucide-react";
import { formatNumber } from "../shared/formatters";
import { exportToCSV } from "../shared/csvExport";
import type { TableRow } from "../shared/types";

interface CVUTableProps {
  data: TableRow[];
}

export function CVUTable({ data }: CVUTableProps) {
  if (!data || data.length === 0) {
    return (
      <div className="bg-card border border-border rounded-lg p-4 sm:p-6">
        <h3 className="text-base sm:text-lg font-semibold text-card-foreground mb-2">
          CVU (Custo Variável Unitário)
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
        : "";
      return {
        Ano: ano,
        Classe: row.classe || "",
        "CVU (R$/MWh)": row.valor ?? null,
      };
    });
    exportToCSV(csvData, "cvu");
  };

  return (
    <div className="bg-card border border-border rounded-lg p-4 sm:p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-base sm:text-lg font-semibold text-card-foreground">
          CVU por Ano e Classe
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
                  Ano
                </th>
                <th className="px-3 sm:px-4 py-3 text-left text-xs font-semibold text-card-foreground uppercase tracking-wider whitespace-nowrap">
                  Classe
                </th>
                <th className="px-3 sm:px-4 py-3 text-right text-xs font-semibold text-card-foreground uppercase tracking-wider whitespace-nowrap">
                  CVU (R$/MWh)
                </th>
              </tr>
            </thead>
            <tbody>
              {data.map((row, index) => {
                const ano = row.ano !== undefined && row.ano !== null 
                  ? String(row.ano) 
                  : "";
                const classe = row.classe || "";
                const valor = row.valor ?? null;

                return (
                  <tr
                    key={`${ano}-${classe}-${index}`}
                    className="border-b border-border/50 hover:bg-background/30 transition-colors"
                  >
                    <td className="px-3 sm:px-4 py-2.5 text-sm text-card-foreground font-medium whitespace-nowrap">
                      {ano}
                    </td>
                    <td className="px-3 sm:px-4 py-2.5 text-sm text-card-foreground whitespace-nowrap">
                      {classe}
                    </td>
                    <td className="px-3 sm:px-4 py-2.5 text-sm text-card-foreground text-right whitespace-nowrap font-mono">
                      {valor !== null ? formatNumber(Number(valor)) : "-"}
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
