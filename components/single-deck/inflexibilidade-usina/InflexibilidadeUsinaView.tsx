"use client";

import React from "react";
import { motion } from "framer-motion";
import { formatNumber } from "../shared/formatters";
import type { SingleDeckVisualizationData } from "../shared/types";

interface InflexibilidadeUsinaViewProps {
  visualizationData: SingleDeckVisualizationData;
}

export function InflexibilidadeUsinaView({ visualizationData }: InflexibilidadeUsinaViewProps) {
  const { inflexibilidade_total, detalhes_patamares, usina } = visualizationData;

  // Verificar se inflexibilidade_total é null ou undefined (não apenas falsy)
  // 0 é um valor válido quando inflexibilidades são zeradas
  if (inflexibilidade_total === null || inflexibilidade_total === undefined) {
    return (
      <div className="bg-card border border-border rounded-lg p-4 sm:p-6">
        <p className="text-sm text-muted-foreground">
          Dados de inflexibilidade não disponíveis.
        </p>
      </div>
    );
  }

  const nomeUsina = usina?.nome || `Usina ${usina?.codigo || "N/A"}`;
  const codigoUsina = usina?.codigo;

  // Cores apenas para o texto do patamar
  const getPatamarTextColor = (patamar: string) => {
    switch (patamar) {
      case "PESADA":
        return "text-red-600 dark:text-red-400";
      case "MEDIA":
        return "text-yellow-600 dark:text-yellow-400";
      case "LEVE":
        return "text-green-600 dark:text-green-400";
      default:
        return "text-card-foreground";
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="w-full space-y-6 mt-4"
    >
      {/* Header com informações da usina */}
      <div className="bg-card border border-border rounded-lg p-4 sm:p-6">
        <h3 className="text-base sm:text-lg font-semibold text-card-foreground mb-2">
          Inflexibilidade Total - {nomeUsina}
        </h3>
        <p className="text-sm text-muted-foreground">
          Código: {codigoUsina} | Submercado: {usina?.submercado}
        </p>
      </div>

      {/* Tabela de dados por patamar */}
      {detalhes_patamares && detalhes_patamares.length > 0 && (
        <div className="bg-card border border-border rounded-lg p-4 sm:p-6">
          <h4 className="text-base sm:text-lg font-semibold text-card-foreground mb-4">
            Dados
          </h4>
          <div className="w-full overflow-x-auto">
            <table className="w-full min-w-[600px] border-collapse">
            <thead>
              <tr className="border-b border-border bg-background/50">
                <th className="px-3 sm:px-4 py-3 text-left text-xs font-semibold text-card-foreground uppercase tracking-wider">
                  Patamar
                </th>
                <th className="px-3 sm:px-4 py-3 text-right text-xs font-semibold text-card-foreground uppercase tracking-wider">
                  Inflexibilidade (MW)
                </th>
                <th className="px-3 sm:px-4 py-3 text-right text-xs font-semibold text-card-foreground uppercase tracking-wider">
                  Duração (horas)
                </th>
              </tr>
            </thead>
            <tbody>
              {detalhes_patamares.map((patamar, index) => (
                <tr
                  key={`${patamar.patamar}-${index}`}
                  className="border-b border-border/50 hover:bg-background/30 transition-colors"
                >
                  <td className={`px-3 sm:px-4 py-2.5 text-sm font-medium ${getPatamarTextColor(patamar.patamar)}`}>
                    {patamar.patamar}
                  </td>
                  <td className="px-3 sm:px-4 py-2.5 text-sm text-card-foreground text-right font-mono">
                    {formatNumber(patamar.inflexibilidade)}
                  </td>
                  <td className="px-3 sm:px-4 py-2.5 text-sm text-card-foreground text-right font-mono">
                    {formatNumber(patamar.duracao)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          </div>
        </div>
      )}

      {/* Card de Inflexibilidade Total */}
      <div className="bg-card border border-border rounded-lg p-4 sm:p-6">
        <div>
          <p className="text-sm text-muted-foreground mb-1">Inflexibilidade Total</p>
          <p className="text-3xl sm:text-4xl font-bold text-card-foreground">
            {formatNumber(inflexibilidade_total)} <span className="text-lg font-normal text-muted-foreground">MW</span>
          </p>
        </div>
      </div>
    </motion.div>
  );
}
