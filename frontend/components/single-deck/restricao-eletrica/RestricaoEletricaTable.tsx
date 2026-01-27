"use client";

import React, { useState } from "react";
import { Download, ChevronDown, ChevronUp } from "lucide-react";
import { formatInteger } from "../shared/formatters";
import { exportToCSV } from "../shared/csvExport";
import type { TableRow } from "../shared/types";

const INITIAL_ROWS = 10;

interface RestricaoEletricaTableProps {
  data: TableRow[];
}

export function RestricaoEletricaTable({ data }: RestricaoEletricaTableProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  
  if (!data || data.length === 0) {
    return null;
  }

  const hasMoreRows = data.length > INITIAL_ROWS;
  const displayedData = isExpanded ? data : data.slice(0, INITIAL_ROWS);

  const firstRow = data[0] || {};
  // Detectar formato DECOMP (Nome + GMIN/GMAX) vs formato antigo (restricao/patamar/periodo)
  const isDecompFormat =
    "Nome" in firstRow &&
    ("GMIN P1" in firstRow || "GMAX P1" in firstRow);
  
  // Usar sempre 3 patamares (P1, P2, P3)
  const maxPatamares = 3;

  const cellToCsv = (val: unknown): string =>
    val === null || val === undefined ? "N/A" : String(val);

  const handleDownloadCSV = () => {
    let csvData;
    if (isDecompFormat) {
      csvData = data.map((row) => {
        const csvRow: Record<string, string> = {
          Nome: (row["Nome"] ?? "") as string,
        };
        for (let i = 1; i <= maxPatamares; i++) {
          csvRow[`GMIN P${i}`] = cellToCsv(row[`GMIN P${i}`]);
          csvRow[`GMAX P${i}`] = cellToCsv(row[`GMAX P${i}`]);
        }
        return csvRow;
      });
    } else {
      csvData = data.map((row) => ({
        Restrição: row.restricao ? String(row.restricao) : "",
        Patamar: row.patamar ? String(row.patamar) : "",
        Período: row.periodo ? String(row.periodo) : "",
        "Limite Superior (MW)": row.limite_superior ?? null,
      }));
    }
    exportToCSV(csvData, "restricoes-eletricas");
  };

  return (
    <div className="bg-card border border-border rounded-lg p-4 sm:p-6">
      <div className="flex items-center justify-between mb-4 gap-2 flex-wrap">
        <div>
          <span className="text-sm text-muted-foreground block">
            {data.length} registros
          </span>
          {isDecompFormat && (
            <p className="text-[10px] text-muted-foreground mt-0.5" title="— = sem restrição neste patamar; 0 = restrição zero">
              — = sem restrição · 0 = restrição zero
            </p>
          )}
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
              {isDecompFormat ? (
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
              ) : (
                <tr className="border-b border-border bg-background/50">
                  <th className="px-3 sm:px-4 py-3 text-left text-xs font-semibold text-card-foreground uppercase tracking-wider">
                    Restrição
                  </th>
                  <th className="px-3 sm:px-4 py-3 text-left text-xs font-semibold text-card-foreground uppercase tracking-wider">
                    Patamar
                  </th>
                  <th className="px-3 sm:px-4 py-3 text-left text-xs font-semibold text-card-foreground uppercase tracking-wider">
                    Período
                  </th>
                  <th className="px-3 sm:px-4 py-3 text-right text-xs font-semibold text-card-foreground uppercase tracking-wider">
                    Limite Superior (MW)
                  </th>
                </tr>
              )}
            </thead>
            <tbody>
              {displayedData.map((row, index) => {
                if (isDecompFormat) {
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
                      {[...gminValues, ...gmaxValues].map((val, idx) => {
                        const isMissing = val === null || val === undefined;
                        return (
                          <td
                            key={idx}
                            className="px-3 sm:px-4 py-2.5 text-sm text-card-foreground text-right whitespace-nowrap font-mono"
                            title={isMissing ? "Sem restrição neste patamar" : (val === 0 ? "Restrição zero" : undefined)}
                          >
                            {isMissing ? "—" : formatInteger(Number(val))}
                          </td>
                        );
                      })}
                    </tr>
                  );
                } else {
                  const restricao = row.restricao ? String(row.restricao) : "";
                  const patamar = row.patamar ? String(row.patamar) : "";
                  const periodo = row.periodo ? String(row.periodo) : "";
                  const limiteSuperior = row.limite_superior ?? null;

                  return (
                    <tr
                      key={`${restricao}-${patamar}-${periodo}-${index}`}
                      className="border-b border-border/50 bg-background/20 hover:bg-background/40 transition-colors"
                    >
                      <td className="px-3 sm:px-4 py-2.5 text-sm text-card-foreground font-medium whitespace-nowrap">
                        {restricao}
                      </td>
                      <td className="px-3 sm:px-4 py-2.5 text-sm text-card-foreground whitespace-nowrap">
                        {patamar}
                      </td>
                      <td className="px-3 sm:px-4 py-2.5 text-sm text-card-foreground whitespace-nowrap">
                        {periodo}
                      </td>
                      <td className="px-3 sm:px-4 py-2.5 text-sm text-card-foreground text-right whitespace-nowrap font-mono">
                        {limiteSuperior !== null ? formatInteger(limiteSuperior as number) : "-"}
                      </td>
                    </tr>
                  );
                }
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
