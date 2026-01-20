"use client";

import React from "react";
import { motion } from "framer-motion";
import { CargaAndeTable } from "./CargaAndeTable";
import { formatNumber } from "../shared/formatters";
import type { SingleDeckVisualizationData } from "../shared/types";

interface CargaAndeViewProps {
  visualizationData: SingleDeckVisualizationData;
}

export function CargaAndeView({ visualizationData }: CargaAndeViewProps) {
  const { table, mw_medios } = visualizationData;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="w-full mt-4 space-y-6"
    >
      {/* Tabela de Carga ANDE */}
      {table && table.length > 0 && (
        <CargaAndeTable data={table as any} />
      )}

      {/* Carga ANDE Média Ponderada (quando houver cálculo) */}
      {mw_medios && mw_medios.length > 0 && (
        <div className="bg-card border border-border rounded-lg p-4 sm:p-6">
          <div>
            <p className="text-sm text-muted-foreground mb-1">Carga ANDE Média Ponderada</p>
            {mw_medios.map((mw: any, index: number) => (
              <div key={index} className="mb-2 last:mb-0">
                <p className="text-3xl sm:text-4xl font-bold text-card-foreground">
                  {formatNumber(mw.mw_medio)}{" "}
                  <span className="text-lg font-normal text-muted-foreground">MWmed</span>
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {(!table || table.length === 0) && (!mw_medios || mw_medios.length === 0) && (
        <div className="bg-card border border-border rounded-lg p-4 sm:p-6">
          <p className="text-sm text-muted-foreground">
            Nenhum dado disponível.
          </p>
        </div>
      )}
    </motion.div>
  );
}
