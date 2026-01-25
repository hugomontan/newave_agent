"use client";

import React, { useState } from "react";
import { Download, ChevronDown, ChevronUp } from "lucide-react";
import { formatInteger } from "../shared/formatters";
import { exportToCSV } from "../shared/csvExport";
import type { TableRow } from "../shared/types";

interface CadicTableProps {
  data: TableRow[];
}

export function CadicTable({ data }: CadicTableProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const INITIAL_ROWS = 10;
  const hasMoreRows = data.length > INITIAL_ROWS;
  const displayedData = isExpanded ? data : data.slice(0, INITIAL_ROWS);

  // Verificar se há campo razao (entidade) nos dados
  const hasRazao = data.length > 0 && data.some((row) => row.razao);

  if (!data || data.length === 0) {
    return (
      <div className="bg-card border border-border rounded-lg p-4 sm:p-6">
        <h3 className="text-base sm:text-lg font-semibold text-card-foreground mb-2">
          Carga Adicional
        </h3>
        <p className="text-sm text-muted-foreground">Nenhum dado disponível.</p>
      </div>
    );
  }

  const handleDownloadCSV = () => {
    const csvData = data.map((row) => {
      const baseRow: Record<string, string | number | null> = {
        Data: row.data || `${row.mes || ""}-${row.ano || ""}`,
        Submercado: row.submercado || "",
        "Carga Adicional (MWmédio)": row.valor ?? null,
      };
      
      // Adicionar coluna Entidade se houver razao
      if (hasRazao) {
        baseRow["Entidade"] = row.razao || "";
      }
      
      return baseRow;
    });
    exportToCSV(csvData, "carga-adicional");
  };

  return (
    <div className="bg-card border border-border rounded-lg p-4 sm:p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-base sm:text-lg font-semibold text-card-foreground">
          Carga Adicional
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
                  Data
                </th>
                <th className="px-3 sm:px-4 py-3 text-left text-xs font-semibold text-card-foreground uppercase tracking-wider whitespace-nowrap">
                  Submercado
                </th>
                {hasRazao && (
                  <th className="px-3 sm:px-4 py-3 text-left text-xs font-semibold text-card-foreground uppercase tracking-wider whitespace-nowrap">
                    Entidade
                  </th>
                )}
                <th className="px-3 sm:px-4 py-3 text-right text-xs font-semibold text-card-foreground uppercase tracking-wider whitespace-nowrap">
                  Carga Adicional (MWmédio)
                </th>
              </tr>
            </thead>
            <tbody>
              {displayedData.map((row, index) => {
                // Formatar data como MM-YYYY (usar campo data se disponível, senão construir)
                const dataFormatada = row.data || (row.mes && row.ano ? `${String(row.mes).padStart(2, '0')}-${row.ano}` : "-");
                
                return (
                  <tr
                    key={`${row.data || row.periodo || `${row.ano}-${row.mes}`}-${row.submercado}-${row.razao || ''}-${index}`}
                    className="border-b border-border/50 hover:bg-background/30 transition-colors"
                  >
                    <td className="px-3 sm:px-4 py-2.5 text-sm text-card-foreground font-medium whitespace-nowrap">
                      {dataFormatada}
                    </td>
                    <td className="px-3 sm:px-4 py-2.5 text-sm text-card-foreground whitespace-nowrap">
                      {row.submercado || "-"}
                    </td>
                    {hasRazao && (
                      <td className="px-3 sm:px-4 py-2.5 text-sm text-card-foreground whitespace-nowrap">
                        {row.razao || "-"}
                      </td>
                    )}
                    <td className="px-3 sm:px-4 py-2.5 text-sm text-card-foreground text-right whitespace-nowrap font-mono">
                      {formatInteger(row.valor as number)}
                    </td>
                  </tr>
                );
              })}
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
