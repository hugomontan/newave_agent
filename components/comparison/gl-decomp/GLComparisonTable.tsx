"use client";

import React, { useState } from "react";
import { formatNumber } from "../shared/formatters";
import type { TableRow } from "../shared/types";
import { ChevronDown, ChevronUp } from "lucide-react";
import { Button } from "@/components/ui/button";

interface GLComparisonTableProps {
  data: TableRow[];
}

export function GLComparisonTable({ 
  data
}: GLComparisonTableProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  
  if (!data || data.length === 0) {
    return null;
  }

  const INITIAL_ROWS = 10;
  const hasMoreRows = data.length > INITIAL_ROWS;
  const displayedData = isExpanded ? data : data.slice(0, INITIAL_ROWS);

  return (
    <div className="bg-card border border-border rounded-lg p-3.5 sm:p-4.5 max-w-full">
      <div className="flex items-center justify-between mb-4">
        <h4 className="text-base sm:text-lg font-semibold text-card-foreground">
          Série Temporal de Gerações GNL por Patamar
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
            <col style={{ minWidth: '80px' }} />
            <col style={{ minWidth: '180px' }} />
            <col style={{ minWidth: '140px' }} />
            <col style={{ minWidth: '140px' }} />
            <col style={{ minWidth: '140px' }} />
          </colgroup>
          <thead>
            <tr className="border-b border-border bg-background/50">
              <th className="px-3.5 sm:px-4.5 py-2.5 text-left text-xs font-semibold text-card-foreground uppercase tracking-wider whitespace-nowrap">
                Data
              </th>
              <th className="px-3.5 sm:px-4.5 py-2.5 text-left text-xs font-semibold text-card-foreground uppercase tracking-wider whitespace-nowrap">
                Semana
              </th>
              <th className="px-3.5 sm:px-4.5 py-2.5 text-left text-xs font-semibold text-card-foreground uppercase tracking-wider whitespace-nowrap">
                Deck
              </th>
              <th className="px-3.5 sm:px-4.5 py-2.5 text-right text-xs font-semibold text-card-foreground uppercase tracking-wider whitespace-nowrap">
                Geração Pat. 1 (PESADA) (MW)
              </th>
              <th className="px-3.5 sm:px-4.5 py-2.5 text-right text-xs font-semibold text-card-foreground uppercase tracking-wider whitespace-nowrap">
                Geração Pat. 2 (MÉDIA) (MW)
              </th>
              <th className="px-3.5 sm:px-4.5 py-2.5 text-right text-xs font-semibold text-card-foreground uppercase tracking-wider whitespace-nowrap">
                Geração Pat. 3 (LEVE) (MW)
              </th>
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
                    {rowData.data_display || rowData.data || "-"}
                  </td>
                  <td className="px-3.5 sm:px-4.5 py-2.5 text-sm text-muted-foreground whitespace-nowrap">
                    {rowData.semana || rowData.estagio || "-"}
                  </td>
                  <td className="px-3.5 sm:px-4.5 py-2.5 text-sm text-muted-foreground whitespace-nowrap">
                    {rowData.display_name || rowData.deck || "-"}
                  </td>
                  <td className="px-3.5 sm:px-4.5 py-2.5 text-sm text-card-foreground text-right whitespace-nowrap">
                    {rowData.geracao_pat_1 !== null && rowData.geracao_pat_1 !== undefined 
                      ? formatNumber(rowData.geracao_pat_1)
                      : "-"
                    }
                  </td>
                  <td className="px-3.5 sm:px-4.5 py-2.5 text-sm text-card-foreground text-right whitespace-nowrap">
                    {rowData.geracao_pat_2 !== null && rowData.geracao_pat_2 !== undefined 
                      ? formatNumber(rowData.geracao_pat_2)
                      : "-"
                    }
                  </td>
                  <td className="px-3.5 sm:px-4.5 py-2.5 text-sm text-card-foreground text-right whitespace-nowrap">
                    {rowData.geracao_pat_3 !== null && rowData.geracao_pat_3 !== undefined 
                      ? formatNumber(rowData.geracao_pat_3)
                      : "-"
                    }
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
