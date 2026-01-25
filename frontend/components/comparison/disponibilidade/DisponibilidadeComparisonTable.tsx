"use client";

import React, { useState } from "react";
import { formatNumber } from "../shared/formatters";
import type { TableRow } from "../shared/types";
import { ChevronDown, ChevronUp } from "lucide-react";
import { Button } from "@/components/ui/button";

interface DisponibilidadeComparisonTableProps {
  data: TableRow[];
  deckNames: string[];
}

export function DisponibilidadeComparisonTable({ 
  data, 
  deckNames 
}: DisponibilidadeComparisonTableProps) {
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
          Disponibilidade por Deck
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
      <div className="w-full">
        <table className="w-full border-collapse table-auto">
          <colgroup>
            <col style={{ minWidth: '100px' }} />
            <col style={{ minWidth: '180px' }} />
            <col style={{ minWidth: '120px' }} />
          </colgroup>
          <thead>
            <tr className="border-b border-border bg-background/50">
              <th className="px-3.5 sm:px-4.5 py-2.5 text-left text-xs font-semibold text-card-foreground uppercase tracking-wider whitespace-nowrap">
                Data
              </th>
              <th className="px-3.5 sm:px-4.5 py-2.5 text-left text-xs font-semibold text-card-foreground uppercase tracking-wider whitespace-nowrap">
                Deck
              </th>
              <th className="px-3.5 sm:px-4.5 py-2.5 text-right text-xs font-semibold text-card-foreground uppercase tracking-wider whitespace-nowrap">
                Disponibilidade (MW)
              </th>
            </tr>
          </thead>
          <tbody>
            {displayedData.map((row, index) => {
              const rowData = row as any;
              // Usar ?? ao invés de || para não tratar 0 como falsy
              const disponibilidade = rowData.disponibilidade ?? rowData.disponibilidade_total;
              const dataValue = rowData.data ?? rowData.date ?? "-";
              const deckName = rowData.display_name ?? rowData.deck ?? "-";
              
              return (
                <tr
                  key={`${rowData.deck}-${index}`}
                  className="border-b border-border/50 hover:bg-background/30 transition-colors"
                >
                  <td className="px-3.5 sm:px-4.5 py-2 text-sm text-card-foreground whitespace-nowrap">
                    {dataValue}
                  </td>
                  <td className="px-3.5 sm:px-4.5 py-2 text-sm text-card-foreground whitespace-nowrap">
                    {deckName}
                  </td>
                  <td className="px-3.5 sm:px-4.5 py-2 text-sm text-card-foreground text-right font-mono whitespace-nowrap">
                    {/* Tratar zero explicitamente - zero é válido quando inflexibilidades são zeradas */}
                    {disponibilidade !== null && disponibilidade !== undefined
                      ? formatNumber(Number(disponibilidade)) 
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
          Mostrando {INITIAL_ROWS} de {data.length} decks
        </div>
      )}
    </div>
  );
}
