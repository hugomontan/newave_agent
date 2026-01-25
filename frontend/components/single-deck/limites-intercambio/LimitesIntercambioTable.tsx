"use client";

import React, { useState } from "react";
import { Download, ChevronDown, ChevronUp } from "lucide-react";
import { formatNumber } from "../shared/formatters";
import { exportToCSV } from "../shared/csvExport";
import type { TableRow } from "../shared/types";

const INITIAL_ROWS = 10;

interface LimitesIntercambioTableProps {
  data: TableRow[];
}

export function LimitesIntercambioTable({ data }: LimitesIntercambioTableProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  
  if (!data || data.length === 0) {
    return (
      <div className="bg-card border border-border rounded-lg p-4 sm:p-6">
        <h3 className="text-base sm:text-lg font-semibold text-card-foreground mb-2">
          Limites de Intercâmbio
        </h3>
        <p className="text-sm text-muted-foreground">Nenhum dado disponível.</p>
      </div>
    );
  }

  // Verificar formato novo (sentido, patamar, limite_mw) ou formato antigo (data, limite)
  const isNewFormat = data[0]?.sentido !== undefined && data[0]?.patamar !== undefined;

  const hasMoreRows = data.length > INITIAL_ROWS;
  const displayedData = isExpanded ? data : data.slice(0, INITIAL_ROWS);

  const handleDownloadCSV = () => {
    let csvData: any[];
    if (isNewFormat) {
      csvData = data.map((row) => ({
        Sentido: row.sentido || "",
        Patamar: row.patamar || "",
        "Limite (MW)": row.limite_mw ?? null,
        "Duração (horas)": row.duracao_horas ?? null,
      }));
    } else {
      csvData = data.map((row) => ({
        Período: row.data ? String(row.data) : "",
        "Limite (MW)": row.limite ?? null,
      }));
    }
    exportToCSV(csvData, "limites-intercambio");
  };

  return (
    <div className="bg-card border border-border rounded-lg p-4 sm:p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <h3 className="text-base sm:text-lg font-semibold text-card-foreground">
            Limites de Intercâmbio
          </h3>
          <span className="text-sm text-muted-foreground">
            {data.length} registros
          </span>
        </div>
        <button
          onClick={handleDownloadCSV}
          className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-card-foreground bg-background/50 hover:bg-background/70 border border-border rounded-lg transition-colors"
          title="Baixar como CSV"
        >
          <Download className="w-4 h-4" />
          CSV
        </button>
      </div>

      <div className="w-full">
        <table className="w-full border-collapse">
          <thead>
            <tr className="border-b border-border bg-background/50">
              {isNewFormat ? (
                <>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-card-foreground uppercase tracking-wider">
                    Sentido
                  </th>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-card-foreground uppercase tracking-wider">
                    Patamar
                  </th>
                  <th className="px-4 py-3 text-right text-sm font-semibold text-card-foreground uppercase tracking-wider">
                    Limite (MW)
                  </th>
                  <th className="px-4 py-3 text-right text-sm font-semibold text-card-foreground uppercase tracking-wider">
                    Duração (horas)
                  </th>
                </>
              ) : (
                <>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-card-foreground uppercase tracking-wider">
                    Período
                  </th>
                  <th className="px-4 py-3 text-right text-sm font-semibold text-card-foreground uppercase tracking-wider">
                    Limite (MW)
                  </th>
                </>
              )}
            </tr>
          </thead>
          <tbody>
            {displayedData.map((row, index) => {
              if (isNewFormat) {
                const sentido = row.sentido || "-";
                const patamar = row.patamar || "-";
                const limite_mw = row.limite_mw ?? null;
                const duracao_horas = row.duracao_horas ?? null;

                return (
                  <tr
                    key={`${sentido}-${patamar}-${index}`}
                    className="border-b border-border/50 hover:bg-background/30 transition-colors"
                  >
                    <td className="px-4 py-3 text-base text-card-foreground font-medium">
                      {sentido}
                    </td>
                    <td className="px-4 py-3 text-base text-card-foreground">
                      {patamar}
                    </td>
                    <td className="px-4 py-3 text-base text-card-foreground text-right font-mono">
                      {limite_mw !== null ? formatNumber(limite_mw as number) : "-"}
                    </td>
                    <td className="px-4 py-3 text-base text-card-foreground text-right font-mono">
                      {duracao_horas !== null ? formatNumber(duracao_horas as number) : "-"}
                    </td>
                  </tr>
                );
              } else {
                const periodo = row.data ? String(row.data) : "";
                const limite = row.limite ?? null;

                return (
                  <tr
                    key={`${periodo}-${index}`}
                    className="border-b border-border/50 hover:bg-background/30 transition-colors"
                  >
                    <td className="px-4 py-3 text-base text-card-foreground font-medium">
                      {periodo}
                    </td>
                    <td className="px-4 py-3 text-base text-card-foreground text-right font-mono">
                      {limite !== null ? formatNumber(limite as number) : "-"}
                    </td>
                  </tr>
                );
              }
            })}
          </tbody>
        </table>
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

      <div className="mt-4 text-base text-muted-foreground">
        <p>
          <strong>Total de registros:</strong> {data.length}
        </p>
      </div>
    </div>
  );
}
