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
  if (value === 0) return "0.00";
  return value.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function formatPercent(value: number): string {
  if (value === 0) return "0.00%";
  const sign = value >= 0 ? "+" : "";
  return `${sign}${value.toFixed(2)}%`;
}

export function DifferencesTable({ differences, deck1Name, deck2Name }: DifferencesTableProps) {
  const [isExpanded, setIsExpanded] = useState(true); // Iniciar expandido por padrão
  const maxInitial = 50;
  const hasMore = differences.length > maxInitial;
  const displayedDifferences = isExpanded ? differences : differences.slice(0, maxInitial);

  if (differences.length === 0) {
    return null;
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-card border border-border rounded-lg p-4 sm:p-6 mt-4"
    >
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-base sm:text-lg font-semibold text-card-foreground">
          ⚠️ Discrepâncias Encontradas
        </h3>
        <span className="text-sm text-muted-foreground">
          Total: {differences.length}
        </span>
      </div>

      <div className="overflow-x-auto -mx-4 sm:mx-0">
        <div className="inline-block min-w-full align-middle px-4 sm:px-0">
          <table className="min-w-full border-collapse">
            <thead>
              <tr className="border-b border-border">
                <th className="px-3 sm:px-4 py-2 text-left text-xs font-medium text-card-foreground uppercase tracking-wider bg-background whitespace-nowrap">
                  Período
                </th>
                <th className="px-3 sm:px-4 py-2 text-left text-xs font-medium text-card-foreground uppercase tracking-wider bg-background whitespace-nowrap">
                  {deck1Name}
                </th>
                <th className="px-3 sm:px-4 py-2 text-left text-xs font-medium text-card-foreground uppercase tracking-wider bg-background whitespace-nowrap">
                  {deck2Name}
                </th>
                <th className="px-3 sm:px-4 py-2 text-left text-xs font-medium text-card-foreground uppercase tracking-wider bg-background whitespace-nowrap">
                  Diferença Nominal
                </th>
                <th className="px-3 sm:px-4 py-2 text-left text-xs font-medium text-card-foreground uppercase tracking-wider bg-background whitespace-nowrap">
                  Diferença %
                </th>
              </tr>
            </thead>
            <tbody>
              <AnimatePresence>
                {displayedDifferences.map((diff, index) => (
                  <motion.tr
                    key={index}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="border-b border-border hover:bg-background transition-colors"
                  >
                    <td className="px-3 sm:px-4 py-2 text-xs sm:text-sm text-card-foreground/90 whitespace-nowrap">
                      {diff.period}
                    </td>
                    <td className="px-3 sm:px-4 py-2 text-xs sm:text-sm text-card-foreground/90 whitespace-nowrap">
                      {formatNumber(diff.deck_1_value)}
                    </td>
                    <td className="px-3 sm:px-4 py-2 text-xs sm:text-sm text-card-foreground/90 whitespace-nowrap">
                      {formatNumber(diff.deck_2_value)}
                    </td>
                    <td className="px-3 sm:px-4 py-2 text-xs sm:text-sm whitespace-nowrap">
                      <span className={diff.difference >= 0 ? "text-green-400" : "text-red-400"}>
                        {formatNumber(diff.difference)}
                      </span>
                    </td>
                    <td className="px-3 sm:px-4 py-2 text-xs sm:text-sm whitespace-nowrap">
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
                Ocultar Diferenças ({differences.length - maxInitial} ocultas)
              </>
            ) : (
              <>
                <ChevronDown className="w-4 h-4 mr-2" />
                Expandir Todas as Diferenças ({differences.length - maxInitial} adicionais)
              </>
            )}
          </Button>
        </div>
      )}

      <p className="text-xs text-muted-foreground mt-4">
        Nota: Diferenças são consideradas significativas quando excedem 0.1% de diferença relativa ou 0.01 de diferença absoluta. 
        A diferença nominal é calculada como {deck2Name} - {deck1Name}, e a diferença percentual mantém o sinal (valores positivos indicam aumento, negativos indicam redução).
      </p>
    </motion.div>
  );
}

