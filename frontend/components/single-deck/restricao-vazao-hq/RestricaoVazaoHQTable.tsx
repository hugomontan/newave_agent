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

  const cellToCsv = (val: unknown): string =>
    val === null || val === undefined ? "N/A" : String(val);

  const handleDownloadCSV = () => {
    const csvData = data.map((row) => {
      const csvRow: Record<string, string> = {
        Nome: (row["Nome"] ?? "") as string,
      };
      for (let i = 1; i <= maxPatamares; i++) {
        csvRow[`VAZMIN P${i}`] = cellToCsv(row[`GMIN P${i}`]);
        csvRow[`VAZMAX P${i}`] = cellToCsv(row[`GMAX P${i}`]);
      }
      return csvRow;
    });
    exportToCSV(csvData, "restricoes-vazao-hq");
  };

  return (
    <div className="bg-card border border-border rounded-lg p-3 sm:p-4">
      <div className="flex items-center justify-between mb-3 gap-2 flex-wrap">
        <div>
          <span className="text-xs text-muted-foreground block">
            {data.length} registros
          </span>
          <p className="text-[10px] text-muted-foreground mt-0.5" title="— = sem restrição neste patamar; 0 = restrição zero">
            — = sem restrição · 0 = restrição zero
          </p>
        </div>
        <button
          onClick={handleDownloadCSV}
          className="flex items-center gap-1 px-2 py-1 text-xs font-medium text-card-foreground bg-background/50 hover:bg-background/70 border border-border rounded transition-colors"
          title="Baixar como CSV"
        >
          <Download className="w-3 h-3" />
          CSV
        </button>
      </div>

      <div className="w-full">
        <div className="inline-block w-full align-middle px-0">
          <table className="w-full table-fixed border-collapse bg-background/30">
            <thead>
              <tr className="border-b border-border bg-background/50">
                <th className="w-[28%] px-2 py-2 text-left text-[11px] font-semibold text-card-foreground uppercase tracking-tight">
                  Nome
                </th>
                {Array.from({ length: maxPatamares }, (_, i) => (
                  <th
                    key={`vazmin-${i + 1}`}
                    className="px-1.5 py-2 text-right text-[11px] font-semibold text-card-foreground uppercase tracking-tight"
                  >
                    VAZMIN P{i + 1}
                  </th>
                ))}
                {Array.from({ length: maxPatamares }, (_, i) => (
                  <th
                    key={`vazmax-${i + 1}`}
                    className="px-1.5 py-2 text-right text-[11px] font-semibold text-card-foreground uppercase tracking-tight"
                  >
                    VAZMAX P{i + 1}
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
                    <td className="w-[28%] px-2 py-1.5 text-xs text-card-foreground font-medium truncate" title={nome}>
                      {nome}
                    </td>
                    {[...gminValues, ...gmaxValues].map((val, idx) => {
                      const isMissing = val === null || val === undefined;
                      return (
                        <td
                          key={idx}
                          className="px-1.5 py-1.5 text-xs text-card-foreground text-right font-mono"
                          title={isMissing ? "Sem restrição neste patamar" : (val === 0 ? "Restrição zero" : undefined)}
                        >
                          {isMissing ? "—" : formatInteger(Number(val))}
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

      {hasMoreRows && (
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="mt-3 flex items-center gap-2 text-xs text-muted-foreground hover:text-card-foreground transition-colors"
        >
          {isExpanded ? (
            <>
              <ChevronUp className="w-3 h-3" />
              Mostrar menos
            </>
          ) : (
            <>
              <ChevronDown className="w-3 h-3" />
              Mostrar mais ({data.length - INITIAL_ROWS} registros)
            </>
          )}
        </button>
      )}
    </div>
  );
}
