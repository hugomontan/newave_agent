"use client";

import React, { useState } from "react";
import { formatNumber } from "../shared/formatters";
import type { TableRow } from "../shared/types";
import { ChevronDown, ChevronUp, Download } from "lucide-react";
import { Button } from "@/components/ui/button";
import { exportToCSV } from "../shared/csvExport";

interface CVUComparisonTableProps {
  data: TableRow[];
  deckNames: string[];
}

export function CVUComparisonTable({ 
  data, 
  deckNames 
}: CVUComparisonTableProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  
  if (!data || data.length === 0) {
    return null;
  }

  const INITIAL_ROWS = 10;
  const hasMoreRows = data.length > INITIAL_ROWS;
  const displayedData = isExpanded ? data : data.slice(0, INITIAL_ROWS);

  const handleDownloadCSV = () => {
    const csvData = data.map((row) => {
      const rowData = row as any;
      return {
        Semana: rowData.semana_operativa ?? "",
        Data: rowData.data ?? rowData.date ?? "",
        Deck: rowData.display_name ?? rowData.deck ?? "",
        "CVU Pesada (R$/MWh)": rowData.cvu_pesada !== null && rowData.cvu_pesada !== undefined 
          ? rowData.cvu_pesada 
          : null,
        "CVU Média (R$/MWh)": rowData.cvu_media !== null && rowData.cvu_media !== undefined 
          ? rowData.cvu_media 
          : null,
        "CVU Leve (R$/MWh)": rowData.cvu_leve !== null && rowData.cvu_leve !== undefined 
          ? rowData.cvu_leve 
          : null,
      };
    });
    exportToCSV(csvData, "cvu-comparison");
  };

  return (
    <div className="bg-card border border-border rounded-lg p-3.5 sm:p-4.5 max-w-full">
      <div className="flex items-center justify-between mb-4">
        <h4 className="text-base sm:text-lg font-semibold text-card-foreground">
          CVU por Semana Operativa
        </h4>
        <div className="flex items-center gap-2">
          <button
            onClick={handleDownloadCSV}
            className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-card-foreground bg-background/50 hover:bg-background/70 border border-border rounded-lg transition-colors"
            title="Baixar como CSV"
          >
            <Download className="w-4 h-4" />
            CSV
          </button>
          {hasMoreRows && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsExpanded(!isExpanded)}
              className="text-sm text-muted-foreground hover:text-card-foreground"
            >
              {isExpanded ? (
                <>
                  <ChevronUp className="w-4 h-4 mr-1" />
                  Minimizar
                </>
              ) : (
                <>
                  <ChevronDown className="w-4 h-4 mr-1" />
                  Ver todos ({data.length})
                </>
              )}
            </Button>
          )}
        </div>
      </div>
      <div className="w-full">
        <table className="w-full border-collapse table-auto">
          <colgroup>
            <col style={{ minWidth: '80px' }} />
            <col style={{ minWidth: '100px' }} />
            <col style={{ minWidth: '180px' }} />
            <col style={{ minWidth: '120px' }} />
            <col style={{ minWidth: '120px' }} />
            <col style={{ minWidth: '120px' }} />
          </colgroup>
          <thead>
            <tr className="border-b border-border bg-background/50">
              <th className="px-3.5 sm:px-4.5 py-2.5 text-left text-xs font-semibold text-card-foreground uppercase tracking-wider whitespace-nowrap">
                Semana
              </th>
              <th className="px-3.5 sm:px-4.5 py-2.5 text-left text-xs font-semibold text-card-foreground uppercase tracking-wider whitespace-nowrap">
                Data
              </th>
              <th className="px-3.5 sm:px-4.5 py-2.5 text-left text-xs font-semibold text-card-foreground uppercase tracking-wider whitespace-nowrap">
                Deck
              </th>
              <th className="px-3.5 sm:px-4.5 py-2.5 text-right text-xs font-semibold text-card-foreground uppercase tracking-wider whitespace-nowrap">
                CVU Pesada (R$/MWh)
              </th>
              <th className="px-3.5 sm:px-4.5 py-2.5 text-right text-xs font-semibold text-card-foreground uppercase tracking-wider whitespace-nowrap">
                CVU Média (R$/MWh)
              </th>
              <th className="px-3.5 sm:px-4.5 py-2.5 text-right text-xs font-semibold text-card-foreground uppercase tracking-wider whitespace-nowrap">
                CVU Leve (R$/MWh)
              </th>
            </tr>
          </thead>
          <tbody>
            {displayedData.map((row, index) => {
              const rowData = row as any;
              // Usar ?? ao invés de || para não tratar 0 como falsy
              const semanaOperativa = rowData.semana_operativa ?? "-";
              const dataValue = rowData.data ?? rowData.date ?? "-";
              const deckName = rowData.display_name ?? rowData.deck ?? "-";
              const cvuPesada = rowData.cvu_pesada;
              const cvuMedia = rowData.cvu_media;
              const cvuLeve = rowData.cvu_leve;
              
              return (
                <tr
                  key={`${rowData.semana_operativa}-${index}`}
                  className="border-b border-border/50 hover:bg-background/30 transition-colors"
                >
                  <td className="px-3.5 sm:px-4.5 py-2 text-sm text-card-foreground whitespace-nowrap font-medium">
                    {semanaOperativa}
                  </td>
                  <td className="px-3.5 sm:px-4.5 py-2 text-sm text-card-foreground whitespace-nowrap">
                    {dataValue}
                  </td>
                  <td className="px-3.5 sm:px-4.5 py-2 text-sm text-card-foreground whitespace-nowrap">
                    {deckName}
                  </td>
                  <td className="px-3.5 sm:px-4.5 py-2 text-sm text-card-foreground text-right font-mono whitespace-nowrap">
                    {/* Tratar zero explicitamente */}
                    {cvuPesada !== null && cvuPesada !== undefined
                      ? formatNumber(Number(cvuPesada)) 
                      : "-"}
                  </td>
                  <td className="px-3.5 sm:px-4.5 py-2 text-sm text-card-foreground text-right font-mono whitespace-nowrap">
                    {cvuMedia !== null && cvuMedia !== undefined
                      ? formatNumber(Number(cvuMedia)) 
                      : "-"}
                  </td>
                  <td className="px-3.5 sm:px-4.5 py-2 text-sm text-card-foreground text-right font-mono whitespace-nowrap">
                    {cvuLeve !== null && cvuLeve !== undefined
                      ? formatNumber(Number(cvuLeve)) 
                      : "-"}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      {hasMoreRows && !isExpanded && (
        <div className="mt-2 text-center text-sm text-muted-foreground">
          Mostrando {INITIAL_ROWS} de {data.length} semanas operativas
        </div>
      )}
    </div>
  );
}
