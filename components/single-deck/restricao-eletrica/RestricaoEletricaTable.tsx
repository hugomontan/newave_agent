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

  const handleDownloadCSV = () => {
    let csvData;
    if (isDecompFormat) {
      csvData = data.map((row) => ({
        Nome: row["Nome"] ?? "",
        "GMIN P1": row["GMIN P1"] ?? 0,
        "GMIN P2": row["GMIN P2"] ?? 0,
        "GMIN P3": row["GMIN P3"] ?? 0,
        "GMAX P1": row["GMAX P1"] ?? 0,
        "GMAX P2": row["GMAX P2"] ?? 0,
        "GMAX P3": row["GMAX P3"] ?? 0,
      }));
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
          <table className="w-full border-collapse">
            <thead>
              {isDecompFormat ? (
                <tr className="border-b border-border bg-background/50">
                  <th className="px-3 sm:px-4 py-3 text-left text-xs font-semibold text-card-foreground uppercase tracking-wider">
                    Nome
                  </th>
                  <th className="px-3 sm:px-4 py-3 text-right text-xs font-semibold text-card-foreground uppercase tracking-wider">
                    GMIN P1
                  </th>
                  <th className="px-3 sm:px-4 py-3 text-right text-xs font-semibold text-card-foreground uppercase tracking-wider">
                    GMIN P2
                  </th>
                  <th className="px-3 sm:px-4 py-3 text-right text-xs font-semibold text-card-foreground uppercase tracking-wider">
                    GMIN P3
                  </th>
                  <th className="px-3 sm:px-4 py-3 text-right text-xs font-semibold text-card-foreground uppercase tracking-wider">
                    GMAX P1
                  </th>
                  <th className="px-3 sm:px-4 py-3 text-right text-xs font-semibold text-card-foreground uppercase tracking-wider">
                    GMAX P2
                  </th>
                  <th className="px-3 sm:px-4 py-3 text-right text-xs font-semibold text-card-foreground uppercase tracking-wider">
                    GMAX P3
                  </th>
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
                  const gmin1 = row["GMIN P1"] as number | null;
                  const gmin2 = row["GMIN P2"] as number | null;
                  const gmin3 = row["GMIN P3"] as number | null;
                  const gmax1 = row["GMAX P1"] as number | null;
                  const gmax2 = row["GMAX P2"] as number | null;
                  const gmax3 = row["GMAX P3"] as number | null;

                  return (
                    <tr
                      key={`${nome}-${index}`}
                      className="border-b border-border/50 hover:bg-background/30 transition-colors"
                    >
                      <td className="px-3 sm:px-4 py-2.5 text-sm text-card-foreground font-medium whitespace-nowrap">
                        {nome}
                      </td>
                      {[gmin1, gmin2, gmin3, gmax1, gmax2, gmax3].map((val, idx) => (
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
                } else {
                  const restricao = row.restricao ? String(row.restricao) : "";
                  const patamar = row.patamar ? String(row.patamar) : "";
                  const periodo = row.periodo ? String(row.periodo) : "";
                  const limiteSuperior = row.limite_superior ?? null;

                  return (
                    <tr
                      key={`${restricao}-${patamar}-${periodo}-${index}`}
                      className="border-b border-border/50 hover:bg-background/30 transition-colors"
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
