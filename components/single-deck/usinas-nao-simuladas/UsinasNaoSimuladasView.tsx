"use client";

import React, { useState } from "react";
import { motion } from "framer-motion";
import { Download, ChevronDown, ChevronUp } from "lucide-react";
import { exportToCSV } from "../shared/csvExport";
import type { SingleDeckVisualizationData, TableRow } from "../shared/types";

interface UsinasNaoSimuladasViewProps {
  visualizationData: SingleDeckVisualizationData;
}

export function UsinasNaoSimuladasView({ visualizationData }: UsinasNaoSimuladasViewProps) {
  const { table, tables_by_fonte } = visualizationData;
  const [expandedFontes, setExpandedFontes] = useState<Set<string>>(new Set());

  if (!table || table.length === 0) {
    return (
      <div className="bg-card border border-border rounded-lg p-4 sm:p-6 mt-4">
        <h3 className="text-base sm:text-lg font-semibold text-card-foreground mb-2">
          Usinas Não Simuladas
        </h3>
        <p className="text-sm text-muted-foreground">Nenhum dado disponível.</p>
      </div>
    );
  }

  // Se houver múltiplas fontes, renderizar tabelas separadas
  const hasMultipleFontes = tables_by_fonte && Object.keys(tables_by_fonte).length > 1;

  const toggleExpand = (fonte: string) => {
    const newExpanded = new Set(expandedFontes);
    if (newExpanded.has(fonte)) {
      newExpanded.delete(fonte);
    } else {
      newExpanded.add(fonte);
    }
    setExpandedFontes(newExpanded);
  };

  const renderTable = (tableData: Array<Record<string, any>>, fonte?: string) => {
    const columns = ["data", "fonte", "valor"];
    const title = fonte ? `Fonte: ${fonte}` : "Usinas Não Simuladas";
    const fonteKey = fonte || "single";
    const isExpanded = expandedFontes.has(fonteKey);
    const INITIAL_ROWS = 10;
    const shouldShowExpand = tableData.length > INITIAL_ROWS;
    const displayData = shouldShowExpand && !isExpanded 
      ? tableData.slice(0, INITIAL_ROWS) 
      : tableData;

    return (
      <div key={fonteKey} className="bg-card border border-border rounded-lg p-4 sm:p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-base sm:text-lg font-semibold text-card-foreground">
            {title}
            {shouldShowExpand && (
              <span className="ml-2 text-sm font-normal text-muted-foreground">
                ({tableData.length} registros)
              </span>
            )}
          </h3>
          <button
            onClick={() => exportToCSV(tableData, `usinas-nao-simuladas${fonte ? `-${fonte}` : ""}`)}
            className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-card-foreground bg-background/50 hover:bg-background/70 border border-border rounded-lg transition-colors"
          >
            <Download className="w-4 h-4" />
            CSV
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full border-collapse">
            <thead>
              <tr className="border-b border-border bg-background/50">
                {columns.map((col) => (
                  <th
                    key={col}
                    className="px-4 py-3 text-left text-xs font-semibold text-card-foreground uppercase"
                  >
                    {col === "data" ? "Data (MM-YYYY)" : col === "valor" ? "Valor (MWméd)" : col}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {displayData.map((row, index) => (
                <tr
                  key={index}
                  className="border-b border-border/50 hover:bg-background/30"
                >
                  {columns.map((col) => (
                    <td key={col} className="px-4 py-2.5 text-sm text-card-foreground">
                      {row[col] !== null && row[col] !== undefined ? String(row[col]) : "-"}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {shouldShowExpand && (
          <div className="mt-4 flex justify-center">
            <button
              onClick={() => toggleExpand(fonteKey)}
              className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-card-foreground bg-background/50 hover:bg-background/70 border border-border rounded-lg transition-colors"
            >
              {isExpanded ? (
                <>
                  <ChevronUp className="w-4 h-4" />
                  Mostrar menos
                </>
              ) : (
                <>
                  <ChevronDown className="w-4 h-4" />
                  Mostrar todos ({tableData.length - INITIAL_ROWS} mais)
                </>
              )}
            </button>
          </div>
        )}
      </div>
    );
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="w-full mt-4 space-y-4"
    >
      {hasMultipleFontes && tables_by_fonte ? (
        // Renderizar tabela separada para cada fonte
        Object.entries(tables_by_fonte).map(([fonte, tableData]) => (
          renderTable(tableData as Array<Record<string, any>>, fonte)
        ))
      ) : (
        // Renderizar tabela única
        renderTable(table as Array<Record<string, any>>)
      )}
    </motion.div>
  );
}
