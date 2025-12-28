"use client";

import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import { ChevronDown, ChevronUp } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

interface Difference {
  field: string;
  period: string;
  deck_1_value: number;
  deck_2_value: number;
  difference: number;
  difference_percent: number;
}

interface DifferencesTableProps {
  differences: Difference[];
  deck1Name: string;
  deck2Name: string;
}

function formatNumber(value: number): string {
  if (value === null || value === undefined) return "-";
  return value.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function formatPercent(value: number): string {
  if (value === null || value === undefined) return "-";
  const sign = value >= 0 ? "+" : "";
  return `${sign}${value.toFixed(2)}%`;
}

export function DifferencesTable({ differences, deck1Name, deck2Name }: DifferencesTableProps) {
  const [isExpanded, setIsExpanded] = useState(true);
  const maxInitial = 50;
  const hasMore = differences.length > maxInitial;
  const displayedDifferences = isExpanded ? differences : differences.slice(0, maxInitial);

  console.log("[DifferencesTable] Renderizando:", differences?.length || 0, "diferenças");

  if (!differences || differences.length === 0) {
    return (
      <div className="bg-card border border-border rounded-lg p-4 sm:p-6 mt-4">
        <h3 className="text-base sm:text-lg font-semibold text-card-foreground mb-2">
          📊 Comparação de Dados
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
          📊 Comparação Mensal
        </h3>
        <span className="text-sm text-muted-foreground">
          {differences.length} registros
        </span>
      </div>

      <div className="overflow-x-auto -mx-4 sm:mx-0">
        <div className="inline-block min-w-full align-middle px-4 sm:px-0">
          <table className="min-w-full border-collapse">
            <thead>
              <tr className="border-b border-border bg-background/50">
                <th className="px-3 sm:px-4 py-3 text-left text-xs font-semibold text-card-foreground uppercase tracking-wider whitespace-nowrap">
                  Período
                </th>
                <th className="px-3 sm:px-4 py-3 text-right text-xs font-semibold text-blue-400 uppercase tracking-wider whitespace-nowrap">
                  {deck1Name}
                </th>
                <th className="px-3 sm:px-4 py-3 text-right text-xs font-semibold text-purple-400 uppercase tracking-wider whitespace-nowrap">
                  {deck2Name}
                </th>
                <th className="px-3 sm:px-4 py-3 text-right text-xs font-semibold text-card-foreground uppercase tracking-wider whitespace-nowrap">
                  Diferença (MWmed)
                </th>
                <th className="px-3 sm:px-4 py-3 text-right text-xs font-semibold text-card-foreground uppercase tracking-wider whitespace-nowrap">
                  Variação %
                </th>
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
                    <td className="px-3 sm:px-4 py-2.5 text-sm text-blue-400 text-right whitespace-nowrap font-mono">
                      {formatNumber(diff.deck_1_value)}
                    </td>
                    <td className="px-3 sm:px-4 py-2.5 text-sm text-purple-400 text-right whitespace-nowrap font-mono">
                      {formatNumber(diff.deck_2_value)}
                    </td>
                    <td className="px-3 sm:px-4 py-2.5 text-sm text-right whitespace-nowrap font-mono">
                      <span className={diff.difference >= 0 ? "text-green-400" : "text-red-400"}>
                        {diff.difference >= 0 ? "+" : ""}{formatNumber(diff.difference)}
                      </span>
                    </td>
                    <td className="px-3 sm:px-4 py-2.5 text-sm text-right whitespace-nowrap font-mono">
                      <span className={diff.difference_percent >= 0 ? "text-green-400" : "text-red-400"}>
                        {formatPercent(diff.difference_percent)}
                      </span>
                    </td>
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
