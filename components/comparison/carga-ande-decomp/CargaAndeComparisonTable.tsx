"use client";

import React, { useState } from "react";
import { formatNumber } from "../shared/formatters";
import type { TableRow } from "../shared/types";
import { ChevronDown, ChevronUp, Download } from "lucide-react";
import { Button } from "@/components/ui/button";
import { exportToCSV } from "../shared/csvExport";

interface CargaAndeComparisonTableProps {
  data: TableRow[];
}

export function CargaAndeComparisonTable({ 
  data
}: CargaAndeComparisonTableProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  
  if (!data || data.length === 0) {
    return null;
  }

  const INITIAL_ROWS = 10;
  const hasMoreRows = data.length > INITIAL_ROWS;
  const displayedData = isExpanded ? data : data.slice(0, INITIAL_ROWS);

  const handleDownloadCSV = () => {
    exportToCSV(data, "carga-ande-comparison");
  };

  const formatValue = (value: any): string => {
    if (value === null || value === undefined) return "-";
    if (typeof value === "number") {
      return formatNumber(value);
    }
    return String(value);
  };

  return (
    <div className="bg-card border border-border rounded-lg p-3.5 sm:p-4.5 max-w-full">
      <div className="flex items-center justify-between mb-4">
        <h4 className="text-base sm:text-lg font-semibold text-card-foreground">
          Carga ANDE por Data
        </h4>
        <div className="flex items-center gap-2">
          <button
            onClick={handleDownloadCSV}
            className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-card-foreground bg-background/50 hover:bg-background/70 border border-border rounded-lg transition-colors"
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
      <div className="w-full overflow-x-auto">
        <table className="w-full border-collapse table-auto min-w-full">
          <colgroup>
            <col style={{ minWidth: '120px' }} />
            <col style={{ minWidth: '140px' }} />
          </colgroup>
          <thead>
            <tr className="border-b border-border bg-background/50">
              <th className="px-3.5 sm:px-4.5 py-2.5 text-left text-xs font-semibold text-card-foreground uppercase tracking-wider whitespace-nowrap">
                Data
              </th>
              <th className="px-3.5 sm:px-4.5 py-2.5 text-left text-xs font-semibold text-card-foreground uppercase tracking-wider whitespace-nowrap">
                MWmed
              </th>
            </tr>
          </thead>
          <tbody>
            {displayedData.map((row, index) => (
              <tr
                key={index}
                className="border-b border-border/50 hover:bg-background/30 transition-colors"
              >
                <td className="px-3.5 sm:px-4.5 py-2.5 text-sm text-card-foreground whitespace-nowrap">
                  {row.data ? String(row.data) : "-"}
                </td>
                <td className="px-3.5 sm:px-4.5 py-2.5 text-sm text-card-foreground whitespace-nowrap">
                  {formatValue(row.mwmed)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {hasMoreRows && (
        <div className="mt-3 text-sm text-muted-foreground text-center">
          Mostrando {displayedData.length} de {data.length} registros
        </div>
      )}
    </div>
  );
}
