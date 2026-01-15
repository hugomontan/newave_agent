"use client";

import React from "react";
import { motion } from "framer-motion";

interface MatrixCell {
  value: number | null;
  difference: number | null;
}

interface MatrixRow {
  nome_usina: string;
  codigo_usina: number;
  periodo_inicio: string;
  periodo_fim: string;
  gtmin_values: Record<string, number | null>;
  matrix: Record<string, number | null>;
}

interface GTMINMatrixTableProps {
  matrixData: MatrixRow[];
  deckNames: string[];
}

export function GTMINMatrixTable({ matrixData, deckNames }: GTMINMatrixTableProps) {
  if (!matrixData || matrixData.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        Nenhum dado disponível para exibição.
      </div>
    );
  }

  // Função para formatar valor
  const formatValue = (value: number | null | undefined): string => {
    if (value === null || value === undefined) return "-";
    return value.toFixed(2);
  };

  // Função para obter cor da célula baseada na diferença
  const getCellColor = (difference: number | null): string => {
    if (difference === null || difference === undefined) return "bg-muted/30";
    if (difference > 0) return "bg-green-500/20 border-green-500/50";
    if (difference < 0) return "bg-red-500/20 border-red-500/50";
    return "bg-muted/30";
  };

  // Função para obter cor do texto baseada na diferença
  const getTextColor = (difference: number | null): string => {
    if (difference === null || difference === undefined) return "text-muted-foreground";
    if (difference > 0) return "text-green-600 dark:text-green-400";
    if (difference < 0) return "text-red-600 dark:text-red-400";
    return "text-foreground";
  };

  return (
    <div className="w-full space-y-6 overflow-x-auto">
      {matrixData.map((row, rowIndex) => {
        const periodoStr = 
          row.periodo_inicio !== "N/A" && row.periodo_fim !== "N/A"
            ? `${row.periodo_inicio} a ${row.periodo_fim}`
            : row.periodo_inicio !== "N/A"
            ? row.periodo_inicio
            : row.periodo_fim !== "N/A"
            ? row.periodo_fim
            : "N/A";

        return (
          <motion.div
            key={`${row.codigo_usina}-${row.periodo_inicio}-${row.periodo_fim}`}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: rowIndex * 0.05 }}
            className="bg-card rounded-lg border border-border p-4 space-y-3"
          >
            {/* Cabeçalho da usina */}
            <div className="flex items-center justify-between border-b border-border pb-2">
              <div>
                <h3 className="text-lg font-semibold text-card-foreground">
                  {row.nome_usina}
                </h3>
                <p className="text-sm text-muted-foreground">
                  Código: {row.codigo_usina} | Período: {periodoStr}
                </p>
              </div>
            </div>

            {/* Tabela de matriz */}
            <div className="overflow-x-auto">
              <table className="w-full border-collapse">
                <thead>
                  <tr>
                    <th className="border border-border bg-muted/50 px-3 py-2 text-left text-sm font-semibold text-card-foreground sticky left-0 z-10">
                      De \ Para
                    </th>
                    {deckNames.map((deckName) => (
                      <th
                        key={deckName}
                        className="border border-border bg-muted/50 px-3 py-2 text-center text-sm font-semibold text-card-foreground min-w-[100px]"
                      >
                        {deckName}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {deckNames.map((deckFrom, fromIndex) => (
                    <tr key={deckFrom}>
                      <td className="border border-border bg-muted/30 px-3 py-2 text-sm font-medium text-card-foreground sticky left-0 z-10">
                        {deckFrom}
                      </td>
                      {deckNames.map((deckTo, toIndex) => {
                        const matrixKey = `${deckFrom},${deckTo}`;
                        const difference = row.matrix[matrixKey] ?? null;
                        const isDiagonal = fromIndex === toIndex;
                        
                        return (
                          <td
                            key={deckTo}
                            className={`border border-border px-3 py-2 text-center text-sm ${getCellColor(difference)} ${getTextColor(difference)}`}
                          >
                            {isDiagonal ? (
                              <span className="text-muted-foreground">-</span>
                            ) : difference !== null ? (
                              <div className="flex flex-col items-center">
                                <span className="font-medium">
                                  {difference > 0 ? "+" : ""}{formatValue(difference)}
                                </span>
                                {row.gtmin_values[deckFrom] !== null && row.gtmin_values[deckFrom] !== undefined && (
                                  <span className="text-xs text-muted-foreground mt-1">
                                    ({formatValue(row.gtmin_values[deckFrom])} → {formatValue(row.gtmin_values[deckTo] ?? null)})
                                  </span>
                                )}
                              </div>
                            ) : (
                              <span className="text-muted-foreground">-</span>
                            )}
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Valores absolutos por deck */}
            <div className="mt-4 pt-3 border-t border-border">
              <h4 className="text-sm font-semibold text-card-foreground mb-2">
                Valores de GTMIN por Deck:
              </h4>
              <div className="flex flex-wrap gap-2">
                {deckNames.map((deckName) => {
                  const value = row.gtmin_values[deckName];
                  return (
                    <div
                      key={deckName}
                      className="bg-muted/30 rounded px-3 py-1 text-sm"
                    >
                      <span className="font-medium text-card-foreground">{deckName}:</span>{" "}
                      <span className="text-muted-foreground">
                        {value !== null && value !== undefined ? formatValue(value) : "-"}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          </motion.div>
        );
      })}
    </div>
  );
}
