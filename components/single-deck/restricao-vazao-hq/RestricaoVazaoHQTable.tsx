"use client";

import React, { useState } from "react";
import { Download, ChevronDown, ChevronUp } from "lucide-react";
import { formatInteger } from "../shared/formatters";
import { exportToCSV } from "../shared/csvExport";
import type { TableRow } from "../shared/types";

const INITIAL_ROWS = 10;

interface RestricaoVazaoHQTableProps {
  data: TableRow[];
}

export function RestricaoVazaoHQTable({ data }: RestricaoVazaoHQTableProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  
  if (!data || data.length === 0) {
    return null;
  }

  const hasMoreRows = data.length > INITIAL_ROWS;
  const displayedData = isExpanded ? data : data.slice(0, INITIAL_ROWS);

  const maxPatamares = 3;

  const handleDownloadCSV = () => {
    const csvData = data.map((row) => {
      const csvRow: Record<string, any> = {
        Nome: row["Nome"] ?? "",
      };
      for (let i = 1; i <= maxPatamares; i++) {
        csvRow[`GMIN P${i}`] = row[`GMIN P${i}`] ?? null;
        csvRow[`GMAX P${i}`] = row[`GMAX P${i}`] ?? null;
      }
      return csvRow;
    });
    exportToCSV(csvData, "restricoes-vazao-hq");
  };

  return (
    <div className="bg-card border border-border rounded-lg p-4 sm:p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
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
        <div className="inline-block w-full align-middle px-0">
          <table className="w-full border-collapse bg-background/30">
            <thead>
              <tr className="border-b border-border bg-background/50">
                <th className="px-3 sm:px-4 py-3 text-left text-xs font-semibold text-card-foreground uppercase tracking-wider">
                  Nome
                </th>
                {Array.from({ length: maxPatamares }, (_, i) => (
                  <th
                    key={`gmin-${i + 1}`}
                    className="px-3 sm:px-4 py-3 text-right text-xs font-semibold text-card-foreground uppercase tracking-wider"
                  >
                    GMIN P{i + 1}
                  </th>
                ))}
                {Array.from({ length: maxPatamares }, (_, i) => (
                  <th
                    key={`gmax-${i + 1}`}
                    className="px-3 sm:px-4 py-3 text-right text-xs font-semibold text-card-foreground uppercase tracking-wider"
                  >
                    GMAX P{i + 1}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {displayedData.map((row, index) => {
                const nome = (row["Nome"] ?? "") as string;
                const gminValues: (number | null)[] = [];
                const gmaxValues: (number | null)[] = [];
                
                for (let i = 1; i <= maxPatamares; i++) {
                  gminValues.push(row[`GMIN P${i}`] as number | null | undefined ?? null);
                  gmaxValues.push(row[`GMAX P${i}`] as number | null | undefined ?? null);
                }

                return (
                  <tr
                    key={`${nome}-${index}`}
                    className="border-b border-border/50 bg-background/20 hover:bg-background/40 transition-colors"
                  >
                    <td className="px-3 sm:px-4 py-2.5 text-sm text-card-foreground font-medium whitespace-nowrap">
                      {nome}
                    </td>
                    {[...gminValues, ...gmaxValues].map((val, idx) => (
                      <td
                        key={idx}
                        className="px-3 sm:px-4 py-2.5 text-sm text-card-foreground text-right whitespace-nowrap font-mono"
                      >
                        {val !== null && val !== undefined
                          ? formatInteger(Number(val))
                          : "0"}
                      </td>
                    ))}
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
