"use client";

import React, { useState } from "react";
import { formatNumber } from "../shared/formatters";
import type { TableRow } from "../shared/types";
import { ChevronDown, ChevronUp } from "lucide-react";
import { Button } from "@/components/ui/button";

interface PQComparisonTableProps {
  data: TableRow[];
  tipos?: Array<{ tipo: string }>;
}

export function PQComparisonTable({ 
  data,
  tipos = []
}: PQComparisonTableProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  
  if (!data || data.length === 0) {
    return null;
  }

  const INITIAL_ROWS = 10;
  const hasMoreRows = data.length > INITIAL_ROWS;
  const displayedData = isExpanded ? data : data.slice(0, INITIAL_ROWS);

  // Determinar colunas de tipos dinamicamente
  const tipoColumns = tipos.length > 0 
    ? tipos 
    : // Se não fornecido, inferir das colunas dos dados
      Array.from(new Set(
        Object.keys(data[0] || {})
          .filter(key => key.startsWith("tipo_"))
          .map(key => ({
            tipo: key.replace("tipo_", "")
          }))
      ));

  return (
    <div className="bg-card border border-border rounded-lg p-3.5 sm:p-4.5 max-w-full">
      <div className="flex items-center justify-between mb-4">
        <h4 className="text-base sm:text-lg font-semibold text-card-foreground">
          MW Médio por Deck/Data
        </h4>
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
      <div className="w-full overflow-x-auto">
        <table className="w-full border-collapse table-auto min-w-full">
          <colgroup>
            <col style={{ minWidth: '120px' }} />
            <col style={{ minWidth: '180px' }} />
            {tipoColumns.map(() => (
              <col key={Math.random()} style={{ minWidth: '140px' }} />
            ))}
          </colgroup>
          <thead>
            <tr className="border-b border-border bg-background/50">
              <th className="px-3.5 sm:px-4.5 py-2.5 text-left text-xs font-semibold text-card-foreground uppercase tracking-wider whitespace-nowrap">
                Data
              </th>
              <th className="px-3.5 sm:px-4.5 py-2.5 text-left text-xs font-semibold text-card-foreground uppercase tracking-wider whitespace-nowrap">
                Deck
              </th>
              {tipoColumns.map((tipo) => (
                <th 
                  key={tipo.tipo}
                  className="px-3.5 sm:px-4.5 py-2.5 text-right text-xs font-semibold text-card-foreground uppercase tracking-wider whitespace-nowrap"
                >
                  {tipo.tipo} (MWmed)
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {displayedData.map((row, idx) => {
              const rowData = row as any;
              return (
                <tr 
                  key={idx}
                  className="border-b border-border/50 hover:bg-background/30 transition-colors"
                >
                  <td className="px-3.5 sm:px-4.5 py-2.5 text-sm text-card-foreground whitespace-nowrap">
                    {rowData.data || "-"}
                  </td>
                  <td className="px-3.5 sm:px-4.5 py-2.5 text-sm text-muted-foreground whitespace-nowrap">
                    {rowData.display_name || rowData.deck || "-"}
                  </td>
                  {tipoColumns.map((tipo) => {
                    const mw_medio = rowData[`tipo_${tipo.tipo}`];
                    return (
                      <td 
                        key={tipo.tipo}
                        className="px-3.5 sm:px-4.5 py-2.5 text-sm text-card-foreground text-right whitespace-nowrap"
                      >
                        {mw_medio !== null && mw_medio !== undefined 
                          ? formatNumber(mw_medio)
                          : "-"
                        }
                      </td>
                    );
                  })}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
