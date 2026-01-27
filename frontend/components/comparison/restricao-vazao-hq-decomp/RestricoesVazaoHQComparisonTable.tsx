"use client";

import React, { useState } from "react";
import { formatNumber } from "../shared/formatters";
import { exportToCSV } from "../shared/csvExport";
import type { TableRow } from "../shared/types";
import { Download, ChevronDown, ChevronUp } from "lucide-react";
import { Button } from "@/components/ui/button";

interface RestricoesVazaoHQComparisonTableProps {
  data: TableRow[];
}

export function RestricoesVazaoHQComparisonTable({ 
  data
}: RestricoesVazaoHQComparisonTableProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  
  if (!data || data.length === 0) {
    return null;
  }

  const INITIAL_ROWS = 10;
  const hasMoreRows = data.length > INITIAL_ROWS;
  const displayedData = isExpanded ? data : data.slice(0, INITIAL_ROWS);

  // null/undefined = sem restrição → N/A no CSV; 0 = restrição zero → "0"
  const cellToCsv = (val: unknown): string =>
    val === null || val === undefined ? "N/A" : String(val);

  const handleDownloadCSV = () => {
    const csvData = data.map((row) => {
      const rowData = row as any;
      return {
        Deck: rowData.display_name || rowData.deck || "",
        Nome: rowData.Nome || "",
        "VAZMIN P1": cellToCsv(rowData["VAZMIN P1"]),
        "VAZMIN P2": cellToCsv(rowData["VAZMIN P2"]),
        "VAZMIN P3": cellToCsv(rowData["VAZMIN P3"]),
        "VAZMAX P1": cellToCsv(rowData["VAZMAX P1"]),
        "VAZMAX P2": cellToCsv(rowData["VAZMAX P2"]),
        "VAZMAX P3": cellToCsv(rowData["VAZMAX P3"]),
      };
    });
    exportToCSV(csvData, "restricoes-vazao-hq-comparison");
  };

  return (
    <div className="bg-card border border-border rounded-lg p-2 sm:p-3 max-w-full">
      <div className="flex items-center justify-between mb-2 gap-2">
        <div>
          <h4 className="text-base sm:text-lg font-semibold text-card-foreground" title="— = sem restrição neste patamar; 0 = restrição zero">
            Valores por Deck
          </h4>
          <p className="text-[10px] text-muted-foreground mt-0.5">
            — = sem restrição · 0 = restrição zero
          </p>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <Button
            variant="outline"
            size="sm"
            onClick={handleDownloadCSV}
            className="text-sm"
          >
            <Download className="w-4 h-4 mr-1" />
            CSV
          </Button>
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
            <col style={{ minWidth: '100px' }} />
            <col style={{ minWidth: '140px' }} />
            <col style={{ minWidth: '80px' }} />
            <col style={{ minWidth: '80px' }} />
            <col style={{ minWidth: '80px' }} />
            <col style={{ minWidth: '80px' }} />
            <col style={{ minWidth: '80px' }} />
            <col style={{ minWidth: '80px' }} />
          </colgroup>
          <thead>
            <tr className="border-b border-border bg-background/50">
              <th className="px-2 py-1.5 text-left text-[10px] font-semibold text-card-foreground uppercase tracking-tight whitespace-nowrap">
                Deck
              </th>
              <th className="px-2 py-1.5 text-left text-[10px] font-semibold text-card-foreground uppercase tracking-tight whitespace-nowrap">
                Nome
              </th>
              <th className="px-1.5 py-1.5 text-right text-[10px] font-semibold text-card-foreground uppercase tracking-tight whitespace-nowrap">
                VAZMIN P1
              </th>
              <th className="px-1.5 py-1.5 text-right text-[10px] font-semibold text-card-foreground uppercase tracking-tight whitespace-nowrap">
                VAZMIN P2
              </th>
              <th className="px-1.5 py-1.5 text-right text-[10px] font-semibold text-card-foreground uppercase tracking-tight whitespace-nowrap">
                VAZMIN P3
              </th>
              <th className="px-1.5 py-1.5 text-right text-[10px] font-semibold text-card-foreground uppercase tracking-tight whitespace-nowrap">
                VAZMAX P1
              </th>
              <th className="px-1.5 py-1.5 text-right text-[10px] font-semibold text-card-foreground uppercase tracking-tight whitespace-nowrap">
                VAZMAX P2
              </th>
              <th className="px-1.5 py-1.5 text-right text-[10px] font-semibold text-card-foreground uppercase tracking-tight whitespace-nowrap">
                VAZMAX P3
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
                  <td className="px-2 py-1.5 text-xs text-card-foreground whitespace-nowrap">
                    {rowData.display_name || rowData.deck || "-"}
                  </td>
                  <td className="px-2 py-1.5 text-xs text-card-foreground font-medium whitespace-nowrap">
                    {rowData.Nome || "-"}
                  </td>
                  {(["VAZMIN P1", "VAZMIN P2", "VAZMIN P3", "VAZMAX P1", "VAZMAX P2", "VAZMAX P3"] as const).map((key) => {
                    const val = rowData[key];
                    const isMissing = val === null || val === undefined;
                    return (
                      <td
                        key={key}
                        className="px-1.5 py-1.5 text-xs text-card-foreground text-right whitespace-nowrap font-mono"
                        title={isMissing ? "Sem restrição neste patamar" : (val === 0 ? "Restrição zero" : undefined)}
                      >
                        {isMissing ? "—" : formatNumber(val)}
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
