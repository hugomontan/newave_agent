"use client";

import React, { useState } from "react";
import { Download, ChevronDown, ChevronUp } from "lucide-react";
import { exportToCSV } from "../shared/csvExport";
import type { TableRow } from "../shared/types";

interface VolumeInicialComparisonTableProps {
  data: TableRow[];
}

export function VolumeInicialComparisonTable({ data }: VolumeInicialComparisonTableProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  if (!data || data.length === 0) {
    return (
      <div className="bg-card border border-border rounded-lg p-4 sm:p-6">
        <h3 className="text-base sm:text-lg font-semibold text-card-foreground mb-2">
          Volume Inicial
        </h3>
        <p className="text-sm text-muted-foreground">
          Nenhum dado disponível.
        </p>
      </div>
    );
  }

  const INITIAL_ROWS = 10;
  const hasMoreRows = data.length > INITIAL_ROWS;
  const displayedData = isExpanded ? data : data.slice(0, INITIAL_ROWS);

  const handleDownloadCSV = () => {
    const csvData = data.map((row) => {
      return {
        "Data": row.data || "",
        "Volume Inicial": row.volume_inicial || "",
      };
    });
    exportToCSV(csvData, "volume_inicial");
  };

  return (
    <div className="bg-card border border-border rounded-lg p-4 sm:p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-base sm:text-lg font-semibold text-card-foreground">
          Volume Inicial
        </h3>
        <div className="flex items-center gap-2">
          {hasMoreRows && (
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-card-foreground bg-background/50 hover:bg-background/70 border border-border rounded-lg transition-colors"
            >
              {isExpanded ? (
                <>
                  <ChevronUp className="w-4 h-4" />
                  Minimizar
                </>
              ) : (
                <>
                  <ChevronDown className="w-4 h-4" />
                  Ver todos ({data.length})
                </>
              )}
            </button>
          )}
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

      <div className="overflow-x-auto">
        <table className="min-w-full border-collapse">
          <thead>
            <tr className="border-b border-border bg-background/50">
              <th className="px-4 py-3 text-left text-xs font-semibold text-card-foreground uppercase whitespace-nowrap">
                Data
              </th>
              <th className="px-4 py-3 text-right text-xs font-semibold text-card-foreground uppercase whitespace-nowrap">
                Volume Inicial
              </th>
            </tr>
          </thead>
          <tbody>
            {displayedData.map((row, index) => {
              const dataValue = row.data || "";
              const volumeInicial = row.volume_inicial || "-";

              return (
                <tr
                  key={`${dataValue}-${index}`}
                  className="border-b border-border/50 hover:bg-background/30 transition-colors"
                >
                  <td className="px-4 py-2.5 text-sm text-card-foreground font-medium whitespace-nowrap">
                    {dataValue}
                  </td>
                  <td className="px-4 py-2.5 text-sm text-card-foreground text-right whitespace-nowrap">
                    {volumeInicial}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {hasMoreRows && !isExpanded && (
        <div className="mt-4 text-center">
          <p className="text-sm text-muted-foreground">
            Mostrando {INITIAL_ROWS} de {data.length} registros
          </p>
        </div>
      )}
    </div>
  );
}
