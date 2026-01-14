"use client";

import React from "react";
import { Download } from "lucide-react";
import { formatNumber } from "../shared/formatters";
import { exportToCSV } from "../shared/csvExport";
import type { TableRow } from "../shared/types";

interface ReservatorioInicialTableProps {
  data: TableRow[];
  deck1Name: string;
  deck2Name: string;
}

export function ReservatorioInicialTable({ data, deck1Name, deck2Name }: ReservatorioInicialTableProps) {
  if (!data || data.length === 0) {
    return (
      <div className="bg-card border border-border rounded-lg p-4 sm:p-6">
        <h3 className="text-base sm:text-lg font-semibold text-card-foreground mb-2">
          Comparação de Volume Inicial
        </h3>
        <p className="text-sm text-muted-foreground">
          Nenhum dado disponível.
        </p>
      </div>
    );
  }

  // Agrupar por usina para mostrar nome apenas na primeira linha
  const groupedByUsina = React.useMemo(() => {
    const grouped: Record<string, TableRow[]> = {};
    data.forEach((row) => {
      const usinaKey = row.usina || `Usina ${row.codigo_usina || ""}`;
      if (!grouped[usinaKey]) {
        grouped[usinaKey] = [];
      }
      grouped[usinaKey].push(row);
    });
    return grouped;
  }, [data]);

  const handleDownloadCSV = () => {
    const csvData = data.map((row) => {
      return {
        "Data (MM-YYYY)": row.data || row.periodo || "",
        "Volume Inicial (%)": row.volume_inicial ?? null,
      };
    });
    exportToCSV(csvData, "reservatorio_inicial");
  };

  // Contar usinas únicas
  const uniqueUsinas = Object.keys(groupedByUsina).length;
  // Se há apenas uma usina, mostrar o nome no topo
  const singleUsinaName = uniqueUsinas === 1 ? Object.keys(groupedByUsina)[0] : null;

  return (
    <div className="bg-card border border-border rounded-lg p-4 sm:p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex flex-col">
          <h3 className="text-base sm:text-lg font-semibold text-card-foreground">
            Comparação de Volume Inicial
          </h3>
          {singleUsinaName && (
            <p className="text-sm text-muted-foreground mt-1">
              {singleUsinaName}
            </p>
          )}
        </div>
        <div className="flex items-center gap-3">
          <span className="text-sm text-muted-foreground">
            {uniqueUsinas} usina{uniqueUsinas !== 1 ? "s" : ""}
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
                  Data
                </th>
                <th className="px-3 sm:px-4 py-3 text-right text-xs font-semibold text-card-foreground uppercase tracking-wider whitespace-nowrap">
                  Volume Inicial (%)
                </th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(groupedByUsina).map(([usinaKey, rows], usinaIndex) => {
                return rows.map((row, rowIndex) => {
                  const dataValue = row.data || row.periodo || "";
                  const volumeInicial = row.volume_inicial ?? null;
                  const isFirstUsina = usinaIndex === 0;

                  return (
                    <tr
                      key={`${usinaKey}-${rowIndex}`}
                      className={`border-b border-border/50 hover:bg-background/30 transition-colors ${rowIndex === 0 && !isFirstUsina ? 'border-t-2 border-border' : ''}`}
                    >
                      <td className="px-3 sm:px-4 py-2.5 text-sm text-card-foreground font-medium whitespace-nowrap">
                        {dataValue}
                      </td>
                      <td className="px-3 sm:px-4 py-2.5 text-sm text-card-foreground text-right whitespace-nowrap font-mono">
                        {volumeInicial !== null ? `${formatNumber(Number(volumeInicial))}%` : "-"}
                      </td>
                    </tr>
                  );
                });
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
