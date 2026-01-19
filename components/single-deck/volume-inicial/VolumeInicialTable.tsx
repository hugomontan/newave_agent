"use client";

import React from "react";
import { Download } from "lucide-react";
import { exportToCSV } from "../shared/csvExport";

interface VolumeInicialTableProps {
  data: Array<{
    usina: string;
    codigo: number;
    data: string;
    volume_inicial: string;
  }>;
}

export function VolumeInicialTable({ data }: VolumeInicialTableProps) {
  if (!data || data.length === 0) {
    return (
      <div className="bg-card border border-border rounded-lg p-4 sm:p-6">
        <h3 className="text-base sm:text-lg font-semibold text-card-foreground mb-2">
          Volume Inicial
        </h3>
        <p className="text-sm text-muted-foreground">Nenhum dado disponível.</p>
      </div>
    );
  }

  const handleDownloadCSV = () => {
    exportToCSV(data, "volume-inicial");
  };

  return (
    <div className="bg-card border border-border rounded-lg p-4 sm:p-6 w-full max-w-4xl">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-base sm:text-lg font-semibold text-card-foreground">
          Volume Inicial
        </h3>
        <button
          onClick={handleDownloadCSV}
          className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-card-foreground bg-background/50 hover:bg-background/70 border border-border rounded-lg transition-colors"
        >
          <Download className="w-4 h-4" />
          CSV
        </button>
      </div>

      <div>
        <table className="w-full border-collapse">
          <thead>
            <tr className="border-b border-border bg-background/50">
              <th className="px-4 py-3 text-left text-xs font-semibold text-card-foreground uppercase">
                Usina
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-card-foreground uppercase">
                Código
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-card-foreground uppercase whitespace-nowrap">
                Data
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-card-foreground uppercase">
                Volume Inicial
              </th>
            </tr>
          </thead>
          <tbody>
            {data.map((row, index) => (
              <tr
                key={`${row.codigo}-${index}`}
                className="border-b border-border/50 hover:bg-background/30"
              >
                <td className="px-4 py-2.5 text-sm text-card-foreground font-medium">
                  {row.usina ?? "-"}
                </td>
                <td className="px-4 py-2.5 text-sm text-card-foreground">
                  {row.codigo ?? "-"}
                </td>
                <td className="px-4 py-2.5 text-sm text-card-foreground whitespace-nowrap">
                  {row.data ?? "-"}
                </td>
                <td className="px-4 py-2.5 text-sm text-card-foreground">
                  {row.volume_inicial ?? "-"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
