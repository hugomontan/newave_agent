"use client";

import React, { useState } from "react";
import { formatNumber } from "../shared/formatters";
import { exportToCSV } from "../shared/csvExport";
import type { TableRow } from "../shared/types";
import { Download, ChevronDown, ChevronUp } from "lucide-react";
import { Button } from "@/components/ui/button";

interface RestricoesEletricasComparisonTableProps {
  data: TableRow[];
}

export function RestricoesEletricasComparisonTable({ 
  data
}: RestricoesEletricasComparisonTableProps) {
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
        Deck: rowData.display_name || rowData.deck || "",
        Nome: rowData.Nome || "",
        "GMIN P1": rowData["GMIN P1"] ?? "",
        "GMIN P2": rowData["GMIN P2"] ?? "",
        "GMIN P3": rowData["GMIN P3"] ?? "",
        "GMAX P1": rowData["GMAX P1"] ?? "",
        "GMAX P2": rowData["GMAX P2"] ?? "",
        "GMAX P3": rowData["GMAX P3"] ?? "",
      };
    });
    exportToCSV(csvData, "restricoes-eletricas-comparison");
  };

  return (
    <div className="bg-card border border-border rounded-lg p-3.5 sm:p-4.5 max-w-full">
      <div className="flex items-center justify-between mb-4">
        <h4 className="text-base sm:text-lg font-semibold text-card-foreground">
          Valores por Deck
        </h4>
        <div className="flex items-center gap-2">
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
            <col style={{ minWidth: '120px' }} />
            <col style={{ minWidth: '180px' }} />
            <col style={{ minWidth: '150px' }} />
            <col style={{ minWidth: '100px' }} />
            <col style={{ minWidth: '100px' }} />
            <col style={{ minWidth: '100px' }} />
            <col style={{ minWidth: '100px' }} />
            <col style={{ minWidth: '100px' }} />
            <col style={{ minWidth: '100px' }} />
          </colgroup>
          <thead>
            <tr className="border-b border-border bg-background/50">
              <th className="px-3.5 sm:px-4.5 py-2.5 text-left text-xs font-semibold text-card-foreground uppercase tracking-wider whitespace-nowrap">
                Deck
              </th>
              <th className="px-3.5 sm:px-4.5 py-2.5 text-left text-xs font-semibold text-card-foreground uppercase tracking-wider whitespace-nowrap">
                Nome
              </th>
              <th className="px-3.5 sm:px-4.5 py-2.5 text-right text-xs font-semibold text-card-foreground uppercase tracking-wider whitespace-nowrap">
                GMIN P1 (MW)
              </th>
              <th className="px-3.5 sm:px-4.5 py-2.5 text-right text-xs font-semibold text-card-foreground uppercase tracking-wider whitespace-nowrap">
                GMIN P2 (MW)
              </th>
              <th className="px-3.5 sm:px-4.5 py-2.5 text-right text-xs font-semibold text-card-foreground uppercase tracking-wider whitespace-nowrap">
                GMIN P3 (MW)
              </th>
              <th className="px-3.5 sm:px-4.5 py-2.5 text-right text-xs font-semibold text-card-foreground uppercase tracking-wider whitespace-nowrap">
                GMAX P1 (MW)
              </th>
              <th className="px-3.5 sm:px-4.5 py-2.5 text-right text-xs font-semibold text-card-foreground uppercase tracking-wider whitespace-nowrap">
                GMAX P2 (MW)
              </th>
              <th className="px-3.5 sm:px-4.5 py-2.5 text-right text-xs font-semibold text-card-foreground uppercase tracking-wider whitespace-nowrap">
                GMAX P3 (MW)
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
                    {rowData.display_name || rowData.deck || "-"}
                  </td>
                  <td className="px-3.5 sm:px-4.5 py-2.5 text-sm text-card-foreground font-medium whitespace-nowrap">
                    {rowData.Nome || "-"}
                  </td>
                  <td className="px-3.5 sm:px-4.5 py-2.5 text-sm text-card-foreground text-right whitespace-nowrap font-mono">
                    {rowData["GMIN P1"] !== null && rowData["GMIN P1"] !== undefined 
                      ? formatNumber(rowData["GMIN P1"])
                      : "-"
                    }
                  </td>
                  <td className="px-3.5 sm:px-4.5 py-2.5 text-sm text-card-foreground text-right whitespace-nowrap font-mono">
                    {rowData["GMIN P2"] !== null && rowData["GMIN P2"] !== undefined 
                      ? formatNumber(rowData["GMIN P2"])
                      : "-"
                    }
                  </td>
                  <td className="px-3.5 sm:px-4.5 py-2.5 text-sm text-card-foreground text-right whitespace-nowrap font-mono">
                    {rowData["GMIN P3"] !== null && rowData["GMIN P3"] !== undefined 
                      ? formatNumber(rowData["GMIN P3"])
                      : "-"
                    }
                  </td>
                  <td className="px-3.5 sm:px-4.5 py-2.5 text-sm text-card-foreground text-right whitespace-nowrap font-mono">
                    {rowData["GMAX P1"] !== null && rowData["GMAX P1"] !== undefined 
                      ? formatNumber(rowData["GMAX P1"])
                      : "-"
                    }
                  </td>
                  <td className="px-3.5 sm:px-4.5 py-2.5 text-sm text-card-foreground text-right whitespace-nowrap font-mono">
                    {rowData["GMAX P2"] !== null && rowData["GMAX P2"] !== undefined 
                      ? formatNumber(rowData["GMAX P2"])
                      : "-"
                    }
                  </td>
                  <td className="px-3.5 sm:px-4.5 py-2.5 text-sm text-card-foreground text-right whitespace-nowrap font-mono">
                    {rowData["GMAX P3"] !== null && rowData["GMAX P3"] !== undefined 
                      ? formatNumber(rowData["GMAX P3"])
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
