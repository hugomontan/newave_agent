"use client";

import React from "react";
import { formatNumber } from "../shared/formatters";
import type { TableRow } from "../shared/types";

interface DisponibilidadeComparisonTableProps {
  data: TableRow[];
  deckNames: string[];
}

export function DisponibilidadeComparisonTable({ 
  data, 
  deckNames 
}: DisponibilidadeComparisonTableProps) {
  if (!data || data.length === 0) {
    return null;
  }

  return (
    <div className="bg-card border border-border rounded-lg p-4 sm:p-6">
      <h4 className="text-base sm:text-lg font-semibold text-card-foreground mb-4">
        Disponibilidade por Deck
      </h4>
      <div className="w-full overflow-x-auto">
        <table className="w-full border-collapse">
          <thead>
            <tr className="border-b border-border bg-background/50">
              <th className="px-3 sm:px-4 py-3 text-left text-xs font-semibold text-card-foreground uppercase tracking-wider">
                Data
              </th>
              <th className="px-3 sm:px-4 py-3 text-left text-xs font-semibold text-card-foreground uppercase tracking-wider">
                Deck
              </th>
              <th className="px-3 sm:px-4 py-3 text-right text-xs font-semibold text-card-foreground uppercase tracking-wider">
                Disponibilidade (MW)
              </th>
            </tr>
          </thead>
          <tbody>
            {data.map((row, index) => {
              const rowData = row as any;
              const disponibilidade = rowData.disponibilidade || rowData.disponibilidade_total;
              const dataValue = rowData.data || rowData.date || "-";
              const deckName = rowData.display_name || rowData.deck || "-";
              
              return (
                <tr
                  key={`${rowData.deck}-${index}`}
                  className="border-b border-border/50 hover:bg-background/30 transition-colors"
                >
                  <td className="px-3 sm:px-4 py-2.5 text-sm text-card-foreground">
                    {dataValue}
                  </td>
                  <td className="px-3 sm:px-4 py-2.5 text-sm text-card-foreground">
                    {deckName}
                  </td>
                  <td className="px-3 sm:px-4 py-2.5 text-sm text-card-foreground text-right font-mono">
                    {disponibilidade != null ? formatNumber(disponibilidade) : "-"}
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
