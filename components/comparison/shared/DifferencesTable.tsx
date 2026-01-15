"use client";

import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import { ChevronDown, ChevronUp, Download } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { formatNumber, formatMonth, formatPercent } from "./formatters";
import { exportToCSV } from "./csvExport";
import type { Difference } from "./types";

interface DifferencesTableProps {
  differences: Difference[];
  deck1Name: string;
  deck2Name: string;
  firstColumnLabel?: string;  // Label da primeira coluna ("Usina" ou "Ano")
}

export function DifferencesTable({ differences, deck1Name, deck2Name, firstColumnLabel = "Usina" }: DifferencesTableProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const maxInitial = 15;
  const hasMore = differences.length > maxInitial;
  const displayedDifferences = isExpanded ? differences : differences.slice(0, maxInitial);

  const handleDownloadCSV = () => {
    const hasMes = differences.some(d => d.mes !== undefined && d.mes !== null);
    const hasPeriodoColuna = differences.some(d => d.periodo_coluna);
    const hasDifference = differences.some(d => !d.is_inclusao_ou_exclusao && d.difference !== null && d.difference !== undefined);

    const csvData = differences.map((diff) => {
      const row: Record<string, string | number | null> = {
        [firstColumnLabel]: diff.period,
        [deck1Name]: diff.deck_1_value ?? null,
        [deck2Name]: diff.deck_2_value ?? null,
      };
      if (hasMes && diff.mes !== undefined && diff.mes !== null) {
        row.Mês = formatMonth(diff.mes);
      }
      if (hasPeriodoColuna && diff.periodo_coluna) {
        row.Período = diff.periodo_coluna;
      }
      if (hasDifference && !diff.is_inclusao_ou_exclusao && diff.difference !== null && diff.difference !== undefined) {
        row.Diferença = diff.difference;
        row["Variação %"] = diff.difference_percent ?? null;
      }
      return row;
    });
    exportToCSV(csvData, "comparacao");
  };

  console.log("[DifferencesTable] Renderizando:", differences?.length || 0, "diferenças");

  if (!differences || differences.length === 0) {
    return (
      <div className="bg-card border border-border rounded-lg p-4 sm:p-6 mt-4">
        <h3 className="text-base sm:text-lg font-semibold text-card-foreground mb-2">
           Comparação de Dados
        </h3>
        <p className="text-sm text-muted-foreground">
          Nenhuma diferença encontrada entre os decks.
        </p>
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-card border border-border rounded-lg p-4 sm:p-6 mt-4"
    >
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-base sm:text-lg font-semibold text-card-foreground">
           Tabela Comparativa
        </h3>
        <div className="flex items-center gap-3">
          <span className="text-sm text-muted-foreground">
            {differences.length} registros
          </span>
          <button
            onClick={handleDownloadCSV}
            className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-card-foreground bg-background/50 hover:bg-background/70 border border-border rounded-lg transition-colors"
            title="Baixar como CSV"
          >
            <Download className="w-4 h-4" />
            CSV
          </button>
        </div>
      </div>

      <div className="overflow-x-auto -mx-4 sm:mx-0">
        <div className="inline-block min-w-full align-middle px-4 sm:px-0">
          <table className="min-w-full border-collapse">
            <thead>
              <tr className="border-b border-border bg-background/50">
                <th className="px-3 sm:px-4 py-3 text-left text-xs font-semibold text-card-foreground uppercase tracking-wider whitespace-nowrap">
                  {firstColumnLabel}
                </th>
                {differences.some(d => d.mes !== undefined && d.mes !== null) && (
                  <th className="px-3 sm:px-4 py-3 text-left text-xs font-semibold text-card-foreground uppercase tracking-wider whitespace-nowrap">
                    Mês
                  </th>
                )}
                {differences.some(d => d.periodo_coluna) && (
                  <th className="px-3 sm:px-4 py-3 text-left text-xs font-semibold text-card-foreground uppercase tracking-wider whitespace-nowrap">
                    Período
                  </th>
                )}
                <th className="px-3 sm:px-4 py-3 text-right text-xs font-semibold text-blue-400 uppercase tracking-wider whitespace-nowrap">
                  {deck1Name}
                </th>
                <th className="px-3 sm:px-4 py-3 text-right text-xs font-semibold text-purple-400 uppercase tracking-wider whitespace-nowrap">
                  {deck2Name}
                </th>
                {/* Mostrar colunas de diferença/variação apenas se houver pelo menos uma linha que não seja inclusão/exclusão */}
                {differences.some(d => !d.is_inclusao_ou_exclusao && d.difference !== null && d.difference !== undefined) && (
                  <>
                    <th className="px-3 sm:px-4 py-3 text-right text-xs font-semibold text-card-foreground uppercase tracking-wider whitespace-nowrap">
                      Diferença
                    </th>
                    <th className="px-3 sm:px-4 py-3 text-right text-xs font-semibold text-card-foreground uppercase tracking-wider whitespace-nowrap">
                      Variação %
                    </th>
                  </>
                )}
              </tr>
            </thead>
            <tbody>
              <AnimatePresence>
                {displayedDifferences.map((diff, index) => (
                  <motion.tr
                    key={`${diff.period}-${index}`}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="border-b border-border/50 hover:bg-background/30 transition-colors"
                  >
                    <td className="px-3 sm:px-4 py-2.5 text-sm text-card-foreground font-medium whitespace-nowrap">
                      {diff.period}
                    </td>
                    {diff.mes !== undefined && diff.mes !== null && (
                      <td className="px-3 sm:px-4 py-2.5 text-sm text-muted-foreground whitespace-nowrap">
                        {formatMonth(diff.mes)}
                      </td>
                    )}
                    {diff.periodo_coluna && (
                      <td className="px-3 sm:px-4 py-2.5 text-sm text-muted-foreground whitespace-nowrap">
                        {diff.periodo_coluna}
                      </td>
                    )}
                    <td className="px-3 sm:px-4 py-2.5 text-sm text-blue-400 text-right whitespace-nowrap font-mono">
                      {formatNumber(diff.deck_1_value)}
                    </td>
                    <td className="px-3 sm:px-4 py-2.5 text-sm text-purple-400 text-right whitespace-nowrap font-mono">
                      {formatNumber(diff.deck_2_value)}
                    </td>
                    {!diff.is_inclusao_ou_exclusao && diff.difference !== null && diff.difference !== undefined && (
                      <>
                        <td className="px-3 sm:px-4 py-2.5 text-sm text-right whitespace-nowrap font-mono">
                          <span className={diff.difference >= 0 ? "text-green-400" : "text-red-400"}>
                            {diff.difference >= 0 ? "+" : ""}{formatNumber(diff.difference)}
                          </span>
                        </td>
                        <td className="px-3 sm:px-4 py-2.5 text-sm text-right whitespace-nowrap font-mono">
                          <span className={(diff.difference_percent ?? 0) >= 0 ? "text-green-400" : "text-red-400"}>
                            {formatPercent(diff.difference_percent ?? 0)}
                          </span>
                        </td>
                      </>
                    )}
                  </motion.tr>
                ))}
              </AnimatePresence>
            </tbody>
          </table>
        </div>
      </div>

      {hasMore && (
        <div className="mt-4 flex justify-center">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setIsExpanded(!isExpanded)}
            className="text-foreground border-border hover:bg-background"
          >
            {isExpanded ? (
              <>
                <ChevronUp className="w-4 h-4 mr-2" />
                Mostrar menos
              </>
            ) : (
              <>
                <ChevronDown className="w-4 h-4 mr-2" />
                Mostrar todos ({differences.length - maxInitial} restantes)
              </>
            )}
          </Button>
        </div>
      )}

      <p className="text-xs text-muted-foreground mt-4 pt-3 border-t border-border/50">
        <strong>Nota:</strong> A diferença é calculada como {deck2Name} − {deck1Name}. 
        Valores positivos indicam aumento, negativos indicam redução.
      </p>
    </motion.div>
  );
}
